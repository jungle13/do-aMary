import flet as ft
import threading
import time
import json
import os
from pypdf import PdfReader, PdfWriter
from config import Config
from core.supabase_client import SupabaseClient
from core.gemini_parser import GeminiParser
from core.pdf_native_parser import detectar_y_parsear_pdf
from ui.components.cargas_consolidada import CargasConsolidadaView
import math
import datetime
from ui.components.autocomplete import CustomAutoComplete

class VentasView(ft.Container):
    def safe_update(self):
        """Actualiza la UI de forma segura solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
        self.expand = True
        
        self.db = SupabaseClient()
        self.ai_parser = GeminiParser()
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        self.parsed_data = None # Para guardar temporalmente los datos extraídos
        
        # --- ESTADO PANEL HISTÓRICO VENTAS ---
        from core.fecha_utils import get_hoy_local_str
        self.panel_abierto = False
        self.fecha_historial_activa = get_hoy_local_str()
        self.modo_agrupacion_ventas = "CATEGORIA" # "CATEGORIA" o "FACTURA"
        self.filtro_categoria_activo = None
        self.filtro_factura_activo = None

        self.date_picker_ventas_timeline = ft.DatePicker(on_change=self.on_date_ventas_timeline_change)
        # ---------------------------------------
        
        # Controles de Búsqueda
        def on_select_busqueda_ventas(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            if not texto or not texto.strip():
                self.search_input_text.value = ""
            elif "[" in texto and "]" in texto:
                self.search_input_text.value = texto.split("]")[0].replace("[", "").strip()
            elif "Factura: " in texto:
                self.search_input_text.value = texto.replace("Factura: ", "").strip()
            else:
                self.search_input_text.value = texto.strip()
            self.current_page = 1
            self.on_search(None)

        self.search_input_text = ft.TextField(visible=False)

        self.search_autocomplete = CustomAutoComplete(
            hint_text="Buscar por código, descripción o factura...",
            on_select=on_select_busqueda_ventas,
            text_size=12,
            expand=True
        )
        
        # Filtro de fecha
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )
        self.btn_date = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_OUTLINED,
            tooltip="Filtrar por Fecha",
            on_click=self.open_date_picker
        )
        
        self.btn_crear_manual = ft.ElevatedButton(
            text="Registrar Manual",
            icon=ft.icons.ADD_BOX,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=40,
            on_click=self.abrir_modal_crear_venta,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Dashboard Resumen Financiero Compacto y Detallado
        self.lbl_ventas_hist = ft.Text("$0", size=16, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_ventas_pos = ft.Text("$0", size=12, weight="bold", color="blue700")
        self.lbl_ventas_remi = ft.Text("$0", size=12, weight="bold", color="teal800")
        self.lbl_ventas_hoy = ft.Text("$0", size=15, weight="bold", color="green700")
        self.lbl_ventas_hoy_sub = ft.Text("POS: $0  •  Remi: $0", size=10, color="grey600")
        self.lbl_iva_hist = ft.Text("$0", size=15, weight="bold", color="purple700")
        self.lbl_iva_hoy_sub = ft.Text("Hoy: $0", size=10, color="grey600")
        
        self.summary_container = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=10,
            border=ft.border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.colors.with_opacity(0.04, "black")),
            content=ft.Row([
                # Bloque 1: TOTAL VENTAS ACUMULADO
                ft.Container(
                    expand=2,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.POINT_OF_SALE, size=15, color=Config.COLOR_PRIMARY),
                            ft.Text("TOTAL VENTAS", size=10, weight="bold", color="grey700")
                        ], spacing=4),
                        self.lbl_ventas_hist,
                        ft.Text("Acumulado en Sistema", size=10, color="grey500")
                    ], spacing=2)
                ),
                ft.VerticalDivider(width=1, color="#e2e8f0"),
                # Bloque 2: DESGLOSE POR CANAL
                ft.Container(
                    expand=3,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.PIE_CHART_OUTLINE, size=15, color="blue700"),
                            ft.Text("VENTAS POR CANAL", size=10, weight="bold", color="grey700")
                        ], spacing=4),
                        ft.Row([
                            ft.Container(
                                content=ft.Row([
                                    ft.Text("🧾 POS:", size=10, color="grey700", weight="w500"),
                                    self.lbl_ventas_pos
                                ], spacing=3),
                                bgcolor="#eff6ff", padding=ft.padding.symmetric(horizontal=6, vertical=3), border_radius=5
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Text("📋 Remi:", size=10, color="grey700", weight="w500"),
                                    self.lbl_ventas_remi
                                ], spacing=3),
                                bgcolor="#f0fdf4", padding=ft.padding.symmetric(horizontal=6, vertical=3), border_radius=5
                            )
                        ], spacing=6)
                    ], spacing=3)
                ),
                ft.VerticalDivider(width=1, color="#e2e8f0"),
                # Bloque 3: VENTAS DE HOY
                ft.Container(
                    expand=2,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.TODAY, size=15, color="green700"),
                            ft.Text("VENTAS DE HOY", size=10, weight="bold", color="grey700")
                        ], spacing=4),
                        self.lbl_ventas_hoy,
                        self.lbl_ventas_hoy_sub
                    ], spacing=2)
                ),
                ft.VerticalDivider(width=1, color="#e2e8f0"),
                # Bloque 4: IVA RECAUDADO
                ft.Container(
                    expand=2,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, size=15, color="purple700"),
                            ft.Text("IVA TOTAL", size=10, weight="bold", color="grey700")
                        ], spacing=4),
                        self.lbl_iva_hist,
                        self.lbl_iva_hoy_sub
                    ], spacing=2)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )
        
        self.btn_agregar = ft.ElevatedButton(
            text="Agregar Venta",
            icon=ft.icons.ADD,
            bgcolor=Config.COLOR_SECONDARY,
            color="white",
            height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # Filtro de Tipo de Documento para la tabla principal
        self.drop_filtro_tipo_doc_tabla = ft.Dropdown(
            options=[
                ft.dropdown.Option("TODOS", "Todos los Tipos"),
                ft.dropdown.Option("Factura POS", "Facturas POS"),
                ft.dropdown.Option("Remisión", "Remisiones")
            ],
            value="TODOS",
            label="Tipo Doc.",
            dense=True,
            width=150,
            border_radius=8,
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            height=38,
            on_change=lambda e: self.on_filtro_tipo_doc_change(e)
        )

        # File Picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        
        # Diálogo de Carga
        self.lbl_loading_text = ft.Text("Preparando archivo...", text_align=ft.TextAlign.CENTER)
        self.dlg_loading = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesando Documento PDF (Motor Local)"),
            content=ft.Column([
                ft.ProgressRing(),
                self.lbl_loading_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
        )
        
        # Diálogo de Procesamiento Nativo
        self.dlg_procesando_pdf = ft.AlertDialog(
            modal=True,
            content=ft.Row([
                ft.ProgressRing(),
                ft.Text("Extrayendo ventas con motor local...")
            ], alignment=ft.MainAxisAlignment.CENTER)
        )
        
        # Diálogo de Confirmación
        self.dlg_confirm = ft.AlertDialog(modal=True)
        
        # Tabla de Datos Optimizada (Sin scroll horizontal y con acciones siempre a la vista)
        self.data_table = ft.DataTable(
            data_row_min_height=36,
            data_row_max_height=42,
            heading_row_height=38,
            columns=[
                ft.DataColumn(ft.Text("Documento & Fecha", weight="bold", size=12)),
                ft.DataColumn(ft.Container(content=ft.Text("Insumo / Descripción", weight="bold", size=12), width=320)),
                ft.DataColumn(ft.Text("Cant.", weight="bold", size=12), numeric=True),
                ft.DataColumn(ft.Text("Subtotal", weight="bold", size=12), numeric=True),
                ft.DataColumn(ft.Text("IVA", weight="bold", size=12), numeric=True),
                ft.DataColumn(ft.Text("Total", weight="bold", size=12), numeric=True),
                ft.DataColumn(ft.Text("Acciones", weight="bold", size=12)),
            ],
            rows=[],
            heading_row_color="#f8fafc",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, "#f1f5f9"),
            horizontal_lines=ft.border.BorderSide(1, "#e2e8f0"),
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, tooltip="Página Anterior", on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, tooltip="Página Siguiente", on_click=self.on_next_page, disabled=True)
        
        # Inicializar memoria local
        self.cargas_file = "cargas_locales.json"
        self.cargas_data = {}
        self._load_cargas()
        
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        # --- FILTROS TAB GESTIÓN DE CARGAS ---
        self.fecha_filtro_cargas = None
        self.date_picker_filtro_cargas = ft.DatePicker(on_change=self.on_date_filtro_cargas_change)
        
        self.btn_filtro_fecha_cargas = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_OUTLINED,
            tooltip="Filtrar por Fecha",
            on_click=lambda e: self.date_picker_filtro_cargas.pick_date()
        )
        self.btn_clear_filtro_cargas = ft.IconButton(
            icon=ft.icons.CLEAR, tooltip="Limpiar Fecha",
            on_click=self.clear_filtro_fecha_cargas, visible=False, icon_color="red"
        )
        
        # Dropdowns con height ajustado y content_padding para evitar que el label se corte
        self.drop_filtro_tipo_cargas = ft.Dropdown(
            options=[ft.dropdown.Option("Todas"), ft.dropdown.Option("Remisiones"), ft.dropdown.Option("Ventas POS")],
            value="Todas", label="Tipo", dense=True, width=160, border_radius=8, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8), height=38,
            on_change=lambda e: self._render_tabla_cargas()
        )
        self.drop_filtro_estado_cargas = ft.Dropdown(
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("EXTRAIDO_POR_AGENTE"),
                ft.dropdown.Option("Nuevo"),
                ft.dropdown.Option("Procesado con éxito"),
                ft.dropdown.Option("Falló"),
                ft.dropdown.Option("Guardado"),
                ft.dropdown.Option("Sobreescrito")
            ],
            value="Todos", label="Estado", dense=True, width=190, border_radius=8, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8), height=38,
            on_change=lambda e: self._render_tabla_cargas()
        )

        # --- NUEVA TABLA DE GESTIÓN DE CARGAS ---
        self.table_cargas = ft.DataTable(
            data_row_min_height=40,
            data_row_max_height=40,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("ID", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Página", weight="bold")),
                ft.DataColumn(ft.Text("Tipo de Documento", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )

        # --- PREPARACIÓN DE LAS PESTAÑAS (TABS) ---

        # 1. Contenido del Tab 1: Registro Ventas
        
        row_filtros_ventas = ft.Row([
            self.search_autocomplete,
            self.drop_filtro_tipo_doc_tabla,
            self.btn_date,
            self.btn_clear_date,
            ft.Container(expand=True),
            self.btn_crear_manual
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        contenedor_tabla_ventas = ft.Container(
            content=ft.Row([ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )

        footer_paginacion = ft.Container(
            content=ft.Row([self.lbl_total, ft.Container(expand=True), self.btn_prev, self.lbl_page_info, self.btn_next], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=10)
        )

        layout_tab_ventas = ft.Container(
            content=ft.Column([row_filtros_ventas, contenedor_tabla_ventas, footer_paginacion], expand=True, spacing=10),
            padding=ft.padding.only(top=15),
            expand=True
        )

        self.btn_extraer_todo = ft.ElevatedButton(
            text="Extraer Todo",
            icon=ft.icons.AUTO_MODE,
            bgcolor="purple700",
            color="white",
            height=45,
            on_click=self.on_extraer_todo_masivo,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        # 2. Contenido del Tab 2: Gestión de Cargas Consolidada
        self.vista_cargas_consolidada = CargasConsolidadaView(
            modulo="VENTAS",
            on_upload_click=self.on_agregar_click,
            on_save_callback=self._guardar_ventas_lote,
            on_discard_callback=lambda: self.load_data()
        )

        # 3. Definición del Contenedor de Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Registro Ventas", icon=ft.icons.LIST_ALT, content=layout_tab_ventas),
                ft.Tab(text="Gestión de Cargas", icon=ft.icons.DRIVE_FOLDER_UPLOAD, content=self.vista_cargas_consolidada)
            ],
            expand=True
        )

        # --- DISEÑO DEL PANEL HISTÓRICO ---
        self.lbl_tot_ventas_panel = ft.Text("$0 COP", size=14, weight="bold", color="blue800")
        self.lbl_cant_ventas_panel = ft.Text("0 unds", size=10, color="grey")
        self.panel_page = 1
        self.panel_page_size = 10
        self.panel_total_pages = 1
        self.panel_items_cache = []

        kpi_ventas_panel = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.POINT_OF_SALE, color="blue700", size=20),
                ft.Column([
                    ft.Text("TOTAL VENTAS FILTRO", size=9, weight="bold", color="grey"),
                    self.lbl_tot_ventas_panel
                ], spacing=0, expand=True),
                self.lbl_cant_ventas_panel
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, bgcolor="#e8f0fe", border_radius=8, border=ft.border.all(1, "#d2e3fc")
        )

        self.segment_agrupacion_ventas = ft.SegmentedButton(
            segments=[
                ft.Segment(value="CATEGORIA", label=ft.Text("Categoría", size=10)),
                ft.Segment(value="FACTURA", label=ft.Text("Factura", size=10)),
            ],
            selected={"CATEGORIA"},
            on_change=self.on_agrupacion_ventas_change,
            show_selected_icon=False
        )

        self.drop_filtro_panel_tipo = ft.Dropdown(
            options=[
                ft.dropdown.Option("TODOS", "Todos"),
                ft.dropdown.Option("Factura POS", "POS"),
                ft.dropdown.Option("Remisión", "Remi")
            ],
            value="TODOS",
            label="Tipo",
            dense=True,
            width=110,
            border_radius=8,
            text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            height=32,
            on_change=lambda e: self.cargar_historial_panel()
        )

        self.btn_fecha_ventas_panel = ft.OutlinedButton(
            self.fecha_historial_activa or "Ver Todo",
            icon=ft.icons.CALENDAR_TODAY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=4),
            height=30,
            on_click=lambda e: self.date_picker_ventas_timeline.pick_date()
        )

        self.btn_ver_todo_panel = ft.TextButton(
            "Ver Todo",
            icon=ft.icons.ALL_INCLUSIVE,
            style=ft.ButtonStyle(padding=2),
            height=28,
            on_click=self.limpiar_fecha_panel
        )

        self.panel_ventas_list = ft.ListView(expand=True, spacing=6)

        # Controles de paginación del panel
        self.lbl_panel_page_info = ft.Text("Pág 1/1", size=10, color="grey700")
        self.btn_panel_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, icon_size=16, tooltip="Anterior", on_click=self.on_panel_prev_page, disabled=True)
        self.btn_panel_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, icon_size=16, tooltip="Siguiente", on_click=self.on_panel_next_page, disabled=True)

        footer_panel = ft.Row([
            self.btn_ver_todo_panel,
            ft.Container(expand=True),
            self.btn_panel_prev,
            self.lbl_panel_page_info,
            self.btn_panel_next
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Botón para copiar histórico de ventas
        self.btn_copiar_ventas_panel = ft.IconButton(
            icon=ft.icons.COPY_ROUNDED,
            icon_size=16,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Copiar Histórico de Ventas al Portapapeles",
            on_click=self.copiar_historial_ventas
        )

        self.right_panel = ft.Container(
            width=0, visible=False, bgcolor="white", border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.05, "black")),
            animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
            content=ft.Column([
                # Cabecera Panel con el botón de copiar
                ft.Container(
                    content=ft.Row([
                        ft.Text("Histórico de Ventas", weight="bold", size=13, color=Config.COLOR_PRIMARY, expand=True),
                        self.btn_copiar_ventas_panel,
                        self.btn_fecha_ventas_panel,
                        ft.IconButton(ft.icons.CLOSE, icon_size=16, on_click=self.toggle_right_panel)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=10, bgcolor="#f4f6f8", border_radius=ft.border_radius.only(top_left=8, top_right=8)
                ),
                ft.Container(content=kpi_ventas_panel, padding=ft.padding.symmetric(horizontal=10)),
                ft.Container(
                    content=ft.Row([
                        self.segment_agrupacion_ventas,
                        self.drop_filtro_panel_tipo
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10)
                ),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Container(content=self.panel_ventas_list, expand=True, padding=10),
                ft.Container(content=footer_panel, padding=ft.padding.symmetric(horizontal=10, vertical=4), bgcolor="#f8fafc")
            ], spacing=6)
        )

        self.filtro_badge_ventas = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.FILTER_ALT, size=14, color="white"),
                ft.Text("Filtro Activo", color="white", weight="bold", size=11),
                ft.IconButton(
                    ft.icons.CLOSE, icon_size=14, icon_color="white",
                    on_click=self.limpiar_filtro_ventas,
                    style=ft.ButtonStyle(padding=0), width=20, height=20
                )
            ], tight=True),
            bgcolor="blue700", padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=12, visible=False
        )

        self.btn_toggle_panel = ft.IconButton(
            icon=ft.icons.HISTORY_TOGGLE_OFF,
            tooltip="Ver Histórico de Ventas del Día",
            on_click=self.toggle_right_panel
        )

        # --- ENSAMBLAJE FINAL DE LA VISTA ---
        self.lbl_titulo = ft.Text("Registro de Ventas (Salidas)", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        main_column = ft.Column([
            self.progress_bar,
            ft.Row([self.lbl_titulo, self.filtro_badge_ventas, ft.Container(expand=True), self.btn_toggle_panel, self.btn_fullscreen]),
            self.summary_container,
            self.tabs
        ], expand=True, spacing=10)

        self.content = ft.Row([
            main_column,
            self.right_panel
        ], expand=True, spacing=10)

        # Llamar al método de renderizado en lugar del mock
        self._render_tabla_cargas()

    def toggle_right_panel(self, e):
        self.panel_abierto = not self.panel_abierto
        self.right_panel.width = 380 if self.panel_abierto else 0
        self.right_panel.visible = self.panel_abierto
        self.right_panel.padding = 0
        self.btn_toggle_panel.icon = ft.icons.HISTORY if self.panel_abierto else ft.icons.HISTORY_TOGGLE_OFF
        if self.panel_abierto:
            self.cargar_historial_panel()
        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def on_date_ventas_timeline_change(self, e):
        if self.date_picker_ventas_timeline.value:
            self.fecha_historial_activa = self.date_picker_ventas_timeline.value.strftime("%Y-%m-%d")
            self.btn_fecha_ventas_panel.text = self.fecha_historial_activa
            self.panel_page = 1
            self.cargar_historial_panel()

    def limpiar_fecha_panel(self, e):
        self.fecha_historial_activa = None
        self.date_picker_ventas_timeline.value = None
        self.btn_fecha_ventas_panel.text = "Ver Todo"
        self.panel_page = 1
        self.cargar_historial_panel()

    def on_panel_prev_page(self, e):
        if self.panel_page > 1:
            self.panel_page -= 1
            self._render_panel_items()

    def on_panel_next_page(self, e):
        if self.panel_page < self.panel_total_pages:
            self.panel_page += 1
            self._render_panel_items()

    def on_agrupacion_ventas_change(self, e):
        if e.control.selected:
            self.modo_agrupacion_ventas = list(e.control.selected)[0]
            self.panel_page = 1
            self.cargar_historial_panel()

    def cargar_historial_panel(self):
        if not self.page: return

        def worker():
            tipo_filtro = getattr(self.drop_filtro_panel_tipo, "value", "TODOS")
            items = self.db.get_historial_ventas_dia(
                fecha_dia=self.fecha_historial_activa,
                agrupar_por=self.modo_agrupacion_ventas,
                tipo_documento=tipo_filtro
            )

            self.panel_items_cache = items
            self.panel_total_pages = max(1, math.ceil(len(items) / self.panel_page_size))
            if self.panel_page > self.panel_total_pages:
                self.panel_page = 1

            tot_pesos = sum([item["total"] for item in items])

            self.lbl_tot_ventas_panel.value = f"${tot_pesos:,.0f} COP"
            self.lbl_cant_ventas_panel.value = f"{len(items)} reg."

            self._render_panel_items()

        threading.Thread(target=worker, daemon=True).start()

    def _render_panel_items(self):
        self.panel_ventas_list.controls.clear()
        start = (self.panel_page - 1) * self.panel_page_size
        end = start + self.panel_page_size
        page_items = self.panel_items_cache[start:end]

        for item in page_items:
            self.panel_ventas_list.controls.append(self._crear_card_item_ventas(item))

        if not self.panel_items_cache:
            self.panel_ventas_list.controls.append(
                ft.Container(
                    content=ft.Text("Sin ventas registradas para este filtro.", size=11, color="grey"),
                    padding=20, alignment=ft.alignment.center
                )
            )

        self.lbl_panel_page_info.value = f"Pág {self.panel_page}/{self.panel_total_pages}"
        self.btn_panel_prev.disabled = (self.panel_page <= 1)
        self.btn_panel_next.disabled = (self.panel_page >= self.panel_total_pages)

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def _crear_card_item_ventas(self, item):
        tipo = item["tipo"]

        if tipo == "CATEGORIA_RESUMEN":
            badge_txt = f"CAT: {item['categoria']}"
            badge_bg, badge_col = "#e8f0fe", "blue800"
            sub_txt = f"{item['items_count']} ítems vendidos"
            icon_mat = ft.icons.CATEGORY
        else:
            # FACTURA_VENTA
            subtipo = item.get("subtipo", "POS")
            is_pos = "POS" in subtipo.upper()
            badge_txt = f"#{item['factura']} ({'POS' if is_pos else 'REMI'})"
            badge_bg, badge_col = ("#eff6ff", "blue800") if is_pos else ("#f0fdf4", "teal800")
            sub_txt = f"Venta {subtipo}"
            icon_mat = ft.icons.RECEIPT_LONG

        badge = ft.Container(
            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_col, no_wrap=True),
            padding=ft.padding.symmetric(horizontal=6, vertical=2), bgcolor=badge_bg, border_radius=6
        )

        card = ft.Container(
            content=ft.Row([
                ft.Icon(icon_mat, size=16, color=Config.COLOR_PRIMARY),
                ft.Column([
                    badge,
                    ft.Text(sub_txt, size=10, color="grey700", no_wrap=True),
                ], expand=True, spacing=2),
                ft.Column([
                    ft.Text(f"${item['total']:,.0f}", size=11, weight="bold", color="teal800"),
                    ft.Text(f"{item['unidades']:g} unds", size=9, color="grey", text_align=ft.TextAlign.RIGHT)
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=1)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=8,
            border_radius=6,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#e2e8f0"),
            on_click=lambda e, i=item: self.aplicar_filtro_cruzado_ventas(i),
            ink=True
        )
        return card

    def aplicar_filtro_cruzado_ventas(self, item):
        tipo = item["tipo"]
        self.progress_bar.visible = True
        if hasattr(self, "safe_update"):
            self.safe_update()
        else:
            self.page.update()

        if tipo == "CATEGORIA_RESUMEN":
            self.filtro_categoria_activo = item["categoria"]
            self.filtro_factura_activo = None
            desc = f"Categoría: {item['categoria']}"
        else:
            self.filtro_factura_activo = item["ref"]
            self.filtro_categoria_activo = None
            desc = f"Factura/Doc: {item['factura']}"

        lbl = self.filtro_badge_ventas.content.controls[1]
        lbl.value = desc
        self.filtro_badge_ventas.visible = True

        self.current_page = 1
        self.load_data()

    def limpiar_filtro_ventas(self, e=None):
        self.filtro_categoria_activo = None
        self.filtro_factura_activo = None
        self.filtro_badge_ventas.visible = False
        self.current_page = 1
        self.load_data()

    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def did_mount(self):
        if hasattr(self, "date_picker_ventas_timeline") and self.date_picker_ventas_timeline not in self.page.overlay:
            self.page.overlay.append(self.date_picker_ventas_timeline)
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        if hasattr(self, "dlg_loading") and self.dlg_loading not in self.page.overlay:
            self.page.overlay.append(self.dlg_loading)
        if hasattr(self, "dlg_confirm") and self.dlg_confirm not in self.page.overlay:
            self.page.overlay.append(self.dlg_confirm)
        if hasattr(self, "dlg_procesando_pdf") and self.dlg_procesando_pdf not in self.page.overlay:
            self.page.overlay.append(self.dlg_procesando_pdf)
        if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
            
        self.page.update()
        self.load_summary()
        self.cargar_sugerencias_ventas()
        self.load_data()

    def cargar_sugerencias_ventas(self):
        ventas, _ = self.db.get_ventas(page=1, page_size=1000)
        sug_set = set()
        for v in ventas:
            cat_info = v.get("catalogo_insumos") or {}
            cod = v.get("codigo_insumo")
            nom = cat_info.get("nombre")
            fact = v.get("factura_no")
            
            if cod and nom: sug_set.add(f"[{cod}] {nom}")
            if fact and fact != "N/A": sug_set.add(f"Factura: {fact}")

        self.search_autocomplete.suggestions = [
            {"key": str(idx), "value": val}
            for idx, val in enumerate(sorted(sug_set))
        ]
        if hasattr(self, 'safe_update'):
            self.safe_update()
        elif self.page:
            self.page.update()

    def _abrir_modal_metadatos(self, e):
        self.on_agregar_click(e)

    def _cerrar_modal_metadatos(self, e=None):
        pass

    def on_date_filtro_cargas_change(self, e):
        if self.date_picker_filtro_cargas.value:
            self.fecha_filtro_cargas = self.date_picker_filtro_cargas.value.strftime("%Y-%m-%d")
            self.btn_filtro_fecha_cargas.tooltip = f"Fecha: {self.fecha_filtro_cargas}"
            self.btn_filtro_fecha_cargas.icon_color = "blue"
            self.btn_clear_filtro_cargas.visible = True
            if self.page:
                self.page.update()
            self._render_tabla_cargas()

    def clear_filtro_fecha_cargas(self, e):
        self.fecha_filtro_cargas = None
        self.date_picker_filtro_cargas.value = None
        self.btn_filtro_fecha_cargas.tooltip = "Filtrar por Fecha"
        self.btn_filtro_fecha_cargas.icon_color = None
        self.btn_clear_filtro_cargas.visible = False
        if self.page:
            self.page.update()
        self._render_tabla_cargas()

    def on_date_cargas_change(self, e):
        if self.date_picker_cargas.value:
            self.fecha_carga_actual = self.date_picker_cargas.value.strftime("%Y-%m-%d")
            self.fecha_carga_btn.text = self.fecha_carga_actual
            if self.page:
                self.page.update()

    def _load_cargas(self):
        if os.path.exists(self.cargas_file):
            try:
                with open(self.cargas_file, "r", encoding="utf-8") as f:
                    self.cargas_data = json.load(f)
            except Exception:
                self.cargas_data = {}

    def _save_cargas(self):
        with open(self.cargas_file, "w", encoding="utf-8") as f:
            json.dump(self.cargas_data, f, indent=4)

    def _render_tabla_cargas(self):
        if not hasattr(self, 'table_cargas'): return
        self.table_cargas.rows.clear()
        
        # Aplanar diccionario
        lista_cargas = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                lista_cargas.append(data)
                
        # Ordenar por ID descendente (más nuevos arriba)
        lista_cargas.sort(key=lambda x: x["id"], reverse=True)
        
        for data in lista_cargas:
            # Descartar registros que no correspondan a Ventas (ej. Compras)
            if str(data.get("tipo", "")).upper() in ["COMPRA", "COMPRAS"]:
                continue

            # --- Filtrado Visual ---
            if self.fecha_filtro_cargas and data.get("fecha") != self.fecha_filtro_cargas:
                continue
                
            if self.drop_filtro_tipo_cargas.value != "Todas":
                # Traducir los nombres de los filtros a los nombres internos guardados
                tipo_bd = "Remisión" if self.drop_filtro_tipo_cargas.value == "Remisiones" else "Factura POS"
                if data.get("tipo") != tipo_bd:
                    continue
                    
            if self.drop_filtro_estado_cargas.value != "Todos" and data.get("estado") != self.drop_filtro_estado_cargas.value:
                continue
            # -----------------------
            
            id_carga = data["id"]
            nombre = f"Página No. {data['pagina']} ({data['fecha']})"
            tipo = data["tipo"]
            estado = data["estado"]
            
            txt_crono = ft.Text("⏱️ 20s", color="red", weight="bold", visible=False)
            
            if estado == "EXTRAIDO_POR_AGENTE":
                texto_btn = "Ver y Guardar"
                color_btn = Config.COLOR_ACCENT
                icon_btn = ft.icons.FACT_CHECK_OUTLINED
            elif estado in ["Nuevo", "Falló", "Sobreescrito"]:
                texto_btn = "Extraer Datos"
                color_btn = Config.COLOR_PRIMARY
                icon_btn = ft.icons.DOCUMENT_SCANNER
            else:
                texto_btn = "Ver"
                color_btn = "grey"
                icon_btn = ft.icons.VISIBILITY
            
            btn_accion = ft.ElevatedButton(
                text=texto_btn,
                icon=icon_btn,
                bgcolor=color_btn,
                color="white",
                height=30,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                on_click=lambda e, d=data, txt=txt_crono: self.on_accion_carga(e, d, txt)
            )
            
            btn_eliminar = ft.IconButton(
                icon=ft.icons.DELETE_OUTLINED,
                icon_color="red700",
                icon_size=18,
                tooltip="Eliminar Carga",
                on_click=lambda e, d=data: self.on_eliminar_carga(d)
            )
            acciones_row = ft.Row([btn_accion, txt_crono, btn_eliminar], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            color_estado = "black"
            if estado == "EXTRAIDO_POR_AGENTE": color_estado = "#7C3AED"
            elif estado == "Procesado con éxito": color_estado = "green"
            elif estado == "Falló": color_estado = "red"
            elif estado == "Guardado": color_estado = "blue"
            elif estado == "Sobreescrito": color_estado = "orange"
            
            self.table_cargas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(id_carga))),
                        ft.DataCell(ft.Text(nombre, weight="bold")),
                        ft.DataCell(ft.Text(tipo)),
                        ft.DataCell(ft.Text(estado, color=color_estado, weight="bold")),
                        ft.DataCell(acciones_row),
                    ]
                )
            )
            
        if self.page:
            self.page.update()

    def on_eliminar_carga(self, data):
        estado = data.get("estado")
        id_carga = data["id"]
        
        # Encontrar grupo_key y num_pag en cargas_data
        grupo_key = None
        num_pag = str(data["pagina"])
        for g_k, pags in self.cargas_data.items():
            if num_pag in pags and pags[num_pag].get("id") == id_carga:
                grupo_key = g_k
                break
                
        if not grupo_key:
            grupo_key = f"{data['fecha']}_{data.get('tipo', 'Remisión')}"

        if estado == "Guardado":
            datos_ext = data.get("datos_extraidos", [])
            filas_resumen = []
            lista_facturas = []
            cant_tot = 0.0
            venta_tot = 0.0

            for inv in datos_ext:
                fact = inv.get("numero_factura") or ""
                if fact and fact not in lista_facturas:
                    lista_facturas.append(fact)
                    
                for p in inv.get("productos", []):
                    cod = p.get("codigo_item", "")
                    nom = getattr(self, 'nombres_insumos', {}).get(cod, f"Insumo [{cod}]")
                    cant = float(p.get("cantidad") or 0)
                    tot = float(p.get("costo_total") or p.get("subtotal") or 0)
                    
                    cant_tot += cant
                    venta_tot += tot
                    
                    filas_resumen.append(
                        ft.Row([
                            ft.Text(f"• [{cod}] {nom[:22]}", size=11, expand=True, weight="bold"),
                            ft.Text(f"{cant:g} unds", size=11, color="grey"),
                            ft.Text(f"${tot:,.0f}", size=11, weight="bold", color="blue700")
                        ])
                    )

            if not filas_resumen:
                filas_resumen.append(ft.Text("Sin detalle de insumos registrado.", size=11, color="grey"))

            def confirmar_eliminar_guardado(e):
                dlg.open = False
                self.safe_update()
                
                # 1. Eliminar en Supabase
                exito = self.db.eliminar_ventas_por_facturas(lista_facturas)
                if exito:
                    # 2. Remover localmente
                    if grupo_key in self.cargas_data and num_pag in self.cargas_data[grupo_key]:
                        del self.cargas_data[grupo_key][num_pag]
                        if not self.cargas_data[grupo_key]:
                            del self.cargas_data[grupo_key]
                    self._save_cargas()
                    
                    self.page.snack_bar = ft.SnackBar(ft.Text("Carga e inventario de ventas revertidos exitosamente."), bgcolor="orange700")
                    self.page.snack_bar.open = True
                    self.load_data()
                    self.load_summary()
                    self._render_tabla_cargas()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar registros en base de datos."), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.safe_update()

            def cerrar_dialogo_v_guardado(e):
                dlg.open = False
                self.safe_update()

            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                    ft.Text("Eliminar Carga Guardada (Afecta BD)", size=16, weight="bold", color="red700")
                ]),
                content=ft.Container(
                    width=450,
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(
                                "⚠️ ATENCIÓN: Esta carga ya fue guardada en el sistema. Al eliminarla se BORRARÁN DEFINITIVAMENTE las ventas de Supabase y se REVERTIRÁ EL STOCK DEL INVENTARIO (las unidades volverán al saldo disponible):",
                                size=11, color="red900", weight="bold"
                            ),
                            padding=10, bgcolor="#fde8e8", border_radius=6
                        ),
                        ft.Text("Insumos vendidos a revertir:", size=12, weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(
                            content=ft.Column(filas_resumen, scroll=ft.ScrollMode.AUTO),
                            height=180,
                            padding=8, bgcolor="#f8f9fa", border_radius=6, border=ft.border.all(1, "#e0e0e0")
                        ),
                        ft.Divider(height=5),
                        ft.Row([
                            ft.Text("Total Unidades:", size=11, color="grey"),
                            ft.Text(f"{cant_tot:g} unds", size=11, weight="bold"),
                            ft.Container(expand=True),
                            ft.Text("Total Venta a Revertir:", size=11, color="grey"),
                            ft.Text(f"${venta_tot:,.0f}", size=12, weight="bold", color="blue700")
                        ])
                    ], tight=True, spacing=10)
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo_v_guardado),
                    ft.ElevatedButton("Eliminar Definitivamente", bgcolor="red700", color="white", on_click=confirmar_eliminar_guardado)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.safe_update()

        else:
            # Carga No Guardada
            def confirmar_eliminar_simple(e):
                dlg.open = False
                self.safe_update()
                
                import os
                arch_local = data.get("archivo")
                if arch_local and os.path.exists(arch_local):
                    try: os.remove(arch_local)
                    except: pass
                    
                if grupo_key in self.cargas_data and num_pag in self.cargas_data[grupo_key]:
                    del self.cargas_data[grupo_key][num_pag]
                    if not self.cargas_data[grupo_key]:
                        del self.cargas_data[grupo_key]
                        
                self._save_cargas()
                self.page.snack_bar = ft.SnackBar(ft.Text("Página de carga eliminada de la lista."), bgcolor="green")
                self.page.snack_bar.open = True
                self._render_tabla_cargas()

            def cerrar_dialogo_v_simple(e):
                dlg.open = False
                self.safe_update()

            dlg = ft.AlertDialog(
                title=ft.Text("Eliminar Carga de la Lista"),
                content=ft.Text(f"¿Estás seguro de eliminar la Página No. {data['pagina']} ({data['fecha']})? Esta carga aún no ha afectado la base de datos."),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo_v_simple),
                    ft.ElevatedButton("Eliminar", bgcolor="red700", color="white", on_click=confirmar_eliminar_simple)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.safe_update()

    def on_accion_carga(self, e, data, txt_crono):
        btn = e.control
        if btn.text in ["Ver", "Ver y Guardar"]:
            # Cargar los datos extraídos previamente en la memoria de la vista
            self.carga_activa = data
            self.parsed_data = data.get("datos_extraidos") or data.get("invoices", [])
            
            # Recuperar nombres_insumos
            codigos_extraidos = set()
            for invoice in self.parsed_data:
                for p in invoice.get("productos", []):
                    codigos_extraidos.add(str(p.get("codigo_item", "")))
            if codigos_extraidos:
                self.nombres_insumos = self.db.get_nombres_insumos(list(codigos_extraidos))
            else:
                self.nombres_insumos = {}
                
            self.show_confirm_ui()
            return
            
        if getattr(self, "is_extraccion_activa", False):
            self.page.snack_bar = ft.SnackBar(ft.Text("Hay una extracción en proceso. Espere que termine el cronómetro."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Bloquear estado global
        self.is_extraccion_activa = True
        
        # Cambiar el texto del botón clickeado
        btn.text = "Extrayendo..."
        btn.icon = ft.icons.HOURGLASS_TOP
        
        # Deshabilitar TODOS los demás botones de extraer en la tabla
        for row in self.table_cargas.rows:
            accion_row = row.cells[-1].content
            b = accion_row.controls[0]
            if b.text == "Extraer Datos":
                b.disabled = True
                
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Analizando documento con Inteligencia Artificial..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()
        
        # Iniciar worker en segundo plano para no congelar la pantalla
        import threading
        threading.Thread(target=self._worker_extraccion, args=(data, btn, txt_crono), daemon=True).start()

    def _worker_extraccion(self, data, btn, txt_crono):
        try:
            # Como el archivo ya es de 1 página, pasamos el índice 0
            extracted = self.ai_parser.parse_ventas_pdf_page(data["archivo"], 0, data.get("tipo", "Remisión"))
            
            if extracted and isinstance(extracted, list) and len(extracted) > 0:
                data["estado"] = "Procesado con éxito"
                data["datos_extraidos"] = extracted
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("¡Extracción exitosa!"), bgcolor="green")
            else:
                data["estado"] = "Falló"
                data["datos_extraidos"] = []
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Fallo en la extracción. Revise el PDF o intente de nuevo."), bgcolor="red")
                    
            if self.page:
                self.page.snack_bar.open = True
            self._save_cargas()
            
            # --- INICIO DEL CRONÓMETRO DE ENFRIAMIENTO (COOLDOWN) ---
            txt_crono.visible = True
            btn.text = "Enfriando..."
            btn.icon = ft.icons.TIMER
            for i in range(20, 0, -1):
                txt_crono.value = f"⏱️ {i}s"
                if self.page:
                    self.page.update()
                import time
                time.sleep(1)
                
        except Exception as ex:
            data["estado"] = "Falló"
            self._save_cargas()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error en extracción: {ex}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            self.is_extraccion_activa = False
            # Renderizar la tabla reactiva los botones automáticamente según su estado
            self._render_tabla_cargas()
        
    def on_filtro_tipo_doc_change(self, e):
        self.current_page = 1
        self.load_data()

    def load_summary(self):
        f_corte = getattr(self, "fecha_corte", None)
        res = self.db.get_ventas_summary(fecha_corte=f_corte)
        tot_hist = res.get("total_historico", 0.0)
        tot_pos = res.get("total_pos", 0.0)
        tot_remi = res.get("total_remi", 0.0)
        tot_hoy = res.get("total_hoy", 0.0)
        hoy_pos = res.get("hoy_pos", 0.0)
        hoy_remi = res.get("hoy_remi", 0.0)
        iva_hist = res.get("iva_historico", 0.0)
        iva_hoy = res.get("iva_hoy", 0.0)

        self.lbl_ventas_hist.value = f"${tot_hist:,.2f}"
        self.lbl_ventas_pos.value = f"${tot_pos:,.2f}"
        self.lbl_ventas_remi.value = f"${tot_remi:,.2f}"
        self.lbl_ventas_hoy.value = f"${tot_hoy:,.2f}"
        self.lbl_ventas_hoy_sub.value = f"POS: ${hoy_pos:,.0f}  •  Remi: ${hoy_remi:,.0f}"
        self.lbl_iva_hist.value = f"${iva_hist:,.2f}"
        self.lbl_iva_hoy_sub.value = f"Hoy: ${iva_hoy:,.2f}"
        if self.page:
            try:
                self.summary_container.update()
            except Exception:
                pass
            
    def open_date_picker(self, e):
        self.date_picker.pick_date()
        
    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_date.tooltip = f"Fecha: {self.fecha_corte}"
            self.btn_date.icon_color = "blue"
            self.btn_clear_date.visible = True
            if self.page:
                self.page.update()
            self.current_page = 1
            self.load_data()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e):
        self.fecha_corte = None
        self.btn_date.tooltip = "Filtrar por Fecha"
        self.btn_date.icon_color = None
        self.btn_clear_date.visible = False
        self.date_picker.value = None
        if self.page:
            self.page.update()
        self.current_page = 1
        self.load_data()
        
    def on_agregar_click(self, e=None):
        if self.page:
            if self.file_picker not in self.page.overlay:
                self.page.overlay.append(self.file_picker)
                self.page.update()
            self.file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["pdf"],
                dialog_title="Selecciona el Reporte de Ventas (POS o Remisiones)"
            )

    def _abrir_file_picker_desde_modal(self, e):
        self.on_agregar_click(e)

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            pdf_path = e.files[0].path
            self.dlg_procesando_pdf.open = True
            if self.page:
                self.page.update()
            threading.Thread(target=self._procesar_pdf_ventas_nativo, args=(pdf_path,), daemon=True).start()

    def _procesar_pdf_ventas_nativo(self, pdf_path):
        try:
            res = detectar_y_parsear_pdf(pdf_path)
            res['nombre_archivo'] = os.path.basename(pdf_path)
            
            # Validar duplicados contra Supabase
            facturas_nums = [f['factura_no'] for f in res.get('facturas', []) if f.get('factura_no')]
            existentes = self.db.get_ventas_existentes(facturas_nums)
            
            for f in res.get('facturas', []):
                is_dup = f['factura_no'] in existentes
                f['ya_registrada'] = is_dup
                f['seleccionada'] = not is_dup
                f['expandida'] = False
                
            self.vista_cargas_consolidada.set_data(res)
            self.tabs.selected_index = 1 # Cambiar a la pestaña de Gestión de Cargas
            
            self.dlg_procesando_pdf.open = False
            self.mostrar_alerta(f"✓ PDF de Ventas procesado: {res['total_facturas']} documentos y {res['total_insumos']} insumos detectados.", "green700")
            
        except Exception as ex:
            self.dlg_procesando_pdf.open = False
            self.mostrar_alerta(f"Error procesando PDF de ventas: {str(ex)}", "red")
        finally:
            if self.page:
                self.page.update()

    def _guardar_ventas_lote(self, facturas_seleccionadas):
        try:
            self.dlg_procesando_pdf.open = True
            if self.page:
                self.page.update()
                
            payload = []
            for f in facturas_seleccionadas:
                fecha_doc = f.get('fecha')
                num_fac = f.get('factura_no')
                tipo_doc = f.get('tipo_documento', 'Factura POS')
                pag_orig = f.get('pagina_origen', 1)
                
                for it in f.get('items', []):
                    payload.append({
                        "fecha": fecha_doc,
                        "factura_no": num_fac,
                        "tipo_documento": tipo_doc,
                        "pagina_origen": pag_orig,
                        "codigo_insumo": it.get('codigo_insumo'),
                        "descripcion": it.get('descripcion'),
                        "cantidad": float(it.get('cantidad', 0)),
                        "subtotal": float(it.get('subtotal', 0)),
                        "iva": float(it.get('iva', 0)),
                        "total": float(it.get('total', 0)),
                        "estado_registro": "VÁLIDO"
                    })
                    
            exito = self.db.insert_ventas(payload)
            self.dlg_procesando_pdf.open = False
            
            if exito:
                self.vista_cargas_consolidada.set_data(None)
                self.tabs.selected_index = 0 # Volver a la tabla principal de ventas
                self.load_data()
                self.load_summary()
                self.mostrar_alerta(f"✓ {len(facturas_seleccionadas)} documentos ({len(payload)} insumos) guardados exitosamente.", "green700")
            else:
                self.mostrar_alerta("Error al guardar ventas en la base de datos.", "red")
        except Exception as ex:
            self.dlg_procesando_pdf.open = False
            self.mostrar_alerta(f"Error al guardar lote de ventas: {str(ex)}", "red")
        finally:
            if self.page:
                self.page.update()

    def mostrar_alerta(self, mensaje: str, color: str = "red"):
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(mensaje, weight="bold", color="white"),
                bgcolor=color,
                duration=3500
            )
            self.page.snack_bar.open = True
            try:
                self.page.update()
            except Exception:
                pass

    def animate_loading(self, base_msg):
        messages = [
            base_msg,
            "Puliendo datos para enviarlos...",
            "Generando el formato de carga...",
            "A unos pasos de finalizar..."
        ]
        idx = 0
        while getattr(self, "is_loading", False):
            if hasattr(self, "lbl_loading_text") and self.page:
                self.lbl_loading_text.value = messages[idx % len(messages)]
                try:
                    self.page.update()
                except Exception:
                    pass
            idx += 1
            time.sleep(5)

    def procesar_siguiente_pagina(self):
        if self.current_page_idx >= self.total_pages_pdf:
            self.page.snack_bar = ft.SnackBar(ft.Text("¡Proceso finalizado con éxito!", color="white"), bgcolor="green")
            self.page.snack_bar.open = True
            self.close_confirm_ui(None)
            self.load_data()
            return
            
        pagina_actual = self.current_page_idx + 1
        base_msg = f"Extrayendo datos de la página {pagina_actual} de {self.total_pages_pdf}..."
        self.lbl_loading_text.value = base_msg
        self.dlg_loading.open = True
        self.page.update()
        
        self.is_loading = True
        threading.Thread(target=self.animate_loading, args=(base_msg,), daemon=True).start()
        
        try:
            data = self.ai_parser.parse_ventas_pdf_page(self.current_pdf_path, self.current_page_idx)
            
            if data and isinstance(data, list):
                lista_facturas = [item.get("numero_factura") for item in data if item.get("numero_factura")]
                existentes = self.db.get_ventas_existentes(lista_facturas)
                
                data_nueva = []
                codigos_extraidos = set()
                for invoice in data:
                    factura = invoice.get("numero_factura")
                    if factura not in existentes:
                        data_nueva.append(invoice)
                        for p in invoice.get("productos", []):
                            codigos_extraidos.add(str(p.get("codigo_item", "")))
                
                self.parsed_data = data_nueva
                
                if codigos_extraidos:
                    self.nombres_insumos = self.db.get_nombres_insumos(list(codigos_extraidos))
                else:
                    self.nombres_insumos = {}
            else:
                self.parsed_data = []
                
            self.is_loading = False
            self.dlg_loading.open = False
            self.page.update()
            
            self.show_confirm_ui()
            
            if data and isinstance(data, list) and not self.parsed_data:
                self.page.snack_bar = ft.SnackBar(ft.Text("Todos los datos de esta página ya están registrados. Haz clic en Continuar.", color="white"), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
            elif not data:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al procesar la página o no se extrajo información.", color="white"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as e:
            self.is_loading = False
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ocurrió un error inesperado: {str(e)}", color="white"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
                
    def update_totals(self, e=None):
        gran_cant = 0.0
        gran_costo = 0.0
        gran_iva = 0.0
        gran_total = 0.0
        
        factura_totals = {}
        
        for item in self.productos_rows:
            if item["type"] == "product":
                try:
                    cant = float(item["cantidad_ctl"].value.replace(',', '.'))
                    subtotal = float(item["subtotal_ctl"].value.replace(',', '.'))
                    iva = float(item["iva_ctl"].value.replace(',', '.'))
                    
                    row_total = subtotal + iva
                    item["total_ctl"].value = f"${row_total:,.2f}"
                    
                    precio_u = subtotal / cant if cant > 0 else 0
                    item["costo_ctl"].value = f"${precio_u:,.2f}"
                    
                    factura_idx = item["factura_idx"]
                    factura_totals[factura_idx] = factura_totals.get(factura_idx, 0) + row_total
                    
                    gran_cant += cant
                    gran_costo += precio_u
                    gran_iva += iva
                    gran_total += row_total
                except:
                    item["total_ctl"].value = "Error"
                    
        for item in self.productos_rows:
            if item["type"] == "header":
                idx = item["factura_idx"]
                total = factura_totals.get(idx, 0)
                item["total_factura_ctl"].value = f"Total Factura: ${total:,.2f}"
                
        self.txt_gran_cant.value = f"{gran_cant:,.2f}"
        self.txt_gran_costo.value = f"${gran_costo:,.2f}"
        self.txt_gran_iva.value = f"${gran_iva:,.2f}"
        self.txt_gran_total.value = f"${gran_total:,.2f}"
        if self.page:
            self.page.update()

    def show_confirm_ui(self):
        if not hasattr(self, "main_content"):
            self.main_content = self.content
            
        self.productos_rows = []

        # 1. Consolidar facturas con la misma clave y filtrar facturas vacías sin productos
        invoices_consolidadas = {}
        for inv in (self.parsed_data or []):
            fac = inv.get("numero_factura", "")
            fec = inv.get("fecha", "")
            key = (fac, fec)
            prods = inv.get("productos", [])
            if key not in invoices_consolidadas:
                invoices_consolidadas[key] = dict(inv)
                invoices_consolidadas[key]["productos"] = list(prods)
            else:
                invoices_consolidadas[key]["productos"].extend(prods)

        invoices_limpias = [
            inv for inv in invoices_consolidadas.values()
            if inv.get("productos") and len(inv["productos"]) > 0
        ]

        facturas_count = len(invoices_limpias)
        productos_count = 0
        
        estado_carga = self.carga_activa.get("estado", "") if hasattr(self, "carga_activa") else ""
        ya_guardado = estado_carga in ["Guardado", "Procesado con éxito"]

        for idx, invoice in enumerate(invoices_limpias):
            fecha = invoice.get("fecha", "")
            factura = invoice.get("numero_factura", "")
            
            total_factura_ctl = ft.Text("Total Factura: $0", weight="bold", size=11.5, color=Config.COLOR_PRIMARY)
            self.productos_rows.append({
                "type": "header",
                "factura_idx": idx,
                "total_factura_ctl": total_factura_ctl,
                "row_ctl": ft.Container(
                    content=ft.Row([
                        ft.Text(f"Factura No.: {factura} | Fecha: {fecha}", weight="bold", size=11.5, color=Config.COLOR_PRIMARY),
                        ft.Container(expand=True),
                        total_factura_ctl
                    ]),
                    bgcolor=ft.colors.with_opacity(0.08, Config.COLOR_PRIMARY),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=5
                )
            })
            
            for p in invoice.get("productos", []):
                productos_count += 1
                cod = str(p.get("codigo_item", ""))
                nombre = self.nombres_insumos.get(cod, "Desconocido")
                
                def get_codigo_change_handler(nombre_control):
                    def handler(e):
                        val = e.control.value
                        if val:
                            nombres = self.db.get_nombres_insumos([val])
                            nombre_control.value = nombres.get(val, "Desconocido")
                        else:
                            nombre_control.value = "Desconocido"
                        nombre_control.tooltip = nombre_control.value
                        if self.page: self.page.update()
                    return handler
                
                nombre_ctl = ft.Text(nombre[:26], width=200, size=11, no_wrap=True, tooltip=nombre, color="#374151")
                codigo_ctl = ft.TextField(
                    value=cod, width=80, height=32, text_size=11, dense=True, read_only=ya_guardado,
                    content_padding=ft.padding.symmetric(horizontal=8, vertical=2), border_radius=6,
                    on_change=get_codigo_change_handler(nombre_ctl)
                )
                
                cantidad_val = float(p.get("cantidad", 0))
                subtotal_val = float(p.get("subtotal", 0))
                precio_unitario = subtotal_val / cantidad_val if cantidad_val > 0 else 0.0
                
                cantidad_ctl = ft.TextField(
                    value=str(p.get("cantidad", 0)), width=60, height=32, text_size=11, dense=True, read_only=ya_guardado,
                    content_padding=ft.padding.symmetric(horizontal=8, vertical=2), border_radius=6,
                    on_change=self.update_totals
                )
                costo_ctl = ft.Text(f"${precio_unitario:,.0f}", width=70, size=11, color="grey")
                subtotal_ctl = ft.TextField(
                    value=str(subtotal_val), width=75, height=32, text_size=11, dense=True, read_only=ya_guardado,
                    content_padding=ft.padding.symmetric(horizontal=8, vertical=2), border_radius=6,
                    on_change=self.update_totals
                )
                iva_ctl = ft.TextField(
                    value=str(p.get("iva", 0)), width=75, height=32, text_size=11, dense=True, read_only=ya_guardado,
                    content_padding=ft.padding.symmetric(horizontal=8, vertical=2), border_radius=6,
                    on_change=self.update_totals
                )
                total_ctl = ft.Text("$0", width=90, size=11.5, weight="bold", color="#111827")
                
                prod_row_data = {
                    "type": "product",
                    "factura_idx": idx,
                    "fecha": fecha,
                    "factura": factura,
                    "codigo_ctl": codigo_ctl,
                    "nombre_ctl": nombre_ctl,
                    "cantidad_ctl": cantidad_ctl,
                    "subtotal_ctl": subtotal_ctl,
                    "costo_ctl": costo_ctl,
                    "iva_ctl": iva_ctl,
                    "total_ctl": total_ctl
                }

                btn_del = ft.IconButton(
                    icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                    icon_color="red400",
                    icon_size=16,
                    tooltip="Eliminar este insumo",
                    visible=not ya_guardado,
                    on_click=lambda e, item=prod_row_data, f_idx=idx: self._eliminar_insumo_de_factura(e, item, f_idx)
                )

                prod_row_data["row_ctl"] = ft.Row(
                    [codigo_ctl, nombre_ctl, cantidad_ctl, costo_ctl, subtotal_ctl, iva_ctl, total_ctl, btn_del],
                    spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
                self.productos_rows.append(prod_row_data)
            
        if len(self.productos_rows) == 0:
            self.list_view_confirm = ft.Container(
                content=ft.Text(
                    "Todos los datos de esta página ya están registrados en la base de datos.",
                    color="orange",
                    weight="bold",
                    text_align=ft.TextAlign.CENTER,
                    size=13
                ),
                padding=30,
                alignment=ft.alignment.center,
                expand=True
            )
        else:
            self.list_view_confirm = ft.ListView(
                controls=[item["row_ctl"] for item in self.productos_rows],
                expand=True,
                spacing=4
            )
        
        self.txt_gran_cant = ft.Text("0", weight="bold", size=12)
        self.txt_gran_costo = ft.Text("$0", weight="bold", size=12)
        self.txt_gran_iva = ft.Text("$0", weight="bold", size=12)
        self.txt_gran_total = ft.Text("$0", weight="bold", size=14, color=Config.COLOR_PRIMARY)
        
        # Lógica de Botones Footer
        is_last_page = not (hasattr(self, 'total_pages_pdf') and self.current_page_idx < self.total_pages_pdf - 1)
        botones_acciones = [ft.TextButton("← Volver", on_click=self.close_confirm_ui)]
        
        if ya_guardado:
            botones_acciones.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.CHECK_CIRCLE, color="green700", size=15),
                        ft.Text("Carga guardada en Base de Datos", color="green800", size=11.5, weight="bold")
                    ], spacing=6),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    bgcolor="#E8F5E9",
                    border_radius=6
                )
            )
        else:
            if not is_last_page:
                botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar", height=32, bgcolor="grey", color="white", on_click=self.on_guardar_venta_partial))
                botones_acciones.append(ft.ElevatedButton("Confirmar y Continuar", height=32, bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_venta))
            else:
                botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar Todo", height=32, bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_venta))
        
        # --- NUEVO DISEÑO DEL FOOTER ---
        # 1. Fila de Información Financiera (Estilo Dashboard)
        info_row = ft.Row([
            ft.Text("RESUMEN TOTAL", weight="bold", size=13, color=Config.COLOR_PRIMARY),
            ft.Container(expand=True),
            
            ft.Column([ft.Text("Cant. Total", size=10.5, color="grey"), self.txt_gran_cant], spacing=1, horizontal_alignment="end"),
            ft.Container(width=1, height=24, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=8)),
            
            ft.Column([ft.Text("Costo Base", size=10.5, color="grey"), self.txt_gran_costo], spacing=1, horizontal_alignment="end"),
            ft.Container(width=1, height=24, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=8)),
            
            ft.Column([ft.Text("IVA Total", size=10.5, color="grey"), self.txt_gran_iva], spacing=1, horizontal_alignment="end"),
            ft.Container(width=1, height=24, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=8)),
            
            ft.Column([ft.Text("GRAN TOTAL", size=10.5, color="grey", weight="bold"), self.txt_gran_total], spacing=1, horizontal_alignment="end"),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 2. Fila de Botones de Acción
        buttons_row = ft.Row([
            ft.Container(expand=True),
            *botones_acciones
        ], alignment=ft.MainAxisAlignment.END, spacing=10)

        # 3. Contenedor Principal del Footer
        footer = ft.Container(
            content=ft.Column([
                info_row,
                ft.Divider(height=10, color=ft.colors.with_opacity(0.1, "black")),
                buttons_row
            ], spacing=0),
            bgcolor=ft.colors.with_opacity(0.03, Config.COLOR_PRIMARY),
            padding=12,
            border_radius=8,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY)),
            margin=ft.padding.only(top=6)
        )
        
        if hasattr(self, 'total_pages_pdf'):
            titulo = f"Datos Extraídos - Pág. No. {self.current_page_idx + 1} de {self.total_pages_pdf}"
        elif hasattr(self, 'carga_activa'):
            titulo = f"Datos Extraídos - Pág. No. {self.carga_activa.get('pagina', 1)} ({self.carga_activa.get('tipo', '')})"
        else:
            titulo = "Revisión de Ventas (Modo Inmersivo)"
        self.lbl_confirm_subtitle = ft.Text(f"{facturas_count} Facturas extraídas | {productos_count} Productos en total", size=11.5, color="grey")
        header = ft.Row([
            ft.Text(titulo, size=16, weight="bold"),
            self.lbl_confirm_subtitle
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.content = ft.Column([
            header,
            ft.Divider(height=6),
            ft.Row([
                ft.Container(width=80, content=ft.Text("Código", weight="bold", size=11, color="grey")),
                ft.Container(width=200, content=ft.Text("Nombre (desde BD)", weight="bold", size=11, color="grey")),
                ft.Container(width=60, content=ft.Text("Cantidad", weight="bold", size=11, color="grey")),
                ft.Container(width=70, content=ft.Text("Precio U.", weight="bold", size=11, color="grey")),
                ft.Container(width=75, content=ft.Text("Subtotal", weight="bold", size=11, color="grey")),
                ft.Container(width=75, content=ft.Text("IVA", weight="bold", size=11, color="grey")),
                ft.Container(width=90, content=ft.Text("Costo Total", weight="bold", size=11, color="grey")),
                ft.Container(width=30, content=ft.Text("", size=11))
            ], spacing=6),
            self.list_view_confirm,
            footer
        ], expand=True, spacing=6)
        
        self.update_totals()
        self.page.update()

    def _eliminar_insumo_de_factura(self, e, item_dict, fac_idx):
        try:
            # 1. Remover de self.productos_rows
            if item_dict in self.productos_rows:
                self.productos_rows.remove(item_dict)

            # 2. Remover de los controles visuales de ListView
            if hasattr(self, 'list_view_confirm') and hasattr(self.list_view_confirm, 'controls') and item_dict.get("row_ctl") in self.list_view_confirm.controls:
                self.list_view_confirm.controls.remove(item_dict["row_ctl"])

            # 3. Si la factura se quedó sin productos, remover también el encabezado de la factura
            prods_restantes = [it for it in self.productos_rows if it.get("type") == "product" and it.get("factura_idx") == fac_idx]
            if not prods_restantes:
                header_item = next((it for it in self.productos_rows if it.get("type") == "header" and it.get("factura_idx") == fac_idx), None)
                if header_item:
                    if header_item in self.productos_rows:
                        self.productos_rows.remove(header_item)
                    if hasattr(self, 'list_view_confirm') and hasattr(self.list_view_confirm, 'controls') and header_item.get("row_ctl") in self.list_view_confirm.controls:
                        self.list_view_confirm.controls.remove(header_item["row_ctl"])

            # 4. Actualizar contador en el encabezado
            prods_tot = sum(1 for it in self.productos_rows if it.get("type") == "product")
            facs_tot = len(set(it.get("factura_idx") for it in self.productos_rows if it.get("type") == "product"))
            if hasattr(self, 'lbl_confirm_subtitle'):
                self.lbl_confirm_subtitle.value = f"{facs_tot} Facturas extraídas | {prods_tot} Productos en total"

            # 5. Actualizar totales y sincronizar en staging
            self.update_totals()
            self._sincronizar_productos_rows_a_staging()

            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Insumo eliminado de la factura."), bgcolor="orange700", duration=2000)
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as ex:
            from core.logger import log_error
            log_error("_eliminar_insumo_de_factura", ex)

    def _sincronizar_productos_rows_a_staging(self):
        if hasattr(self, "carga_activa") and self.carga_activa:
            grupo_key = self.carga_activa.get("fecha")
            pagina_origen = self.carga_activa.get("pagina")
            
            # Reconstruir lista de facturas con sus productos actuales
            facturas_map = {}
            for it in self.productos_rows:
                if it.get("type") == "product":
                    f_idx = it.get("factura_idx")
                    if f_idx not in facturas_map:
                        facturas_map[f_idx] = {
                            "fecha": it.get("fecha", ""),
                            "numero_factura": it.get("factura", ""),
                            "productos": []
                        }
                    try:
                        cant = float(str(it["cantidad_ctl"].value).replace(',', '.'))
                        subtot = float(str(it["subtotal_ctl"].value).replace(',', '.'))
                        iva = float(str(it["iva_ctl"].value).replace(',', '.'))
                        tot = subtot + iva
                    except:
                        cant, subtot, iva, tot = 0.0, 0.0, 0.0, 0.0

                    facturas_map[f_idx]["productos"].append({
                        "codigo_item": it["codigo_ctl"].value,
                        "cantidad": cant,
                        "subtotal": subtot,
                        "iva": iva,
                        "total": tot
                    })

            nuevos_datos = list(facturas_map.values())
            self.carga_activa["datos_extraidos"] = nuevos_datos
            self.carga_activa["total_facturas"] = len(nuevos_datos)

            # Guardar en archivo de staging
            if grupo_key and str(pagina_origen) in self.cargas_data.get(grupo_key, {}):
                self.cargas_data[grupo_key][str(pagina_origen)]["datos_extraidos"] = nuevos_datos
                self.cargas_data[grupo_key][str(pagina_origen)]["total_facturas"] = len(nuevos_datos)
                self._save_cargas()
        
    def close_confirm_ui(self, e):
        self.content = self.main_content
        self.page.update()
        
    def on_guardar_venta_partial(self, e):
        # Engañar a la lógica para que crea que es la última página
        if hasattr(self, 'total_pages_pdf'):
            self.current_page_idx = self.total_pages_pdf
        self.on_guardar_venta(e)

    def on_guardar_venta(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if self.page:
            self.update()
            
        threading.Thread(target=self._on_guardar_venta_worker, args=(btn_control,), daemon=True).start()

    def _on_guardar_venta_worker(self, btn_control):
        try:
            ventas_list = []
            
            # Recuperar metadatos de la carga que estamos confirmando
            fecha_doc = self.carga_activa["fecha"]
            tipo_doc = self.carga_activa["tipo"]
            pagina_origen = self.carga_activa["pagina"]
            
            for item in self.productos_rows:
                if item["type"] == "product":
                    try:
                        cant_str = str(item["cantidad_ctl"].value).replace(',', '.')
                        subtotal_str = str(item["subtotal_ctl"].value).replace(',', '.')
                        iva_str = str(item["iva_ctl"].value).replace(',', '.')
                        
                        cantidad = float(cant_str)
                        subtotal = float(subtotal_str)
                        iva = float(iva_str)
                        total = subtotal + iva
                        
                        ventas_list.append({
                            "fecha": fecha_doc, # Forzar la fecha seleccionada en el modal
                            "numero_factura": item["factura"],
                            "codigo_item": item["codigo_ctl"].value,
                            "descripcion": item["nombre_ctl"].value,
                            "cantidad": cantidad,
                            "precio_unitario": subtotal,
                            "iva": iva,
                            "costo_total": total,
                            "tipo_documento": tipo_doc,
                            "pagina_origen": pagina_origen
                        })
                    except ValueError:
                        self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico en cantidad, costo o IVA."), bgcolor="red")
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
            
            if ventas_list:
                # 1. Eliminar datos viejos de esta misma página (si fue una sobreescritura)
                self.db.eliminar_ventas_origen(fecha_doc, tipo_doc, pagina_origen)
                
                # 2. Insertar los nuevos datos
                if self.db.insert_ventas(ventas_list):
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"Página guardada exitosamente en BD."), bgcolor="green")
                    self.page.snack_bar.open = True
                    
                    # 3. Actualizar el estado local a Guardado de forma robusta
                    if hasattr(self, "carga_activa") and self.carga_activa:
                        self.carga_activa["estado"] = "Guardado"
                        carga_id = self.carga_activa.get("id")
                    else:
                        carga_id = None

                    for g_k, paginas in self.cargas_data.items():
                        if isinstance(paginas, dict):
                            for p_k, p_data in paginas.items():
                                if isinstance(p_data, dict):
                                    if (carga_id is not None and p_data.get("id") == carga_id) or (g_k.startswith(str(fecha_doc)) and str(p_k) == str(pagina_origen)):
                                        p_data["estado"] = "Guardado"

                    self._save_cargas()
                    self.close_confirm_ui(None)
                    self._render_tabla_cargas()
                    self.load_data()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar en base de datos"), bgcolor="red")
                    self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("No hay datos para guardar."), bgcolor="orange")
                self.page.snack_bar.open = True
                
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.update()
            
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        if self.page:
            self.update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        raw_auto = (self.search_autocomplete.value or "").strip()
        if not raw_auto:
            search_val = ""
            self.search_input_text.value = ""
        else:
            search_val = self.search_input_text.value or raw_auto
        
        cat_filtro = getattr(self, 'filtro_categoria_activo', None)
        fact_filtro = getattr(self, 'filtro_factura_activo', None)
        f_corte = getattr(self, 'fecha_corte', None)
        tipo_doc_filtro = getattr(self.drop_filtro_tipo_doc_tabla, "value", "TODOS")

        data, total = self.db.get_ventas(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val,
            fecha_corte=f_corte,
            categoria_filtro=cat_filtro,
            factura_filtro=fact_filtro,
            tipo_documento_filtro=tipo_doc_filtro
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        self.data_table.rows.clear()
        
        for item in data:
            fecha_raw = str(item.get('fecha', ''))
            str_fecha = fecha_raw[:10] if len(fecha_raw) >= 10 else fecha_raw
            
            str_factura = str(item.get('factura_no') or 'N/A')
            str_tipo_doc = str(item.get('tipo_documento') or 'Remisión')
            str_codigo = str(item.get('codigo_insumo', ''))
            
            cat_info = item.get('catalogo_insumos') or {}
            nombre_bd = cat_info.get('nombre')
            nombre_desc = item.get('descripcion')
            str_nombre = nombre_bd if nombre_bd else (nombre_desc if nombre_desc else 'Desconocido')
            
            cantidad = float(item.get('cantidad', 0) or 0)
            precio_unitario = float(item.get('subtotal', 0) or 0)
            iva = float(item.get('iva', 0) or 0)
            costo_total = float(item.get('total', 0) or 0)
            
            str_precio_unit = f"${precio_unitario:,.2f}"
            str_iva = f"${iva:,.2f}"
            str_total = f"${costo_total:,.2f}"
            str_cant = f"{int(cantidad)} unds" if cantidad.is_integer() else f"{cantidad:g} unds"
            
            is_pos = "POS" in str_tipo_doc.upper()
            badge_color = "blue700" if is_pos else "teal800"
            badge_bg = "#eff6ff" if is_pos else "#f0fdf4"
            badge_txt = "POS" if is_pos else "REMI"
            
            cell_doc = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_color),
                            bgcolor=badge_bg, padding=ft.padding.symmetric(horizontal=4, vertical=1), border_radius=3
                        ),
                        ft.Text(f"#{str_factura}", size=11, weight="bold", color=Config.COLOR_PRIMARY)
                    ], spacing=4),
                    ft.Text(str_fecha, size=10, color="grey600")
                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=2)
            )

            cell_item = ft.Container(
                content=ft.Row([
                    ft.Text(f"[{str_codigo}]", size=11, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Text(str_nombre, size=11, weight="w500", overflow=ft.TextOverflow.ELLIPSIS, expand=True)
                ], spacing=5),
                width=320
            )

            row = ft.DataRow(
                cells=[
                    ft.DataCell(cell_doc),
                    ft.DataCell(cell_item),
                    ft.DataCell(ft.Text(str_cant, size=11)),
                    ft.DataCell(ft.Text(str_precio_unit, size=11)),
                    ft.DataCell(ft.Text(str_iva, size=11, color="grey700")),
                    ft.DataCell(ft.Text(str_total, size=11, color="teal800", weight="bold")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.EDIT_OUTLINED, 
                                icon_color="blue", 
                                icon_size=18,
                                tooltip="Editar Venta", 
                                on_click=lambda e, i=item: self.abrir_modal_editar_venta(i)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINED, 
                                icon_color="red", 
                                icon_size=18,
                                tooltip="Eliminar Venta", 
                                on_click=lambda e, i=item: self.confirmar_eliminar_venta(i)
                            )
                        ], spacing=0)
                    ),
                ]
            )
            self.data_table.rows.append(row)
            
        self.update_pagination_ui()
        
    def update_pagination_ui(self):
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros en total"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        # Apagar indicador de carga al finalizar
        self.progress_bar.visible = False
        
        if self.page:
            self.update()
        
    def on_search(self, e):
        self.current_page = 1
        self.load_data()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()

    def on_extraer_todo_masivo(self, e):
        if getattr(self, "is_extraccion_activa", False):
            self.page.snack_bar = ft.SnackBar(ft.Text("Ya hay una extracción en curso."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        import threading
        threading.Thread(target=self._worker_extraccion_masiva, daemon=True).start()

    def _worker_extraccion_masiva(self):
        self.is_extraccion_activa = True

        # 1. Recopilar pendientes
        pendientes = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                if data.get("estado") in ["Nuevo", "Falló", "Sobreescrito"]:
                    pendientes.append(data)

        if not pendientes:
            self.is_extraccion_activa = False
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("No hay páginas pendientes por extraer."), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
            return

        # 2. Calcular Tiempos
        total_items = len(pendientes)
        # Estimado: 5 seg proceso + 20 seg enfriamiento por página (salvo la última)
        tiempo_estimado_segundos = (total_items * 25) - 20 

        # 3. Interfaz de Progreso Inmersiva
        lbl_estado_progreso = ft.Text(f"Páginas en cola: {total_items}", weight="bold", size=16)
        lbl_tiempo = ft.Text(f"Tiempo estimado total: ~{tiempo_estimado_segundos // 60} min {tiempo_estimado_segundos % 60} seg", color="grey")
        lbl_enfriamiento = ft.Text("", size=12, color="orange", weight="bold")
        barra_progreso = ft.ProgressBar(width=400, color="purple700", bgcolor="#eeeeee", value=0)

        dlg_progreso = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesamiento Masivo IA", color="purple700"),
            content=ft.Column([
                lbl_estado_progreso,
                lbl_tiempo,
                barra_progreso,
                lbl_enfriamiento,
                ft.Text("Por favor NO cierres esta ventana ni la aplicación.", size=11, color="red")
            ], tight=True, spacing=10)
        )

        if self.page:
            self.page.overlay.append(dlg_progreso)
            dlg_progreso.open = True
            self.page.update()

        exitos = 0
        fallos = 0
        import time

        # 4. Bucle de Procesamiento
        for idx, data in enumerate(pendientes):
            try:
                if self.page:
                    lbl_estado_progreso.value = f"Extrayendo página {idx + 1} de {total_items}..."
                    lbl_tiempo.value = f"Analizando estructura de {data.get('archivo', '')}..."
                    barra_progreso.value = idx / total_items
                    self.page.update()

                # Resolución dinámica según el módulo
                if hasattr(self.ai_parser, "parse_ventas_pdf_page") and "ventas" in str(self.__class__).lower():
                    extracted = self.ai_parser.parse_ventas_pdf_page(data["archivo"], 0, data.get("tipo", "Remisión"))
                else:
                    extracted = self.ai_parser.parse_compras_pdf_page(data["archivo"], 0)

                if extracted and isinstance(extracted, list) and len(extracted) > 0:
                    data["estado"] = "Procesado con éxito"
                    data["datos_extraidos"] = extracted
                    exitos += 1
                else:
                    data["estado"] = "Falló"
                    data["datos_extraidos"] = []
                    fallos += 1

                self._save_cargas()

                if self.page:
                    self._render_tabla_cargas()

                # 5. Enfriamiento de seguridad API (No se aplica al último registro)
                if idx < total_items - 1:
                    for i in range(20, 0, -1):
                        if self.page and dlg_progreso.open:
                            lbl_enfriamiento.value = f"Pausa anti-saturación de API: {i}s..."
                            self.page.update()
                        time.sleep(1)
                    if self.page:
                        lbl_enfriamiento.value = ""

            except Exception as ex:
                data["estado"] = "Falló"
                self._save_cargas()
                fallos += 1

        # 6. Finalización
        self.is_extraccion_activa = False
        if self.page:
            dlg_progreso.open = False
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Proceso masivo completado. Éxitos: {exitos}, Fallos: {fallos}"), 
                bgcolor="green" if fallos == 0 else "orange"
            )
            self.page.snack_bar.open = True
            barra_progreso.value = 1
            self.page.update()
            self._render_tabla_cargas()

    def copiar_historial_ventas(self, e):
        """
        Obtiene las ventas del día agrupadas por categoría y construye
        un texto formateado para el portapapeles del sistema.
        """
        if not self.page: return

        def worker():
            # Consultar desglose por tipo de documento para la fecha activa
            items_doc = self.db.get_historial_ventas_dia(self.fecha_historial_activa, "TIPO_DOCUMENTO")

            tot_pesos = self.lbl_tot_ventas_panel.value

            if self.fecha_historial_activa is None:
                fecha_str = "Todo el Mes"
                label_total = "Total Venta del Mes"
            else:
                fecha_str = str(self.fecha_historial_activa)
                label_total = "Total Ventas del Día"

            lineas_doc = []
            for item in items_doc:
                tdoc = item.get("tipo_documento", "Factura POS")
                total = item.get("total", 0)
                fact_cant = item.get("facturas_cant", 1)
                fact_txt = "factura" if fact_cant == 1 else "facturas"
                lineas_doc.append(f"  • {tdoc}: {fact_cant} {fact_txt} - ${total:,.0f} COP")

            doc_text = "\n".join(lineas_doc) if lineas_doc else "  (Sin ventas registradas por tipo de documento)"

            texto_copia = (
                f"📊 HISTÓRICO DE VENTAS / SALIDAS\n"
                f"📅 Fecha: {fecha_str}\n"
                f"💵 {label_total}: {tot_pesos}\n"
                f"-----------------------------------------\n"
                f"📄 DESGLOSE POR TIPO DE DOCUMENTO:\n"
                f"{doc_text}\n"
                f"-----------------------------------------"
            )

            self.page.set_clipboard(texto_copia)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="white", size=18),
                    ft.Text("Histórico de ventas copiado al portapapeles exitosamente", color="white")
                ]),
                bgcolor="blue800"
            )
            self.page.snack_bar.open = True

            if hasattr(self, "safe_update"):
                self.safe_update()
            else:
                self.page.update()

        import threading
        threading.Thread(target=worker, daemon=True).start()

    # --- INICIO CRUD MANUAL VENTAS ---
    def _construir_modal_crud(self):
        self.crud_codigo_insumo = CustomAutoComplete(
            hint_text="Buscar insumo (Código o Nombre)...",
            on_select=self._on_insumo_crud_select
        )
        self.crud_codigo_insumo.width = 350
        self.crud_fecha = ft.TextField(label="Fecha (YYYY-MM-DD)", width=150)
        self.crud_factura = ft.TextField(label="N° Factura / Remisión", width=180)
        self.crud_tipo_doc = ft.Dropdown(label="Tipo Doc.", options=[ft.dropdown.Option("Remisión"), ft.dropdown.Option("Factura POS")], width=150)
        
        self.crud_cantidad = ft.TextField(label="Cantidad", width=120, on_change=self._calc_tot_crud)
        self.crud_precio_unit = ft.TextField(label="Subtotal", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_descuento = ft.TextField(label="Descuento", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_iva = ft.TextField(label="IVA", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        
        self.crud_total_lbl = ft.Text("$ 0.00", size=20, weight="bold", color="green700")
        self.crud_item_id = None
        
        self.dlg_crud = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar Venta"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    self.crud_codigo_insumo,
                    ft.Row([self.crud_fecha, self.crud_factura, self.crud_tipo_doc]),
                    ft.Row([self.crud_cantidad, self.crud_precio_unit]),
                    ft.Row([self.crud_descuento, self.crud_iva]),
                    ft.Divider(height=10),
                    ft.Row([ft.Text("Total Venta:", size=16, weight="bold"), self.crud_total_lbl])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_crud()),
                ft.ElevatedButton("Guardar", bgcolor="green700", color="white", on_click=self.guardar_venta_formulario)
            ]
        )

    def _on_insumo_crud_select(self, e):
        pass

    def _calc_tot_crud(self, e=None):
        try:
            subt = float(self.crud_precio_unit.value or 0)
            desc = float(self.crud_descuento.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = subt + iva - desc
            self.crud_total_lbl.value = f"$ {tot:,.2f}"
            self.safe_update()
        except ValueError:
            self.crud_total_lbl.value = "$ 0.00"
            self.safe_update()

    def _cerrar_crud(self):
        self.dlg_crud.open = False
        self.safe_update()

    def abrir_modal_crear_venta(self, e=None):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.suggestions = [{"key": i['codigo_insumo'], "value": f"[{i['codigo_insumo']}] {i['nombre']}"} for i in insumos]
        
        self.crud_item_id = None
        self.dlg_crud.title.value = "Registrar Nueva Venta"
        self.crud_codigo_insumo.value = ""
        from core.fecha_utils import get_hoy_local_str
        self.crud_fecha.value = get_hoy_local_str()
        self.crud_factura.value = ""
        self.crud_tipo_doc.value = "Remisión"
        self.crud_cantidad.value = ""
        self.crud_precio_unit.value = ""
        self.crud_descuento.value = "0"
        self.crud_iva.value = "0"
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def abrir_modal_editar_venta(self, item):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.suggestions = [{"key": i['codigo_insumo'], "value": f"[{i['codigo_insumo']}] {i['nombre']}"} for i in insumos]
        
        self.crud_item_id = item.get("id_venta")
        self.dlg_crud.title.value = "Editar Venta"
        
        cod = item.get("codigo_insumo", "")
        nom_bd = item.get("catalogo_insumos", {}).get("nombre", "")
        nom_desc = item.get("descripcion", "")
        nom_final = nom_bd if nom_bd else nom_desc
        
        self.crud_codigo_insumo.value = f"[{cod}] {nom_final}" if cod else ""
        self.crud_fecha.value = str(item.get("fecha") or "")[:10]
        self.crud_factura.value = str(item.get("factura_no") or "")
        self.crud_tipo_doc.value = str(item.get("tipo_documento") or "Remisión")
        
        cant = float(item.get("cantidad") or 0)
        self.crud_cantidad.value = str(int(cant)) if cant.is_integer() else str(cant)
        
        self.crud_precio_unit.value = str(item.get("subtotal") or 0)
        self.crud_descuento.value = str(item.get("descuento") or 0)
        self.crud_iva.value = str(item.get("iva") or 0)
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def guardar_venta_formulario(self, e):
        cod_raw = self.crud_codigo_insumo.value
        if not cod_raw or "[" not in cod_raw or "]" not in cod_raw:
            self.page.snack_bar = ft.SnackBar(ft.Text("Selecciona un insumo válido del listado."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        codigo_insumo = cod_raw.split("[")[1].split("]")[0]
        
        try:
            cant = float(self.crud_cantidad.value or 0)
            precio = float(self.crud_precio_unit.value or 0)
            desc = float(self.crud_descuento.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * precio) + iva - desc
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Revisa los valores numéricos ingresados."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        datos = {
            "fecha": self.crud_fecha.value,
            "factura_no": self.crud_factura.value,
            "tipo_documento": self.crud_tipo_doc.value,
            "codigo_insumo": codigo_insumo,
            "cantidad": cant,
            "subtotal": precio,
            "descuento": desc,
            "iva": iva,
            "total": tot
        }
        
        if self.crud_item_id:
            # Edit
            ok = self.db.update_venta_individual(self.crud_item_id, datos)
            msg = "Venta actualizada exitosamente."
        else:
            # Create
            datos["estado_registro"] = "VÁLIDO"
            ok = self.db.insert_venta_individual(datos)
            msg = "Venta registrada exitosamente."
            
        if ok:
            self._cerrar_crud()
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green")
            self.page.snack_bar.open = True
            self.load_data()
            self.load_summary()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar la venta en la BD."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()

    def confirmar_eliminar_venta(self, item):
        id_venta = item.get("id_venta")
        cant = float(item.get("cantidad") or 0)
        
        cat_info = item.get("catalogo_insumos", {})
        nom_bd = cat_info.get("nombre") if isinstance(cat_info, dict) else None
        insumo = nom_bd or item.get("descripcion", "Desconocido")
        
        fact = item.get("factura_no") or "S/D"
        tot = float(item.get("total") or 0)
        
        def do_eliminar(e):
            dlg.open = False
            self.safe_update()
            if self.db.eliminar_venta_individual(id_venta):
                self.page.snack_bar = ft.SnackBar(ft.Text("Venta eliminada y stock reincorporado."), bgcolor="green")
                self.page.snack_bar.open = True
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar la venta en la BD."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                ft.Text("Eliminar Registro de Venta", color="red700")
            ]),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(f"Insumo: {insumo}", weight="bold"),
                    ft.Text(f"N° Factura: {fact}"),
                    ft.Text(f"Cantidad: {cant:g} unds"),
                    ft.Text(f"Total Venta: ${tot:,.2f}", color="green700", weight="bold"),
                    ft.Divider(),
                    ft.Text(
                        f"⚠️ ADVERTENCIA: Al eliminar este registro de venta, se devolverán {cant:g} unidades al inventario disponible (reincorporación de stock) y se restará del histórico de ingresos.",
                        color="red900", weight="bold"
                    )
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), self.safe_update())),
                ft.ElevatedButton("Eliminar Definitivamente", bgcolor="red700", color="white", on_click=do_eliminar)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()
    # --- FIN CRUD MANUAL VENTAS ---
