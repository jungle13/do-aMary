with open('ui/views/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove imports
content = content.replace("import plotly.graph_objects as go\n", "")
content = content.replace("from flet.plotly_chart import PlotlyChart\n", "")

# 2. Replace __init__ section
start_init = content.find("        # Contenedor preparado para Plotly")
end_init = content.find("        # Tables")

new_init = """        # Series de datos (Grosor y puntas redondeadas)
        self.chart_ventas = ft.LineChartData(
            data_points=[], 
            color=ft.colors.BLUE_400,
            stroke_width=4, 
            curved=True,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE_400)
        )
        self.chart_compras = ft.LineChartData(
            data_points=[], 
            color="#2ecca0", 
            stroke_width=4, 
            curved=True,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, "#2ecca0")
        )
        
        # Gráfico habilitando los ejes visuales
        self.line_chart = ft.LineChart(
            data_series=[self.chart_ventas, self.chart_compras],
            border=ft.border.all(1, ft.colors.with_opacity(0.2, "white")),
            min_y=0,
            min_x=0,
            expand=True,
            tooltip_bgcolor=ft.colors.BLUE_GREY_900,
            left_axis=ft.ChartAxis(labels_size=50), 
            bottom_axis=ft.ChartAxis(labels_size=40), 
        )
        
        # Leyenda adaptada a fondo oscuro
        leyenda = ft.Row([
            ft.Row([ft.Container(width=12, height=12, bgcolor=ft.colors.BLUE_400, border_radius=6), ft.Text("Ingresos", size=12, weight="bold", color="white")]),
            ft.Row([ft.Container(width=12, height=12, bgcolor="#2ecca0", border_radius=6), ft.Text("Costos", size=12, weight="bold", color="white")]),
        ], spacing=30, alignment=ft.MainAxisAlignment.CENTER)
        
        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Text("Tendencia Diaria: Ingresos vs Costo de Ventas", size=16, weight="bold", color="white"),
                leyenda,
                ft.Container(content=self.line_chart, height=320, expand=True, margin=ft.padding.only(top=10))
            ]),
            bgcolor="#111111", # Fondo negro estético
            padding=20,
            border_radius=10,
            border=ft.border.all(1, "#333333"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.2, "black"))
        )
        
"""

content = content[:start_init] + new_init + content[end_init:]

# 3. Replace load_data section
start_load = content.find("        # 2. Load Chart Data con Plotly")
end_load = content.find("        # 3. Load Tables Data")

new_load = """        # 2. Load Chart Data (Nativo Flet)
        try:
            tendencia = self.db.get_tendencia_diaria()
            dias_ordenados = sorted(tendencia.keys())
            max_val_y = 0
            
            pts_ventas = []
            pts_compras = []
            etiquetas_x = []
            
            for i, dia in enumerate(dias_ordenados):
                v = tendencia[dia]["ventas"]
                c = tendencia[dia]["compras"]
                if v > max_val_y: max_val_y = v
                if c > max_val_y: max_val_y = c
                
                tt_ventas = f"{dia}\\nIngresos: ${v:,.0f}         "
                tt_compras = f"{dia}\\nCostos: ${c:,.0f}         "
                estilo_tt = ft.TextStyle(size=14, weight="bold", color="white")
                
                pts_ventas.append(ft.LineChartDataPoint(i, v, tooltip=tt_ventas, tooltip_style=estilo_tt))
                pts_compras.append(ft.LineChartDataPoint(i, c, tooltip=tt_compras, tooltip_style=estilo_tt))
                
                # Densidad en Eje X: Mostrar la etiqueta cada 2 días
                if i % 2 == 0: 
                    dia_numero = dia[-2:] # Extrae solo el día (ej: "15")
                    etiquetas_x.append(
                        ft.ChartAxisLabel(
                            value=i, 
                            label=ft.Text(dia_numero, size=11, color="white70")
                        )
                    )
                
            if not pts_ventas:
                pts_ventas = [ft.LineChartDataPoint(0, 0)]
                pts_compras = [ft.LineChartDataPoint(0, 0)]
                
            self.chart_ventas.data_points = pts_ventas
            self.chart_compras.data_points = pts_compras
            
            self.line_chart.max_x = len(dias_ordenados) - 1 if dias_ordenados else 0
            max_y_calc = max_val_y * 1.15 if max_val_y > 0 else 1000
            self.line_chart.max_y = max_y_calc
            
            def formato_moneda_corta(valor):
                if valor >= 1000000: return f"${valor/1000000:.1f}M"
                if valor >= 1000: return f"${valor/1000:.0f}k"
                return f"${valor:.0f}"
                
            # Mayor densidad en Y: 8 divisiones en lugar de 5
            intervalo_y = max_y_calc / 8 if max_y_calc > 0 else 100
            etiquetas_y = [
                ft.ChartAxisLabel(value=step * intervalo_y, label=ft.Text(formato_moneda_corta(step * intervalo_y), size=11, color="white70"))
                for step in range(9)
            ]
            
            self.line_chart.left_axis.labels = etiquetas_y
            self.line_chart.bottom_axis.labels = etiquetas_x
            
            # Cuadrícula visible completa con efecto punteado
            self.line_chart.horizontal_grid_lines = ft.ChartGridLines(
                interval=intervalo_y,
                color=ft.colors.with_opacity(0.15, "white"),
                width=1,
                dash_pattern=[4, 4]
            )
            self.line_chart.vertical_grid_lines = ft.ChartGridLines(
                interval=2, # Línea vertical sincronizada con el eje X
                color=ft.colors.with_opacity(0.15, "white"),
                width=1,
                dash_pattern=[4, 4]
            )
            
        except Exception as e:
            print(f"Error crítico construyendo Chart Flet: {e}")
        
"""

content = content[:start_load] + new_load + content[end_load:]

with open('ui/views/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Reverted to native Flet chart")
