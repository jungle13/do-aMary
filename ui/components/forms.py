import flet as ft
from config import Config

def crear_input_estandar(label, icon=None, password=False, multiline=False, on_change=None):
    """
    Fábrica (Factory) para crear campos de texto estandarizados en toda la app.
    Cualquier cambio global en bordes, colores o tamaño se hace aquí y afecta todo el sistema.
    """
    return ft.TextField(
        label=label,
        prefix_icon=icon,
        password=password,
        multiline=multiline,
        on_change=on_change,
        border_radius=8,
        border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
        focused_border_color=Config.COLOR_PRIMARY,
        cursor_color=Config.COLOR_PRIMARY,
        text_size=14,
        content_padding=15
    )

def crear_boton_primario(text, icon=None, on_click=None):
    """
    Fábrica para botones primarios con el tema Azul Oscuro.
    """
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            padding=ft.padding.symmetric(horizontal=20, vertical=15)
        )
    )
