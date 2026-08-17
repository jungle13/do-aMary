import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
import datetime
from dateutil.relativedelta import relativedelta

class ConteoInicialView(ft.Container):
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
        
        # State
        self.data_completa = []
        self.cambios_pendientes = {} # {codigo: nuevo_valor}
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        # Generar meses para el Dropdown
        hoy = datetime.date.today()
        opciones_meses = []
        for i in range(12): # Últimos 12 meses
            m = hoy - relativedelta(months=i)
            # Formato YYYY-MM
            val = m.strftime("%Y-%m")
            # Label bonito
            nombre_mes = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][m.month - 1]
            opciones_meses.append(ft.dropdown.Option(key=val, text=f"{nombre_mes} {m.year}"))
            
        self.mes_seleccionado = hoy.strftime("%Y-%m")
        
        # UI Filters
        self.search_input = ft.TextField(
            hint_text="Buscar código o insumo...",
            prefix_icon=ft.icons.SEARCH,
            border_radius=8,
            expand=True,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_filter_change
        )
        
        self.category_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            label="Categoría",
            width=200,
            border_radius=8,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_filter_change
        )
        
        self.month_dropdown = ft.Dropdown(
            options=opciones_meses,
            value=self.mes_seleccionado,
            label="Mes de Conteo",
            width=200,
            border_radius=8,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_month_change
        )
        
        # Tabla
        self.data_table = ft.DataTable(
            column_spacing=15,
            data_row_min_height=45,
            data_row_max_height=45,
            heading_row_height=40,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Categoría", weight="bold")),
                ft.DataColumn(ft.Text("Cierre Mes Ant.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Stock Inicial Reg.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Nuevo Conteo", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[]
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        
        # Bulk Action Bar
        self.btn_guardar_masivo = ft.ElevatedButton("Guardar Todos los Registros", bgcolor="green", color="white", on_click=self.guardar_masivo)
        self.action_bar = ft.Container(
            content=ft.Row([
                ft.Text("Tienes cambios pendientes por guardar", color="white", weight="bold"),
                ft.Container(expand=True),
                ft.OutlinedButton("Cancelar Todas las Ediciones", style=ft.ButtonStyle(color="white"), on_click=self.cancelar_masivo),
                self.btn_guardar_masivo
            ]),
            bgcolor=Config.COLOR_PRIMARY,
            padding=15,
            border_radius=10,
            visible=False,
            margin=ft.padding.only(top=10)
        )
        
        self.content = ft.Column([
            self.lbl_titulo,
            
            # Filtros
            ft.Container(
                content=ft.Row([
                    self.search_input,
                    self.category_dropdown,
                    self.month_dropdown,
                    ft.IconButton(icon=ft.icons.REFRESH, on_click=self.on_month_change, tooltip="Recargar")
                ]),
                bgcolor="white",
                padding=10,
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            # Tabla
            ft.Container(
                content=ft.Column(
                    [self.data_table],
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True
                ),
                bgcolor="white",
                padding=5,
                border_radius=10,
                expand=True,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
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
            
        ], expand=True, spacing=15)

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
        self.load_categories()
        self.load_data()
        
    def load_categories(self):
        cats = self.db.get_categorias()
        opts = [ft.dropdown.Option("Todas")]
        for c in cats:
            if c: opts.append(ft.dropdown.Option(c))
        self.category_dropdown.options = opts
        if self.page:
            self.update()
            
    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.cambios_pendientes.clear()
        self.current_page = 1
        self.load_data()
        
    def on_filter_change(self, e):
        self.current_page = 1
        self.render_table()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_table()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_table()
        
    def load_data(self):
        self.data_completa = self.db.get_datos_conteo_inicial(self.mes_seleccionado)
        self.render_table()
        
    def render_table(self):
        import math
        search_val = (self.search_input.value or "").lower()
        cat_val = self.category_dropdown.value or "Todas"
        
        self.data_table.rows.clear()
        
        filtered_data = []
        for item in self.data_completa:
            # Filtros
            nombre = str(item.get("nombre", "")).lower()
            codigo = str(item.get("codigo_insumo", "")).lower()
            categoria = str(item.get("categoria", ""))
            
            if search_val and search_val not in nombre and search_val not in codigo:
                continue
            if cat_val != "Todas" and cat_val != categoria:
                continue
                
            filtered_data.append(item)
            
        self.total_records = len(filtered_data)
        self.total_pages = math.ceil(self.total_records / self.page_size) if self.total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        
        page_data = filtered_data[start_idx:end_idx]
        
        for item in page_data:
            self.data_table.rows.append(self.crear_fila(item))
            
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros filtrados"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
            
        self.actualizar_action_bar()
        if self.page:
            self.update()
            
    def crear_fila(self, item):
        codigo = item["codigo_insumo"]
        cierre_ant = item["cierre_mes_anterior"]
        stock_ini = item["stock_inicial_actual"]
        
        input_conteo = ft.TextField(
            value=str(stock_ini),
            dense=True,
            width=80,
            text_size=13,
            content_padding=10,
            border_color=ft.colors.with_opacity(0.2, "black"),
            bgcolor="white"
        )
        
        acciones_container = ft.Row(visible=False, spacing=0)
        
        def on_change(e):
            val = input_conteo.value
            try:
                numeric_val = float(val) if '.' in val else int(val)
                if numeric_val != stock_ini:
                    self.cambios_pendientes[codigo] = numeric_val
                    acciones_container.visible = True
                else:
                    if codigo in self.cambios_pendientes:
                        del self.cambios_pendientes[codigo]
                    acciones_container.visible = False
            except ValueError:
                if codigo in self.cambios_pendientes:
                    del self.cambios_pendientes[codigo]
                acciones_container.visible = False
                
            e.control.update()
            acciones_container.update()
            self.actualizar_action_bar()
            
        input_conteo.on_change = on_change
        
        # Si ya había un cambio pendiente de antes (al buscar/filtrar)
        if codigo in self.cambios_pendientes:
            input_conteo.value = str(self.cambios_pendientes[codigo])
            acciones_container.visible = True
            
        def guardar_individual(e):
            if codigo in self.cambios_pendientes:
                val = self.cambios_pendientes[codigo]
                registro = {
                    "fecha_cierre": f"{self.mes_seleccionado}-01",
                    "codigo_insumo": codigo,
                    "tipo_registro": "INVENTARIO_INICIAL",
                    "cantidad_fisica": val,
                    "estado": "APLICADO"
                }
                exito = self.db.upsert_conteos_iniciales([registro])
                if exito:
                    item["stock_inicial_actual"] = val
                    del self.cambios_pendientes[codigo]
                    acciones_container.visible = False
                    self.page.snack_bar = ft.SnackBar(ft.Text("Guardado exitoso"), bgcolor="green")
                    self.page.snack_bar.open = True
                    self.render_table()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar"), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.page.update()
                    
        def cancelar_individual(e):
            if codigo in self.cambios_pendientes:
                del self.cambios_pendientes[codigo]
            input_conteo.value = str(item["stock_inicial_actual"])
            acciones_container.visible = False
            input_conteo.update()
            acciones_container.update()
            self.actualizar_action_bar()
            
        acciones_container.controls = [
            ft.IconButton(ft.icons.CHECK, icon_color="green", tooltip="Guardar", on_click=guardar_individual),
            ft.IconButton(ft.icons.CLOSE, icon_color="red", tooltip="Descartar", on_click=cancelar_individual)
        ]
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(codigo)),
                ft.DataCell(ft.Container(content=ft.Text(item["nombre"], no_wrap=True, tooltip=item["nombre"]), width=150)),
                ft.DataCell(ft.Text(item["categoria"])),
                ft.DataCell(ft.Text(str(cierre_ant))),
                ft.DataCell(ft.Text(str(stock_ini), weight="bold")),
                ft.DataCell(input_conteo),
                ft.DataCell(acciones_container),
            ]
        )
        
    def actualizar_action_bar(self):
        if len(self.cambios_pendientes) > 1:
            self.action_bar.visible = True
        else:
            self.action_bar.visible = False
        if self.page:
            self.action_bar.update()
            
    def cancelar_masivo(self, e):
        self.cambios_pendientes.clear()
        self.render_table()
        
    def guardar_masivo(self, e):
        if not self.cambios_pendientes:
            return
            
        registros = []
        for codigo, val in self.cambios_pendientes.items():
            registros.append({
                "fecha_cierre": f"{self.mes_seleccionado}-01",
                "codigo_insumo": codigo,
                "tipo_registro": "INVENTARIO_INICIAL",
                "cantidad_fisica": val,
                "estado": "APLICADO"
            })
            
        exito = self.db.upsert_conteos_iniciales(registros)
        if exito:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Se guardaron {len(registros)} registros exitosamente"), bgcolor="green")
            self.cambios_pendientes.clear()
            self.load_data() # Recargar todo de BD para asegurar sincronía
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar registros masivos"), bgcolor="red")
            
        self.page.snack_bar.open = True
        self.page.update()
