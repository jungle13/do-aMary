import flet as ft
from ui.app import AppLayout
from config import Config

def main(page: ft.Page):
    # Configuración de la página principal
    page.title = "Abarrotes y Desechables Doña Mary"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.window_maximized = True
    page.fonts = {
        "Inter": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bslnt%2Cwght%5D.ttf"
    }
    
    # Sistema de Diseño Responsivo y Tema Global
    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme=ft.ColorScheme(
            primary=Config.COLOR_PRIMARY,
            primary_container=Config.COLOR_SECONDARY,
            secondary=Config.COLOR_SECONDARY,
            background=Config.COLOR_BACKGROUND,
            surface="white",
            on_surface=Config.COLOR_TEXT,
        ),
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
    )

    # Inicializar el layout de la app
    app_layout = AppLayout(page)
    
    # Agregar a la página
    page.add(app_layout)
    page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
