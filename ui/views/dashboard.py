import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import datetime

class DashboardView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        
        self.lbl_periodo_dash = ft.Text("Periodo: ...", size=13, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_estado_dash = ft.Text("Estado: ...", size=13, weight="bold")
        self.lbl_fecha_hora = ft.Text("...", size=12, color="grey")

        self.fecha_filtro_dash = None
        self.date_picker_dash = ft.DatePicker(on_change=self.on_fecha_dash_change)

        self.btn_fecha_dash = ft.OutlinedButton(
            text=f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')}",
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
        self.val_inventario = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_compras = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_rotacion = ft.Text("N/D", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_compras_hoy = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        
        # SECCIÓN VENTAS
        self.val_ingresos = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_ventas_hoy = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_rentabilidad = ft.Text("0.0%", size=14, weight="bold", color="#2ecca0")
        self.val_proyeccion_ventas = ft.Text("$ 0", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_proyeccion_rentabilidad = ft.Text("0.0%", size=14, weight="bold", color="#2ecca0")
        
        self.kpi_costos_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Costo Inv. Actual", self.val_inventario, ft.icons.INVENTORY_2_ROUNDED, card_color=Config.COLOR_INFO), col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(content=self._build_kpi_card("Total Compras (Mes)", self.val_compras, ft.icons.SHOPPING_BAG_ROUNDED, card_color=Config.COLOR_ACCENT), col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(content=self._build_kpi_card("Compras (Hoy)", self.val_compras_hoy, ft.icons.PAYMENTS_ROUNDED, card_color=Config.COLOR_WARNING), col={"xs": 12, "sm": 6, "md": 4}),
        ], spacing=10, run_spacing=10)

        self.kpi_ventas_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Total Ventas (Mes)", self.val_ingresos, ft.icons.TRENDING_UP_ROUNDED, card_color=Config.COLOR_SUCCESS), col={"xs": 12, "sm": 6, "md": 6}),
            ft.Container(content=self._build_kpi_card("Ventas (Hoy)", self.val_ventas_hoy, ft.icons.MONETIZATION_ON_ROUNDED, card_color=Config.COLOR_SUCCESS), col={"xs": 12, "sm": 6, "md": 6}),
        ], spacing=10, run_spacing=10)
        
        # Paso 3: Crear la Barra de Métricas Secundarias
        self.val_meta_diaria = ft.Text("$ 0 / día", size=13, weight="bold", color="teal700")

        self.kpi_secundarios = ft.Container(
            content=ft.Row([
                ft.Text("Objetivo Comercial:", weight="bold", color=Config.COLOR_PRIMARY, size=12),
                ft.Text("Proy. Ventas Stock:", size=12, color="grey"), self.val_proyeccion_ventas,
                ft.Text(" | Proy. Rentabilidad:", size=12, color="grey"), self.val_proyeccion_rentabilidad,
                ft.Container(width=1, height=20, bgcolor="#d0d0d0", margin=ft.padding.symmetric(horizontal=8)),
                ft.Icon(ft.icons.FLAG, size=16, color="teal700"),
                ft.Text("Meta Venta Diaria:", weight="bold", size=12, color="grey"), self.val_meta_diaria,
                ft.Container(expand=True),
                ft.Text("Rotación Global:", size=12, color="grey"), self.val_rotacion,
            ], spacing=5, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor="#f0f4f8", border_radius=8, border=ft.border.all(1, "#d0d7de")
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
                    ft.Text("Ajustes de Salida (-)", size=16, weight="bold", color="red"),
                    ft.Divider(height=1),
                    self.col_ajustes_salida
                ]),
                bgcolor="white",
                padding=15,
                border_radius=8,
                expand=True,
                border=ft.border.all(1, "#f0f0f0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
            ),
            # Panel Entrada
            ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes de Entrada (+)", size=16, weight="bold", color="green"),
                    ft.Divider(height=1),
                    self.col_ajustes_entrada
                ]),
                bgcolor="white",
                padding=15,
                border_radius=8,
                expand=True,
                border=ft.border.all(1, "#f0f0f0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
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
            ft.Text("Resumen Financiero y Operativo", size=20, weight="bold", color=Config.COLOR_PRIMARY),
            self.btn_copiar_resumen
        ], tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Ensamblaje del Layout
        self.seccion_kpis = ft.Column([
            header_kpis_row,
            self.kpi_costos_row,
            self.kpi_ventas_row,
            self.kpi_secundarios
        ], spacing=10)

        # SECCIÓN RESUMEN DE IMPUESTOS
        self.val_iva_generado_mes = ft.Text("$ 0", size=22, weight="bold", color="blue700")
        self.val_iva_generado_hoy = ft.Text("$ 0", size=22, weight="bold", color="blue700")
        self.val_iva_pagado_mes = ft.Text("$ 0", size=22, weight="bold", color="teal700")
        self.val_iva_pagado_hoy = ft.Text("$ 0", size=22, weight="bold", color="teal700")

        header_impuestos_row = ft.Row([
            ft.Text("Resumen de Impuestos", size=20, weight="bold", color=Config.COLOR_PRIMARY),
        ], tight=True)

        self.kpi_iva_generado_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("IVA Generado (Mes)", self.val_iva_generado_mes, ft.icons.RECEIPT_LONG_ROUNDED, card_color=Config.COLOR_INFO), col={"xs": 12, "sm": 6}),
            ft.Container(content=self._build_kpi_card("IVA Generado (Hoy)", self.val_iva_generado_hoy, ft.icons.POINT_OF_SALE_ROUNDED, card_color=Config.COLOR_INFO), col={"xs": 12, "sm": 6}),
        ], spacing=10, run_spacing=10)

        self.kpi_iva_pagado_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("IVA Pagado (Mes)", self.val_iva_pagado_mes, ft.icons.SHOPPING_CART_CHECKOUT_ROUNDED, card_color=Config.COLOR_WARNING), col={"xs": 12, "sm": 6}),
            ft.Container(content=self._build_kpi_card("IVA Pagado (Hoy)", self.val_iva_pagado_hoy, ft.icons.SHOPPING_BAG_ROUNDED, card_color=Config.COLOR_WARNING), col={"xs": 12, "sm": 6}),
        ], spacing=10, run_spacing=10)

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
        # Series de datos (Grosor y puntas redondeadas)
        self.chart_ventas = ft.LineChartData(
            data_points=[], 
            color=ft.colors.BLUE_400,
            stroke_width=4, 
            curved=False,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE_400)
        )
        self.chart_compras = ft.LineChartData(
            data_points=[], 
            color="#2ecca0", 
            stroke_width=4, 
            curved=False,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, "#2ecca0")
        )
        
        # Contenedor de Categorías (Grilla Responsiva)
        self.categorias_row = ft.ResponsiveRow(columns=12, spacing=15, run_spacing=15)
        self.categorias_container = ft.Container(
            content=ft.Column([
                ft.Text("Rendimiento Detallado por Categoría", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.categorias_row
            ]),
            margin=ft.padding.only(top=10, bottom=10)
        )

        # Gráfico habilitando los ejes visuales
        self.line_chart = ft.LineChart(
            data_series=[self.chart_ventas, self.chart_compras],
            border=ft.border.all(1, "#f0f0f0"),
            min_y=0,
            min_x=0,
            expand=True,
            tooltip_bgcolor="white",
            left_axis=ft.ChartAxis(labels_size=50), 
            bottom_axis=ft.ChartAxis(labels_size=40), 
        )
        
        # Leyenda adaptada a fondo claro
        leyenda = ft.Row([
            ft.Row([ft.Container(width=12, height=12, bgcolor=ft.colors.BLUE_400, border_radius=6), ft.Text("Ingresos", size=12, weight="bold", color="black87")]),
            ft.Row([ft.Container(width=12, height=12, bgcolor="#2ecca0", border_radius=6), ft.Text("Costos", size=12, weight="bold", color="black87")]),
        ], spacing=30, alignment=ft.MainAxisAlignment.CENTER)
        
        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Text("Tendencia Diaria: Ingresos vs Costo de Ventas", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                leyenda,
                ft.Container(content=self.line_chart, height=320, margin=ft.padding.only(top=10))
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

        # 2. Main content Column
        self.content = ft.Column([
            self.progress_bar, 
            header_row,
            ft.Divider(height=10, color="transparent"),
            self.seccion_kpis,
            ft.Divider(height=10, color="transparent"),
            self.seccion_impuestos, # <-- Ubicación antes del impacto de ajustes
            ft.Divider(height=10, color="transparent"),
            self.seccion_ajustes,
            ft.Divider(height=10, color="transparent"),
            self.categorias_container,
            ft.Divider(height=10, color="transparent"),
            self.chart_container,
            ft.Divider(height=10, color="transparent"),
            self.tables_row,
            ft.Container(height=30) # Bottom padding
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def did_mount(self):
        if not hasattr(self, "overlay_added"):
            self.page.overlay.append(self.date_picker_dash)
            self.overlay_added = True
        self.load_data()

    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
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

    def _fetch_data_worker(self):
        """Ejecuta todas las llamadas HTTP síncronas sin congelar la ventana."""
        # Cargar contexto temporal
        mes_actual = datetime.date.today().strftime("%Y-%m")
        datos_cierre = self.db.obtener_estado_cierre(mes_actual)
        estado_periodo = datos_cierre.get('periodo', {}).get('estado', 'ABIERTO') if datos_cierre and datos_cierre.get('periodo') else 'ABIERTO'

        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        partes = mes_actual.split('-')
        nombre_mes = f"{meses[int(partes[1]) - 1]} {partes[0]}"

        self.lbl_periodo_dash.value = f"Periodo: {nombre_mes}"
        self.lbl_estado_dash.value = f"Estado: {estado_periodo}"

        colores_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
        self.lbl_estado_dash.color = colores_estado.get(estado_periodo, 'black')

        ahora = datetime.datetime.now()
        self.lbl_fecha_hora.value = ahora.strftime("%d/%m/%Y - %I:%M %p")

        # 1. Load KPIs
        kpis_cat = self.db.get_rendimiento_categorias_periodo(fecha_inicio=None, fecha_fin=self.fecha_filtro_dash)
        val_inv_real = sum([c["inventario_costo"] for c in kpis_cat])
        val_inv = val_inv_real
        self.val_inventario.value = f"$ {val_inv:,.0f}"
        
        res_cat = self.db.get_catalogo_summary(fecha_corte=self.fecha_filtro_dash)
        res_ven = self.db.get_ventas_summary(fecha_corte=self.fecha_filtro_dash)
        res_com = self.db.get_compras_summary(fecha_corte=self.fecha_filtro_dash)
        
        ingresos = float(res_ven.get('total_mes') or 0)
        compras = float(res_com.get('total_mes') or 0)
        
        ventas_hoy = float(res_ven.get('total_hoy') or 0)
        compras_hoy = float(res_com.get('total_hoy') or 0)
        
        self.val_ingresos.value = f"$ {ingresos:,.0f}"
        self.val_ventas_hoy.value = f"$ {ventas_hoy:,.0f}"
        self.val_compras.value = f"$ {compras:,.0f}"
        self.val_compras_hoy.value = f"$ {compras_hoy:,.0f}"

        # Extraer montos de IVA de Ventas y Compras
        iva_gen_mes = float(res_ven.get('iva_mes') or 0)
        iva_gen_hoy = float(res_ven.get('iva_hoy') or 0)
        iva_pag_mes = float(res_com.get('iva_mes') or 0)
        iva_pag_hoy = float(res_com.get('iva_hoy') or 0)

        self.val_iva_generado_mes.value = f"$ {iva_gen_mes:,.0f}"
        self.val_iva_generado_hoy.value = f"$ {iva_gen_hoy:,.0f}"
        self.val_iva_pagado_mes.value = f"$ {iva_pag_mes:,.0f}"
        self.val_iva_pagado_hoy.value = f"$ {iva_pag_hoy:,.0f}"
        
        rentabilidad = 0
        if ingresos > 0:
            rentabilidad = ((ingresos - compras) / ingresos) * 100
            
        self.val_rentabilidad.value = f"{rentabilidad:.1f}%"
        self.val_rentabilidad.color = "#2ecca0" if rentabilidad >= 0 else "#f26c61"
        
        # Basic rotacion (Ventas / Inventario)
        if val_inv > 0:
            rotacion_global = ingresos / val_inv
            self.val_rotacion.value = f"{rotacion_global:.2f}x"
        else:
            self.val_rotacion.value = "N/D"

        # Nuevos KPIs y Ajustes
        proyeccion_ventas = self.db.get_proyeccion_ventas(fecha_corte=self.fecha_filtro_dash)
        self.val_proyeccion_ventas.value = f"$ {proyeccion_ventas:,.0f}"
        
        proy_rent = 0
        if proyeccion_ventas > 0:
            proy_rent = ((proyeccion_ventas - val_inv) / proyeccion_ventas) * 100
        
        self.val_proyeccion_rentabilidad.value = f"{proy_rent:.1f}%"
        self.val_proyeccion_rentabilidad.color = "#2ecca0" if proy_rent >= 0 else "#f26c61"

        hoy_obj = datetime.datetime.strptime(self.fecha_filtro_dash, "%Y-%m-%d").date() if self.fecha_filtro_dash else datetime.date.today()
        if hoy_obj.month == 12:
            ultimo_dia_mes = datetime.date(hoy_obj.year, 12, 31).day
        else:
            ultimo_dia_mes = (datetime.date(hoy_obj.year, hoy_obj.month + 1, 1) - datetime.timedelta(days=1)).day
        dias_restantes = max(1, ultimo_dia_mes - hoy_obj.day + 1)
        restante_vender = max(0, proyeccion_ventas - ingresos)
        meta_diaria = restante_vender / dias_restantes
        self.val_meta_diaria.value = f"$ {meta_diaria:,.0f} / día"

        mes_actual = hoy_obj.strftime("%Y-%m")
        ajustes_bd = self.db.get_ajustes_mes(mes_actual, fecha_corte=self.fecha_filtro_dash)
        
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
        
        for fila in ajustes_bd:
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
                    # Fallback por tipo
                    if tipo_bd == "BAJA_VENCIMIENTO": k = "Vencimiento"
                    elif tipo_bd == "SALIDA_POR_FALTANTE": k = "Pérdida"
                    else: k = "Otro (Salida)"
                    tipos_salida[k]["conteo"] += conteo
                    tipos_salida[k]["cantidad"] += cant
                    tipos_salida[k]["costo"] += costo

        total_costo_entradas = sum([d["costo"] for d in tipos_entrada.values()])
        total_costo_salidas = sum([d["costo"] for d in tipos_salida.values()])
        
        total_cant_entradas = sum([d["cantidad"] for d in tipos_entrada.values()])
        total_cant_salidas = sum([d["cantidad"] for d in tipos_salida.values()])
        
        neto = total_costo_entradas - total_costo_salidas
        if neto > 0:
            self.lbl_neto_ajustes_header.value = f"NETO (POSITIVO): +${neto:,.0f}"
            self.lbl_neto_ajustes_header.color = "#2ecca0"
        elif neto < 0:
            self.lbl_neto_ajustes_header.value = f"NETO (NEGATIVO): -${abs(neto):,.0f}"
            self.lbl_neto_ajustes_header.color = "#f26c61"
        else:
            self.lbl_neto_ajustes_header.value = f"NETO: $0"
            self.lbl_neto_ajustes_header.color = "grey"

        # Limpiar columnas
        self.col_ajustes_entrada.controls.clear()
        self.col_ajustes_salida.controls.clear()

        # Render Entrada
        for key, datos in tipos_entrada.items():
            self.col_ajustes_entrada.controls.append(
                ft.Row([
                    ft.Text(f"{key} ({datos['conteo']})", size=12, color="black87", expand=True),
                    ft.Text(f"{datos['cantidad']:.0f} unds", size=12, color="grey"),
                    ft.Text(f"${datos['costo']:,.0f}", size=12, weight="bold", color="#2ecca0")
                ])
            )
            
        # Rellenar con espacio invisible para igualar simetría
        filas_faltantes = len(tipos_salida) - len(tipos_entrada)
        for _ in range(max(0, filas_faltantes)):
            self.col_ajustes_entrada.controls.append(
                ft.Container(height=18, content=ft.Text("")) # Fila transparente de relleno
            )
            
        self.col_ajustes_entrada.controls.append(ft.Divider(color="black12", height=10))
        self.col_ajustes_entrada.controls.append(
            ft.Row([
                ft.Text("TOTAL ENTRADAS", size=12, weight="bold"),
                ft.Text(f"{total_cant_entradas:.0f} unds", size=12, weight="bold", color="grey", expand=True, text_align=ft.TextAlign.CENTER),
                ft.Text(f"${total_costo_entradas:,.0f}", size=12, weight="bold", color="#2ecca0")
            ])
        )
        
        # Render Salida
        for key, datos in tipos_salida.items():
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
                ft.Text(f"{total_cant_salidas:.0f} unds", size=12, weight="bold", color="grey", expand=True, text_align=ft.TextAlign.CENTER),
                ft.Text(f"${total_costo_salidas:,.0f}", size=12, weight="bold", color="#f26c61")
            ])
        )

        # 2. Load Chart Data (Nativo Flet)
        try:
            tendencia = self.db.get_tendencia_diaria(fecha_corte=self.fecha_filtro_dash)
            dias_ordenados = sorted(tendencia.keys())
            max_val_y = 0
            
            pts_ventas = []
            pts_compras = []
            etiquetas_x = []
            
            for i, dia in enumerate(dias_ordenados):
                v = float(tendencia[dia]["ventas"])
                c = float(tendencia[dia]["compras"])
                if v > max_val_y: max_val_y = v
                if c > max_val_y: max_val_y = c
                # Poner la fecha SOLO en el tooltip de arriba (compras) para que Flet no la duplique al apilar
                tt_compras = f"{dia}\nCostos: ${c:,.0f}"
                tt_ventas = f"Ingresos: ${v:,.0f}"
                estilo_tt = ft.TextStyle(size=12, weight="bold", color="black87")
                
                pts_ventas.append(ft.LineChartDataPoint(i, v, tooltip=tt_ventas, tooltip_style=estilo_tt))
                pts_compras.append(ft.LineChartDataPoint(i, c, tooltip=tt_compras, tooltip_style=estilo_tt))
                
                # Densidad en Eje X: Mostrar todos los días con la fecha completa rotada
                etiquetas_x.append(
                    ft.ChartAxisLabel(
                        value=i, 
                        label=ft.Container(
                            content=ft.Text(dia, size=9, color="grey"),
                            padding=ft.padding.only(top=10),
                            rotate=-0.5
                        )
                    )
                )
                
            if not pts_ventas:
                pts_ventas = [ft.LineChartDataPoint(0, 0)]
                pts_compras = [ft.LineChartDataPoint(0, 0)]
                
            self.chart_ventas.data_points = pts_ventas
            self.chart_compras.data_points = pts_compras
            
            self.line_chart.max_x = len(dias_ordenados) - 1 if dias_ordenados else 0
            max_y_calc = max_val_y * 1.15 if max_val_y > 0 else 1000
            self.line_chart.max_y = max_y_calc
            
            def formato_moneda_corta(valor):
                if valor >= 1000000: return f"${valor/1000000:.1f}M"
                if valor >= 1000: return f"${valor/1000:.0f}k"
                return f"${valor:.0f}"
                
            # Mayor densidad en Y: 8 divisiones en lugar de 5
            intervalo_y = max_y_calc / 8 if max_y_calc > 0 else 100
            etiquetas_y = [
                ft.ChartAxisLabel(value=step * intervalo_y, label=ft.Text(formato_moneda_corta(step * intervalo_y), size=11, color="grey"))
                for step in range(9)
            ]
            
            self.line_chart.left_axis.labels = etiquetas_y
            self.line_chart.left_axis.labels_interval = intervalo_y
            self.line_chart.bottom_axis.labels = etiquetas_x
            self.line_chart.bottom_axis.labels_interval = 1
            
            # Cuadrícula visible completa con efecto punteado
            self.line_chart.horizontal_grid_lines = ft.ChartGridLines(
                interval=intervalo_y,
                color=ft.colors.with_opacity(0.05, "black"),
                width=1,
                dash_pattern=[4, 4]
            )
            self.line_chart.vertical_grid_lines = ft.ChartGridLines(
                interval=2, # Línea vertical sincronizada con el eje X
                color=ft.colors.with_opacity(0.05, "black"),
                width=1,
                dash_pattern=[4, 4]
            )
            
        except Exception as e:
            print(f"Error crítico construyendo Chart Flet: {e}")
        
        # 3. Load Tables Data (A prueba de fallos)
        try:
            top_ventas = self.db.get_top_ventas_mes(limit=10, fecha_corte=self.fecha_filtro_dash)
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
        except Exception as e:
            print(f"Error crítico en tabla ventas: {e}")
            
        try:
            top_costos = self.db.get_top_costo_inventario(limit=10, fecha_corte=self.fecha_filtro_dash)
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
        except Exception as e:
            print(f"Error crítico en tabla costos: {e}")
            
        try:
            self.categorias_row.controls.clear()
            for cat in kpis_cat:
                self.categorias_row.controls.append(self._crear_card_categoria(cat))
        except Exception as e:
            print(f"Error cargando KPIs por categoría: {e}")
            
        # Apagar indicador de carga al finalizar todo el trabajo
        self.progress_bar.visible = False
        
        self.safe_update()

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
            border=ft.border.all(1, Config.COLOR_BORDER),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.colors.with_opacity(0.04, "black"), offset=ft.Offset(0, 2))
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
