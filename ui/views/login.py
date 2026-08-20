"""
Vista de autenticación / Login para Sistema Doña Mary.
Diseño moderno, tarjetas con sombras difusas e inputs estilizados.
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
        
        # Fondo Slate Profundo
        self.bgcolor = Config.COLOR_PRIMARY

        # Campos de texto modernos
        self.txt_usuario = ft.TextField(
            label="Usuario",
            prefix_icon=ft.icons.PERSON_ROUNDED,
            border_radius=10,
            height=46,
            dense=True,
            text_size=13,
            bgcolor="#F8FAFC",
            border_color=Config.COLOR_BORDER,
            focused_border_color=Config.COLOR_ACCENT,
            focused_bgcolor="white"
        )
        self.txt_clave = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.icons.LOCK_ROUNDED,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            height=46,
            dense=True,
            text_size=13,
            bgcolor="#F8FAFC",
            border_color=Config.COLOR_BORDER,
            focused_border_color=Config.COLOR_ACCENT,
            focused_bgcolor="white",
            on_submit=self.autenticar
        )
        self.lbl_error = ft.Text("", color=Config.COLOR_DANGER, size=12, visible=False, weight="bold")
        self.progress = ft.ProgressBar(width=300, color=Config.COLOR_ACCENT, visible=False)

        self.btn_ingresar = ft.ElevatedButton(
            "Iniciar Sesión",
            icon=ft.icons.LOGIN_ROUNDED,
            bgcolor=Config.COLOR_ACCENT,
            color="white",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=0
            ),
            width=300,
            height=44,
            on_click=self.autenticar
        )

        self.lbl_creditos = ft.Text(
            "Elaborado por Eliana Garces 2026",
            size=11,
            color=Config.COLOR_TEXT_LIGHT,
            italic=True,
            text_align=ft.TextAlign.CENTER
        )

        # Formulario de credenciales
        self.form_column = ft.Column([
            ft.Container(
                content=ft.Icon(ft.icons.STOREFRONT_ROUNDED, size=40, color=Config.COLOR_ACCENT),
                padding=14,
                bgcolor=ft.colors.with_opacity(0.12, Config.COLOR_ACCENT),
                border_radius=50
            ),
            ft.Text("Abarrotes Doña Mary", size=22, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Text("Ingreso al Sistema", size=13, color=Config.COLOR_TEXT_MUTED),
            ft.Divider(height=10, color="transparent"),
            self.txt_usuario,
            self.txt_clave,
            self.lbl_error,
            self.progress,
            ft.Container(height=4),
            self.btn_ingresar,
            ft.Divider(height=10, color="transparent"),
            self.lbl_creditos
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)

        # Panel Flotante Blanco Centrado
        self.card_container = ft.Container(
            width=390,
            padding=36,
            bgcolor="white",
            border_radius=18,
            border=ft.border.all(1, Config.COLOR_BORDER),
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=24,
                color=ft.colors.with_opacity(0.25, "black"),
                offset=ft.Offset(0, 8)
            ),
            content=self.form_column
        )

        self.content = self.card_container

    def autenticar(self, e):
        user = self.txt_usuario.value.strip().lower()
        pwd = self.txt_clave.value.strip()

        if not user or not pwd:
            self.lbl_error.value = "Por favor ingresa usuario y contraseña."
            self.lbl_error.visible = True
            self.update()
            return

        self.progress.visible = True
        self.btn_ingresar.disabled = True
        self.lbl_error.visible = False
        self.update()

        threading.Thread(target=self._worker_autenticar, args=(user, pwd), daemon=True).start()

    def _worker_autenticar(self, user, pwd):
        try:
            datos_usuario = self.db.autenticar_usuario(user, pwd)
            if datos_usuario:
                self._mostrar_bienvenida_en_tarjeta(datos_usuario)
            else:
                self.lbl_error.value = "Credenciales incorrectas o usuario inactivo."
                self.lbl_error.visible = True
                self.progress.visible = False
                self.btn_ingresar.disabled = False
                if self.page:
                    self.page.update()
        except Exception as ex:
            log_error(f"Login de usuario {user}", ex)
            self.lbl_error.value = f"Error al verificar credenciales: {ex}"
            self.lbl_error.visible = True
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

        self.card_container.content = ft.Column([
            ft.Container(height=10),
            ft.Icon(ft.icons.WAVING_HAND_ROUNDED, size=48, color=Config.COLOR_WARNING),
            ft.Text(f"¡Bienvenido, {primer_nombre}!", size=20, weight="bold", color=Config.COLOR_PRIMARY, text_align=ft.TextAlign.CENTER),
            ft.Text("Accediendo al sistema...", size=13, color=Config.COLOR_TEXT_MUTED),
            ft.Divider(height=10, color="transparent"),
            ft.ProgressRing(width=28, height=28, color=Config.COLOR_ACCENT, stroke_width=3),
            ft.Divider(height=15, color="transparent"),
            self.lbl_creditos
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)

        if self.page:
            self.page.update()

        time.sleep(1.2)
        self.on_login_success(datos_usuario)
