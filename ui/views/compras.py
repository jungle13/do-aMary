import flet as ft
import threading
import time
import json
import os
import datetime
from pypdf import PdfReader, PdfWriter
from config import Config
from core.supabase_client import SupabaseClient
from core.gemini_parser import GeminiParser
import math
from ui.components.autocomplete import CustomAutoComplete

class ComprasView(ft.Container):
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
        
        # --- ESTADO PANEL HISTÓRICO ---
        self.panel_abierto = False
        self.fecha_historial_activa = datetime.date.today().strftime("%Y-%m-%d")
        self.modo_agrupacion_compras = "FACTURA" # "FACTURA" o "PROVEEDOR"
        self.filtro_factura_activo = None
        self.filtro_proveedor_activo = None
        self.date_picker_compras_timeline = ft.DatePicker(on_change=self.on_date_compras_timeline_change)
        # ------------------------------
        
        # Controles de Búsqueda
        def on_select_busqueda_compras(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            if "[" in texto and "]" in texto:
                query = texto.split("]")[0].replace("[", "").strip()
            elif "Factura: " in texto:
                query = texto.replace("Factura: ", "").strip()
            elif "Proveedor: " in texto:
                query = texto.replace("Proveedor: ", "").strip()
            else:
                query = texto.strip()
            self.search_input_text.value = query
            self.on_search(None)

        self.search_input_text = ft.TextField(visible=False)

        self.search_autocomplete = CustomAutoComplete(
            hint_text="Buscar por código, proveedor o factura...",
            on_select=on_select_busqueda_compras,
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
            on_click=self.abrir_modal_crear_compra,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Dashboard Resumen
        self.lbl_compras_mes = ft.Text("$0", size=20, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_compras_hoy = ft.Text("$0", size=20, weight="bold", color="green")
        self.lbl_cantidad = ft.Text("0", size=20, weight="bold")
        
        self.summary_container = ft.Container(
            content=ft.Row([
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Total Compras en el Mes"), self.lbl_compras_mes]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Total Compras Hoy"), self.lbl_compras_hoy]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Cantidad Productos Comprados"), self.lbl_cantidad]), padding=5), expand=True),
            ])
        )
        
        self.btn_agregar = ft.ElevatedButton(
            text="Agregar Compra",
            icon=ft.icons.ADD,
            bgcolor=Config.COLOR_SECONDARY,
            color="white",
            height=40,
            on_click=self.on_agregar_click,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # File Picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        
        # Diálogo de Carga
        self.lbl_loading_text = ft.Text("Preparando archivo...", text_align=ft.TextAlign.CENTER)
        self.dlg_loading = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesando con Inteligencia Artificial"),
            content=ft.Column([
                ft.ProgressRing(),
                self.lbl_loading_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
        )
        
        # Diálogo de Confirmación (se construirá dinámicamente)
        self.dlg_confirm = ft.AlertDialog(modal=True)
        
        # Tabla de Datos
        self.data_table = ft.DataTable(
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("Fecha", weight="bold")),
                ft.DataColumn(ft.Text("No. Factura", weight="bold")),
                ft.DataColumn(ft.Text("Proveedor", weight="bold")),
                ft.DataColumn(ft.Text("Código Item", weight="bold")),
                ft.DataColumn(ft.Container(content=ft.Text("Nombre", weight="bold"), width=230)),
                ft.DataColumn(ft.Text("Cantidad", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Unit.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("IVA", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Total", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, tooltip="Página Anterior", on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, tooltip="Página Siguiente", on_click=self.on_next_page, disabled=True)
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        # --- TAB 2: GESTIÓN DE CARGAS ---
        self.cargas_file = "cargas_compras_locales.json"
        self.cargas_data = {}
        self._load_cargas()
        
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
        
        self.drop_filtro_estado_cargas = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Procesado con éxito"), ft.dropdown.Option("Falló"), ft.dropdown.Option("Guardado"), ft.dropdown.Option("Sobreescrito")],
            value="Todos", label="Estado", dense=True, width=170, border_radius=8, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8), height=38,
            on_change=lambda e: self._render_tabla_cargas()
        )
        
        self.table_cargas = ft.DataTable(
            data_row_min_height=40,
            data_row_max_height=40,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("ID", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Página", weight="bold")),
                ft.DataColumn(ft.Text("Archivo Original", weight="bold")),
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
        
        # --- NUEVO MODAL DE METADATOS ---
        self.fecha_carga_actual = datetime.date.today().strftime("%Y-%m-%d")
        self.date_picker_cargas = ft.DatePicker(on_change=self.on_date_cargas_change)
        self.fecha_carga_btn = ft.OutlinedButton(
            text=self.fecha_carga_actual, icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_cargas.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=40, width=250
        )
        self.dlg_metadatos_pdf = ft.AlertDialog(
            modal=True,
            title=ft.Text("Selecciona la Fecha de la Carga"),
            content=ft.Column([
                ft.Text("Fecha asignada a las compras del PDF:", size=12, color="grey", weight="bold"),
                self.fecha_carga_btn
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cerrar_modal_metadatos),
                ft.ElevatedButton("Seleccionar Archivo PDF", on_click=self._abrir_file_picker_desde_modal)
            ]
        )
        
        # --- PREPARACIÓN DE LAS PESTAÑAS (TABS) ---
        
        # 1. Contenido Tab 1: Registro Compras
        row_filtros_compras = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            ft.Container(expand=True),
            self.btn_crear_manual
        ])
        
        contenedor_tabla_compras = ft.Container(
            content=ft.Row([ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        footer_paginacion = ft.Container(
            content=ft.Row([self.lbl_total, ft.Container(expand=True), self.btn_prev, self.lbl_page_info, self.btn_next], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=10)
        )
        
        layout_tab_compras = ft.Container(
            content=ft.Column([row_filtros_compras, contenedor_tabla_compras, footer_paginacion], expand=True, spacing=10),
            padding=10
        )
        
        # 2. Contenido Tab 2: Gestión de Cargas
        self.btn_extraer_todo = ft.ElevatedButton(
            text="Extraer Todo",
            icon=ft.icons.AUTO_MODE,
            bgcolor="purple700",
            color="white",
            height=40,
            on_click=self.on_extraer_todo_masivo,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        row_filtros_tab_cargas = ft.Row([
            self.btn_filtro_fecha_cargas,
            self.btn_clear_filtro_cargas,
            self.drop_filtro_estado_cargas,
            ft.Container(expand=True),
            self.btn_extraer_todo,
            ft.ElevatedButton(
                text="Subir PDF de Compras", icon=ft.icons.CLOUD_UPLOAD, bgcolor=Config.COLOR_SECONDARY, color="white", height=40,
                on_click=self.on_agregar_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
        ])
        
        contenedor_tabla_cargas = ft.Container(
            content=ft.Row([ft.Column([self.table_cargas], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        layout_tab_cargas = ft.Container(
            content=ft.Column([row_filtros_tab_cargas, contenedor_tabla_cargas], expand=True, spacing=10),
            padding=10
        )
        
        # Integrar las Pestañas
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Registro de Compras", content=layout_tab_compras, icon=ft.icons.SHOPPING_CART),
                ft.Tab(text="Gestión de Cargas", content=layout_tab_cargas, icon=ft.icons.FILE_UPLOAD),
            ],
            expand=True
        )

        # --- DISEÑO DEL PANEL HISTÓRICO ---
        self.lbl_tot_compras_panel = ft.Text("$0 COP", size=14, weight="bold", color="teal800")
        self.lbl_cant_compras_panel = ft.Text("0 unds", size=10, color="grey")

        kpi_compras_panel = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.SHOPPING_BAG, color="teal700", size=20),
                ft.Column([
                    ft.Text("TOTAL COMPRAS DEL DÍA", size=9, weight="bold", color="grey"),
                    self.lbl_tot_compras_panel
                ], spacing=0, expand=True),
                self.lbl_cant_compras_panel
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, bgcolor="#e6f4ea", border_radius=8, border=ft.border.all(1, "#c3e6cb")
        )

        self.segment_agrupacion = ft.SegmentedButton(
            segments=[
                ft.Segment(value="FACTURA", label=ft.Text("Por Factura", size=10)),
                ft.Segment(value="PROVEEDOR", label=ft.Text("Por Proveedor", size=10)),
            ],
            selected={"FACTURA"},
            on_change=self.on_agrupacion_change,
            show_selected_icon=False
        )

        self.btn_fecha_compras_panel = ft.OutlinedButton(
            self.fecha_historial_activa,
            icon=ft.icons.CALENDAR_TODAY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=5),
            height=30,
            on_click=lambda e: self.date_picker_compras_timeline.pick_date()
        )

        self.panel_compras_list = ft.ListView(expand=True, spacing=6)

        # Botón para copiar histórico de compras
        self.btn_copiar_compras_panel = ft.IconButton(
            icon=ft.icons.COPY_ROUNDED,
            icon_size=16,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Copiar Histórico de Compras al Portapapeles",
            on_click=self.copiar_historial_compras
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
                        ft.Text("Histórico de Entradas", weight="bold", size=13, color=Config.COLOR_PRIMARY, expand=True),
                        self.btn_copiar_compras_panel,
                        self.btn_fecha_compras_panel,
                        ft.IconButton(ft.icons.CLOSE, icon_size=16, on_click=self.toggle_right_panel)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=10, bgcolor="#f4f6f8", border_radius=ft.border_radius.only(top_left=8, top_right=8)
                ),
                ft.Container(content=kpi_compras_panel, padding=ft.padding.symmetric(horizontal=10)),
                ft.Container(content=self.segment_agrupacion, padding=ft.padding.symmetric(horizontal=10), alignment=ft.alignment.center),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Container(content=self.panel_compras_list, expand=True, padding=10)
            ], spacing=8)
        )

        self.filtro_badge_compras = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.FILTER_ALT, size=14, color="white"),
                ft.Text("Filtro Activo", color="white", weight="bold", size=11),
                ft.IconButton(
                    ft.icons.CLOSE, icon_size=14, icon_color="white",
                    on_click=self.limpiar_filtro_compras,
                    style=ft.ButtonStyle(padding=0), width=20, height=20
                )
            ], tight=True),
            bgcolor="teal700", padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=12, visible=False
        )

        self.btn_toggle_panel = ft.IconButton(
            icon=ft.icons.HISTORY_TOGGLE_OFF,
            tooltip="Ver Histórico de Compras del Día",
            on_click=self.toggle_right_panel
        )

        self.lbl_titulo = ft.Text("Módulo de Compras", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        main_column = ft.Column([
            self.progress_bar,
            ft.Row([self.lbl_titulo, self.filtro_badge_compras, ft.Container(expand=True), self.btn_toggle_panel, self.btn_fullscreen]),
            self.summary_container,
            self.tabs
        ], expand=True, spacing=10)

        self.content = ft.Row([
            main_column,
            self.right_panel
        ], expand=True, spacing=10)
        
        self.load_data()
        self._render_tabla_cargas()

    def toggle_right_panel(self, e):
        self.panel_abierto = not self.panel_abierto
        self.right_panel.width = 330 if self.panel_abierto else 0
        self.right_panel.visible = self.panel_abierto
        self.right_panel.padding = 0
        self.btn_toggle_panel.icon = ft.icons.HISTORY if self.panel_abierto else ft.icons.HISTORY_TOGGLE_OFF
        if self.panel_abierto:
            self.cargar_historial_panel()
        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def on_date_compras_timeline_change(self, e):
        if self.date_picker_compras_timeline.value:
            self.fecha_historial_activa = self.date_picker_compras_timeline.value.strftime("%Y-%m-%d")
            self.btn_fecha_compras_panel.text = self.fecha_historial_activa
            self.cargar_historial_panel()

    def on_agrupacion_change(self, e):
        if e.control.selected:
            self.modo_agrupacion_compras = list(e.control.selected)[0]
            self.cargar_historial_panel()

    def cargar_historial_panel(self):
        if not self.page: return

        def worker():
            items = self.db.get_historial_compras_dia(self.fecha_historial_activa, self.modo_agrupacion_compras)

            tot_pesos = sum([item["total"] for item in items])
            tot_unds = sum([item["unidades"] for item in items])

            self.lbl_tot_compras_panel.value = f"${tot_pesos:,.0f} COP"
            self.lbl_cant_compras_panel.value = f"{tot_unds:g} unds"

            self.panel_compras_list.controls.clear()

            for item in items:
                self.panel_compras_list.controls.append(self._crear_card_item_compras(item))

            if not self.panel_compras_list.controls:
                self.panel_compras_list.controls.append(
                    ft.Container(content=ft.Text("Sin compras registradas en esta fecha.", size=11, color="grey"), padding=20, alignment=ft.alignment.center)
                )

            if hasattr(self, "safe_update"):
                self.safe_update()
            else:
                self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _crear_card_item_compras(self, item):
        tipo = item["tipo"]

        if tipo == "COMPRA":
            badge_txt = f"FACTURA: {item['factura']}"
            badge_bg, badge_col = "#e6f4ea", "teal800"
            sub_txt = item["proveedor"]
            icon_mat = ft.icons.RECEIPT
        elif tipo == "PROVEEDOR_RESUMEN":
            badge_txt = f"{item['facturas_cant']} Facturas"
            badge_bg, badge_col = "#e8f0fe", "blue800"
            sub_txt = item["proveedor"]
            icon_mat = ft.icons.BUSINESS
        else:
            # AJUSTE_ENTRADA
            badge_txt = "ENTRADA AJUSTE (+)"
            badge_bg, badge_col = "#fef3c7", "orange800"
            sub_txt = item["factura"]
            icon_mat = ft.icons.TUNE

        badge = ft.Container(
            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_col, no_wrap=True),
            padding=ft.padding.symmetric(horizontal=6, vertical=2), bgcolor=badge_bg, border_radius=10
        )

        card = ft.Container(
            content=ft.Row([
                ft.Icon(icon_mat, size=16, color="teal700"),
                ft.Column([
                    badge,
                    ft.Text(sub_txt, size=11, weight="bold", color="black87", no_wrap=True, tooltip=sub_txt),
                ], expand=True, spacing=2),
                ft.Column([
                    ft.Text(f"${item['total']:,.0f}", size=11, weight="bold", color="black87"),
                    ft.Text(f"{item['unidades']:g} unds", size=9, color="grey", text_align=ft.TextAlign.RIGHT)
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=1)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=8,
            border_radius=6,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#eeeeee"),
            on_click=lambda e, i=item: self.aplicar_filtro_cruzado_compras(i),
            ink=True
        )
        return card

    def aplicar_filtro_cruzado_compras(self, item):
        tipo = item["tipo"]
        self.progress_bar.visible = True
        if hasattr(self, "safe_update"):
            self.safe_update()
        else:
            self.page.update()

        if tipo == "PROVEEDOR_RESUMEN":
            self.filtro_proveedor_activo = item["proveedor"]
            self.filtro_factura_activo = None
            desc = f"Proveedor: {item['proveedor']}"
        else:
            self.filtro_factura_activo = item["ref"]
            self.filtro_proveedor_activo = None
            desc = f"Factura: {item['factura']}"

        lbl = self.filtro_badge_compras.content.controls[1]
        lbl.value = desc
        self.filtro_badge_compras.visible = True

        self.current_page = 1
        self.load_data()

    def limpiar_filtro_compras(self, e=None):
        self.filtro_factura_activo = None
        self.filtro_proveedor_activo = None
        self.filtro_badge_compras.visible = False
        self.current_page = 1
        self.load_data()

    def _load_cargas(self):
        if os.path.exists(self.cargas_file):
            try:
                with open(self.cargas_file, "r", encoding="utf-8") as f:
                    self.cargas_data = json.load(f)
            except Exception:
                self.cargas_data = {}
        else:
            self.cargas_data = {}

    def _save_cargas(self):
        try:
            with open(self.cargas_file, "w", encoding="utf-8") as f:
                json.dump(self.cargas_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error guardando cargas: {e}")

    def on_date_cargas_change(self, e):
        if self.date_picker_cargas.value:
            self.fecha_carga_actual = self.date_picker_cargas.value.strftime("%Y-%m-%d")
            self.fecha_carga_btn.text = self.fecha_carga_actual
            if self.page:
                self.page.update()

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
        self.btn_filtro_fecha_cargas.tooltip = "Filtrar por Fecha"
        self.btn_filtro_fecha_cargas.icon_color = None
        self.btn_clear_filtro_cargas.visible = False
        self.date_picker_filtro_cargas.value = None
        if self.page:
            self.page.update()
        self._render_tabla_cargas()

    def _render_tabla_cargas(self):
        self.table_cargas.rows.clear()
        
        lista_cargas = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                lista_cargas.append(data)
                
        # Ordenar por ID descendente (más nuevos arriba)
        lista_cargas.sort(key=lambda x: x["id"], reverse=True)
        
        for data in lista_cargas:
            # --- Filtrado Visual ---
            if self.fecha_filtro_cargas and data.get("fecha") != self.fecha_filtro_cargas:
                continue
                    
            if self.drop_filtro_estado_cargas.value != "Todos" and data.get("estado") != self.drop_filtro_estado_cargas.value:
                continue
            # -----------------------
            
            id_carga = data["id"]
            nombre = f"Página No. {data['pagina']} ({data['fecha']})"
            archivo_orig = os.path.basename(data.get("archivo_original", "Desconocido"))
            estado = data["estado"]
            
            txt_crono = ft.Text("⏱️ 20s", color="red", weight="bold", visible=False)
            
            texto_btn = "Extraer Datos" if estado in ["Nuevo", "Falló", "Sobreescrito"] else "Ver"
            color_btn = Config.COLOR_PRIMARY if texto_btn == "Extraer Datos" else "grey"
            icon_btn = ft.icons.DOCUMENT_SCANNER if texto_btn == "Extraer Datos" else ft.icons.VISIBILITY
            
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
                icon_color="red",
                tooltip="Eliminar Carga",
                on_click=lambda e, d=data: self.on_eliminar_carga(d)
            )
            
            acciones_row = ft.Row([btn_accion, txt_crono, btn_eliminar], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            color_estado = "black"
            if estado == "Procesado con éxito": color_estado = "green"
            elif estado == "Falló": color_estado = "red"
            elif estado == "Guardado": color_estado = "blue"
            elif estado == "Sobreescrito": color_estado = "orange"
            
            self.table_cargas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(id_carga))),
                        ft.DataCell(ft.Text(nombre, weight="bold")),
                        ft.DataCell(ft.Text(archivo_orig[:20] + "..." if len(archivo_orig) > 20 else archivo_orig, tooltip=archivo_orig)),
                        ft.DataCell(ft.Text(estado, color=color_estado, weight="bold")),
                        ft.DataCell(acciones_row),
                    ]
                )
            )
            
        if self.page:
            self.page.update()


    def on_eliminar_carga(self, data):
        grupo_key = data.get("fecha")
        num_pag = str(data.get("pagina"))
        estado = data.get("estado")
        id_carga = data["id"]
        
        if estado == "Guardado":
            datos_ext = data.get("datos_extraidos", [])
            filas_resumen = []
            lista_eas = []
            cant_tot = 0.0
            costo_tot = 0.0

            for inv in datos_ext:
                ea = inv.get("numero_entrada") or inv.get("numero_factura") or ""
                if ea and ea not in lista_eas:
                    lista_eas.append(ea)
                    
                for p in inv.get("productos", []):
                    cod = p.get("codigo_insumo", "")
                    nom = getattr(self, 'nombres_insumos', {}).get(cod, f"Insumo [{cod}]")
                    cant = float(p.get("cantidad") or 0)
                    costo = float(p.get("costo_unitario") or 0)
                    iva = float(p.get("iva") or 0)
                    subtot = (cant * costo) + iva
                    
                    cant_tot += cant
                    costo_tot += subtot
                    
                    filas_resumen.append(
                        ft.Row([
                            ft.Text(f"• [{cod}] {nom[:22]}", size=11, expand=True, weight="bold"),
                            ft.Text(f"{cant:g} unds", size=11, color="grey"),
                            ft.Text(f"${subtot:,.0f}", size=11, weight="bold", color="red700")
                        ])
                    )

            if not filas_resumen:
                filas_resumen.append(ft.Text("Sin detalle de insumos registrado.", size=11, color="grey"))

            def confirmar_eliminar_guardado(e):
                dlg.open = False
                self.safe_update()
                
                # 1. Eliminar en Supabase
                exito = self.db.eliminar_compras_por_entradas(lista_eas)
                if exito:
                    # 2. Remover localmente
                    if grupo_key in self.cargas_data and num_pag in self.cargas_data[grupo_key]:
                        del self.cargas_data[grupo_key][num_pag]
                        if not self.cargas_data[grupo_key]:
                            del self.cargas_data[grupo_key]
                    self._save_cargas()
                    
                    self.page.snack_bar = ft.SnackBar(ft.Text("Carga e inventario revertidos exitosamente."), bgcolor="orange700")
                    self.page.snack_bar.open = True
                    self.load_data()
                    self.load_summary()
                    self._render_tabla_cargas()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar registros en base de datos."), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.safe_update()

            def cerrar_dialogo_guardado(e):
                dlg.open = False
                self.safe_update()

            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                    ft.Text("Eliminar Carga Guardada (Afecta BD)", size=16, weight="bold", color="red700")
                ]),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(
                                "⚠️ ATENCIÓN: Esta carga ya fue guardada en el sistema. Al eliminarla se BORRARÁN DEFINITIVAMENTE los siguientes movimientos de compra de Supabase y se REVERTIRÁ EL STOCK DEL INVENTARIO:",
                                size=11, color="red900", weight="bold"
                            ),
                            padding=10, bgcolor="#fde8e8", border_radius=6
                        ),
                        ft.Text("Insumos que se eliminarán:", size=12, weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(
                            content=ft.Column(filas_resumen, scroll=ft.ScrollMode.AUTO),
                            height=180,
                            padding=8, bgcolor="#f8f9fa", border_radius=6, border=ft.border.all(1, "#e0e0e0")
                        ),
                        ft.Divider(height=5),
                        ft.Row([
                            ft.Text("Total Productos:", size=11, color="grey"),
                            ft.Text(f"{cant_tot:g} unds", size=11, weight="bold"),
                            ft.Container(expand=True),
                            ft.Text("Costo Total a Revertir:", size=11, color="grey"),
                            ft.Text(f"${costo_tot:,.0f}", size=12, weight="bold", color="red700")
                        ])
                    ], tight=True, spacing=10),
                    width=450
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo_guardado),
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

            def cerrar_dialogo_simple(e):
                dlg.open = False
                self.safe_update()

            dlg = ft.AlertDialog(
                title=ft.Text("Eliminar Carga de la Lista"),
                content=ft.Text(f"¿Estás seguro de eliminar la Página No. {data['pagina']} ({data['fecha']})? Esta carga aún no ha afectado la base de datos."),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo_simple),
                    ft.ElevatedButton("Eliminar", bgcolor="red700", color="white", on_click=confirmar_eliminar_simple)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.safe_update()

    def on_accion_carga(self, e, data, txt_crono):
        btn = e.control
        if btn.text == "Ver":
            self.carga_activa = data
            self.parsed_data = data.get("datos_extraidos", [])
            
            codigos_extraidos = set()
            for invoice in self.parsed_data:
                for p in invoice.get("productos", []):
                    codigos_extraidos.add(str(p.get("codigo_insumo", "")))
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

        self.is_extraccion_activa = True
        btn.text = "Extrayendo..."
        btn.icon = ft.icons.HOURGLASS_TOP
        
        for row in self.table_cargas.rows:
            accion_row = row.cells[-1].content
            b = accion_row.controls[0]
            if b.text == "Extraer Datos":
                b.disabled = True
                
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Analizando documento con Inteligencia Artificial..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()
        
        threading.Thread(target=self._worker_extraccion, args=(data, btn, txt_crono), daemon=True).start()

    def _worker_extraccion(self, data, btn, txt_crono):
        try:
            extracted = self.ai_parser.parse_compras_pdf_page(data["archivo"], 0)
            
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
            
            txt_crono.visible = True
            btn.text = "Enfriando..."
            btn.icon = ft.icons.TIMER
            for i in range(20, 0, -1):
                txt_crono.value = f"⏱️ {i}s"
                if self.page:
                    self.page.update()
                time.sleep(1)
                
        except Exception as ex:
            data["estado"] = "Falló"
            self._save_cargas()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error en extracción: {ex}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            self.is_extraccion_activa = False
            self._render_tabla_cargas()
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
        # Agregar los overlays a la página principal
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        if self.dlg_loading not in self.page.overlay:
            self.page.overlay.append(self.dlg_loading)
        if self.dlg_confirm not in self.page.overlay:
            self.page.overlay.append(self.dlg_confirm)
        if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        if hasattr(self, "date_picker_compras_timeline") and self.date_picker_compras_timeline not in self.page.overlay:
            self.page.overlay.append(self.date_picker_compras_timeline)
            
        # Nuevos overlays para Cargas
        if hasattr(self, "dlg_metadatos_pdf") and self.dlg_metadatos_pdf not in self.page.overlay:
            self.page.overlay.append(self.dlg_metadatos_pdf)
        if hasattr(self, "date_picker_cargas") and self.date_picker_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_cargas)
        if hasattr(self, "date_picker_filtro_cargas") and self.date_picker_filtro_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_filtro_cargas)
            
        self.page.update()
        self.load_summary()
        self.cargar_sugerencias_compras()
        self.load_data()

    def cargar_sugerencias_compras(self):
        compras, _ = self.db.get_compras(page=1, page_size=1000)
        sug_set = set()
        for c in compras:
            cat_info = c.get("catalogo_insumos") or {}
            cod = c.get("codigo_insumo")
            nom = cat_info.get("nombre")
            prov = c.get("proveedor")
            fact = c.get("numero_factura")
            
            if cod and nom: sug_set.add(f"[{cod}] {nom}")
            if prov and prov != "N/A": sug_set.add(f"Proveedor: {prov}")
            if fact: sug_set.add(f"Factura: {fact}")

        self.search_autocomplete.suggestions = [
            {"key": str(idx), "value": val}
            for idx, val in enumerate(sorted(sug_set))
        ]
        if hasattr(self, 'safe_update'):
            self.safe_update()
        elif self.page:
            self.page.update()
        
    def load_summary(self):
        res = self.db.get_compras_summary()
        self.lbl_compras_mes.value = f"${res.get('total_mes', 0):,.2f}"
        self.lbl_compras_hoy.value = f"${res.get('total_hoy', 0):,.2f}"
        self.lbl_cantidad.value = f"{res.get('cantidad_total', 0):,.2f}"
        if self.page:
            self.update()
            
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
        
    def on_agregar_click(self, e):
        # En lugar de abrir file_picker, abrimos el modal de metadatos
        self.dlg_metadatos_pdf.open = True
        if self.page:
            self.page.update()

    def _cerrar_modal_metadatos(self, e=None):
        self.dlg_metadatos_pdf.open = False
        if self.page:
            self.page.update()

    def _abrir_file_picker_desde_modal(self, e):
        self.fecha_seleccionada = self.fecha_carga_actual
        self._cerrar_modal_metadatos()
        self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"], dialog_title="Selecciona el Reporte de Compras")

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            pdf_path = e.files[0].path
            
            self.lbl_loading_text.value = "Dividiendo PDF en páginas..."
            self.dlg_loading.open = True
            self.page.update()
            
            threading.Thread(target=self._dividir_y_guardar_pdf, args=(pdf_path,), daemon=True).start()

    def _dividir_y_guardar_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            grupo_key = self.fecha_seleccionada
            if grupo_key not in self.cargas_data:
                self.cargas_data[grupo_key] = {}
                
            paginas_existentes = [int(p) for p in self.cargas_data[grupo_key].keys()]
            max_pagina = max(paginas_existentes) if paginas_existentes else 0
            
            max_id = 0
            for k, pags in self.cargas_data.items():
                for p_num, d in pags.items():
                    if d.get("id", 0) > max_id:
                        max_id = d["id"]
            
            os.makedirs("pdfs_locales", exist_ok=True)
            
            for p_idx in range(total_pages):
                num_pag = max_pagina + p_idx + 1
                id_carga = max_id + p_idx + 1
                
                writer = PdfWriter()
                writer.add_page(reader.pages[p_idx])
                
                nombre_archivo = f"compra_{grupo_key}_pag_{num_pag}.pdf"
                ruta_local = os.path.join("pdfs_locales", nombre_archivo)
                
                with open(ruta_local, "wb") as f:
                    writer.write(f)
                    
                self.cargas_data[grupo_key][str(num_pag)] = {
                    "id": id_carga,
                    "fecha": grupo_key,
                    "pagina": num_pag,
                    "archivo_original": pdf_path,
                    "archivo": ruta_local,
                    "estado": "Nuevo"
                }
                
            self._save_cargas()
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Se dividió el PDF en {total_pages} páginas exitosamente."), bgcolor="green")
            self.page.snack_bar.open = True
            
        except Exception as e:
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error procesando PDF: {e}"), bgcolor="red")
            self.page.snack_bar.open = True
            
        finally:
            if self.page:
                self.page.update()
                self._render_tabla_cargas()

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
            self.is_loading = False
            self.dlg_loading.open = False
            if self.page:
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
                    costo = float(item["costo_ctl"].value.replace(',', '.'))
                    iva = float(item["iva_ctl"].value.replace(',', '.'))
                    
                    row_total = (cant * costo) + iva
                    item["total_ctl"].value = f"${row_total:,.2f}"
                    
                    factura_idx = item["factura_idx"]
                    factura_totals[factura_idx] = factura_totals.get(factura_idx, 0) + row_total
                    
                    gran_cant += cant
                    gran_costo += costo
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
        # Guardar el contenido original de la vista para poder volver a él
        if not hasattr(self, "main_content"):
            self.main_content = self.content
            
        self.productos_rows = []
        facturas_count = len(self.parsed_data)
        productos_count = 0
        
        # Como ahora parsed_data es una lista de facturas, las iteramos todas
        for idx, invoice in enumerate(self.parsed_data):
            ea = invoice.get("numero_entrada", "")
            fecha = invoice.get("fecha", "")
            factura = invoice.get("numero_factura", "")
            proveedor = invoice.get("proveedor", "")
            
            total_factura_ctl = ft.Text("Total Factura: $0.00", weight="bold", color=Config.COLOR_PRIMARY)
            self.productos_rows.append({
                "type": "header",
                "factura_idx": idx,
                "total_factura_ctl": total_factura_ctl,
                "row_ctl": ft.Container(
                    content=ft.Row([
                        ft.Text(f"EA: {ea} | Factura: {factura} | Proveedor: {proveedor} | Fecha: {fecha}", weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(expand=True),
                        total_factura_ctl
                    ]),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY),
                    padding=5,
                    border_radius=5
                )
            })
            
            # Productos de esta factura
            for p in invoice.get("productos", []):
                productos_count += 1
                cod = str(p.get("codigo_insumo", ""))
                # Extraemos el nombre de la BD si existe, sino lo dejamos como "Desconocido"
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
                
                nombre_ctl = ft.Text(nombre[:25], width=180, no_wrap=True, tooltip=nombre)
                codigo_ctl = ft.TextField(label="Código", value=cod, width=90, dense=True, on_change=get_codigo_change_handler(nombre_ctl))
                cantidad_ctl = ft.TextField(label="Cant.", value=str(p.get("cantidad", 0)), width=70, dense=True, on_change=self.update_totals)
                costo_ctl = ft.TextField(label="Costo U.", value=str(p.get("costo_unitario", 0)), width=80, dense=True, on_change=self.update_totals)
                iva_ctl = ft.TextField(label="IVA", value=str(p.get("iva", 0)), width=80, dense=True, on_change=self.update_totals)
                total_ctl = ft.Text("$0.00", width=100, weight="bold")
                
                self.productos_rows.append({
                    "type": "product",
                    "factura_idx": idx,
                    "ea": ea,
                    "fecha": fecha,
                    "factura": factura,
                    "proveedor": proveedor,
                    "codigo_ctl": codigo_ctl,
                    "nombre_ctl": nombre_ctl,
                    "cantidad_ctl": cantidad_ctl,
                    "costo_ctl": costo_ctl,
                    "iva_ctl": iva_ctl,
                    "total_ctl": total_ctl,
                    "row_ctl": ft.Row([codigo_ctl, nombre_ctl, cantidad_ctl, costo_ctl, iva_ctl, total_ctl])
                })
            
        list_view = ft.ListView(
            controls=[item["row_ctl"] for item in self.productos_rows],
            expand=True,
            spacing=10
        )
        
        # Resumen Visual y Controles de Totales
        self.txt_gran_cant = ft.Text("0", weight="bold")
        self.txt_gran_costo = ft.Text("$0", weight="bold")
        self.txt_gran_iva = ft.Text("$0", weight="bold")
        self.txt_gran_total = ft.Text("$0", weight="bold", size=18, color=Config.COLOR_PRIMARY)
        
        is_last_page = not (hasattr(self, 'total_pages_pdf') and self.current_page_idx < self.total_pages_pdf - 1)
        botones_acciones = [ft.TextButton("Volver", on_click=self.close_confirm_ui)]
        
        if not is_last_page:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar", bgcolor="grey", color="white", on_click=self.on_guardar_compra_partial))
            botones_acciones.append(ft.ElevatedButton("Confirmar y Continuar", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_compra))
        else:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar Todo", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_compra))
            
        # --- NUEVO DISEÑO DEL FOOTER ---
        # 1. Fila de Información Financiera (Estilo Dashboard)
        info_row = ft.Row([
            ft.Text("RESUMEN TOTAL", weight="bold", size=18, color=Config.COLOR_PRIMARY),
            ft.Container(expand=True), # Empuja los totales hacia la derecha
            
            ft.Column([ft.Text("Cant. Total", size=12, color="grey"), self.txt_gran_cant], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("Costo Base", size=12, color="grey"), self.txt_gran_costo], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("IVA Total", size=12, color="grey"), self.txt_gran_iva], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("GRAN TOTAL", size=12, color="grey", weight="bold"), self.txt_gran_total], spacing=2, horizontal_alignment="end"),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 2. Fila de Botones de Acción
        buttons_row = ft.Row([
            ft.Container(expand=True), # Empuja los botones hacia el extremo derecho
            *botones_acciones # Desempaqueta la lista de botones dinámicos
        ], alignment=ft.MainAxisAlignment.END)

        # 3. Contenedor Principal del Footer
        footer = ft.Container(
            content=ft.Column([
                info_row,
                ft.Divider(height=15, color=ft.colors.with_opacity(0.1, "black")),
                buttons_row
            ], spacing=0),
            bgcolor=ft.colors.with_opacity(0.03, Config.COLOR_PRIMARY),
            padding=20,
            border_radius=8,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY)),
            margin=ft.padding.only(top=10)
        )
        
        if hasattr(self, 'total_pages_pdf'):
            titulo = f"Datos Extraídos - Pág. No. {self.current_page_idx + 1} de {self.total_pages_pdf}"
        elif hasattr(self, 'carga_activa'):
            titulo = f"Datos Extraídos - Pág. No. {self.carga_activa.get('pagina', 1)}"
        else:
            titulo = "Revisión de Compras (Modo Inmersivo)"
        header = ft.Row([
            ft.Text(titulo, size=24, weight="bold"),
            ft.Text(f"{facturas_count} Facturas extraídas | {productos_count} Productos en total", color="grey")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Reemplazamos el contenido actual por el modo Inmersivo/Fullscreen
        self.content = ft.Column([
            header,
            ft.Divider(),
            ft.Row([
                ft.Container(width=90, content=ft.Text("Código", weight="bold")),
                ft.Container(width=180, content=ft.Text("Nombre (desde BD)", weight="bold")),
                ft.Container(width=70, content=ft.Text("Cantidad", weight="bold")),
                ft.Container(width=80, content=ft.Text("Costo U.", weight="bold")),
                ft.Container(width=80, content=ft.Text("IVA", weight="bold")),
                ft.Container(width=100, content=ft.Text("Costo Total", weight="bold"))
            ]),
            list_view,
            footer
        ], expand=True)
        
        self.update_totals()
        self.page.update()
        
    def close_confirm_ui(self, e):
        # Volver al diseño principal
        self.content = self.main_content
        self.page.update()
        
    def on_guardar_compra_partial(self, e):
        if hasattr(self, 'total_pages_pdf'):
            self.current_page_idx = self.total_pages_pdf
        self.on_guardar_compra(e)

    def on_guardar_compra(self, e):
        # 1. Bloquear interfaz y mostrar carga
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        if self.page:
            self.page.update()
            
        # 2. Lanzar worker de guardado
        import threading
        threading.Thread(target=self._guardar_compra_worker, args=(btn_control,), daemon=True).start()

    def _guardar_compra_worker(self, btn_control):
        try:
            compras_list = []
            lista_eas_to_delete = []
            
            # Si venimos del flujo nuevo de carga_activa:
            grupo_key = None
            pagina_origen = None
            if hasattr(self, 'carga_activa'):
                grupo_key = self.carga_activa["fecha"]
                pagina_origen = self.carga_activa["pagina"]

            for item in self.productos_rows:
                if item["type"] == "product":
                    cant_str = str(item["cantidad_ctl"].value).replace(',', '.')
                    costo_str = str(item["costo_ctl"].value).replace(',', '.')
                    iva_str = str(item["iva_ctl"].value).replace(',', '.')
                    
                    cantidad = float(cant_str)
                    costo = float(costo_str)
                    iva = float(iva_str)
                    total = (cantidad * costo) + iva
                    
                    fecha_val = grupo_key if grupo_key else item["fecha"]
                    if not fecha_val:
                        import datetime
                        fecha_val = datetime.date.today().strftime("%Y-%m-%d")
                        
                    compras_list.append({
                        "numero_entrada": item["ea"],
                        "fecha": fecha_val,
                        "numero_factura": item["factura"],
                        "proveedor": item["proveedor"],
                        "codigo_insumo": item["codigo_ctl"].value,
                        "cantidad": cantidad,
                        "costo_unitario": costo,
                        "iva": iva,
                        "costo_total": total
                    })
                    
                    if item["ea"] not in lista_eas_to_delete:
                        lista_eas_to_delete.append(item["ea"])
                        
            if compras_list:
                codigos_unicos = list(set([c["codigo_insumo"] for c in compras_list]))
                codigos_validos = self.db.get_nombres_insumos(codigos_unicos)
                
                codigos_invalidos = [c for c in codigos_unicos if c not in codigos_validos]
                if codigos_invalidos:
                    if self.page:
                        self.page.snack_bar = ft.SnackBar(
                            ft.Text(f"Códigos no existen en catálogo: {', '.join(codigos_invalidos)}. Corrígelos en la tabla primero.", color="white"), 
                            bgcolor="red",
                            duration=8000
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                    return
            
            if compras_list:
                # 1. Eliminar datos viejos de esta misma página
                self.db.eliminar_compras_por_entradas(lista_eas_to_delete)
                
                # 2. Insertar los nuevos datos
                if self.db.insert_compras(compras_list):
                    self.page.snack_bar = ft.SnackBar(ft.Text("Página guardada exitosamente en BD."), bgcolor="green")
                    self.page.snack_bar.open = True
                    
                    # 3. Actualizar el estado local a Guardado
                    if grupo_key and str(pagina_origen) in self.cargas_data.get(grupo_key, {}):
                        self.cargas_data[grupo_key][str(pagina_origen)]["estado"] = "Guardado"
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
                    
        except ValueError:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico en cantidad, costo o IVA."), bgcolor="red")
                self.page.snack_bar.open = True
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            # 3. Restaurar interfaz incondicionalmente
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
                
            if self.page:
                self.page.update()
            
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        if self.page:
            self.update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        search_val = self.search_input_text.value or self.search_autocomplete.value or ""
        
        fact_filtro = getattr(self, 'filtro_factura_activo', None)
        prov_filtro = getattr(self, 'filtro_proveedor_activo', None)
        f_corte = getattr(self, 'fecha_corte', None)

        data, total = self.db.get_compras(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val,
            fecha_corte=f_corte,
            factura_filtro=fact_filtro,
            proveedor_filtro=prov_filtro
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        self.data_table.rows.clear()
        
        for item in data:
            fecha_raw = str(item.get('fecha', ''))
            # Cortar a 'YYYY-MM-DD' si viene con timestamp
            fecha_formateada = fecha_raw[:10] if len(fecha_raw) >= 10 else fecha_raw
            
            # El nombre viene del JOIN con catalogo_insumos: catalogo_insumos.nombre
            cat_info = item.get('catalogo_insumos') or {}
            nombre_insumo = cat_info.get('nombre', 'Desconocido')
            
            cantidad = int(item.get('cantidad', 0) or 0)
            costo_unit = float(item.get('costo_unitario', 0) or 0)
            costo_tot = float(item.get('costo_total', 0) or 0)
            
            iva_val = float(item.get('iva') or item.get('valor_iva') or 0)
            
            str_costo_unit = f"${costo_unit:,.2f}"
            str_iva = f"${iva_val:,.2f}"
            str_costo_tot = f"${costo_tot:,.2f}"
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(fecha_formateada)),
                    ft.DataCell(ft.Text(str(item.get('numero_factura') or 'N/A'))),
                    ft.DataCell(ft.Text(str(item.get('proveedor') or 'N/A'))),
                    ft.DataCell(ft.Text(str(item.get('codigo_insumo', '')))),
                    ft.DataCell(ft.Container(content=ft.Text(nombre_insumo), width=280)),
                    ft.DataCell(ft.Text(str(cantidad), weight="bold")),
                    ft.DataCell(ft.Text(str_costo_unit)),
                    ft.DataCell(ft.Text(str_iva)),
                    ft.DataCell(ft.Text(str_costo_tot, color="blue", weight="bold")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT_OUTLINED, icon_color="blue", tooltip="Editar", on_click=lambda e, i=item: self.abrir_modal_editar_compra(i)),
                            ft.IconButton(icon=ft.icons.DELETE_OUTLINED, icon_color="red", tooltip="Eliminar", on_click=lambda e, i=item: self.confirmar_eliminar_compra(i))
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

    def copiar_historial_compras(self, e):
        """
        Obtiene las compras del día agrupadas por proveedor y construye
        un texto limpio formateado para el portapapeles del sistema.
        """
        if not self.page: return

        def worker():
            # Consultar desglose exacto por proveedor para la fecha activa
            items_prov = self.db.get_historial_compras_dia(self.fecha_historial_activa, "PROVEEDOR")

            tot_pesos = self.lbl_tot_compras_panel.value
            tot_unds = self.lbl_cant_compras_panel.value

            lineas_prov = []
            for item in items_prov:
                prov = item.get("proveedor", "Clientes Varios")
                total = item.get("total", 0)
                unds = item.get("unidades", 0)
                fact_cant = item.get("facturas_cant", 1)
                lineas_prov.append(f"  • {prov}: ${total:,.0f} COP ({unds:g} unds | {fact_cant} fact.)")

            prov_text = "\n".join(lineas_prov) if lineas_prov else "  (Sin registros de proveedores)"

            texto_copia = (
                f"🛍️ HISTÓRICO DE ENTRADAS / COMPRAS\n"
                f"📅 Fecha: {self.fecha_historial_activa}\n"
                f"💵 Total Compras del Día: {tot_pesos} ({tot_unds})\n"
                f"-----------------------------------------\n"
                f"🏢 DESGLOSE POR PROVEEDOR:\n"
                f"{prov_text}\n"
                f"-----------------------------------------"
            )

            self.page.set_clipboard(texto_copia)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="white", size=18),
                    ft.Text("Histórico de compras copiado al portapapeles exitosamente", color="white")
                ]),
                bgcolor="teal700"
            )
            self.page.snack_bar.open = True

            if hasattr(self, "safe_update"):
                self.safe_update()
            else:
                self.page.update()

        import threading
        threading.Thread(target=worker, daemon=True).start()

    # --- INICIO CRUD MANUAL COMPRAS ---
    def _construir_modal_crud(self):
        self.crud_codigo_insumo = CustomAutoComplete(
            hint_text="Buscar insumo (Código o Nombre)",
            on_select=self._on_insumo_crud_select
        )
        self.crud_codigo_insumo.width = 350
        self.crud_fecha = ft.TextField(label="Fecha (YYYY-MM-DD)", width=150)
        self.crud_ea = ft.TextField(label="N° Entrada (EA)", width=150)
        self.crud_factura = ft.TextField(label="N° Factura", width=150)
        self.crud_proveedor = ft.TextField(label="Proveedor", width=250)
        self.crud_cantidad = ft.TextField(label="Cantidad", width=120, on_change=self._calc_tot_crud)
        self.crud_costo_unit = ft.TextField(label="Costo Unit.", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_iva = ft.TextField(label="IVA", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_total_lbl = ft.Text("$ 0.00", size=20, weight="bold", color="blue700")
        self.crud_item_id = None
        
        self.dlg_crud = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar Compra"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    self.crud_codigo_insumo,
                    ft.Row([self.crud_fecha, self.crud_ea, self.crud_factura]),
                    self.crud_proveedor,
                    ft.Row([self.crud_cantidad, self.crud_costo_unit, self.crud_iva]),
                    ft.Divider(height=10),
                    ft.Row([ft.Text("Costo Total:", size=16, weight="bold"), self.crud_total_lbl])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_crud()),
                ft.ElevatedButton("Guardar", bgcolor="blue700", color="white", on_click=self.guardar_compra_formulario)
            ]
        )

    def _on_insumo_crud_select(self, e):
        pass

    def _calc_tot_crud(self, e=None):
        try:
            cant = float(self.crud_cantidad.value or 0)
            cost = float(self.crud_costo_unit.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * cost) + iva
            self.crud_total_lbl.value = f"$ {tot:,.2f}"
            self.safe_update()
        except ValueError:
            self.crud_total_lbl.value = "$ 0.00"
            self.safe_update()

    def _cerrar_crud(self):
        self.dlg_crud.open = False
        self.safe_update()

    def abrir_modal_crear_compra(self, e=None):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.suggestions = [{"key": i['codigo_insumo'], "value": f"[{i['codigo_insumo']}] {i['nombre']}"} for i in insumos]
        
        self.crud_item_id = None
        self.dlg_crud.title.value = "Registrar Nueva Compra"
        self.crud_codigo_insumo.value = ""
        self.crud_fecha.value = datetime.date.today().strftime("%Y-%m-%d")
        self.crud_ea.value = ""
        self.crud_factura.value = ""
        self.crud_proveedor.value = ""
        self.crud_cantidad.value = ""
        self.crud_costo_unit.value = ""
        self.crud_iva.value = "0"
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def abrir_modal_editar_compra(self, item):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.suggestions = [{"key": i['codigo_insumo'], "value": f"[{i['codigo_insumo']}] {i['nombre']}"} for i in insumos]
        
        self.crud_item_id = item.get("id_compra")
        self.dlg_crud.title.value = "Editar Compra"
        
        cod = item.get("codigo_insumo", "")
        nom = item.get("catalogo_insumos", {}).get("nombre", "")
        self.crud_codigo_insumo.value = f"[{cod}] {nom}" if cod else ""
        self.crud_fecha.value = str(item.get("fecha") or "")[:10]
        self.crud_ea.value = str(item.get("numero_entrada") or "")
        self.crud_factura.value = str(item.get("numero_factura") or "")
        self.crud_proveedor.value = str(item.get("proveedor") or "")
        self.crud_cantidad.value = str(item.get("cantidad") or 0)
        self.crud_costo_unit.value = str(item.get("costo_unitario") or 0)
        self.crud_iva.value = str(item.get("iva") or item.get("valor_iva") or 0)
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def guardar_compra_formulario(self, e):
        cod_raw = self.crud_codigo_insumo.value
        if not cod_raw or "[" not in cod_raw or "]" not in cod_raw:
            self.page.snack_bar = ft.SnackBar(ft.Text("Selecciona un insumo válido del listado."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        codigo_insumo = cod_raw.split("[")[1].split("]")[0]
        
        try:
            cant = float(self.crud_cantidad.value or 0)
            costo = float(self.crud_costo_unit.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * costo) + iva
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Revisa los valores numéricos ingresados."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        datos = {
            "fecha": self.crud_fecha.value,
            "numero_entrada": self.crud_ea.value,
            "numero_factura": self.crud_factura.value,
            "proveedor": self.crud_proveedor.value,
            "codigo_insumo": codigo_insumo,
            "cantidad": cant,
            "costo_unitario": costo,
            "iva": iva,
            "valor_iva": iva,
            "costo_total": tot
        }
        
        if self.crud_item_id:
            # Edit
            ok = self.db.update_compra_individual(self.crud_item_id, datos)
            msg = "Compra actualizada exitosamente."
        else:
            # Create
            datos["estado_registro"] = "VÁLIDO"
            ok = self.db.insert_compras([datos])
            msg = "Compra registrada exitosamente."
            
        if ok:
            self._cerrar_crud()
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green")
            self.page.snack_bar.open = True
            self.load_data()
            self.load_summary()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar la compra en la BD."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()

    def confirmar_eliminar_compra(self, item):
        id_compra = item.get("id_compra")
        cant = float(item.get("cantidad") or 0)
        insumo = item.get("catalogo_insumos", {}).get("nombre", "Desconocido")
        ea = item.get("numero_entrada") or item.get("numero_factura") or "S/D"
        tot = float(item.get("costo_total") or 0)
        
        def do_eliminar(e):
            dlg.open = False
            self.safe_update()
            if self.db.eliminar_compra_individual(id_compra):
                self.page.snack_bar = ft.SnackBar(ft.Text("Compra eliminada y stock revertido."), bgcolor="green")
                self.page.snack_bar.open = True
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar la compra en la BD."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                ft.Text("Eliminar Registro de Compra", color="red700")
            ]),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(f"Insumo: {insumo}", weight="bold"),
                    ft.Text(f"N° Documento: {ea}"),
                    ft.Text(f"Cantidad: {cant:g} unds"),
                    ft.Text(f"Costo Total: ${tot:,.2f}", color="blue700", weight="bold"),
                    ft.Divider(),
                    ft.Text(
                        f"⚠️ ADVERTENCIA: Al eliminar este registro de compra, se restarán {cant:g} unidades del inventario disponible y se ajustará el histórico financiero.",
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
    # --- FIN CRUD MANUAL COMPRAS ---
