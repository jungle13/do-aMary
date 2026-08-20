"""
Repositorio para gestión de usuarios, autenticación y roles.
"""
from core.database import BaseDatabase
from core.logger import get_logger, log_error

logger = get_logger("UsuariosRepo")

class UsuariosRepository:
    def __init__(self, db: BaseDatabase | None = None):
        self.db = db or BaseDatabase()

    def autenticar(self, usuario: str, clave: str) -> dict | None:
        """Verifica credenciales del usuario en la base de datos."""
        try:
            endpoint = f"usuarios?usuario=eq.{usuario}&clave=eq.{clave}&activo=eq.true"
            res = self.db.get(endpoint, timeout=8)
            if res and res.status_code == 200:
                data = res.json()
                if data and len(data) > 0:
                    return data[0]
            return None
        except Exception as ex:
            log_error(f"autenticar({usuario})", ex)
            return None
