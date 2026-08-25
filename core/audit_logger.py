"""
Módulo de Auditoría y Registro de Acciones de Usuario para Doña Mary App.
Registra: fecha, hora, nombre_usuario y acción realizada en cada módulo.
Mantiene persistencia en logs/auditoria_acciones.jsonl y en memoria para consultas rápidas.
"""
import os
import json
import datetime
import threading
from core.logger import get_logger, log_error

logger = get_logger("AuditLogger")

# Almacén de usuario actual en sesión
_CURRENT_USER = {"usuario": "admin", "nombre": "Administrador", "rol": "ADMINISTRADOR"}
_LOCK = threading.Lock()
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "auditoria_acciones.jsonl")

def set_current_user(usuario_data: dict):
    global _CURRENT_USER
    with _LOCK:
        if usuario_data:
            _CURRENT_USER = {
                "usuario": usuario_data.get("usuario") or usuario_data.get("username") or "admin",
                "nombre": usuario_data.get("nombre") or usuario_data.get("usuario") or "Usuario",
                "rol": usuario_data.get("rol") or "OPERADOR"
            }

def get_current_user_name() -> str:
    with _LOCK:
        return _CURRENT_USER.get("usuario", "admin")

def registrar_accion(accion: str, modulo: str = "GENERAL", usuario: str = None, detalles: dict = None):
    """
    Registra una acción de usuario en el historial de auditoría.
    
    Args:
        accion: Descripción clara de la acción realizada (ej: 'Registro manual de compra #FAC-123')
        modulo: Módulo del sistema (COMPRAS, VENTAS, AJUSTES, CONTEO, INVENTARIO)
        usuario: Nombre del usuario (opcional, si es None toma el usuario en sesión activa)
        detalles: Diccionario opcional con metadatos extra
    """
    def _worker():
        try:
            from core.fecha_utils import get_ahora_local
            ahora = get_ahora_local()
            fecha_str = ahora.strftime("%Y-%m-%d")
            hora_str = ahora.strftime("%H:%M:%S")
            
            user_final = usuario or get_current_user_name()
            
            registro = {
                "fecha": fecha_str,
                "hora": hora_str,
                "timestamp": ahora.isoformat(),
                "nombre_usuario": user_final,
                "modulo": modulo.upper(),
                "accion": accion,
                "detalles": detalles or {}
            }
            
            # Asegurar directorio de logs
            os.makedirs(_LOG_DIR, exist_ok=True)
            
            # Escribir en archivo JSON Lines (respaldo local garantizado)
            with _LOCK:
                with open(_LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(registro, ensure_ascii=False) + "\n")
            
            # Sincronizar en Supabase si la tabla historial_acciones_usuario está creada
            try:
                from core.supabase_client import get_client
                db = get_client()
                db._db.post("historial_acciones_usuario", json_data=[registro], timeout=4)
            except Exception:
                pass

            logger.info(f"[AUDITORIA] [{fecha_str} {hora_str}] [{user_final}] [{modulo}] {accion}")
        except Exception as ex:
            log_error("AuditLogger.registrar_accion", ex)

    threading.Thread(target=_worker, daemon=True).start()

def obtener_historial_acciones(limit: int = 100, modulo: str = None, fecha: str = None, usuario: str = None) -> list:
    """
    Lee las últimas acciones registradas. Intenta primero desde Supabase y si no, desde el respaldo local.
    """
    # 1. Intentar consultar desde Supabase
    try:
        from core.supabase_client import get_client
        db = get_client()
        endpoint = f"historial_acciones_usuario?order=timestamp.desc&limit={limit}"
        if modulo and modulo.upper() != "TODOS":
            endpoint += f"&modulo=eq.{modulo.upper()}"
        if fecha:
            endpoint += f"&fecha=eq.{fecha}"
        if usuario:
            endpoint += f"&nombre_usuario=ilike.*{usuario}*"
        res = db._db.get(endpoint, timeout=5)
        if res and res.status_code == 200 and isinstance(res.json(), list) and len(res.json()) > 0:
            return res.json()
    except Exception:
        pass

    # 2. Respaldo local desde archivo JSON Lines
    if not os.path.exists(_LOG_FILE):
        return []
    
    registros = []
    try:
        with _LOCK:
            with open(_LOG_FILE, "r", encoding="utf-8") as f:
                lineas = f.readlines()
                
        for line in reversed(lineas):
            if not line.strip():
                continue
            try:
                item = json.loads(line.strip())
                if modulo and modulo.upper() != "TODOS" and item.get("modulo") != modulo.upper():
                    continue
                if fecha and item.get("fecha") != fecha:
                    continue
                if usuario and usuario.lower() not in item.get("nombre_usuario", "").lower():
                    continue
                registros.append(item)
                if len(registros) >= limit:
                    break
            except json.JSONDecodeError:
                continue
    except Exception as ex:
        log_error("AuditLogger.obtener_historial_acciones", ex)
        
    return registros
