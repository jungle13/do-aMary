"""
Vista de Cierre de Inventario, Auditoría y Conciliación Mensual.
Integra la experiencia ágil de registro rápido, buscador inteligente,
cálculo de rentabilidad por periodo y generación de ajustes prediligenciados.
"""
import flet as ft
import threading
import datetime
import math
from config import Config
from core.supabase_client import SupabaseClient
from core.repositories.cierres_repo import CierresRepository
from core.repositories.insumos_repo import InsumosRepository
from ui.views.conteo_inicial import ConteoInicialView
from core.mobile_service import MobileCountingService
from core.mobile_server import iniciar_servidor_en_hilo
from core.logger import get_logger, log_error

logger = get_logger("CierreInventarioView")

class CierreInventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        self.cierres_repo = CierresRepository()
        self.insumos_repo = InsumosRepository()
        self.mobile_service = MobileCountingService()

        # Variables de Estado
        self.mes_seleccionado = datetime.date.today().strftime('%Y-%m')
        self.periodos_data = []
        self.insumos_lista = []
        self.insumos_filtrados = []
        self.datos_cierre = {}
        self.insumo_activo = None

        # Paginación
        self.page_size = 20
        self.current_page = 1
        self.total_pages = 1

        # Filtros
        self.filtro_busqueda = ""
        self.filtro_categoria = "Todas"
        self.filtro_estado = "Todos"

        # --- VISTAS HIJAS ---
        self.vista_lista = ft.Container(expand=True, padding=24)
        self.vista_detalle = ft.Container(expand=True, padding=24, visible=False)
        self.vista_conteo_container = ft.Container(expand=True, visible=False)

        # ==========================================
        # 1. COMPONENTES: VISTA HISTORIAL DE PERIODOS
        # ==========================================
        self.dt_periodos = ft.DataTable(
            column_spacing=24,
            heading_row_color=ft.colors.with_opacity(0.04, Config.COLOR_PRIMARY),
            data_row_min_height=48,
            data_row_max_height=48,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=10,
            columns=[
                ft.DataColumn(ft.Text("Periodo", weight="bold")),
                ft.DataColumn(ft.Text("Mes", weight="bold")),
                ft.DataColumn(ft.Text("Año", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Costo Inventario Total", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Ingresos del Mes", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Rentabilidad (%)", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[]
        )

        self._construir_vista_lista()

        # ==========================================
        # 2. CONTROLES VISTA DETALLE AUDITORÍA
        # ==========================================
        self.lbl_titulo_auditoria = ft.Text("Auditoría de Inventario", size=15, weight="bold", color=Config.COLOR_PRIMARY)
        self.badge_estado_auditoria = ft.Container(
            content=ft.Row([
                ft.Container(width=6, height=6, bgcolor="green", border_radius=3),
                ft.Text("ABIERTO", size=10, weight="bold", color="green")
            ], spacing=4, tight=True),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor=ft.colors.with_opacity(0.1, "green"),
            border_radius=10
        )

        # KPIs Superiores Compactos
        self.lbl_kpi_auditados = ft.Text("0 / 0", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_kpi_sobrantes = ft.Text("$0", size=14, weight="bold", color="green")
        self.lbl_kpi_faltantes = ft.Text("$0", size=14, weight="bold", color="red")
        self.lbl_kpi_neto = ft.Text("$0", size=14, weight="bold", color=Config.COLOR_ACCENT)

        # Formulario de Registro Rápido Compacto
        self.txt_buscar_rapido = ft.TextField(
            hint_text="Escribe código o nombre del insumo...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            bgcolor="white",
            border_radius=7,
            height=34,
            text_size=11.5,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            expand=True,
            on_change=self.on_buscar_sugerencias_rapidas
        )

        self.lv_sugerencias_rapidas = ft.ListView(spacing=2, height=110, visible=False)
        self.lbl_info_seleccionado = ft.Text("Ningún insumo seleccionado (haz clic en ✏️ en la tabla)", size=10.5, color=Config.COLOR_TEXT_MUTED)

        self.txt_cant_fisica = ft.TextField(
            label="Conteo Físico",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=7,
            height=34,
            text_size=11.5,
            width=135,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            text_align=ft.TextAlign.RIGHT
        )

        self.txt_costo_unit = ft.TextField(
            label="Costo Unit. ($)",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=7,
            height=34,
            text_size=11.5,
            width=130,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            text_align=ft.TextAlign.RIGHT
        )

        self.btn_guardar_conteo_rapido = ft.ElevatedButton(
            "✓ Guardar Conteo",
            bgcolor=Config.COLOR_SUCCESS,
            color="white",
            height=34,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=7),
                padding=ft.padding.symmetric(horizontal=12, vertical=0)
            ),
            on_click=self.on_guardar_conteo_rapido_click
        )

        # Filtros de Tabla Detalle Compactos
        self.input_filtro_tabla = ft.TextField(
            hint_text="Filtrar por código o nombre...",
            prefix_icon=ft.icons.FILTER_ALT_ROUNDED,
            bgcolor="white",
            border_radius=7,
            height=34,
            text_size=11.5,
            expand=True,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=self.on_filtro_detalle_change
        )

        self.drop_filtro_cat = ft.Dropdown(
            label="Categoría",
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            dense=True,
            width=140,
            height=34,
            text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=self.on_filtro_detalle_change
        )

        self.drop_filtro_est = ft.Dropdown(
            label="Estado",
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("PENDIENTE"),
                ft.dropdown.Option("CONCILIADO"),
                ft.dropdown.Option("DESCUADRADO"),
                ft.dropdown.Option("AJUSTADO")
            ],
            value="Todos",
            dense=True,
            width=130,
            height=34,
            text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=self.on_filtro_detalle_change
        )

        # Tabla de Auditoría Compacta
        self.dt_auditoria = ft.DataTable(
            column_spacing=10,
            heading_row_color=ft.colors.with_opacity(0.04, Config.COLOR_PRIMARY),
            data_row_min_height=32,
            data_row_max_height=36,
            heading_row_height=30,
            border=ft.border.all(1, ft.colors.with_opacity(0.08, "black")),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Insumo", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Inicial", weight="bold", size=11), numeric=True),
                ft.DataColumn(ft.Text("Sistema", weight="bold", size=11), numeric=True),
                ft.DataColumn(ft.Text("Físico", weight="bold", size=11), numeric=True),
                ft.DataColumn(ft.Text("Dif.", weight="bold", size=11), numeric=True),
                ft.DataColumn(ft.Text("Valor Total", weight="bold", size=11), numeric=True),
                ft.DataColumn(ft.Text("Estado", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Acciones", weight="bold", size=11)),
            ],
            rows=[]
        )

        # Paginación UI
        self.txt_paginacion = ft.Text("Página 1 de 1", size=12, color="grey", weight="bold")
        self.btn_pag_ant = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_pag_anterior, disabled=True)
        self.btn_pag_sig = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_pag_siguiente, disabled=True)

        self._construir_vista_detalle()

        # ==========================================
        # 3. MODAL DE AJUSTE AUTOMÁTICO
        # ==========================================
        self._construir_modal_ajuste()

        # Contenedor Principal
        self.content = ft.Stack([
            self.vista_lista,
            self.vista_detalle,
            self.vista_conteo_container
        ])

    def did_mount(self):
        if self.modal_ajuste not in self.page.overlay:
            self.page.overlay.append(self.modal_ajuste)
        self.cargar_historial_periodos()

    def _cerrar_dialogo(self, dlg):
        """Cierra un diálogo limpiamente notificando al motor gráfico de Flet."""
        try:
            if dlg:
                dlg.open = False
                self.safe_update()
        except Exception:
            pass

    def safe_update(self):
        try:
            if self.page and self.uid:
                self.page.update()
        except:
            pass

    def mostrar_alerta(self, msj: str, color: str = "green"):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msj, color="white"), bgcolor=color)
            self.page.snack_bar.open = True
            self.safe_update()

    # ==========================================
    # CONSTRUCCIÓN DE VISTAS (LAYOUTS)
    # ==========================================

    def _construir_vista_lista(self):
        header_lista = ft.Row([
            ft.Column([
                ft.Text("Historial de Periodos e Inventario", size=22, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Control mensual de cierres contables, auditorías y rentabilidad neta.", size=12, color=Config.COLOR_TEXT_MUTED)
            ], spacing=2),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "Actualizar Lista",
                icon=ft.icons.REFRESH_ROUNDED,
                bgcolor=Config.COLOR_PRIMARY,
                color="white",
                height=38,
                on_click=lambda e: self.cargar_historial_periodos()
            )
        ])

        card_tabla_periodos = ft.Container(
            content=ft.Column([
                ft.Row([self.dt_periodos], scroll=ft.ScrollMode.ADAPTIVE)
            ]),
            bgcolor="white",
            padding=16,
            border_radius=12,
            border=ft.border.all(1, Config.COLOR_BORDER),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.with_opacity(0.04, "black"))
        )

        self.vista_lista.content = ft.Column([
            header_lista,
            ft.Container(height=10),
            card_tabla_periodos
        ], spacing=12)

    def _construir_vista_detalle(self):
        # 1. Header Compacto
        header_detalle = ft.Row([
            ft.IconButton(ft.icons.ARROW_BACK_ROUNDED, icon_size=18, tooltip="Volver al Historial", on_click=self.on_volver_al_historial),
            self.lbl_titulo_auditoria,
            self.badge_estado_auditoria,
            ft.Container(expand=True),
            ft.ElevatedButton(
                "Actualizar",
                icon=ft.icons.REFRESH_ROUNDED,
                bgcolor=Config.COLOR_BACKGROUND,
                color=Config.COLOR_PRIMARY,
                height=32,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=7),
                    padding=ft.padding.symmetric(horizontal=10, vertical=0)
                ),
                tooltip="Recargar conteos y diferencias en tiempo real",
                on_click=lambda e: threading.Thread(target=self._worker_cargar_datos_auditoria, daemon=True).start()
            ),
            ft.ElevatedButton(
                "QR Móvil",
                icon=ft.icons.QR_CODE_SCANNER_ROUNDED,
                bgcolor=Config.COLOR_PRIMARY,
                color="white",
                height=32,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=7),
                    padding=ft.padding.symmetric(horizontal=10, vertical=0)
                ),
                on_click=self.abrir_modal_qr
            ),
            ft.ElevatedButton(
                "Cerrar Periodo",
                icon=ft.icons.LOCK_ROUNDED,
                bgcolor=Config.COLOR_ACCENT,
                color="white",
                height=32,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=7),
                    padding=ft.padding.symmetric(horizontal=10, vertical=0)
                ),
                on_click=self.on_aprobar_cierre_click
            )
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

        # 2. Tarjetas KPI Compactas
        def crear_kpi(titulo, lbl_control, icono, color_icon):
            return ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Icon(icono, color=color_icon, size=17), padding=6, bgcolor=ft.colors.with_opacity(0.12, color_icon), border_radius=8),
                    ft.Column([
                        ft.Text(titulo, size=9.5, color=Config.COLOR_TEXT_MUTED, weight="w500"),
                        lbl_control
                    ], spacing=0)
                ], spacing=8),
                bgcolor="white", padding=ft.padding.symmetric(horizontal=10, vertical=8), border_radius=10,
                border=ft.border.all(1, Config.COLOR_BORDER), expand=True,
                shadow=ft.BoxShadow(blur_radius=4, color=ft.colors.with_opacity(0.02, "black"))
            )

        row_kpis = ft.Row([
            crear_kpi("Insumos Auditados", self.lbl_kpi_auditados, ft.icons.CHECKLIST_RTL_ROUNDED, Config.COLOR_PRIMARY),
            crear_kpi("Ajustes Entrada (+)", self.lbl_kpi_sobrantes, ft.icons.ARROW_UPWARD_ROUNDED, "green"),
            crear_kpi("Ajustes Salida (-)", self.lbl_kpi_faltantes, ft.icons.ARROW_DOWNWARD_ROUNDED, "red"),
            crear_kpi("Impacto Neto Ajustes", self.lbl_kpi_neto, ft.icons.BALANCE_ROUNDED, Config.COLOR_ACCENT),
        ], spacing=8)

        # 3. Formulario Registro Rápido Compacto
        card_registro_rapido = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.EDIT_NOTE_ROUNDED, size=16, color=Config.COLOR_PRIMARY),
                    ft.Text("Registro Rápido de Conteo de Cierre", weight="bold", size=12, color=Config.COLOR_PRIMARY)
                ], spacing=4),
                ft.Row([
                    self.txt_buscar_rapido,
                    self.txt_cant_fisica,
                    self.txt_costo_unit,
                    self.btn_guardar_conteo_rapido
                ], spacing=8),
                self.lv_sugerencias_rapidas,
                self.lbl_info_seleccionado
            ], spacing=6),
            bgcolor="white", padding=10, border_radius=10,
            border=ft.border.all(1, Config.COLOR_BORDER),
            shadow=ft.BoxShadow(blur_radius=6, color=ft.colors.with_opacity(0.02, "black"))
        )

        # 4. Filtros y Tabla Compacta
        row_filtros = ft.Row([
            self.input_filtro_tabla,
            self.drop_filtro_cat,
            self.drop_filtro_est,
            ft.IconButton(
                icon=ft.icons.REFRESH_ROUNDED,
                icon_size=18,
                icon_color=Config.COLOR_PRIMARY,
                tooltip="Refrescar conteos y diferencias",
                on_click=lambda e: threading.Thread(target=self._worker_cargar_datos_auditoria, daemon=True).start()
            )
        ], spacing=8)

        card_tabla_auditoria = ft.Container(
            content=ft.Column([
                row_filtros,
                ft.Container(height=2),
                ft.Row([self.dt_auditoria], scroll=ft.ScrollMode.ADAPTIVE),
                ft.Container(height=2),
                ft.Row([
                    self.txt_paginacion,
                    ft.Container(expand=True),
                    self.btn_pag_ant,
                    self.btn_pag_sig
                ], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=6),
            bgcolor="white", padding=10, border_radius=10,
            border=ft.border.all(1, Config.COLOR_BORDER),
            shadow=ft.BoxShadow(blur_radius=6, color=ft.colors.with_opacity(0.02, "black"))
        )

        self.vista_detalle.content = ft.Column([
            header_detalle,
            row_kpis,
            card_registro_rapido,
            card_tabla_auditoria
        ], spacing=8, scroll=ft.ScrollMode.AUTO)

    def _construir_modal_ajuste(self):
        self.modal_txt_codigo = ft.TextField(label="Cód. Insumo", width=110, disabled=True)
        self.modal_txt_nombre = ft.Text("Nombre del Insumo", weight="bold", size=13, color=Config.COLOR_PRIMARY)
        self.modal_drop_tipo = ft.Dropdown(
            label="Tipo Ajuste",
            options=[ft.dropdown.Option("ENTRADA"), ft.dropdown.Option("SALIDA")],
            width=140,
            on_change=self._on_modal_tipo_change
        )
        self.modal_drop_motivo = ft.Dropdown(label="Motivo Específico", width=360)
        self.modal_txt_cant = ft.TextField(label="Cantidad Ajuste", width=140, on_change=self._calc_tot_modal_ajuste)
        self.modal_txt_costo = ft.TextField(label="Costo Unitario ($)", width=140, on_change=self._calc_tot_modal_ajuste)
        self.modal_lbl_total = ft.Text("$0", size=15, weight="bold", color=Config.COLOR_ACCENT)
        self.modal_txt_obs = ft.TextField(label="Observaciones (Opcional)", width=510)

        self.modal_ajuste = ft.AlertDialog(
            title=ft.Text("Registrar Ajuste de Auditoría", weight="bold"),
            content=ft.Container(
                width=520,
                content=ft.Column([
                    ft.Row([
                        self.modal_txt_codigo,
                        ft.Container(content=self.modal_txt_nombre, width=390, padding=10, bgcolor="#F8FAFC", border_radius=8)
                    ], spacing=10),
                    ft.Row([self.modal_drop_tipo, self.modal_drop_motivo], spacing=10),
                    ft.Row([self.modal_txt_cant, self.modal_txt_costo], spacing=10),
                    ft.Row([
                        ft.Text("Impacto Financiero:", size=13, weight="w500"),
                        self.modal_lbl_total
                    ], spacing=6),
                    self.modal_txt_obs
                ], tight=True, spacing=12)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal_ajuste()),
                ft.ElevatedButton("✓ Aplicar Ajuste", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=self._on_guardar_ajuste_modal)
            ]
        )

    # ==========================================
    # LÓGICA DE DATOS Y CARGA
    # ==========================================

    def cargar_historial_periodos(self):
        threading.Thread(target=self._worker_cargar_periodos, daemon=True).start()

    def _worker_cargar_periodos(self):
        periodos = self.cierres_repo.get_periodos_inventario()
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        filas = []
        for p in periodos:
            mes_periodo = p.get("mes_periodo", "")
            if not mes_periodo: continue

            parts = mes_periodo.split("-")
            year = parts[0]
            month_num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            month_nombre = meses_nombres[month_num - 1]

            import calendar
            last_day = calendar.monthrange(int(year), month_num)[1]
            fecha_corte_mes = f"{mes_periodo}-{last_day:02d}"

            # KPIs específicos para este periodo
            kpis_inv = self.db.get_inventario_kpis(fecha_corte=fecha_corte_mes)
            tot_costo_inv = float(kpis_inv.get("valor_inventario") or 0.0)

            res_v = self.db.get_ventas_summary(fecha_corte=fecha_corte_mes)
            res_c = self.db.get_compras_summary(fecha_corte=fecha_corte_mes)
            tot_ventas = float(res_v.get("total_mes") or 0.0)
            tot_compras = float(res_c.get("total_mes") or 0.0)
            rentabilidad = ((tot_ventas - tot_compras) / tot_ventas * 100) if tot_ventas > 0 else 0.0

            estado = p.get("estado", "ABIERTO")
            color_est = {"ABIERTO": "green", "EN_AUDITORIA": "blue", "CERRADO": "red"}.get(estado, "black")

            btn_inventario_texto = f"Inventario ({month_nombre})"

            fila = ft.DataRow(cells=[
                ft.DataCell(ft.Text(mes_periodo, weight="bold")),
                ft.DataCell(ft.Text(month_nombre)),
                ft.DataCell(ft.Text(year)),
                ft.DataCell(ft.Container(
                    content=ft.Text(estado, size=11, weight="bold", color=color_est),
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    bgcolor=ft.colors.with_opacity(0.1, color_est),
                    border_radius=8
                )),
                ft.DataCell(ft.Text(f"${tot_costo_inv:,.0f}", weight="bold")),
                ft.DataCell(ft.Text(f"${tot_ventas:,.0f}", weight="bold", color="green700")),
                ft.DataCell(ft.Container(
                    content=ft.Text(f"{rentabilidad:+.1f}%", size=11, weight="bold", color="green" if rentabilidad >= 0 else "red"),
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    bgcolor=ft.colors.with_opacity(0.1, "green" if rentabilidad >= 0 else "red"),
                    border_radius=8
                )),
                ft.DataCell(
                    ft.Row([
                        ft.ElevatedButton(
                            "Conteo",
                            icon=ft.icons.CHECKLIST_RTL_ROUNDED,
                            bgcolor=Config.COLOR_PRIMARY,
                            color="white",
                            height=32,
                            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=4)),
                            tooltip=f"Conteo y Stock Inicial de {month_nombre}",
                            on_click=lambda e, m=mes_periodo: self.mostrar_conteo(m)
                        ),
                        ft.ElevatedButton(
                            btn_inventario_texto,
                            icon=ft.icons.INVENTORY_ROUNDED,
                            bgcolor=Config.COLOR_ACCENT,
                            color="white",
                            height=32,
                            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=4)),
                            tooltip=f"Auditoría y Conciliación de {month_nombre}",
                            on_click=lambda e, m=mes_periodo, nom=month_nombre, a=year: self.mostrar_auditoria(m, nom, a)
                        )
                    ], spacing=6)
                )
            ])
            filas.append(fila)

        self.dt_periodos.rows = filas
        self.safe_update()

    def mostrar_conteo(self, mes: str):
        self.vista_lista.visible = False
        self.vista_detalle.visible = False
        self.vista_conteo_container.content = ConteoInicialView(mes_periodo=mes, on_volver=self.on_volver_al_historial)
        self.vista_conteo_container.visible = True
        self.safe_update()

    def mostrar_auditoria(self, mes: str, mes_nombre: str, year: str):
        self.mes_seleccionado = mes
        self.lbl_titulo_auditoria.value = f"Inventario y Auditoría • {mes_nombre} {year}"
        self.vista_lista.visible = False
        self.vista_conteo_container.visible = False
        self.vista_detalle.visible = True
        self.current_page = 1
        self.safe_update()

        threading.Thread(target=self._worker_cargar_datos_auditoria, daemon=True).start()

    def on_volver_al_historial(self, e=None):
        self.vista_detalle.visible = False
        self.vista_conteo_container.visible = False
        self.vista_conteo_container.content = None
        self.vista_lista.visible = True
        self.cargar_historial_periodos()
        self.safe_update()

    def _worker_cargar_datos_auditoria(self):
        data = self.cierres_repo.obtener_estado_cierre(self.mes_seleccionado)
        self.datos_cierre = data if isinstance(data, dict) else {}
        self.insumos_lista = self.datos_cierre.get("insumos", [])

        # Categorías únicas
        cats = sorted(list(set(i.get("categoria") or "GENERAL" for i in self.insumos_lista)))
        self.drop_filtro_cat.options = [ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in cats]

        self._filtrar_y_renderizar_tabla()

    def _filtrar_y_renderizar_tabla(self):
        q = (self.input_filtro_tabla.value or "").strip().lower()
        cat = self.drop_filtro_cat.value or "Todas"
        est = self.drop_filtro_est.value or "Todos"

        filtrados = []
        sobrantes_tot = 0.0
        faltantes_tot = 0.0
        auditados_count = 0

        for item in self.insumos_lista:
            cod = str(item.get("codigo_insumo", "")).lower()
            nom = str(item.get("nombre", "")).lower()
            c_cat = item.get("categoria") or "GENERAL"
            
            # Cantidades
            fisico = item.get("cantidad_fisica")
            teorico = float(item.get("cantidad_sistema") if item.get("cantidad_sistema") is not None else (item.get("stock_actual") or 0.0))
            costo = float(item.get("costo_unitario_snapshot") or item.get("costo_unitario") or 0.0)

            # Determinar estado
            if fisico is not None:
                auditados_count += 1
                dif = float(fisico) - teorico
                if item.get("estado") == "AJUSTADO":
                    estado_ui = "AJUSTADO"
                    if dif > 0: sobrantes_tot += (dif * costo)
                    else: faltantes_tot += (abs(dif) * costo)
                elif abs(dif) < 0.001:
                    estado_ui = "CONCILIADO"
                else:
                    estado_ui = "DESCUADRADO"
                    if dif > 0: sobrantes_tot += (dif * costo)
                    else: faltantes_tot += (abs(dif) * costo)
            else:
                estado_ui = "PENDIENTE"

            item["_estado_ui"] = estado_ui
            item["_diferencia"] = (float(fisico) - teorico) if fisico is not None else None

            # Filtros
            if q and (q not in cod and q not in nom):
                continue
            if cat != "Todas" and c_cat != cat:
                continue
            if est != "Todos" and estado_ui != est:
                continue

            filtrados.append(item)

        self.insumos_filtrados = filtrados
        tot_items = len(self.insumos_lista)
        self.lbl_kpi_auditados.value = f"{auditados_count} / {tot_items}"
        self.lbl_kpi_sobrantes.value = f"+${sobrantes_tot:,.0f}"
        self.lbl_kpi_faltantes.value = f"-${faltantes_tot:,.0f}"
        neto = sobrantes_tot - faltantes_tot
        self.lbl_kpi_neto.value = f"{neto:+,.0f}" if neto != 0 else "$0"

        # Paginación
        self.total_pages = max(1, math.ceil(len(filtrados) / self.page_size))
        self.current_page = min(self.current_page, self.total_pages)

        # Renderizar filas
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_items = filtrados[start_idx:end_idx]

        filas = []
        for it in page_items:
            cod = it.get("codigo_insumo", "")
            nom = it.get("nombre", "")
            c_cat = it.get("categoria", "GENERAL")
            inicial = float(it.get("stock_inicial") or 0.0)
            teorico = float(it.get("stock_actual") or it.get("cantidad_sistema") or 0.0)
            fisico = it.get("cantidad_fisica")
            costo = float(it.get("costo_unitario_snapshot") or it.get("costo_unitario") or 0.0)
            est_ui = it.get("_estado_ui", "PENDIENTE")
            dif = it.get("_diferencia")

            # Color Estado
            color_map = {
                "PENDIENTE": "orange",
                "CONCILIADO": "green",
                "DESCUADRADO": "red",
                "AJUSTADO": "blue"
            }
            color_badge = color_map.get(est_ui, "grey")

            # Texto Diferencia
            if dif is None:
                txt_dif = ft.Text("-", color="grey")
            elif dif == 0:
                txt_dif = ft.Text("0.0", color="green", weight="bold")
            elif dif > 0:
                txt_dif = ft.Text(f"+{dif:g}", color="green", weight="bold")
            else:
                txt_dif = ft.Text(f"{dif:g}", color="red", weight="bold")

            val_total = (float(fisico) * costo) if fisico is not None else 0.0
            audit_info = it.get("observacion") or "Sin registrar"
            if it.get("usuario_conteo"):
                audit_info = f"{it.get('usuario_conteo')}"

            # Botones de Acción
            btn_ojo = ft.IconButton(
                icon=ft.icons.REMOVE_RED_EYE_ROUNDED,
                icon_color=Config.COLOR_ACCENT,
                icon_size=17,
                tooltip="Ver Historial de Conteos y Auditoría",
                on_click=lambda e, item_sel=it: self.mostrar_modal_historial_insumo(item_sel)
            )

            btn_lapiz = ft.IconButton(
                icon=ft.icons.EDIT_ROUNDED,
                icon_color=Config.COLOR_PRIMARY,
                icon_size=17,
                tooltip="Digitar Conteo Físico",
                on_click=lambda e, item_sel=it: self.seleccionar_insumo_para_conteo(item_sel)
            )

            btn_eliminar = ft.IconButton(
                icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                icon_color="red600",
                icon_size=17,
                tooltip="Eliminar Conteo Físico",
                visible=(fisico is not None),
                on_click=lambda e, item_sel=it: self.confirmar_eliminar_conteo(item_sel)
            )

            acciones_row = [btn_ojo, btn_lapiz, btn_eliminar]

            # Botón Ajuste (solo si hay descuadre y no está ajustado)
            if est_ui == "DESCUADRADO" and dif is not None and dif != 0:
                btn_ajuste = ft.ElevatedButton(
                    "Ajuste",
                    icon=ft.icons.BALANCE_ROUNDED,
                    bgcolor=Config.COLOR_WARNING,
                    color="white",
                    height=28,
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=2)),
                    tooltip="Crear Ajuste Automático",
                    on_click=lambda e, item_sel=it: self.abrir_modal_ajuste(item_sel)
                )
                acciones_row.append(btn_ajuste)

            filas.append(ft.DataRow(cells=[
                ft.DataCell(ft.Container(content=ft.Text(cod, size=11, weight="bold", color="white"), bgcolor=Config.COLOR_PRIMARY, padding=ft.padding.symmetric(horizontal=5, vertical=2), border_radius=5)),
                ft.DataCell(ft.Column([
                    ft.Text(nom[:32], size=11.5, weight="w500"),
                    ft.Text(c_cat, size=9.5, color="grey")
                ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)),
                ft.DataCell(ft.Text(f"{inicial:g}", size=11.5)),
                ft.DataCell(ft.Text(f"{teorico:g}", size=11.5, weight="bold")),
                ft.DataCell(ft.Text(f"{float(fisico):g}" if fisico is not None else "-", size=11.5, weight="bold", color=Config.COLOR_ACCENT if fisico is not None else "grey")),
                ft.DataCell(txt_dif),
                ft.DataCell(ft.Text(f"${val_total:,.0f}", size=11.5)),
                ft.DataCell(ft.Container(
                    content=ft.Text(est_ui, size=9.5, weight="bold", color=color_badge),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    bgcolor=ft.colors.with_opacity(0.1, color_badge),
                    border_radius=5
                )),
                ft.DataCell(ft.Row(acciones_row, spacing=2))
            ]))

        self.dt_auditoria.rows = filas
        self.txt_paginacion.value = f"Página {self.current_page} de {self.total_pages} ({len(filtrados)} insumos)"
        self.btn_pag_ant.disabled = (self.current_page <= 1)
        self.btn_pag_sig.disabled = (self.current_page >= self.total_pages)
        self.safe_update()

    # ==========================================
    # ACCIONES: REGISTRO RÁPIDO
    # ==========================================

    def on_buscar_sugerencias_rapidas(self, e):
        q = (self.txt_buscar_rapido.value or "").strip().lower()

        # Si el usuario borró o limpió el texto del buscador, deseleccionar y limpiar campos
        if not q or len(q) < 2:
            self.lv_sugerencias_rapidas.visible = False
            if self.insumo_activo:
                self.insumo_activo = None
                self.txt_cant_fisica.value = "0"
                self.txt_costo_unit.value = "0"
                self.lbl_info_seleccionado.value = "Ningún insumo seleccionado (haz clic en ✏️ en la tabla o busca arriba)"
            self.safe_update()
            return

        # Si el texto ya no coincide con el insumo que estaba activo, deseleccionarlo
        if self.insumo_activo:
            cod_act = str(self.insumo_activo.get("codigo_insumo", "")).lower()
            nom_act = str(self.insumo_activo.get("nombre", "")).lower()
            if q not in cod_act and q not in nom_act:
                self.insumo_activo = None
                self.txt_cant_fisica.value = "0"
                self.txt_costo_unit.value = "0"
                self.lbl_info_seleccionado.value = "Buscando insumo..."

        coincidencias = [
            it for it in self.insumos_lista
            if q in str(it.get("codigo_insumo", "")).lower() or q in str(it.get("nombre", "")).lower()
        ][:8]

        if not coincidencias:
            self.lv_sugerencias_rapidas.visible = False
            self.safe_update()
            return

        items_ui = []
        for it in coincidencias:
            cod = it.get("codigo_insumo", "")
            nom = it.get("nombre", "")
            teorico = float(it.get("stock_actual") or it.get("cantidad_sistema") or 0.0)
            items_ui.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.INVENTORY_2_ROUNDED, size=16, color=Config.COLOR_ACCENT),
                    title=ft.Text(f"[{cod}] {nom}", size=12, weight="bold"),
                    subtitle=ft.Text(f"Stock Sistema: {teorico:g} unds", size=11, color="grey"),
                    dense=True,
                    on_click=lambda e, item_sel=it: self.seleccionar_insumo_para_conteo(item_sel)
                )
            )

        self.lv_sugerencias_rapidas.controls = items_ui
        self.lv_sugerencias_rapidas.visible = True
        self.safe_update()

    def seleccionar_insumo_para_conteo(self, item):
        self.insumo_activo = item
        self.lv_sugerencias_rapidas.visible = False
        cod = item.get("codigo_insumo", "")
        nom = item.get("nombre", "")
        cat = item.get("categoria", "GENERAL")
        teorico = float(item.get("stock_actual") or item.get("cantidad_sistema") or 0.0)
        costo = float(item.get("costo_unitario_snapshot") or item.get("costo_unitario") or 0.0)

        fisico = item.get("cantidad_fisica")
        val_cant = str(fisico) if fisico is not None else str(teorico)

        self.txt_buscar_rapido.value = f"[{cod}] {nom}"
        self.txt_cant_fisica.value = val_cant
        self.txt_costo_unit.value = str(costo)
        self.lbl_info_seleccionado.value = f"Insumo activo: [{cod}] {nom} • Categoría: {cat} • Stock Sistema: {teorico:g}"
        self.safe_update()

    def on_guardar_conteo_rapido_click(self, e):
        if not self.insumo_activo:
            self.mostrar_alerta("Por favor selecciona un insumo primero.", "orange")
            return

        try:
            cant = float(self.txt_cant_fisica.value.replace(",", "."))
            costo = float(self.txt_costo_unit.value.replace(",", "."))
        except:
            self.mostrar_alerta("Valores numéricos inválidos.", "red")
            return

        cod = self.insumo_activo.get("codigo_insumo")
        id_auditoria = self.insumo_activo.get("id_auditoria")

        # Actualizar en base de datos
        threading.Thread(target=self._worker_guardar_conteo, args=(id_auditoria, cod, cant, costo), daemon=True).start()

    def _worker_guardar_conteo(self, id_auditoria, cod, cant, costo):
        try:
            # Usar servicio unificado que actualiza registro_auditorias_cierres, catalogo_insumos y traza de auditoría
            self.mobile_service.guardar_conteo_movil(
                codigo_insumo=cod,
                cantidad=cant,
                costo=costo,
                modo_registro="REEMPLAZAR",
                usuario="Escritorio",
                rol="ADMINISTRADOR",
                observacion="",
                mes_periodo=self.mes_seleccionado
            )

            # Actualizar memoria local inmediata (solo físico y costo)
            for it in self.insumos_lista:
                if str(it.get("codigo_insumo")) == str(cod):
                    it["cantidad_fisica"] = cant
                    it["costo_unitario_snapshot"] = costo
                    it["costo_unitario"] = costo
                    it["estado"] = "AUDITADO"
                    it["observacion"] = f"[Escritorio (ADMINISTRADOR)] Conteo directo establecido en {cant:g} unds"
                    it["usuario_conteo"] = "Escritorio"
                    break

            self.mostrar_alerta(f"✓ Conteo guardado para [{cod}]: {cant:g} unds", "green")
            self._filtrar_y_renderizar_tabla()
        except Exception as ex:
            log_error(f"_worker_guardar_conteo({cod})", ex)
            self.mostrar_alerta(f"Error al guardar conteo: {ex}", "red")

    def confirmar_eliminar_conteo(self, item):
        cod = item.get("codigo_insumo")
        nom = item.get("nombre")
        fisico = item.get("cantidad_fisica")

        def on_confirmar(e):
            self._cerrar_dialogo(dlg_del)
            self._ejecutar_eliminar_conteo(item)

        dlg_del = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.DELETE_SWEEP_ROUNDED, color="red600", size=22),
                ft.Text("Eliminar Conteo Físico", weight="bold", size=15, color=Config.COLOR_PRIMARY)
            ], spacing=6),
            content=ft.Container(
                width=420,
                content=ft.Column([
                    ft.Text("¿Estás seguro de eliminar el conteo físico de este insumo?", size=13),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"[{cod}] {nom}", weight="bold", size=12.5, color=Config.COLOR_PRIMARY),
                            ft.Text(f"Conteo actual a limpiar: {float(fisico):g} unidades" if fisico is not None else "Sin conteo", size=11.5, color="red700", weight="bold"),
                        ], spacing=2),
                        padding=8,
                        bgcolor="#FEF2F2",
                        border=ft.border.all(1, "#FECACA"),
                        border_radius=6
                    ),
                    ft.Text("El estado volverá a PENDIENTE y la acción quedará registrada en el Historial de Conteo y Auditoría.", size=11, color="grey700")
                ], tight=True, spacing=8)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_dialogo(dlg_del)),
                ft.ElevatedButton("Eliminar Conteo", bgcolor="red600", color="white", on_click=on_confirmar)
            ]
        )
        self.page.overlay.append(dlg_del)
        dlg_del.open = True
        self.safe_update()

    def _ejecutar_eliminar_conteo(self, item):
        threading.Thread(target=self._worker_eliminar_conteo, args=(item,), daemon=True).start()

    def _worker_eliminar_conteo(self, item):
        cod = item.get("codigo_insumo")
        try:
            res = self.mobile_service.eliminar_conteo(
                codigo_insumo=cod,
                mes_periodo=self.mes_seleccionado,
                usuario="Escritorio",
                rol="ADMINISTRADOR"
            )

            # Actualizar memoria local
            for it in self.insumos_lista:
                if str(it.get("codigo_insumo")) == str(cod):
                    it["cantidad_fisica"] = None
                    it["estado"] = "PENDIENTE"
                    it["observacion"] = "[Escritorio (ADMINISTRADOR)] Conteo físico eliminado/limpiado"
                    it["usuario_conteo"] = "Escritorio"
                    break

            # Si el insumo eliminado estaba activo en el panel rápido de conteo, limpiarlo
            if self.insumo_activo and str(self.insumo_activo.get("codigo_insumo")) == str(cod):
                self.insumo_activo["cantidad_fisica"] = None
                self.txt_cant_fisica.value = "0"

            self.mostrar_alerta(f"✓ Conteo físico eliminado para [{cod}]", "green")
            self._filtrar_y_renderizar_tabla()
        except Exception as ex:
            log_error(f"_worker_eliminar_conteo({cod})", ex)
            self.mostrar_alerta(f"Error al eliminar conteo: {ex}", "red")

    # ==========================================
    # MODAL DE AJUSTE AUTOMÁTICO
    # ==========================================

    def abrir_modal_ajuste(self, item):
        self.insumo_activo_ajuste = item
        cod = item.get("codigo_insumo", "")
        nom = item.get("nombre", "")
        teorico = float(item.get("stock_actual") or item.get("cantidad_sistema") or 0.0)
        fisico = float(item.get("cantidad_fisica") or 0.0)
        costo = float(item.get("costo_unitario_snapshot") or item.get("costo_unitario") or 0.0)

        dif = fisico - teorico
        tipo = "ENTRADA" if dif > 0 else "SALIDA"
        cant_sugerida = abs(dif)

        self.modal_txt_codigo.value = cod
        self.modal_txt_nombre.value = f"[{cod}] {nom}"
        self.modal_drop_tipo.value = tipo
        self.modal_txt_cant.value = f"{cant_sugerida:g}"
        self.modal_txt_costo.value = f"{costo:g}"
        self.modal_txt_obs.value = f"Ajuste por auditoría física {self.mes_seleccionado}"
        self.modal_lbl_total.value = f"${(cant_sugerida * costo):,.0f}"

        # Cargar motivos según tipo
        self._actualizar_motivos_modal(tipo)

        if self.modal_ajuste not in self.page.overlay:
            self.page.overlay.append(self.modal_ajuste)
        self.modal_ajuste.open = True
        self.safe_update()

    def _actualizar_motivos_modal(self, tipo):
        if tipo == "ENTRADA":
            motivos = [
                "Sobrante de conteo físico",
                "Inventario no registrado previamente",
                "Devolución de cliente no procesada",
                "Reclasificación / corrección"
            ]
        else:
            motivos = [
                "Faltante de conteo físico",
                "Merma / Deterioro / Rotura",
                "Vencimiento de producto",
                "Consumo interno no registrado",
                "Pérdida / Descuadre de bodega"
            ]
        self.modal_drop_motivo.options = [ft.dropdown.Option(m) for m in motivos]
        self.modal_drop_motivo.value = motivos[0]

    def _on_modal_tipo_change(self, e):
        tipo = self.modal_drop_tipo.value
        self._actualizar_motivos_modal(tipo)
        self.safe_update()

    def _calc_tot_modal_ajuste(self, e):
        try:
            cant = float(self.modal_txt_cant.value.replace(",", "."))
            costo = float(self.modal_txt_costo.value.replace(",", "."))
            self.modal_lbl_total.value = f"${(cant * costo):,.0f}"
        except:
            self.modal_lbl_total.value = "$0"
        self.safe_update()

    def _cerrar_modal_ajuste(self):
        self._cerrar_dialogo(self.modal_ajuste)

    def _on_guardar_ajuste_modal(self, e):
        try:
            cant = float(self.modal_txt_cant.value.replace(",", "."))
            costo = float(self.modal_txt_costo.value.replace(",", "."))
            tot = cant * costo
        except:
            self.mostrar_alerta("Cantidades o costos inválidos.", "red")
            return

        cod = self.modal_txt_codigo.value
        tipo = self.modal_drop_tipo.value
        motivo = self.modal_drop_motivo.value
        obs = self.modal_txt_obs.value

        # Registrar ajuste en registro_ajustes_inventario
        tipo_ajuste_db = "AJUSTE_ENTRADA" if tipo == "ENTRADA" else "AJUSTE_SALIDA"
        motivo_final = f"[{motivo}] {obs}".strip() if obs else str(motivo)
        datos_ajuste = {
            "codigo_insumo": cod,
            "tipo_ajuste": tipo_ajuste_db,
            "cantidad": cant,
            "costo_unitario_congelado": costo,
            "costo_total_ajuste": tot,
            "motivo_observacion": motivo_final,
            "estado_registro": "VÁLIDO"
        }
        id_periodo = self.datos_cierre.get("periodo", {}).get("id_periodo")
        if id_periodo:
            datos_ajuste["id_periodo"] = id_periodo

        ok = self.insumos_repo.insert_ajuste_individual(datos_ajuste)

        if ok:
            # 1. Actualizar estado y costo en auditorías mediante repositorio
            update_aud = {
                "estado": "AJUSTADO",
                "costo_unitario_snapshot": costo,
                "observacion": f"Ajuste {tipo} por {cant:g} unds ({motivo_final})"
            }
            self.cierres_repo.actualizar_auditoria_ajustada(cod, update_aud, id_periodo=id_periodo)

            # 2. Actualizar costo_unitario en catálogo maestro si costo > 0
            if costo > 0:
                self.insumos_repo.actualizar_costo_unitario(cod, costo)

            self._cerrar_modal_ajuste()
            self.mostrar_alerta(f"✓ Ajuste de {tipo} aplicado con éxito para [{cod}].", "green")
            
            # 3. Marcar en memoria local como ajustado y refrescar valores
            for it in self.insumos_lista:
                if str(it.get("codigo_insumo")) == str(cod):
                    it["estado"] = "AJUSTADO"
                    it["costo_unitario_snapshot"] = costo
                    it["costo_unitario"] = costo
                    break
            self._filtrar_y_renderizar_tabla()
        else:
            self.mostrar_alerta("Error al registrar ajuste en Supabase.", "red")

    def on_aprobar_cierre_click(self, e):
        # 1. Analizar descuadres pendientes en self.insumos_lista
        descuadres_pos = []
        descuadres_neg = []
        pendientes_count = 0
        conciliados_count = 0

        val_sobrantes_tot = 0.0
        val_faltantes_tot = 0.0
        cant_sobrantes_tot = 0.0
        cant_faltantes_tot = 0.0

        for it in self.insumos_lista:
            fisico = it.get("cantidad_fisica")
            teorico = float(it.get("cantidad_sistema") if it.get("cantidad_sistema") is not None else (it.get("stock_actual") or 0.0))
            costo = float(it.get("costo_unitario_snapshot") or it.get("costo_unitario") or 0.0)
            est = it.get("_estado_ui") or it.get("estado")

            if fisico is None:
                pendientes_count += 1
            else:
                dif = float(fisico) - teorico
                if est == "AJUSTADO" or abs(dif) < 0.001:
                    conciliados_count += 1
                elif dif > 0:
                    descuadres_pos.append(it)
                    val_sobrantes_tot += (dif * costo)
                    cant_sobrantes_tot += dif
                else:
                    descuadres_neg.append(it)
                    val_faltantes_tot += (abs(dif) * costo)
                    cant_faltantes_tot += abs(dif)

        # CASO 1: Si NO hay descuadres sin justificar
        if not descuadres_pos and not descuadres_neg:
            def confirmar_cierre_limpio(ev):
                self._cerrar_dialogo(dlg_conf)
                threading.Thread(target=self._worker_aprobar_cierre_final, args=([], [], "", ""), daemon=True).start()

            dlg_conf = ft.AlertDialog(
                title=ft.Text("Aprobar y Cerrar Periodo", weight="bold"),
                content=ft.Container(
                    width=440,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED, color="green", size=28),
                            ft.Text("¡Inventario 100% Conciliado!", weight="bold", size=15, color=Config.COLOR_PRIMARY)
                        ], spacing=8),
                        ft.Text(f"Todos los insumos auditados están cuadrados o con su ajuste respectivo."),
                        ft.Divider(height=10),
                        ft.Row([ft.Text("Insumos Auditados / Conciliados:", size=12), ft.Text(f"{conciliados_count} ítems", size=12, weight="bold")]),
                        ft.Row([ft.Text("Insumos sin conteo (Stock Sistema):", size=12), ft.Text(f"{pendientes_count} ítems", size=12, weight="bold", color="grey")]),
                        ft.Divider(height=10),
                        ft.Text("¿Deseas cerrar definitivamente el mes? El stock auditado será el inventario inicial del próximo periodo.", size=11, color="grey")
                    ], tight=True, spacing=6)
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda ev: self._cerrar_dialogo(dlg_conf)),
                    ft.ElevatedButton("🔒 Sí, Cerrar Periodo", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=confirmar_cierre_limpio)
                ]
            )
            self.page.overlay.append(dlg_conf)
            dlg_conf.open = True
            self.safe_update()
            return

        # CASO 2: Si HAY descuadres pendientes: Modal Inteligente de Ajustes Masivos
        drop_motivo_sobrantes = ft.Dropdown(
            label="Motivo para Sobrantes (+)",
            options=[
                ft.dropdown.Option("Sobrante de Inventario"),
                ft.dropdown.Option("Donación Entrante"),
                ft.dropdown.Option("Devolución Cliente"),
                ft.dropdown.Option("Ajuste Global de Entrada")
            ],
            value="Sobrante de Inventario",
            dense=True,
            text_size=12,
            height=38,
            width=500,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=4)
        )

        drop_motivo_faltantes = ft.Dropdown(
            label="Motivo para Faltantes (-)",
            options=[
                ft.dropdown.Option("Merma / Daño"),
                ft.dropdown.Option("Vencimiento"),
                ft.dropdown.Option("Pérdida"),
                ft.dropdown.Option("Consumo Familiar"),
                ft.dropdown.Option("Ajuste Global de Salida")
            ],
            value="Merma / Daño",
            dense=True,
            text_size=12,
            height=38,
            width=500,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=4)
        )

        def ejecutar_cierre_con_ajustes(ev):
            motivo_pos = drop_motivo_sobrantes.value
            motivo_neg = drop_motivo_faltantes.value
            self._cerrar_dialogo(dlg_smart)
            self.mostrar_alerta("Procesando ajustes masivos y cerrando periodo...", "blue")
            threading.Thread(
                target=self._worker_aprobar_cierre_final,
                args=(descuadres_pos, descuadres_neg, motivo_pos, motivo_neg),
                daemon=True
            ).start()

        # Lista previa de insumos descuadrados
        items_preview = []
        for it in (descuadres_pos + descuadres_neg)[:10]:
            c_cod = it.get("codigo_insumo")
            c_nom = (it.get("nombre") or "")[:22]
            c_sis = float(it.get("cantidad_sistema") if it.get("cantidad_sistema") is not None else (it.get("stock_actual") or 0.0))
            c_fis = float(it.get("cantidad_fisica") or 0.0)
            c_dif = c_fis - c_sis
            c_color = "green" if c_dif > 0 else "red"
            items_preview.append(
                ft.Row([
                    ft.Text(f"[{c_cod}] {c_nom}", size=11, weight="bold", width=210, no_wrap=True),
                    ft.Text(f"Sis: {c_sis:g} | Fís: {c_fis:g}", size=10.5, color="grey", width=110),
                    ft.Text(f"{c_dif:+g}", size=11, weight="bold", color=c_color)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

        contenido_smart = ft.Container(
            width=540,
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=Config.COLOR_WARNING, size=24),
                        ft.Column([
                            ft.Text("Descuadres Pendientes de Justificación", weight="bold", size=13.5, color=Config.COLOR_PRIMARY),
                            ft.Text(f"Existen {len(descuadres_pos) + len(descuadres_neg)} insumos con diferencias. Selecciona los motivos para los ajustes automáticos:", size=11, color=Config.COLOR_TEXT_MUTED)
                        ], spacing=1, expand=True)
                    ], spacing=10),
                    padding=10,
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_WARNING),
                    border_radius=8
                ),
                
                # Bloque Sobrantes (+)
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.ARROW_UPWARD_ROUNDED, color="green", size=16),
                            ft.Text(f"Ajustes Positivos: {len(descuadres_pos)} insumos (+{cant_sobrantes_tot:g} unds)", weight="bold", size=11.5, color="green"),
                            ft.Container(expand=True),
                            ft.Text(f"+${val_sobrantes_tot:,.0f}", weight="bold", size=12.5, color="green")
                        ]),
                        drop_motivo_sobrantes
                    ], spacing=6),
                    padding=10,
                    bgcolor="#F0FDF4",
                    border=ft.border.all(1, ft.colors.with_opacity(0.2, "green")),
                    border_radius=8,
                    visible=bool(descuadres_pos)
                ),

                # Bloque Faltantes (-)
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.ARROW_DOWNWARD_ROUNDED, color="red", size=16),
                            ft.Text(f"Ajustes Negativos: {len(descuadres_neg)} insumos (-{cant_faltantes_tot:g} unds)", weight="bold", size=11.5, color="red"),
                            ft.Container(expand=True),
                            ft.Text(f"-${val_faltantes_tot:,.0f}", weight="bold", size=12.5, color="red")
                        ]),
                        drop_motivo_faltantes
                    ], spacing=6),
                    padding=10,
                    bgcolor="#FEF2F2",
                    border=ft.border.all(1, ft.colors.with_opacity(0.2, "red")),
                    border_radius=8,
                    visible=bool(descuadres_neg)
                ),

                # Resumen de insumos descuadrados
                ft.Container(
                    content=ft.Column([
                        ft.Text("Muestra de Insumos a Ajustar Automáticamente:", size=11, weight="bold", color="grey"),
                        *items_preview
                    ], spacing=3),
                    padding=8,
                    bgcolor="#F8FAFC",
                    border_radius=6,
                    border=ft.border.all(1, "#E2E8F0")
                ) if items_preview else ft.Container(),

                # Insumos no contados
                ft.Row([
                    ft.Icon(ft.icons.INFO_OUTLINE_ROUNDED, size=15, color="grey"),
                    ft.Text(f"{pendientes_count} insumos sin conteo se cerrarán con el saldo teórico ($0 de ajuste).", size=11, color="grey")
                ], spacing=6)
            ], spacing=8, scroll=ft.ScrollMode.AUTO)
        )

        dlg_smart = ft.AlertDialog(
            title=ft.Text("Conciliación Inteligente de Cierre", weight="bold"),
            content=contenido_smart,
            actions=[
                ft.TextButton("Revisar Manualmente", on_click=lambda ev: self._cerrar_dialogo(dlg_smart)),
                ft.ElevatedButton(
                    "Aplicar Ajustes y Cerrar Mes",
                    bgcolor=Config.COLOR_PRIMARY,
                    color="white",
                    icon=ft.icons.LOCK_ROUNDED,
                    on_click=ejecutar_cierre_con_ajustes
                )
            ]
        )
        self.page.overlay.append(dlg_smart)
        dlg_smart.open = True
        self.safe_update()

    def _worker_aprobar_cierre_final(self, descuadres_pos, descuadres_neg, motivo_pos, motivo_neg):
        try:
            id_periodo = self.datos_cierre.get("periodo", {}).get("id_periodo")
            ajustes_batch = []

            # 1. Acumular ajustes masivos de entrada
            for it in descuadres_pos:
                cod = it.get("codigo_insumo")
                fisico = float(it.get("cantidad_fisica") or 0.0)
                teorico = float(it.get("stock_actual") or it.get("cantidad_sistema") or 0.0)
                dif = fisico - teorico
                costo = float(it.get("costo_unitario_snapshot") or it.get("costo_unitario") or 0.0)
                if dif > 0:
                    d_pos = {
                        "codigo_insumo": cod,
                        "tipo_ajuste": "AJUSTE_ENTRADA",
                        "cantidad": dif,
                        "costo_unitario_congelado": costo,
                        "costo_total_ajuste": dif * costo,
                        "motivo_observacion": f"[{motivo_pos}] Cierre mensual automático {self.mes_seleccionado}",
                        "estado_registro": "VÁLIDO"
                    }
                    if id_periodo:
                        d_pos["id_periodo"] = id_periodo
                    ajustes_batch.append(d_pos)

            # 2. Acumular ajustes masivos de salida
            for it in descuadres_neg:
                cod = it.get("codigo_insumo")
                fisico = float(it.get("cantidad_fisica") or 0.0)
                teorico = float(it.get("stock_actual") or it.get("cantidad_sistema") or 0.0)
                dif = abs(fisico - teorico)
                costo = float(it.get("costo_unitario_snapshot") or it.get("costo_unitario") or 0.0)
                if dif > 0:
                    d_neg = {
                        "codigo_insumo": cod,
                        "tipo_ajuste": "AJUSTE_SALIDA",
                        "cantidad": dif,
                        "costo_unitario_congelado": costo,
                        "costo_total_ajuste": dif * costo,
                        "motivo_observacion": f"[{motivo_neg}] Cierre mensual automático {self.mes_seleccionado}",
                        "estado_registro": "VÁLIDO"
                    }
                    if id_periodo:
                        d_neg["id_periodo"] = id_periodo
                    ajustes_batch.append(d_neg)

            # 3. Insertar TODOS los ajustes en UNA sola llamada masiva (batch)
            if ajustes_batch:
                ok_ajustes = self.insumos_repo.insert_ajustes_masivo(ajustes_batch)
                if not ok_ajustes:
                    self.mostrar_alerta("Advertencia: Algunos ajustes no pudieron registrarse en lote.", "orange")

            # 4. Sellar y aprobar periodo mediante el repositorio
            self.cierres_repo.sellar_periodo_cierre(self.mes_seleccionado, id_periodo=id_periodo)

            # 5. Actualizar UI y feedback
            self.badge_estado_auditoria.content.controls[1].value = "CERRADO"
            self.badge_estado_auditoria.bgcolor = ft.colors.with_opacity(0.1, "red")
            self.badge_estado_auditoria.content.controls[0].bgcolor = "red"
            self.badge_estado_auditoria.content.controls[1].color = "red"

            self.mostrar_alerta(f"✓ Periodo {self.mes_seleccionado} cerrado, ajustado y aprobado con éxito.", "green")
            self.safe_update()
            self._worker_cargar_datos_auditoria()

        except Exception as ex:
            log_error("Error al aprobar cierre final", ex)
            self.mostrar_alerta(f"Error al cerrar periodo: {ex}", "red")

    # ==========================================
    # EVENTOS DE FILTROS Y PAGINACIÓN
    # ==========================================

    def on_filtro_detalle_change(self, e):
        self.current_page = 1
        self._filtrar_y_renderizar_tabla()

    def on_pag_anterior(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self._filtrar_y_renderizar_tabla()

    def on_pag_siguiente(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._filtrar_y_renderizar_tabla()

    # ==========================================
    # MODALES: QR MÓVIL & HISTORIAL DE INSUMO
    # ==========================================

    def abrir_modal_qr(self, e):
        self.mobile_service.set_mes_activo(self.mes_seleccionado)
        iniciar_servidor_en_hilo(port=8550)
        url_local = self.mobile_service.get_server_url(port=8550)
        qr_local_b64 = self.mobile_service.get_qr_base64(port=8550)

        modo_actual = "LOCAL"

        img_qr = ft.Image(src_base64=qr_local_b64, width=190, height=190, fit=ft.ImageFit.CONTAIN)
        txt_url = ft.Text(url_local, size=12, weight="bold", color=Config.COLOR_ACCENT, selectable=True, expand=True)
        badge_status_text = ft.Text("Servidor Web Activo en Red Local", size=11, weight="bold", color=Config.COLOR_SUCCESS)
        badge_status_dot = ft.Container(width=8, height=8, bgcolor=Config.COLOR_SUCCESS, border_radius=4)
        txt_explicacion = ft.Text(
            f"Apunta con la cámara de cualquier teléfono conectado al Wi-Fi para acceder a la web de conteo de {self.mes_seleccionado}.",
            size=11, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER
        )
        
        loading_tunnel = ft.Container(
            content=ft.Row([
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=Config.COLOR_ACCENT),
                ft.Text("Iniciando túnel seguro Cloudflare...", size=11, color=Config.COLOR_PRIMARY, weight="w500")
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            visible=False
        )

        btn_activar_tunnel = ft.ElevatedButton(
            "Activar Acceso por Internet (Cloudflare)",
            icon=ft.icons.CLOUD_SYNC_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=34,
            visible=False,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        def actualizar_vista_modo():
            nonlocal modo_actual
            if modo_actual == "LOCAL":
                btn_tab_local.bgcolor = Config.COLOR_PRIMARY
                btn_tab_local.color = "white"
                btn_tab_internet.bgcolor = "#F1F5F9"
                btn_tab_internet.color = "grey800"
                
                img_qr.src_base64 = qr_local_b64
                img_qr.visible = True
                txt_url.value = url_local
                badge_status_text.value = "Servidor Web Activo en Red Local"
                badge_status_text.color = Config.COLOR_SUCCESS
                badge_status_dot.bgcolor = Config.COLOR_SUCCESS
                txt_explicacion.value = f"Apunta con la cámara de cualquier teléfono conectado al Wi-Fi de bodega ({self.mes_seleccionado})."
                loading_tunnel.visible = False
                btn_activar_tunnel.visible = False
            else:
                btn_tab_local.bgcolor = "#F1F5F9"
                btn_tab_local.color = "grey800"
                btn_tab_internet.bgcolor = Config.COLOR_PRIMARY
                btn_tab_internet.color = "white"
                
                pub_url = self.mobile_service.get_public_url()
                if pub_url:
                    qr_pub_b64 = self.mobile_service.get_qr_base64(custom_url=pub_url)
                    img_qr.src_base64 = qr_pub_b64
                    img_qr.visible = True
                    txt_url.value = pub_url
                    badge_status_text.value = "Enlace Cloudflare HTTPS Activo (Datos Móviles / 4G)"
                    badge_status_text.color = "#2563EB"
                    badge_status_dot.bgcolor = "#2563EB"
                    txt_explicacion.value = "Escanea desde cualquier celular con datos móviles (4G/5G) o fuera del local."
                    loading_tunnel.visible = False
                    btn_activar_tunnel.visible = False
                else:
                    img_qr.visible = False
                    txt_url.value = "Túnel no iniciado"
                    badge_status_text.value = "Listo para conectar túnel seguro"
                    badge_status_text.color = "orange800"
                    badge_status_dot.bgcolor = "orange800"
                    txt_explicacion.value = "Presiona el botón para generar un enlace público temporal con HTTPS."
                    loading_tunnel.visible = False
                    btn_activar_tunnel.visible = True
            
            self.safe_update()

        def on_activar_tunnel_click(ev):
            btn_activar_tunnel.visible = False
            loading_tunnel.visible = True
            loading_tunnel.content.controls[1].value = "Iniciando túnel seguro Cloudflare..."
            self.safe_update()

            def _on_ready(pub_url):
                actualizar_vista_modo()

            def _on_status(st, msg):
                loading_tunnel.content.controls[1].value = msg
                self.safe_update()

            def _on_error(err_msg):
                loading_tunnel.visible = False
                btn_activar_tunnel.visible = True
                self.mostrar_alerta(f"Error en túnel: {err_msg}", "red")
                self.safe_update()

            self.mobile_service.start_public_tunnel(
                port=8550,
                on_ready=_on_ready,
                on_status=_on_status,
                on_error=_on_error
            )

        btn_activar_tunnel.on_click = on_activar_tunnel_click

        def set_modo_local(ev):
            nonlocal modo_actual
            modo_actual = "LOCAL"
            actualizar_vista_modo()

        def set_modo_internet(ev):
            nonlocal modo_actual
            modo_actual = "INTERNET"
            pub_url = self.mobile_service.get_public_url()
            if not pub_url:
                on_activar_tunnel_click(None)
            else:
                actualizar_vista_modo()

        btn_tab_local = ft.ElevatedButton(
            "🏠 Wi-Fi Local",
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=32,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=12)),
            on_click=set_modo_local
        )

        btn_tab_internet = ft.ElevatedButton(
            "🌐 Datos Móviles (4G/5G)",
            bgcolor="#F1F5F9",
            color="grey800",
            height=32,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=12)),
            on_click=set_modo_internet
        )

        def copiar_url(ev):
            current_url = txt_url.value
            if self.page and current_url and current_url.startswith("http"):
                self.page.set_clipboard(current_url)
                self.mostrar_alerta(f"Enlace copiado al portapapeles: {current_url}", "green")

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.PHONE_ANDROID_ROUNDED, color=Config.COLOR_ACCENT),
                ft.Text("Conteo Móvil Multi-Dispositivo", size=16, weight="bold", color=Config.COLOR_PRIMARY)
            ]),
            content=ft.Column([
                ft.Row([btn_tab_local, btn_tab_internet], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            badge_status_dot,
                            badge_status_text
                        ], spacing=6),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=Config.COLOR_SUCCESS_BG,
                        border_radius=12,
                        border=ft.border.all(1, ft.colors.with_opacity(0.3, Config.COLOR_SUCCESS))
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                loading_tunnel,
                btn_activar_tunnel,
                ft.Container(
                    content=img_qr,
                    alignment=ft.alignment.center,
                    padding=10,
                    bgcolor="white",
                    border=ft.border.all(1, Config.COLOR_BORDER),
                    border_radius=12
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.LINK_ROUNDED, size=16, color=Config.COLOR_ACCENT),
                        txt_url,
                        ft.IconButton(icon=ft.icons.COPY_ALL_ROUNDED, icon_size=18, tooltip="Copiar enlace", on_click=copiar_url)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    bgcolor=Config.COLOR_BACKGROUND,
                    border=ft.border.all(1, Config.COLOR_BORDER),
                    border_radius=8
                ),
                txt_explicacion
            ], tight=True, spacing=10, width=400, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Copiar Enlace", on_click=copiar_url),
                ft.ElevatedButton("Cerrar", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=lambda ev: self._cerrar_dialogo(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=14)
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()

    def mostrar_modal_historial_insumo(self, item):
        cod = item.get("codigo_insumo")
        nom = item.get("nombre")
        cat = item.get("categoria", "GENERAL")
        fisico = item.get("cantidad_fisica")

        historial = self.mobile_service.obtener_historial_insumo(cod)
        total_ediciones = len(historial)

        items_timeline = []
        if not historial:
            items_timeline.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.HISTORY_ROUNDED, size=32, color="grey"),
                        ft.Text("Sin registros de conteo previos para este insumo.", size=12, color="grey")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    padding=20, alignment=ft.alignment.center
                )
            )
        else:
            for h in historial:
                es_eliminacion = (h.get("modo") == "ELIMINAR_CONTEO")
                if es_eliminacion:
                    disp_icon = ft.icons.DELETE_SWEEP_ROUNDED
                    disp_color = "red600"
                    badge_cant = ft.Container(
                        content=ft.Text("ELIMINADO", size=10, weight="bold", color="red700"),
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        bgcolor="#fef2f2",
                        border=ft.border.all(1, "#fecaca"),
                        border_radius=6
                    )
                else:
                    disp_icon = ft.icons.PHONE_ANDROID_ROUNDED if h.get("dispositivo") == "WEB_MOVIL" else ft.icons.DESKTOP_WINDOWS_ROUNDED
                    disp_color = Config.COLOR_ACCENT if h.get("dispositivo") == "WEB_MOVIL" else Config.COLOR_PRIMARY
                    badge_cant = ft.Container(
                        content=ft.Text(f"{h.get('cantidad_ingresada')} unds", size=11, weight="bold", color="green700"),
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        bgcolor=ft.colors.with_opacity(0.1, "green"),
                        border_radius=6
                    )
                
                items_timeline.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Row([
                                    ft.Icon(disp_icon, size=15, color=disp_color),
                                    ft.Text(f"{h.get('usuario')} ({h.get('rol')})", size=12, weight="bold", color=Config.COLOR_PRIMARY if not es_eliminacion else "red800"),
                                ], spacing=6),
                                ft.Container(expand=True),
                                badge_cant
                            ]),
                            ft.Row([
                                ft.Text(f"🕒 {h.get('fecha')} {h.get('hora')} • {h.get('dispositivo')}", size=10, color=Config.COLOR_TEXT_MUTED),
                                ft.Container(expand=True),
                                ft.Text(f"Modo: {h.get('modo')}", size=10, weight="w500", color="red700" if es_eliminacion else "grey700")
                            ]),
                            ft.Text(h.get("observacion") or "", size=11, color="black87", italic=True) if h.get("observacion") else ft.Container()
                        ], spacing=3),
                        padding=10,
                        bgcolor="#fff5f5" if es_eliminacion else "#F8FAFC",
                        border=ft.border.all(1, "#fecaca" if es_eliminacion else "#E2E8F0"),
                        border_radius=8
                    )
                )

        dlg_hist = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.HISTORY_EDU_ROUNDED, color=Config.COLOR_PRIMARY),
                ft.Column([
                    ft.Text("Historial de Conteo y Auditoría", size=15, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Text(f"[{cod}] {nom} • {cat}", size=11, color=Config.COLOR_TEXT_MUTED)
                ], spacing=1)
            ], spacing=8),
            content=ft.Container(
                width=480,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Row([
                                ft.Text("Conteo Total Actual:", size=11, color=Config.COLOR_TEXT_MUTED),
                                ft.Text(f"{float(fisico):g} unds" if fisico is not None else "Sin contar", size=12, weight="bold", color=Config.COLOR_ACCENT)
                            ], spacing=4),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            bgcolor="#EEF2FF",
                            border_radius=8
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Text("Ediciones/Conteos:", size=11, color=Config.COLOR_TEXT_MUTED),
                                ft.Text(f"{total_ediciones} veces", size=12, weight="bold", color=Config.COLOR_PRIMARY)
                            ], spacing=4),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            bgcolor="#F1F5F9",
                            border_radius=8
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=8),
                    ft.Container(
                        content=ft.Column(items_timeline, spacing=6, scroll=ft.ScrollMode.AUTO),
                        height=280,
                        width=480
                    )
                ], tight=True, spacing=8)
            ),
            actions=[
                ft.ElevatedButton("Cerrar", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=lambda ev: self._cerrar_dialogo(dlg_hist))
            ],
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        self.page.overlay.append(dlg_hist)
        dlg_hist.open = True
        self.safe_update()
