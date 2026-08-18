import flet as ft
import threading
from ui.layout.sidebar import Sidebar
from ui.views.dashboard import DashboardView
from ui.views.inventario import InventarioView
from ui.views.compras import ComprasView
from ui.views.ventas import VentasView
from ui.views.cierre_inventario import CierreInventarioView
from ui.views.ajustes_inventario import AjustesInventarioView
from ui.views.informes import InformesView

class AppLayout(ft.Row):
    def __init__(self, page: ft.Page, usuario_data=None, on_logout=None):
        super().__init__()
        self.page = page
        self.usuario_data = usuario_data or {}
        self.on_logout = on_logout
        self.expand = True
        self.spacing = 0

        # Ruta por defecto
        username = str(self.usuario_data.get("usuario", "")).lower()
        rol = str(self.usuario_data.get("rol", "OPERADOR")).upper()
        es_admin = username in ["eliana", "cesar", "mary"] or rol == "ADMINISTRADOR"
        
        self.initial_route = "dashboard" if es_admin else "inventario"

        # Instanciar vista inicial
        self.views = {}
        if self.initial_route == "dashboard":
            self.views["dashboard"] = DashboardView()
        else:
            self.views["inventario"] = InventarioView()

        self.active_view = ft.Container(
            content=self.views[self.initial_route],
            expand=True,
            bgcolor="#F4F6F7",
            padding=15,
            alignment=ft.alignment.top_left
        )

        self.sidebar = Sidebar(self.on_route_change, usuario_data=self.usuario_data, on_logout=self.on_logout)

        self.controls = [
            self.sidebar,
            self.active_view
        ]

    def did_mount(self):
        # Actualizar estado activo en el sidebar para la vista inicial
        if hasattr(self.sidebar, "actualizar_estado_activo"):
            self.sidebar.actualizar_estado_activo(self.initial_route)
            
        # Iniciar carga de datos
        def load_data_bg():
            vista = self.views[self.initial_route]
            if hasattr(vista, 'load_data'):
                try: vista.load_data()
                except Exception as e: pass
            if hasattr(vista, 'load_summary'):
                try: vista.load_summary()
                except Exception as e: pass
        threading.Thread(target=load_data_bg, daemon=True).start()
        
    def on_route_change(self, route_name):
        if not route_name: return
        
        # Instanciar de forma perezosa (Lazy Loading) para evitar lag inicial
        if route_name not in self.views:
            if route_name == "dashboard": self.views[route_name] = DashboardView()
            elif route_name == "inventario": self.views[route_name] = InventarioView()
            elif route_name == "compras": self.views[route_name] = ComprasView()
            elif route_name == "ventas": self.views[route_name] = VentasView()
            elif route_name == "ajustes_inventario": self.views[route_name] = AjustesInventarioView()
            elif route_name == "cierre_mes": self.views[route_name] = CierreInventarioView()
            elif route_name == "informes": self.views[route_name] = InformesView()
            
        # Cambiar el contenido del contenedor principal
        if route_name in self.views:
            vista = self.views[route_name]
            self.active_view.content = vista
            self.active_view.update()
            
            # Resaltar la ruta activa en el menú lateral
            if hasattr(self.sidebar, "actualizar_estado_activo"):
                self.sidebar.actualizar_estado_activo(route_name)
            
            # Forzar recarga de datos al navegar para evitar caché estancada
            # Se ejecuta en hilo secundario para evitar congelar la interfaz
            def load_data_bg():
                if hasattr(vista, 'load_data'):
                    try:
                        vista.load_data()
                    except Exception as e:
                        print(f"Error reload load_data en {route_name}: {e}")
                        
                if hasattr(vista, 'load_summary'):
                    try:
                        vista.load_summary()
                    except Exception as e:
                        print(f"Error reload load_summary en {route_name}: {e}")
            
            threading.Thread(target=load_data_bg, daemon=True).start()
