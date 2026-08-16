import ast

with open('requirements.txt', 'r') as f:
    reqs = f.read()
if 'plotly' not in reqs:
    with open('requirements.txt', 'a') as f:
        f.write('\nplotly\n')

with open('ui/views/dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Add imports at the top
lines.insert(4, "import plotly.graph_objects as go\nfrom flet.plotly_chart import PlotlyChart\n")

# 2. Re-read as single string to do simple targeted replacements
content = "".join(lines)

# Find the block for Chart in __init__
start_chart_init = content.find("        # Chart")
end_chart_init = content.find("        # Tables")

new_chart_init = """        # Contenedor preparado para Plotly
        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Text("Tendencia Diaria: Ingresos vs Costo de Ventas", size=16, weight="bold", color="white"),
                ft.Container(height=320, expand=True) # Placeholder que se llenará en load_data
            ]),
            bgcolor="#111111", # Fondo oscuro
            padding=20,
            border_radius=10,
            border=ft.border.all(1, "#333333"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.2, "black"))
        )
        
"""

content = content[:start_chart_init] + new_chart_init + content[end_chart_init:]


# 3. Find the block in load_data
start_load_data = content.find("        # 2. Load Chart Data")
end_load_data = content.find("        # 3. Load Tables Data")

new_load_data = """        # 2. Load Chart Data con Plotly
        try:
            tendencia = self.db.get_tendencia_diaria()
            dias_ordenados = sorted(tendencia.keys())
            
            x_data = []
            y_ventas = []
            y_compras = []
            
            for dia in dias_ordenados:
                # Formateo de fecha para mejor visualización en el eje X
                dia_formateado = dia[-2:] # Extrae el día
                x_data.append(dia_formateado)
                y_ventas.append(tendencia[dia]["ventas"])
                y_compras.append(tendencia[dia]["compras"])
                
            fig = go.Figure()
            
            # Serie: Ingresos por Ventas
            fig.add_trace(go.Scatter(
                x=x_data, y=y_ventas,
                mode='lines+markers',
                name='Ingresos',
                line=dict(color='#42a5f5', width=3, shape='spline'), # Azul claro para contraste en fondo oscuro
                fill='tozeroy',
                fillcolor='rgba(66, 165, 245, 0.1)',
                hovertemplate='Día: %{x}<br>Ingresos: $%{y:,.0f}<extra></extra>'
            ))
            
            # Serie: Costo de Ventas
            fig.add_trace(go.Scatter(
                x=x_data, y=y_compras,
                mode='lines+markers',
                name='Costos',
                line=dict(color='#2ecca0', width=3, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(46, 204, 160, 0.1)',
                hovertemplate='Día: %{x}<br>Costos: $%{y:,.0f}<extra></extra>'
            ))
            
            # Layout Dark Mode avanzado
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', # Transparente para que tome el color del contenedor Flet
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=10, b=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                xaxis=dict(
                    showgrid=True, gridcolor='#333333', gridwidth=1, griddash='dot',
                    tickmode='linear', dtick=2 # Muestra etiquetas en el eje X cada 2 días
                ),
                yaxis=dict(
                    showgrid=True, gridcolor='#333333', gridwidth=1, griddash='dot', 
                    tickprefix='$',
                    zeroline=True, zerolinecolor='#444444'
                ),
                hovermode="x unified", # Tooltip unificado que cruza ambas líneas verticalmente
                hoverlabel=dict(bgcolor="#222222", font_size=13, font_family="Inter")
            )
            
            # Inyectar la gráfica en el contenedor
            self.chart_container.content.controls[1] = PlotlyChart(fig, expand=True)
            
        except Exception as e:
            print(f"Error crítico construyendo Plotly Chart: {e}")
        
"""

content = content[:start_load_data] + new_load_data + content[end_load_data:]

with open('ui/views/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Update complete.")
