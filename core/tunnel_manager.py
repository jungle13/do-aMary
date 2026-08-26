import os
import sys
import re
import atexit
import shutil
import threading
import subprocess
import urllib.request
from typing import Callable, Optional
from core.logger import get_logger, log_error

logger = get_logger('TunnelManager')

CLOUDFLARED_DOWNLOAD_URL = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'

class TunnelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TunnelManager, cls).__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self.process: Optional[subprocess.Popen] = None
        self.public_url: Optional[str] = None
        self.is_running = False
        self.is_downloading = False
        self.status = 'DETENIDO'
        self.status_message = 'Túnel no iniciado'
        self._reader_thread = None
        
        base_dir = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
        self.bin_dir = os.path.join(base_dir, 'DonaMaryApp', 'bin')
        self.binary_path = os.path.join(self.bin_dir, 'cloudflared.exe')

        atexit.register(self.stop_tunnel)

    def get_binary_path(self) -> Optional[str]:
        system_bin = shutil.which('cloudflared')
        if system_bin:
            return system_bin
        
        if os.path.exists(self.binary_path) and os.path.getsize(self.binary_path) > 1000000:
            return self.binary_path

        return None

    def download_cloudflared(self, on_progress: Optional[Callable[[float, str], None]] = None) -> bool:
        try:
            self.is_downloading = True
            self.status = 'DESCARGANDO'
            self.status_message = 'Descargando componente de conexión segura...'
            os.makedirs(self.bin_dir, exist_ok=True)

            logger.info('Descargando cloudflared...')
            
            temp_path = self.binary_path + '.tmp'
            
            def _reporthook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(1.0, (block_num * block_size) / total_size)
                    mb_descargados = (block_num * block_size) / (1024 * 1024)
                    mb_totales = total_size / (1024 * 1024)
                    pct_int = int(percent * 100)
                    msg = f'Descargando Cloudflare Tunnel: {mb_descargados:.1f} MB / {mb_totales:.1f} MB ({pct_int} pct)'
                    if on_progress:
                        on_progress(percent, msg)

            urllib.request.urlretrieve(CLOUDFLARED_DOWNLOAD_URL, temp_path, _reporthook)

            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1000000:
                if os.path.exists(self.binary_path):
                    try:
                        os.remove(self.binary_path)
                    except Exception:
                        pass
                os.rename(temp_path, self.binary_path)
                logger.info('Cloudflared instalado en cache local.')
                self.is_downloading = False
                return True
            else:
                raise RuntimeError('Archivo descargado incompleto o corrupto.')

        except Exception as ex:
            log_error(f'Error descargando cloudflared: {ex}', 'TunnelManager')
            self.status = 'ERROR'
            self.status_message = f'Error en descarga: {str(ex)}'
            self.is_downloading = False
            return False

    def start_tunnel(
        self,
        port: int = 8550,
        on_ready: Optional[Callable[[str], None]] = None,
        on_status: Optional[Callable[[str, str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        def _worker():
            with self._lock:
                if self.is_running and self.public_url:
                    if on_ready:
                        on_ready(self.public_url)
                    return

                bin_path = self.get_binary_path()
                if not bin_path:
                    if on_status:
                        on_status('DESCARGANDO', 'Preparando módulo de conexión segura (primera vez)...')
                    
                    def _progress_cb(pct, msg):
                        if on_status:
                            on_status('DESCARGANDO', msg)

                    if not self.download_cloudflared(on_progress=_progress_cb):
                        if on_error:
                            on_error('No se pudo descargar el componente Cloudflare Tunnel.')
                        return
                    
                    bin_path = self.get_binary_path()

                if not bin_path or not os.path.exists(bin_path):
                    if on_error:
                        on_error('No se encontró el ejecutable de Cloudflare Tunnel.')
                    return

                self.status = 'CONECTANDO'
                self.status_message = 'Estableciendo túnel seguro con Cloudflare...'
                if on_status:
                    on_status('CONECTANDO', self.status_message)

                try:
                    cmd = [
                        bin_path,
                        'tunnel',
                        '--url', f'http://127.0.0.1:{port}',
                        '--no-autoupdate'
                    ]

                    creationflags = 0
                    if sys.platform == 'win32':
                        creationflags = subprocess.CREATE_NO_WINDOW

                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        creationflags=creationflags
                    )

                    logger.info(f'Proceso cloudflared iniciado (PID: {self.process.pid})')

                    url_found = None
                    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

                    def _read_output(stream):
                        nonlocal url_found
                        try:
                            for line in iter(stream.readline, ''):
                                if not line:
                                    break
                                line_str = line.strip()
                                match = url_pattern.search(line_str)
                                if match and not url_found:
                                    url_found = match.group(0)
                                    self.public_url = url_found
                                    self.is_running = True
                                    self.status = 'ACTIVO'
                                    self.status_message = f'Túnel activo: {self.public_url}'
                                    logger.info(f'URL Pública Cloudflare Tunnel: {self.public_url}')
                                    if on_ready:
                                        on_ready(self.public_url)
                                    if on_status:
                                        on_status('ACTIVO', self.status_message)
                        except Exception:
                            pass

                    t_err = threading.Thread(target=_read_output, args=(self.process.stderr,), daemon=True)
                    t_out = threading.Thread(target=_read_output, args=(self.process.stdout,), daemon=True)
                    t_err.start()
                    t_out.start()

                    for _ in range(50):
                        if url_found:
                            break
                        if self.process.poll() is not None:
                            break
                        threading.Event().wait(0.5)

                    if not url_found:
                        self.status = 'ERROR'
                        self.status_message = 'Tiempo de espera agotado al conectar con Cloudflare.'
                        if on_error:
                            on_error('No se pudo obtener la dirección pública de Cloudflare a tiempo.')
                        self.stop_tunnel()

                except Exception as ex:
                    log_error(f'Error al iniciar proceso de túnel: {ex}', 'TunnelManager')
                    self.status = 'ERROR'
                    self.status_message = f'Error: {str(ex)}'
                    if on_error:
                        on_error(str(ex))
                    self.stop_tunnel()

        threading.Thread(target=_worker, daemon=True).start()

    def stop_tunnel(self):
        with self._lock:
            if self.process:
                try:
                    logger.info(f'Deteniendo Cloudflare Tunnel (PID: {self.process.pid})...')
                    self.process.terminate()
                    self.process.wait(timeout=3)
                except Exception:
                    try:
                        self.process.kill()
                    except Exception:
                        pass
                self.process = None

            self.public_url = None
            self.is_running = False
            self.status = 'DETENIDO'
            self.status_message = 'Túnel detenido'

    def get_public_url(self) -> Optional[str]:
        return self.public_url if self.is_running else None
