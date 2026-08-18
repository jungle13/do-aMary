import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import math
from datetime import datetime

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
        
        # Variables de Ordenamiento por Servidor
        self.sort_col_name = "Insumo"
        self.sort_is_asc = True
        
        self.view_mode = "cards"
        self.btn_toggle_view = ft.IconButton(
            icon=ft.icons.TABLE_ROWS,
            tooltip="Cambiar a vista de Tabla",
            on_click=self.toggle_view
        )
        
        # Controles de Búsqueda
        self.search_input = ft.TextField(
            hint_text="Buscar por código o nombre...", 
            prefix_icon=ft.icons.SEARCH,
            border_radius=8,
            expand=True,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_submit=self.on_search
        )
        
        self.category_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            label="Categoría",
            width=220,
            border_radius=8,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_search
        )
        
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )
        self.btn_date = ft.OutlinedButton(
            text="Filtrar por Fecha",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=self.open_date_picker,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=40,
            width=200
        )
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Definición de la Tabla de Datos (Ajuste de espacios y ordenamiento)
        self.data_table = ft.DataTable(
            column_spacing=10, # Reduce el espacio entre columnas
            horizontal_margin=10,
            data_row_min_height=30, # Reduce la altura de las filas
            data_row_max_height=30,
            heading_row_height=40,
            sort_column_index=0,
            sort_ascending=True,
            columns=[
                ft.DataColumn(ft.Container(width=25)),
                ft.DataColumn(ft.Text("Código", weight="bold", size=10), on_sort=self.on_sort_table),
                ft.DataColumn(ft.Container(content=ft.Text("Insumo", weight="bold", size=10), width=250), on_sort=self.on_sort_table),
                ft.DataColumn(ft.Text("Categoría", weight="bold", size=10), on_sort=self.on_sort_table),
                ft.DataColumn(ft.Text("Ubicación", weight="bold", size=10)),
                ft.DataColumn(ft.Container(content=ft.Text("Stock Ini.", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text("Stock Mín.", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text("Entradas", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
                ft.DataColumn(ft.Container(content=ft.Text("Salidas", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
                ft.DataColumn(ft.Container(content=ft.Text("Stock Real", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
                ft.DataColumn(ft.Text("Costo Unit.", weight="bold", size=10), numeric=True),
                ft.DataColumn(ft.Text("Costo Total", weight="bold", size=10), numeric=True),
                ft.DataColumn(ft.Text("Precio Venta", weight="bold", size=10), numeric=True),
                ft.DataColumn(ft.Text("Venta Total", weight="bold", size=10), numeric=True),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        self.table_container = ft.Container(
            content=ft.Column(
                [self.data_table],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            )
        )
        
        self.table_wrapper = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [self.table_container],
                        scroll=ft.ScrollMode.ALWAYS
                    )
                ],
                scroll=ft.ScrollMode.ALWAYS,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            bgcolor="white",
            padding=5,
            border_radius=10,
            expand=True,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black")),
            visible=False
        )
        
        self.card_list_view = ft.ListView(expand=True, spacing=10, visible=True)
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        
        self.current_edit_context = None
        
        self.edit_panel_title = ft.Text("Editando Insumo", color="white", weight="bold", size=16)
        
        input_style = {
            "text_size": 13,
            "height": 40,
            "content_padding": 10,
            "bgcolor": "white",
            "color": "black",
            "border_color": ft.colors.with_opacity(0.3, "white"),
        }
        
        self.edit_stock_minimo = ft.TextField(width=120, **input_style)
        self.edit_costo = ft.TextField(width=120, **input_style)
        self.edit_margen = ft.Dropdown(
            width=100, 
            options=[ft.dropdown.Option(f"{p}%") for p in [10, 15, 20, 25, 30, 35]],
            **input_style
        )
        self.edit_precio = ft.TextField(width=120, **input_style)
        
        self.edit_categoria = ft.Dropdown(
            width=200, 
            **input_style
        )
        
        def calcular_precio(e):
            try:
                costo = float(self.edit_costo.value.replace(',', '.') or 0)
                if self.edit_margen.value:
                    margen_str = self.edit_margen.value.replace('%', '')
                    margen_dec = float(margen_str) / 100.0
                    if margen_dec < 1 and costo > 0:
                        # Fórmula financiera de margen sobre precio de venta
                        precio_calculado = costo / (1 - margen_dec)
                        self.edit_precio.value = f"{precio_calculado:.2f}"
            except ValueError:
                pass
            verificar_cambios_panel(e)

        def verificar_cambios_panel(e):
            if not self.current_edit_context: return
            item = self.current_edit_context['item']
            cambiado = False
            try:
                if str(int(self.edit_stock_minimo.value)) != str(int(item.get('stock_minimo', 5) or 5)): cambiado = True
                if str(float(self.edit_costo.value)) != str(float(item.get('costo_unitario') or 0)): cambiado = True
                if str(float(self.edit_precio.value)) != str(float(item.get('precio_venta') or 0)): cambiado = True
                if self.edit_categoria.value != str(item.get('categoria', '')): cambiado = True
            except ValueError:
                cambiado = False
                
            self.btn_guardar_edicion.disabled = not cambiado
            self.action_bar.update()

        self.edit_margen.on_change = calcular_precio
        self.edit_costo.on_change = calcular_precio
        self.edit_precio.on_change = verificar_cambios_panel
        self.edit_stock_minimo.on_change = verificar_cambios_panel
        self.edit_categoria.on_change = verificar_cambios_panel
        
        self.btn_guardar_edicion = ft.ElevatedButton(
            "Guardar Cambios",
            disabled=True,
            on_click=self.on_guardar_global,
            style=ft.ButtonStyle(
                bgcolor={ft.MaterialState.DISABLED: "#495057", ft.MaterialState.DEFAULT: "green"},
                color={ft.MaterialState.DISABLED: "white70", ft.MaterialState.DEFAULT: "white"},
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )
        
        self.btn_gestionar_ajustes = ft.OutlinedButton(
            "Gestionar Ajustes",
            icon=ft.icons.TUNE,
            style=ft.ButtonStyle(color="white"),
            on_click=self.on_gestionar_ajustes
        )
        
        self.action_bar = ft.Container(
            content=ft.Column([
                ft.Row([self.edit_panel_title, self.btn_gestionar_ajustes], alignment=ft.MainAxisAlignment.START, spacing=15),
                ft.Row([
                    ft.Column([
                        ft.Text("Stock Mínimo", color="white70", size=11, weight="bold"),
                        self.edit_stock_minimo
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Costo Unit.", color="white70", size=11, weight="bold"),
                        self.edit_costo
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Ganancia", color="white70", size=11, weight="bold"),
                        self.edit_margen
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Precio Venta", color="white70", size=11, weight="bold"),
                        self.edit_precio
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Categoría", color="white70", size=11, weight="bold"),
                        self.edit_categoria
                    ], spacing=4),
                    ft.Container(expand=True),
                    ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color="white"), on_click=self.on_cancelar_global),
                    self.btn_guardar_edicion
                ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=10),
            bgcolor=Config.COLOR_PRIMARY,
            padding=15,
            border_radius=10,
            visible=False,
            margin=ft.padding.only(top=10)
        )
        
        # Dashboard Resumen
        self.lbl_valor_inventario = ft.Text("$0", size=20, weight="bold", color="blue")
        self.lbl_ventas_total = ft.Text("$0", size=20, weight="bold", color="green")
        self.lbl_proyeccion_ventas = ft.Text("$0", size=20, weight="bold", color="blue")
        
        self.summary_container = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.INVENTORY, color="blue", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "blue"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Valorización del Inventario", size=12, color="grey", weight="bold"),
                        self.lbl_valor_inventario
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.ATTACH_MONEY, color="green", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "green"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Ingreso Total (Ventas)", size=12, color="grey", weight="bold"),
                        self.lbl_ventas_total
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.MONETIZATION_ON, color="blue", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "blue"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Proyección de Ventas", size=12, color="grey", weight="bold"),
                        self.lbl_proyeccion_ventas
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            )
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
        
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        self.lbl_titulo = ft.Text("Catálogo de Insumos", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.content = ft.Column([
            self.progress_bar,
            self.lbl_titulo,
            self.summary_container,
            
            # Toolbar de Filtros
            ft.Container(
                content=ft.Row([
                    self.search_input,
                    self.category_dropdown,
                    self.btn_date,
                    self.btn_clear_date,
                    ft.ElevatedButton(
                        text="Buscar", 
                        icon=ft.icons.SEARCH,
                        bgcolor=Config.COLOR_PRIMARY,
                        color="white",
                        height=40,
                        on_click=self.on_search,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    self.btn_toggle_view,
                    self.btn_fullscreen
                ]),
                bgcolor="white",
                padding=10,
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            # Contenedores de Vista Dual
            self.table_wrapper,
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
            ),
            self.action_bar
        ], expand=True, spacing=10)
        
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
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
            self.safe_update()
            
        # Lógica responsiva para la tabla
        def handle_resize(e):
            if getattr(self, "page", None) and getattr(self, "table_container", None):
                available = self.page.width - 320
                self.table_container.width = max(1300, available)
                try:
                    self.table_container.update()
                except Exception:
                    pass
                
        self.handle_resize = handle_resize
        
        # Suscribir de manera segura según la versión de Flet
        if hasattr(self.page.on_resize, "subscribe"):
            self.page.on_resize.subscribe(self.handle_resize)
        else:
            self.original_on_resize = self.page.on_resize
            self.page.on_resize = self.handle_resize
            
        handle_resize(None) # Ejecutar una vez para inicializar tamaño
            
        self.load_categories()
        self.load_summary()
        self.load_data()
        

    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass
    def load_summary(self):
        res_v = self.db.get_ventas_summary()
        res_i = self.db.get_inventario_kpis()
        self.lbl_valor_inventario.value = f"${res_i.get('valor_inventario', 0):,.2f}"
        self.lbl_ventas_total.value = f"${res_v.get('total_mes', 0):,.2f}"
        # La proyección se calcula localmente en _fetch_data_worker
        self.safe_update()
            
    def will_unmount(self):
        """Se ejecuta cuando se destruye la vista."""
        if hasattr(self.page, "on_resize") and hasattr(self.page.on_resize, "unsubscribe") and hasattr(self, "handle_resize"):
            self.page.on_resize.unsubscribe(self.handle_resize)
        elif hasattr(self, "original_on_resize"):
            self.page.on_resize = self.original_on_resize
        
    def load_categories(self):
        cats = self.db.get_categorias()
        options = [ft.dropdown.Option("Todas")]
        for c in cats:
            if c: options.append(ft.dropdown.Option(c))
        self.category_dropdown.options = options
        
    def toggle_view(self, e):
        if self.view_mode == "table":
            self.view_mode = "cards"
            self.btn_toggle_view.icon = ft.icons.TABLE_ROWS
            self.btn_toggle_view.tooltip = "Cambiar a vista de Tabla"
            self.table_wrapper.visible = False
            self.card_list_view.visible = True
        else:
            self.view_mode = "table"
            self.btn_toggle_view.icon = ft.icons.GRID_VIEW
            self.btn_toggle_view.tooltip = "Cambiar a vista de Tarjetas"
            self.table_wrapper.visible = True
            self.card_list_view.visible = False
        self.safe_update()
        
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        self.safe_update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        search_val = self.search_input.value or ""
        cat_val = self.category_dropdown.value or "Todas"
        
        data, total = self.db.get_insumos(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val, 
            categoria=cat_val,
            fecha_corte=self.fecha_corte,
            sort_col=self.sort_col_name,
            sort_asc=self.sort_is_asc
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        # Limpiar filas previas
        self.data_table.rows.clear()
        self.card_list_view.controls.clear()
        
        # Calcular Totales Globales iterando la lista completa sin paginación
        data_completa, _ = self.db.get_insumos(
            page=1, 
            page_size=999999, 
            search=search_val, 
            categoria=cat_val,
            fecha_corte=self.fecha_corte,
            sort_col=self.sort_col_name,
            sort_asc=self.sort_is_asc
        )

        proyeccion_global = 0.0
        self.valor_total_inventario = 0.0
        
        for insumo in data_completa:
            stock = float(insumo.get("stock_actual") or insumo.get("stock_real") or 0)
            p_venta = float(insumo.get("precio_venta") or 0)
            
            if stock > 0:
                proyeccion_global += (stock * p_venta)
                
            self.valor_total_inventario += float(insumo.get("costo_total_insumo") or 0)
            
        self.lbl_proyeccion_ventas.value = f"${proyeccion_global:,.0f}"
        self.safe_update()
        
        # Llenar tabla y tarjetas
        total_entradas = 0
        total_salidas = 0
        
        for item in data:
            row = self._crear_fila_inventario(item)
            self.data_table.rows.append(row)
            self.card_list_view.controls.append(self._crear_tarjeta_inventario(item, row))
            
            
        self.update_pagination_ui()


    def crear_celdas_fila(self, item, row_ref, edit_mode=False):
        stock_inicial = int(item.get('stock_inicial', 0) or 0)
        stock_minimo = int(item.get('stock_minimo', 5) or 5)
        entradas = int(item.get('entradas', 0) or 0)
        salidas = int(item.get('salidas', 0) or 0)
        
        stock_final = int(item.get('stock_real', item.get('stock_actual', 0)) or 0)
        
        costo_unit = float(item.get('costo_unitario') or 0)
        precio_venta = float(item.get('precio_venta') or 0)
        costo_total = float(item.get('costo_total_insumo') or 0)
        venta_total = float(item.get('venta_total_insumo') or 0)
        
        str_costo_unit = f"${costo_unit:,.2f}"
        str_precio_venta = f"${precio_venta:,.2f}"
        str_costo_total = f"${costo_total:,.2f}"
        str_venta_total = f"${venta_total:,.2f}"
        
        color_entradas = "green" if entradas > 0 else "black"
        color_salidas = "red" if salidas > 0 else "black"
        color_stock = "blue" if stock_final > 0 else "red"
        
        codigo = str(item.get('codigo_insumo', ''))
        nombre = str(item.get('nombre', ''))
        categoria = str(item.get('categoria', ''))
        ubicacion = str(item.get('ubicacion') or 'N/A')

        checkbox = ft.Checkbox(value=False, on_change=lambda e, i=item, r=row_ref: self.toggle_edit(e, i, r))
        
        cells_data = [
            ft.DataCell(ft.Container(content=checkbox, width=25, alignment=ft.alignment.center)),
            ft.DataCell(ft.Text(codigo, size=10)),
            ft.DataCell(ft.Container(content=ft.Text(nombre, size=10, no_wrap=True, tooltip=nombre), width=250)),
            ft.DataCell(ft.Text(categoria, size=10)),
            ft.DataCell(ft.Text(ubicacion, size=10)),
            ft.DataCell(ft.Container(content=ft.Text(str(stock_inicial), size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Container(content=ft.Text(str(stock_minimo), size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Container(content=ft.Text(str(entradas), color=color_entradas, weight="bold", size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Container(content=ft.Text(str(salidas), color=color_salidas, weight="bold", size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Container(content=ft.Text(str(stock_final), color=color_stock, weight="bold", size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Text(str_costo_unit, size=10)),
            ft.DataCell(ft.Text(str_costo_total, color="blue", size=10)),
            ft.DataCell(ft.Text(str_precio_venta, size=10)),
            ft.DataCell(ft.Text(str_venta_total, color="green", size=10)),
        ]
            
        return cells_data

    def abrir_edicion_desde_tarjeta(self, item, row_ref):
        # Simular que se marcó el checkbox de la tabla para mantener sincronía
        if len(row_ref.cells) > 0:
            cb = row_ref.cells[0].content.content
            if isinstance(cb, ft.Checkbox):
                cb.value = True
                self.safe_update()
                    
        class DummyEvent:
            class DummyControl:
                value = True
            control = DummyControl()
            
        self.toggle_edit(DummyEvent(), item, row_ref)

    def toggle_edit(self, e, item, row_ref):
        if not e.control.value:
            self.cancelar_edicion()
            return
            
        if self.current_edit_context and self.current_edit_context['row'] != row_ref:
            prev_row = self.current_edit_context['row']
            if prev_row and len(prev_row.cells) > 0:
                cb = prev_row.cells[0].content.content
                if isinstance(cb, ft.Checkbox):
                    cb.value = False
                    
        self.current_edit_context = {
            'item': item,
            'row': row_ref
        }
        
        codigo = item.get('codigo_insumo')
        nombre = item.get('nombre')
        
        self.edit_panel_title.value = f"Editando: [{codigo}] {nombre}"
        self.edit_stock_minimo.value = str(int(item.get('stock_minimo', 5) or 5))
        self.edit_costo.value = str(float(item.get('costo_unitario') or 0))
        self.edit_precio.value = str(float(item.get('precio_venta') or 0))
        
        # Recargar opciones frescas
        categorias_bd = self.db.get_categorias() if hasattr(self.db, 'get_categorias') else []
        opts = [ft.dropdown.Option(c) for c in categorias_bd if c]
        self.edit_categoria.options = opts

        # Limpiar dropdowns
        self.edit_margen.value = None

        # Asignar categoría exacta
        cat_val = str(item.get('categoria') or '').strip()
        if any(o.key == cat_val for o in opts):
            self.edit_categoria.value = cat_val
        elif opts:
            self.edit_categoria.value = opts[0].key
        else:
            self.edit_categoria.value = None
        
        self.btn_guardar_edicion.disabled = True
        self.action_bar.visible = True
        self.safe_update()

    def cancelar_edicion(self, e=None):
        if self.current_edit_context:
            row_ref = self.current_edit_context['row']
            if row_ref and len(row_ref.cells) > 0:
                cb = row_ref.cells[0].content.content
                if isinstance(cb, ft.Checkbox):
                    cb.value = False
        self.current_edit_context = None
        self.action_bar.visible = False
        self.safe_update()

    def abrir_dialogo_confirmacion(self):
        if not self.current_edit_context: return
        item = self.current_edit_context['item']
        
        cambios = []
        try:
            nuevo_stock_min = int(self.edit_stock_minimo.value)
            if nuevo_stock_min != int(item.get('stock_minimo', 5) or 5):
                cambios.append(f"Stock Mínimo: {int(item.get('stock_minimo', 5) or 5)} -> {nuevo_stock_min}")
                
            nuevo_costo = float(self.edit_costo.value)
            if nuevo_costo != float(item.get('costo_unitario') or 0):
                cambios.append(f"Costo Unitario: ${float(item.get('costo_unitario') or 0):.2f} -> ${nuevo_costo:.2f}")
                
            nuevo_precio = float(self.edit_precio.value)
            if nuevo_precio != float(item.get('precio_venta') or 0):
                cambios.append(f"Precio Venta: ${float(item.get('precio_venta') or 0):.2f} -> ${nuevo_precio:.2f}")
                
            nueva_cat = self.edit_categoria.value
            if nueva_cat != str(item.get('categoria', '')):
                cambios.append(f"Categoría: {item.get('categoria', '')} -> {nueva_cat}")
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error: Asegúrate de ingresar números válidos."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return

        if not cambios:
            self.cancelar_edicion()
            return

        resumen = "\n".join(cambios)
        
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Actualización"),
            content=ft.Text(f"Estás a punto de modificar el insumo: {item.get('codigo_insumo')} - {item.get('nombre')}.\n\nCambios detectados:\n{resumen}"),
        )
        
        def on_cancel(e):
            dlg.open = False
            self.safe_update()
            
        def on_save(e):
            self.ejecutar_guardado(dlg)
            
        dlg.actions = [
            ft.TextButton("Cancelar", on_click=on_cancel),
            ft.ElevatedButton("Guardar", bgcolor="green", color="white", on_click=on_save)
        ]
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()

    def ejecutar_guardado(self, dialog=None):
        if dialog:
            dialog.open = False
            
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        self.safe_update()
            
        threading.Thread(target=self._ejecutar_guardado_worker, daemon=True).start()

    def _ejecutar_guardado_worker(self):
        try:
            if not self.current_edit_context: return
            item = self.current_edit_context['item']
            
            try:
                datos_actualizados = {
                    "stock_minimo": int(self.edit_stock_minimo.value),
                    "costo_unitario": float(self.edit_costo.value),
                    "precio_venta": float(self.edit_precio.value),
                    "categoria": self.edit_categoria.value
                }
            except ValueError:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico al guardar."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()
                return
                
            codigo = item.get('codigo_insumo')
            exito = self.db.update_insumo(codigo, datos_actualizados)
            
            if exito:
                self.cancelar_edicion()
                
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Insumo {codigo} actualizado exitosamente."), bgcolor="green")
                self.page.snack_bar.open = True
                self.safe_update()
                
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al actualizar en Base de Datos."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()
                
            self.update_pagination_ui()

        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            self.safe_update()
        
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
        
    def open_date_picker(self, e):
        self.date_picker.pick_date()
        
    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_date.text = f"Fecha: {self.fecha_corte}"
            self.btn_clear_date.visible = True
            self.current_page = 1
            self.load_data()
            self.safe_update()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e):
        self.fecha_corte = None
        self.date_picker.value = None
        self.btn_date.text = "Filtrar por Fecha"
        self.btn_clear_date.visible = False
        self.current_page = 1
        self.load_data()
        self.safe_update()

    def on_sort_table(self, e: ft.DataColumnSortEvent):
        """Delega el ordenamiento a la base de datos solicitando una nueva carga de datos."""
        self.data_table.sort_column_index = e.column_index
        self.data_table.sort_ascending = e.ascending
        
        # Identificar qué columna se hizo clic basándose en el diccionario
        column_keys = list(self.columnas_def.keys())
        
        # Descontar las columnas que estén ocultas para encontrar el índice real
        visible_keys = [k for k in column_keys if self.columnas_visibles.get(k, True)]
        
        if e.column_index < len(visible_keys):
            self.sort_col_name = visible_keys[e.column_index]
        
        self.sort_is_asc = e.ascending
        self.current_page = 1 # Volver a la primera página tras ordenar
        self.load_data()

    def on_guardar_global(self, e):
        self.abrir_dialogo_confirmacion()

    def on_cancelar_global(self, e):
        self.cancelar_edicion()

    def on_gestionar_ajustes(self, e):
        # Placeholder para enviar el código del insumo seleccionado al futuro módulo de ajustes
        if self.current_edit_context:
            codigo = self.current_edit_context['item'].get('codigo_insumo')
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Redirigiendo a gestión de ajustes para el insumo {codigo}..."), bgcolor="blue")
            self.page.snack_bar.open = True
            self.safe_update()

    def _crear_fila_inventario(self, item):
        row = ft.DataRow(cells=[])
        row.cells = self.crear_celdas_fila(item, row, edit_mode=False)
        return row

    def _crear_tarjeta_inventario(self, item, row):
        codigo = str(item.get('codigo_insumo') or '')
        nombre = str(item.get('nombre') or '')
        categoria = str(item.get('categoria') or '')
        ubicacion = str(item.get('ubicacion') or 'N/A')
        
        # Extracción Segura
        stock_inicial = float(item.get("stock_inicial") or 0)
        valor_inicial = float(item.get("valor_inicial") or 0)
        compras = float(item.get("compras") or 0)
        valor_compras = float(item.get("valor_compras") or 0)
        ventas = float(item.get("ventas") or 0)
        valor_ventas = float(item.get("valor_ventas") or 0)
        ajustes_entrantes = float(item.get("ajustes_entrantes") or 0)
        valor_ajustes_entrantes = float(item.get("valor_ajustes_entrantes") or 0)
        ajustes_salientes = float(item.get("ajustes_salientes") or 0)
        valor_ajustes_salientes = float(item.get("valor_ajustes_salientes") or 0)
        neto_ajustes = float(item.get("neto_ajustes") or 0)
        valor_neto_ajustes = float(item.get("valor_neto_ajustes") or 0)
        
        stock_actual = float(item.get('stock_actual') or item.get('stock_real') or 0)
        costo_total_insumo = float(item.get('costo_total_insumo') or 0)
        costo_u = float(item.get('costo_unitario') or 0)
        p_venta = float(item.get('precio_venta') or 0)
        
        proyeccion_venta = stock_actual * p_venta if stock_actual > 0 else 0
        participacion = (costo_total_insumo / self.valor_total_inventario) * 100 if getattr(self, 'valor_total_inventario', 0) > 0 else 0
        
        # Badges
        badge_costo = ft.Container(content=ft.Text(f"Costo U: ${costo_u:,.0f}", size=11, weight="bold", color="black87"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="grey100", border_radius=15)
        badge_pventa = ft.Container(content=ft.Text(f"Precio de Venta: ${p_venta:,.0f}", size=11, weight="bold", color="black87"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="grey100", border_radius=15)
        badge_peso = ft.Container(content=ft.Text(f"Peso Inv: {participacion:.1f}%", size=11, weight="bold", color="purple900"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="#f3e5f5", border_radius=15)
        badge_proy = ft.Container(content=ft.Text(f"Proyección de Venta: ${proyeccion_venta:,.0f}", size=11, weight="bold", color="blue900"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="#e3f2fd", border_radius=15)
        badge_stock = ft.Container(content=ft.Text(f"Stock Actual: {stock_actual:g} unds ($ {costo_total_insumo:,.0f})", size=11, weight="bold", color="green900"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="#e8f5e9", border_radius=15)
        
        contenedor_badges = ft.Row(
            [badge_costo, badge_pventa, badge_peso, badge_proy, badge_stock], 
            spacing=5, 
            alignment=ft.MainAxisAlignment.END,
            wrap=True
        )
        
        def crear_bloque_metricas(titulo, cantidad, valor, color_cant, color_valor):
            return ft.Column([
                ft.Text(titulo, size=10, color="grey", weight="bold"),
                ft.Text(f"{cantidad:g} unds", size=12, weight="bold", color=color_cant),
                ft.Text(f"${valor:,.0f}", size=12, color=color_valor)
            ], spacing=2, alignment=ft.MainAxisAlignment.START)
            
        color_neto = "red" if valor_neto_ajustes < 0 else ("green" if valor_neto_ajustes > 0 else "grey")
            
        fila_resultados = ft.Row([
            crear_bloque_metricas("INICIAL", stock_inicial, valor_inicial, "grey", "grey"),
            crear_bloque_metricas("COMPRAS", compras, valor_compras, "#2ecca0", "black87"),
            crear_bloque_metricas("VENTAS", ventas, valor_ventas, "#42a5f5", "black87"),
            crear_bloque_metricas("AJUSTES ENTRANTES", ajustes_entrantes, valor_ajustes_entrantes, "green", "green"),
            crear_bloque_metricas("AJUSTES SALIENTES", ajustes_salientes, valor_ajustes_salientes, "red", "red"),
            crear_bloque_metricas("NETO DEL AJUSTE", neto_ajustes, valor_neto_ajustes, color_neto, color_neto)
        ], spacing=20, wrap=True)
        
        tarjeta = ft.Container(
            bgcolor="white",
            padding=15,
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            content=ft.Column([
                ft.Row([
                    ft.Text(f"{categoria} | {ubicacion}", size=12, color="grey"),
                    contenedor_badges
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(f"[{codigo}] {nombre}", size=15, weight="bold", expand=True),
                    ft.OutlinedButton(text="Editar Insumo", icon=ft.icons.EDIT, on_click=lambda e, i=item, r=row: self.abrir_edicion_desde_tarjeta(i, r))
                ]),
                fila_resultados
            ], spacing=8)
        )
        return tarjeta

