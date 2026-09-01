"""
Módulo base de conexión HTTP con Supabase PostgREST.
Proporciona manejo de sesiones, timeouts y logging centralizado de errores.
"""
import requests
import json
from config import Config
from core.logger import get_logger, log_error

logger = get_logger("Database")

class BaseDatabase:
    """Cliente HTTP centralizado para comunicarse con la API PostgREST de Supabase."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BaseDatabase, cls).__new__(cls)
            cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY

        if self.url and self.url.endswith('/'):
            self.url = self.url[:-1]
        if self.url and not self.url.endswith('/rest/v1'):
            self.url = self.url + "/rest/v1"

        self.session = requests.Session()
        from requests.adapters import HTTPAdapter
        from urllib3.util import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }
        self.session.headers.update(self.headers)
        logger.info("Sesión HTTP de base de datos inicializada correctamente.")

    def reset_session(self):
        """Cierra sockets anteriores y renueva la sesión HTTP para auto-recuperación de conexión."""
        try:
            if hasattr(self, "session") and self.session:
                self.session.close()
        except Exception:
            pass
        self._init_connection()
        logger.info("Sesión HTTP de base de datos restablecida correctamente.")

    def check_connection(self) -> tuple[bool, str]:
        if not self.url or not self.key:
            return False, "Faltan credenciales de Supabase en configuración (.env)"
        try:
            res = self.session.get(f"{self.url}/catalogo_insumos?limit=1", headers=self.headers, timeout=12)
            if res.status_code == 200:
                return True, "Conexión exitosa con Supabase"
            return False, f"Error del servidor HTTP {res.status_code}: {res.text}"
        except requests.exceptions.RequestException as req_e:
            msg = log_error("check_connection", req_e)
            return False, msg
        except Exception as e:
            msg = log_error("check_connection_generico", e)
            return False, msg

    def get(self, endpoint: str, params: dict | None = None, custom_headers: dict | None = None, timeout: int = 15) -> requests.Response | None:
        try:
            url = f"{self.url}/{endpoint}" if not endpoint.startswith("http") else endpoint
            headers = self.headers.copy()
            if custom_headers:
                headers.update(custom_headers)
            response = self.session.get(url, params=params, headers=headers, timeout=timeout)
            return response
        except Exception as ex:
            log_error(f"GET {endpoint}", ex)
            return None

    def get_all(self, endpoint: str, page_size: int = 2000, timeout: int = 25) -> list[dict]:
        """Descarga todos los registros paginados de un endpoint PostgREST con alta resiliencia."""
        all_rows = []
        offset = 0
        sep = "&" if "?" in endpoint else "?"
        while True:
            p_endpoint = f"{endpoint}{sep}limit={page_size}&offset={offset}"
            res = self.get(p_endpoint, timeout=timeout)
            if not res or res.status_code != 200:
                break
            data = res.json()
            if not data or not isinstance(data, list):
                break
            all_rows.extend(data)
            if len(data) < page_size:
                break
            offset += page_size
        return all_rows


    def post(self, endpoint: str, json_data: dict | list | None = None, custom_headers: dict | None = None, timeout: int = 10) -> requests.Response | None:
        try:
            url = f"{self.url}/{endpoint}" if not endpoint.startswith("http") else endpoint
            headers = self.headers.copy()
            if custom_headers:
                headers.update(custom_headers)
            response = self.session.post(url, json=json_data, headers=headers, timeout=timeout)
            return response
        except Exception as ex:
            log_error(f"POST {endpoint}", ex)
            return None

    def patch(self, endpoint: str, json_data: dict | list | None = None, custom_headers: dict | None = None, timeout: int = 10) -> requests.Response | None:
        try:
            url = f"{self.url}/{endpoint}" if not endpoint.startswith("http") else endpoint
            headers = self.headers.copy()
            if custom_headers:
                headers.update(custom_headers)
            response = self.session.patch(url, json=json_data, headers=headers, timeout=timeout)
            return response
        except Exception as ex:
            log_error(f"PATCH {endpoint}", ex)
            return None

    def delete(self, endpoint: str, custom_headers: dict | None = None, timeout: int = 10) -> requests.Response | None:
        try:
            url = f"{self.url}/{endpoint}" if not endpoint.startswith("http") else endpoint
            headers = self.headers.copy()
            if custom_headers:
                headers.update(custom_headers)
            response = self.session.delete(url, headers=headers, timeout=timeout)
            return response
        except Exception as ex:
            log_error(f"DELETE {endpoint}", ex)
            return None
