"""
Módulo de gestión y sincronización de catálogos comerciales para Sistema Doña Mary.
Maneja la carga de metadatos, sincronización con precios de inventario de Supabase
y exportación a PDF de alta resolución mediante Microsoft Edge / Chrome headless.
"""
import os
import json
import re
import subprocess
import tempfile
import io
import urllib.parse
import unicodedata
import requests
from PIL import Image
from config import Config
from core.logger import get_logger, log_error
from core.database import BaseDatabase

logger = get_logger("CatalogManager")

# Configuración de Supabase Storage para Fotos de Catálogos
BUCKET_FOTOS = "catalogo_fotos"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024 # Límite de 5 MB de subida
FORMATOS_FOTOS_PERMITIDOS = [".jpg", ".jpeg", ".png", ".webp"]

CATALOGOS_CONFIG = {
    "aseo": {
        "key": "aseo",
        "nombre": "Aseo",
        "titulo_completo": "Catálogo Oficial Línea de Aseo",
        "subtitulo": "LÍNEA DE ASEO INSTITUCIONAL",
        "icono": "CLEANING_SERVICES_ROUNDED",
        "color_base": "#0096c7",
        "color_oscuro": "#023e8a",
        "color_acento": "#00e5ff",
        "archivo_html": "Catalogo_Aseo_Dona_Mary.html",
        "json_file": "catalogo_aseo_items.json"
    },
    "bolsas": {
        "key": "bolsas",
        "nombre": "Bolsas",
        "titulo_completo": "Catálogo Oficial Línea de Bolsas",
        "subtitulo": "LÍNEA DE BOLSAS Y EMPAQUES",
        "icono": "SHOPPING_BAG_ROUNDED",
        "color_base": "#059669",
        "color_oscuro": "#064e3b",
        "color_acento": "#34d399",
        "archivo_html": "Catalogo_Bolsas_Dona_Mary.html",
        "json_file": "catalogo_bolsas_items.json"
    },
    "desechables": {
        "key": "desechables",
        "nombre": "Desechables",
        "titulo_completo": "Catálogo Oficial Línea de Desechables",
        "subtitulo": "LÍNEA DE DESECHABLES Y EPP",
        "icono": "RESTAURANT_ROUNDED",
        "color_base": "#d97706",
        "color_oscuro": "#78350f",
        "color_acento": "#fbbf24",
        "archivo_html": "Catalogo_Desechables_Dona_Mary.html",
        "json_file": "catalogo_desechables_items.json"
    },
    "papeleria": {
        "key": "papeleria",
        "nombre": "Papelería",
        "titulo_completo": "Catálogo Oficial Línea de Papelería",
        "subtitulo": "LÍNEA DE PAPELERÍA COMERCIAL",
        "icono": "DESCRIPTION_ROUNDED",
        "color_base": "#2563eb",
        "color_oscuro": "#1e3a8a",
        "color_acento": "#60a5fa",
        "archivo_html": "Catalogo_Papeleria_Dona_Mary.html",
        "json_file": "catalogo_papeleria_items.json"
    },
    "reposteria": {
        "key": "reposteria",
        "nombre": "Repostería & Dulcería",
        "titulo_completo": "Catálogo Oficial Línea de Repostería & Dulcería",
        "subtitulo": "LÍNEA DE REPOSTERÍA Y DULCERÍA",
        "icono": "CAKE_ROUNDED",
        "color_base": "#db2777",
        "color_oscuro": "#831843",
        "color_acento": "#f472b6",
        "archivo_html": "Catalogo_Reposteria_Dona_Mary.html",
        "json_file": "catalogo_reposteria_items.json"
    },
    "salsamentaria": {
        "key": "salsamentaria",
        "nombre": "Salsamentaria",
        "titulo_completo": "Catálogo Oficial Línea de Salsamentaria",
        "subtitulo": "LÍNEA DE SALSAMENTARIA Y CONDIMENTOS",
        "icono": "FASTFOOD_ROUNDED",
        "color_base": "#dc2626",
        "color_oscuro": "#7f1d1d",
        "color_acento": "#f87171",
        "archivo_html": "Catalogo_Salsamentaria_Dona_Mary.html",
        "json_file": "catalogo_salsamentaria_items.json"
    }
}

RUTA_DEFAULT_CATALOGOS = r"C:\Users\Home\Desktop\CATALOGO DOÑA MARY"
RUTA_FOTOS_BASE = os.path.join(RUTA_DEFAULT_CATALOGOS, "CATALOGO IMAGENES NUEVAS DOÑA MARY")

def guardar_items_catalogo(catalogo_key: str, items: list[dict]) -> bool:
    """Guarda la lista de ítems de un catálogo tanto en assets como en Desktop."""
    global _CACHE_MAPEO_PAGINAS
    _CACHE_MAPEO_PAGINAS.pop(catalogo_key, None)

    cfg = CATALOGOS_CONFIG.get(catalogo_key)
    if not cfg:
        return False
    json_name = cfg["json_file"]

    # Deduplicación estricta por código dentro del mismo catálogo
    items_dedup = []
    seen_cods = set()
    for it in items:
        cod = str(it.get("codigo", "")).strip()
        if cod and cod in seen_cods:
            continue
        if cod:
            seen_cods.add(cod)
        items_dedup.append(it)
    
    # 1. Guardar en assets
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    asset_path = os.path.join(base_dir, "assets", "catalogos", json_name)
    os.makedirs(os.path.dirname(asset_path), exist_ok=True)
    try:
        with open(asset_path, "w", encoding="utf-8") as f:
            json.dump(items_dedup, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        logger.warning(f"No se pudo guardar en {asset_path}: {ex}")

    # 2. Guardar en Desktop
    desktop_json = os.path.join(RUTA_DEFAULT_CATALOGOS, json_name)
    try:
        with open(desktop_json, "w", encoding="utf-8") as f:
            json.dump(items_dedup, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        logger.warning(f"No se pudo guardar en {desktop_json}: {ex}")

    return True

def _normalizar_nombre_archivo(nombre: str) -> str:
    """
    Limpia y normaliza el nombre a caracteres ASCII seguros ([A-Za-z0-9_-])
    eliminando tildes y diacríticos (ej: 'Ñ' -> 'N', 'Ó' -> 'O') para garantizar
    compatibilidad total con las restricciones de clave S3 de Supabase Storage.
    """
    if not nombre:
        return "INSUMO"
    # 1. Separar tildes y diacríticos (Ñ -> N, Ó -> O, etc.)
    norm_nfkd = unicodedata.normalize('NFKD', str(nombre))
    solo_ascii = "".join(c for c in norm_nfkd if not unicodedata.combining(c))
    # 2. Reemplazar espacios por _ y conservar únicamente caracteres seguros
    con_guiones = solo_ascii.strip().replace(" ", "_")
    limpio = re.sub(r'[^A-Za-z0-9_-]', '', con_guiones)
    # 3. Colapsar guiones bajos repetidos
    limpio = re.sub(r'_+', '_', limpio).strip('_').upper()
    return limpio or "INSUMO"

def get_supabase_storage_base_url() -> str:
    """Extrae la URL base del proyecto Supabase (ej: https://xxx.supabase.co)."""
    parsed = urllib.parse.urlparse(Config.SUPABASE_URL)
    return f"{parsed.scheme}://{parsed.netloc}"

def get_foto_storage_path(catalogo_key: str, nombre_insumo: str) -> str:
    """Retorna la ruta relativa del archivo en el bucket (ej: aseo/JABON_REY.jpg)."""
    nombre_limpio = _normalizar_nombre_archivo(nombre_insumo)
    return f"{catalogo_key.lower()}/{nombre_limpio}.jpg"

def get_foto_public_url(catalogo_key: str, nombre_insumo: str) -> str:
    """Retorna la URL pública directa de la foto alojada en Supabase Storage."""
    base_url = get_supabase_storage_base_url()
    storage_path = get_foto_storage_path(catalogo_key, nombre_insumo)
    return f"{base_url}/storage/v1/object/public/{BUCKET_FOTOS}/{storage_path}"

# Cache en memoria de fotos existentes en Supabase Storage (O(1) lookups)
_CACHE_FOTOS_STORAGE: dict[str, set[str]] = {}

def precargar_cache_fotos_storage(catalogo_key: str = None) -> set[str]:
    """
    Descarga en 1 sola petición HTTP ligera la lista completa de fotos en Supabase Storage
    y la indexa en memoria para búsquedas O(1) instantáneas (< 0.001 ms).
    """
    global _CACHE_FOTOS_STORAGE
    base_url = get_supabase_storage_base_url()
    headers = {
        "apikey": Config.SUPABASE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    cats = [catalogo_key.lower()] if catalogo_key else [k.lower() for k in CATALOGOS_CONFIG.keys()]
    for c_key in cats:
        try:
            url = f"{base_url}/storage/v1/object/list/{BUCKET_FOTOS}"
            res = requests.post(url, headers=headers, json={"prefix": c_key, "limit": 1000}, timeout=8)
            if res.status_code == 200:
                archivos_set = set(obj.get("name", "").upper() for obj in res.json() if obj.get("name"))
                _CACHE_FOTOS_STORAGE[c_key] = archivos_set
            else:
                if c_key not in _CACHE_FOTOS_STORAGE:
                    _CACHE_FOTOS_STORAGE[c_key] = set()
        except Exception as ex:
            logger.warning(f"Error precargando cache de fotos para {c_key}: {ex}")
            if c_key not in _CACHE_FOTOS_STORAGE:
                _CACHE_FOTOS_STORAGE[c_key] = set()
                
    return _CACHE_FOTOS_STORAGE.get(catalogo_key.lower() if catalogo_key else "aseo", set())

def comprobar_foto_en_storage(catalogo_key: str, nombre_insumo: str) -> str | None:
    """
    Verifica instantáneamente en memoria si la foto existe en Supabase Storage.
    Cero latencia de red. Retorna la URL pública si existe, o None si no.
    """
    if not nombre_insumo:
        return None
    c_key = catalogo_key.lower()
    if c_key not in _CACHE_FOTOS_STORAGE:
        precargar_cache_fotos_storage(c_key)
        
    nombre_limpio = _normalizar_nombre_archivo(nombre_insumo)
    archivo_esperado = f"{nombre_limpio}.JPG"
    
    if archivo_esperado in _CACHE_FOTOS_STORAGE.get(c_key, set()):
        return get_foto_public_url(catalogo_key, nombre_insumo)
    return None

def optimizar_imagen(ruta_origen: str, max_dimension: int = 800, calidad: int = 85) -> bytes:
    """
    Redimensiona la imagen a un máximo de 800x800 px, convierte fondos transparentes a blanco
    y la comprime en JPEG de alta eficiencia (40KB - 120KB) para optimizar el plan gratuito.
    """
    with Image.open(ruta_origen) as img:
        # Convertir a RGB si tiene canal alfa o es PNG/P
        if img.mode in ("RGBA", "LA", "P"):
            fondo = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                fondo.paste(img, mask=img.split()[3])
            else:
                fondo.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])
            img = fondo
        elif img.mode != "RGB":
            img = img.convert("RGB")
            
        # Redimensionar conservando proporción
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Guardar en memoria como JPEG optimizado progresivo
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=calidad, optimize=True, progressive=True)
        return buf.getvalue()

def guardar_foto_insumo(catalogo_key: str, nombre_insumo: str, ruta_archivo_origen: str) -> tuple[bool, str]:
    """
    Valida, comprime y sube la foto del insumo a Supabase Storage con x-upsert.
    Garantiza 1 sola foto por insumo.
    
    Returns:
        (True, public_url) en éxito.
        (False, mensaje_error) en caso de fallo.
    """
    if not os.path.exists(ruta_archivo_origen):
        return False, "El archivo seleccionado no existe."
        
    _, ext = os.path.splitext(ruta_archivo_origen)
    ext = ext.lower()
    if ext not in FORMATOS_FOTOS_PERMITIDOS:
        return False, f"Formato no permitido ({ext}). Formatos válidos: JPG, PNG, WEBP."
        
    tam_bytes = os.path.getsize(ruta_archivo_origen)
    if tam_bytes > MAX_UPLOAD_BYTES:
        return False, f"La imagen supera el límite de 5 MB ({tam_bytes / (1024*1024):.1f} MB)."
        
    try:
        jpeg_bytes = optimizar_imagen(ruta_archivo_origen)
        base_url = get_supabase_storage_base_url()
        storage_path = get_foto_storage_path(catalogo_key, nombre_insumo)
        upload_url = f"{base_url}/storage/v1/object/{BUCKET_FOTOS}/{storage_path}"
        
        headers = {
            "apikey": Config.SUPABASE_KEY,
            "Authorization": f"Bearer {Config.SUPABASE_KEY}",
            "Content-Type": "image/jpeg",
            "x-upsert": "true"
        }
        
        res = requests.post(upload_url, headers=headers, data=jpeg_bytes, timeout=15)
        if res.status_code in (200, 201):
            public_url = get_foto_public_url(catalogo_key, nombre_insumo)
            nombre_limpio = _normalizar_nombre_archivo(nombre_insumo)
            c_key = catalogo_key.lower()
            if c_key not in _CACHE_FOTOS_STORAGE:
                _CACHE_FOTOS_STORAGE[c_key] = set()
            _CACHE_FOTOS_STORAGE[c_key].add(f"{nombre_limpio}.JPG")
            logger.info(f"Foto subida a Supabase Storage: {storage_path} ({len(jpeg_bytes)/1024:.1f} KB)")
            return True, public_url
        else:
            logger.error(f"Error Storage ({res.status_code}): {res.text}")
            return False, f"Error en servidor Storage ({res.status_code}): {res.text}"
            
    except Exception as ex:
        logger.error(f"Error procesando imagen: {ex}")
        return False, f"Error al procesar la imagen: {ex}"

def eliminar_foto_insumo(catalogo_key: str, nombre_insumo: str) -> bool:
    """Elimina la foto del insumo de Supabase Storage y actualiza el cache en memoria."""
    try:
        base_url = get_supabase_storage_base_url()
        storage_path = get_foto_storage_path(catalogo_key, nombre_insumo)
        delete_url = f"{base_url}/storage/v1/object/{BUCKET_FOTOS}"
        
        headers = {
            "apikey": Config.SUPABASE_KEY,
            "Authorization": f"Bearer {Config.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {"prefixes": [storage_path]}
        res = requests.delete(delete_url, headers=headers, json=payload, timeout=10)
        if res.status_code in (200, 204):
            c_key = catalogo_key.lower()
            nombre_limpio = _normalizar_nombre_archivo(nombre_insumo)
            if c_key in _CACHE_FOTOS_STORAGE:
                _CACHE_FOTOS_STORAGE[c_key].discard(f"{nombre_limpio}.JPG")
            return True
        return False
    except Exception as ex:
        logger.error(f"Error al eliminar foto de Storage: {ex}")
        return False

def buscar_foto_insumo(catalogo_key: str, nombre_insumo: str) -> str | None:
    """
    Retorna la URL pública de Supabase Storage para el insumo de forma instantánea.
    Búsqueda O(1) en memoria: 0 milisegundos, nunca bloquea la interfaz de usuario.
    """
    return comprobar_foto_en_storage(catalogo_key, nombre_insumo)

def listar_fotos_existentes_en_storage(catalogo_key: str = None) -> set[str]:
    """
    Consulta en Supabase Storage la lista de archivos ya subidos.
    Retorna un set con las rutas normalizadas (ej: {'aseo/JABON_REY.JPG', ...}).
    """
    existentes = set()
    base_url = get_supabase_storage_base_url()
    headers = {
        "apikey": Config.SUPABASE_KEY,
        "Authorization": f"Bearer {Config.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    cats = [catalogo_key.lower()] if catalogo_key else [k.lower() for k in CATALOGOS_CONFIG.keys()]
    for c_key in cats:
        try:
            url = f"{base_url}/storage/v1/object/list/{BUCKET_FOTOS}"
            res = requests.post(url, headers=headers, json={"prefix": c_key, "limit": 1000}, timeout=10)
            if res.status_code == 200:
                for obj in res.json():
                    obj_name = obj.get("name", "")
                    if obj_name:
                        existentes.add(f"{c_key}/{obj_name.upper()}")
        except Exception as ex:
            logger.warning(f"Error listando fotos en storage para {c_key}: {ex}")
            
    return existentes

def sincronizar_todas_fotos_a_storage(catalogo_key: str = None, forzar_reemplazo: bool = False, progreso_fn = None) -> dict:
    """
    Migra masivamente todas las imágenes de Desktop a Supabase Storage.
    Comprueba previamente qué fotos ya existen en la nube para omitirlas
    y optimizar drásticamente el tiempo de sincronización.
    """
    resultados = {"subidas": 0, "ya_existentes": 0, "errores": 0, "detalles": []}
    cats = [catalogo_key] if catalogo_key else list(CATALOGOS_CONFIG.keys())
    
    # Obtener el inventario de fotos ya subidas a Supabase
    fotos_en_storage = set()
    if not forzar_reemplazo:
        fotos_en_storage = listar_fotos_existentes_en_storage(catalogo_key)
        logger.info(f"Fotos ya existentes en Supabase Storage: {len(fotos_en_storage)}")

    for c_key in cats:
        cat_folder = c_key.upper()
        carpeta = os.path.join(RUTA_FOTOS_BASE, cat_folder)
        if not os.path.exists(carpeta):
            continue
            
        archivos = [f for f in os.listdir(carpeta) if any(f.lower().endswith(ext) for ext in FORMATOS_FOTOS_PERMITIDOS)]
        total = len(archivos)
        
        for idx, arch in enumerate(archivos):
            nombre_base, _ = os.path.splitext(arch)
            nombre_limpio = _normalizar_nombre_archivo(nombre_base)
            storage_key_check = f"{c_key.lower()}/{nombre_limpio}.JPG"
            
            # Si ya existe en storage y no forzamos reemplazo, omitir
            if not forzar_reemplazo and storage_key_check in fotos_en_storage:
                resultados["ya_existentes"] += 1
                if progreso_fn:
                    progreso_fn(c_key, idx + 1, total, arch)
                continue
                
            ruta_img = os.path.join(carpeta, arch)
            ok, msg = guardar_foto_insumo(c_key, nombre_base, ruta_img)
            if ok:
                resultados["subidas"] += 1
                fotos_en_storage.add(storage_key_check)
            else:
                resultados["errores"] += 1
                resultados["detalles"].append(f"{arch}: {msg}")
                
            if progreso_fn:
                progreso_fn(c_key, idx + 1, total, arch)
                
    return resultados

def get_todos_insumos_inventario() -> list[dict]:
    """Obtiene la lista completa de insumos de Supabase para el selector de añadir."""
    try:
        db = BaseDatabase()
        res = db.get_all("catalogo_insumos?select=codigo_insumo,nombre,descripcion,categoria,precio_venta,costo_unitario,stock_actual&order=nombre.asc")
        return res or []
    except Exception as ex:
        log_error(logger, ex, "Error al obtener catálogo general de insumos")
        return []

def get_items_catalogo(catalogo_key: str) -> list[dict]:
    """Carga los ítems de un catálogo desde assets o JSON en Desktop."""
    cfg = CATALOGOS_CONFIG.get(catalogo_key)
    if not cfg:
        return []

    # 1. Intentar cargar desde assets del proyecto
    json_name = cfg["json_file"]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    asset_path = os.path.join(base_dir, "assets", "catalogos", json_name)
    
    if os.path.exists(asset_path):
        try:
            with open(asset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as ex:
            logger.warning(f"No se pudo leer {asset_path}: {ex}")

    # 2. Fallback a ruta de Desktop
    desktop_json = os.path.join(RUTA_DEFAULT_CATALOGOS, json_name)
    if os.path.exists(desktop_json):
        try:
            with open(desktop_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as ex:
            logger.warning(f"No se pudo leer {desktop_json}: {ex}")

    return []

def get_mapa_catalogos_asignados() -> dict[str, list[str]]:
    """
    Escanea todos los catálogos configurados y retorna un mapa
    {codigo_insumo: ['Aseo', 'Bolsas', ...]} indicando a cuáles catálogos
    ya ha sido asignado cada insumo.
    """
    mapa = {}
    for cat_key, cfg in CATALOGOS_CONFIG.items():
        nom_cat = cfg.get("nombre", cat_key)
        items = get_items_catalogo(cat_key)
        for it in items:
            cod = str(it.get("codigo", "")).strip()
            if cod:
                if cod not in mapa:
                    mapa[cod] = []
                if nom_cat not in mapa[cod]:
                    mapa[cod].append(nom_cat)
    return mapa

def actualizar_insumo_inventario_db(codigo_insumo: str, datos: dict) -> bool:
    """
    Actualiza la información maestro del insumo en Supabase (catalogo_insumos).
    Permite sincronizar nombre, descripcion, costo_unitario y precio_venta.
    """
    if not codigo_insumo or not datos:
        return False
    try:
        db = BaseDatabase()
        endpoint = f"catalogo_insumos?codigo_insumo=eq.{codigo_insumo}"
        res = db.patch(endpoint, json_data=datos)
        if res and res.status_code in (200, 204):
            logger.info(f"Insumo {codigo_insumo} actualizado exitosamente en Supabase: {datos}")
            return True
        return False
    except Exception as ex:
        log_error(logger, ex, f"Error al actualizar insumo {codigo_insumo} en DB")
        return False

def get_datos_inventario_db() -> tuple[dict[str, float], dict[str, float], dict[str, float], set[str]]:
    """
    Obtiene los precios de venta vigentes, costos unitarios, stocks actuales y el conjunto
    de insumos que han tenido compras en el sistema desde Supabase.
    
    Returns:
        (precios_map, costos_map, stocks_map, codigos_comprados_set)
    """
    precios = {}
    costos = {}
    stocks = {}
    comprados = set()

    try:
        db = BaseDatabase()
        # Traer catálogo con precios, costos y stock
        res_cat = db.get_all("catalogo_insumos?select=codigo_insumo,precio_venta,costo_unitario,stock_actual")
        if res_cat:
            for item in res_cat:
                cod = str(item.get("codigo_insumo") or "").strip()
                if cod:
                    try:
                        pv = float(item.get("precio_venta") or 0.0)
                    except (ValueError, TypeError):
                        pv = 0.0
                    try:
                        cu = float(item.get("costo_unitario") or 0.0)
                    except (ValueError, TypeError):
                        cu = 0.0
                    try:
                        st = float(item.get("stock_actual") or 0.0)
                    except (ValueError, TypeError):
                        st = 0.0
                    precios[cod] = pv
                    costos[cod] = cu
                    stocks[cod] = st

        # Traer códigos con compras registradas
        res_comp = db.get_all("registro_compras?select=codigo_insumo&(estado_registro.is.null,estado_registro.neq.ANULADO)")
        if res_comp:
            for c in res_comp:
                cod = str(c.get("codigo_insumo") or "").strip()
                if cod:
                    comprados.add(cod)

    except Exception as ex:
        log_error(logger, ex, "Error al consultar precios y compras para catálogos")

    return precios, costos, stocks, comprados

def formatear_precio(valor: float) -> str:
    """Formatea un número decimal a formato moneda colombiana ($15.500)."""
    try:
        val_int = int(round(valor))
        return f"${val_int:,.0f}".replace(",", ".")
    except Exception:
        return "$0"

# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# MAPEO Y DISTRIBUCIÓN DE PÁGINAS DEL CATÁLOGO
# -------------------------------------------------------------------------
_CACHE_MAPEO_PAGINAS: dict[str, dict] = {}

def _generar_card_html(cod: str, it: dict, precios_map: dict, cfg: dict, catalogo_key: str) -> str:
    """Genera el bloque HTML de una tarjeta de producto (con foto + zoom o diseño editorial sin foto)."""
    nom = str(it.get("nombre", f"Insumo {cod}")).strip()
    desc = str(it.get("descripcion", "") or nom).strip()
    pv = float(it.get("precio_venta", 0.0) or precios_map.get(cod, 0.0))
    pv_fmt = formatear_precio(pv) if pv > 0 else "$0"
    foto_url = buscar_foto_insumo(catalogo_key, nom)

    if catalogo_key == "desechables":
        if foto_url:
            return f'''
            <div class="product-card">
                <div class="photo-box">
                    <img src="{foto_url}" alt="{nom}">
                </div>
                <div class="details-box">
                    <div class="details-top">
                        <span class="code-pill">CÓD: {cod}</span>
                        <h3 class="prod-name">{nom}</h3>
                        <p class="prod-desc">{desc}</p>
                    </div>
                    <div class="price-section">
                        <span class="price-lbl">PRECIO DE VENTA</span>
                        <span class="price-num">{pv_fmt}</span>
                    </div>
                </div>
            </div>'''
        else:
            return f'''
            <div class="product-card no-photo-card">
                <div class="card-main-content">
                    <div class="no-photo-header">
                        <span class="code-pill">CÓD: {cod}</span>
                        <span class="no-photo-badge">✦ INSUMO OFICIAL ✦</span>
                    </div>
                    <div class="no-photo-body">
                        <h3 class="prod-name">{nom}</h3>
                        <div class="no-photo-divider"></div>
                        <p class="prod-desc">{desc}</p>
                        <div class="no-photo-meta">
                            <span class="no-photo-tag">DISTRIBUIDORA DOÑA MARY</span>
                            <span class="no-photo-tag">{cfg.get("nombre", "DESECHABLES").upper()}</span>
                        </div>
                    </div>
                </div>
                <div class="price-section" style="margin-top: 8px;">
                    <span class="price-lbl">PRECIO DE VENTA</span>
                    <span class="price-num">{pv_fmt}</span>
                </div>
            </div>'''

    if foto_url:
        return f'''
        <div class="product-card">
            <div class="card-main-content">
                <div class="photo-box">
                    <img src="{foto_url}" alt="{nom}">
                </div>
                <div class="details-box">
                    <span class="code-pill">CÓD: {cod}</span>
                    <h3 class="prod-name">{nom}</h3>
                    <p class="prod-desc">{desc}</p>
                </div>
            </div>
            <div class="price-ribbon">
                <div class="price-lbl-group">
                    <span class="price-lbl-text">PRECIO DE VENTA</span>
                    <span class="price-tag-badge">🏷</span>
                </div>
                <span class="price-num">{pv_fmt}</span>
            </div>
        </div>'''
    else:
        return f'''
        <div class="product-card no-photo-card">
            <div class="card-main-content">
                <div class="no-photo-header">
                    <span class="code-pill">CÓD: {cod}</span>
                    <span class="no-photo-badge">✦ INSUMO OFICIAL ✦</span>
                </div>
                <div class="no-photo-body">
                    <h3 class="prod-name">{nom}</h3>
                    <div class="no-photo-divider"></div>
                    <p class="prod-desc">{desc}</p>
                    <div class="no-photo-meta">
                        <span class="no-photo-tag">DISTRIBUIDORA DOÑA MARY</span>
                        <span class="no-photo-tag">{cfg.get("nombre", "CATÁLOGO").upper()}</span>
                    </div>
                </div>
            </div>
            <div class="price-ribbon">
                <div class="price-lbl-group">
                    <span class="price-lbl-text">PRECIO DE VENTA</span>
                    <span class="price-tag-badge">🏷</span>
                </div>
                <span class="price-num">{pv_fmt}</span>
            </div>
        </div>'''


def obtener_mapeo_paginas_catalogo(catalogo_key: str, forzar_recarga: bool = False, items_data: list[dict] = None) -> dict:
    """
    Analiza la plantilla HTML del catálogo comercial y extrae con precisión quirúrgica
    el número total de páginas físicas y la distribución exacta de qué insumos pertenecen
    a cada página (cuadrícula de productos y tablas resumen estandarizadas a 30 ítems/pág),
    garantizando que no existan insumos duplicados dentro del mismo catálogo y respetando
    las asignaciones de slots y páginas específicas.
    """
    global _CACHE_MAPEO_PAGINAS
    if not forzar_recarga and items_data is None and catalogo_key in _CACHE_MAPEO_PAGINAS:
        return _CACHE_MAPEO_PAGINAS[catalogo_key]

    cfg = CATALOGOS_CONFIG.get(catalogo_key)
    if not cfg:
        return {"total_paginas": 0, "paginas": [], "mapa_codigo_a_pagina": {}}

    html_name = cfg["archivo_html"]
    html_origen = os.path.join(RUTA_DEFAULT_CATALOGOS, html_name)

    if not os.path.exists(html_origen):
        ruta_alt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "catalogos", html_name)
        if os.path.exists(ruta_alt):
            html_origen = ruta_alt
        else:
            return {"total_paginas": 0, "paginas": [], "mapa_codigo_a_pagina": {}}

    if items_data is None:
        items_data = get_items_catalogo(catalogo_key)

    # 0. Deduplicación estricta por código (un insumo solo puede existir 1 vez en el mismo catálogo)
    seen_codes = set()
    dedup_items = []
    for it in items_data:
        c = str(it.get("codigo", "")).strip()
        if c and c not in seen_codes:
            seen_codes.add(c)
            dedup_items.append(it)
    items_data = dedup_items

    active_items_map = {str(it.get("codigo", "")).strip(): it for it in items_data if str(it.get("codigo", "")).strip()}
    active_codes = set(active_items_map.keys())

    try:
        with open(html_origen, "r", encoding="utf-8", errors="ignore") as f:
            contenido_html = f.read()

        page_chunks = re.split(r'<div\s+class=["\']page(?:\s+[^"\']*)?["\']', contenido_html)
        paginas_info = []
        mapa_codigo = {}
        assigned_codes = set()

        # Extraer estructura de chunks de plantilla (excluyendo tablas viejas)
        template_grid_chunks = []
        for idx, chunk in enumerate(page_chunks[1:], start=1):
            is_orig_table = "td-code-cell" in chunk or "catalog-table" in chunk
            if is_orig_table:
                continue

            orig_codes = []
            for m in re.finditer(r'class="code-pill"[^>]*>(?:CÓD:|COD:|C\?D:)?\s*([A-Za-z0-9_-]+)', chunk):
                c = m.group(1).strip()
                if c not in orig_codes:
                    orig_codes.append(c)
            if not orig_codes:
                for m in re.finditer(r'class="card-code"[^>]*>\s*([A-Za-z0-9_-]+)', chunk):
                    c = m.group(1).strip()
                    if c not in orig_codes:
                        orig_codes.append(c)

            is_cover = idx == 1 or "cover-page" in chunk[:300]
            is_grid = len(orig_codes) > 0 or ("products-grid" in chunk)
            is_back = (idx == len(page_chunks) - 1) and not is_grid

            header_snippet = chunk[:4000]
            sub_m = (re.search(r'class="header-category-subtitle"[^>]*>([^<]+)', header_snippet) or
                     re.search(r'class="header-badge"[^>]*>([^<]+)', header_snippet))
            title_m = (re.search(r'class="header-family-title"[^>]*>([^<]+)', header_snippet) or
                       re.search(r'class="header-title-text"[^>]*>([^<]+)', header_snippet))
            sub = sub_m.group(1).strip() if sub_m else ""
            title = title_m.group(1).strip() if title_m else ""
            title = re.sub(r'[✦★◆■●*]+', '', title).strip()
            sub = re.sub(r'[✦★◆■●*]+', '', sub).strip()

            tipo = "Portada" if is_cover and not is_grid else "Rejilla de Productos" if is_grid else "Contraportada" if is_back else "Separador de Sección"
            template_grid_chunks.append({
                "chunk_idx": idx,
                "orig_codes": orig_codes,
                "tipo": tipo,
                "categoria": sub or cfg["nombre"],
                "familia": title or f"Página {len(template_grid_chunks) + 1}",
                "is_cover": is_cover,
                "is_grid": is_grid,
                "is_back": is_back
            })

        # 1. Asignar ítems a las páginas de la plantilla
        for p_tmpl in template_grid_chunks:
            if p_tmpl["tipo"] in ("Portada", "Contraportada", "Separador de Sección"):
                p_data = {
                    "num_pagina": len(paginas_info) + 1,
                    "tipo": p_tmpl["tipo"],
                    "categoria": p_tmpl["categoria"],
                    "familia": p_tmpl["familia"],
                    "items_cards": [],
                    "items_tablas": [],
                    "total_items": 0
                }
                paginas_info.append(p_data)
                continue

            card_items = []
            cur_pnum = len(paginas_info) + 1

            # A. Ítems con asignación explícita a esta página
            for it in items_data:
                c = str(it.get("codigo", "")).strip()
                if c in active_codes and c not in assigned_codes:
                    it_pag = it.get("pagina")
                    if it_pag is not None and (it_pag == cur_pnum or it_pag == p_tmpl["chunk_idx"]):
                        if len(card_items) < 4:
                            card_items.append(c)
                            assigned_codes.add(c)

            # B. Ítems que originalmente estaban en este chunk y aún no tienen página asignada
            for c in p_tmpl["orig_codes"]:
                if c in active_codes and c not in assigned_codes and len(card_items) < 4:
                    it = active_items_map[c]
                    it_pag = it.get("pagina")
                    if it_pag is None or it_pag == cur_pnum or it_pag == p_tmpl["chunk_idx"]:
                        card_items.append(c)
                        assigned_codes.add(c)

            if not card_items:
                continue

            fam_page = p_tmpl["familia"]
            cat_page = p_tmpl["categoria"]
            if card_items and card_items[0] in active_items_map:
                custom_f = active_items_map[card_items[0]].get("familia", "")
                if custom_f and not custom_f.startswith("✦") and custom_f.upper() != "GENERAL":
                    fam_page = custom_f
                custom_c = active_items_map[card_items[0]].get("categoria", "")
                if custom_c and custom_c.upper() != "GENERAL":
                    cat_page = custom_c

            p_data = {
                "num_pagina": cur_pnum,
                "tipo": "Rejilla de Productos",
                "categoria": cat_page,
                "familia": fam_page,
                "items_cards": card_items,
                "items_tablas": [],
                "total_items": len(card_items)
            }
            paginas_info.append(p_data)
            for c in card_items:
                mapa_codigo[c] = {
                    "num_pagina": cur_pnum,
                    "tipo": "Rejilla",
                    "categoria": cat_page,
                    "familia": fam_page
                }

        # 2. Insumos restantes por asignar (con página explícita o nuevos sin asignar)
        insumos_restantes = [c for c in active_codes if c not in assigned_codes]
        if insumos_restantes:
            grupos_por_pag = {}
            sin_pag_expl = []
            for c in insumos_restantes:
                it = active_items_map[c]
                p_exp = it.get("pagina")
                if p_exp and isinstance(p_exp, int) and p_exp > len(paginas_info):
                    grupos_por_pag.setdefault(p_exp, []).append(c)
                else:
                    sin_pag_expl.append(c)

            # Crear páginas explícitas
            for p_exp in sorted(grupos_por_pag.keys()):
                chunk_c = grupos_por_pag[p_exp][:4]
                p_num_nueva = len(paginas_info) + 1
                fam_label = f"Novedades & Adicionales ({p_num_nueva})"
                if chunk_c and chunk_c[0] in active_items_map:
                    custom_f = active_items_map[chunk_c[0]].get("familia", "")
                    if custom_f and not custom_f.startswith("✦"):
                        fam_label = custom_f
                p_nueva = {
                    "num_pagina": p_num_nueva,
                    "tipo": "Rejilla de Productos",
                    "categoria": cfg["nombre"],
                    "familia": fam_label,
                    "items_cards": chunk_c,
                    "items_tablas": [],
                    "total_items": len(chunk_c)
                }
                paginas_info.append(p_nueva)
                for c in chunk_c:
                    assigned_codes.add(c)
                    mapa_codigo[c] = {
                        "num_pagina": p_num_nueva,
                        "tipo": "Rejilla",
                        "categoria": cfg["nombre"],
                        "familia": fam_label
                    }

            # Para los que no tienen página explícita, chunkear en páginas de hasta 4
            sin_asignar_final = [c for c in sin_pag_expl if c not in assigned_codes]
            if sin_asignar_final:
                chunks_nuevos = [sin_asignar_final[i:i+4] for i in range(0, len(sin_asignar_final), 4)]
                for ch_idx, chunk_cods in enumerate(chunks_nuevos, start=1):
                    p_num_nueva = len(paginas_info) + 1
                    fam_label = f"Novedades & Adicionales ({ch_idx})"
                    if chunk_cods and chunk_cods[0] in active_items_map:
                        custom_fam = active_items_map[chunk_cods[0]].get("familia", "")
                        if custom_fam and not custom_fam.startswith("✦"):
                            fam_label = custom_fam
                    p_nueva = {
                        "num_pagina": p_num_nueva,
                        "tipo": "Rejilla de Productos",
                        "categoria": cfg["nombre"],
                        "familia": fam_label,
                        "items_cards": chunk_cods,
                        "items_tablas": [],
                        "total_items": len(chunk_cods)
                    }
                    paginas_info.append(p_nueva)
                    for c in chunk_cods:
                        assigned_codes.add(c)
                        mapa_codigo[c] = {
                            "num_pagina": p_num_nueva,
                            "tipo": "Rejilla",
                            "categoria": cfg["nombre"],
                            "familia": fam_label
                        }

        # 3. Generar páginas de tablas estandarizadas con exactamente 30 insumos por página
        cods_ordenados = []
        for p in paginas_info:
            for c in p.get("items_cards", []):
                if c not in cods_ordenados:
                    cods_ordenados.append(c)
        for c in active_codes:
            if c not in cods_ordenados:
                cods_ordenados.append(c)

        if cods_ordenados:
            table_chunks = [cods_ordenados[i:i+30] for i in range(0, len(cods_ordenados), 30)]
            for t_idx, t_cods in enumerate(table_chunks, start=1):
                p_num_tabla = len(paginas_info) + 1
                p_tabla = {
                    "num_pagina": p_num_tabla,
                    "tipo": "Tabla Resumen",
                    "categoria": cfg["nombre"],
                    "familia": f"LISTADO OFICIAL MAESTRO ({t_idx})",
                    "items_cards": [],
                    "items_tablas": t_cods,
                    "total_items": len(t_cods)
                }
                paginas_info.append(p_tabla)
                for c in t_cods:
                    if c not in mapa_codigo:
                        mapa_codigo[c] = {
                            "num_pagina": p_num_tabla,
                            "tipo": "Tabla Resumen",
                            "categoria": cfg["nombre"],
                            "familia": f"LISTADO OFICIAL MAESTRO ({t_idx})"
                        }

        resultado = {
            "total_paginas": len(paginas_info),
            "paginas": paginas_info,
            "mapa_codigo_a_pagina": mapa_codigo
        }
        if items_data is None:
            _CACHE_MAPEO_PAGINAS[catalogo_key] = resultado
        return resultado

    except Exception as ex:
        logger.error(f"Error al mapear páginas de {catalogo_key}: {ex}")
        return {"total_paginas": 0, "paginas": [], "mapa_codigo_a_pagina": {}}


# -------------------------------------------------------------------------
# GENERACIÓN DINÁMICA DE HTML ACTUALIZADO (PRECIOS, NOMBRES, DESCRIPCIONES, FOTOS, ALTAS Y BAJAS)
# -------------------------------------------------------------------------
def generar_html_catalogo_actualizado(catalogo_key: str, precios_map: dict[str, float] = None, items_data: list[dict] = None) -> tuple[bool, str]:
    """
    Lee la plantilla HTML del catálogo e inyecta en vivo todas las modificaciones vigentes:
    - Retira productos eliminados del catálogo (remueve tarjetas).
    - Mantiene intacta la estructura de páginas sin robar espacios de páginas anteriores.
    - Añade nuevas páginas con logo de la empresa para productos adicionales.
    - Estandariza las páginas de tablas a exactamente 30 insumos por página.
    - Aplica zoom óptico (1.22x) para eliminar bordes blancos en fotos.
    - Renumera automáticamente todas las páginas del PDF.
    """
    cfg = CATALOGOS_CONFIG.get(catalogo_key)
    if not cfg:
        return False, f"Catálogo desconocido: {catalogo_key}"

    html_name = cfg["archivo_html"]
    html_origen = os.path.join(RUTA_DEFAULT_CATALOGOS, html_name)

    if not os.path.exists(html_origen):
        ruta_alt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "catalogos", html_name)
        if os.path.exists(ruta_alt):
            html_origen = ruta_alt
        else:
            return False, f"No se encontró el archivo plantilla del catálogo en: {html_origen}"

    if precios_map is None:
        precios_map, _, _, _ = get_datos_inventario_db()

    if items_data is None:
        items_data = get_items_catalogo(catalogo_key)

    precargar_cache_fotos_storage(catalogo_key)

    active_items_map = {str(it.get("codigo", "")).strip(): it for it in items_data if str(it.get("codigo", "")).strip()}

    try:
        with open(html_origen, "r", encoding="utf-8", errors="ignore") as f:
            contenido_html = f.read()

        # Inyectar CSS de Zoom Óptico, Control de Logos y Diseño Editorial para Cards sin foto
        css_zoom = """
        /* REGLA CRÍTICA UNIVERSAL: CONTROL DE TAMAÑO DE LOGOS EN CABECERA */
        .page-header img,
        .header-logo-img,
        .header-logo-circle img {
            max-height: 44px !important;
            max-width: 140px !important;
            width: auto !important;
            height: auto !important;
            object-fit: contain !important;
            display: block !important;
        }
        .header-logo-circle {
            width: 54px !important;
            height: 54px !important;
            border-radius: 50% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
            overflow: hidden !important;
        }

        /* ZOOM ÓPTICO DINÁMICO DE PRODUCTOS CON FOTO */
        .photo-box {
            overflow: hidden !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: #ffffff !important;
        }
        .photo-box img {
            transform: scale(1.22) !important;
            transform-origin: center center !important;
            object-fit: contain !important;
            max-width: 100% !important;
            max-height: 100% !important;
        }

        /* DISEÑO EDITORIAL ELEGANTE PARA CARDS SIN FOTO */
        .product-card.no-photo-card {
            background: linear-gradient(160deg, #ffffff 0%, #f8fafc 100%) !important;
            border: 1.5px solid #cbd5e1 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            position: relative !important;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12) !important;
            box-sizing: border-box !important;
        }
        .product-card.no-photo-card .card-main-content {
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
            padding: 4px 2px 0 2px !important;
            flex: 1 !important;
            overflow: hidden !important;
        }
        .product-card.no-photo-card .no-photo-header {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            width: 100% !important;
            margin-bottom: 2px !important;
        }
        .product-card.no-photo-card .no-photo-badge {
            font-size: 7pt !important;
            font-weight: 800 !important;
            color: #64748b !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
        }
        .product-card.no-photo-card .no-photo-body {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
            padding: 16px 14px !important;
            flex: 1 !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.015) !important;
        }
        .product-card.no-photo-card .prod-name {
            font-size: 11.5pt !important;
            font-weight: 800 !important;
            color: #0f172a !important;
            line-height: 1.3 !important;
            margin-bottom: 8px !important;
            text-transform: uppercase !important;
            display: -webkit-box !important;
            -webkit-line-clamp: 3 !important;
            -webkit-box-orient: vertical !important;
            overflow: hidden !important;
        }
        .product-card.no-photo-card .no-photo-divider {
            width: 38px !important;
            height: 3px !important;
            background: #00509d !important;
            border-radius: 2px !important;
            margin-bottom: 10px !important;
        }
        .product-card.no-photo-card .prod-desc {
            font-size: 9pt !important;
            color: #475569 !important;
            line-height: 1.5 !important;
            display: -webkit-box !important;
            -webkit-line-clamp: 7 !important;
            -webkit-box-orient: vertical !important;
            overflow: hidden !important;
            flex: 1 !important;
        }
        .product-card.no-photo-card .no-photo-meta {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 6px !important;
            margin-top: auto !important;
            padding-top: 8px !important;
        }
        .product-card.no-photo-card .no-photo-tag {
            background: #f1f5f9 !important;
            color: #475569 !important;
            font-size: 7.2pt !important;
            font-weight: 700 !important;
            padding: 3px 8px !important;
            border-radius: 6px !important;
            border: 1px solid #e2e8f0 !important;
            letter-spacing: 0.3px !important;
        }
        """
        if "</style>" in contenido_html:
            contenido_html = contenido_html.replace("</style>", f"{css_zoom}\n</style>", 1)
        elif "</head>" in contenido_html:
            contenido_html = contenido_html.replace("</head>", f"<style>{css_zoom}</style>\n</head>", 1)

        # Extraer logo oficial de la empresa desde la plantilla
        m_logo = (re.search(r'class="header-logo[^"]*"[^>]*src="([^"]+)"', contenido_html) or
                  re.search(r'class="header-logo[^"]*"[\s\S]*?<img\s+src="([^"]+)"', contenido_html) or
                  re.search(r'<div class="header-logo-circle">\s*<img\s+src="([^"]+)"', contenido_html) or
                  re.search(r'class="cover-logo-wrapper"[\s\S]*?<img\s+src="([^"]+)"', contenido_html))
        logo_src = m_logo.group(1) if m_logo else ""

        # Obtener mapeo dinámico de páginas actualizado
        mapeo = obtener_mapeo_paginas_catalogo(catalogo_key, forzar_recarga=True, items_data=items_data)
        paginas_mapeo = mapeo.get("paginas", [])

        # Extraer portada y contraportada originales de la plantilla
        page_chunks = re.split(r'(<div\s+class=["\']page(?:\s+[^"\']*)?["\'])', contenido_html)
        portada_body = None
        portada_open_tag = '<div class="page cover-page">'
        contraportada_body = None
        contraportada_open_tag = '<div class="page">'

        for i in range(1, len(page_chunks), 2):
            ot = page_chunks[i]
            pb = page_chunks[i+1] if (i+1) < len(page_chunks) else ""
            if (i == 1) or ("cover-page" in pb[:400]):
                portada_open_tag = ot
                portada_body = pb
            elif (i >= len(page_chunks) - 2) and ("product-card" not in pb) and ("catalog-table" not in pb) and ("td-code-cell" not in pb):
                contraportada_open_tag = ot
                contraportada_body = pb

        processed_pages = []
        logo_img_tag = f'<img class="header-logo-img" src="{logo_src}" alt="Logo Doña Mary">' if logo_src else '<div style="font-weight:bold;color:#00509d;font-size:11px;">DM</div>'

        for p_info in paginas_mapeo:
            tipo = p_info.get("tipo", "")

            if tipo == "Portada" and portada_body:
                processed_pages.append((portada_open_tag, portada_body))
            elif tipo == "Contraportada" and contraportada_body:
                processed_pages.append((contraportada_open_tag, contraportada_body))
            elif tipo == "Rejilla de Productos":
                cards_cods = p_info.get("items_cards", [])
                if not cards_cods:
                    continue
                cards_html = []
                for c in cards_cods:
                    it = active_items_map.get(c, {"codigo": c, "nombre": f"Insumo {c}"})
                    cards_html.append(_generar_card_html(c, it, precios_map, cfg, catalogo_key))
                
                grid_content = "\n".join(cards_html)
                fam_titulo = p_info.get("familia", f"Rejilla {p_info.get('num_pagina', '')}")
                fam_clean = re.sub(r'[✦★◆■●*]+', '', fam_titulo).strip() or cfg.get("nombre", "General")
                cat_sub = p_info.get("categoria", cfg.get("subtitulo", "CATÁLOGO OFICIAL"))

                if catalogo_key == "desechables":
                    header_content = f'''
                    <div class="page-header">
                        <img class="header-logo-img" src="{logo_src}" alt="Logo Doña Mary">
                        <div class="header-info-box">
                            <span class="header-badge">{cat_sub}</span>
                            <div class="header-title-text">✦ {fam_clean.upper()} ✦</div>
                        </div>
                    </div>'''
                else:
                    header_content = f'''
                    <div class="page-header">
                        <div class="header-logo-circle">
                            {logo_img_tag}
                        </div>
                        <div class="header-banner-capsule">
                            <span class="header-category-subtitle">{cat_sub}</span>
                            <div class="header-family-title">✦ {fam_clean.upper()} ✦</div>
                        </div>
                    </div>'''

                nueva_pag_body = f'''
                    <div class="page-pattern-layer"></div>
                    {header_content}
                    <div class="page-body">
                        <div class="products-grid">
                            {grid_content}
                        </div>
                    </div>
                    <div class="page-footer">
                        <span class="legal-note">Los precios de nuestros productos son IVA incluido y están sujetos a cambios sin previo aviso</span>
                        <div class="footer-center-badges"><div class="footer-check-icon">✓</div></div>
                        <span class="page-number">Página {p_info.get("num_pagina", "")}</span>
                    </div>
                </div>'''
                processed_pages.append(('<div class="page">', nueva_pag_body))

            elif tipo == "Tabla Resumen":
                tablas_cods = p_info.get("items_tablas", [])
                if not tablas_cods:
                    continue
                rows_html = []
                for c in tablas_cods:
                    it = active_items_map.get(c, {"codigo": c, "nombre": f"Insumo {c}"})
                    nom = it.get("nombre", f"Insumo {c}")
                    fam = it.get("familia", cfg.get("nombre", "General"))
                    fam_clean = re.sub(r'[✦★◆■●*]+', '', fam).strip() or cfg.get("nombre", "General")
                    pv = float(it.get("precio_venta", 0.0) or precios_map.get(c, 0.0))
                    pv_fmt = formatear_precio(pv) if pv > 0 else "$0"
                    rows_html.append(f'<tr><td class="td-code-cell">{c}</td><td class="td-name-cell">{nom}</td><td class="td-fam-cell">{fam_clean}</td><td class="td-price-cell">{pv_fmt}</td></tr>')

                tbody_content = "\n".join(rows_html)
                fam_label = p_info.get("familia", "LISTADO OFICIAL MAESTRO")
                
                if catalogo_key == "desechables":
                    table_header_content = f'''
                    <div class="page-header">
                        <img class="header-logo-img" src="{logo_src}" alt="Logo Doña Mary">
                        <div class="header-info-box">
                            <span class="header-badge">{cfg.get("subtitulo", "CATÁLOGO OFICIAL")}</span>
                            <div class="header-title-text">✦ {fam_label.upper()} ✦</div>
                        </div>
                    </div>'''
                else:
                    table_header_content = f'''
                    <div class="page-header">
                        <div class="header-logo-circle">
                            {logo_img_tag}
                        </div>
                        <div class="header-banner-capsule">
                            <span class="header-category-subtitle">{cfg.get("subtitulo", "CATÁLOGO OFICIAL")}</span>
                            <div class="header-family-title">✦ {fam_label.upper()} ✦</div>
                        </div>
                    </div>'''

                tabla_pag_body = f'''
                    <div class="page-pattern-layer"></div>
                    {table_header_content}
                    <div class="table-page-body">
                        <div class="table-header-box">
                            <h2>Lista Completa de Insumos de {cfg.get("nombre", "Catálogo")}</h2>
                            <p>Consulte a continuación la totalidad de insumos registrados en inventario con su código oficial y precio de venta.</p>
                        </div>
                        <div class="table-container">
                            <table class="catalog-table">
                               <thead>
                                    <tr>
                                        <th style="width: 60px;">Cód.</th>
                                        <th>Descripción del Insumo</th>
                                        <th>Línea / Familia</th>
                                        <th class="th-right">Precio Unit.</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {tbody_content}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="page-footer">
                        <span class="legal-note">Los precios de nuestros productos son IVA incluido y están sujetos a cambios sin previo aviso</span>
                        <div class="footer-center-badges"><div class="footer-check-icon">✓</div></div>
                        <span class="page-number">Página {p_info.get("num_pagina", "")}</span>
                    </div>
                </div>'''
                processed_pages.append(('<div class="page table-page">', tabla_pag_body))

        # 4. Re-enumerar páginas limpiamente en los footers
        total_valid = len(processed_pages)
        final_output = [page_chunks[0]]
        for num_p, (ot, pb) in enumerate(processed_pages, start=1):
            pb = re.sub(r'(class="page-number">)([^<]+)(</span>)', rf'\g<1>Página {num_p} de {total_valid}\g<3>', pb)
            final_output.append(ot + pb)

        contenido_actualizado = "".join(final_output)

        # 5. Guardar archivo temporal enriquecido
        temp_html = os.path.join(tempfile.gettempdir(), f"preview_{cfg['key']}_{os.getpid()}.html")
        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(contenido_actualizado)

        return True, temp_html

    except Exception as ex:
        logger.error(f"Error al procesar plantilla HTML para {catalogo_key}: {ex}")
        return False, f"Error al procesar plantilla HTML: {ex}"


# -------------------------------------------------------------------------
# EXPORTACIÓN A PDF VECTORIAL HEADLESS
# -------------------------------------------------------------------------
def exportar_catalogo_pdf(catalogo_key: str, ruta_salida_pdf: str, precios_map: dict[str, float] = None, items_data: list[dict] = None) -> tuple[bool, str]:
    """
    Genera el PDF vectorial de alta resolución compilando el HTML dinámicamente actualizado
    a través del motor headless de Microsoft Edge o Google Chrome.
    """
    ok_html, res_html = generar_html_catalogo_actualizado(catalogo_key, precios_map, items_data)
    if not ok_html:
        return False, res_html

    temp_html = res_html

    # Localizar navegador headless (Edge o Chrome)
    navegador = None
    candidatos = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    for c in candidatos:
        if os.path.exists(c):
            navegador = c
            break

    if not navegador:
        try:
            os.remove(temp_html)
        except Exception:
            pass
        return False, "No se encontró Microsoft Edge o Chrome en el sistema para compilar a PDF."

    # Ejecutar compilación a PDF
    try:
        dir_salida = os.path.dirname(os.path.abspath(ruta_salida_pdf))
        os.makedirs(dir_salida, exist_ok=True)

        cmd = [
            navegador,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--disable-extensions",
            "--no-sandbox",
            f"--print-to-pdf={os.path.abspath(ruta_salida_pdf)}",
            f"file:///{os.path.abspath(temp_html).replace(chr(92), '/')}"
        ]

        logger.info(f"Generando PDF con comando: {' '.join(cmd[:4])} ...")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)

        if os.path.exists(ruta_salida_pdf) and os.path.getsize(ruta_salida_pdf) > 0:
            logger.info(f"PDF generado exitosamente ({os.path.getsize(ruta_salida_pdf):,} bytes): {ruta_salida_pdf}")
            return True, ruta_salida_pdf
        else:
            err = proc.stderr.decode("utf-8", errors="ignore")
            return False, f"El proceso terminó sin generar archivo: {err}"

    except subprocess.TimeoutExpired:
        return False, "La generación del PDF tomó demasiado tiempo y fue cancelada."
    except Exception as ex:
        return False, f"Fallo al invocar el compilador PDF: {ex}"
    finally:
        if os.path.exists(temp_html):
            try:
                os.remove(temp_html)
            except Exception:
                pass
