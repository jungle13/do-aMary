"""
Servidor Web Móvil FastAPI para Conteo Físico, Auditoría y Trazabilidad Multi-Usuario.
Diseñado 100% Mobile-First para smartphones, con autenticación, roles diferenciados
(Bodeguero ciego vs Auxiliar supervisor) y acumulación colaborativa por zonas.
"""
import uvicorn
import threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from core.mobile_service import MobileCountingService
from core.logger import get_logger, log_error

logger = get_logger("MobileServer")
app = FastAPI(title="Doña Mary - Conteo Móvil", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = MobileCountingService()

# --- MODELOS PYDANTIC ---

class LoginRequest(BaseModel):
    usuario: str
    clave: str

class GuardarStockRequest(BaseModel):
    codigo_insumo: str
    cantidad: float
    modo_registro: str = "REEMPLAZAR"  # 'REEMPLAZAR' o 'SUMAR'
    usuario: str = "Móvil Bodega"
    rol: str = "BODEGUERO"
    observacion: str = ""
    mes_periodo: str = "2026-08"

# --- ENDPOINTS API ---

@app.post("/api/login")
def login_movil(req: LoginRequest):
    user_data = service.autenticar_operario(req.usuario, req.clave)
    if user_data:
        return {"exito": True, "usuario": user_data}
    return JSONResponse(status_code=401, content={"exito": False, "error": "Usuario o contraseña incorrectos"})

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "mes_periodo": "2026-08",
        "ip_local": service.get_local_ip(),
        "insumos_en_catalogo": len(service.catalogo_cache)
    }

@app.get("/api/buscar")
def buscar_insumos(q: str = "", mes: str = "2026-08"):
    try:
        return service.buscar_insumos(q, mes_periodo=mes, limit=0)
    except Exception as ex:
        log_error("buscar_insumos endpoint", ex)
        return []

@app.post("/api/guardar")
def guardar_stock(req: GuardarStockRequest):
    res = service.guardar_conteo_movil(
        codigo_insumo=req.codigo_insumo,
        cantidad=req.cantidad,
        modo_registro=req.modo_registro,
        usuario=req.usuario,
        rol=req.rol,
        observacion=req.observacion,
        mes_periodo=req.mes_periodo
    )
    return res

@app.get("/api/insumo/historial/{codigo_insumo}")
def get_historial_insumo(codigo_insumo: str):
    return service.obtener_historial_insumo(codigo_insumo)

# --- ENDPOINTS DE STAGING Y FACTURAS ---

class StagingCargaRequest(BaseModel):
    tipo: str
    fecha: str
    archivo_origen: str = ""
    invoices: list[dict] = []

@app.get("/api/v1/documentos_existentes")
def get_documentos_existentes(tipo: str, fecha: str | None = None, req: Request = None):
    api_key = req.headers.get("X-API-KEY") if req else None
    from config import Config
    if api_key != Config.API_SECRET_KEY:
        return JSONResponse(status_code=401, content={"detail": "No autorizado: API Key inválida"})
    
    from core.supabase_client import get_client
    from core.invoice_classifier import obtener_documentos_registrados
    db = get_client()
    docs = list(obtener_documentos_registrados(db, tipo, fecha))
    return {"tipo": tipo, "fecha": fecha, "total": len(docs), "documentos": docs}

@app.post("/api/v1/cargas/staging")
def recibir_carga_staging(data: StagingCargaRequest, req: Request):
    api_key = req.headers.get("X-API-KEY")
    from config import Config
    if api_key != Config.API_SECRET_KEY:
        return JSONResponse(status_code=401, content={"detail": "No autorizado: API Key inválida"})
    
    from core.invoice_classifier import guardar_lote_en_staging
    ok = guardar_lote_en_staging({
        "tipo": data.tipo,
        "fecha": data.fecha,
        "archivo_origen": data.archivo_origen,
        "invoices": data.invoices
    })
    if ok:
        return {"status": "success", "message": "Carga registrada en Staging", "total_facturas": len(data.invoices)}
    return JSONResponse(status_code=500, content={"detail": "Error al guardar en Staging"})

# --- INTERFAZ WEB MÓVIL (SPA TAILWIND + JS) ---

@app.get("/", response_class=HTMLResponse)
def index_mobile():
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Doña Mary • Conteo Móvil</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { -webkit-tap-highlight-color: transparent; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        .touch-btn:active { transform: scale(0.97); }
        .slide-up { animation: slideUp 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        @keyframes slideUp {
            from { transform: translateY(100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    </style>
</head>
<body class="bg-slate-100 text-slate-800 min-h-screen flex flex-col antialiased select-none">

    <!-- 1. PANTALLA DE LOGIN -->
    <div id="loginScreen" class="fixed inset-0 z-50 bg-slate-900 flex flex-col justify-center items-center p-6 text-white">
        <div class="w-full max-w-sm bg-slate-800/90 border border-slate-700 p-6 rounded-2xl shadow-2xl backdrop-blur">
            <div class="flex items-center space-x-3 mb-6">
                <div class="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg">
                    <i class="fa-solid fa-boxes-stacked text-lg"></i>
                </div>
                <div>
                    <h1 class="text-base font-bold tracking-tight">Doña Mary</h1>
                    <p class="text-xs text-slate-400">Conteo Móvil de Bodega</p>
                </div>
            </div>

            <div id="loginError" class="hidden mb-4 p-3 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-xs flex items-center space-x-2">
                <i class="fa-solid fa-circle-exclamation"></i>
                <span id="loginErrorTxt">Credenciales incorrectas</span>
            </div>

            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Usuario</label>
                    <div class="relative flex items-center">
                        <i class="fa-solid fa-user absolute left-3 text-slate-400 text-sm"></i>
                        <input id="loginUser" type="text" placeholder="Ej: bod1 o aux1" 
                               class="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-sm font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition text-white">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Contraseña</label>
                    <div class="relative flex items-center">
                        <i class="fa-solid fa-lock absolute left-3 text-slate-400 text-sm"></i>
                        <input id="loginPass" type="password" placeholder="••••••••" 
                               class="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-sm font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition text-white"
                               onkeydown="if(event.key==='Enter') login()">
                    </div>
                </div>

                <button onclick="login()" id="btnLogin" class="w-full py-3 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-bold rounded-xl text-sm shadow-lg shadow-blue-600/30 transition flex items-center justify-center space-x-2 touch-btn">
                    <span>Iniciar Conteo</span>
                    <i class="fa-solid fa-arrow-right text-xs"></i>
                </button>
            </div>
            
            <p class="text-[11px] text-slate-500 text-center mt-6">Acceso exclusivo para operarios y auxiliares autorizados en red local Wi-Fi.</p>
        </div>
    </div>

    <!-- 2. APLICACIÓN PRINCIPAL (POST-LOGIN) -->
    <div id="mainApp" class="hidden flex-1 flex flex-col pb-20">
        <!-- Header Fijo -->
        <header class="bg-slate-900 text-white px-4 py-3 sticky top-0 z-30 shadow-md flex items-center justify-between">
            <div class="flex items-center space-x-2.5">
                <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow">
                    <i class="fa-solid fa-boxes-stacked text-sm"></i>
                </div>
                <div>
                    <h1 class="text-sm font-bold tracking-tight">Doña Mary</h1>
                    <div class="flex items-center space-x-1.5">
                        <span id="userBadge" class="text-[10px] text-slate-300 font-semibold">Operario</span>
                        <span id="roleBadge" class="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-blue-400 border border-blue-500/30 font-bold uppercase">Bodega</span>
                    </div>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1 animate-pulse"></span>
                    Wi-Fi
                </span>
                <button onclick="logout()" class="p-1.5 text-slate-400 hover:text-white" title="Cerrar sesión">
                    <i class="fa-solid fa-right-from-bracket text-sm"></i>
                </button>
            </div>
        </header>

        <!-- Buscador Fijo -->
        <div class="bg-white p-3 shadow-sm sticky top-[53px] z-20 border-b border-slate-200">
            <div class="relative flex items-center">
                <i class="fa-solid fa-magnifying-glass absolute left-3 text-slate-400 text-sm"></i>
                <input id="searchInput" type="text" placeholder="Buscar código o nombre del producto..." 
                       class="w-full pl-9 pr-9 py-2.5 bg-slate-100 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none transition"
                       autocomplete="off" autocapitalize="off" spellcheck="false">
                <button id="btnClear" onclick="clearSearch()" class="hidden absolute right-3 w-6 h-6 rounded-full bg-slate-300 text-slate-600 flex items-center justify-center text-xs">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
        </div>

        <!-- Lista de Insumos -->
        <main class="flex-1 p-3 max-w-lg mx-auto w-full">
            <div class="flex justify-between items-center px-1 mb-2">
                <span id="resultsCount" class="text-xs text-slate-500 font-semibold">Cargando catálogo...</span>
                <button onclick="cargarCatalogo()" class="text-xs text-blue-600 font-semibold flex items-center space-x-1">
                    <i class="fa-solid fa-rotate text-[10px]"></i> <span>Actualizar</span>
                </button>
            </div>
            <div id="itemsContainer" class="space-y-2.5"></div>

            <!-- Paginador Móvil Táctil (50 productos por página) -->
            <div id="paginationBar" class="mt-4 p-3 bg-white border border-slate-200 rounded-2xl shadow-sm flex justify-between items-center">
                <button id="btnPrevPage" onclick="cambiarPagina(-1)" class="px-3.5 py-2 bg-slate-100 border border-slate-200 text-slate-700 font-bold rounded-xl text-xs flex items-center space-x-1.5 disabled:opacity-30 disabled:pointer-events-none touch-btn">
                    <i class="fa-solid fa-chevron-left text-[10px]"></i>
                    <span>Anterior</span>
                </button>
                <div class="text-center">
                    <span id="pageIndicator" class="text-xs font-extrabold text-slate-800 block">Pág. 1 de 1</span>
                    <span class="text-[10px] text-slate-400 font-semibold">50 por página</span>
                </div>
                <button id="btnNextPage" onclick="cambiarPagina(1)" class="px-3.5 py-2 bg-slate-100 border border-slate-200 text-slate-700 font-bold rounded-xl text-xs flex items-center space-x-1.5 disabled:opacity-30 disabled:pointer-events-none touch-btn">
                    <span>Siguiente</span>
                    <i class="fa-solid fa-chevron-right text-[10px]"></i>
                </button>
            </div>
        </main>
    </div>

    <!-- 3. MODAL TÁCTIL DE CONTEO (BOTTOM SHEET) -->
    <div id="countModal" class="fixed inset-0 z-40 bg-black/60 hidden flex items-end justify-center backdrop-blur-sm transition-opacity">
        <div class="bg-white w-full max-w-lg rounded-t-3xl p-5 shadow-2xl slide-up">
            <!-- Header Modal -->
            <div class="flex justify-between items-start mb-3 pb-2 border-b border-slate-100">
                <div>
                    <span id="modalCod" class="text-[11px] font-extrabold px-2 py-0.5 rounded bg-blue-600 text-white">0000</span>
                    <h2 id="modalNom" class="text-base font-bold text-slate-900 mt-1 leading-tight">Nombre del Producto</h2>
                    <p id="modalCat" class="text-xs text-slate-500">Categoría</p>
                </div>
                <button onclick="closeModal()" class="w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center touch-btn">
                    <i class="fa-solid fa-xmark text-sm"></i>
                </button>
            </div>

            <!-- Panel Conteo Actual Previo (Visible para todos) -->
            <div id="modalConteoPrevioPanel" class="hidden mb-3 p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl flex justify-between items-center text-xs">
                <div>
                    <span class="text-emerald-700 font-semibold block text-[10px]">Conteo Físico Actual:</span>
                    <span id="modalCantPreviaTxt" class="font-extrabold text-emerald-800 text-sm">0 unds</span>
                </div>
                <div id="modalUltimoUsuarioTxt" class="text-[10px] text-slate-500 font-medium text-right max-w-[180px] truncate">
                    Por Operario
                </div>
            </div>

            <!-- Fila de Información y Botón de Historial (Visible para TODOS) -->
            <div class="mb-3 flex justify-between items-center p-2.5 bg-slate-50 border border-slate-200 rounded-xl">
                <!-- Stock Sistema (Visible SOLO para Auxiliares / Admins) -->
                <div id="auxiliarInfoPanel" class="hidden text-xs">
                    <span class="text-slate-400 text-[10px] block">Stock Sistema:</span>
                    <span id="modalStockSis" class="font-bold text-blue-700 text-xs">0 unds</span>
                </div>
                
                <!-- Botón Historial (Visible para TODOS: Bodegueros, Auxiliares, Admins) -->
                <button type="button" onclick="verHistorialInsumo()" class="ml-auto px-3 py-1.5 bg-white border border-blue-300 text-blue-700 font-bold text-xs rounded-lg shadow-xs flex items-center space-x-1.5 touch-btn">
                    <i class="fa-solid fa-clock-rotate-left text-xs"></i>
                    <span>Ver Historial de Conteos</span>
                </button>
            </div>

            <!-- Selector de Modo de Conteo: Reemplazar o Sumar -->
            <div class="mb-3">
                <label class="block text-xs font-bold text-slate-700 mb-1.5">Modo de Registro:</label>
                <div class="grid grid-cols-2 gap-2">
                    <button type="button" id="btnModoReemplazar" onclick="setModoConteo('REEMPLAZAR')" 
                            class="py-2 px-3 rounded-xl border-2 border-blue-600 bg-blue-50 text-blue-700 font-bold text-xs flex items-center justify-center space-x-1.5 touch-btn">
                        <i class="fa-solid fa-pen-to-square"></i>
                        <span>Reemplazar Total</span>
                    </button>
                    <button type="button" id="btnModoSumar" onclick="setModoConteo('SUMAR')" 
                            class="py-2 px-3 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-xs flex items-center justify-center space-x-1.5 touch-btn">
                        <i class="fa-solid fa-plus"></i>
                        <span>+ Sumar al Conteo</span>
                    </button>
                </div>
            </div>

            <!-- Input Cantidad -->
            <div class="mb-3">
                <label class="block text-xs font-bold text-slate-700 mb-1">Cantidad Física Contada:</label>
                <div class="relative flex items-center">
                    <input id="modalCantInput" type="number" step="any" placeholder="0" 
                           class="w-full py-3 px-4 bg-slate-100 border-2 border-slate-300 rounded-2xl text-2xl font-black text-center text-slate-900 focus:bg-white focus:border-blue-600 focus:ring-4 focus:ring-blue-100 outline-none transition">
                </div>
            </div>

            <!-- Nota / Zona Opcional -->
            <div class="mb-4">
                <input id="modalObsInput" type="text" placeholder="Observación (Ej: Zona B, Estante 2)..." 
                       class="w-full py-2 px-3 bg-slate-100 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:border-blue-500 transition">
            </div>

            <!-- Botón Guardar -->
            <button onclick="guardarConteoModal()" id="btnGuardarModal" 
                    class="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white font-black text-sm rounded-2xl shadow-lg shadow-emerald-600/30 flex items-center justify-center space-x-2 touch-btn">
                <i class="fa-solid fa-check"></i>
                <span>Guardar Conteo Físico</span>
            </button>
        </div>
    </div>

    <!-- 4. MODAL HISTORIAL DE AUDITORÍA DEL INSUMO -->
    <div id="historyModal" class="fixed inset-0 z-50 bg-black/60 hidden flex items-center justify-center p-4 backdrop-blur-sm">
        <div class="bg-white w-full max-w-md rounded-2xl p-5 shadow-2xl max-h-[85vh] flex flex-col">
            <div class="flex justify-between items-center pb-2 border-b border-slate-100 mb-3">
                <div>
                    <h3 class="text-sm font-bold text-slate-900">Historial de Conteo</h3>
                    <p id="histCodNom" class="text-xs text-slate-500">[0001] Insumo</p>
                </div>
                <button onclick="document.getElementById('historyModal').classList.add('hidden')" class="w-7 h-7 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center">
                    <i class="fa-solid fa-xmark text-xs"></i>
                </button>
            </div>
            <div id="histList" class="flex-1 overflow-y-auto space-y-2 pr-1"></div>
        </div>
    </div>

    <!-- SCRIPT JS -->
    <script>
        let currentUser = null;
        let catalogo = [];
        let itemSeleccionado = null;
        let modoConteoActual = 'REEMPLAZAR';

        // Auto-login con localStorage
        window.addEventListener('DOMContentLoaded', () => {
            const saved = localStorage.getItem('dm_user_session');
            if (saved) {
                try {
                    currentUser = JSON.parse(saved);
                    mostrarAppPrincipal();
                } catch(e) { localStorage.removeItem('dm_user_session'); }
            }

            document.getElementById('searchInput').addEventListener('input', debounce(filtrarInsumos, 200));
        });

        async function login() {
            const u = document.getElementById('loginUser').value.trim();
            const p = document.getElementById('loginPass').value.trim();
            const errDiv = document.getElementById('loginError');
            const errTxt = document.getElementById('loginErrorTxt');

            if (!u || !p) {
                errTxt.innerText = "Por favor ingresa usuario y clave";
                errDiv.classList.remove('hidden');
                return;
            }

            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ usuario: u, clave: p })
                });
                const data = await res.json();
                if (res.ok && data.exito) {
                    currentUser = data.usuario;
                    localStorage.setItem('dm_user_session', JSON.stringify(currentUser));
                    mostrarAppPrincipal();
                } else {
                    errTxt.innerText = data.error || "Credenciales incorrectas";
                    errDiv.classList.remove('hidden');
                }
            } catch (ex) {
                errTxt.innerText = "Error de conexión con el servidor";
                errDiv.classList.remove('hidden');
            }
        }

        function logout() {
            localStorage.removeItem('dm_user_session');
            currentUser = null;
            document.getElementById('mainApp').classList.add('hidden');
            document.getElementById('loginScreen').classList.remove('hidden');
            document.getElementById('loginPass').value = '';
        }

        function mostrarAppPrincipal() {
            document.getElementById('loginScreen').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            document.getElementById('userBadge').innerText = currentUser.nombre_completo || currentUser.usuario;
            document.getElementById('roleBadge').innerText = currentUser.rol;
            cargarCatalogo();
        }

        async function cargarCatalogo() {
            const rc = document.getElementById('resultsCount');
            rc.innerText = "Cargando catálogo completo...";
            try {
                const res = await fetch('/api/buscar');
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                if (Array.isArray(data)) {
                    catalogo = data;
                    itemsFiltrados = catalogo;
                    currentPage = 1;
                    renderizarItems();
                } else {
                    throw new Error("Formato de catálogo no válido");
                }
            } catch(e) {
                console.error("Error al cargar catálogo:", e);
                if (rc) rc.innerHTML = `<span class="text-red-500 font-bold">Error: ${escapeHTML(e.message || String(e))}</span> <button onclick="cargarCatalogo()" class="underline text-blue-600 ml-1 font-bold">Reintentar</button>`;
            }
        }

        let itemsFiltrados = [];
        let currentPage = 1;
        const pageSize = 50;

        function filtrarInsumos() {
            const q = document.getElementById('searchInput').value.trim().toLowerCase();
            const btnClear = document.getElementById('btnClear');
            if (q) btnClear.classList.remove('hidden');
            else btnClear.classList.add('hidden');

            currentPage = 1;
            if (!q) {
                itemsFiltrados = catalogo;
            } else {
                const tokens = q.split(' ').filter(t => t.length > 0);
                itemsFiltrados = catalogo.filter(it => {
                    const txt = `${it.codigo_insumo} ${it.nombre} ${it.categoria || ''}`.toLowerCase();
                    return tokens.every(t => txt.includes(t));
                });
            }
            renderizarItems();
        }

        function clearSearch() {
            document.getElementById('searchInput').value = '';
            filtrarInsumos();
        }

        function cambiarPagina(delta) {
            const totalPages = Math.max(1, Math.ceil(itemsFiltrados.length / pageSize));
            const nuevaPag = currentPage + delta;
            if (nuevaPag >= 1 && nuevaPag <= totalPages) {
                currentPage = nuevaPag;
                renderizarItems();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }

        function escapeHTML(str) {
            if (!str) return '';
            return String(str).replace(/[&<>'"]/g, tag => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
            }[tag] || tag));
        }

        window.onerror = function(msg, url, line) {
            console.error("Error global JS:", msg, "linea:", line);
            const rc = document.getElementById('resultsCount');
            if (rc) rc.innerHTML = `<span class="text-red-500 font-bold">Error JS: ${escapeHTML(msg)} (L:${line})</span>`;
        };

        function renderizarItems() {
            const cont = document.getElementById('itemsContainer');
            const rc = document.getElementById('resultsCount');
            const esAuxiliar = (currentUser && (currentUser.rol === 'AUXILIAR' || currentUser.rol === 'ADMINISTRADOR'));
            const totalItems = itemsFiltrados.length;
            const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
            currentPage = Math.min(currentPage, totalPages);

            const contadosCount = catalogo.filter(i => i.cantidad_fisica !== null && i.cantidad_fisica !== undefined).length;
            if (rc) rc.innerText = `${totalItems} productos • ${contadosCount} auditados`;

            // Actualizar paginador táctil
            const pageInd = document.getElementById('pageIndicator');
            if (pageInd) pageInd.innerText = `Pág. ${currentPage} de ${totalPages}`;
            const btnPrev = document.getElementById('btnPrevPage');
            if (btnPrev) btnPrev.disabled = (currentPage <= 1);
            const btnNext = document.getElementById('btnNextPage');
            if (btnNext) btnNext.disabled = (currentPage >= totalPages);
            const pagBar = document.getElementById('paginationBar');
            if (pagBar) pagBar.style.display = (totalItems > 0) ? 'flex' : 'none';

            if (!totalItems) {
                if (cont) cont.innerHTML = '<div class="p-8 text-center text-slate-400 text-sm"><i class="fa-solid fa-box-open text-2xl block mb-2"></i>No se encontraron productos coincidentes.</div>';
                return;
            }

            const start = (currentPage - 1) * pageSize;
            const end = start + pageSize;
            const itemsVisibles = itemsFiltrados.slice(start, end);

            if (cont) {
                cont.innerHTML = itemsVisibles.map(it => {
                    const cod = escapeHTML(it.codigo_insumo);
                    const nom = escapeHTML(it.nombre);
                    const cat = escapeHTML(it.categoria || 'GENERAL');
                    const stockSis = parseFloat(it.cantidad_sistema !== undefined ? it.cantidad_sistema : (it.stock_actual || 0));
                    const fisico = it.cantidad_fisica;
                    const tieneConteo = (fisico !== null && fisico !== undefined);
                    const obs = escapeHTML(it.observacion_conteo || '');

                    const dif = tieneConteo ? (parseFloat(fisico) - stockSis) : 0;
                    let difColor = 'text-slate-500';
                    let difTxt = '0';
                    if (dif > 0) { difColor = 'text-emerald-600'; difTxt = `+${dif}`; }
                    else if (dif < 0) { difColor = 'text-red-600'; difTxt = `${dif}`; }

                    return `
                    <div onclick="abrirModalConteo('${cod}')" class="bg-white p-3.5 rounded-2xl border ${tieneConteo ? 'border-emerald-200 shadow-sm' : 'border-slate-200'} active:border-blue-500 touch-btn cursor-pointer transition">
                        <div class="flex justify-between items-start">
                            <div class="flex-1 pr-2">
                                <div class="flex items-center space-x-1.5 mb-1">
                                    <span class="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-slate-900 text-white">${cod}</span>
                                    <span class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">${cat}</span>
                                </div>
                                <h3 class="text-sm font-bold text-slate-900 leading-snug">${nom}</h3>
                                ${obs ? `<p class="text-[10px] text-slate-500 font-medium mt-1"><i class="fa-solid fa-clock-rotate-left mr-1 text-[9px] text-slate-400"></i>${obs}</p>` : ''}
                            </div>
                            
                            <div class="text-right flex flex-col items-end shrink-0">
                                <!-- Conteo Físico (Visible para todos) -->
                                ${tieneConteo ? `
                                    <span class="text-[9px] font-bold text-emerald-700 uppercase">Físico</span>
                                    <div class="px-2.5 py-0.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 font-black text-sm shadow-xs">
                                        ${parseFloat(fisico)} unds
                                    </div>
                                ` : `
                                    <div class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-400 font-semibold text-[10px]">
                                        Sin contar
                                    </div>
                                `}

                                <!-- Botón Ver Historial directo en Tarjeta (Visible para TODOS) -->
                                <button onclick="event.stopPropagation(); verHistorialInsumo('${cod}')" class="mt-1 px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-700 font-semibold text-[10px] rounded-md shadow-xs flex items-center space-x-1 touch-btn">
                                    <i class="fa-solid fa-clock-rotate-left text-[9px]"></i>
                                    <span>Historial</span>
                                </button>

                                <!-- Información Extra para Auxiliares / Admins -->
                                ${esAuxiliar ? `
                                    <div class="mt-1 text-[10px] font-semibold text-slate-400 flex items-center space-x-1.5">
                                        <span>Sis: <b class="text-slate-700">${stockSis}</b></span>
                                        ${tieneConteo ? `<span>• Dif: <b class="${difColor}">${difTxt}</b></span>` : ''}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                    `;
                }).join('');
            }
        }

        function abrirModalConteo(codigo) {
            itemSeleccionado = catalogo.find(i => String(i.codigo_insumo) === String(codigo));
            if (!itemSeleccionado) return;

            document.getElementById('modalCod').innerText = itemSeleccionado.codigo_insumo;
            document.getElementById('modalNom').innerText = itemSeleccionado.nombre;
            document.getElementById('modalCat').innerText = itemSeleccionado.categoria || 'GENERAL';
            document.getElementById('modalStockSis').innerText = `${itemSeleccionado.cantidad_sistema !== undefined ? itemSeleccionado.cantidad_sistema : (itemSeleccionado.stock_actual || 0)} unds`;

            const fisicoPrev = itemSeleccionado.cantidad_fisica;
            const tieneFisico = (fisicoPrev !== null && fisicoPrev !== undefined);
            
            const prevPanel = document.getElementById('modalConteoPrevioPanel');
            if (tieneFisico) {
                prevPanel.classList.remove('hidden');
                document.getElementById('modalCantPreviaTxt').innerText = `${parseFloat(fisicoPrev)} unds`;
                document.getElementById('modalUltimoUsuarioTxt').innerText = itemSeleccionado.observacion_conteo || 'Conteo previo';
                document.getElementById('modalCantInput').value = parseFloat(fisicoPrev);
            } else {
                prevPanel.classList.add('hidden');
                document.getElementById('modalCantInput').value = '';
            }

            document.getElementById('modalObsInput').value = '';

            const esAuxiliar = (currentUser && (currentUser.rol === 'AUXILIAR' || currentUser.rol === 'ADMINISTRADOR'));
            const auxPanel = document.getElementById('auxiliarInfoPanel');
            if (esAuxiliar) auxPanel.classList.remove('hidden');
            else auxPanel.classList.add('hidden');

            setModoConteo('REEMPLAZAR');

            document.getElementById('countModal').classList.remove('hidden');
            setTimeout(() => document.getElementById('modalCantInput').focus(), 100);
        }

        function closeModal() {
            document.getElementById('countModal').classList.add('hidden');
            itemSeleccionado = null;
        }

        function setModoConteo(modo) {
            modoConteoActual = modo;
            const btnR = document.getElementById('btnModoReemplazar');
            const btnS = document.getElementById('btnModoSumar');

            if (modo === 'REEMPLAZAR') {
                btnR.className = "py-2 px-3 rounded-xl border-2 border-blue-600 bg-blue-50 text-blue-700 font-bold text-xs flex items-center justify-center space-x-1.5 touch-btn";
                btnS.className = "py-2 px-3 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-xs flex items-center justify-center space-x-1.5 touch-btn";
            } else {
                btnS.className = "py-2 px-3 rounded-xl border-2 border-emerald-600 bg-emerald-50 text-emerald-700 font-bold text-xs flex items-center justify-center space-x-1.5 touch-btn";
                btnR.className = "py-2 px-3 rounded-xl border border-slate-300 bg-white text-slate-700 font-semibold text-xs flex items-center justify-center space-x-1.5 touch-btn";
            }
        }

        async function guardarConteoModal() {
            if (!itemSeleccionado) {
                alert("Por favor selecciona un insumo.");
                return;
            }
            if (!currentUser) {
                alert("Tu sesión no está activa. Por favor ingresa nuevamente.");
                logout();
                return;
            }

            const cantVal = document.getElementById('modalCantInput').value;
            if (cantVal === '' || isNaN(cantVal)) {
                alert("Por favor ingresa una cantidad numérica válida.");
                return;
            }

            const cant = parseFloat(cantVal);
            const obs = (document.getElementById('modalObsInput').value || '').trim();
            const btn = document.getElementById('btnGuardarModal');
            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin mr-1"></i> <span>Guardando...</span>';

            const payload = {
                codigo_insumo: String(itemSeleccionado.codigo_insumo),
                cantidad: cant,
                modo_registro: modoConteoActual || 'REEMPLAZAR',
                usuario: currentUser.nombre_completo || currentUser.usuario || 'Operario',
                rol: currentUser.rol || 'BODEGUERO',
                observacion: obs,
                mes_periodo: '2026-08'
            };

            try {
                const res = await fetch('/api/guardar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok && data && data.exito) {
                    const cod = payload.codigo_insumo;
                    const cantTotal = parseFloat(data.cantidad_total);
                    const obsTexto = `[${payload.usuario} (${payload.rol})] ${payload.modo_registro === 'SUMAR' ? 'Suma' : 'Conteo directo'}: ${cantTotal} unds${payload.observacion ? ' - ' + payload.observacion : ''}`;

                    // 1. Actualizar catálogo maestro en memoria (solo cantidad_fisica)
                    const it = catalogo.find(i => String(i.codigo_insumo) === String(cod));
                    if (it) {
                        it.cantidad_fisica = cantTotal;
                        it.observacion_conteo = obsTexto;
                        it.fecha_conteo = new Date().toISOString();
                    }

                    // 2. Actualizar en lista filtrada activa (solo cantidad_fisica)
                    const itF = itemsFiltrados.find(i => String(i.codigo_insumo) === String(cod));
                    if (itF) {
                        itF.cantidad_fisica = cantTotal;
                        itF.observacion_conteo = obsTexto;
                        itF.fecha_conteo = new Date().toISOString();
                    }

                    closeModal();
                    renderizarItems();
                    mostrarToast(`✓ Guardado: ${cantTotal} unds`);
                } else {
                    const msg = (data && (data.error || data.detail || data.mensaje)) || "No se pudo guardar";
                    alert("Aviso: " + msg);
                }
            } catch(e) {
                console.error("Error al guardar:", e);
                alert("Error de comunicación: " + (e.message || "Verifica tu conexión Wi-Fi"));
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-check mr-1"></i> <span>Guardar Conteo Físico</span>';
            }
        }

        function mostrarToast(mensaje) {
            let toast = document.getElementById('appToast');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'appToast';
                toast.className = 'fixed bottom-5 left-1/2 -translate-x-1/2 z-50 bg-slate-900 text-white text-xs font-bold px-4 py-2.5 rounded-full shadow-2xl flex items-center space-x-2 border border-slate-700 transition-all duration-300 opacity-0 pointer-events-none';
                document.body.appendChild(toast);
            }
            toast.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> <span>${mensaje}</span>`;
            toast.classList.remove('opacity-0', 'pointer-events-none');
            setTimeout(() => {
                toast.classList.add('opacity-0', 'pointer-events-none');
            }, 2500);
        }

        async function verHistorialInsumo(codigo) {
            let it = itemSeleccionado;
            if (codigo) {
                it = catalogo.find(i => String(i.codigo_insumo) === String(codigo)) || itemSeleccionado;
            }
            if (!it) return;

            document.getElementById('histCodNom').innerText = `[${it.codigo_insumo}] ${it.nombre}`;
            const list = document.getElementById('histList');
            list.innerHTML = '<div class="p-4 text-center text-xs text-slate-400"><i class="fa-solid fa-spinner animate-spin"></i> Cargando historial...</div>';
            document.getElementById('historyModal').classList.remove('hidden');

            try {
                const res = await fetch(`/api/insumo/historial/${it.codigo_insumo}`);
                const data = await res.json();
                if (!data || !data.length) {
                    list.innerHTML = '<div class="p-4 text-center text-xs text-slate-400">Sin historial de conteos registrados.</div>';
                    return;
                }

                list.innerHTML = data.map(h => `
                    <div class="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                        <div class="flex justify-between items-center font-bold text-slate-800">
                            <span class="flex items-center space-x-1">
                                <i class="fa-solid fa-user text-[10px] text-blue-500"></i>
                                <span>${h.usuario || 'Operario'} <span class="text-[10px] font-semibold text-slate-400">(${h.rol || 'OPERADOR'})</span></span>
                            </span>
                            <span class="text-blue-700 font-extrabold text-sm">${h.cantidad_ingresada} unds</span>
                        </div>
                        <div class="text-[10px] text-slate-500 flex justify-between">
                            <span><i class="fa-regular fa-clock mr-1"></i>${h.fecha || ''} ${h.hora || ''} • ${h.dispositivo || 'WEB'}</span>
                            <span class="font-semibold px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 text-[9px]">${h.modo || 'REGISTRO'}</span>
                        </div>
                        ${h.observacion ? `<p class="text-[10px] text-slate-600 bg-white p-1 rounded border border-slate-100 italic">${h.observacion}</p>` : ''}
                    </div>
                `).join('');
            } catch(e) {
                list.innerHTML = '<div class="p-4 text-center text-xs text-red-500">Error al cargar historial.</div>';
            }
        }

        function debounce(fn, ms) {
            let timer;
            return (...args) => {
                clearTimeout(timer);
                timer = setTimeout(() => fn.apply(this, args), ms);
            };
        }
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

def iniciar_servidor_en_hilo(port: int = 8550):
    if not MobileCountingService._server_running:
        def run_server():
            MobileCountingService._server_running = True
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        MobileCountingService._server_thread = thread
        logger.info(f"Servidor Web Móvil iniciado en 0.0.0.0:{port}")
