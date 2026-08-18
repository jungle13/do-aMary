import flet as ft
from config import Config

class CustomAutoComplete(ft.Container):
    """
    Componente Autocompletado nativo compatible con Flet 0.21.2
    Emula la interfaz de ft.AutoComplete para reemplazar textfields existentes.
    """
    def __init__(self, hint_text="Buscar por código o nombre...", on_select=None, text_size=12, height=40, expand=False):
        super().__init__()
        self.on_select = on_select
        self.suggestions = [] # Lista de dicts: [{"key": str, "value": str}]
        self.expand = expand
        
        # Guard textfield interno para mantener compatibilidad con el request del usuario
        self.search_input_text = ft.TextField(visible=False)
        
        self.search_input = ft.TextField(
            hint_text=hint_text,
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            border_radius=8,
            dense=True,
            height=height,
            text_size=text_size,
            bgcolor="white",
            content_padding=10,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            on_change=self._on_text_change,
            on_submit=self._on_submit
        )

        self.sug_list = ft.ListView(expand=True, spacing=0, height=150)
        self.sug_container = ft.Container(
            content=self.sug_list,
            visible=False,
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.1, "black"))
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
        except:
            pass

    def _on_text_change(self, e):
        query = self.search_input.value.lower()
        self.sug_list.controls.clear()
        
        if query and self.suggestions:
            for item in self.suggestions:
                val = item.get("value", "")
                if query in val.lower():
                    self.sug_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(val, size=12),
                            on_click=self._create_on_click_handler(item),
                            dense=True,
                        )
                    )
            self.sug_container.visible = len(self.sug_list.controls) > 0
        else:
            self.sug_container.visible = False
            
        self._safe_update()

    def _create_on_click_handler(self, item):
        def handler(e):
            self.search_input.value = item.get("value", "")
            self.sug_container.visible = False
            self._safe_update()
            
            # Emitir evento compatible con la estructura e.selection.value
            class MockSelection:
                def __init__(self, key, value):
                    self.key = key
                    self.value = value
            
            class MockEvent:
                def __init__(self, key, value, control):
                    self.selection = MockSelection(key, value)
                    self.control = control
            
            if self.on_select:
                self.on_select(MockEvent(item.get("key"), item.get("value"), self.search_input))
        return handler

    def _on_submit(self, e):
        self.sug_container.visible = False
        self._safe_update()
        
        class MockEvent:
            def __init__(self, control):
                self.selection = None
                self.control = control
                
        if self.on_select:
            self.on_select(MockEvent(self.search_input))

    @property
    def value(self):
        return self.search_input.value
        
    @value.setter
    def value(self, new_value):
        self.search_input.value = new_value
        if self.page:
            self.search_input.update()
