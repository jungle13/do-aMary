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

def log_error(context: str, error: Exception, extra_info: dict | None = None) -> str:
    """
    Registra un error detallado con traceback completo y contexto.
    Retorna un mensaje legible para mostrar al usuario.
    """
    tb = traceback.format_exc()
    info_str = f" | Contexto extra: {extra_info}" if extra_info else ""
    logger.error(f"Error en [{context}]: {str(error)}{info_str}\nTraceback:\n{tb}")
    
    # Mensaje amigable para la UI
    return f"Ocurrió un error en [{context}]: {str(error)}"
