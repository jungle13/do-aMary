import flet as ft
from config import Config

class Sidebar(ft.Container):
    def __init__(self, on_route_change, usuario_data=None, on_logout=None):
        super().__init__()
        self.on_route_change = on_route_change
        self.usuario_data = usuario_data or {}
        self.on_logout = on_logout
        self.is_expanded = True
        
        self.width = 250
        self.bgcolor = Config.COLOR_PRIMARY
        self.padding = 15
        self.border_radius = ft.border_radius.only(top_right=15, bottom_right=15)
        self.animate = ft.animation.Animation(300, ft.AnimationCurve.DECELERATE)

        # Botón Toggle
        self.toggle_btn = ft.IconButton(
            icon=ft.icons.MENU,
            icon_color="white",
            on_click=self.toggle_sidebar,
            tooltip="Ocultar/Mostrar Menú"
        )
        self.toggle_row = ft.Row([self.toggle_btn], alignment=ft.MainAxisAlignment.END)

        # Extraer Primer Nombre
        nombre_completo = self.usuario_data.get("nombre_completo") or self.usuario_data.get("usuario") or "Usuario"
        partes = nombre_completo.split()
        primer_nombre = partes[0] if partes else "Usuario"
        if primer_nombre.lower() in ["doña", "dona"] and len(partes) > 1:
            primer_nombre = f"{partes[0]} {partes[1]}"
            
        rol_txt = str(self.usuario_data.get("rol", "OPERADOR")).capitalize()

        # Componentes Estéticos del Perfil de Usuario (Compacto)
        self.user_avatar = ft.Icon(ft.icons.ACCOUNT_CIRCLE_ROUNDED, color="white", size=32)
        self.lbl_saludo = ft.Text(f"Hola, {primer_nombre}", color="white", size=12, weight="bold", no_wrap=True)
        self.lbl_rol = ft.Text(rol_txt, color="white54", size=10, no_wrap=True)

        self.user_info_col = ft.Column([
            self.lbl_saludo,
            self.lbl_rol
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)

        # Botón Cerrar Sesión
        self.btn_logout = ft.IconButton(
            icon=ft.icons.LOGOUT_ROUNDED,
            icon_color="white54",
            icon_size=18,
            tooltip="Cerrar Sesión",
            on_click=lambda e: self.on_logout() if self.on_logout else None
        )

        self.user_badge = ft.Container(
            content=ft.Row([
                self.user_avatar,
                self.user_info_col,
                ft.Container(expand=True),
                self.btn_logout
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            bgcolor=ft.colors.with_opacity(0.12, "white"),
            border_radius=8,
            margin=ft.padding.only(bottom=10)
        )

        self.menu_items = {}
        self.footer_text = ft.Text(
            "Elaborado por Eliana Garces 2026\npara Abarrotes y Desechables de Doña Mary SAS",
            color="white54", size=10, text_align=ft.TextAlign.CENTER
        )

        # Permisos
        username = str(self.usuario_data.get("usuario", "")).lower()
        rol = str(self.usuario_data.get("rol", "OPERADOR")).upper()
        es_admin = username in ["eliana", "cesar", "mary"] or rol == "ADMINISTRADOR"

        menu_controls = [
            self.toggle_row,
            self.user_badge
        ]

        if es_admin:
            menu_controls.append(self._create_menu_item("Dashboard", ft.icons.DASHBOARD, "dashboard"))

        menu_controls.append(self._create_menu_item("Inventario", ft.icons.INVENTORY_2, "inventario"))
        menu_controls.append(self._create_menu_item("Compras", ft.icons.ADD_SHOPPING_CART, "compras"))
        menu_controls.append(self._create_menu_item("Ventas", ft.icons.POINT_OF_SALE, "ventas"))
        menu_controls.append(self._create_menu_item("Ajustes de Inventario", ft.icons.TUNE, "ajustes_inventario"))

        if es_admin or rol == "AUDITOR":
            menu_controls.append(self._create_menu_item("Cierre de Mes", ft.icons.FACT_CHECK, "cierre_mes"))
            menu_controls.append(self._create_menu_item("Informes", ft.icons.PIE_CHART, "informes"))

        menu_controls.extend([
            ft.Container(expand=True),
            ft.Container(
                content=self.footer_text,
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=5, bottom=5),
                on_click=self.mostrar_disclaimer,
                tooltip="Ver Información Legal y Créditos"
            )
        ])

        self.content = ft.Column(controls=menu_controls, spacing=5)

    def _create_menu_item(self, text, icon, route):
        item = ft.ListTile(
            leading=ft.Icon(icon, color="white70", size=22),
            title=ft.Text(text, color="white70", size=13),
            hover_color=ft.colors.with_opacity(0.1, "white"),
            content_padding=ft.padding.only(left=12, right=12),
            on_click=lambda _, r=route: self.on_route_change(r),
            tooltip=text
        )
        self.menu_items[route] = item
        return item

    def actualizar_estado_activo(self, ruta_actual):
        for route, item in self.menu_items.items():
            is_active = (route == ruta_actual)
            item.bgcolor = ft.colors.with_opacity(0.2, "white") if is_active else None
            item.leading.color = "white" if is_active else "white70"
            item.title.color = "white" if is_active else "white70"
            item.title.weight = "bold" if is_active else "normal"
        try:
            self.update()
        except Exception:
            pass

    def toggle_sidebar(self, e):
        self.is_expanded = not self.is_expanded
        self.width = 250 if self.is_expanded else 70

        # Ocultar o mostrar elementos informativos al colapsar
        self.user_info_col.visible = self.is_expanded
        self.btn_logout.visible = self.is_expanded
        self.footer_text.visible = self.is_expanded

        self.user_avatar.size = 32 if self.is_expanded else 24
        self.user_badge.padding = ft.padding.symmetric(horizontal=8, vertical=6) if self.is_expanded else ft.padding.all(4)

        for control in self.content.controls:
            if isinstance(control, ft.ListTile):
                control.title.visible = self.is_expanded
                control.content_padding = ft.padding.only(left=12 if self.is_expanded else 8, right=12 if self.is_expanded else 8)

        self.update()

    def mostrar_disclaimer(self, e):
        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.GAVEL_ROUNDED, color=Config.COLOR_PRIMARY),
                ft.Text("Información Legal y Créditos", size=16, weight="bold", color=Config.COLOR_PRIMARY)
            ]),
            content=ft.Column([
                ft.Text("Versión del Software: 1.0", size=13, weight="bold"),
                ft.Divider(height=10, color="transparent"),
                ft.Text("Autoría Intelectual:", size=13, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Este software fue diseñado, estructurado y desarrollado en su totalidad por Eliana Garces. Todos los derechos sobre el código fuente y la arquitectura de la aplicación están reservados a su autor.", size=12, color="grey700", text_align=ft.TextAlign.JUSTIFY),
                ft.Divider(height=10, color="transparent"),
                ft.Text("Descargo de Responsabilidad:", size=13, weight="bold", color="red700"),
                ft.Text("La veracidad de la información, el manejo de inventarios, la gestión financiera y el uso general de los datos introducidos en esta plataforma, así como las decisiones operativas tomadas en base a los mismos, son responsabilidad única y exclusiva de Abarrotes y Desechables de Doña Mary SAS.", size=12, color="grey700", text_align=ft.TextAlign.JUSTIFY)
            ], tight=True, spacing=5, width=400),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self._cerrar_dialogo(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        if self.page:
            if hasattr(self.page, "open"):
                self.page.open(dlg)
            else:
                self.page.overlay.append(dlg)
                dlg.open = True
                self.page.update()

    def _cerrar_dialogo(self, dlg):
        if self.page:
            if hasattr(self.page, "close"):
                self.page.close(dlg)
            else:
                dlg.open = False
                self.page.update()
