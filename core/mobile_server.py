"""
Servidor Web Móvil FastAPI para Conteo Físico y Actualización de Stock Inicial de Agosto en Red Wi-Fi.
Diseñado 100% Mobile-First para uso táctil en smartphones de bodega.
"""
import uvicorn
import threading
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from core.mobile_service import MobileCountingService
from core.logger import get_logger, log_error

logger = get_logger("MobileServer")
app = FastAPI(title="Doña Mary - Conteo Móvil", docs_url=None, redoc_url=None)
service = MobileCountingService()

class GuardarStockRequest(BaseModel):
    codigo_insumo: str
    cantidad: float
    costo_unitario: float | None = None
    usuario: str = "Móvil Bodega"

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "mes_periodo": "2026-08",
        "ip_local": service.get_local_ip(),
        "insumos_en_catalogo": len(service.catalogo_cache)
    }

@app.get("/api/buscar")
def buscar_insumos(q: str = ""):
    return service.buscar_insumos(q, limit=40)

@app.post("/api/guardar")
def guardar_stock(req: GuardarStockRequest):
    res = service.guardar_stock_inicial(
        codigo_insumo=req.codigo_insumo,
        cantidad=req.cantidad,
        costo_unitario=req.costo_unitario,
        usuario=req.usuario
    )
    return res

@app.get("/api/historial")
def get_historial():
    return service.get_historial()

# --- ENDPOINTS SEGUROS DE STAGING Y DEDUPLICACIÓN DE FACTURAS ---

class StagingCargaRequest(BaseModel):
    tipo: str  # VENTAS_POS, VENTAS_REMISION, COMPRAS
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

@app.get("/", response_class=HTMLResponse)
def index_mobile():
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Doña Mary • Conteo Bodega</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { -webkit-tap-highlight-color: transparent; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        .touch-btn:active { transform: scale(0.96); }
        .slide-up { animation: slideUp 0.25s ease-out forwards; }
        @keyframes slideUp {
            from { transform: translateY(100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    </style>
</head>
<body class="bg-slate-100 text-slate-800 min-h-screen flex flex-col antialiased select-none pb-20">

    <!-- Header Fijo Superior -->
    <header class="bg-slate-900 text-white px-4 py-3 sticky top-0 z-30 shadow-md flex items-center justify-between">
        <div class="flex items-center space-x-2">
            <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow">
                <i class="fa-solid fa-boxes-stacked text-sm"></i>
            </div>
            <div>
                <h1 class="text-sm font-bold tracking-tight">Doña Mary</h1>
                <p class="text-[10px] text-slate-400 font-medium">Stock Inicial • Agosto 2026</p>
            </div>
        </div>
        <div class="flex items-center space-x-1.5">
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1 animate-pulse"></span>
                Wi-Fi En Vivo
            </span>
        </div>
    </header>

    <!-- Barra de Búsqueda Fija -->
    <div class="bg-white p-3 shadow-sm sticky top-[53px] z-20 border-b border-slate-200">
        <div class="relative flex items-center">
            <i class="fa-solid fa-magnifying-glass absolute left-3 text-slate-400 text-sm"></i>
            <input id="searchInput" type="text" placeholder="Escribe código o nombre del producto..." 
                   class="w-full pl-9 pr-9 py-2.5 bg-slate-100 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:border-blue-600 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                   autocomplete="off" autocapitalize="off" spellcheck="false">
            <button id="btnClear" onclick="clearSearch()" class="hidden absolute right-3 w-6 h-6 rounded-full bg-slate-300 text-slate-600 flex items-center justify-center text-xs">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
    </div>

    <!-- Contenido Principal: Lista de Insumos -->
    <main class="flex-1 p-3 max-w-lg mx-auto w-full">
        <!-- Indicador de cantidad de resultados -->
        <div class="flex justify-between items-center px-1 mb-2">
            <span id="resultsCount" class="text-xs text-slate-500 font-semibold">Cargando catálogo...</span>
            <button onclick="cargarCatalogo(true)" class="text-xs text-blue-600 font-medium flex items-center space-x-1">
                <i class="fa-solid fa-rotate text-[10px]"></i> <span>Actualizar</span>
            </button>
        </div>

        <!-- Lista de Resultados -->
        <div id="itemsContainer" class="space-y-2"></div>
        
        <!-- Estado Vacío -->
        <div id="emptyState" class="hidden py-12 text-center text-slate-400">
            <i class="fa-solid fa-box-open text-4xl mb-2 text-slate-300"></i>
            <p class="text-sm font-medium">No se encontraron insumos</p>
            <p class="text-xs text-slate-400">Verifica la ortografía o busca por código</p>
        </div>
    </main>

    <!-- Vista de Historial Modal/Panel -->
    <div id="historialPanel" class="hidden fixed inset-0 bg-slate-900/60 z-40 backdrop-blur-sm flex flex-col justify-end">
        <div class="bg-white rounded-t-3xl p-4 max-h-[80vh] flex flex-col slide-up shadow-2xl">
            <div class="flex justify-between items-center border-b pb-3 mb-2">
                <h3 class="font-bold text-base text-slate-900 flex items-center">
                    <i class="fa-solid fa-clock-rotate-left mr-2 text-blue-600"></i> Últimos Guardados
                </h3>
                <button onclick="toggleHistorial()" class="w-8 h-8 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            <div id="historialList" class="flex-1 overflow-y-auto space-y-2 divide-y divide-slate-100 pr-1"></div>
        </div>
    </div>

    <!-- Modal / Bottom Sheet para Registrar Conteo -->
    <div id="conteoModal" class="hidden fixed inset-0 bg-slate-900/60 z-50 backdrop-blur-sm flex flex-col justify-end">
        <div class="bg-white rounded-t-3xl p-5 slide-up shadow-2xl border-t border-slate-200 max-w-lg mx-auto w-full">
            <div class="flex justify-between items-start mb-3">
                <div class="pr-2">
                    <span id="modalCategory" class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200"></span>
                    <h2 id="modalNombre" class="text-base font-bold text-slate-900 mt-1 leading-snug"></h2>
                    <p id="modalCodigo" class="text-xs font-semibold text-slate-400 mt-0.5"></p>
                </div>
                <button onclick="cerrarModal()" class="w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center touch-btn">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <!-- Cantidad Actual y Selector -->
            <div class="bg-slate-50 rounded-2xl p-4 border border-slate-200 mb-3 text-center">
                <label class="block text-xs font-semibold text-slate-500 mb-1">CANTIDAD STOCK INICIAL (FÍSICO):</label>
                
                <div class="flex items-center justify-center space-x-3 my-2">
                    <button onclick="ajustarCantidad(-1)" class="w-12 h-12 rounded-xl bg-white border border-slate-200 text-slate-700 font-bold text-xl shadow-sm touch-btn flex items-center justify-center">
                        <i class="fa-solid fa-minus"></i>
                    </button>
                    <input id="modalCantidad" type="number" step="any" min="0" 
                           class="w-36 text-center text-3xl font-extrabold text-slate-900 bg-white border-2 border-blue-600 rounded-xl py-2 shadow-inner outline-none"
                           value="0">
                    <button onclick="ajustarCantidad(1)" class="w-12 h-12 rounded-xl bg-white border border-slate-200 text-slate-700 font-bold text-xl shadow-sm touch-btn flex items-center justify-center">
                        <i class="fa-solid fa-plus"></i>
                    </button>
                </div>

                <!-- Botones Rápidos de Suma -->
                <div class="grid grid-cols-4 gap-2 mt-3">
                    <button onclick="sumarRapido(1)" class="py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-bold text-slate-600 shadow-sm touch-btn">+1</button>
                    <button onclick="sumarRapido(5)" class="py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-bold text-slate-600 shadow-sm touch-btn">+5</button>
                    <button onclick="sumarRapido(10)" class="py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-bold text-slate-600 shadow-sm touch-btn">+10</button>
                    <button onclick="sumarRapido(50)" class="py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-bold text-slate-600 shadow-sm touch-btn">+50</button>
                </div>
            </div>

            <!-- Costo Unitario Editable -->
            <div class="bg-slate-50 rounded-2xl p-3.5 border border-slate-200 mb-4">
                <div class="flex justify-between items-center mb-1">
                    <label class="text-xs font-bold text-slate-600">COSTO UNITARIO ($):</label>
                    <span class="text-[10px] text-blue-600 font-semibold">Traído de Catálogo / Compra</span>
                </div>
                <div class="relative flex items-center">
                    <span class="absolute left-3 text-slate-400 font-bold text-sm">$</span>
                    <input id="modalCosto" type="number" step="any" min="0" placeholder="0" 
                           class="w-full pl-8 pr-3 py-2 bg-white border border-slate-300 rounded-xl text-base font-bold text-slate-800 focus:border-blue-600 outline-none">
                </div>
            </div>

            <!-- Botón Guardar -->
            <button id="btnGuardar" onclick="confirmarGuardado()" class="w-full py-3.5 bg-emerald-600 text-white rounded-xl font-bold text-base flex items-center justify-center space-x-2 shadow-lg shadow-emerald-600/30 touch-btn">
                <i class="fa-solid fa-check text-lg"></i>
                <span>Confirmar y Guardar Agosto</span>
            </button>
        </div>
    </div>

    <!-- Barra de Navegación Inferior Fija -->
    <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-6 py-2 flex justify-around items-center z-30 shadow-lg max-w-lg mx-auto">
        <button onclick="window.scrollTo({top: 0, behavior: 'smooth'})" class="flex flex-col items-center text-blue-600 font-medium">
            <i class="fa-solid fa-magnifying-glass text-lg"></i>
            <span class="text-[10px] mt-0.5 font-bold">Buscar</span>
        </button>
        <button onclick="toggleHistorial()" class="flex flex-col items-center text-slate-500 font-medium hover:text-blue-600">
            <i class="fa-solid fa-list-check text-lg"></i>
            <span class="text-[10px] mt-0.5">Historial</span>
        </button>
    </nav>

    <!-- Notificación Toast Flotante -->
    <div id="toast" class="hidden fixed top-4 left-1/2 transform -translate-x-1/2 z-50 bg-slate-900 text-white px-4 py-2.5 rounded-2xl shadow-xl flex items-center space-x-2 text-xs font-bold transition-all border border-slate-700">
        <i id="toastIcon" class="fa-solid fa-circle-check text-emerald-400 text-base"></i>
        <span id="toastMsg">Mensaje</span>
    </div>

    <!-- Script de Lógica Frontend -->
    <script>
        let currentItem = null;
        let searchTimeout = null;

        document.addEventListener('DOMContentLoaded', () => {
            cargarCatalogo();
            document.getElementById('searchInput').addEventListener('input', (e) => {
                const val = e.target.value;
                document.getElementById('btnClear').classList.toggle('hidden', !val);
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => buscar(val), 200);
            });
        });

        function clearSearch() {
            const input = document.getElementById('searchInput');
            input.value = '';
            document.getElementById('btnClear').classList.add('hidden');
            buscar('');
            input.focus();
        }

        async function cargarCatalogo(forzar = false) {
            buscar(document.getElementById('searchInput').value || '');
        }

        async function buscar(query) {
            try {
                const res = await fetch(`/api/buscar?q=${encodeURIComponent(query)}`);
                const items = await res.json();
                renderItems(items);
            } catch (err) {
                mostrarToast('Error al conectar con la base de datos', false);
            }
        }

        function renderItems(items) {
            const container = document.getElementById('itemsContainer');
            const emptyState = document.getElementById('emptyState');
            const countLabel = document.getElementById('resultsCount');
            
            container.innerHTML = '';
            countLabel.textContent = `${items.length} insumo(s) disponible(s)`;

            if (items.length === 0) {
                emptyState.classList.remove('hidden');
                return;
            }
            emptyState.classList.add('hidden');

            items.forEach(item => {
                const card = document.createElement('div');
                card.className = 'bg-white rounded-2xl p-3.5 border border-slate-200/80 shadow-sm flex items-center justify-between touch-btn';
                card.onclick = () => abrirModalConteo(item);

                const stock = item.stock_actual !== null && item.stock_actual !== undefined ? item.stock_actual : 0;
                const costo = item.costo_unitario !== null && item.costo_unitario !== undefined ? item.costo_unitario : 0;

                card.innerHTML = `
                    <div class="pr-2 flex-1">
                        <div class="flex items-center space-x-1.5 mb-1">
                            <span class="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-slate-800 text-white">${item.codigo_insumo}</span>
                            <span class="text-[10px] font-semibold text-slate-500 uppercase truncate max-w-[150px]">${item.categoria || 'Sin categoría'}</span>
                        </div>
                        <h3 class="text-xs font-bold text-slate-800 leading-tight line-clamp-2">${item.nombre}</h3>
                        <span class="text-[10px] text-slate-400 font-medium mt-0.5 block">Costo: $${costo.toLocaleString()}</span>
                    </div>
                    <div class="text-right pl-2 border-l border-slate-100 flex flex-col items-end">
                        <span class="text-[10px] text-slate-400 font-semibold">Stock Actual</span>
                        <span class="text-sm font-extrabold text-blue-600">${stock}</span>
                        <span class="text-[9px] text-slate-400 uppercase">${item.tipo_unidad || 'und'}</span>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function abrirModalConteo(item) {
            currentItem = item;
            document.getElementById('modalNombre').textContent = item.nombre;
            document.getElementById('modalCodigo').textContent = `Código Maestro: [${item.codigo_insumo}]`;
            document.getElementById('modalCategory').textContent = item.categoria || 'GENERAL';
            
            const cantInput = document.getElementById('modalCantidad');
            cantInput.value = item.stock_actual || 0;

            const costoInput = document.getElementById('modalCosto');
            costoInput.value = item.costo_unitario || 0;

            document.getElementById('conteoModal').classList.remove('hidden');
            if (navigator.vibrate) navigator.vibrate(30);
            cantInput.focus();
            cantInput.select();
        }

        function cerrarModal() {
            document.getElementById('conteoModal').classList.add('hidden');
            currentItem = null;
        }

        function ajustarCantidad(delta) {
            const input = document.getElementById('modalCantidad');
            let val = parseFloat(input.value) || 0;
            val = Math.max(0, val + delta);
            input.value = val;
            if (navigator.vibrate) navigator.vibrate(20);
        }

        function sumarRapido(delta) {
            const input = document.getElementById('modalCantidad');
            let val = parseFloat(input.value) || 0;
            input.value = val + delta;
            if (navigator.vibrate) navigator.vibrate(20);
        }

        async function confirmarGuardado() {
            if (!currentItem) return;

            const btn = document.getElementById('btnGuardar');
            const cantInput = document.getElementById('modalCantidad');
            const costoInput = document.getElementById('modalCosto');
            const cantidad = parseFloat(cantInput.value) || 0;
            const costo = parseFloat(costoInput.value) || 0;

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Guardando en Agosto...</span>';

            try {
                const res = await fetch('/api/guardar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        codigo_insumo: currentItem.codigo_insumo,
                        cantidad: cantidad,
                        costo_unitario: costo,
                        usuario: 'Operario Móvil Bodega'
                    })
                });

                const data = await res.json();
                if (data.exito) {
                    mostrarToast(`[${currentItem.codigo_insumo}] Guardado (${cantidad} unds - $${costo})`, true);
                    if (navigator.vibrate) navigator.vibrate([50, 50, 50]);
                    cerrarModal();
                    buscar(document.getElementById('searchInput').value || '');
                } else {
                    mostrarToast(data.error || 'Error al guardar', false);
                }
            } catch (err) {
                mostrarToast('Error de conexión con el servidor', false);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-check text-lg"></i> <span>Confirmar y Guardar Agosto</span>';
            }
        }

        async function toggleHistorial() {
            const panel = document.getElementById('historialPanel');
            const isHidden = panel.classList.contains('hidden');
            if (isHidden) {
                panel.classList.remove('hidden');
                cargarHistorialList();
            } else {
                panel.classList.add('hidden');
            }
        }

        async function cargarHistorialList() {
            const list = document.getElementById('historialList');
            list.innerHTML = '<p class="text-center text-xs text-slate-400 py-4">Cargando...</p>';
            try {
                const res = await fetch('/api/historial');
                const data = await res.json();
                if (data.length === 0) {
                    list.innerHTML = '<p class="text-center text-xs text-slate-400 py-6">No hay registros guardados en esta sesión.</p>';
                    return;
                }
                list.innerHTML = '';
                data.forEach(h => {
                    const row = document.createElement('div');
                    row.className = 'py-2 flex justify-between items-center';
                    row.innerHTML = `
                        <div class="pr-2">
                            <span class="text-[10px] font-bold text-slate-800">[${h.codigo}]</span>
                            <h4 class="text-xs font-semibold text-slate-700 leading-tight">${h.nombre}</h4>
                            <span class="text-[9px] text-slate-400">${h.hora} • ${h.usuario}</span>
                        </div>
                        <div class="text-right">
                            <span class="text-sm font-bold text-emerald-600">${h.cantidad}</span>
                        </div>
                    `;
                    list.appendChild(row);
                });
            } catch (err) {
                list.innerHTML = '<p class="text-center text-xs text-red-500 py-4">Error al cargar historial</p>';
            }
        }

        function mostrarToast(msg, isSuccess = true) {
            const toast = document.getElementById('toast');
            const toastMsg = document.getElementById('toastMsg');
            const toastIcon = document.getElementById('toastIcon');

            toastMsg.textContent = msg;
            if (isSuccess) {
                toastIcon.className = 'fa-solid fa-circle-check text-emerald-400 text-base';
            } else {
                toastIcon.className = 'fa-solid fa-circle-exclamation text-rose-400 text-base';
            }

            toast.classList.remove('hidden');
            setTimeout(() => {
                toast.classList.add('hidden');
            }, 3000);
        }
    </script>
</body>
</html>
    """
    return html_content

def iniciar_servidor_en_hilo(port: int = 8550):
    """Lanza el servidor FastAPI en segundo plano en 0.0.0.0."""
    if MobileCountingService._server_running:
        logger.info("El servidor móvil ya se encuentra activo.")
        return

    def run():
        MobileCountingService._server_running = True
        logger.info(f"Servidor Web Móvil iniciado en 0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

    thread = threading.Thread(target=run, daemon=True)
    MobileCountingService._server_thread = thread
    thread.start()
