"""
Fábricas y utilidades de formularios y componentes de UI estandarizados para Sistema Doña Mary.
"""
import flet as ft
from config import Config

def crear_input_estandar(label, icon=None, password=False, multiline=False, on_change=None, height=44, dense=True):
    """
    Fábrica para crear campos de texto estandarizados en toda la app.
    """
    return ft.TextField(
        label=label,
        prefix_icon=icon,
        password=password,
        multiline=multiline,
        on_change=on_change,
        border_radius=8,
        height=height if not multiline else None,
        dense=dense,
        border_color=Config.COLOR_BORDER,
        focused_border_color=Config.COLOR_ACCENT,
        cursor_color=Config.COLOR_ACCENT,
        bgcolor="#FFFFFF",
        text_size=13,
        content_padding=12
    )

def crear_boton_primario(text, icon=None, on_click=None, height=40):
    """
    Fábrica para botones de acción principal (Royal Blue).
    """
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        height=height,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=Config.COLOR_ACCENT,
            color="white",
            elevation=0,
            padding=ft.padding.symmetric(horizontal=16, vertical=10)
        )
    )

def crear_boton_secundario(text, icon=None, on_click=None, height=40):
    """
    Fábrica para botones secundarios / contorno (Outlined).
    """
    return ft.OutlinedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        height=height,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            side=ft.BorderSide(1, Config.COLOR_BORDER),
            color=Config.COLOR_TEXT,
            padding=ft.padding.symmetric(horizontal=14, vertical=10)
        )
    )

def crear_badge_estado(estado: str) -> ft.Container:
    """
    Retorna una píldora visual estilizada con color según el estado del registro.
    """
    est = str(estado or "").upper().strip()
    if est in ("VÁLIDO", "VALIDO", "APROBADO", "GUARDADO", "ACTIVO"):
        bg = Config.COLOR_SUCCESS_BG
        fg = Config.COLOR_SUCCESS
    elif est in ("ANULADO", "ELIMINADO", "INACTIVO", "RECHAZADO"):
        bg = Config.COLOR_DANGER_BG
        fg = Config.COLOR_DANGER
    elif est in ("PENDIENTE", "EN_AUDITORIA", "PRELIMINAR", "NUEVO"):
        bg = Config.COLOR_WARNING_BG
        fg = Config.COLOR_WARNING
    else:
        bg = Config.COLOR_INFO_BG
        fg = Config.COLOR_INFO

    return ft.Container(
        content=ft.Text(est, size=11, weight="bold", color=fg),
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        bgcolor=bg,
        border_radius=12,
        border=ft.border.all(1, ft.colors.with_opacity(0.3, fg))
    )
