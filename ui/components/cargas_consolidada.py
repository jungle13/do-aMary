"""
ui/components/cargas_consolidada.py
Componente visual consolidado y moderno para la gestión de cargas de reportes PDF
(Compras y Ventas) sin paginación tediosa, con detección de duplicados, acordeón interactivo
y guardado en lote masivo.
"""
import flet as ft
from config import Config
from typing import Callable, Optional, Dict, Any, List

class CargasConsolidadaView(ft.Container):
    def __init__(
        self,
        modulo: str, # "COMPRAS" o "VENTAS"
        on_upload_click: Callable,
        on_save_callback: Callable,
        on_discard_callback: Optional[Callable] = None
    ):
        super().__init__(expand=True)
        self.modulo = modulo
        self.on_upload_click = on_upload_click
        self.on_save_callback = on_save_callback
        self.on_discard_callback = on_discard_callback
        
        self.carga_data: Optional[Dict[str, Any]] = None
        self.search_query = ""
        self.filtro_estado = "TODOS" # "TODOS", "NUEVOS", "REGISTRADOS"
        
        self.lista_facturas_view = ft.ListView(expand=True, spacing=8)
        self._construir_ui()

    def set_data(self, data: Optional[Dict[str, Any]]):
        """Establece los datos extraídos del PDF y reconstruye la vista."""
        self.carga_data = data
        self.search_query = ""
        self.filtro_estado = "TODOS"
        self._actualizar_contenido()

    def _construir_ui(self):
        self.main_column = ft.Column(expand=True, spacing=10)
        self.content = self.main_column
        self._actualizar_contenido()

    def _actualizar_contenido(self):
        self.main_column.controls.clear()
        if not self.carga_data or not self.carga_data.get("facturas"):
            self.main_column.controls.append(self._construir_dropzone_vacia())
        else:
            self.main_column.controls.append(self._construir_resumen_header())
            self.main_column.controls.append(self._construir_barra_filtros())
            self.main_column.controls.append(ft.Container(content=self.lista_facturas_view, expand=True))
            self.main_column.controls.append(self._construir_barra_inferior())
            self._render_lista_facturas()

        try:
            if self.page:
                self.update()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # 1. DROPZONE VACÍA
    # --------------------------------------------------------------------------
    def _construir_dropzone_vacia(self) -> ft.Container:
        subtitulo = (
            "Sube un reporte PDF de Entradas de Almacén (EA) para procesar compras."
            if self.modulo == "COMPRAS" else
            "Sube un reporte PDF de Facturas POS (FV) o Ventas Diarias (Remisiones PP)."
        )
        btn_txt = "Subir PDF de Compras" if self.modulo == "COMPRAS" else "Subir PDF de Ventas"
        
        return ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Container(
                width=650,
                padding=40,
                bgcolor="white",
                border_radius=16,
                border=ft.border.all(1.5, "#e2e8f0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.colors.with_opacity(0.04, "black")),
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(ft.icons.CLOUD_UPLOAD_ROUNDED, size=56, color=Config.COLOR_PRIMARY),
                        bgcolor="#eff6ff",
                        padding=20,
                        border_radius=50
                    ),
                    ft.Text("Carga Inteligente de Documentos PDF", size=20, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Text(subtitulo, size=13, color="grey600", text_align=ft.TextAlign.CENTER),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        text=btn_txt,
                        icon=ft.icons.PICTURE_AS_PDF_ROUNDED,
                        bgcolor=Config.COLOR_PRIMARY,
                        color="white",
                        height=46,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        on_click=self.on_upload_click
                    ),
                    ft.Row([
                        ft.Icon(ft.icons.FLASH_ON_ROUNDED, size=16, color="amber700"),
                        ft.Text("Extracción determinista en 0.1s sin IA  •  Detección automática de duplicados", size=11, color="grey600")
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=6)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)
            )
        )

    # --------------------------------------------------------------------------
    # 2. HEADER CON MÉTRICAS RESUMEN
    # --------------------------------------------------------------------------
    def _construir_resumen_header(self) -> ft.Container:
        f_list = self.carga_data.get("facturas", [])
        total_docs = len(f_list)
        nuevas = sum(1 for f in f_list if not f.get("ya_registrada", False))
        repetidas = total_docs - nuevas
        
        nombre_archivo = self.carga_data.get("nombre_archivo", "Reporte.pdf")
        tipo_rep = self.carga_data.get("tipo_reporte", "DOCUMENTO").replace("_", " ")
        rango = f"{self.carga_data.get('rango_desde', '')} - {self.carga_data.get('rango_hasta', '')}"
        
        tot_general = self.carga_data.get("total_general", 0.0)
        tot_pie = self.carga_data.get("total_reporte_pie", tot_general)
        tot_insumos = self.carga_data.get("total_insumos", 0)
        
        diff = abs(tot_general - tot_pie)
        cuadrado = diff < 10.0
        
        return ft.Container(
            bgcolor="white",
            padding=15,
            border_radius=12,
            border=ft.border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.04, "black")),
            content=ft.Row([
                # Card 1: Archivo y Fechas
                ft.Container(
                    expand=2,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.PICTURE_AS_PDF_ROUNDED, color="red600", size=20),
                            ft.Text(nombre_archivo, weight="bold", size=14, color=Config.COLOR_PRIMARY, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ]),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(tipo_rep, size=10, weight="bold", color="blue800"),
                                bgcolor="#dbeafe", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4
                            ),
                            ft.Text(f"📅 {rango}", size=11, color="grey700", weight="w500")
                        ], spacing=6)
                    ], spacing=4)
                ),
                ft.VerticalDivider(width=1, color="#cbd5e1"),
                # Card 2: Documentos Extraídos
                ft.Container(
                    expand=2,
                    content=ft.Column([
                        ft.Text(f"{total_docs} Documentos Extraídos", size=14, weight="bold", color="black87"),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(f"✓ {nuevas} Nuevos", size=10, weight="bold", color="green800"),
                                bgcolor="#dcfce7", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4
                            ),
                            ft.Container(
                                content=ft.Text(f"⚠️ {repetidas} Ya Registrados", size=10, weight="bold", color="orange900" if repetidas > 0 else "grey600"),
                                bgcolor="#ffedd5" if repetidas > 0 else "#f1f5f9", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4
                            ),
                            ft.Text(f"📦 {tot_insumos} ítems", size=11, color="grey600")
                        ], spacing=6)
                    ], spacing=4)
                ),
                ft.VerticalDivider(width=1, color="#cbd5e1"),
                # Card 3: Total Financiero Conciliado
                ft.Container(
                    expand=2,
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Total del Reporte:", size=11, color="grey600"),
                            ft.Container(
                                content=ft.Text("✓ Conciliado 100%" if cuadrado else f"Dif: ${diff:,.0f}", size=9, weight="bold", color="green800" if cuadrado else "red800"),
                                bgcolor="#dcfce7" if cuadrado else "#fee2e2", padding=ft.padding.symmetric(horizontal=4, vertical=1), border_radius=4
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"${tot_general:,.2f}", size=16, weight="bold", color=Config.COLOR_PRIMARY)
                    ], spacing=2)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # --------------------------------------------------------------------------
    # 3. BARRA DE BÚSQUEDA Y FILTROS
    # --------------------------------------------------------------------------
    def _construir_barra_filtros(self) -> ft.Row:
        f_list = self.carga_data.get("facturas", [])
        total_docs = len(f_list)
        nuevas = sum(1 for f in f_list if not f.get("ya_registrada", False))
        repetidas = total_docs - nuevas

        txt_buscar = ft.TextField(
            hint_text="Buscar por factura, proveedor/cliente, o código de insumo...",
            prefix_icon=ft.icons.SEARCH,
            height=38,
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            expand=True,
            border_radius=8,
            on_change=self._on_search_change
        )

        def set_filtro(est):
            self.filtro_estado = est
            self._render_lista_facturas()

        btn_todos = ft.OutlinedButton(f"Todos ({total_docs})", on_click=lambda e: set_filtro("TODOS"), height=36)
        btn_nuevos = ft.ElevatedButton(f"Nuevos ({nuevas})", bgcolor="#dcfce7", color="green900", on_click=lambda e: set_filtro("NUEVOS"), height=36)
        btn_dups = ft.OutlinedButton(f"Ya Registrados ({repetidas})", on_click=lambda e: set_filtro("REGISTRADOS"), height=36)

        return ft.Row([
            txt_buscar,
            btn_todos,
            btn_nuevos,
            btn_dups,
            ft.IconButton(
                icon=ft.icons.SELECT_ALL_ROUNDED,
                tooltip="Seleccionar / Deseleccionar Todo",
                on_click=self._toggle_select_all
            ),
            ft.IconButton(
                icon=ft.icons.UNFOLD_MORE_ROUNDED,
                tooltip="Expandir / Colapsar Todo",
                on_click=self._toggle_expand_all
            ),
            ft.IconButton(
                icon=ft.icons.DELETE_SWEEP_ROUNDED,
                icon_color="red600",
                tooltip="Descartar este PDF",
                on_click=self._descartar_carga
            )
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # --------------------------------------------------------------------------
    # 4. RENDERIZADO DE LA LISTA DE FACTURAS (ACORDEÓN)
    # --------------------------------------------------------------------------
    def _render_lista_facturas(self):
        self.lista_facturas_view.controls.clear()
        if not self.carga_data:
            return

        q = self.search_query.lower().strip()
        filtro_est = self.filtro_estado

        for idx, fact in enumerate(self.carga_data.get("facturas", [])):
            is_dup = fact.get("ya_registrada", False)
            if filtro_est == "NUEVOS" and is_dup:
                continue
            if filtro_est == "REGISTRADOS" and not is_dup:
                continue

            # Filtro de búsqueda
            ref_doc = str(fact.get("factura_no") or fact.get("numero_entrada") or "").lower()
            ent_doc = str(fact.get("numero_entrada") or "").lower()
            tercero = str(fact.get("proveedor") or fact.get("cliente") or "").lower()
            items_str = " ".join([f"{it.get('codigo_insumo','')} {it.get('descripcion','')}".lower() for it in fact.get("items", [])])
            
            if q and (q not in ref_doc and q not in ent_doc and q not in tercero and q not in items_str):
                continue

            card = self._crear_tarjeta_factura(fact, idx)
            self.lista_facturas_view.controls.append(card)

        try:
            self.lista_facturas_view.update()
        except Exception:
            pass

    def _crear_tarjeta_factura(self, fact: Dict[str, Any], fact_idx: int) -> ft.Container:
        is_dup = fact.get("ya_registrada", False)
        is_selected = fact.get("seleccionada", not is_dup)
        is_expanded = fact.get("expandida", False)
        
        num_doc = fact.get("factura_no") or fact.get("numero_entrada") or "S/N"
        num_ea = fact.get("numero_entrada", "")
        tercero = fact.get("proveedor") or fact.get("cliente") or "General"
        fecha = fact.get("fecha_display") or fact.get("fecha") or ""
        tipo_doc = fact.get("tipo_documento", "Documento")
        items = fact.get("items", [])
        
        total_val = fact.get("total_entrada") or fact.get("total_factura") or sum(it.get("total", it.get("costo_total", 0)) for it in items)
        
        # Checkbox selector
        def on_cb_change(e, f=fact):
            f["seleccionada"] = e.control.value
            self._actualizar_barra_inferior()

        cb = ft.Checkbox(value=is_selected, on_change=on_cb_change)
        
        # Badge de estado
        badge_estado = ft.Container(
            content=ft.Text("✓ NUEVA", size=10, weight="bold", color="green800") if not is_dup else ft.Text("⚠️ YA REGISTRADA", size=10, weight="bold", color="orange900"),
            bgcolor="#dcfce7" if not is_dup else "#ffedd5",
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=6
        )

        def toggle_expand(e, f=fact):
            f["expandida"] = not f.get("expandida", False)
            self._render_lista_facturas()

        def eliminar_factura(e, f_idx=fact_idx):
            self.carga_data["facturas"].pop(f_idx)
            self._actualizar_contenido()

        btn_expand = ft.IconButton(
            icon=ft.icons.KEYBOARD_ARROW_UP_ROUNDED if is_expanded else ft.icons.KEYBOARD_ARROW_DOWN_ROUNDED,
            tooltip="Colapsar" if is_expanded else "Ver Insumos",
            on_click=toggle_expand
        )
        
        btn_eliminar = ft.IconButton(
            icon=ft.icons.DELETE_OUTLINE_ROUNDED,
            icon_color="grey600",
            tooltip="Descartar esta factura",
            on_click=eliminar_factura
        )

        doc_label = f"[{num_ea}] Factura #{num_doc}" if num_ea and num_ea != num_doc else f"Doc #{num_doc}"

        fila_cabecera = ft.Row([
            cb,
            ft.Text(doc_label, weight="bold", size=13, color=Config.COLOR_PRIMARY),
            ft.Text(f"• {tercero}", weight="w600", size=12, color="grey800", expand=True, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Text(f"📅 {fecha}", size=11, color="grey600"),
            ft.Container(
                content=ft.Text(f"{len(items)} ítems", size=10, weight="bold", color="grey700"),
                bgcolor="#f1f5f9", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4
            ),
            ft.Text(f"${total_val:,.2f}", weight="bold", size=13, color="teal800"),
            badge_estado,
            btn_expand,
            btn_eliminar
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        contenido_tarjeta = [fila_cabecera]

        # Si está expandida, renderizar la tabla compacta de insumos
        if is_expanded:
            tabla_items = self._construir_tabla_items(fact, fact_idx)
            contenido_tarjeta.append(ft.Divider(height=1, color="#e2e8f0"))
            contenido_tarjeta.append(tabla_items)

        return ft.Container(
            bgcolor="white",
            padding=10,
            border_radius=8,
            border=ft.border.all(1, "#cbd5e1" if is_selected else "#e2e8f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.03, "black")),
            content=ft.Column(contenido_tarjeta, spacing=6)
        )

    def _construir_tabla_items(self, fact: Dict[str, Any], fact_idx: int) -> ft.Container:
        items = fact.get("items", [])
        is_compra = self.modulo == "COMPRAS"

        cols = [
            ft.DataColumn(ft.Text("Código", size=11, weight="bold")),
            ft.DataColumn(ft.Text("Descripción / Insumo", size=11, weight="bold")),
        ]
        if is_compra:
            cols.append(ft.DataColumn(ft.Text("Bodega", size=11, weight="bold")))
        cols.extend([
            ft.DataColumn(ft.Text("Cantidad", size=11, weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Costo Unit." if is_compra else "Precio Unit.", size=11, weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("IVA", size=11, weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("Total", size=11, weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("", size=11)) # Para botón de eliminar
        ])

        rows = []
        for it_idx, it in enumerate(items):
            cod = it.get("codigo_insumo", "")
            nom = it.get("descripcion", "Desconocido")
            cant = float(it.get("cantidad", 0) or 0)
            costo_u = float(it.get("costo_unitario") or (it.get("subtotal", 0) / cant if cant > 0 else 0))
            iva = float(it.get("valor_iva", it.get("iva", 0)) or 0)
            tot = float(it.get("costo_total", it.get("total", 0)) or 0)

            def eliminar_item(e, f_idx=fact_idx, i_idx=it_idx):
                fact["items"].pop(i_idx)
                if not fact["items"]:
                    self.carga_data["facturas"].pop(f_idx)
                self._actualizar_contenido()

            btn_del_item = ft.IconButton(
                icon=ft.icons.CLOSE_ROUNDED,
                icon_size=14,
                icon_color="red400",
                tooltip="Quitar ítem",
                on_click=eliminar_item
            )

            row_cells = [
                ft.DataCell(ft.Text(cod, size=11, weight="bold", color=Config.COLOR_PRIMARY)),
                ft.DataCell(ft.Text(nom, size=11, overflow=ft.TextOverflow.ELLIPSIS)),
            ]
            if is_compra:
                bod = it.get("bodega", "Bodega 1")
                row_cells.append(ft.DataCell(ft.Text(bod, size=10, color="grey700")))
            row_cells.extend([
                ft.DataCell(ft.Text(f"{cant:g}", size=11)),
                ft.DataCell(ft.Text(f"${costo_u:,.2f}", size=11)),
                ft.DataCell(ft.Text(f"${iva:,.2f}", size=11, color="grey700")),
                ft.DataCell(ft.Text(f"${tot:,.2f}", size=11, weight="bold", color="teal800")),
                ft.DataCell(btn_del_item)
            ])
            rows.append(ft.DataRow(cells=row_cells))

        return ft.Container(
            padding=ft.padding.only(left=30, right=10, top=5, bottom=5),
            content=ft.DataTable(
                columns=cols,
                rows=rows,
                data_row_min_height=30,
                data_row_max_height=35,
                heading_row_height=32,
                heading_row_color="#f8fafc",
                border=ft.border.all(1, "#e2e8f0"),
                border_radius=6
            )
        )

    # --------------------------------------------------------------------------
    # 5. BARRA INFERIOR DE ACCIÓN MAESTRA
    # --------------------------------------------------------------------------
    def _construir_barra_inferior(self) -> ft.Container:
        self.lbl_seleccionados = ft.Text("", size=13, weight="w600", color="black87")
        self.btn_guardar_lote = ft.ElevatedButton(
            text="Confirmar y Guardar Lote",
            icon=ft.icons.SAVE_ROUNDED,
            bgcolor="green700",
            color="white",
            height=44,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=self._on_guardar_click
        )
        self._actualizar_barra_inferior()

        return ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            border_radius=10,
            border=ft.border.all(1, "#cbd5e1"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.05, "black")),
            content=ft.Row([
                self.lbl_seleccionados,
                ft.Container(expand=True),
                self.btn_guardar_lote
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _actualizar_barra_inferior(self):
        if not self.carga_data:
            return
        f_list = self.carga_data.get("facturas", [])
        seleccionadas = [f for f in f_list if f.get("seleccionada", False)]
        cant_sel = len(seleccionadas)
        tot_sel = sum(
            f.get("total_entrada") or f.get("total_factura") or sum(it.get("total", it.get("costo_total", 0)) for it in f.get("items", []))
            for f in seleccionadas
        )
        
        self.lbl_seleccionados.value = f"Seleccionados para guardar: {cant_sel} de {len(f_list)} documentos  •  Monto: ${tot_sel:,.2f}"
        self.btn_guardar_lote.text = f"💾 Confirmar y Guardar {cant_sel} Documentos (${tot_sel:,.0f})"
        self.btn_guardar_lote.disabled = cant_sel == 0

        try:
            if hasattr(self, "lbl_seleccionados") and self.lbl_seleccionados.page:
                self.lbl_seleccionados.update()
                self.btn_guardar_lote.update()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # ACCIONES Y EVENTOS
    # --------------------------------------------------------------------------
    def _on_search_change(self, e):
        self.search_query = e.control.value
        self._render_lista_facturas()

    def _toggle_select_all(self, e):
        if not self.carga_data: return
        f_list = self.carga_data.get("facturas", [])
        # Si alguno está desmarcado, marcar todos los nuevos
        hay_desmarcados = any(not f.get("seleccionada", False) for f in f_list)
        for f in f_list:
            f["seleccionada"] = hay_desmarcados
        self._render_lista_facturas()
        self._actualizar_barra_inferior()

    def _toggle_expand_all(self, e):
        if not self.carga_data: return
        f_list = self.carga_data.get("facturas", [])
        hay_colapsados = any(not f.get("expandida", False) for f in f_list)
        for f in f_list:
            f["expandida"] = hay_colapsados
        self._render_lista_facturas()

    def _descartar_carga(self, e=None):
        self.set_data(None)
        if self.on_discard_callback:
            self.on_discard_callback()

    def _on_guardar_click(self, e):
        if not self.carga_data: return
        seleccionadas = [f for f in self.carga_data.get("facturas", []) if f.get("seleccionada", False)]
        if not seleccionadas:
            return
        self.on_save_callback(seleccionadas)
