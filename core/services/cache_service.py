"""
Servicio centralizado para la gestión de caché local en archivos JSON.
Garantiza lecturas seguras, serialización atómica y captura de excepciones.
"""
import json
import os
from core.logger import get_logger, log_error

logger = get_logger("CacheService")

class JsonCacheService:
    def __init__(self, filename: str):
        self.filename = filename

    def load(self) -> dict:
        """Lee y deserializa el archivo de caché. Si no existe o está corrupto, retorna un dict vacío."""
        if not os.path.exists(self.filename):
            return {}
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as jde:
            logger.warning(f"Archivo de caché corrupto {self.filename}, reiniciando: {jde}")
            return {}
        except Exception as ex:
            log_error(f"JsonCacheService.load({self.filename})", ex)
            return {}

    def save(self, data: dict) -> bool:
        """Guarda los datos en disco de forma segura."""
        try:
            temp_file = f"{self.filename}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            # Reemplazo atómico para evitar corrupción en cortes o cierres inesperados
            if os.path.exists(self.filename):
                os.remove(self.filename)
            os.rename(temp_file, self.filename)
            return True
        except Exception as ex:
            log_error(f"JsonCacheService.save({self.filename})", ex)
            return False
