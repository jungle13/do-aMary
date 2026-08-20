import flet as ft
from ui.app import AppLayout
from ui.views.login import LoginView
from config import Config

def main(page: ft.Page):
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
    ft.app(target=main, assets_dir="assets")
