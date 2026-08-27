import flet as ft
import threading
import datetime
import calendar
from concurrent.futures import ThreadPoolExecutor
from config import Config
from core.supabase_client import SupabaseClient
from core.fecha_utils import get_ahora_local, get_hoy_local_str, get_mes_actual_str

class DashboardView(ft.Container):
    def __init__(self, page: ft.Page = None):
        super().__init__()
        self.page = page
        self.expand = True
        self.padding = 20
        self.db = SupabaseClient()
        
        self.lbl_periodo_dash = ft.Text("Periodo: ...", size=13, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_estado_dash = ft.Text("Estado: ...", size=13, weight="bold")
        self.lbl_fecha_hora = ft.Text("...", size=12, color="grey")

        self.fecha_filtro_dash = None
        self.date_picker_dash = ft.DatePicker(
            on_change=self.on_fecha_dash_change,
            first_date=datetime.datetime(2020, 1, 1),
            last_date=datetime.datetime(2035, 12, 31)
        )

        self.btn_fecha_dash = ft.OutlinedButton(
            text=f"Fecha: {get_ahora_local().strftime('%d/%m/%Y')}",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_dash.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=38
        )
        self.btn_clear_fecha_dash = ft.IconButton(
            icon=ft.icons.CLEAR, icon_color="red", tooltip="Restablecer a Hoy",
            visible=False, on_click=self.limpiar_filtro_fecha_dash
        )

        badge_info = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Row([self.lbl_periodo_dash, ft.Text("|", color="grey", size=13), self.lbl_estado_dash], spacing=5),
                    ft.Row([ft.Icon(ft.icons.ACCESS_TIME, size=14, color="grey"), self.lbl_fecha_hora], spacing=5)
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                ft.Container(width=10),
                self.btn_fecha_dash,
                self.btn_clear_fecha_dash
            ], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, Config.COLOR_BORDER),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.04, "black"), offset=ft.Offset(0, 1))
        )

        header_row = ft.Row([
            ft.Column([
                ft.Text("Dashboard General", size=26, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Resumen ejecutivo del sistema", size=13, color=Config.COLOR_TEXT_MUTED),
            ], spacing=2),
            badge_info
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Tarjetas de KPIs (Valores Iniciales) - SECCIÓN COSTOS
        self.val_inventario = ft.Text("$ 0", size=22, weight="bold", color=Config.COLOR_PRIMARY)
        self.sub_inventario = ft.Text("Valoración real stock > 0", size=10, color="grey600")
        
        self.val_compras = ft.Text("$ 0", size=22, weight="bold", color=Config.COLOR_PRIMARY)
        self.sub_compras = ft.Text("Entradas acumuladas del mes", size=10, color="grey600")
        
        self.val_compras_hoy = ft.Text("$ 0", size=22, weight="bold", color=Config.COLOR_PRIMARY)
        self.sub_compras_hoy = ft.Text("Registradas hoy", size=10, color="grey600")
        
        self.val_rotacion = ft.Text("N/D", size=13, weight="bold", color="teal800")
        
        # SECCIÓN VENTAS
        self.val_ingresos = ft.Text("$ 0", size=22, weight="bold", color=Config.COLOR_PRIMARY)
        self.sub_ingresos = ft.Text("Salidas acumuladas del mes", size=10, color="grey600")
        
        self.val_cumplimiento_mes = ft.Text("0.0%", size=22, weight="bold", color="teal800")
        self.sub_cumplimiento_mes = ft.Text("Capacidad: $ 0", size=10, color="grey600")

        self.val_ventas_hoy = ft.Text("$ 0", size=22, weight="bold", color=Config.COLOR_PRIMARY)
        self.sub_ventas_hoy = ft.Text("Registradas hoy", size=10, color="grey600")
        
        self.val_cumplimiento_hoy = ft.Text("0.0%", size=22, weight="bold", color="teal800")
        self.sub_cumplimiento_hoy = ft.Text("Meta diaria: $ 0", size=10, color="grey600")

        self.val_rentabilidad = ft.Text("0.0%", size=13, weight="bold", color="teal800")
        self.val_proyeccion_ventas = ft.Text("$ 0", size=13, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_proyeccion_rentabilidad = ft.Text("0.0%", size=13, weight="bold", color="teal800")
        
        self.kpi_costos_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Costo Inv. Actual", self.val_inventario, ft.icons.INVENTORY_2_ROUNDED, subtext_control=self.sub_inventario, card_color="#3b82f6"), col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(content=self._build_kpi_card("Total Compras (Mes)", self.val_compras, ft.icons.SHOPPING_BAG_ROUNDED, subtext_control=self.sub_compras, card_color="#8b5cf6"), col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(content=self._build_kpi_card("Compras (Hoy)", self.val_compras_hoy, ft.icons.PAYMENTS_ROUNDED, subtext_control=self.sub_compras_hoy, card_color="#f59e0b"), col={"xs": 12, "sm": 6, "md": 4}),
        ], spacing=12, run_spacing=12)

        self.kpi_ventas_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Total Ventas (Mes)", self.val_ingresos, ft.icons.TRENDING_UP_ROUNDED, subtext_control=self.sub_ingresos, card_color="#10b981"), col={"xs": 12, "sm": 6, "md": 3}),
            ft.Container(content=self._build_kpi_card("Cumplimiento Mes", self.val_cumplimiento_mes, ft.icons.SPEED_ROUNDED, subtext_control=self.sub_cumplimiento_mes, card_color="#0284c7"), col={"xs": 12, "sm": 6, "md": 3}),
            ft.Container(content=self._build_kpi_card("Ventas (Hoy)", self.val_ventas_hoy, ft.icons.MONETIZATION_ON_ROUNDED, subtext_control=self.sub_ventas_hoy, card_color="#059669"), col={"xs": 12, "sm": 6, "md": 3}),
            ft.Container(content=self._build_kpi_card("Cumplimiento Hoy", self.val_cumplimiento_hoy, ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED, subtext_control=self.sub_cumplimiento_hoy, card_color="#0d9488"), col={"xs": 12, "sm": 6, "md": 3}),
        ], spacing=12, run_spacing=12)
        
        # SECCIÓN CARTERA (Total Recaudado y Saldo por Cobrar)
        self.val_total_recaudado = ft.Text("$ 0", size=22, weight="bold", color=Config.COLOR_PRIMARY)
        self.sub_total_recaudado = ft.Text("Recaudo efectivo y bancos", size=10, color="grey600")

        self.val_saldo_por_cobrar = ft.Text("$ 0", size=22, weight="bold", color=Config.COLOR_PRIMARY)
        self.sub_saldo_por_cobrar = ft.Text("Cartera pendiente a clientes", size=10, color="grey600")

        self.kpi_cartera_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Total Recaudado (Cartera)", self.val_total_recaudado, ft.icons.SAVINGS_ROUNDED, subtext_control=self.sub_total_recaudado, card_color="#059669"), col={"xs": 12, "sm": 6, "md": 6}),
            ft.Container(content=self._build_kpi_card("Saldo por Cobrar (Cartera)", self.val_saldo_por_cobrar, ft.icons.WARNING_AMBER_ROUNDED, subtext_control=self.sub_saldo_por_cobrar, card_color="#d97706"), col={"xs": 12, "sm": 6, "md": 6}),
        ], spacing=12, run_spacing=12)

        # Paso 3: Barra de Métricas Secundarias
        self.val_meta_diaria = ft.Text("$ 0 / día", size=13, weight="bold", color="teal700")

        self.kpi_secundarios = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.INSIGHTS, size=16, color=Config.COLOR_PRIMARY),
                ft.Text("Objetivo Comercial:", weight="bold", color=Config.COLOR_PRIMARY, size=12),
                ft.Text("Proy. Ventas Stock:", size=12, color="grey700"), self.val_proyeccion_ventas,
                ft.Text(" | Margen Proy.:", size=12, color="grey700"), self.val_proyeccion_rentabilidad,
                ft.Container(width=1, height=18, bgcolor="#e2e8f0", margin=ft.padding.symmetric(horizontal=6)),
                ft.Icon(ft.icons.FLAG, size=16, color="teal700"),
                ft.Text("Meta Venta Diaria:", weight="bold", size=12, color="grey700"), self.val_meta_diaria,
                ft.Container(expand=True),
                ft.Text("Rotación Global:", size=12, color="grey700"), self.val_rotacion,
            ], spacing=5, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor="white", border_radius=10, border=ft.border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.colors.with_opacity(0.04, "black"), offset=ft.Offset(0, 2))
        )

        # SECCIÓN AJUSTES
        self.col_ajustes_salida = ft.Column(spacing=5)
        self.col_ajustes_entrada = ft.Column(spacing=5)
        
        self.lbl_neto_ajustes_header = ft.Text("NETO: $0", weight="bold", size=16)
        header_ajustes = ft.Row([
            ft.Text("Impacto de Ajustes de Inventario (Mes Actual)", size=16, weight="bold", color=Config.COLOR_PRIMARY),
            self.lbl_neto_ajustes_header
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.panel_ajustes = ft.Row([
            # Panel Salida
            ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes de Salida (-)", size=15, weight="bold", color="red700"),
                    ft.Divider(height=1, color="#fee2e2"),
                    self.col_ajustes_salida
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                expand=True,
                border=ft.border.all(1, "#fecaca"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.04, "black"))
            ),
            # Panel Entrada
            ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes de Entrada (+)", size=15, weight="bold", color="teal700"),
                    ft.Divider(height=1, color="#d1fae5"),
                    self.col_ajustes_entrada
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                expand=True,
                border=ft.border.all(1, "#a7f3d0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.04, "black"))
            )
        ], spacing=15)

        # Botón para copiar resumen al portapapeles
        self.btn_copiar_resumen = ft.IconButton(
            icon=ft.icons.COPY_ROUNDED,
            icon_size=18,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Copiar Resumen Financiero al Portapapeles",
            on_click=self.copiar_resumen_kpis
        )
        
        header_kpis_row = ft.Row([
            ft.Text("Resumen Financiero y Operativo", size=18, weight="bold", color=Config.COLOR_PRIMARY),
            self.btn_copiar_resumen
        ], tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Ensamblaje del Layout
        self.seccion_kpis = ft.Column([
            header_kpis_row,
            self.kpi_costos_row,
            self.kpi_ventas_row,
            self.kpi_cartera_row,
            self.kpi_secundarios
        ], spacing=10)

        # SECCIÓN RESUMEN DE IMPUESTOS
        self.val_iva_generado_mes = ft.Text("$ 0", size=20, weight="bold", color="blue800")
        self.sub_iva_gen_mes = ft.Text("IVA facturado en ventas", size=10, color="grey600")
        
        self.val_iva_generado_hoy = ft.Text("$ 0", size=20, weight="bold", color="blue800")
        self.sub_iva_gen_hoy = ft.Text("IVA cobrado hoy", size=10, color="grey600")
        
        self.val_iva_pagado_mes = ft.Text("$ 0", size=20, weight="bold", color="purple800")
        self.sub_iva_pag_mes = ft.Text("Crédito fiscal en compras", size=10, color="grey600")
        
        self.val_iva_pagado_hoy = ft.Text("$ 0", size=20, weight="bold", color="purple800")
        self.sub_iva_pag_hoy = ft.Text("IVA compras de hoy", size=10, color="grey600")

        header_impuestos_row = ft.Row([
            ft.Text("Resumen de Impuestos (IVA)", size=18, weight="bold", color=Config.COLOR_PRIMARY),
        ], tight=True)

        self.kpi_iva_generado_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("IVA Generado (Mes)", self.val_iva_generado_mes, ft.icons.RECEIPT_LONG_ROUNDED, subtext_control=self.sub_iva_gen_mes, card_color="#2563eb"), col={"xs": 12, "sm": 6}),
            ft.Container(content=self._build_kpi_card("IVA Generado (Hoy)", self.val_iva_generado_hoy, ft.icons.POINT_OF_SALE_ROUNDED, subtext_control=self.sub_iva_gen_hoy, card_color="#3b82f6"), col={"xs": 12, "sm": 6}),
        ], spacing=12, run_spacing=12)

        self.kpi_iva_pagado_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("IVA Pagado (Mes)", self.val_iva_pagado_mes, ft.icons.SHOPPING_CART_CHECKOUT_ROUNDED, subtext_control=self.sub_iva_pag_mes, card_color="#7c3aed"), col={"xs": 12, "sm": 6}),
            ft.Container(content=self._build_kpi_card("IVA Pagado (Hoy)", self.val_iva_pagado_hoy, ft.icons.SHOPPING_BAG_ROUNDED, subtext_control=self.sub_iva_pag_hoy, card_color="#9333ea"), col={"xs": 12, "sm": 6}),
        ], spacing=12, run_spacing=12)

        self.seccion_impuestos = ft.Column([
            header_impuestos_row,
            self.kpi_iva_generado_row,
            self.kpi_iva_pagado_row
        ], spacing=10)

        self.seccion_ajustes = ft.Column([
            header_ajustes,
            self.panel_ajustes
        ], spacing=10)

        # Gráficos y Tablas
        # Contenedor de Categorías (Grilla Responsiva)
        self.categorias_row = ft.ResponsiveRow(columns=12, spacing=15, run_spacing=15)
        self.categorias_container = ft.Container(
            content=ft.Column([
                ft.Text("Rendimiento Detallado por Categoría", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.categorias_row
            ]),
            margin=ft.padding.only(top=10, bottom=10)
        )

        # Gráfico de Barras Moderno
        self.bar_chart = ft.BarChart(
            bar_groups=[],
            border=ft.border.all(1, "#f0f0f0"),
            min_y=0,
            expand=True,
            tooltip_bgcolor="white",
            interactive=True,
            left_axis=ft.ChartAxis(labels_size=50), 
            bottom_axis=ft.ChartAxis(labels_size=40), 
        )

        # Indicadores de Resumen del Gráfico
        self.badge_dias_cumplidos = ft.Text("...", size=13, weight="bold", color="teal800")
        self.badge_mejor_dia = ft.Text("...", size=13, weight="bold", color="blue800")
        self.badge_promedio_diario = ft.Text("...", size=13, weight="bold", color="grey800")
        self.badge_meta_promedio = ft.Text("...", size=13, weight="bold", color="purple800")

        kpi_strip_chart = ft.ResponsiveRow([
            ft.Container(
                content=ft.Column([
                    ft.Text("DÍAS META CUMPLIDA", size=10, color="grey600", weight="w600"),
                    self.badge_dias_cumplidos
                ], spacing=2),
                padding=10, bgcolor="#ecfdf5", border_radius=8, border=ft.border.all(1, "#a7f3d0"),
                col={"xs": 6, "sm": 3}
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("MEJOR DÍA DE VENTAS", size=10, color="grey600", weight="w600"),
                    self.badge_mejor_dia
                ], spacing=2),
                padding=10, bgcolor="#eff6ff", border_radius=8, border=ft.border.all(1, "#bfdbfe"),
                col={"xs": 6, "sm": 3}
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("PROMEDIO VENTA DÍA", size=10, color="grey600", weight="w600"),
                    self.badge_promedio_diario
                ], spacing=2),
                padding=10, bgcolor="#f8fafc", border_radius=8, border=ft.border.all(1, "#e2e8f0"),
                col={"xs": 6, "sm": 3}
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("META DIARIA BASE", size=10, color="grey600", weight="w600"),
                    self.badge_meta_promedio
                ], spacing=2),
                padding=10, bgcolor="#faf5ff", border_radius=8, border=ft.border.all(1, "#e9d5ff"),
                col={"xs": 6, "sm": 3}
            ),
        ], spacing=10, run_spacing=10)

        # Leyenda moderna
        leyenda = ft.Row([
            ft.Row([ft.Container(width=12, height=12, bgcolor="#10b981", border_radius=3), ft.Text("Ventas (Meta Superada)", size=11, weight="bold", color="black87")]),
            ft.Row([ft.Container(width=12, height=12, bgcolor="#3b82f6", border_radius=3), ft.Text("Ventas (En progreso)", size=11, weight="bold", color="black87")]),
            ft.Row([ft.Container(width=12, height=12, bgcolor="#a78bfa", border_radius=3), ft.Text("Meta Diaria", size=11, weight="bold", color="black87")]),
            ft.Row([ft.Container(width=12, height=12, bgcolor="#06b6d4", border_radius=3), ft.Text("Compras", size=11, weight="bold", color="black87")]),
        ], spacing=20, alignment=ft.MainAxisAlignment.CENTER, wrap=True)

        # Tira de tarjetas diarias
        self.cards_diarias_row = ft.Row(scroll=ft.ScrollMode.ALWAYS, spacing=10)

        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("Desempeño Diario: Ventas vs Meta de Venta vs Compras", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Text("Monitoreo día a día con cumplimiento porcentual de la meta de ventas", size=12, color="grey"),
                    ], expand=True, spacing=2),
                ]),
                ft.Divider(height=5, color="transparent"),
                kpi_strip_chart,
                ft.Divider(height=10, color="transparent"),
                leyenda,
                ft.Container(content=self.bar_chart, height=320, margin=ft.padding.only(top=10, bottom=15)),
                ft.Divider(height=1, color="#f0f0f0"),
                ft.Row([
                    ft.Icon(ft.icons.CALENDAR_VIEW_DAY, size=16, color=Config.COLOR_PRIMARY),
                    ft.Text("Seguimiento Día a Día (Desliza horizontalmente para ver el mes completo)", size=13, weight="bold", color="grey800"),
                ], spacing=6),
                ft.Container(
                    content=self.cards_diarias_row,
                    padding=ft.padding.symmetric(vertical=8),
                )
            ]),
            bgcolor="white",
            padding=20,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        # Tables
        self.dt_ventas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", size=12)),
                ft.DataColumn(ft.Text("Producto", size=12)),
                ft.DataColumn(ft.Text("Unidades", size=12), numeric=True),
                ft.DataColumn(ft.Text("Ingreso Total", size=12), numeric=True)
            ],
            rows=[],
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            column_spacing=15,
        )
        
        self.dt_costos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", size=12)),
                ft.DataColumn(ft.Text("Producto", size=12)),
                ft.DataColumn(ft.Text("Valor Inv.", size=12), numeric=True),
                ft.DataColumn(ft.Text("Rotación", size=12))
            ],
            rows=[],
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            column_spacing=15,
        )
        
        table_ventas_container = ft.Container(
            content=ft.Column([
                ft.Text("Top 10 Productos con Mayor Ingreso", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.dt_ventas
            ], scroll=ft.ScrollMode.AUTO),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            col={"xs": 12, "md": 6}
        )
        
        table_costos_container = ft.Container(
            content=ft.Column([
                ft.Text("Top 10 Productos con Mayor Costo", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.dt_costos
            ], scroll=ft.ScrollMode.AUTO),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            col={"xs": 12, "md": 6}
        )
        
        self.tables_row = ft.ResponsiveRow([
            table_ventas_container,
            table_costos_container
        ], spacing=15, run_spacing=15)

        # Indicador de carga superior
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)

        # ── TAB 1: Contenido del Resumen General (vista actual) ──────────────
        self.tab1_content = ft.Column([
            self.seccion_kpis,
            ft.Divider(height=10, color="transparent"),
            self.seccion_impuestos,
            ft.Divider(height=10, color="transparent"),
            self.seccion_ajustes,
            ft.Divider(height=10, color="transparent"),
            self.categorias_container,
            ft.Divider(height=10, color="transparent"),
            self.chart_container,
            ft.Divider(height=10, color="transparent"),
            self.tables_row,
            ft.Container(height=30)
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # ── TAB 2: Resumen Financiero por Día (Agrupado por Semanas) ─────────
        self.semanas_col = ft.Column(spacing=14)
        self._semanas_bodies: list[tuple[ft.Container, ft.Icon]] = []
        self._dias_cargados = False

        self._tab2_loading = ft.Row(
            [ft.ProgressRing(width=28, height=28, color=Config.COLOR_PRIMARY),
             ft.Text("Cargando resumen diario por semanas...", size=13, color="grey600")],
            alignment=ft.MainAxisAlignment.CENTER,
            visible=False
        )

        self.btn_toggle_all = ft.OutlinedButton(
            text="Contraer Todas",
            icon=ft.icons.UNFOLD_LESS_ROUNDED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=12, vertical=6)
            ),
            on_click=self._toggle_todas_semanas
        )

        self.tab2_content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.CALENDAR_MONTH_ROUNDED, size=20, color=Config.COLOR_PRIMARY),
                    ft.Text("Matriz Financiera Diaria por Semanas", size=16, weight="bold",
                            color=Config.COLOR_PRIMARY),
                    ft.Container(expand=True),
                    self.btn_toggle_all,
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="white", padding=ft.padding.symmetric(horizontal=16, vertical=12),
                border_radius=10,
                border=ft.border.all(1, "#e8edf2"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=4,
                                    color=ft.colors.with_opacity(0.04, "black")),
                margin=ft.padding.only(bottom=8)
            ),
            self._tab2_loading,
            self.semanas_col,
            ft.Container(height=40)
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # ── Selector de Pestañas (SegmentedButton) ────────────────────────────
        self.tab_selector = ft.SegmentedButton(
            selected={"GENERAL"},
            allow_multiple_selection=False,
            segments=[
                ft.Segment(
                    value="GENERAL",
                    label=ft.Text("Resumen General", size=12.5, weight="w600"),
                    icon=ft.Icon(ft.icons.DASHBOARD_ROUNDED, size=16)
                ),
                ft.Segment(
                    value="DIAS",
                    label=ft.Text("Resumen Financiero por Día", size=12.5, weight="w600"),
                    icon=ft.Icon(ft.icons.CALENDAR_VIEW_MONTH_ROUNDED, size=16)
                ),
            ],
            height=36,
            on_change=self._on_tab_selector_change
        )

        self.tab1_content.visible = True
        self.tab2_content.visible = False

        # ── Layout raíz ───────────────────────────────────────────────────────
        self.content = ft.Column([
            self.progress_bar,
            header_row,
            ft.Container(
                content=ft.Row([
                    self.tab_selector,
                    ft.Container(expand=True),
                ]),
                margin=ft.padding.only(top=4, bottom=6)
            ),
            self.tab1_content,
            self.tab2_content,
        ], expand=True)

    def _on_tab_selector_change(self, e) -> None:
        """Cambia el contenido activo entre Resumen General y Resumen por Día."""
        sel = "GENERAL"
        if e and hasattr(e, "control") and e.control.selected:
            sel = list(e.control.selected)[0]

        self.tab_selector.selected = {sel}
        self.tab1_content.visible = (sel == "GENERAL")
        self.tab2_content.visible = (sel == "DIAS")

        # Cargar datos detallados del mes solo cuando la pestaña 'DIAS' es seleccionada por primera vez
        if sel == "DIAS" and not self._dias_cargados:
            self._tab2_loading.visible = True
            self.safe_update()
            threading.Thread(target=self._fetch_dias_worker, daemon=True).start()
        else:
            self.safe_update()

    def did_mount(self):
        if not hasattr(self, "overlay_added"):
            self.page.overlay.append(self.date_picker_dash)
            self.overlay_added = True
        self.load_data()

    def safe_update(self):
        """Actualiza la UI con seguridad."""
        try:
            if self.page:
                self.page.update()
            elif self.uid:
                self.update()
        except Exception:
            pass

    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self._dias_cargados = False
        self.progress_bar.visible = True
        self.safe_update()

        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def on_fecha_dash_change(self, e):
        if self.date_picker_dash.value:
            self.fecha_filtro_dash = self.date_picker_dash.value.strftime("%Y-%m-%d")
            self.btn_fecha_dash.text = f"Fecha: {self.date_picker_dash.value.strftime('%d/%m/%Y')}"
            self.btn_clear_fecha_dash.visible = True
            self.load_data()

    def limpiar_filtro_fecha_dash(self, e):
        self.fecha_filtro_dash = None
        self.date_picker_dash.value = None
        self.btn_fecha_dash.text = f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')}"
        self.btn_clear_fecha_dash.visible = False
        self.load_data()

    def _clasificar_ajustes(self, ajustes_bd: list) -> tuple[dict, dict, float, float, float, float, float]:
        """Clasifica los ajustes de inventario en entradas y salidas calculando totales y neto."""
        tipos_salida = {
            "Daño / Merma": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Vencimiento": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Pérdida": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Consumo Familiar": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Consumo Cliente (Cortesía)": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Donación Saliente": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Otro (Salida)": {"conteo": 0, "cantidad": 0, "costo": 0.0}
        }

        tipos_entrada = {
            "Sobrante de Inventario": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Donación Entrante": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Devolución Cliente": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Otro (Entrada)": {"conteo": 0, "cantidad": 0, "costo": 0.0}
        }

        for fila in (ajustes_bd or []):
            tipo_bd = fila.get("tipo_ajuste", "")
            motivo_bd = fila.get("motivo_observacion", "")
            cant = float(fila.get("cantidad_total") or 0)
            costo = float(fila.get("costo_total") or 0)
            conteo = int(fila.get("conteo") or 0)

            asignado = False
            if tipo_bd in ("AJUSTE_ENTRADA", "ENTRADA_POR_SOBRANTE"):
                for key in tipos_entrada.keys():
                    if key.lower() in motivo_bd.lower():
                        tipos_entrada[key]["conteo"] += conteo
                        tipos_entrada[key]["cantidad"] += cant
                        tipos_entrada[key]["costo"] += costo
                        asignado = True
                        break
                if not asignado:
                    tipos_entrada["Otro (Entrada)"]["conteo"] += conteo
                    tipos_entrada["Otro (Entrada)"]["cantidad"] += cant
                    tipos_entrada["Otro (Entrada)"]["costo"] += costo
            else:
                for key in tipos_salida.keys():
                    if key.lower() in motivo_bd.lower():
                        tipos_salida[key]["conteo"] += conteo
                        tipos_salida[key]["cantidad"] += cant
                        tipos_salida[key]["costo"] += costo
                        asignado = True
                        break
                if not asignado:
                    if tipo_bd == "BAJA_VENCIMIENTO": k = "Vencimiento"
                    elif tipo_bd == "SALIDA_POR_FALTANTE": k = "Pérdida"
                    else: k = "Otro (Salida)"
                    tipos_salida[k]["conteo"] += conteo
                    tipos_salida[k]["cantidad"] += cant
                    tipos_salida[k]["costo"] += costo

        tot_cost_ent = sum([d["costo"] for d in tipos_entrada.values()])
        tot_cost_sal = sum([d["costo"] for d in tipos_salida.values()])
        tot_cant_ent = sum([d["cantidad"] for d in tipos_entrada.values()])
        tot_cant_sal = sum([d["cantidad"] for d in tipos_salida.values()])
        neto = tot_cost_ent - tot_cost_sal

        return tipos_entrada, tipos_salida, tot_cost_ent, tot_cost_sal, tot_cant_ent, tot_cant_sal, neto

    def _fetch_data_worker(self):
        """Ejecuta consultas eficientes para la vista general sin sobrecargar la red ni la UI."""
        try:
            hoy_obj = (
                datetime.datetime.strptime(self.fecha_filtro_dash, "%Y-%m-%d").date()
                if self.fecha_filtro_dash
                else datetime.date.today()
            )
            mes_actual = hoy_obj.strftime("%Y-%m")

            # 1. Cargar consultas esenciales en un pool controlado de máximo 5 hilos
            with ThreadPoolExecutor(max_workers=5) as executor:
                f_cierre = executor.submit(self.db.obtener_estado_cierre, mes_actual)
                f_cat_kpis = executor.submit(self.db.get_rendimiento_categorias_periodo, None, self.fecha_filtro_dash)
                f_ven = executor.submit(self.db.get_ventas_summary, fecha_corte=self.fecha_filtro_dash)
                f_com = executor.submit(self.db.get_compras_summary, fecha_corte=self.fecha_filtro_dash)
                f_proy = executor.submit(self.db.get_proyeccion_ventas, fecha_corte=self.fecha_filtro_dash)
                f_ajustes = executor.submit(self.db.get_ajustes_mes, mes_actual, fecha_corte=self.fecha_filtro_dash)
                f_tendencia = executor.submit(self.db.get_tendencia_diaria, fecha_corte=self.fecha_filtro_dash)
                f_top_ventas = executor.submit(self.db.get_top_ventas_mes, limit=10, fecha_corte=self.fecha_filtro_dash)
                f_top_costos = executor.submit(self.db.get_top_costo_inventario, limit=10, fecha_corte=self.fecha_filtro_dash)
                f_cartera = executor.submit(self.db.cartera_repo.get_resumen_cartera, fecha_filtro=self.fecha_filtro_dash or "")

                datos_cierre = f_cierre.result() or {}
                kpis_cat = f_cat_kpis.result() or []
                res_ven = f_ven.result() or {}
                res_com = f_com.result() or {}
                proyeccion_ventas = float(f_proy.result() or 0.0)
                ajustes_bd = f_ajustes.result() or []
                tendencia = f_tendencia.result() or {}
                top_ventas = f_top_ventas.result() or []
                top_costos = f_top_costos.result() or []
                res_cartera_kpis, _, _ = f_cartera.result() or ({}, [], [])

            # 2. Contexto Temporal y Estado de Periodo
            estado_periodo = datos_cierre.get('periodo', {}).get('estado', 'ABIERTO') if datos_cierre and datos_cierre.get('periodo') else 'ABIERTO'
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            partes = mes_actual.split('-')
            nombre_mes = f"{meses[int(partes[1]) - 1]} {partes[0]}"

            self.lbl_periodo_dash.value = f"Periodo: {nombre_mes}"
            self.lbl_estado_dash.value = f"Estado: {estado_periodo}"

            colores_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
            self.lbl_estado_dash.color = colores_estado.get(estado_periodo, 'black')

            ahora = get_ahora_local()
            self.lbl_fecha_hora.value = ahora.strftime("%d/%m/%Y - %I:%M %p")

            # 3. KPIs de Inventario, Ventas, Compras e IVA
            val_inv = sum([float(c.get("inventario_costo") or 0.0) for c in kpis_cat])
            self.val_inventario.value = f"$ {val_inv:,.0f}"

            ingresos = float(res_ven.get('total_mes') or 0.0)
            compras = float(res_com.get('total_mes') or 0.0)
            ventas_hoy = float(res_ven.get('total_hoy') or 0.0)
            compras_hoy = float(res_com.get('total_hoy') or 0.0)

            self.val_ingresos.value = f"$ {ingresos:,.0f}"
            self.val_ventas_hoy.value = f"$ {ventas_hoy:,.0f}"
            self.val_compras.value = f"$ {compras:,.0f}"
            self.val_compras_hoy.value = f"$ {compras_hoy:,.0f}"

            iva_gen_mes = float(res_ven.get('iva_mes') or 0.0)
            iva_gen_hoy = float(res_ven.get('iva_hoy') or 0.0)
            iva_pag_mes = float(res_com.get('iva_mes') or 0.0)
            iva_pag_hoy = float(res_com.get('iva_hoy') or 0.0)

            self.val_iva_generado_mes.value = f"$ {iva_gen_mes:,.0f}"
            self.val_iva_generado_hoy.value = f"$ {iva_gen_hoy:,.0f}"
            self.val_iva_pagado_mes.value = f"$ {iva_pag_mes:,.0f}"
            self.val_iva_pagado_hoy.value = f"$ {iva_pag_hoy:,.0f}"

            # 4. KPIs de Cartera y Recaudos
            tot_recaudado = float(res_cartera_kpis.get('total_recaudado') or 0.0)
            tot_efectivo = float(res_cartera_kpis.get('total_efectivo') or 0.0)
            tot_transferencias = float(res_cartera_kpis.get('total_transferencias') or 0.0)
            saldo_pendiente = float(res_cartera_kpis.get('total_saldo_pendiente') or 0.0)
            clientes_deuda = int(res_cartera_kpis.get('clientes_con_deuda') or 0)

            self.val_total_recaudado.value = f"$ {tot_recaudado:,.0f}"
            self.sub_total_recaudado.value = f"Efectivo: ${tot_efectivo:,.0f} | Bancos: ${tot_transferencias:,.0f}"

            self.val_saldo_por_cobrar.value = f"$ {saldo_pendiente:,.0f}"
            self.sub_saldo_por_cobrar.value = f"{clientes_deuda} Clientes con saldo pendiente"

            rentabilidad = ((ingresos - compras) / ingresos * 100) if ingresos > 0 else 0.0
            self.val_rentabilidad.value = f"{rentabilidad:.1f}%"
            self.val_rentabilidad.color = "teal800" if rentabilidad >= 0 else "red700"

            rotacion_global = (ingresos / val_inv) if val_inv > 0 else 0.0
            self.val_rotacion.value = f"{rotacion_global:.2f}x" if val_inv > 0 else "N/D"

            self.val_proyeccion_ventas.value = f"$ {proyeccion_ventas:,.0f}"
            proy_rent = ((proyeccion_ventas - val_inv) / proyeccion_ventas * 100) if (proyeccion_ventas > 0 and val_inv > 0) else 0.0
            self.val_proyeccion_rentabilidad.value = f"{proy_rent:.1f}%"
            self.val_proyeccion_rentabilidad.color = "teal800" if proy_rent >= 0 else "red700"

            meta_total_mes = ingresos + proyeccion_ventas
            pct_cumplimiento_mes = (ingresos / meta_total_mes * 100) if meta_total_mes > 0 else 0.0
            self.val_cumplimiento_mes.value = f"{pct_cumplimiento_mes:.1f}%"
            self.val_cumplimiento_mes.color = "teal800" if pct_cumplimiento_mes >= 100 else ("blue800" if pct_cumplimiento_mes >= 50 else "amber800")
            self.sub_cumplimiento_mes.value = f"Capacidad total: $ {meta_total_mes:,.0f}"

            dias_en_mes = calendar.monthrange(hoy_obj.year, hoy_obj.month)[1]
            dias_restantes = max(1, dias_en_mes - hoy_obj.day + 1)
            meta_diaria = (proyeccion_ventas / dias_restantes) if dias_restantes > 0 and proyeccion_ventas > 0 else 0.0
            self.val_meta_diaria.value = f"$ {meta_diaria:,.0f} / día"

            pct_cumplimiento_hoy = (ventas_hoy / meta_diaria * 100) if meta_diaria > 0 else 0.0
            self.val_cumplimiento_hoy.value = f"{pct_cumplimiento_hoy:.1f}%"
            self.val_cumplimiento_hoy.color = "teal800" if pct_cumplimiento_hoy >= 100 else ("blue800" if pct_cumplimiento_hoy > 0 else "grey700")
            self.sub_cumplimiento_hoy.value = f"Meta diaria: $ {meta_diaria:,.0f}"

            # 5. Ajustes e Indicadores
            tipos_ent, tipos_sal, tot_cost_ent, tot_cost_sal, tot_cant_ent, tot_cant_sal, neto = self._clasificar_ajustes(ajustes_bd)

            if neto > 0:
                self.lbl_neto_ajustes_header.value = f"NETO (POSITIVO): +${neto:,.0f}"
                self.lbl_neto_ajustes_header.color = "#2ecca0"
            elif neto < 0:
                self.lbl_neto_ajustes_header.value = f"NETO (NEGATIVO): -${abs(neto):,.0f}"
                self.lbl_neto_ajustes_header.color = "#f26c61"
            else:
                self.lbl_neto_ajustes_header.value = "NETO: $0"
                self.lbl_neto_ajustes_header.color = "grey"

            self.col_ajustes_entrada.controls.clear()
            self.col_ajustes_salida.controls.clear()

            for key, datos in tipos_ent.items():
                self.col_ajustes_entrada.controls.append(
                    ft.Row([
                        ft.Text(f"{key} ({datos['conteo']})", size=12, color="black87", expand=True),
                        ft.Text(f"{datos['cantidad']:.0f} unds", size=12, color="grey"),
                        ft.Text(f"${datos['costo']:,.0f}", size=12, weight="bold", color="#2ecca0")
                    ])
                )
            self.col_ajustes_entrada.controls.append(ft.Divider(color="black12", height=10))
            self.col_ajustes_entrada.controls.append(
                ft.Row([
                    ft.Text("TOTAL ENTRADAS", size=12, weight="bold"),
                    ft.Text(f"{tot_cant_ent:.0f} unds", size=12, weight="bold", color="grey", expand=True, text_align=ft.TextAlign.CENTER),
                    ft.Text(f"${tot_cost_ent:,.0f}", size=12, weight="bold", color="#2ecca0")
                ])
            )

            for key, datos in tipos_sal.items():
                self.col_ajustes_salida.controls.append(
                    ft.Row([
                        ft.Text(f"{key} ({datos['conteo']})", size=12, color="black87", expand=True),
                        ft.Text(f"{datos['cantidad']:.0f} unds", size=12, color="grey"),
                        ft.Text(f"${datos['costo']:,.0f}", size=12, weight="bold", color="#f26c61")
                    ])
                )
            self.col_ajustes_salida.controls.append(ft.Divider(color="black12", height=10))
            self.col_ajustes_salida.controls.append(
                ft.Row([
                    ft.Text("TOTAL SALIDAS", size=12, weight="bold"),
                    ft.Text(f"{tot_cant_sal:.0f} unds", size=12, weight="bold", color="grey", expand=True, text_align=ft.TextAlign.CENTER),
                    ft.Text(f"${tot_cost_sal:,.0f}", size=12, weight="bold", color="#f26c61")
                ])
            )

            # 6. Gráfico de Barras y Tira Diaria
            meta_diaria_base = (meta_total_mes / dias_en_mes) if (dias_en_mes > 0 and meta_total_mes > 0) else 0.0
            dias_ordenados = sorted(tendencia.keys())
            
            dias_cumplidos = 0
            dias_activos = 0
            suma_ventas_activos = 0.0
            mejor_dia_fecha = ""
            mejor_dia_venta = 0.0
            max_val_y = meta_diaria_base
            bar_groups = []
            etiquetas_x = []

            for i, dia in enumerate(dias_ordenados):
                v = float(tendencia[dia]["ventas"])
                c = float(tendencia[dia]["compras"])
                m = meta_diaria_base
                
                if v > 0:
                    dias_activos += 1
                    suma_ventas_activos += v
                if v >= m and m > 0:
                    dias_cumplidos += 1
                if v > mejor_dia_venta:
                    mejor_dia_venta = v
                    mejor_dia_fecha = dia

                if v > max_val_y: max_val_y = v
                if c > max_val_y: max_val_y = c

                pct_dia = (v / m * 100) if m > 0 else 0.0
                col_v = "#10b981" if pct_dia >= 100 else ("#3b82f6" if v > 0 else "#cbd5e1")
                dt = datetime.datetime.strptime(dia, "%Y-%m-%d").date()

                rod_v = ft.BarChartRod(from_y=0, to_y=v, color=col_v, width=8, border_radius=ft.border_radius.vertical(top=4))
                rod_m = ft.BarChartRod(from_y=0, to_y=m, color="#a78bfa", width=8, border_radius=ft.border_radius.vertical(top=4))
                rod_c = ft.BarChartRod(from_y=0, to_y=c, color="#06b6d4", width=8, border_radius=ft.border_radius.vertical(top=4))

                bar_groups.append(ft.BarChartGroup(x=i, bar_rods=[rod_v, rod_m, rod_c]))
                etiquetas_x.append(
                    ft.ChartAxisLabel(
                        value=i,
                        label=ft.Container(content=ft.Text(f"{dt.day:02d}", size=9, color="grey700"), padding=ft.padding.only(top=5))
                    )
                )

            pct_dias_cumplidos = (dias_cumplidos / dias_activos * 100) if dias_activos > 0 else 0.0
            self.badge_dias_cumplidos.value = f"{dias_cumplidos} / {dias_activos} días ({pct_dias_cumplidos:.0f}%)"
            
            dt_mejor = datetime.datetime.strptime(mejor_dia_fecha, "%Y-%m-%d") if mejor_dia_fecha else None
            str_mejor = f"{dt_mejor.strftime('%d/%m')} (${mejor_dia_venta/1000000:.1f}M)" if dt_mejor else "N/D"
            self.badge_mejor_dia.value = str_mejor

            prom_v = (suma_ventas_activos / dias_activos) if dias_activos > 0 else 0.0
            self.badge_promedio_diario.value = f"${prom_v:,.0f} / día"
            self.badge_meta_promedio.value = f"${meta_diaria_base:,.0f} / día"

            self.bar_chart.bar_groups = bar_groups
            self.bar_chart.max_y = max_val_y * 1.15 if max_val_y > 0 else 1000.0

            def formato_moneda_corta(valor):
                if valor >= 1000000: return f"${valor/1000000:.1f}M"
                if valor >= 1000: return f"${valor/1000:.0f}k"
                return f"${valor:.0f}"

            intervalo_y = self.bar_chart.max_y / 6 if self.bar_chart.max_y > 0 else 100
            etiquetas_y = [
                ft.ChartAxisLabel(value=step * intervalo_y, label=ft.Text(formato_moneda_corta(step * intervalo_y), size=10, color="grey"))
                for step in range(7)
            ]
            self.bar_chart.left_axis.labels = etiquetas_y
            self.bar_chart.left_axis.labels_interval = intervalo_y
            self.bar_chart.bottom_axis.labels = etiquetas_x
            self.bar_chart.bottom_axis.labels_interval = 1

            self.cards_diarias_row.controls.clear()
            for dia in dias_ordenados:
                v_dia = float(tendencia[dia]["ventas"])
                c_dia = float(tendencia[dia]["compras"])
                card = self._crear_card_dia(dia, v_dia, c_dia, meta_diaria_base)
                self.cards_diarias_row.controls.append(card)

            # 7. Tablas
            self.dt_ventas.rows.clear()
            for item in top_ventas:
                self.dt_ventas.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(item.get('codigo') or ''), size=11)),
                        ft.DataCell(ft.Container(content=ft.Text(str(item.get('producto') or ''), size=11, no_wrap=True), width=120)),
                        ft.DataCell(ft.Text(str(item.get('unidades_vendidas') or 0), size=11)),
                        ft.DataCell(ft.Text(f"${float(item.get('ingreso_total') or 0):,.2f}", size=11))
                    ])
                )

            self.dt_costos.rows.clear()
            for item in top_costos:
                self.dt_costos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(item.get('codigo') or ''), size=11)),
                        ft.DataCell(ft.Container(content=ft.Text(str(item.get('producto') or ''), size=11, no_wrap=True), width=120)),
                        ft.DataCell(ft.Text(f"${float(item.get('valor_inventario') or 0):,.2f}", size=11)),
                        ft.DataCell(ft.Text(str(item.get('rotacion') or ''), size=11))
                    ])
                )

            self.categorias_row.controls.clear()
            for cat in kpis_cat:
                self.categorias_row.controls.append(self._crear_card_categoria(cat))

        except Exception as ex:
            import traceback
            traceback.print_exc()
        finally:
            self.progress_bar.visible = False
            self.safe_update()

    # ─── TAB 2: Carga y Renderizado del Resumen por Día Agrupado por Semanas ──

    def _toggle_todas_semanas(self, e):
        """Contrae o despliega todas las semanas simultáneamente."""
        cualquiera_visible = any(body.visible for body, _ in self._semanas_bodies)
        nuevo_estado = not cualquiera_visible

        for body, icon in self._semanas_bodies:
            body.visible = nuevo_estado
            icon.name = (
                ft.icons.KEYBOARD_ARROW_UP_ROUNDED
                if nuevo_estado
                else ft.icons.KEYBOARD_ARROW_DOWN_ROUNDED
            )

        self.btn_toggle_all.text = "Contraer Todas" if nuevo_estado else "Desplegar Todas"
        self.btn_toggle_all.icon = (
            ft.icons.UNFOLD_LESS_ROUNDED
            if nuevo_estado
            else ft.icons.UNFOLD_MORE_ROUNDED
        )
        self.safe_update()

    def _render_dias_grid(
        self,
        detalle_mes: dict,
        hoy_obj: datetime.date,
        meta_diaria: float,
        costo_inv_global: float,
    ) -> None:
        """Construye y agrupa por semanas las tarjetas de cada día del mes."""
        try:
            self.semanas_col.controls.clear()
            self._semanas_bodies.clear()

            dias_en_mes = calendar.monthrange(hoy_obj.year, hoy_obj.month)[1]
            dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

            # Generar semanas (Semana 1 a Semana 4 o 5 según días del mes)
            semanas_info = []
            dia_inicio = 1
            num_sem = 1
            while dia_inicio <= dias_en_mes:
                dia_fin = min(dia_inicio + 6, dias_en_mes)
                semanas_info.append((f"Semana {num_sem}", dia_inicio, dia_fin))
                dia_inicio = dia_fin + 1
                num_sem += 1

            for titulo_sem, ini_dia, fin_dia in semanas_info:
                cards_semana = []
                tot_v_sem = 0.0
                tot_c_sem = 0.0
                tot_r_sem = 0.0

                for num_dia in range(ini_dia, fin_dia + 1):
                    fecha_obj = datetime.date(hoy_obj.year, hoy_obj.month, num_dia)
                    dia_key = fecha_obj.strftime("%Y-%m-%d")
                    datos_dia = detalle_mes.get(dia_key, {})
                    nombre_dia = dias_semana[fecha_obj.weekday()]
                    es_futuro = fecha_obj > hoy_obj

                    tot_v_sem += float(datos_dia.get("ventas_total") or 0.0)
                    tot_c_sem += float(datos_dia.get("compras") or 0.0)
                    tot_r_sem += float(datos_dia.get("recaudado") or 0.0)

                    card = self._build_card_dia_resumen(
                        fecha_obj=fecha_obj,
                        nombre_dia=nombre_dia,
                        datos=datos_dia,
                        meta_diaria=meta_diaria,
                        costo_inv_global=costo_inv_global,
                        es_futuro=es_futuro,
                    )
                    # 3 columnas en pantallas grandes (lg: 4), 2 en medianas (md: 6), 1 en pequeñas (sm: 12)
                    cards_semana.append(
                        ft.Container(content=card, col={"xs": 12, "sm": 12, "md": 6, "lg": 4})
                    )

                seccion = self._crear_seccion_semana(
                    titulo_semana=titulo_sem,
                    dia_ini=ini_dia,
                    dia_fin=fin_dia,
                    cards_dias=cards_semana,
                    tot_ventas=tot_v_sem,
                    tot_compras=tot_c_sem,
                    tot_recaudado=tot_r_sem,
                    fecha_base=hoy_obj,
                    abierta_por_defecto=True,
                )
                self.semanas_col.controls.append(seccion)

            self.btn_toggle_all.text = "Contraer Todas"
            self.btn_toggle_all.icon = ft.icons.UNFOLD_LESS_ROUNDED
            self._dias_cargados = True
            self._tab2_loading.visible = False
        except Exception as ex:
            import traceback
            traceback.print_exc()

    def _crear_seccion_semana(
        self,
        titulo_semana: str,
        dia_ini: int,
        dia_fin: int,
        cards_dias: list,
        tot_ventas: float,
        tot_compras: float,
        tot_recaudado: float,
        fecha_base: datetime.date,
        abierta_por_defecto: bool = True
    ) -> ft.Container:
        """Crea un módulo colapsable (acordeón) para una semana con su resumen financiero."""
        meses_abr = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        mes_nom = meses_abr[fecha_base.month - 1]
        rango_txt = f"{dia_ini:02d} {mes_nom} - {dia_fin:02d} {mes_nom}"

        grid_dias = ft.ResponsiveRow(controls=cards_dias, columns=12, spacing=14, run_spacing=14)
        body_container = ft.Container(
            content=grid_dias,
            visible=abierta_por_defecto,
            padding=ft.padding.only(top=10, bottom=6)
        )

        arrow_icon = ft.Icon(
            ft.icons.KEYBOARD_ARROW_UP_ROUNDED if abierta_por_defecto else ft.icons.KEYBOARD_ARROW_DOWN_ROUNDED,
            size=22,
            color=Config.COLOR_PRIMARY
        )

        self._semanas_bodies.append((body_container, arrow_icon))

        def _toggle(e):
            body_container.visible = not body_container.visible
            arrow_icon.name = (
                ft.icons.KEYBOARD_ARROW_UP_ROUNDED
                if body_container.visible
                else ft.icons.KEYBOARD_ARROW_DOWN_ROUNDED
            )
            cualquiera_visible = any(b.visible for b, _ in self._semanas_bodies)
            self.btn_toggle_all.text = "Contraer Todas" if cualquiera_visible else "Desplegar Todas"
            self.btn_toggle_all.icon = (
                ft.icons.UNFOLD_LESS_ROUNDED
                if cualquiera_visible
                else ft.icons.UNFOLD_MORE_ROUNDED
            )
            self.safe_update()

        resumen_chips = [
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.TRENDING_UP_ROUNDED, size=13, color="teal800"),
                    ft.Text(f"Ventas: ${tot_ventas:,.0f}", size=11, weight="bold", color="teal800"),
                ], spacing=4),
                bgcolor="#f0fdf4", padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=6, border=ft.border.all(1, "#bbf7d0")
            ),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.SHOPPING_CART_ROUNDED, size=13, color="purple800"),
                    ft.Text(f"Compras: ${tot_compras:,.0f}", size=11, weight="bold", color="purple800"),
                ], spacing=4),
                bgcolor="#faf5ff", padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=6, border=ft.border.all(1, "#e9d5ff")
            ),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.SAVINGS_ROUNDED, size=13, color="green800"),
                    ft.Text(f"Recaudado: ${tot_recaudado:,.0f}", size=11, weight="bold", color="green800"),
                ], spacing=4),
                bgcolor="#ecfdf5", padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=6, border=ft.border.all(1, "#a7f3d0")
            ),
        ]

        header = ft.Container(
            content=ft.Row([
                # Izquierda: Título y rango de fechas
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.CALENDAR_VIEW_WEEK_ROUNDED, size=18, color=Config.COLOR_PRIMARY),
                        bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY),
                        padding=6,
                        border_radius=6
                    ),
                    ft.Text(titulo_semana, size=14, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Container(
                        content=ft.Text(rango_txt, size=11, weight="w600", color="grey700"),
                        bgcolor="#f1f5f9",
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        border_radius=12,
                        border=ft.border.all(1, "#e2e8f0")
                    ),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                
                # Centro: Chips de resumen financiero semanal
                ft.Row(resumen_chips, spacing=6, wrap=True),
                
                # Derecha: Conteo de días e ícono de acordeón
                ft.Row([
                    ft.Text(f"{len(cards_dias)} días", size=11, color="grey600", weight="w500"),
                    arrow_icon
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#ffffff",
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border_radius=10,
            border=ft.border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.03, "black")),
            on_click=_toggle,
            ink=True,
        )

        return ft.Container(
            content=ft.Column([
                header,
                body_container
            ], spacing=0),
            margin=ft.padding.only(bottom=4)
        )

    def _fetch_dias_worker(self) -> None:
        """
        Descarga los datos diarios del mes desde Supabase y renderiza
        la cuadrícula de tarjetas del Resumen Financiero por Día.
        """
        try:
            self._tab2_loading.visible = True
            self.safe_update()

            hoy_obj = (
                datetime.datetime.strptime(self.fecha_filtro_dash, "%Y-%m-%d").date()
                if self.fecha_filtro_dash
                else datetime.date.today()
            )
            mes_actual = hoy_obj.strftime("%Y-%m")
            dias_en_mes = calendar.monthrange(hoy_obj.year, hoy_obj.month)[1]

            # Calcular meta diaria
            try:
                ing_raw = self.val_ingresos.value.replace("$", "").replace(",", "").strip()
                ingresos = float(ing_raw) if ing_raw else 0.0
            except (ValueError, AttributeError):
                ingresos = 0.0

            try:
                proyeccion_raw = self.val_proyeccion_ventas.value.replace("$", "").replace(",", "").strip()
                proyeccion = float(proyeccion_raw) if proyeccion_raw else 0.0
            except (ValueError, AttributeError):
                proyeccion = 0.0

            meta_total_mes = ingresos + proyeccion
            meta_diaria = (meta_total_mes / dias_en_mes) if (dias_en_mes > 0 and meta_total_mes > 0) else ((proyeccion / dias_en_mes) if dias_en_mes > 0 else 0.0)

            # Costo de inventario global (snapshot actual)
            try:
                inv_raw = self.val_inventario.value.replace("$", "").replace(",", "").strip()
                costo_inv_global = float(inv_raw) if inv_raw else 0.0
            except (ValueError, AttributeError):
                costo_inv_global = 0.0

            # Descargar detalle diario del mes en paralelo
            detalle_mes = self.db.get_detalle_diario_mes(mes_actual)

            self._render_dias_grid(detalle_mes, hoy_obj, meta_diaria, costo_inv_global)
        except Exception as ex:
            import traceback
            traceback.print_exc()
        finally:
            self._tab2_loading.visible = False
            self.safe_update()

    def _build_card_dia_resumen(
        self,
        fecha_obj: datetime.date,
        nombre_dia: str,
        datos: dict,
        meta_diaria: float,
        costo_inv_global: float,
        es_futuro: bool = False,
    ) -> ft.Container:
        """Construye una tarjeta liviana y de alto rendimiento para cada día del mes."""
        v_total = float(datos.get("ventas_total") or 0.0)
        v_pos = float(datos.get("ventas_pos") or 0.0)
        v_rem = float(datos.get("ventas_remision") or 0.0)
        iva_ven = float(datos.get("iva_ventas") or 0.0)
        compras = float(datos.get("compras") or 0.0)
        iva_com = float(datos.get("iva_compras") or 0.0)
        recaudado = float(datos.get("recaudado") or 0.0)
        rec_efec = float(datos.get("recaudado_efectivo") or 0.0)
        rec_banco = float(datos.get("recaudado_banco") or 0.0)
        aj_ent_costo = float(datos.get("ajustes_entrada_costo") or 0.0)
        aj_sal_costo = float(datos.get("ajustes_salida_costo") or 0.0)

        tiene_datos = bool(datos and (v_total > 0 or compras > 0 or recaudado > 0 or aj_ent_costo > 0 or aj_sal_costo > 0))
        pct_meta = (v_total / meta_diaria * 100) if meta_diaria > 0 else 0.0

        if es_futuro:
            badge_txt, badge_bg, badge_col = "Pendiente", "#f1f5f9", "#94a3b8"
        elif not tiene_datos:
            badge_txt, badge_bg, badge_col = "Sin datos", "#f8fafc", "#94a3b8"
        elif pct_meta >= 100:
            badge_txt, badge_bg, badge_col = f"✓ {pct_meta:.0f}% meta", "#ecfdf5", "#059669"
        elif pct_meta >= 60:
            badge_txt, badge_bg, badge_col = f"◑ {pct_meta:.0f}% meta", "#eff6ff", "#2563eb"
        else:
            badge_txt, badge_bg, badge_col = f"↓ {pct_meta:.0f}% meta", "#fff7ed", "#c2410c"

        def _fmt(val: float) -> str:
            return f"${val:,.0f}"

        def _fila_métrica(label: str, valor: str, color_val: str = "black87", subtext: str = None) -> ft.Row:
            return ft.Row([
                ft.Text(label, size=11, color="grey700", expand=True),
                ft.Column([
                    ft.Text(valor, size=12, weight="bold", color=color_val, text_align=ft.TextAlign.RIGHT),
                    ft.Text(subtext, size=9, color="grey500", text_align=ft.TextAlign.RIGHT) if subtext else ft.Container()
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        es_finde = fecha_obj.weekday() >= 5
        hdr_bg = "#f0fdf4" if (tiene_datos and pct_meta >= 100) else ("#f0f9ff" if es_finde else "#f8fafc")

        return ft.Container(
            padding=12,
            bgcolor="white",
            border_radius=10,
            border=ft.border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.04, "black")),
            opacity=0.6 if es_futuro else 1.0,
            content=ft.Column([
                # Cabecera del día
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    bgcolor=hdr_bg,
                    border_radius=8,
                    content=ft.Row([
                        ft.Row([
                            ft.Text(f"{nombre_dia}", size=12, weight="bold", color="grey700"),
                            ft.Text(f"{fecha_obj.day:02d}", size=18, weight="bold", color="black87"),
                        ], spacing=6),
                        ft.Container(
                            content=ft.Text(badge_txt, size=10, weight="bold", color=badge_col),
                            bgcolor=badge_bg,
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            border_radius=12
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ),
                ft.Divider(height=4, color="transparent"),
                # Métricas simplificadas en tarjetas de 2 columnas
                _fila_métrica("Ventas Total:", _fmt(v_total), "teal800", f"POS: {_fmt(v_pos)} | Rem: {_fmt(v_rem)}" if v_total > 0 else None),
                _fila_métrica("Meta Diaria:", _fmt(meta_diaria), "blue800"),
                _fila_métrica("Compras del Día:", _fmt(compras), "purple800" if compras > 0 else "grey600"),
                _fila_métrica("Total Recaudado:", _fmt(recaudado), "green800", f"Efec: {_fmt(rec_efec)} | Banco: {_fmt(rec_banco)}" if recaudado > 0 else None),
                _fila_métrica("Impuestos (IVA):", f"Gen: {_fmt(iva_ven)}", "blue700", f"Pagado: {_fmt(iva_com)}"),
                _fila_métrica("Ajustes Inv.:", f"+{_fmt(aj_ent_costo)}", "green700", f"-{_fmt(aj_sal_costo)}" if aj_sal_costo > 0 else None),
            ], spacing=6)
        )


    def _build_kpi_card(self, title, value_control, icon, subtext_control=None, card_color=None):
        accent = card_color or Config.COLOR_ACCENT
        column_controls = [
            ft.Row([
                ft.Text(title.upper(), size=11, color=Config.COLOR_TEXT_MUTED, weight="w600", expand=True),
            ], spacing=5),
            value_control,
        ]
        if subtext_control:
            column_controls.append(subtext_control)
            
        value_control.size = 20
        value_control.weight = "bold"
        value_control.color = Config.COLOR_PRIMARY
            
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=accent, size=22),
                    bgcolor=ft.colors.with_opacity(0.12, accent),
                    padding=10,
                    border_radius=10
                ),
                ft.Column(column_controls, spacing=2, expand=True)
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=Config.COLOR_SURFACE,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            border_radius=12,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.colors.with_opacity(0.04, "black"), offset=ft.Offset(0, 2))
        )

    def _crear_card_dia(self, fecha_str: str, venta: float, compras: float, meta_diaria: float) -> ft.Container:
        """Crea una tarjeta estética para el seguimiento individual de ventas, meta y compras de cada día."""
        dt = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
        dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        nombre_dia = f"{dias_semana[dt.weekday()]} {dt.day:02d}"
        
        pct_meta = (venta / meta_diaria * 100) if meta_diaria > 0 else 0.0
        
        if pct_meta >= 100:
            badge_bg, badge_col = "#ecfdf5", "#059669"
            badge_txt = f"{pct_meta:.0f}% 🎯"
            border_col = "#a7f3d0"
        elif pct_meta >= 50:
            badge_bg, badge_col = "#eff6ff", "#2563eb"
            badge_txt = f"{pct_meta:.0f}%"
            border_col = "#bfdbfe"
        elif venta > 0:
            badge_bg, badge_col = "#fffbeb", "#d97706"
            badge_txt = f"{pct_meta:.0f}%"
            border_col = "#fde68a"
        else:
            badge_bg, badge_col = "#f1f5f9", "#64748b"
            badge_txt = "0%"
            border_col = "#e2e8f0"

        progreso_val = min(1.0, pct_meta / 100.0) if pct_meta > 0 else 0.0
        progreso_col = "#10b981" if pct_meta >= 100 else ("#3b82f6" if pct_meta >= 50 else ("#f59e0b" if venta > 0 else "#cbd5e1"))

        return ft.Container(
            width=175,
            padding=12,
            bgcolor="white",
            border_radius=10,
            border=ft.border.all(1, border_col),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.04, "black")),
            content=ft.Column([
                ft.Row([
                    ft.Text(nombre_dia, size=11, weight="bold", color="grey800"),
                    ft.Container(
                        content=ft.Text(badge_txt, size=10, weight="bold", color=badge_col),
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        bgcolor=badge_bg,
                        border_radius=6
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=6, color="transparent"),
                ft.Text(f"${venta:,.0f}", size=13, weight="bold", color="#1e293b" if venta > 0 else "grey500"),
                ft.ProgressBar(value=progreso_val, color=progreso_col, bgcolor="#f1f5f9", height=4),
                ft.Divider(height=4, color="transparent"),
                ft.Row([
                    ft.Text("Meta:", size=9, color="grey600"),
                    ft.Text(f"${meta_diaria:,.0f}", size=9, weight="bold", color="#7c3aed")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("Compras:", size=9, color="grey600"),
                    ft.Text(f"${compras:,.0f}", size=9, weight="w600", color="#0891b2" if compras > 0 else "grey500")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=3)
        )

    def _crear_card_categoria(self, cat_data):
        nombre = cat_data["categoria"]
        inv_costo = cat_data["inventario_costo"]
        ventas = cat_data["ventas_realizadas"]
        proy_venta = cat_data["proyeccion_venta"]
        cumplimiento = cat_data["cumplimiento_pct"]
        rotacion = cat_data["rotacion"]
        rendimiento = cat_data["rendimiento_pct"]
    
        # Color condicional para cumplimiento
        color_cumplimiento = "green700" if cumplimiento >= 50 else ("orange700" if cumplimiento > 0 else "grey")
        color_rendimiento = "green700" if rendimiento >= 0 else "red700"
    
        return ft.Container(
            content=ft.Column([
                # Cabecera Categoría
                ft.Row([
                    ft.Icon(ft.icons.CATEGORY_OUTLINED, size=16, color=Config.COLOR_PRIMARY),
                    ft.Text(nombre.upper(), weight="bold", size=12, color=Config.COLOR_PRIMARY, expand=True)
                ]),
                ft.Divider(height=1, color="#eeeeee"),
                
                # Fila 1: Inventario Costo vs Ventas
                ft.Row([
                    ft.Text("Inventario (Costo):", size=11, color="grey", expand=True),
                    ft.Text(f"${inv_costo:,.0f}", size=11, weight="bold")
                ]),
                ft.Row([
                    ft.Text("Ventas Realizadas:", size=11, color="grey", expand=True),
                    ft.Text(f"${ventas:,.0f}", size=11, weight="bold", color="green700")
                ]),
                
                # Fila 2: Proyección Venta vs % Cumplimiento
                ft.Row([
                    ft.Text("Proyección Venta:", size=11, color="grey", expand=True),
                    ft.Text(f"${proy_venta:,.0f}", size=11, weight="bold", color="blue700")
                ]),
                ft.Row([
                    ft.Text("% Cumplimiento:", size=11, color="grey", expand=True),
                    ft.Text(f"{cumplimiento:.1f}%", size=11, weight="bold", color=color_cumplimiento)
                ]),
                
                ft.Divider(height=1, color="#f0f0f0"),
                
                # Fila 3: Rotación y Rendimiento Real
                ft.Row([
                    ft.Text("Rotación:", size=11, color="grey"),
                    ft.Text(f"{rotacion:.2f}x", size=11, weight="bold"),
                    ft.Container(expand=True),
                    ft.Text("Rendimiento Real:", size=11, color="grey"),
                    ft.Text(f"{rendimiento:.1f}%", size=11, weight="bold", color=color_rendimiento)
                ])
            ], spacing=4),
            padding=12,
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.03, "black")),
            col={"sm": 12, "md": 6, "lg": 4}
        )

    def copiar_resumen_kpis(self, e):
        """
        Construye un texto formateado con todos los indicadores actuales
        del resumen financiero y lo guarda en el portapapeles del sistema.
        """
        periodo = self.lbl_periodo_dash.value.replace("Periodo: ", "").strip()
        fecha_hora = self.lbl_fecha_hora.value
        
        texto_copia = (
            f"📊 RESUMEN FINANCIERO Y OPERATIVO ({periodo.upper()})\n"
            f"📅 Generado el: {fecha_hora}\n"
            f"-----------------------------------------\n"
            f"💰 COSTOS E INVENTARIO:\n"
            f"  • Costo Inv. Actual: {self.val_inventario.value}\n"
            f"  • Total Compras (Mes): {self.val_compras.value}\n"
            f"  • Compras (Hoy): {self.val_compras_hoy.value}\n\n"
            f"📈 VENTAS E INGRESOS:\n"
            f"  • Total Ventas (Mes): {self.val_ingresos.value}\n"
            f"  • Ventas (Hoy): {self.val_ventas_hoy.value}\n"
            f"  • Margen Rentabilidad: {self.val_rentabilidad.value}\n\n"
            f"💳 CARTERA Y RECAUDOS:\n"
            f"  • Total Recaudado: {self.val_total_recaudado.value}\n"
            f"  • Saldo por Cobrar: {self.val_saldo_por_cobrar.value}\n\n"
            f"🎯 OBJETIVOS Y PROYECCIONES:\n"
            f"  • Proy. Ventas Stock: {self.val_proyeccion_ventas.value}\n"
            f"  • Proy. Rentabilidad: {self.val_proyeccion_rentabilidad.value}\n"
            f"  • Meta Venta Diaria: {self.val_meta_diaria.value}\n"
            f"  • Rotación Global: {self.val_rotacion.value}\n"
            f"-----------------------------------------"
        )

        if self.page:
            self.page.set_clipboard(texto_copia)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="white", size=18),
                    ft.Text("Resumen financiero copiado al portapapeles exitosamente", color="white")
                ]),
                bgcolor="green700"
            )
            self.page.snack_bar.open = True
            self.safe_update()
