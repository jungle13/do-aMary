import ast

with open('core/supabase_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

tree = ast.parse(''.join(lines))

methods_to_remove = [
    'get_compras_summary',
    'get_ventas_summary',
    'get_catalogo_summary',
    'get_top_ventas_mes',
    'get_tendencia_diaria',
    'get_inventario_kpis'
]

ranges_to_delete = []

class MethodVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        if node.name in methods_to_remove:
            ranges_to_delete.append((node.lineno, node.end_lineno))
        self.generic_visit(node)

visitor = MethodVisitor()
visitor.visit(tree)

# Sort ranges in reverse to delete from bottom up without messing up line indices
ranges_to_delete.sort(key=lambda x: x[0], reverse=True)

for start, end in ranges_to_delete:
    del lines[start-1:end]

# Append the new methods
new_methods = '''
    def get_compras_summary(self) -> dict:
        \"\"\"Invoca RPC para totales de compras\"\"\"
        import datetime
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        
        url = f"{self.url}/rpc/get_compras_summary_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual, "dia_hoy": hoy}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC compras_summary: {e}")
        return {"total_mes": 0.0, "total_hoy": 0.0, "cantidad_total": 0.0}

    def get_ventas_summary(self) -> dict:
        \"\"\"Invoca RPC para totales de ingresos e IVA\"\"\"
        import datetime
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        
        url = f"{self.url}/rpc/get_ventas_summary_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual, "dia_hoy": hoy}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC ventas_summary: {e}")
        return {"total_historico": 0.0, "total_mes": 0.0, "total_hoy": 0.0, "iva_historico": 0.0, "iva_hoy": 0.0}

    def get_catalogo_summary(self) -> dict:
        \"\"\"Invoca RPC para compras totales y ventas totales en pesos\"\"\"
        url = f"{self.url}/rpc/get_catalogo_summary_rpc"
        try:
            res = requests.post(url, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC catalogo_summary: {e}")
        return {"total_compras": 0.0, "total_ventas": 0.0}

    def get_top_ventas_mes(self, limit=10) -> list:
        import datetime
        mes_actual = datetime.date.today().strftime("%Y-%m")
        url = f"{self.url}/rpc/get_top_ventas_mes_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual, "limite": limit}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC top_ventas: {e}")
        return []

    def get_tendencia_diaria(self) -> dict:
        \"\"\"Invoca RPC para obtener ventas y compras agrupadas por día\"\"\"
        import datetime
        hoy = datetime.date.today()
        mes_actual = hoy.strftime("%Y-%m")
        
        # Pre-poblar el diccionario con ceros para todos los días transcurridos
        tendencia = {f"{mes_actual}-{i:02d}": {"ventas": 0.0, "compras": 0.0} for i in range(1, hoy.day + 1)}
        
        url = f"{self.url}/rpc/get_tendencia_diaria_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual}, headers=self.headers)
            if res.status_code == 200:
                for row in res.json():
                    dia = row.get("dia")
                    if dia in tendencia:
                        tendencia[dia]["ventas"] = float(row.get("ventas", 0))
                        tendencia[dia]["compras"] = float(row.get("compras", 0))
        except Exception as e:
            print(f"Error RPC tendencia_diaria: {e}")
        return tendencia

    def get_inventario_kpis(self) -> dict:
        import datetime
        mes_actual = datetime.date.today().strftime("%Y-%m")
        url = f"{self.url}/rpc/get_inventario_kpis_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC inventario_kpis: {e}")
        return {"valor_inventario": 0.0, "alertas_criticas": 0}
'''

lines.append(new_methods)

with open('core/supabase_client.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('File updated successfully.')
