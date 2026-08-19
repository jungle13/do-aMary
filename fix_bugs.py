import re

def fix_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Fix on_eliminar_carga signature and inject variables
    old_sig = "def on_eliminar_carga(self, data, grupo_key, num_pag):"
    new_sig = """def on_eliminar_carga(self, data):
        grupo_key = data.get("fecha")
        num_pag = str(data.get("pagina"))"""
    content = content.replace(old_sig, new_sig)

    # 2. Fix CustomAutoComplete instantiation
    old_auto = """self.crud_codigo_insumo = CustomAutoComplete(
            options=[],
            width=350,
            label="Insumo (Buscar por Código o Nombre)",
            on_select=self._on_insumo_crud_select
        )"""
    new_auto = """self.crud_codigo_insumo = CustomAutoComplete(
            hint_text="Buscar insumo (Código o Nombre)",
            on_select=self._on_insumo_crud_select
        )
        self.crud_codigo_insumo.width = 350"""
    content = content.replace(old_auto, new_auto)

    # 3. Fix CustomAutoComplete options -> suggestions
    old_opts = 'self.crud_codigo_insumo.options = [f"[{i[\'codigo_insumo\']}] {i[\'nombre\']}" for i in insumos]'
    new_opts = 'self.crud_codigo_insumo.suggestions = [{"key": i[\'codigo_insumo\'], "value": f"[{i[\'codigo_insumo\']}] {i[\'nombre\']}"} for i in insumos]'
    content = content.replace(old_opts, new_opts)
    
    # Also fix it if there are multiple occurrences (like in editar and crear modals)
    
    # 4. In ventas.py, the autocomplete might have a different label, let's just do regex if it doesn't match
    if 'CustomAutoComplete(' in content and old_auto not in content:
        # regex to fix it
        content = re.sub(
            r'self.crud_codigo_insumo\s*=\s*CustomAutoComplete\(\s*options=\[.*?on_select=self\._on_insumo_crud_select\s*\)',
            new_auto,
            content,
            flags=re.DOTALL
        )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
fix_file("ui/views/compras.py")
fix_file("ui/views/ventas.py")
print("Bugs fixed")
