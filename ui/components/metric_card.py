"""
Componente reutilizable de tarjeta de métricas / KPI para el Sistema Doña Mary.
Diseño moderno con contenedor de icono translúcido, sombras suaves y jerarquía clara.
"""
import flet as ft
from config import Config

class MetricCard(ft.Container):
    def __init__(
        self,
        title: str,
        value_control: ft.Control | str,
        icon: str | None = None,
        color: str | None = None,
        subtitle: str | None = None,
        expand: bool = True,
        col: dict | int | None = None
    ):
        card_color = color or Config.COLOR_ACCENT

        if isinstance(value_control, str):
            val_text = ft.Text(value_control, size=22, weight="bold", color=Config.COLOR_PRIMARY)
        else:
            val_text = value_control

        items = [
            ft.Text(title.upper(), size=11, color=Config.COLOR_TEXT_MUTED, weight="w600"),
            val_text
        ]
        if subtitle:
            items.append(ft.Text(subtitle, size=11, color=Config.COLOR_TEXT_LIGHT))

        text_col = ft.Column(items, spacing=2)

        if icon:
            icon_pill = ft.Container(
                content=ft.Icon(icon, size=22, color=card_color),
                padding=10,
                bgcolor=ft.colors.with_opacity(0.12, card_color),
                border_radius=10
            )
            inner_content = ft.Row([
                icon_pill,
                text_col
            ], spacing=14, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        else:
            inner_content = text_col

        super().__init__(
            content=inner_content,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor=Config.COLOR_SURFACE,
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=6,
                color=ft.colors.with_opacity(0.04, "black"),
                offset=ft.Offset(0, 2)
            ),
            expand=expand,
            col=col
        )
