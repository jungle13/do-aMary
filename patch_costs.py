import os

file_client = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\core\supabase_client.py'
with open(file_client, 'r', encoding='utf-8') as f:
    content = f.read()

new_method = """
    def get_catalogo_costos(self) -> dict:
        \"\"\"Obtiene un diccionario con los costos actuales del catálogo de insumos\"\"\"
        url = f"{self.url}/catalogo_insumos?select=codigo_insumo,costo_unitario"
        try:
            import requests
            res = requests.get(url, headers=self.headers)
            if res.status_code == 200:
                return {item.get('codigo_insumo'): float(item.get('costo_unitario') or 0) for item in res.json()}
        except Exception as e:
            print(f"Error get_catalogo_costos: {e}")
        return {}
"""
with open(file_client, 'a', encoding='utf-8') as f:
    f.write(new_method)

file_view = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(file_view, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    def load_data(self):
        import math
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.insumos_lista = self.datos_cierre.get("insumos", [])"""

repl = """    def load_data(self):
        import math
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.insumos_lista = self.datos_cierre.get("insumos", [])
        
        # Recuperar fallback de costos para los insumos que no tienen costo_unitario_snapshot
        costos_fallback = self.db.get_catalogo_costos()
        for ins in self.insumos_lista:
            if not ins.get("costo_unitario_snapshot"):
                ins["costo_unitario_snapshot"] = costos_fallback.get(ins.get("codigo_insumo"), 0)"""

content = content.replace(target, repl)

with open(file_view, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
