import flet as ft
import threading
import uuid
from config import Config
from core.supabase_client import SupabaseClient
from core.gemini_parser import GeminiParser
from core.fecha_utils import parsear_a_fecha_local, get_hoy_local_str, get_ahora_iso, formatear_fecha_hora_local
from core.audit_logger import registrar_accion
from ui.components.autocomplete import CustomAutoComplete
from ui.components.periodo_selector import PeriodoSelectorWidget

class AjustesInventarioView(ft.Container):
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
        self.gemini_parser = GeminiParser()
        self.tipo_ajuste_actual = "ENTRADA"
        
        # Mapeo estricto contra restricciones de BD
        self.mapa_motivos = {
            "Sobrante de Inventario": "ENTRADA_POR_SOBRANTE",
            "Donación Entrante": "AJUSTE_ENTRADA",
            "Devolución Cliente": "AJUSTE_ENTRADA",
            "Daño / Merma": "AJUSTE_SALIDA",
            "Vencimiento": "BAJA_VENCIMIENTO",
            "Pérdida": "SALIDA_POR_FALTANTE",
            "Consumo Familiar": "AJUSTE_SALIDA",
            "Consumo Cliente (Cortesía)": "AJUSTE_SALIDA",
            "Donación Saliente": "AJUSTE_SALIDA",
            "Otro (Entrada)": "AJUSTE_ENTRADA",
            "Otro (Salida)": "AJUSTE_SALIDA"
        }

        # --- Labels reactivos de Resumen (Tab 1) ---
        self.lbl_ent_actual = ft.Text("$0.00", weight="bold")
        self.lbl_ent_pos = ft.Text("$0.00", weight="bold", color="green")
        self.lbl_sal_neg = ft.Text("$0.00", weight="bold", color="red")
        self.lbl_ent_neto = ft.Text("$0.00", weight="bold")
        self.lbl_ent_proyectado = ft.Text("$0.00", weight="bold", color=Config.COLOR_PRIMARY)

        # --- Paginación y Filtros (Tab 1) ---
        self.data_completa = []
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        self.catalogo_completo = []
        self.catalogo_cache = {}

        def on_select_filtro_ajustes(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            if not texto or not texto.strip():
                self.search_input_text.value = ""
            elif "[" in texto and "]" in texto:
                self.search_input_text.value = texto.split("]")[0].replace("[", "").strip()
            else:
                self.search_input_text.value = texto.strip()
            self.current_page = 1
            self._on_filter_change()

        self.search_input_text = ft.TextField(visible=False)

        self.search_filter_autocomplete = CustomAutoComplete(
            hint_text="Buscar por código o nombre...",
            on_select=on_select_filtro_ajustes,
            text_size=12,
            height=40,
            expand=True
        )
        
        self.date_picker = ft.DatePicker(on_change=lambda e: self._on_filter_change())
        
        # Panel de Filtros Unificado (Colapsable)
        self.panel_filtros_abierto = False
        self.btn_toggle_filtros = ft.IconButton(
            icon=ft.icons.TUNE_ROUNDED,
            tooltip="Filtros de Ajustes",
            on_click=self.toggle_panel_filtros
        )

        self.btn_date_filtro = ft.OutlinedButton(
            text="Filtrar por Fecha",
            icon=ft.icons.CALENDAR_MONTH_ROUNDED,
            height=36,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=10, vertical=4)
            ),
            on_click=self._open_date_picker
        )
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            icon_color="red",
            visible=False,
            tooltip="Limpiar Fecha",
            on_click=self._clear_date
        )

        self.drop_tipo = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Entrada"), ft.dropdown.Option("Salida")],
            value="Todos", label="Tipo", dense=True, width=120, height=36, text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4), on_change=lambda e: self._on_filter_change()
        )

        self.drop_origen = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Cierre de Mes"), ft.dropdown.Option("Manual")],
            value="Todos", label="Origen", dense=True, width=135, height=36, text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4), on_change=lambda e: self._on_filter_change()
        )
        
        motivos_combinados = ["Todos"] + list(self.mapa_motivos.keys())
        self.drop_motivo = ft.Dropdown(
            options=[ft.dropdown.Option(m) for m in motivos_combinados],
            value="Todos", label="Motivo", dense=True, width=160, height=36, text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4), on_change=lambda e: self._on_filter_change()
        )

        self.btn_limpiar_todos_filtros = ft.TextButton(
            text="Limpiar Filtros",
            icon=ft.icons.CLEAR_ALL_ROUNDED,
            icon_color="red600",
            style=ft.ButtonStyle(color="red700"),
            on_click=self.limpiar_todos_los_filtros
        )

        self.panel_filtros = ft.Container(
            visible=False,
            bgcolor="white",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.03, "black")),
            content=ft.Row([
                self.btn_date_filtro,
                self.btn_clear_date,
                self.drop_tipo,
                self.drop_origen,
                self.drop_motivo,
                ft.Container(expand=True),
                self.btn_limpiar_todos_filtros
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, wrap=False)
        )

        self.btn_prev = ft.IconButton(icon=ft.icons.ARROW_BACK_IOS, icon_size=14, on_click=self._prev_page, disabled=True)
        self.btn_next = ft.IconButton(icon=ft.icons.ARROW_FORWARD_IOS, icon_size=14, on_click=self._next_page, disabled=True)
        self.lbl_page_info = ft.Text("Pág 1 de 1", size=11, weight="bold")

        # --- Vista de Tarjetas (Lista Tab 1) ---
        self.lista_ajustes = ft.ListView(expand=True, spacing=6, auto_scroll=False)
        self.btn_agregar_ajuste = ft.ElevatedButton(
            "Registrar Ajuste",
            icon=ft.icons.ADD,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=34,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=7),
                padding=ft.padding.symmetric(horizontal=10, vertical=0)
            ),
            on_click=lambda e: self.abrir_modal_ajuste()
        )

        # --- Modal Formulario Manual ---
        self.modal_ajuste = self._crear_modal_formulario()

        # =========================================================================
        # --- ESTADO Y CONTROLES TAB 2: AJUSTES ESCANEADOS CON IA (OCR) ---
        # =========================================================================
        self.items_escaneados = [] # Lista de dicts extraídos
        self.file_picker_ocr = ft.FilePicker(on_result=self._on_ocr_file_selected)

        self.lbl_badge_total_escaneados = ft.Text("0 escaneados", size=11, weight="bold", color="grey700")
        self.lbl_badge_validados = ft.Text("0 listos", size=11, weight="bold", color="green700")
        self.lbl_badge_pendientes_codigo = ft.Text("0 requieren código", size=11, weight="bold", color="orange800")
        
        self.btn_guardar_todos_validados = ft.ElevatedButton(
            "Guardar Validados",
            icon=ft.icons.DONE_ALL_ROUNDED,
            bgcolor=Config.COLOR_SUCCESS,
            color="white",
            height=34,
            visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=7)),
            on_click=self.guardar_todos_escaneados_validados
        )

        self.btn_limpiar_escaneados = ft.TextButton(
            "Limpiar",
            icon=ft.icons.DELETE_SWEEP_ROUNDED,
            icon_color="red",
            style=ft.ButtonStyle(color="red"),
            visible=False,
            on_click=self.limpiar_lista_escaneados
        )

        self.ocr_loading_container = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=18, height=18, stroke_width=2.5, color=Config.COLOR_ACCENT),
                ft.Text("Analizando formato físico con Gemini Flash... Extrayendo productos y motivos...", size=12, color=Config.COLOR_PRIMARY, weight="w500")
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            padding=12,
            bgcolor="#EFF6FF",
            border_radius=8,
            border=ft.border.all(1, "#BFDBFE"),
            visible=False
        )

        self.lista_escaneados = ft.ListView(expand=True, spacing=10, auto_scroll=False)

        # =========================================================================
        # --- CONSTRUCCIÓN DE CONTENEDORES DE PESTAÑAS ---
        # =========================================================================
        # Tab 1: Historial de Ajustes
        kpi_bar = ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("Valor Inventario Base:", size=10, color="grey"), self.lbl_ent_actual], spacing=0),
                ft.Container(width=1, height=24, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Valor Entradas (+):", size=10, color="grey"), self.lbl_ent_pos], spacing=0),
                ft.Container(width=1, height=24, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Valor Salidas (-):", size=10, color="grey"), self.lbl_sal_neg], spacing=0),
                ft.Container(width=1, height=24, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Impacto Neto:", size=10, color="grey"), self.lbl_ent_neto], spacing=0),
                ft.Container(expand=True),
                ft.Column([ft.Text("Inventario Proyectado:", size=10, color="grey"), self.lbl_ent_proyectado], spacing=0, horizontal_alignment="end"),
            ], alignment=ft.MainAxisAlignment.START),
            padding=10, bgcolor="#fafafa", border_radius=8, border=ft.border.all(1, "#eeeeee")
        )
        
        filtros_row = ft.Container(
            content=ft.Row([
                ft.Container(content=self.search_filter_autocomplete, expand=True),
                self.btn_toggle_filtros,
                self.btn_agregar_ajuste
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="white",
            padding=8,
            border_radius=8,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.04, "black"))
        )
        
        paginacion_row = ft.Row([
            ft.Container(expand=True),
            self.btn_prev,
            self.lbl_page_info,
            self.btn_next
        ], alignment=ft.MainAxisAlignment.END)

        tab_historial_content = ft.Container(
            content=ft.Column([
                kpi_bar,
                filtros_row,
                self.panel_filtros,
                ft.Container(content=self.lista_ajustes, expand=True, bgcolor="#f5f5f5", border_radius=10, padding=8, shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))),
                paginacion_row
            ], expand=True, spacing=8),
            padding=ft.padding.only(top=6),
            expand=True
        )

        # Tab 2: Escaneados con IA
        header_escaneo = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    "Escanear Hoja de Ajustes (Foto / PDF)",
                    icon=ft.icons.CAMERA_ALT_ROUNDED,
                    bgcolor=Config.COLOR_PRIMARY,
                    color="white",
                    height=36,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda e: self.file_picker_ocr.pick_files(
                        allow_multiple=False,
                        allowed_extensions=["jpg", "jpeg", "png", "webp", "pdf"],
                        dialog_title="Seleccionar foto de hoja de control de ajustes"
                    )
                ),
                ft.Container(width=8),
                ft.Container(
                    content=ft.Row([
                        self.lbl_badge_total_escaneados,
                        ft.Container(width=1, height=14, bgcolor="#CBD5E1"),
                        self.lbl_badge_validados,
                        ft.Container(width=1, height=14, bgcolor="#CBD5E1"),
                        self.lbl_badge_pendientes_codigo,
                    ], spacing=8),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    bgcolor="#F8FAFC",
                    border_radius=8,
                    border=ft.border.all(1, "#E2E8F0")
                ),
                ft.Container(expand=True),
                self.btn_guardar_todos_validados,
                self.btn_limpiar_escaneados
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor="#ffffff",
            border_radius=8,
            border=ft.border.all(1, "#e2e8f0")
        )

        tab_escaneo_content = ft.Container(
            content=ft.Column([
                header_escaneo,
                self.ocr_loading_container,
                ft.Container(
                    content=self.lista_escaneados,
                    expand=True,
                    bgcolor="#f8fafc",
                    border_radius=10,
                    padding=10,
                    border=ft.border.all(1, "#e2e8f0")
                )
            ], expand=True, spacing=10),
            padding=ft.padding.only(top=8),
            expand=True
        )

        # Tab Navigation
        self.tabs_control = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            tabs=[
                ft.Tab(
                    text="Historial de Ajustes",
                    icon=ft.icons.HISTORY_ROUNDED,
                    content=tab_historial_content
                ),
                ft.Tab(
                    text="Ajustes Escaneados con IA",
                    icon=ft.icons.DOCUMENT_SCANNER_ROUNDED,
                    content=tab_escaneo_content
                )
            ],
            expand=True
        )

        self.periodo_selector = PeriodoSelectorWidget(on_change_callback=self.on_periodo_change, page=self.page)
        self.content = ft.Column([
            ft.Row([
                ft.Icon(ft.icons.TUNE_ROUNDED, size=24, color=Config.COLOR_PRIMARY),
                ft.Text("Gestión y Ajustes de Inventario", size=22, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Container(expand=True),
                self.periodo_selector,
                self.btn_fullscreen
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.tabs_control
        ], expand=True, spacing=10)

    def _crear_modal_formulario(self):
        def on_tipo_change(e):
            tipo = self.form_tipo_ajuste.value
            if tipo == "ENTRADA":
                self.form_motivo.options = [ft.dropdown.Option(x) for x in ["Sobrante de Inventario", "Donación Entrante", "Devolución Cliente", "Otro (Entrada)"]]
            elif tipo == "SALIDA":
                self.form_motivo.options = [ft.dropdown.Option(x) for x in ["Daño / Merma", "Vencimiento", "Pérdida", "Consumo Familiar", "Consumo Cliente (Cortesía)", "Donación Saliente", "Otro (Salida)"]]
            else:
                self.form_motivo.options = []
            self.form_motivo.value = None
            if self.form_codigo.value:
                self.buscar_detalle_insumo(None)
            self.safe_update()

        def on_costo_change(e):
            try:
                nuevo_costo = float(self.form_costo.value.replace(',', '.') or 0)
                valor_inv = nuevo_costo * getattr(self, 'current_stock_modal', 0)
                self.lbl_valor_inv_modal.value = f"Valor del Inv: ${valor_inv:,.0f}"
            except ValueError:
                self.lbl_valor_inv_modal.value = "Valor del Inv: $0"
            self.safe_update()

        def on_nuevo_stock_change(e):
            val_txt = (self.form_nuevo_stock_real.value or "").strip().replace(',', '.')
            if not val_txt or not self.form_codigo.value:
                return
            try:
                nuevo_stock = float(val_txt)
                stock_sist = getattr(self, 'current_stock_modal', 0.0)
                diff = nuevo_stock - stock_sist

                if diff > 0:
                    self.form_tipo_ajuste.value = "ENTRADA"
                    self.form_motivo.options = [ft.dropdown.Option(x) for x in ["Sobrante de Inventario", "Donación Entrante", "Devolución Cliente", "Otro (Entrada)"]]
                    self.form_motivo.value = "Sobrante de Inventario"
                    self.form_cant.value = str(int(diff) if diff.is_integer() else diff)
                elif diff < 0:
                    self.form_tipo_ajuste.value = "SALIDA"
                    self.form_motivo.options = [ft.dropdown.Option(x) for x in ["Pérdida", "Daño / Merma", "Vencimiento", "Consumo Familiar", "Consumo Cliente (Cortesía)", "Donación Saliente", "Otro (Salida)"]]
                    self.form_motivo.value = "Pérdida"
                    self.form_cant.value = str(int(abs(diff)) if abs(diff).is_integer() else abs(diff))
                else:
                    self.form_cant.value = "0"
                self.safe_update()
            except ValueError:
                pass

        self.form_tipo_ajuste = ft.Dropdown(label="Tipo de Movimiento", options=[ft.dropdown.Option("ENTRADA"), ft.dropdown.Option("SALIDA")], dense=True, expand=True, border_radius=8, on_change=on_tipo_change)

        self.form_codigo = ft.TextField(visible=False) # Guard de código en segundo plano

        self.txt_buscador_insumo = ft.TextField(
            hint_text="Escribe código o palabras del insumo (ej: vaso 4 sin)...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            bgcolor="white",
            border_radius=8,
            height=40,
            content_padding=10,
            expand=True,
            on_change=self.on_buscar_sugerencias_modal
        )

        self.lbl_info_seleccionado_modal = ft.Text(
            "Ningún insumo seleccionado",
            size=11,
            color="grey600",
            weight="w500"
        )

        self.lv_sugerencias_modal = ft.ListView(
            spacing=2,
            height=130,
            visible=False
        )

        self.form_nombre = ft.Text("Selecciona o busca un insumo...", color="grey", italic=True, size=13)
        self.lbl_stock_actual = ft.Text("Stock Sist: 0 unds", weight="bold", color=Config.COLOR_PRIMARY, size=12)
        
        self.form_nuevo_stock_real = ft.TextField(
            label="Nuevo Stock Real",
            hint_text="Ej: 15",
            width=140,
            dense=True,
            border_radius=8,
            text_align=ft.TextAlign.RIGHT,
            on_change=on_nuevo_stock_change
        )

        self.form_motivo = ft.Dropdown(label="Motivo del Ajuste", dense=True, expand=True, border_radius=8)
        self.form_cant = ft.TextField(label="Cantidad Ajuste", expand=True, dense=True, border_radius=8)

        # Eliminamos el expand=True para evitar el desbordamiento vertical en la columna
        self.form_costo = ft.TextField(label="Costo Unitario ($)", dense=True, border_radius=8, on_change=on_costo_change)
        self.lbl_valor_inv_modal = ft.Text("Valor del Inv: $0", size=11, color="grey")

        self.form_obs = ft.TextField(label="Observación (Opcional)", expand=True, dense=True, multiline=True, min_lines=2, border_radius=8)

        return ft.AlertDialog(
            title=ft.Text("Registrar Ajuste de Inventario"),
            content=ft.Container(
                width=540,
                content=ft.Column([
                    # Buscador Inteligente y Panel de Sugerencias
                    ft.Column([
                        ft.Row([self.txt_buscador_insumo]),
                        self.lbl_info_seleccionado_modal,
                        self.lv_sugerencias_modal
                    ], spacing=4),
                    # Tarjeta de Insumo Seleccionado con Input de Nuevo Stock
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.INVENTORY_2_ROUNDED, size=20, color=Config.COLOR_PRIMARY),
                            ft.Column([
                                self.form_nombre,
                                self.lbl_stock_actual
                            ], spacing=2, expand=True),
                            self.form_nuevo_stock_real
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER), 
                        padding=10, 
                        bgcolor="#f8f9fa", 
                        border_radius=8,
                        border=ft.border.all(1, "#e0e0e0")
                    ),
                    ft.Row([self.form_tipo_ajuste, self.form_motivo]),
                    ft.Row([
                        self.form_cant, 
                        ft.Column([self.form_costo, self.lbl_valor_inv_modal], expand=True, spacing=2)
                    ]),
                    ft.Row([self.form_obs])
                ], tight=True, spacing=12)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cerrar_modal()),
                ft.ElevatedButton("Guardar Ajuste", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=self.on_guardar_ajuste)
            ]
        )

    # --- Lógica de Negocio ---
    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page:
                self.page.update()
            elif self.uid:
                self.update()
        except Exception:
            pass

    def safe_page_update(self):
        """Alias para actualización segura de página."""
        self.safe_update()

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
        if self.page:
            if self.modal_ajuste not in self.page.overlay:
                self.page.overlay.append(self.modal_ajuste)
            if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
                self.page.overlay.append(self.date_picker)
            if hasattr(self, "file_picker_ocr") and self.file_picker_ocr not in self.page.overlay:
                self.page.overlay.append(self.file_picker_ocr)
        self.load_data()
        self.renderizar_lista_escaneados()

    def buscar_detalle_insumo(self, e):
        codigo = self.form_codigo.value.strip()
        if not codigo: return
        detalle = self.db.get_insumo_detalle(codigo)
        if detalle:
            self.form_nombre.value = detalle.get("nombre", "")
            self.form_nombre.color = "black"
            self.current_stock_modal = float(detalle.get('stock_actual') or 0)
            self.lbl_stock_actual.value = f"Stock Sist: {self.current_stock_modal:g} unds"
            self.form_nuevo_stock_real.value = ""

            tipo = self.form_tipo_ajuste.value
            nuevo_costo = 0
            if tipo == "ENTRADA":
                nuevo_costo = float(detalle.get("costo_unitario") or 0)
                self.form_costo.value = str(nuevo_costo)
            elif tipo == "SALIDA":
                nuevo_costo = float(detalle.get("precio_venta") or 0)
                self.form_costo.value = str(nuevo_costo)
            else:
                nuevo_costo = float(detalle.get("costo_unitario") or 0)
                self.form_costo.value = str(nuevo_costo)

            valor_inv = nuevo_costo * self.current_stock_modal
            self.lbl_valor_inv_modal.value = f"Valor del Inv: ${valor_inv:,.0f}"
        else:
            self.form_nombre.value = "Insumo no encontrado."
            self.form_nombre.color = "red"
            self.current_stock_modal = 0
            self.lbl_stock_actual.value = "Stock Sist: 0"
            self.lbl_valor_inv_modal.value = "Valor del Inv: $0"
        self.safe_update()

    def on_buscar_sugerencias_modal(self, e):
        """Búsqueda inteligente por múltiples palabras clave (tokens) para el modal de ajustes."""
        q = (self.txt_buscador_insumo.value or "").strip().lower()
        if not q or len(q) < 2:
            self.lv_sugerencias_modal.visible = False
            self.lv_sugerencias_modal.controls.clear()
            self.safe_update()
            return

        catalogo = getattr(self, "catalogo_completo", [])
        if not catalogo:
            try:
                catalogo, _ = self.db.get_insumos(page=1, page_size=99999)
                self.catalogo_completo = catalogo
            except Exception:
                catalogo = []

        tokens = q.split()
        matches = []
        for item in catalogo:
            cod = str(item.get("codigo_insumo") or "").lower()
            nom = str(item.get("nombre") or "").lower()
            texto = f"{cod} {nom}"
            if all(t in texto for t in tokens):
                matches.append(item)
                if len(matches) >= 8:
                    break

        self.lv_sugerencias_modal.controls.clear()
        for m in matches:
            cod_m = str(m.get("codigo_insumo"))
            nom_m = str(m.get("nombre"))
            costo_m = float(m.get("costo_unitario") or 0)
            
            btn = ft.Container(
                content=ft.Row([
                    ft.Text(f"[{cod_m}]", size=11, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Text(nom_m, size=11, weight="w500", expand=True, color="black87"),
                    ft.Text(f"Costo: ${costo_m:,.0f}", size=10, color=Config.COLOR_TEXT_MUTED)
                ], spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(horizontal=8, vertical=5),
                bgcolor="#f8fafc",
                border_radius=6,
                border=ft.border.all(1, "#e2e8f0"),
                on_click=lambda ev, it=m: self.seleccionar_insumo_modal(it)
            )
            self.lv_sugerencias_modal.controls.append(btn)

        self.lv_sugerencias_modal.visible = (len(matches) > 0)
        self.safe_update()

    def seleccionar_insumo_modal(self, item):
        """Selecciona el insumo desde la lista de sugerencias y carga sus datos."""
        self.lv_sugerencias_modal.visible = False
        cod = str(item.get("codigo_insumo"))
        nom = item.get("nombre")
        cat = item.get("categoria") or "GENERAL"
        
        self.form_codigo.value = cod
        self.txt_buscador_insumo.value = f"[{cod}] {nom}"
        self.form_nombre.value = f"[{cod}] {nom}"
        self.form_nombre.color = "black"
        self.lbl_info_seleccionado_modal.value = f"Insumo activo: [{cod}] {nom} • Categoría: {cat}"
        self.lbl_info_seleccionado_modal.color = Config.COLOR_PRIMARY
        self.lbl_info_seleccionado_modal.weight = "w500"
        
        self.current_stock_modal = float(item.get("stock_actual") or 0)
        self.lbl_stock_actual.value = f"Stock Sist: {self.current_stock_modal:g} unds"
        self.form_nuevo_stock_real.value = ""
        
        # 1. Costo unitario
        costo = float(item.get("costo_unitario") or 0)
        if costo <= 0:
            try:
                res_c = self.db._db.get(f"registro_compras?codigo_insumo=eq.{cod}&order=fecha.desc&limit=1&select=costo_unitario", timeout=4)
                if res_c and res_c.status_code == 200 and res_c.json():
                    costo = float(res_c.json()[0].get("costo_unitario") or 0)
            except Exception:
                pass

        self.form_costo.value = str(int(costo) if costo.is_integer() else costo)
        valor_inv = costo * self.current_stock_modal
        self.lbl_valor_inv_modal.value = f"Valor del Inv: ${valor_inv:,.0f}"
        
        self.safe_update()

    def abrir_modal_ajuste(self):
        self.modal_ajuste.title.value = "Registrar Ajuste de Inventario"
        
        # Cargar catálogo para sugerencias inteligentes
        try:
            insumos, _ = self.db.get_insumos(page=1, page_size=99999)
            self.catalogo_completo = insumos
            self.catalogo_cache = {i["codigo_insumo"]: i for i in insumos}
            suggs = [
                {"key": i["codigo_insumo"], "value": f"[{i['codigo_insumo']}] {i['nombre']}"}
                for i in insumos
            ]
            self.search_filter_autocomplete.suggestions = suggs
        except Exception:
            pass

        # Limpiar valores del formulario
        self.form_tipo_ajuste.value = None
        self.form_tipo_ajuste.error_text = None
        
        self.form_motivo.options = []
        self.form_motivo.value = None
        self.form_motivo.error_text = None
        
        self.form_codigo.value = ""
        self.form_codigo.error_text = None
        
        self.form_nombre.value = "Selecciona o busca un insumo..."
        self.form_nombre.color = "grey"
        self.lbl_stock_actual.value = "Stock Sist: 0 unds"
        self.lbl_info_seleccionado_modal.value = "Ningún insumo seleccionado"
        self.lbl_info_seleccionado_modal.color = "grey600"
        self.lbl_info_seleccionado_modal.weight = "w500"
        self.form_nuevo_stock_real.value = ""
        
        self.form_cant.value = ""
        self.form_cant.error_text = None
        
        self.form_costo.value = ""
        self.form_costo.error_text = None
        self.lbl_valor_inv_modal.value = "Valor del Inv: $0"
        
        self.form_obs.value = ""
        self.form_obs.error_text = None
        
        self.txt_buscador_insumo.value = ""
        self.lv_sugerencias_modal.visible = False
        self.lv_sugerencias_modal.controls.clear()
        
        self.modal_ajuste.open = True
        if self.page:
            self.page.update()

    def cerrar_modal(self):
        self.modal_ajuste.open = False
        self.page.update()

    def on_guardar_ajuste(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if self.page:
            self.update()
            
        threading.Thread(target=self._on_guardar_ajuste_worker, args=(btn_control,), daemon=True).start()

    def _on_guardar_ajuste_worker(self, btn_control):
        try:
            self.form_codigo.error_text = None
            self.form_cant.error_text = None
            self.form_costo.error_text = None
            if self.page:
                self.page.update()
                
            try:
                codigo = self.form_codigo.value.strip()
                motivo_ui = self.form_motivo.value
                cant = float(self.form_cant.value.replace(',', '.'))
                costo = float(self.form_costo.value.replace(',', '.'))
                obs = self.form_obs.value.strip()
            except ValueError:
                self.mostrar_alerta("Error en los formatos numéricos. Usa números válidos para cantidad y costo.", "red")
                return

            if not codigo or not motivo_ui or cant <= 0:
                self.mostrar_alerta("Completa los campos obligatorios y asegúrate que la cantidad sea mayor a cero.", "red")
                return

            tipo_bd = self.mapa_motivos.get(motivo_ui)
            if not tipo_bd: return

            datos = {
                "codigo_insumo": codigo,
                "tipo_ajuste": tipo_bd,
                "cantidad": cant,
                "costo_unitario_congelado": costo,
                "costo_total_ajuste": cant * costo,
                "motivo_observacion": obs if obs else motivo_ui,
                "estado_registro": "VÁLIDO"
            }

            if self.db.insert_ajuste_individual(datos):
                self.mostrar_alerta("Ajuste registrado exitosamente.", "green")
                self.cerrar_modal()
                self.load_data()
            else:
                self.mostrar_alerta("Error al registrar en la base de datos.", "red")
        except Exception as ex:
            if self.page:
                self.mostrar_alerta(f"Error interno: {str(ex)}", "red")
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.page.update()

    def anular_registro(self, id_ajuste):
        if self.db.anular_ajuste(id_ajuste):
            self.mostrar_alerta("Registro anulado. El stock ha sido revertido.", "orange")
            self.load_data()
        else:
            self.mostrar_alerta("Error al anular.", "red")

    def mostrar_alerta(self, msj, color):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msj, weight="bold", color="white"), bgcolor=color, duration=3000)
            self.page.snack_bar.open = True
            try:
                self.page.update()
            except Exception:
                pass

    def _open_date_picker(self, e=None):
        if not self.page:
            return
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
            try:
                self.page.update()
            except Exception:
                pass
        try:
            self.date_picker.pick_date()
        except AssertionError:
            try:
                self.page.update()
                self.date_picker.pick_date()
            except Exception:
                pass

    def _clear_date(self, e=None):
        self.date_picker.value = None
        self.btn_date_filtro.text = "Filtrar por Fecha"
        self.btn_clear_date.visible = False
        self._on_filter_change()
        
    def _on_filter_change(self):
        self.current_page = 1
        if self.date_picker.value:
            self.btn_date_filtro.text = self.date_picker.value.strftime('%Y-%m-%d')
            self.btn_clear_date.visible = True
        else:
            self.btn_date_filtro.text = "Filtrar por Fecha"
            self.btn_clear_date.visible = False
        self.render_table()
        self.safe_update()

    def toggle_panel_filtros(self, e=None):
        self.panel_filtros_abierto = not self.panel_filtros_abierto
        self.panel_filtros.visible = self.panel_filtros_abierto
        self.btn_toggle_filtros.icon = ft.icons.FILTER_ALT_OFF_ROUNDED if self.panel_filtros_abierto else ft.icons.TUNE_ROUNDED
        self.safe_update()

    def limpiar_todos_los_filtros(self, e=None):
        self.search_filter_autocomplete.value = ""
        self.search_input_text.value = ""
        self.date_picker.value = None
        self.btn_date_filtro.text = "Filtrar por Fecha"
        self.btn_clear_date.visible = False
        self.drop_tipo.value = "Todos"
        self.drop_origen.value = "Todos"
        self.drop_motivo.value = "Todos"
        self.current_page = 1
        self.render_table()
        self.safe_update()

    def abrir_modal_editar_ajuste(self, aj):
        id_ajuste = aj.get("id_ajuste")
        cod = aj.get("codigo_insumo", "")
        cat_info = aj.get("catalogo_insumos", {})
        nombre = cat_info.get("nombre", "Desconocido") if isinstance(cat_info, dict) else "Desconocido"
        es_entrada = aj.get("tipo_ajuste") in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
        
        tipo_drop = ft.Dropdown(
            label="Tipo de Ajuste",
            options=[ft.dropdown.Option("ENTRADA"), ft.dropdown.Option("SALIDA")],
            value="ENTRADA" if es_entrada else "SALIDA",
            dense=True,
            expand=True,
            border_radius=8
        )
        
        def _get_motivos(tipo):
            if tipo == "ENTRADA":
                return ["Sobrante de Inventario", "Donación Entrante", "Devolución Cliente", "Otro (Entrada)"]
            else:
                return ["Daño / Merma", "Vencimiento", "Pérdida", "Consumo Familiar", "Consumo Cliente (Cortesía)", "Donación Saliente", "Otro (Salida)"]
        
        motivo_actual = aj.get("motivo_observacion", "")
        motivos_opts = _get_motivos(tipo_drop.value)
        if motivo_actual and motivo_actual not in motivos_opts:
            motivos_opts.insert(0, motivo_actual)
            
        motivo_drop = ft.Dropdown(
            label="Motivo del Ajuste",
            options=[ft.dropdown.Option(m) for m in motivos_opts],
            value=motivo_actual if motivo_actual in motivos_opts else (motivos_opts[0] if motivos_opts else None),
            dense=True,
            expand=True,
            border_radius=8
        )
        
        def _on_edit_tipo_change(e):
            nuevos = _get_motivos(tipo_drop.value)
            motivo_drop.options = [ft.dropdown.Option(m) for m in nuevos]
            motivo_drop.value = nuevos[0] if nuevos else None
            self.safe_page_update()
            
        tipo_drop.on_change = _on_edit_tipo_change
        
        cant_actual = float(aj.get("cantidad") or 0.0)
        costo_u_actual = float(aj.get("costo_unitario_congelado") or 0.0)
        
        txt_cant = ft.TextField(
            label="Cantidad",
            value=str(int(cant_actual) if cant_actual.is_integer() else cant_actual),
            dense=True,
            expand=True,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        txt_costo = ft.TextField(
            label="Costo Unitario ($)",
            value=str(int(costo_u_actual) if costo_u_actual.is_integer() else costo_u_actual),
            dense=True,
            expand=True,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        lbl_tot_calc = ft.Text(f"Total Impacto: ${float(aj.get('costo_total_ajuste') or 0.0):,.2f}", size=12, weight="bold", color=Config.COLOR_PRIMARY)
        
        def _recalc_tot(e):
            try:
                c = float((txt_cant.value or "0").replace(',', '.'))
                cu = float((txt_costo.value or "0").replace(',', '.'))
                lbl_tot_calc.value = f"Total Impacto: ${c * cu:,.2f}"
            except ValueError:
                lbl_tot_calc.value = "Total Impacto: $0.00"
            self.safe_page_update()
            
        txt_cant.on_change = _recalc_tot
        txt_costo.on_change = _recalc_tot
        
        def _do_guardar(e):
            try:
                nueva_cant = float((txt_cant.value or "0").replace(',', '.'))
                nuevo_cu = float((txt_costo.value or "0").replace(',', '.'))
                if nueva_cant <= 0:
                    self.mostrar_alerta("La cantidad debe ser mayor a cero.", "red")
                    return
                if nuevo_cu < 0:
                    self.mostrar_alerta("El costo unitario no puede ser negativo.", "red")
                    return
                if not motivo_drop.value:
                    self.mostrar_alerta("Debes seleccionar un motivo.", "red")
                    return
                    
                tipo_bd = "AJUSTE_ENTRADA" if tipo_drop.value == "ENTRADA" else "AJUSTE_SALIDA"
                if tipo_drop.value == "ENTRADA" and motivo_drop.value == "Sobrante de Inventario":
                    tipo_bd = "ENTRADA_POR_SOBRANTE"
                elif tipo_drop.value == "SALIDA" and motivo_drop.value == "Vencimiento":
                    tipo_bd = "BAJA_VENCIMIENTO"
                elif tipo_drop.value == "SALIDA" and motivo_drop.value == "Pérdida":
                    tipo_bd = "SALIDA_POR_FALTANTE"
                    
                tot_ajuste = round(nueva_cant * nuevo_cu, 2)
                
                payload = {
                    "tipo_ajuste": tipo_bd,
                    "motivo_observacion": motivo_drop.value,
                    "cantidad": nueva_cant,
                    "costo_unitario_congelado": nuevo_cu,
                    "costo_total_ajuste": tot_ajuste
                }
                
                dlg_edit.open = False
                self.safe_page_update()
                
                if self.db.actualizar_ajuste(id_ajuste, payload):
                    self.mostrar_alerta(f"✓ Ajuste de [{cod}] actualizado exitosamente.", "green700")
                    self.load_data()
                else:
                    self.mostrar_alerta("Error al actualizar el ajuste en la base de datos.", "red")
            except Exception as ex:
                self.mostrar_alerta(f"Error al procesar: {ex}", "red")

        dlg_edit = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.EDIT_NOTE_ROUNDED, color=Config.COLOR_PRIMARY, size=20),
                ft.Text(f"Editar Ajuste - [{cod}]", size=15, weight="bold", color=Config.COLOR_PRIMARY, expand=True)
            ], spacing=6),
            content=ft.Container(
                width=460,
                content=ft.Column([
                    ft.Text(nombre, size=12, color="grey700", weight="w500"),
                    ft.Row([tipo_drop, motivo_drop], spacing=8),
                    ft.Row([txt_cant, txt_costo], spacing=8),
                    lbl_tot_calc
                ], tight=True, spacing=10)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg_edit, 'open', False), self.safe_page_update())),
                ft.ElevatedButton("Guardar Cambios", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=_do_guardar)
            ]
        )
        
        if self.page:
            if dlg_edit not in self.page.overlay:
                self.page.overlay.append(dlg_edit)
            dlg_edit.open = True
            self.safe_page_update()
        
    def _prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_table()
            
    def _next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_table()

    def load_data(self):
        # Actualizar resúmenes globales
        kpis_inv = self.db.get_inventario_kpis()
        val_inv_base = kpis_inv.get('valor_inventario', 0)
        self.lbl_ent_actual.value = f"${val_inv_base:,.2f}"

        # Cargar catálogo para sugerencias inteligentes en el buscador desde el inicio
        try:
            insumos, _ = self.db.get_insumos(page=1, page_size=99999)
            self.catalogo_completo = insumos
            self.catalogo_cache = {i["codigo_insumo"]: i for i in insumos}
            suggs = [
                {"key": i["codigo_insumo"], "value": f"[{i['codigo_insumo']}] {i['nombre']}"}
                for i in insumos
            ]
            self.search_filter_autocomplete.suggestions = suggs
        except Exception:
            pass

        self.data_completa = self.db.get_ajustes_inventario()
        self.render_table(val_inv_base)

    def on_periodo_change(self, nuevo_periodo: str):
        self.current_page = 1
        self.render_table()
        self.safe_update()

    def render_table(self, val_inv_base=None):
        if val_inv_base is None:
            # Recuperar el valor base desde el label si no se provee (eliminando caracteres de moneda)
            try:
                val_inv_base = float(self.lbl_ent_actual.value.replace('$', '').replace(',', ''))
            except:
                val_inv_base = 0.0

        self.lista_ajustes.controls.clear()
        
        raw_auto = (self.search_filter_autocomplete.value or "").strip()
        if not raw_auto:
            filtro_texto = ""
            self.search_input_text.value = ""
        else:
            filtro_texto = (self.search_input_text.value or raw_auto).lower().strip()
        filtro_fecha = self.date_picker.value.strftime("%Y-%m-%d") if self.date_picker.value else None
        filtro_tipo = self.drop_tipo.value
        filtro_origen = self.drop_origen.value if hasattr(self, "drop_origen") else "Todos"
        filtro_motivo = self.drop_motivo.value
        mes_filtro = self.periodo_selector.get_periodo_actual() if hasattr(self, "periodo_selector") else None
        
        filtered_data = []
        total_ent_pos = 0.0
        total_sal_neg = 0.0

        tokens_filtro = filtro_texto.split()
        from core.fecha_utils import parsear_a_fecha_local

        for aj in self.data_completa:
            es_entrada = aj["tipo_ajuste"] in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
            cat_info = aj.get("catalogo_insumos", {})
            nombre = cat_info.get("nombre", "Desconocido") if isinstance(cat_info, dict) else "Desconocido"
            
            periodo_info = aj.get("periodos_inventario")
            mes_periodo = periodo_info.get("mes_periodo") if isinstance(periodo_info, dict) else None
            obs_lower = str(aj.get("motivo_observacion", "")).lower()
            es_cierre_mes = bool(
                mes_periodo or 
                aj.get("id_periodo") or 
                aj.get("id_auditoria_origen") or 
                "auditoría" in obs_lower or 
                "conteo físico" in obs_lower or 
                "cierre" in obs_lower
            )

            # Reglas de coincidencia multi-token
            texto_aj = f"{aj['codigo_insumo']} {nombre}".lower()
            match_texto = all(t in texto_aj for t in tokens_filtro) if tokens_filtro else True
            fecha_ajuste_local = parsear_a_fecha_local(aj.get("fecha_ajuste"))
            match_fecha = filtro_fecha is None or fecha_ajuste_local == filtro_fecha
            f_aj = str(aj.get("fecha_ajuste") or "")[:7]
            match_periodo = (filtro_fecha is not None) or (mes_filtro is None) or (f_aj == mes_filtro)
            
            tipo_ajuste_str = "Entrada" if es_entrada else "Salida"
            match_tipo = filtro_tipo == "Todos" or filtro_tipo == tipo_ajuste_str
            
            match_origen = True
            if filtro_origen == "Cierre de Mes":
                match_origen = es_cierre_mes
            elif filtro_origen == "Manual":
                match_origen = not es_cierre_mes

            match_motivo = filtro_motivo == "Todos" or filtro_motivo == aj["motivo_observacion"]
            
            if match_texto and match_fecha and match_tipo and match_origen and match_motivo and match_periodo:
                filtered_data.append(aj)

            # Acumular KPIs sobre todos los datos VÁLIDOS del historial general, sin importar los filtros visuales.
            if aj["estado_registro"] == "VÁLIDO":
                val_total = float(aj["costo_total_ajuste"])
                if es_entrada: total_ent_pos += val_total
                else: total_sal_neg += val_total

        import math
        self.total_records = len(filtered_data)
        self.total_pages = math.ceil(self.total_records / self.page_size) if self.total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = filtered_data[start_idx:end_idx]

        for aj in page_data:
            es_entrada = aj["tipo_ajuste"] in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
            val_total = float(aj["costo_total_ajuste"])
            val_total_str = f"${val_total:,.2f}"
            
            cat_info = aj.get("catalogo_insumos", {})
            nombre = cat_info.get("nombre", "Desconocido") if isinstance(cat_info, dict) else "Desconocido"

            periodo_info = aj.get("periodos_inventario")
            mes_periodo = periodo_info.get("mes_periodo") if isinstance(periodo_info, dict) else None
            obs_lower = str(aj.get("motivo_observacion", "")).lower()
            es_cierre_mes = bool(
                mes_periodo or 
                aj.get("id_periodo") or 
                aj.get("id_auditoria_origen") or 
                "auditoría" in obs_lower or 
                "conteo físico" in obs_lower or 
                "cierre" in obs_lower
            )

            # Badge de Origen (Cierre de Mes vs Ajuste Manual)
            if es_cierre_mes:
                lbl_origen = f"Cierre {mes_periodo}" if mes_periodo else "Cierre de Mes"
                badge_origen = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.LOCK_CLOCK_ROUNDED, size=11, color="#6D28D9"),
                        ft.Text(lbl_origen, color="#6D28D9", weight="bold", size=9.5)
                    ], spacing=3, tight=True),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    bgcolor="#EDE9FE",
                    border_radius=10,
                    border=ft.border.all(1, "#DDD6FE"),
                    tooltip="Ajuste originado por auditoría de Cierre de Mes"
                )
            else:
                badge_origen = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.EDIT_NOTE_ROUNDED, size=11, color="#475569"),
                        ft.Text("Manual", color="#475569", weight="bold", size=9.5)
                    ], spacing=3, tight=True),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    bgcolor="#F1F5F9",
                    border_radius=10,
                    border=ft.border.all(1, "#E2E8F0"),
                    tooltip="Ajuste operativo manual registrado de forma individual"
                )

            # Tipo de Ajuste
            tipo_bg = "#ecfdf5" if es_entrada else "#fef2f2"
            tipo_color = "green700" if es_entrada else "red700"
            badge_tipo = ft.Container(
                content=ft.Text("Entrada (+)" if es_entrada else "Salida (-)", color=tipo_color, weight="bold", size=10),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                bgcolor=tipo_bg,
                border=ft.border.all(1, "#a7f3d0" if es_entrada else "#fecaca"),
                border_radius=10
            )

            fecha_item_local = parsear_a_fecha_local(aj.get("fecha_ajuste"))

            # Fila 1: Badges, Insumo, Fecha e Importe Total
            fila1 = ft.Row([
                badge_tipo,
                badge_origen,
                ft.Text(f"[{aj['codigo_insumo']}] {nombre}", size=12.5, weight="bold", color="black87", expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Row([
                    ft.Icon(ft.icons.CALENDAR_MONTH_ROUNDED, size=12, color="grey600"),
                    ft.Text(fecha_item_local, size=10.5, color="grey600"),
                ], spacing=3, tight=True),
                ft.Text(val_total_str, size=13, weight="bold", color=tipo_color)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

            # Fila 2: Detalles (Motivo, Cantidad, Costo Unitario) y Botones de Acción (Iconos con Tooltips)
            btn_style_compact = ft.ButtonStyle(padding=0)
            
            if aj["estado_registro"] == "VÁLIDO":
                btn_editar = ft.IconButton(
                    icon=ft.icons.EDIT_OUTLINED,
                    icon_size=15,
                    icon_color="blue700",
                    width=26,
                    height=26,
                    style=btn_style_compact,
                    tooltip="Editar ajuste",
                    on_click=lambda e, a=aj: self.abrir_modal_editar_ajuste(a)
                )
                btn_anular = ft.IconButton(
                    icon=ft.icons.CANCEL_OUTLINED,
                    icon_size=15,
                    icon_color="red700",
                    width=26,
                    height=26,
                    style=btn_style_compact,
                    tooltip="Anular ajuste",
                    on_click=lambda e, id_aj=aj["id_ajuste"]: self.anular_registro(id_aj)
                )
                acciones_row = ft.Row([btn_editar, btn_anular], spacing=2, tight=True)
            else:
                acciones_row = ft.Container(
                    content=ft.Text("ANULADO", size=9, weight="bold", color="red400"),
                    bgcolor="#fef2f2",
                    border=ft.border.all(1, "#fecaca"),
                    padding=ft.padding.symmetric(horizontal=5, vertical=1),
                    border_radius=4
                )

            fila2 = ft.Row([
                ft.Row([
                    ft.Text("Motivo: ", size=10.5, color="grey600"),
                    ft.Text(str(aj.get('motivo_observacion') or 'N/A'), size=10.5, weight="w500", color="black87"),
                    ft.Text(" • ", color="grey400", size=10),
                    ft.Text("Cant: ", size=10.5, color="grey600"),
                    ft.Text(f"{float(aj.get('cantidad') or 0):g} unds", size=10.5, weight="bold", color="black87"),
                    ft.Text(" • ", color="grey400", size=10),
                    ft.Text(f"Costo U: ${float(aj.get('costo_unitario_congelado') or 0):,.0f}", size=10.5, color="grey700")
                ], spacing=2, expand=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                acciones_row
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

            tarjeta = ft.Container(
                content=ft.Column([fila1, fila2], spacing=4),
                bgcolor="white",
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                border_radius=8,
                border=ft.border.all(1, "#e2e8f0")
            )
            self.lista_ajustes.controls.append(tarjeta)
            
        # Actualización UI
        self.btn_prev.disabled = self.current_page <= 1
        self.btn_next.disabled = self.current_page >= self.total_pages
        self.lbl_page_info.value = f"Pág {self.current_page} de {self.total_pages} ({self.total_records} reg.)"

        # Configuración de KPIs Dinámicos
        self.lbl_ent_pos.value = f"+${total_ent_pos:,.2f}"
        self.lbl_sal_neg.value = f"-${total_sal_neg:,.2f}"
        
        impacto_neto = total_ent_pos - total_sal_neg
        self.lbl_ent_neto.value = f"{'+' if impacto_neto >= 0 else '-'}${abs(impacto_neto):,.2f}"
        
        self.lbl_ent_proyectado.value = f"${(val_inv_base + impacto_neto):,.2f}"

        if self.page:
            self.page.update()

    # =========================================================================
    # --- MÉTODOS DE ESCANEO OCR CON IA (GEMINI FLASH) Y GESTIÓN TAB 2 ---
    # =========================================================================
    def _on_ocr_file_selected(self, e: ft.FilePickerResultEvent):
        if not e.files or len(e.files) == 0:
            return
        
        file_path = e.files[0].path
        if not file_path:
            return

        self.ocr_loading_container.visible = True
        self.safe_update()

        threading.Thread(target=self._worker_procesar_imagen_ocr, args=(file_path,), daemon=True).start()

    def _worker_procesar_imagen_ocr(self, file_path: str):
        try:
            # Asegurar catálogo en memoria
            if not self.catalogo_cache:
                try:
                    insumos, _ = self.db.get_insumos(page=1, page_size=99999)
                    self.catalogo_completo = insumos
                    self.catalogo_cache = {str(i["codigo_insumo"]).strip(): i for i in insumos}
                except Exception:
                    pass

            raw_extraidos = self.gemini_parser.parse_ajustes_image(file_path)
            
            if raw_extraidos is None:
                self.mostrar_alerta("Error al conectar con la IA de Gemini. Verifica tu conexión o clave de API.", "red")
                return

            if len(raw_extraidos) == 0:
                self.mostrar_alerta("No se detectaron filas de ajustes legibles en la imagen.", "orange")
                return

            hoy_str = get_hoy_local_str()
            nuevos_items = []

            for r in raw_extraidos:
                f_raw = str(r.get("fecha") or "").strip()
                fecha_final = parsear_a_fecha_local(f_raw) if f_raw and f_raw != "null" else hoy_str
                
                cod_raw = str(r.get("codigo_insumo") or "").strip()
                nom_raw = str(r.get("nombre_extraido") or "").strip()
                cant_val = float(r.get("cantidad") or 1.0)
                motivo_extraido = str(r.get("motivo_extraido") or "").strip()
                tipo_extraido = str(r.get("tipo_ajuste") or "AJUSTE_SALIDA").strip().upper()
                motivo_estandarizado = str(r.get("motivo_estandarizado") or "Otro (Salida)").strip()

                # Normalizar tipo y motivo
                if motivo_estandarizado not in self.mapa_motivos:
                    motivo_estandarizado = "Otro (Entrada)" if "ENTRADA" in tipo_extraido else "Otro (Salida)"

                # Verificar si el código existe en el catálogo
                insumo_matched = self.catalogo_cache.get(cod_raw) if cod_raw else None

                if insumo_matched:
                    cod_final = cod_raw
                    nom_final = insumo_matched.get("nombre", nom_raw)
                    costo_val = float(insumo_matched.get("costo_unitario") or 0.0)
                    estado_val = "VALIDO"
                else:
                    cod_final = ""
                    nom_final = nom_raw
                    costo_val = 0.0
                    estado_val = "REQUIERE_CODIGO"

                item_obj = {
                    "id": uuid.uuid4().hex,
                    "fecha": fecha_final,
                    "codigo_insumo": cod_final,
                    "nombre": nom_final,
                    "nombre_extraido": nom_raw,
                    "cantidad": cant_val,
                    "costo_unitario": costo_val,
                    "tipo_ajuste": tipo_extraido,
                    "motivo_ui": motivo_estandarizado,
                    "observacion": f"Extraído: {motivo_extraido}" if motivo_extraido else "",
                    "estado_validacion": estado_val
                }
                nuevos_items.append(item_obj)

            self.items_escaneados.extend(nuevos_items)
            self.tabs_control.selected_index = 1
            self.mostrar_alerta(f"¡Extracción exitosa! {len(nuevos_items)} registros escaneados con IA.", "green")

        except Exception as ex:
            self.mostrar_alerta(f"Error procesando formato: {str(ex)}", "red")
        finally:
            self.ocr_loading_container.visible = False
            self.renderizar_lista_escaneados()
            self.safe_update()

    def renderizar_lista_escaneados(self):
        self.lista_escaneados.controls.clear()
        
        tot = len(self.items_escaneados)
        validados = sum(1 for x in self.items_escaneados if x["estado_validacion"] == "VALIDO")
        pendientes = tot - validados

        self.lbl_badge_total_escaneados.value = f"{tot} escaneados"
        self.lbl_badge_validados.value = f"{validados} listos"
        self.lbl_badge_pendientes_codigo.value = f"{pendientes} requieren código"

        self.btn_guardar_todos_validados.visible = (validados > 0)
        self.btn_limpiar_escaneados.visible = (tot > 0)

        if tot == 0:
            banner_vacio = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.DOCUMENT_SCANNER_OUTLINED, size=50, color=Config.COLOR_PRIMARY),
                    ft.Text("Escaneo Inteligente de Formatos Físicos de Ajustes", weight="bold", size=15, color=Config.COLOR_PRIMARY),
                    ft.Text("Digitaliza hojas de reporte de salidas, mermas, cortesías o sobrantes usando Gemini Flash.", size=12, color="grey700", text_align=ft.TextAlign.CENTER),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.icons.LOOKS_ONE_ROUNDED, size=16, color=Config.COLOR_ACCENT), ft.Text("1. Toma una foto", weight="bold", size=12)]),
                                ft.Text("Foto clara del formato con columnas: Fecha, Código, Nombre, Cant, Motivo.", size=11, color="grey600")
                            ], spacing=2),
                            padding=10, bgcolor="white", border_radius=8, border=ft.border.all(1, "#e2e8f0"), width=220
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.icons.LOOKS_TWO_ROUNDED, size=16, color=Config.COLOR_ACCENT), ft.Text("2. Sube la imagen", weight="bold", size=12)]),
                                ft.Text("Presiona el botón de arriba para subir la foto o archivo PDF.", size=11, color="grey600")
                            ], spacing=2),
                            padding=10, bgcolor="white", border_radius=8, border=ft.border.all(1, "#e2e8f0"), width=220
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.icons.LOOKS_3_ROUNDED, size=16, color=Config.COLOR_ACCENT), ft.Text("3. Valida y Guarda", weight="bold", size=12)]),
                                ft.Text("Si falta el código, búscalo inteligentemente y guarda individual o en lote.", size=11, color="grey600")
                            ], spacing=2),
                            padding=10, bgcolor="white", border_radius=8, border=ft.border.all(1, "#e2e8f0"), width=220
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                padding=35,
                alignment=ft.alignment.center
            )
            self.lista_escaneados.controls.append(banner_vacio)
        else:
            for idx, it in enumerate(self.items_escaneados):
                try:
                    tarjeta = self._crear_tarjeta_escaneada(it, idx)
                    self.lista_escaneados.controls.append(tarjeta)
                except Exception as ex:
                    print(f"Error renderizando tarjeta #{idx+1}: {ex}")

        self.safe_update()

    def _crear_tarjeta_escaneada(self, it: dict, index: int):
        es_valido = (it["estado_validacion"] == "VALIDO")
        es_entrada = "ENTRADA" in it.get("tipo_ajuste", "")
        item_id = it["id"]

        # 1. Cabecera de la Tarjeta
        badge_idx = ft.Container(
            content=ft.Text(f"#{index + 1}", size=11, weight="bold", color="white"),
            bgcolor=Config.COLOR_PRIMARY,
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
            border_radius=10
        )

        chip_fecha = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CALENDAR_MONTH_ROUNDED, size=13, color="grey700"),
                ft.Text(it["fecha"], size=11, weight="bold", color="grey800")
            ], spacing=4),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor="#F1F5F9",
            border_radius=6,
            border=ft.border.all(1, "#CBD5E1")
        )

        if es_valido:
            badge_estado = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED, size=13, color="green700"),
                    ft.Text("Listo para Guardar", size=11, weight="bold", color="green800")
                ], spacing=4),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                bgcolor="#DCFCE7",
                border_radius=12,
                border=ft.border.all(1, "#86EFAC")
            )
        else:
            badge_estado = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, size=13, color="orange800"),
                    ft.Text("Requiere Código / Insumo", size=11, weight="bold", color="orange900")
                ], spacing=4),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                bgcolor="#FEF3C7",
                border_radius=12,
                border=ft.border.all(1, "#FDE68A")
            )

        btn_descartar = ft.IconButton(
            icon=ft.icons.CLOSE_ROUNDED,
            icon_color="red400",
            tooltip="Descartar este registro",
            on_click=lambda e, i_id=item_id: self.descartar_item_escaneado(i_id)
        )

        fila_cabecera = ft.Row([
            ft.Row([badge_idx, chip_fecha, badge_estado], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            btn_descartar
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 2. Selector de Insumo con Buscador Inteligente
        lv_suggs = ft.ListView(height=110, spacing=2, visible=False)

        def on_search_insumo_change(e):
            q = (e.control.value or "").strip().lower()
            if not q or len(q) < 2:
                lv_suggs.visible = False
                lv_suggs.controls.clear()
                self.safe_update()
                return

            tokens = q.split()
            matches = []
            for m in self.catalogo_completo:
                c_txt = f"{m.get('codigo_insumo')} {m.get('nombre')}".lower()
                if all(t in c_txt for t in tokens):
                    matches.append(m)
                    if len(matches) >= 8:
                        break

            lv_suggs.controls.clear()
            for m in matches:
                c_cod = str(m.get("codigo_insumo"))
                c_nom = str(m.get("nombre"))
                c_costo = float(m.get("costo_unitario") or 0)
                
                sugg_row = ft.Container(
                    content=ft.Row([
                        ft.Text(f"[{c_cod}]", size=11, weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Text(c_nom, size=11, weight="w500", expand=True, color="black87"),
                        ft.Text(f"Costo: ${c_costo:,.0f}", size=10, color=Config.COLOR_TEXT_MUTED)
                    ], spacing=6),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor="#F8FAFC",
                    border_radius=6,
                    border=ft.border.all(1, "#E2E8F0"),
                    on_click=lambda ev, chosen=m, i_id=item_id: self._seleccionar_insumo_para_item_escaneado(i_id, chosen)
                )
                lv_suggs.controls.append(sugg_row)

            lv_suggs.visible = (len(matches) > 0)
            self.safe_update()

        txt_buscador_fila = ft.TextField(
            value=f"[{it['codigo_insumo']}] {it['nombre']}" if es_valido else (it.get("nombre_extraido") or it.get("nombre") or ""),
            hint_text="Escribe palabras del nombre o código para buscar en BD...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            border_radius=8,
            height=38,
            text_size=12,
            content_padding=10,
            border_color=Config.COLOR_PRIMARY if es_valido else "orange700",
            on_change=on_search_insumo_change
        )

        contenedor_buscador = ft.Column([
            txt_buscador_fila,
            lv_suggs
        ], spacing=2)

        # 3. Campos de Detalle (Cantidad, Tipo, Motivo, Costo, Impacto)
        def on_cant_change(e):
            try:
                c_val = float(e.control.value.replace(',', '.') or 0)
                it["cantidad"] = c_val
                txt_impacto.value = f"${(c_val * it['costo_unitario']):,.0f}"
                self.safe_update()
            except ValueError:
                pass

        def on_costo_change(e):
            try:
                c_val = float(e.control.value.replace(',', '.') or 0)
                it["costo_unitario"] = c_val
                txt_impacto.value = f"${(it['cantidad'] * c_val):,.0f}"
                self.safe_update()
            except ValueError:
                pass

        def on_tipo_change(e):
            n_tipo = e.control.value
            it["tipo_ajuste"] = "AJUSTE_ENTRADA" if n_tipo == "ENTRADA" else "AJUSTE_SALIDA"
            if n_tipo == "ENTRADA":
                opts = ["Sobrante de Inventario", "Donación Entrante", "Devolución Cliente", "Otro (Entrada)"]
                it["motivo_ui"] = "Sobrante de Inventario"
            else:
                opts = ["Consumo Cliente (Cortesía)", "Daño / Merma", "Vencimiento", "Pérdida", "Consumo Familiar", "Donación Saliente", "Otro (Salida)"]
                it["motivo_ui"] = "Consumo Cliente (Cortesía)"
            drop_motivo_item.options = [ft.dropdown.Option(x) for x in opts]
            drop_motivo_item.value = it["motivo_ui"]
            self.safe_update()

        def on_motivo_change(e):
            it["motivo_ui"] = e.control.value
            it["tipo_ajuste"] = self.mapa_motivos.get(it["motivo_ui"], it["tipo_ajuste"])
            self.safe_update()

        txt_cant_item = ft.TextField(
            label="Cantidad",
            value=str(int(it["cantidad"]) if it["cantidad"].is_integer() else it["cantidad"]),
            width=95,
            height=38,
            dense=True,
            text_size=12,
            border_radius=8,
            text_align=ft.TextAlign.RIGHT,
            on_change=on_cant_change
        )

        drop_tipo_item = ft.Dropdown(
            label="Tipo",
            options=[ft.dropdown.Option("ENTRADA"), ft.dropdown.Option("SALIDA")],
            value="ENTRADA" if es_entrada else "SALIDA",
            width=110,
            height=38,
            dense=True,
            text_size=11,
            border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=on_tipo_change
        )

        motivos_disp = ["Sobrante de Inventario", "Donación Entrante", "Devolución Cliente", "Otro (Entrada)"] if es_entrada else ["Consumo Cliente (Cortesía)", "Daño / Merma", "Vencimiento", "Pérdida", "Consumo Familiar", "Donación Saliente", "Otro (Salida)"]
        drop_motivo_item = ft.Dropdown(
            label="Motivo",
            options=[ft.dropdown.Option(m) for m in motivos_disp],
            value=it["motivo_ui"] if it["motivo_ui"] in motivos_disp else motivos_disp[0],
            expand=True,
            height=38,
            dense=True,
            text_size=11,
            border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=on_motivo_change
        )

        txt_costo_item = ft.TextField(
            label="Costo U. ($)",
            value=str(int(it["costo_unitario"]) if it["costo_unitario"].is_integer() else it["costo_unitario"]),
            width=115,
            height=38,
            dense=True,
            text_size=12,
            border_radius=8,
            text_align=ft.TextAlign.RIGHT,
            on_change=on_costo_change
        )

        val_impacto = it["cantidad"] * it["costo_unitario"]
        txt_impacto = ft.Text(f"${val_impacto:,.0f}", size=13, weight="bold", color="green" if es_entrada else "red")

        fila_detalles = ft.Row([
            txt_cant_item,
            drop_tipo_item,
            drop_motivo_item,
            txt_costo_item,
            ft.Column([
                ft.Text("Total Impacto:", size=10, color="grey600"),
                txt_impacto
            ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 4. Observación y Botón de Guardado Individual
        def on_obs_change(e):
            it["observacion"] = e.control.value

        txt_obs_item = ft.TextField(
            label="Observación (Opcional)",
            value=it.get("observacion", ""),
            expand=True,
            height=36,
            dense=True,
            text_size=11,
            border_radius=8,
            on_change=on_obs_change
        )

        btn_guardar_item = ft.ElevatedButton(
            "Guardar Ajuste",
            icon=ft.icons.CHECK_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY if es_valido else "grey400",
            color="white",
            height=34,
            disabled=not es_valido,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=7)),
            on_click=lambda e, i_id=item_id: self.guardar_item_escaneado(i_id)
        )

        fila_acciones = ft.Row([
            txt_obs_item,
            btn_guardar_item
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                fila_cabecera,
                contenedor_buscador,
                fila_detalles,
                fila_acciones
            ], spacing=8),
            bgcolor="white",
            padding=12,
            border_radius=8,
            border=ft.border.all(1, "#86EFAC" if es_valido else "#FDE68A"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.04, "black"))
        )

    def _seleccionar_insumo_para_item_escaneado(self, item_id: str, insumo_dict: dict):
        for it in self.items_escaneados:
            if it["id"] == item_id:
                cod = str(insumo_dict.get("codigo_insumo"))
                nom = str(insumo_dict.get("nombre"))
                costo = float(insumo_dict.get("costo_unitario") or 0.0)

                # Si el costo es 0, intentar buscar última compra
                if costo <= 0:
                    try:
                        res_c = self.db._db.get(f"registro_compras?codigo_insumo=eq.{cod}&order=fecha.desc&limit=1&select=costo_unitario", timeout=4)
                        if res_c and res_c.status_code == 200 and res_c.json():
                            costo = float(res_c.json()[0].get("costo_unitario") or 0.0)
                    except Exception:
                        pass

                it["codigo_insumo"] = cod
                it["nombre"] = nom
                it["costo_unitario"] = costo
                it["estado_validacion"] = "VALIDO"
                break

        self.renderizar_lista_escaneados()

    def descartar_item_escaneado(self, item_id: str):
        self.items_escaneados = [x for x in self.items_escaneados if x["id"] != item_id]
        self.renderizar_lista_escaneados()

    def limpiar_lista_escaneados(self, e=None):
        self.items_escaneados.clear()
        self.renderizar_lista_escaneados()

    def guardar_item_escaneado(self, item_id: str):
        target = None
        for it in self.items_escaneados:
            if it["id"] == item_id:
                target = it
                break

        if not target:
            return

        cod = target.get("codigo_insumo", "").strip()
        cant = float(target.get("cantidad", 0))
        costo = float(target.get("costo_unitario", 0))
        motivo_ui = target.get("motivo_ui", "Otro (Salida)")
        tipo_bd = self.mapa_motivos.get(motivo_ui, "AJUSTE_SALIDA")
        obs = target.get("observacion", "").strip() or motivo_ui
        fecha_val = target.get("fecha") or get_hoy_local_str()

        if not cod:
            self.mostrar_alerta("Debes seleccionar un insumo con código válido antes de guardar.", "orange")
            return

        if cant <= 0:
            self.mostrar_alerta("La cantidad ajustada debe ser mayor a cero.", "red")
            return

        datos = {
            "codigo_insumo": cod,
            "tipo_ajuste": tipo_bd,
            "cantidad": cant,
            "costo_unitario_congelado": costo,
            "costo_total_ajuste": cant * costo,
            "motivo_observacion": obs,
            "fecha_ajuste": fecha_val,
            "estado_registro": "VÁLIDO"
        }

        if self.db.insert_ajuste_individual(datos):
            registrar_accion(
                accion=f"Registro de ajuste OCR ({tipo_bd}) para insumo [{cod}]: {cant} unds (Motivo: {motivo_ui})",
                modulo="AJUSTES",
                detalles=datos
            )
            self.descartar_item_escaneado(item_id)
            self.mostrar_alerta(f"Ajuste [{cod}] guardado exitosamente.", "green")
            self.load_data()
        else:
            self.mostrar_alerta(f"Error al guardar ajuste [{cod}] en la base de datos.", "red")

    def guardar_todos_escaneados_validados(self, e=None):
        validados = [x for x in self.items_escaneados if x["estado_validacion"] == "VALIDO" and x["cantidad"] > 0]
        if not validados:
            self.mostrar_alerta("No hay registros validados listos para guardar.", "orange")
            return

        lista_insert = []
        for v in validados:
            cod = v["codigo_insumo"].strip()
            cant = float(v["cantidad"])
            costo = float(v["costo_unitario"])
            motivo_ui = v.get("motivo_ui", "Otro (Salida)")
            tipo_bd = self.mapa_motivos.get(motivo_ui, "AJUSTE_SALIDA")
            obs = v.get("observacion", "").strip() or motivo_ui
            fecha_val = v.get("fecha") or get_hoy_local_str()

            lista_insert.append({
                "codigo_insumo": cod,
                "tipo_ajuste": tipo_bd,
                "cantidad": cant,
                "costo_unitario_congelado": costo,
                "costo_total_ajuste": cant * costo,
                "motivo_observacion": obs,
                "fecha_ajuste": fecha_val,
                "estado_registro": "VÁLIDO"
            })

        if self.db.insert_ajustes_masivo(lista_insert):
            ids_guardados = {x["id"] for x in validados}
            self.items_escaneados = [x for x in self.items_escaneados if x["id"] not in ids_guardados]
            registrar_accion(
                accion=f"Guardado masivo OCR de {len(lista_insert)} ajustes de inventario",
                modulo="AJUSTES",
                detalles={"conteo": len(lista_insert)}
            )
            self.renderizar_lista_escaneados()
            self.mostrar_alerta(f"¡{len(lista_insert)} ajustes guardados exitosamente!", "green")
            self.load_data()
        else:
            self.mostrar_alerta("Error al guardar el lote de ajustes en la base de datos.", "red")

