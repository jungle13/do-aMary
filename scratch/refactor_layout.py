import sys
import re

path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update did_mount
content = content.replace('def did_mount(self):\n        self.load_data()', 'def did_mount(self):\n        self.load_lista_periodos()')

# 2. Rename load_data to load_data_detalle
content = re.sub(r'def load_data\(self\):', r'def load_data_detalle(self):', content)
content = content.replace('self.load_data()', 'self.load_data_detalle()')

# 3. Update __init__
init_replacement_start = 'self.content = ft.Column(['
idx_start = content.find(init_replacement_start)
idx_end = content.find('    def _crear_kpi_card')

new_layout = '''
        # Controles vista_lista (Maestro)
        self.month_dropdown.label = 'Mes a iniciar'
        self.dt_periodos = ft.DataTable(
            column_spacing=15,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text('Periodo', weight='bold')),
                ft.DataColumn(ft.Text('Mes', weight='bold')),
                ft.DataColumn(ft.Text('Año', weight='bold')),
                ft.DataColumn(ft.Text('Estado', weight='bold')),
                ft.DataColumn(ft.Text('Acción', weight='bold')),
            ],
            rows=[]
        )
        self.vista_lista = ft.Column([
            ft.Text('Historial de Periodos', size=24, weight='bold', color=Config.COLOR_PRIMARY),
            ft.Row([self.month_dropdown, self.btn_iniciar_snapshot]),
            ft.Container(
                content=ft.Column([self.dt_periodos], scroll=ft.ScrollMode.ALWAYS, expand=True),
                expand=True
            )
        ], visible=True, expand=True)

        # Controles vista_detalle (Detalle)
        self.btn_volver = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=self.on_volver_lista)
        self.lbl_titulo_detalle = ft.Text('Auditoría: ...', size=24, weight='bold', color=Config.COLOR_PRIMARY)
        
        self.vista_detalle = ft.Column([
            ft.Row([self.btn_volver, self.lbl_titulo_detalle]),
            self.summary_container,
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    ft.Column([self.txt_estado_periodo, self.txt_progreso], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                    self.btn_aprobar_cierre
                ]),
                padding=15,
                bgcolor='white',
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, 'black'))
            ),
            ft.Container(
                content=ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS, expand=True),
                bgcolor='white',
                padding=5,
                border_radius=10,
                expand=True,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, 'black'))
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.only(top=10)
            ),
            self.action_bar
        ], visible=False, expand=True, spacing=15)

        self.content = ft.Column([self.vista_lista, self.vista_detalle], expand=True)
'''

content = content[:idx_start] + new_layout.lstrip('\n') + '\n' + content[idx_end:]

# 4. Inject new methods
new_methods = '''
    def load_lista_periodos(self):
        periodos = self.db.get_periodos_inventario()
        self.dt_periodos.rows.clear()
        
        for p in periodos:
            mes_periodo = p.get('mes_periodo', '')
            if not mes_periodo: continue
            
            parts = mes_periodo.split('-')
            year = parts[0]
            month = parts[1] if len(parts)>1 else ''
            
            estado = p.get('estado', 'DESCONOCIDO')
            color_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
            
            row = ft.DataRow(cells=[
                ft.DataCell(ft.Text(mes_periodo)),
                ft.DataCell(ft.Text(month)),
                ft.DataCell(ft.Text(year)),
                ft.DataCell(ft.Text(estado, color=color_estado.get(estado, 'black'), weight='bold')),
                ft.DataCell(ft.ElevatedButton('Ver', on_click=lambda e, m=mes_periodo: self.mostrar_detalle(m)))
            ])
            self.dt_periodos.rows.append(row)
            
        if self.page:
            self.page.update()

    def mostrar_detalle(self, mes):
        self.vista_lista.visible = False
        self.vista_detalle.visible = True
        self.mes_seleccionado = mes
        self.lbl_titulo_detalle.value = f'Auditoría: {mes}'
        self.load_data_detalle()

    def on_volver_lista(self, e):
        self.cancelar_edicion()
        self.vista_detalle.visible = False
        self.vista_lista.visible = True
        self.load_lista_periodos()
'''
content = content + new_methods

# 5. Fix on_month_change
content = content.replace(
'''    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.month_dropdown.update()
        self.current_page = 1
        self.load_data_detalle()''',
'''    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.month_dropdown.update()'''
)

# 6. Fix _on_generar_snapshot_worker
content = content.replace(
'''            if res.get("exito"):
                self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
                self.current_page = 1
                self.load_data_detalle()''',
'''            if res.get("exito"):
                self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
                self.current_page = 1
                self.mostrar_detalle(self.mes_seleccionado)'''
)

# 7. Standardize updates
content = re.sub(r'if self\.page:\s+self\.update\(\)', 'if self.page:\n            self.page.update()', content)
content = re.sub(r'(?<!\.)self\.update\(\)', 'if self.page:\n            self.page.update()', content)
content = re.sub(r'(?<!\.)self\.page\.update\(\)', 'if self.page:\n            self.page.update()', content)
content = re.sub(r'if self\.page:\s*if self\.page:\s*self\.page\.update\(\)', 'if self.page:\n            self.page.update()', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done layout rewrite')
