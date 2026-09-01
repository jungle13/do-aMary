import flet as ft
import threading
from ui.layout.sidebar import Sidebar
from ui.views.dashboard import DashboardView
from ui.views.inventario import InventarioView
from ui.views.compras import ComprasView
from ui.views.ventas import VentasView
from ui.views.cartera import CarteraView
from ui.views.cierre_inventario import CierreInventarioView
from ui.views.conteo_inicial import ConteoInicialView
from ui.views.ajustes_inventario import AjustesInventarioView
from ui.views.informes import InformesView
from config import Config
from core.logger import get_logger, log_error

logger = get_logger("AppLayout")

class AppLayout(ft.Row):
    def __init__(self, page: ft.Page, usuario_data=None, on_logout=None):
        super().__init__()
        self.page = page
        self.usuario_data = usuario_data or {}
        from core.audit_logger import set_current_user
        set_current_user(self.usuario_data)
        self.on_logout = on_logout
        self.expand = True
        self.spacing = 0

        # Ruta por defecto
        username = str(self.usuario_data.get("usuario", "")).lower()
        rol = str(self.usuario_data.get("rol", "OPERADOR")).upper()
        es_admin = username in ["eliana", "cesar", "mary"] or rol == "ADMINISTRADOR"
        
        self.initial_route = "dashboard" if es_admin else "inventario"

        self.active_route = self.initial_route
        self._nav_token = 0

        # Instanciar vista inicial limpia
        self.views = {}
        self.views[self.initial_route] = self._crear_vista(self.initial_route)

        self.active_view = ft.Container(
            content=self.views[self.initial_route],
            expand=True,
            bgcolor=Config.COLOR_BACKGROUND,
            padding=18,
            alignment=ft.alignment.top_left
        )

        self.sidebar = Sidebar(
            self.on_route_change,
            usuario_data=self.usuario_data,
            on_logout=self.on_logout,
            on_reset=self.reset_global_state
        )

        self.controls = [
            self.sidebar,
            self.active_view
        ]

    def _crear_vista(self, route_name: str):
        """Fábrica de vistas para instanciación limpia bajo demanda."""
        if route_name == "dashboard": return DashboardView()
        elif route_name == "inventario": return InventarioView()
        elif route_name == "compras": return ComprasView()
        elif route_name == "ventas": return VentasView()
        elif route_name == "cartera": return CarteraView()
        elif route_name == "conteo": return ConteoInicialView()
        elif route_name == "ajustes_inventario": return AjustesInventarioView()
        elif route_name == "cierre_mes": return CierreInventarioView()
        elif route_name == "informes": return InformesView()
        return InventarioView()

    def reset_global_state(self):
        """
        Auto-recuperación y purga total en caliente:
        1. Limpia modales y diálogos huérfanos en overlay.
        2. Restablece la sesión HTTP y sockets TCP con Supabase.
        3. Vacía la caché de vistas y recarga la vista actual desde cero.
        """
        logger.info("Iniciando auto-recuperación y purga global de caché...")
        try:
            # 1. Limpiar overlay
            if self.page and hasattr(self.page, "overlay"):
                self.page.overlay.clear()

            # 2. Resetear sesión HTTP
            from core.database import BaseDatabase
            BaseDatabase().reset_session()

            # 3. Limpiar caché de clientes
            try:
                from core.repositories.clientes_repo import ClientesRepository
                ClientesRepository().limpiar_cache()
            except Exception:
                pass

            # 4. Vaciar vistas y re-instanciar la activa
            self.views.clear()
            self._nav_token += 1
            curr_token = self._nav_token
            
            nueva_vista = self._crear_vista(self.active_route)
            self.views[self.active_route] = nueva_vista
            self.active_view.content = nueva_vista

            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.icons.CHECK_CIRCLE, color="white", size=18),
                        ft.Text("Sistema restaurado y caché purgada", color="white")
                    ]),
                    bgcolor="green700",
                    duration=2500
                )
                self.page.snack_bar.open = True
                self.page.update()

            # 5. Cargar datos en segundo plano protegido
            def reload_bg():
                if hasattr(nueva_vista, 'load_data'):
                    try:
                        nueva_vista.load_data()
                    except Exception as ex:
                        log_error(f"reset load_data en {self.active_route}", ex)
                if hasattr(nueva_vista, 'load_summary'):
                    try:
                        nueva_vista.load_summary()
                    except Exception as ex:
                        log_error(f"reset load_summary en {self.active_route}", ex)
            threading.Thread(target=reload_bg, daemon=True).start()

        except Exception as e:
            log_error("reset_global_state", e)

    def did_mount(self):
        # Actualizar estado activo en el sidebar para la vista inicial
        if hasattr(self.sidebar, "actualizar_estado_activo"):
            self.sidebar.actualizar_estado_activo(self.initial_route)
            
        # Iniciar carga de datos con token de protección
        self._nav_token += 1
        curr_token = self._nav_token
        def load_data_bg():
            if curr_token != self._nav_token:
                return
            vista = self.views.get(self.initial_route)
            if not vista:
                return
            if hasattr(vista, 'load_data'):
                try:
                    vista.load_data()
                except Exception as e:
                    log_error(f"load_data en vista inicial {self.initial_route}", e)
            if curr_token != self._nav_token:
                return
            if hasattr(vista, 'load_summary'):
                try:
                    vista.load_summary()
                except Exception as e:
                    log_error(f"load_summary en vista inicial {self.initial_route}", e)
        threading.Thread(target=load_data_bg, daemon=True).start()
        
    def on_route_change(self, route_name):
        if not route_name:
            return
        
        logger.info(f"Navegando a ruta: {route_name}")
        self.active_route = route_name
        self._nav_token += 1
        curr_token = self._nav_token

        # Auto-purga de modales residuales al cambiar de pantalla
        if self.page and hasattr(self.page, "overlay"):
            try:
                self.page.overlay.clear()
            except Exception:
                pass

        # Instanciación limpia bajo demanda
        if route_name not in self.views:
            try:
                self.views[route_name] = self._crear_vista(route_name)
            except Exception as e:
                log_error(f"Error instanciando vista {route_name}", e)
                return
            
        # Cambiar el contenido del contenedor principal
        if route_name in self.views:
            vista = self.views[route_name]
            self.active_view.content = vista
            try:
                self.active_view.update()
            except Exception:
                try:
                    if self.page:
                        self.page.update()
                except Exception as e:
                    log_error(f"Error actualizando vista al navegar a {route_name}", e)
            
            # Resaltar la ruta activa en el menú lateral
            if hasattr(self.sidebar, "actualizar_estado_activo"):
                self.sidebar.actualizar_estado_activo(route_name)
            
            # Recarga protegida contra carreras de hilos (thread cancellation)
            def load_data_bg():
                if curr_token != self._nav_token:
                    return  # El usuario ya navegó a otra pestaña, abortar silenciosamente
                if hasattr(vista, 'load_data'):
                    try:
                        vista.load_data()
                    except Exception as e:
                        log_error(f"reload load_data en {route_name}", e)
                        
                if curr_token != self._nav_token:
                    return  # El usuario ya navegó a otra pestaña, abortar silenciosamente
                if hasattr(vista, 'load_summary'):
                    try:
                        vista.load_summary()
                    except Exception as e:
                        log_error(f"reload load_summary en {route_name}", e)
            
            threading.Thread(target=load_data_bg, daemon=True).start()
