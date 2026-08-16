import os
import sys
from dotenv import load_dotenv

# Determinar la ruta base dependiendo de si se ejecuta como script o como .exe
if getattr(sys, 'frozen', False):
    # Si es un ejecutable empaquetado (flet pack / PyInstaller), usar la carpeta temporal _MEIPASS
    base_path = sys._MEIPASS
else:
    # Si es el código fuente normal, usar la carpeta actual
    base_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(base_path, '.env')

# Cargar variables de entorno apuntando explícitamente al archivo
load_dotenv(dotenv_path=env_path)
class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Colores de la aplicación (Tema)
    COLOR_PRIMARY = "#0B2447" # Azul Oscuro (Primario)
    COLOR_SECONDARY = "#19376D" # Azul Medio (Secundario)
    COLOR_BACKGROUND = "#F8F9FA" # Blanco/Gris claro (Fondo)
    COLOR_TEXT = "#333333"
