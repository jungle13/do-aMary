import sys
import io

# Garantizar streams válidos en ejecutables de escritorio sin consola (--noconsole)
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import flet as ft
from ui.app import AppLayout
from ui.views.login import LoginView
from config import Config
from core.mobile_server import iniciar_servidor_en_hilo

def main(page: ft.Page):
    # Iniciar servidor web móvil en red local Wi-Fi (puerto 8550)
    iniciar_servidor_en_hilo(port=8550)
    page.title = "Abarrotes y Desechables Doña Mary"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.window_maximized = True

    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme=ft.ColorScheme(
            primary=Config.COLOR_ACCENT,
            primary_container=Config.COLOR_MUTED,
            secondary=Config.COLOR_SECONDARY,
            background=Config.COLOR_BACKGROUND,
            surface=Config.COLOR_SURFACE,
            on_surface=Config.COLOR_TEXT,
            outline=Config.COLOR_BORDER,
        ),
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
    )

    def cerrar_sesion():
        page.overlay.clear()  # Purga diálogos flotantes residuales
        page.clean()
        mostrar_login()

    def on_login_success(usuario_data):
        page.overlay.clear()  # Asegura que el modal de bienvenida sea destruido
        page.clean()
        from core.audit_logger import set_current_user
        set_current_user(usuario_data)
        # Instanciar el layout e iniciar la carga inmediata
        app_layout = AppLayout(page, usuario_data=usuario_data, on_logout=cerrar_sesion)
        page.add(app_layout)
        page.update()

    def mostrar_login():
        login_view = LoginView(on_login_success=on_login_success)
        page.add(login_view)
        page.update()

    # Iniciar en pantalla de Login
    mostrar_login()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    try:
        iniciar_servidor_en_hilo(port=8550)
    except Exception:
        pass
    ft.app(target=main, assets_dir="assets")
