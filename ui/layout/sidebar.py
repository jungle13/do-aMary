"""
Barra lateral de navegación (Sidebar) para Sistema Doña Mary.
Diseño moderno, responsivo por roles, con micro-interacciones y botón de despliegue siempre visible.
"""
import flet as ft
from config import Config

class Sidebar(ft.Container):
    def __init__(self, on_route_change, usuario_data=None, on_logout=None, on_reset=None):
        super().__init__()
        self.on_route_change = on_route_change
        self.usuario_data = usuario_data or {}
        self.on_logout = on_logout
        self.on_reset = on_reset
        self.is_expanded = True
        
        self.width = 250
        self.bgcolor = Config.COLOR_PRIMARY
        self.padding = ft.padding.all(12)
        self.border_radius = ft.border_radius.only(top_right=16, bottom_right=16)
        self.animate = ft.animation.Animation(280, ft.AnimationCurve.EASE_OUT)

        # Encabezado de Marca
        self.logo_icon = ft.Icon(ft.icons.STOREFRONT_ROUNDED, color=Config.COLOR_ACCENT, size=22)
        self.lbl_brand = ft.Text("Doña Mary", size=16, weight="bold", color="white", no_wrap=True)
        self.lbl_brand_sub = ft.Text("Inventario & POS", size=10, color="white54", no_wrap=True)
        
        self.brand_text_col = ft.Column([self.lbl_brand, self.lbl_brand_sub], spacing=0)
        
        self.toggle_btn = ft.IconButton(
            icon=ft.icons.MENU_OPEN_ROUNDED,
            icon_color="white",
            icon_size=20,
            on_click=self.toggle_sidebar,
            tooltip="Colapsar menú"
        )

        self.logo_box = ft.Container(
            content=self.logo_icon,
            bgcolor=ft.colors.with_opacity(0.15, Config.COLOR_ACCENT),
            padding=6,
            border_radius=8,
            on_click=self.toggle_sidebar,
            tooltip="Alternar menú"
        )

        self.brand_header = ft.Container(
            content=ft.Row([
                self.logo_box,
                self.brand_text_col,
                ft.Container(expand=True),
                self.toggle_btn
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(left=2, right=2, top=4, bottom=8)
        )

        # Extraer Datos de Usuario
        nombre_completo = self.usuario_data.get("nombre_completo") or self.usuario_data.get("usuario") or "Usuario"
        partes = nombre_completo.split()
        primer_nombre = partes[0] if partes else "Usuario"
        if primer_nombre.lower() in ["doña", "dona"] and len(partes) > 1:
            primer_nombre = f"{partes[0]} {partes[1]}"
            
        rol_txt = str(self.usuario_data.get("rol", "OPERADOR")).capitalize()

        # Avatar y Badge de Usuario
        iniciales = primer_nombre[:2].upper()
        self.user_avatar = ft.Container(
            content=ft.Text(iniciales, size=12, weight="bold", color="white"),
            width=32,
            height=32,
            bgcolor=Config.COLOR_ACCENT,
            border_radius=16,
            alignment=ft.alignment.center
        )

        self.lbl_saludo = ft.Text(f"{primer_nombre}", color="white", size=12, weight="w600", no_wrap=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self.lbl_rol = ft.Text(rol_txt, color="white54", size=10, no_wrap=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

        self.user_info_col = ft.Column([
            self.lbl_saludo,
            self.lbl_rol
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER, expand=True)

        self.btn_reset = ft.IconButton(
            icon=ft.icons.REFRESH_ROUNDED,
            icon_color="white70",
            icon_size=16,
            width=28,
            height=28,
            style=ft.ButtonStyle(padding=0),
            tooltip="Restaurar estado y limpiar caché",
            on_click=lambda e: self.on_reset() if self.on_reset else None
        )

        self.btn_logout = ft.IconButton(
            icon=ft.icons.LOGOUT_ROUNDED,
            icon_color="white54",
            icon_size=16,
            width=28,
            height=28,
            style=ft.ButtonStyle(padding=0),
            tooltip="Cerrar Sesión",
            on_click=lambda e: self.on_logout() if self.on_logout else None
        )

        self.user_badge = ft.Container(
            content=ft.Row([
                self.user_avatar,
                self.user_info_col,
                ft.Row([self.btn_reset, self.btn_logout], spacing=2, tight=True)
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            bgcolor=ft.colors.with_opacity(0.08, "white"),
            border=ft.border.all(1, ft.colors.with_opacity(0.12, "white")),
            border_radius=10,
            margin=ft.padding.only(bottom=10)
        )

        self.menu_items = {}
        self.footer_text = ft.Text(
            "v1.0 • Eliana Garces 2026",
            color="white38", size=10, text_align=ft.TextAlign.CENTER
        )

        # Control de Permisos
        username = str(self.usuario_data.get("usuario", "")).lower()
        rol = str(self.usuario_data.get("rol", "OPERADOR")).upper()
        es_admin = username in ["eliana", "cesar", "mary"] or rol == "ADMINISTRADOR"

        menu_controls = [
            self.brand_header,
            self.user_badge
        ]

        if es_admin:
            menu_controls.append(self._create_menu_item("Dashboard", ft.icons.DASHBOARD_ROUNDED, "dashboard"))

        menu_controls.append(self._create_menu_item("Inventario", ft.icons.INVENTORY_2_ROUNDED, "inventario"))
        menu_controls.append(self._create_menu_item("Compras", ft.icons.ADD_SHOPPING_CART_ROUNDED, "compras"))
        menu_controls.append(self._create_menu_item("Ventas", ft.icons.POINT_OF_SALE_ROUNDED, "ventas"))
        menu_controls.append(self._create_menu_item("Cartera", ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, "cartera"))
        menu_controls.append(self._create_menu_item("Ajustes de Stock", ft.icons.TUNE_ROUNDED, "ajustes_inventario"))

        if es_admin or rol == "AUDITOR":
            menu_controls.append(self._create_menu_item("Cierre de Mes", ft.icons.FACT_CHECK_ROUNDED, "cierre_mes"))
            menu_controls.append(self._create_menu_item("Informes", ft.icons.INSERT_CHART_ROUNDED, "informes"))

        menu_controls.extend([
            ft.Container(expand=True),
            ft.Container(
                content=self.footer_text,
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=5, bottom=5),
                on_click=self.mostrar_disclaimer,
                tooltip="Ver Créditos e Información Legal"
            )
        ])

        self.content = ft.Column(controls=menu_controls, spacing=4)

    def _create_menu_item(self, text, icon, route):
        item = ft.ListTile(
            leading=ft.Icon(icon, color="white70", size=20),
            title=ft.Text(text, color="white70", size=13, weight="w500"),
            hover_color=ft.colors.with_opacity(0.08, "white"),
            content_padding=ft.padding.only(left=10, right=10),
            on_click=lambda _, r=route: self.on_route_change(r),
            tooltip=text
        )
        self.menu_items[route] = item
        return item

    def actualizar_estado_activo(self, ruta_actual):
        for route, item in self.menu_items.items():
            is_active = (route == ruta_actual)
            item.bgcolor = ft.colors.with_opacity(0.18, Config.COLOR_ACCENT) if is_active else None
            item.leading.color = Config.COLOR_ACCENT if is_active else "white70"
            item.title.color = "white" if is_active else "white70"
            item.title.weight = "bold" if is_active else "w500"
        try:
            self.update()
        except Exception:
            pass

    def toggle_sidebar(self, e):
        self.is_expanded = not self.is_expanded
        self.width = 250 if self.is_expanded else 70
        self.toggle_btn.icon = ft.icons.MENU_OPEN_ROUNDED if self.is_expanded else ft.icons.MENU_ROUNDED
        self.toggle_btn.tooltip = "Colapsar menú" if self.is_expanded else "Desplegar menú"

        self.brand_text_col.visible = self.is_expanded
        self.user_info_col.visible = self.is_expanded
        self.btn_reset.visible = self.is_expanded
        self.btn_logout.visible = self.is_expanded
        self.footer_text.visible = self.is_expanded

        # Alternar estructura del encabezado según esté colapsado o expandido
        if self.is_expanded:
            self.brand_header.content = ft.Row([
                self.logo_box,
                self.brand_text_col,
                ft.Container(expand=True),
                self.toggle_btn
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            self.brand_header.padding = ft.padding.only(left=2, right=2, top=4, bottom=8)
        else:
            # En modo colapsado, centrar el botón de menú para fácil despliegue
            self.brand_header.content = ft.Row([
                self.toggle_btn
            ], alignment=ft.MainAxisAlignment.CENTER)
            self.brand_header.padding = ft.padding.only(top=4, bottom=8)

        self.user_avatar.width = 32 if self.is_expanded else 26
        self.user_avatar.height = 32 if self.is_expanded else 26
        self.user_badge.padding = ft.padding.symmetric(horizontal=8, vertical=6) if self.is_expanded else ft.padding.all(4)

        for control in self.content.controls:
            if isinstance(control, ft.ListTile):
                control.title.visible = self.is_expanded
                control.content_padding = ft.padding.only(left=10 if self.is_expanded else 6, right=10 if self.is_expanded else 6)

        try:
            self.update()
        except Exception:
            pass

    def mostrar_disclaimer(self, e):
        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.GAVEL_ROUNDED, color=Config.COLOR_ACCENT),
                ft.Text("Información Legal y Créditos", size=16, weight="bold", color=Config.COLOR_PRIMARY)
            ]),
            content=ft.Column([
                ft.Text("Versión del Software: 1.0", size=13, weight="bold"),
                ft.Divider(height=10, color=Config.COLOR_BORDER),
                ft.Text("Autoría Intelectual:", size=13, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Este software fue diseñado, estructurado y desarrollado en su totalidad por Eliana Garces. Todos los derechos sobre el código fuente y la arquitectura de la aplicación están reservados a su autor.", size=12, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.JUSTIFY),
                ft.Divider(height=10, color=Config.COLOR_BORDER),
                ft.Text("Descargo de Responsabilidad:", size=13, weight="bold", color=Config.COLOR_DANGER),
                ft.Text("La veracidad de la información, el manejo de inventarios, la gestión financiera y el uso general de los datos introducidos en esta plataforma, así como las decisiones operativas tomadas en base a los mismos, son responsabilidad única y exclusiva de Abarrotes y Desechables de Doña Mary SAS.", size=12, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.JUSTIFY)
            ], tight=True, spacing=5, width=420),
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

    def mostrar_modal_qr(self, e=None):
        from core.mobile_service import MobileCountingService
        from core.mobile_server import iniciar_servidor_en_hilo
        iniciar_servidor_en_hilo(port=8550)
        
        service = MobileCountingService()
        url = service.get_server_url(port=8550)
        qr_b64 = service.get_qr_base64(port=8550)

        def copiar_url(ev):
            if self.page:
                self.page.set_clipboard(url)
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Enlace copiado al portapapeles: {url}"), bgcolor=Config.COLOR_SUCCESS)
                self.page.snack_bar.open = True
                self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.PHONE_ANDROID_ROUNDED, color=Config.COLOR_ACCENT),
                ft.Text("Conteo Móvil Wi-Fi (Bodega)", size=16, weight="bold", color=Config.COLOR_PRIMARY)
            ]),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=8, height=8, bgcolor=Config.COLOR_SUCCESS, border_radius=4),
                            ft.Text("Servidor Activo en Red Local", size=11, weight="bold", color=Config.COLOR_SUCCESS)
                        ], spacing=6),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=Config.COLOR_SUCCESS_BG,
                        border_radius=12,
                        border=ft.border.all(1, ft.colors.with_opacity(0.3, Config.COLOR_SUCCESS))
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(
                    content=ft.Image(src_base64=qr_b64, width=190, height=190, fit=ft.ImageFit.CONTAIN),
                    alignment=ft.alignment.center,
                    padding=10,
                    bgcolor="white",
                    border=ft.border.all(1, Config.COLOR_BORDER),
                    border_radius=12
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.LINK_ROUNDED, size=16, color=Config.COLOR_ACCENT),
                        ft.Text(url, size=13, weight="bold", color=Config.COLOR_ACCENT, selectable=True),
                        ft.IconButton(icon=ft.icons.COPY_ALL_ROUNDED, icon_size=18, tooltip="Copiar enlace", on_click=copiar_url)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    bgcolor=Config.COLOR_BACKGROUND,
                    border=ft.border.all(1, Config.COLOR_BORDER),
                    border_radius=8
                ),
                ft.Text(
                    "Apunta con la cámara de cualquier teléfono conectado a la red Wi-Fi de la bodega para registrar el stock inicial de Agosto sin cables ni instalaciones.",
                    size=11, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER
                )
            ], tight=True, spacing=10, width=380, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Copiar Enlace", on_click=copiar_url),
                ft.ElevatedButton("Cerrar", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=lambda e: self._cerrar_dialogo(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=14)
        )
        if self.page:
            if hasattr(self.page, "open"):
                self.page.open(dlg)
            else:
                self.page.overlay.append(dlg)
                dlg.open = True
                self.page.update()
