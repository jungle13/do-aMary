"""
Vista de autenticación / Login para Sistema Doña Mary.
Diseño split-hero ejecutivo, tarjeta flotante central, branding institucional y micro-interacciones.
"""
import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
from core.logger import get_logger, log_error
import time
import threading

logger = get_logger("LoginView")

class LoginView(ft.Container):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.db = SupabaseClient()
        self.expand = True
        self.alignment = ft.alignment.center
        
        # Fondo oscuro profundo con gradiente espacial
        self.gradient = ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#090D16", "#0F172A", "#1E293B"]
        )

        # --- CAMPOS DEL FORMULARIO ---
        self.txt_usuario = ft.TextField(
            label="Usuario",
            hint_text="Ingresa tu usuario",
            prefix_icon=ft.icons.PERSON_ROUNDED,
            border_radius=12,
            height=48,
            text_size=13,
            bgcolor="#F8FAFC",
            border_color="#E2E8F0",
            focused_border_color=Config.COLOR_ACCENT,
            focused_bgcolor="white",
            content_padding=ft.padding.symmetric(horizontal=15, vertical=12)
        )

        self.txt_clave = ft.TextField(
            label="Contraseña",
            hint_text="••••••••",
            prefix_icon=ft.icons.LOCK_ROUNDED,
            password=True,
            can_reveal_password=True,
            border_radius=12,
            height=48,
            text_size=13,
            bgcolor="#F8FAFC",
            border_color="#E2E8F0",
            focused_border_color=Config.COLOR_ACCENT,
            focused_bgcolor="white",
            content_padding=ft.padding.symmetric(horizontal=15, vertical=12),
            on_submit=self.autenticar
        )

        self.lbl_error = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.ERROR_OUTLINE_ROUNDED, color=Config.COLOR_DANGER, size=16),
                ft.Text("", color=Config.COLOR_DANGER, size=12, weight="bold", expand=True)
            ], spacing=6),
            visible=False,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_DANGER),
            border_radius=8
        )

        self.progress = ft.ProgressBar(color=Config.COLOR_ACCENT, bgcolor="#E2E8F0", visible=False)

        self.btn_ingresar = ft.ElevatedButton(
            "Iniciar Sesión",
            icon=ft.icons.ARROW_FORWARD_ROUNDED,
            bgcolor=Config.COLOR_ACCENT,
            color="white",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                elevation=2
            ),
            height=48,
            on_click=self.autenticar
        )

        self.lbl_creditos = ft.Text(
            "Sistema Doña Mary • v2.0 • Elaborado por Eliana Garcés 2026",
            size=10.5,
            color="#94A3B8",
            text_align=ft.TextAlign.CENTER
        )

        # --- LADO IZQUIERDO: HERO BRANDING ---
        item_features = [
            ("boxes_stacked", "Control de Stock e Inventario"),
            ("chart_line", "Analítica Financiera & Ventas POS"),
            ("shield_check", "Auditorías y Cierres Mensuales"),
        ]
        
        feature_rows = []
        icons_map = {
            "boxes_stacked": ft.icons.INVENTORY_2_ROUNDED,
            "chart_line": ft.icons.QUERY_STATS_ROUNDED,
            "shield_check": ft.icons.VERIFIED_USER_ROUNDED
        }

        for icon_key, text in item_features:
            feature_rows.append(
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icons_map[icon_key], size=16, color="#60A5FA"),
                        padding=6,
                        bgcolor=ft.colors.with_opacity(0.15, "#3B82F6"),
                        border_radius=8
                    ),
                    ft.Text(text, size=12, color="#E2E8F0", weight="w500")
                ], spacing=10)
            )

        self.panel_izquierdo = ft.Container(
            width=360,
            padding=32,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=["#0F172A", "#1E293B"]
            ),
            border_radius=ft.border_radius.only(top_left=24, bottom_left=24),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.STOREFRONT_ROUNDED, size=28, color="white"),
                        padding=10,
                        bgcolor=Config.COLOR_ACCENT,
                        border_radius=12,
                        shadow=ft.BoxShadow(
                            blur_radius=12,
                            color=ft.colors.with_opacity(0.4, Config.COLOR_ACCENT),
                            offset=ft.Offset(0, 4)
                        )
                    ),
                    ft.Column([
                        ft.Text("DOÑA MARY", size=17, weight="bold", color="white"),
                        ft.Text("Abarrotes & Desechables", size=11, color="#94A3B8")
                    ], spacing=1)
                ], spacing=12),
                
                ft.Container(height=20),
                
                ft.Text("Gestión Inteligente de Inventario y Operaciones", size=20, weight="bold", color="white"),
                ft.Text("Plataforma centralizada para control de existencias, remisiones y facturación.", size=12, color="#94A3B8"),
                
                ft.Container(height=10),
                ft.Divider(color=ft.colors.with_opacity(0.2, "#FFFFFF")),
                ft.Container(height=10),
                
                ft.Column(feature_rows, spacing=12),
                
                ft.Container(expand=True),
                
                ft.Row([
                    ft.Container(width=8, height=8, bgcolor="#22C55E", border_radius=4),
                    ft.Text("Sistema Conectado • Cloud Supabase", size=11, color="#86EFAC")
                ], spacing=6)
            ])
        )

        # --- LADO DERECHO: FORMULARIO DE ACCESO ---
        self.form_column = ft.Column([
            ft.Text("Iniciar Sesión", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Text("Ingresa tus credenciales para acceder al sistema.", size=12.5, color=Config.COLOR_TEXT_MUTED),
            
            ft.Container(height=12),
            
            self.txt_usuario,
            self.txt_clave,
            self.lbl_error,
            self.progress,
            
            ft.Container(height=6),
            
            self.btn_ingresar,
            
            ft.Container(expand=True),
            
            self.lbl_creditos
        ], horizontal_alignment=ft.CrossAxisAlignment.STRETCH, spacing=10)

        self.panel_derecho = ft.Container(
            width=420,
            padding=ft.padding.only(left=36, right=36, top=36, bottom=28),
            bgcolor="white",
            border_radius=ft.border_radius.only(top_right=24, bottom_right=24),
            content=self.form_column
        )

        # --- TARJETA PRINCIPAL COMBINADA (SPLIT HERO) ---
        self.card_container = ft.Container(
            width=780,
            height=490,
            border_radius=24,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.all(1, ft.colors.with_opacity(0.15, "white")),
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=36,
                color=ft.colors.with_opacity(0.5, "black"),
                offset=ft.Offset(0, 16)
            ),
            content=ft.Row([
                self.panel_izquierdo,
                self.panel_derecho
            ], spacing=0, expand=True)
        )

        self.content = self.card_container

    def autenticar(self, e=None):
        user = self.txt_usuario.value.strip().lower() if self.txt_usuario.value else ""
        pwd = self.txt_clave.value.strip() if self.txt_clave.value else ""

        if not user or not pwd:
            self._mostrar_error("Por favor ingresa tu usuario y contraseña.")
            return

        self.progress.visible = True
        self.btn_ingresar.disabled = True
        self.lbl_error.visible = False
        self.update()

        threading.Thread(target=self._worker_autenticar, args=(user, pwd), daemon=True).start()

    def _mostrar_error(self, mensaje: str):
        lbl_text = self.lbl_error.content.controls[1]
        lbl_text.value = mensaje
        self.lbl_error.visible = True
        self.update()

    def _worker_autenticar(self, user, pwd):
        try:
            datos_usuario = self.db.autenticar_usuario(user, pwd)
            if datos_usuario:
                self._mostrar_bienvenida_en_tarjeta(datos_usuario)
            else:
                self._mostrar_error("Credenciales incorrectas o usuario inactivo.")
                self.progress.visible = False
                self.btn_ingresar.disabled = False
                if self.page:
                    self.page.update()
        except Exception as ex:
            log_error(f"Login de usuario {user}", ex)
            self._mostrar_error(f"Error de conexión: {ex}")
            self.progress.visible = False
            self.btn_ingresar.disabled = False
            if self.page:
                self.page.update()

    def _mostrar_bienvenida_en_tarjeta(self, datos_usuario):
        nombre_completo = datos_usuario.get("nombre_completo") or datos_usuario.get("usuario") or "Usuario"
        partes = nombre_completo.split()
        primer_nombre = partes[0] if partes else "Usuario"
        if primer_nombre.lower() in ["doña", "dona"] and len(partes) > 1:
            primer_nombre = f"{partes[0]} {partes[1]}"

        self.panel_derecho.content = ft.Column([
            ft.Container(height=30),
            ft.Container(
                content=ft.Icon(ft.icons.WAVING_HAND_ROUNDED, size=44, color=Config.COLOR_WARNING),
                padding=16,
                bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_WARNING),
                border_radius=50
            ),
            ft.Text(f"¡Bienvenido, {primer_nombre}!", size=22, weight="bold", color=Config.COLOR_PRIMARY, text_align=ft.TextAlign.CENTER),
            ft.Text("Iniciando tu entorno de trabajo...", size=13, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            ft.Container(height=15),
            ft.ProgressRing(width=32, height=32, color=Config.COLOR_ACCENT, stroke_width=3),
            ft.Container(expand=True),
            self.lbl_creditos
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

        if self.page:
            self.page.update()

        time.sleep(1.0)
        self.on_login_success(datos_usuario)
