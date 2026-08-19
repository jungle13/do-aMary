import re

with open("ui/views/ventas.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add "Acciones" column to FIRST table only
match = re.search(r'columns=\[\s*(.*?)\]', content, re.DOTALL)
if match:
    cols_content = match.group(1)
    if 'ft.DataColumn(ft.Text("Acciones", weight="bold"))' not in cols_content:
        new_cols_content = cols_content.replace('ft.DataColumn(ft.Text("Total", weight="bold"), numeric=True),', 'ft.DataColumn(ft.Text("Total", weight="bold"), numeric=True),\n                ft.DataColumn(ft.Text("Acciones", weight="bold")),')
        # Adjust width
        new_cols_content = new_cols_content.replace('width=300', 'width=250')
        
        content = content.replace(cols_content, new_cols_content, 1)

# 2. Add btn_crear_manual to init
if 'self.btn_crear_manual =' not in content:
    add_btn_code = """
        self.btn_crear_manual = ft.ElevatedButton(
            text="Registrar Manual",
            icon=ft.icons.ADD_BOX,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=40,
            on_click=self.abrir_modal_crear_venta,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
"""
    # Insert after btn_clear_date
    content = content.replace('self.btn_clear_date = ft.IconButton(', add_btn_code + '\n        self.btn_clear_date = ft.IconButton(')

# 3. Add btn_crear_manual to row_filtros_ventas
if 'self.btn_crear_manual' not in content.split('row_filtros_ventas =')[1][:100]:
    content = content.replace("""        row_filtros_ventas = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date
        ])""", """        row_filtros_ventas = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            ft.Container(expand=True),
            self.btn_crear_manual
        ])""")

# 4. Restore the delete logic in _render_tabla_cargas
if 'btn_eliminar = ft.IconButton(' not in content:
    old_acciones_row = """            btn_accion = ft.ElevatedButton(
                text=texto_btn,
                icon=icon_btn,
                bgcolor=color_btn,
                color="white",
                height=30,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                on_click=lambda e, d=data, txt=txt_crono: self.on_accion_carga(e, d, txt)
            )
            
            acciones_row = ft.Row([btn_accion, txt_crono], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)"""
            
    new_acciones_row = """            btn_accion = ft.ElevatedButton(
                text=texto_btn,
                icon=icon_btn,
                bgcolor=color_btn,
                color="white",
                height=30,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                on_click=lambda e, d=data, txt=txt_crono: self.on_accion_carga(e, d, txt)
            )
            
            btn_eliminar = ft.IconButton(
                icon=ft.icons.DELETE_OUTLINED,
                icon_color="red",
                tooltip="Eliminar Carga",
                on_click=lambda e, d=data: self.on_eliminar_carga(d)
            )
            
            acciones_row = ft.Row([btn_accion, txt_crono, btn_eliminar], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER)"""
            
    content = content.replace(old_acciones_row, new_acciones_row)

with open("ui/views/ventas.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Ventas fixed")
