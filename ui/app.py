import flet as ft
import threading
from ui.layout.sidebar import Sidebar
from ui.views.dashboard import DashboardView
from ui.views.inventario import InventarioView
from ui.views.compras import ComprasView
from ui.views.ventas import VentasView
from ui.views.cierre_inventario import CierreInventarioView
from ui.views.ajustes_inventario import AjustesInventarioView
class AppLayout(ft.Row):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.spacing = 0
        
        # Vistas
        self.views = {
            "dashboard": DashboardView(),
            "inventario": InventarioView(),
            "compras": ComprasView(),
            "ventas": VentasView(),
            "ajustes_inventario": AjustesInventarioView(),
            "cierre_mes": CierreInventarioView(),
        }
        
        # Contenedor principal de la vista activa
        self.active_view = ft.Container(
            content=self.views["dashboard"],
            expand=True,
            bgcolor="#F4F6F7",
            padding=15,
            alignment=ft.alignment.top_left
        )
        
        # Sidebar
        self.sidebar = Sidebar(self.on_route_change)
        
        # Componentes del Row
        self.controls = [
            self.sidebar,
            self.active_view
        ]
        
    def on_route_change(self, route_name):
        # Cambiar el contenido del contenedor principal
        if route_name in self.views:
            vista = self.views[route_name]
            self.active_view.content = vista
            self.active_view.update()
            
            # Resaltar la ruta activa en el menú lateral
            self.sidebar.update_active_route(route_name)
            
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
