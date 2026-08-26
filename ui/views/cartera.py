"""
Vista de Gestión de Cartera y Cuentas por Cobrar para Sistema Doña Mary.
Permite consultar estados de cuenta por cliente, registrar pagos/abonos (FIFO o manual),
diferir deudas en cuotas con amortización automática, buscar por cliente o documento y filtrar por fecha.
"""
import datetime
import flet as ft
from config import Config
from core.database import BaseDatabase
from core.logger import get_logger, log_error
from core.supabase_client import get_client

logger = get_logger("CarteraView")

class CarteraView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.bgcolor = Config.COLOR_BACKGROUND
        self.padding = 16

        self.db = get_client()
        self.cartera_repo = self.db.cartera_repo
        self.clientes_repo = self.db.clientes_repo

        # Estado local
        self.kpis_data = {}
        self.clientes_lista = []
        self.documentos_lista = []
        self.cliente_seleccionado = None
        self.documento_preseleccionado = None
        self.modo_vista_izq = "CLIENTES"
        self.facturas_cliente = []
        self.historial_pagos = []
        self.cuotas_cliente = []
        self.filtro_saldo_actual = "TODOS"
        self.busqueda_actual = ""
        self.fecha_filtro = ""
        self.tab_activo = 0
        self._is_loading = False
        self._is_loading_subdatos = False

        # UI Components
        self._init_ui()

    def _init_ui(self):
        # 1. Encabezado y KPIs
        self.lbl_titulo = ft.Text("Gestión de Cartera y Cuentas por Cobrar", size=20, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_subtitulo = ft.Text("Control de créditos a clientes, recaudos, asignación de pagos y fechas de cobro", size=11, color=Config.COLOR_TEXT_MUTED)

        self.btn_refrescar = ft.IconButton(
            icon=ft.icons.REFRESH_ROUNDED,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Actualizar Cartera",
            on_click=lambda e: self.load_data()
        )

        # Tarjetas KPI
        self.card_total_ventas = self._crear_kpi_card("Total Facturado", "$0", ft.icons.POINT_OF_SALE_ROUNDED, Config.COLOR_PRIMARY)
        self.card_total_recaudo = self._crear_kpi_card("Total Recaudado", "$0", ft.icons.SAVINGS_ROUNDED, Config.COLOR_SUCCESS, subtexto="Efectivo: $0 | Bancos: $0")
        self.card_total_pendiente = self._crear_kpi_card("Saldo por Cobrar", "$0", ft.icons.WARNING_AMBER_ROUNDED, "orange800")
        self.card_clientes_deuda = self._crear_kpi_card("Clientes con Deuda", "0", ft.icons.PEOPLE_ROUNDED, Config.COLOR_ACCENT)

        self.kpis_row = ft.Row([
            self.card_total_ventas,
            self.card_total_recaudo,
            self.card_total_pendiente,
            self.card_clientes_deuda
        ], spacing=10, alignment=ft.MainAxisAlignment.START)

        # 2. Panel Izquierdo: Rediseño Compacto (2 Niveles: Vista + Buscador/Fecha + Chips)
        self.seg_modo_vista = ft.SegmentedButton(
            selected={"CLIENTES"},
            allow_multiple_selection=False,
            segments=[
                ft.Segment(
                    value="CLIENTES",
                    label=ft.Text("Clientes", size=10.5, weight="w600"),
                    icon=ft.Icon(ft.icons.PEOPLE_ROUNDED, size=15)
                ),
                ft.Segment(
                    value="DOCUMENTOS",
                    label=ft.Text("Documentos", size=10.5, weight="w600"),
                    icon=ft.Icon(ft.icons.RECEIPT_LONG_ROUNDED, size=15)
                ),
            ],
            height=32,
            on_change=self._on_modo_vista_change
        )

        # Buscador + Botón de Calendario Integrado
        self.txt_buscador = ft.TextField(
            hint_text="Buscar cliente o No. doc...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            dense=True,
            text_size=11,
            height=36,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
            bgcolor=Config.COLOR_SURFACE,
            border_color=Config.COLOR_BORDER,
            on_change=self._on_search_change,
            expand=True
        )

        self.date_picker = ft.DatePicker(
            on_change=self._on_date_picked,
            help_text="Seleccionar fecha de factura"
        )

        self.btn_date_icon = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_ROUNDED,
            icon_size=18,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Filtrar por fecha",
            bgcolor=ft.colors.with_opacity(0.08, Config.COLOR_PRIMARY),
            width=36,
            height=36,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=0),
            on_click=self._abrir_date_picker
        )

        # Chips de Estado Rápidos
        self.chip_todos = ft.Chip(
            label=ft.Text("Todos", size=10),
            selected=True,
            on_select=lambda e: self._on_chip_filtro_select("TODOS")
        )
        self.chip_con_deuda = ft.Chip(
            label=ft.Text("Con Deuda", size=10),
            selected=False,
            on_select=lambda e: self._on_chip_filtro_select("CON_DEUDA")
        )
        self.chip_al_dia = ft.Chip(
            label=ft.Text("Al Día", size=10),
            selected=False,
            on_select=lambda e: self._on_chip_filtro_select("AL_DIA")
        )

        # Indicador de Fecha Activa Compacto
        self.lbl_fecha_filtro = ft.Text("", size=10, weight="bold", color=Config.COLOR_PRIMARY)
        self.btn_limpiar_fecha = ft.IconButton(
            icon=ft.icons.CLOSE_ROUNDED,
            icon_size=13,
            icon_color="red600",
            tooltip="Quitar filtro de fecha",
            width=20,
            height=20,
            style=ft.ButtonStyle(padding=0),
            on_click=self._limpiar_fecha
        )

        self.chip_fecha_activa = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.EVENT_ROUNDED, size=12, color=Config.COLOR_PRIMARY),
                self.lbl_fecha_filtro,
                self.btn_limpiar_fecha
            ], spacing=2, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.colors.with_opacity(0.12, Config.COLOR_PRIMARY),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=12,
            visible=False
        )

        self.fila_chips = ft.Row([
            ft.Text("Estado:", size=10, color="grey600", weight="bold"),
            self.chip_todos,
            self.chip_con_deuda,
            self.chip_al_dia,
            self.chip_fecha_activa
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)

        self.lista_clientes_view = ft.ListView(
            expand=True,
            spacing=6,
            padding=ft.padding.only(right=2)
        )

        self.col_izquierda = ft.Container(
            content=ft.Column([
                ft.Row([self.seg_modo_vista], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.txt_buscador, self.btn_date_icon], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.fila_chips,
                ft.Divider(height=1, color=Config.COLOR_BORDER),
                self.lista_clientes_view
            ], expand=True, spacing=6),
            width=360,
            bgcolor=Config.COLOR_SURFACE,
            padding=10,
            border_radius=12,
            border=ft.border.all(1, Config.COLOR_BORDER)
        )



        # 3. Panel Derecho (Detalle del Cliente)
        self.panel_derecho_contenido = ft.Container(
            content=self._crear_placeholder_vacio(),
            expand=True,
            bgcolor=Config.COLOR_SURFACE,
            padding=12,
            border_radius=12,
            border=ft.border.all(1, Config.COLOR_BORDER)
        )

        # Botones de Acción del Cliente (visibles solo cuando hay cliente seleccionado)
        self.btn_pagar_global = ft.ElevatedButton(
            text="Registrar Pago",
            icon=ft.icons.PAYMENTS_ROUNDED,
            bgcolor=Config.COLOR_SUCCESS,
            color="white",
            height=34,
            visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=lambda e: self._abrir_modal_pago(self.cliente_seleccionado)
        )
        self.btn_cuotas_global = ft.OutlinedButton(
            text="Plan de Cuotas",
            icon=ft.icons.EVENT_NOTE_ROUNDED,
            height=34,
            visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=lambda e: self._abrir_modal_cuotas(self.cliente_seleccionado)
        )

        # 4. Ensamble Principal
        self.content = ft.Column([
            ft.Row([
                ft.Column([self.lbl_titulo, self.lbl_subtitulo], spacing=2),
                ft.Container(expand=True),
                self.btn_cuotas_global,
                self.btn_pagar_global,
                self.btn_refrescar
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            self.kpis_row,
            ft.Row([
                self.col_izquierda,
                self.panel_derecho_contenido
            ], expand=True, spacing=10)
        ], expand=True, spacing=10)

    def _crear_kpi_card(self, titulo: str, valor: str, icono, color: str, subtexto: str = "") -> ft.Container:
        lbl_val = ft.Text(valor, size=16, weight="bold", color=color)
        lbl_sub = ft.Text(subtexto, size=9.5, color=Config.COLOR_TEXT_MUTED, visible=bool(subtexto))
        
        card = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icono, color=color, size=20),
                    bgcolor=ft.colors.with_opacity(0.12, color),
                    padding=8,
                    border_radius=8
                ),
                ft.Column([
                    ft.Text(titulo, size=10.5, color=Config.COLOR_TEXT_MUTED, weight="w500"),
                    lbl_val,
                    lbl_sub
                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=Config.COLOR_SURFACE,
            border_radius=10,
            border=ft.border.all(1, Config.COLOR_BORDER),
            expand=True
        )
        card._lbl_val = lbl_val
        card._lbl_sub = lbl_sub
        return card

    def _crear_placeholder_vacio(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, size=48, color=Config.COLOR_TEXT_LIGHT),
                ft.Text("Selecciona un cliente de la lista", size=15, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Consulta sus facturas pendientes, historial de abonos, registra pagos y acuerdos de cuotas.", size=11, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            alignment=ft.alignment.center,
            expand=True
        )

    def _crear_loading_indicador(self, mensaje: str = "Cargando datos...") -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=28, height=28, stroke_width=2.5, color=Config.COLOR_PRIMARY),
                ft.Text(mensaje, size=11, color=Config.COLOR_TEXT_MUTED)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            alignment=ft.alignment.center,
            expand=True,
            padding=25
        )

    def did_mount(self):
        # Registrar DatePicker en overlay de la página al montarse
        if self.page and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        # Iniciar carga solo si no se ha cargado
        if not self.clientes_lista and not self._is_loading:
            self.load_data()

    def safe_update(self):
        try:
            if self.page:
                self.page.update()
        except Exception:
            pass

    def load_data(self):
        """Carga en segundo plano los KPIs, la lista de clientes y la lista de documentos."""
        if self._is_loading:
            return
        self._is_loading = True

        def worker():
            try:
                # Una sola llamada que descarga ventas una vez y calcula KPIs + clientes + documentos
                kpis, clientes, documentos = self.cartera_repo.get_resumen_cartera(
                    search=self.busqueda_actual,
                    filtro_saldo=self.filtro_saldo_actual,
                    fecha_filtro=self.fecha_filtro
                )
                self.kpis_data = kpis
                self.clientes_lista = clientes
                self.documentos_lista = documentos

                # Actualizar UI
                self._actualizar_kpis_ui()
                self._render_lista_izquierda()

                if self.cliente_seleccionado:
                    nom_sel = self.cliente_seleccionado.get("nombre")
                    c_upd = next((c for c in clientes if c["nombre"] == nom_sel), None)
                    if c_upd:
                        self.cliente_seleccionado = c_upd
                        self._cargar_detalle_cliente(c_upd, recargar_datos=True)
                    else:
                        self.cliente_seleccionado = None
                        self.btn_pagar_global.visible = False
                        self.btn_cuotas_global.visible = False
                        self.panel_derecho_contenido.content = self._crear_placeholder_vacio()

                self.safe_update()
            except Exception as ex:
                log_error("CarteraView.load_data", ex)
            finally:
                self._is_loading = False

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def _actualizar_kpis_ui(self):
        k = self.kpis_data or {}
        tot_v = k.get("total_ventas", 0.0)
        tot_r = k.get("total_recaudado", 0.0)
        tot_ef = k.get("total_efectivo", 0.0)
        tot_tr = k.get("total_transferencias", 0.0)
        tot_p = k.get("total_saldo_pendiente", 0.0)
        c_deuda = k.get("clientes_con_deuda", 0)

        self.card_total_ventas._lbl_val.value = f"${tot_v:,.0f}"
        self.card_total_recaudo._lbl_val.value = f"${tot_r:,.0f}"
        self.card_total_recaudo._lbl_sub.value = f"Efectivo: ${tot_ef:,.0f} | Bancos: ${tot_tr:,.0f}"
        self.card_total_pendiente._lbl_val.value = f"${tot_p:,.0f}"
        self.card_clientes_deuda._lbl_val.value = f"{c_deuda} Clientes"

    def _on_modo_vista_change(self, e):
        if e.control.selected:
            self.modo_vista_izq = list(e.control.selected)[0]
            self._render_lista_izquierda()
            self.safe_update()

    def _render_lista_izquierda(self):
        if self.modo_vista_izq == "DOCUMENTOS":
            self._render_lista_documentos()
        else:
            self._render_lista_clientes()

    def _render_lista_clientes(self):
        self.lista_clientes_view.controls.clear()

        if not self.clientes_lista:
            self.lista_clientes_view.controls.append(
                ft.Container(
                    content=ft.Text("No se encontraron clientes", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
            return

        for cli in self.clientes_lista:
            nom = cli.get("nombre", "SIN NOMBRE")
            saldo = cli.get("saldo_pendiente", 0.0)
            facturas_cant = cli.get("cantidad_facturas", 0)
            u_fecha = cli.get("ultima_fecha_venta") or "Sin ventas"

            is_selected = (self.cliente_seleccionado and self.cliente_seleccionado.get("nombre") == nom)

            if saldo > 0.01:
                badge_bg = "#FEE2E2"
                badge_fg = "#DC2626"
                badge_txt = f"Debe ${saldo:,.0f}"
            else:
                badge_bg = "#DCFCE7"
                badge_fg = "#16A34A"
                badge_txt = "Al Día"

            item_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(nom, size=11.5, weight="bold", color=Config.COLOR_PRIMARY, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Container(
                            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_fg),
                            bgcolor=badge_bg,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=6
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text(f"{facturas_cant} facturas • Últ. venta: {u_fecha}", size=9.5, color=Config.COLOR_TEXT_MUTED),
                    ], alignment=ft.MainAxisAlignment.START)
                ], spacing=2),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                bgcolor="#EFF6FF" if is_selected else Config.COLOR_SURFACE,
                border_radius=8,
                border=ft.border.all(1.5 if is_selected else 1, Config.COLOR_PRIMARY if is_selected else Config.COLOR_BORDER),
                on_click=lambda e, c=cli: self._on_cliente_click(c),
                ink=True
            )
            self.lista_clientes_view.controls.append(item_card)

    def _render_lista_documentos(self):
        self.lista_clientes_view.controls.clear()

        if not self.documentos_lista:
            self.lista_clientes_view.controls.append(
                ft.Container(
                    content=ft.Text("No se encontraron documentos", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
            return

        for doc in self.documentos_lista:
            fac_no = str(doc.get("factura_no", "S/N"))
            t_doc = doc.get("tipo_documento", "Factura")
            cli_nom = doc.get("cliente", "SIN CLIENTE")
            fec = doc.get("fecha") or "Sin fecha"
            tot_fac = float(doc.get("total_factura") or 0.0)
            saldo = float(doc.get("saldo_pendiente") or 0.0)
            est = doc.get("estado", "PENDIENTE")

            is_selected = (
                self.documento_preseleccionado == fac_no or
                (self.cliente_seleccionado and self.cliente_seleccionado.get("nombre") == cli_nom and not self.documento_preseleccionado)
            )

            if est == "PAGADA":
                badge_bg = "#DCFCE7"
                badge_fg = "#16A34A"
                badge_txt = "PAGADA"
            elif est == "PARCIAL":
                badge_bg = "#FEF3C7"
                badge_fg = "#D97706"
                badge_txt = f"Debe ${saldo:,.0f}"
            else:
                badge_bg = "#FEE2E2"
                badge_fg = "#DC2626"
                badge_txt = f"Debe ${saldo:,.0f}"

            item_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Icon(
                                ft.icons.DESCRIPTION_ROUNDED if "REM" in t_doc.upper() else ft.icons.POINT_OF_SALE_ROUNDED,
                                size=14,
                                color=Config.COLOR_PRIMARY
                            ),
                            ft.Text(f"{t_doc} #{fac_no}", size=11.5, weight="bold", color=Config.COLOR_PRIMARY),
                        ], spacing=4),
                        ft.Container(
                            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_fg),
                            bgcolor=badge_bg,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=6
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(cli_nom, size=10.5, weight="w500", color=Config.COLOR_TEXT, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row([
                        ft.Text(f"📅 {fec} • Total: ${tot_fac:,.0f}", size=9.5, color=Config.COLOR_TEXT_MUTED),
                    ], alignment=ft.MainAxisAlignment.START)
                ], spacing=2),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                bgcolor="#EFF6FF" if is_selected else Config.COLOR_SURFACE,
                border_radius=8,
                border=ft.border.all(1.5 if is_selected else 1, Config.COLOR_PRIMARY if is_selected else Config.COLOR_BORDER),
                on_click=lambda e, d=doc: self._on_documento_click(d),
                ink=True
            )
            self.lista_clientes_view.controls.append(item_card)

    def _on_search_change(self, e):
        self.busqueda_actual = e.control.value
        self.load_data()

    def _on_chip_filtro_select(self, valor: str):
        self.chip_todos.selected = (valor == "TODOS")
        self.chip_con_deuda.selected = (valor == "CON_DEUDA")
        self.chip_al_dia.selected = (valor == "AL_DIA")
        self.filtro_saldo_actual = valor
        self.load_data()

    def _abrir_date_picker(self, e):
        if self.page:
            self.date_picker.open = True
            self.page.update()

    def _on_date_picked(self, e):
        if e.control.value:
            dt_val = e.control.value
            self.fecha_filtro = dt_val.strftime("%Y-%m-%d")
            self.lbl_fecha_filtro.value = f"{self.fecha_filtro}"
            self.chip_fecha_activa.visible = True
            self.btn_date_icon.icon_color = "amber800"
            self.load_data()

    def _limpiar_fecha(self, e):
        self.fecha_filtro = ""
        self.lbl_fecha_filtro.value = ""
        self.chip_fecha_activa.visible = False
        self.btn_date_icon.icon_color = Config.COLOR_PRIMARY
        self.load_data()


    def _on_documento_click(self, doc: dict):
        self.documento_preseleccionado = str(doc.get("factura_no"))
        cli_nom = doc.get("cliente", "")
        # Buscar cliente asociado
        cli = next((c for c in self.clientes_lista if c["nombre"] == cli_nom), None)
        if not cli:
            cli = {
                "nombre": cli_nom,
                "saldo_pendiente": doc.get("saldo_pendiente", 0.0),
                "total_facturado": doc.get("total_factura", 0.0),
                "total_abonado": doc.get("total_abonado", 0.0)
            }
        self.cliente_seleccionado = cli
        self._render_lista_izquierda()
        self._cargar_detalle_cliente(cli, recargar_datos=True)

    def _on_cliente_click(self, cli: dict):
        self.documento_preseleccionado = None
        self.cliente_seleccionado = cli
        self._render_lista_izquierda()
        self._cargar_detalle_cliente(cli, recargar_datos=True)

    def _cargar_detalle_cliente(self, cli: dict, recargar_datos: bool = True):
        nom = cli.get("nombre", "")
        saldo = cli.get("saldo_pendiente", 0.0)
        tot_fac = cli.get("total_facturado", 0.0)
        tot_ab = cli.get("total_abonado", 0.0)

        # Mostrar botones de acción en el top bar
        self.btn_pagar_global.visible = True
        self.btn_cuotas_global.visible = True

        # Header informativo del cliente con métricas compactas
        header_cliente = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.icons.ACCOUNT_CIRCLE_ROUNDED, color=Config.COLOR_PRIMARY, size=28),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY),
                    padding=6,
                    border_radius=10
                ),
                ft.Column([
                    ft.Row([
                        ft.Text(nom, size=14, weight="bold", color=Config.COLOR_PRIMARY, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                        ft.Container(
                            content=ft.Text(f"Saldo Total: ${saldo:,.0f}", size=10.5, weight="bold", color="white"),
                            bgcolor="#DC2626" if saldo > 0.01 else "#16A34A",
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            border_radius=6
                        )
                    ], spacing=8),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(f"Facturado: ${tot_fac:,.0f}", size=9.5, color=Config.COLOR_TEXT, weight="w500"),
                            bgcolor="#F1F5F9",
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=4
                        ),
                        ft.Container(
                            content=ft.Text(f"Abonado: ${tot_ab:,.0f}", size=9.5, color="#15803D", weight="bold"),
                            bgcolor="#DCFCE7",
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=4
                        ),
                        ft.Container(
                            content=ft.Text(f"Pendiente: ${saldo:,.0f}", size=9.5, color="#B91C1C" if saldo > 0.01 else "#15803D", weight="bold"),
                            bgcolor="#FEE2E2" if saldo > 0.01 else "#DCFCE7",
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=4
                        )
                    ], spacing=6)
                ], spacing=3, expand=True)
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=Config.COLOR_SURFACE,
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=10
        )


        # Tab Bar Compacto
        self.tabs_detalle = ft.Tabs(
            selected_index=self.tab_activo,
            animation_duration=150,
            height=40,
            tabs=[
                ft.Tab(text="Facturas (Remisiones & POS)", icon=ft.icons.RECEIPT_LONG_ROUNDED),
                ft.Tab(text="Historial de Pagos", icon=ft.icons.HISTORY_ROUNDED),
                ft.Tab(text="Plan de Cuotas", icon=ft.icons.EVENT_NOTE_ROUNDED)
            ],
            on_change=self._on_tab_change
        )

        self.tab_content_container = ft.Container(
            content=self._crear_loading_indicador(f"Cargando información de {nom}...") if recargar_datos else None,
            expand=True,
            padding=ft.padding.only(top=4)
        )

        self.panel_derecho_contenido.content = ft.Column([
            header_cliente,
            self.tabs_detalle,
            self.tab_content_container
        ], expand=True, spacing=6)

        # Actualizar pantalla INMEDIATAMENTE para que aparezca el panel del cliente
        self.safe_update()

        if recargar_datos:
            self._recargar_subdatos_cliente(nom, saldo)
        else:
            self._render_tab_activo()
            self.safe_update()

    def _on_tab_change(self, e):
        self.tab_activo = e.control.selected_index
        self._render_tab_activo()
        self.safe_update()

    def _recargar_subdatos_cliente(self, nombre_cliente: str, saldo_actual: float = 0.0):
        self._is_loading_subdatos = True
        self.tab_content_container.content = self._crear_loading_indicador(f"Cargando facturas y pagos de {nombre_cliente}...")
        self.safe_update()

        def worker():
            try:
                self.facturas_cliente = self.cartera_repo.get_facturas_cliente(nombre_cliente)
                self.historial_pagos = self.cartera_repo.get_historial_pagos_cliente(nombre_cliente)
                self.cuotas_cliente = self.cartera_repo.get_cuotas_cliente(nombre_cliente, saldo_actual_cliente=saldo_actual)
            except Exception as ex:
                log_error("CarteraView._recargar_subdatos_cliente", ex)
            finally:
                self._is_loading_subdatos = False
                self._render_tab_activo()
                self.safe_update()

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def _render_tab_activo(self):
        if self._is_loading_subdatos:
            nom = self.cliente_seleccionado.get("nombre", "") if self.cliente_seleccionado else ""
            self.tab_content_container.content = self._crear_loading_indicador(f"Cargando datos de {nom}...")
            return

        if self.tab_activo == 0:
            self._render_tab_facturas()
        elif self.tab_activo == 1:
            self._render_tab_historial_pagos()
        elif self.tab_activo == 2:
            self._render_tab_cuotas()

    def _render_tab_facturas(self):
        if not self.facturas_cliente:
            self.tab_content_container.content = ft.Container(
                content=ft.Text("Este cliente no tiene facturas registradas.", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
                alignment=ft.alignment.center,
                padding=20
            )
            return

        dt = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Tipo Doc.", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Factura No.", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Total Factura", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Total Abonado", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Saldo Pendiente", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Estado", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Acciones", size=11, weight="bold")),
            ],
            rows=[],
            heading_row_height=30,
            data_row_min_height=28,
            data_row_max_height=32,
            column_spacing=12,
            heading_row_color=Config.COLOR_MUTED
        )

        for f in self.facturas_cliente:
            fac_no = str(f.get("factura_no", ""))
            est = f.get("estado_factura", "PENDIENTE")
            saldo_f = float(f.get("saldo_pendiente", 0.0))
            if est == "PAGADA":
                b_bg, b_fg, b_tx = "#DCFCE7", "#16A34A", "PAGADA"
            elif est == "PARCIAL":
                b_bg, b_fg, b_tx = "#FEF3C7", "#D97706", "PARCIAL"
            else:
                b_bg, b_fg, b_tx = "#FEE2E2", "#DC2626", "PENDIENTE"

            btn_pagar_linea = ft.IconButton(
                icon=ft.icons.PAYMENTS_ROUNDED,
                icon_color=Config.COLOR_SUCCESS,
                icon_size=16,
                tooltip=f"Registrar pago para #{fac_no}",
                on_click=lambda e, fno=fac_no: self._abrir_modal_pago(self.cliente_seleccionado, doc_preseleccionado=fno)
            ) if saldo_f > 0.01 else ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=Config.COLOR_SUCCESS, size=16)

            dt.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f.get("fecha", ""), size=11)),
                    ft.DataCell(ft.Text(f.get("tipo_documento", "POS"), size=11)),
                    ft.DataCell(ft.Text(fac_no, size=11, weight="bold")),
                    ft.DataCell(ft.Text(f"${f.get('total_factura', 0.0):,.0f}", size=11)),
                    ft.DataCell(ft.Text(f"${f.get('total_abonado', 0.0):,.0f}", size=11, color=Config.COLOR_SUCCESS)),
                    ft.DataCell(ft.Text(f"${saldo_f:,.0f}", size=11, weight="bold", color="#DC2626" if saldo_f > 0 else "grey")),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(b_tx, size=9, weight="bold", color=b_fg),
                            bgcolor=b_bg,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=6
                        )
                    ),
                    ft.DataCell(btn_pagar_linea)
                ])
            )

        self.tab_content_container.content = ft.ListView(
            controls=[dt],
            expand=True
        )

    def _render_tab_historial_pagos(self):
        if not self.historial_pagos:
            self.tab_content_container.content = ft.Container(
                content=ft.Text("No hay pagos registrados para este cliente.", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
                alignment=ft.alignment.center,
                padding=20
            )
            return

        dt = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Monto Recaudado", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Medio de Pago", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Banco / Ref", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Facturas Afectadas", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Usuario", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Acciones", size=11, weight="bold")),
            ],
            rows=[],
            heading_row_height=30,
            data_row_min_height=30,
            data_row_max_height=34,
            column_spacing=12,
            heading_row_color=Config.COLOR_MUTED
        )

        for p in self.historial_pagos:
            p_id = p.get("id_pago")
            f_afectadas = p.get("facturas_afectadas", [])
            facs_str = ", ".join([f"#{d.get('factura_no')} (${float(d.get('monto_aplicado',0)):,.0f})" for d in f_afectadas]) if f_afectadas else "Global (FIFO)"
            metodo = p.get("metodo_pago", "EFECTIVO")
            banco_ref = f"{p.get('banco_origen') or ''} {p.get('referencia_comprobante') or ''}".strip() or "-"

            btn_anular = ft.IconButton(
                icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                icon_color="red400",
                icon_size=16,
                tooltip="Anular Recaudo",
                on_click=lambda e, pid=p_id: self._confirmar_anular_pago(pid)
            )

            dt.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p.get("fecha_formateada", ""), size=11)),
                    ft.DataCell(ft.Text(f"${p.get('monto_total', 0.0):,.0f}", size=11, weight="bold", color=Config.COLOR_SUCCESS)),
                    ft.DataCell(ft.Text(metodo, size=11)),
                    ft.DataCell(ft.Text(banco_ref, size=11)),
                    ft.DataCell(ft.Text(facs_str[:40], size=10, tooltip=facs_str)),
                    ft.DataCell(ft.Text(p.get("usuario_registro") or "admin", size=10, color=Config.COLOR_TEXT_MUTED)),
                    ft.DataCell(btn_anular)
                ])
            )

        self.tab_content_container.content = ft.ListView(
            controls=[dt],
            expand=True
        )

    def _render_tab_cuotas(self):
        if not self.cuotas_cliente:
            self.tab_content_container.content = ft.Container(
                content=ft.Column([
                    ft.Text("No hay cronograma de cuotas activo para este cliente.", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
                    ft.ElevatedButton(
                        "Crear Plan de Cuotas",
                        icon=ft.icons.ADD_ROUNDED,
                        bgcolor=Config.COLOR_PRIMARY,
                        color="white",
                        height=30,
                        on_click=lambda e: self._abrir_modal_cuotas(self.cliente_seleccionado)
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                alignment=ft.alignment.center,
                padding=20
            )
            return

        dt = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Cuota", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Fecha Cobro Sugerida", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Valor Cuota", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Abonado", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Saldo Cuota", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Estado", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Observación", size=11, weight="bold")),
            ],
            rows=[],
            heading_row_height=30,
            data_row_min_height=28,
            data_row_max_height=32,
            column_spacing=14,
            heading_row_color=Config.COLOR_MUTED
        )

        for c in self.cuotas_cliente:
            num = c.get("numero_cuota", 1)
            tot = c.get("total_cuotas", 1)
            est = c.get("estado", "PENDIENTE")
            m_cuota = float(c.get("monto_cuota") or 0.0)
            m_abono = float(c.get("monto_abonado") or 0.0)
            s_cuota = float(c.get("saldo_cuota", m_cuota - m_abono))

            if est == "COBRADO":
                badge_bg = "#DCFCE7"
                badge_fg = "#16A34A"
                badge_txt = "COBRADA"
            elif est == "PARCIAL":
                badge_bg = "#FEF3C7"
                badge_fg = "#D97706"
                badge_txt = "PARCIAL"
            else:
                badge_bg = "#FEE2E2"
                badge_fg = "#DC2626"
                badge_txt = "PENDIENTE"

            dt.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"{num} de {tot}", size=11, weight="bold")),
                    ft.DataCell(ft.Text(c.get("fecha_cobro", ""), size=11, color=Config.COLOR_ACCENT, weight="w500")),
                    ft.DataCell(ft.Text(f"${m_cuota:,.0f}", size=11, weight="bold")),
                    ft.DataCell(ft.Text(f"${m_abono:,.0f}", size=11, color=Config.COLOR_SUCCESS)),
                    ft.DataCell(ft.Text(f"${s_cuota:,.0f}", size=11, weight="bold", color="#DC2626" if s_cuota > 0 else "grey")),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_fg),
                            bgcolor=badge_bg,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=6
                        )
                    ),
                    ft.DataCell(ft.Text(c.get("observacion") or "-", size=10, color=Config.COLOR_TEXT_MUTED))
                ])
            )

        self.tab_content_container.content = ft.ListView(
            controls=[dt],
            expand=True
        )

    # ==========================================
    # MODAL: REGISTRAR PAGO / ABONO
    # ==========================================
    def _abrir_modal_pago(self, cli: dict, doc_preseleccionado: str | None = None):
        if not cli:
            return

        nom = cli.get("nombre", "")
        saldo_cliente = float(cli.get("saldo_pendiente", 0.0))

        # Facturas del cliente para construir opciones del dropdown
        facturas = self.facturas_cliente or self.cartera_repo.get_facturas_cliente(nom)
        facturas_pendientes = [f for f in facturas if float(f.get("saldo_pendiente", 0.0)) > 0.01]

        dd_doc_options = [
            ft.dropdown.Option("TODAS", "Todas las facturas (Distribución FIFO Automática)")
        ]
        doc_saldo_map: dict[str, float] = {}

        for f in facturas_pendientes:
            f_no = str(f.get("factura_no"))
            t_doc = f.get("tipo_documento", "Doc")
            s_f = float(f.get("saldo_pendiente", 0.0))
            tot_f = float(f.get("total_factura", 0.0))
            doc_saldo_map[f_no] = s_f
            dd_doc_options.append(
                ft.dropdown.Option(
                    f_no,
                    f"{t_doc} #{f_no} — Saldo: ${s_f:,.0f} (Total: ${tot_f:,.0f})"
                )
            )

        # Preselección si se seleccionó previamente un documento
        target_doc = doc_preseleccionado or self.documento_preseleccionado
        doc_inicial = "TODAS"
        monto_inicial = saldo_cliente

        if target_doc and target_doc in doc_saldo_map:
            doc_inicial = target_doc
            monto_inicial = doc_saldo_map[target_doc]

        txt_monto = ft.TextField(
            label="Monto a Recaudar (COP)",
            value=f"{int(monto_inicial)}" if monto_inicial > 0 else "",
            text_size=13,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        def on_doc_change(e):
            val = dd_documento.value
            if val == "TODAS":
                txt_monto.value = f"{int(saldo_cliente)}" if saldo_cliente > 0 else ""
            elif val in doc_saldo_map:
                txt_monto.value = f"{int(doc_saldo_map[val])}"
            if self.page:
                self.page.update()

        dd_documento = ft.Dropdown(
            label="Documento a Pagar / Imputar",
            value=doc_inicial,
            options=dd_doc_options,
            dense=True,
            text_size=11.5,
            on_change=on_doc_change
        )

        dd_metodo = ft.Dropdown(
            label="Método de Pago",
            value="EFECTIVO",
            options=[
                ft.dropdown.Option("EFECTIVO", "Efectivo"),
                ft.dropdown.Option("TRANSFERENCIA", "Transferencia Bancaria"),
            ],
            dense=True,
            text_size=12
        )

        dd_banco = ft.Dropdown(
            label="Banco / Entidad (Colombia)",
            value="Bancolombia",
            options=[
                ft.dropdown.Option("Bancolombia", "Bancolombia"),
                ft.dropdown.Option("Nequi", "Nequi"),
                ft.dropdown.Option("Daviplata", "Daviplata"),
                ft.dropdown.Option("Davivienda", "Davivienda"),
                ft.dropdown.Option("BBVA", "BBVA Colombia"),
                ft.dropdown.Option("Banco de Bogotá", "Banco de Bogotá"),
                ft.dropdown.Option("Scotiabank Colpatria", "Scotiabank Colpatria"),
                ft.dropdown.Option("Dale", "Dale!"),
                ft.dropdown.Option("Otro", "Otro Banco"),
            ],
            dense=True,
            text_size=12,
            visible=False
        )

        txt_ref = ft.TextField(
            label="Comprobante / Referencia",
            hint_text="No. transacción o recibo",
            text_size=12,
            dense=True,
            visible=False
        )

        txt_obs = ft.TextField(
            label="Observaciones",
            hint_text="Notas opcionales del pago",
            text_size=12,
            dense=True
        )

        def on_metodo_change(e):
            is_transf = (dd_metodo.value == "TRANSFERENCIA")
            dd_banco.visible = is_transf
            txt_ref.visible = is_transf
            if self.page:
                self.page.update()

        dd_metodo.on_change = on_metodo_change

        def guardar_pago(e):
            try:
                monto_val = float(str(txt_monto.value or "").replace("$", "").replace(".", "").replace(",", ".").strip())
                if monto_val <= 0:
                    self._mostrar_snackbar("El monto debe ser mayor a 0", "red")
                    return

                # Si seleccionó un documento específico, imputar a ese documento
                facturas_seleccionadas = None
                if dd_documento.value and dd_documento.value != "TODAS":
                    facturas_seleccionadas = {dd_documento.value: monto_val}

                ok = self.cartera_repo.registrar_pago_cartera(
                    id_cliente=cli.get("id_cliente"),
                    nombre_cliente=nom,
                    monto_total=monto_val,
                    metodo_pago=dd_metodo.value,
                    banco_origen=dd_banco.value if dd_metodo.value == "TRANSFERENCIA" else None,
                    referencia=txt_ref.value or "",
                    observaciones=txt_obs.value or "",
                    facturas_seleccionadas=facturas_seleccionadas,
                    usuario="admin"
                )

                if ok:
                    dlg.open = False
                    doc_msg = f" a {dd_documento.value}" if (dd_documento.value and dd_documento.value != "TODAS") else ""
                    self._mostrar_snackbar(f"✓ Recaudo de ${monto_val:,.0f}{doc_msg} registrado con éxito.", "green")
                    self.load_data()
                else:
                    self._mostrar_snackbar("Error registrando pago en base de datos.", "red")
            except Exception as ex:
                self._mostrar_snackbar(f"Error: {ex}", "red")

        dlg = ft.AlertDialog(
            title=ft.Text(f"Registrar Recaudo: {nom}", size=15, weight="bold", color=Config.COLOR_PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Saldo Pendiente Total: ${saldo_cliente:,.0f}", size=11.5, weight="bold", color="#DC2626" if saldo_cliente > 0 else "grey"),
                    dd_documento,
                    txt_monto,
                    dd_metodo,
                    dd_banco,
                    txt_ref,
                    txt_obs
                ], spacing=10, tight=True),
                width=420
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal(dlg)),
                ft.ElevatedButton("Confirmar Recaudo", bgcolor=Config.COLOR_SUCCESS, color="white", on_click=guardar_pago)
            ]
        )

        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    # ==========================================
    # MODAL: CREAR PLAN DE CUOTAS
    # ==========================================
    def _abrir_modal_cuotas(self, cli: dict):
        if not cli:
            return

        nom = cli.get("nombre", "")
        saldo = cli.get("saldo_pendiente", 0.0)

        txt_saldo = ft.TextField(
            label="Saldo a Diferir (COP)",
            value=f"{int(saldo)}" if saldo > 0 else "",
            text_size=12,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        dd_cuotas = ft.Dropdown(
            label="Número de Cuotas",
            value="3",
            options=[ft.dropdown.Option(str(i), f"{i} Cuotas") for i in range(2, 13)],
            dense=True,
            text_size=12
        )

        dd_periodo = ft.Dropdown(
            label="Periodicidad",
            value="QUINCENAL",
            options=[
                ft.dropdown.Option("SEMANAL", "Semanal (Cada 7 días)"),
                ft.dropdown.Option("QUINCENAL", "Quincenal (Cada 15 días)"),
                ft.dropdown.Option("MENSUAL", "Mensual (Cada 30 días)"),
            ],
            dense=True,
            text_size=12
        )

        lbl_simulacion = ft.Text("Cálculo estimado: ...", size=10.5, color=Config.COLOR_PRIMARY, weight="w500")

        def actualizar_simulacion(e=None):
            try:
                s_val = float(str(txt_saldo.value or "").replace("$", "").replace(".", "").replace(",", ".").strip())
                n_c = int(dd_cuotas.value)
                val_c = s_val / n_c
                lbl_simulacion.value = f"→ {n_c} cuotas de ${val_c:,.0f} ({dd_periodo.value.lower()})"
            except Exception:
                lbl_simulacion.value = "Ingresa un saldo válido."
            if self.page:
                self.page.update()

        txt_saldo.on_change = actualizar_simulacion
        dd_cuotas.on_change = actualizar_simulacion
        dd_periodo.on_change = actualizar_simulacion
        actualizar_simulacion()

        def guardar_plan(e):
            try:
                s_val = float(str(txt_saldo.value or "").replace("$", "").replace(".", "").replace(",", ".").strip())
                if s_val <= 0:
                    self._mostrar_snackbar("El saldo debe ser mayor a 0", "red")
                    return

                ok = self.cartera_repo.crear_plan_cuotas(
                    id_cliente=cli.get("id_cliente"),
                    nombre_cliente=nom,
                    saldo_a_diferir=s_val,
                    num_cuotas=int(dd_cuotas.value),
                    periodicidad=dd_periodo.value
                )

                if ok:
                    dlg.open = False
                    self._mostrar_snackbar("✓ Plan de cuotas acordado exitosamente.", "green")
                    self.tab_activo = 2
                    self.load_data()
                else:
                    self._mostrar_snackbar("Error guardando plan de cuotas.", "red")
            except Exception as ex:
                self._mostrar_snackbar(f"Error: {ex}", "red")

        dlg = ft.AlertDialog(
            title=ft.Text(f"Plan de Cuotas: {nom}", size=15, weight="bold", color=Config.COLOR_PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Acuerda fechas de cobro y montos divididos para el saldo del cliente:", size=11, color=Config.COLOR_TEXT_MUTED),
                    txt_saldo,
                    dd_cuotas,
                    dd_periodo,
                    lbl_simulacion
                ], spacing=8, tight=True),
                width=360
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal(dlg)),
                ft.ElevatedButton("Guardar Cronograma", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=guardar_plan)
            ]
        )

        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _confirmar_anular_pago(self, id_pago: str):
        def anular(e):
            dlg.open = False
            ok = self.cartera_repo.anular_pago_cartera(id_pago)
            if ok:
                self._mostrar_snackbar("✓ Recaudo anulado exitosamente.", "orange800")
                self.load_data()
            else:
                self._mostrar_snackbar("Error anulando recaudo.", "red")

        dlg = ft.AlertDialog(
            title=ft.Text("¿Anular Recaudo?", size=15, weight="bold", color="red800"),
            content=ft.Text("Esta acción revertirá el pago y restaurará los saldos adeudados en las facturas.", size=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal(dlg)),
                ft.ElevatedButton("Sí, Anular Pago", bgcolor="red800", color="white", on_click=anular)
            ]
        )

        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _cerrar_modal(self, dlg):
        dlg.open = False
        if self.page:
            self.page.update()

    def _mostrar_snackbar(self, msg: str, color: str = "green"):
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(msg, weight="bold", color="white"),
                bgcolor=color,
                duration=3500
            )
            self.page.snack_bar.open = True
            self.page.update()
