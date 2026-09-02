import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import math
from datetime import datetime
from ui.components.autocomplete import CustomAutoComplete
from ui.components.periodo_selector import PeriodoSelectorWidget
from core.fecha_utils import get_ahora_local, get_hoy_local_str, parsear_a_fecha_local, formatear_fecha_hora_local

class InventarioView(ft.Container):
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
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        self.current_data = []
        
        # Variables de Ordenamiento por Servidor
        self.sort_col_name = "Insumo"
        self.sort_is_asc = True
        
        # Control de Desglose de Métricas (Inicial, Compras, Ventas, Ajustes) - Oculto por defecto
        self.mostrar_detalle_kpis = False
        self.btn_toggle_detalle = ft.IconButton(
            icon=ft.icons.VIEW_AGENDA_OUTLINED,
            tooltip="Mostrar desglose de métricas (Inicial, Compras, Ventas, Ajustes)",
            on_click=self.toggle_detalle_kpis
        )
        
        # Controles de Búsqueda
        def on_select_busqueda_inv(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            if not texto or not texto.strip():
                self.search_input_text.value = ""
            elif "[" in texto and "]" in texto:
                self.search_input_text.value = texto.split("]")[0].replace("[", "").strip()
            else:
                self.search_input_text.value = texto.strip()
            self.current_page = 1
            self.on_search(None)

        self.search_input_text = ft.TextField(visible=False)

        self.search_autocomplete = CustomAutoComplete(
            hint_text="Buscar por código o nombre...",
            on_select=on_select_busqueda_inv,
            text_size=12,
            expand=True
        )

        # Panel de Filtros Unificado (Colapsable)
        self.panel_filtros_abierto = False
        self.btn_toggle_filtros = ft.IconButton(
            icon=ft.icons.TUNE_ROUNDED,
            tooltip="Filtros de Inventario",
            on_click=self.toggle_panel_filtros
        )
        
        self.category_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            label="Categoría",
            width=200,
            dense=True,
            border_radius=8,
            bgcolor="white",
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_color=ft.colors.with_opacity(0.15, "black"),
            focused_border_color=Config.COLOR_PRIMARY,
            on_change=self.on_search
        )

        self.drop_estado = ft.Dropdown(
            options=[
                ft.dropdown.Option("Habilitados"),
                ft.dropdown.Option("Inhabilitados"),
                ft.dropdown.Option("Todos")
            ],
            value="Habilitados",
            label="Estado",
            width=145,
            dense=True,
            border_radius=8,
            bgcolor="white",
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_color=ft.colors.with_opacity(0.15, "black"),
            focused_border_color=Config.COLOR_PRIMARY,
            on_change=self.on_search
        )
        
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )

        self.btn_fecha_filtro = ft.OutlinedButton(
            text="Filtrar por Fecha",
            icon=ft.icons.CALENDAR_MONTH_ROUNDED,
            height=38,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=12, vertical=4)
            ),
            on_click=self.open_date_picker
        )
        
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
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
                self.category_dropdown,
                self.drop_estado,
                self.btn_fecha_filtro,
                self.btn_clear_date,
                ft.Container(expand=True),
                self.btn_limpiar_todos_filtros
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, wrap=False)
        )

        self.dlg_filtro_fecha_info = ft.AlertDialog(
            title=ft.Text("Filtrar información por fecha", weight="bold", color=Config.COLOR_PRIMARY, size=16),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(
                        "Selecciona una fecha de corte para calcular la fotografía exacta del inventario en ese día.\n\n"
                        "El sistema reconstruirá el Stock Inicial, Compras, Ventas y Ajustes acumulados hasta la fecha seleccionada.",
                        size=12, color="grey"
                    )
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cerrar_modal_info_fecha()),
                ft.ElevatedButton("Seleccionar Fecha", icon=ft.icons.DATE_RANGE, bgcolor=Config.COLOR_PRIMARY, color="white", on_click=self.lanzar_date_picker)
            ]
        )
        
        self.card_list_view = ft.ListView(expand=True, spacing=10, visible=True)
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        
        self.current_edit_context = None
        
        # Dashboard Resumen Financiero Compacto de Inventario
        self.lbl_valor_inventario = ft.Text("$0", size=16, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_sub_inv_det = ft.Text("Stock positivo real", size=10, color="grey500")

        self.lbl_ventas_total = ft.Text("$0", size=16, weight="bold", color="green700")
        self.lbl_cumplimiento_mes = ft.Container(
            content=ft.Text("🎯 0.0% meta", size=9, weight="bold", color="teal800"),
            bgcolor="#e6f4ea", padding=ft.padding.symmetric(horizontal=5, vertical=1), border_radius=4
        )

        self.lbl_proyeccion_ventas = ft.Text("$0", size=16, weight="bold", color="purple700")
        self.lbl_sub_proy = ft.Text("Proyección stock disponible", size=10, color="grey500")

        self.lbl_meta_diaria = ft.Text("$0 / día", size=15, weight="bold", color="teal800")
        self.lbl_cumplimiento_hoy = ft.Text("Hoy: $0 • 0.0%", size=10, color="grey600")

        self.summary_container = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=10,
            border=ft.border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.colors.with_opacity(0.04, "black")),
            content=ft.Row([
                # Bloque 1: VALORIZACIÓN DEL INVENTARIO
                ft.Container(
                    expand=1,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.INVENTORY_2_OUTLINED, size=15, color=Config.COLOR_PRIMARY),
                            ft.Text("VALORIZACIÓN INVENTARIO", size=10, weight="bold", color="grey700")
                        ], spacing=4),
                        self.lbl_valor_inventario,
                        self.lbl_sub_inv_det
                    ], spacing=2)
                ),
                ft.VerticalDivider(width=1, color="#e2e8f0"),
                # Bloque 2: VENTAS DEL MES & CUMPLIMIENTO
                ft.Container(
                    expand=1,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.TRENDING_UP, size=15, color="green700"),
                            ft.Text("VENTAS DEL MES", size=10, weight="bold", color="grey700")
                        ], spacing=4),
                        self.lbl_ventas_total,
                        ft.Row([self.lbl_cumplimiento_mes], spacing=2)
                    ], spacing=2)
                ),
                ft.VerticalDivider(width=1, color="#e2e8f0"),
                # Bloque 3: OBJETIVO DE VENTA (STOCK MES)
                ft.Container(
                    expand=1,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.MONETIZATION_ON_OUTLINED, size=15, color="purple700"),
                            ft.Text("OBJETIVO DE VENTA (STOCK)", size=10, weight="bold", color="grey700")
                        ], spacing=4),
                        self.lbl_proyeccion_ventas,
                        self.lbl_sub_proy
                    ], spacing=2)
                ),
                ft.VerticalDivider(width=1, color="#e2e8f0"),
                # Bloque 4: META DIARIA & CUMPLIMIENTO HOY
                ft.Container(
                    expand=1,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.FLAG, size=15, color="teal800"),
                            ft.Text("OBJETIVO DIARIO (META)", size=10, weight="bold", color="grey700")
                        ], spacing=4),
                        self.lbl_meta_diaria,
                        self.lbl_cumplimiento_hoy
                    ], spacing=2)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )
        
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)

        self.periodo_selector = PeriodoSelectorWidget(on_change_callback=self.on_periodo_change, page=self.page)
        self.lbl_titulo = ft.Text("Catálogo de Insumos", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        main_column = ft.Column([
            self.progress_bar,
            ft.Row([self.lbl_titulo, ft.Container(expand=True), self.periodo_selector, self.btn_fullscreen], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.summary_container,
            
            # Toolbar de Búsqueda y Filtros
            ft.Container(
                content=ft.Row([
                    self.search_autocomplete,
                    self.btn_toggle_filtros,
                    self.btn_toggle_detalle,
                    self.btn_fullscreen
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="white",
                padding=10,
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            self.panel_filtros,
            self.card_list_view,
            
            # Footer Paginación
            ft.Container(
                content=ft.Row([
                    self.lbl_total,
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(top=10)
            )
        ], expand=True, spacing=10)

        self.content = main_column
        
        # No llamamos a los métodos aquí porque el control no está en la página todavía
        
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
        """Se ejecuta cuando la vista se agrega a la pantalla."""
        if self.page:
            if self.date_picker not in self.page.overlay:
                self.page.overlay.append(self.date_picker)
            if hasattr(self, "dlg_filtro_fecha_info") and self.dlg_filtro_fecha_info not in self.page.overlay:
                self.page.overlay.append(self.dlg_filtro_fecha_info)
                
        # Lanzar inicializaciones secundarias en hilos daemon para no bloquear la UI
        threading.Thread(target=self.load_categories, daemon=True).start()
        threading.Thread(target=self.cargar_sugerencias_buscador, daemon=True).start()
        self.load_data()
        
    def cargar_sugerencias_buscador(self):
        try:
            res = self.db._db.get("catalogo_insumos?select=codigo_insumo,nombre&limit=3000", timeout=10)
            if res and res.status_code == 200:
                insumos = res.json()
                self.search_autocomplete.suggestions = [
                    {"key": str(i.get("codigo_insumo") or ""), "value": f"[{i.get('codigo_insumo')}] {i.get('nombre', '')}"}
                    for i in insumos
                    if i.get("codigo_insumo")
                ]
                self.safe_update()
        except Exception:
            pass

    def safe_update(self):
        """Actualiza la UI local solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.update()
        except Exception:
            pass

    def safe_page_update(self):
        """Actualiza la página principal para reflejar overlays, modales y snackbars."""
        try:
            if self.page:
                self.page.update()
        except Exception:
            pass

    def mostrar_alerta(self, mensaje: str, color: str = "red"):
        """Muestra un mensaje SnackBar flotante asegurando actualización de pantalla."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(mensaje, weight="bold", color="white"),
                bgcolor=color,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.safe_page_update()

    def load_summary(self):
        # La carga completa y cálculo detallado se delega a _fetch_data_worker
        pass
            
    def will_unmount(self):
        """Se ejecuta cuando se destruye la vista."""
        pass
        
    def load_categories(self):
        try:
            cats = self.db.get_categorias()
            options = [ft.dropdown.Option("Todas")]
            for c in cats:
                if c: options.append(ft.dropdown.Option(c))
            self.category_dropdown.options = options
            self.safe_update()
        except Exception:
            pass

    def toggle_detalle_kpis(self, e=None):
        self.mostrar_detalle_kpis = not self.mostrar_detalle_kpis
        self.btn_toggle_detalle.icon = ft.icons.VIEW_AGENDA if self.mostrar_detalle_kpis else ft.icons.VIEW_AGENDA_OUTLINED
        self.btn_toggle_detalle.tooltip = "Ocultar desglose de métricas" if self.mostrar_detalle_kpis else "Mostrar desglose de métricas (Inicial, Compras, Ventas, Ajustes)"
        self._render_cards_local()

    def toggle_panel_filtros(self, e=None):
        self.panel_filtros_abierto = not self.panel_filtros_abierto
        self.panel_filtros.visible = self.panel_filtros_abierto
        self.btn_toggle_filtros.icon = ft.icons.FILTER_ALT_OFF_ROUNDED if self.panel_filtros_abierto else ft.icons.TUNE_ROUNDED
        self.safe_update()

    def limpiar_todos_los_filtros(self, e=None):
        self.category_dropdown.value = "Todas"
        self.drop_estado.value = "Habilitados"
        self.fecha_corte = None
        self.btn_fecha_filtro.text = "Filtrar por Fecha"
        self.btn_clear_date.visible = False
        self.date_picker.value = None
        self.search_autocomplete.value = ""
        self.search_input_text.value = ""
        self.current_page = 1
        self.load_data()

    def _render_cards_local(self):
        if hasattr(self, "current_data") and self.current_data:
            self.card_list_view.controls.clear()
            for item in self.current_data:
                self.card_list_view.controls.append(self._crear_tarjeta_inventario(item))
            self.safe_update()
        
    def on_periodo_change(self, nuevo_periodo: str):
        self.current_page = 1
        self.load_data()

    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano con control de concurrencia."""
        if getattr(self, "_is_loading_data", False):
            return
        self._is_loading_data = True
        self.progress_bar.visible = True
        self.safe_update()
            
        def _worker_wrapper():
            try:
                self._fetch_data_worker()
            finally:
                self._is_loading_data = False

        threading.Thread(target=_worker_wrapper, daemon=True).start()

    def _fetch_data_worker(self):
        try:
            raw_auto = (self.search_autocomplete.value or "").strip()
            if not raw_auto:
                search_val = ""
                self.search_input_text.value = ""
            else:
                search_val = self.search_input_text.value or raw_auto
            cat_val = self.category_dropdown.value or "Todas"
            estado_val = self.drop_estado.value or "Habilitados"
            
            corte_efectivo = self.fecha_corte or self.periodo_selector.get_fecha_corte()

            data, total = self.db.get_insumos(
                page=self.current_page, 
                page_size=self.page_size, 
                search=search_val, 
                categoria=cat_val,
                fecha_corte=corte_efectivo,
                sort_col=self.sort_col_name,
                sort_asc=self.sort_is_asc,
                codigos_filtro=None,
                estado_filtro=estado_val
            )
            
            self.total_records = total
            self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
            
            # 1. Obtener Valorización de Inventario vía RPC nativo
            kpis = self.db.get_inventario_kpis(fecha_corte=corte_efectivo)
            self.valor_total_inventario = float(kpis.get("valor_inventario") or 0.0)

            # 2. Obtener Proyección Global de Ventas
            proyeccion_global = float(self.db.get_proyeccion_ventas(fecha_corte=corte_efectivo) or 0.0)

            # 3. Obtener ventas mes y hoy para calcular cumplimiento
            res_v = self.db.get_ventas_summary(fecha_corte=corte_efectivo)
            ventas_mes = float(res_v.get("total_mes") or 0.0)
            ventas_hoy = float(res_v.get("total_hoy") or 0.0)

            self.lbl_valor_inventario.value = f"${self.valor_total_inventario:,.0f}"
            self.lbl_sub_inv_det.value = "207 insumos con stock real > 0"
            self.lbl_proyeccion_ventas.value = f"${proyeccion_global:,.0f}"
            self.lbl_ventas_total.value = f"${ventas_mes:,.0f}"

            # Cumplimiento mes: Ventas realizadas / Capacidad Total (Ventas + Stock restante)
            meta_total_mes = ventas_mes + proyeccion_global
            cumpl_mes = (ventas_mes / meta_total_mes * 100) if meta_total_mes > 0 else 0.0
            txt_cumpl_mes = self.lbl_cumplimiento_mes.content
            txt_cumpl_mes.value = f"🎯 {cumpl_mes:.1f}% meta mes"
            self.lbl_cumplimiento_mes.bgcolor = "#e6f4ea" if cumpl_mes >= 100 else ("#e0f2fe" if cumpl_mes >= 50 else "#eff6ff")
            txt_cumpl_mes.color = "teal800" if cumpl_mes >= 100 else ("blue900" if cumpl_mes >= 50 else "blue800")
            self.lbl_sub_proy.value = f"Capacidad total: ${meta_total_mes:,.0f}"

            # Meta diaria
            hoy_dt = datetime.strptime(self.fecha_corte, "%Y-%m-%d").date() if self.fecha_corte else get_ahora_local().date()
            if hoy_dt.month == 12:
                ultimo_dia_mes = 31
            else:
                import calendar
                ultimo_dia_mes = calendar.monthrange(hoy_dt.year, hoy_dt.month)[1]
            dias_restantes = max(1, ultimo_dia_mes - hoy_dt.day + 1)
            meta_diaria = (proyeccion_global / dias_restantes) if dias_restantes > 0 and proyeccion_global > 0 else 0.0

            cumpl_hoy = (ventas_hoy / meta_diaria * 100) if meta_diaria > 0 else 0.0
            self.lbl_meta_diaria.value = f"${meta_diaria:,.0f} / día"
            self.lbl_cumplimiento_hoy.value = f"Hoy: ${ventas_hoy:,.0f} • {cumpl_hoy:.1f}% meta"

            # Guardar datos en memoria y renderizar tarjetas
            self.current_data = data
            self.card_list_view.controls.clear()
            
            for item in data:
                self.card_list_view.controls.append(self._crear_tarjeta_inventario(item))

        except Exception as ex:
            import traceback
            traceback.print_exc()
        finally:
            self.update_pagination_ui()

    def confirmar_cambio_estado_insumo(self, item, nuevo_estado: bool):
        codigo = str(item.get('codigo_insumo') or '')
        nombre = str(item.get('nombre') or '')
        
        accion_str = "Habilitar" if nuevo_estado else "Inhabilitar"
        color_btn = "green700" if nuevo_estado else "red700"
        
        if nuevo_estado:
            mensaje = f"¿Deseas volver a habilitar el insumo [{codigo}] {nombre}?\n\nVolverá a aparecer en el catálogo habitual y en las búsquedas activas de compras y ventas."
        else:
            mensaje = f"¿Deseas inhabilitar el insumo [{codigo}] {nombre}?\n\nNo se mostrará más en el catálogo estándar ni en búsquedas habituales, pero SE PRESERVARÁ toda su información y su historial completo de compras, ventas y ajustes."

        def on_confirmar(e):
            dlg.open = False
            self.safe_page_update()
            
            exito = self.db.update_insumo(codigo, {"estado": nuevo_estado})
            if exito:
                self.mostrar_alerta(f"✓ Insumo [{codigo}] {'habilitado' if nuevo_estado else 'inhabilitado'} exitosamente.", "green700")
                self.load_data()
            else:
                self.mostrar_alerta("Error al cambiar el estado del insumo en la base de datos.", "red")

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE if nuevo_estado else ft.icons.BLOCK_ROUNDED, color=color_btn, size=22),
                ft.Text(f"{accion_str} Insumo", size=16, weight="bold", color=Config.COLOR_PRIMARY)
            ], spacing=6),
            content=ft.Container(
                width=450,
                content=ft.Text(mensaje, size=12.5, color="grey800")
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), self.safe_page_update())),
                ft.ElevatedButton(f"Sí, {accion_str}", bgcolor=color_btn, color="white", on_click=on_confirmar)
            ]
        )
        
        if self.page:
            if dlg not in self.page.overlay:
                self.page.overlay.append(dlg)
            dlg.open = True
            self.safe_page_update()

    def abrir_modal_editar_insumo(self, item):
        codigo = str(item.get('codigo_insumo') or '')
        nombre_actual = str(item.get('nombre') or '')
        cat_actual = str(item.get('categoria') or 'GENERAL')
        ubicacion_actual = str(item.get('ubicacion') or '')
        zona_actual = str(item.get('zona') or '')
        tipo_unidad_actual = str(item.get('tipo_unidad') or 'UND')
        stock_min_actual = float(item.get('stock_minimo', 5) or 5)
        costo_u_actual = float(item.get('costo_unitario') or 0.0)
        p_venta_actual = float(item.get('precio_venta') or 0.0)
        stock_actual = float(item.get('stock_actual') or item.get('stock_real') or 0.0)
        estado_actual = item.get('estado', True) is not False

        txt_nombre = ft.TextField(
            label="Nombre del Insumo / Descripción",
            value=nombre_actual,
            dense=True,
            expand=True,
            border_radius=8,
            text_size=13
        )

        categorias_bd = self.db.get_categorias() if hasattr(self.db, 'get_categorias') else []
        opts_cat = [ft.dropdown.Option(c) for c in categorias_bd if c]
        if cat_actual and not any(o.key == cat_actual for o in opts_cat):
            opts_cat.insert(0, ft.dropdown.Option(cat_actual))
            
        drop_categoria = ft.Dropdown(
            label="Categoría",
            options=opts_cat,
            value=cat_actual if cat_actual in [o.key for o in opts_cat] else (opts_cat[0].key if opts_cat else None),
            dense=True,
            expand=True,
            border_radius=8,
            text_size=12
        )

        txt_ubicacion = ft.TextField(
            label="Ubicación / Bodega",
            value=ubicacion_actual,
            dense=True,
            expand=True,
            border_radius=8,
            text_size=12
        )

        txt_zona = ft.TextField(
            label="Zona",
            value=zona_actual,
            dense=True,
            width=130,
            border_radius=8,
            text_size=12
        )

        txt_costo = ft.TextField(
            label="Costo Unitario ($)",
            value=str(int(costo_u_actual) if costo_u_actual.is_integer() else costo_u_actual),
            dense=True,
            expand=True,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=12
        )

        txt_precio = ft.TextField(
            label="Precio Venta ($)",
            value=str(int(p_venta_actual) if p_venta_actual.is_integer() else p_venta_actual),
            dense=True,
            expand=True,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=12
        )

        txt_stock_min = ft.TextField(
            label="Stock Mínimo (Alerta)",
            value=str(int(stock_min_actual) if stock_min_actual.is_integer() else stock_min_actual),
            dense=True,
            expand=True,
            border_radius=8,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=12
        )

        txt_tipo_unidad = ft.TextField(
            label="Unidad Medida",
            value=tipo_unidad_actual,
            dense=True,
            expand=True,
            border_radius=8,
            text_size=12
        )

        drop_estado_edit = ft.Dropdown(
            label="Estado",
            options=[ft.dropdown.Option("Habilitado"), ft.dropdown.Option("Inhabilitado")],
            value="Habilitado" if estado_actual else "Inhabilitado",
            dense=True,
            expand=True,
            border_radius=8,
            text_size=12
        )

        # Labels de KPIs Financieros calculados
        lbl_costo_sin_iva = ft.Text("$0", size=11, weight="bold")
        lbl_margen_calc = ft.Text("0%", size=11, weight="bold", color="green700")
        lbl_ganancia_unidad = ft.Text("$0", size=11, weight="bold", color="blue800")
        lbl_val_stock = ft.Text(f"${costo_u_actual * stock_actual:,.0f}", size=11, weight="bold")
        lbl_obj_venta = ft.Text(f"${p_venta_actual * stock_actual:,.0f}", size=11, weight="bold", color="purple700")

        def _recalc_financiero(e=None):
            try:
                cu = float((txt_costo.value or "0").replace(',', '.'))
                pv = float((txt_precio.value or "0").replace(',', '.'))
                cu_sin_iva = (cu / 1.19) if cu > 0 else 0.0
                lbl_costo_sin_iva.value = f"${cu_sin_iva:,.0f}"
                
                if pv > 0 and cu > 0 and pv > cu:
                    margen = round((1 - (cu / pv)) * 100)
                    ganancia = pv - cu
                    lbl_margen_calc.value = f"{margen}%"
                    lbl_margen_calc.color = "green700" if margen >= 15 else "orange800"
                    lbl_ganancia_unidad.value = f"${ganancia:,.0f}"
                else:
                    lbl_margen_calc.value = "0%"
                    lbl_ganancia_unidad.value = "$0"

                lbl_val_stock.value = f"${cu * stock_actual:,.0f}"
                lbl_obj_venta.value = f"${pv * stock_actual:,.0f}"
            except ValueError:
                pass
            self.safe_page_update()

        txt_costo.on_change = _recalc_financiero
        txt_precio.on_change = _recalc_financiero
        _recalc_financiero()

        def _aplicar_margen_sugerido(pct):
            try:
                cu = float((txt_costo.value or "0").replace(',', '.'))
                if cu > 0 and pct < 100:
                    pv_calc = round(cu / (1 - (pct / 100)))
                    txt_precio.value = str(int(pv_calc))
                    _recalc_financiero()
            except ValueError:
                pass

        btn_margen_15 = ft.OutlinedButton("15%", height=28, style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=0)), on_click=lambda _: _aplicar_margen_sugerido(15))
        btn_margen_20 = ft.OutlinedButton("20%", height=28, style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=0)), on_click=lambda _: _aplicar_margen_sugerido(20))
        btn_margen_25 = ft.OutlinedButton("25%", height=28, style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=0)), on_click=lambda _: _aplicar_margen_sugerido(25))
        btn_margen_30 = ft.OutlinedButton("30%", height=28, style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=0)), on_click=lambda _: _aplicar_margen_sugerido(30))

        def _do_guardar_insumo(e):
            nuevo_nom = (txt_nombre.value or "").strip()
            if not nuevo_nom:
                self.mostrar_alerta("El nombre del insumo no puede estar vacío.", "red")
                return

            try:
                nuevo_costo = float((txt_costo.value or "0").replace(',', '.'))
                nuevo_precio = float((txt_precio.value or "0").replace(',', '.'))
                nuevo_stock_min = float((txt_stock_min.value or "0").replace(',', '.'))
            except ValueError:
                self.mostrar_alerta("Por favor ingresa valores numéricos válidos.", "red")
                return

            if nuevo_costo < 0 or nuevo_precio < 0 or nuevo_stock_min < 0:
                self.mostrar_alerta("Los valores de costo, precio y stock mínimo no pueden ser negativos.", "red")
                return

            payload = {
                "nombre": nuevo_nom,
                "categoria": (drop_categoria.value or cat_actual).strip(),
                "ubicacion": (txt_ubicacion.value or "").strip(),
                "zona": (txt_zona.value or "").strip(),
                "costo_unitario": nuevo_costo,
                "precio_venta": nuevo_precio,
                "stock_minimo": nuevo_stock_min,
                "tipo_unidad": (txt_tipo_unidad.value or "UND").strip(),
                "estado": (drop_estado_edit.value == "Habilitado")
            }

            dlg_editar.open = False
            self.safe_page_update()

            if self.db.update_insumo(codigo, payload):
                self.mostrar_alerta(f"✓ Insumo [{codigo}] actualizado correctamente.", "green700")
                self.load_data()
            else:
                self.mostrar_alerta(f"Error al actualizar el insumo [{codigo}] en la base de datos.", "red")

        panel_kpis_financieros = ft.Container(
            bgcolor="#f8fafc",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            content=ft.Row([
                ft.Column([ft.Text("Costo s/IVA:", size=10, color="grey600"), lbl_costo_sin_iva], spacing=1),
                ft.VerticalDivider(width=1, color="#cbd5e1"),
                ft.Column([ft.Text("Margen Bruto:", size=10, color="grey600"), lbl_margen_calc], spacing=1),
                ft.VerticalDivider(width=1, color="#cbd5e1"),
                ft.Column([ft.Text("Ganancia / Und:", size=10, color="grey600"), lbl_ganancia_unidad], spacing=1),
                ft.VerticalDivider(width=1, color="#cbd5e1"),
                ft.Column([ft.Text("Val. Stock Total:", size=10, color="grey600"), lbl_val_stock], spacing=1),
                ft.VerticalDivider(width=1, color="#cbd5e1"),
                ft.Column([ft.Text("Obj. Venta Total:", size=10, color="grey600"), lbl_obj_venta], spacing=1),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        dlg_editar = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.EDIT_NOTE_ROUNDED, color=Config.COLOR_PRIMARY, size=22),
                ft.Text(f"Editar Insumo [{codigo}]", size=16, weight="bold", color=Config.COLOR_PRIMARY, expand=True),
                ft.Container(
                    content=ft.Text(f"Stock Actual: {stock_actual:g} unds", size=11, weight="bold", color="teal800"),
                    bgcolor="#e6f4ea", padding=ft.padding.symmetric(horizontal=8, vertical=3), border_radius=6
                )
            ], spacing=6),
            content=ft.Container(
                width=620,
                content=ft.Column([
                    ft.Text("Información Básica", size=12, weight="bold", color="grey700"),
                    ft.Row([txt_nombre]),
                    ft.Row([drop_categoria, txt_ubicacion, txt_zona], spacing=8),
                    ft.Divider(height=1, color="#f1f5f9"),
                    ft.Row([
                        ft.Text("Precios y Márgenes", size=12, weight="bold", color="grey700", expand=True),
                        ft.Text("Fijar margen:", size=10.5, color="grey600"),
                        btn_margen_15, btn_margen_20, btn_margen_25, btn_margen_30
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    ft.Row([txt_costo, txt_precio], spacing=8),
                    panel_kpis_financieros,
                    ft.Divider(height=1, color="#f1f5f9"),
                    ft.Text("Control y Estado", size=12, weight="bold", color="grey700"),
                    ft.Row([txt_stock_min, txt_tipo_unidad, drop_estado_edit], spacing=8),
                ], tight=True, spacing=10)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg_editar, 'open', False), self.safe_page_update())),
                ft.ElevatedButton("Guardar Insumo", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=_do_guardar_insumo)
            ]
        )

        if self.page:
            if dlg_editar not in self.page.overlay:
                self.page.overlay.append(dlg_editar)
            dlg_editar.open = True
            self.safe_page_update()
        
    def update_pagination_ui(self):
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros en total"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        # Apagar indicador de carga al finalizar
        self.progress_bar.visible = False
        
        self.safe_update()
        
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
            
    def close_notification(self, e):
        self.notification_banner.visible = False
        self.safe_update()
        
    def open_date_picker(self, e=None):
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

    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_fecha_filtro.text = self.fecha_corte
            self.btn_clear_date.visible = True
            self.current_page = 1
            self.load_data()
            self.safe_update()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e=None):
        self.fecha_corte = None
        self.date_picker.value = None
        self.btn_fecha_filtro.text = "Filtrar por Fecha"
        self.btn_clear_date.visible = False
        self.current_page = 1
        self.load_data()
        self.safe_update()

    def abrir_modal_info_fecha(self, e=None):
        if self.page:
            if self.dlg_filtro_fecha_info not in self.page.overlay:
                self.page.overlay.append(self.dlg_filtro_fecha_info)
            self.dlg_filtro_fecha_info.open = True
            self.safe_page_update()

    def cerrar_modal_info_fecha(self, e=None):
        self.dlg_filtro_fecha_info.open = False
        self.safe_page_update()

    def lanzar_date_picker(self, e=None):
        self.cerrar_modal_info_fecha()
        self.open_date_picker()

    def ordenar_por(self, col_name: str):
        """Permite ordenar directamente al hacer clic en cualquier badge o métrica de las tarjetas."""
        if self.sort_col_name == col_name:
            self.sort_is_asc = not self.sort_is_asc
        else:
            self.sort_col_name = col_name
            # Para columnas numéricas, el primer clic ordena descendentemente (mayor a menor)
            self.sort_is_asc = False if col_name not in ["Insumo", "Código", "Categoría", "Ubicación"] else True

        self.current_page = 1
        direccion_txt = "Menor a Mayor ↑" if self.sort_is_asc else "Mayor a Menor ↓"
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"📊 Ordenando por {col_name} ({direccion_txt})", weight="bold"),
                bgcolor=Config.COLOR_PRIMARY,
                duration=1200
            )
            self.page.snack_bar.open = True
            self.page.update()
        self.load_data()

    def on_guardar_global(self, e=None):
        pass

    def on_cancelar_global(self, e=None):
        pass

    def _construir_modal_ajuste_inventario(self):
        self.mapa_motivos_inventario = {
            "Sobrante de Inventario": "ENTRADA_POR_SOBRANTE",
            "Donación Entrante": "AJUSTE_ENTRADA",
            "Devolución Cliente": "AJUSTE_ENTRADA",
            "Otro (Entrada)": "AJUSTE_ENTRADA",
            "Daño / Merma": "AJUSTE_SALIDA",
            "Vencimiento": "BAJA_VENCIMIENTO",
            "Pérdida": "SALIDA_POR_FALTANTE",
            "Consumo Familiar": "AJUSTE_SALIDA",
            "Consumo Cliente (Cortesía)": "AJUSTE_SALIDA",
            "Donación Saliente": "AJUSTE_SALIDA",
            "Otro (Salida)": "AJUSTE_SALIDA"
        }
        
        self.ajuste_lbl_insumo = ft.Text("Insumo seleccionado", weight="bold", size=14, color=Config.COLOR_PRIMARY)
        self.ajuste_lbl_stock_actual = ft.Text("Stock Actual: 0 unds", size=12, color="grey700", weight="w500")
        
        self.ajuste_tipo = ft.Dropdown(
            label="Tipo de Ajuste",
            options=[ft.dropdown.Option("ENTRADA (+)"), ft.dropdown.Option("SALIDA (-)")],
            value="SALIDA (-)",
            width=250,
            dense=True,
            on_change=self._on_ajuste_tipo_change
        )
        
        self.ajuste_motivo = ft.Dropdown(
            label="Motivo del Ajuste",
            options=[],
            width=250,
            dense=True
        )
        
        self.ajuste_cantidad = ft.TextField(
            label="Cantidad a Ajustar",
            width=160,
            dense=True,
            on_change=self._calc_tot_ajuste_modal
        )
        
        self.ajuste_costo = ft.TextField(
            label="Costo Unitario",
            prefix_text="$",
            width=160,
            dense=True,
            on_change=self._calc_tot_ajuste_modal
        )
        
        self.ajuste_lbl_impacto = ft.Text("$ 0", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.ajuste_lbl_nuevo_stock = ft.Text("0 unds", size=14, weight="bold", color="teal700")
        
        self.ajuste_obs = ft.TextField(
            label="Observaciones / Justificación (Opcional)",
            multiline=True,
            min_lines=2,
            max_lines=3,
            dense=True
        )
        
        self.dlg_ajuste_inventario = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.TUNE, color=Config.COLOR_ACCENT, size=24),
                ft.Text("Registrar Ajuste de Inventario", weight="bold", size=18, color=Config.COLOR_PRIMARY)
            ], spacing=10),
            content=ft.Container(
                width=550,
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            self.ajuste_lbl_insumo,
                            self.ajuste_lbl_stock_actual
                        ], spacing=2),
                        padding=12,
                        bgcolor="#f1f5f9",
                        border_radius=8,
                        border=ft.border.all(1, "#cbd5e1")
                    ),
                    ft.Row([self.ajuste_tipo, self.ajuste_motivo], spacing=15),
                    ft.Row([self.ajuste_cantidad, self.ajuste_costo], spacing=15),
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text("Impacto Financiero:", size=11, color="grey"),
                                self.ajuste_lbl_impacto
                            ], spacing=2),
                            ft.Column([
                                ft.Text("Nuevo Stock Resultante:", size=11, color="grey"),
                                self.ajuste_lbl_nuevo_stock
                            ], spacing=2)
                        ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                        padding=10,
                        bgcolor="#f8fafc",
                        border_radius=8,
                        border=ft.border.all(1, "#e2e8f0")
                    ),
                    self.ajuste_obs
                ], tight=True, spacing=14)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_modal_ajuste()),
                ft.ElevatedButton(
                    "Guardar Ajuste",
                    icon=ft.icons.CHECK,
                    bgcolor="green700",
                    color="white",
                    on_click=self._guardar_ajuste_insumo
                )
            ]
        )

    def _on_ajuste_tipo_change(self, e=None):
        tipo = self.ajuste_tipo.value or "SALIDA (-)"
        if "ENTRADA" in tipo:
            motivos = ["Sobrante de Inventario", "Donación Entrante", "Devolución Cliente", "Otro (Entrada)"]
        else:
            motivos = ["Daño / Merma", "Vencimiento", "Pérdida", "Consumo Familiar", "Consumo Cliente (Cortesía)", "Donación Saliente", "Otro (Salida)"]
        self.ajuste_motivo.options = [ft.dropdown.Option(m) for m in motivos]
        self.ajuste_motivo.value = motivos[0] if motivos else None
        self._calc_tot_ajuste_modal()
        self.safe_page_update()

    def _calc_tot_ajuste_modal(self, e=None):
        try:
            cant_str = (self.ajuste_cantidad.value or "").replace(',', '.').strip()
            costo_str = (self.ajuste_costo.value or "").replace(',', '.').strip()
            cant = float(cant_str) if cant_str else 0.0
            costo = float(costo_str) if costo_str else 0.0
            tot = cant * costo
            self.ajuste_lbl_impacto.value = f"$ {tot:,.0f}"
            
            tipo = self.ajuste_tipo.value or "SALIDA (-)"
            stock_act = getattr(self, '_ajuste_stock_base', 0.0)
            if "ENTRADA" in tipo:
                nuevo_stock = stock_act + cant
            else:
                nuevo_stock = stock_act - cant
            self.ajuste_lbl_nuevo_stock.value = f"{nuevo_stock:g} unds"
            self.safe_page_update()
        except ValueError:
            self.ajuste_lbl_impacto.value = "$ 0"
            self.safe_page_update()

    def abrir_modal_ajuste_insumo(self, item):
        if not hasattr(self, 'dlg_ajuste_inventario'):
            self._construir_modal_ajuste_inventario()
            
        cod = str(item.get('codigo_insumo') or '')
        nom = str(item.get('nombre') or 'Desconocido')
        cat = str(item.get('categoria') or 'GENERAL')
        stock = float(item.get('stock_actual') or item.get('stock_real') or 0)
        costo = float(item.get('costo_unitario') or 0)
        
        self._ajuste_item_actual = item
        self._ajuste_stock_base = stock
        
        self.ajuste_lbl_insumo.value = f"[{cod}] {nom}"
        self.ajuste_lbl_stock_actual.value = f"Categoría: {cat}  •  Stock Sistema: {stock:g} unds"
        self.ajuste_tipo.value = "SALIDA (-)"
        self._on_ajuste_tipo_change()
        
        self.ajuste_cantidad.value = ""
        self.ajuste_costo.value = str(int(costo) if costo.is_integer() else costo)
        self.ajuste_obs.value = ""
        self._calc_tot_ajuste_modal()
        
        if self.page:
            if self.dlg_ajuste_inventario not in self.page.overlay:
                self.page.overlay.append(self.dlg_ajuste_inventario)
            self.dlg_ajuste_inventario.open = True
            self.safe_page_update()

    def _cerrar_modal_ajuste(self):
        if hasattr(self, 'dlg_ajuste_inventario'):
            self.dlg_ajuste_inventario.open = False
            self.safe_page_update()

    def _guardar_ajuste_insumo(self, e):
        try:
            cant_str = (self.ajuste_cantidad.value or "").replace(',', '.').strip()
            costo_str = (self.ajuste_costo.value or "").replace(',', '.').strip()
            cant = float(cant_str) if cant_str else 0.0
            costo = float(costo_str) if costo_str else 0.0
            motivo_ui = self.ajuste_motivo.value
            obs = (self.ajuste_obs.value or "").strip()
            
            if cant <= 0:
                self.mostrar_alerta("La cantidad a ajustar debe ser mayor a cero.", "red")
                return
                
            if not motivo_ui:
                self.mostrar_alerta("Debes seleccionar un motivo para el ajuste.", "red")
                return
                
            item = getattr(self, '_ajuste_item_actual', {})
            cod = str(item.get('codigo_insumo') or '')
            tipo_bd = self.mapa_motivos_inventario.get(motivo_ui, "AJUSTE_SALIDA")
            
            datos = {
                "codigo_insumo": cod,
                "tipo_ajuste": tipo_bd,
                "cantidad": cant,
                "costo_unitario_congelado": costo,
                "costo_total_ajuste": cant * costo,
                "motivo_observacion": obs if obs else motivo_ui,
                "estado_registro": "VÁLIDO"
            }
            
            if self.db.insert_ajuste_individual(datos):
                self._cerrar_modal_ajuste()
                self.load_data()
                self.load_summary()
                self.mostrar_alerta(f"✓ Ajuste ({tipo_bd}) registrado exitosamente para [{cod}]", "green700")
            else:
                self.mostrar_alerta("Error al registrar el ajuste en la base de datos.", "red")
        except ValueError:
            self.mostrar_alerta("Formato numérico inválido en cantidad o costo.", "red")
        except Exception as ex:
            self.mostrar_alerta(f"Error al guardar ajuste: {str(ex)}", "red")

    def _crear_tarjeta_inventario(self, item):
        codigo = str(item.get('codigo_insumo') or '')
        nombre = str(item.get('nombre') or '')
        categoria = str(item.get('categoria') or '')
        ubicacion = str(item.get('ubicacion') or 'N/A')
        
        # Extracción Segura
        stock_inicial = float(item.get("stock_inicial") or 0)
        valor_inicial = float(item.get("valor_inicial") or 0)
        costo_u = float(item.get('costo_unitario') or 0)
        costo_antes_iva = (costo_u / 1.19) if costo_u > 0 else 0
        p_venta = float(item.get('precio_venta') or 0)

        compras = float(item.get("compras") if item.get("compras") is not None else (item.get("entradas") or 0))
        valor_compras = float(item.get("valor_compras") if item.get("valor_compras") is not None else (compras * costo_u))
        ventas = float(item.get("ventas") if item.get("ventas") is not None else (item.get("salidas") or 0))
        valor_ventas = float(item.get("valor_ventas") if item.get("valor_ventas") is not None else (item.get("venta_total_insumo") or (ventas * p_venta)))
        ajustes_entrantes = float(item.get("ajustes_entrantes") or 0)
        valor_ajustes_entrantes = float(item.get("valor_ajustes_entrantes") or (ajustes_entrantes * costo_u))
        ajustes_salientes = float(item.get("ajustes_salientes") or 0)
        valor_ajustes_salientes = float(item.get("valor_ajustes_salientes") or (ajustes_salientes * costo_u))
        neto_ajustes = float(item.get("neto_ajustes") if item.get("neto_ajustes") is not None else (item.get("ajustes") or (ajustes_entrantes - ajustes_salientes)))
        valor_neto_ajustes = float(item.get("valor_neto_ajustes") if item.get("valor_neto_ajustes") is not None else (valor_ajustes_entrantes - valor_ajustes_salientes))
        
        stock_actual = float(item.get('stock_actual') if item.get('stock_actual') is not None else (item.get('stock_real') or 0))
        costo_total_insumo = float(item.get('costo_total_insumo') if item.get('costo_total_insumo') is not None else (stock_actual * costo_u))
        objetivo_venta = stock_actual * p_venta if stock_actual > 0 else 0
        
        # 1. Costo s/IVA (primero)
        badge_costo_sin_iva = ft.Container(
            content=ft.Text(
                spans=[
                    ft.TextSpan("Costo s/IVA: ", ft.TextStyle(size=11, color="grey700", weight="w500")),
                    ft.TextSpan(f"${costo_antes_iva:,.0f}", ft.TextStyle(size=11, color="black87", weight="bold")),
                ]
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor="#f8fafc",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=6,
            tooltip="Clic para ordenar por Costo antes de IVA",
            on_click=lambda _: self.ordenar_por("Costo s/IVA")
        )

        # 2. Costo Unitario (después)
        badge_costo = ft.Container(
            content=ft.Text(
                spans=[
                    ft.TextSpan("Costo U: ", ft.TextStyle(size=11, color="grey700", weight="w500")),
                    ft.TextSpan(f"${costo_u:,.0f}", ft.TextStyle(size=11, color="black87", weight="bold")),
                ]
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor="#f1f5f9",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=6,
            tooltip="Clic para ordenar por Costo Unitario",
            on_click=lambda _: self.ordenar_por("Costo U")
        )

        # 3. Precio Venta Dinámico
        txt_pventa = ft.Text(
            spans=[
                ft.TextSpan("P. Venta: ", ft.TextStyle(size=11, color="blue800", weight="w500")),
                ft.TextSpan(f"${p_venta:,.0f}", ft.TextStyle(size=11, color="blue900", weight="bold")),
            ]
        )
        badge_pventa = ft.Container(
            content=txt_pventa,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor="#eff6ff",
            border=ft.border.all(1, "#bfdbfe"),
            border_radius=6,
            tooltip="Clic para ordenar por Precio de Venta",
            on_click=lambda _: self.ordenar_por("P. Venta")
        )

        # 4. Checks rápidos de margen (10, 15, 20)
        checks_map = {}
        txt_objetivo = ft.Text(
            spans=[
                ft.TextSpan("Objetivo Venta: ", ft.TextStyle(size=11, color="blue800", weight="w500")),
                ft.TextSpan(f"${objetivo_venta:,.0f}", ft.TextStyle(size=11, color="blue900", weight="bold")),
            ]
        )

        def cambiar_margen_rapido(pct):
            if costo_u <= 0:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("El insumo no tiene costo unitario para calcular el margen."), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.page.update()
                return

            nuevo_p = round(costo_u / (1 - (pct / 100)))
            exito = self.db.update_insumo(codigo, {"precio_venta": nuevo_p})
            if exito:
                item["precio_venta"] = nuevo_p
                # Actualizar TextSpans
                txt_pventa.spans = [
                    ft.TextSpan("P. Venta: ", ft.TextStyle(size=11, color="blue800", weight="w500")),
                    ft.TextSpan(f"${nuevo_p:,.0f}", ft.TextStyle(size=11, color="blue900", weight="bold")),
                ]
                nuevo_obj = stock_actual * nuevo_p if stock_actual > 0 else 0
                txt_objetivo.spans = [
                    ft.TextSpan("Objetivo Venta: ", ft.TextStyle(size=11, color="blue800", weight="w500")),
                    ft.TextSpan(f"${nuevo_obj:,.0f}", ft.TextStyle(size=11, color="blue900", weight="bold")),
                ]
                # Actualizar aspecto visual de los 3 checks
                for p_val, c_btn in checks_map.items():
                    is_sel = (p_val == pct)
                    c_btn.bgcolor = Config.COLOR_PRIMARY if is_sel else "#f1f5f9"
                    c_btn.border = ft.border.all(1, Config.COLOR_PRIMARY if is_sel else "#cbd5e1")
                    c_btn.content.color = "white" if is_sel else "grey800"
                    c_btn.content.weight = "bold" if is_sel else "w500"

                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"✓ [{codigo}] {nombre}: Precio ajustado al {pct}% (${nuevo_p:,.0f})"), bgcolor=Config.COLOR_SUCCESS)
                    self.page.snack_bar.open = True
                    self.page.update()
            else:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al actualizar precio en base de datos"), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.page.update()

        def crear_check_margen(pct):
            margen_est = round((1 - (costo_u / p_venta)) * 100) if (p_venta > 0 and costo_u > 0) else 0
            is_active = (abs(margen_est - pct) <= 1)
            btn = ft.Container(
                content=ft.Text(f"{pct}%", size=10, weight="bold" if is_active else "w500", color="white" if is_active else "grey800"),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                bgcolor=Config.COLOR_PRIMARY if is_active else "#f1f5f9",
                border=ft.border.all(1, Config.COLOR_PRIMARY if is_active else "#cbd5e1"),
                border_radius=10,
                tooltip=f"Fijar precio con margen del {pct}%",
                on_click=lambda e, p=pct: cambiar_margen_rapido(p)
            )
            checks_map[pct] = btn
            return btn

        # 5. Conteo Físico (si existe registro móvil/auditoría)
        badge_conteo_fisico = None
        cant_fisica = item.get("cantidad_fisica")
        if cant_fisica is not None:
            cant_fis_num = float(cant_fisica)
            dif_fisica = cant_fis_num - stock_actual
            dif_txt = f" ({dif_fisica:+g})" if abs(dif_fisica) > 0.001 else " (OK)"
            dif_color = "#047857" if abs(dif_fisica) < 0.001 else ("#0284c7" if dif_fisica > 0 else "#dc2626")
            
            badge_conteo_fisico = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.FACT_CHECK_ROUNDED, size=13, color="#6366f1"),
                    ft.Text(
                        spans=[
                            ft.TextSpan("Físico: ", ft.TextStyle(size=11, color="grey800", weight="bold")),
                            ft.TextSpan(f"{cant_fis_num:g} unds", ft.TextStyle(size=12, color="#4338ca", weight="extrabold")),
                            ft.TextSpan(dif_txt, ft.TextStyle(size=10, color=dif_color, weight="bold")),
                        ]
                    )
                ], spacing=3, tight=True),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                bgcolor="#eef2ff",
                border=ft.border.all(1.5, "#c7d2fe"),
                border_radius=8,
                tooltip=f"Conteo físico registrado desde la web: {cant_fis_num:g} unds | {item.get('observacion_auditoria') or ''}"
            )

        # 6. Stock Actual DESTACADO Y MÁS GRANDE (Alineado a la derecha)
        if stock_actual > 0:
            bg_stock = "#ecfdf5"
            border_stock = "#a7f3d0"
            color_stock = "#047857"
        elif stock_actual == 0:
            bg_stock = "#fffbe8"
            border_stock = "#fde68a"
            color_stock = "#b45309"
        else:
            bg_stock = "#fef2f2"
            border_stock = "#fecaca"
            color_stock = "#b91c1c"

        badge_stock = ft.Container(
            content=ft.Text(
                spans=[
                    ft.TextSpan("Stock Actual: ", ft.TextStyle(size=12, color=color_stock, weight="bold")),
                    ft.TextSpan(f"{stock_actual:g} unds", ft.TextStyle(size=13, color=color_stock, weight="extrabold")),
                ]
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            bgcolor=bg_stock,
            border=ft.border.all(1.5, border_stock),
            border_radius=8,
            tooltip="Clic para ordenar por Stock Actual",
            on_click=lambda _: self.ordenar_por("Stock Actual")
        )

        # 7. Valor Total en Costo
        badge_valor_costo = ft.Container(
            content=ft.Text(
                spans=[
                    ft.TextSpan("Valor Costo: ", ft.TextStyle(size=11, color="grey700", weight="w500")),
                    ft.TextSpan(f"${costo_total_insumo:,.0f}", ft.TextStyle(size=11, color="black87", weight="bold")),
                ]
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor="#f8fafc",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=6,
            tooltip="Clic para ordenar por Valor Total en Costo",
            on_click=lambda _: self.ordenar_por("Valor Costo")
        )

        # 8. Objetivo de Venta
        badge_objetivo_venta = ft.Container(
            content=txt_objetivo,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor="#eff6ff",
            border=ft.border.all(1, "#bfdbfe"),
            border_radius=6,
            tooltip="Clic para ordenar por Objetivo de Venta",
            on_click=lambda _: self.ordenar_por("Objetivo Venta")
        )

        # Contenedor dividido: Izquierda (Precios y Margen) y Derecha (Stock y Totales)
        badges_derecha = [b for b in [badge_conteo_fisico, badge_stock, badge_valor_costo, badge_objetivo_venta] if b is not None]
        contenedor_badges = ft.Row(
            [
                ft.Row([
                    badge_costo_sin_iva,
                    badge_costo,
                    badge_pventa,
                    ft.Container(
                        content=ft.Row([
                            ft.Text("Margen:", size=10, color="grey600", weight="w500"),
                            crear_check_margen(10),
                            crear_check_margen(15),
                            crear_check_margen(20)
                        ], spacing=3, tight=True),
                        padding=ft.padding.only(left=2)
                    )
                ], spacing=6, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
                
                ft.Container(expand=True),
                
                ft.Row(badges_derecha, spacing=6, alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
            ], 
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=False
        )

        def crear_bloque_metricas(titulo, cantidad, valor, color_cant, color_valor):
            return ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Text(titulo, size=9, color="grey", weight="bold"),
                    ft.Text(f"{cantidad:g} unds", size=11, weight="bold", color=color_cant, no_wrap=True),
                    ft.Text(f"${valor:,.0f}", size=11, color=color_valor, weight="w500", no_wrap=True)
                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=4),
                tooltip=f"Clic para ordenar por {titulo}",
                on_click=lambda _, t=titulo: self.ordenar_por(t)
            )

        def crear_separador_vertical():
            return ft.Container(
                width=1,
                height=26,
                bgcolor="#e0e0e0",
                margin=ft.padding.symmetric(horizontal=4)
            )
            
        color_neto = "red" if valor_neto_ajustes < 0 else ("green" if valor_neto_ajustes > 0 else "grey")
            
        fila_resultados = ft.Container(
            content=ft.Row([
                crear_bloque_metricas("INICIAL", stock_inicial, valor_inicial, "grey", "grey"),
                crear_separador_vertical(),
                crear_bloque_metricas("COMPRAS", compras, valor_compras, "green700", "black87"),
                crear_separador_vertical(),
                crear_bloque_metricas("VENTAS", ventas, valor_ventas, "blue700", "black87"),
                crear_separador_vertical(),
                crear_bloque_metricas("AJUSTES (+)", ajustes_entrantes, valor_ajustes_entrantes, "green700", "green700"),
                crear_separador_vertical(),
                crear_bloque_metricas("AJUSTES (-)", ajustes_salientes, valor_ajustes_salientes, "red700", "red700"),
                crear_separador_vertical(),
                crear_bloque_metricas("NETO", neto_ajustes, valor_neto_ajustes, color_neto, color_neto)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#fafafa",
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            border_radius=6,
            border=ft.border.all(1, "#f0f0f0"),
            visible=self.mostrar_detalle_kpis
        )

        esta_activo = item.get("estado", True) is not False
        badge_inhabilitado = ft.Container(
            content=ft.Text("INHABILITADO", size=9, weight="bold", color="red700"),
            bgcolor="#fef2f2",
            border=ft.border.all(1, "#fecaca"),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=4,
            visible=not esta_activo
        )

        btn_ajustar_stock = ft.IconButton(
            icon=ft.icons.TUNE,
            icon_size=16,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Ajustar Stock",
            on_click=lambda e, i=item: self.abrir_modal_ajuste_insumo(i)
        )

        btn_editar_insumo = ft.IconButton(
            icon=ft.icons.EDIT_OUTLINED,
            icon_size=16,
            icon_color="blue700",
            tooltip="Editar Insumo",
            on_click=lambda e, i=item: self.abrir_modal_editar_insumo(i)
        )

        if esta_activo:
            btn_estado_insumo = ft.IconButton(
                icon=ft.icons.BLOCK_ROUNDED,
                icon_size=16,
                icon_color="red700",
                tooltip="Inhabilitar Insumo",
                on_click=lambda e, i=item: self.confirmar_cambio_estado_insumo(i, False)
            )
        else:
            btn_estado_insumo = ft.IconButton(
                icon=ft.icons.CHECK_CIRCLE_ROUNDED,
                icon_size=18,
                icon_color="green700",
                tooltip="Habilitar / Reactivar Insumo",
                on_click=lambda e, i=item: self.confirmar_cambio_estado_insumo(i, True)
            )

        tarjeta = ft.Container(
            bgcolor="white" if esta_activo else "#fafafa",
            padding=10,
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0" if esta_activo else "#fecaca"),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"{categoria} | {ubicacion}", size=10, weight="bold", color="grey700"),
                        bgcolor="#f5f5f5", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4
                    ),
                    badge_inhabilitado,
                    ft.Text(f"[{codigo}] {nombre}", size=13, weight="bold", color="black87" if esta_activo else "grey700", expand=True),
                    btn_ajustar_stock,
                    btn_editar_insumo,
                    btn_estado_insumo
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                contenedor_badges,
                fila_resultados
            ], spacing=6)
        )
        return tarjeta

