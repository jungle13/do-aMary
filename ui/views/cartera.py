"""
Vista de Gestión de Cartera y Cuentas por Cobrar para Sistema Doña Mary.
Permite consultar estados de cuenta por cliente, registrar pagos/abonos (FIFO o manual),
diferir deudas en cuotas con amortización automática, buscar por cliente o documento y filtrar por fecha.
"""
import datetime
import os
import tempfile
import flet as ft
from fpdf import FPDF
from config import Config
from core.database import BaseDatabase
from core.logger import get_logger, log_error
from core.supabase_client import get_client
from ui.components.periodo_selector import PeriodoSelectorWidget

logger = get_logger("CarteraView")

def clean_fpdf_str(txt: str) -> str:
    if not txt:
        return ""
    txt = str(txt).replace("•", "-").replace("✦", "*").replace("✓", "V").replace("—", "-").replace("º", "o").replace("ª", "a")
    return txt.encode("latin-1", "replace").decode("latin-1")

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
        self.todos_clientes = []
        self.todos_documentos = []
        self.todos_encargados = []
        self.clientes_lista = []
        self.documentos_lista = []
        self.encargados_lista = []
        self.cliente_seleccionado = None
        self.documento_preseleccionado = None
        self.modo_vista_izq = "CLIENTES"
        self.facturas_cliente = []
        self.historial_pagos = []
        self.cuotas_cliente = []
        self.filtro_saldo_actual = "TODOS"
        self.filtro_tipo_doc_actual = "TODOS"
        self.busqueda_actual = ""
        self.fecha_filtro = ""
        self.filtros_expandidos = True
        self.panel_cliente_expandido = False
        self.mostrar_plan_cuotas = False  # Alternar a True cuando se desee habilitar el módulo de cuotas
        self.tab_activo = 0
        self.encargado_seleccionado = None
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

        # 2. Panel Izquierdo: Rediseño Modular con Minimódulo de Filtros Colapsable
        self.seg_modo_vista = ft.SegmentedButton(
            selected={"CLIENTES"},
            allow_multiple_selection=False,
            segments=[
                ft.Segment(
                    value="CLIENTES",
                    label=ft.Text("Clientes", size=11, weight="w600")
                ),
                ft.Segment(
                    value="DOCUMENTOS",
                    label=ft.Text("Documentos", size=11, weight="w600")
                ),
                ft.Segment(
                    value="ENCARGADOS",
                    label=ft.Text("Encargados", size=11, weight="w600")
                ),
            ],
            height=32,
            expand=True,
            show_selected_icon=False,
            on_change=self._on_modo_vista_change
        )

        self.btn_toggle_filtros = ft.IconButton(
            icon=ft.icons.TUNE_ROUNDED,
            icon_size=17,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Ocultar / Mostrar filtros avanzados",
            bgcolor=ft.colors.with_opacity(0.08, Config.COLOR_PRIMARY),
            width=32,
            height=32,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=0),
            on_click=self._toggle_filtros
        )

        # Chips de Estado
        self.chip_todos = ft.Chip(
            label=ft.Text("Todos", size=9.5),
            selected=True,
            on_select=lambda e: self._on_chip_filtro_select("TODOS")
        )
        self.chip_con_deuda = ft.Chip(
            label=ft.Text("Con Deuda", size=9.5),
            selected=False,
            on_select=lambda e: self._on_chip_filtro_select("CON_DEUDA")
        )
        self.chip_al_dia = ft.Chip(
            label=ft.Text("Al Día", size=9.5),
            selected=False,
            on_select=lambda e: self._on_chip_filtro_select("AL_DIA")
        )

        # Chips de Tipo de Documento
        self.chip_tipo_todos = ft.Chip(
            label=ft.Text("Todos", size=9.5),
            selected=True,
            on_select=lambda e: self._on_chip_tipo_select("TODOS")
        )
        self.chip_tipo_remision = ft.Chip(
            label=ft.Text("Remisión", size=9.5),
            selected=False,
            on_select=lambda e: self._on_chip_tipo_select("REMISIÓN")
        )
        self.chip_tipo_pos = ft.Chip(
            label=ft.Text("Factura POS", size=9.5),
            selected=False,
            on_select=lambda e: self._on_chip_tipo_select("FACTURA_POS")
        )

        # Filtro de Fecha
        self.date_picker = ft.DatePicker(
            on_change=self._on_date_picked,
            help_text="Seleccionar fecha de factura"
        )

        self.btn_date_icon = ft.OutlinedButton(
            text="Elegir fecha",
            icon=ft.icons.CALENDAR_MONTH_ROUNDED,
            height=28,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=8, vertical=2)
            ),
            on_click=self._abrir_date_picker
        )

        self.lbl_fecha_filtro = ft.Text("", size=9.5, weight="bold", color=Config.COLOR_PRIMARY)
        self.btn_limpiar_fecha = ft.IconButton(
            icon=ft.icons.CLOSE_ROUNDED,
            icon_size=12,
            icon_color="red600",
            tooltip="Quitar filtro de fecha",
            width=18,
            height=18,
            style=ft.ButtonStyle(padding=0),
            on_click=self._limpiar_fecha
        )

        self.chip_fecha_activa = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.EVENT_ROUNDED, size=11, color=Config.COLOR_PRIMARY),
                self.lbl_fecha_filtro,
                self.btn_limpiar_fecha
            ], spacing=2, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.colors.with_opacity(0.12, Config.COLOR_PRIMARY),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=10,
            visible=False
        )

        # Minimódulo de Filtros (Organizado en hileras con su propio fondo)
        self.contenedor_filtros = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Estado:", size=9.5, weight="bold", color="grey700", width=42),
                    self.chip_todos,
                    self.chip_con_deuda,
                    self.chip_al_dia
                ], spacing=3, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Text("Tipo:", size=9.5, weight="bold", color="grey700", width=42),
                    self.chip_tipo_todos,
                    self.chip_tipo_remision,
                    self.chip_tipo_pos
                ], spacing=3, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Text("Fecha:", size=9.5, weight="bold", color="grey700", width=42),
                    self.btn_date_icon,
                    self.chip_fecha_activa
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=4),
            bgcolor="#F8FAFC",
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            visible=True
        )

        # Buscador en fila completa debajo del minimódulo de filtros
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

        self.lista_clientes_view = ft.ListView(
            expand=True,
            spacing=6,
            padding=ft.padding.only(right=2)
        )

        self.col_izquierda = ft.Container(
            content=ft.Column([
                ft.Row([self.seg_modo_vista, self.btn_toggle_filtros], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.contenedor_filtros,
                ft.Row([self.txt_buscador], expand=False),
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
        self.btn_informe_global = ft.ElevatedButton(
            text="Generar Informe",
            icon=ft.icons.ASSESSMENT_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=34,
            visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=lambda e: self._abrir_modal_informe_facturas(self.cliente_seleccionado)
        )
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
        self.periodo_selector = PeriodoSelectorWidget(on_change_callback=self.on_periodo_change, page=self.page)
        self.content = ft.Column([
            ft.Row([
                ft.Column([self.lbl_titulo, self.lbl_subtitulo], spacing=2),
                ft.Container(expand=True),
                self.periodo_selector,
                self.btn_informe_global,
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
        lbl_titulo = ft.Text(titulo, size=10.5, color=Config.COLOR_TEXT_MUTED, weight="w500")
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
                    lbl_titulo,
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
        card._lbl_titulo = lbl_titulo
        card._lbl_val = lbl_val
        card._lbl_sub = lbl_sub
        return card

    def _crear_placeholder_vacio(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, size=48, color=Config.COLOR_TEXT_LIGHT),
                ft.Text("Selecciona un cliente de la lista", size=15, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Consulta sus facturas pendientes, historial de abonos y asignación de vendedor.", size=11, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER)
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

    def on_periodo_change(self, nuevo_periodo: str):
        self.load_data()

    def _aplicar_filtros_locales(self):
        """Filtra en memoria clientes, documentos y encargados de forma instantánea sin latencia."""
        s_upper = (self.busqueda_actual or "").strip().upper()
        f_saldo = self.filtro_saldo_actual
        f_tipo = self.filtro_tipo_doc_actual
        f_fecha = self.fecha_filtro

        # 1. Filtrar Clientes
        clis = []
        for c in (self.todos_clientes or []):
            nom = (c.get("nombre") or "").upper()
            tel = (c.get("telefono") or "").upper()
            vend = (c.get("vendedor_encargado") or "").upper()
            facs = [str(f).upper() for f in (c.get("facturas_list") or [])]
            saldo = float(c.get("saldo_pendiente") or 0.0)

            # Filtro Saldo
            if f_saldo == "CON_DEUDA" and saldo <= 0.01:
                continue
            if f_saldo == "AL_DIA" and saldo > 0.01:
                continue

            # Filtro Búsqueda: nombre, teléfono, vendedor o cualquiera de sus números de factura/remisión
            if s_upper:
                coincide = (s_upper in nom) or (s_upper in tel) or (s_upper in vend) or any(s_upper in f for f in facs)
                if not coincide:
                    continue

            clis.append(c)
        self.clientes_lista = clis

        # 2. Filtrar Documentos
        docs = []
        for d in (self.todos_documentos or []):
            fac = str(d.get("factura_no") or "").upper()
            cli = (d.get("cliente") or "").upper()
            t_doc = (d.get("tipo_documento") or "").upper()
            fec = (d.get("fecha") or "")
            saldo = float(d.get("saldo_pendiente") or 0.0)

            # Filtro Saldo
            if f_saldo == "CON_DEUDA" and saldo <= 0.01:
                continue
            if f_saldo == "AL_DIA" and saldo > 0.01:
                continue

            # Filtro Tipo Doc
            if f_tipo == "REMISIÓN" and "REM" not in t_doc:
                continue
            if f_tipo in ("FACTURA_POS", "POS") and "POS" not in t_doc:
                continue

            # Filtro Fecha
            if f_fecha and fec != f_fecha:
                continue

            # Filtro Búsqueda: No. de factura, nombre del cliente o tipo de documento
            if s_upper:
                coincide = (s_upper in fac) or (s_upper in cli) or (s_upper in t_doc)
                if not coincide:
                    continue

            docs.append(d)
        self.documentos_lista = docs

        # 3. Filtrar Encargados
        encs = []
        for e in (self.todos_encargados or []):
            nom = (e.get("nombre") or "").upper()
            tel = (e.get("telefono") or "").upper()
            if s_upper:
                if not (s_upper in nom or s_upper in tel):
                    continue
            encs.append(e)
        self.encargados_lista = encs

    def load_data(self):
        """Carga en segundo plano los KPIs, la lista de clientes y la lista de documentos."""
        if self._is_loading:
            return
        self._is_loading = True

        def worker():
            try:
                # Una sola llamada que descarga ventas una vez y calcula KPIs + clientes + documentos
                periodo_activo = self.periodo_selector.get_periodo_actual() if hasattr(self, "periodo_selector") else None
                kpis, clientes, documentos = self.cartera_repo.get_resumen_cartera(
                    search="",
                    filtro_saldo="TODOS",
                    fecha_filtro="",
                    filtro_tipo_doc="TODOS",
                    mes_periodo=periodo_activo
                )
                self.kpis_data = kpis
                self.todos_clientes = clientes
                self.todos_documentos = documentos
                self.todos_encargados = self.clientes_repo.get_encargados_completos(mes_periodo=periodo_activo)

                # Aplicar filtros locales activos (búsqueda, chips, fechas)
                self._aplicar_filtros_locales()

                # Actualizar UI
                self._actualizar_kpis_ui()
                self._render_lista_izquierda()

                if self.modo_vista_izq == "ENCARGADOS" and self.encargado_seleccionado:
                    id_sel = self.encargado_seleccionado.get("id_encargado")
                    e_upd = next((e for e in self.todos_encargados if e.get("id_encargado") == id_sel), None)
                    if e_upd:
                        self._cargar_detalle_encargado(e_upd)
                    elif self.todos_encargados:
                        self._cargar_detalle_encargado(self.todos_encargados[0])
                    else:
                        self.panel_derecho_contenido.content = self._crear_placeholder_vacio()

                elif self.cliente_seleccionado:
                    nom_sel = self.cliente_seleccionado.get("nombre")
                    c_upd = next((c for c in self.todos_clientes if c["nombre"] == nom_sel), None)
                    if c_upd:
                        self.cliente_seleccionado = c_upd
                        self._cargar_detalle_cliente(c_upd, recargar_datos=True)
                    else:
                        self.cliente_seleccionado = None
                        self.btn_pagar_global.visible = False
                        self.btn_cuotas_global.visible = False
                        self.btn_informe_global.visible = False
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
        rec_pos = k.get("recaudado_pos", 0.0)
        rec_rem = k.get("recaudado_remision", 0.0)

        mes_activo = self.periodo_selector.get_periodo_actual() if hasattr(self, "periodo_selector") else None

        if hasattr(self.card_total_ventas, "_lbl_titulo"):
            self.card_total_ventas._lbl_titulo.value = f"Facturado ({mes_activo})" if mes_activo else "Total Facturado"
        self.card_total_ventas._lbl_val.value = f"${tot_v:,.0f}"
        if hasattr(self.card_total_ventas, "_lbl_sub"):
            self.card_total_ventas._lbl_sub.value = f"Ventas del mes {mes_activo}" if mes_activo else "Histórico"
            self.card_total_ventas._lbl_sub.visible = True

        if hasattr(self.card_total_recaudo, "_lbl_titulo"):
            self.card_total_recaudo._lbl_titulo.value = f"Recaudado ({mes_activo})" if mes_activo else "Total Recaudado"
        self.card_total_recaudo._lbl_val.value = f"${tot_r:,.0f}"
        if hasattr(self.card_total_recaudo, "_lbl_sub"):
            if rec_pos > 0 and rec_rem > 0:
                self.card_total_recaudo._lbl_sub.value = f"POS: ${rec_pos:,.0f} • Remi: ${rec_rem:,.0f}"
            elif rec_rem > 0:
                self.card_total_recaudo._lbl_sub.value = f"Abonos Remisiones: ${rec_rem:,.0f}"
            elif rec_pos > 0:
                self.card_total_recaudo._lbl_sub.value = f"POS Contado: ${rec_pos:,.0f}"
            else:
                self.card_total_recaudo._lbl_sub.value = f"Efectivo: ${tot_ef:,.0f} | Bancos: ${tot_tr:,.0f}"
            self.card_total_recaudo._lbl_sub.visible = True

        if hasattr(self.card_total_pendiente, "_lbl_titulo"):
            self.card_total_pendiente._lbl_titulo.value = "Saldo Total por Cobrar"
        self.card_total_pendiente._lbl_val.value = f"${tot_p:,.0f}"
        if hasattr(self.card_total_pendiente, "_lbl_sub"):
            self.card_total_pendiente._lbl_sub.value = "Cartera pendiente acumulada"
            self.card_total_pendiente._lbl_sub.visible = True

        if hasattr(self.card_clientes_deuda, "_lbl_titulo"):
            self.card_clientes_deuda._lbl_titulo.value = "Clientes con Deuda"
        self.card_clientes_deuda._lbl_val.value = f"{c_deuda} Clientes"
        if hasattr(self.card_clientes_deuda, "_lbl_sub"):
            self.card_clientes_deuda._lbl_sub.value = "Con saldo pendiente activo"
            self.card_clientes_deuda._lbl_sub.visible = True

    def _on_modo_vista_change(self, e):
        if e.control.selected:
            self.modo_vista_izq = list(e.control.selected)[0]
            self._render_lista_izquierda()
            if self.modo_vista_izq == "ENCARGADOS":
                if not self.encargado_seleccionado and self.encargados_lista:
                    self._cargar_detalle_encargado(self.encargados_lista[0])
                elif not self.encargados_lista:
                    self.panel_derecho_contenido.content = self._crear_placeholder_vacio()
            self.safe_update()

    def _render_lista_izquierda(self):
        if self.modo_vista_izq == "DOCUMENTOS":
            self._render_lista_documentos()
        elif self.modo_vista_izq == "ENCARGADOS":
            self._render_lista_encargados()
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

            vend_nom = cli.get("vendedor_encargado") or ""
            row_sub = [
                ft.Text(f"{facturas_cant} facturas • Últ. venta: {u_fecha}", size=9.5, color=Config.COLOR_TEXT_MUTED, expand=True)
            ]
            if vend_nom:
                row_sub.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.BADGE_OUTLINED, size=10, color="purple700"),
                            ft.Text(vend_nom, size=9, weight="w600", color="purple800", overflow=ft.TextOverflow.ELLIPSIS)
                        ], spacing=2, tight=True),
                        bgcolor="#F5F3FF",
                        padding=ft.padding.symmetric(horizontal=4, vertical=1),
                        border_radius=4
                    )
                )

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
                    ft.Row(row_sub, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
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

    def _render_lista_encargados(self):
        self.lista_clientes_view.controls.clear()

        # Botón superior para crear nuevo encargado
        btn_nuevo_encargado = ft.ElevatedButton(
            "Nuevo",
            icon=ft.icons.PERSON_ADD_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=30,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=10, vertical=4)
            ),
            on_click=lambda e: self._abrir_modal_crear_encargado()
        )

        header_encargados = ft.Container(
            content=ft.Row([
                ft.Text(f"{len(self.encargados_lista)} Encargados", size=11.5, weight="bold", color=Config.COLOR_PRIMARY),
                btn_nuevo_encargado
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=6, vertical=4)
        )
        self.lista_clientes_view.controls.append(header_encargados)

        if not self.encargados_lista:
            self.lista_clientes_view.controls.append(
                ft.Container(
                    content=ft.Text("No se encontraron encargados", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
            return

        periodo_activo = self.periodo_selector.get_periodo_actual() if hasattr(self, "periodo_selector") else "Mes"

        for enc in self.encargados_lista:
            id_enc = enc.get("id_encargado")
            nom_enc = enc.get("nombre", "")
            com_pct = float(enc.get("porcentaje_comision") or 0.0)
            tot_rec_per = float(enc.get("total_recaudado_periodo") or 0.0)
            cant_pagos = int(enc.get("cantidad_pagos_periodo") or 0)
            is_selected = (self.encargado_seleccionado and self.encargado_seleccionado.get("id_encargado") == id_enc)

            btn_editar = ft.IconButton(
                icon=ft.icons.EDIT_OUTLINED,
                icon_color=Config.COLOR_PRIMARY,
                icon_size=16,
                tooltip="Editar Encargado",
                on_click=lambda e, o=enc: self._abrir_modal_editar_encargado(o)
            )

            btn_eliminar = ft.IconButton(
                icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                icon_color="red400",
                icon_size=16,
                tooltip="Eliminar Encargado",
                on_click=lambda e, o=enc: self._confirmar_eliminar_encargado(o)
            )

            click_area = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.PERSON_PIN_ROUNDED, size=20, color=Config.COLOR_PRIMARY),
                        bgcolor=ft.colors.with_opacity(0.12, Config.COLOR_PRIMARY),
                        padding=6,
                        border_radius=8
                    ),
                    ft.Column([
                        ft.Row([
                            ft.Text(nom_enc, size=11.5, weight="bold", color="grey900", expand=True),
                            ft.Container(
                                content=ft.Text(f"{com_pct:g}% Com.", size=9, weight="bold", color="purple900"),
                                bgcolor="#F3E8FF",
                                padding=ft.padding.symmetric(horizontal=5, vertical=1),
                                border_radius=4,
                                visible=bool(com_pct > 0)
                            )
                        ]),
                        ft.Row([
                            ft.Text(f"Recaudado ({periodo_activo}):", size=9.5, color=Config.COLOR_TEXT_MUTED),
                            ft.Text(f"${tot_rec_per:,.0f}", size=10, weight="bold", color=Config.COLOR_SUCCESS if tot_rec_per > 0 else "grey700"),
                            ft.Text(f"({cant_pagos} pagos)", size=8.5, color=Config.COLOR_TEXT_MUTED)
                        ], spacing=3)
                    ], spacing=2, expand=True),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                ink=True,
                on_click=lambda e, o=enc: self._cargar_detalle_encargado(o)
            )

            card_enc = ft.Container(
                content=ft.Row([
                    click_area,
                    ft.Row([
                        btn_editar,
                        btn_eliminar
                    ], spacing=0)
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.only(left=8, right=4, top=4, bottom=4),
                bgcolor=ft.colors.with_opacity(0.08, Config.COLOR_PRIMARY) if is_selected else Config.COLOR_SURFACE,
                border=ft.border.all(1.5 if is_selected else 1, Config.COLOR_PRIMARY if is_selected else Config.COLOR_BORDER),
                border_radius=8
            )
            self.lista_clientes_view.controls.append(card_enc)

    def _cargar_detalle_encargado(self, enc: dict):
        self.encargado_seleccionado = enc
        self.cliente_seleccionado = None
        self.btn_pagar_global.visible = False
        self.btn_cuotas_global.visible = False
        self.btn_informe_global.visible = False

        nom_enc = enc.get("nombre", "")
        com_pct = float(enc.get("porcentaje_comision") or 0.0)
        tel_enc = enc.get("telefono") or "Sin teléfono"
        tot_per = float(enc.get("total_recaudado_periodo") or 0.0)
        tot_hist = float(enc.get("total_recaudado_historico") or 0.0)
        com_per = float(enc.get("comision_estimada_periodo") or 0.0)
        pagos_lista = enc.get("pagos_lista") or []

        periodo_activo = self.periodo_selector.get_periodo_actual() if hasattr(self, "periodo_selector") else "Mes"

        # 1. Header Encargado
        header_enc = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.icons.BADGE_ROUNDED, color=Config.COLOR_PRIMARY, size=28),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY),
                    padding=8,
                    border_radius=10
                ),
                ft.Column([
                    ft.Row([
                        ft.Text(nom_enc, size=15, weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(
                            content=ft.Text(f"Comisión: {com_pct:g}%", size=10, weight="bold", color="purple900"),
                            bgcolor="#F3E8FF",
                            padding=ft.padding.symmetric(horizontal=7, vertical=2),
                            border_radius=6
                        )
                    ], spacing=6),
                    ft.Text(f"Teléfono: {tel_enc} | {len(pagos_lista)} Recaudos históricos registrados", size=10, color=Config.COLOR_TEXT_MUTED)
                ], spacing=2, expand=True),
                ft.Row([
                    ft.ElevatedButton(
                        "Editar",
                        icon=ft.icons.EDIT_OUTLINED,
                        bgcolor=Config.COLOR_PRIMARY,
                        color="white",
                        height=32,
                        on_click=lambda e, o=enc: self._abrir_modal_editar_encargado(o)
                    ),
                    ft.OutlinedButton(
                        "Eliminar",
                        icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                        height=32,
                        style=ft.ButtonStyle(color="red700"),
                        on_click=lambda e, o=enc: self._confirmar_eliminar_encargado(o)
                    )
                ], spacing=6)
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=Config.COLOR_SURFACE,
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=10
        )

        # 2. Tarjetas de métricas del encargado
        card_kpi_per = self._crear_kpi_card(f"Recaudado ({periodo_activo})", f"${tot_per:,.0f}", ft.icons.SAVINGS_ROUNDED, Config.COLOR_SUCCESS)
        card_kpi_com = self._crear_kpi_card("Comisión Estimada", f"${com_per:,.0f}", ft.icons.PAID_ROUNDED, "purple800", subtexto=f"{com_pct:g}% sobre ${tot_per:,.0f}")
        card_kpi_hist = self._crear_kpi_card("Recaudo Histórico Total", f"${tot_hist:,.0f}", ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, Config.COLOR_PRIMARY)

        row_kpis = ft.Row([card_kpi_per, card_kpi_com, card_kpi_hist], spacing=8)

        # 3. Tabla de Pagos de este encargado
        dt_pagos_enc = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Cliente", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Monto Recaudado", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Método", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Comisión Ganada", size=11, weight="bold")),
            ],
            rows=[],
            heading_row_height=30,
            data_row_min_height=28,
            data_row_max_height=32,
            column_spacing=12,
            heading_row_color=Config.COLOR_MUTED
        )

        pagos_filtrados_periodo = [p for p in pagos_lista if not periodo_activo or str(p.get("fecha_pago") or "")[:7] == periodo_activo]
        pagos_mostrar = pagos_filtrados_periodo if pagos_filtrados_periodo else pagos_lista

        for p in pagos_mostrar:
            monto_p = float(p.get("monto_total") or 0.0)
            com_p = monto_p * (com_pct / 100.0)
            fec_p = (p.get("fecha_pago") or "")[:10]
            cli_p = p.get("nombre_cliente") or "-"
            met_p = p.get("metodo_pago") or "EFECTIVO"

            dt_pagos_enc.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(fec_p, size=11)),
                    ft.DataCell(ft.Text(cli_p[:35], size=10.5, weight="w500", tooltip=cli_p)),
                    ft.DataCell(ft.Text(f"${monto_p:,.0f}", size=11, weight="bold", color=Config.COLOR_SUCCESS)),
                    ft.DataCell(ft.Text(met_p, size=11)),
                    ft.DataCell(ft.Text(f"${com_p:,.0f}", size=11, weight="bold", color="purple800" if com_p > 0 else "grey600")),
                ])
            )

        tabla_pagos_container = ft.Container(
            content=dt_pagos_enc,
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=8,
            padding=0
        ) if pagos_mostrar else ft.Container(
            content=ft.Text(f"No hay pagos registrados para este encargado en el periodo {periodo_activo}.", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
            alignment=ft.alignment.center,
            padding=20
        )

        self.panel_derecho_contenido.content = ft.ListView(
            controls=[
                header_enc,
                row_kpis,
                ft.Text(f"Historial de Recaudos ({'Periodo ' + periodo_activo if pagos_filtrados_periodo else 'Histórico Completo'}):", size=11, weight="bold", color=Config.COLOR_PRIMARY),
                tabla_pagos_container
            ],
            expand=True,
            spacing=10
        )
        self._render_lista_encargados()
        self.safe_update()

    def _abrir_modal_crear_encargado(self):
        txt_nombre = ft.TextField(label="Nombre del Encargado", hint_text="Ej: Pedro Pérez", dense=True, text_size=12, autofocus=True)
        txt_comision = ft.TextField(label="% Comisión por Defecto", value="0", suffix_text="%", dense=True, text_size=12, keyboard_type=ft.KeyboardType.NUMBER)
        txt_telefono = ft.TextField(label="Teléfono / Contacto (Opcional)", hint_text="Ej: 3001234567", dense=True, text_size=12)

        def guardar(e):
            nom = (txt_nombre.value or "").strip()
            if not nom:
                self._mostrar_snackbar("El nombre del encargado es obligatorio", "red")
                return
            try:
                com = float(str(txt_comision.value or "0").replace(",", "."))
            except ValueError:
                com = 0.0

            tel = (txt_telefono.value or "").strip()
            res = self.clientes_repo.crear_encargado(nom, com, tel)
            if res:
                self._mostrar_snackbar(f"✓ Encargado '{nom}' creado con éxito.", "green")
                dlg.open = False
                self.load_data()
            else:
                self._mostrar_snackbar("Error al crear el encargado en la base de datos.", "red")

        dlg = ft.AlertDialog(
            title=ft.Text("Nuevo Encargado de Recaudos", size=15, weight="bold", color=Config.COLOR_PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    txt_nombre,
                    txt_comision,
                    txt_telefono
                ], spacing=8, tight=True),
                width=380
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal(dlg)),
                ft.ElevatedButton("Crear Encargado", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=guardar)
            ]
        )
        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _abrir_modal_editar_encargado(self, enc: dict):
        id_enc = enc.get("id_encargado")
        nom_ant = enc.get("nombre", "")
        txt_nombre = ft.TextField(label="Nombre del Encargado", value=nom_ant, dense=True, text_size=12, autofocus=True)
        txt_comision = ft.TextField(label="% Comisión", value=f"{float(enc.get('porcentaje_comision') or 0):g}", suffix_text="%", dense=True, text_size=12, keyboard_type=ft.KeyboardType.NUMBER)
        txt_telefono = ft.TextField(label="Teléfono / Contacto", value=enc.get("telefono") or "", dense=True, text_size=12)

        def guardar(e):
            nom_nue = (txt_nombre.value or "").strip()
            if not nom_nue:
                self._mostrar_snackbar("El nombre no puede estar vacío", "red")
                return
            try:
                com = float(str(txt_comision.value or "0").replace(",", "."))
            except ValueError:
                com = 0.0

            tel = (txt_telefono.value or "").strip()
            ok = self.clientes_repo.actualizar_encargado(id_enc, nom_ant, nom_nue, com, tel)
            if ok:
                self._mostrar_snackbar(f"✓ Encargado '{nom_nue}' actualizado con éxito.", "green")
                dlg.open = False
                self.load_data()
            else:
                self._mostrar_snackbar("Error al actualizar el encargado.", "red")

        dlg = ft.AlertDialog(
            title=ft.Text(f"Editar Encargado: {nom_ant}", size=15, weight="bold", color=Config.COLOR_PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    txt_nombre,
                    txt_comision,
                    txt_telefono
                ], spacing=8, tight=True),
                width=380
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal(dlg)),
                ft.ElevatedButton("Guardar Cambios", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=guardar)
            ]
        )
        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _confirmar_eliminar_encargado(self, enc: dict):
        id_enc = enc.get("id_encargado")
        nom = enc.get("nombre", "")

        def eliminar(e):
            ok = self.clientes_repo.eliminar_encargado(id_encargado=id_enc, nombre=nom)
            if ok:
                self._mostrar_snackbar(f"✓ Encargado '{nom}' eliminado.", "green")
                self._cerrar_modal(dlg)
                if self.encargado_seleccionado and (self.encargado_seleccionado.get("id_encargado") == id_enc or self.encargado_seleccionado.get("nombre") == nom):
                    self.encargado_seleccionado = None
                    self.panel_derecho_contenido.content = self._crear_placeholder_vacio()
                self.load_data()
            else:
                self._mostrar_snackbar("Error al eliminar el encargado.", "red")

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación", size=15, weight="bold", color="red700"),
            content=ft.Text(f"¿Estás seguro de que deseas eliminar al encargado '{nom}'?", size=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal(dlg)),
                ft.ElevatedButton("Eliminar", bgcolor="red700", color="white", on_click=eliminar)
            ]
        )
        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    def _toggle_filtros(self, e=None):
        self.filtros_expandidos = not self.filtros_expandidos
        self.contenedor_filtros.visible = self.filtros_expandidos
        self.btn_toggle_filtros.icon = ft.icons.KEYBOARD_ARROW_UP_ROUNDED if self.filtros_expandidos else ft.icons.TUNE_ROUNDED
        self.btn_toggle_filtros.bgcolor = ft.colors.with_opacity(0.14, Config.COLOR_PRIMARY) if self.filtros_expandidos else ft.colors.with_opacity(0.04, Config.COLOR_PRIMARY)
        self.safe_update()

    def _on_search_change(self, e):
        self.busqueda_actual = e.control.value or ""
        self._aplicar_filtros_locales()
        self._render_lista_izquierda()
        self.safe_update()

    def _on_chip_filtro_select(self, valor: str):
        self.chip_todos.selected = (valor == "TODOS")
        self.chip_con_deuda.selected = (valor == "CON_DEUDA")
        self.chip_al_dia.selected = (valor == "AL_DIA")
        self.filtro_saldo_actual = valor
        self._aplicar_filtros_locales()
        self._render_lista_izquierda()
        self.safe_update()

    def _on_chip_tipo_select(self, valor: str):
        self.chip_tipo_todos.selected = (valor == "TODOS")
        self.chip_tipo_remision.selected = (valor == "REMISIÓN")
        self.chip_tipo_pos.selected = (valor in ("FACTURA_POS", "POS"))
        self.filtro_tipo_doc_actual = valor
        self._aplicar_filtros_locales()
        self._render_lista_izquierda()
        self.safe_update()

    def _abrir_date_picker(self, e):
        if self.page:
            if self.date_picker not in self.page.overlay:
                self.page.overlay.append(self.date_picker)
            try:
                self.date_picker.open = True
                self.page.update()
            except Exception:
                pass

    def _on_date_picked(self, e):
        if e.control.value:
            dt_val = e.control.value
            self.fecha_filtro = dt_val.strftime("%Y-%m-%d")
            self.lbl_fecha_filtro.value = f"{self.fecha_filtro}"
            self.chip_fecha_activa.visible = True
            self.btn_date_icon.icon_color = "amber800"
            self._aplicar_filtros_locales()
            self._render_lista_izquierda()
            self.safe_update()

    def _limpiar_fecha(self, e):
        self.fecha_filtro = ""
        self.lbl_fecha_filtro.value = ""
        self.chip_fecha_activa.visible = False
        self.btn_date_icon.icon_color = Config.COLOR_PRIMARY
        self._aplicar_filtros_locales()
        self._render_lista_izquierda()
        self.safe_update()


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

    def _toggle_expandir_panel_cliente(self, e=None):
        self.panel_cliente_expandido = not self.panel_cliente_expandido
        
        # Ocultar o mostrar elementos externos
        self.kpis_row.visible = not self.panel_cliente_expandido
        self.col_izquierda.visible = not self.panel_cliente_expandido
        self.lbl_titulo.visible = not self.panel_cliente_expandido
        self.lbl_subtitulo.visible = not self.panel_cliente_expandido
        self.btn_refrescar.visible = not self.panel_cliente_expandido
        self.btn_pagar_global.visible = bool(self.cliente_seleccionado)
        self.btn_cuotas_global.visible = self.mostrar_plan_cuotas and bool(self.cliente_seleccionado)
        self.btn_informe_global.visible = bool(self.cliente_seleccionado)

        if self.cliente_seleccionado:
            self._cargar_detalle_cliente(self.cliente_seleccionado, recargar_datos=False)
        else:
            self.safe_update()

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
        vend = (cli.get("vendedor_encargado") or "").strip()
        com = float(cli.get("porcentaje_comision") or 0.0)
        com_str = f"{com:g}%" if com > 0 else ""

        # Mostrar botones de acción en el top bar
        self.btn_pagar_global.visible = True
        self.btn_cuotas_global.visible = self.mostrar_plan_cuotas
        self.btn_informe_global.visible = True

        # Chip visual interactivo del vendedor en la cabecera
        if vend:
            chip_vendedor = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.BADGE_OUTLINED, size=13, color="purple800"),
                    ft.Text(f"Vendedor: {vend}" + (f" ({com_str})" if com_str else ""), size=9.5, weight="bold", color="purple900"),
                ], spacing=4, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#F5F3FF",
                border=ft.border.all(1, "#DDD6FE"),
                padding=ft.padding.symmetric(horizontal=7, vertical=2),
                border_radius=6,
                tooltip="Clic para cambiar vendedor encargado o porcentaje de comisión",
                on_click=lambda e, c=cli: self._abrir_modal_asignar_vendedor(c),
                ink=True
            )
        else:
            chip_vendedor = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.PERSON_ADD_ALT_1_ROUNDED, size=12, color="grey700"),
                    ft.Text("Sin Vendedor (+ Asignar)", size=9.5, weight="w500", color="grey700"),
                ], spacing=3, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#F8FAFC",
                border=ft.border.all(1, "#E2E8F0"),
                padding=ft.padding.symmetric(horizontal=7, vertical=2),
                border_radius=6,
                tooltip="Clic para asignar un vendedor/encargado a este cliente",
                on_click=lambda e, c=cli: self._abrir_modal_asignar_vendedor(c),
                ink=True
            )

        # Botón de Expandir / Restaurar Panel a Pantalla Completa
        btn_expandir_panel = ft.IconButton(
            icon=ft.icons.FULLSCREEN_EXIT_ROUNDED if self.panel_cliente_expandido else ft.icons.FULLSCREEN_ROUNDED,
            icon_color=Config.COLOR_PRIMARY,
            icon_size=21,
            tooltip="Restaurar vista normal" if self.panel_cliente_expandido else "Expandir a pantalla completa (Ocultar panel lateral y KPIs)",
            on_click=self._toggle_expandir_panel_cliente
        )

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
                        chip_vendedor,
                        ft.Container(
                            content=ft.Text(f"Saldo Total: ${saldo:,.0f}", size=10.5, weight="bold", color="white"),
                            bgcolor="#DC2626" if saldo > 0.01 else "#16A34A",
                            padding=ft.padding.symmetric(horizontal=8, vertical=3),
                            border_radius=6
                        ),
                        btn_expandir_panel
                    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
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
        tabs_list = [
            ft.Tab(text="Facturas", icon=ft.icons.RECEIPT_LONG_ROUNDED),
            ft.Tab(text="Pagos", icon=ft.icons.HISTORY_ROUNDED),
        ]
        if self.mostrar_plan_cuotas:
            tabs_list.append(ft.Tab(text="Cuotas", icon=ft.icons.EVENT_NOTE_ROUNDED))

        self.tabs_detalle = ft.Tabs(
            selected_index=min(self.tab_activo, len(tabs_list) - 1),
            animation_duration=150,
            height=40,
            tabs=tabs_list,
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
                if self.mostrar_plan_cuotas:
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
        elif self.mostrar_plan_cuotas and self.tab_activo == 2:
            self._render_tab_cuotas()
        else:
            self._render_tab_facturas()

    def _render_tab_facturas(self):
        if not self.facturas_cliente:
            self.tab_content_container.content = ft.Container(
                content=ft.Text("Este cliente no tiene facturas registradas.", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
                alignment=ft.alignment.center,
                padding=20
            )
            return

        btn_generar_informe_tab = ft.ElevatedButton(
            text="Generar Informe",
            icon=ft.icons.ASSESSMENT_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=30,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=10, vertical=2)
            ),
            on_click=lambda e: self._abrir_modal_informe_facturas(self.cliente_seleccionado)
        )

        toolbar = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.icons.RECEIPT_LONG_ROUNDED, size=15, color=Config.COLOR_PRIMARY),
                    ft.Text(f"{len(self.facturas_cliente)} facturas registradas", size=11, weight="bold", color=Config.COLOR_PRIMARY),
                ], spacing=4),
                ft.Container(expand=True),
                btn_generar_informe_tab
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(left=2, right=2, top=2, bottom=4)
        )

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
            controls=[toolbar, dt],
            expand=True,
            spacing=4
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
                ft.DataColumn(ft.Text("Encargado", size=11, weight="bold")),
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
            vend_pago = (p.get("vendedor_encargado") or "").strip()

            btn_anular = ft.IconButton(
                icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                icon_color="red400",
                icon_size=16,
                tooltip="Anular Recaudo",
                on_click=lambda e, pid=p_id: self._confirmar_anular_pago(pid)
            )

            cell_encargado = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.BADGE_OUTLINED, size=12, color="purple800" if vend_pago else "grey500"),
                    ft.Text(vend_pago if vend_pago else "Sin Asignar", size=10.5, weight="w600" if vend_pago else "normal", color="purple950" if vend_pago else "grey600")
                ], spacing=3, tight=True),
                bgcolor="#f5f3ff" if vend_pago else "transparent",
                padding=ft.padding.symmetric(horizontal=5, vertical=2) if vend_pago else None,
                border_radius=4
            )

            dt.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p.get("fecha_formateada", ""), size=11)),
                    ft.DataCell(ft.Text(f"${p.get('monto_total', 0.0):,.0f}", size=11, weight="bold", color=Config.COLOR_SUCCESS)),
                    ft.DataCell(ft.Text(metodo, size=11)),
                    ft.DataCell(cell_encargado),
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
    # TAB 4: VENDEDOR & COMISIÓN
    # ==========================================
    def _render_tab_vendedor(self):
        if not self.cliente_seleccionado:
            return

        nom = self.cliente_seleccionado.get("nombre", "")
        vend_actual = (self.cliente_seleccionado.get("vendedor_encargado") or "").strip()
        com_pct = float(self.cliente_seleccionado.get("porcentaje_comision") or 0.0)
        tot_recaudado = float(self.cliente_seleccionado.get("total_abonado") or 0.0)
        saldo_pend = float(self.cliente_seleccionado.get("saldo_pendiente") or 0.0)
        tot_facturado = float(self.cliente_seleccionado.get("total_facturado") or 0.0)

        comision_ganada = tot_recaudado * (com_pct / 100.0)
        comision_potencial = saldo_pend * (com_pct / 100.0)

        vendedores_disponibles = self.clientes_repo.get_vendedores_disponibles()
        vend_com_map = {c.get("vendedor_encargado"): float(c.get("porcentaje_comision") or 0.0) for c in self.clientes_lista if c.get("vendedor_encargado")}

        # 1. Tarjeta de Asignación / Edición
        txt_vendedor = ft.TextField(
            label="Encargado",
            value=vend_actual,
            hint_text="Escribe o selecciona un encargado...",
            dense=True,
            height=38,
            text_size=12,
            expand=True
        )
        txt_comision = ft.TextField(
            label="% Comisión",
            value=f"{com_pct:g}" if com_pct > 0 else "0",
            suffix_text="%",
            dense=True,
            height=38,
            text_size=12,
            width=110,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        row_sugerencias_tab = ft.Row(wrap=True, spacing=4)

        def _actualizar_sug_tab(filtro=""):
            f_up = filtro.strip().upper()
            row_sugerencias_tab.controls.clear()
            coincidencias = [v for v in vendedores_disponibles if not f_up or f_up in v.upper()]
            for v in coincidencias[:6]:
                def _selec_tab(e, v_nom=v):
                    txt_vendedor.value = v_nom
                    if v_nom in vend_com_map and float(vend_com_map[v_nom]) > 0 and (not txt_comision.value or txt_comision.value == "0"):
                        txt_comision.value = f"{vend_com_map[v_nom]:g}"
                    _actualizar_sug_tab(v_nom)
                    self.safe_update()

                row_sugerencias_tab.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.PERSON_PIN_ROUNDED, size=11, color="purple800"),
                            ft.Text(v, size=10, weight="bold", color="purple950")
                        ], spacing=3, tight=True),
                        bgcolor="#F5F3FF",
                        border=ft.border.all(1, "#DDD6FE"),
                        padding=ft.padding.symmetric(horizontal=7, vertical=2),
                        border_radius=4,
                        ink=True,
                        tooltip=f"Seleccionar a {v}",
                        on_click=_selec_tab
                    )
                )
            row_sugerencias_tab.visible = bool(row_sugerencias_tab.controls)
            self.safe_update()

        txt_vendedor.on_change = lambda e: _actualizar_sug_tab(txt_vendedor.value)
        _actualizar_sug_tab(vend_actual)

        def _guardar_desde_tab(e):
            nuevo_v = (txt_vendedor.value or "").strip()
            try:
                nuevo_pct = float(str(txt_comision.value or "0").replace(",", "."))
            except ValueError:
                nuevo_pct = 0.0

            if self.clientes_repo.asignar_vendedor_cliente(nom, nuevo_v, nuevo_pct):
                self.cliente_seleccionado["vendedor_encargado"] = nuevo_v
                self.cliente_seleccionado["porcentaje_comision"] = nuevo_pct

                # Actualizar en la lista general de clientes en memoria
                for c in self.clientes_lista:
                    if c.get("nombre") == nom:
                        c["vendedor_encargado"] = nuevo_v
                        c["porcentaje_comision"] = nuevo_pct

                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Encargado '{nuevo_v or 'Sin asignar'}' guardado correctamente para {nom}."),
                        bgcolor="green"
                    )
                    self.page.snack_bar.open = True

                self._render_lista_izquierda()
                self._cargar_detalle_cliente(self.cliente_seleccionado, recargar_datos=False)
                self.safe_update()
            else:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Error al actualizar el encargado en la base de datos."),
                        bgcolor="red"
                    )
                    self.page.snack_bar.open = True
                    self.safe_update()

        def _desasignar_desde_tab(e):
            if self.clientes_repo.asignar_vendedor_cliente(nom, "", 0.0):
                self.cliente_seleccionado["vendedor_encargado"] = ""
                self.cliente_seleccionado["porcentaje_comision"] = 0.0

                for c in self.clientes_lista:
                    if c.get("nombre") == nom:
                        c["vendedor_encargado"] = ""
                        c["porcentaje_comision"] = 0.0

                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Encargado desasignado correctamente para {nom}."),
                        bgcolor="green"
                    )
                    self.page.snack_bar.open = True

                self._render_lista_izquierda()
                self._cargar_detalle_cliente(self.cliente_seleccionado, recargar_datos=False)
                self.safe_update()

        btn_guardar_tab = ft.ElevatedButton(
            "Guardar",
            icon=ft.icons.SAVE_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=38,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=_guardar_desde_tab
        )
        btn_desasignar_tab = ft.OutlinedButton(
            "Desasignar",
            icon=ft.icons.PERSON_REMOVE_ROUNDED,
            height=38,
            visible=bool(vend_actual),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), color="red700"),
            on_click=_desasignar_desde_tab
        )

        card_formulario = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.BADGE_OUTLINED, color=Config.COLOR_PRIMARY, size=16),
                    ft.Text("Encargado", size=12, weight="bold", color=Config.COLOR_PRIMARY),
                ], spacing=6),
                ft.Row([
                    txt_vendedor,
                    txt_comision,
                    btn_desasignar_tab,
                    btn_guardar_tab
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column([
                    ft.Text("Sugerencias de encargados existentes:", size=9.5, color=Config.COLOR_TEXT_MUTED, italic=True),
                    row_sugerencias_tab
                ], spacing=2, visible=bool(vendedores_disponibles))
            ], spacing=6),
            padding=10,
            bgcolor="#F8FAFC",
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=8
        )

        # 2. Tabla de Pagos y Comisión Individual
        dt_pagos_comision = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha de Pago", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Monto Recaudado", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Encargado Recaudo", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Método", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Facturas Afectadas", size=11, weight="bold")),
                ft.DataColumn(ft.Text("% Comisión", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Comisión Sugerida", size=11, weight="bold")),
            ],
            rows=[],
            heading_row_height=30,
            data_row_min_height=28,
            data_row_max_height=32,
            column_spacing=12,
            heading_row_color=Config.COLOR_MUTED
        )

        for p in self.historial_pagos:
            monto_p = float(p.get("monto_total") or 0.0)
            com_p = monto_p * (com_pct / 100.0)
            f_afectadas = p.get("facturas_afectadas", [])
            facs_str = ", ".join([f"#{d.get('factura_no')}" for d in f_afectadas]) if f_afectadas else "Global (FIFO)"
            metodo = p.get("metodo_pago", "EFECTIVO")
            vend_pago = (p.get("vendedor_encargado") or vend_actual or "").strip()

            dt_pagos_comision.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p.get("fecha_formateada", ""), size=11)),
                    ft.DataCell(ft.Text(f"${monto_p:,.0f}", size=11, weight="bold", color=Config.COLOR_SUCCESS)),
                    ft.DataCell(ft.Text(vend_pago if vend_pago else "Sin Asignar", size=11, weight="w600" if vend_pago else "normal", color="purple950" if vend_pago else "grey600")),
                    ft.DataCell(ft.Text(metodo, size=11)),
                    ft.DataCell(ft.Text(facs_str[:35], size=10, tooltip=facs_str)),
                    ft.DataCell(ft.Text(f"{com_pct:g}%", size=11, color="purple700")),
                    ft.DataCell(ft.Text(f"${com_p:,.2f}", size=11, weight="bold", color="purple800")),
                ])
            )

        tabla_scroll = ft.Container(
            content=dt_pagos_comision,
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=8,
            padding=0
        ) if self.historial_pagos else ft.Container(
            content=ft.Text("No hay pagos registrados para calcular comisión en este cliente.", size=11, color=Config.COLOR_TEXT_MUTED, italic=True),
            alignment=ft.alignment.center,
            padding=20
        )

        self.tab_content_container.content = ft.ListView(
            controls=[
                card_formulario,
                ft.Text("Desglose de Comisiones por Pago Recaudado:", size=11, weight="bold", color=Config.COLOR_PRIMARY),
                tabla_scroll
            ],
            expand=True,
            spacing=10
        )

    # ==========================================
    # MODAL: ASIGNAR VENDEDOR RÁPIDO
    # ==========================================
    def _abrir_modal_asignar_vendedor(self, cli: dict):
        if not cli:
            return

        nom = cli.get("nombre", "")
        vend_actual = (cli.get("vendedor_encargado") or "").strip()
        com_pct = float(cli.get("porcentaje_comision") or 0.0)

        vendedores_disponibles = self.clientes_repo.get_vendedores_disponibles()
        vend_com_map = {c.get("vendedor_encargado"): float(c.get("porcentaje_comision") or 0.0) for c in self.clientes_lista if c.get("vendedor_encargado")}

        txt_vendedor_modal = ft.TextField(
            label="Encargado",
            value=vend_actual,
            hint_text="Escribe o selecciona un encargado...",
            dense=True,
            autofocus=True
        )
        txt_comision_modal = ft.TextField(
            label="% Comisión",
            value=f"{com_pct:g}" if com_pct > 0 else "0",
            suffix_text="%",
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        row_sugerencias_modal = ft.Row(wrap=True, spacing=4)

        def _actualizar_sug_modal(filtro=""):
            f_up = filtro.strip().upper()
            row_sugerencias_modal.controls.clear()
            coincidencias = [v for v in vendedores_disponibles if not f_up or f_up in v.upper()]
            for v in coincidencias[:6]:
                def _selec_modal(e, v_nom=v):
                    txt_vendedor_modal.value = v_nom
                    if v_nom in vend_com_map and float(vend_com_map[v_nom]) > 0 and (not txt_comision_modal.value or txt_comision_modal.value == "0"):
                        txt_comision_modal.value = f"{vend_com_map[v_nom]:g}"
                    _actualizar_sug_modal(v_nom)
                    self.safe_update()

                row_sugerencias_modal.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.PERSON_PIN_ROUNDED, size=11, color="purple800"),
                            ft.Text(v, size=10, weight="bold", color="purple950")
                        ], spacing=3, tight=True),
                        bgcolor="#F5F3FF",
                        border=ft.border.all(1, "#DDD6FE"),
                        padding=ft.padding.symmetric(horizontal=7, vertical=2.5),
                        border_radius=4,
                        ink=True,
                        tooltip=f"Seleccionar a {v}",
                        on_click=_selec_modal
                    )
                )
            row_sugerencias_modal.visible = bool(row_sugerencias_modal.controls)
            self.safe_update()

        txt_vendedor_modal.on_change = lambda e: _actualizar_sug_modal(txt_vendedor_modal.value)
        _actualizar_sug_modal(vend_actual)

        def _do_guardar(e):
            nuevo_v = (txt_vendedor_modal.value or "").strip()
            try:
                nuevo_pct = float(str(txt_comision_modal.value or "0").replace(",", "."))
            except ValueError:
                nuevo_pct = 0.0

            dlg.open = False
            self.safe_update()

            if self.clientes_repo.asignar_vendedor_cliente(nom, nuevo_v, nuevo_pct):
                cli["vendedor_encargado"] = nuevo_v
                cli["porcentaje_comision"] = nuevo_pct

                # Actualizar en la lista general de clientes en memoria
                for c in self.clientes_lista:
                    if c.get("nombre") == nom:
                        c["vendedor_encargado"] = nuevo_v
                        c["porcentaje_comision"] = nuevo_pct

                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Encargado '{nuevo_v or 'Sin asignar'}' guardado correctamente para {nom}."),
                        bgcolor="green"
                    )
                    self.page.snack_bar.open = True

                self._render_lista_izquierda()
                self._cargar_detalle_cliente(cli, recargar_datos=False)
                self.safe_update()
            else:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Error al actualizar el encargado en la base de datos."),
                        bgcolor="red"
                    )
                    self.page.snack_bar.open = True
                    self.safe_update()

        def _do_desasignar(e):
            dlg.open = False
            self.safe_update()

            if self.clientes_repo.asignar_vendedor_cliente(nom, "", 0.0):
                cli["vendedor_encargado"] = ""
                cli["porcentaje_comision"] = 0.0

                for c in self.clientes_lista:
                    if c.get("nombre") == nom:
                        c["vendedor_encargado"] = ""
                        c["porcentaje_comision"] = 0.0

                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text(f"Encargado desasignado correctamente para {nom}."),
                        bgcolor="green"
                    )
                    self.page.snack_bar.open = True

                self._render_lista_izquierda()
                self._cargar_detalle_cliente(cli, recargar_datos=False)
                self.safe_update()
            else:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        ft.Text("Error al desasignar el encargado."),
                        bgcolor="red"
                    )
                    self.page.snack_bar.open = True
                    self.safe_update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.BADGE_OUTLINED, color=Config.COLOR_PRIMARY, size=18),
                ft.Text(f"Encargado - {nom}", size=14, weight="bold", color=Config.COLOR_PRIMARY),
            ], spacing=6),
            content=ft.Container(
                width=420,
                content=ft.Column([
                    ft.Text(
                        "Asigna la persona encargada de la gestión de este cliente.",
                        size=11,
                        color=Config.COLOR_TEXT_MUTED
                    ),
                    txt_vendedor_modal,
                    ft.Column([
                        ft.Text("Sugerencias de encargados existentes:", size=9.5, color=Config.COLOR_TEXT_MUTED, italic=True),
                        row_sugerencias_modal
                    ], spacing=2, visible=bool(vendedores_disponibles)),
                    txt_comision_modal,
                ], tight=True, spacing=10)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), self.safe_update())),
                ft.OutlinedButton("Desasignar", icon=ft.icons.PERSON_REMOVE_ROUNDED, style=ft.ButtonStyle(color="red700"), visible=bool(vend_actual), on_click=_do_desasignar),
                ft.ElevatedButton("Guardar", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=_do_guardar)
            ]
        )

        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()

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

        txt_monto_efectivo = ft.TextField(
            label="💵 Monto Efectivo (COP)",
            value="",
            text_size=12,
            dense=True,
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        txt_monto_transferencia = ft.TextField(
            label="🏦 Monto Transferencia (COP)",
            value="",
            text_size=12,
            dense=True,
            expand=True,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        lbl_total_mixto = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CALCULATE_ROUNDED, size=15, color=Config.COLOR_PRIMARY),
                ft.Text("Total Combinado: $0 COP", size=11.5, weight="bold", color=Config.COLOR_PRIMARY),
            ], spacing=5),
            bgcolor="#EFF6FF",
            border=ft.border.all(1, "#BFDBFE"),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=6,
            visible=False
        )

        def actualizar_suma_mixta(e=None):
            try:
                e_val = float(str(txt_monto_efectivo.value or "0").replace("$", "").replace(".", "").replace(",", ".").strip())
            except ValueError:
                e_val = 0.0
            try:
                t_val = float(str(txt_monto_transferencia.value or "0").replace("$", "").replace(".", "").replace(",", ".").strip())
            except ValueError:
                t_val = 0.0
            tot = e_val + t_val
            lbl_total_mixto.content.controls[1].value = f"Total Combinado: ${tot:,.0f} COP"
            if self.page:
                self.page.update()

        txt_monto_efectivo.on_change = actualizar_suma_mixta
        txt_monto_transferencia.on_change = actualizar_suma_mixta

        row_mixto_montos = ft.Row([
            txt_monto_efectivo,
            txt_monto_transferencia
        ], spacing=8, visible=False)

        def on_doc_change(e):
            val = dd_documento.value
            nuevo_s = saldo_cliente if val == "TODAS" else doc_saldo_map.get(val, saldo_cliente)
            txt_monto.value = f"{int(nuevo_s)}" if nuevo_s > 0 else ""
            if dd_metodo.value == "MIXTO" and nuevo_s > 0:
                txt_monto_efectivo.value = f"{int(nuevo_s / 2)}"
                txt_monto_transferencia.value = f"{int(nuevo_s - int(nuevo_s / 2))}"
                actualizar_suma_mixta()
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
                ft.dropdown.Option("MIXTO", "Pago Mixto (Efectivo + Transferencia)"),
            ],
            dense=True,
            text_size=12
        )

        dd_banco = ft.Dropdown(
            label="Banco / Entidad (Transferencia)",
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
            label="Comprobante / Referencia (Transferencia)",
            hint_text="No. transacción o comprobante",
            text_size=12,
            dense=True,
            visible=False
        )

        vendedores_disponibles = self.clientes_repo.get_vendedores_disponibles()
        vendedor_actual_cli = (cli.get("vendedor_encargado") or "").strip()
        if vendedor_actual_cli and vendedor_actual_cli not in vendedores_disponibles:
            vendedor_actual_cli = ""

        # Input inteligente con autocompletado para Encargado del Recaudo
        txt_encargado_pago = ft.TextField(
            label="Encargado / Cobrador del Recaudo",
            value=vendedor_actual_cli,
            hint_text="Digita para buscar o ingresar un encargado nuevo...",
            text_size=12,
            dense=True,
            prefix_icon=ft.icons.BADGE_OUTLINED,
        )

        col_sugerencias_items = ft.Column(spacing=2, tight=True)
        container_sugerencias = ft.Container(
            content=col_sugerencias_items,
            bgcolor=Config.COLOR_SURFACE,
            border=ft.border.all(1, "#CBD5E1"),
            border_radius=8,
            padding=6,
            visible=False
        )

        def _seleccionar_encargado(nombre_enc):
            txt_encargado_pago.value = nombre_enc
            container_sugerencias.visible = False
            if self.page:
                self.page.update()

        def _actualizar_sugerencias_inteligentes(filtro=""):
            f_clean = filtro.strip()
            f_up = f_clean.upper()
            col_sugerencias_items.controls.clear()

            coincidencias = [v for v in vendedores_disponibles if f_up in v.upper()] if f_up else list(vendedores_disponibles)

            if coincidencias:
                col_sugerencias_items.controls.append(
                    ft.Text("Encargados existentes:", size=9.5, weight="bold", color=Config.COLOR_TEXT_MUTED)
                )
                for v in coincidencias[:6]:
                    col_sugerencias_items.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.PERSON_PIN_ROUNDED, size=15, color=Config.COLOR_PRIMARY),
                                ft.Text(v, size=11, weight="w600", color="grey900", expand=True),
                                ft.Container(
                                    content=ft.Text("Existente", size=8.5, color="purple800", weight="bold"),
                                    bgcolor="#F5F3FF",
                                    padding=ft.padding.symmetric(horizontal=5, vertical=1),
                                    border_radius=4
                                )
                            ], alignment=ft.MainAxisAlignment.START),
                            padding=ft.padding.symmetric(horizontal=8, vertical=5),
                            border_radius=6,
                            ink=True,
                            on_click=lambda e, v_nom=v: _seleccionar_encargado(v_nom)
                        )
                    )

            if f_clean and not any(v.upper() == f_up for v in vendedores_disponibles):
                col_sugerencias_items.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.PERSON_ADD_ALT_1_ROUNDED, size=15, color=Config.COLOR_SUCCESS),
                            ft.Text(f"Usar nuevo encargado: '{f_clean}'", size=11, weight="bold", color="green800", expand=True),
                            ft.Container(
                                content=ft.Text("Nuevo", size=8.5, color="green900", weight="bold"),
                                bgcolor="#DCFCE7",
                                padding=ft.padding.symmetric(horizontal=5, vertical=1),
                                border_radius=4
                            )
                        ]),
                        bgcolor="#F0FDF4",
                        border=ft.border.all(1, "#BBF7D0"),
                        padding=ft.padding.symmetric(horizontal=8, vertical=5),
                        border_radius=6,
                        ink=True,
                        on_click=lambda e, nuevo=f_clean: _seleccionar_encargado(nuevo)
                    )
                )

            container_sugerencias.visible = bool(col_sugerencias_items.controls)
            if self.page:
                self.page.update()

        def _toggle_lista_encargados(e):
            if container_sugerencias.visible:
                container_sugerencias.visible = False
            else:
                _actualizar_sugerencias_inteligentes(txt_encargado_pago.value or "")
            if self.page:
                self.page.update()

        btn_toggle_sug = ft.IconButton(
            icon=ft.icons.ARROW_DROP_DOWN_ROUNDED,
            icon_size=20,
            tooltip="Ver lista de encargados",
            on_click=_toggle_lista_encargados
        )
        txt_encargado_pago.suffix = btn_toggle_sug
        txt_encargado_pago.on_focus = lambda e: _actualizar_sugerencias_inteligentes(txt_encargado_pago.value or "")
        txt_encargado_pago.on_change = lambda e: _actualizar_sugerencias_inteligentes(txt_encargado_pago.value or "")

        box_encargado_inteligente = ft.Column([
            txt_encargado_pago,
            container_sugerencias
        ], spacing=2, tight=True)

        txt_obs = ft.TextField(
            label="Observaciones",
            hint_text="Notas opcionales del pago",
            text_size=12,
            dense=True
        )

        def on_metodo_change(e):
            m = dd_metodo.value
            is_mixto = (m == "MIXTO")
            is_transf = (m == "TRANSFERENCIA")

            txt_monto.visible = not is_mixto
            row_mixto_montos.visible = is_mixto
            lbl_total_mixto.visible = is_mixto
            dd_banco.visible = (is_transf or is_mixto)
            txt_ref.visible = (is_transf or is_mixto)

            if is_mixto and not txt_monto_efectivo.value and not txt_monto_transferencia.value:
                try:
                    curr_monto = float(str(txt_monto.value or "0").replace("$", "").replace(".", "").replace(",", ".").strip())
                except ValueError:
                    curr_monto = 0.0
                if curr_monto > 0:
                    txt_monto_efectivo.value = f"{int(curr_monto / 2)}"
                    txt_monto_transferencia.value = f"{int(curr_monto - int(curr_monto / 2))}"
                actualizar_suma_mixta()

            if self.page:
                self.page.update()

        dd_metodo.on_change = on_metodo_change

        is_submitting_pago = False

        def guardar_pago(e):
            nonlocal is_submitting_pago
            if is_submitting_pago:
                return

            metodo = dd_metodo.value
            doc_sel = dd_documento.value
            encargado_sel = (txt_encargado_pago.value or "").strip()

            if metodo == "MIXTO":
                try:
                    m_efectivo = float(str(txt_monto_efectivo.value or "0").replace("$", "").replace(".", "").replace(",", ".").strip())
                except ValueError:
                    m_efectivo = 0.0
                try:
                    m_transf = float(str(txt_monto_transferencia.value or "0").replace("$", "").replace(".", "").replace(",", ".").strip())
                except ValueError:
                    m_transf = 0.0

                monto_total = m_efectivo + m_transf
                if monto_total <= 0:
                    self._mostrar_snackbar("Debes ingresar un monto mayor a 0 en efectivo o transferencia.", "red")
                    return

                is_submitting_pago = True
                btn_confirmar_pago.disabled = True
                dlg.open = False
                self.safe_update()

                facturas_seleccionadas = None
                if doc_sel and doc_sel != "TODAS":
                    facturas_seleccionadas = {doc_sel: monto_total}

                ok = self.cartera_repo.registrar_pago_mixto_cartera(
                    id_cliente=cli.get("id_cliente"),
                    nombre_cliente=nom,
                    monto_efectivo=m_efectivo,
                    monto_transferencia=m_transf,
                    banco_origen=dd_banco.value if m_transf > 0 else None,
                    referencia=txt_ref.value or "",
                    observaciones=txt_obs.value or "",
                    facturas_seleccionadas=facturas_seleccionadas,
                    usuario="admin",
                    vendedor_encargado=encargado_sel
                )

                if ok:
                    if encargado_sel and encargado_sel not in vendedores_disponibles:
                        self.clientes_repo.crear_encargado(encargado_sel)
                    doc_msg = f" a {doc_sel}" if (doc_sel and doc_sel != "TODAS") else ""
                    self._mostrar_snackbar(
                        f"✓ Pago mixto (${monto_total:,.0f}{doc_msg}) registrado con éxito (💵 ${m_efectivo:,.0f} + 🏦 ${m_transf:,.0f}).",
                        "green"
                    )
                    self.load_data()
                else:
                    self._mostrar_snackbar("Error registrando pago mixto en base de datos.", "red")

            else:
                try:
                    monto_val = float(str(txt_monto.value or "").replace("$", "").replace(".", "").replace(",", ".").strip())
                except ValueError:
                    monto_val = 0.0

                if monto_val <= 0:
                    self._mostrar_snackbar("El monto debe ser mayor a 0", "red")
                    return

                is_submitting_pago = True
                btn_confirmar_pago.disabled = True
                dlg.open = False
                self.safe_update()

                facturas_seleccionadas = None
                if doc_sel and doc_sel != "TODAS":
                    facturas_seleccionadas = {doc_sel: monto_val}

                ok = self.cartera_repo.registrar_pago_cartera(
                    id_cliente=cli.get("id_cliente"),
                    nombre_cliente=nom,
                    monto_total=monto_val,
                    metodo_pago=metodo,
                    banco_origen=dd_banco.value if metodo == "TRANSFERENCIA" else None,
                    referencia=txt_ref.value or "",
                    observaciones=txt_obs.value or "",
                    facturas_seleccionadas=facturas_seleccionadas,
                    usuario="admin",
                    vendedor_encargado=encargado_sel
                )

                if ok:
                    if encargado_sel and encargado_sel not in vendedores_disponibles:
                        self.clientes_repo.crear_encargado(encargado_sel)
                    doc_msg = f" a {doc_sel}" if (doc_sel and doc_sel != "TODAS") else ""
                    self._mostrar_snackbar(f"✓ Recaudo de ${monto_val:,.0f}{doc_msg} registrado con éxito.", "green")
                    self.load_data()
                else:
                    self._mostrar_snackbar("Error registrando pago en base de datos.", "red")

        btn_confirmar_pago = ft.ElevatedButton("Confirmar Recaudo", bgcolor=Config.COLOR_SUCCESS, color="white", on_click=guardar_pago)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Registrar Recaudo: {nom}", size=15, weight="bold", color=Config.COLOR_PRIMARY),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Saldo Pendiente Total: ${saldo_cliente:,.0f}", size=11.5, weight="bold", color="#DC2626" if saldo_cliente > 0 else "grey"),
                    dd_documento,
                    txt_monto,
                    row_mixto_montos,
                    lbl_total_mixto,
                    dd_metodo,
                    dd_banco,
                    txt_ref,
                    box_encargado_inteligente,
                    txt_obs
                ], spacing=8, tight=True, scroll=ft.ScrollMode.AUTO),
                width=460,
                height=480
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal(dlg)),
                btn_confirmar_pago
            ]
        )

        if self.page:
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

    # ==========================================
    # MODAL: GENERAR INFORME DE FACTURAS
    # ==========================================
    def _abrir_modal_informe_facturas(self, cli: dict):
        """
        Abre un modal detallado con todas las facturas del cliente (pagadas, parciales, pendientes).
        Permite filtrar por período, estado, tipo de documento o texto de búsqueda,
        seleccionar facturas con casillas de verificación (checkboxes),
        actualizar KPIs en tiempo real y exportar en PDF o copiar al portapapeles.
        """
        if not cli:
            self._mostrar_snackbar("Selecciona un cliente para generar su informe.", "amber800")
            return

        nom_cliente = cli.get("nombre", "")
        vendedor = (cli.get("vendedor_encargado") or "").strip() or "Sin Asignar"
        comision_pct = float(cli.get("porcentaje_comision") or 0.0)

        # Facturas del cliente cargadas actualmente
        facturas_totales = list(self.facturas_cliente or [])
        if not facturas_totales:
            self._mostrar_snackbar("Este cliente no tiene facturas para generar informe.", "amber800")
            return

        # Extraer periodos disponibles (YYYY-MM)
        periodos_set = set()
        for f in facturas_totales:
            fec = str(f.get("fecha") or "")
            if len(fec) >= 7 and "-" in fec:
                periodos_set.add(fec[:7])
        periodos_ordenados = sorted(list(periodos_set), reverse=True)

        # Set de facturas seleccionadas (por defecto todas seleccionadas)
        seleccionadas = set(str(f.get("factura_no")) for f in facturas_totales)

        # Controles de filtros
        dd_periodo_opts = [ft.dropdown.Option("TODOS", "Todos los períodos")] + [
            ft.dropdown.Option(p, f"Período {p}") for p in periodos_ordenados
        ]

        # Período inicial: coincide con el selector superior si existe en las facturas
        periodo_activo = self.periodo_selector.get_periodo_actual() if hasattr(self, "periodo_selector") else None
        periodo_inicial = periodo_activo if periodo_activo in periodos_set else "TODOS"

        dd_periodo = ft.Dropdown(
            label="Período",
            value=periodo_inicial,
            options=dd_periodo_opts,
            dense=True,
            text_size=11,
            width=165
        )

        dd_estado = ft.Dropdown(
            label="Estado",
            value="TODOS",
            options=[
                ft.dropdown.Option("TODOS", "Todos los estados"),
                ft.dropdown.Option("CON_SALDO", "Con saldo / Pendientes"),
                ft.dropdown.Option("PAGADA", "Pagadas (Al día)"),
                ft.dropdown.Option("PARCIAL", "Abono parcial"),
            ],
            dense=True,
            text_size=11,
            width=165
        )

        dd_tipo_doc = ft.Dropdown(
            label="Tipo Documento",
            value="TODOS",
            options=[
                ft.dropdown.Option("TODOS", "Todos los tipos"),
                ft.dropdown.Option("REMISIÓN", "Remisión"),
                ft.dropdown.Option("FACTURA_POS", "Factura POS"),
            ],
            dense=True,
            text_size=11,
            width=150
        )

        txt_buscar = ft.TextField(
            label="Buscar factura...",
            hint_text="No. doc o tipo",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            dense=True,
            text_size=11,
            expand=True,
            height=38
        )

        chk_todos = ft.Checkbox(
            label="Seleccionar Todo (Visibles)",
            value=True
        )

        # Tarjetas KPI dinámicas del modal
        lbl_kpi_facturado = ft.Text("$0", size=15, weight="bold", color=Config.COLOR_PRIMARY)
        lbl_kpi_abonado = ft.Text("$0", size=15, weight="bold", color=Config.COLOR_SUCCESS)
        lbl_kpi_pendiente = ft.Text("$0", size=15, weight="bold", color="#DC2626")
        lbl_kpi_conteo = ft.Text("0 facturas", size=10.5, color=Config.COLOR_TEXT_MUTED, weight="w500")

        card_facturado = ft.Container(
            content=ft.Column([
                ft.Text("Total Facturado", size=9.5, color=Config.COLOR_TEXT_MUTED, weight="w500"),
                lbl_kpi_facturado
            ], spacing=1),
            bgcolor="#F8FAFC",
            border=ft.border.all(1, Config.COLOR_BORDER),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=8,
            expand=True
        )

        card_abonado = ft.Container(
            content=ft.Column([
                ft.Text("Total Abonado", size=9.5, color=Config.COLOR_TEXT_MUTED, weight="w500"),
                lbl_kpi_abonado
            ], spacing=1),
            bgcolor="#F0FDF4",
            border=ft.border.all(1, "#BBF7D0"),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=8,
            expand=True
        )

        card_pendiente = ft.Container(
            content=ft.Column([
                ft.Text("Saldo Pendiente", size=9.5, color=Config.COLOR_TEXT_MUTED, weight="w500"),
                lbl_kpi_pendiente
            ], spacing=1),
            bgcolor="#FEF2F2",
            border=ft.border.all(1, "#FECACA"),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=8,
            expand=True
        )

        row_kpis_modal = ft.Row([
            card_facturado,
            card_abonado,
            card_pendiente,
        ], spacing=8)

        # DataTable del Modal
        dt_modal = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("", size=10)),
                ft.DataColumn(ft.Text("Fecha", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Tipo", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Factura No.", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Total Factura", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Total Abonado", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Saldo Pendiente", size=11, weight="bold")),
                ft.DataColumn(ft.Text("Estado", size=11, weight="bold")),
            ],
            rows=[],
            heading_row_height=30,
            data_row_min_height=28,
            data_row_max_height=32,
            column_spacing=10,
            heading_row_color=Config.COLOR_MUTED
        )

        container_tabla_modal = ft.Container(
            content=ft.ListView([dt_modal], expand=True),
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=8,
            height=280,
            expand=True
        )

        facturas_visibles_actuales = []

        def recalcular_totales():
            tot_f = 0.0
            tot_a = 0.0
            tot_p = 0.0
            cnt_sel = 0

            for f in facturas_visibles_actuales:
                fno = str(f.get("factura_no"))
                if fno in seleccionadas:
                    cnt_sel += 1
                    tot_f += float(f.get("total_factura") or 0.0)
                    tot_a += float(f.get("total_abonado") or 0.0)
                    tot_p += float(f.get("saldo_pendiente") or 0.0)

            lbl_kpi_facturado.value = f"${tot_f:,.0f}"
            lbl_kpi_abonado.value = f"${tot_a:,.0f}"
            lbl_kpi_pendiente.value = f"${tot_p:,.0f}"
            lbl_kpi_conteo.value = f"{cnt_sel} de {len(facturas_visibles_actuales)} visibles seleccionadas ({len(facturas_totales)} en total)"

            if facturas_visibles_actuales:
                todos_marcados = all(str(f.get("factura_no")) in seleccionadas for f in facturas_visibles_actuales)
                chk_todos.value = todos_marcados
            else:
                chk_todos.value = False

            if self.page:
                self.page.update()

        def on_check_fila(fno: str, valor: bool):
            if valor:
                seleccionadas.add(fno)
            else:
                seleccionadas.discard(fno)
            recalcular_totales()

        def on_toggle_todos(e):
            nuevo_val = bool(chk_todos.value)
            for f in facturas_visibles_actuales:
                fno = str(f.get("factura_no"))
                if nuevo_val:
                    seleccionadas.add(fno)
                else:
                    seleccionadas.discard(fno)
            actualizar_filas_tabla()
            recalcular_totales()

        chk_todos.on_change = on_toggle_todos

        def actualizar_filas_tabla():
            nonlocal facturas_visibles_actuales
            f_per = dd_periodo.value
            f_est = dd_estado.value
            f_tipo = dd_tipo_doc.value
            busq = (txt_buscar.value or "").strip().upper()

            visibles = []
            for f in facturas_totales:
                fec = str(f.get("fecha") or "")
                fac_no = str(f.get("factura_no") or "")
                tipo = str(f.get("tipo_documento") or "")
                est = str(f.get("estado_factura") or "PENDIENTE")
                saldo = float(f.get("saldo_pendiente") or 0.0)

                # Filtro periodo
                if f_per != "TODOS" and not fec.startswith(f_per):
                    continue

                # Filtro estado
                if f_est == "CON_SALDO" and saldo <= 0.01:
                    continue
                if f_est == "PAGADA" and est != "PAGADA":
                    continue
                if f_est == "PARCIAL" and est != "PARCIAL":
                    continue

                # Filtro tipo
                if f_tipo == "REMISIÓN" and "REM" not in tipo.upper():
                    continue
                if f_tipo in ("FACTURA_POS", "POS") and "POS" not in tipo.upper():
                    continue

                # Filtro búsqueda
                if busq:
                    if busq not in fac_no.upper() and busq not in tipo.upper() and busq not in fec:
                        continue

                visibles.append(f)

            facturas_visibles_actuales = visibles
            dt_modal.rows.clear()

            for f in facturas_visibles_actuales:
                fac_no = str(f.get("factura_no", ""))
                is_checked = fac_no in seleccionadas
                est = f.get("estado_factura", "PENDIENTE")
                saldo_f = float(f.get("saldo_pendiente", 0.0))

                if est == "PAGADA":
                    b_bg, b_fg, b_tx = "#DCFCE7", "#16A34A", "PAGADA"
                elif est == "PARCIAL":
                    b_bg, b_fg, b_tx = "#FEF3C7", "#D97706", "PARCIAL"
                else:
                    b_bg, b_fg, b_tx = "#FEE2E2", "#DC2626", "PENDIENTE"

                chk_fila = ft.Checkbox(
                    value=is_checked,
                    on_change=lambda e, fno=fac_no: on_check_fila(fno, e.control.value)
                )

                dt_modal.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(chk_fila),
                        ft.DataCell(ft.Text(f.get("fecha", ""), size=10.5)),
                        ft.DataCell(ft.Text(f.get("tipo_documento", "POS"), size=10.5)),
                        ft.DataCell(ft.Text(fac_no, size=10.5, weight="bold")),
                        ft.DataCell(ft.Text(f"${f.get('total_factura', 0.0):,.0f}", size=10.5)),
                        ft.DataCell(ft.Text(f"${f.get('total_abonado', 0.0):,.0f}", size=10.5, color=Config.COLOR_SUCCESS)),
                        ft.DataCell(ft.Text(f"${saldo_f:,.0f}", size=10.5, weight="bold", color="#DC2626" if saldo_f > 0 else "grey")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(b_tx, size=8.5, weight="bold", color=b_fg),
                                bgcolor=b_bg,
                                padding=ft.padding.symmetric(horizontal=5, vertical=1),
                                border_radius=4
                            )
                        )
                    ])
                )

        def on_filtro_change(e):
            actualizar_filas_tabla()
            recalcular_totales()

        dd_periodo.on_change = on_filtro_change
        dd_estado.on_change = on_filtro_change
        dd_tipo_doc.on_change = on_filtro_change
        txt_buscar.on_change = on_filtro_change

        # Inicializar filas y métricas
        actualizar_filas_tabla()
        recalcular_totales()

        # Botón 1: Copiar al Portapapeles
        def copiar_al_portapapeles(e):
            facturas_a_incluir = [f for f in facturas_visibles_actuales if str(f.get("factura_no")) in seleccionadas]
            if not facturas_a_incluir:
                self._mostrar_snackbar("No hay facturas seleccionadas para copiar.", "amber800")
                return

            tot_f = sum(float(f.get("total_factura") or 0.0) for f in facturas_a_incluir)
            tot_a = sum(float(f.get("total_abonado") or 0.0) for f in facturas_a_incluir)
            tot_p = sum(float(f.get("saldo_pendiente") or 0.0) for f in facturas_a_incluir)

            p_texto = f"Período: {dd_periodo.value}" if dd_periodo.value != "TODOS" else "Período: Todos los períodos"
            fecha_gen = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")

            lineas = [
                "====================================================",
                "TIENDA Y ABARROTES LOS DESECHABLES DE DOÑA MARY SAS",
                "ESTADO DE CUENTA / INFORME DE FACTURAS",
                "====================================================",
                f"Cliente: {nom_cliente}",
                f"Vendedor Encargado: {vendedor}",
                f"{p_texto}",
                f"Fecha de Generación: {fecha_gen}",
                "----------------------------------------------------",
                "RESUMEN CONSOLIDADO:",
                f"• Facturas Seleccionadas: {len(facturas_a_incluir)}",
                f"• Total Facturado: ${tot_f:,.0f}",
                f"• Total Abonado: ${tot_a:,.0f}",
                f"• Saldo Total Pendiente: ${tot_p:,.0f}",
                "----------------------------------------------------",
                "DETALLE DE FACTURAS:",
            ]

            for idx, f in enumerate(facturas_a_incluir, 1):
                fno = f.get("factura_no", "")
                fec = f.get("fecha", "")
                tipo = f.get("tipo_documento", "Factura")
                tf = float(f.get("total_factura") or 0.0)
                ta = float(f.get("total_abonado") or 0.0)
                sp = float(f.get("saldo_pendiente") or 0.0)
                est = f.get("estado_factura", "PENDIENTE")

                lineas.append(
                    f"{idx}. Factura #{fno} ({fec}) [{tipo}]\n"
                    f"   Total: ${tf:,.0f} | Abonado: ${ta:,.0f} | Saldo: ${sp:,.0f} | Estado: {est}"
                )

            lineas.append("====================================================")
            texto_completo = "\n".join(lineas)

            if self.page:
                self.page.set_clipboard(texto_completo)
                self._mostrar_snackbar("✓ Informe copiado al portapapeles. Listo para pegar.", "green")

        # Botón 2: Exportar a PDF
        def exportar_pdf(e):
            facturas_a_incluir = [f for f in facturas_visibles_actuales if str(f.get("factura_no")) in seleccionadas]
            if not facturas_a_incluir:
                self._mostrar_snackbar("No hay facturas seleccionadas para generar el PDF.", "amber800")
                return

            try:
                tot_f = sum(float(f.get("total_factura") or 0.0) for f in facturas_a_incluir)
                tot_a = sum(float(f.get("total_abonado") or 0.0) for f in facturas_a_incluir)
                tot_p = sum(float(f.get("saldo_pendiente") or 0.0) for f in facturas_a_incluir)

                periodo_label = f"Período: {dd_periodo.value}" if dd_periodo.value != "TODOS" else "Período: Todos los períodos"
                fecha_gen = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")

                class ClienteInformePDF(FPDF):
                    def header(self):
                        self.set_font("Arial", "B", 12)
                        self.set_text_color(15, 23, 42)
                        self.cell(0, 6, clean_fpdf_str("TIENDA Y ABARROTES LOS DESECHABLES DE DOÑA MARY SAS"), ln=True, align="C")
                        self.set_font("Arial", "B", 10)
                        self.set_text_color(37, 99, 235)
                        self.cell(0, 5, clean_fpdf_str("ESTADO DE CUENTA / INFORME DETALLADO DE FACTURAS"), ln=True, align="C")
                        self.set_font("Arial", "", 8)
                        self.set_text_color(100, 116, 139)
                        self.cell(0, 4, f"Generado el: {fecha_gen}", ln=True, align="C")
                        self.ln(3)
                        self.set_draw_color(226, 232, 240)
                        self.set_line_width(0.4)
                        self.line(10, self.get_y(), 200, self.get_y())
                        self.ln(4)

                    def footer(self):
                        self.set_y(-15)
                        self.set_font("Arial", "I", 8)
                        self.set_text_color(148, 163, 184)
                        self.cell(0, 10, clean_fpdf_str(f"Página {self.page_no()}/{{nb}} • Sistema Doña Mary SAS"), align="C")

                pdf = ClienteInformePDF(orientation="P", unit="mm", format="A4")
                pdf.alias_nb_pages()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)

                # Info Box Cliente
                pdf.set_fill_color(248, 250, 252)
                pdf.set_draw_color(203, 213, 225)
                pdf.rect(10, pdf.get_y(), 190, 24, "FD")

                y_box = pdf.get_y() + 3
                pdf.set_xy(14, y_box)
                pdf.set_font("Arial", "B", 10)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(90, 5, clean_fpdf_str(f"CLIENTE: {nom_cliente}"), ln=False)
                pdf.set_font("Arial", "", 9)
                pdf.set_text_color(71, 85, 105)
                pdf.cell(90, 5, clean_fpdf_str(f"VENDEDOR: {vendedor}"), ln=True)

                pdf.set_x(14)
                pdf.cell(90, 5, clean_fpdf_str(periodo_label), ln=False)
                pdf.cell(90, 5, clean_fpdf_str(f"FACTURAS SELECCIONADAS: {len(facturas_a_incluir)}"), ln=True)

                pdf.set_x(14)
                pdf.set_font("Arial", "B", 9)
                pdf.set_text_color(220, 38, 38)
                pdf.cell(90, 5, clean_fpdf_str(f"SALDO TOTAL PENDIENTE: ${tot_p:,.0f}"), ln=False)
                pdf.set_text_color(22, 163, 74)
                pdf.cell(90, 5, clean_fpdf_str(f"TOTAL ABONADO: ${tot_a:,.0f}"), ln=True)

                pdf.set_y(y_box + 26)

                # Tabla Header
                pdf.set_fill_color(15, 23, 42)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", "B", 8.5)

                col_w = [24, 28, 30, 28, 28, 28, 24]
                headers = ["FECHA", "TIPO DOC.", "FACTURA NO.", "TOTAL FAC.", "TOTAL ABON.", "SALDO PEND.", "ESTADO"]
                for w, h in zip(col_w, headers):
                    pdf.cell(w, 7, clean_fpdf_str(h), border=1, align="C", fill=True)
                pdf.ln(7)

                pdf.set_font("Arial", "", 8)
                for idx, r in enumerate(facturas_a_incluir):
                    fill = (idx % 2 == 1)
                    pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
                    pdf.set_text_color(15, 23, 42)

                    r_fec = str(r.get("fecha") or "")
                    r_tipo = str(r.get("tipo_documento") or "Factura")
                    r_fac = str(r.get("factura_no") or "")
                    r_tot = float(r.get("total_factura") or 0.0)
                    r_ab = float(r.get("total_abonado") or 0.0)
                    r_saldo = float(r.get("saldo_pendiente") or 0.0)
                    r_est = str(r.get("estado_factura") or "PENDIENTE")

                    pdf.cell(col_w[0], 6, r_fec, border="LRB", align="C", fill=fill)
                    pdf.cell(col_w[1], 6, clean_fpdf_str(r_tipo), border="LRB", align="L", fill=fill)

                    pdf.set_font("Arial", "B", 8)
                    pdf.cell(col_w[2], 6, r_fac, border="LRB", align="C", fill=fill)

                    pdf.set_font("Arial", "", 8)
                    pdf.cell(col_w[3], 6, f"${r_tot:,.0f}", border="LRB", align="R", fill=fill)

                    pdf.set_text_color(22, 163, 74)
                    pdf.cell(col_w[4], 6, f"${r_ab:,.0f}", border="LRB", align="R", fill=fill)

                    if r_saldo > 0:
                        pdf.set_font("Arial", "B", 8)
                        pdf.set_text_color(220, 38, 38)
                    else:
                        pdf.set_font("Arial", "", 8)
                        pdf.set_text_color(100, 116, 139)
                    pdf.cell(col_w[5], 6, f"${r_saldo:,.0f}", border="LRB", align="R", fill=fill)

                    pdf.set_font("Arial", "B", 7.5)
                    if r_est == "PAGADA":
                        pdf.set_text_color(22, 163, 74)
                    elif r_est == "PARCIAL":
                        pdf.set_text_color(217, 119, 6)
                    else:
                        pdf.set_text_color(220, 38, 38)
                    pdf.cell(col_w[6], 6, r_est, border="LRB", align="C", fill=fill)
                    pdf.ln(6)

                # Totales Finales
                pdf.ln(3)
                pdf.set_fill_color(241, 245, 249)
                pdf.set_draw_color(203, 213, 225)
                pdf.set_font("Arial", "B", 8.5)
                pdf.set_text_color(15, 23, 42)

                pdf.cell(col_w[0] + col_w[1] + col_w[2], 7, "TOTALES CONSOLIDADOS (SELECCIÓN):", border=1, align="R", fill=True)
                pdf.cell(col_w[3], 7, f"${tot_f:,.0f}", border=1, align="R", fill=True)
                pdf.set_text_color(22, 163, 74)
                pdf.cell(col_w[4], 7, f"${tot_a:,.0f}", border=1, align="R", fill=True)
                pdf.set_text_color(220, 38, 38)
                pdf.cell(col_w[5], 7, f"${tot_p:,.0f}", border=1, align="R", fill=True)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(col_w[6], 7, "-", border=1, align="C", fill=True)
                pdf.ln(8)

                # Guardar PDF
                user_home = os.path.expanduser("~")
                downloads_dir = os.path.join(user_home, "Downloads")
                if not os.path.exists(downloads_dir):
                    downloads_dir = tempfile.gettempdir()

                nom_sanitizado = "".join(c for c in nom_cliente if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
                ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Informe_Cartera_{nom_sanitizado}_{ts_str}.pdf"
                out_path = os.path.join(downloads_dir, filename)

                pdf.output(out_path)

                if os.path.exists(out_path):
                    try:
                        os.startfile(out_path)
                    except Exception:
                        pass
                    self._mostrar_snackbar(f"✓ PDF generado: {filename}", "green")
                else:
                    self._mostrar_snackbar("Error generando archivo PDF.", "red")

            except Exception as ex:
                log_error("CarteraView.exportar_pdf", ex)
                self._mostrar_snackbar(f"Error generando PDF: {ex}", "red")

        # Botones de Acción en el pie del modal
        btn_copiar = ft.ElevatedButton(
            text="Copiar al Portapapeles",
            icon=ft.icons.COPY_ALL_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=36,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=copiar_al_portapapeles
        )

        btn_pdf = ft.ElevatedButton(
            text="Descargar PDF",
            icon=ft.icons.PICTURE_AS_PDF_ROUNDED,
            bgcolor="#DC2626",
            color="white",
            height=36,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=exportar_pdf
        )

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.ASSESSMENT_ROUNDED, color=Config.COLOR_PRIMARY, size=24),
                ft.Column([
                    ft.Text(f"Informe de Facturas: {nom_cliente}", size=15, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Text(f"Vendedor: {vendedor} | Filtra, selecciona con casilla y exporta el reporte", size=10.5, color=Config.COLOR_TEXT_MUTED)
                ], spacing=1, expand=True),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            content=ft.Container(
                content=ft.Column([
                    # Fila 1: Filtros
                    ft.Row([
                        dd_periodo,
                        dd_estado,
                        dd_tipo_doc,
                        txt_buscar
                    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                    # Fila 2: KPIs dinámicos
                    row_kpis_modal,

                    # Fila 3: Selección y tabla
                    ft.Row([
                        chk_todos,
                        ft.Container(expand=True),
                        lbl_kpi_conteo
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                    container_tabla_modal
                ], spacing=8, tight=True),
                width=800,
                height=480
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self._cerrar_modal(dlg)),
                btn_copiar,
                btn_pdf
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
        is_submitting = False

        def anular(e):
            nonlocal is_submitting
            if is_submitting:
                return
            is_submitting = True
            btn_anular_confirm.disabled = True
            dlg.open = False
            self.safe_update()

            ok = self.cartera_repo.anular_pago_cartera(id_pago)
            if ok:
                self._mostrar_snackbar("✓ Recaudo anulado exitosamente.", "orange800")
                self.load_data()
            else:
                self._mostrar_snackbar("Error anulando recaudo.", "red")

        btn_anular_confirm = ft.ElevatedButton("Sí, Anular Pago", bgcolor="red800", color="white", on_click=anular)

        dlg = ft.AlertDialog(
            title=ft.Text("¿Anular Recaudo?", size=15, weight="bold", color="red800"),
            content=ft.Text("Esta acción revertirá el pago y restaurará los saldos adeudados en las facturas.", size=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal(dlg)),
                btn_anular_confirm
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
