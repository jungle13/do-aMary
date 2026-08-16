import os

# 1. Update supabase_client.py
client_path = r"c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\core\supabase_client.py"
with open(client_path, 'r', encoding='utf-8') as f:
    client_code = f.read()

new_method = """
    def get_kpis_por_categoria(self) -> list:
        \"\"\"Invoca RPC para extraer rendimiento y rotación agrupada por categoría.\"\"\"
        url = f"{self.url}/rpc/get_kpis_por_categoria_rpc"
        try:
            import requests
            res = requests.post(url, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC get_kpis_por_categoria: {e}")
        return []
"""

if "def get_kpis_por_categoria" not in client_code:
    client_code += new_method
    with open(client_path, 'w', encoding='utf-8') as f:
        f.write(client_code)


# 2. Update dashboard.py
dashboard_path = r"c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\dashboard.py"
with open(dashboard_path, 'r', encoding='utf-8') as f:
    dashboard_code = f.read()

init_target = "        self.kpi_row = ft.ResponsiveRow(["
init_end = dashboard_code.find("        # Gráfico habilitando los ejes visuales", dashboard_code.find(init_target))

new_container = """        # Contenedor de Categorías (Scroll Horizontal)
        self.categorias_row = ft.Row(wrap=False, scroll=ft.ScrollMode.ADAPTIVE, spacing=15)
        self.categorias_container = ft.Container(
            content=ft.Column([
                ft.Text("Rendimiento Detallado por Categoría", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.categorias_row
            ]),
            margin=ft.padding.only(top=10, bottom=10)
        )
"""
if "self.categorias_row = ft.Row" not in dashboard_code:
    # Insert right before "# Gráfico"
    dashboard_code = dashboard_code[:init_end] + new_container + "\n" + dashboard_code[init_end:]

# Insert into self.content
if "self.categorias_container," not in dashboard_code:
    dashboard_code = dashboard_code.replace(
        "            self.kpi_row,\n            ft.Divider(height=10, color=\"transparent\"),\n            self.chart_container,",
        "            self.kpi_row,\n            ft.Divider(height=10, color=\"transparent\"),\n            self.categorias_container,\n            ft.Divider(height=10, color=\"transparent\"),\n            self.chart_container,"
    )

# Add to load_data
load_target = """        if self.page:
            self.update()"""

new_load = """        try:
            kpis_cat = self.db.get_kpis_por_categoria()
            self.categorias_row.controls.clear()
            for cat in kpis_cat:
                self.categorias_row.controls.append(self._build_categoria_card(cat))
        except Exception as e:
            print(f"Error cargando KPIs por categoría: {e}")
            
        if self.page:
            self.update()"""

if "kpis_cat = self.db.get_kpis_por_categoria()" not in dashboard_code:
    dashboard_code = dashboard_code.replace(load_target, new_load)


# Add _build_categoria_card
card_method = """
    def _build_categoria_card(self, data):
        rentabilidad = data.get('rentabilidad', 0)
        return ft.Container(
            width=260,
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.CATEGORY, color=Config.COLOR_SECONDARY, size=20),
                    ft.Text(str(data.get("categoria", "N/A")).upper(), weight="bold", size=13, color=Config.COLOR_PRIMARY, expand=True)
                ]),
                ft.Divider(height=1, color="#f0f0f0"),
                ft.Row([ft.Text("Inventario:", size=11, color="grey"), ft.Text(f"${data.get('costo_inventario', 0):,.0f}", size=12, weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Ventas:", size=11, color="grey"), ft.Text(f"${data.get('ventas_totales', 0):,.0f}", size=12, weight="bold", color="green")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Rotación:", size=11, color="grey"), ft.Text(f"{data.get('rotacion', 0):.2f}x", size=12, weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Rendimiento:", size=11, color="grey"), ft.Text(f"{rentabilidad:.1f}%", size=12, weight="bold", color="#2ecca0" if rentabilidad >= 0 else "red")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=6)
        )
"""

if "def _build_categoria_card" not in dashboard_code:
    dashboard_code += card_method

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(dashboard_code)

print("Update script finished.")
