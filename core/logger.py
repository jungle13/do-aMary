"""
Módulo centralizado de logging y diagnóstico de errores para Sistema Doña Mary.
Proporciona trazabilidad completa en consola y archivo de log para facilitar la depuración.
"""
import logging
import os
import sys
import traceback
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Configurar logger principal
logger = logging.getLogger("DonaMaryApp")
logger.setLevel(logging.INFO)

# Formato claro y legible
formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(module)s:%(lineno)d]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Handler de consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Handler de archivo
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def get_logger(name: str = "DonaMaryApp") -> logging.Logger:
    """Retorna un logger con el nombre especificado que hereda la configuración base."""
    return logging.getLogger(f"DonaMaryApp.{name}")

def _enviar_error_remoto_bg(context: str, tipo_error: str, mensaje: str, tb: str, extra_info: dict | None):
    """Envía el registro del error a Supabase en segundo plano sin bloquear la aplicación."""
    try:
        from core.database import BaseDatabase
        usuario = "admin"
        try:
            from core.audit_logger import get_current_user_name
            usuario = get_current_user_name() or "admin"
        except Exception:
            pass
        
        db = BaseDatabase()
        payload = {
            "modulo": str(context)[:100],
            "tipo_error": str(tipo_error)[:100],
            "mensaje_error": str(mensaje)[:500],
            "traceback": str(tb)[:4000],
            "usuario": str(usuario)[:50],
            "datos_adicionales": extra_info or {}
        }
        db.post("registro_errores_sistema", json_data=payload, timeout=5)
    except Exception:
        # Fallo silencioso si no hay internet o si la base de datos no está disponible
        pass

def log_error(context: str, error: Exception, extra_info: dict | None = None) -> str:
    """
    Registra un error detallado con traceback completo y contexto en consola,
    en archivo local app.log y en la base de datos Supabase para telemetría en producción.
    Retorna un mensaje legible para mostrar al usuario.
    """
    tb = traceback.format_exc()
    tipo_error = type(error).__name__
    mensaje = str(error)
    info_str = f" | Contexto extra: {extra_info}" if extra_info else ""
    logger.error(f"Error en [{context}]: {mensaje}{info_str}\nTraceback:\n{tb}")
    
    # Enviar a Supabase en hilo secundario daemon
    import threading
    threading.Thread(
        target=_enviar_error_remoto_bg,
        args=(context, tipo_error, mensaje, tb, extra_info),
        daemon=True
    ).start()
    
    # Mensaje amigable para la UI
    return f"Ocurrió un error en [{context}]: {mensaje}"
