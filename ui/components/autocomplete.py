"""
Componente Autocompletado nativo compatible con Flet 0.21.2.
Diseño moderno con botón de limpieza instantánea, cierre automático y sincronización en tiempo real.
"""
import flet as ft
from config import Config

class CustomAutoComplete(ft.Container):
    def __init__(self, hint_text="Buscar por código o nombre...", on_select=None, text_size=12, height=40, expand=False):
        super().__init__()
        self.on_select = on_select
        self.suggestions = []
        self.expand = expand
        
        self.search_input_text = ft.TextField(visible=False)
        
        self.btn_clear = ft.IconButton(
            icon=ft.icons.CLOSE_ROUNDED,
            icon_size=16,
            icon_color="grey600",
            tooltip="Limpiar búsqueda",
            visible=False,
            on_click=self.clear
        )

        self.search_input = ft.TextField(
            hint_text=hint_text,
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            suffix=self.btn_clear,
            border_radius=8,
            dense=True,
            height=height,
            text_size=text_size,
            bgcolor="white",
            content_padding=10,
            border_color=Config.COLOR_BORDER,
            focused_border_color=Config.COLOR_ACCENT,
            cursor_color=Config.COLOR_ACCENT,
            on_change=self._on_text_change,
            on_submit=self._on_submit
        )

        self.sug_list = ft.ListView(expand=True, spacing=0, height=160)
        self.sug_container = ft.Container(
            content=self.sug_list,
            visible=False,
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, Config.COLOR_BORDER),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.colors.with_opacity(0.12, "black"),
                offset=ft.Offset(0, 4)
            )
        )
        
        self.content = ft.Column(
            controls=[
                self.search_input,
                self.sug_container
            ],
            spacing=0,
            tight=True
        )

    def _safe_update(self):
        try:
            if self.page:
                self.update()
        except Exception:
            pass

    def clear(self, e=None):
        """Limpia el texto, oculta las sugerencias y notifica el reset de búsqueda."""
        self.search_input.value = ""
        self.search_input_text.value = ""
        self.btn_clear.visible = False
        self.sug_container.visible = False
        self._safe_update()

        class MockSelection:
            def __init__(self):
                self.key = ""
                self.value = ""

        class MockEvent:
            def __init__(self, ctrl):
                self.selection = MockSelection()
                self.control = ctrl

        if self.on_select:
            try:
                self.on_select(MockEvent(self.search_input))
            except Exception:
                pass

    def _on_text_change(self, e):
        raw_val = self.search_input.value or ""
        query = raw_val.strip().lower()
        self.sug_list.controls.clear()
        self.btn_clear.visible = bool(raw_val)

        if query and self.suggestions:
            matches = 0
            for item in self.suggestions:
                val = item.get("value", "")
                if query in val.lower():
                    self.sug_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(val, size=12, color=Config.COLOR_TEXT),
                            hover_color=ft.colors.with_opacity(0.06, Config.COLOR_ACCENT),
                            on_click=self._create_on_click_handler(item),
                            dense=True,
                        )
                    )
                    matches += 1
                    if matches >= 20:  # Limitar para fluidez
                        break
            self.sug_container.visible = len(self.sug_list.controls) > 0
        else:
            # Si el texto está vacío, cerrar el desplegable de sugerencias y refrescar búsqueda global
            self.sug_container.visible = False
            self.search_input_text.value = ""
            if not raw_val and self.on_select:
                class MockSelection:
                    def __init__(self):
                        self.key = ""
                        self.value = ""

                class MockEvent:
                    def __init__(self, ctrl):
                        self.selection = MockSelection()
                        self.control = ctrl
                try:
                    self.on_select(MockEvent(self.search_input))
                except Exception:
                    pass

        self._safe_update()

    def _create_on_click_handler(self, item):
        def handler(e):
            val = item.get("value", "")
            self.search_input.value = val
            self.btn_clear.visible = bool(val)
            self.sug_container.visible = False
            self._safe_update()
            
            class MockSelection:
                def __init__(self, key, value):
                    self.key = key
                    self.value = value
            
            class MockEvent:
                def __init__(self, key, value, control):
                    self.selection = MockSelection(key, value)
                    self.control = control
            
            if self.on_select:
                try:
                    self.on_select(MockEvent(item.get("key"), val, self.search_input))
                except Exception:
                    pass
        return handler

    def _on_submit(self, e):
        self.sug_container.visible = False
        self._safe_update()
        
        val = self.search_input.value or ""
        class MockSelection:
            def __init__(self, value):
                self.key = value
                self.value = value

        class MockEvent:
            def __init__(self, value, control):
                self.selection = MockSelection(value)
                self.control = control
                
        if self.on_select:
            try:
                self.on_select(MockEvent(val, self.search_input))
            except Exception:
                pass

    @property
    def value(self):
        return self.search_input.value
        
    @value.setter
    def value(self, new_value):
        self.search_input.value = new_value
        self.btn_clear.visible = bool(new_value)
        if not new_value:
            self.sug_container.visible = False
            self.search_input_text.value = ""
        self._safe_update()
