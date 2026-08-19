import re

with open("ui/views/ventas.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Reparar el Botón de Creación Manual
if "self.btn_crear_manual =" not in content:
    btn_crear_manual = """        self.btn_crear_manual = ft.ElevatedButton(
            text="Registrar Manual",
            icon=ft.icons.ADD_BOX,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=40,
            on_click=self.abrir_modal_crear_venta,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )"""
    content = content.replace("        self.btn_clear_date = ft.IconButton(", btn_crear_manual + "\n\n        self.btn_clear_date = ft.IconButton(")

# Reemplazar btn_nueva_venta por el nuevo arreglo (con el expand=True)
old_row_filtros = """        row_filtros_ventas = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            btn_nueva_venta
        ])"""
if old_row_filtros in content:
    new_row_filtros = """        row_filtros_ventas = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            ft.Container(expand=True),
            self.btn_crear_manual
        ])"""
    content = content.replace(old_row_filtros, new_row_filtros)
else:
    # Si btn_nueva_venta no estaba ahí, asegurar que ft.Container(expand=True) y self.btn_crear_manual estén:
    if "self.btn_crear_manual" not in content.split("row_filtros_ventas =")[1][:150]:
        content = re.sub(
            r'row_filtros_ventas = ft\.Row\(\[\s*self\.search_autocomplete,\s*self\.btn_date,\s*self\.btn_clear_date\s*\]\)',
            """row_filtros_ventas = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            ft.Container(expand=True),
            self.btn_crear_manual
        ])""",
            content
        )

# Eliminar referencia de btn_nueva_venta si estaba antes (limpieza)
content = re.sub(r'btn_nueva_venta = ft\.ElevatedButton\([\s\S]*?\)\s*', '', content)


# 2. Agregar Columna y Celdas de Acciones (Editar / Eliminar) en la Tabla principal
# Verificamos si no tiene Acciones en la principal (la que tiene IVA y Total)
match = re.search(r'columns=\[\s*ft\.DataColumn.*?ft\.DataColumn\(ft\.Text\("IVA".*?\].*?rows=\[\]', content, re.DOTALL)
if match:
    cols_content = match.group(0)
    if 'ft.DataColumn(ft.Text("Acciones"' not in cols_content:
        new_cols_content = cols_content.replace('ft.DataColumn(ft.Text("Total", weight="bold"), numeric=True),', 'ft.DataColumn(ft.Text("Total", weight="bold"), numeric=True),\n                ft.DataColumn(ft.Text("Acciones", weight="bold")),')
        # Reducir width si hace falta
        new_cols_content = new_cols_content.replace('width=300', 'width=250')
        content = content.replace(cols_content, new_cols_content, 1)

# Celda final en _fetch_data_worker()
# Asegurarse que están los IconButton de EDIT_OUTLINED y DELETE_OUTLINED
old_cell = """                    ft.DataCell(ft.Text(str_iva, color="grey")),
                    ft.DataCell(ft.Text(str_total, color="green", weight="bold")),
                ]"""
new_cell = """                    ft.DataCell(ft.Text(str_iva, color="grey")),
                    ft.DataCell(ft.Text(str_total, color="green", weight="bold")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.EDIT_OUTLINED,
                                icon_color="blue",
                                tooltip="Editar Venta",
                                on_click=lambda e, i=item: self.abrir_modal_editar_venta(i)
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINED,
                                icon_color="red",
                                tooltip="Eliminar Venta",
                                on_click=lambda e, i=item: self.confirmar_eliminar_venta(i)
                            )
                        ], spacing=0)
                    ),
                ]"""
if "Editar Venta" not in content and old_cell in content:
    content = content.replace(old_cell, new_cell)


# 3. Corregir la Instanciación de CustomAutoComplete en Modales
old_auto_init = """self.crud_codigo_insumo = CustomAutoComplete(
            options=[],
            width=350,
            label="Insumo (Buscar por Código o Nombre)",
            on_select=self._on_insumo_crud_select
        )"""
new_auto_init = """self.crud_codigo_insumo = CustomAutoComplete(
            hint_text="Buscar insumo (Código o Nombre)...",
            on_select=self._on_insumo_crud_select
        )
        self.crud_codigo_insumo.width = 350"""
content = content.replace(old_auto_init, new_auto_init)

# Si ya existía uno parecido pero con label, limpiar con regex
content = re.sub(r'self\.crud_codigo_insumo = CustomAutoComplete\(\s*hint_text="Buscar insumo.*?\n\s*on_select=self\._on_insumo_crud_select\s*\)', 
"""self.crud_codigo_insumo = CustomAutoComplete(
            hint_text="Buscar insumo (Código o Nombre)...",
            on_select=self._on_insumo_crud_select
        )""", content)

# 4. Asignar sugerencias correctamente en abrir_modal_crear_venta y editar_venta
# Para abrir_modal_crear_venta
content = re.sub(
    r'self\.crud_codigo_insumo\.options\s*=\s*\[f"\[\{i\[\'codigo_insumo\'\]\}\] \{i\[\'nombre\'\]\}" for i in insumos\]',
    """self.crud_codigo_insumo.suggestions = [
            {"key": i["codigo_insumo"], "value": f"[{i['codigo_insumo']}] {i['nombre']}"}
            for i in insumos
        ]""",
    content
)

# Para abrir_modal_editar_venta (por si acaso estaba separado)
# Arriba ya debería reemplazar todas las ocurrencias si son idénticas, pero Flet a veces formatea diferente.
# Así que la regex de arriba cubrirá todas las instancias donde asigne a .options de esa forma.

# Asegurarse que se usa .suggestions y no .options en todo ventas.py respecto a crud_codigo_insumo
content = content.replace(".options = [f", ".suggestions = [{'key': i['codigo_insumo'], 'value': f") # Fallback, pero el regex es mejor.

with open("ui/views/ventas.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Ventas fully refactored!")
