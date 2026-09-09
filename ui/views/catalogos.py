"""
Módulo de Gestión de Catálogos Comerciales para Sistema Doña Mary.
Vista tabular optimizada con paginación, filtros por catálogo/condición,
búsqueda inteligente, modificación directa de precios de venta, adición y retiro
de insumos, asignación única de foto por insumo y exportación a PDF.
"""
import os
import math
import unicodedata
import threading
import webbrowser
import flet as ft
from config import Config
from core.catalog_manager import (
    CATALOGOS_CONFIG,
    RUTA_DEFAULT_CATALOGOS,
    get_items_catalogo,
    guardar_items_catalogo,
    buscar_foto_insumo,
    guardar_foto_insumo,
    eliminar_foto_insumo,
    precargar_cache_fotos_storage,
    sincronizar_todas_fotos_a_storage,
    comprobar_foto_en_storage,
    get_datos_inventario_db,
    get_todos_insumos_inventario,
    get_mapa_catalogos_asignados,
    actualizar_insumo_inventario_db,
    formatear_precio,
    obtener_mapeo_paginas_catalogo,
    generar_html_catalogo_actualizado,
    exportar_catalogo_pdf
)
from core.logger import get_logger

logger = get_logger("CatalogosView")

def _normalizar_texto(texto: str) -> str:
    """Elimina tildes, signos y normaliza a mayúsculas para búsquedas flexibles."""
    if not texto:
        return ""
    texto_norm = unicodedata.normalize('NFKD', str(texto))
    return "".join(c for c in texto_norm if not unicodedata.combining(c)).upper().strip()

def cumple_busqueda_inteligente(query: str, *campos) -> bool:
    """
    Buscador inteligente: evalúa si cada palabra de la consulta existe en
    alguno de los campos evaluados, sin importar el orden ni los acentos.
    """
    if not query or not query.strip():
        return True
    
    terminos = _normalizar_texto(query).split()
    if not terminos:
        return True
    
    texto_evaluar = " ".join(_normalizar_texto(c) for c in campos if c)
    return all(t in texto_evaluar for t in terminos)

class CatalogosView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.padding = ft.padding.all(16)
        
        # Estado interno de datos
        self.catalogo_actual_key = "aseo"
        self.items_totales = []
        self.items_filtrados = []
        self.precios_db = {}
        self.costos_db = {}
        self.stocks_db = {}
        self.comprados_set = set()
        
        # Modo de Vista: "TABLA" o "EDITOR_PAGINAS"
        self.modo_vista = "TABLA"
        self.seccion_editor = "REJILLAS" # "REJILLAS" o "TABLAS"
        self.pagina_editor_seleccionada = 1

        # Paginación (Modo Tabla)
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        
        # Estado de modales y operaciones
        self.insumo_para_foto = None
        self.insumo_para_precio = None
        self.mapeo_paginas_actual = {"total_paginas": 0, "paginas": [], "mapa_codigo_a_pagina": {}}
        
        # FilePickers
        self.file_picker_foto = ft.FilePicker(on_result=self._on_foto_picked)
        self.file_picker_exportar = ft.FilePicker(on_result=self._on_exportar_pdf_result)

        # -------------------------------------------------------------
        # 1. FILA SUPERIOR: FILTROS Y ACCIONES GLOBALES
        # -------------------------------------------------------------
        self.btn_volver_principal = ft.IconButton(
            icon=ft.icons.ARROW_BACK_ROUNDED,
            icon_color=Config.COLOR_PRIMARY,
            icon_size=24,
            tooltip="Volver al Catálogo Principal (Vista Tabla)",
            visible=False,
            on_click=self._volver_vista_principal
        )

        self.drop_catalogo = ft.Dropdown(
            label="Catálogo Comercial",
            options=[
                ft.dropdown.Option("aseo", "🧼 Aseo"),
                ft.dropdown.Option("bolsas", "🛍️ Bolsas"),
                ft.dropdown.Option("desechables", "🍽️ Desechables"),
                ft.dropdown.Option("papeleria", "📎 Papelería"),
                ft.dropdown.Option("reposteria", "🎂 Repostería"),
                ft.dropdown.Option("salsamentaria", "🌭 Salsamentaria"),
            ],
            value="aseo",
            width=165,
            dense=True,
            border_radius=8,
            height=40,
            text_size=11.5,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=6),
            on_change=self._on_catalogo_change
        )

        self.drop_condicion = ft.Dropdown(
            label="Condición",
            options=[
                ft.dropdown.Option("TODOS", "Todos los insumos"),
                ft.dropdown.Option("SOLO_COMPRADOS", "Solo con compras"),
                ft.dropdown.Option("SOLO_STOCK", "Solo con stock (> 0)")
            ],
            value="TODOS",
            width=165,
            dense=True,
            border_radius=8,
            height=40,
            text_size=11.5,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=6),
            on_change=self._on_filtros_change
        )

        self.drop_filtro_pagina = ft.Dropdown(
            label="Página",
            options=[
                ft.dropdown.Option("TODAS", "Todas las páginas")
            ],
            value="TODAS",
            width=180,
            dense=True,
            border_radius=8,
            height=40,
            text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=self._on_filtros_change
        )

        self.btn_toggle_vista = ft.ElevatedButton(
            "Gestionar Rejillas",
            icon=ft.icons.VIEW_QUILT_ROUNDED,
            bgcolor="#00509d",
            color="white",
            height=38,
            tooltip="Abrir Editor Visual de Páginas de Rejilla",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=12, vertical=4)),
            on_click=self._on_click_boton_seccion
        )

        self.menu_herramientas = ft.PopupMenuButton(
            icon=ft.icons.SETTINGS_ROUNDED,
            tooltip="Opciones avanzadas",
            items=[
                ft.PopupMenuItem(
                    text="Exportar Catálogo a PDF",
                    icon=ft.icons.PICTURE_AS_PDF_ROUNDED,
                    on_click=self._on_exportar_pdf_click
                ),
                ft.PopupMenuItem(
                    text="Sincronizar Precios",
                    icon=ft.icons.SYNC_ROUNDED,
                    on_click=self._on_sincronizar_precios_click
                ),
                ft.PopupMenuItem(
                    text="Ver Catálogo HTML",
                    icon=ft.icons.OPEN_IN_BROWSER_ROUNDED,
                    on_click=self._on_ver_catalogo_html_click
                ),
            ]
        )

        self.indicador_exportando = ft.Container(
            visible=False,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            bgcolor="#eff6ff",
            border_radius=8,
            border=ft.border.all(1, "#bfdbfe"),
            content=ft.Row([
                ft.ProgressRing(width=16, height=16, stroke_width=2.5, color=Config.COLOR_ACCENT),
                ft.Text("Generando...", size=11, weight="bold", color=Config.COLOR_ACCENT)
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        self.fila_superior = ft.Row([
            self.btn_volver_principal,
            self.drop_catalogo,
            self.drop_condicion,
            self.drop_filtro_pagina,
            ft.Container(expand=True),
            self.indicador_exportando,
            self.btn_toggle_vista,
            self.menu_herramientas
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # -------------------------------------------------------------
        # 2. FILA DE BÚSQUEDA Y ADICIÓN (VISTA TABLA)
        # -------------------------------------------------------------
        self.txt_buscador = ft.TextField(
            hint_text="Buscar insumo por código o nombre en este catálogo...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            expand=True,
            on_change=self._on_buscador_change
        )

        self.btn_anadir_insumo = ft.ElevatedButton(
            "Añadir Insumo",
            icon=ft.icons.ADD_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=self._abrir_modal_anadir_insumo
        )

        self.fila_busqueda = ft.Row([
            self.txt_buscador,
            self.btn_anadir_insumo
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # -------------------------------------------------------------
        # 3. TABLA DE INSUMOS DEL CATÁLOGO
        # -------------------------------------------------------------
        self.tabla_insumos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Foto", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED)),
                ft.DataColumn(ft.Text("Código", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED)),
                ft.DataColumn(ft.Text("Nombre del Insumo", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED)),
                ft.DataColumn(ft.Text("Pág. Catálogo", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED)),
                ft.DataColumn(ft.Text("Costo Unitario", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED), numeric=True),
                ft.DataColumn(ft.Text("% Margen", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED)),
                ft.DataColumn(ft.Text("Precio Venta Catálogo", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED), numeric=True),
                ft.DataColumn(ft.Text("Origen Precio", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED)),
                ft.DataColumn(ft.Text("Acciones", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED)),
            ],
            rows=[],
            heading_row_height=42,
            data_row_min_height=56,
            column_spacing=16,
            border_radius=8
        )

        # Contenedor con scroll bidireccional adaptable para la tabla
        self.contenedor_tabla = ft.Container(
            expand=True,
            border_radius=10,
            bgcolor=Config.COLOR_SURFACE,
            border=ft.border.all(1, Config.COLOR_BORDER),
            padding=ft.padding.all(8),
            content=ft.ListView([
                ft.Row([self.tabla_insumos], scroll=ft.ScrollMode.ADAPTIVE)
            ], expand=True)
        )

        # -------------------------------------------------------------
        # 4. PIE DE PÁGINA: PAGINACIÓN (VISTA TABLA)
        # -------------------------------------------------------------
        self.lbl_info_paginacion = ft.Text(
            "Cargando insumos...",
            size=12,
            color=Config.COLOR_TEXT_MUTED,
            weight="w600"
        )

        self.btn_prev_page = ft.IconButton(
            icon=ft.icons.CHEVRON_LEFT_ROUNDED,
            tooltip="Página anterior",
            icon_size=20,
            on_click=self._on_prev_page
        )
        self.lbl_num_pagina = ft.Text("Pág 1 de 1", size=12, weight="bold", color=Config.COLOR_TEXT)
        self.btn_next_page = ft.IconButton(
            icon=ft.icons.CHEVRON_RIGHT_ROUNDED,
            tooltip="Página siguiente",
            icon_size=20,
            on_click=self._on_next_page
        )

        self.barra_paginacion = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            content=ft.Row([
                self.lbl_info_paginacion,
                ft.Row([
                    self.btn_prev_page,
                    self.lbl_num_pagina,
                    self.btn_next_page
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # CONTENEDOR 1: VISTA TABULAR COMPLETA
        self.contenedor_vista_tabla = ft.Column([
            self.fila_busqueda,
            self.contenedor_tabla,
            self.barra_paginacion
        ], spacing=10, expand=True, visible=True)

        # CONTENEDOR 2: EDITOR VISUAL DE PÁGINAS (PANEL COMPLETO)
        self.contenedor_vista_editor = ft.Column([], spacing=10, expand=True, visible=False)
        self._construir_estructura_editor_paginas()

        # Layout Principal de la Vista
        self.content = ft.Column([
            ft.Row([
                ft.Text("Gestión de Catálogos Comerciales", size=22, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Container(expand=True),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.fila_superior,
            self.contenedor_vista_tabla,
            self.contenedor_vista_editor
        ], spacing=10, expand=True)

    def _construir_estructura_editor_paginas(self):
        """Inicializa la sub-barra y el lienzo principal del Editor Visual de Páginas."""
        self.drop_pagina_editor = ft.Dropdown(
            label="Página en Edición",
            options=[],
            value="1",
            width=280,
            dense=True,
            border_radius=8,
            height=40,
            text_size=11.5,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=self._on_pagina_editor_change
        )

        self.btn_prev_pag_editor = ft.IconButton(
            icon=ft.icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_size=16,
            tooltip="Página Anterior",
            on_click=self._on_prev_pag_editor
        )

        self.btn_next_pag_editor = ft.IconButton(
            icon=ft.icons.ARROW_FORWARD_IOS_ROUNDED,
            icon_size=16,
            tooltip="Página Siguiente",
            on_click=self._on_next_pag_editor
        )

        self.btn_editar_pagina_editor = ft.OutlinedButton(
            "Editar Familia",
            icon=ft.icons.EDIT_NOTE_ROUNDED,
            icon_color=Config.COLOR_PRIMARY,
            height=38,
            tooltip="Editar el título de familia y categoría de esta página",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=10)),
            on_click=self._abrir_modal_editar_pagina
        )

        self.btn_nueva_pagina_editor = ft.OutlinedButton(
            "Nueva Página",
            icon=ft.icons.NOTE_ADD_ROUNDED,
            icon_color=Config.COLOR_PRIMARY,
            height=38,
            tooltip="Añadir una nueva página física al catálogo",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=10)),
            on_click=self._abrir_modal_nueva_pagina
        )

        self.btn_eliminar_pagina_editor = ft.OutlinedButton(
            "Eliminar Página",
            icon=ft.icons.DELETE_SWEEP_ROUNDED,
            icon_color="red700",
            height=38,
            tooltip="Eliminar esta página completa y retirar sus insumos del catálogo",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=10)),
            on_click=self._confirmar_eliminar_pagina_actual
        )

        self.barra_herramientas_editor = ft.Container(
            bgcolor="#f8fafc",
            border=ft.border.all(1, "#cbd5e1"),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            content=ft.Row([
                self.btn_prev_pag_editor,
                self.drop_pagina_editor,
                self.btn_next_pag_editor,
                ft.Container(expand=True),
                self.btn_editar_pagina_editor,
                self.btn_nueva_pagina_editor,
                self.btn_eliminar_pagina_editor
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # Lienzo donde se renderizan las tarjetas de productos de la página (máx 4)
        self.lienzo_pagina_editor = ft.Container(
            expand=True,
            bgcolor="#f1f5f9",
            border_radius=10,
            border=ft.border.all(1, "#cbd5e1"),
            padding=ft.padding.all(14),
            content=ft.Column([], scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        )

        self.contenedor_vista_editor.controls = [
            self.barra_herramientas_editor,
            self.lienzo_pagina_editor
        ]

    def _volver_vista_principal(self, e):
        """Regresa al módulo principal de gestión de inventario / catálogo."""
        self.modo_vista = "TABLA"
        self.btn_volver_principal.visible = False
        self.btn_toggle_vista.text = "Gestionar Rejillas"
        self.btn_toggle_vista.icon = ft.icons.VIEW_QUILT_ROUNDED
        self.btn_toggle_vista.bgcolor = "#00509d"
        self.btn_toggle_vista.tooltip = "Abrir Editor de Páginas de Rejilla con fotos"
        self.drop_condicion.visible = True
        self.drop_filtro_pagina.visible = True
        self.contenedor_vista_tabla.visible = True
        self.contenedor_vista_editor.visible = False
        self._aplicar_filtros()
        self._safe_update()

    def _on_click_boton_seccion(self, e):
        """
        Conmuta entre Gestión de Rejillas y Gestión de Tablas o ingresa al editor.
        """
        if self.modo_vista == "TABLA":
            self.modo_vista = "EDITOR_PAGINAS"
            self.seccion_editor = "REJILLAS"
            self.btn_volver_principal.visible = True
            self.btn_toggle_vista.text = "Gestionar Tablas"
            self.btn_toggle_vista.icon = ft.icons.TABLE_ROWS_ROUNDED
            self.btn_toggle_vista.bgcolor = "#334155"
            self.btn_toggle_vista.tooltip = "Ver y gestionar las páginas de tablas resumen de insumos"
            self.drop_condicion.visible = False
            self.drop_filtro_pagina.visible = False
            self.contenedor_vista_tabla.visible = False
            self.contenedor_vista_editor.visible = True
            self._actualizar_opciones_drop_editor()
            self._render_pagina_editor_visual()
        elif self.seccion_editor == "REJILLAS":
            self.seccion_editor = "TABLAS"
            self.btn_toggle_vista.text = "Gestionar Rejillas"
            self.btn_toggle_vista.icon = ft.icons.VIEW_QUILT_ROUNDED
            self.btn_toggle_vista.bgcolor = "#00509d"
            self.btn_toggle_vista.tooltip = "Volver a la edición de páginas de rejilla con fotos"
            self._actualizar_opciones_drop_editor()
            self._render_pagina_editor_visual()
        else: # seccion_editor == "TABLAS"
            self.seccion_editor = "REJILLAS"
            self.btn_toggle_vista.text = "Gestionar Tablas"
            self.btn_toggle_vista.icon = ft.icons.TABLE_ROWS_ROUNDED
            self.btn_toggle_vista.bgcolor = "#334155"
            self.btn_toggle_vista.tooltip = "Ver y gestionar las páginas de tablas resumen de insumos"
            self._actualizar_opciones_drop_editor()
            self._render_pagina_editor_visual()

        self._safe_update()

    def did_mount(self):
        """Al montarse en pantalla, registra los FilePickers y carga datos."""
        if self.page:
            if self.file_picker_foto not in self.page.overlay:
                self.page.overlay.append(self.file_picker_foto)
            if self.file_picker_exportar not in self.page.overlay:
                self.page.overlay.append(self.file_picker_exportar)
            self.page.update()

        threading.Thread(target=self._cargar_datos_db, daemon=True).start()

    # -------------------------------------------------------------
    # CARGA Y ACTUALIZACIÓN DE DATOS
    # -------------------------------------------------------------
    def _cargar_datos_db(self):
        try:
            # Precargar inventario de fotos de Supabase Storage en memoria en segundo plano
            precargar_cache_fotos_storage()
            self.precios_db, self.costos_db, self.stocks_db, self.comprados_set = get_datos_inventario_db()
            self._cargar_catalogo_activo()
        except Exception as ex:
            logger.error(f"Error al cargar datos de inventario: {ex}")
        finally:
            self._safe_update()

    def _cargar_catalogo_activo(self):
        """Carga la lista de ítems del catálogo activo y su mapeo físico de páginas."""
        self.items_totales = get_items_catalogo(self.catalogo_actual_key)
        self.mapeo_paginas_actual = obtener_mapeo_paginas_catalogo(self.catalogo_actual_key, forzar_recarga=True, items_data=self.items_totales)

        # 1. Poblar opciones del filtro por página (Vista Tabla, omitiendo Portada)
        opciones_p = [ft.dropdown.Option("TODAS", "Todas las páginas")]
        for p in self.mapeo_paginas_actual.get("paginas", []):
            if p.get("tipo") in ("Portada", "Contraportada", "Separador de Sección") or p.get("total_items", 0) == 0:
                continue
            num = p["num_pagina"]
            tipo_txt = "Rejilla" if p["tipo"] == "Rejilla de Productos" else "Tabla" if p["tipo"] == "Tabla Resumen" else p["tipo"]
            cnt = p["total_items"]
            opciones_p.append(
                ft.dropdown.Option(str(num), f"Pág. {num} ({tipo_txt}) • {cnt} ins.")
            )
        self.drop_filtro_pagina.options = opciones_p
        self.drop_filtro_pagina.value = "TODAS"

        # 2. Actualizar opciones del selector de página en el Editor Visual
        self._actualizar_opciones_drop_editor()

        # 3. Si un ítem no tiene precio asignado en su JSON, poblarlo con el precio de inventario
        for it in self.items_totales:
            cod = str(it.get("codigo", "")).strip()
            if "precio_venta" not in it:
                if cod in self.precios_db and self.precios_db[cod] > 0:
                    it["precio_venta"] = self.precios_db[cod]
                    it["precio_manual"] = False
                else:
                    try:
                        p_orig = float(str(it.get("precio_original", "0")).replace("$", "").replace(".", "").replace(",", "."))
                    except Exception:
                        p_orig = 0.0
                    it["precio_venta"] = p_orig
                    it["precio_manual"] = False

        self.current_page = 1
        self._aplicar_filtros()
        if self.modo_vista == "EDITOR_PAGINAS":
            self._render_pagina_editor_visual()

    def _obtener_paginas_seccion_activa(self) -> list[dict]:
        """Obtiene las páginas físicas pertenecientes a la sección activa (REJILLAS o TABLAS), excluyendo portadas/diseño."""
        paginas = self.mapeo_paginas_actual.get("paginas", [])
        if self.seccion_editor == "TABLAS":
            return [p for p in paginas if p.get("tipo") == "Tabla Resumen"]
        else:
            # Sección REJILLAS (Únicamente Rejillas de productos, excluyendo Portada y Contraportada)
            return [p for p in paginas if p.get("tipo") == "Rejilla de Productos"]

    def _actualizar_opciones_drop_editor(self):
        """Actualiza el dropdown de páginas mostrando ÚNICAMENTE las páginas de la sección activa."""
        pags_seccion = self._obtener_paginas_seccion_activa()
        opciones = []
        for p in pags_seccion:
            num = p["num_pagina"]
            tipo = p["tipo"]
            cnt = p["total_items"]
            if tipo == "Rejilla de Productos":
                texto_opt = f"Pág. {num} • Rejilla ({cnt}/4)"
            elif tipo == "Tabla Resumen":
                texto_opt = f"Pág. {num} • Tabla ({cnt} ins.)"
            else:
                texto_opt = f"Pág. {num} • {tipo}"
            
            opciones.append(ft.dropdown.Option(str(num), texto_opt))

        if not opciones:
            if self.seccion_editor == "TABLAS":
                opciones.append(ft.dropdown.Option("none", "No hay páginas de tablas en este catálogo"))
            else:
                opciones.append(ft.dropdown.Option("none", "No hay páginas de rejilla en este catálogo"))

        self.drop_pagina_editor.options = opciones

        # Validar si la página seleccionada actualmente pertenece a esta sección
        nums_seccion = [p["num_pagina"] for p in pags_seccion]
        if nums_seccion:
            if self.pagina_editor_seleccionada not in nums_seccion:
                self.pagina_editor_seleccionada = nums_seccion[0]
            self.drop_pagina_editor.value = str(self.pagina_editor_seleccionada)
        else:
            self.drop_pagina_editor.value = "none"

    def _on_pagina_editor_change(self, e):
        try:
            if self.drop_pagina_editor.value and self.drop_pagina_editor.value != "none":
                self.pagina_editor_seleccionada = int(self.drop_pagina_editor.value)
                self._render_pagina_editor_visual()
                self._safe_update()
        except Exception:
            pass

    def _on_prev_pag_editor(self, e):
        pags_seccion = self._obtener_paginas_seccion_activa()
        nums_seccion = [p["num_pagina"] for p in pags_seccion]
        if not nums_seccion or self.pagina_editor_seleccionada not in nums_seccion:
            return
        idx = nums_seccion.index(self.pagina_editor_seleccionada)
        if idx > 0:
            self.pagina_editor_seleccionada = nums_seccion[idx - 1]
            self.drop_pagina_editor.value = str(self.pagina_editor_seleccionada)
            self._render_pagina_editor_visual()
            self._safe_update()

    def _on_next_pag_editor(self, e):
        pags_seccion = self._obtener_paginas_seccion_activa()
        nums_seccion = [p["num_pagina"] for p in pags_seccion]
        if not nums_seccion or self.pagina_editor_seleccionada not in nums_seccion:
            return
        idx = nums_seccion.index(self.pagina_editor_seleccionada)
        if idx < len(nums_seccion) - 1:
            self.pagina_editor_seleccionada = nums_seccion[idx + 1]
            self.drop_pagina_editor.value = str(self.pagina_editor_seleccionada)
            self._render_pagina_editor_visual()
            self._safe_update()

    def _aplicar_filtros(self):
        """Filtra la lista de insumos y recalcula la paginación."""
        cond = self.drop_condicion.value
        busq = self.txt_buscador.value or ""
        filtro_pag = self.drop_filtro_pagina.value

        codigos_en_pagina = None
        if filtro_pag and filtro_pag != "TODAS":
            try:
                num_p = int(filtro_pag)
                paginas = self.mapeo_paginas_actual.get("paginas", [])
                if 1 <= num_p <= len(paginas):
                    p_sel = paginas[num_p - 1]
                    codigos_en_pagina = set(p_sel.get("items_cards", []) + p_sel.get("items_tablas", []))
            except Exception:
                codigos_en_pagina = None

        filtrados = []
        for it in self.items_totales:
            cod = str(it.get("codigo", "")).strip()

            # 1. Filtro por página del catálogo
            if codigos_en_pagina is not None and cod not in codigos_en_pagina:
                continue

            # 2. Filtro Condición
            if cond == "SOLO_COMPRADOS" and cod not in self.comprados_set:
                continue
            if cond == "SOLO_STOCK" and self.stocks_db.get(cod, 0.0) <= 0:
                continue

            # 3. Filtro Buscador inteligente
            if not cumple_busqueda_inteligente(busq, cod, it.get("nombre"), it.get("descripcion"), it.get("familia")):
                continue

            filtrados.append(it)

        self.items_filtrados = filtrados
        self.total_pages = max(1, math.ceil(len(filtrados) / self.page_size))
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages

        self._render_pagina_actual()

    def _render_pagina_actual(self):
        """Construye las filas de la tabla para la página actual (15 ítems)."""
        self.tabla_insumos.rows.clear()
        
        total_items = len(self.items_filtrados)
        if total_items == 0:
            self.lbl_info_paginacion.value = "No hay insumos para mostrar"
            self.lbl_num_pagina.value = "Pág 0 de 0"
            self.btn_prev_page.disabled = True
            self.btn_next_page.disabled = True
            return

        inicio = (self.current_page - 1) * self.page_size
        fin = min(inicio + self.page_size, total_items)
        pagina_items = self.items_filtrados[inicio:fin]

        self.lbl_info_paginacion.value = f"Mostrando {inicio + 1} - {fin} de {total_items} insumos en catálogo"
        self.lbl_num_pagina.value = f"Pág {self.current_page} de {self.total_pages}"
        self.btn_prev_page.disabled = (self.current_page <= 1)
        self.btn_next_page.disabled = (self.current_page >= self.total_pages)

        for it in pagina_items:
            cod = str(it.get("codigo", "")).strip()
            nom = str(it.get("nombre", "")).strip()
            precio_val = float(it.get("precio_venta", 0.0))
            es_manual = bool(it.get("precio_manual", False))
            costo_val = self.costos_db.get(cod, 0.0)

            # 1. Foto: buscar si ya existe la foto oficial para este insumo en Supabase Storage
            foto_url = buscar_foto_insumo(self.catalogo_actual_key, nom)
            if foto_url:
                thumb_content = ft.Container(
                    width=38,
                    height=38,
                    border_radius=6,
                    border=ft.border.all(1, "#cbd5e1"),
                    bgcolor="#ffffff",
                    content=ft.Image(src=foto_url, fit=ft.ImageFit.CONTAIN),
                    tooltip=f"Ver / Cambiar foto de {nom} (Supabase Storage)",
                    on_click=lambda _, item=it: self._abrir_modal_gestion_foto(item)
                )
            else:
                thumb_content = ft.IconButton(
                    icon=ft.icons.ADD_A_PHOTO_ROUNDED,
                    icon_color=Config.COLOR_PRIMARY,
                    icon_size=18,
                    tooltip=f"Añadir foto a {nom} (Supabase Storage)",
                    on_click=lambda _, item=it: self._abrir_modal_gestion_foto(item)
                )

            # 2. Código
            badge_cod = ft.Container(
                content=ft.Text(cod, size=10, weight="bold", color="white"),
                bgcolor="#00509d",
                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                border_radius=6
            )

            # 3. Página en Catálogo (Badge de ubicación física en el PDF/HTML)
            map_info = self.mapeo_paginas_actual.get("mapa_codigo_a_pagina", {}).get(cod)
            if map_info:
                es_rejilla = (map_info["tipo"] == "Rejilla")
                bg_p = "#eff6ff" if es_rejilla else "#f0fdf4"
                txt_p = "#1e40af" if es_rejilla else "#166534"
                brd_p = "#bfdbfe" if es_rejilla else "#bbf7d0"
                ic_p = ft.icons.VIEW_QUILT_ROUNDED if es_rejilla else ft.icons.TABLE_ROWS_ROUNDED
                lbl_tipo = "Rejilla" if es_rejilla else "Tabla"
                badge_pagina = ft.Container(
                    content=ft.Row([
                        ft.Icon(ic_p, size=12, color=txt_p),
                        ft.Text(f"Pág. {map_info['num_pagina']} ({lbl_tipo})", size=10, weight="bold", color=txt_p)
                    ], spacing=3, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=bg_p,
                    border=ft.border.all(1, brd_p),
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    tooltip=f"Página física {map_info['num_pagina']} en el PDF\n{map_info['categoria']} - {map_info['familia']}"
                )
            else:
                badge_pagina = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.FIBER_NEW_ROUNDED, size=12, color="#b45309"),
                        ft.Text("Pág. Final", size=10, weight="bold", color="#b45309")
                    ], spacing=3, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor="#fffbeb",
                    border=ft.border.all(1, "#fde68a"),
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    tooltip="Insumo nuevo incorporado al catálogo"
                )

            # 4. Costo Unitario
            if costo_val > 0:
                txt_costo = ft.Text(formatear_precio(costo_val), size=11, weight="w500", color=Config.COLOR_TEXT_MUTED)
            else:
                txt_costo = ft.Text("Sin costo", size=10, italic=True, color="grey500")

            # 5. % Margen / Ganancia interactivo
            if costo_val > 0:
                pct = ((precio_val - costo_val) / costo_val) * 100
                color_bg = "#dcfce7" if pct >= 0 else "#fee2e2"
                color_txt = "green900" if pct >= 0 else "red900"
                signo = "+" if pct > 0 else ""
                badge_pct = ft.Container(
                    content=ft.Text(f"{signo}{pct:.1f}%", size=10, weight="bold", color=color_txt),
                    bgcolor=color_bg,
                    padding=ft.padding.symmetric(horizontal=7, vertical=3),
                    border_radius=6,
                    tooltip="Click para ajustar margen o precio",
                    on_click=lambda _, item=it: self._abrir_modal_editar_precio(item)
                )
            else:
                badge_pct = ft.Container(
                    content=ft.Text("N/A", size=9.5, color="grey600"),
                    bgcolor="#f1f5f9",
                    padding=ft.padding.symmetric(horizontal=6, vertical=3),
                    border_radius=4,
                    tooltip="Insumo sin costo registrado en inventario"
                )

            # 6. Origen del precio
            badge_origen = ft.Container(
                content=ft.Text("Manual" if es_manual else "Inventario", size=9.5, weight="w600", color="white"),
                bgcolor="amber800" if es_manual else "blueGrey700",
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=4
            )

            # 7. Botones de acción
            acciones_row = ft.Row([
                ft.IconButton(
                    icon=ft.icons.EDIT_NOTE_ROUNDED,
                    icon_color="blue700",
                    icon_size=18,
                    tooltip="Modificar precio de venta",
                    on_click=lambda _, item=it: self._abrir_modal_editar_precio(item)
                ),
                ft.IconButton(
                    icon=ft.icons.ADD_PHOTO_ALTERNATE_ROUNDED,
                    icon_color="teal700",
                    icon_size=18,
                    tooltip="Foto en Supabase Storage",
                    on_click=lambda _, item=it: self._abrir_modal_gestion_foto(item)
                ),
                ft.IconButton(
                    icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                    icon_color="red700",
                    icon_size=18,
                    tooltip="Retirar del catálogo",
                    on_click=lambda _, item=it: self._confirmar_retirar_insumo(item)
                )
            ], spacing=2)

            fila = ft.DataRow(
                cells=[
                    ft.DataCell(thumb_content),
                    ft.DataCell(badge_cod),
                    ft.DataCell(ft.Text(nom, size=11, weight="w600", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)),
                    ft.DataCell(badge_pagina),
                    ft.DataCell(txt_costo),
                    ft.DataCell(badge_pct),
                    ft.DataCell(
                        ft.Text(formatear_precio(precio_val), size=12, weight="bold", color=Config.COLOR_PRIMARY)
                    ),
                    ft.DataCell(badge_origen),
                    ft.DataCell(acciones_row)
                ]
            )
            self.tabla_insumos.rows.append(fila)

    # -------------------------------------------------------------
    # EVENTOS DE NAVEGACIÓN Y FILTROS
    # -------------------------------------------------------------
    def _on_catalogo_change(self, e):
        self.catalogo_actual_key = self.drop_catalogo.value
        self.txt_buscador.value = ""
        self._cargar_catalogo_activo()
        self._safe_update()

    def _on_filtros_change(self, e):
        self.current_page = 1
        self._aplicar_filtros()
        self._safe_update()

    def _on_buscador_change(self, e):
        self.current_page = 1
        self._aplicar_filtros()
        self._safe_update()

    def _on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self._render_pagina_actual()
            self._safe_update()

    def _on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._render_pagina_actual()
            self._safe_update()

    # -------------------------------------------------------------
    # HERRAMIENTAS: SINCRONIZACIÓN Y VISTA PREVIA HTML
    # -------------------------------------------------------------
    def _on_sincronizar_precios_click(self, e):
        """
        Trae los precios vigentes de venta de Supabase y actualiza los insumos
        del catálogo activo, respetando los que hayan sido modificados manualmente.
        """
        self.menu_herramientas.disabled = True
        self._safe_update()
        self._mostrar_snackbar("🔄 Sincronizando precios desde inventario...", "blue")

        def _tarea():
            try:
                self.precios_db, self.costos_db, self.stocks_db, self.comprados_set = get_datos_inventario_db()
                actualizados = 0
                for it in self.items_totales:
                    cod = str(it.get("codigo", "")).strip()
                    # Solo actualizar si no fue modificado manualmente en el catálogo
                    if not it.get("precio_manual", False):
                        if cod in self.precios_db and self.precios_db[cod] > 0:
                            it["precio_venta"] = self.precios_db[cod]
                            actualizados += 1

                # Guardar cambios
                guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
                self._aplicar_filtros()
                self._mostrar_snackbar(f"✅ Precios sincronizados ({actualizados} actualizados desde inventario).", "green")
            except Exception as ex:
                self._mostrar_snackbar(f"Error al sincronizar precios: {ex}", "red")
            finally:
                self.menu_herramientas.disabled = False
                self._safe_update()

        threading.Thread(target=_tarea, daemon=True).start()

    def _on_sincronizar_fotos_click(self, e):
        """
        Sube masivamente las imágenes locales a Supabase Storage,
        omitiendo las que ya están cargadas para una sincronización rápida y sin duplicados.
        """
        self.menu_herramientas.disabled = True
        self._safe_update()
        self._mostrar_snackbar("☁️ Verificando y sincronizando fotos con Supabase Storage...", "blue")

        def _tarea_fotos():
            try:
                res = sincronizar_todas_fotos_a_storage(self.catalogo_actual_key)
                subidas = res.get("subidas", 0)
                ya_existentes = res.get("ya_existentes", 0)
                errores = res.get("errores", 0)
                self._mostrar_snackbar(
                    f"✅ Sincronización: {subidas} nuevas fotos subidas | {ya_existentes} ya en Storage | {errores} errores",
                    "green"
                )
                self._render_pagina_actual()
            except Exception as ex:
                self._mostrar_snackbar(f"Error durante la sincronización: {ex}", "red")
            finally:
                self.menu_herramientas.disabled = False
                self._safe_update()

        threading.Thread(target=_tarea_fotos, daemon=True).start()

    def _on_ver_catalogo_html_click(self, e):
        """Abre la plantilla interactiva HTML del catálogo con todas las modificaciones en vivo."""
        try:
            cfg = CATALOGOS_CONFIG.get(self.catalogo_actual_key)
            if not cfg:
                self._mostrar_snackbar("Catálogo no encontrado.", "red")
                return

            self._mostrar_snackbar(f"Generando vista previa HTML de {cfg['nombre']}...", "blue")
            ok, res = generar_html_catalogo_actualizado(self.catalogo_actual_key, self.precios_db, self.items_totales)
            if ok:
                webbrowser.open(os.path.abspath(res))
                self._mostrar_snackbar(f"✅ Catálogo HTML ({cfg['nombre']}) abierto en el navegador con datos actualizados.", "green")
            else:
                self._mostrar_snackbar(f"Error al generar HTML: {res}", "red")
        except Exception as ex:
            self._mostrar_snackbar(f"Error al abrir catálogo HTML: {ex}", "red")

    # -------------------------------------------------------------
    # EDITOR VISUAL DE PÁGINAS: RENDERIZADO Y CONTROL (PANEL COMPLETO)
    # -------------------------------------------------------------
    def _render_pagina_editor_visual(self):
        """
        Renderiza en lienzo interactivo la página seleccionada del catálogo,
        con límite estricto de máximo 4 insumos por página y acceso directo a edición/fotos.
        """
        paginas = self.mapeo_paginas_actual.get("paginas", [])
        total_p = len(paginas)
        self.lienzo_pagina_editor.content.controls.clear()

        pags_seccion = self._obtener_paginas_seccion_activa()
        nums_seccion = [p["num_pagina"] for p in pags_seccion]

        if not nums_seccion:
            self.btn_prev_pag_editor.disabled = True
            self.btn_next_pag_editor.disabled = True
            self.btn_eliminar_pagina_editor.disabled = True
            
            tipo_label = "tablas resumen" if self.seccion_editor == "TABLAS" else "rejilla de productos"
            empty_banner = ft.Container(
                width=800,
                bgcolor="#ffffff",
                border=ft.border.all(1, "#cbd5e1"),
                border_radius=12,
                padding=ft.padding.all(35),
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.icons.TABLE_ROWS_ROUNDED if self.seccion_editor == "TABLAS" else ft.icons.VIEW_QUILT_ROUNDED, size=48, color="#94a3b8"),
                    ft.Text(f"No hay páginas de {tipo_label} en este catálogo.", size=14, weight="bold", color="#334155"),
                    ft.Text("Puedes agregar una nueva página para comenzar a estructurar tus insumos.", size=11, color=Config.COLOR_TEXT_MUTED),
                    ft.ElevatedButton(
                        "+ Crear Nueva Página",
                        icon=ft.icons.ADD_ROUNDED,
                        bgcolor=Config.COLOR_PRIMARY,
                        color="white",
                        height=36,
                        on_click=self._abrir_modal_nueva_pagina
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
            )
            self.lienzo_pagina_editor.content.controls.append(empty_banner)
            if self.page:
                self.page.update()
            return

        if self.pagina_editor_seleccionada not in nums_seccion:
            self.pagina_editor_seleccionada = nums_seccion[0]
            self.drop_pagina_editor.value = str(self.pagina_editor_seleccionada)

        p_info = paginas[self.pagina_editor_seleccionada - 1]
        num_pag = p_info["num_pagina"]
        tipo = p_info["tipo"]
        cat = p_info.get("categoria", "")
        fam = p_info.get("familia", f"Página {num_pag}")
        cards_cods = p_info.get("items_cards", [])
        tablas_cods = p_info.get("items_tablas", [])

        # Actualizar botones de anterior y siguiente según la lista de la sección activa
        idx_sec = nums_seccion.index(num_pag)
        self.btn_prev_pag_editor.disabled = (idx_sec <= 0)
        self.btn_next_pag_editor.disabled = (idx_sec >= len(nums_seccion) - 1)
        self.btn_eliminar_pagina_editor.disabled = (num_pag == 1 or total_p <= 1)
        self.btn_editar_pagina_editor.disabled = (tipo in ("Portada", "Contraportada"))

        # Mapear ítems actuales por código para fotos y precios
        items_dict = {str(it.get("codigo", "")).strip(): it for it in self.items_totales}

        # Header de la Página dentro del lienzo
        cabecera_lienzo = ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            bgcolor="#ffffff",
            border_radius=8,
            border=ft.border.all(1, "#cbd5e1"),
            content=ft.Row([
                ft.Column([
                    ft.Text(f"PÁGINA FÍSICA {num_pag} • {cat.upper() if cat else 'CATÁLOGO'}", size=11, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Row([
                        ft.Text(fam, size=15, weight="bold", color="#0f172a"),
                        ft.IconButton(
                            icon=ft.icons.EDIT_NOTE_ROUNDED,
                            icon_color=Config.COLOR_PRIMARY,
                            icon_size=18,
                            tooltip="Editar título de familia / línea de esta página",
                            visible=(tipo not in ("Portada", "Contraportada")),
                            on_click=self._abrir_modal_editar_pagina
                        )
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=2, expand=True),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    bgcolor="#eff6ff",
                    border_radius=6,
                    border=ft.border.all(1, "#bfdbfe"),
                    content=ft.Text(
                        f"{len(cards_cods)} / 4 Insumos Asignados" if tipo == "Rejilla de Productos" else f"{len(tablas_cods)} Insumos",
                        size=11,
                        weight="bold",
                        color="#1e40af"
                    )
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )
        self.lienzo_pagina_editor.content.controls.append(cabecera_lienzo)

        # -------------------------------------------------------------
        # CASO 1: REJILLA DE PRODUCTOS (MÁXIMO 4 INSUMOS CON FOTO)
        # -------------------------------------------------------------
        if tipo == "Rejilla de Productos":
            cards_fila = ft.Row(wrap=True, spacing=14, run_spacing=14)
            
            # 1. Renderizar insumos existentes en esta página (hasta 4)
            for cod_c in cards_cods:
                it = items_dict.get(cod_c, {
                    "codigo": cod_c,
                    "nombre": f"Insumo {cod_c}",
                    "descripcion": "",
                    "precio_venta": self.precios_db.get(cod_c, 0.0),
                    "precio_manual": False
                })
                nom = it.get("nombre", f"Insumo {cod_c}")
                desc = it.get("descripcion", "") or "Sin descripción adicional"
                pv = float(it.get("precio_venta", 0.0))
                cu = self.costos_db.get(cod_c, 0.0)
                es_manual = bool(it.get("precio_manual", False))

                foto_url = buscar_foto_insumo(self.catalogo_actual_key, nom)
                
                # Thumbnail con zoom óptico
                if foto_url:
                    img_preview = ft.Container(
                        width=110,
                        height=110,
                        border_radius=8,
                        bgcolor="#ffffff",
                        border=ft.border.all(1, "#cbd5e1"),
                        content=ft.Image(src=foto_url, fit=ft.ImageFit.CONTAIN),
                        alignment=ft.alignment.center,
                        tooltip="Click para gestionar o cambiar foto",
                        on_click=lambda _, item_ref=it: self._abrir_modal_gestion_foto(item_ref)
                    )
                else:
                    img_preview = ft.Container(
                        width=110,
                        height=110,
                        border_radius=8,
                        bgcolor="#f8fafc",
                        border=ft.border.all(1, "#cbd5e1"),
                        content=ft.Column([
                            ft.Icon(ft.icons.ADD_A_PHOTO_ROUNDED, size=26, color=Config.COLOR_PRIMARY),
                            ft.Text("Subir Foto", size=10, weight="bold", color=Config.COLOR_PRIMARY)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=3),
                        alignment=ft.alignment.center,
                        tooltip="Subir foto a Supabase Storage",
                        on_click=lambda _, item_ref=it: self._abrir_modal_gestion_foto(item_ref)
                    )

                # Margen badge
                if cu > 0 and pv > 0:
                    pct = ((pv - cu) / cu) * 100
                    color_bg = "#dcfce7" if pct >= 0 else "#fee2e2"
                    color_txt = "green900" if pct >= 0 else "red900"
                    signo = "+" if pct > 0 else ""
                    badge_margen = ft.Container(
                        content=ft.Text(f"{signo}{pct:.1f}%", size=10, weight="bold", color=color_txt),
                        bgcolor=color_bg,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=4
                    )
                else:
                    badge_margen = ft.Container(
                        content=ft.Text("Sin costo", size=9.5, color="grey600"),
                        bgcolor="#f1f5f9",
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=4
                    )

                tarjeta_insumo = ft.Container(
                    width=420,
                    bgcolor="#ffffff",
                    border=ft.border.all(1, "#cbd5e1"),
                    border_radius=10,
                    padding=ft.padding.all(12),
                    shadow=ft.BoxShadow(blur_radius=4, color="#0000000d", offset=ft.Offset(0, 2)),
                    content=ft.Column([
                        # Fila superior de badges
                        ft.Row([
                            ft.Container(
                                content=ft.Text(f"CÓD: {cod_c}", size=11, weight="bold", color="white"),
                                bgcolor="#00509d",
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                border_radius=5
                            ),
                            ft.Container(
                                content=ft.Text("Manual" if es_manual else "Inventario", size=9.5, weight="bold", color="white"),
                                bgcolor="amber800" if es_manual else "blueGrey700",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            ),
                            badge_margen,
                            ft.Container(expand=True),
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        
                        # Cuerpo con foto y descripción
                        ft.Row([
                            img_preview,
                            ft.Column([
                                ft.Text(nom, size=12, weight="bold", color="#0f172a", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(desc, size=10.5, color=Config.COLOR_TEXT_MUTED, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Row([
                                    ft.Text("Costo: " + (formatear_precio(cu) if cu > 0 else "N/A"), size=10, color="grey600"),
                                ], spacing=4),
                                ft.Text(formatear_precio(pv) if pv > 0 else "Sin Precio", size=15, weight="bold", color=Config.COLOR_PRIMARY),
                            ], spacing=3, expand=True)
                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),

                        ft.Divider(height=1, color="#f1f5f9"),
                        
                        # Botones de Acción de la Tarjeta
                        ft.Row([
                            ft.ElevatedButton(
                                "Editar",
                                icon=ft.icons.EDIT_NOTE_ROUNDED,
                                height=32,
                                bgcolor=Config.COLOR_PRIMARY,
                                color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=8)),
                                on_click=lambda _, item_ref=it: self._abrir_modal_editar_precio(item_ref)
                            ),
                            ft.ElevatedButton(
                                "Foto",
                                icon=ft.icons.ADD_PHOTO_ALTERNATE_ROUNDED,
                                height=32,
                                bgcolor="teal700",
                                color="white",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=8)),
                                on_click=lambda _, item_ref=it: self._abrir_modal_gestion_foto(item_ref)
                            ),
                            ft.Container(expand=True),
                            ft.OutlinedButton(
                                "Quitar",
                                icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                                icon_color="red700",
                                height=32,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=8)),
                                on_click=lambda _, item_ref=it, p_n=num_pag: self._confirmar_retirar_insumo_de_pagina(item_ref, p_n)
                            )
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    ], spacing=8)
                )
                cards_fila.controls.append(tarjeta_insumo)

            # 2. Renderizar Espacios Disponibles (Slots vacíos hasta completar exactamente 4)
            for s_idx in range(len(cards_cods) + 1, 5):
                slot_vacio = ft.Container(
                    width=420,
                    height=200,
                    bgcolor="#f8fafc",
                    border=ft.border.all(2, "#cbd5e1"),
                    border_radius=10,
                    padding=ft.padding.all(16),
                    alignment=ft.alignment.center,
                    tooltip=f"Asignar insumo al espacio {s_idx} de 4 de esta página",
                    on_click=lambda _, p_num=num_pag: self._abrir_modal_asignar_insumo_a_slot(p_num),
                    content=ft.Column([
                        ft.Icon(ft.icons.ADD_CIRCLE_OUTLINE_ROUNDED, size=36, color=Config.COLOR_PRIMARY),
                        ft.Text(f"+ Espacio Disponible (Slot {s_idx} de 4)", size=13, weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Text("Haz clic aquí para asignar un nuevo insumo a esta página", size=11, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            bgcolor="#eff6ff",
                            border_radius=6,
                            content=ft.Text("Límite máx: 4 insumos por página", size=9.5, weight="bold", color="#1e40af")
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=6)
                )
                cards_fila.controls.append(slot_vacio)

            self.lienzo_pagina_editor.content.controls.append(cards_fila)

        # -------------------------------------------------------------
        # CASO 2: TABLA RESUMEN
        # -------------------------------------------------------------
        elif tipo == "Tabla Resumen":
            tabla_res = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Código", size=11, weight="bold")),
                    ft.DataColumn(ft.Text("Nombre del Insumo", size=11, weight="bold")),
                    ft.DataColumn(ft.Text("Precio Venta", size=11, weight="bold"), numeric=True),
                    ft.DataColumn(ft.Text("Acciones", size=11, weight="bold")),
                ],
                rows=[],
                heading_row_height=38,
                data_row_min_height=48,
                border_radius=8
            )

            for cod_t in tablas_cods:
                it = items_dict.get(cod_t, {"codigo": cod_t, "nombre": f"Insumo {cod_t}", "precio_venta": 0.0})
                nom = it.get("nombre", f"Insumo {cod_t}")
                pv = float(it.get("precio_venta", 0.0))

                acciones_fila = ft.Row([
                    ft.IconButton(
                        icon=ft.icons.EDIT_NOTE_ROUNDED,
                        icon_color="blue700",
                        icon_size=18,
                        tooltip="Modificar precio",
                        on_click=lambda _, item_ref=it: self._abrir_modal_editar_precio(item_ref)
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                        icon_color="red700",
                        icon_size=18,
                        tooltip="Quitar de esta tabla",
                        on_click=lambda _, item_ref=it, p_n=num_pag: self._confirmar_retirar_insumo_de_pagina(item_ref, p_n)
                    )
                ], spacing=2)

                tabla_res.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Container(
                            content=ft.Text(cod_t, size=10, weight="bold", color="white"),
                            bgcolor="#00509d",
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=4
                        )),
                        ft.DataCell(ft.Text(nom, size=11, weight="w600")),
                        ft.DataCell(ft.Text(formatear_precio(pv), size=11, weight="bold", color=Config.COLOR_PRIMARY)),
                        ft.DataCell(acciones_fila)
                    ])
                )

            contenedor_tabla_res = ft.Container(
                bgcolor="#ffffff",
                border=ft.border.all(1, "#cbd5e1"),
                border_radius=10,
                padding=ft.padding.all(12),
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"Filas de Tabla Resumen ({len(tablas_cods)} insumos)", size=12, weight="bold", color="#0f172a"),
                        ft.ElevatedButton(
                            "+ Añadir Insumo a esta Tabla",
                            icon=ft.icons.ADD_ROUNDED,
                            bgcolor=Config.COLOR_PRIMARY,
                            color="white",
                            height=32,
                            on_click=lambda _, p_num=num_pag: self._abrir_modal_asignar_insumo_a_slot(p_num)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Divider(height=1, color="#f1f5f9"),
                    tabla_res
                ], spacing=8)
            )
            self.lienzo_pagina_editor.content.controls.append(contenedor_tabla_res)

        # -------------------------------------------------------------
        # CASO 3: PORTADA / CONTRAPORTADA / DISEÑO
        # -------------------------------------------------------------
        else:
            banner_diseno = ft.Container(
                width=800,
                bgcolor="#ffffff",
                border=ft.border.all(1, "#cbd5e1"),
                border_radius=12,
                padding=ft.padding.all(30),
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.icons.AUTO_STORIES_ROUNDED, size=50, color=Config.COLOR_PRIMARY),
                    ft.Text(f"Página de {tipo}", size=18, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Text("Esta es una página gráfica y estructural del catálogo (Portada / Contraportada / Separador de Sección).", size=12, color=Config.COLOR_TEXT_MUTED),
                    ft.Container(height=10),
                    ft.Text("Los insumos de venta se gestionan en las páginas de Rejilla de Productos y Tabla Resumen.", size=11, italic=True, color="grey600")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
            )
            self.lienzo_pagina_editor.content.controls.append(banner_diseno)

        if self.page:
            self.page.update()

    def _abrir_modal_asignar_insumo_a_slot(self, num_pagina: int):
        """Abre un modal paginado para seleccionar un insumo del inventario general y asignarlo al slot de la página."""
        paginas = self.mapeo_paginas_actual.get("paginas", [])
        if num_pagina < 1 or num_pagina > len(paginas):
            return
        
        p_info = paginas[num_pagina - 1]
        cards_cods = p_info.get("items_cards", [])
        tipo = p_info.get("tipo", "")

        # Verificación de límite estricto de 4 insumos en páginas de rejilla
        if tipo == "Rejilla de Productos" and len(cards_cods) >= 4:
            self._mostrar_snackbar("⚠️ Esta página ya alcanzó el límite máximo de 4 insumos con foto.", "amber800")
            return

        todos_inv = get_todos_insumos_inventario()
        mapa_otros_catalogos = get_mapa_catalogos_asignados()
        mapa_cod_a_pag = self.mapeo_paginas_actual.get("mapa_codigo_a_pagina", {})

        txt_buscar_slot = ft.TextField(
            hint_text="Buscar insumo por código, nombre o categoría...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            dense=True,
            border_radius=8,
            height=38,
            text_size=11.5,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
            autofocus=True
        )

        columna_resultados = ft.Column(spacing=4, expand=True)
        page_state = {"current": 1, "size": 6}
        lbl_paginacion = ft.Text("Pág 1 de 1", size=10.5, color=Config.COLOR_TEXT_MUTED)
        btn_prev = ft.IconButton(icon=ft.icons.CHEVRON_LEFT_ROUNDED, icon_size=18, disabled=True)
        btn_next = ft.IconButton(icon=ft.icons.CHEVRON_RIGHT_ROUNDED, icon_size=18, disabled=True)

        def _asignar_insumo(ins_data: dict, mover_de_pagina: int = None):
            c_cod = str(ins_data.get("codigo_insumo", "")).strip()
            c_nom = str(ins_data.get("nombre", "")).strip()
            c_desc = str(ins_data.get("descripcion", "") or c_nom).strip()
            c_pv = float(ins_data.get("precio_venta") or 0.0)

            # Buscar si el insumo ya existe en el catálogo para actualizar su página
            encontrado = False
            for it in self.items_totales:
                if str(it.get("codigo", "")).strip() == c_cod:
                    it["pagina"] = num_pagina
                    it["familia"] = p_info.get("familia", it.get("familia", "General"))
                    encontrado = True
                    break

            if not encontrado:
                nuevo_item = {
                    "codigo": c_cod,
                    "nombre": c_nom,
                    "descripcion": c_desc,
                    "familia": p_info.get("familia", "General"),
                    "precio_venta": c_pv,
                    "precio_manual": False,
                    "pagina": num_pagina
                }
                self.items_totales.append(nuevo_item)

            # Deduplicación estricta por código (nunca duplicados en el mismo catálogo)
            seen = set()
            dedup = []
            for it in self.items_totales:
                c = str(it.get("codigo", "")).strip()
                if c and c not in seen:
                    seen.add(c)
                    dedup.append(it)
            self.items_totales = dedup

            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            self._cerrar_modal(dialogo)
            self._cargar_catalogo_activo()
            self.pagina_editor_seleccionada = num_pagina
            self._render_pagina_editor_visual()

            if mover_de_pagina:
                self._mostrar_snackbar(f"✅ Insumo [{c_cod}] {c_nom} movido de Pág. {mover_de_pagina} a Pág. {num_pagina}.", "green")
            else:
                self._mostrar_snackbar(f"✅ Insumo [{c_cod}] {c_nom} asignado a la Página {num_pagina}.", "green")
            self._safe_update()

        def _obtener_candidatos() -> list[dict]:
            q = (txt_buscar_slot.value or "").strip()
            return [
                ins for ins in todos_inv
                if cumple_busqueda_inteligente(
                    q,
                    ins.get("codigo_insumo"),
                    ins.get("nombre"),
                    ins.get("categoria"),
                    ins.get("descripcion")
                )
            ]

        def _render_candidatos():
            columna_resultados.controls.clear()
            candidatos = _obtener_candidatos()
            tot = len(candidatos)
            tot_p = max(1, math.ceil(tot / page_state["size"]))
            if page_state["current"] > tot_p:
                page_state["current"] = tot_p

            cur_p = page_state["current"]
            ini = (cur_p - 1) * page_state["size"]
            fin = min(ini + page_state["size"], tot)
            items_p = candidatos[ini:fin]

            lbl_paginacion.value = f"Pág {cur_p} de {tot_p} ({tot} insumos)"
            btn_prev.disabled = (cur_p <= 1)
            btn_next.disabled = (cur_p >= tot_p)

            if not items_p:
                columna_resultados.controls.append(
                    ft.Container(
                        padding=ft.padding.all(24),
                        alignment=ft.alignment.center,
                        content=ft.Text("No se encontraron insumos para asignar.", size=11, color="grey600", italic=True)
                    )
                )
            else:
                for ins in items_p:
                    c_cod = str(ins.get("codigo_insumo", "")).strip()
                    c_nom = str(ins.get("nombre", "")).strip()
                    c_pv = float(ins.get("precio_venta") or 0.0)

                    esta_en_este_cat = (c_cod in mapa_cod_a_pag)
                    p_actual = mapa_cod_a_pag[c_cod].get("num_pagina") if esta_en_este_cat else None

                    if esta_en_este_cat:
                        if p_actual == num_pagina:
                            badge_estado = ft.Container(
                                content=ft.Text("✅ Ya en esta página", size=9, weight="bold", color="#1e40af"),
                                bgcolor="#dbeafe",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            )
                            btn_accion = ft.OutlinedButton(
                                "Asignado",
                                disabled=True,
                                height=28,
                                style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8))
                            )
                        else:
                            badge_estado = ft.Container(
                                content=ft.Text(f"⚠️ En Pág. {p_actual} (este catálogo)", size=9, weight="bold", color="#9a3412"),
                                bgcolor="#ffedd5",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            )
                            btn_accion = ft.ElevatedButton(
                                f"Mover a Pág. {num_pagina}",
                                bgcolor="#ea580c",
                                color="white",
                                height=28,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=8)),
                                on_click=lambda _, ins_ref=ins, prev_p=p_actual: _asignar_insumo(ins_ref, mover_de_pagina=prev_p)
                            )
                    else:
                        otros = [c for c in mapa_otros_catalogos.get(c_cod, []) if c.lower() != self.catalogo_actual_key.lower()]
                        if otros:
                            badge_estado = ft.Container(
                                content=ft.Text(f"En: {', '.join(otros)}", size=9, weight="bold", color="#334155"),
                                bgcolor="#e2e8f0",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            )
                        else:
                            badge_estado = ft.Container(
                                content=ft.Text("Libre", size=9, weight="bold", color="green900"),
                                bgcolor="#dcfce7",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            )
                        btn_accion = ft.ElevatedButton(
                            "Asignar",
                            icon=ft.icons.ADD_ROUNDED,
                            bgcolor=Config.COLOR_PRIMARY,
                            color="white",
                            height=28,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=8)),
                            on_click=lambda _, ins_ref=ins: _asignar_insumo(ins_ref)
                        )

                    fila_item = ft.Container(
                        bgcolor="#ffffff",
                        border=ft.border.all(1, "#cbd5e1"),
                        border_radius=6,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(c_cod, size=9.5, weight="bold", color="white"),
                                bgcolor="#00509d",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            ),
                            ft.Column([
                                ft.Text(c_nom, size=11, weight="bold", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Row([
                                    badge_estado,
                                    ft.Text(f"Precio: {formatear_precio(c_pv)}", size=9.5, color=Config.COLOR_TEXT_MUTED)
                                ], spacing=6)
                            ], spacing=2, expand=True),
                            btn_accion
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                    columna_resultados.controls.append(fila_item)

            if columna_resultados.page:
                columna_resultados.update()
            if lbl_paginacion.page:
                lbl_paginacion.update()
            if btn_prev.page:
                btn_prev.update()
            if btn_next.page:
                btn_next.update()

        def _on_prev_click(_):
            if page_state["current"] > 1:
                page_state["current"] -= 1
                _render_candidatos()

        def _on_next_click(_):
            cands = _obtener_candidatos()
            tot_p = max(1, math.ceil(len(cands) / page_state["size"]))
            if page_state["current"] < tot_p:
                page_state["current"] += 1
                _render_candidatos()

        btn_prev.on_click = _on_prev_click
        btn_next.on_click = _on_next_click

        def _on_search_slot_change(_):
            page_state["current"] = 1
            _render_candidatos()

        txt_buscar_slot.on_change = _on_search_slot_change
        _render_candidatos()

        dialogo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.ADD_TO_PHOTOS_ROUNDED, color=Config.COLOR_PRIMARY),
                ft.Text(f"Asignar Insumo a Página {num_pagina} ({p_info.get('familia', '')})", size=15, weight="bold")
            ], spacing=8),
            content=ft.Container(
                width=580,
                height=450,
                content=ft.Column([
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        bgcolor="#eff6ff",
                        border_radius=6,
                        content=ft.Text(
                            f"Selecciona un insumo disponible para ubicarlo en el espacio de la Página {num_pagina} "
                            f"(Capacidad: {len(cards_cods)} de 4 ocupados)",
                            size=10.5,
                            color="#1e40af"
                        )
                    ),
                    txt_buscar_slot,
                    columna_resultados,
                    ft.Row([
                        lbl_paginacion,
                        ft.Container(expand=True),
                        btn_prev,
                        btn_next
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ], spacing=6, expand=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cerrar_modal(dialogo))
            ]
        )
        self._abrir_modal(dialogo)

    def _confirmar_retirar_insumo_de_pagina(self, item: dict, num_pagina: int):
        """Pide confirmación y retira un insumo de la página y del catálogo."""
        nom = item.get("nombre", "este insumo")
        cod = item.get("codigo", "")

        def _ejecutar_retirar(e):
            self.items_totales = [it for it in self.items_totales if str(it.get("codigo", "")).strip() != str(cod).strip()]
            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            self._cerrar_modal(dialogo)
            self._cargar_catalogo_activo()
            self._mostrar_snackbar(f"Insumo [{cod}] {nom} retirado de la Página {num_pagina}.", "amber800")
            self._safe_update()

        dialogo = ft.AlertDialog(
            title=ft.Text("Retirar Insumo de Página", size=14, weight="bold"),
            content=ft.Text(f"¿Deseas retirar '{nom}' [CÓD: {cod}] de la Página {num_pagina}? (El insumo se removerá del catálogo pero seguirá disponible en inventario).", size=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cerrar_modal(dialogo)),
                ft.ElevatedButton("Retirar", bgcolor="red700", color="white", on_click=_ejecutar_retirar)
            ]
        )
        self._abrir_modal(dialogo)

    def _abrir_modal_editar_pagina(self, e):
        """Permite editar el título de familia y subtítulo de categoría de la página actual."""
        paginas = self.mapeo_paginas_actual.get("paginas", [])
        total_p = len(paginas)
        if self.pagina_editor_seleccionada < 1 or self.pagina_editor_seleccionada > total_p:
            return

        p_info = paginas[self.pagina_editor_seleccionada - 1]
        num_pag = p_info["num_pagina"]
        tipo = p_info["tipo"]

        if tipo in ("Portada", "Contraportada"):
            self._mostrar_snackbar("⚠️ La portada y contraportada no tienen encabezado de familia editable.", "amber800")
            return

        cfg = CATALOGOS_CONFIG.get(self.catalogo_actual_key, {})
        fam_actual = p_info.get("familia", "")
        cat_actual = p_info.get("categoria", cfg.get("nombre", "General"))
        todos_cods = set(p_info.get("items_cards", []) + p_info.get("items_tablas", []))

        txt_familia = ft.TextField(
            label="Título de Familia / Línea (Encabezado)",
            hint_text="Ej: LÍNEA QUÍMICOS YILOP, AMBIENTADORES, etc.",
            value=fam_actual,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            autofocus=True
        )

        txt_categoria = ft.TextField(
            label="Subtítulo / Categoría (Opcional)",
            hint_text="Ej: LÍNEA DE ASEO INSTITUCIONAL",
            value=cat_actual,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12
        )

        def _guardar_cambios_pagina(ev):
            nueva_fam = (txt_familia.value or "").strip()
            nueva_cat = (txt_categoria.value or "").strip()

            if not nueva_fam:
                self._mostrar_snackbar("El título de familia no puede estar vacío", "red")
                return

            # Actualizar familia y categoría para todos los insumos contenidos en esta página
            for it in self.items_totales:
                cod = str(it.get("codigo", "")).strip()
                if cod in todos_cods:
                    it["familia"] = nueva_fam
                    if nueva_cat:
                        it["categoria"] = nueva_cat

            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            self._cerrar_modal(dialogo)
            
            # Recargar y actualizar UI
            self._cargar_catalogo_activo()
            self.pagina_editor_seleccionada = num_pag
            self._render_pagina_editor_visual()
            self._mostrar_snackbar(f"✅ Título de familia actualizado a '{nueva_fam}' para la Página {num_pag}.", "green")
            self._safe_update()

        dialogo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.EDIT_NOTE_ROUNDED, color=Config.COLOR_PRIMARY),
                ft.Text(f"Editar Encabezado de Página {num_pag}", size=15, weight="bold")
            ], spacing=8),
            content=ft.Container(
                width=480,
                content=ft.Column([
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        bgcolor="#eff6ff",
                        border_radius=6,
                        content=ft.Row([
                            ft.Icon(ft.icons.INFO_OUTLINE_ROUNDED, size=16, color="#1e40af"),
                            ft.Text(f"Página {num_pag} ({tipo}) • {len(todos_cods)} insumos asociados", size=10.5, color="#1e40af")
                        ], spacing=6)
                    ),
                    txt_familia,
                    txt_categoria
                ], spacing=10, tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cerrar_modal(dialogo)),
                ft.ElevatedButton("Guardar Cambios", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=_guardar_cambios_pagina)
            ]
        )
        self._abrir_modal(dialogo)

    def _abrir_modal_nueva_pagina(self, e):
        """Permite crear una nueva página física en el catálogo y seleccionar hasta 4 insumos con paginador y checkboxes."""
        cfg = CATALOGOS_CONFIG.get(self.catalogo_actual_key, {})
        todos_inv = get_todos_insumos_inventario()
        mapa_otros_catalogos = get_mapa_catalogos_asignados()
        mapa_cod_a_pag = self.mapeo_paginas_actual.get("mapa_codigo_a_pagina", {})

        txt_familia = ft.TextField(
            label="Título / Familia de la Página",
            hint_text="Ej: Bolsas Metalizadas y Selladas",
            value="Nuevos Productos",
            dense=True,
            border_radius=8,
            height=38,
            text_size=11.5,
            expand=True
        )
        txt_categoria = ft.TextField(
            label="Subtítulo / Categoría",
            hint_text="Ej: Línea Especial",
            value=cfg.get("nombre", "General"),
            dense=True,
            border_radius=8,
            height=38,
            text_size=11.5,
            width=180
        )

        txt_buscar = ft.TextField(
            hint_text="Buscar insumos por código, nombre o categoría...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            dense=True,
            border_radius=8,
            height=38,
            text_size=11.5,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6)
        )

        seleccionados: dict[str, dict] = {}
        page_state = {"current": 1, "size": 6}

        columna_items = ft.Column(spacing=4, expand=True)
        lbl_contador = ft.Text("Seleccionados: 0 / 4", size=11, weight="bold", color="#1e40af")
        lbl_paginacion = ft.Text("Pág 1 de 1", size=10.5, color=Config.COLOR_TEXT_MUTED)
        btn_prev = ft.IconButton(icon=ft.icons.CHEVRON_LEFT_ROUNDED, icon_size=18, disabled=True)
        btn_next = ft.IconButton(icon=ft.icons.CHEVRON_RIGHT_ROUNDED, icon_size=18, disabled=True)
        btn_crear = ft.ElevatedButton(
            "Crear Página (0 Seleccionados)",
            icon=ft.icons.ADD_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=36,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
        )

        def _obtener_candidatos() -> list[dict]:
            q = (txt_buscar.value or "").strip()
            return [
                ins for ins in todos_inv
                if cumple_busqueda_inteligente(
                    q,
                    ins.get("codigo_insumo"),
                    ins.get("nombre"),
                    ins.get("categoria"),
                    ins.get("descripcion")
                )
            ]

        def _on_toggle_checkbox(ins_item: dict, is_checked: bool, cb_control: ft.Checkbox):
            cod_ins = str(ins_item.get("codigo_insumo", "")).strip()
            if is_checked:
                if len(seleccionados) >= 4:
                    cb_control.value = False
                    if cb_control.page:
                        cb_control.update()
                    self._mostrar_snackbar("⚠️ Límite alcanzado: máximo 4 insumos por página de rejilla.", "amber800")
                    return
                seleccionados[cod_ins] = ins_item
            else:
                seleccionados.pop(cod_ins, None)

            cnt = len(seleccionados)
            lbl_contador.value = f"Seleccionados: {cnt} / 4"
            btn_crear.text = f"Crear Página ({cnt} Seleccionados)"
            if lbl_contador.page:
                lbl_contador.update()
            if btn_crear.page:
                btn_crear.update()

        def _render_lista():
            columna_items.controls.clear()
            cands = _obtener_candidatos()
            tot = len(cands)
            tot_p = max(1, math.ceil(tot / page_state["size"]))
            if page_state["current"] > tot_p:
                page_state["current"] = tot_p

            cur_p = page_state["current"]
            ini = (cur_p - 1) * page_state["size"]
            fin = min(ini + page_state["size"], tot)
            items_p = cands[ini:fin]

            lbl_paginacion.value = f"Pág {cur_p} de {tot_p} ({tot} insumos)"
            btn_prev.disabled = (cur_p <= 1)
            btn_next.disabled = (cur_p >= tot_p)

            if not items_p:
                columna_items.controls.append(
                    ft.Container(
                        padding=ft.padding.all(24),
                        alignment=ft.alignment.center,
                        content=ft.Text("No se encontraron insumos para asignar.", size=11, color="grey600", italic=True)
                    )
                )
            else:
                for ins in items_p:
                    c_cod = str(ins.get("codigo_insumo", "")).strip()
                    c_nom = str(ins.get("nombre", "")).strip()
                    c_pv = float(ins.get("precio_venta") or 0.0)

                    esta_en_este_cat = (c_cod in mapa_cod_a_pag)
                    p_actual = mapa_cod_a_pag[c_cod].get("num_pagina") if esta_en_este_cat else None

                    if esta_en_este_cat:
                        badge_estado = ft.Container(
                            content=ft.Text(f"⚠️ En Pág. {p_actual} (este catálogo)", size=8.5, weight="bold", color="#9a3412"),
                            bgcolor="#ffedd5",
                            padding=ft.padding.symmetric(horizontal=5, vertical=2),
                            border_radius=4
                        )
                    else:
                        otros = [c for c in mapa_otros_catalogos.get(c_cod, []) if c.lower() != self.catalogo_actual_key.lower()]
                        if otros:
                            badge_estado = ft.Container(
                                content=ft.Text(f"En: {', '.join(otros)}", size=8.5, weight="bold", color="#334155"),
                                bgcolor="#e2e8f0",
                                padding=ft.padding.symmetric(horizontal=5, vertical=2),
                                border_radius=4
                            )
                        else:
                            badge_estado = ft.Container(
                                content=ft.Text("Libre", size=8.5, weight="bold", color="green900"),
                                bgcolor="#dcfce7",
                                padding=ft.padding.symmetric(horizontal=5, vertical=2),
                                border_radius=4
                            )

                    cb = ft.Checkbox(
                        value=(c_cod in seleccionados),
                        scale=0.85
                    )
                    cb.on_change = lambda ev, it_ref=ins, cb_ref=cb: _on_toggle_checkbox(it_ref, ev.control.value, cb_ref)

                    fila = ft.Container(
                        bgcolor="#ffffff",
                        border=ft.border.all(1, "#cbd5e1"),
                        border_radius=6,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        content=ft.Row([
                            cb,
                            ft.Container(
                                content=ft.Text(c_cod, size=9.5, weight="bold", color="white"),
                                bgcolor="#00509d",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4
                            ),
                            ft.Column([
                                ft.Text(c_nom, size=11, weight="bold", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Row([
                                    badge_estado,
                                    ft.Text(f"Precio: {formatear_precio(c_pv)}", size=9.5, color=Config.COLOR_TEXT_MUTED)
                                ], spacing=6)
                            ], spacing=2, expand=True)
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                    columna_items.controls.append(fila)

            if columna_items.page:
                columna_items.update()
            if lbl_paginacion.page:
                lbl_paginacion.update()
            if btn_prev.page:
                btn_prev.update()
            if btn_next.page:
                btn_next.update()

        def _on_prev_click(_):
            if page_state["current"] > 1:
                page_state["current"] -= 1
                _render_lista()

        def _on_next_click(_):
            cands = _obtener_candidatos()
            tot_p = max(1, math.ceil(len(cands) / page_state["size"]))
            if page_state["current"] < tot_p:
                page_state["current"] += 1
                _render_lista()

        btn_prev.on_click = _on_prev_click
        btn_next.on_click = _on_next_click

        def _on_search_change(_):
            page_state["current"] = 1
            _render_lista()

        txt_buscar.on_change = _on_search_change

        def _ejecutar_creacion_pagina(ev):
            fam_val = (txt_familia.value or "").strip() or "Nuevos Productos"
            cat_val = (txt_categoria.value or "").strip() or cfg.get("nombre", "General")

            if not seleccionados:
                self._mostrar_snackbar("⚠️ Debes seleccionar al menos 1 insumo (hasta 4) para crear la página.", "amber800")
                return

            pags_grid = [p for p in self.mapeo_paginas_actual.get("paginas", []) if p.get("tipo") == "Rejilla de Productos"]
            nueva_pag_num = (max([p["num_pagina"] for p in pags_grid], default=1) + 1)

            for c_cod, ins_data in seleccionados.items():
                c_nom = str(ins_data.get("nombre", "")).strip()
                c_desc = str(ins_data.get("descripcion", "") or c_nom).strip()
                c_pv = float(ins_data.get("precio_venta") or 0.0)

                # Si el ítem ya estaba en el catálogo, actualizar su asignación de página (se quita de la anterior)
                encontrado = False
                for it in self.items_totales:
                    if str(it.get("codigo", "")).strip() == c_cod:
                        it["pagina"] = nueva_pag_num
                        it["familia"] = fam_val
                        encontrado = True
                        break

                if not encontrado:
                    nuevo_item = {
                        "codigo": c_cod,
                        "nombre": c_nom,
                        "descripcion": c_desc,
                        "familia": fam_val,
                        "precio_venta": c_pv,
                        "precio_manual": False,
                        "pagina": nueva_pag_num
                    }
                    self.items_totales.append(nuevo_item)

            # Deduplicación estricta de seguridad
            seen = set()
            dedup = []
            for it in self.items_totales:
                c = str(it.get("codigo", "")).strip()
                if c and c not in seen:
                    seen.add(c)
                    dedup.append(it)
            self.items_totales = dedup

            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            self._cerrar_modal(dialogo)
            
            # Recargar y ubicar el editor en la nueva página
            self._cargar_catalogo_activo()
            pags_seccion = self._obtener_paginas_seccion_activa()
            if pags_seccion:
                self.pagina_editor_seleccionada = pags_seccion[-1]["num_pagina"]
                self.drop_pagina_editor.value = str(self.pagina_editor_seleccionada)
                self._render_pagina_editor_visual()

            self._mostrar_snackbar(f"✅ Nueva página {nueva_pag_num} creada con {len(seleccionados)} insumos en '{fam_val}'.", "green")
            self._safe_update()

        btn_crear.on_click = _ejecutar_creacion_pagina

        _render_lista()

        dialogo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.NOTE_ADD_ROUNDED, color=Config.COLOR_PRIMARY),
                ft.Text("Añadir Nueva Página al Catálogo", size=15, weight="bold")
            ], spacing=8),
            content=ft.Container(
                width=580,
                height=480,
                content=ft.Column([
                    ft.Row([txt_categoria, txt_familia], spacing=8),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        bgcolor="#eff6ff",
                        border_radius=6,
                        content=ft.Row([
                            ft.Icon(ft.icons.INFO_OUTLINE_ROUNDED, size=15, color="#1e40af"),
                            ft.Text("Selecciona hasta 4 insumos con su checkbox para la nueva página:", size=10.5, color="#1e40af"),
                            ft.Container(expand=True),
                            lbl_contador
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    txt_buscar,
                    columna_items,
                    ft.Row([
                        lbl_paginacion,
                        ft.Container(expand=True),
                        btn_prev,
                        btn_next
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ], spacing=6, expand=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cerrar_modal(dialogo)),
                btn_crear
            ]
        )
        self._abrir_modal(dialogo)

    def _confirmar_eliminar_pagina_actual(self, e):
        """Pide confirmación para eliminar la página actual y remover todos sus insumos del catálogo."""
        paginas = self.mapeo_paginas_actual.get("paginas", [])
        total_p = len(paginas)
        if self.pagina_editor_seleccionada < 1 or self.pagina_editor_seleccionada > total_p:
            return

        if self.pagina_editor_seleccionada == 1:
            self._mostrar_snackbar("⚠️ La portada no se puede eliminar.", "amber800")
            return

        p_info = paginas[self.pagina_editor_seleccionada - 1]
        num_pag = p_info["num_pagina"]
        fam = p_info.get("familia", f"Página {num_pag}")
        todos_cods = set(p_info.get("items_cards", []) + p_info.get("items_tablas", []))

        def _ejecutar_eliminar_pagina(ev):
            # Remover todos los insumos de esta página
            self.items_totales = [it for it in self.items_totales if str(it.get("codigo", "")).strip() not in todos_cods]
            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            self._cerrar_modal(dialogo)
            
            # Recalcular páginas y ajustar selector
            self.mapeo_paginas_actual = obtener_mapeo_paginas_catalogo(self.catalogo_actual_key, forzar_recarga=True, items_data=self.items_totales)
            tot_nuevas = self.mapeo_paginas_actual.get("total_paginas", 1)
            self.pagina_editor_seleccionada = max(1, min(self.pagina_editor_seleccionada, tot_nuevas))
            
            self._cargar_catalogo_activo()
            self._mostrar_snackbar(f"Página {num_pag} eliminada y sus {len(todos_cods)} insumos retirados del catálogo.", "amber800")
            self._safe_update()

        dialogo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                ft.Text(f"Eliminar Página {num_pag}", size=14, weight="bold", color="red700")
            ], spacing=8),
            content=ft.Text(
                f"¿Estás seguro de eliminar la Página {num_pag} ('{fam}')?\n\n"
                f"Se retirarán los {len(todos_cods)} insumos contenidos en ella de este catálogo.",
                size=12
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cerrar_modal(dialogo)),
                ft.ElevatedButton("Eliminar Página", bgcolor="red700", color="white", on_click=_ejecutar_eliminar_pagina)
            ]
        )
        self._abrir_modal(dialogo)

    # -------------------------------------------------------------
    # MODAL: EDITAR PRECIO DE VENTA, MARGEN Y DATOS DEL INSUMO
    # -------------------------------------------------------------
    def _abrir_modal_editar_precio(self, item: dict):
        self.insumo_para_precio = item
        cod = str(item.get("codigo", "")).strip()
        nom_inicial = str(item.get("nombre", "")).strip()
        desc_inicial = str(item.get("descripcion", "") or "").strip()
        costo_val = self.costos_db.get(cod, 0.0)
        precio_actual = float(item.get("precio_venta", 0.0))
        es_manual_inicial = bool(item.get("precio_manual", False))

        # Helper seguro de parseo numérico sin errores de comas o puntos
        def _parse_input_decimal(val_raw) -> float:
            if val_raw is None:
                return 0.0
            if isinstance(val_raw, (int, float)):
                return max(0.0, float(val_raw))
            t = str(val_raw).strip().replace("$", "").replace("%", "").replace(" ", "")
            if not t:
                return 0.0
            if "." in t and "," in t:
                if t.rfind(",") > t.rfind("."):
                    t = t.replace(".", "").replace(",", ".")
                else:
                    t = t.replace(",", "")
            elif "," in t:
                partes = t.split(",")
                if len(partes) == 2 and len(partes[1]) <= 2:
                    t = t.replace(",", ".")
                else:
                    t = t.replace(",", "")
            elif "." in t:
                partes = t.split(".")
                if len(partes) > 2:
                    t = t.replace(".", "")
                elif len(partes) == 2:
                    if len(partes[1]) <= 2:
                        pass # Decimal válido ej 8508.50
                    elif len(partes[0]) <= 3 and len(partes[1]) == 3:
                        t = t.replace(".", "") # Separador de miles ej 8.508
            try:
                return max(0.0, float(t))
            except Exception:
                return 0.0

        def _formatear_input_num(v: float) -> str:
            if v <= 0:
                return "0"
            if v == int(v):
                return str(int(v))
            return f"{v:.2f}".rstrip('0').rstrip('.')

        # Calcular porcentaje inicial si hay costo
        if costo_val > 0:
            pct_inicial = ((precio_actual - costo_val) / costo_val) * 100
        else:
            pct_inicial = 0.0

        # Campo: Nombre del Insumo (editable)
        txt_nombre = ft.TextField(
            label="Nombre del Insumo",
            value=nom_inicial,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        # Campo: Descripción para el Catálogo
        txt_descripcion = ft.TextField(
            label="Descripción para Catálogo (opcional)",
            value=desc_inicial,
            dense=True,
            border_radius=8,
            multiline=True,
            min_lines=2,
            max_lines=3,
            text_size=11.5,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            hint_text="Detalles, usos o presentación que se mostrarán en el catálogo...",
        )

        # Campo: Costo con IVA (editable)
        txt_costo_con_iva = ft.TextField(
            label="Costo con IVA ($)",
            value=_formatear_input_num(costo_val),
            prefix_text="$ ",
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            expand=True,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        # Campo: Costo sin IVA (calculado automáticamente con base 19%)
        txt_costo_sin_iva = ft.TextField(
            label="Costo sin IVA (19%)",
            value=formatear_precio(costo_val / 1.19) if costo_val > 0 else "$0",
            read_only=True,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            expand=True,
            bgcolor="#f1f5f9",
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        # Dropdown Margen rápido
        drop_margenes = ft.Dropdown(
            label="Margen Rápido",
            options=[
                ft.dropdown.Option("custom", "Personalizado"),
                ft.dropdown.Option("10", "10%"),
                ft.dropdown.Option("15", "15%"),
                ft.dropdown.Option("20", "20%"),
                ft.dropdown.Option("25", "25%"),
                ft.dropdown.Option("30", "30%"),
                ft.dropdown.Option("35", "35%"),
                ft.dropdown.Option("40", "40%"),
                ft.dropdown.Option("50", "50%"),
                ft.dropdown.Option("60", "60%"),
                ft.dropdown.Option("70", "70%"),
                ft.dropdown.Option("80", "80%"),
                ft.dropdown.Option("100", "100%"),
            ],
            value=str(int(round(pct_inicial))) if str(int(round(pct_inicial))) in ["10","15","20","25","30","35","40","50","60","70","80","100"] else "custom",
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            expand=True,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        txt_porcentaje = ft.TextField(
            label="% Margen",
            value=f"{pct_inicial:.1f}" if costo_val > 0 else "",
            suffix_text="%",
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            width=120,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        txt_nuevo_precio = ft.TextField(
            label="Precio de Venta ($)",
            value=_formatear_input_num(precio_actual),
            prefix_text="$ ",
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            expand=True,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        chk_marcar_manual = ft.Checkbox(
            label="Fijar como precio manual en catálogo",
            value=es_manual_inicial,
            label_style=ft.TextStyle(size=11.5)
        )

        chk_sincronizar_db = ft.Checkbox(
            label="Aplicar cambios al inventario general (Supabase)",
            value=False,
            label_style=ft.TextStyle(size=11.5, weight="bold", color=Config.COLOR_PRIMARY)
        )

        # Flag para sincronización en tiempo real sin bucles
        is_updating = [False]

        def _get_costo_actual() -> float:
            return _parse_input_decimal(txt_costo_con_iva.value)

        def _get_precio_actual() -> float:
            return _parse_input_decimal(txt_nuevo_precio.value)

        def _on_costo_change(e):
            if is_updating[0]:
                return
            is_updating[0] = True
            try:
                c = _get_costo_actual()
                txt_costo_sin_iva.value = formatear_precio(c / 1.19) if c > 0 else "$0"
                if txt_costo_sin_iva.page:
                    txt_costo_sin_iva.update()
                
                # Si hay porcentaje ingresado, recalcular precio de venta
                pct = _parse_input_decimal(txt_porcentaje.value)
                if pct > 0 and c > 0:
                    nuevo_pv = round(c * (1 + pct / 100))
                    txt_nuevo_precio.value = _formatear_input_num(nuevo_pv)
                    if txt_nuevo_precio.page:
                        txt_nuevo_precio.update()
            except Exception:
                pass
            finally:
                is_updating[0] = False

        def _on_drop_margen_change(e):
            if is_updating[0]:
                return
            sel = drop_margenes.value
            c = _get_costo_actual()
            if sel != "custom" and c > 0:
                is_updating[0] = True
                try:
                    pct = float(sel)
                    txt_porcentaje.value = f"{pct:.1f}"
                    nuevo_pv = round(c * (1 + pct / 100))
                    txt_nuevo_precio.value = _formatear_input_num(nuevo_pv)
                    if txt_porcentaje.page:
                        txt_porcentaje.update()
                    if txt_nuevo_precio.page:
                        txt_nuevo_precio.update()
                finally:
                    is_updating[0] = False

        def _on_porcentaje_change(e):
            if is_updating[0]:
                return
            c = _get_costo_actual()
            is_updating[0] = True
            try:
                pct = _parse_input_decimal(txt_porcentaje.value)
                if pct > 0 and c > 0:
                    nuevo_pv = round(c * (1 + pct / 100))
                    txt_nuevo_precio.value = _formatear_input_num(nuevo_pv)
                    drop_margenes.value = str(int(round(pct))) if str(int(round(pct))) in [opt.key for opt in drop_margenes.options] else "custom"
                    if drop_margenes.page:
                        drop_margenes.update()
                    if txt_nuevo_precio.page:
                        txt_nuevo_precio.update()
            except Exception:
                pass
            finally:
                is_updating[0] = False

        def _on_precio_change(e):
            if is_updating[0]:
                return
            c = _get_costo_actual()
            is_updating[0] = True
            try:
                pv = _get_precio_actual()
                if pv > 0 and c > 0:
                    calc_pct = ((pv - c) / c) * 100
                    txt_porcentaje.value = f"{calc_pct:.1f}"
                    drop_margenes.value = str(int(round(calc_pct))) if str(int(round(calc_pct))) in [opt.key for opt in drop_margenes.options] else "custom"
                    if drop_margenes.page:
                        drop_margenes.update()
                    if txt_porcentaje.page:
                        txt_porcentaje.update()
            except Exception:
                pass
            finally:
                is_updating[0] = False

        txt_costo_con_iva.on_change = _on_costo_change
        drop_margenes.on_change = _on_drop_margen_change
        txt_porcentaje.on_change = _on_porcentaje_change
        txt_nuevo_precio.on_change = _on_precio_change

        def _guardar_precio(e):
            try:
                nuevo_nom = (txt_nombre.value or "").strip()
                if not nuevo_nom:
                    raise ValueError("El nombre del insumo no puede estar vacío")

                nueva_desc = (txt_descripcion.value or "").strip()
                c_val = _get_costo_actual()
                val_pv = _get_precio_actual()

                if val_pv < 0:
                    raise ValueError("El precio no puede ser negativo")
                
                # 1. Actualizar en el catálogo local
                item["nombre"] = nuevo_nom
                item["descripcion"] = nueva_desc
                item["precio_venta"] = val_pv
                item["precio_manual"] = chk_marcar_manual.value
                
                # Actualizar costo en memoria local si cambió
                if c_val > 0:
                    self.costos_db[cod] = c_val
                
                guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
                
                # 2. Si el usuario marcó actualizar en inventario general (Supabase)
                if chk_sincronizar_db.value:
                    datos_db = {
                        "nombre": nuevo_nom,
                        "costo_unitario": c_val,
                        "precio_venta": val_pv
                    }
                    if nueva_desc:
                        datos_db["descripcion"] = nueva_desc
                    
                    def _tarea_sync_db():
                        ok = actualizar_insumo_inventario_db(cod, datos_db)
                        if ok:
                            logger.info(f"Sincronizado {cod} con inventario general")
                    threading.Thread(target=_tarea_sync_db, daemon=True).start()

                self.mapeo_paginas_actual = obtener_mapeo_paginas_catalogo(self.catalogo_actual_key, forzar_recarga=True, items_data=self.items_totales)
                self._render_pagina_actual()
                if self.modo_vista == "EDITOR_PAGINAS" or (hasattr(self, "contenedor_vista_editor") and self.contenedor_vista_editor.visible):
                    self._render_pagina_editor_visual()
                self._cerrar_modal(dialogo)
                self._mostrar_snackbar(f"Guardado: [{cod}] {nuevo_nom} - Venta: {formatear_precio(val_pv)}", "green")
                self._safe_update()
            except Exception as ex:
                self._mostrar_snackbar(f"Error: {ex}", "red")

        dialogo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.EDIT_NOTE_ROUNDED, color=Config.COLOR_PRIMARY),
                ft.Text("Editar Insumo & Precio de Catálogo", size=15, weight="bold")
            ], spacing=8),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(f"CÓD: {cod}", size=11, weight="bold", color="white"),
                            bgcolor="#00509d",
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=6
                        ),
                        ft.Text("Código Maestro (No editable)", size=10, italic=True, color=Config.COLOR_TEXT_MUTED)
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    txt_nombre,
                    txt_descripcion,
                    ft.Divider(height=1, color="#e2e8f0"),
                    ft.Text("Costos e IVA:", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED),
                    ft.Row([
                        txt_costo_con_iva,
                        txt_costo_sin_iva
                    ], spacing=8),
                    ft.Text("Margen de Ganancia y Precio de Venta:", size=11, weight="bold", color=Config.COLOR_TEXT_MUTED),
                    ft.Row([
                        drop_margenes,
                        txt_porcentaje
                    ], spacing=8),
                    txt_nuevo_precio,
                    ft.Divider(height=1, color="#e2e8f0"),
                    chk_marcar_manual,
                    chk_sincronizar_db
                ], spacing=8, tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cerrar_modal(dialogo)),
                ft.ElevatedButton("Guardar Cambios", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=_guardar_precio)
            ]
        )
        self._abrir_modal(dialogo)

    # -------------------------------------------------------------
    # GESTIÓN DE FOTOS EN SUPABASE STORAGE
    # -------------------------------------------------------------
    def _abrir_modal_gestion_foto(self, item: dict):
        nom = str(item.get("nombre", "")).strip()
        cod = str(item.get("codigo", "")).strip()
        self.insumo_para_foto = item
        
        foto_url = buscar_foto_insumo(self.catalogo_actual_key, nom)
        
        img_preview = ft.Image(
            src=foto_url if foto_url else "",
            width=230,
            height=230,
            fit=ft.ImageFit.CONTAIN,
            visible=bool(foto_url)
        )
        
        placeholder_no_foto = ft.Container(
            width=230,
            height=230,
            bgcolor="#f1f5f9",
            border_radius=8,
            border=ft.border.all(1, "#cbd5e1"),
            alignment=ft.alignment.center,
            visible=not bool(foto_url),
            content=ft.Column([
                ft.Icon(ft.icons.IMAGE_NOT_SUPPORTED_ROUNDED, size=44, color="grey400"),
                ft.Text("Sin foto en Supabase Storage", size=11, color="grey600", italic=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6, alignment=ft.MainAxisAlignment.CENTER)
        )
        
        lbl_estado_subida = ft.Text("", size=11, weight="bold", color=Config.COLOR_PRIMARY)
        spinner_subida = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False, color=Config.COLOR_ACCENT)
        
        btn_seleccionar = ft.ElevatedButton(
            "Subir Nueva Foto",
            icon=ft.icons.UPLOAD_FILE_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=36,
            on_click=lambda _: self.file_picker_foto.pick_files(
                dialog_title=f"Seleccionar foto para {nom}",
                file_type=ft.FilePickerFileType.IMAGE,
                allowed_extensions=["jpg", "jpeg", "png", "webp"],
                allow_multiple=False
            )
        )
        
        def _ejecutar_eliminar(e):
            btn_eliminar.disabled = True
            if dialogo.page:
                dialogo.update()
            
            def _tarea_del():
                ok = eliminar_foto_insumo(self.catalogo_actual_key, nom)
                if ok:
                    self._mostrar_snackbar(f"Foto de {nom} eliminada de Supabase Storage", "amber800")
                    img_preview.visible = False
                    placeholder_no_foto.visible = True
                    btn_eliminar.visible = False
                    if dialogo.page:
                        dialogo.update()
                    self.mapeo_paginas_actual = obtener_mapeo_paginas_catalogo(self.catalogo_actual_key, forzar_recarga=True, items_data=self.items_totales)
                    self._render_pagina_actual()
                    if self.modo_vista == "EDITOR_PAGINAS" or (hasattr(self, "contenedor_vista_editor") and self.contenedor_vista_editor.visible):
                        self._render_pagina_editor_visual()
                    self._safe_update()
                else:
                    btn_eliminar.disabled = False
                    self._mostrar_snackbar(f"No se pudo eliminar la foto de {nom}", "red")
                    if dialogo.page:
                        dialogo.update()

            threading.Thread(target=_tarea_del, daemon=True).start()

        btn_eliminar = ft.OutlinedButton(
            "Eliminar Foto",
            icon=ft.icons.DELETE_FOREVER_ROUNDED,
            icon_color="red700",
            visible=bool(foto_url),
            height=36,
            on_click=_ejecutar_eliminar
        )
        
        self._modal_foto_contexto = {
            "item": item,
            "img_preview": img_preview,
            "placeholder": placeholder_no_foto,
            "btn_eliminar": btn_eliminar,
            "lbl_estado": lbl_estado_subida,
            "spinner": spinner_subida,
            "dialogo": None
        }
        
        dialogo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.CLOUD_DONE_ROUNDED, color="teal700"),
                ft.Text("Foto en Supabase Storage", size=15, weight="bold")
            ], spacing=8),
            content=ft.Container(
                width=440,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(f"[{cod}]", size=11, weight="bold", color="white"),
                            bgcolor="#00509d",
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            border_radius=4
                        ),
                        ft.Text(nom, size=12, weight="bold", expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                    ], spacing=6),
                    ft.Divider(height=1, color="#e2e8f0"),
                    ft.Container(
                        content=ft.Stack([
                            placeholder_no_foto,
                            img_preview
                        ]),
                        alignment=ft.alignment.center,
                        padding=ft.padding.symmetric(vertical=6)
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=6),
                        bgcolor="#f8fafc",
                        border_radius=6,
                        border=ft.border.all(1, "#e2e8f0"),
                        content=ft.Text(
                            "☁️ Optimización activa: Compresión progresiva JPEG de alta definición a 800px (~80KB). Formatos permitidos: JPG, PNG, WEBP. Límite máx: 5MB.",
                            size=9.5,
                            color=Config.COLOR_TEXT_MUTED
                        )
                    ),
                    ft.Row([spinner_subida, lbl_estado_subida], spacing=6, alignment=ft.MainAxisAlignment.CENTER)
                ], spacing=8, tight=True)
            ),
            actions=[
                btn_eliminar,
                btn_seleccionar,
                ft.TextButton("Cerrar", on_click=lambda _: self._cerrar_modal(dialogo))
            ]
        )
        self._modal_foto_contexto["dialogo"] = dialogo
        self._abrir_modal(dialogo)

    def _on_foto_picked(self, e: ft.FilePickerResultEvent):
        if not e.files or not self.insumo_para_foto:
            return

        archivo_sel = e.files[0].path
        nom = self.insumo_para_foto.get("nombre", "")
        
        ctx = getattr(self, "_modal_foto_contexto", None)
        if ctx and ctx.get("spinner") and ctx.get("lbl_estado"):
            ctx["spinner"].visible = True
            ctx["lbl_estado"].value = "Optimizando y subiendo a Supabase Storage..."
            if ctx.get("dialogo") and ctx["dialogo"].page:
                ctx["dialogo"].update()

        def _tarea_foto():
            import time
            ok, res_data = guardar_foto_insumo(self.catalogo_actual_key, nom, archivo_sel)
            if ok:
                nueva_url = res_data
                self._mostrar_snackbar(f"✅ Foto subida exitosamente a Supabase Storage: {nom}", "green")
                if ctx and ctx.get("img_preview"):
                    ctx["img_preview"].src = f"{nueva_url}?t={int(time.time())}"
                    ctx["img_preview"].visible = True
                    ctx["placeholder"].visible = False
                    ctx["btn_eliminar"].visible = True
                    ctx["spinner"].visible = False
                    ctx["lbl_estado"].value = "Foto guardada en Storage"
                    if ctx.get("dialogo") and ctx["dialogo"].page:
                        ctx["dialogo"].update()
                self.mapeo_paginas_actual = obtener_mapeo_paginas_catalogo(self.catalogo_actual_key, forzar_recarga=True, items_data=self.items_totales)
                self._render_pagina_actual()
                if self.modo_vista == "EDITOR_PAGINAS" or (hasattr(self, "contenedor_vista_editor") and self.contenedor_vista_editor.visible):
                    self._render_pagina_editor_visual()
                self._safe_update()
            else:
                if ctx and ctx.get("spinner"):
                    ctx["spinner"].visible = False
                    ctx["lbl_estado"].value = f"Error: {res_data}"
                    if ctx.get("dialogo") and ctx["dialogo"].page:
                        ctx["dialogo"].update()
                self._mostrar_snackbar(f"❌ Error al guardar foto: {res_data}", "red")

        threading.Thread(target=_tarea_foto, daemon=True).start()

    # -------------------------------------------------------------
    # MODAL: AÑADIR INSUMOS AL CATÁLOGO (LISTAS PARALELAS DINÁMICAS)
    # -------------------------------------------------------------
    def _abrir_modal_anadir_insumo(self, e):
        # 1. Cargar insumos generales y asignaciones
        todos_inv = get_todos_insumos_inventario()
        mapa_asignaciones = get_mapa_catalogos_asignados()
        nombre_cat_actual = CATALOGOS_CONFIG.get(self.catalogo_actual_key, {}).get("nombre", self.catalogo_actual_key)

        # Estado interno del modal
        seleccionados_disp = set() # Códigos seleccionados para traslado masivo
        
        # Paginación izquierda (Disponibles)
        page_size_disp = 6
        current_page_disp = [1]
        filtro_disp_texto = [""]
        
        # Paginación derecha (En Catálogo)
        page_size_cat = 6
        current_page_cat = [1]
        filtro_cat_texto = [""]

        # Controles UI Izquierda
        txt_buscar_disp = ft.TextField(
            hint_text="Buscar por código, nombre o categoría...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            bgcolor="#ffffff",
            border_color="#cbd5e1",
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        chk_todos_pagina = ft.Checkbox(
            label="Sel. pág",
            value=False,
            label_style=ft.TextStyle(size=10.5, weight="bold")
        )

        btn_transfer_masivo = ft.ElevatedButton(
            "Añadir Sel. >>",
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=30,
            disabled=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=ft.padding.symmetric(horizontal=8))
        )

        lista_disp_ctrl = ft.ListView(spacing=4, expand=True)
        lbl_info_pag_disp = ft.Text("Pág 1 de 1", size=11, weight="bold", color="#1e293b")
        btn_prev_disp = ft.IconButton(
            icon=ft.icons.CHEVRON_LEFT_ROUNDED,
            icon_size=18,
            icon_color="#0f172a",
            tooltip="Página anterior",
            style=ft.ButtonStyle(
                bgcolor={ft.MaterialState.DEFAULT: "#ffffff", ft.MaterialState.DISABLED: "#f1f5f9"},
                padding=ft.padding.all(4),
                shape=ft.RoundedRectangleBorder(radius=4)
            )
        )
        btn_next_disp = ft.IconButton(
            icon=ft.icons.CHEVRON_RIGHT_ROUNDED,
            icon_size=18,
            icon_color="#0f172a",
            tooltip="Página siguiente",
            style=ft.ButtonStyle(
                bgcolor={ft.MaterialState.DEFAULT: "#ffffff", ft.MaterialState.DISABLED: "#f1f5f9"},
                padding=ft.padding.all(4),
                shape=ft.RoundedRectangleBorder(radius=4)
            )
        )
        lbl_total_disp = ft.Text("0 disponibles", size=12, weight="bold", color="#0f172a")

        # Controles UI Derecha
        txt_buscar_cat = ft.TextField(
            hint_text="Buscar en este catálogo...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            dense=True,
            border_radius=8,
            height=40,
            text_size=12,
            bgcolor="#ffffff",
            border_color="#cbd5e1",
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

        lista_cat_ctrl = ft.ListView(spacing=4, expand=True)
        lbl_info_pag_cat = ft.Text("Pág 1 de 1", size=11, weight="bold", color="#1e293b")
        btn_prev_cat = ft.IconButton(
            icon=ft.icons.CHEVRON_LEFT_ROUNDED,
            icon_size=18,
            icon_color="#0f172a",
            tooltip="Página anterior",
            style=ft.ButtonStyle(
                bgcolor={ft.MaterialState.DEFAULT: "#ffffff", ft.MaterialState.DISABLED: "#f1f5f9"},
                padding=ft.padding.all(4),
                shape=ft.RoundedRectangleBorder(radius=4)
            )
        )
        btn_next_cat = ft.IconButton(
            icon=ft.icons.CHEVRON_RIGHT_ROUNDED,
            icon_size=18,
            icon_color="#0f172a",
            tooltip="Página siguiente",
            style=ft.ButtonStyle(
                bgcolor={ft.MaterialState.DEFAULT: "#ffffff", ft.MaterialState.DISABLED: "#f1f5f9"},
                padding=ft.padding.all(4),
                shape=ft.RoundedRectangleBorder(radius=4)
            )
        )
        lbl_total_cat = ft.Text("0 en catálogo", size=12, weight="bold", color="#0f172a")

        def _obtener_codigos_actuales() -> set:
            return set(str(it.get("codigo", "")).strip() for it in self.items_totales)

        def _render_ambas_listas():
            codigos_cat = _obtener_codigos_actuales()

            # --- 1. FILTRAR Y RENDERIZAR IZQUIERDA (DISPONIBLES CON BÚSQUEDA INTELIGENTE) ---
            candidatos_disp = [
                ins for ins in todos_inv
                if str(ins.get("codigo_insumo", "")).strip() not in codigos_cat
                and cumple_busqueda_inteligente(
                    filtro_disp_texto[0],
                    ins.get("codigo_insumo"),
                    ins.get("nombre"),
                    ins.get("categoria"),
                    ins.get("descripcion")
                )
            ]

            total_disp = len(candidatos_disp)
            tot_pages_disp = max(1, math.ceil(total_disp / page_size_disp))
            if current_page_disp[0] > tot_pages_disp:
                current_page_disp[0] = tot_pages_disp
            
            ini_disp = (current_page_disp[0] - 1) * page_size_disp
            fin_disp = min(ini_disp + page_size_disp, total_disp)
            pagina_disp = candidatos_disp[ini_disp:fin_disp]

            lbl_total_disp.value = f"Disponibles ({total_disp})"
            lbl_info_pag_disp.value = f"Pág {current_page_disp[0]} de {tot_pages_disp}"
            btn_prev_disp.disabled = (current_page_disp[0] <= 1)
            btn_next_disp.disabled = (current_page_disp[0] >= tot_pages_disp)

            lista_disp_ctrl.controls.clear()
            if not pagina_disp:
                lista_disp_ctrl.controls.append(
                    ft.Container(
                        padding=ft.padding.all(20),
                        alignment=ft.alignment.center,
                        content=ft.Text("No se encontraron insumos disponibles", size=11, color="grey500", italic=True)
                    )
                )
            else:
                for ins in pagina_disp:
                    c_cod = str(ins.get("codigo_insumo", "")).strip()
                    c_nom = str(ins.get("nombre", "")).strip()
                    c_pv = float(ins.get("precio_venta") or 0.0)
                    
                    # Ver asignaciones a otros catálogos
                    otros_cats = mapa_asignaciones.get(c_cod, [])
                    if otros_cats:
                        badge_cat_asign = ft.Container(
                            content=ft.Text(f"En: {', '.join(otros_cats)}", size=8.5, weight="bold", color="#1e293b"),
                            bgcolor="#e2e8f0",
                            padding=ft.padding.symmetric(horizontal=5, vertical=2),
                            border_radius=4
                        )
                    else:
                        badge_cat_asign = ft.Container(
                            content=ft.Text("Libre", size=8.5, weight="bold", color="green900"),
                            bgcolor="#dcfce7",
                            padding=ft.padding.symmetric(horizontal=5, vertical=2),
                            border_radius=4
                        )

                    is_checked = (c_cod in seleccionados_disp)

                    def _crear_toggle_cb(codigo):
                        return lambda e: _toggle_seleccion(codigo, e.control.value)

                    def _crear_anadir_uno(ins_item):
                        return lambda e: _anadir_insumo_individual(ins_item)

                    fila_item_disp = ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=6,
                        bgcolor="#ffffff",
                        border=ft.border.all(1, "#cbd5e1" if not is_checked else Config.COLOR_PRIMARY),
                        content=ft.Row([
                            ft.Checkbox(value=is_checked, on_change=_crear_toggle_cb(c_cod)),
                            ft.Column([
                                ft.Row([
                                    ft.Text(f"[{c_cod}]", size=10.5, weight="bold", color="#00509d"),
                                    ft.Text(c_nom, size=11, weight="w600", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                                ], spacing=4),
                                ft.Row([
                                    badge_cat_asign,
                                    ft.Text(f"Venta: {formatear_precio(c_pv)}", size=9.5, color=Config.COLOR_TEXT_MUTED)
                                ], spacing=6)
                            ], expand=True, spacing=1),
                            ft.IconButton(
                                icon=ft.icons.ADD_CIRCLE_OUTLINE_ROUNDED,
                                icon_color=Config.COLOR_PRIMARY,
                                icon_size=20,
                                tooltip=f"Añadir {c_nom} al catálogo",
                                on_click=_crear_anadir_uno(ins)
                            )
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                    lista_disp_ctrl.controls.append(fila_item_disp)

            btn_transfer_masivo.disabled = (len(seleccionados_disp) == 0)
            btn_transfer_masivo.text = f"Añadir ({len(seleccionados_disp)}) >>"

            # --- 2. FILTRAR Y RENDERIZAR DERECHA (EN CATÁLOGO CON BÚSQUEDA INTELIGENTE) ---
            candidatos_cat = [
                it for it in self.items_totales
                if cumple_busqueda_inteligente(
                    filtro_cat_texto[0],
                    it.get("codigo"),
                    it.get("nombre"),
                    it.get("descripcion"),
                    it.get("familia")
                )
            ]

            total_cat = len(candidatos_cat)
            tot_pages_cat = max(1, math.ceil(total_cat / page_size_cat))
            if current_page_cat[0] > tot_pages_cat:
                current_page_cat[0] = tot_pages_cat

            ini_cat = (current_page_cat[0] - 1) * page_size_cat
            fin_cat = min(ini_cat + page_size_cat, total_cat)
            pagina_cat = candidatos_cat[ini_cat:fin_cat]

            lbl_total_cat.value = f"En Catálogo ({len(self.items_totales)})"
            lbl_info_pag_cat.value = f"Pág {current_page_cat[0]} de {tot_pages_cat}"
            btn_prev_cat.disabled = (current_page_cat[0] <= 1)
            btn_next_cat.disabled = (current_page_cat[0] >= tot_pages_cat)

            lista_cat_ctrl.controls.clear()
            if not pagina_cat:
                lista_cat_ctrl.controls.append(
                    ft.Container(
                        padding=ft.padding.all(20),
                        alignment=ft.alignment.center,
                        content=ft.Text("No hay insumos en este catálogo aún", size=11, color="grey500", italic=True)
                    )
                )
            else:
                for it in pagina_cat:
                    k_cod = str(it.get("codigo", "")).strip()
                    k_nom = str(it.get("nombre", "")).strip()
                    k_pv = float(it.get("precio_venta", 0.0))

                    def _crear_retirar_uno(item_ret):
                        return lambda e: _retirar_insumo_individual(item_ret)

                    fila_item_cat = ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=6,
                        bgcolor="#f8fafc",
                        border=ft.border.all(1, "#e2e8f0"),
                        content=ft.Row([
                            ft.Column([
                                ft.Row([
                                    ft.Text(f"[{k_cod}]", size=10.5, weight="bold", color="#00509d"),
                                    ft.Text(k_nom, size=11, weight="w600", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                                ], spacing=4),
                                ft.Text(f"Precio Catálogo: {formatear_precio(k_pv)}", size=9.5, weight="bold", color=Config.COLOR_PRIMARY)
                            ], expand=True, spacing=1),
                            ft.IconButton(
                                icon=ft.icons.REMOVE_CIRCLE_OUTLINE_ROUNDED,
                                icon_color="red700",
                                icon_size=20,
                                tooltip=f"Retirar {k_nom} del catálogo",
                                on_click=_crear_retirar_uno(it)
                            )
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                    lista_cat_ctrl.controls.append(fila_item_cat)

            if lista_disp_ctrl.page:
                lista_disp_ctrl.update()
            if lista_cat_ctrl.page:
                lista_cat_ctrl.update()
            if btn_transfer_masivo.page:
                btn_transfer_masivo.update()
            if lbl_total_disp.page:
                lbl_total_disp.update()
            if lbl_total_cat.page:
                lbl_total_cat.update()
            if lbl_info_pag_disp.page:
                lbl_info_pag_disp.update()
            if lbl_info_pag_cat.page:
                lbl_info_pag_cat.update()
            if btn_prev_disp.page:
                btn_prev_disp.update()
            if btn_next_disp.page:
                btn_next_disp.update()
            if btn_prev_cat.page:
                btn_prev_cat.update()
            if btn_next_cat.page:
                btn_next_cat.update()

        # Operaciones de traslado
        def _toggle_seleccion(cod: str, valor: bool):
            if valor:
                seleccionados_disp.add(cod)
            else:
                seleccionados_disp.discard(cod)
            btn_transfer_masivo.disabled = (len(seleccionados_disp) == 0)
            btn_transfer_masivo.text = f"Añadir ({len(seleccionados_disp)}) >>"
            if btn_transfer_masivo.page:
                btn_transfer_masivo.update()

        def _on_chk_todos_pagina(e):
            codigos_cat = _obtener_codigos_actuales()
            candidatos_disp = [
                ins for ins in todos_inv
                if str(ins.get("codigo_insumo", "")).strip() not in codigos_cat
                and cumple_busqueda_inteligente(
                    filtro_disp_texto[0],
                    ins.get("codigo_insumo"),
                    ins.get("nombre"),
                    ins.get("categoria"),
                    ins.get("descripcion")
                )
            ]
            ini_disp = (current_page_disp[0] - 1) * page_size_disp
            fin_disp = min(ini_disp + page_size_disp, len(candidatos_disp))
            for ins in candidatos_disp[ini_disp:fin_disp]:
                c_cod = str(ins.get("codigo_insumo", "")).strip()
                if e.control.value:
                    seleccionados_disp.add(c_cod)
                else:
                    seleccionados_disp.discard(c_cod)
            _render_ambas_listas()

        def _anadir_insumo_individual(ins_data: dict):
            c_cod = str(ins_data.get("codigo_insumo", "")).strip()
            c_nom = str(ins_data.get("nombre", "")).strip()
            c_desc = str(ins_data.get("descripcion", "") or c_nom).strip()
            c_pv = float(ins_data.get("precio_venta") or 0.0)

            nuevo_item = {
                "codigo": c_cod,
                "nombre": c_nom,
                "descripcion": c_desc,
                "familia": "General",
                "precio_venta": c_pv,
                "precio_manual": False
            }
            self.items_totales.append(nuevo_item)
            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            seleccionados_disp.discard(c_cod)
            
            # Actualizar mapa de asignaciones
            if c_cod not in mapa_asignaciones:
                mapa_asignaciones[c_cod] = []
            if nombre_cat_actual not in mapa_asignaciones[c_cod]:
                mapa_asignaciones[c_cod].append(nombre_cat_actual)

            self.mapeo_paginas_actual = obtener_mapeo_paginas_catalogo(self.catalogo_actual_key, forzar_recarga=True, items_data=self.items_totales)
            self._actualizar_opciones_drop_editor()
            _render_ambas_listas()
            self._aplicar_filtros()
            self._safe_update()

        def _anadir_seleccionados_masivo(e):
            if not seleccionados_disp:
                return
            
            map_inv = {str(i.get("codigo_insumo", "")).strip(): i for i in todos_inv}
            agregados = 0
            for c_cod in list(seleccionados_disp):
                if c_cod in map_inv:
                    ins_data = map_inv[c_cod]
                    c_nom = str(ins_data.get("nombre", "")).strip()
                    c_desc = str(ins_data.get("descripcion", "") or c_nom).strip()
                    c_pv = float(ins_data.get("precio_venta") or 0.0)

                    nuevo_item = {
                        "codigo": c_cod,
                        "nombre": c_nom,
                        "descripcion": c_desc,
                        "familia": "General",
                        "precio_venta": c_pv,
                        "precio_manual": False
                    }
                    self.items_totales.append(nuevo_item)
                    
                    if c_cod not in mapa_asignaciones:
                        mapa_asignaciones[c_cod] = []
                    if nombre_cat_actual not in mapa_asignaciones[c_cod]:
                        mapa_asignaciones[c_cod].append(nombre_cat_actual)
                    
                    agregados += 1

            seleccionados_disp.clear()
            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            self.mapeo_paginas_actual = obtener_mapeo_paginas_catalogo(self.catalogo_actual_key, forzar_recarga=True, items_data=self.items_totales)
            self._actualizar_opciones_drop_editor()
            _render_ambas_listas()
            self._aplicar_filtros()
            self._mostrar_snackbar(f"Se agregaron {agregados} insumos al catálogo de {nombre_cat_actual}", "green")
            self._safe_update()

        def _retirar_insumo_individual(item_ret: dict):
            c_cod = str(item_ret.get("codigo", "")).strip()
            self.items_totales = [it for it in self.items_totales if str(it.get("codigo", "")).strip() != c_cod]
            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            
            if c_cod in mapa_asignaciones and nombre_cat_actual in mapa_asignaciones[c_cod]:
                mapa_asignaciones[c_cod].remove(nombre_cat_actual)

            self.mapeo_paginas_actual = obtener_mapeo_paginas_catalogo(self.catalogo_actual_key, forzar_recarga=True, items_data=self.items_totales)
            self._actualizar_opciones_drop_editor()
            _render_ambas_listas()
            self._aplicar_filtros()
            self._safe_update()

        # Callbacks de búsqueda y paginación
        def _on_buscar_disp_change(e):
            filtro_disp_texto[0] = (txt_buscar_disp.value or "").strip()
            current_page_disp[0] = 1
            _render_ambas_listas()

        def _on_buscar_cat_change(e):
            filtro_cat_texto[0] = (txt_buscar_cat.value or "").strip()
            current_page_cat[0] = 1
            _render_ambas_listas()

        def _on_prev_disp(e):
            if current_page_disp[0] > 1:
                current_page_disp[0] -= 1
                _render_ambas_listas()

        def _on_next_disp(e):
            current_page_disp[0] += 1
            _render_ambas_listas()

        def _on_prev_cat(e):
            if current_page_cat[0] > 1:
                current_page_cat[0] -= 1
                _render_ambas_listas()

        def _on_next_cat(e):
            current_page_cat[0] += 1
            _render_ambas_listas()

        txt_buscar_disp.on_change = _on_buscar_disp_change
        txt_buscar_cat.on_change = _on_buscar_cat_change
        chk_todos_pagina.on_change = _on_chk_todos_pagina
        btn_transfer_masivo.on_click = _anadir_seleccionados_masivo
        btn_prev_disp.on_click = _on_prev_disp
        btn_next_disp.on_click = _on_next_disp
        btn_prev_cat.on_click = _on_prev_cat
        btn_next_cat.on_click = _on_next_cat

        _render_ambas_listas()

        # Construcción visual del Modal de Dos Columnas
        barra_pag_disp = ft.Container(
            bgcolor="#e2e8f0",
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            content=ft.Row([
                lbl_info_pag_disp,
                ft.Row([btn_prev_disp, btn_next_disp], spacing=4)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        barra_pag_cat = ft.Container(
            bgcolor="#e2e8f0",
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            content=ft.Row([
                lbl_info_pag_cat,
                ft.Row([btn_prev_cat, btn_next_cat], spacing=4)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        columna_izquierda = ft.Container(
            expand=True,
            bgcolor="#f8fafc",
            border=ft.border.all(1, "#cbd5e1"),
            border_radius=8,
            padding=ft.padding.all(10),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.INVENTORY_2_ROUNDED, size=18, color="#0284c7"),
                    lbl_total_disp,
                ], spacing=6),
                txt_buscar_disp,
                ft.Row([
                    chk_todos_pagina,
                    btn_transfer_masivo
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(content=lista_disp_ctrl, expand=True),
                barra_pag_disp
            ], spacing=6, expand=True)
        )

        columna_derecha = ft.Container(
            expand=True,
            bgcolor="#f8fafc",
            border=ft.border.all(1, "#cbd5e1"),
            border_radius=8,
            padding=ft.padding.all(10),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.MENU_BOOK_ROUNDED, size=18, color="#059669"),
                    lbl_total_cat,
                ], spacing=6),
                txt_buscar_cat,
                ft.Container(
                    height=30,
                    content=ft.Text("Insumos en este catálogo:", size=11, color=Config.COLOR_TEXT_MUTED, weight="w600"),
                    alignment=ft.alignment.center_left
                ),
                ft.Container(content=lista_cat_ctrl, expand=True),
                barra_pag_cat
            ], spacing=6, expand=True)
        )

        dialogo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.SWAP_HORIZ_ROUNDED, color=Config.COLOR_PRIMARY),
                ft.Text(f"Gestión y Asignación de Insumos - Catálogo de {nombre_cat_actual}", size=15, weight="bold")
            ], spacing=8),
            content=ft.Container(
                width=980,
                height=570,
                content=ft.Row([
                    columna_izquierda,
                    ft.VerticalDivider(width=1, color="#cbd5e1"),
                    columna_derecha
                ], spacing=12, expand=True)
            ),
            actions=[
                ft.ElevatedButton("Finalizar y Cerrar", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=lambda _: self._cerrar_modal(dialogo))
            ]
        )
        self._abrir_modal(dialogo)

    # -------------------------------------------------------------
    # RETIRAR INSUMO DEL CATÁLOGO
    # -------------------------------------------------------------
    def _confirmar_retirar_insumo(self, item: dict):
        nom = item.get("nombre", "este insumo")
        cod = item.get("codigo", "")

        def _ejecutar_retirar(e):
            self.items_totales = [it for it in self.items_totales if str(it.get("codigo", "")).strip() != str(cod).strip()]
            guardar_items_catalogo(self.catalogo_actual_key, self.items_totales)
            self._cerrar_modal(dialogo)
            self._aplicar_filtros()
            self._mostrar_snackbar(f"Insumo {nom} retirado del catálogo", "amber800")
            self._safe_update()

        dialogo = ft.AlertDialog(
            title=ft.Text("Retirar Insumo del Catálogo", size=13, weight="bold"),
            content=ft.Text(f"¿Deseas retirar '{nom}' de este catálogo? (No se borrará del inventario general).", size=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cerrar_modal(dialogo)),
                ft.ElevatedButton("Retirar", bgcolor="red700", color="white", on_click=_ejecutar_retirar)
            ]
        )
        self._abrir_modal(dialogo)

    # -------------------------------------------------------------
    # EXPORTAR CATÁLOGO A PDF
    # -------------------------------------------------------------
    def _on_exportar_pdf_click(self, e):
        cfg = CATALOGOS_CONFIG.get(self.catalogo_actual_key, {})
        nombre_defecto = f"Catalogo_{cfg.get('nombre', 'Oficial')}_Dona_Mary.pdf"
        self.file_picker_exportar.save_file(
            dialog_title="Guardar Catálogo en PDF",
            file_name=nombre_defecto,
            allowed_extensions=["pdf"]
        )

    def _on_exportar_pdf_result(self, e: ft.FilePickerResultEvent):
        if not e.path:
            return

        ruta_destino = e.path
        self.indicador_exportando.visible = True
        self.menu_herramientas.disabled = True
        self._safe_update()
        self._mostrar_snackbar("⏳ Generando PDF oficial con Microsoft Edge... Por favor espera un momento.", "blue")

        # Construir mapa de precios actualizados (respetando precios manuales y de inventario)
        mapa_precios_actuales = {}
        for it in self.items_totales:
            cod = str(it.get("codigo", "")).strip()
            pv = float(it.get("precio_venta", 0.0))
            if pv > 0:
                mapa_precios_actuales[cod] = pv

        def _tarea_export():
            try:
                ok, msg = exportar_catalogo_pdf(
                    self.catalogo_actual_key,
                    ruta_destino,
                    precios_map=mapa_precios_actuales,
                    items_data=self.items_totales
                )
                if ok:
                    self._mostrar_snackbar(f"✅ Catálogo PDF generado con éxito en: {os.path.basename(ruta_destino)}", "green")
                    try:
                        os.startfile(ruta_destino)
                    except Exception:
                        pass
                else:
                    self._mostrar_snackbar(f"❌ Error al generar PDF: {msg}", "red")
            finally:
                self.indicador_exportando.visible = False
                self.menu_herramientas.disabled = False
                self._safe_update()

        threading.Thread(target=_tarea_export, daemon=True).start()

    # -------------------------------------------------------------
    # UTILIDADES DE MODALES Y SNACKBAR
    # -------------------------------------------------------------
    def _abrir_modal(self, modal: ft.AlertDialog):
        if self.page:
            if modal not in self.page.overlay:
                self.page.overlay.append(modal)
            modal.open = True
            self.page.update()

    def _cerrar_modal(self, modal: ft.AlertDialog):
        if modal:
            modal.open = False
        if self.page:
            self.page.update()

    def _mostrar_snackbar(self, texto: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(texto, color="white", weight="bold"),
                bgcolor=color,
                duration=4000
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _safe_update(self):
        try:
            self.update()
        except Exception:
            pass
