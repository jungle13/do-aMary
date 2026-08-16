import flet as ft
from config import Config

class Sidebar(ft.Container):
    def __init__(self, on_route_change):
        super().__init__()
        self.on_route_change = on_route_change
        self.is_expanded = True
        
        # Propiedades dinámicas del contenedor
        self.width = 250
        self.bgcolor = Config.COLOR_PRIMARY
        self.padding = 15
        self.border_radius = ft.border_radius.only(top_right=15, bottom_right=15)
        self.animate = ft.animation.Animation(300, ft.AnimationCurve.DECELERATE)
        
        # Botón para colapsar/expandir
        self.toggle_btn = ft.IconButton(
            icon=ft.icons.MENU,
            icon_color="white",
            on_click=self.toggle_sidebar,
            tooltip="Ocultar/Mostrar Menú"
        )
        
        # Logo y textos
        self.logo_icon = ft.Icon(ft.icons.STOREFRONT, color="white", size=40)
        self.logo_title = ft.Text("Doña Mary", color="white", size=24, weight="bold")
        self.logo_subtitle = ft.Text("Abarrotes & Desechables", color="white70", size=12)
        
        self.header_content = ft.Column([
            self.logo_icon,
            self.logo_title,
            self.logo_subtitle,
        ], horizontal_alignment="center", spacing=5)

        self.toggle_row = ft.Row([self.toggle_btn], alignment=ft.MainAxisAlignment.END)

        # Almacenar referencias de los botones del menú
        self.menu_items = {}
        
        self.footer_text = ft.Text("Elaborado por: Eliana Garces 2026", color="white54", size=10, text_align=ft.TextAlign.CENTER)
        
        self.content = ft.Column(
            controls=[
                # Cabecera con botón de toggle
                self.toggle_row,
                ft.Container(
                    content=self.header_content,
                    padding=ft.padding.only(bottom=20),
                    alignment=ft.alignment.center
                ),
                
                # Menú
                self._create_menu_item("Dashboard", ft.icons.DASHBOARD, "dashboard"),
                self._create_menu_item("Inventario", ft.icons.INVENTORY_2, "inventario"),
                self._create_menu_item("Compras", ft.icons.ADD_SHOPPING_CART, "compras"),
                self._create_menu_item("Ventas", ft.icons.POINT_OF_SALE, "ventas"),
                self._create_menu_item("Ajustes de Inventario", ft.icons.TUNE, "ajustes_inventario"),
                self._create_menu_item("Cierre de Mes", ft.icons.FACT_CHECK, "cierre_mes"),
                
                ft.Container(expand=True), # Spacer
                
                self._create_menu_item("Configuración", ft.icons.SETTINGS, "settings"),
                
                # Footer Copyright
                ft.Container(
                    content=self.footer_text,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=10, bottom=5)
                )
            ],
            spacing=5
        )
        
    def _create_menu_item(self, text, icon, route, is_sub_item=False):
        icon_size = 20 if is_sub_item else 24
        text_size = 13 if is_sub_item else 14
        pad_left = 35 if is_sub_item else 15
        
        item = ft.ListTile(
            leading=ft.Icon(icon, color="white70", size=icon_size),
            title=ft.Text(text, color="white70", size=text_size),
            hover_color=ft.colors.with_opacity(0.1, "white"),
            content_padding=ft.padding.only(left=pad_left, right=15),
            on_click=lambda _: self.on_route_change(route),
            data={"is_sub_item": is_sub_item, "pad_left": pad_left}
        )
        self.menu_items[route] = item
        return item
        
    def update_active_route(self, route_name):
        for route, item in self.menu_items.items():
            is_active = (route == route_name)
            item.bgcolor = ft.colors.with_opacity(0.2, "white") if is_active else None
            item.leading.color = "white" if is_active else "white70"
            item.title.color = "white" if is_active else "white70"
            item.title.weight = "bold" if is_active else "normal"
        self.update()

    def toggle_sidebar(self, e):
        """Alterna el ancho del sidebar y oculta/muestra los textos."""
        self.is_expanded = not self.is_expanded
        
        # Ajustar ancho
        self.width = 250 if self.is_expanded else 70
        
        # Mostrar u ocultar elementos del header según el estado
        self.logo_title.visible = self.is_expanded
        self.logo_subtitle.visible = self.is_expanded
        self.logo_icon.size = 40 if self.is_expanded else 24
        
        # Mostrar u ocultar el footer
        self.footer_text.visible = self.is_expanded
        
        self.toggle_row.alignment = ft.MainAxisAlignment.END if self.is_expanded else ft.MainAxisAlignment.CENTER
        
        # Mostrar u ocultar el texto de los ListTile
        for control in self.content.controls:
            if isinstance(control, ft.ListTile):
                control.title.visible = self.is_expanded
                pad_left = control.data["pad_left"] if self.is_expanded else 8
                control.content_padding = ft.padding.only(left=pad_left, right=15 if self.is_expanded else 8)
                
        self.update()
