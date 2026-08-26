import os
import sys
from dotenv import load_dotenv

# Determinar la ruta base dependiendo de si se ejecuta como script o como .exe
if getattr(sys, 'frozen', False):
    # Primero cargar el .env interno empaquetado en _MEIPASS
    internal_env = os.path.join(sys._MEIPASS, '.env')
    if os.path.exists(internal_env):
        load_dotenv(dotenv_path=internal_env)
    # También permitir sobrescribir con un .env externo junto al .exe si existe
    external_env = os.path.join(os.path.dirname(sys.executable), '.env')
    if os.path.exists(external_env):
        load_dotenv(dotenv_path=external_env, override=True)
else:
    # Si es el código fuente normal, usar la carpeta actual
    base_path = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_path, '.env')
    load_dotenv(dotenv_path=env_path)
class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    API_SECRET_KEY = os.getenv("API_SECRET_KEY", "donamary-secure-agent-key-2026")
    
    # --- SISTEMA DE DISEÑO / PALETA GLOBAL (Modern Slate & Royal Blue) ---
    COLOR_PRIMARY = "#0F172A"       # Slate 900 (Primario Institucional / Títulos)
    COLOR_SECONDARY = "#1E293B"     # Slate 800 (Secundario / Sidebar / Fondos Oscuros)
    COLOR_ACCENT = "#2563EB"        # Royal Blue 600 (Acciones interactivas / Botones principales)
    COLOR_ACCENT_HOVER = "#1D4ED8"  # Royal Blue 700 (Hover)
    COLOR_BACKGROUND = "#F8FAFC"    # Slate 50 (Fondo principal de la aplicación)
    COLOR_SURFACE = "#FFFFFF"       # Blanco puro para tarjetas y tablas
    COLOR_MUTED = "#F1F5F9"         # Slate 100 para fondos atenuados y encabezados
    COLOR_BORDER = "#E2E8F0"        # Slate 200 para bordes sutiles y divisores
    COLOR_TEXT = "#0F172A"          # Slate 900 para texto principal de alto contraste
    COLOR_TEXT_DARK = "#0F172A"     # Alias Slate 900
    COLOR_TEXT_MUTED = "#64748B"    # Slate 500 para subtítulos y etiquetas
    COLOR_TEXT_LIGHT = "#94A3B8"    # Slate 400 para placeholders y metadatos
    
    # Colores Semánticos / Estados
    COLOR_SUCCESS = "#10B981"       # Emerald 500 (Éxito / Válido / Ganancias)
    COLOR_SUCCESS_BG = "#ECFDF5"    # Emerald 50 (Fondo píldora éxito)
    COLOR_WARNING = "#F59E0B"       # Amber 500 (Alertas / Stock Mínimo)
    COLOR_WARNING_BG = "#FFFBEB"    # Amber 50 (Fondo píldora alerta)
    COLOR_DANGER = "#EF4444"        # Red 500 (Errores / Anulado / Salidas)
    COLOR_DANGER_BG = "#FEF2F2"     # Red 50 (Fondo píldora peligro)
    COLOR_INFO = "#3B82F6"          # Blue 500 (Información / Compras)
    COLOR_INFO_BG = "#EFF6FF"       # Blue 50 (Fondo píldora info)

