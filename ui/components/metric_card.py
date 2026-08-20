"""
Componente reutilizable de tarjeta de métricas / KPI para el Sistema Doña Mary.
"""
import flet as ft
from config import Config

class MetricCard(ft.Card):
    def __init__(
        self,
        title: str,
        value_control: ft.Control | str,
        icon: str | None = None,
        color: str | None = None,
        subtitle: str | None = None,
        expand: bool = True
    ):
        if isinstance(value_control, str):
            val_text = ft.Text(value_control, size=20, weight="bold", color=color or Config.COLOR_PRIMARY)
        else:
            val_text = value_control

        items = [
            ft.Text(title, size=12, color="grey700", weight="w500"),
            val_text
        ]
        if subtitle:
            items.append(ft.Text(subtitle, size=11, color="grey500"))

        content_col = ft.Column(items, spacing=2)

        if icon:
            row_content = ft.Row([
                ft.Icon(icon, size=28, color=color or Config.COLOR_PRIMARY),
                content_col
            ], spacing=12, alignment=ft.MainAxisAlignment.START)
            container_content = row_content
        else:
            container_content = content_col

        super().__init__(
            content=ft.Container(
                content=container_content,
                padding=10,
                border_radius=8
            ),
            expand=expand,
            elevation=1
        )
