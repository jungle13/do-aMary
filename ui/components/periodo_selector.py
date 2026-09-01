"""
ui/components/periodo_selector.py
Widget compacto reutilizable para seleccionar y visualizar el periodo y su estado en cada módulo.
"""
import flet as ft
from config import Config
from core.periodo_manager import PeriodoManager


class PeriodoSelectorWidget(ft.Container):
    def __init__(self, on_change_callback=None, page: ft.Page | None = None):
        super().__init__()
        self.page = page
        self.on_change_callback = on_change_callback
        self.pm = PeriodoManager()
        
        self.border_radius = 8
        self.bgcolor = "white"
        self.border = ft.border.all(1, Config.COLOR_BORDER)
        self.padding = ft.padding.symmetric(horizontal=8, vertical=2)
        self.height = 36
        self.shadow = ft.BoxShadow(
            spread_radius=0.5,
            blur_radius=3,
            color=ft.colors.with_opacity(0.04, "black"),
            offset=ft.Offset(0, 1)
        )

        # Dropdown de periodos
        self.drop_periodo = ft.Dropdown(
            dense=True,
            text_size=11,
            width=140,
            content_padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_color=ft.colors.TRANSPARENT,
            focused_border_color=Config.COLOR_PRIMARY,
            on_change=self._on_dropdown_change
        )

        # Píldora de estado
        self.lbl_estado = ft.Text("ABIERTO", size=9.5, weight="bold", color="green800")
        self.badge_estado = ft.Container(
            content=self.lbl_estado,
            bgcolor="#e8f5e9",
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=4
        )

        # Botón de refresco rápido
        self.btn_refresh = ft.IconButton(
            icon=ft.icons.REFRESH_ROUNDED,
            icon_size=14,
            icon_color=Config.COLOR_TEXT_MUTED,
            tooltip="Refrescar datos del periodo",
            on_click=self._on_refresh_click
        )

        self.content = ft.Row([
            ft.Icon(ft.icons.CALENDAR_MONTH_ROUNDED, size=15, color=Config.COLOR_PRIMARY),
            ft.Text("Periodo:", size=11, weight="bold", color=Config.COLOR_PRIMARY),
            self.drop_periodo,
            self.badge_estado,
            self.btn_refresh
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        self._poblar_opciones()
        self.pm.subscribe(self._on_global_periodo_notified)

    def _poblar_opciones(self):
        """Llena el dropdown con los periodos disponibles."""
        periodos = self.pm.cargar_periodos()
        opciones = []
        for p in periodos:
            mes = p.get("mes_periodo")
            if not mes:
                continue
            nombre = self.pm.formatear_nombre_mes(mes)
            opciones.append(ft.dropdown.Option(key=mes, text=nombre))

        self.drop_periodo.options = opciones
        periodo_actual = self.pm.get_periodo_activo()
        self.drop_periodo.value = periodo_actual
        self._actualizar_badge_estado(periodo_actual)

    def _actualizar_badge_estado(self, mes: str):
        """Actualiza el color y texto del badge de estado del periodo."""
        estado = self.pm.get_estado_periodo(mes)
        self.lbl_estado.value = estado

        colores = {
            "ABIERTO": ("#e8f5e9", "green800"),
            "CERRADO": ("#ffebee", "red800"),
            "EN_AUDITORIA": ("#e3f2fd", "blue800"),
            "PRELIMINAR": ("#fff8e1", "amber900")
        }
        bg, fg = colores.get(estado, ("#f5f5f5", "grey800"))
        self.badge_estado.bgcolor = bg
        self.lbl_estado.color = fg

    def _on_dropdown_change(self, e):
        nuevo_mes = self.drop_periodo.value
        if not nuevo_mes:
            return
        self._actualizar_badge_estado(nuevo_mes)
        self.pm.set_periodo_activo(nuevo_mes, notify_source=self)
        if self.on_change_callback:
            self.on_change_callback(nuevo_mes)
        self._safe_update()

    def _on_refresh_click(self, e):
        self._poblar_opciones()
        actual = self.pm.get_periodo_activo()
        if self.on_change_callback:
            self.on_change_callback(actual)
        self._safe_update()

    def _on_global_periodo_notified(self, nuevo_periodo: str, source):
        if source is self:
            return
        self._poblar_opciones()
        self.drop_periodo.value = nuevo_periodo
        self._actualizar_badge_estado(nuevo_periodo)
        if self.on_change_callback:
            self.on_change_callback(nuevo_periodo)
        self._safe_update()

    def _safe_update(self):
        try:
            if self.page:
                self.page.update()
            elif self.uid:
                self.update()
        except Exception:
            pass

    def get_periodo_actual(self) -> str:
        return self.drop_periodo.value or self.pm.get_periodo_activo()

    def get_fecha_corte(self) -> str:
        return self.pm.get_fecha_corte(self.get_periodo_actual())

    def get_rango_fechas(self) -> tuple[str, str]:
        return self.pm.get_rango_fechas(self.get_periodo_actual())
