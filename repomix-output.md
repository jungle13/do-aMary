This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: **/*.md, **/*.txt, **/*.ps1, package.json, supabase/.temp/**
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
````
core/
  excel_manager.py
  gemini_parser.py
  supabase_client.py
scratch/
  refactor_layout.py
  refactor.py
supabase/
  .gitignore
  config.toml
ui/
  components/
    autocomplete.py
    forms.py
  layout/
    sidebar.py
  views/
    ajustes_inventario.py
    cierre_inventario.py
    compras.py
    conteo_inicial.py
    dashboard.py
    informes.py
    inventario.py
    login.py
    ventas.py
  app.py
.gitignore
append_crud.py
cargas_compras_locales.json
cargas_locales.json
config.py
fix_bugs.py
fix_compras_final.py
fix_ventas_final.py
main.py
openapi.json
Sistema_Dona_Mary.spec
supabase_schema.sql
update_compras.py
update_ventas.py
````

# Files

## File: append_crud.py
````python
with open("core/supabase_client.py", "a", encoding="utf-8") as f:
    f.write('''

    # --- CRUD COMPRAS INDIVIDUALES ---
    def update_compra_individual(self, id_compra, datos):
        """Actualiza un registro de compra individual por su UUID."""
        try:
            url = f"{self.url}/registro_compras?id_compra=eq.{id_compra}"
            res = self.session.patch(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en update_compra_individual: {ex}")
            return False

    def eliminar_compra_individual(self, id_compra):
        """Elimina un registro de compra individual de Supabase."""
        try:
            url = f"{self.url}/registro_compras?id_compra=eq.{id_compra}"
            res = self.session.delete(url, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en eliminar_compra_individual: {ex}")
            return False

    # --- CRUD VENTAS INDIVIDUALES ---
    def insert_venta_individual(self, datos):
        """Crea un registro de venta individual en Supabase."""
        try:
            url = f"{self.url}/registro_ventas"
            res = self.session.post(url, json=[datos], headers=self.headers, timeout=10)
            return res.status_code in (200, 201)
        except Exception as ex:
            print(f"Error en insert_venta_individual: {ex}")
            return False

    def update_venta_individual(self, id_venta, datos):
        """Actualiza un registro de venta individual por su UUID."""
        try:
            url = f"{self.url}/registro_ventas?id_venta=eq.{id_venta}"
            res = self.session.patch(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en update_venta_individual: {ex}")
            return False

    def eliminar_venta_individual(self, id_venta):
        """Elimina un registro de venta individual de Supabase."""
        try:
            url = f"{self.url}/registro_ventas?id_venta=eq.{id_venta}"
            res = self.session.delete(url, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en eliminar_venta_individual: {ex}")
            return False
''')
````

## File: fix_bugs.py
````python
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
````

## File: fix_compras_final.py
````python
import re

with open("ui/views/compras.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add "Acciones" column to FIRST table only
# We can do this by finding the first instance of 'columns=[' and replacing within it
match = re.search(r'columns=\[\s*(.*?)\]', content, re.DOTALL)
if match:
    cols_content = match.group(1)
    if 'ft.DataColumn(ft.Text("Acciones", weight="bold"))' not in cols_content:
        new_cols_content = cols_content.replace('ft.DataColumn(ft.Text("Costo Total", weight="bold"), numeric=True),', 'ft.DataColumn(ft.Text("Costo Total", weight="bold"), numeric=True),\n                ft.DataColumn(ft.Text("Acciones", weight="bold")),')
        # Adjust width
        new_cols_content = new_cols_content.replace('width=280', 'width=230')
        
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
            on_click=self.abrir_modal_crear_compra,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
"""
    # Insert after btn_clear_date
    content = content.replace('self.btn_clear_date = ft.IconButton(', add_btn_code + '\n        self.btn_clear_date = ft.IconButton(')

# 3. Add btn_crear_manual to row_filtros_compras
if 'self.btn_crear_manual' not in content.split('row_filtros_compras =')[1][:100]:
    content = content.replace("""        row_filtros_compras = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date
        ])""", """        row_filtros_compras = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            ft.Container(expand=True),
            self.btn_crear_manual
        ])""")

# 4. Restore the delete logic in _render_tabla_cargas
if 'btn_eliminar = ft.IconButton(' not in content:
    # Find _render_tabla_cargas row creation
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

with open("ui/views/compras.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Compras fixed")
````

## File: fix_ventas_final.py
````python
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
````

## File: update_compras.py
````python
import re

file_path = "ui/views/compras.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add "Acciones" column to data_table
if 'ft.DataColumn(ft.Text("Acciones", weight="bold"))' not in content:
    old_cols = """                ft.DataColumn(ft.Text("IVA", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Total", weight="bold"), numeric=True),
            ],"""
    new_cols = """                ft.DataColumn(ft.Text("IVA", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Total", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],"""
    content = content.replace(old_cols, new_cols)
    
    # Adjust width to fit the actions column
    content = content.replace('ft.DataColumn(ft.Container(content=ft.Text("Nombre", weight="bold"), width=280)),', 'ft.DataColumn(ft.Container(content=ft.Text("Nombre", weight="bold"), width=230)),')

# 2. Add Edit/Delete buttons in _fetch_data_worker
old_row = """                    ft.DataCell(ft.Text(str_costo_unit)),
                    ft.DataCell(ft.Text(str_iva)),
                    ft.DataCell(ft.Text(str_costo_tot, color="blue", weight="bold")),
                ]
            )
            self.data_table.rows.append(row)"""
new_row = """                    ft.DataCell(ft.Text(str_costo_unit)),
                    ft.DataCell(ft.Text(str_iva)),
                    ft.DataCell(ft.Text(str_costo_tot, color="blue", weight="bold")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT_OUTLINED, icon_color="blue", tooltip="Editar", on_click=lambda e, i=item: self.abrir_modal_editar_compra(i)),
                            ft.IconButton(icon=ft.icons.DELETE_OUTLINED, icon_color="red", tooltip="Eliminar", on_click=lambda e, i=item: self.confirmar_eliminar_compra(i))
                        ], spacing=0)
                    ),
                ]
            )
            self.data_table.rows.append(row)"""
content = content.replace(old_row, new_row)

# 3. Add CRUD methods
if "def abrir_modal_editar_compra(self, item):" not in content:
    crud_methods = """
    # --- INICIO CRUD MANUAL COMPRAS ---
    def _construir_modal_crud(self):
        self.crud_codigo_insumo = CustomAutoComplete(
            options=[],
            width=350,
            label="Insumo (Buscar por Código o Nombre)",
            on_select=self._on_insumo_crud_select
        )
        self.crud_fecha = ft.TextField(label="Fecha (YYYY-MM-DD)", width=150)
        self.crud_ea = ft.TextField(label="N° Entrada (EA)", width=150)
        self.crud_factura = ft.TextField(label="N° Factura", width=150)
        self.crud_proveedor = ft.TextField(label="Proveedor", width=250)
        self.crud_cantidad = ft.TextField(label="Cantidad", width=120, on_change=self._calc_tot_crud)
        self.crud_costo_unit = ft.TextField(label="Costo Unit.", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_iva = ft.TextField(label="IVA", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_total_lbl = ft.Text("$ 0.00", size=20, weight="bold", color="blue700")
        self.crud_item_id = None
        
        self.dlg_crud = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar Compra"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    self.crud_codigo_insumo,
                    ft.Row([self.crud_fecha, self.crud_ea, self.crud_factura]),
                    self.crud_proveedor,
                    ft.Row([self.crud_cantidad, self.crud_costo_unit, self.crud_iva]),
                    ft.Divider(height=10),
                    ft.Row([ft.Text("Costo Total:", size=16, weight="bold"), self.crud_total_lbl])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_crud()),
                ft.ElevatedButton("Guardar", bgcolor="blue700", color="white", on_click=self.guardar_compra_formulario)
            ]
        )

    def _on_insumo_crud_select(self, e):
        pass

    def _calc_tot_crud(self, e=None):
        try:
            cant = float(self.crud_cantidad.value or 0)
            cost = float(self.crud_costo_unit.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * cost) + iva
            self.crud_total_lbl.value = f"$ {tot:,.2f}"
            self.safe_update()
        except ValueError:
            self.crud_total_lbl.value = "$ 0.00"
            self.safe_update()

    def _cerrar_crud(self):
        self.dlg_crud.open = False
        self.safe_update()

    def abrir_modal_crear_compra(self, e=None):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.options = [f"[{i['codigo_insumo']}] {i['nombre']}" for i in insumos]
        
        self.crud_item_id = None
        self.dlg_crud.title.value = "Registrar Nueva Compra"
        self.crud_codigo_insumo.value = ""
        self.crud_fecha.value = datetime.date.today().strftime("%Y-%m-%d")
        self.crud_ea.value = ""
        self.crud_factura.value = ""
        self.crud_proveedor.value = ""
        self.crud_cantidad.value = ""
        self.crud_costo_unit.value = ""
        self.crud_iva.value = "0"
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def abrir_modal_editar_compra(self, item):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.options = [f"[{i['codigo_insumo']}] {i['nombre']}" for i in insumos]
        
        self.crud_item_id = item.get("id_compra")
        self.dlg_crud.title.value = "Editar Compra"
        
        cod = item.get("codigo_insumo", "")
        nom = item.get("catalogo_insumos", {}).get("nombre", "")
        self.crud_codigo_insumo.value = f"[{cod}] {nom}" if cod else ""
        self.crud_fecha.value = str(item.get("fecha") or "")[:10]
        self.crud_ea.value = str(item.get("numero_entrada") or "")
        self.crud_factura.value = str(item.get("numero_factura") or "")
        self.crud_proveedor.value = str(item.get("proveedor") or "")
        self.crud_cantidad.value = str(item.get("cantidad") or 0)
        self.crud_costo_unit.value = str(item.get("costo_unitario") or 0)
        self.crud_iva.value = str(item.get("iva") or item.get("valor_iva") or 0)
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def guardar_compra_formulario(self, e):
        cod_raw = self.crud_codigo_insumo.value
        if not cod_raw or "[" not in cod_raw or "]" not in cod_raw:
            self.page.snack_bar = ft.SnackBar(ft.Text("Selecciona un insumo válido del listado."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        codigo_insumo = cod_raw.split("[")[1].split("]")[0]
        
        try:
            cant = float(self.crud_cantidad.value or 0)
            costo = float(self.crud_costo_unit.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * costo) + iva
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Revisa los valores numéricos ingresados."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        datos = {
            "fecha": self.crud_fecha.value,
            "numero_entrada": self.crud_ea.value,
            "numero_factura": self.crud_factura.value,
            "proveedor": self.crud_proveedor.value,
            "codigo_insumo": codigo_insumo,
            "cantidad": cant,
            "costo_unitario": costo,
            "iva": iva,
            "valor_iva": iva,
            "costo_total": tot
        }
        
        if self.crud_item_id:
            # Edit
            ok = self.db.update_compra_individual(self.crud_item_id, datos)
            msg = "Compra actualizada exitosamente."
        else:
            # Create
            datos["estado_registro"] = "VÁLIDO"
            ok = self.db.insert_compras([datos])
            msg = "Compra registrada exitosamente."
            
        if ok:
            self._cerrar_crud()
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green")
            self.page.snack_bar.open = True
            self.load_data()
            self.load_summary()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar la compra en la BD."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()

    def confirmar_eliminar_compra(self, item):
        id_compra = item.get("id_compra")
        cant = float(item.get("cantidad") or 0)
        insumo = item.get("catalogo_insumos", {}).get("nombre", "Desconocido")
        ea = item.get("numero_entrada") or item.get("numero_factura") or "S/D"
        tot = float(item.get("costo_total") or 0)
        
        def do_eliminar(e):
            dlg.open = False
            self.safe_update()
            if self.db.eliminar_compra_individual(id_compra):
                self.page.snack_bar = ft.SnackBar(ft.Text("Compra eliminada y stock revertido."), bgcolor="green")
                self.page.snack_bar.open = True
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar la compra en la BD."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                ft.Text("Eliminar Registro de Compra", color="red700")
            ]),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(f"Insumo: {insumo}", weight="bold"),
                    ft.Text(f"N° Documento: {ea}"),
                    ft.Text(f"Cantidad: {cant:g} unds"),
                    ft.Text(f"Costo Total: ${tot:,.2f}", color="blue700", weight="bold"),
                    ft.Divider(),
                    ft.Text(
                        f"⚠️ ADVERTENCIA: Al eliminar este registro de compra, se restarán {cant:g} unidades del inventario disponible y se ajustará el histórico financiero.",
                        color="red900", weight="bold"
                    )
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), self.safe_update())),
                ft.ElevatedButton("Eliminar Definitivamente", bgcolor="red700", color="white", on_click=do_eliminar)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()
    # --- FIN CRUD MANUAL COMPRAS ---
"""
    content = content + crud_methods

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Compras updated")
````

## File: update_ventas.py
````python
import re

file_path = "ui/views/ventas.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add "Acciones" column to data_table
if 'ft.DataColumn(ft.Text("Acciones", weight="bold"))' not in content:
    old_cols = """                ft.DataColumn(ft.Text("IVA", weight="bold")),
                ft.DataColumn(ft.Text("Total", weight="bold"), numeric=True),
            ],"""
    new_cols = """                ft.DataColumn(ft.Text("IVA", weight="bold")),
                ft.DataColumn(ft.Text("Total", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],"""
    content = content.replace(old_cols, new_cols)
    
    # Adjust width to fit the actions column
    content = content.replace('ft.DataColumn(ft.Container(content=ft.Text("Nombre / Descripción", weight="bold"), width=300)),', 'ft.DataColumn(ft.Container(content=ft.Text("Nombre / Descripción", weight="bold"), width=250)),')

# 2. Add Edit/Delete buttons in _fetch_data_worker
old_row = """                    ft.DataCell(ft.Text(str_iva, color="grey")),
                    ft.DataCell(ft.Text(str_total, color="green", weight="bold")),
                ]
            )
            self.data_table.rows.append(row)"""
new_row = """                    ft.DataCell(ft.Text(str_iva, color="grey")),
                    ft.DataCell(ft.Text(str_total, color="green", weight="bold")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT_OUTLINED, icon_color="blue", tooltip="Editar", on_click=lambda e, i=item: self.abrir_modal_editar_venta(i)),
                            ft.IconButton(icon=ft.icons.DELETE_OUTLINED, icon_color="red", tooltip="Eliminar", on_click=lambda e, i=item: self.confirmar_eliminar_venta(i))
                        ], spacing=0)
                    ),
                ]
            )
            self.data_table.rows.append(row)"""
content = content.replace(old_row, new_row)

# 3. Add CRUD methods
if "def abrir_modal_editar_venta(self, item):" not in content:
    crud_methods = """
    # --- INICIO CRUD MANUAL VENTAS ---
    def _construir_modal_crud(self):
        self.crud_codigo_insumo = CustomAutoComplete(
            options=[],
            width=350,
            label="Insumo (Buscar por Código o Nombre)",
            on_select=self._on_insumo_crud_select
        )
        self.crud_fecha = ft.TextField(label="Fecha (YYYY-MM-DD)", width=150)
        self.crud_factura = ft.TextField(label="N° Factura / Remisión", width=180)
        self.crud_tipo_doc = ft.Dropdown(label="Tipo Doc.", options=[ft.dropdown.Option("Remisión"), ft.dropdown.Option("Factura POS")], width=150)
        
        self.crud_cantidad = ft.TextField(label="Cantidad", width=120, on_change=self._calc_tot_crud)
        self.crud_precio_unit = ft.TextField(label="Precio Unit.", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_descuento = ft.TextField(label="Descuento", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_iva = ft.TextField(label="IVA", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        
        self.crud_total_lbl = ft.Text("$ 0.00", size=20, weight="bold", color="green700")
        self.crud_item_id = None
        
        self.dlg_crud = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar Venta"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    self.crud_codigo_insumo,
                    ft.Row([self.crud_fecha, self.crud_factura, self.crud_tipo_doc]),
                    ft.Row([self.crud_cantidad, self.crud_precio_unit]),
                    ft.Row([self.crud_descuento, self.crud_iva]),
                    ft.Divider(height=10),
                    ft.Row([ft.Text("Total Venta:", size=16, weight="bold"), self.crud_total_lbl])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_crud()),
                ft.ElevatedButton("Guardar", bgcolor="green700", color="white", on_click=self.guardar_venta_formulario)
            ]
        )

    def _on_insumo_crud_select(self, e):
        pass

    def _calc_tot_crud(self, e=None):
        try:
            cant = float(self.crud_cantidad.value or 0)
            precio = float(self.crud_precio_unit.value or 0)
            desc = float(self.crud_descuento.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * precio) + iva - desc
            self.crud_total_lbl.value = f"$ {tot:,.2f}"
            self.safe_update()
        except ValueError:
            self.crud_total_lbl.value = "$ 0.00"
            self.safe_update()

    def _cerrar_crud(self):
        self.dlg_crud.open = False
        self.safe_update()

    def abrir_modal_crear_venta(self, e=None):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.options = [f"[{i['codigo_insumo']}] {i['nombre']}" for i in insumos]
        
        self.crud_item_id = None
        self.dlg_crud.title.value = "Registrar Nueva Venta"
        self.crud_codigo_insumo.value = ""
        self.crud_fecha.value = datetime.date.today().strftime("%Y-%m-%d")
        self.crud_factura.value = ""
        self.crud_tipo_doc.value = "Remisión"
        self.crud_cantidad.value = ""
        self.crud_precio_unit.value = ""
        self.crud_descuento.value = "0"
        self.crud_iva.value = "0"
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def abrir_modal_editar_venta(self, item):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.options = [f"[{i['codigo_insumo']}] {i['nombre']}" for i in insumos]
        
        self.crud_item_id = item.get("id_venta")
        self.dlg_crud.title.value = "Editar Venta"
        
        cod = item.get("codigo_insumo", "")
        nom_bd = item.get("catalogo_insumos", {}).get("nombre", "")
        nom_desc = item.get("descripcion", "")
        nom_final = nom_bd if nom_bd else nom_desc
        
        self.crud_codigo_insumo.value = f"[{cod}] {nom_final}" if cod else ""
        self.crud_fecha.value = str(item.get("fecha") or "")[:10]
        self.crud_factura.value = str(item.get("factura_no") or "")
        self.crud_tipo_doc.value = str(item.get("tipo_documento") or "Remisión")
        
        cant = float(item.get("cantidad") or 0)
        self.crud_cantidad.value = str(int(cant)) if cant.is_integer() else str(cant)
        
        self.crud_precio_unit.value = str(item.get("subtotal") or 0)
        self.crud_descuento.value = str(item.get("descuento") or 0)
        self.crud_iva.value = str(item.get("iva") or 0)
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def guardar_venta_formulario(self, e):
        cod_raw = self.crud_codigo_insumo.value
        if not cod_raw or "[" not in cod_raw or "]" not in cod_raw:
            self.page.snack_bar = ft.SnackBar(ft.Text("Selecciona un insumo válido del listado."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        codigo_insumo = cod_raw.split("[")[1].split("]")[0]
        
        try:
            cant = float(self.crud_cantidad.value or 0)
            precio = float(self.crud_precio_unit.value or 0)
            desc = float(self.crud_descuento.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * precio) + iva - desc
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Revisa los valores numéricos ingresados."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        datos = {
            "fecha": self.crud_fecha.value,
            "factura_no": self.crud_factura.value,
            "tipo_documento": self.crud_tipo_doc.value,
            "codigo_insumo": codigo_insumo,
            "cantidad": cant,
            "subtotal": precio,
            "descuento": desc,
            "iva": iva,
            "total": tot
        }
        
        if self.crud_item_id:
            # Edit
            ok = self.db.update_venta_individual(self.crud_item_id, datos)
            msg = "Venta actualizada exitosamente."
        else:
            # Create
            datos["estado_registro"] = "VÁLIDO"
            ok = self.db.insert_venta_individual(datos)
            msg = "Venta registrada exitosamente."
            
        if ok:
            self._cerrar_crud()
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green")
            self.page.snack_bar.open = True
            self.load_data()
            self.load_summary()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar la venta en la BD."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()

    def confirmar_eliminar_venta(self, item):
        id_venta = item.get("id_venta")
        cant = float(item.get("cantidad") or 0)
        
        cat_info = item.get("catalogo_insumos", {})
        nom_bd = cat_info.get("nombre") if isinstance(cat_info, dict) else None
        insumo = nom_bd or item.get("descripcion", "Desconocido")
        
        fact = item.get("factura_no") or "S/D"
        tot = float(item.get("total") or 0)
        
        def do_eliminar(e):
            dlg.open = False
            self.safe_update()
            if self.db.eliminar_venta_individual(id_venta):
                self.page.snack_bar = ft.SnackBar(ft.Text("Venta eliminada y stock reincorporado."), bgcolor="green")
                self.page.snack_bar.open = True
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar la venta en la BD."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                ft.Text("Eliminar Registro de Venta", color="red700")
            ]),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(f"Insumo: {insumo}", weight="bold"),
                    ft.Text(f"N° Factura: {fact}"),
                    ft.Text(f"Cantidad: {cant:g} unds"),
                    ft.Text(f"Total Venta: ${tot:,.2f}", color="green700", weight="bold"),
                    ft.Divider(),
                    ft.Text(
                        f"⚠️ ADVERTENCIA: Al eliminar este registro de venta, se devolverán {cant:g} unidades al inventario disponible (reincorporación de stock) y se restará del histórico de ingresos.",
                        color="red900", weight="bold"
                    )
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), self.safe_update())),
                ft.ElevatedButton("Eliminar Definitivamente", bgcolor="red700", color="white", on_click=do_eliminar)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()
    # --- FIN CRUD MANUAL VENTAS ---
"""
    content = content + crud_methods

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Ventas updated")
````

## File: core/excel_manager.py
````python
import pandas as pd
import os

class ExcelManager:
    def __init__(self, filepath="Sistema_Inventario_Abarrotes_Desechabes_Mary_v2_Procesado.xlsx"):
        self.filepath = filepath
        
    def verify_file(self):
        """Verifica si el archivo Excel existe."""
        return os.path.exists(self.filepath)
        
    # Aquí irán los métodos para leer hojas (Compras, Ventas, etc.) 
    # y escribir datos sincronizados desde Supabase.
````

## File: scratch/refactor_layout.py
````python
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
````

## File: scratch/refactor.py
````python
import re

path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\core\supabase_client.py'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
current_method = 'unknown'

for line in lines:
    # Update current method
    m_def = re.match(r'^\s*def\s+([a-zA-Z0-9_]+)\(', line)
    if m_def:
        current_method = m_def.group(1)
        
    # Inject timeout
    new_line = line
    if 'self.session.' in new_line and ('get(' in new_line or 'post(' in new_line or 'patch(' in new_line or 'delete(' in new_line or 'put(' in new_line):
        if 'timeout=' not in new_line:
            # Reemplazar la última ocurrencia de ')' con ', timeout=10)'
            # Dado que hay una llamada por línea, podemos hacer rsplit
            parts = new_line.rsplit(')', 1)
            if len(parts) == 2:
                new_line = parts[0] + ', timeout=10)' + parts[1]

    # Inject exception
    m_exc = re.match(r'^(\s*)except Exception as e:', new_line)
    if m_exc:
        indent = m_exc.group(1)
        new_lines.append(f'{indent}except requests.exceptions.RequestException as req_e:\n')
        new_lines.append(f'{indent}    print(f"Error de conexión con Supabase en {current_method}: el servidor no responde")\n')
        
    new_lines.append(new_line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done!')
````

## File: supabase/.gitignore
````
# Supabase
.branches
.temp

# dotenvx
.env.keys
.env.local
.env.*.local
````

## File: supabase/config.toml
````toml
# For detailed configuration reference documentation, visit:
# https://supabase.com/docs/guides/local-development/cli/config
# A string used to distinguish different Supabase projects on the same host. Defaults to the
# working directory name when running `supabase init`.
project_id = "do-aMary"

[api]
enabled = true
# Port to use for the API URL.
port = 54321
# Schemas to expose in your API. Tables, views and stored procedures in this schema will get API
# endpoints. `public` and `graphql_public` schemas are included by default.
schemas = ["public", "graphql_public"]
# Extra schemas to add to the search_path of every request.
extra_search_path = ["public", "extensions"]
# The maximum number of rows returns from a view, table, or stored procedure. Limits payload size
# for accidental or malicious requests.
max_rows = 1000
# Controls whether new tables, views, sequences and functions created in the `public` schema by
# `postgres` are reachable through the Data API roles (`anon`, `authenticated`, `service_role`)
# without explicit GRANTs. When unset, new entities are NOT auto-exposed, matching the new cloud
# default. Set to `true` to keep the legacy behaviour of auto-exposing new entities; this is
# deprecated and the field is removed on 2026-10-30 once the always-revoked behaviour is permanent.
# auto_expose_new_tables = true

[api.tls]
# Enable HTTPS endpoints locally using a self-signed certificate.
enabled = false
# Paths to self-signed certificate pair.
# cert_path = "../certs/my-cert.pem"
# key_path = "../certs/my-key.pem"

[db]
# Port to use for the local database URL.
port = 54322
# Port used by db diff command to initialize the shadow database.
shadow_port = 54320
# Maximum amount of time to wait for health check when starting the local database.
health_timeout = "2m"
# The database major version to use. This has to be the same as your remote database's. Run `SHOW
# server_version;` on the remote database to check.
major_version = 17

[db.pooler]
enabled = false
# Port to use for the local connection pooler.
port = 54329
# Specifies when a server connection can be reused by other clients.
# Configure one of the supported pooler modes: `transaction`, `session`.
pool_mode = "transaction"
# How many server connections to allow per user/database pair.
default_pool_size = 20
# Maximum number of client connections allowed.
max_client_conn = 100

# [db.vault]
# secret_key = "env(SECRET_VALUE)"

[db.migrations]
# If disabled, migrations will be skipped during a db push or reset.
enabled = true
# Specifies an ordered list of schema files, directories, or glob patterns that describe your database.
# Supports paths relative to supabase directory: "./schemas/*.sql", "./database".
schema_paths = []

[db.seed]
# If enabled, seeds the database after migrations during a db reset.
enabled = true
# Specifies an ordered list of seed files to load during db reset.
# Supports glob patterns relative to supabase directory: "./seeds/*.sql"
sql_paths = ["./seed.sql"]

[db.network_restrictions]
# Enable management of network restrictions.
enabled = false
# List of IPv4 CIDR blocks allowed to connect to the database.
# Defaults to allow all IPv4 connections. Set empty array to block all IPs.
allowed_cidrs = ["0.0.0.0/0"]
# List of IPv6 CIDR blocks allowed to connect to the database.
# Defaults to allow all IPv6 connections. Set empty array to block all IPs.
allowed_cidrs_v6 = ["::/0"]

# Uncomment to reject non-secure connections to the database.
# [db.ssl_enforcement]
# enabled = true

[realtime]
enabled = true
# Bind realtime via either IPv4 or IPv6. (default: IPv4)
# ip_version = "IPv6"
# The maximum length in bytes of HTTP request headers. (default: 4096)
# max_header_length = 4096

[studio]
enabled = true
# Port to use for Supabase Studio.
port = 54323
# External URL of the API server that frontend connects to.
api_url = "http://127.0.0.1"
# OpenAI API Key to use for Supabase AI in the Supabase Studio.
openai_api_key = "env(OPENAI_API_KEY)"

# Email testing server. Emails sent with the local dev setup are not actually sent - rather, they
# are monitored, and you can view the emails that would have been sent from the web interface.
[local_smtp]
enabled = true
# Port to use for the email testing server web interface.
port = 54324
# Uncomment to expose additional ports for testing user applications that send emails.
# smtp_port = 54325
# pop3_port = 54326
# admin_email = "admin@email.com"
# sender_name = "Admin"

[storage]
enabled = true
# The maximum file size allowed (e.g. "5MB", "500KB").
file_size_limit = "50MiB"

# Uncomment to configure local storage buckets
# [storage.buckets.images]
# public = false
# file_size_limit = "50MiB"
# allowed_mime_types = ["image/png", "image/jpeg"]
# objects_path = "./images"

# Allow connections via S3 compatible clients
[storage.s3_protocol]
enabled = true

# Image transformation API is available to Supabase Pro plan.
# [storage.image_transformation]
# enabled = true

# Store analytical data in S3 for running ETL jobs over Iceberg Catalog
# This feature is only available on the hosted platform.
[storage.analytics]
enabled = false
max_namespaces = 5
max_tables = 10
max_catalogs = 2

# Analytics Buckets is available to Supabase Pro plan.
# [storage.analytics.buckets.my-warehouse]

# Store vector embeddings in S3 for large and durable datasets
[storage.vector]
enabled = true
max_buckets = 10
max_indexes = 5

# Vector Buckets is available to Supabase Pro plan.
# [storage.vector.buckets.documents-openai]

[auth]
enabled = true
# The base URL of your website. Used as an allow-list for redirects and for constructing URLs used
# in emails.
site_url = "http://127.0.0.1:3000"
# The public URL that Auth serves on. Defaults to the API external URL with `/auth/v1` appended.
# external_url = ""
# A list of *exact* URLs that auth providers are permitted to redirect to post authentication.
additional_redirect_urls = ["https://127.0.0.1:3000"]
# How long tokens are valid for, in seconds. Defaults to 3600 (1 hour), maximum 604,800 (1 week).
jwt_expiry = 3600
# JWT issuer URL. If not set, defaults to auth.external_url.
# jwt_issuer = ""
# Path to JWT signing key. DO NOT commit your signing keys file to git.
# signing_keys_path = "./signing_keys.json"
# If disabled, the refresh token will never expire.
enable_refresh_token_rotation = true
# Allows refresh tokens to be reused after expiry, up to the specified interval in seconds.
# Requires enable_refresh_token_rotation = true.
refresh_token_reuse_interval = 10
# Allow/disallow new user signups to your project.
enable_signup = true
# Allow/disallow anonymous sign-ins to your project.
enable_anonymous_sign_ins = false
# Allow/disallow testing manual linking of accounts
enable_manual_linking = false
# Passwords shorter than this value will be rejected as weak. Minimum 6, recommended 8 or more.
minimum_password_length = 6
# Passwords that do not meet the following requirements will be rejected as weak. Supported values
# are: `letters_digits`, `lower_upper_letters_digits`, `lower_upper_letters_digits_symbols`
password_requirements = ""

# Configure passkey sign-ins.
# [auth.passkey]
# enabled = false

# Configure WebAuthn relying party settings (required when passkey is enabled).
# [auth.webauthn]
# rp_display_name = "Supabase"
# rp_id = "localhost"
# rp_origins = ["http://127.0.0.1:3000"]

[auth.rate_limit]
# Number of emails that can be sent per hour. Requires auth.email.smtp to be enabled.
email_sent = 2
# Number of SMS messages that can be sent per hour. Requires auth.sms to be enabled.
sms_sent = 30
# Number of anonymous sign-ins that can be made per hour per IP address. Requires enable_anonymous_sign_ins = true.
anonymous_users = 30
# Number of sessions that can be refreshed in a 5 minute interval per IP address.
token_refresh = 150
# Number of sign up and sign-in requests that can be made in a 5 minute interval per IP address (excludes anonymous users).
sign_in_sign_ups = 30
# Number of OTP / Magic link verifications that can be made in a 5 minute interval per IP address.
token_verifications = 30
# Number of Web3 logins that can be made in a 5 minute interval per IP address.
web3 = 30

# Configure one of the supported captcha providers: `hcaptcha`, `turnstile`.
# [auth.captcha]
# enabled = true
# provider = "hcaptcha"
# secret = ""

[auth.email]
# Allow/disallow new user signups via email to your project.
enable_signup = true
# If enabled, a user will be required to confirm any email change on both the old, and new email
# addresses. If disabled, only the new email is required to confirm.
double_confirm_changes = true
# If enabled, users need to confirm their email address before signing in.
enable_confirmations = false
# If enabled, users will need to reauthenticate or have logged in recently to change their password.
secure_password_change = false
# Controls the minimum amount of time that must pass before sending another signup confirmation or password reset email.
max_frequency = "1s"
# Number of characters used in the email OTP.
otp_length = 6
# Number of seconds before the email OTP expires (defaults to 1 hour).
otp_expiry = 3600

# Use a production-ready SMTP server
# [auth.email.smtp]
# enabled = true
# host = "smtp.sendgrid.net"
# port = 587
# user = "apikey"
# pass = "env(SENDGRID_API_KEY)"
# admin_email = "admin@email.com"
# sender_name = "Admin"

# Uncomment to customize email template
# [auth.email.template.invite]
# subject = "You have been invited"
# content_path = "./supabase/templates/invite.html"

# Uncomment to customize notification email template
# [auth.email.notification.password_changed]
# enabled = true
# subject = "Your password has been changed"
# content_path = "./templates/password_changed_notification.html"

[auth.sms]
# Allow/disallow new user signups via SMS to your project.
enable_signup = false
# If enabled, users need to confirm their phone number before signing in.
enable_confirmations = false
# Template for sending OTP to users
template = "Your code is {{ .Code }}"
# Controls the minimum amount of time that must pass before sending another sms otp.
max_frequency = "5s"

# Use pre-defined map of phone number to OTP for testing.
# [auth.sms.test_otp]
# 4152127777 = "123456"

# Configure logged in session timeouts.
# [auth.sessions]
# Force log out after the specified duration.
# timebox = "24h"
# Force log out if the user has been inactive longer than the specified duration.
# inactivity_timeout = "8h"

# This hook runs before a new user is created and allows developers to reject the request based on the incoming user object.
# [auth.hook.before_user_created]
# enabled = true
# uri = "pg-functions://postgres/auth/before-user-created-hook"

# This hook runs before a token is issued and allows you to add additional claims based on the authentication method used.
# [auth.hook.custom_access_token]
# enabled = true
# uri = "pg-functions://<database>/<schema>/<hook_name>"

# Configure one of the supported SMS providers: `twilio`, `twilio_verify`, `messagebird`, `textlocal`, `vonage`.
[auth.sms.twilio]
enabled = false
account_sid = ""
message_service_sid = ""
# DO NOT commit your Twilio auth token to git. Use environment variable substitution instead:
auth_token = "env(SUPABASE_AUTH_SMS_TWILIO_AUTH_TOKEN)"

# Multi-factor-authentication is available to Supabase Pro plan.
[auth.mfa]
# Control how many MFA factors can be enrolled at once per user.
max_enrolled_factors = 10

# Control MFA via App Authenticator (TOTP)
[auth.mfa.totp]
enroll_enabled = false
verify_enabled = false

# Configure MFA via Phone Messaging
[auth.mfa.phone]
enroll_enabled = false
verify_enabled = false
otp_length = 6
template = "Your code is {{ .Code }}"
max_frequency = "5s"

# Configure MFA via WebAuthn
# [auth.mfa.web_authn]
# enroll_enabled = true
# verify_enabled = true

# Use an external OAuth provider. The full list of providers are: `apple`, `azure`, `bitbucket`,
# `discord`, `facebook`, `github`, `gitlab`, `google`, `keycloak`, `linkedin_oidc`, `notion`, `twitch`,
# `twitter`, `x`, `slack`, `spotify`, `workos`, `zoom`.
[auth.external.apple]
enabled = false
client_id = ""
# DO NOT commit your OAuth provider secret to git. Use environment variable substitution instead:
secret = "env(SUPABASE_AUTH_EXTERNAL_APPLE_SECRET)"
# Overrides the default auth callback URL derived from auth.external_url.
redirect_uri = ""
# Overrides the default auth provider URL. Used to support self-hosted gitlab, single-tenant Azure,
# or any other third-party OIDC providers.
url = ""
# If enabled, the nonce check will be skipped. Required for local sign in with Google auth.
skip_nonce_check = false
# If enabled, it will allow the user to successfully authenticate when the provider does not return an email address.
email_optional = false

# Allow Solana wallet holders to sign in to your project via the Sign in with Solana (SIWS, EIP-4361) standard.
# You can configure "web3" rate limit in the [auth.rate_limit] section and set up [auth.captcha] if self-hosting.
[auth.web3.solana]
enabled = false

# Use Firebase Auth as a third-party provider alongside Supabase Auth.
[auth.third_party.firebase]
enabled = false
# project_id = "my-firebase-project"

# Use Auth0 as a third-party provider alongside Supabase Auth.
[auth.third_party.auth0]
enabled = false
# tenant = "my-auth0-tenant"
# tenant_region = "us"

# Use AWS Cognito (Amplify) as a third-party provider alongside Supabase Auth.
[auth.third_party.aws_cognito]
enabled = false
# user_pool_id = "my-user-pool-id"
# user_pool_region = "us-east-1"

# Use Clerk as a third-party provider alongside Supabase Auth.
[auth.third_party.clerk]
enabled = false
# Obtain from https://clerk.com/setup/supabase
# domain = "example.clerk.accounts.dev"

# OAuth server configuration
[auth.oauth_server]
# Enable OAuth server functionality
enabled = false
# Path for OAuth consent flow UI
authorization_url_path = "/oauth/consent"
# Allow dynamic client registration
allow_dynamic_registration = false

[edge_runtime]
enabled = true
# Supported request policies: `oneshot`, `per_worker`.
# `per_worker` (default) — enables hot reload during local development.
# `oneshot` — fallback mode if hot reload causes issues (e.g. in large repos or with symlinks).
policy = "per_worker"
# Port to attach the Chrome inspector for debugging edge functions.
inspector_port = 8083
# The Deno major version to use.
deno_version = 2

# [edge_runtime.secrets]
# secret_key = "env(SECRET_VALUE)"

[analytics]
enabled = true
port = 54327
# Configure one of the supported backends: `postgres`, `bigquery`.
backend = "postgres"

# Experimental features may be deprecated any time
[experimental]
# Configures Postgres storage engine to use OrioleDB (S3)
orioledb_version = ""
# Configures S3 bucket URL, eg. <bucket_name>.s3-<region>.amazonaws.com
s3_host = "env(S3_HOST)"
# Configures S3 bucket region, eg. us-east-1
s3_region = "env(S3_REGION)"
# Configures AWS_ACCESS_KEY_ID for S3 bucket
s3_access_key = "env(S3_ACCESS_KEY)"
# Configures AWS_SECRET_ACCESS_KEY for S3 bucket
s3_secret_key = "env(S3_SECRET_KEY)"

# pg-delta is the schema diff engine for db diff / db pull / db remote commit.
# Set enabled = false to fall back to the legacy migra engine.
[experimental.pgdelta]
enabled = true
# Directory under `supabase/` where declarative files are written.
# declarative_schema_path = "./database"
# JSON string passed through to pg-delta SQL formatting.
# format_options = "{\"keywordCase\":\"upper\",\"indent\":2,\"maxWidth\":80,\"commaStyle\":\"trailing\"}"
````

## File: ui/components/autocomplete.py
````python
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
````

## File: ui/components/forms.py
````python
import flet as ft
from config import Config

def crear_input_estandar(label, icon=None, password=False, multiline=False, on_change=None):
    """
    Fábrica (Factory) para crear campos de texto estandarizados en toda la app.
    Cualquier cambio global en bordes, colores o tamaño se hace aquí y afecta todo el sistema.
    """
    return ft.TextField(
        label=label,
        prefix_icon=icon,
        password=password,
        multiline=multiline,
        on_change=on_change,
        border_radius=8,
        border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
        focused_border_color=Config.COLOR_PRIMARY,
        cursor_color=Config.COLOR_PRIMARY,
        text_size=14,
        content_padding=15
    )

def crear_boton_primario(text, icon=None, on_click=None):
    """
    Fábrica para botones primarios con el tema Azul Oscuro.
    """
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            padding=ft.padding.symmetric(horizontal=20, vertical=15)
        )
    )
````

## File: ui/views/login.py
````python
import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
import time
import threading

class LoginView(ft.Container):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.db = SupabaseClient()
        self.expand = True
        self.alignment = ft.alignment.center
        
        # Fondo Azul Oscuro Institucional
        self.bgcolor = Config.COLOR_PRIMARY

        # Campos de texto estilizados
        self.txt_usuario = ft.TextField(
            label="Usuario",
            prefix_icon=ft.icons.PERSON_OUTLINED,
            border_radius=10,
            height=45,
            dense=True,
            text_size=13,
            bgcolor="#f8f9fa",
            border_color="#e0e0e0",
            focused_border_color=Config.COLOR_PRIMARY,
            focused_bgcolor="white"
        )
        self.txt_clave = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            border_radius=10,
            height=45,
            dense=True,
            text_size=13,
            bgcolor="#f8f9fa",
            border_color="#e0e0e0",
            focused_border_color=Config.COLOR_PRIMARY,
            focused_bgcolor="white",
            on_submit=self.autenticar
        )
        self.lbl_error = ft.Text("", color="red700", size=12, visible=False, weight="bold")
        self.progress = ft.ProgressBar(width=300, color=Config.COLOR_PRIMARY, visible=False)

        self.btn_ingresar = ft.ElevatedButton(
            "Iniciar Sesión",
            icon=ft.icons.LOGIN_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=2
            ),
            width=300,
            height=45,
            on_click=self.autenticar
        )

        self.lbl_creditos = ft.Text(
            "Elaborado por Eliana Garces 2026",
            size=11,
            color="grey600",
            italic=True,
            text_align=ft.TextAlign.CENTER
        )

        # Formulario de credenciales
        self.form_column = ft.Column([
            ft.Container(
                content=ft.Icon(ft.icons.STOREFRONT_ROUNDED, size=44, color=Config.COLOR_PRIMARY),
                padding=12,
                bgcolor=ft.colors.with_opacity(0.08, Config.COLOR_PRIMARY),
                border_radius=50
            ),
            ft.Text("Abarrotes Doña Mary", size=22, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Text("Ingreso al Sistema", size=13, color="grey600"),
            ft.Divider(height=10, color="transparent"),
            self.txt_usuario,
            self.txt_clave,
            self.lbl_error,
            self.progress,
            ft.Container(height=5),
            self.btn_ingresar,
            ft.Divider(height=10, color="transparent"),
            self.lbl_creditos
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)

        # Panel Flotante Blanco Centrado
        self.card_container = ft.Container(
            width=380,
            padding=35,
            bgcolor="white",
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=20,
                color=ft.colors.with_opacity(0.3, "black"),
                offset=ft.Offset(0, 8)
            ),
            content=self.form_column
        )

        self.content = self.card_container

    def autenticar(self, e):
        user = self.txt_usuario.value.strip().lower()
        pwd = self.txt_clave.value.strip()

        if not user or not pwd:
            self.lbl_error.value = "Por favor ingresa usuario y contraseña."
            self.lbl_error.visible = True
            self.update()
            return

        self.progress.visible = True
        self.btn_ingresar.disabled = True
        self.lbl_error.visible = False
        self.update()

        threading.Thread(target=self._worker_autenticar, args=(user, pwd), daemon=True).start()

    def _worker_autenticar(self, user, pwd):
        try:
            url = f"{self.db.url}/usuarios?usuario=eq.{user}&clave=eq.{pwd}&activo=eq.true"
            res = self.db.session.get(url, headers=self.db.headers, timeout=5)

            if res.status_code == 200 and len(res.json()) > 0:
                datos_usuario = res.json()[0]
                
                # Transformar la tarjeta flotante en el estado de bienvenida (sin lanzar AlertDialog)
                self._mostrar_bienvenida_en_tarjeta(datos_usuario)
            else:
                self.lbl_error.value = "Credenciales incorrectas o usuario inactivo."
                self.lbl_error.visible = True
                self.progress.visible = False
                self.btn_ingresar.disabled = False
                if self.page:
                    self.page.update()
        except Exception as ex:
            self.lbl_error.value = f"Error de conexión: {ex}"
            self.lbl_error.visible = True
            self.progress.visible = False
            self.btn_ingresar.disabled = False
            if self.page:
                self.page.update()

    def _mostrar_bienvenida_en_tarjeta(self, datos_usuario):
        nombre_completo = datos_usuario.get("nombre_completo") or datos_usuario.get("usuario") or "Usuario"
        partes = nombre_completo.split()
        primer_nombre = partes[0] if partes else "Usuario"
        if primer_nombre.lower() in ["doña", "dona"] and len(partes) > 1:
            primer_nombre = f"{partes[0]} {partes[1]}"

        # Cambiar el contenido de la tarjeta blanca al mensaje de bienvenida de forma limpia
        self.card_container.content = ft.Column([
            ft.Container(height=10),
            ft.Icon(ft.icons.WAVING_HAND_ROUNDED, size=48, color="orange700"),
            ft.Text(f"¡Bienvenido, {primer_nombre}!", size=20, weight="bold", color=Config.COLOR_PRIMARY, text_align=ft.TextAlign.CENTER),
            ft.Text("Accediendo al sistema...", size=13, color="grey600"),
            ft.Divider(height=10, color="transparent"),
            ft.ProgressRing(width=28, height=28, color=Config.COLOR_PRIMARY, stroke_width=3),
            ft.Divider(height=15, color="transparent"),
            self.lbl_creditos
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)

        if self.page:
            self.page.update()

        # Tiempo para mostrar el saludo
        time.sleep(2.0)

        # Cargar aplicación principal
        self.on_login_success(datos_usuario)
````

## File: .gitignore
````
# Entornos virtuales
venv/
env/
.env

# Archivos de caché y logs
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.log

# Archivos pesados o temporales
*.pdf
*.xlsx
*.csv
~$*.xlsx

# Configuración del IDE/Sistema
.vscode/
.idea/
.DS_Store
.kiro/

# Carpetas de dependencias y compilación
build/
dist/
node_modules/
````

## File: config.py
````python
import os
import sys
from dotenv import load_dotenv

# Determinar la ruta base dependiendo de si se ejecuta como script o como .exe
if getattr(sys, 'frozen', False):
    # Si es un ejecutable empaquetado (flet pack / PyInstaller), usar la carpeta temporal _MEIPASS
    base_path = sys._MEIPASS
else:
    # Si es el código fuente normal, usar la carpeta actual
    base_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(base_path, '.env')

# Cargar variables de entorno apuntando explícitamente al archivo
load_dotenv(dotenv_path=env_path)
class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Colores de la aplicación (Tema)
    COLOR_PRIMARY = "#0B2447" # Azul Oscuro (Primario)
    COLOR_SECONDARY = "#19376D" # Azul Medio (Secundario)
    COLOR_BACKGROUND = "#F8F9FA" # Blanco/Gris claro (Fondo)
    COLOR_TEXT = "#333333"
````

## File: openapi.json
````json
{"code": "PGRST125", "details": null, "hint": null, "message": "Invalid path specified in request URL"}
````

## File: Sistema_Dona_Mary.spec
````
# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Sistema_Dona_Mary',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:/Users/Home/AppData/Local/Temp/8eefa800-9c76-474d-b9a1-33f4a3d6fe9b',
)
````

## File: supabase_schema.sql
````sql
-- Script de Creación de Base de Datos para Dashboard Abarrotes Mary
-- Ejecuta este script en el "SQL Editor" de tu panel de Supabase

-- 1. Tabla: Catalogo_Insumos (El Maestro de Productos)
CREATE TABLE IF NOT EXISTS public.Catalogo_Insumos (
    id_insumo UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    categoria TEXT,
    costo_unitario DECIMAL(10,2) DEFAULT 0,
    precio_venta DECIMAL(10,2) DEFAULT 0,
    stock_actual INTEGER DEFAULT 0,
    stock_minimo INTEGER DEFAULT 5,
    estado BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. Tabla: Registro_Compras (Entradas)
CREATE TABLE IF NOT EXISTS public.Registro_Compras (
    id_compra UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    id_insumo UUID REFERENCES public.Catalogo_Insumos(id_insumo),
    insumo TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    proveedor TEXT,
    estado_registro TEXT DEFAULT 'VÁLIDO' CHECK (estado_registro IN ('VÁLIDO', 'ANULADO'))
);

-- 3. Tabla: Registro_Ventas (Salidas)
CREATE TABLE IF NOT EXISTS public.Registro_Ventas (
    id_venta UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factura_no TEXT,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    codigo_item TEXT REFERENCES public.Catalogo_Insumos(codigo),
    descripcion TEXT,
    cantidad INTEGER NOT NULL,
    subtotal DECIMAL(10,2) DEFAULT 0,
    descuento DECIMAL(10,2) DEFAULT 0,
    iva DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) DEFAULT 0,
    estado_registro TEXT DEFAULT 'VÁLIDO' CHECK (estado_registro IN ('VÁLIDO', 'ANULADO'))
);

-- Configuración de Seguridad (Opcional por ahora, pero recomendado)
-- Desactivamos RLS para que la app pueda acceder fácilmente (al ser de escritorio admin)
ALTER TABLE public.Catalogo_Insumos DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.Registro_Compras DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.Registro_Ventas DISABLE ROW LEVEL SECURITY;
````

## File: ui/views/conteo_inicial.py
````python
import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
import datetime
from dateutil.relativedelta import relativedelta

class ConteoInicialView(ft.Container):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
        self.expand = True
        self.db = SupabaseClient()
        
        # State
        self.data_completa = []
        self.cambios_pendientes = {} # {codigo: nuevo_valor}
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        # Generar meses para el Dropdown
        hoy = datetime.date.today()
        opciones_meses = []
        for i in range(12): # Últimos 12 meses
            m = hoy - relativedelta(months=i)
            # Formato YYYY-MM
            val = m.strftime("%Y-%m")
            # Label bonito
            nombre_mes = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][m.month - 1]
            opciones_meses.append(ft.dropdown.Option(key=val, text=f"{nombre_mes} {m.year}"))
            
        self.mes_seleccionado = hoy.strftime("%Y-%m")
        
        # UI Filters
        self.search_input = ft.TextField(
            hint_text="Buscar código o insumo...",
            prefix_icon=ft.icons.SEARCH,
            border_radius=8,
            expand=True,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_filter_change
        )
        
        self.category_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            label="Categoría",
            width=200,
            border_radius=8,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_filter_change
        )
        
        self.month_dropdown = ft.Dropdown(
            options=opciones_meses,
            value=self.mes_seleccionado,
            label="Mes de Conteo",
            width=200,
            border_radius=8,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_month_change
        )
        
        # Tabla
        self.data_table = ft.DataTable(
            column_spacing=15,
            data_row_min_height=45,
            data_row_max_height=45,
            heading_row_height=40,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Categoría", weight="bold")),
                ft.DataColumn(ft.Text("Cierre Mes Ant.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Stock Inicial Reg.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Nuevo Conteo", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[]
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        
        # Bulk Action Bar
        self.btn_guardar_masivo = ft.ElevatedButton("Guardar Todos los Registros", bgcolor="green", color="white", on_click=self.guardar_masivo)
        self.action_bar = ft.Container(
            content=ft.Row([
                ft.Text("Tienes cambios pendientes por guardar", color="white", weight="bold"),
                ft.Container(expand=True),
                ft.OutlinedButton("Cancelar Todas las Ediciones", style=ft.ButtonStyle(color="white"), on_click=self.cancelar_masivo),
                self.btn_guardar_masivo
            ]),
            bgcolor=Config.COLOR_PRIMARY,
            padding=15,
            border_radius=10,
            visible=False,
            margin=ft.padding.only(top=10)
        )
        
        self.content = ft.Column([
            self.lbl_titulo,
            
            # Filtros
            ft.Container(
                content=ft.Row([
                    self.search_input,
                    self.category_dropdown,
                    self.month_dropdown,
                    ft.IconButton(icon=ft.icons.REFRESH, on_click=self.on_month_change, tooltip="Recargar")
                ]),
                bgcolor="white",
                padding=10,
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            # Tabla
            ft.Container(
                content=ft.Column(
                    [self.data_table],
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True
                ),
                bgcolor="white",
                padding=5,
                border_radius=10,
                expand=True,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            # Footer Paginación
            ft.Container(
                content=ft.Row([
                    self.lbl_total,
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(top=10)
            ),
            
            self.action_bar
            
        ], expand=True, spacing=15)

    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def did_mount(self):
        self.load_categories()
        self.load_data()
        
    def load_categories(self):
        cats = self.db.get_categorias()
        opts = [ft.dropdown.Option("Todas")]
        for c in cats:
            if c: opts.append(ft.dropdown.Option(c))
        self.category_dropdown.options = opts
        if self.page:
            self.update()
            
    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.cambios_pendientes.clear()
        self.current_page = 1
        self.load_data()
        
    def on_filter_change(self, e):
        self.current_page = 1
        self.render_table()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_table()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_table()
        
    def load_data(self):
        self.data_completa = self.db.get_datos_conteo_inicial(self.mes_seleccionado)
        self.render_table()
        
    def render_table(self):
        import math
        search_val = (self.search_input.value or "").lower()
        cat_val = self.category_dropdown.value or "Todas"
        
        self.data_table.rows.clear()
        
        filtered_data = []
        for item in self.data_completa:
            # Filtros
            nombre = str(item.get("nombre", "")).lower()
            codigo = str(item.get("codigo_insumo", "")).lower()
            categoria = str(item.get("categoria", ""))
            
            if search_val and search_val not in nombre and search_val not in codigo:
                continue
            if cat_val != "Todas" and cat_val != categoria:
                continue
                
            filtered_data.append(item)
            
        self.total_records = len(filtered_data)
        self.total_pages = math.ceil(self.total_records / self.page_size) if self.total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        
        page_data = filtered_data[start_idx:end_idx]
        
        for item in page_data:
            self.data_table.rows.append(self.crear_fila(item))
            
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros filtrados"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
            
        self.actualizar_action_bar()
        if self.page:
            self.update()
            
    def crear_fila(self, item):
        codigo = item["codigo_insumo"]
        cierre_ant = item["cierre_mes_anterior"]
        stock_ini = item["stock_inicial_actual"]
        
        input_conteo = ft.TextField(
            value=str(stock_ini),
            dense=True,
            width=80,
            text_size=13,
            content_padding=10,
            border_color=ft.colors.with_opacity(0.2, "black"),
            bgcolor="white"
        )
        
        acciones_container = ft.Row(visible=False, spacing=0)
        
        def on_change(e):
            val = input_conteo.value
            try:
                numeric_val = float(val) if '.' in val else int(val)
                if numeric_val != stock_ini:
                    self.cambios_pendientes[codigo] = numeric_val
                    acciones_container.visible = True
                else:
                    if codigo in self.cambios_pendientes:
                        del self.cambios_pendientes[codigo]
                    acciones_container.visible = False
            except ValueError:
                if codigo in self.cambios_pendientes:
                    del self.cambios_pendientes[codigo]
                acciones_container.visible = False
                
            e.control.update()
            acciones_container.update()
            self.actualizar_action_bar()
            
        input_conteo.on_change = on_change
        
        # Si ya había un cambio pendiente de antes (al buscar/filtrar)
        if codigo in self.cambios_pendientes:
            input_conteo.value = str(self.cambios_pendientes[codigo])
            acciones_container.visible = True
            
        def guardar_individual(e):
            if codigo in self.cambios_pendientes:
                val = self.cambios_pendientes[codigo]
                registro = {
                    "fecha_cierre": f"{self.mes_seleccionado}-01",
                    "codigo_insumo": codigo,
                    "tipo_registro": "INVENTARIO_INICIAL",
                    "cantidad_fisica": val,
                    "estado": "APLICADO"
                }
                exito = self.db.upsert_conteos_iniciales([registro])
                if exito:
                    item["stock_inicial_actual"] = val
                    del self.cambios_pendientes[codigo]
                    acciones_container.visible = False
                    self.page.snack_bar = ft.SnackBar(ft.Text("Guardado exitoso"), bgcolor="green")
                    self.page.snack_bar.open = True
                    self.render_table()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar"), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.page.update()
                    
        def cancelar_individual(e):
            if codigo in self.cambios_pendientes:
                del self.cambios_pendientes[codigo]
            input_conteo.value = str(item["stock_inicial_actual"])
            acciones_container.visible = False
            input_conteo.update()
            acciones_container.update()
            self.actualizar_action_bar()
            
        acciones_container.controls = [
            ft.IconButton(ft.icons.CHECK, icon_color="green", tooltip="Guardar", on_click=guardar_individual),
            ft.IconButton(ft.icons.CLOSE, icon_color="red", tooltip="Descartar", on_click=cancelar_individual)
        ]
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(codigo)),
                ft.DataCell(ft.Container(content=ft.Text(item["nombre"], no_wrap=True, tooltip=item["nombre"]), width=150)),
                ft.DataCell(ft.Text(item["categoria"])),
                ft.DataCell(ft.Text(str(cierre_ant))),
                ft.DataCell(ft.Text(str(stock_ini), weight="bold")),
                ft.DataCell(input_conteo),
                ft.DataCell(acciones_container),
            ]
        )
        
    def actualizar_action_bar(self):
        if len(self.cambios_pendientes) > 1:
            self.action_bar.visible = True
        else:
            self.action_bar.visible = False
        if self.page:
            self.action_bar.update()
            
    def cancelar_masivo(self, e):
        self.cambios_pendientes.clear()
        self.render_table()
        
    def guardar_masivo(self, e):
        if not self.cambios_pendientes:
            return
            
        registros = []
        for codigo, val in self.cambios_pendientes.items():
            registros.append({
                "fecha_cierre": f"{self.mes_seleccionado}-01",
                "codigo_insumo": codigo,
                "tipo_registro": "INVENTARIO_INICIAL",
                "cantidad_fisica": val,
                "estado": "APLICADO"
            })
            
        exito = self.db.upsert_conteos_iniciales(registros)
        if exito:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Se guardaron {len(registros)} registros exitosamente"), bgcolor="green")
            self.cambios_pendientes.clear()
            self.load_data() # Recargar todo de BD para asegurar sincronía
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar registros masivos"), bgcolor="red")
            
        self.page.snack_bar.open = True
        self.page.update()
````

## File: main.py
````python
import flet as ft
from ui.app import AppLayout
from ui.views.login import LoginView
from config import Config

def main(page: ft.Page):
    page.title = "Abarrotes y Desechables Doña Mary"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.window_maximized = True

    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme=ft.ColorScheme(
            primary=Config.COLOR_PRIMARY,
            primary_container=Config.COLOR_SECONDARY,
            secondary=Config.COLOR_SECONDARY,
            background=Config.COLOR_BACKGROUND,
            surface="white",
            on_surface=Config.COLOR_TEXT,
        ),
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
    )

    def cerrar_sesion():
        page.overlay.clear()  # Purga diálogos flotantes residuales
        page.clean()
        mostrar_login()

    def on_login_success(usuario_data):
        page.overlay.clear()  # Asegura que el modal de bienvenida sea destruido
        page.clean()
        # Instanciar el layout e iniciar la carga inmediata
        app_layout = AppLayout(page, usuario_data=usuario_data, on_logout=cerrar_sesion)
        page.add(app_layout)
        page.update()

    def mostrar_login():
        login_view = LoginView(on_login_success=on_login_success)
        page.add(login_view)
        page.update()

    # Iniciar en pantalla de Login
    mostrar_login()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
````

## File: core/gemini_parser.py
````python
import google.generativeai as genai
from config import Config
import json
import time
import re
from typing import TypedDict

class GeminiParser:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3.6-flash')

            
    def parse_invoice_pdf(self, pdf_path):
        """
        Envía un PDF a Gemini para extraer productos y cantidades.
        Retorna un diccionario con los datos extraídos o None si hay un error.
        """
        if not self.api_key:
            print("Error: No hay API key de Gemini configurada.")
            return None
            
        try:
            print(f"Subiendo archivo a Gemini: {pdf_path}")
            # 1. Subir archivo a la API de File de Gemini
            uploaded_file = genai.upload_file(path=pdf_path)
            
            # 2. Esperar a que el archivo se procese (opcional, recomendado para PDFs)
            while uploaded_file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            print("\nArchivo listo. Extrayendo datos...")
            
            # 3. Armar el prompt estricto
            prompt = """
            Extrae TODOS los datos de TODAS las páginas del reporte de entradas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas el nombre del proveedor ni la descripción del producto. Limítate a los datos numéricos y códigos.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada compra inicia en el extremo izquierdo con un código "EA-" (ej. EA-9273). Procesa TODOS los que encuentres.
            2. FECHA Y FACTURA: La "fecha" suele estar bajo el código EA (conviértela a YYYY-MM-DD). El "numero_factura" está junto a la palabra "Factura No.". Si no hay, pon null.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Totales de Entrada:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_insumo": Código de 4 dígitos al extremo izquierdo.
               - "cantidad": Dato bajo la columna 'Cant.'
               - "costo_unitario": Dato bajo la columna 'Costo'.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
            5. FORMATO NUMÉRICO ESTRICTO: Convierte puntos a miles y comas a decimales (ej. "13.100" -> 13100.0 y "16,50" -> 16.5).
            
            ESTRUCTURA EXACTA REQUERIDA (Sigue este patrón para todos los bloques e insumos):
            [
              {
                "numero_entrada": "EA-9276",
                "fecha": "2026-08-03",
                "numero_factura": "19284",
                "productos": [
                  {
                    "codigo_insumo": "0471",
                    "cantidad": 10.0,
                    "costo_unitario": 7353.0,
                    "iva": 13971.0
                  },
                  {
                    "codigo_insumo": "4182",
                    "cantidad": 50.0,
                    "costo_unitario": 2815.0,
                    "iva": 26744.0
                  }
                ]
              }
            ]
            """
            
            # 4. Enviar a Gemini forzando el motor JSON y maximizando los tokens
            response = self.model.generate_content(
                [uploaded_file, prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.0, # Temperatura cero para formato robótico y determinista
                    max_output_tokens=8192 # Darle el máximo espacio posible para PDFs grandes
                )
            )
            
            # Como forzamos el mime_type, la respuesta ya es un string JSON limpio
            text_response = response.text.strip()
            
            # Limpiar comas huérfanas (trailing commas) que la IA suele dejar por error antes de cerrar llaves o corchetes
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            # Parsear el JSON de forma segura
            data = json.loads(text_response)
            
            # --- Escudo de formato (Ahora esperamos una lista) ---
            if isinstance(data, dict):
                # Si Gemini se equivoca y devuelve un solo objeto, lo envolvemos en una lista
                data = [data]
            elif not isinstance(data, list):
                data = []
            # -------------------------------
            
            # Eliminar archivo subido
            genai.delete_file(uploaded_file.name)
            
            print("¡Extracción completada! Conexión con Gemini cerrada.")
            return data
            
        except Exception as e:
            print(f"Error procesando PDF con Gemini: {e}")
            return None

    def parse_compras_pdf_page(self, pdf_path, page_index):
        """
        Extrae datos de compras de una única página del PDF.
        """
        if not self.api_key:
            return None
            
        try:
            
            from pypdf import PdfReader, PdfWriter
            import os
            from typing import TypedDict
        except ImportError:
            return None
            
        try:
            reader = PdfReader(pdf_path)
            if page_index < 0 or page_index >= len(reader.pages):
                return None
                
            class ProductoCompra(TypedDict):
                codigo_insumo: str
                cantidad: float
                costo_unitario: float
                iva: float

            class FacturaCompra(TypedDict):
                numero_entrada: str
                fecha: str
                numero_factura: str
                proveedor: str
                productos: list[ProductoCompra]
                
            prompt = """
            Extrae TODOS los datos de TODAS las facturas en esta página del reporte de entradas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas la descripción del producto. Limítate a los datos solicitados.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada compra inicia en el extremo izquierdo con un código "EA-" (ej. EA-9273). Procesa TODOS los que encuentres.
            2. CABECERA DEL BLOQUE (Fecha, Factura y Proveedor): 
               En la misma línea que el "EA-" (o en la línea inmediatamente inferior):
               - La "fecha" suele estar a continuación del EA (conviértela a YYYY-MM-DD).
               - El "numero_factura" está precedido por la palabra "Factura No." o "Factura". Si no hay número, pon null.
               - El "proveedor" se encuentra AL LADO DERECHO de la palabra "Factura" o del número de factura. Extrae SOLO el nombre comercial (ej. "DISTRIBUCIONES PUNTO CHEVERE SAS", "AJOVER SAS"). 
               - REGLA ESTRICTA PARA PROVEEDOR: ESTÁ TOTALMENTE PROHIBIDO incluir explicaciones, razonamientos internos, notas de OCR o caracteres asiáticos en este campo. El valor debe ser ÚNICAMENTE el nombre de la empresa.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Totales de Entrada:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_insumo": Código de 4 dígitos al extremo izquierdo.
               - "cantidad": Dato bajo la columna 'Cant.'
               - "costo_unitario": Dato bajo la columna 'Costo'.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
            5. FORMATO NUMÉRICO ESTRICTO: Convierte puntos a miles y comas a decimales (ej. "13.100" -> 13100.0 y "16,50" -> 16.5).
            
            ESTRUCTURA EXACTA REQUERIDA (Sigue este patrón para todos los bloques e insumos):
            [
              {
                "numero_entrada": "EA-9276",
                "fecha": "2026-08-03",
                "numero_factura": "19284",
                "proveedor": "NOMBRE DEL PROVEEDOR SAS",
                "productos": [
                  {
                    "codigo_insumo": "0471",
                    "cantidad": 10.0,
                    "costo_unitario": 7353.0,
                    "iva": 13971.0
                  }
                ]
              }
            ]
            """
            
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            
            temp_pdf_path = f"temp_compras_page_{page_index}.pdf"
            with open(temp_pdf_path, "wb") as f:
                writer.write(f)
            
            uploaded_file = genai.upload_file(path=temp_pdf_path)
            time.sleep(2)
            
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            intentos = 0
            max_intentos = 3
            response = None
            
            while intentos < max_intentos:
                try:
                    response = self.model.generate_content(
                        [uploaded_file, prompt],
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=list[FacturaCompra],
                            temperature=0.0,
                            max_output_tokens=8192
                        )
                    )
                    break
                except Exception as api_e:
                    error_str = str(api_e)
                    if "429" in error_str or "quota" in error_str.lower():
                        print(f"⚠️ Límite de Google alcanzado (429). Esperando 60s de forma invisible... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(60)
                        intentos += 1
                    elif "500" in error_str or "internal error" in error_str.lower():
                        print(f"⚠️ Error interno en Google (500). Reintentando en 15s... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(15)
                        intentos += 1
                    else:
                        raise api_e
                        
            if response is None:
                print("Error: Se superaron los intentos máximos o respuesta nula.")
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)
                return []
            
            text_response = response.text.strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            text_response = text_response.strip()
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            genai.delete_file(uploaded_file.name)
            os.remove(temp_pdf_path)
            
            try:
                data = json.loads(text_response)
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                return []
            except json.JSONDecodeError as je:
                print(f"Error parseando JSON en página {page_index + 1}. Error: {je}")
                print(f"Texto problemático:\n{text_response[:500]}...")
                return []
                
        except Exception as e:
            print(f"Error procesando página {page_index + 1} de compras con Gemini: {e}")
            return None

    def parse_ventas_pdf(self, pdf_path, progress_callback=None):
        """
        Envía un PDF de ventas a Gemini (en bloques) para evitar el límite de memoria.
        Retorna un arreglo con los datos extraídos o None si hay un error.
        """
        if not self.api_key:
            print("Error: No hay API key de Gemini configurada.")
            return None
            
        try:
            from pypdf import PdfReader, PdfWriter
            import os
        except ImportError:
            msg = "Error: Falta la librería pypdf. Ejecuta 'pip install pypdf' en la terminal."
            print(msg)
            if progress_callback: progress_callback(msg)
            return None
            
        try:
            msg = f"Preparando división automática para el PDF..."
            print(msg)
            if progress_callback: progress_callback(msg)
            
            reader = PdfReader(pdf_path)
            total_paginas = len(reader.pages)
            tamano_bloque = 1 # Procesar de a 1 página para máxima precisión y evitar errores de JSON
            todas_las_facturas = []
            
            # --- EL MOLDE ESTRICTO PARA VENTAS ---
            class ProductoVenta(TypedDict):
                codigo_item: str
                cantidad: float
                subtotal: float
                iva: float
                costo_total: float

            class FacturaVenta(TypedDict):
                fecha: str
                numero_factura: str
                productos: list[ProductoVenta]
            # --------------------------------------------
            
            prompt = """
            Extrae TODOS los datos de TODAS las páginas de este fragmento del reporte de facturas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas el nombre del cliente ni la descripción del producto. Limítate a los datos numéricos y códigos.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada bloque de venta inicia con "Fact.No." seguido del número de factura. Procesa TODOS los que encuentres en el documento.
            2. FECHA Y FACTURA: La "fecha" suele estar en la misma línea que el "Fact.No." (conviértela a YYYY-MM-DD). Extrae el número de factura.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Total Factura:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_item": Código al extremo izquierdo (ej. 0847, 0571-1).
               - "cantidad": Dato bajo la columna 'Cantidad'.
               - "subtotal": Dato bajo la columna 'Subtotal'. NO HAGAS NINGÚN CÁLCULO.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
               - "costo_total": Dato bajo la columna 'Total'.
            5. FORMATO NUMÉRICO ESTRICTO: Todo valor monetario o cantidad debe ser número (float). Usa puntos (.) solo para decimales. NO uses comas (,) para separar los miles dentro de los números (ej. "93,277" debe ser 93277.0).
            """
            
            # Ciclo para iterar el documento por pedazos
            for i in range(0, total_paginas, tamano_bloque):
                rango_inicio = i + 1
                rango_fin = min(i + tamano_bloque, total_paginas)
                msg = f"Extrayendo datos: Página {rango_inicio} de {total_paginas}..." if tamano_bloque == 1 else f"Extrayendo datos: Páginas {rango_inicio} a {rango_fin} de {total_paginas}..."
                print(msg)
                if progress_callback: progress_callback(msg)
                
                # 1. Crear PDF temporal con solo un bloque de páginas
                writer = PdfWriter()
                for j in range(i, rango_fin):
                    writer.add_page(reader.pages[j])
                    
                temp_pdf_path = f"temp_ventas_chunk_{i}.pdf"
                with open(temp_pdf_path, "wb") as f:
                    writer.write(f)
                
                # 2. Subir el fragmento a Gemini
                uploaded_file = genai.upload_file(path=temp_pdf_path)
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(1)
                    uploaded_file = genai.get_file(uploaded_file.name)
                
                # 3. Extraer los datos forzando el motor JSON y el esquema
                response = self.model.generate_content(
                    [uploaded_file, prompt],
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=list[FacturaVenta],
                        temperature=0.0,
                        max_output_tokens=8192
                    )
                )
                
                text_response = response.text.strip()
                
                # Limpiar la basura residual y comas huérfanas
                if text_response.startswith("```json"):
                    text_response = text_response[7:]
                if text_response.startswith("```"):
                    text_response = text_response[3:]
                if text_response.endswith("```"):
                    text_response = text_response[:-3]
                
                text_response = text_response.strip()
                text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
                
                try:
                    data = json.loads(text_response)
                    # Agrupar los resultados
                    if isinstance(data, dict):
                        todas_las_facturas.append(data)
                    elif isinstance(data, list):
                        todas_las_facturas.extend(data)
                except json.JSONDecodeError as je:
                    print(f"Error parseando el JSON en página {rango_inicio}. Saltando bloque. Error: {je}")
                    print(f"JSON Problemático:\n{text_response[:500]}...")
                
                # 4. Limpiar los archivos temporales para no llenar el disco ni la nube
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)

            msg = "¡Extracción de todas las páginas completada!"
            print(msg)
            if progress_callback: progress_callback(msg)
            
            return todas_las_facturas
            
        except Exception as e:
            print(f"Error procesando PDF de ventas con Gemini: {e}")
            return None

    def parse_ventas_pdf_page(self, pdf_path, page_index, tipo_documento="Remisión"):
        """
        Extrae datos de una única página del PDF.
        """
        if not self.api_key:
            return None
            
        try:
            from pypdf import PdfReader, PdfWriter
            import os
        except ImportError:
            return None
            
        try:
            reader = PdfReader(pdf_path)
            if page_index < 0 or page_index >= len(reader.pages):
                return None
                
            # --- EL MOLDE ESTRICTO PARA VENTAS ---
            class ProductoVenta(TypedDict):
                codigo_item: str
                cantidad: float
                subtotal: float
                iva: float
                costo_total: float

            class FacturaVenta(TypedDict):
                fecha: str
                numero_factura: str
                productos: list[ProductoVenta]
            
            if tipo_documento == "Factura POS":
                prompt = """
                Extrae los datos de ventas formato POS de este documento y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
                Solo se requiere el numero de factura, codigo insumo, cantidad y precio unitario.
                NO extraigas fechas (el sistema las asignará), ni nombres de clientes.
                
                REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
                1. BLOQUES DE FACTURA: Cada factura inicia debajo de la palabra "TIPO NUMERO" con el prefijo "PP" seguido del número (ej. "PP 26396"). Extrae SOLO los números.
                2. PRODUCTOS: Debajo de "Clientes Varios", cada línea de producto tiene 3 valores separados por espacios. 
                   - "codigo_item": El primer número de la línea (ej. 2151).
                   - "cantidad": El segundo número (ej. 50.00).
                   - "precio_unitario": El tercer número (ej. 1900.00).
                3. CÁLCULOS OBLIGATORIOS PARA EL JSON:
                   - "subtotal": DEBES multiplicar la "cantidad" por el "precio_unitario".
                   - "iva": Siempre será 0.0 para este formato.
                   - "costo_total": Será exactamente igual al "subtotal".
                4. FORMATO NUMÉRICO: Todo valor monetario o cantidad debe ser número (float). Usa puntos (.) solo para decimales. NO uses comas.
                """
            else:
                prompt = """
                Extrae TODOS los datos de TODAS las páginas de este fragmento del reporte de facturas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
                NO extraigas el nombre del cliente ni la descripción del producto. Limítate a los datos numéricos y códigos.
                
                REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
                1. BLOQUES: Cada bloque de venta inicia con "Fact.No." seguido del número de factura. Procesa TODOS los que encuentres.
                2. FECHA Y FACTURA: La "fecha" suele estar en la misma línea que el "Fact.No.". Extrae el número de factura.
                3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a "Total Factura:".
                4. CAMPOS POR PRODUCTO:
                   - "codigo_item": Código al extremo izquierdo.
                   - "cantidad": Dato bajo la columna 'Cantidad'.
                   - "subtotal": Dato bajo la columna 'Subtotal'. NO HAGAS NINGÚN CÁLCULO.
                   - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
                   - "costo_total": Dato bajo la columna 'Total'.
                5. FORMATO NUMÉRICO: Usa puntos (.) solo para decimales. NO uses comas (,).
                """
            
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            
            temp_pdf_path = f"temp_ventas_page_{page_index}.pdf"
            with open(temp_pdf_path, "wb") as f:
                writer.write(f)
            
            uploaded_file = genai.upload_file(path=temp_pdf_path)
            time.sleep(2) # Pausa inicial para dar respiro a la API
            
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5) # Preguntar solo cada 5 segundos
                uploaded_file = genai.get_file(uploaded_file.name)
            
            intentos = 0
            max_intentos = 3
            response = None
            
            while intentos < max_intentos:
                try:
                    response = self.model.generate_content(
                        [uploaded_file, prompt],
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=list[FacturaVenta],
                            temperature=0.0,
                            max_output_tokens=8192
                        )
                    )
                    break
                except Exception as api_e:
                    error_str = str(api_e)
                    if "429" in error_str or "quota" in error_str.lower():
                        print(f"⚠️ Límite de Google alcanzado (429). Esperando 60s de forma invisible... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(60)
                        intentos += 1
                    elif "500" in error_str or "internal error" in error_str.lower():
                        print(f"⚠️ Error interno en los servidores de Google (500). Reintentando en 15s... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(15)
                        intentos += 1
                    else:
                        raise api_e
                        
            if response is None:
                print("Error: Se superaron los intentos máximos o la respuesta es nula.")
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)
                return []
            
            text_response = response.text.strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
            
            text_response = text_response.strip()
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            genai.delete_file(uploaded_file.name)
            os.remove(temp_pdf_path)
            
            try:
                data = json.loads(text_response)
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                return []
            except json.JSONDecodeError as je:
                print(f"Error parseando el JSON de página {page_index + 1}. Error: {je}")
                return []
                
        except Exception as e:
            print(f"Error procesando página {page_index + 1} de ventas con Gemini: {e}")
            return None
````

## File: ui/app.py
````python
import flet as ft
import threading
from ui.layout.sidebar import Sidebar
from ui.views.dashboard import DashboardView
from ui.views.inventario import InventarioView
from ui.views.compras import ComprasView
from ui.views.ventas import VentasView
from ui.views.cierre_inventario import CierreInventarioView
from ui.views.ajustes_inventario import AjustesInventarioView
from ui.views.informes import InformesView

class AppLayout(ft.Row):
    def __init__(self, page: ft.Page, usuario_data=None, on_logout=None):
        super().__init__()
        self.page = page
        self.usuario_data = usuario_data or {}
        self.on_logout = on_logout
        self.expand = True
        self.spacing = 0

        # Ruta por defecto
        username = str(self.usuario_data.get("usuario", "")).lower()
        rol = str(self.usuario_data.get("rol", "OPERADOR")).upper()
        es_admin = username in ["eliana", "cesar", "mary"] or rol == "ADMINISTRADOR"
        
        self.initial_route = "dashboard" if es_admin else "inventario"

        # Instanciar vista inicial
        self.views = {}
        if self.initial_route == "dashboard":
            self.views["dashboard"] = DashboardView()
        else:
            self.views["inventario"] = InventarioView()

        self.active_view = ft.Container(
            content=self.views[self.initial_route],
            expand=True,
            bgcolor="#F4F6F7",
            padding=15,
            alignment=ft.alignment.top_left
        )

        self.sidebar = Sidebar(self.on_route_change, usuario_data=self.usuario_data, on_logout=self.on_logout)

        self.controls = [
            self.sidebar,
            self.active_view
        ]

    def did_mount(self):
        # Actualizar estado activo en el sidebar para la vista inicial
        if hasattr(self.sidebar, "actualizar_estado_activo"):
            self.sidebar.actualizar_estado_activo(self.initial_route)
            
        # Iniciar carga de datos
        def load_data_bg():
            vista = self.views[self.initial_route]
            if hasattr(vista, 'load_data'):
                try: vista.load_data()
                except Exception as e: pass
            if hasattr(vista, 'load_summary'):
                try: vista.load_summary()
                except Exception as e: pass
        threading.Thread(target=load_data_bg, daemon=True).start()
        
    def on_route_change(self, route_name):
        if not route_name: return
        
        # Instanciar de forma perezosa (Lazy Loading) para evitar lag inicial
        if route_name not in self.views:
            if route_name == "dashboard": self.views[route_name] = DashboardView()
            elif route_name == "inventario": self.views[route_name] = InventarioView()
            elif route_name == "compras": self.views[route_name] = ComprasView()
            elif route_name == "ventas": self.views[route_name] = VentasView()
            elif route_name == "ajustes_inventario": self.views[route_name] = AjustesInventarioView()
            elif route_name == "cierre_mes": self.views[route_name] = CierreInventarioView()
            elif route_name == "informes": self.views[route_name] = InformesView()
            
        # Cambiar el contenido del contenedor principal
        if route_name in self.views:
            vista = self.views[route_name]
            self.active_view.content = vista
            self.active_view.update()
            
            # Resaltar la ruta activa en el menú lateral
            if hasattr(self.sidebar, "actualizar_estado_activo"):
                self.sidebar.actualizar_estado_activo(route_name)
            
            # Forzar recarga de datos al navegar para evitar caché estancada
            # Se ejecuta en hilo secundario para evitar congelar la interfaz
            def load_data_bg():
                if hasattr(vista, 'load_data'):
                    try:
                        vista.load_data()
                    except Exception as e:
                        print(f"Error reload load_data en {route_name}: {e}")
                        
                if hasattr(vista, 'load_summary'):
                    try:
                        vista.load_summary()
                    except Exception as e:
                        print(f"Error reload load_summary en {route_name}: {e}")
            
            threading.Thread(target=load_data_bg, daemon=True).start()
````

## File: ui/layout/sidebar.py
````python
import flet as ft
from config import Config

class Sidebar(ft.Container):
    def __init__(self, on_route_change, usuario_data=None, on_logout=None):
        super().__init__()
        self.on_route_change = on_route_change
        self.usuario_data = usuario_data or {}
        self.on_logout = on_logout
        self.is_expanded = True
        
        self.width = 250
        self.bgcolor = Config.COLOR_PRIMARY
        self.padding = 15
        self.border_radius = ft.border_radius.only(top_right=15, bottom_right=15)
        self.animate = ft.animation.Animation(300, ft.AnimationCurve.DECELERATE)

        # Botón Toggle
        self.toggle_btn = ft.IconButton(
            icon=ft.icons.MENU,
            icon_color="white",
            on_click=self.toggle_sidebar,
            tooltip="Ocultar/Mostrar Menú"
        )
        self.toggle_row = ft.Row([self.toggle_btn], alignment=ft.MainAxisAlignment.END)

        # Extraer Primer Nombre
        nombre_completo = self.usuario_data.get("nombre_completo") or self.usuario_data.get("usuario") or "Usuario"
        partes = nombre_completo.split()
        primer_nombre = partes[0] if partes else "Usuario"
        if primer_nombre.lower() in ["doña", "dona"] and len(partes) > 1:
            primer_nombre = f"{partes[0]} {partes[1]}"
            
        rol_txt = str(self.usuario_data.get("rol", "OPERADOR")).capitalize()

        # Componentes Estéticos del Perfil de Usuario (Compacto)
        self.user_avatar = ft.Icon(ft.icons.ACCOUNT_CIRCLE_ROUNDED, color="white", size=32)
        self.lbl_saludo = ft.Text(f"Hola, {primer_nombre}", color="white", size=12, weight="bold", no_wrap=True)
        self.lbl_rol = ft.Text(rol_txt, color="white54", size=10, no_wrap=True)

        self.user_info_col = ft.Column([
            self.lbl_saludo,
            self.lbl_rol
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)

        # Botón Cerrar Sesión
        self.btn_logout = ft.IconButton(
            icon=ft.icons.LOGOUT_ROUNDED,
            icon_color="white54",
            icon_size=18,
            tooltip="Cerrar Sesión",
            on_click=lambda e: self.on_logout() if self.on_logout else None
        )

        self.user_badge = ft.Container(
            content=ft.Row([
                self.user_avatar,
                self.user_info_col,
                ft.Container(expand=True),
                self.btn_logout
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            bgcolor=ft.colors.with_opacity(0.12, "white"),
            border_radius=8,
            margin=ft.padding.only(bottom=10)
        )

        self.menu_items = {}
        self.footer_text = ft.Text(
            "Elaborado por Eliana Garces 2026\npara Abarrotes y Desechables de Doña Mary SAS",
            color="white54", size=10, text_align=ft.TextAlign.CENTER
        )

        # Permisos
        username = str(self.usuario_data.get("usuario", "")).lower()
        rol = str(self.usuario_data.get("rol", "OPERADOR")).upper()
        es_admin = username in ["eliana", "cesar", "mary"] or rol == "ADMINISTRADOR"

        menu_controls = [
            self.toggle_row,
            self.user_badge
        ]

        if es_admin:
            menu_controls.append(self._create_menu_item("Dashboard", ft.icons.DASHBOARD, "dashboard"))

        menu_controls.append(self._create_menu_item("Inventario", ft.icons.INVENTORY_2, "inventario"))
        menu_controls.append(self._create_menu_item("Compras", ft.icons.ADD_SHOPPING_CART, "compras"))
        menu_controls.append(self._create_menu_item("Ventas", ft.icons.POINT_OF_SALE, "ventas"))
        menu_controls.append(self._create_menu_item("Ajustes de Inventario", ft.icons.TUNE, "ajustes_inventario"))

        if es_admin or rol == "AUDITOR":
            menu_controls.append(self._create_menu_item("Cierre de Mes", ft.icons.FACT_CHECK, "cierre_mes"))
            menu_controls.append(self._create_menu_item("Informes", ft.icons.PIE_CHART, "informes"))

        menu_controls.extend([
            ft.Container(expand=True),
            ft.Container(
                content=self.footer_text,
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=5, bottom=5),
                on_click=self.mostrar_disclaimer,
                tooltip="Ver Información Legal y Créditos"
            )
        ])

        self.content = ft.Column(controls=menu_controls, spacing=5)

    def _create_menu_item(self, text, icon, route):
        item = ft.ListTile(
            leading=ft.Icon(icon, color="white70", size=22),
            title=ft.Text(text, color="white70", size=13),
            hover_color=ft.colors.with_opacity(0.1, "white"),
            content_padding=ft.padding.only(left=12, right=12),
            on_click=lambda _, r=route: self.on_route_change(r),
            tooltip=text
        )
        self.menu_items[route] = item
        return item

    def actualizar_estado_activo(self, ruta_actual):
        for route, item in self.menu_items.items():
            is_active = (route == ruta_actual)
            item.bgcolor = ft.colors.with_opacity(0.2, "white") if is_active else None
            item.leading.color = "white" if is_active else "white70"
            item.title.color = "white" if is_active else "white70"
            item.title.weight = "bold" if is_active else "normal"
        try:
            self.update()
        except Exception:
            pass

    def toggle_sidebar(self, e):
        self.is_expanded = not self.is_expanded
        self.width = 250 if self.is_expanded else 70

        # Ocultar o mostrar elementos informativos al colapsar
        self.user_info_col.visible = self.is_expanded
        self.btn_logout.visible = self.is_expanded
        self.footer_text.visible = self.is_expanded

        self.user_avatar.size = 32 if self.is_expanded else 24
        self.user_badge.padding = ft.padding.symmetric(horizontal=8, vertical=6) if self.is_expanded else ft.padding.all(4)

        for control in self.content.controls:
            if isinstance(control, ft.ListTile):
                control.title.visible = self.is_expanded
                control.content_padding = ft.padding.only(left=12 if self.is_expanded else 8, right=12 if self.is_expanded else 8)

        self.update()

    def mostrar_disclaimer(self, e):
        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.GAVEL_ROUNDED, color=Config.COLOR_PRIMARY),
                ft.Text("Información Legal y Créditos", size=16, weight="bold", color=Config.COLOR_PRIMARY)
            ]),
            content=ft.Column([
                ft.Text("Versión del Software: 1.0", size=13, weight="bold"),
                ft.Divider(height=10, color="transparent"),
                ft.Text("Autoría Intelectual:", size=13, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Este software fue diseñado, estructurado y desarrollado en su totalidad por Eliana Garces. Todos los derechos sobre el código fuente y la arquitectura de la aplicación están reservados a su autor.", size=12, color="grey700", text_align=ft.TextAlign.JUSTIFY),
                ft.Divider(height=10, color="transparent"),
                ft.Text("Descargo de Responsabilidad:", size=13, weight="bold", color="red700"),
                ft.Text("La veracidad de la información, el manejo de inventarios, la gestión financiera y el uso general de los datos introducidos en esta plataforma, así como las decisiones operativas tomadas en base a los mismos, son responsabilidad única y exclusiva de Abarrotes y Desechables de Doña Mary SAS.", size=12, color="grey700", text_align=ft.TextAlign.JUSTIFY)
            ], tight=True, spacing=5, width=400),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self._cerrar_dialogo(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        if self.page:
            if hasattr(self.page, "open"):
                self.page.open(dlg)
            else:
                self.page.overlay.append(dlg)
                dlg.open = True
                self.page.update()

    def _cerrar_dialogo(self, dlg):
        if self.page:
            if hasattr(self.page, "close"):
                self.page.close(dlg)
            else:
                dlg.open = False
                self.page.update()
````

## File: ui/views/ajustes_inventario.py
````python
import flet as ft
import threading
from config import Config
from config import Config
from core.supabase_client import SupabaseClient
from ui.components.autocomplete import CustomAutoComplete

class AjustesInventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
        self.expand = True
        self.db = SupabaseClient()
        self.tipo_ajuste_actual = "ENTRADA"
        
        # Mapeo estricto contra restricciones de BD
        self.mapa_motivos = {
            "Sobrante de Inventario": "ENTRADA_POR_SOBRANTE",
            "Donación Entrante": "AJUSTE_ENTRADA",
            "Devolución Cliente": "AJUSTE_ENTRADA",
            "Daño / Merma": "AJUSTE_SALIDA",
            "Vencimiento": "BAJA_VENCIMIENTO",
            "Pérdida": "SALIDA_POR_FALTANTE",
            "Consumo Familiar": "AJUSTE_SALIDA",
            "Consumo Cliente (Cortesía)": "AJUSTE_SALIDA",
            "Donación Saliente": "AJUSTE_SALIDA",
            "Otro (Entrada)": "AJUSTE_ENTRADA",
            "Otro (Salida)": "AJUSTE_SALIDA"
        }

        # --- Labels reactivos de Resumen ---
        self.lbl_ent_actual = ft.Text("$0.00", weight="bold")
        self.lbl_ent_pos = ft.Text("$0.00", weight="bold", color="green")
        self.lbl_sal_neg = ft.Text("$0.00", weight="bold", color="red")
        self.lbl_ent_neto = ft.Text("$0.00", weight="bold")
        self.lbl_ent_proyectado = ft.Text("$0.00", weight="bold", color=Config.COLOR_PRIMARY)

        # --- Paginación y Filtros ---
        self.data_completa = []
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0

        def on_select_filtro_ajustes(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            if "[" in texto and "]" in texto:
                query = texto.split("]")[0].replace("[", "").strip()
            else:
                query = texto.strip()
            self.search_input_text.value = query
            self._on_filter_change()

        self.search_input_text = ft.TextField(visible=False)

        self.search_filter_autocomplete = CustomAutoComplete(
            hint_text="Buscar código o nombre...",
            on_select=on_select_filtro_ajustes,
            text_size=12,
            height=38,
            expand=2
        )
        
        self.date_picker = ft.DatePicker(on_change=lambda e: self._on_filter_change())
        self.btn_date = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_OUTLINED,
            tooltip="Filtrar por Fecha de Ajuste",
            on_click=lambda e: self.date_picker.pick_date()
        )
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            icon_color="red",
            visible=False,
            on_click=self._clear_date
        )

        self.drop_tipo = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Entrada"), ft.dropdown.Option("Salida")],
            value="Todos", label="Tipo", dense=True, width=150, height=38, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8), on_change=lambda e: self._on_filter_change()
        )
        
        motivos_combinados = ["Todos"] + list(self.mapa_motivos.keys())
        self.drop_motivo = ft.Dropdown(
            options=[ft.dropdown.Option(m) for m in motivos_combinados],
            value="Todos", label="Motivo", dense=True, width=200, height=38, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8), on_change=lambda e: self._on_filter_change()
        )

        self.btn_prev = ft.IconButton(icon=ft.icons.ARROW_BACK_IOS, on_click=self._prev_page, disabled=True)
        self.btn_next = ft.IconButton(icon=ft.icons.ARROW_FORWARD_IOS, on_click=self._next_page, disabled=True)
        self.lbl_page_info = ft.Text("Pág 1 de 1", weight="bold")

        # --- Vista de Tarjetas (Lista) ---
        self.lista_ajustes = ft.ListView(expand=True, spacing=10, auto_scroll=False)
        self.btn_agregar_ajuste = ft.ElevatedButton("Registrar Ajuste", icon=ft.icons.ADD, bgcolor=Config.COLOR_PRIMARY, color="white", on_click=lambda e: self.abrir_modal_ajuste())

        # --- Modal ---
        self.modal_ajuste = self._crear_modal_formulario()

        # --- Layout Principal Unificado ---
        kpi_bar = ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("Valor Inventario Base:", size=11, color="grey"), self.lbl_ent_actual], spacing=0),
                ft.Container(width=1, height=30, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Valor Entradas (+):", size=11, color="grey"), self.lbl_ent_pos], spacing=0),
                ft.Container(width=1, height=30, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Valor Salidas (-):", size=11, color="grey"), self.lbl_sal_neg], spacing=0),
                ft.Container(width=1, height=30, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Impacto Neto:", size=11, color="grey"), self.lbl_ent_neto], spacing=0),
                ft.Container(expand=True),
                ft.Column([ft.Text("Inventario Proyectado:", size=11, color="grey"), self.lbl_ent_proyectado], spacing=0, horizontal_alignment="end"),
            ], alignment=ft.MainAxisAlignment.START),
            padding=15, bgcolor="#fafafa", border_radius=8, border=ft.border.all(1, "#eeeeee")
        )
        
        filtros_row = ft.Row([
            self.search_filter_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            self.drop_tipo,
            self.drop_motivo,
            ft.Container(expand=True),
            self.btn_agregar_ajuste
        ], spacing=10)
        
        paginacion_row = ft.Row([
            ft.Container(expand=True),
            self.btn_prev,
            self.lbl_page_info,
            self.btn_next
        ], alignment=ft.MainAxisAlignment.END)

        self.content = ft.Column([
            ft.Text("Gestión y Ajustes de Inventario", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            kpi_bar,
            filtros_row,
            ft.Container(content=self.lista_ajustes, expand=True, bgcolor="#f5f5f5", border_radius=10, padding=10, shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))),
            paginacion_row
        ], expand=True)

    def _crear_modal_formulario(self):
        def on_tipo_change(e):
            tipo = self.form_tipo_ajuste.value
            if tipo == "ENTRADA":
                self.form_motivo.options = [ft.dropdown.Option(x) for x in ["Sobrante de Inventario", "Donación Entrante", "Devolución Cliente", "Otro (Entrada)"]]
            elif tipo == "SALIDA":
                self.form_motivo.options = [ft.dropdown.Option(x) for x in ["Daño / Merma", "Vencimiento", "Pérdida", "Consumo Familiar", "Consumo Cliente (Cortesía)", "Donación Saliente", "Otro (Salida)"]]
            else:
                self.form_motivo.options = []
            self.form_motivo.value = None
            if self.form_codigo.value:
                self.buscar_detalle_insumo(None)
            self.safe_update()

        def on_costo_change(e):
            try:
                nuevo_costo = float(self.form_costo.value.replace(',', '.') or 0)
                valor_inv = nuevo_costo * getattr(self, 'current_stock_modal', 0)
                self.lbl_valor_inv_modal.value = f"Valor del Inv: ${valor_inv:,.0f}"
            except ValueError:
                self.lbl_valor_inv_modal.value = "Valor del Inv: $0"
            self.safe_update()

        def on_seleccionar_insumo_manual(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            codigo = e.selection.key if hasattr(e, 'selection') and hasattr(e.selection, 'key') and e.selection.key else ""
            if not codigo:
                if "[" in texto and "]" in texto:
                    codigo = texto.split("]")[0].replace("[", "").strip()
                else:
                    codigo = texto.strip()
            self.form_codigo.value = codigo
            self.buscar_detalle_insumo(None)
            self.safe_update()

        self.form_tipo_ajuste = ft.Dropdown(label="Tipo de Movimiento", options=[ft.dropdown.Option("ENTRADA"), ft.dropdown.Option("SALIDA")], dense=True, expand=True, border_radius=8, on_change=on_tipo_change)

        self.form_codigo = ft.TextField(visible=False) # Guard de código en segundo plano

        self.txt_buscador_insumo = CustomAutoComplete(
            hint_text="Buscar por Código o Nombre...",
            on_select=on_seleccionar_insumo_manual,
            text_size=12,
            height=40,
            expand=True
        )

        self.form_nombre = ft.Text("Selecciona o busca un insumo...", color="grey", italic=True, size=13)
        self.lbl_stock_actual = ft.Text("Stock Sist: 0", weight="bold", color=Config.COLOR_PRIMARY, size=12)

        self.form_motivo = ft.Dropdown(label="Motivo del Ajuste", dense=True, expand=True, border_radius=8)
        self.form_cant = ft.TextField(label="Cantidad", expand=True, dense=True, border_radius=8)

        # Eliminamos el expand=True para evitar el desbordamiento vertical en la columna
        self.form_costo = ft.TextField(label="Costo Unitario ($)", dense=True, border_radius=8, on_change=on_costo_change)
        self.lbl_valor_inv_modal = ft.Text("Valor del Inv: $0", size=11, color="grey")

        self.form_obs = ft.TextField(label="Observación (Opcional)", expand=True, dense=True, multiline=True, min_lines=2, border_radius=8)

        return ft.AlertDialog(
            title=ft.Text("Registrar Ajuste de Inventario"),
            content=ft.Container(
                width=520,
                content=ft.Column([
                    # Buscador Inteligente
                    ft.Column([
                        ft.Row([self.txt_buscador_insumo])
                    ], spacing=0),
                    # Tarjeta de Insumo Seleccionado
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.INVENTORY_2, size=18, color=Config.COLOR_PRIMARY),
                            ft.Column([
                                self.form_nombre,
                                self.lbl_stock_actual
                            ], spacing=1, expand=True)
                        ]), 
                        padding=10, 
                        bgcolor="#f8f9fa", 
                        border_radius=8,
                        border=ft.border.all(1, "#e0e0e0")
                    ),
                    ft.Row([self.form_tipo_ajuste, self.form_motivo]),
                    ft.Row([
                        self.form_cant, 
                        ft.Column([self.form_costo, self.lbl_valor_inv_modal], expand=True, spacing=2)
                    ]),
                    ft.Row([self.form_obs])
                ], tight=True, spacing=12)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cerrar_modal()),
                ft.ElevatedButton("Guardar Ajuste", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=self.on_guardar_ajuste)
            ]
        )

    # --- Lógica de Negocio ---
    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def did_mount(self):
        if self.modal_ajuste not in self.page.overlay:
            self.page.overlay.append(self.modal_ajuste)
        if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        self.load_data()

    def buscar_detalle_insumo(self, e):
        codigo = self.form_codigo.value.strip()
        if not codigo: return
        detalle = self.db.get_insumo_detalle(codigo)
        if detalle:
            self.form_nombre.value = detalle.get("nombre", "")
            self.form_nombre.color = "black"
            self.current_stock_modal = float(detalle.get('stock_actual') or 0)
            self.lbl_stock_actual.value = f"Stock Sist: {self.current_stock_modal:g} unds"

            tipo = self.form_tipo_ajuste.value
            nuevo_costo = 0
            if tipo == "ENTRADA":
                nuevo_costo = float(detalle.get("costo_unitario") or 0)
                self.form_costo.value = str(nuevo_costo)
            elif tipo == "SALIDA":
                nuevo_costo = float(detalle.get("precio_venta") or 0)
                self.form_costo.value = str(nuevo_costo)
            else:
                nuevo_costo = float(detalle.get("costo_unitario") or 0)
                self.form_costo.value = str(nuevo_costo)

            valor_inv = nuevo_costo * self.current_stock_modal
            self.lbl_valor_inv_modal.value = f"Valor del Inv: ${valor_inv:,.0f}"
        else:
            self.form_nombre.value = "Insumo no encontrado."
            self.form_nombre.color = "red"
            self.current_stock_modal = 0
            self.lbl_stock_actual.value = "Stock Sist: 0"
            self.lbl_valor_inv_modal.value = "Valor del Inv: $0"
        self.safe_update()

    def abrir_modal_ajuste(self):
        self.modal_ajuste.title.value = "Registrar Ajuste de Inventario"
        
        # Cargar catálogo para sugerencias inteligentes
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.catalogo_cache = {i["codigo_insumo"]: i for i in insumos}
        self.txt_buscador_insumo.suggestions = [
            {"key": i["codigo_insumo"], "value": f"[{i['codigo_insumo']}] {i['nombre']}"}
            for i in insumos
        ]
        self.search_filter_autocomplete.suggestions = self.txt_buscador_insumo.suggestions

        # Limpiar valores del formulario
        self.form_tipo_ajuste.value = None
        self.form_tipo_ajuste.error_text = None
        
        self.form_motivo.options = []
        self.form_motivo.value = None
        self.form_motivo.error_text = None
        
        self.form_codigo.value = ""
        self.form_codigo.error_text = None
        
        self.form_nombre.value = "Selecciona o busca un insumo..."
        self.form_nombre.color = "grey"
        
        self.form_cant.value = ""
        self.form_cant.error_text = None
        
        self.form_costo.value = ""
        self.form_costo.error_text = None
        
        self.form_obs.value = ""
        self.form_obs.error_text = None
        
        self.txt_buscador_insumo.value = ""
        
        self.modal_ajuste.open = True
        if self.page:
            self.page.update()

    def cerrar_modal(self):
        self.modal_ajuste.open = False
        self.page.update()

    def on_guardar_ajuste(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if self.page:
            self.update()
            
        threading.Thread(target=self._on_guardar_ajuste_worker, args=(btn_control,), daemon=True).start()

    def _on_guardar_ajuste_worker(self, btn_control):
        try:
            self.form_codigo.error_text = None
            self.form_cant.error_text = None
            self.form_costo.error_text = None
            if self.page:
                self.page.update()
                
            try:
                codigo = self.form_codigo.value.strip()
                motivo_ui = self.form_motivo.value
                cant = float(self.form_cant.value.replace(',', '.'))
                costo = float(self.form_costo.value.replace(',', '.'))
                obs = self.form_obs.value.strip()
            except ValueError:
                self.mostrar_alerta("Error en los formatos numéricos. Usa números válidos para cantidad y costo.", "red")
                return

            if not codigo or not motivo_ui or cant <= 0:
                self.mostrar_alerta("Completa los campos obligatorios y asegúrate que la cantidad sea mayor a cero.", "red")
                return

            tipo_bd = self.mapa_motivos.get(motivo_ui)
            if not tipo_bd: return

            datos = {
                "codigo_insumo": codigo,
                "tipo_ajuste": tipo_bd,
                "cantidad": cant,
                "costo_unitario_congelado": costo,
                "costo_total_ajuste": cant * costo,
                "motivo_observacion": obs if obs else motivo_ui,
                "estado_registro": "VÁLIDO"
            }

            if self.db.insert_ajuste_individual(datos):
                self.mostrar_alerta("Ajuste registrado exitosamente.", "green")
                self.cerrar_modal()
                self.load_data()
            else:
                self.mostrar_alerta("Error al registrar en la base de datos.", "red")
        except Exception as ex:
            if self.page:
                self.mostrar_alerta(f"Error interno: {str(ex)}", "red")
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.page.update()

    def anular_registro(self, id_ajuste):
        if self.db.anular_ajuste(id_ajuste):
            self.mostrar_alerta("Registro anulado. El stock ha sido revertido.", "orange")
            self.load_data()
        else:
            self.mostrar_alerta("Error al anular.", "red")

    def mostrar_alerta(self, msj, color):
        self.page.snack_bar = ft.SnackBar(ft.Text(msj), bgcolor=color)
        self.page.snack_bar.open = True

    def _clear_date(self, e):
        self.date_picker.value = None
        self.btn_date.tooltip = "Filtrar por Fecha de Ajuste"
        self.btn_date.icon_color = None
        self.btn_clear_date.visible = False
        self._on_filter_change()
        
    def _on_filter_change(self):
        self.current_page = 1
        if self.date_picker.value:
            self.btn_date.tooltip = f"Fecha: {self.date_picker.value.strftime('%Y-%m-%d')}"
            self.btn_date.icon_color = "blue"
            self.btn_clear_date.visible = True
        self.render_table()
        
    def _prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_table()
            
    def _next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_table()

    def load_data(self):
        # Actualizar resúmenes globales
        kpis_inv = self.db.get_inventario_kpis()
        val_inv_base = kpis_inv.get('valor_inventario', 0)
        self.lbl_ent_actual.value = f"${val_inv_base:,.2f}"

        self.data_completa = self.db.get_ajustes_inventario()
        self.render_table(val_inv_base)

    def render_table(self, val_inv_base=None):
        if val_inv_base is None:
            # Recuperar el valor base desde el label si no se provee (eliminando caracteres de moneda)
            try:
                val_inv_base = float(self.lbl_ent_actual.value.replace('$', '').replace(',', ''))
            except:
                val_inv_base = 0.0

        self.lista_ajustes.controls.clear()
        
        filtro_texto = self.search_input_text.value.lower().strip() if self.search_input_text.value else ""
        filtro_fecha = self.date_picker.value.strftime("%Y-%m-%d") if self.date_picker.value else None
        filtro_tipo = self.drop_tipo.value
        filtro_motivo = self.drop_motivo.value
        
        filtered_data = []
        total_ent_pos = 0.0
        total_sal_neg = 0.0

        for aj in self.data_completa:
            es_entrada = aj["tipo_ajuste"] in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
            cat_info = aj.get("catalogo_insumos", {})
            nombre = cat_info.get("nombre", "Desconocido") if isinstance(cat_info, dict) else "Desconocido"
            
            # Reglas de coincidencia
            match_texto = filtro_texto in aj["codigo_insumo"].lower() or filtro_texto in nombre.lower()
            match_fecha = filtro_fecha is None or aj["fecha_ajuste"][:10] == filtro_fecha
            
            tipo_ajuste_str = "Entrada" if es_entrada else "Salida"
            match_tipo = filtro_tipo == "Todos" or filtro_tipo == tipo_ajuste_str
            match_motivo = filtro_motivo == "Todos" or filtro_motivo == aj["motivo_observacion"]
            
            if match_texto and match_fecha and match_tipo and match_motivo:
                filtered_data.append(aj)

            # Acumular KPIs sobre todos los datos VÁLIDOS del historial general, sin importar los filtros visuales.
            # (El usuario quiere ver el total global de impacto)
            if aj["estado_registro"] == "VÁLIDO":
                val_total = float(aj["costo_total_ajuste"])
                if es_entrada: total_ent_pos += val_total
                else: total_sal_neg += val_total

        import math
        self.total_records = len(filtered_data)
        self.total_pages = math.ceil(self.total_records / self.page_size) if self.total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = filtered_data[start_idx:end_idx]

        for aj in page_data:
            es_entrada = aj["tipo_ajuste"] in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
            val_total = float(aj["costo_total_ajuste"])
            val_total_str = f"${val_total:,.2f}"
            
            cat_info = aj.get("catalogo_insumos", {})
            nombre = cat_info.get("nombre", "Desconocido") if isinstance(cat_info, dict) else "Desconocido"

            # Tarjeta de Ajuste (Card UI)
            tipo_bg = "#e8f5e9" if es_entrada else "#ffebee"
            tipo_color = "green" if es_entrada else "red"
            badge_tipo = ft.Container(
                content=ft.Text("Entrada" if es_entrada else "Salida", color=tipo_color, weight="bold", size=12),
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                bgcolor=tipo_bg,
                border_radius=15
            )

            fila1_cabecera = ft.Row([
                ft.Row([ft.Icon(ft.icons.CALENDAR_MONTH, size=16, color="grey"), ft.Text(aj["fecha_ajuste"][:10], color="grey")]),
                badge_tipo
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            fila2_principal = ft.Row([
                ft.Container(content=ft.Text(f"[{aj['codigo_insumo']}] {nombre}", size=16, weight="bold"), expand=True),
                ft.Text(val_total_str, size=16, weight="bold", color=tipo_color)
            ])

            fila3_detalles = ft.Row([
                ft.Container(content=ft.Text(f"Motivo: {aj['motivo_observacion']}", size=13, color="grey"), expand=True),
                ft.Text(f"Cant: {aj['cantidad']}", size=13, color="grey", weight="bold"),
                ft.Text(f"Costo U: ${aj['costo_unitario_congelado']:,.2f}", size=13, color="grey")
            ], alignment=ft.MainAxisAlignment.START, spacing=20)

            tarjeta_content = [fila1_cabecera, fila2_principal, fila3_detalles]

            if aj["estado_registro"] == "VÁLIDO":
                fila4_acciones = ft.Column([
                    ft.Divider(height=1, color="#f0f0f0"),
                    ft.Row([
                        ft.TextButton("Anular Registro", icon=ft.icons.CANCEL, icon_color="red", style=ft.ButtonStyle(color="red"), on_click=lambda e, id_aj=aj["id_ajuste"]: self.anular_registro(id_aj))
                    ], alignment=ft.MainAxisAlignment.END)
                ])
                tarjeta_content.append(fila4_acciones)
            else:
                fila4_acciones = ft.Column([
                    ft.Divider(height=1, color="#f0f0f0"),
                    ft.Row([
                        ft.Text("Registro Anulado", color="grey", italic=True)
                    ], alignment=ft.MainAxisAlignment.END)
                ])
                tarjeta_content.append(fila4_acciones)

            tarjeta = ft.Container(
                content=ft.Column(tarjeta_content, spacing=8),
                bgcolor="white",
                padding=15,
                border_radius=8,
                border=ft.border.all(1, "#e0e0e0")
            )
            self.lista_ajustes.controls.append(tarjeta)
            
        # Actualización UI
        self.btn_prev.disabled = self.current_page <= 1
        self.btn_next.disabled = self.current_page >= self.total_pages
        self.lbl_page_info.value = f"Pág {self.current_page} de {self.total_pages} ({self.total_records} reg.)"

        # Configuración de KPIs Dinámicos
        self.lbl_ent_pos.value = f"+${total_ent_pos:,.2f}"
        self.lbl_sal_neg.value = f"-${total_sal_neg:,.2f}"
        
        impacto_neto = total_ent_pos - total_sal_neg
        self.lbl_ent_neto.value = f"{'+' if impacto_neto >= 0 else '-'}${abs(impacto_neto):,.2f}"
        
        self.lbl_ent_proyectado.value = f"${(val_inv_base + impacto_neto):,.2f}"

        if self.page:
            self.page.update()
````

## File: ui/views/inventario.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import math
from datetime import datetime
from ui.components.autocomplete import CustomAutoComplete

class InventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
        self.expand = True
        
        self.db = SupabaseClient()
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        # Variables de Ordenamiento por Servidor
        self.sort_col_name = "Insumo"
        self.sort_is_asc = True
        
        self.view_mode = "cards"
        self.btn_toggle_view = ft.IconButton(
            icon=ft.icons.TABLE_ROWS,
            tooltip="Cambiar a vista de Tabla",
            on_click=self.toggle_view
        )
        
        # Controles de Búsqueda
        def on_select_busqueda_inv(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            if "[" in texto and "]" in texto:
                query = texto.split("]")[0].replace("[", "").strip()
            else:
                query = texto.strip()
            self.search_input_text.value = query
            self.on_search(None)

        self.search_input_text = ft.TextField(visible=False)

        self.search_autocomplete = CustomAutoComplete(
            hint_text="Buscar por código o nombre...",
            on_select=on_select_busqueda_inv,
            text_size=12,
            expand=True
        )
        
        self.category_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            hint_text="Categoría",
            width=170,
            dense=True,
            border_radius=8,
            bgcolor="white",
            text_size=12,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_color=ft.colors.with_opacity(0.15, "black"),
            focused_border_color=Config.COLOR_PRIMARY,
            on_change=self.on_search
        )
        
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )
        
        self.btn_date_icon = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_OUTLINED,
            tooltip="Filtrar por Fecha de Corte",
            on_click=self.abrir_modal_info_fecha
        )

        self.dlg_filtro_fecha_info = ft.AlertDialog(
            title=ft.Text("Filtrar información por fecha", weight="bold", color=Config.COLOR_PRIMARY, size=16),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(
                        "Selecciona una fecha de corte para calcular la fotografía exacta del inventario en ese día.\n\n"
                        "El sistema reconstruirá el Stock Inicial, Compras, Ventas y Ajustes acumulados hasta la fecha seleccionada.",
                        size=12, color="grey"
                    )
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cerrar_modal_info_fecha()),
                ft.ElevatedButton("Seleccionar Fecha", icon=ft.icons.DATE_RANGE, bgcolor=Config.COLOR_PRIMARY, color="white", on_click=self.lanzar_date_picker)
            ]
        )
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Definición de la Tabla de Datos (Ajuste de espacios y ordenamiento)
        self.data_table = ft.DataTable(
            column_spacing=10, # Reduce el espacio entre columnas
            horizontal_margin=10,
            data_row_min_height=30, # Reduce la altura de las filas
            data_row_max_height=30,
            heading_row_height=40,
            sort_column_index=0,
            sort_ascending=True,
            columns=[
                ft.DataColumn(ft.Container(width=25)),
                ft.DataColumn(ft.Text("Código", weight="bold", size=10), on_sort=self.on_sort_table),
                ft.DataColumn(ft.Container(content=ft.Text("Insumo", weight="bold", size=10), width=250), on_sort=self.on_sort_table),
                ft.DataColumn(ft.Text("Categoría", weight="bold", size=10), on_sort=self.on_sort_table),
                ft.DataColumn(ft.Text("Ubicación", weight="bold", size=10)),
                ft.DataColumn(ft.Container(content=ft.Text("Stock Ini.", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text("Stock Mín.", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text("Entradas", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
                ft.DataColumn(ft.Container(content=ft.Text("Salidas", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
                ft.DataColumn(ft.Container(content=ft.Text("Stock Real", weight="bold", size=10, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
                ft.DataColumn(ft.Text("Costo Unit.", weight="bold", size=10), numeric=True),
                ft.DataColumn(ft.Text("Costo Total", weight="bold", size=10), numeric=True),
                ft.DataColumn(ft.Text("Precio Venta", weight="bold", size=10), numeric=True),
                ft.DataColumn(ft.Text("Venta Total", weight="bold", size=10), numeric=True),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        self.table_container = ft.Container(
            content=ft.Column(
                [self.data_table],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            )
        )
        
        self.table_wrapper = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [self.table_container],
                        scroll=ft.ScrollMode.ALWAYS
                    )
                ],
                scroll=ft.ScrollMode.ALWAYS,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            bgcolor="white",
            padding=5,
            border_radius=10,
            expand=True,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black")),
            visible=False
        )
        
        self.card_list_view = ft.ListView(expand=True, spacing=10, visible=True)
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        
        self.current_edit_context = None
        
        self.edit_panel_title = ft.Text("Editando Insumo", color="white", weight="bold", size=16)
        
        input_style = {
            "text_size": 13,
            "height": 40,
            "content_padding": 10,
            "bgcolor": "white",
            "color": "black",
            "border_color": ft.colors.with_opacity(0.3, "white"),
        }
        
        self.edit_stock_minimo = ft.TextField(width=120, **input_style)
        self.edit_costo = ft.TextField(width=120, **input_style)
        self.edit_margen = ft.Dropdown(
            width=100, 
            options=[ft.dropdown.Option(f"{p}%") for p in [10, 15, 20, 25, 30, 35]],
            **input_style
        )
        self.edit_precio = ft.TextField(width=120, **input_style)
        
        self.edit_categoria = ft.Dropdown(
            width=200, 
            **input_style
        )
        
        def calcular_precio(e):
            try:
                costo = float(self.edit_costo.value.replace(',', '.') or 0)
                if self.edit_margen.value:
                    margen_str = self.edit_margen.value.replace('%', '')
                    margen_dec = float(margen_str) / 100.0
                    if margen_dec < 1 and costo > 0:
                        # Fórmula financiera de margen sobre precio de venta
                        precio_calculado = costo / (1 - margen_dec)
                        self.edit_precio.value = f"{precio_calculado:.2f}"
            except ValueError:
                pass
            verificar_cambios_panel(e)

        def verificar_cambios_panel(e):
            if not self.current_edit_context: return
            item = self.current_edit_context['item']
            cambiado = False
            try:
                if str(int(self.edit_stock_minimo.value)) != str(int(item.get('stock_minimo', 5) or 5)): cambiado = True
                if str(float(self.edit_costo.value)) != str(float(item.get('costo_unitario') or 0)): cambiado = True
                if str(float(self.edit_precio.value)) != str(float(item.get('precio_venta') or 0)): cambiado = True
                if self.edit_categoria.value != str(item.get('categoria', '')): cambiado = True
            except ValueError:
                cambiado = False
                
            self.btn_guardar_edicion.disabled = not cambiado
            self.action_bar.update()

        self.edit_margen.on_change = calcular_precio
        self.edit_costo.on_change = calcular_precio
        self.edit_precio.on_change = verificar_cambios_panel
        self.edit_stock_minimo.on_change = verificar_cambios_panel
        self.edit_categoria.on_change = verificar_cambios_panel
        
        self.btn_guardar_edicion = ft.ElevatedButton(
            "Guardar Cambios",
            disabled=True,
            on_click=self.on_guardar_global,
            style=ft.ButtonStyle(
                bgcolor={ft.MaterialState.DISABLED: "#495057", ft.MaterialState.DEFAULT: "green"},
                color={ft.MaterialState.DISABLED: "white70", ft.MaterialState.DEFAULT: "white"},
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )
        
        self.btn_gestionar_ajustes = ft.OutlinedButton(
            "Gestionar Ajustes",
            icon=ft.icons.TUNE,
            style=ft.ButtonStyle(color="white"),
            on_click=self.on_gestionar_ajustes
        )
        
        self.action_bar = ft.Container(
            content=ft.Column([
                ft.Row([self.edit_panel_title, self.btn_gestionar_ajustes], alignment=ft.MainAxisAlignment.START, spacing=15),
                ft.Row([
                    ft.Column([
                        ft.Text("Stock Mínimo", color="white70", size=11, weight="bold"),
                        self.edit_stock_minimo
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Costo Unit.", color="white70", size=11, weight="bold"),
                        self.edit_costo
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Ganancia", color="white70", size=11, weight="bold"),
                        self.edit_margen
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Precio Venta", color="white70", size=11, weight="bold"),
                        self.edit_precio
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Categoría", color="white70", size=11, weight="bold"),
                        self.edit_categoria
                    ], spacing=4),
                    ft.Container(expand=True),
                    ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color="white"), on_click=self.on_cancelar_global),
                    self.btn_guardar_edicion
                ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=10),
            bgcolor=Config.COLOR_PRIMARY,
            padding=15,
            border_radius=10,
            visible=False,
            margin=ft.padding.only(top=10)
        )
        
        # Dashboard Resumen
        self.lbl_valor_inventario = ft.Text("$0", size=20, weight="bold", color="blue")
        self.lbl_ventas_total = ft.Text("$0", size=20, weight="bold", color="green")
        self.lbl_proyeccion_ventas = ft.Text("$0", size=20, weight="bold", color="blue")
        
        self.summary_container = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.INVENTORY, color="blue", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "blue"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Valorización del Inventario", size=12, color="grey", weight="bold"),
                        self.lbl_valor_inventario
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.ATTACH_MONEY, color="green", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "green"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Ingreso Total (Ventas)", size=12, color="grey", weight="bold"),
                        self.lbl_ventas_total
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.MONETIZATION_ON, color="blue", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "blue"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Proyección de Ventas", size=12, color="grey", weight="bold"),
                        self.lbl_proyeccion_ventas
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            )
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
        
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        self.panel_abierto = False
        self.fecha_historial_activa = datetime.now().strftime("%Y-%m-%d")
        self.filtro_tipo_timeline = "TODO" # "TODO", "COMPRAS", "VENTAS", "AJUSTES"
        self.codigos_filtro_activos = None

        self.date_picker_timeline = ft.DatePicker(on_change=self.on_date_timeline_change)

        self.lbl_tot_compras_dia = ft.Text("$0", size=11, weight="bold", color="teal700")
        self.lbl_tot_ventas_dia = ft.Text("$0", size=11, weight="bold", color="blue700")
        self.lbl_tot_neto_dia = ft.Text("$0", size=11, weight="bold")

        kpis_dia_row = ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("Compras Día", size=9, color="grey"), self.lbl_tot_compras_dia], spacing=1),
                ft.Container(width=1, height=20, bgcolor="#e0e0e0"),
                ft.Column([ft.Text("Ventas Día", size=9, color="grey"), self.lbl_tot_ventas_dia], spacing=1),
                ft.Container(width=1, height=20, bgcolor="#e0e0e0"),
                ft.Column([ft.Text("Balance", size=9, color="grey"), self.lbl_tot_neto_dia], spacing=1),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            padding=8, bgcolor="#f8f9fa", border_radius=6, border=ft.border.all(1, "#e0e0e0")
        )

        self.chip_filtro_timeline = ft.SegmentedButton(
            segments=[
                ft.Segment(value="TODO", label=ft.Text("Todo", size=10)),
                ft.Segment(value="COMPRAS", label=ft.Text("Compras", size=10)),
                ft.Segment(value="VENTAS", label=ft.Text("Ventas", size=10)),
                ft.Segment(value="AJUSTES", label=ft.Text("Ajustes", size=10)),
            ],
            selected={"TODO"},
            on_change=self.on_tipo_timeline_change,
            show_selected_icon=False
        )

        self.btn_fecha_timeline = ft.OutlinedButton(
            self.fecha_historial_activa,
            icon=ft.icons.CALENDAR_TODAY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=5),
            height=30,
            on_click=lambda e: self.date_picker_timeline.pick_date()
        )

        self.panel_timeline_list = ft.ListView(expand=True, spacing=6)

        self.right_panel = ft.Container(
            width=0, visible=False, bgcolor="white", border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.05, "black")),
            animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
            content=ft.Column([
                # Cabecera Panel
                ft.Container(
                    content=ft.Row([
                        ft.Text("Historial Diario", weight="bold", size=13, color=Config.COLOR_PRIMARY, expand=True),
                        self.btn_fecha_timeline,
                        ft.IconButton(ft.icons.CLOSE, icon_size=16, on_click=self.toggle_right_panel)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=10, bgcolor="#f4f6f8", border_radius=ft.border_radius.only(top_left=8, top_right=8)
                ),
                ft.Container(content=kpis_dia_row, padding=ft.padding.symmetric(horizontal=10)),
                ft.Container(content=self.chip_filtro_timeline, padding=ft.padding.symmetric(horizontal=10), alignment=ft.alignment.center),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Container(content=self.panel_timeline_list, expand=True, padding=10)
            ], spacing=8)
        )

        self.btn_toggle_panel = ft.IconButton(
            icon=ft.icons.HISTORY_TOGGLE_OFF,
            tooltip="Ver Historial del Día",
            on_click=self.toggle_right_panel
        )

        self.filtro_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.FILTER_ALT, size=16, color="white"),
                ft.Text("", size=12, color="white", weight="bold"),
                ft.IconButton(ft.icons.CLOSE, icon_size=14, icon_color="white", on_click=self.limpiar_filtro_factura, style=ft.ButtonStyle(padding=0), width=24, height=24)
            ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="blue700",
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=15,
            visible=False
        )

        self.lbl_titulo = ft.Text("Catálogo de Insumos", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        main_column = ft.Column([
            self.progress_bar,
            ft.Row([self.lbl_titulo, self.filtro_badge], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.summary_container,
            
            # Toolbar de Filtros
            ft.Container(
                content=ft.Row([
                    self.search_autocomplete,
                    self.category_dropdown,
                    self.btn_date_icon,
                    self.btn_clear_date,
                    self.btn_toggle_view,
                    self.btn_toggle_panel,
                    self.btn_fullscreen
                ]),
                bgcolor="white",
                padding=10,
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            # Contenedores de Vista Dual
            self.table_wrapper,
            self.card_list_view,
            
            # Footer Paginación
            ft.Container(
                content=ft.Row([
                    self.lbl_total,
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(top=10)
            ),
            self.action_bar
        ], expand=True, spacing=10)

        self.content = ft.Row([
            main_column,
            self.right_panel
        ], expand=True, spacing=10)
        
        # No llamamos a los métodos aquí porque el control no está en la página todavía
        
    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def did_mount(self):
        """Se ejecuta cuando la vista se agrega a la pantalla."""
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        if hasattr(self, "date_picker_timeline") and self.date_picker_timeline not in self.page.overlay:
            self.page.overlay.append(self.date_picker_timeline)
        if hasattr(self, "dlg_filtro_fecha_info") and self.dlg_filtro_fecha_info not in self.page.overlay:
            self.page.overlay.append(self.dlg_filtro_fecha_info)
        self.safe_update()
            
        # Lógica responsiva para la tabla
        def handle_resize(e):
            if getattr(self, "page", None) and getattr(self, "table_container", None):
                available = self.page.width - 320
                self.table_container.width = max(1300, available)
                try:
                    self.table_container.update()
                except Exception:
                    pass
                
        self.handle_resize = handle_resize
        
        # Suscribir de manera segura según la versión de Flet
        if hasattr(self.page.on_resize, "subscribe"):
            self.page.on_resize.subscribe(self.handle_resize)
        else:
            self.original_on_resize = self.page.on_resize
            self.page.on_resize = self.handle_resize
            
        handle_resize(None) # Ejecutar una vez para inicializar tamaño
            
        self.load_categories()
        self.load_summary()
        self.cargar_sugerencias_buscador()
        self.load_data()
        
    def cargar_sugerencias_buscador(self):
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.search_autocomplete.suggestions = [
            {"key": i["codigo_insumo"], "value": f"[{i['codigo_insumo']}] {i['nombre']}"}
            for i in insumos
        ]
        self.safe_update()
        

    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass
    def load_summary(self):
        res_v = self.db.get_ventas_summary()
        res_i = self.db.get_inventario_kpis()
        self.lbl_valor_inventario.value = f"${res_i.get('valor_inventario', 0):,.2f}"
        self.lbl_ventas_total.value = f"${res_v.get('total_mes', 0):,.2f}"
        # La proyección se calcula localmente en _fetch_data_worker
        self.safe_update()
            
    def will_unmount(self):
        """Se ejecuta cuando se destruye la vista."""
        if hasattr(self.page, "on_resize") and hasattr(self.page.on_resize, "unsubscribe") and hasattr(self, "handle_resize"):
            self.page.on_resize.unsubscribe(self.handle_resize)
        elif hasattr(self, "original_on_resize"):
            self.page.on_resize = self.original_on_resize
        
    def load_categories(self):
        cats = self.db.get_categorias()
        options = [ft.dropdown.Option("Todas")]
        for c in cats:
            if c: options.append(ft.dropdown.Option(c))
        self.category_dropdown.options = options
        
    def toggle_view(self, e):
        if self.view_mode == "table":
            self.view_mode = "cards"
            self.btn_toggle_view.icon = ft.icons.TABLE_ROWS
            self.btn_toggle_view.tooltip = "Cambiar a vista de Tabla"
            self.table_wrapper.visible = False
            self.card_list_view.visible = True
        else:
            self.view_mode = "table"
            self.btn_toggle_view.icon = ft.icons.GRID_VIEW
            self.btn_toggle_view.tooltip = "Cambiar a vista de Tarjetas"
            self.table_wrapper.visible = True
            self.card_list_view.visible = False
        self.safe_update()
        
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        self.safe_update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        search_val = self.search_input_text.value or self.search_autocomplete.value or ""
        cat_val = self.category_dropdown.value or "Todas"
        
        data, total = self.db.get_insumos(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val, 
            categoria=cat_val,
            fecha_corte=self.fecha_corte,
            sort_col=self.sort_col_name,
            sort_asc=self.sort_is_asc,
            codigos_filtro=self.codigos_filtro_activos
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        # Limpiar filas previas
        self.data_table.rows.clear()
        self.card_list_view.controls.clear()
        
        # Calcular Totales Globales iterando la lista completa sin paginación
        data_completa, _ = self.db.get_insumos(
            page=1, 
            page_size=999999, 
            search=search_val, 
            categoria=cat_val,
            fecha_corte=self.fecha_corte,
            sort_col=self.sort_col_name,
            sort_asc=self.sort_is_asc,
            codigos_filtro=self.codigos_filtro_activos
        )

        proyeccion_global = 0.0
        self.valor_total_inventario = 0.0
        
        for insumo in data_completa:
            stock = float(insumo.get("stock_actual") or insumo.get("stock_real") or 0)
            p_venta = float(insumo.get("precio_venta") or 0)
            
            if stock > 0:
                proyeccion_global += (stock * p_venta)
                
            self.valor_total_inventario += float(insumo.get("costo_total_insumo") or 0)
            
        self.lbl_proyeccion_ventas.value = f"${proyeccion_global:,.0f}"
        self.safe_update()
        
        # Llenar tabla y tarjetas
        total_entradas = 0
        total_salidas = 0
        
        for item in data:
            row = self._crear_fila_inventario(item)
            self.data_table.rows.append(row)
            self.card_list_view.controls.append(self._crear_tarjeta_inventario(item, row))
            
            
        self.update_pagination_ui()


    def crear_celdas_fila(self, item, row_ref, edit_mode=False):
        stock_inicial = int(item.get('stock_inicial', 0) or 0)
        stock_minimo = int(item.get('stock_minimo', 5) or 5)
        entradas = int(item.get('entradas', 0) or 0)
        salidas = int(item.get('salidas', 0) or 0)
        
        stock_final = int(item.get('stock_real', item.get('stock_actual', 0)) or 0)
        
        costo_unit = float(item.get('costo_unitario') or 0)
        precio_venta = float(item.get('precio_venta') or 0)
        costo_total = float(item.get('costo_total_insumo') or 0)
        venta_total = float(item.get('venta_total_insumo') or 0)
        
        str_costo_unit = f"${costo_unit:,.2f}"
        str_precio_venta = f"${precio_venta:,.2f}"
        str_costo_total = f"${costo_total:,.2f}"
        str_venta_total = f"${venta_total:,.2f}"
        
        color_entradas = "green" if entradas > 0 else "black"
        color_salidas = "red" if salidas > 0 else "black"
        color_stock = "blue" if stock_final > 0 else "red"
        
        codigo = str(item.get('codigo_insumo', ''))
        nombre = str(item.get('nombre', ''))
        categoria = str(item.get('categoria', ''))
        ubicacion = str(item.get('ubicacion') or 'N/A')

        checkbox = ft.Checkbox(value=False, on_change=lambda e, i=item, r=row_ref: self.toggle_edit(e, i, r))
        
        cells_data = [
            ft.DataCell(ft.Container(content=checkbox, width=25, alignment=ft.alignment.center)),
            ft.DataCell(ft.Text(codigo, size=10)),
            ft.DataCell(ft.Container(content=ft.Text(nombre, size=10, no_wrap=True, tooltip=nombre), width=250)),
            ft.DataCell(ft.Text(categoria, size=10)),
            ft.DataCell(ft.Text(ubicacion, size=10)),
            ft.DataCell(ft.Container(content=ft.Text(str(stock_inicial), size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Container(content=ft.Text(str(stock_minimo), size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Container(content=ft.Text(str(entradas), color=color_entradas, weight="bold", size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Container(content=ft.Text(str(salidas), color=color_salidas, weight="bold", size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Container(content=ft.Text(str(stock_final), color=color_stock, weight="bold", size=10), width=60, alignment=ft.alignment.center_right)),
            ft.DataCell(ft.Text(str_costo_unit, size=10)),
            ft.DataCell(ft.Text(str_costo_total, color="blue", size=10)),
            ft.DataCell(ft.Text(str_precio_venta, size=10)),
            ft.DataCell(ft.Text(str_venta_total, color="green", size=10)),
        ]
            
        return cells_data

    def abrir_edicion_desde_tarjeta(self, item, row_ref):
        # Simular que se marcó el checkbox de la tabla para mantener sincronía
        if len(row_ref.cells) > 0:
            cb = row_ref.cells[0].content.content
            if isinstance(cb, ft.Checkbox):
                cb.value = True
                self.safe_update()
                    
        class DummyEvent:
            class DummyControl:
                value = True
            control = DummyControl()
            
        self.toggle_edit(DummyEvent(), item, row_ref)

    def toggle_edit(self, e, item, row_ref):
        if not e.control.value:
            self.cancelar_edicion()
            return
            
        if self.current_edit_context and self.current_edit_context['row'] != row_ref:
            prev_row = self.current_edit_context['row']
            if prev_row and len(prev_row.cells) > 0:
                cb = prev_row.cells[0].content.content
                if isinstance(cb, ft.Checkbox):
                    cb.value = False
                    
        self.current_edit_context = {
            'item': item,
            'row': row_ref
        }
        
        codigo = item.get('codigo_insumo')
        nombre = item.get('nombre')
        
        self.edit_panel_title.value = f"Editando: [{codigo}] {nombre}"
        self.edit_stock_minimo.value = str(int(item.get('stock_minimo', 5) or 5))
        self.edit_costo.value = str(float(item.get('costo_unitario') or 0))
        self.edit_precio.value = str(float(item.get('precio_venta') or 0))
        
        # Recargar opciones frescas
        categorias_bd = self.db.get_categorias() if hasattr(self.db, 'get_categorias') else []
        opts = [ft.dropdown.Option(c) for c in categorias_bd if c]
        self.edit_categoria.options = opts

        # Limpiar dropdowns
        self.edit_margen.value = None

        # Asignar categoría exacta
        cat_val = str(item.get('categoria') or '').strip()
        if any(o.key == cat_val for o in opts):
            self.edit_categoria.value = cat_val
        elif opts:
            self.edit_categoria.value = opts[0].key
        else:
            self.edit_categoria.value = None
        
        self.btn_guardar_edicion.disabled = True
        self.action_bar.visible = True
        self.safe_update()

    def cancelar_edicion(self, e=None):
        if self.current_edit_context:
            row_ref = self.current_edit_context['row']
            if row_ref and len(row_ref.cells) > 0:
                cb = row_ref.cells[0].content.content
                if isinstance(cb, ft.Checkbox):
                    cb.value = False
        self.current_edit_context = None
        self.action_bar.visible = False
        self.safe_update()

    def abrir_dialogo_confirmacion(self):
        if not self.current_edit_context: return
        item = self.current_edit_context['item']
        
        cambios = []
        try:
            nuevo_stock_min = int(self.edit_stock_minimo.value)
            if nuevo_stock_min != int(item.get('stock_minimo', 5) or 5):
                cambios.append(f"Stock Mínimo: {int(item.get('stock_minimo', 5) or 5)} -> {nuevo_stock_min}")
                
            nuevo_costo = float(self.edit_costo.value)
            if nuevo_costo != float(item.get('costo_unitario') or 0):
                cambios.append(f"Costo Unitario: ${float(item.get('costo_unitario') or 0):.2f} -> ${nuevo_costo:.2f}")
                
            nuevo_precio = float(self.edit_precio.value)
            if nuevo_precio != float(item.get('precio_venta') or 0):
                cambios.append(f"Precio Venta: ${float(item.get('precio_venta') or 0):.2f} -> ${nuevo_precio:.2f}")
                
            nueva_cat = self.edit_categoria.value
            if nueva_cat != str(item.get('categoria', '')):
                cambios.append(f"Categoría: {item.get('categoria', '')} -> {nueva_cat}")
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error: Asegúrate de ingresar números válidos."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return

        if not cambios:
            self.cancelar_edicion()
            return

        resumen = "\n".join(cambios)
        
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Actualización"),
            content=ft.Text(f"Estás a punto de modificar el insumo: {item.get('codigo_insumo')} - {item.get('nombre')}.\n\nCambios detectados:\n{resumen}"),
        )
        
        def on_cancel(e):
            dlg.open = False
            self.safe_update()
            
        def on_save(e):
            self.ejecutar_guardado(dlg)
            
        dlg.actions = [
            ft.TextButton("Cancelar", on_click=on_cancel),
            ft.ElevatedButton("Guardar", bgcolor="green", color="white", on_click=on_save)
        ]
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()

    def ejecutar_guardado(self, dialog=None):
        if dialog:
            dialog.open = False
            
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        self.safe_update()
            
        threading.Thread(target=self._ejecutar_guardado_worker, daemon=True).start()

    def _ejecutar_guardado_worker(self):
        try:
            if not self.current_edit_context: return
            item = self.current_edit_context['item']
            
            try:
                datos_actualizados = {
                    "stock_minimo": int(self.edit_stock_minimo.value),
                    "costo_unitario": float(self.edit_costo.value),
                    "precio_venta": float(self.edit_precio.value),
                    "categoria": self.edit_categoria.value
                }
            except ValueError:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico al guardar."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()
                return
                
            codigo = item.get('codigo_insumo')
            exito = self.db.update_insumo(codigo, datos_actualizados)
            
            if exito:
                self.cancelar_edicion()
                
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Insumo {codigo} actualizado exitosamente."), bgcolor="green")
                self.page.snack_bar.open = True
                self.safe_update()
                
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al actualizar en Base de Datos."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()
                
            self.update_pagination_ui()

        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            self.safe_update()
        
    def update_pagination_ui(self):
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros en total"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        # Apagar indicador de carga al finalizar
        self.progress_bar.visible = False
        
        self.safe_update()
        
    def on_search(self, e):
        self.current_page = 1
        self.load_data()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()
            
    def close_notification(self, e):
        self.notification_banner.visible = False
        self.safe_update()
        
    def open_date_picker(self, e):
        self.date_picker.pick_date()
        
    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_date_icon.tooltip = f"Fecha: {self.fecha_corte}"
            self.btn_date_icon.icon_color = "blue"
            self.btn_clear_date.visible = True
            self.current_page = 1
            self.load_data()
            self.safe_update()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e):
        self.fecha_corte = None
        self.date_picker.value = None
        self.btn_date_icon.tooltip = "Filtrar por Fecha de Corte"
        self.btn_date_icon.icon_color = None
        self.btn_clear_date.visible = False
        self.current_page = 1
        self.load_data()
        self.safe_update()

    def abrir_modal_info_fecha(self, e):
        self.dlg_filtro_fecha_info.open = True
        self.safe_update()

    def cerrar_modal_info_fecha(self, e=None):
        self.dlg_filtro_fecha_info.open = False
        self.safe_update()

    def lanzar_date_picker(self, e):
        self.cerrar_modal_info_fecha()
        self.date_picker.pick_date()

    def on_sort_table(self, e: ft.DataColumnSortEvent):
        """Delega el ordenamiento a la base de datos solicitando una nueva carga de datos."""
        self.data_table.sort_column_index = e.column_index
        self.data_table.sort_ascending = e.ascending
        
        # Identificar qué columna se hizo clic basándose en el diccionario
        column_keys = list(self.columnas_def.keys())
        
        # Descontar las columnas que estén ocultas para encontrar el índice real
        visible_keys = [k for k in column_keys if self.columnas_visibles.get(k, True)]
        
        if e.column_index < len(visible_keys):
            self.sort_col_name = visible_keys[e.column_index]
        
        self.sort_is_asc = e.ascending
        self.current_page = 1 # Volver a la primera página tras ordenar
        self.load_data()

    def on_guardar_global(self, e):
        self.abrir_dialogo_confirmacion()

    def on_cancelar_global(self, e):
        self.cancelar_edicion()

    def on_gestionar_ajustes(self, e):
        # Placeholder para enviar el código del insumo seleccionado al futuro módulo de ajustes
        if self.current_edit_context:
            codigo = self.current_edit_context['item'].get('codigo_insumo')
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Redirigiendo a gestión de ajustes para el insumo {codigo}..."), bgcolor="blue")
            self.page.snack_bar.open = True
            self.safe_update()

    def _crear_fila_inventario(self, item):
        row = ft.DataRow(cells=[])
        row.cells = self.crear_celdas_fila(item, row, edit_mode=False)
        return row

    def _crear_tarjeta_inventario(self, item, row):
        codigo = str(item.get('codigo_insumo') or '')
        nombre = str(item.get('nombre') or '')
        categoria = str(item.get('categoria') or '')
        ubicacion = str(item.get('ubicacion') or 'N/A')
        
        # Extracción Segura
        stock_inicial = float(item.get("stock_inicial") or 0)
        valor_inicial = float(item.get("valor_inicial") or 0)
        compras = float(item.get("compras") or 0)
        valor_compras = float(item.get("valor_compras") or 0)
        ventas = float(item.get("ventas") or 0)
        valor_ventas = float(item.get("valor_ventas") or 0)
        ajustes_entrantes = float(item.get("ajustes_entrantes") or 0)
        valor_ajustes_entrantes = float(item.get("valor_ajustes_entrantes") or 0)
        ajustes_salientes = float(item.get("ajustes_salientes") or 0)
        valor_ajustes_salientes = float(item.get("valor_ajustes_salientes") or 0)
        neto_ajustes = float(item.get("neto_ajustes") or 0)
        valor_neto_ajustes = float(item.get("valor_neto_ajustes") or 0)
        
        stock_actual = float(item.get('stock_actual') or item.get('stock_real') or 0)
        costo_total_insumo = float(item.get('costo_total_insumo') or 0)
        costo_u = float(item.get('costo_unitario') or 0)
        p_venta = float(item.get('precio_venta') or 0)
        
        proyeccion_venta = stock_actual * p_venta if stock_actual > 0 else 0
        participacion = (costo_total_insumo / self.valor_total_inventario) * 100 if getattr(self, 'valor_total_inventario', 0) > 0 else 0
        
        # Badges Pastel
        badge_costo = ft.Container(content=ft.Text(f"Costo U: ${costo_u:,.0f}", size=11, weight="bold", color="grey800"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="grey100", border_radius=15)
        badge_pventa = ft.Container(content=ft.Text(f"Precio Venta: ${p_venta:,.0f}", size=11, weight="bold", color="grey800"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="grey100", border_radius=15)
        badge_peso = ft.Container(content=ft.Text(f"Peso Inv: {participacion:.1f}%", size=11, weight="bold", color="purple800"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="#f3e5f5", border_radius=15)
        badge_proy = ft.Container(content=ft.Text(f"Proy Venta: ${proyeccion_venta:,.0f}", size=11, weight="bold", color="blue800"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="#e3f2fd", border_radius=15)
        
        color_bg_stock = "#e8f5e9" if stock_actual > 0 else "#ffebee"
        color_txt_stock = "green800" if stock_actual > 0 else "red800"
        badge_stock = ft.Container(content=ft.Text(f"Stock Actual: {stock_actual:g} unds ($ {costo_total_insumo:,.0f})", size=11, weight="bold", color=color_txt_stock), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor=color_bg_stock, border_radius=15)
        
        contenedor_badges = ft.Row(
            [badge_costo, badge_pventa, badge_peso, badge_proy, badge_stock], 
            spacing=5, 
            alignment=ft.MainAxisAlignment.START,
            wrap=True
        )
        
        def crear_bloque_metricas(titulo, cantidad, valor, color_cant, color_valor):
            return ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Text(titulo, size=9, color="grey", weight="bold"),
                    ft.Text(f"{cantidad:g} unds", size=11, weight="bold", color=color_cant, no_wrap=True),
                    ft.Text(f"${valor:,.0f}", size=11, color=color_valor, weight="w500", no_wrap=True)
                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=4)
            )

        def crear_separador_vertical():
            return ft.Container(
                width=1,
                height=28,
                bgcolor="#e0e0e0",
                margin=ft.padding.symmetric(horizontal=6)
            )
            
        color_neto = "red" if valor_neto_ajustes < 0 else ("green" if valor_neto_ajustes > 0 else "grey")
            
        fila_resultados = ft.Container(
            content=ft.Row([
                crear_bloque_metricas("INICIAL", stock_inicial, valor_inicial, "grey", "grey"),
                crear_separador_vertical(),
                crear_bloque_metricas("COMPRAS", compras, valor_compras, "green700", "black87"),
                crear_separador_vertical(),
                crear_bloque_metricas("VENTAS", ventas, valor_ventas, "blue700", "black87"),
                crear_separador_vertical(),
                crear_bloque_metricas("AJUSTES (+)", ajustes_entrantes, valor_ajustes_entrantes, "green700", "green700"),
                crear_separador_vertical(),
                crear_bloque_metricas("AJUSTES (-)", ajustes_salientes, valor_ajustes_salientes, "red700", "red700"),
                crear_separador_vertical(),
                crear_bloque_metricas("NETO", neto_ajustes, valor_neto_ajustes, color_neto, color_neto)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#fafafa",
            padding=10,
            border_radius=8,
            border=ft.border.all(1, "#f0f0f0")
        )
        
        tarjeta = ft.Container(
            bgcolor="white",
            padding=15,
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"{categoria} | {ubicacion}", size=10, weight="bold", color="grey700"),
                        bgcolor="#f5f5f5", padding=ft.padding.symmetric(horizontal=8, vertical=2), border_radius=4
                    ),
                    ft.Text(f"[{codigo}] {nombre}", size=14, weight="bold", color="black87", expand=True),
                    ft.IconButton(icon=ft.icons.EDIT, icon_size=16, tooltip="Editar Insumo", on_click=lambda e, i=item, r=row: self.abrir_edicion_desde_tarjeta(i, r))
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                contenedor_badges,
                fila_resultados
            ], spacing=10)
        )
        return tarjeta

    def toggle_right_panel(self, e):
        self.panel_abierto = not self.panel_abierto
        self.right_panel.width = 340 if self.panel_abierto else 0
        self.right_panel.visible = self.panel_abierto
        self.right_panel.padding = 0
        self.btn_toggle_panel.icon = ft.icons.HISTORY if self.panel_abierto else ft.icons.HISTORY_TOGGLE_OFF
        if self.panel_abierto:
            self.cargar_historial_panel()
        self.safe_update()

    def on_date_timeline_change(self, e):
        if self.date_picker_timeline.value:
            self.fecha_historial_activa = self.date_picker_timeline.value.strftime("%Y-%m-%d")
            self.btn_fecha_timeline.text = self.fecha_historial_activa
            self.cargar_historial_panel()

    def on_tipo_timeline_change(self, e):
        if e.control.selected:
            self.filtro_tipo_timeline = list(e.control.selected)[0]
            self.cargar_historial_panel()

    def cargar_historial_panel(self):
        if not getattr(self, "page", None): return

        def worker():
            facturas = self.db.get_historial_facturas_dia(self.fecha_historial_activa)

            tot_compras = sum([f["total"] for f in facturas if f["tipo"] == "COMPRA"])
            tot_ventas = sum([f["total"] for f in facturas if f["tipo"].startswith("VENTA")])
            neto = tot_ventas - tot_compras

            self.lbl_tot_compras_dia.value = f"${tot_compras:,.0f}"
            self.lbl_tot_ventas_dia.value = f"${tot_ventas:,.0f}"
            self.lbl_tot_neto_dia.value = f"${neto:,.0f}"
            self.lbl_tot_neto_dia.color = "green700" if neto >= 0 else "red700"

            self.panel_timeline_list.controls.clear()

            for f in facturas:
                tipo = f["tipo"]
                # Aplicar filtro de pestaña
                if self.filtro_tipo_timeline == "COMPRAS" and tipo != "COMPRA": continue
                if self.filtro_tipo_timeline == "VENTAS" and not tipo.startswith("VENTA"): continue
                if self.filtro_tipo_timeline == "AJUSTES" and not tipo.startswith("AJUSTE"): continue

                self.panel_timeline_list.controls.append(self._crear_card_factura_timeline(f))

            if not self.panel_timeline_list.controls:
                self.panel_timeline_list.controls.append(
                    ft.Container(content=ft.Text("Sin movimientos registrados en esta fecha.", size=11, color="grey"), padding=20, alignment=ft.alignment.center)
                )

            self.safe_update()

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def _crear_card_factura_timeline(self, f):
        tipo = f["tipo"]

        # Estilos por tipo
        if tipo == "COMPRA":
            badge_bg, badge_col, badge_txt = "#e6f4ea", "teal800", f"COMPRA | {f['proveedor']}"
            icon_mat, icon_col = ft.icons.SHOPPING_CART, "teal"
        elif "VENTA" in tipo:
            subtipo = f.get("subtipo", "POS")
            badge_bg, badge_col = ("#e8f0fe", "blue800") if "POS" in tipo else ("#f3e8fd", "purple800")
            badge_txt = f"VENTA ({subtipo})"
            icon_mat, icon_col = ft.icons.RECEIPT_LONG, "blue"
        else:
            is_ent = tipo == "AJUSTE_ENTRADA"
            badge_bg, badge_col = ("#e6f4ea", "green800") if is_ent else ("#fce8e6", "red800")
            badge_txt = f"AJUSTE {'ENTRADA' if is_ent else 'SALIDA'}"
            icon_mat, icon_col = ft.icons.TUNE, "orange"

        badge = ft.Container(
            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_col, no_wrap=True),
            padding=ft.padding.symmetric(horizontal=6, vertical=2), bgcolor=badge_bg, border_radius=10
        )

        ref = f["ref"]
        desc_fact = f"Fact/Doc: {f['factura']}"

        card = ft.Container(
            content=ft.Row([
                ft.Icon(icon_mat, size=20, color=icon_col),
                # Detalle Factura
                ft.Column([
                    badge,
                    ft.Text(desc_fact, size=11, weight="bold", color="black87", no_wrap=True),
                ], expand=True, spacing=2),

                # Total Monetario
                ft.Text(f"${f['total']:,.0f}", size=11, weight="bold", color="black87")
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=8,
            border_radius=6,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#eeeeee"),
            on_click=lambda e, t=tipo, r=ref, d=desc_fact: self.aplicar_filtro_factura(t, r, d),
            ink=True
        )
        return card

    def aplicar_filtro_factura(self, tipo, ref, desc):
        self.progress_bar.visible = True
        self.safe_update()

        def worker():
            codigos = self.db.get_codigos_factura_especifica(tipo, ref)
            self.codigos_filtro_activos = codigos if codigos else []
            self.current_page = 1

            # Actualizar Badge superior
            lbl = self.filtro_badge.content.controls[1]
            lbl.value = f"Filtrado por: {desc}"
            self.filtro_badge.visible = True

            self._fetch_data_worker()

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def limpiar_filtro_factura(self, e=None):
        self.codigos_filtro_activos = None
        self.current_page = 1
        self.filtro_badge.visible = False
        self.progress_bar.visible = True
        self.safe_update()
        
        import threading
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()
````

## File: cargas_compras_locales.json
````json
{
    "2026-08-18": {
        "1": {
            "id": 1,
            "fecha": "2026-08-18",
            "pagina": 1,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-18_pag_1.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9273",
                    "numero_factura": "7957448",
                    "productos": [
                        {
                            "cantidad": 200.0,
                            "codigo_insumo": "0578",
                            "costo_unitario": 328.0,
                            "iva": 12464.0
                        }
                    ],
                    "proveedor": "AJOVER SAS"
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9274",
                    "numero_factura": "0174",
                    "productos": [
                        {
                            "cantidad": 16.5,
                            "codigo_insumo": "1347",
                            "costo_unitario": 13100.0,
                            "iva": 41069.0
                        }
                    ],
                    "proveedor": "Clientes Varios"
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9275",
                    "numero_factura": "040826",
                    "productos": [
                        {
                            "cantidad": 145.0,
                            "codigo_insumo": "1893",
                            "costo_unitario": 1933.0,
                            "iva": 53248.0
                        }
                    ],
                    "proveedor": "Clientes Varios"
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9276",
                    "numero_factura": "19284",
                    "productos": [
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "0471",
                            "costo_unitario": 7353.0,
                            "iva": 13971.0
                        },
                        {
                            "cantidad": 50.0,
                            "codigo_insumo": "4182",
                            "costo_unitario": 2815.0,
                            "iva": 26744.0
                        },
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "9104",
                            "costo_unitario": 5252.0,
                            "iva": 9979.0
                        },
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "9104",
                            "costo_unitario": 5252.0,
                            "iva": 9979.0
                        },
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "9104",
                            "costo_unitario": 5252.0,
                            "iva": 9979.0
                        }
                    ],
                    "proveedor": "DISTRIBUCIONES PUNTO CHEVERE SAS"
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9277",
                    "numero_factura": "639921",
                    "productos": [
                        {
                            "cantidad": 4000.0,
                            "codigo_insumo": "0581",
                            "costo_unitario": 296.0,
                            "iva": 224960.0
                        },
                        {
                            "cantidad": 10000.0,
                            "codigo_insumo": "0572",
                            "costo_unitario": 180.0,
                            "iva": 341617.0
                        },
                        {
                            "cantidad": 4000.0,
                            "codigo_insumo": "0573",
                            "costo_unitario": 296.0,
                            "iva": 224960.0
                        },
                        {
                            "cantidad": 60.0,
                            "codigo_insumo": "1514",
                            "costo_unitario": 3643.0,
                            "iva": 41531.0
                        },
                        {
                            "cantidad": 60.0,
                            "codigo_insumo": "1164",
                            "costo_unitario": 6056.0,
                            "iva": 0.0
                        },
                        {
                            "cantidad": 180.0,
                            "codigo_insumo": "0855",
                            "costo_unitario": 1555.0,
                            "iva": 53168.0
                        },
                        {
                            "cantidad": 36.0,
                            "codigo_insumo": "2206",
                            "costo_unitario": 3536.0,
                            "iva": 24186.0
                        },
                        {
                            "cantidad": 370.0,
                            "codigo_insumo": "0847",
                            "costo_unitario": 2269.0,
                            "iva": 159504.0
                        },
                        {
                            "cantidad": 148.0,
                            "codigo_insumo": "0848",
                            "costo_unitario": 2563.0,
                            "iva": 72072.0
                        },
                        {
                            "cantidad": 80.0,
                            "codigo_insumo": "0688",
                            "costo_unitario": 2643.0,
                            "iva": 40168.0
                        }
                    ],
                    "proveedor": "REPRESENTACIONES LASTRA SAS"
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9278",
                    "numero_factura": "639914",
                    "productos": [
                        {
                            "cantidad": 600.0,
                            "codigo_insumo": "2152",
                            "costo_unitario": 1311.0,
                            "iva": 149503.0
                        },
                        {
                            "cantidad": 180.0,
                            "codigo_insumo": "0855",
                            "costo_unitario": 1487.0,
                            "iva": 50869.0
                        },
                        {
                            "cantidad": 185.0,
                            "codigo_insumo": "0847",
                            "costo_unitario": 2227.0,
                            "iva": 78275.0
                        }
                    ],
                    "proveedor": "REPRESENTACIONES LASTRA SAS"
                }
            ]
        },
        "2": {
            "id": 2,
            "fecha": "2026-08-18",
            "pagina": 2,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-18_pag_2.pdf",
            "estado": "Nuevo"
        },
        "3": {
            "id": 3,
            "fecha": "2026-08-18",
            "pagina": 3,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-18_pag_3.pdf",
            "estado": "Nuevo"
        }
    }
}
````

## File: ui/views/cierre_inventario.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import datetime
import math
from dateutil.relativedelta import relativedelta

class CierreInventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        self.datos_cierre = {}
        
        # Variables de Paginación Interna
        self.page_size = 50
        self.current_page = 1
        self.total_pages = 1
        self.insumos_lista = []
        
        self.selected_items = set()
        self.filtro_busqueda = ""
        self.filtro_categoria = "Todas"
        self.filtro_estado = "Todos"
        
        # Filtros Visuales
        self.input_search = ft.TextField(hint_text="Buscar código o nombre...", prefix_icon=ft.icons.SEARCH, height=38, expand=True, dense=True, text_size=12, on_submit=self.on_filter_change)
        self.drop_categoria = ft.Dropdown(label="Categoría", options=[ft.dropdown.Option("Todas")], height=38, width=150, dense=True, text_size=12, content_padding=ft.padding.symmetric(horizontal=10, vertical=8), on_change=self.on_filter_change)
        self.drop_estado = ft.Dropdown(label="Estado", options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("PENDIENTE"), ft.dropdown.Option("AUDITADO"), ft.dropdown.Option("AJUSTADO")], value="Todos", height=38, width=150, dense=True, text_size=12, content_padding=ft.padding.symmetric(horizontal=10, vertical=8), on_change=self.on_filter_change)
        
        self.btn_masivo = ft.ElevatedButton("Aceptar Stock Seleccionado", icon=ft.icons.CHECK_BOX, bgcolor="green", color="white", on_click=self.abrir_modal_masivo)
        self.action_bar_masiva = ft.Row([self.btn_masivo], visible=False)
        
        # Mes Seleccionado por defecto (se actualiza al ver detalle)
        hoy = datetime.date.today()
        self.mes_seleccionado = hoy.strftime('%Y-%m')
        
        self.btn_iniciar_snapshot = ft.ElevatedButton(
            text='1. Generar Preliminar',
            icon=ft.icons.CAMERA_ALT,
            bgcolor=Config.COLOR_SECONDARY,
            color='white',
            on_click=self.on_generar_snapshot
        )
        
        self.btn_aprobar_cierre = ft.ElevatedButton(
            text='3. Aprobar Cierre',
            icon=ft.icons.CHECK_CIRCLE,
            bgcolor='green',
            color='white',
            disabled=True,
            on_click=self.on_aprobar_cierre
        )

        # Indicadores de Estado
        self.txt_estado_periodo = ft.Text('Estado: DESCONOCIDO', weight='bold')
        self.txt_progreso = ft.Text('Pendientes: 0 | Auditados: 0', color='grey')

        # Tabla de Auditoría
        self.data_table = ft.DataTable(
            column_spacing=20,
            data_row_min_height=50,
            data_row_max_height=50,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Checkbox(on_change=self.on_select_all_change)),
                ft.DataColumn(ft.Text('Código', weight='bold')),
                ft.DataColumn(ft.Text('Insumo', weight='bold')),
                ft.DataColumn(ft.Text('Inicial', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Entradas', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Salidas', weight='bold'), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text('Ajustes', weight='bold'), width=60), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text('Stock Actual', weight='bold'), width=80), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text('Físico', weight='bold'), width=80)),
                ft.DataColumn(ft.Text('Diferencia', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Costo Ajuste', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Observación', weight='bold')),
                ft.DataColumn(ft.Text('Estado', weight='bold')),
                ft.DataColumn(ft.Text('Acción', weight='bold')),
            ],
            rows=[]
        )

        self.table_wrapper = ft.Container(content=ft.Row([ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS, expand=True)], scroll=ft.ScrollMode.ALWAYS, expand=True), expand=True)
        self.card_list_view = ft.ListView(expand=True, spacing=10, visible=False)
        self.current_auditoria_id = None
        self.current_fisico = 0
        
        # Modal de Ajuste
        self.form_codigo = ft.TextField(label='Cód. Insumo', width=120, disabled=True)
        self.form_nombre = ft.Text('Nombre del Insumo...', color='grey', size=14, weight='bold')
        self.form_tipo_ajuste = ft.Dropdown(
            label='Tipo',
            options=[ft.dropdown.Option('ENTRADA'), ft.dropdown.Option('SALIDA')],
            width=150,
            disabled=True
        )
        self.form_motivo = ft.Dropdown(label='Motivo Específico', width=250)
        self.form_cant = ft.TextField(label='Cantidad Ajuste', width=150, disabled=True)
        self.form_costo = ft.TextField(label='Costo Unitario ($)', width=150)
        self.form_obs = ft.TextField(label='Observaciones (Opcional)', expand=True)

        self.modal_ajuste = ft.AlertDialog(
            title=ft.Text('Ingresar Ajuste de Cierre'),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Row([self.form_codigo, ft.Container(content=self.form_nombre, expand=True, padding=10, bgcolor='#f5f5f5', border_radius=8)]),
                    ft.Row([self.form_tipo_ajuste, self.form_motivo]),
                    ft.Row([self.form_cant, self.form_costo]),
                    ft.Row([self.form_obs])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda e: self.cerrar_modal_ajuste()),
                ft.ElevatedButton('Guardar Ajuste', bgcolor=Config.COLOR_PRIMARY, color='white', on_click=self.on_guardar_ajuste_modal)
            ]
        )

        # Controles Paginación Interfaz
        self.lbl_page_info = ft.Text('Página 1 de 1')
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, tooltip="Página Anterior", on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, tooltip="Página Siguiente", on_click=self.on_next_page, disabled=True)

        # Controles Dashboard Financiero
        self.lbl_valor_sistema = ft.Text("$0.00", size=15, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_ajustes_entrada = ft.Text('$0.00', size=16, weight='bold', color='green')
        self.lbl_cant_entrada = ft.Text('0 unds', size=10, color='grey')
        self.lbl_ajustes_salida = ft.Text('$0.00', size=16, weight='bold', color='red')
        self.lbl_cant_salida = ft.Text('0 unds', size=10, color='grey')
        self.lbl_neto_ajustes = ft.Text('$0.00', size=16, weight='bold')
        self.lbl_valor_fisico = ft.Text("$0.00", size=15, weight="bold", color="blue700")

        self.kpi_compacto = ft.Container(
            content=ft.Row([
                # Columna 1: Valorizaciones
                ft.Column([
                    ft.Text("COSTO DE INVENTARIO", size=10, weight="bold", color="grey"),
                    ft.Row([
                        ft.Column([ft.Text("Sistema Actual", size=10, color="grey"), self.lbl_valor_sistema]),
                        ft.Container(width=1, height=25, bgcolor="#e0e0e0", margin=ft.padding.symmetric(horizontal=10)),
                        ft.Column([ft.Text("Proyectado Tras Ajustes", size=10, color="grey"), self.lbl_valor_fisico]),
                    ])
                ], expand=True),
                
                ft.Container(width=1, height=35, bgcolor="#cccccc", margin=ft.padding.symmetric(horizontal=15)),
                
                # Columna 2: Impacto Auditado
                ft.Column([
                    ft.Text("DESVIACIONES Y AUDITORÍA", size=10, weight="bold", color="grey"),
                    ft.Row([
                        ft.Column([ft.Text("Sobrantes (+)", size=10, color="grey"), self.lbl_ajustes_entrada]),
                        ft.Container(width=1, height=25, bgcolor="#e0e0e0", margin=ft.padding.symmetric(horizontal=10)),
                        ft.Column([ft.Text("Faltantes (-)", size=10, color="grey"), self.lbl_ajustes_salida]),
                        ft.Container(width=1, height=25, bgcolor="#e0e0e0", margin=ft.padding.symmetric(horizontal=10)),
                        ft.Column([ft.Text("Neto Ajustes", size=10, color="grey"), self.lbl_neto_ajustes]),
                    ])
                ], expand=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="white", padding=12, border_radius=8, border=ft.border.all(1, "#e0e0e0")
        )

        # Controles vista_lista (Maestro)
        self.dt_periodos = ft.DataTable(
            column_spacing=20,
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
            ft.Container(
                content=ft.Column([self.dt_periodos], scroll=ft.ScrollMode.ALWAYS, expand=True),
                expand=True
            )
        ], visible=True, expand=True)

        # Controles vista_detalle (Detalle)
        self.view_mode = "table"
        self.btn_toggle_view = ft.IconButton(icon=ft.icons.GRID_VIEW, tooltip="Cambiar a Tarjetas", on_click=self.toggle_view)
        
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
        
        self.filtro_container = ft.Container(
            content=ft.Row([self.input_search, self.drop_categoria, self.drop_estado, self.btn_toggle_view, self.btn_fullscreen]),
            bgcolor="white", padding=10, border_radius=8,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black"))
        )
        self.btn_volver = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=self.on_volver_lista)
        self.lbl_titulo_detalle = ft.Text('Auditoría: ...', size=24, weight='bold', color=Config.COLOR_PRIMARY)
        
        self.btn_aceptar_stock_masivo = ft.ElevatedButton("Aceptar Stock de Cierre", bgcolor="green", color="white", on_click=self.abrir_modal_masivo)
        
        self.row_pasos_cierre = ft.ResponsiveRow([
            self._crear_tarjeta_paso(1, "Generar Preliminar", "Congela el stock actual para compararlo con el físico.", self.btn_iniciar_snapshot),
            self._crear_tarjeta_paso(2, "Ajustar y Aceptar", "Ingresa ajustes o acepta el stock del sistema.", self.btn_aceptar_stock_masivo),
            self._crear_tarjeta_paso(3, "Aprobar Cierre", "Consolida ajustes y finaliza el mes.", self.btn_aprobar_cierre)
        ], spacing=15)
        
        self.row_filtros = self.filtro_container
        
        self.header_row = ft.Row([
            self.btn_volver, 
            self.lbl_titulo_detalle, 
            ft.Container(expand=True), 
            self.txt_estado_periodo, 
            self.txt_progreso
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.vista_detalle = ft.Column([
            self.header_row,
            self.row_pasos_cierre,
            self.kpi_compacto,
            self.row_filtros,
            self.table_wrapper,
            self.card_list_view,
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.only(top=10)
            )
        ], visible=False, expand=True, spacing=15)

        self.content = ft.Column([self.vista_lista, self.vista_detalle], expand=True)


    def _crear_tarjeta_paso(self, numero, titulo, descripcion, control_accion):
        return ft.Container(
            col={"xs": 12, "md": 4},
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(str(numero), color="white", weight="bold", size=12), bgcolor=Config.COLOR_PRIMARY, width=22, height=22, border_radius=11, alignment=ft.alignment.center),
                    ft.Text(titulo, weight="bold", size=14, color=Config.COLOR_PRIMARY)
                ]),
                ft.Text(descripcion, size=11, color="grey"),
                ft.Container(content=control_accion, alignment=ft.alignment.center_right)
            ], spacing=5),
            bgcolor="white", padding=12, border_radius=10,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black"))
        )


    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def mostrar_alerta(self, msj, color="red"):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msj, color="white"), bgcolor=color)
            self.page.snack_bar.open = True
            self.safe_update()

    def did_mount(self):
        if self.modal_ajuste not in self.page.overlay:
            self.page.overlay.append(self.modal_ajuste)
        self.load_lista_periodos()


    # --- Nuevos Métodos de Filtro y Selección ---
    def on_filter_change(self, e):
        self.filtro_busqueda = self.input_search.value or ""
        self.filtro_categoria = self.drop_categoria.value or "Todas"
        self.filtro_estado = self.drop_estado.value or "Todos"
        self.current_page = 1
        self.render_view()
        self.safe_update()

    def actualizar_boton_masivo(self):
        cantidad = len(self.selected_items)
        if cantidad > 0:
            self.btn_aceptar_stock_masivo.text = f"Aceptar Stock Seleccionado ({cantidad})"
        else:
            self.btn_aceptar_stock_masivo.text = "Aceptar Stock de Cierre"
        self.safe_update()

    def on_select_all_change(self, e):
        is_checked = e.control.value
        estado_periodo = self.datos_cierre.get('estado', '')
        if is_checked:
            for item in self.insumos_lista:
                if estado_periodo != 'CERRADO' and item.get('estado') != 'APROBADO':
                    self.selected_items.add(item.get('id_auditoria'))
        else:
            self.selected_items.clear()
        self.actualizar_boton_masivo()
        self.render_view()
        self.safe_update()

    def on_item_select(self, e, id_auditoria):
        if e.control.value:
            self.selected_items.add(id_auditoria)
        else:
            self.selected_items.discard(id_auditoria)
        self.actualizar_boton_masivo()
        self.safe_update()

    def abrir_modal_masivo(self, e):
        ids_a_procesar = []
        is_global = False
        if len(self.selected_items) > 0:
            ids_a_procesar = list(self.selected_items)
            mensaje_principal = f"¿Deseas aceptar el stock del sistema para los {len(ids_a_procesar)} insumos seleccionados?"
        else:
            ids_a_procesar = [i['id_auditoria'] for i in self.insumos_lista if i.get('estado') == 'PENDIENTE']
            if not ids_a_procesar:
                self.mostrar_alerta("No hay insumos PENDIENTES para aceptar globalmente.", "orange")
                return
            is_global = True
            mensaje_principal = f"¿Deseas aceptar globalmente el stock para TODOS los {len(ids_a_procesar)} insumos pendientes?"
            
        try:
            val_sist = self.lbl_valor_sistema.value
            val_ent = self.lbl_ajustes_entrada.value
            val_sal = self.lbl_ajustes_salida.value
            val_neto = self.lbl_neto_ajustes.value
            val_proy = self.lbl_valor_fisico.value
        except:
            val_sist, val_ent, val_sal, val_neto, val_proy = "$0", "$0", "$0", "$0", "$0"
                
        def confirm_masivo(e):
            dialog.open = False
            self.safe_update()
            
            if hasattr(self, 'progress_bar'): self.progress_bar.visible = True
            self.safe_update()
            
            res = self.db.aceptar_stock_sistema_masivo(ids_a_procesar)
            if res.get("exito"):
                self.mostrar_alerta("Aceptación masiva completada con éxito.", "green")
                self.selected_items.clear()
                self.actualizar_boton_masivo()
                self.mostrar_detalle(self.mes_seleccionado) # Reload
            else:
                self.mostrar_alerta(f"Error masivo: {res.get('error')}", "red")
                if hasattr(self, 'progress_bar'): self.progress_bar.visible = False
                self.safe_update()

        resumen_ui = ft.Column([
            ft.Text(mensaje_principal, weight="bold", color="red" if is_global else "black"),
            ft.Text("Esto significa que declaras que la cantidad física coincide exactamente con la del sistema (Ajuste de $0).", size=11, color="grey"),
            ft.Divider(height=10),
            ft.Text("Estado Global de la Auditoría:", size=12, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Row([ft.Text("Valor del Sistema:", size=12), ft.Text(val_sist, size=12, weight="bold")]),
            ft.Row([ft.Text("Sobrantes Registrados:", size=12), ft.Text(val_ent, size=12, weight="bold", color="green")]),
            ft.Row([ft.Text("Faltantes Registrados:", size=12), ft.Text(val_sal, size=12, weight="bold", color="red")]),
            ft.Row([ft.Text("Impacto Neto Acumulado:", size=12), ft.Text(val_neto, size=12, weight="bold")]),
            ft.Row([ft.Text("Valor Físico Proyectado Final:", size=12), ft.Text(val_proy, size=13, weight="bold", color="blue")], spacing=5)
        ], spacing=5, tight=True)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmación Global" if is_global else "Confirmación Masiva"),
            content=ft.Container(width=450, content=resumen_ui),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or self.safe_update()),
                ft.ElevatedButton("Confirmar y Aceptar", bgcolor="green", color="white", on_click=confirm_masivo)
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.safe_update()


    def procesar_eliminar_ajuste(self, id_auditoria):
        def confirm_eliminar(e):
            dialog.open = False
            self.safe_update()
            
            if hasattr(self, 'progress_bar'): self.progress_bar.visible = True
            self.safe_update()
            
            res = self.db.eliminar_ajuste_cierre(id_auditoria)
            if res.get("exito"):
                self.mostrar_alerta("Ajuste eliminado correctamente.", "green")
                self.mostrar_detalle(self.mes_seleccionado) # Reload
            else:
                self.mostrar_alerta(f"Error al eliminar: {res.get('error')}", "red")
                if hasattr(self, 'progress_bar'): self.progress_bar.visible = False
                self.safe_update()

        dialog = ft.AlertDialog(
            title=ft.Text("Eliminar Ajuste"),
            content=ft.Text("¿Estás seguro de eliminar este ajuste? El insumo volverá a PENDIENTE."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or self.safe_update()),
                ft.ElevatedButton("Eliminar", bgcolor="red", color="white", on_click=confirm_eliminar)
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.safe_update()

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
                ft.DataCell(ft.ElevatedButton('Ver', tooltip="Ver Detalles del Cierre", on_click=lambda e, m=mes_periodo: self.mostrar_detalle(m)))
            ])
            self.dt_periodos.rows.append(row)
            
        if self.page:
            self.page.update()

    def mostrar_detalle(self, mes):
        self.vista_lista.visible = False
        self.vista_detalle.visible = True
        self.mes_seleccionado = mes
        
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        partes = mes.split('-')
        nombre_mes = meses[int(partes[1]) - 1]
        self.lbl_titulo_detalle.value = f"Auditoría: {nombre_mes} {partes[0]}"
        
        self.current_page = 1
        self.load_data_detalle()

    def on_volver_lista(self, e):
        self.vista_detalle.visible = False
        self.vista_lista.visible = True
        self.load_lista_periodos()

    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_view()

    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_view()

    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.month_dropdown.update()

    def on_generar_snapshot(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        self.btn_aprobar_cierre.disabled = True
            
        if self.page:
            self.page.update()
            
        threading.Thread(target=self._on_generar_snapshot_worker, args=(btn_control,), daemon=True).start()

    def _on_generar_snapshot_worker(self, btn_control):
        try:
            res = self.db.iniciar_snapshot_cierre(self.mes_seleccionado)
            if res.get('exito'):
                self.page.snack_bar = ft.SnackBar(ft.Text('Preliminar generado correctamente.'), bgcolor='green')
                self.mostrar_detalle(self.mes_seleccionado)
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {res.get("error", "Desconocido")}'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page:
                self.page.update()
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f'Error interno: {str(ex)}'), bgcolor='red')
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.page.update()

    def on_aprobar_cierre(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        self.btn_iniciar_snapshot.disabled = True
            
        if self.page:
            self.page.update()
            
        threading.Thread(target=self._on_aprobar_cierre_worker, args=(btn_control,), daemon=True).start()

    def _on_aprobar_cierre_worker(self, btn_control):
        try:
            id_periodo = self.datos_cierre.get('periodo', {}).get('id_periodo')
            if not id_periodo:
                return
                
            res = self.db.aprobar_cierre_mes(id_periodo, 'Administrador Sistema')
            if res.get('exito'):
                self.page.snack_bar = ft.SnackBar(ft.Text('Período cerrado y consolidado con éxito.'), bgcolor='green')
                self.load_data_detalle()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {res.get("error", "Desconocido")}'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page:
                self.page.update()
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f'Error interno: {str(ex)}'), bgcolor='red')
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.page.update()

    def load_data_detalle(self):
        import math
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado) or {}
        self.insumos_lista = self.datos_cierre.get('insumos', [])
        
        costos_fallback = self.db.get_catalogo_costos()
        for ins in self.insumos_lista:
            if not ins.get('costo_unitario_snapshot'):
                ins['costo_unitario_snapshot'] = costos_fallback.get(ins.get('codigo_insumo'), 0)
        
        total_records = len(self.insumos_lista)
        self.total_pages = math.ceil(total_records / self.page_size) if total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        self.render_view()

    def render_view(self):
        self.data_table.rows.clear()
        
        periodo = self.datos_cierre.get('periodo', {})
        resumen = self.datos_cierre.get('resumen', {})
        estado_periodo = periodo.get('estado', 'ABIERTO')
        
        # Validar fecha para Generar Preliminar
        hoy = datetime.date.today()
        partes_mes = self.mes_seleccionado.split('-')
        año_sel = int(partes_mes[0])
        mes_sel = int(partes_mes[1])
        mes_sig = mes_sel + 1
        año_sig = año_sel
        if mes_sig > 12:
            mes_sig = 1
            año_sig += 1
        fecha_habilitacion = datetime.date(año_sig, mes_sig, 1)
        
        if estado_periodo == 'ABIERTO' and hoy >= fecha_habilitacion:
            self.btn_iniciar_snapshot.disabled = False
            self.btn_iniciar_snapshot.tooltip = None
        else:
            self.btn_iniciar_snapshot.disabled = True
            if estado_periodo == 'ABIERTO':
                self.btn_iniciar_snapshot.tooltip = f'Disponible a partir del {fecha_habilitacion.strftime("%Y-%m-%d")}'
            else:
                self.btn_iniciar_snapshot.tooltip = 'Ya se generó el preliminar'

        if not self.datos_cierre or not self.datos_cierre.get('periodo'):
            self.txt_estado_periodo.value = 'Estado: NO INICIALIZADO'
            self.txt_estado_periodo.color = 'grey'
            self.txt_progreso.value = 'Requiere generar preliminar'
            self.btn_aceptar_stock_masivo.disabled = True
            self.btn_aprobar_cierre.disabled = True
            self.btn_aprobar_cierre.bgcolor = "grey"
            if self.page:
                self.page.update()
            return

        self.txt_estado_periodo.value = f'Estado: {estado_periodo} | '
        color_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, 'black')
        
        pendientes = resumen.get('pendientes', 0)
        listos = resumen.get('auditados', 0) + resumen.get('ajustados', 0)
        self.txt_progreso.value = f'Pendientes: {pendientes} | Listos: {listos}'

        if estado_periodo == "CERRADO":
            self.btn_aceptar_stock_masivo.disabled = True
            self.btn_aprobar_cierre.text = "3. Cierre Exitoso"
            self.btn_aprobar_cierre.icon = ft.icons.VERIFIED
            self.btn_aprobar_cierre.disabled = True
            self.btn_aprobar_cierre.bgcolor = "green900"
        elif estado_periodo == "ABIERTO":
            self.btn_aceptar_stock_masivo.disabled = True
            self.btn_aprobar_cierre.text = "3. Aprobar Cierre"
            self.btn_aprobar_cierre.icon = ft.icons.CHECK_CIRCLE
            self.btn_aprobar_cierre.disabled = True
            self.btn_aprobar_cierre.bgcolor = "grey"
        else:
            # PRELIMINAR o EN_AUDITORIA
            self.btn_aceptar_stock_masivo.disabled = False
            self.btn_aprobar_cierre.text = "3. Aprobar Cierre"
            self.btn_aprobar_cierre.icon = ft.icons.CHECK_CIRCLE
            self.btn_aprobar_cierre.disabled = (pendientes > 0)
            self.btn_aprobar_cierre.bgcolor = "grey" if pendientes > 0 else "green" 

        # Update category options
        categorias = set([item.get('categoria', 'Sin Categoría') for item in self.insumos_lista])
        opciones_cat = [ft.dropdown.Option("Todas")] + [ft.dropdown.Option(cat) for cat in sorted(list(categorias))]
        self.drop_categoria.options = opciones_cat

        # Apply filters
        filtered_data = []
        q = self.filtro_busqueda.lower()
        for item in self.insumos_lista:
            if q and q not in str(item.get('codigo_insumo','')).lower() and q not in str(item.get('nombre','')).lower():
                continue
            if self.filtro_categoria != "Todas" and item.get('categoria') != self.filtro_categoria:
                continue
            if self.filtro_estado != "Todos" and item.get('estado') != self.filtro_estado:
                continue
            filtered_data.append(item)

        # KPIs Financieros sobre datos filtrados o sobre todos? Sobre TODOS (insumos_lista)
        valor_sistema = 0.0
        valor_entrada = 0.0
        cant_entrada = 0.0
        valor_salida = 0.0
        cant_salida = 0.0

        for ins in self.insumos_lista:
            cant_sist = float(ins.get('cantidad_sistema') or 0)
            costo_u = float(ins.get('costo_unitario_snapshot') or 0)
            dif = ins.get('diferencia')

            valor_sistema += (cant_sist * costo_u)

            if dif is not None:
                dif_flt = float(dif)
                if dif_flt > 0:
                    valor_entrada += (dif_flt * costo_u)
                    cant_entrada += dif_flt
                elif dif_flt < 0:
                    valor_salida += (abs(dif_flt) * costo_u)
                    cant_salida += abs(dif_flt)

        valor_neto = valor_entrada - valor_salida
        valor_fisico = valor_sistema + valor_neto

        self.lbl_valor_sistema.value = f'${valor_sistema:,.2f}'
        self.lbl_ajustes_entrada.value = f'${valor_entrada:,.2f}'
        self.lbl_cant_entrada.value = f'+{cant_entrada:g} unds'
        self.lbl_ajustes_salida.value = f'${valor_salida:,.2f}'
        self.lbl_cant_salida.value = f'-{cant_salida:g} unds'
        self.lbl_neto_ajustes.value = f'${valor_neto:,.2f}'
        self.lbl_neto_ajustes.color = 'green' if valor_neto >= 0 else 'red'
        self.lbl_valor_fisico.value = f'${valor_fisico:,.2f}'

        # Paginacion sobre filtered_data
        total_filtered = len(filtered_data)
        self.total_pages = math.ceil(total_filtered / self.page_size) if total_filtered > 0 else 1
        
        if self.current_page > self.total_pages and self.total_pages > 0:
            self.current_page = self.total_pages

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = filtered_data[start_idx:end_idx]

        self.card_list_view.controls.clear()
        for insumo in page_data:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))
            self.card_list_view.controls.append(self._crear_tarjeta_auditoria(insumo, estado_periodo))

        self.lbl_page_info.value = f'Página {self.current_page} de {self.total_pages}'
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        self.actualizar_boton_masivo()

        if self.page:
            self.page.update()



    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)

        # Ocultar o mostrar las secciones superiores
        visibilidad = not self.is_fullscreen
        if hasattr(self, "header_row"): self.header_row.visible = visibilidad
        if hasattr(self, "row_pasos_cierre"): self.row_pasos_cierre.visible = visibilidad
        if hasattr(self, "kpi_compacto"): self.kpi_compacto.visible = visibilidad

        # Cambiar el icono y el tooltip del botón
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        self.safe_update()

    def toggle_view(self, e):
        if self.view_mode == "table":
            self.view_mode = "cards"
            self.table_wrapper.visible = False
            self.card_list_view.visible = True
            self.btn_toggle_view.icon = ft.icons.TABLE_ROWS
            self.btn_toggle_view.tooltip = "Cambiar a Tabla"
        else:
            self.view_mode = "table"
            self.table_wrapper.visible = True
            self.card_list_view.visible = False
            self.btn_toggle_view.icon = ft.icons.GRID_VIEW
            self.btn_toggle_view.tooltip = "Cambiar a Tarjetas"
        self.safe_update()

    def _crear_tarjeta_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo.get('id_auditoria')
        estado_insumo = insumo.get('estado', 'PENDIENTE')
        observacion = insumo.get('observacion') or ''
        cant_sistema = insumo.get('cantidad_sistema')
        cant_fisica = insumo.get('cantidad_fisica')
        diferencia = insumo.get('diferencia')
        
        stock_inicial = insumo.get('stock_inicial', 0)
        entradas = insumo.get('entradas', 0)
        salidas = insumo.get('salidas', 0)
        ajustes = insumo.get('ajustes', 0)
        stock_actual = insumo.get('stock_actual', 0)
        
        habilitar_txt_ajuste = estado_periodo == "PRELIMINAR" and estado_insumo != "APROBADO"
        
        check_row = ft.Checkbox(
            value=id_auditoria in self.selected_items,
            disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO'),
            on_change=lambda e: self.on_item_select(e, id_auditoria)
        )
        
        def on_txt_conteo_change(e):
            try:
                if e.control.value.strip() == "":
                    btn_ajuste.disabled = True
                else:
                    val = float(e.control.value.replace(',', '.'))
                    btn_ajuste.disabled = (val == cant_sistema)
            except ValueError:
                btn_ajuste.disabled = True
            self.safe_update()

        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else '',
            dense=True, width=80, text_size=13, content_padding=10, label="Conteo",
            disabled=not habilitar_txt_ajuste,
            on_change=on_txt_conteo_change
        )
        
        colores_estado = {"PENDIENTE": "grey", "AUDITADO": "green", "AJUSTADO": "orange", "APROBADO": "blue"}
        color_badge = colores_estado.get(estado_insumo, "black")
        badge_estado = ft.Container(
            content=ft.Text(estado_insumo, size=10, weight="bold", color="white"),
            bgcolor=color_badge, padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=10
        )
        
        txt_obs = ft.Container(
            content=ft.Text(f"Obs: {observacion}" if observacion else "Sin observaciones", size=11, color="grey", italic=True, no_wrap=True, tooltip=observacion),
            expand=True, padding=ft.padding.only(left=10)
        )
        
        botones_accion = []
        if estado_insumo == "PENDIENTE":
            botones_accion.append(ft.ElevatedButton("Aceptar", tooltip="Aceptar sin diferencias", icon=ft.icons.CHECK, bgcolor="green50", color="green900", on_click=lambda e, i_id=id_auditoria: self.procesar_aceptar_sistema(i_id), scale=0.85, disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO')))
            btn_ajuste_pendiente = ft.OutlinedButton("Ingresar Ajuste", tooltip="Registrar diferencia", icon=ft.icons.TUNE, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=True)
            botones_accion.append(btn_ajuste_pendiente)
            if txt_conteo.value:
                try:
                    if float(txt_conteo.value.replace(',', '.')) != cant_sistema:
                        btn_ajuste_pendiente.disabled = False
                except ValueError:
                    pass
            # Update the original btn_ajuste reference used by on_txt_conteo_change closure
            btn_ajuste = btn_ajuste_pendiente
        elif estado_insumo == "AUDITADO":
            btn_ajuste = ft.OutlinedButton("Editar Ajuste", tooltip="Modificar ajuste", icon=ft.icons.EDIT, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=(estado_periodo == 'CERRADO'))
            botones_accion.append(btn_ajuste)
            btn_ajuste.disabled = False if txt_conteo.value else True
        elif estado_insumo == "AJUSTADO":
            btn_ajuste = ft.OutlinedButton("Editar Ajuste", tooltip="Modificar ajuste", icon=ft.icons.EDIT, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=(estado_periodo == 'CERRADO'))
            botones_accion.append(btn_ajuste)
            botones_accion.append(ft.OutlinedButton("Eliminar Ajuste", tooltip="Descartar ajuste", icon=ft.icons.DELETE, icon_color="red", style=ft.ButtonStyle(color="red"), on_click=lambda e, i_id=id_auditoria: self.procesar_eliminar_ajuste(i_id), scale=0.85, disabled=(estado_periodo == 'CERRADO')))
            btn_ajuste.disabled = False if txt_conteo.value else True
        else:
            # Fallback (e.g., APROBADO) - disabled buttons or none
            btn_ajuste = ft.OutlinedButton("Bloqueado", tooltip="Acción no permitida", disabled=True, scale=0.85)
            botones_accion.append(btn_ajuste)

        cant_final = float(insumo.get("cantidad_fisica") if insumo.get("cantidad_fisica") is not None else insumo.get("cantidad_sistema", 0))
        costo_u = float(insumo.get("costo_unitario_snapshot") or 0)
        valor_total = cant_final * costo_u

        column_controls = [
            ft.Row([check_row, ft.Text(insumo.get('codigo_insumo', ''), weight="bold", color=Config.COLOR_PRIMARY), ft.Text(insumo.get('nombre', ''), expand=True, weight="bold")], alignment=ft.MainAxisAlignment.START),
            ft.Row([
                ft.Text(f"Inicial: {stock_inicial}", size=12),
                ft.Text(f"Entradas: {entradas}", size=12, color="green"),
                ft.Text(f"Salidas: {salidas}", size=12, color="red"),
                ft.Text(f"Ajustes: {ajustes}", size=12, color="orange"),
                ft.Text(f"Stock Sist: {stock_actual}", size=12, weight="bold", color="blue"),
            ], wrap=True),
            ft.Divider(height=1, color="#f0f0f0")
        ]

        if estado_periodo == "CERRADO":
            for btn in botones_accion:
                btn.disabled = True
            check_row.disabled = True
            
            label_cierre = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.LOCK, size=16, color="green900"),
                    ft.Text(f"Stock Cierre: {cant_final:g} unds", size=14, weight="bold", color="green900"),
                    ft.Text(f" | Costo Total: ${valor_total:,.2f}", size=14, weight="bold", color="green900")
                ]),
                bgcolor="#e8f5e9", padding=10, border_radius=8, margin=ft.padding.only(bottom=10, top=5)
            )
            column_controls.append(label_cierre)

        column_controls.append(
            ft.Row([
                txt_conteo,
                badge_estado,
                txt_obs,
                *botones_accion
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        return ft.Container(
            content=ft.Column(column_controls),
            bgcolor="#f8f9fa", padding=15, border_radius=8,
            border=ft.border.all(1, "#e9ecef")
        )

    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo.get('id_auditoria')
        estado_insumo = insumo.get('estado', 'PENDIENTE')
        observacion = insumo.get('observacion') or ''
        cant_sistema = insumo.get('cantidad_sistema')
        cant_fisica = insumo.get('cantidad_fisica')
        diferencia = insumo.get('diferencia')
        observacion = insumo.get('observacion') or ''
        
        # Nuevas variables del Monitor en Tiempo Real
        stock_inicial = insumo.get('stock_inicial', 0)
        entradas = insumo.get('entradas', 0)
        salidas = insumo.get('salidas', 0)
        ajustes = insumo.get('ajustes', 0)
        stock_actual = insumo.get('stock_actual', 0)
        
        costo_unit = float(insumo.get('costo_unitario_snapshot') or 0)
        
        str_dif = ''
        str_costo_ajuste = ''
        color_diferencia = 'black'

        if diferencia is not None:
            dif_flt = float(diferencia)
            str_dif = f'{dif_flt:g}'
            if dif_flt != 0:
                color_diferencia = 'red'
                str_costo_ajuste = f'${(abs(dif_flt) * costo_unit):,.2f}'
        
        habilitar_txt_ajuste = estado_periodo == "PRELIMINAR" and estado_insumo != "APROBADO"
        
        def on_txt_conteo_change(e):
            try:
                if e.control.value.strip() == "":
                    btn_ajuste.disabled = True
                else:
                    val = float(e.control.value.replace(',', '.'))
                    btn_ajuste.disabled = (val == cant_sistema)
            except ValueError:
                btn_ajuste.disabled = True
            self.safe_update()

        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else '',
            dense=True, width=80, text_size=13, content_padding=10,
            disabled=not habilitar_txt_ajuste,
            on_change=on_txt_conteo_change
        )

        check_row = ft.Checkbox(
            value=id_auditoria in self.selected_items,
            disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO'),
            on_change=lambda e: self.on_item_select(e, id_auditoria)
        )

        if estado_insumo == "AJUSTADO":
            btn_ajuste = ft.ElevatedButton(
                'Editar Ajuste',
                icon=ft.icons.EDIT,
                on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value),
                scale=0.85,
                disabled=(estado_periodo == 'CERRADO')
            )
            btn_eliminar = ft.IconButton(
                icon=ft.icons.DELETE,
                icon_color="red",
                on_click=lambda e, i_id=id_auditoria: self.procesar_eliminar_ajuste(i_id),
                scale=0.85,
                disabled=(estado_periodo == 'CERRADO')
            )
            acciones = ft.Row([btn_ajuste, btn_eliminar], spacing=2)
            
            # Initial validation hack
            btn_ajuste.disabled = False if txt_conteo.value else True
            
        else:
            btn_aceptar_sistema = ft.ElevatedButton(
                text="Aceptar",
                icon=ft.icons.CHECK,
                bgcolor="green50",
                color="green900",
                on_click=lambda e, i_id=id_auditoria: self.procesar_aceptar_sistema(i_id),
                scale=0.85,
                disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO')
            )
            btn_ajuste = ft.ElevatedButton(
                'Ingresar Ajuste',
                icon=ft.icons.TUNE,
                on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value),
                scale=0.85,
                disabled=True
            )
            acciones = ft.Row([btn_aceptar_sistema, btn_ajuste], spacing=2)
            
            # Trigger validation manually on start if value is pre-filled
            if txt_conteo.value:
                try:
                    if float(txt_conteo.value.replace(',', '.')) != cant_sistema:
                        btn_ajuste.disabled = False
                except ValueError:
                    pass

        return ft.DataRow(
            cells=[
                ft.DataCell(check_row),
                ft.DataCell(ft.Text(insumo.get('codigo_insumo', ''))),
                ft.DataCell(ft.Text(insumo.get('nombre', ''), width=150, no_wrap=True, tooltip=insumo.get('nombre'))),
                ft.DataCell(ft.Text(str(stock_inicial))),
                ft.DataCell(ft.Text(str(entradas), color='green')),
                ft.DataCell(ft.Text(str(salidas), color='red')),
                ft.DataCell(ft.Text(str(ajustes), color='orange')),
                ft.DataCell(ft.Text(str(stock_actual), weight='bold', color='blue')),
                ft.DataCell(txt_conteo),
                ft.DataCell(ft.Text(str_dif, color=color_diferencia)),
                ft.DataCell(ft.Text(str_costo_ajuste)),
                ft.DataCell(ft.Text(observacion, width=150, no_wrap=True, tooltip=observacion)),
                ft.DataCell(ft.Text(estado_insumo, size=11, weight='bold', color='grey')),
                ft.DataCell(acciones),
            ]
        )

    def abrir_modal_ajuste_cierre(self, insumo, fisico_txt):
        if not fisico_txt or str(fisico_txt).strip() == '':
            self.page.snack_bar = ft.SnackBar(ft.Text('Debe ingresar primero el conteo físico en la tabla'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()
            return
            
        try:
            fisico = float(fisico_txt)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text('El conteo físico no es un número válido'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()
            return
            
        stock_actual = float(insumo.get('cantidad_sistema') or insumo.get('stock_actual') or 0)
        diferencia = fisico - stock_actual
        
        self.form_codigo.value = insumo.get('codigo_insumo', '')
        self.form_nombre.value = insumo.get('nombre', '')
        self.form_nombre.color = 'black'
        self.form_costo.value = str(insumo.get('costo_unitario_snapshot', 0))
        self.form_cant.value = str(abs(diferencia))
        
        if diferencia > 0:
            self.form_tipo_ajuste.value = 'ENTRADA'
            self.form_motivo.options = [ft.dropdown.Option('SOBRANTE')]
            self.form_motivo.value = 'SOBRANTE'
        elif diferencia < 0:
            self.form_tipo_ajuste.value = 'SALIDA'
            self.form_motivo.options = [ft.dropdown.Option('FALTANTE')]
            self.form_motivo.value = 'FALTANTE'
        else:
            self.procesar_aceptar_sistema(insumo.get('id_auditoria'))
            return
            
        self.current_auditoria_id = insumo.get('id_auditoria')
        self.current_fisico = fisico
        self.modal_ajuste.open = True
        if self.page:
            self.page.update()

    def cerrar_modal_ajuste(self):
        self.modal_ajuste.open = False
        if self.page:
            self.page.update()

    def on_guardar_ajuste_modal(self, e):
        try:
            costo = float(self.form_costo.value)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text('Costo inválido'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()
            return
            
        obs = self.form_obs.value.strip()
        motivo = self.form_motivo.value
        obs_final = f"[{motivo}] {obs}" if obs else f"[{motivo}]"
        
        fisico = self.current_fisico 
        
        res = self.db.registrar_conteo_fisico(self.current_auditoria_id, fisico, costo, obs_final)
        if res.get('exito'):
            self.cerrar_modal_ajuste()
            self.load_data_detalle()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {res.get("error")}'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()

    def procesar_aceptar_sistema(self, id_auditoria):
        if not id_auditoria: return
        res = self.db.aceptar_stock_sistema(id_auditoria)
        if res.get('exito'):
            self.load_data_detalle()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {res.get("error")}'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()
````

## File: ui/views/dashboard.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import datetime

class DashboardView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        
        self.lbl_periodo_dash = ft.Text("Periodo: ...", size=13, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_estado_dash = ft.Text("Estado: ...", size=13, weight="bold")
        self.lbl_fecha_hora = ft.Text("...", size=12, color="grey")

        self.fecha_filtro_dash = None
        self.date_picker_dash = ft.DatePicker(on_change=self.on_fecha_dash_change)

        self.btn_fecha_dash = ft.OutlinedButton(
            text=f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')}",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_dash.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=38
        )
        self.btn_clear_fecha_dash = ft.IconButton(
            icon=ft.icons.CLEAR, icon_color="red", tooltip="Restablecer a Hoy",
            visible=False, on_click=self.limpiar_filtro_fecha_dash
        )

        badge_info = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Row([self.lbl_periodo_dash, ft.Text("|", color="grey", size=13), self.lbl_estado_dash], spacing=5),
                    ft.Row([ft.Icon(ft.icons.ACCESS_TIME, size=14, color="grey"), self.lbl_fecha_hora], spacing=5)
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                ft.Container(width=10),
                self.btn_fecha_dash,
                self.btn_clear_fecha_dash
            ], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
        )

        header_row = ft.Row([
            ft.Column([
                ft.Text("Dashboard General", size=28, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Resumen ejecutivo del sistema", size=14, color="grey"),
            ], spacing=2),
            badge_info
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Tarjetas de KPIs (Valores Iniciales) - SECCIÓN COSTOS
        self.val_inventario = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_compras = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_rotacion = ft.Text("N/D", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_compras_hoy = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        
        # SECCIÓN VENTAS
        self.val_ingresos = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_ventas_hoy = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_rentabilidad = ft.Text("0.0%", size=14, weight="bold", color="#2ecca0")
        self.val_proyeccion_ventas = ft.Text("$ 0", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_proyeccion_rentabilidad = ft.Text("0.0%", size=14, weight="bold", color="#2ecca0")
        
        self.kpi_costos_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Costo Inv. Actual", self.val_inventario, ft.icons.INVENTORY_2), col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(content=self._build_kpi_card("Total Compras (Mes)", self.val_compras, ft.icons.SHOPPING_BAG), col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(content=self._build_kpi_card("Compras (Hoy)", self.val_compras_hoy, ft.icons.MONEY_OFF), col={"xs": 12, "sm": 6, "md": 4}),
        ], spacing=10, run_spacing=10)

        self.kpi_ventas_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Total Ventas (Mes)", self.val_ingresos, ft.icons.TRENDING_UP), col={"xs": 12, "sm": 6, "md": 6}),
            ft.Container(content=self._build_kpi_card("Ventas (Hoy)", self.val_ventas_hoy, ft.icons.ATTACH_MONEY), col={"xs": 12, "sm": 6, "md": 6}),
        ], spacing=10, run_spacing=10)
        
        # Paso 3: Crear la Barra de Métricas Secundarias
        self.val_meta_diaria = ft.Text("$ 0 / día", size=13, weight="bold", color="teal700")

        self.kpi_secundarios = ft.Container(
            content=ft.Row([
                ft.Text("Objetivo Comercial:", weight="bold", color=Config.COLOR_PRIMARY, size=12),
                ft.Text("Proy. Ventas Stock:", size=12, color="grey"), self.val_proyeccion_ventas,
                ft.Text(" | Proy. Rentabilidad:", size=12, color="grey"), self.val_proyeccion_rentabilidad,
                ft.Container(width=1, height=20, bgcolor="#d0d0d0", margin=ft.padding.symmetric(horizontal=8)),
                ft.Icon(ft.icons.FLAG, size=16, color="teal700"),
                ft.Text("Meta Venta Diaria:", weight="bold", size=12, color="grey"), self.val_meta_diaria,
                ft.Container(expand=True),
                ft.Text("Rotación Global:", size=12, color="grey"), self.val_rotacion,
            ], spacing=5, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor="#f0f4f8", border_radius=8, border=ft.border.all(1, "#d0d7de")
        )

        # SECCIÓN AJUSTES
        self.col_ajustes_salida = ft.Column(spacing=5)
        self.col_ajustes_entrada = ft.Column(spacing=5)
        
        self.lbl_neto_ajustes_header = ft.Text("NETO: $0", weight="bold", size=16)
        header_ajustes = ft.Row([
            ft.Text("Impacto de Ajustes de Inventario (Mes Actual)", size=16, weight="bold", color=Config.COLOR_PRIMARY),
            self.lbl_neto_ajustes_header
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.panel_ajustes = ft.Row([
            # Panel Salida
            ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes de Salida (-)", size=16, weight="bold", color="red"),
                    ft.Divider(height=1),
                    self.col_ajustes_salida
                ]),
                bgcolor="white",
                padding=15,
                border_radius=8,
                expand=True,
                border=ft.border.all(1, "#f0f0f0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
            ),
            # Panel Entrada
            ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes de Entrada (+)", size=16, weight="bold", color="green"),
                    ft.Divider(height=1),
                    self.col_ajustes_entrada
                ]),
                bgcolor="white",
                padding=15,
                border_radius=8,
                expand=True,
                border=ft.border.all(1, "#f0f0f0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
            )
        ], spacing=15)

        # Botón para copiar resumen al portapapeles
        self.btn_copiar_resumen = ft.IconButton(
            icon=ft.icons.COPY_ROUNDED,
            icon_size=18,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Copiar Resumen Financiero al Portapapeles",
            on_click=self.copiar_resumen_kpis
        )
        
        header_kpis_row = ft.Row([
            ft.Text("Resumen Financiero y Operativo", size=20, weight="bold", color=Config.COLOR_PRIMARY),
            self.btn_copiar_resumen
        ], tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Ensamblaje del Layout
        self.seccion_kpis = ft.Column([
            header_kpis_row,
            self.kpi_costos_row,
            self.kpi_ventas_row,
            self.kpi_secundarios
        ], spacing=10)

        # SECCIÓN RESUMEN DE IMPUESTOS
        self.val_iva_generado_mes = ft.Text("$ 0", size=22, weight="bold", color="blue700")
        self.val_iva_generado_hoy = ft.Text("$ 0", size=22, weight="bold", color="blue700")
        self.val_iva_pagado_mes = ft.Text("$ 0", size=22, weight="bold", color="teal700")
        self.val_iva_pagado_hoy = ft.Text("$ 0", size=22, weight="bold", color="teal700")

        header_impuestos_row = ft.Row([
            ft.Text("Resumen de Impuestos", size=20, weight="bold", color=Config.COLOR_PRIMARY),
        ], tight=True)

        self.kpi_iva_generado_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("IVA Generado (Mes)", self.val_iva_generado_mes, ft.icons.RECEIPT_LONG), col={"xs": 12, "sm": 6}),
            ft.Container(content=self._build_kpi_card("IVA Generado (Hoy)", self.val_iva_generado_hoy, ft.icons.POINT_OF_SALE), col={"xs": 12, "sm": 6}),
        ], spacing=10, run_spacing=10)

        self.kpi_iva_pagado_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("IVA Pagado (Mes)", self.val_iva_pagado_mes, ft.icons.SHOPPING_CART_CHECKOUT), col={"xs": 12, "sm": 6}),
            ft.Container(content=self._build_kpi_card("IVA Pagado (Hoy)", self.val_iva_pagado_hoy, ft.icons.SHOPPING_BAG_OUTLINED), col={"xs": 12, "sm": 6}),
        ], spacing=10, run_spacing=10)

        self.seccion_impuestos = ft.Column([
            header_impuestos_row,
            self.kpi_iva_generado_row,
            self.kpi_iva_pagado_row
        ], spacing=10)

        self.seccion_ajustes = ft.Column([
            header_ajustes,
            self.panel_ajustes
        ], spacing=10)

        # Gráficos y Tablas
        # Series de datos (Grosor y puntas redondeadas)
        self.chart_ventas = ft.LineChartData(
            data_points=[], 
            color=ft.colors.BLUE_400,
            stroke_width=4, 
            curved=False,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE_400)
        )
        self.chart_compras = ft.LineChartData(
            data_points=[], 
            color="#2ecca0", 
            stroke_width=4, 
            curved=False,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, "#2ecca0")
        )
        
        # Contenedor de Categorías (Grilla Responsiva)
        self.categorias_row = ft.ResponsiveRow(columns=12, spacing=15, run_spacing=15)
        self.categorias_container = ft.Container(
            content=ft.Column([
                ft.Text("Rendimiento Detallado por Categoría", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.categorias_row
            ]),
            margin=ft.padding.only(top=10, bottom=10)
        )

        # Gráfico habilitando los ejes visuales
        self.line_chart = ft.LineChart(
            data_series=[self.chart_ventas, self.chart_compras],
            border=ft.border.all(1, "#f0f0f0"),
            min_y=0,
            min_x=0,
            expand=True,
            tooltip_bgcolor="white",
            left_axis=ft.ChartAxis(labels_size=50), 
            bottom_axis=ft.ChartAxis(labels_size=40), 
        )
        
        # Leyenda adaptada a fondo claro
        leyenda = ft.Row([
            ft.Row([ft.Container(width=12, height=12, bgcolor=ft.colors.BLUE_400, border_radius=6), ft.Text("Ingresos", size=12, weight="bold", color="black87")]),
            ft.Row([ft.Container(width=12, height=12, bgcolor="#2ecca0", border_radius=6), ft.Text("Costos", size=12, weight="bold", color="black87")]),
        ], spacing=30, alignment=ft.MainAxisAlignment.CENTER)
        
        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Text("Tendencia Diaria: Ingresos vs Costo de Ventas", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                leyenda,
                ft.Container(content=self.line_chart, height=320, margin=ft.padding.only(top=10))
            ]),
            bgcolor="white",
            padding=20,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        # Tables
        self.dt_ventas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", size=12)),
                ft.DataColumn(ft.Text("Producto", size=12)),
                ft.DataColumn(ft.Text("Unidades", size=12), numeric=True),
                ft.DataColumn(ft.Text("Ingreso Total", size=12), numeric=True)
            ],
            rows=[],
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            column_spacing=15,
        )
        
        self.dt_costos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", size=12)),
                ft.DataColumn(ft.Text("Producto", size=12)),
                ft.DataColumn(ft.Text("Valor Inv.", size=12), numeric=True),
                ft.DataColumn(ft.Text("Rotación", size=12))
            ],
            rows=[],
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            column_spacing=15,
        )
        
        table_ventas_container = ft.Container(
            content=ft.Column([
                ft.Text("Top 10 Productos con Mayor Ingreso", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.dt_ventas
            ], scroll=ft.ScrollMode.AUTO),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            col={"xs": 12, "md": 6}
        )
        
        table_costos_container = ft.Container(
            content=ft.Column([
                ft.Text("Top 10 Productos con Mayor Costo", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.dt_costos
            ], scroll=ft.ScrollMode.AUTO),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            col={"xs": 12, "md": 6}
        )
        
        self.tables_row = ft.ResponsiveRow([
            table_ventas_container,
            table_costos_container
        ], spacing=15, run_spacing=15)
        
        # Indicador de carga superior
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)

        # 2. Main content Column
        self.content = ft.Column([
            self.progress_bar, 
            header_row,
            ft.Divider(height=10, color="transparent"),
            self.seccion_kpis,
            ft.Divider(height=10, color="transparent"),
            self.seccion_impuestos, # <-- Ubicación antes del impacto de ajustes
            ft.Divider(height=10, color="transparent"),
            self.seccion_ajustes,
            ft.Divider(height=10, color="transparent"),
            self.categorias_container,
            ft.Divider(height=10, color="transparent"),
            self.chart_container,
            ft.Divider(height=10, color="transparent"),
            self.tables_row,
            ft.Container(height=30) # Bottom padding
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def did_mount(self):
        if not hasattr(self, "overlay_added"):
            self.page.overlay.append(self.date_picker_dash)
            self.overlay_added = True
        self.load_data()

    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        self.safe_update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def on_fecha_dash_change(self, e):
        if self.date_picker_dash.value:
            self.fecha_filtro_dash = self.date_picker_dash.value.strftime("%Y-%m-%d")
            self.btn_fecha_dash.text = f"Fecha: {self.date_picker_dash.value.strftime('%d/%m/%Y')}"
            self.btn_clear_fecha_dash.visible = True
            self.load_data()

    def limpiar_filtro_fecha_dash(self, e):
        self.fecha_filtro_dash = None
        self.date_picker_dash.value = None
        self.btn_fecha_dash.text = f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')}"
        self.btn_clear_fecha_dash.visible = False
        self.load_data()

    def _fetch_data_worker(self):
        """Ejecuta todas las llamadas HTTP síncronas sin congelar la ventana."""
        # Cargar contexto temporal
        mes_actual = datetime.date.today().strftime("%Y-%m")
        datos_cierre = self.db.obtener_estado_cierre(mes_actual)
        estado_periodo = datos_cierre.get('periodo', {}).get('estado', 'ABIERTO') if datos_cierre and datos_cierre.get('periodo') else 'ABIERTO'

        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        partes = mes_actual.split('-')
        nombre_mes = f"{meses[int(partes[1]) - 1]} {partes[0]}"

        self.lbl_periodo_dash.value = f"Periodo: {nombre_mes}"
        self.lbl_estado_dash.value = f"Estado: {estado_periodo}"

        colores_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
        self.lbl_estado_dash.color = colores_estado.get(estado_periodo, 'black')

        ahora = datetime.datetime.now()
        self.lbl_fecha_hora.value = ahora.strftime("%d/%m/%Y - %I:%M %p")

        # 1. Load KPIs
        kpis_cat = self.db.get_rendimiento_categorias_periodo(fecha_inicio=None, fecha_fin=self.fecha_filtro_dash)
        val_inv_real = sum([c["inventario_costo"] for c in kpis_cat])
        val_inv = val_inv_real
        self.val_inventario.value = f"$ {val_inv:,.0f}"
        
        res_cat = self.db.get_catalogo_summary(fecha_corte=self.fecha_filtro_dash)
        res_ven = self.db.get_ventas_summary(fecha_corte=self.fecha_filtro_dash)
        res_com = self.db.get_compras_summary(fecha_corte=self.fecha_filtro_dash)
        
        ingresos = float(res_ven.get('total_mes') or 0)
        compras = float(res_com.get('total_mes') or 0)
        
        ventas_hoy = float(res_ven.get('total_hoy') or 0)
        compras_hoy = float(res_com.get('total_hoy') or 0)
        
        self.val_ingresos.value = f"$ {ingresos:,.0f}"
        self.val_ventas_hoy.value = f"$ {ventas_hoy:,.0f}"
        self.val_compras.value = f"$ {compras:,.0f}"
        self.val_compras_hoy.value = f"$ {compras_hoy:,.0f}"

        # Extraer montos de IVA de Ventas y Compras
        iva_gen_mes = float(res_ven.get('iva_mes') or 0)
        iva_gen_hoy = float(res_ven.get('iva_hoy') or 0)
        iva_pag_mes = float(res_com.get('iva_mes') or 0)
        iva_pag_hoy = float(res_com.get('iva_hoy') or 0)

        self.val_iva_generado_mes.value = f"$ {iva_gen_mes:,.0f}"
        self.val_iva_generado_hoy.value = f"$ {iva_gen_hoy:,.0f}"
        self.val_iva_pagado_mes.value = f"$ {iva_pag_mes:,.0f}"
        self.val_iva_pagado_hoy.value = f"$ {iva_pag_hoy:,.0f}"
        
        rentabilidad = 0
        if ingresos > 0:
            rentabilidad = ((ingresos - compras) / ingresos) * 100
            
        self.val_rentabilidad.value = f"{rentabilidad:.1f}%"
        self.val_rentabilidad.color = "#2ecca0" if rentabilidad >= 0 else "#f26c61"
        
        # Basic rotacion (Ventas / Inventario)
        if val_inv > 0:
            rotacion_global = ingresos / val_inv
            self.val_rotacion.value = f"{rotacion_global:.2f}x"
        else:
            self.val_rotacion.value = "N/D"

        # Nuevos KPIs y Ajustes
        proyeccion_ventas = self.db.get_proyeccion_ventas(fecha_corte=self.fecha_filtro_dash)
        self.val_proyeccion_ventas.value = f"$ {proyeccion_ventas:,.0f}"
        
        proy_rent = 0
        if proyeccion_ventas > 0:
            proy_rent = ((proyeccion_ventas - val_inv) / proyeccion_ventas) * 100
        
        self.val_proyeccion_rentabilidad.value = f"{proy_rent:.1f}%"
        self.val_proyeccion_rentabilidad.color = "#2ecca0" if proy_rent >= 0 else "#f26c61"

        hoy_obj = datetime.datetime.strptime(self.fecha_filtro_dash, "%Y-%m-%d").date() if self.fecha_filtro_dash else datetime.date.today()
        if hoy_obj.month == 12:
            ultimo_dia_mes = datetime.date(hoy_obj.year, 12, 31).day
        else:
            ultimo_dia_mes = (datetime.date(hoy_obj.year, hoy_obj.month + 1, 1) - datetime.timedelta(days=1)).day
        dias_restantes = max(1, ultimo_dia_mes - hoy_obj.day + 1)
        restante_vender = max(0, proyeccion_ventas - ingresos)
        meta_diaria = restante_vender / dias_restantes
        self.val_meta_diaria.value = f"$ {meta_diaria:,.0f} / día"

        mes_actual = hoy_obj.strftime("%Y-%m")
        ajustes_bd = self.db.get_ajustes_mes(mes_actual, fecha_corte=self.fecha_filtro_dash)
        
        tipos_salida = {
            "Daño / Merma": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Vencimiento": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Pérdida": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Consumo Familiar": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Consumo Cliente (Cortesía)": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Donación Saliente": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Otro (Salida)": {"conteo": 0, "cantidad": 0, "costo": 0.0}
        }

        tipos_entrada = {
            "Sobrante de Inventario": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Donación Entrante": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Devolución Cliente": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Otro (Entrada)": {"conteo": 0, "cantidad": 0, "costo": 0.0}
        }
        
        for fila in ajustes_bd:
            tipo_bd = fila.get("tipo_ajuste", "")
            motivo_bd = fila.get("motivo_observacion", "")
            cant = float(fila.get("cantidad_total") or 0)
            costo = float(fila.get("costo_total") or 0)
            conteo = int(fila.get("conteo") or 0)
            
            asignado = False
            if tipo_bd in ("AJUSTE_ENTRADA", "ENTRADA_POR_SOBRANTE"):
                for key in tipos_entrada.keys():
                    if key.lower() in motivo_bd.lower():
                        tipos_entrada[key]["conteo"] += conteo
                        tipos_entrada[key]["cantidad"] += cant
                        tipos_entrada[key]["costo"] += costo
                        asignado = True
                        break
                if not asignado:
                    tipos_entrada["Otro (Entrada)"]["conteo"] += conteo
                    tipos_entrada["Otro (Entrada)"]["cantidad"] += cant
                    tipos_entrada["Otro (Entrada)"]["costo"] += costo
            else:
                for key in tipos_salida.keys():
                    if key.lower() in motivo_bd.lower():
                        tipos_salida[key]["conteo"] += conteo
                        tipos_salida[key]["cantidad"] += cant
                        tipos_salida[key]["costo"] += costo
                        asignado = True
                        break
                if not asignado:
                    # Fallback por tipo
                    if tipo_bd == "BAJA_VENCIMIENTO": k = "Vencimiento"
                    elif tipo_bd == "SALIDA_POR_FALTANTE": k = "Pérdida"
                    else: k = "Otro (Salida)"
                    tipos_salida[k]["conteo"] += conteo
                    tipos_salida[k]["cantidad"] += cant
                    tipos_salida[k]["costo"] += costo

        total_costo_entradas = sum([d["costo"] for d in tipos_entrada.values()])
        total_costo_salidas = sum([d["costo"] for d in tipos_salida.values()])
        
        total_cant_entradas = sum([d["cantidad"] for d in tipos_entrada.values()])
        total_cant_salidas = sum([d["cantidad"] for d in tipos_salida.values()])
        
        neto = total_costo_entradas - total_costo_salidas
        if neto > 0:
            self.lbl_neto_ajustes_header.value = f"NETO (POSITIVO): +${neto:,.0f}"
            self.lbl_neto_ajustes_header.color = "#2ecca0"
        elif neto < 0:
            self.lbl_neto_ajustes_header.value = f"NETO (NEGATIVO): -${abs(neto):,.0f}"
            self.lbl_neto_ajustes_header.color = "#f26c61"
        else:
            self.lbl_neto_ajustes_header.value = f"NETO: $0"
            self.lbl_neto_ajustes_header.color = "grey"

        # Limpiar columnas
        self.col_ajustes_entrada.controls.clear()
        self.col_ajustes_salida.controls.clear()

        # Render Entrada
        for key, datos in tipos_entrada.items():
            self.col_ajustes_entrada.controls.append(
                ft.Row([
                    ft.Text(f"{key} ({datos['conteo']})", size=12, color="black87", expand=True),
                    ft.Text(f"{datos['cantidad']:.0f} unds", size=12, color="grey"),
                    ft.Text(f"${datos['costo']:,.0f}", size=12, weight="bold", color="#2ecca0")
                ])
            )
            
        # Rellenar con espacio invisible para igualar simetría
        filas_faltantes = len(tipos_salida) - len(tipos_entrada)
        for _ in range(max(0, filas_faltantes)):
            self.col_ajustes_entrada.controls.append(
                ft.Container(height=18, content=ft.Text("")) # Fila transparente de relleno
            )
            
        self.col_ajustes_entrada.controls.append(ft.Divider(color="black12", height=10))
        self.col_ajustes_entrada.controls.append(
            ft.Row([
                ft.Text("TOTAL ENTRADAS", size=12, weight="bold"),
                ft.Text(f"{total_cant_entradas:.0f} unds", size=12, weight="bold", color="grey", expand=True, text_align=ft.TextAlign.CENTER),
                ft.Text(f"${total_costo_entradas:,.0f}", size=12, weight="bold", color="#2ecca0")
            ])
        )
        
        # Render Salida
        for key, datos in tipos_salida.items():
            self.col_ajustes_salida.controls.append(
                ft.Row([
                    ft.Text(f"{key} ({datos['conteo']})", size=12, color="black87", expand=True),
                    ft.Text(f"{datos['cantidad']:.0f} unds", size=12, color="grey"),
                    ft.Text(f"${datos['costo']:,.0f}", size=12, weight="bold", color="#f26c61")
                ])
            )
        self.col_ajustes_salida.controls.append(ft.Divider(color="black12", height=10))
        self.col_ajustes_salida.controls.append(
            ft.Row([
                ft.Text("TOTAL SALIDAS", size=12, weight="bold"),
                ft.Text(f"{total_cant_salidas:.0f} unds", size=12, weight="bold", color="grey", expand=True, text_align=ft.TextAlign.CENTER),
                ft.Text(f"${total_costo_salidas:,.0f}", size=12, weight="bold", color="#f26c61")
            ])
        )

        # 2. Load Chart Data (Nativo Flet)
        try:
            tendencia = self.db.get_tendencia_diaria(fecha_corte=self.fecha_filtro_dash)
            dias_ordenados = sorted(tendencia.keys())
            max_val_y = 0
            
            pts_ventas = []
            pts_compras = []
            etiquetas_x = []
            
            for i, dia in enumerate(dias_ordenados):
                v = float(tendencia[dia]["ventas"])
                c = float(tendencia[dia]["compras"])
                if v > max_val_y: max_val_y = v
                if c > max_val_y: max_val_y = c
                # Poner la fecha SOLO en el tooltip de arriba (compras) para que Flet no la duplique al apilar
                tt_compras = f"{dia}\nCostos: ${c:,.0f}"
                tt_ventas = f"Ingresos: ${v:,.0f}"
                estilo_tt = ft.TextStyle(size=12, weight="bold", color="black87")
                
                pts_ventas.append(ft.LineChartDataPoint(i, v, tooltip=tt_ventas, tooltip_style=estilo_tt))
                pts_compras.append(ft.LineChartDataPoint(i, c, tooltip=tt_compras, tooltip_style=estilo_tt))
                
                # Densidad en Eje X: Mostrar todos los días con la fecha completa rotada
                etiquetas_x.append(
                    ft.ChartAxisLabel(
                        value=i, 
                        label=ft.Container(
                            content=ft.Text(dia, size=9, color="grey"),
                            padding=ft.padding.only(top=10),
                            rotate=-0.5
                        )
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
                ft.ChartAxisLabel(value=step * intervalo_y, label=ft.Text(formato_moneda_corta(step * intervalo_y), size=11, color="grey"))
                for step in range(9)
            ]
            
            self.line_chart.left_axis.labels = etiquetas_y
            self.line_chart.left_axis.labels_interval = intervalo_y
            self.line_chart.bottom_axis.labels = etiquetas_x
            self.line_chart.bottom_axis.labels_interval = 1
            
            # Cuadrícula visible completa con efecto punteado
            self.line_chart.horizontal_grid_lines = ft.ChartGridLines(
                interval=intervalo_y,
                color=ft.colors.with_opacity(0.05, "black"),
                width=1,
                dash_pattern=[4, 4]
            )
            self.line_chart.vertical_grid_lines = ft.ChartGridLines(
                interval=2, # Línea vertical sincronizada con el eje X
                color=ft.colors.with_opacity(0.05, "black"),
                width=1,
                dash_pattern=[4, 4]
            )
            
        except Exception as e:
            print(f"Error crítico construyendo Chart Flet: {e}")
        
        # 3. Load Tables Data (A prueba de fallos)
        try:
            top_ventas = self.db.get_top_ventas_mes(limit=10, fecha_corte=self.fecha_filtro_dash)
            self.dt_ventas.rows.clear()
            for item in top_ventas:
                self.dt_ventas.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(item.get('codigo') or ''), size=11)),
                        ft.DataCell(ft.Container(content=ft.Text(str(item.get('producto') or ''), size=11, no_wrap=True), width=120)),
                        ft.DataCell(ft.Text(str(item.get('unidades_vendidas') or 0), size=11)),
                        ft.DataCell(ft.Text(f"${float(item.get('ingreso_total') or 0):,.2f}", size=11))
                    ])
                )
        except Exception as e:
            print(f"Error crítico en tabla ventas: {e}")
            
        try:
            top_costos = self.db.get_top_costo_inventario(limit=10, fecha_corte=self.fecha_filtro_dash)
            self.dt_costos.rows.clear()
            for item in top_costos:
                self.dt_costos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(item.get('codigo') or ''), size=11)),
                        ft.DataCell(ft.Container(content=ft.Text(str(item.get('producto') or ''), size=11, no_wrap=True), width=120)),
                        ft.DataCell(ft.Text(f"${float(item.get('valor_inventario') or 0):,.2f}", size=11)),
                        ft.DataCell(ft.Text(str(item.get('rotacion') or ''), size=11))
                    ])
                )
        except Exception as e:
            print(f"Error crítico en tabla costos: {e}")
            
        try:
            self.categorias_row.controls.clear()
            for cat in kpis_cat:
                self.categorias_row.controls.append(self._crear_card_categoria(cat))
        except Exception as e:
            print(f"Error cargando KPIs por categoría: {e}")
            
        # Apagar indicador de carga al finalizar todo el trabajo
        self.progress_bar.visible = False
        
        self.safe_update()

    def _build_kpi_card(self, title, value_control, icon, subtext_control=None):
        column_controls = [
            ft.Row([
                ft.Text(title, size=12, color="grey", weight="w500", expand=True),
                ft.Icon(ft.icons.HELP_OUTLINE, size=12, color="grey")
            ], spacing=5),
            value_control,
        ]
        if subtext_control:
            column_controls.append(subtext_control)
            
        value_control.size = 20
            
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=Config.COLOR_SECONDARY, size=24),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_SECONDARY),
                    padding=10,
                    border_radius=8
                ),
                ft.Column(column_controls, spacing=2, expand=True)
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
        )

    def _crear_card_categoria(self, cat_data):
        nombre = cat_data["categoria"]
        inv_costo = cat_data["inventario_costo"]
        ventas = cat_data["ventas_realizadas"]
        proy_venta = cat_data["proyeccion_venta"]
        cumplimiento = cat_data["cumplimiento_pct"]
        rotacion = cat_data["rotacion"]
        rendimiento = cat_data["rendimiento_pct"]
    
        # Color condicional para cumplimiento
        color_cumplimiento = "green700" if cumplimiento >= 50 else ("orange700" if cumplimiento > 0 else "grey")
        color_rendimiento = "green700" if rendimiento >= 0 else "red700"
    
        return ft.Container(
            content=ft.Column([
                # Cabecera Categoría
                ft.Row([
                    ft.Icon(ft.icons.CATEGORY_OUTLINED, size=16, color=Config.COLOR_PRIMARY),
                    ft.Text(nombre.upper(), weight="bold", size=12, color=Config.COLOR_PRIMARY, expand=True)
                ]),
                ft.Divider(height=1, color="#eeeeee"),
                
                # Fila 1: Inventario Costo vs Ventas
                ft.Row([
                    ft.Text("Inventario (Costo):", size=11, color="grey", expand=True),
                    ft.Text(f"${inv_costo:,.0f}", size=11, weight="bold")
                ]),
                ft.Row([
                    ft.Text("Ventas Realizadas:", size=11, color="grey", expand=True),
                    ft.Text(f"${ventas:,.0f}", size=11, weight="bold", color="green700")
                ]),
                
                # Fila 2: Proyección Venta vs % Cumplimiento
                ft.Row([
                    ft.Text("Proyección Venta:", size=11, color="grey", expand=True),
                    ft.Text(f"${proy_venta:,.0f}", size=11, weight="bold", color="blue700")
                ]),
                ft.Row([
                    ft.Text("% Cumplimiento:", size=11, color="grey", expand=True),
                    ft.Text(f"{cumplimiento:.1f}%", size=11, weight="bold", color=color_cumplimiento)
                ]),
                
                ft.Divider(height=1, color="#f0f0f0"),
                
                # Fila 3: Rotación y Rendimiento Real
                ft.Row([
                    ft.Text("Rotación:", size=11, color="grey"),
                    ft.Text(f"{rotacion:.2f}x", size=11, weight="bold"),
                    ft.Container(expand=True),
                    ft.Text("Rendimiento Real:", size=11, color="grey"),
                    ft.Text(f"{rendimiento:.1f}%", size=11, weight="bold", color=color_rendimiento)
                ])
            ], spacing=4),
            padding=12,
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.colors.with_opacity(0.03, "black")),
            col={"sm": 12, "md": 6, "lg": 4}
        )

    def copiar_resumen_kpis(self, e):
        """
        Construye un texto formateado con todos los indicadores actuales
        del resumen financiero y lo guarda en el portapapeles del sistema.
        """
        periodo = self.lbl_periodo_dash.value.replace("Periodo: ", "").strip()
        fecha_hora = self.lbl_fecha_hora.value
        
        texto_copia = (
            f"📊 RESUMEN FINANCIERO Y OPERATIVO ({periodo.upper()})\n"
            f"📅 Generado el: {fecha_hora}\n"
            f"-----------------------------------------\n"
            f"💰 COSTOS E INVENTARIO:\n"
            f"  • Costo Inv. Actual: {self.val_inventario.value}\n"
            f"  • Total Compras (Mes): {self.val_compras.value}\n"
            f"  • Compras (Hoy): {self.val_compras_hoy.value}\n\n"
            f"📈 VENTAS E INGRESOS:\n"
            f"  • Total Ventas (Mes): {self.val_ingresos.value}\n"
            f"  • Ventas (Hoy): {self.val_ventas_hoy.value}\n"
            f"  • Margen Rentabilidad: {self.val_rentabilidad.value}\n\n"
            f"🎯 OBJETIVOS Y PROYECCIONES:\n"
            f"  • Proy. Ventas Stock: {self.val_proyeccion_ventas.value}\n"
            f"  • Proy. Rentabilidad: {self.val_proyeccion_rentabilidad.value}\n"
            f"  • Meta Venta Diaria: {self.val_meta_diaria.value}\n"
            f"  • Rotación Global: {self.val_rotacion.value}\n"
            f"-----------------------------------------"
        )

        if self.page:
            self.page.set_clipboard(texto_copia)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="white", size=18),
                    ft.Text("Resumen financiero copiado al portapapeles exitosamente", color="white")
                ]),
                bgcolor="green700"
            )
            self.page.snack_bar.open = True
            self.safe_update()
````

## File: ui/views/informes.py
````python
import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
import datetime
from calendar import monthrange
import threading

class InformesView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        self.save_pdf_picker = ft.FilePicker(on_result=self._save_pdf_result)
        self.save_excel_picker = ft.FilePicker(on_result=self._save_excel_result)
        
        # --- PANEL IZQUIERDO: CONSTRUCTOR DE INFORMES ---
        self.drop_tipo_informe = ft.Dropdown(
            label="Tipo de Informe",
            options=[
                ft.dropdown.Option("Valorización de Inventario"),
                ft.dropdown.Option("Informe de Compras"),
                ft.dropdown.Option("Informe de Ventas"),
                ft.dropdown.Option("Historial de Ajustes"),
                ft.dropdown.Option("Informe de Impuestos"),
                ft.dropdown.Option("Resumen de KPIs")
            ],
            value="Valorización de Inventario",
            dense=True, border_radius=8,
            height=38, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8)
        )
        
        self.drop_filtro_fecha = ft.Dropdown(
            label="Periodo",
            options=[
                ft.dropdown.Option("Día de Hoy"),
                ft.dropdown.Option("Mes Actual"),
                ft.dropdown.Option("Histórico Completo")
            ],
            value="Histórico Completo",
            dense=True, border_radius=8,
            height=38, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8)
        )
        
        self.opcion_detalle = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="Completo", label="Completo"),
                ft.Radio(value="Resumido", label="Resumido")
            ]),
            value="Completo"
        )
        
        self.btn_generar = ft.ElevatedButton(
            "Generar Previsualización", 
            icon=ft.icons.PLAY_ARROW, 
            bgcolor=Config.COLOR_PRIMARY, 
            color="white",
            on_click=self.generar_informe,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        self.btn_pdf = ft.OutlinedButton(
            "Exportar a PDF", 
            icon=ft.icons.PICTURE_AS_PDF, 
            icon_color="red", 
            on_click=self.exportar_pdf,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        self.btn_excel = ft.OutlinedButton(
            "Exportar a Excel", 
            icon=ft.icons.TABLE_VIEW, 
            icon_color="green", 
            on_click=self.exportar_excel,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # Tarjeta informativa corta para la exportación a Excel
        info_excel_box = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.INFO_OUTLINED, size=15, color="blue700"),
                ft.Text(
                    "Excel genera el consolidado general completo (Inventario, Compras, Ventas y Ajustes) acumulado a la fecha, sin aplicar los filtros seleccionados.",
                    size=10,
                    color="blue900",
                    expand=True
                )
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            padding=8,
            bgcolor="#e3f2fd",
            border_radius=6,
            border=ft.border.all(1, "#bbdefb")
        )
        
        panel_controles = ft.Container(
            content=ft.Column([
                ft.Text("Parámetros del Informe", weight="bold", color=Config.COLOR_PRIMARY),
                ft.Divider(height=1, color="#eeeeee"),
                self.drop_tipo_informe,
                self.drop_filtro_fecha,
                ft.Text("Nivel de Detalle", size=12, color="grey"),
                self.opcion_detalle,
                ft.Container(height=10),
                self.btn_generar,
                ft.Divider(height=15, color="transparent"),
                ft.Text("Exportación", weight="bold", color=Config.COLOR_PRIMARY),
                ft.Divider(height=1, color="#eeeeee"),
                self.btn_pdf,
                ft.Divider(height=8, color="#f0f0f0"), # Separador suave entre PDF y Excel
                info_excel_box,
                self.btn_excel
            ], spacing=12),
            bgcolor="white", padding=20, border_radius=8, width=300,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        # --- PANEL DERECHO: LIENZO DEL DOCUMENTO (A4) ---
        self.doc_header_empresa = ft.Text("TIENDA Y ABARROTES LOS DESECHABLES DE DOÑA MARY SAS", weight="bold", size=16, text_align=ft.TextAlign.CENTER)
        self.doc_header_titulo = ft.Text("INFORME DE VALORIZACIÓN DE INVENTARIO", weight="bold", size=14, text_align=ft.TextAlign.CENTER)
        self.doc_header_periodo = ft.Text("Periodo: Histórico Completo", size=11, color="grey", text_align=ft.TextAlign.CENTER)
        self.doc_header_fecha = ft.Text(f"Fecha de Generación: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", size=11, color="grey", text_align=ft.TextAlign.CENTER)
        
        self.doc_cuerpo = ft.Column(spacing=5)
        
        self.lienzo_documento = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        self.doc_header_empresa,
                        self.doc_header_titulo,
                        self.doc_header_periodo,
                        self.doc_header_fecha
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=20)
                ),
                ft.Divider(height=2, color="black"),
                self.doc_cuerpo
            ]),
            bgcolor="white",
            padding=40,
            border_radius=5,
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=10, color=ft.colors.with_opacity(0.1, "black"))
        )
        
        scroll_lienzo = ft.Column([self.lienzo_documento], scroll=ft.ScrollMode.ALWAYS, expand=True)
        
        # --- ENSAMBLAJE FINAL ---
        self.content = ft.Row([
            panel_controles,
            scroll_lienzo
        ], expand=True, spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)

    def did_mount(self):
        if self.page:
            if self.save_pdf_picker not in self.page.overlay:
                self.page.overlay.append(self.save_pdf_picker)
            if self.save_excel_picker not in self.page.overlay:
                self.page.overlay.append(self.save_excel_picker)
            self.page.update()

    def generar_informe(self, e):
        self.doc_cuerpo.controls.clear()
        self.doc_cuerpo.controls.append(ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center, padding=50))
        if self.page: self.page.update()
        threading.Thread(target=self._worker_generar_informe, daemon=True).start()

    def _worker_generar_informe(self):
        tipo_informe = self.drop_tipo_informe.value
        detalle = self.opcion_detalle.value
        periodo_filtro = self.drop_filtro_fecha.value

        # 1. Cálculo del Rango de Fechas
        hoy = datetime.date.today()
        if periodo_filtro == "Día de Hoy":
            fecha_inicio = hoy.strftime("%Y-%m-%d")
            fecha_fin = hoy.strftime("%Y-%m-%d")
        elif periodo_filtro == "Mes Actual":
            fecha_inicio = hoy.replace(day=1).strftime("%Y-%m-%d")
            ultimo_dia = monthrange(hoy.year, hoy.month)[1]
            fecha_fin = hoy.replace(day=ultimo_dia).strftime("%Y-%m-%d")
        else:
            # Histórico Completo
            fecha_inicio = "2000-01-01"
            fecha_fin = "2100-12-31"

        # 2. Actualizar Cabecera del Documento
        self.doc_header_titulo.value = f"INFORME DE {tipo_informe.upper()}"
        self.doc_header_periodo.value = f"Periodo: {fecha_inicio} al {fecha_fin} | Tipo: {detalle}"
        self.doc_header_fecha.value = f"Fecha de Generación: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}"

        self.doc_cuerpo.controls.clear()

        # 3. Enrutador según el tipo de informe
        if tipo_informe == "Valorización de Inventario":
            self._generar_valorizacion(detalle, fecha_corte=fecha_fin if periodo_filtro != "Histórico Completo" else None)
        elif tipo_informe == "Informe de Compras":
            self._generar_compras(fecha_inicio, fecha_fin, detalle)
        elif tipo_informe == "Informe de Ventas":
            self._generar_ventas(fecha_inicio, fecha_fin, detalle)
        elif tipo_informe == "Historial de Ajustes":
            self._generar_ajustes(fecha_inicio, fecha_fin, detalle)
        elif tipo_informe == "Informe de Impuestos":
            self._generar_impuestos(fecha_inicio, fecha_fin, detalle)
        elif tipo_informe == "Resumen de KPIs":
            self._generar_kpis(fecha_inicio, fecha_fin)

        if self.page:
            self.page.update()

    def _generar_impuestos(self, fecha_inicio, fecha_fin, detalle):
        raw_compras, _ = self.db.get_compras(page=1, page_size=100000)
        raw_ventas, _ = self.db.get_ventas(page=1, page_size=100000)

        # Filtrar Compras por Rango de Fechas
        compras_filtradas = []
        tot_compras_base = 0.0
        tot_compras_iva = 0.0
        tot_compras_total = 0.0

        for c in raw_compras:
            f = str(c.get("fecha") or "")[:10]
            if fecha_inicio <= f <= fecha_fin:
                tot = float(c.get("costo_total") or 0)
                iva = float(c.get("iva") or c.get("valor_iva") or 0)
                base = tot - iva
                cant = float(c.get("cantidad") or 0)
                cat_i = c.get("catalogo_insumos") or {}
                
                compras_filtradas.append({
                    "fecha": f,
                    "doc": c.get("numero_factura") or c.get("numero_entrada") or "S/D",
                    "insumo": cat_i.get("nombre", "Desconocido"),
                    "cant": cant,
                    "base": base,
                    "iva": iva,
                    "total": tot
                })
                tot_compras_base += base
                tot_compras_iva += iva
                tot_compras_total += tot

        # Filtrar Ventas por Rango de Fechas
        ventas_filtradas = []
        tot_ventas_base = 0.0
        tot_ventas_iva = 0.0
        tot_ventas_total = 0.0

        for v in raw_ventas:
            f = str(v.get("fecha") or "")[:10]
            if fecha_inicio <= f <= fecha_fin:
                tot = float(v.get("total") or 0)
                iva = float(v.get("iva") or 0)
                base = float(v.get("subtotal") or (tot - iva))
                cant = float(v.get("cantidad") or 0)
                cat_i = v.get("catalogo_insumos") or {}

                ventas_filtradas.append({
                    "fecha": f,
                    "doc": v.get("factura_no") or "S/D",
                    "insumo": v.get("descripcion") or cat_i.get("nombre") or "Desconocido",
                    "cant": cant,
                    "base": base,
                    "iva": iva,
                    "total": tot
                })
                tot_ventas_base += base
                tot_ventas_iva += iva
                tot_ventas_total += tot

        balance_iva = tot_ventas_iva - tot_compras_iva

        # Guardar estructura para PDF/Excel
        self.current_data = {
            "compras": compras_filtradas,
            "ventas": ventas_filtradas,
            "tot_compras_base": tot_compras_base,
            "tot_compras_iva": tot_compras_iva,
            "tot_compras_total": tot_compras_total,
            "tot_ventas_base": tot_ventas_base,
            "tot_ventas_iva": tot_ventas_iva,
            "tot_ventas_total": tot_ventas_total,
            "balance_iva": balance_iva
        }
        self.current_total = balance_iva
        self.current_periodo = self.doc_header_periodo.value

        def _crear_resumen_impuestos_row(label, val_base, val_iva, val_total, is_header=False, color_txt="black"):
            weight = "bold" if is_header else "normal"
            size = 12 if is_header else 11
            return ft.Row([
                ft.Text(label, weight=weight, size=size, expand=True, color=color_txt),
                ft.Text(f"${val_base:,.2f}" if isinstance(val_base, (int, float)) else val_base, weight=weight, size=size, width=110, text_align=ft.TextAlign.RIGHT, color=color_txt),
                ft.Text(f"${val_iva:,.2f}" if isinstance(val_iva, (int, float)) else val_iva, weight=weight, size=size, width=110, text_align=ft.TextAlign.RIGHT, color=color_txt),
                ft.Text(f"${val_total:,.2f}" if isinstance(val_total, (int, float)) else val_total, weight=weight, size=size, width=120, text_align=ft.TextAlign.RIGHT, color=color_txt),
            ])

        if detalle == "Resumido":
            self.doc_cuerpo.controls.append(_crear_resumen_impuestos_row("CONCEPTO / CONSOLIDADO", "VALOR BASE", "IVA ACUMULADO", "VALOR TOTAL", is_header=True))
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))
            
            self.doc_cuerpo.controls.append(_crear_resumen_impuestos_row("VENTAS (IVA GENERADO)", tot_ventas_base, tot_ventas_iva, tot_ventas_total, color_txt="blue700"))
            self.doc_cuerpo.controls.append(_crear_resumen_impuestos_row("COMPRAS (IVA PAGADO / DESCONTABLE)", tot_compras_base, tot_compras_iva, tot_compras_total, color_txt="teal700"))
            self.doc_cuerpo.controls.append(ft.Divider(height=2, color="black"))

            color_bal = "red" if balance_iva > 0 else "green"
            lbl_bal = "BALANCE NETO DE IVA (POR PAGAR)" if balance_iva > 0 else "BALANCE NETO DE IVA (A FAVOR)"
            self.doc_cuerpo.controls.append(
                ft.Row([
                    ft.Text(f"{lbl_bal}:", weight="bold", size=13, expand=True, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"${balance_iva:,.2f}", weight="bold", size=14, width=150, text_align=ft.TextAlign.RIGHT, color=color_bal),
                ])
            )
        else:
            # VISTA COMPLETA DETALLADA
            # 1. SECCIÓN COMPRAS
            self.doc_cuerpo.controls.append(ft.Container(content=ft.Text("COMPRAS (IVA PAGADO EN ENTRADAS)", weight="bold", size=13, color="teal700"), padding=ft.padding.only(top=10, bottom=5)))
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text("FECHA", weight="bold", size=10, width=65),
                ft.Text("DOC.", weight="bold", size=10, width=80),
                ft.Text("INSUMO", weight="bold", size=10, expand=True),
                ft.Text("BASE", weight="bold", size=10, width=80, text_align=ft.TextAlign.RIGHT),
                ft.Text("IVA", weight="bold", size=10, width=70, text_align=ft.TextAlign.RIGHT),
                ft.Text("TOTAL", weight="bold", size=10, width=85, text_align=ft.TextAlign.RIGHT),
            ]))
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))

            for c in compras_filtradas:
                self.doc_cuerpo.controls.append(ft.Row([
                    ft.Text(c['fecha'], size=10, width=65),
                    ft.Text(c['doc'], size=10, width=80, no_wrap=True),
                    ft.Text(c['insumo'], size=10, expand=True, no_wrap=True),
                    ft.Text(f"${c['base']:,.2f}", size=10, width=80, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"${c['iva']:,.2f}", size=10, width=70, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"${c['total']:,.2f}", size=10, width=85, text_align=ft.TextAlign.RIGHT),
                ]))

            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text("TOTAL COMPRAS:", weight="bold", size=11, expand=True, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"${tot_compras_base:,.2f}", weight="bold", size=11, width=80, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"${tot_compras_iva:,.2f}", weight="bold", size=11, width=70, text_align=ft.TextAlign.RIGHT, color="teal700"),
                ft.Text(f"${tot_compras_total:,.2f}", weight="bold", size=11, width=85, text_align=ft.TextAlign.RIGHT),
            ]))
            self.doc_cuerpo.controls.append(ft.Divider(height=15, color="transparent"))

            # 2. SECCIÓN VENTAS
            self.doc_cuerpo.controls.append(ft.Container(content=ft.Text("VENTAS (IVA GENERADO EN SALIDAS)", weight="bold", size=13, color="blue700"), padding=ft.padding.only(top=10, bottom=5)))
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text("FECHA", weight="bold", size=10, width=65),
                ft.Text("DOC.", weight="bold", size=10, width=80),
                ft.Text("INSUMO", weight="bold", size=10, expand=True),
                ft.Text("BASE", weight="bold", size=10, width=80, text_align=ft.TextAlign.RIGHT),
                ft.Text("IVA", weight="bold", size=10, width=70, text_align=ft.TextAlign.RIGHT),
                ft.Text("TOTAL", weight="bold", size=10, width=85, text_align=ft.TextAlign.RIGHT),
            ]))
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))

            for v in ventas_filtradas:
                self.doc_cuerpo.controls.append(ft.Row([
                    ft.Text(v['fecha'], size=10, width=65),
                    ft.Text(v['doc'], size=10, width=80, no_wrap=True),
                    ft.Text(v['insumo'], size=10, expand=True, no_wrap=True),
                    ft.Text(f"${v['base']:,.2f}", size=10, width=80, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"${v['iva']:,.2f}", size=10, width=70, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"${v['total']:,.2f}", size=10, width=85, text_align=ft.TextAlign.RIGHT),
                ]))

            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text("TOTAL VENTAS:", weight="bold", size=11, expand=True, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"${tot_ventas_base:,.2f}", weight="bold", size=11, width=80, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"${tot_ventas_iva:,.2f}", weight="bold", size=11, width=70, text_align=ft.TextAlign.RIGHT, color="blue700"),
                ft.Text(f"${tot_ventas_total:,.2f}", weight="bold", size=11, width=85, text_align=ft.TextAlign.RIGHT),
            ]))
            self.doc_cuerpo.controls.append(ft.Divider(height=2, color="black"))

            color_bal = "red" if balance_iva > 0 else "green"
            lbl_bal = "BALANCE NETO DE IVA (POR PAGAR)" if balance_iva > 0 else "BALANCE NETO DE IVA (A FAVOR)"
            self.doc_cuerpo.controls.append(
                ft.Row([
                    ft.Text(f"{lbl_bal}:", weight="bold", size=13, expand=True, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"${balance_iva:,.2f}", weight="bold", size=13, width=120, text_align=ft.TextAlign.RIGHT, color=color_bal),
                ])
            )
            self.doc_cuerpo.controls.append(ft.Divider(height=4, color="black"))

    def _generar_valorizacion(self, detalle, fecha_corte=None):
        # Obtener datos calculados desde la base de datos
        data, _ = self.db.get_insumos(page=1, page_size=100000, fecha_corte=fecha_corte)

        if not data:
            self.doc_cuerpo.controls.append(
                ft.Container(content=ft.Text("No hay datos para los filtros seleccionados.", size=14, color="grey"), padding=30, alignment=ft.alignment.center)
            )
            self.current_data = {}
            self.current_total = 0
            return

        agrupacion = {}
        gran_total_costo = 0.0
        gran_total_cant = 0.0

        for item in data:
            cat = (item.get("categoria") or "SIN CATEGORIA").strip().upper()
            stock_real = float(item.get("stock_actual") or item.get("stock_real") or 0)
            costo_u = float(item.get("costo_unitario") or 0)
            
            # REGLA DE NEGOCIO: Un informe de valorización evalúa existencias reales.
            # Saldos negativos (ventas sin compra ingresada) se evalúan en 0 para evitar cantidades negativas y '$-0.00'.
            stock_val = max(0.0, stock_real)
            costo_total = stock_val * costo_u

            # Solo se valoran ítems con existencia disponible real
            if stock_val > 0 and costo_total > 0:
                if cat not in agrupacion:
                    agrupacion[cat] = {"items": [], "subtotal": 0.0, "cant_total": 0.0}

                agrupacion[cat]["items"].append({
                    "codigo": item.get("codigo_insumo"),
                    "nombre": item.get("nombre"),
                    "stock": stock_val,
                    "costo_u": costo_u,
                    "total": costo_total
                })
                agrupacion[cat]["subtotal"] += costo_total
                agrupacion[cat]["cant_total"] += stock_val
                gran_total_costo += costo_total
                gran_total_cant += stock_val

        # Guardar en memoria para exportación PDF/Excel
        self.current_data = agrupacion
        self.current_total = gran_total_costo
        self.current_periodo = self.doc_header_periodo.value

        if detalle == "Resumido":
            self._dibujar_resumido(agrupacion, "CATEGORÍA", gran_total_costo, gran_total_cant, "GRAN TOTAL VALORIZACIÓN")
        else:
            self.doc_cuerpo.controls.append(
                ft.Row([
                    ft.Text("CÓDIGO", weight="bold", size=11, width=60),
                    ft.Text("INSUMO", weight="bold", size=11, expand=True),
                    ft.Text("CANT.", weight="bold", size=11, width=60, text_align=ft.TextAlign.RIGHT),
                    ft.Text("COSTO U.", weight="bold", size=11, width=80, text_align=ft.TextAlign.RIGHT),
                    ft.Text("TOTAL", weight="bold", size=11, width=100, text_align=ft.TextAlign.RIGHT),
                ])
            )
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))

            for cat, datos_cat in sorted(agrupacion.items()):
                self.doc_cuerpo.controls.append(
                    ft.Container(content=ft.Text(f"GRUPO: {cat.upper()}", weight="bold", size=12, color=Config.COLOR_PRIMARY), padding=ft.padding.only(top=10, bottom=5))
                )
                for i in sorted(datos_cat["items"], key=lambda x: x["nombre"]):
                    self.doc_cuerpo.controls.append(
                        ft.Row([
                            ft.Text(i['codigo'], size=11, width=60),
                            ft.Text(i['nombre'], size=11, expand=True, no_wrap=True),
                            ft.Text(f"{i['stock']:g}", size=11, width=60, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"${i['costo_u']:,.2f}", size=11, width=80, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"${i['total']:,.2f}", size=11, width=100, text_align=ft.TextAlign.RIGHT),
                        ])
                    )
                self.doc_cuerpo.controls.append(
                    ft.Row([
                        ft.Text(f"Total {cat}:", weight="bold", size=11, expand=True, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"${datos_cat['subtotal']:,.2f}", weight="bold", size=12, width=100, text_align=ft.TextAlign.RIGHT),
                    ])
                )
                self.doc_cuerpo.controls.append(ft.Divider(height=1, color="#eeeeee"))

            self.doc_cuerpo.controls.append(ft.Divider(height=2, color="black"))
            self.doc_cuerpo.controls.append(
                ft.Row([
                    ft.Text("GRAN TOTAL VALORIZACIÓN:", weight="bold", size=14, expand=True, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"${gran_total_costo:,.2f}", weight="bold", size=14, width=150, text_align=ft.TextAlign.RIGHT),
                ])
            )
            self.doc_cuerpo.controls.append(ft.Divider(height=4, color="black"))

    def _generar_compras(self, fecha_inicio, fecha_fin, detalle):
        data, _ = self.db.get_compras(page=1, page_size=10000)
        agrupacion = {}
        gran_total = 0.0
        gran_total_cant = 0.0

        for item in data:
            fecha = item.get("fecha", "")[:10]
            if not (fecha_inicio <= fecha <= fecha_fin): continue

            proveedor = item.get("proveedor", "Desconocido")
            costo_total = float(item.get("costo_total") or 0)
            cant = float(item.get("cantidad", 0))

            if proveedor not in agrupacion:
                agrupacion[proveedor] = {"items": [], "subtotal": 0.0, "cant_total": 0.0}

            agrupacion[proveedor]["items"].append({
                "fecha": fecha,
                "factura": item.get("numero_factura", ""),
                "insumo": item.get("catalogo_insumos", {}).get("nombre", ""),
                "cant": cant,
                "total": costo_total
            })
            agrupacion[proveedor]["subtotal"] += costo_total
            agrupacion[proveedor]["cant_total"] += cant
            gran_total += costo_total
            gran_total_cant += cant

        self.current_data = agrupacion
        self.current_total = gran_total
        self.current_periodo = self.doc_header_periodo.value

        if detalle == "Resumido":
            self._dibujar_resumido(agrupacion, "PROVEEDOR", gran_total, gran_total_cant)
        else:
            self._dibujar_tabla_financiera(agrupacion, "PROVEEDOR", gran_total, ["FECHA", "FACTURA", "INSUMO", "CANT.", "TOTAL"])

    def _generar_ventas(self, fecha_inicio, fecha_fin, detalle):
        data, _ = self.db.get_ventas(page=1, page_size=10000)
        agrupacion = {}
        gran_total = 0.0
        gran_total_cant = 0.0

        for item in data:
            fecha = item.get("fecha", "")[:10]
            if not (fecha_inicio <= fecha <= fecha_fin): continue

            cat = item.get("catalogo_insumos", {}).get("categoria", "SIN CATEGORIA")
            
            if cat not in agrupacion:
                agrupacion[cat] = {"items": [], "subtotal": 0.0, "cant_total": 0.0}

            total = float(item.get("total") or 0)
            cant = float(item.get("cantidad", 0))
            agrupacion[cat]["items"].append({
                "fecha": fecha,
                "factura": item.get("factura_no", ""),
                "insumo": item.get("descripcion") or item.get("catalogo_insumos", {}).get("nombre", ""),
                "cant": cant,
                "total": total
            })
            agrupacion[cat]["subtotal"] += total
            agrupacion[cat]["cant_total"] += cant
            gran_total += total
            gran_total_cant += cant

        self.current_data = agrupacion
        self.current_total = gran_total
        self.current_periodo = self.doc_header_periodo.value

        if detalle == "Resumido":
            self._dibujar_resumido(agrupacion, "CATEGORÍA", gran_total, gran_total_cant)
        else:
            self._dibujar_tabla_financiera(agrupacion, "CATEGORÍA", gran_total, ["FECHA", "FACTURA", "INSUMO", "CANT.", "INGRESOS"])

    def _generar_ajustes(self, fecha_inicio, fecha_fin, detalle):
        data = self.db.get_ajustes_inventario()
        agrupacion = {}
        gran_total_neto = 0.0
        gran_total_cant = 0.0

        for item in data:
            if item.get("estado_registro") != "VÁLIDO": continue

            fecha = item.get("fecha_ajuste", "")[:10]
            if not (fecha_inicio <= fecha <= fecha_fin): continue

            tipo = "ENTRADAS (+)" if item.get("tipo_ajuste") in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE') else "SALIDAS (-)"
            if tipo not in agrupacion:
                agrupacion[tipo] = {"items": [], "subtotal": 0.0, "cant_total": 0.0}

            costo = float(item.get("costo_total_ajuste") or 0)
            cant = float(item.get("cantidad", 0))

            raw_motivo = item.get("motivo", "")
            raw_obs = item.get("observacion", "") or item.get("observaciones", "")
            if not raw_motivo and item.get("motivo_observacion"):
                partes = item.get("motivo_observacion").split("]", 1)
                raw_motivo = partes[0].replace("[", "").strip() if len(partes) > 1 else item.get("motivo_observacion")
                raw_obs = partes[1].strip() if len(partes) > 1 else ""

            agrupacion[tipo]["items"].append({
                "fecha": fecha,
                "motivo": raw_motivo,
                "obs": raw_obs,
                "insumo": item.get("catalogo_insumos", {}).get("nombre", ""),
                "cant": cant,
                "total": costo
            })
            agrupacion[tipo]["subtotal"] += costo
            agrupacion[tipo]["cant_total"] += cant
            gran_total_neto += costo if tipo == "ENTRADAS (+)" else -costo
            gran_total_cant += cant if tipo == "ENTRADAS (+)" else -cant

        self.current_data = agrupacion
        self.current_total = gran_total_neto
        self.current_periodo = self.doc_header_periodo.value

        if detalle == "Resumido":
            self._dibujar_resumido(agrupacion, "TIPO DE AJUSTE", gran_total_neto, gran_total_cant, "IMPACTO NETO")
        else:
            self._dibujar_tabla_financiera(agrupacion, "TIPO DE AJUSTE", gran_total_neto, ["FECHA", "MOTIVO", "OBSERVACIÓN", "INSUMO", "CANT.", "COSTO TOTAL"], label_gran_total="IMPACTO NETO", is_ajuste=True)

    def _dibujar_resumido(self, agrupacion, label_grupo, gran_total_val, gran_total_cant=0, label_gran_total="GRAN TOTAL"):
        self.doc_cuerpo.controls.append(ft.Row([
            ft.Text(label_grupo, weight="bold", size=11, expand=True),
            ft.Text("CANT. TOTAL", weight="bold", size=11, width=100, text_align=ft.TextAlign.RIGHT),
            ft.Text("VALOR TOTAL", weight="bold", size=11, width=120, text_align=ft.TextAlign.RIGHT),
        ]))
        self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))

        for grupo, datos in sorted(agrupacion.items()):
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text(grupo.upper(), size=11, expand=True, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text(f"{datos.get('cant_total', 0):g}", size=11, width=100, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"${datos['subtotal']:,.2f}", size=11, width=120, text_align=ft.TextAlign.RIGHT),
            ]))
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="#eeeeee"))

        self.doc_cuerpo.controls.append(ft.Divider(height=2, color="black"))
        color_total = "red" if gran_total_val < 0 else "black"
        self.doc_cuerpo.controls.append(ft.Row([
            ft.Text(f"{label_gran_total}:", weight="bold", size=14, expand=True, text_align=ft.TextAlign.RIGHT),
            ft.Text(f"{gran_total_cant:g}", weight="bold", size=14, width=100, text_align=ft.TextAlign.RIGHT),
            ft.Text(f"${gran_total_val:,.2f}", weight="bold", size=14, width=120, text_align=ft.TextAlign.RIGHT, color=color_total),
        ]))

    def _dibujar_tabla_financiera(self, agrupacion, label_grupo, gran_total, headers, label_gran_total="GRAN TOTAL", is_ajuste=False):
        if not agrupacion:
            self.doc_cuerpo.controls.append(ft.Container(content=ft.Text("No hay datos para los filtros seleccionados.", size=14, color="grey"), padding=30, alignment=ft.alignment.center))
            return

        # Cabeceras
        if is_ajuste:
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text(headers[0], weight="bold", size=11, width=65),
                ft.Text(headers[1], weight="bold", size=11, width=90),
                ft.Text(headers[2], weight="bold", size=11, expand=True),
                ft.Text(headers[3], weight="bold", size=11, width=100),
                ft.Text(headers[4], weight="bold", size=11, width=45, text_align=ft.TextAlign.RIGHT),
                ft.Text(headers[5], weight="bold", size=11, width=70, text_align=ft.TextAlign.RIGHT),
            ]))
        else:
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text(headers[0], weight="bold", size=11, width=70),
                ft.Text(headers[1], weight="bold", size=11, width=90),
                ft.Text(headers[2], weight="bold", size=11, expand=True),
                ft.Text(headers[3], weight="bold", size=11, width=60, text_align=ft.TextAlign.RIGHT),
                ft.Text(headers[4], weight="bold", size=11, width=100, text_align=ft.TextAlign.RIGHT),
            ]))
        self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))

        for grupo, datos in sorted(agrupacion.items()):
            self.doc_cuerpo.controls.append(ft.Container(content=ft.Text(f"{label_grupo}: {grupo.upper()}", weight="bold", size=12, color=Config.COLOR_PRIMARY), padding=ft.padding.only(top=10, bottom=5)))
            for i in datos["items"]:
                if is_ajuste:
                    fila_ui = ft.Row([
                        ft.Text(i['fecha'], size=11, width=65),
                        ft.Text(i['motivo'], size=11, width=90, no_wrap=True, weight="bold"),
                        ft.Text(i['obs'], size=11, expand=True), # Observación toma el espacio restante
                        ft.Text(i['insumo'], size=11, width=100, no_wrap=True),
                        ft.Text(f"{i['cant']:g}", size=11, width=45, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"${i['total']:,.2f}", size=11, width=70, text_align=ft.TextAlign.RIGHT),
                    ])
                else:
                    fila_ui = ft.Row([
                        ft.Text(i['fecha'], size=11, width=70),
                        ft.Text(i['factura'], size=11, width=90, no_wrap=True),
                        ft.Text(i['insumo'], size=11, expand=True, no_wrap=True),
                        ft.Text(f"{i['cant']:g}", size=11, width=60, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"${i['total']:,.2f}", size=11, width=100, text_align=ft.TextAlign.RIGHT),
                    ])
                self.doc_cuerpo.controls.append(fila_ui)
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text(f"Total {grupo}:", weight="bold", size=11, expand=True, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"${datos['subtotal']:,.2f}", weight="bold", size=12, width=100, text_align=ft.TextAlign.RIGHT),
            ]))
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="#eeeeee"))

        self.doc_cuerpo.controls.append(ft.Divider(height=2, color="black"))
        color_total = "red" if gran_total < 0 else "black"
        self.doc_cuerpo.controls.append(ft.Row([
            ft.Text(f"{label_gran_total}:", weight="bold", size=14, expand=True, text_align=ft.TextAlign.RIGHT),
            ft.Text(f"${gran_total:,.2f}", weight="bold", size=14, width=150, text_align=ft.TextAlign.RIGHT, color=color_total),
        ]))
        self.doc_cuerpo.controls.append(ft.Divider(height=4, color="black"))

    def _generar_kpis(self, fecha_inicio, fecha_fin):
        # Como los KPIs son un resumen global dictado por los métodos SQL actuales (que operan por mes/hoy)
        # Mostraremos la foto actual del sistema independientemente del filtro de fechas (con una advertencia visual)

        res_cat = self.db.get_catalogo_summary()
        res_ven = self.db.get_ventas_summary()
        res_com = self.db.get_compras_summary()
        kpis_inv = self.db.get_inventario_kpis()

        val_inv = kpis_inv.get('valor_inventario', 0)
        ingresos = float(res_ven.get('total_mes') or 0)
        compras = float(res_com.get('total_mes') or 0)

        rentabilidad = ((ingresos - compras) / ingresos) * 100 if ingresos > 0 else 0
        rotacion = ingresos / val_inv if val_inv > 0 else 0

        def _crear_kpi_fila(label, valor, color="black"):
            return ft.Row([
                ft.Text(label, size=13, expand=True),
                ft.Text(valor, size=14, weight="bold", color=color, width=150, text_align=ft.TextAlign.RIGHT)
            ])

        self.doc_cuerpo.controls.extend([
            ft.Container(content=ft.Text("NOTA: Este resumen muestra el estado actual del MES EN CURSO según las métricas del Dashboard, independientemente del filtro de fechas seleccionado.", size=10, color="orange", italic=True), padding=10, bgcolor="#fff3cd", border_radius=5),
            ft.Divider(height=10, color="transparent"),
            ft.Text("MÉTRICAS DE INVENTARIO Y COSTOS", weight="bold", size=14, color=Config.COLOR_PRIMARY),
            ft.Divider(height=1, color="black"),
            _crear_kpi_fila("Valorización Actual del Inventario", f"${val_inv:,.2f}"),
            _crear_kpi_fila("Total Compras (Mes Actual)", f"${compras:,.2f}"),
            ft.Divider(height=20, color="transparent"),
            ft.Text("MÉTRICAS DE VENTAS E INGRESOS", weight="bold", size=14, color=Config.COLOR_PRIMARY),
            ft.Divider(height=1, color="black"),
            _crear_kpi_fila("Total Ventas (Mes Actual)", f"${ingresos:,.2f}", "green"),
            _crear_kpi_fila("IVA Recaudado (Mes Actual)", f"${res_ven.get('iva_mes', 0):,.2f}"),
            ft.Divider(height=20, color="transparent"),
            ft.Text("RENDIMIENTO FINANCIERO (MES ACTUAL)", weight="bold", size=14, color=Config.COLOR_PRIMARY),
            ft.Divider(height=1, color="black"),
            _crear_kpi_fila("Margen de Rentabilidad Bruta", f"{rentabilidad:.1f}%", "green" if rentabilidad >= 0 else "red"),
            _crear_kpi_fila("Índice de Rotación", f"{rotacion:.2f}x"),
            ft.Divider(height=4, color="black")
        ])

    def exportar_pdf(self, e):
        if not hasattr(self, 'current_data') or not self.current_data:
            self.page.snack_bar = ft.SnackBar(ft.Text("Primero genera la previsualización del informe."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Garantizar registración en overlay antes de invocar el diálogo
        if self.page:
            if self.save_pdf_picker not in self.page.overlay:
                self.page.overlay.append(self.save_pdf_picker)
                self.page.update()

        nombre_sugerido = f"{self.drop_tipo_informe.value.replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
        self.save_pdf_picker.save_file(
            dialog_title="Guardar Informe PDF",
            file_name=nombre_sugerido,
            allowed_extensions=["pdf"]
        )

    def _save_pdf_result(self, e: ft.FilePickerResultEvent):
        if not e.path:
            return
            
        try:
            from fpdf import FPDF
            
            class PDFReport(FPDF):
                def header(instance):
                    instance.set_font("Arial", 'B', 12)
                    instance.cell(0, 6, "TIENDA Y ABARROTES LOS DESECHABLES DE DOÑA MARY SAS", ln=True, align='C')
                    instance.set_font("Arial", 'B', 10)
                    instance.cell(0, 5, "REPORTE OFICIAL DE INVENTARIOS Y OPERACIONES", ln=True, align='C')
                    instance.set_font("Arial", '', 8)
                    instance.cell(0, 4, f"Generado el: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}", ln=True, align='C')
                    instance.ln(4)
                    instance.line(10, instance.get_y(), 200, instance.get_y())
                    instance.ln(4)

                def footer(instance):
                    instance.set_y(-15)
                    instance.set_font("Arial", 'I', 8)
                    instance.cell(0, 10, f"Página {instance.page_no()}/{{nb}}", align='C')

            pdf = PDFReport()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Título del Informe
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 6, str(self.doc_header_titulo.value).encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 5, str(self.doc_header_periodo.value).encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.ln(4)

            es_resumido = self.opcion_detalle.value == "Resumido"
            es_ajuste = self.drop_tipo_informe.value == "Historial de Ajustes"

            if es_resumido:
                # Tabla Resumida
                pdf.set_font("Arial", 'B', 8)
                pdf.cell(110, 6, "GRUPO / CATEGORIA", border=1)
                pdf.cell(35, 6, "CANT. TOTAL", border=1, align='R')
                pdf.cell(45, 6, "VALOR TOTAL", border=1, align='R')
                pdf.ln()

                pdf.set_font("Arial", '', 8)
                for grupo, datos in sorted(self.current_data.items()):
                    g_nombre = str(grupo).upper().encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(110, 6, g_nombre, border="L,R,B")
                    pdf.cell(35, 6, f"{datos.get('cant_total', 0):g}", border="L,R,B", align='R')
                    pdf.cell(45, 6, f"${datos['subtotal']:,.2f}", border="L,R,B", align='R', ln=True)

                pdf.ln(4)
                pdf.set_font("Arial", 'B', 9)
                pdf.cell(145, 7, "TOTAL GENERAL:", align='R')
                pdf.cell(45, 7, f"${self.current_total:,.2f}", border=1, align='R', ln=True)

            else:
                # Tabla Completa
                pdf.set_font("Arial", 'B', 8)
                if es_ajuste:
                    pdf.cell(20, 6, "FECHA", border=1)
                    pdf.cell(30, 6, "MOTIVO", border=1)
                    pdf.cell(50, 6, "OBSERVACION", border=1)
                    pdf.cell(45, 6, "INSUMO", border=1)
                    pdf.cell(20, 6, "CANT.", border=1, align='R')
                    pdf.cell(25, 6, "COSTO TOT.", border=1, align='R')
                else:
                    pdf.cell(20, 6, "FECHA/COD", border=1)
                    pdf.cell(30, 6, "DOC/FACT", border=1)
                    pdf.cell(75, 6, "INSUMO / DESCRIPCION", border=1)
                    pdf.cell(20, 6, "CANT.", border=1, align='R')
                    pdf.cell(20, 6, "COSTO U.", border=1, align='R')
                    pdf.cell(25, 6, "TOTAL", border=1, align='R')
                pdf.ln()

                for grupo, datos in sorted(self.current_data.items()):
                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(0, 6, f"  GRUPO: {str(grupo).upper().encode('latin-1', 'replace').decode('latin-1')}", border="L,R,B", ln=True)
                    pdf.set_font("Arial", '', 7)

                    for i in datos["items"]:
                        insumo_txt = str(i.get('insumo') or i.get('nombre', '')).encode('latin-1', 'replace').decode('latin-1')[:35]
                        
                        if es_ajuste:
                            motivo_txt = str(i.get('motivo', '')).encode('latin-1', 'replace').decode('latin-1')[:18]
                            obs_txt = str(i.get('obs', '')).encode('latin-1', 'replace').decode('latin-1')[:30]
                            pdf.cell(20, 5, str(i.get('fecha', '')), border="L")
                            pdf.cell(30, 5, motivo_txt)
                            pdf.cell(50, 5, obs_txt)
                            pdf.cell(45, 5, insumo_txt)
                            pdf.cell(20, 5, f"{i.get('cant', 0):g}", align='R')
                            pdf.cell(25, 5, f"${i.get('total', 0):,.2f}", border="R", align='R', ln=True)
                        else:
                            c_code = str(i.get('codigo') or i.get('fecha', ''))
                            c_doc = str(i.get('factura', ''))[:15]
                            c_u = f"${i.get('costo_u', 0):,.2f}" if 'costo_u' in i else "-"
                            pdf.cell(20, 5, c_code, border="L")
                            pdf.cell(30, 5, c_doc)
                            pdf.cell(75, 5, insumo_txt)
                            pdf.cell(20, 5, f"{i.get('stock', i.get('cant', 0)):g}", align='R')
                            pdf.cell(20, 5, c_u, align='R')
                            pdf.cell(25, 5, f"${i.get('total', 0):,.2f}", border="R", align='R', ln=True)

                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(165, 5, f"Subtotal {grupo}:", border="L,B", align='R')
                    pdf.cell(25, 5, f"${datos['subtotal']:,.2f}", border="R,B", align='R', ln=True)

                pdf.ln(4)
                pdf.set_font("Arial", 'B', 9)
                pdf.cell(165, 7, "TOTAL GENERAL:", align='R')
                pdf.cell(25, 7, f"${self.current_total:,.2f}", border=1, align='R', ln=True)

            pdf.output(e.path)
            self.page.snack_bar = ft.SnackBar(ft.Text("¡PDF exportado con éxito!"), bgcolor="green")
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error al generar PDF: {ex}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    def exportar_excel(self, e):
        # Garantizar registración en overlay antes de invocar el diálogo
        if self.page:
            if self.save_excel_picker not in self.page.overlay:
                self.page.overlay.append(self.save_excel_picker)
                self.page.update()

        nombre_sugerido = f"Inventario_Consolidado_Dona_Mary_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
        self.save_excel_picker.save_file(
            dialog_title="Guardar Consolidado Excel",
            file_name=nombre_sugerido,
            allowed_extensions=["xlsx"]
        )

    def _save_excel_result(self, e: ft.FilePickerResultEvent):
        if not e.path:
            return
            
        self.page.snack_bar = ft.SnackBar(ft.Text("Generando consolidado Excel en segundo plano..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()
        
        threading.Thread(target=self._worker_generar_excel, args=(e.path,), daemon=True).start()

    def _worker_generar_excel(self, file_path):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            # 1. Obtener datos completos de la base de datos sin filtros
            raw_inv, _ = self.db.get_insumos(page=1, page_size=999999)
            raw_compras, _ = self.db.get_compras(page=1, page_size=999999)
            raw_ventas, _ = self.db.get_ventas(page=1, page_size=999999)
            raw_ajustes = self.db.get_ajustes_inventario() or []

            wb = openpyxl.Workbook()
            wb.remove(wb.active) # Eliminar hoja por defecto

            # Estilos generales
            fill_header = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
            font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            font_title = Font(name="Calibri", size=14, bold=True, color="1B365D")
            font_sub = Font(name="Calibri", size=10, italic=True, color="555555")
            border_thin = Border(
                left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
                top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC')
            )
            num_fmt_curr = '"$"#,##0.00'
            num_fmt_qty = '#,##0'

            fecha_emision = datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p")
            nombre_empresa = "TIENDA Y ABARROTES LOS DESECHABLES DE DOÑA MARY SAS"

            def agregar_encabezado(ws, titulo):
                ws['A1'] = nombre_empresa
                ws['A1'].font = font_title
                ws['A2'] = f"CONSOLIDADO SISTEMA: {titulo.upper()}"
                ws['A2'].font = Font(name="Calibri", size=12, bold=True)
                ws['A3'] = f"Fecha de emisión: {fecha_emision} | Datos acumulados sin filtros"
                ws['A3'].font = font_sub

            # ----------------------------------------------------
            # HOJA 1: COMPRAS
            # ----------------------------------------------------
            ws_c = wb.create_sheet(title="Compras")
            agregar_encabezado(ws_c, "Detalle de Registro de Compras")
            ws_c.append([])
            ws_c.append(["Fecha", "Código Insumo", "Nombre Insumo", "Factura / Documento", "Cantidad", "Costo Total"])

            for r_idx, c in enumerate(raw_compras, start=6):
                cat_i = c.get("catalogo_insumos") or {}
                ws_c.cell(row=r_idx, column=1, value=str(c.get("fecha", ""))[:10])
                ws_c.cell(row=r_idx, column=2, value=str(c.get("codigo_insumo", "")))
                ws_c.cell(row=r_idx, column=3, value=cat_i.get("nombre", "Desconocido"))
                ws_c.cell(row=r_idx, column=4, value=str(c.get("numero_factura") or c.get("numero_entrada") or ""))
                ws_c.cell(row=r_idx, column=5, value=float(c.get("cantidad") or 0))
                ws_c.cell(row=r_idx, column=6, value=float(c.get("costo_total") or 0))

            # ----------------------------------------------------
            # HOJA 2: VENTAS
            # ----------------------------------------------------
            ws_v = wb.create_sheet(title="Ventas")
            agregar_encabezado(ws_v, "Detalle de Registro de Ventas")
            ws_v.append([])
            ws_v.append(["Fecha", "Código Insumo", "Nombre Insumo", "Comprobante / Pedido", "Cantidad", "Ingreso Total"])

            for r_idx, v in enumerate(raw_ventas, start=6):
                cat_i = v.get("catalogo_insumos") or {}
                ws_v.cell(row=r_idx, column=1, value=str(v.get("fecha", ""))[:10])
                ws_v.cell(row=r_idx, column=2, value=str(v.get("codigo_insumo", "")))
                ws_v.cell(row=r_idx, column=3, value=cat_i.get("nombre") or v.get("descripcion") or "Desconocido")
                ws_v.cell(row=r_idx, column=4, value=str(v.get("factura_no", "")))
                ws_v.cell(row=r_idx, column=5, value=float(v.get("cantidad") or 0))
                ws_v.cell(row=r_idx, column=6, value=float(v.get("total") or 0))

            # ----------------------------------------------------
            # HOJA 3: AJUSTES
            # ----------------------------------------------------
            ws_a = wb.create_sheet(title="Ajustes")
            agregar_encabezado(ws_a, "Detalle de Ajustes de Inventario")
            ws_a.append([])
            ws_a.append(["Fecha", "Código Insumo", "Nombre Insumo", "Tipo", "Cantidad", "Motivo"])

            for r_idx, a in enumerate(raw_ajustes, start=6):
                if a.get("estado_registro") != "VÁLIDO": continue
                cat_i = a.get("catalogo_insumos") or {}
                es_ent = a.get("tipo_ajuste") in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
                
                ws_a.cell(row=r_idx, column=1, value=str(a.get("fecha_ajuste", ""))[:10])
                ws_a.cell(row=r_idx, column=2, value=str(a.get("codigo_insumo", "")))
                ws_a.cell(row=r_idx, column=3, value=cat_i.get("nombre", "Desconocido"))
                ws_a.cell(row=r_idx, column=4, value="Entrada" if es_ent else "Salida")
                ws_a.cell(row=r_idx, column=5, value=float(a.get("cantidad") or 0))
                ws_a.cell(row=r_idx, column=6, value=str(a.get("motivo_observacion", "")))

            # ----------------------------------------------------
            # HOJA 4: INVENTARIO (HOJA MAESTRA CON FÓRMULAS)
            # ----------------------------------------------------
            ws_inv = wb.create_sheet(title="Inventario")
            agregar_encabezado(ws_inv, "Catálogo General de Inventario y Valorización Formulado")
            ws_inv.append([])
            
            headers_inv = [
                "Código", "Nombre", "Categoría", "Ubicación", "Stock Inicial",
                "Entradas", "Costo Entradas", "Salidas", "Ingresos por Salidas",
                "Stock Actual", "Costo del Stock Actual", "Proyección Ingresos Stock Actual",
                "Precio de Venta del Sistema", "Costo Unitario del Sistema",
                "Ajustes Entradas", "Ajustes Salidas", "Costo Ajustes Entradas", "Ingresos Ajustes Salidas"
            ]
            ws_inv.append(headers_inv)

            for idx, i in enumerate(raw_inv, start=6):
                code = str(i.get("codigo_insumo", ""))
                
                # Datos estáticos base
                ws_inv.cell(row=idx, column=1, value=code) # A
                ws_inv.cell(row=idx, column=2, value=str(i.get("nombre", ""))) # B
                ws_inv.cell(row=idx, column=3, value=str(i.get("categoria", ""))) # C
                ws_inv.cell(row=idx, column=4, value=str(i.get("ubicacion") or "N/A")) # D
                ws_inv.cell(row=idx, column=5, value=float(i.get("stock_inicial") or 0)) # E

                # Fórmulas SUMIF sobre Compras y Ventas
                ws_inv.cell(row=idx, column=6, value=f'=SUMIF(Compras!B:B, A{idx}, Compras!E:E)') # F: Entradas
                ws_inv.cell(row=idx, column=7, value=f'=SUMIF(Compras!B:B, A{idx}, Compras!F:F)') # G: Costo Entradas
                ws_inv.cell(row=idx, column=8, value=f'=SUMIF(Ventas!B:B, A{idx}, Ventas!E:E)') # H: Salidas
                ws_inv.cell(row=idx, column=9, value=f'=SUMIF(Ventas!B:B, A{idx}, Ventas!F:F)') # I: Ingresos Salidas

                # Precios/Costos Unitarios Maestros
                ws_inv.cell(row=idx, column=13, value=float(i.get("precio_venta") or 0)) # M: Precio Venta
                ws_inv.cell(row=idx, column=14, value=float(i.get("costo_unitario") or 0)) # N: Costo Unitario

                # Fórmulas SUMIFS sobre Ajustes
                ws_inv.cell(row=idx, column=15, value=f'=SUMIFS(Ajustes!E:E, Ajustes!B:B, A{idx}, Ajustes!D:D, "Entrada")') # O: Ajustes Entradas
                ws_inv.cell(row=idx, column=16, value=f'=SUMIFS(Ajustes!E:E, Ajustes!B:B, A{idx}, Ajustes!D:D, "Salida")') # P: Ajustes Salidas

                # Fórmulas de Totales en Inventario
                ws_inv.cell(row=idx, column=10, value=f'=E{idx}+F{idx}-H{idx}+O{idx}-P{idx}') # J: Stock Actual
                ws_inv.cell(row=idx, column=11, value=f'=J{idx}*N{idx}') # K: Costo Stock Actual
                ws_inv.cell(row=idx, column=12, value=f'=J{idx}*M{idx}') # L: Proyección Ingresos
                ws_inv.cell(row=idx, column=17, value=f'=O{idx}*N{idx}') # Q: Costo Ajustes Entradas
                ws_inv.cell(row=idx, column=18, value=f'=P{idx}*M{idx}') # R: Ingresos Ajustes Salidas

            # ----------------------------------------------------
            # APLICAR FORMATOS Y AUTOFIT A TODAS LAS HOJAS
            # ----------------------------------------------------
            for sheet in wb.worksheets:
                for cell in sheet[5]:
                    cell.fill = fill_header
                    cell.font = font_header
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

                for col in sheet.columns:
                    max_len = 0
                    col_letter = get_column_letter(col[0].column)
                    for cell in col:
                        if cell.row >= 5 and cell.value is not None:
                            max_len = max(max_len, len(str(cell.value)))
                            cell.border = border_thin

                        # Formatear números en la hoja Inventario
                        if sheet.title == "Inventario" and cell.row >= 6:
                            if col_letter in ["G", "I", "K", "L", "M", "N", "Q", "R"]:
                                cell.number_format = num_fmt_curr
                            elif col_letter in ["E", "F", "H", "J", "O", "P"]:
                                cell.number_format = num_fmt_qty
                        elif sheet.title in ["Compras", "Ventas"] and cell.row >= 6:
                            if col_letter == "F": cell.number_format = num_fmt_curr
                            elif col_letter == "E": cell.number_format = num_fmt_qty

                    sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

            wb.save(file_path)

            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("¡Consolidado Excel generado y formulado con éxito!"), bgcolor="green")
                self.page.snack_bar.open = True
                self.page.update()

        except Exception as ex:
            print(f"Error generando Excel: {ex}")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error al generar Excel: {ex}"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
````

## File: ui/views/compras.py
````python
import flet as ft
import threading
import time
import json
import os
import datetime
from pypdf import PdfReader, PdfWriter
from config import Config
from core.supabase_client import SupabaseClient
from core.gemini_parser import GeminiParser
import math
from ui.components.autocomplete import CustomAutoComplete

class ComprasView(ft.Container):
    def safe_update(self):
        """Actualiza la UI de forma segura solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
        self.expand = True
        
        self.db = SupabaseClient()
        self.ai_parser = GeminiParser()
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        self.parsed_data = None # Para guardar temporalmente los datos extraídos
        
        # --- ESTADO PANEL HISTÓRICO ---
        self.panel_abierto = False
        self.fecha_historial_activa = datetime.date.today().strftime("%Y-%m-%d")
        self.modo_agrupacion_compras = "FACTURA" # "FACTURA" o "PROVEEDOR"
        self.filtro_factura_activo = None
        self.filtro_proveedor_activo = None
        self.date_picker_compras_timeline = ft.DatePicker(on_change=self.on_date_compras_timeline_change)
        # ------------------------------
        
        # Controles de Búsqueda
        def on_select_busqueda_compras(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            if "[" in texto and "]" in texto:
                query = texto.split("]")[0].replace("[", "").strip()
            elif "Factura: " in texto:
                query = texto.replace("Factura: ", "").strip()
            elif "Proveedor: " in texto:
                query = texto.replace("Proveedor: ", "").strip()
            else:
                query = texto.strip()
            self.search_input_text.value = query
            self.on_search(None)

        self.search_input_text = ft.TextField(visible=False)

        self.search_autocomplete = CustomAutoComplete(
            hint_text="Buscar por código, proveedor o factura...",
            on_select=on_select_busqueda_compras,
            text_size=12,
            expand=True
        )
        
        # Filtro de fecha
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )
        self.btn_date = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_OUTLINED,
            tooltip="Filtrar por Fecha",
            on_click=self.open_date_picker
        )
        
        self.btn_crear_manual = ft.ElevatedButton(
            text="Registrar Manual",
            icon=ft.icons.ADD_BOX,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=40,
            on_click=self.abrir_modal_crear_compra,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Dashboard Resumen
        self.lbl_compras_mes = ft.Text("$0", size=20, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_compras_hoy = ft.Text("$0", size=20, weight="bold", color="green")
        self.lbl_cantidad = ft.Text("0", size=20, weight="bold")
        
        self.summary_container = ft.Container(
            content=ft.Row([
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Total Compras en el Mes"), self.lbl_compras_mes]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Total Compras Hoy"), self.lbl_compras_hoy]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Cantidad Productos Comprados"), self.lbl_cantidad]), padding=5), expand=True),
            ])
        )
        
        self.btn_agregar = ft.ElevatedButton(
            text="Agregar Compra",
            icon=ft.icons.ADD,
            bgcolor=Config.COLOR_SECONDARY,
            color="white",
            height=40,
            on_click=self.on_agregar_click,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # File Picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        
        # Diálogo de Carga
        self.lbl_loading_text = ft.Text("Preparando archivo...", text_align=ft.TextAlign.CENTER)
        self.dlg_loading = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesando con Inteligencia Artificial"),
            content=ft.Column([
                ft.ProgressRing(),
                self.lbl_loading_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
        )
        
        # Diálogo de Confirmación (se construirá dinámicamente)
        self.dlg_confirm = ft.AlertDialog(modal=True)
        
        # Tabla de Datos
        self.data_table = ft.DataTable(
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("Fecha", weight="bold")),
                ft.DataColumn(ft.Text("No. Factura", weight="bold")),
                ft.DataColumn(ft.Text("Proveedor", weight="bold")),
                ft.DataColumn(ft.Text("Código Item", weight="bold")),
                ft.DataColumn(ft.Container(content=ft.Text("Nombre", weight="bold"), width=230)),
                ft.DataColumn(ft.Text("Cantidad", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Unit.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("IVA", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Total", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, tooltip="Página Anterior", on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, tooltip="Página Siguiente", on_click=self.on_next_page, disabled=True)
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        # --- TAB 2: GESTIÓN DE CARGAS ---
        self.cargas_file = "cargas_compras_locales.json"
        self.cargas_data = {}
        self._load_cargas()
        
        self.fecha_filtro_cargas = None
        self.date_picker_filtro_cargas = ft.DatePicker(on_change=self.on_date_filtro_cargas_change)
        
        self.btn_filtro_fecha_cargas = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_OUTLINED,
            tooltip="Filtrar por Fecha",
            on_click=lambda e: self.date_picker_filtro_cargas.pick_date()
        )
        self.btn_clear_filtro_cargas = ft.IconButton(
            icon=ft.icons.CLEAR, tooltip="Limpiar Fecha",
            on_click=self.clear_filtro_fecha_cargas, visible=False, icon_color="red"
        )
        
        self.drop_filtro_estado_cargas = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Procesado con éxito"), ft.dropdown.Option("Falló"), ft.dropdown.Option("Guardado"), ft.dropdown.Option("Sobreescrito")],
            value="Todos", label="Estado", dense=True, width=170, border_radius=8, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8), height=38,
            on_change=lambda e: self._render_tabla_cargas()
        )
        
        self.table_cargas = ft.DataTable(
            data_row_min_height=40,
            data_row_max_height=40,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("ID", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Página", weight="bold")),
                ft.DataColumn(ft.Text("Archivo Original", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        # --- NUEVO MODAL DE METADATOS ---
        self.fecha_carga_actual = datetime.date.today().strftime("%Y-%m-%d")
        self.date_picker_cargas = ft.DatePicker(on_change=self.on_date_cargas_change)
        self.fecha_carga_btn = ft.OutlinedButton(
            text=self.fecha_carga_actual, icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_cargas.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=40, width=250
        )
        self.dlg_metadatos_pdf = ft.AlertDialog(
            modal=True,
            title=ft.Text("Selecciona la Fecha de la Carga"),
            content=ft.Column([
                ft.Text("Fecha asignada a las compras del PDF:", size=12, color="grey", weight="bold"),
                self.fecha_carga_btn
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cerrar_modal_metadatos),
                ft.ElevatedButton("Seleccionar Archivo PDF", on_click=self._abrir_file_picker_desde_modal)
            ]
        )
        
        # --- PREPARACIÓN DE LAS PESTAÑAS (TABS) ---
        
        # 1. Contenido Tab 1: Registro Compras
        row_filtros_compras = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            ft.Container(expand=True),
            self.btn_crear_manual
        ])
        
        contenedor_tabla_compras = ft.Container(
            content=ft.Row([ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        footer_paginacion = ft.Container(
            content=ft.Row([self.lbl_total, ft.Container(expand=True), self.btn_prev, self.lbl_page_info, self.btn_next], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=10)
        )
        
        layout_tab_compras = ft.Container(
            content=ft.Column([row_filtros_compras, contenedor_tabla_compras, footer_paginacion], expand=True, spacing=10),
            padding=10
        )
        
        # 2. Contenido Tab 2: Gestión de Cargas
        self.btn_extraer_todo = ft.ElevatedButton(
            text="Extraer Todo",
            icon=ft.icons.AUTO_MODE,
            bgcolor="purple700",
            color="white",
            height=40,
            on_click=self.on_extraer_todo_masivo,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        row_filtros_tab_cargas = ft.Row([
            self.btn_filtro_fecha_cargas,
            self.btn_clear_filtro_cargas,
            self.drop_filtro_estado_cargas,
            ft.Container(expand=True),
            self.btn_extraer_todo,
            ft.ElevatedButton(
                text="Subir PDF de Compras", icon=ft.icons.CLOUD_UPLOAD, bgcolor=Config.COLOR_SECONDARY, color="white", height=40,
                on_click=self.on_agregar_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
        ])
        
        contenedor_tabla_cargas = ft.Container(
            content=ft.Row([ft.Column([self.table_cargas], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        layout_tab_cargas = ft.Container(
            content=ft.Column([row_filtros_tab_cargas, contenedor_tabla_cargas], expand=True, spacing=10),
            padding=10
        )
        
        # Integrar las Pestañas
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Registro de Compras", content=layout_tab_compras, icon=ft.icons.SHOPPING_CART),
                ft.Tab(text="Gestión de Cargas", content=layout_tab_cargas, icon=ft.icons.FILE_UPLOAD),
            ],
            expand=True
        )

        # --- DISEÑO DEL PANEL HISTÓRICO ---
        self.lbl_tot_compras_panel = ft.Text("$0 COP", size=14, weight="bold", color="teal800")
        self.lbl_cant_compras_panel = ft.Text("0 unds", size=10, color="grey")

        kpi_compras_panel = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.SHOPPING_BAG, color="teal700", size=20),
                ft.Column([
                    ft.Text("TOTAL COMPRAS DEL DÍA", size=9, weight="bold", color="grey"),
                    self.lbl_tot_compras_panel
                ], spacing=0, expand=True),
                self.lbl_cant_compras_panel
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, bgcolor="#e6f4ea", border_radius=8, border=ft.border.all(1, "#c3e6cb")
        )

        self.segment_agrupacion = ft.SegmentedButton(
            segments=[
                ft.Segment(value="FACTURA", label=ft.Text("Por Factura", size=10)),
                ft.Segment(value="PROVEEDOR", label=ft.Text("Por Proveedor", size=10)),
            ],
            selected={"FACTURA"},
            on_change=self.on_agrupacion_change,
            show_selected_icon=False
        )

        self.btn_fecha_compras_panel = ft.OutlinedButton(
            self.fecha_historial_activa,
            icon=ft.icons.CALENDAR_TODAY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=5),
            height=30,
            on_click=lambda e: self.date_picker_compras_timeline.pick_date()
        )

        self.panel_compras_list = ft.ListView(expand=True, spacing=6)

        # Botón para copiar histórico de compras
        self.btn_copiar_compras_panel = ft.IconButton(
            icon=ft.icons.COPY_ROUNDED,
            icon_size=16,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Copiar Histórico de Compras al Portapapeles",
            on_click=self.copiar_historial_compras
        )

        self.right_panel = ft.Container(
            width=0, visible=False, bgcolor="white", border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.05, "black")),
            animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
            content=ft.Column([
                # Cabecera Panel con el botón de copiar
                ft.Container(
                    content=ft.Row([
                        ft.Text("Histórico de Entradas", weight="bold", size=13, color=Config.COLOR_PRIMARY, expand=True),
                        self.btn_copiar_compras_panel,
                        self.btn_fecha_compras_panel,
                        ft.IconButton(ft.icons.CLOSE, icon_size=16, on_click=self.toggle_right_panel)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=10, bgcolor="#f4f6f8", border_radius=ft.border_radius.only(top_left=8, top_right=8)
                ),
                ft.Container(content=kpi_compras_panel, padding=ft.padding.symmetric(horizontal=10)),
                ft.Container(content=self.segment_agrupacion, padding=ft.padding.symmetric(horizontal=10), alignment=ft.alignment.center),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Container(content=self.panel_compras_list, expand=True, padding=10)
            ], spacing=8)
        )

        self.filtro_badge_compras = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.FILTER_ALT, size=14, color="white"),
                ft.Text("Filtro Activo", color="white", weight="bold", size=11),
                ft.IconButton(
                    ft.icons.CLOSE, icon_size=14, icon_color="white",
                    on_click=self.limpiar_filtro_compras,
                    style=ft.ButtonStyle(padding=0), width=20, height=20
                )
            ], tight=True),
            bgcolor="teal700", padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=12, visible=False
        )

        self.btn_toggle_panel = ft.IconButton(
            icon=ft.icons.HISTORY_TOGGLE_OFF,
            tooltip="Ver Histórico de Compras del Día",
            on_click=self.toggle_right_panel
        )

        self.lbl_titulo = ft.Text("Módulo de Compras", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        main_column = ft.Column([
            self.progress_bar,
            ft.Row([self.lbl_titulo, self.filtro_badge_compras, ft.Container(expand=True), self.btn_toggle_panel, self.btn_fullscreen]),
            self.summary_container,
            self.tabs
        ], expand=True, spacing=10)

        self.content = ft.Row([
            main_column,
            self.right_panel
        ], expand=True, spacing=10)
        
        self.load_data()
        self._render_tabla_cargas()

    def toggle_right_panel(self, e):
        self.panel_abierto = not self.panel_abierto
        self.right_panel.width = 330 if self.panel_abierto else 0
        self.right_panel.visible = self.panel_abierto
        self.right_panel.padding = 0
        self.btn_toggle_panel.icon = ft.icons.HISTORY if self.panel_abierto else ft.icons.HISTORY_TOGGLE_OFF
        if self.panel_abierto:
            self.cargar_historial_panel()
        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def on_date_compras_timeline_change(self, e):
        if self.date_picker_compras_timeline.value:
            self.fecha_historial_activa = self.date_picker_compras_timeline.value.strftime("%Y-%m-%d")
            self.btn_fecha_compras_panel.text = self.fecha_historial_activa
            self.cargar_historial_panel()

    def on_agrupacion_change(self, e):
        if e.control.selected:
            self.modo_agrupacion_compras = list(e.control.selected)[0]
            self.cargar_historial_panel()

    def cargar_historial_panel(self):
        if not self.page: return

        def worker():
            items = self.db.get_historial_compras_dia(self.fecha_historial_activa, self.modo_agrupacion_compras)

            tot_pesos = sum([item["total"] for item in items])
            tot_unds = sum([item["unidades"] for item in items])

            self.lbl_tot_compras_panel.value = f"${tot_pesos:,.0f} COP"
            self.lbl_cant_compras_panel.value = f"{tot_unds:g} unds"

            self.panel_compras_list.controls.clear()

            for item in items:
                self.panel_compras_list.controls.append(self._crear_card_item_compras(item))

            if not self.panel_compras_list.controls:
                self.panel_compras_list.controls.append(
                    ft.Container(content=ft.Text("Sin compras registradas en esta fecha.", size=11, color="grey"), padding=20, alignment=ft.alignment.center)
                )

            if hasattr(self, "safe_update"):
                self.safe_update()
            else:
                self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _crear_card_item_compras(self, item):
        tipo = item["tipo"]

        if tipo == "COMPRA":
            badge_txt = f"FACTURA: {item['factura']}"
            badge_bg, badge_col = "#e6f4ea", "teal800"
            sub_txt = item["proveedor"]
            icon_mat = ft.icons.RECEIPT
        elif tipo == "PROVEEDOR_RESUMEN":
            badge_txt = f"{item['facturas_cant']} Facturas"
            badge_bg, badge_col = "#e8f0fe", "blue800"
            sub_txt = item["proveedor"]
            icon_mat = ft.icons.BUSINESS
        else:
            # AJUSTE_ENTRADA
            badge_txt = "ENTRADA AJUSTE (+)"
            badge_bg, badge_col = "#fef3c7", "orange800"
            sub_txt = item["factura"]
            icon_mat = ft.icons.TUNE

        badge = ft.Container(
            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_col, no_wrap=True),
            padding=ft.padding.symmetric(horizontal=6, vertical=2), bgcolor=badge_bg, border_radius=10
        )

        card = ft.Container(
            content=ft.Row([
                ft.Icon(icon_mat, size=16, color="teal700"),
                ft.Column([
                    badge,
                    ft.Text(sub_txt, size=11, weight="bold", color="black87", no_wrap=True, tooltip=sub_txt),
                ], expand=True, spacing=2),
                ft.Column([
                    ft.Text(f"${item['total']:,.0f}", size=11, weight="bold", color="black87"),
                    ft.Text(f"{item['unidades']:g} unds", size=9, color="grey", text_align=ft.TextAlign.RIGHT)
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=1)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=8,
            border_radius=6,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#eeeeee"),
            on_click=lambda e, i=item: self.aplicar_filtro_cruzado_compras(i),
            ink=True
        )
        return card

    def aplicar_filtro_cruzado_compras(self, item):
        tipo = item["tipo"]
        self.progress_bar.visible = True
        if hasattr(self, "safe_update"):
            self.safe_update()
        else:
            self.page.update()

        if tipo == "PROVEEDOR_RESUMEN":
            self.filtro_proveedor_activo = item["proveedor"]
            self.filtro_factura_activo = None
            desc = f"Proveedor: {item['proveedor']}"
        else:
            self.filtro_factura_activo = item["ref"]
            self.filtro_proveedor_activo = None
            desc = f"Factura: {item['factura']}"

        lbl = self.filtro_badge_compras.content.controls[1]
        lbl.value = desc
        self.filtro_badge_compras.visible = True

        self.current_page = 1
        self.load_data()

    def limpiar_filtro_compras(self, e=None):
        self.filtro_factura_activo = None
        self.filtro_proveedor_activo = None
        self.filtro_badge_compras.visible = False
        self.current_page = 1
        self.load_data()

    def _load_cargas(self):
        if os.path.exists(self.cargas_file):
            try:
                with open(self.cargas_file, "r", encoding="utf-8") as f:
                    self.cargas_data = json.load(f)
            except Exception:
                self.cargas_data = {}
        else:
            self.cargas_data = {}

    def _save_cargas(self):
        try:
            with open(self.cargas_file, "w", encoding="utf-8") as f:
                json.dump(self.cargas_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error guardando cargas: {e}")

    def on_date_cargas_change(self, e):
        if self.date_picker_cargas.value:
            self.fecha_carga_actual = self.date_picker_cargas.value.strftime("%Y-%m-%d")
            self.fecha_carga_btn.text = self.fecha_carga_actual
            if self.page:
                self.page.update()

    def on_date_filtro_cargas_change(self, e):
        if self.date_picker_filtro_cargas.value:
            self.fecha_filtro_cargas = self.date_picker_filtro_cargas.value.strftime("%Y-%m-%d")
            self.btn_filtro_fecha_cargas.tooltip = f"Fecha: {self.fecha_filtro_cargas}"
            self.btn_filtro_fecha_cargas.icon_color = "blue"
            self.btn_clear_filtro_cargas.visible = True
            if self.page:
                self.page.update()
            self._render_tabla_cargas()

    def clear_filtro_fecha_cargas(self, e):
        self.fecha_filtro_cargas = None
        self.btn_filtro_fecha_cargas.tooltip = "Filtrar por Fecha"
        self.btn_filtro_fecha_cargas.icon_color = None
        self.btn_clear_filtro_cargas.visible = False
        self.date_picker_filtro_cargas.value = None
        if self.page:
            self.page.update()
        self._render_tabla_cargas()

    def _render_tabla_cargas(self):
        self.table_cargas.rows.clear()
        
        lista_cargas = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                lista_cargas.append(data)
                
        # Ordenar por ID descendente (más nuevos arriba)
        lista_cargas.sort(key=lambda x: x["id"], reverse=True)
        
        for data in lista_cargas:
            # --- Filtrado Visual ---
            if self.fecha_filtro_cargas and data.get("fecha") != self.fecha_filtro_cargas:
                continue
                    
            if self.drop_filtro_estado_cargas.value != "Todos" and data.get("estado") != self.drop_filtro_estado_cargas.value:
                continue
            # -----------------------
            
            id_carga = data["id"]
            nombre = f"Página No. {data['pagina']} ({data['fecha']})"
            archivo_orig = os.path.basename(data.get("archivo_original", "Desconocido"))
            estado = data["estado"]
            
            txt_crono = ft.Text("⏱️ 20s", color="red", weight="bold", visible=False)
            
            texto_btn = "Extraer Datos" if estado in ["Nuevo", "Falló", "Sobreescrito"] else "Ver"
            color_btn = Config.COLOR_PRIMARY if texto_btn == "Extraer Datos" else "grey"
            icon_btn = ft.icons.DOCUMENT_SCANNER if texto_btn == "Extraer Datos" else ft.icons.VISIBILITY
            
            btn_accion = ft.ElevatedButton(
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
            
            acciones_row = ft.Row([btn_accion, txt_crono, btn_eliminar], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            color_estado = "black"
            if estado == "Procesado con éxito": color_estado = "green"
            elif estado == "Falló": color_estado = "red"
            elif estado == "Guardado": color_estado = "blue"
            elif estado == "Sobreescrito": color_estado = "orange"
            
            self.table_cargas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(id_carga))),
                        ft.DataCell(ft.Text(nombre, weight="bold")),
                        ft.DataCell(ft.Text(archivo_orig[:20] + "..." if len(archivo_orig) > 20 else archivo_orig, tooltip=archivo_orig)),
                        ft.DataCell(ft.Text(estado, color=color_estado, weight="bold")),
                        ft.DataCell(acciones_row),
                    ]
                )
            )
            
        if self.page:
            self.page.update()


    def on_eliminar_carga(self, data):
        grupo_key = data.get("fecha")
        num_pag = str(data.get("pagina"))
        estado = data.get("estado")
        id_carga = data["id"]
        
        if estado == "Guardado":
            datos_ext = data.get("datos_extraidos", [])
            filas_resumen = []
            lista_eas = []
            cant_tot = 0.0
            costo_tot = 0.0

            for inv in datos_ext:
                ea = inv.get("numero_entrada") or inv.get("numero_factura") or ""
                if ea and ea not in lista_eas:
                    lista_eas.append(ea)
                    
                for p in inv.get("productos", []):
                    cod = p.get("codigo_insumo", "")
                    nom = getattr(self, 'nombres_insumos', {}).get(cod, f"Insumo [{cod}]")
                    cant = float(p.get("cantidad") or 0)
                    costo = float(p.get("costo_unitario") or 0)
                    iva = float(p.get("iva") or 0)
                    subtot = (cant * costo) + iva
                    
                    cant_tot += cant
                    costo_tot += subtot
                    
                    filas_resumen.append(
                        ft.Row([
                            ft.Text(f"• [{cod}] {nom[:22]}", size=11, expand=True, weight="bold"),
                            ft.Text(f"{cant:g} unds", size=11, color="grey"),
                            ft.Text(f"${subtot:,.0f}", size=11, weight="bold", color="red700")
                        ])
                    )

            if not filas_resumen:
                filas_resumen.append(ft.Text("Sin detalle de insumos registrado.", size=11, color="grey"))

            def confirmar_eliminar_guardado(e):
                dlg.open = False
                self.safe_update()
                
                # 1. Eliminar en Supabase
                exito = self.db.eliminar_compras_por_entradas(lista_eas)
                if exito:
                    # 2. Remover localmente
                    if grupo_key in self.cargas_data and num_pag in self.cargas_data[grupo_key]:
                        del self.cargas_data[grupo_key][num_pag]
                        if not self.cargas_data[grupo_key]:
                            del self.cargas_data[grupo_key]
                    self._save_cargas()
                    
                    self.page.snack_bar = ft.SnackBar(ft.Text("Carga e inventario revertidos exitosamente."), bgcolor="orange700")
                    self.page.snack_bar.open = True
                    self.load_data()
                    self.load_summary()
                    self._render_tabla_cargas()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar registros en base de datos."), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.safe_update()

            def cerrar_dialogo_guardado(e):
                dlg.open = False
                self.safe_update()

            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                    ft.Text("Eliminar Carga Guardada (Afecta BD)", size=16, weight="bold", color="red700")
                ]),
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(
                                "⚠️ ATENCIÓN: Esta carga ya fue guardada en el sistema. Al eliminarla se BORRARÁN DEFINITIVAMENTE los siguientes movimientos de compra de Supabase y se REVERTIRÁ EL STOCK DEL INVENTARIO:",
                                size=11, color="red900", weight="bold"
                            ),
                            padding=10, bgcolor="#fde8e8", border_radius=6
                        ),
                        ft.Text("Insumos que se eliminarán:", size=12, weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(
                            content=ft.Column(filas_resumen, scroll=ft.ScrollMode.AUTO),
                            height=180,
                            padding=8, bgcolor="#f8f9fa", border_radius=6, border=ft.border.all(1, "#e0e0e0")
                        ),
                        ft.Divider(height=5),
                        ft.Row([
                            ft.Text("Total Productos:", size=11, color="grey"),
                            ft.Text(f"{cant_tot:g} unds", size=11, weight="bold"),
                            ft.Container(expand=True),
                            ft.Text("Costo Total a Revertir:", size=11, color="grey"),
                            ft.Text(f"${costo_tot:,.0f}", size=12, weight="bold", color="red700")
                        ])
                    ], tight=True, spacing=10),
                    width=450
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo_guardado),
                    ft.ElevatedButton("Eliminar Definitivamente", bgcolor="red700", color="white", on_click=confirmar_eliminar_guardado)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.safe_update()

        else:
            # Carga No Guardada
            def confirmar_eliminar_simple(e):
                dlg.open = False
                self.safe_update()
                
                import os
                arch_local = data.get("archivo")
                if arch_local and os.path.exists(arch_local):
                    try: os.remove(arch_local)
                    except: pass
                    
                if grupo_key in self.cargas_data and num_pag in self.cargas_data[grupo_key]:
                    del self.cargas_data[grupo_key][num_pag]
                    if not self.cargas_data[grupo_key]:
                        del self.cargas_data[grupo_key]
                        
                self._save_cargas()
                self.page.snack_bar = ft.SnackBar(ft.Text("Página de carga eliminada de la lista."), bgcolor="green")
                self.page.snack_bar.open = True
                self._render_tabla_cargas()

            def cerrar_dialogo_simple(e):
                dlg.open = False
                self.safe_update()

            dlg = ft.AlertDialog(
                title=ft.Text("Eliminar Carga de la Lista"),
                content=ft.Text(f"¿Estás seguro de eliminar la Página No. {data['pagina']} ({data['fecha']})? Esta carga aún no ha afectado la base de datos."),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo_simple),
                    ft.ElevatedButton("Eliminar", bgcolor="red700", color="white", on_click=confirmar_eliminar_simple)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.safe_update()

    def on_accion_carga(self, e, data, txt_crono):
        btn = e.control
        if btn.text == "Ver":
            self.carga_activa = data
            self.parsed_data = data.get("datos_extraidos", [])
            
            codigos_extraidos = set()
            for invoice in self.parsed_data:
                for p in invoice.get("productos", []):
                    codigos_extraidos.add(str(p.get("codigo_insumo", "")))
            if codigos_extraidos:
                self.nombres_insumos = self.db.get_nombres_insumos(list(codigos_extraidos))
            else:
                self.nombres_insumos = {}
                
            self.show_confirm_ui()
            return
            
        if getattr(self, "is_extraccion_activa", False):
            self.page.snack_bar = ft.SnackBar(ft.Text("Hay una extracción en proceso. Espere que termine el cronómetro."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        self.is_extraccion_activa = True
        btn.text = "Extrayendo..."
        btn.icon = ft.icons.HOURGLASS_TOP
        
        for row in self.table_cargas.rows:
            accion_row = row.cells[-1].content
            b = accion_row.controls[0]
            if b.text == "Extraer Datos":
                b.disabled = True
                
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Analizando documento con Inteligencia Artificial..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()
        
        threading.Thread(target=self._worker_extraccion, args=(data, btn, txt_crono), daemon=True).start()

    def _worker_extraccion(self, data, btn, txt_crono):
        try:
            extracted = self.ai_parser.parse_compras_pdf_page(data["archivo"], 0)
            
            if extracted and isinstance(extracted, list) and len(extracted) > 0:
                data["estado"] = "Procesado con éxito"
                data["datos_extraidos"] = extracted
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("¡Extracción exitosa!"), bgcolor="green")
            else:
                data["estado"] = "Falló"
                data["datos_extraidos"] = []
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Fallo en la extracción. Revise el PDF o intente de nuevo."), bgcolor="red")
                    
            if self.page:
                self.page.snack_bar.open = True
            self._save_cargas()
            
            txt_crono.visible = True
            btn.text = "Enfriando..."
            btn.icon = ft.icons.TIMER
            for i in range(20, 0, -1):
                txt_crono.value = f"⏱️ {i}s"
                if self.page:
                    self.page.update()
                time.sleep(1)
                
        except Exception as ex:
            data["estado"] = "Falló"
            self._save_cargas()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error en extracción: {ex}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            self.is_extraccion_activa = False
            self._render_tabla_cargas()
    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def did_mount(self):
        # Agregar los overlays a la página principal
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        if self.dlg_loading not in self.page.overlay:
            self.page.overlay.append(self.dlg_loading)
        if self.dlg_confirm not in self.page.overlay:
            self.page.overlay.append(self.dlg_confirm)
        if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        if hasattr(self, "date_picker_compras_timeline") and self.date_picker_compras_timeline not in self.page.overlay:
            self.page.overlay.append(self.date_picker_compras_timeline)
            
        # Nuevos overlays para Cargas
        if hasattr(self, "dlg_metadatos_pdf") and self.dlg_metadatos_pdf not in self.page.overlay:
            self.page.overlay.append(self.dlg_metadatos_pdf)
        if hasattr(self, "date_picker_cargas") and self.date_picker_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_cargas)
        if hasattr(self, "date_picker_filtro_cargas") and self.date_picker_filtro_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_filtro_cargas)
            
        self.page.update()
        self.load_summary()
        self.cargar_sugerencias_compras()
        self.load_data()

    def cargar_sugerencias_compras(self):
        compras, _ = self.db.get_compras(page=1, page_size=1000)
        sug_set = set()
        for c in compras:
            cat_info = c.get("catalogo_insumos") or {}
            cod = c.get("codigo_insumo")
            nom = cat_info.get("nombre")
            prov = c.get("proveedor")
            fact = c.get("numero_factura")
            
            if cod and nom: sug_set.add(f"[{cod}] {nom}")
            if prov and prov != "N/A": sug_set.add(f"Proveedor: {prov}")
            if fact: sug_set.add(f"Factura: {fact}")

        self.search_autocomplete.suggestions = [
            {"key": str(idx), "value": val}
            for idx, val in enumerate(sorted(sug_set))
        ]
        if hasattr(self, 'safe_update'):
            self.safe_update()
        elif self.page:
            self.page.update()
        
    def load_summary(self):
        res = self.db.get_compras_summary()
        self.lbl_compras_mes.value = f"${res.get('total_mes', 0):,.2f}"
        self.lbl_compras_hoy.value = f"${res.get('total_hoy', 0):,.2f}"
        self.lbl_cantidad.value = f"{res.get('cantidad_total', 0):,.2f}"
        if self.page:
            self.update()
            
    def open_date_picker(self, e):
        self.date_picker.pick_date()
        
    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_date.tooltip = f"Fecha: {self.fecha_corte}"
            self.btn_date.icon_color = "blue"
            self.btn_clear_date.visible = True
            if self.page:
                self.page.update()
            self.current_page = 1
            self.load_data()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e):
        self.fecha_corte = None
        self.btn_date.tooltip = "Filtrar por Fecha"
        self.btn_date.icon_color = None
        self.btn_clear_date.visible = False
        self.date_picker.value = None
        if self.page:
            self.page.update()
        self.current_page = 1
        self.load_data()
        
    def on_agregar_click(self, e):
        # En lugar de abrir file_picker, abrimos el modal de metadatos
        self.dlg_metadatos_pdf.open = True
        if self.page:
            self.page.update()

    def _cerrar_modal_metadatos(self, e=None):
        self.dlg_metadatos_pdf.open = False
        if self.page:
            self.page.update()

    def _abrir_file_picker_desde_modal(self, e):
        self.fecha_seleccionada = self.fecha_carga_actual
        self._cerrar_modal_metadatos()
        self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"], dialog_title="Selecciona el Reporte de Compras")

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            pdf_path = e.files[0].path
            
            self.lbl_loading_text.value = "Dividiendo PDF en páginas..."
            self.dlg_loading.open = True
            self.page.update()
            
            threading.Thread(target=self._dividir_y_guardar_pdf, args=(pdf_path,), daemon=True).start()

    def _dividir_y_guardar_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            grupo_key = self.fecha_seleccionada
            if grupo_key not in self.cargas_data:
                self.cargas_data[grupo_key] = {}
                
            paginas_existentes = [int(p) for p in self.cargas_data[grupo_key].keys()]
            max_pagina = max(paginas_existentes) if paginas_existentes else 0
            
            max_id = 0
            for k, pags in self.cargas_data.items():
                for p_num, d in pags.items():
                    if d.get("id", 0) > max_id:
                        max_id = d["id"]
            
            os.makedirs("pdfs_locales", exist_ok=True)
            
            for p_idx in range(total_pages):
                num_pag = max_pagina + p_idx + 1
                id_carga = max_id + p_idx + 1
                
                writer = PdfWriter()
                writer.add_page(reader.pages[p_idx])
                
                nombre_archivo = f"compra_{grupo_key}_pag_{num_pag}.pdf"
                ruta_local = os.path.join("pdfs_locales", nombre_archivo)
                
                with open(ruta_local, "wb") as f:
                    writer.write(f)
                    
                self.cargas_data[grupo_key][str(num_pag)] = {
                    "id": id_carga,
                    "fecha": grupo_key,
                    "pagina": num_pag,
                    "archivo_original": pdf_path,
                    "archivo": ruta_local,
                    "estado": "Nuevo"
                }
                
            self._save_cargas()
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Se dividió el PDF en {total_pages} páginas exitosamente."), bgcolor="green")
            self.page.snack_bar.open = True
            
        except Exception as e:
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error procesando PDF: {e}"), bgcolor="red")
            self.page.snack_bar.open = True
            
        finally:
            if self.page:
                self.page.update()
                self._render_tabla_cargas()

    def animate_loading(self, base_msg):
        messages = [
            base_msg,
            "Puliendo datos para enviarlos...",
            "Generando el formato de carga...",
            "A unos pasos de finalizar..."
        ]
        idx = 0
        while getattr(self, "is_loading", False):
            if hasattr(self, "lbl_loading_text") and self.page:
                self.lbl_loading_text.value = messages[idx % len(messages)]
                try:
                    self.page.update()
                except Exception:
                    pass
            idx += 1
            time.sleep(5)
            self.is_loading = False
            self.dlg_loading.open = False
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Ocurrió un error inesperado: {str(e)}", color="white"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
    def update_totals(self, e=None):
        gran_cant = 0.0
        gran_costo = 0.0
        gran_iva = 0.0
        gran_total = 0.0
        
        factura_totals = {}
        
        for item in self.productos_rows:
            if item["type"] == "product":
                try:
                    cant = float(item["cantidad_ctl"].value.replace(',', '.'))
                    costo = float(item["costo_ctl"].value.replace(',', '.'))
                    iva = float(item["iva_ctl"].value.replace(',', '.'))
                    
                    row_total = (cant * costo) + iva
                    item["total_ctl"].value = f"${row_total:,.2f}"
                    
                    factura_idx = item["factura_idx"]
                    factura_totals[factura_idx] = factura_totals.get(factura_idx, 0) + row_total
                    
                    gran_cant += cant
                    gran_costo += costo
                    gran_iva += iva
                    gran_total += row_total
                except:
                    item["total_ctl"].value = "Error"
                    
        for item in self.productos_rows:
            if item["type"] == "header":
                idx = item["factura_idx"]
                total = factura_totals.get(idx, 0)
                item["total_factura_ctl"].value = f"Total Factura: ${total:,.2f}"
                    
        self.txt_gran_cant.value = f"{gran_cant:,.2f}"
        self.txt_gran_costo.value = f"${gran_costo:,.2f}"
        self.txt_gran_iva.value = f"${gran_iva:,.2f}"
        self.txt_gran_total.value = f"${gran_total:,.2f}"
        if self.page:
            self.page.update()

    def show_confirm_ui(self):
        # Guardar el contenido original de la vista para poder volver a él
        if not hasattr(self, "main_content"):
            self.main_content = self.content
            
        self.productos_rows = []
        facturas_count = len(self.parsed_data)
        productos_count = 0
        
        # Como ahora parsed_data es una lista de facturas, las iteramos todas
        for idx, invoice in enumerate(self.parsed_data):
            ea = invoice.get("numero_entrada", "")
            fecha = invoice.get("fecha", "")
            factura = invoice.get("numero_factura", "")
            proveedor = invoice.get("proveedor", "")
            
            total_factura_ctl = ft.Text("Total Factura: $0.00", weight="bold", color=Config.COLOR_PRIMARY)
            self.productos_rows.append({
                "type": "header",
                "factura_idx": idx,
                "total_factura_ctl": total_factura_ctl,
                "row_ctl": ft.Container(
                    content=ft.Row([
                        ft.Text(f"EA: {ea} | Factura: {factura} | Proveedor: {proveedor} | Fecha: {fecha}", weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(expand=True),
                        total_factura_ctl
                    ]),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY),
                    padding=5,
                    border_radius=5
                )
            })
            
            # Productos de esta factura
            for p in invoice.get("productos", []):
                productos_count += 1
                cod = str(p.get("codigo_insumo", ""))
                # Extraemos el nombre de la BD si existe, sino lo dejamos como "Desconocido"
                nombre = self.nombres_insumos.get(cod, "Desconocido")
                
                def get_codigo_change_handler(nombre_control):
                    def handler(e):
                        val = e.control.value
                        if val:
                            nombres = self.db.get_nombres_insumos([val])
                            nombre_control.value = nombres.get(val, "Desconocido")
                        else:
                            nombre_control.value = "Desconocido"
                        nombre_control.tooltip = nombre_control.value
                        if self.page: self.page.update()
                    return handler
                
                nombre_ctl = ft.Text(nombre[:25], width=180, no_wrap=True, tooltip=nombre)
                codigo_ctl = ft.TextField(label="Código", value=cod, width=90, dense=True, on_change=get_codigo_change_handler(nombre_ctl))
                cantidad_ctl = ft.TextField(label="Cant.", value=str(p.get("cantidad", 0)), width=70, dense=True, on_change=self.update_totals)
                costo_ctl = ft.TextField(label="Costo U.", value=str(p.get("costo_unitario", 0)), width=80, dense=True, on_change=self.update_totals)
                iva_ctl = ft.TextField(label="IVA", value=str(p.get("iva", 0)), width=80, dense=True, on_change=self.update_totals)
                total_ctl = ft.Text("$0.00", width=100, weight="bold")
                
                self.productos_rows.append({
                    "type": "product",
                    "factura_idx": idx,
                    "ea": ea,
                    "fecha": fecha,
                    "factura": factura,
                    "proveedor": proveedor,
                    "codigo_ctl": codigo_ctl,
                    "nombre_ctl": nombre_ctl,
                    "cantidad_ctl": cantidad_ctl,
                    "costo_ctl": costo_ctl,
                    "iva_ctl": iva_ctl,
                    "total_ctl": total_ctl,
                    "row_ctl": ft.Row([codigo_ctl, nombre_ctl, cantidad_ctl, costo_ctl, iva_ctl, total_ctl])
                })
            
        list_view = ft.ListView(
            controls=[item["row_ctl"] for item in self.productos_rows],
            expand=True,
            spacing=10
        )
        
        # Resumen Visual y Controles de Totales
        self.txt_gran_cant = ft.Text("0", weight="bold")
        self.txt_gran_costo = ft.Text("$0", weight="bold")
        self.txt_gran_iva = ft.Text("$0", weight="bold")
        self.txt_gran_total = ft.Text("$0", weight="bold", size=18, color=Config.COLOR_PRIMARY)
        
        is_last_page = not (hasattr(self, 'total_pages_pdf') and self.current_page_idx < self.total_pages_pdf - 1)
        botones_acciones = [ft.TextButton("Volver", on_click=self.close_confirm_ui)]
        
        if not is_last_page:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar", bgcolor="grey", color="white", on_click=self.on_guardar_compra_partial))
            botones_acciones.append(ft.ElevatedButton("Confirmar y Continuar", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_compra))
        else:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar Todo", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_compra))
            
        # --- NUEVO DISEÑO DEL FOOTER ---
        # 1. Fila de Información Financiera (Estilo Dashboard)
        info_row = ft.Row([
            ft.Text("RESUMEN TOTAL", weight="bold", size=18, color=Config.COLOR_PRIMARY),
            ft.Container(expand=True), # Empuja los totales hacia la derecha
            
            ft.Column([ft.Text("Cant. Total", size=12, color="grey"), self.txt_gran_cant], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("Costo Base", size=12, color="grey"), self.txt_gran_costo], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("IVA Total", size=12, color="grey"), self.txt_gran_iva], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("GRAN TOTAL", size=12, color="grey", weight="bold"), self.txt_gran_total], spacing=2, horizontal_alignment="end"),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 2. Fila de Botones de Acción
        buttons_row = ft.Row([
            ft.Container(expand=True), # Empuja los botones hacia el extremo derecho
            *botones_acciones # Desempaqueta la lista de botones dinámicos
        ], alignment=ft.MainAxisAlignment.END)

        # 3. Contenedor Principal del Footer
        footer = ft.Container(
            content=ft.Column([
                info_row,
                ft.Divider(height=15, color=ft.colors.with_opacity(0.1, "black")),
                buttons_row
            ], spacing=0),
            bgcolor=ft.colors.with_opacity(0.03, Config.COLOR_PRIMARY),
            padding=20,
            border_radius=8,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY)),
            margin=ft.padding.only(top=10)
        )
        
        if hasattr(self, 'total_pages_pdf'):
            titulo = f"Datos Extraídos - Pág. No. {self.current_page_idx + 1} de {self.total_pages_pdf}"
        elif hasattr(self, 'carga_activa'):
            titulo = f"Datos Extraídos - Pág. No. {self.carga_activa.get('pagina', 1)}"
        else:
            titulo = "Revisión de Compras (Modo Inmersivo)"
        header = ft.Row([
            ft.Text(titulo, size=24, weight="bold"),
            ft.Text(f"{facturas_count} Facturas extraídas | {productos_count} Productos en total", color="grey")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Reemplazamos el contenido actual por el modo Inmersivo/Fullscreen
        self.content = ft.Column([
            header,
            ft.Divider(),
            ft.Row([
                ft.Container(width=90, content=ft.Text("Código", weight="bold")),
                ft.Container(width=180, content=ft.Text("Nombre (desde BD)", weight="bold")),
                ft.Container(width=70, content=ft.Text("Cantidad", weight="bold")),
                ft.Container(width=80, content=ft.Text("Costo U.", weight="bold")),
                ft.Container(width=80, content=ft.Text("IVA", weight="bold")),
                ft.Container(width=100, content=ft.Text("Costo Total", weight="bold"))
            ]),
            list_view,
            footer
        ], expand=True)
        
        self.update_totals()
        self.page.update()
        
    def close_confirm_ui(self, e):
        # Volver al diseño principal
        self.content = self.main_content
        self.page.update()
        
    def on_guardar_compra_partial(self, e):
        if hasattr(self, 'total_pages_pdf'):
            self.current_page_idx = self.total_pages_pdf
        self.on_guardar_compra(e)

    def on_guardar_compra(self, e):
        # 1. Bloquear interfaz y mostrar carga
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        if self.page:
            self.page.update()
            
        # 2. Lanzar worker de guardado
        import threading
        threading.Thread(target=self._guardar_compra_worker, args=(btn_control,), daemon=True).start()

    def _guardar_compra_worker(self, btn_control):
        try:
            compras_list = []
            lista_eas_to_delete = []
            
            # Si venimos del flujo nuevo de carga_activa:
            grupo_key = None
            pagina_origen = None
            if hasattr(self, 'carga_activa'):
                grupo_key = self.carga_activa["fecha"]
                pagina_origen = self.carga_activa["pagina"]

            for item in self.productos_rows:
                if item["type"] == "product":
                    cant_str = str(item["cantidad_ctl"].value).replace(',', '.')
                    costo_str = str(item["costo_ctl"].value).replace(',', '.')
                    iva_str = str(item["iva_ctl"].value).replace(',', '.')
                    
                    cantidad = float(cant_str)
                    costo = float(costo_str)
                    iva = float(iva_str)
                    total = (cantidad * costo) + iva
                    
                    fecha_val = grupo_key if grupo_key else item["fecha"]
                    if not fecha_val:
                        import datetime
                        fecha_val = datetime.date.today().strftime("%Y-%m-%d")
                        
                    compras_list.append({
                        "numero_entrada": item["ea"],
                        "fecha": fecha_val,
                        "numero_factura": item["factura"],
                        "proveedor": item["proveedor"],
                        "codigo_insumo": item["codigo_ctl"].value,
                        "cantidad": cantidad,
                        "costo_unitario": costo,
                        "iva": iva,
                        "costo_total": total
                    })
                    
                    if item["ea"] not in lista_eas_to_delete:
                        lista_eas_to_delete.append(item["ea"])
                        
            if compras_list:
                codigos_unicos = list(set([c["codigo_insumo"] for c in compras_list]))
                codigos_validos = self.db.get_nombres_insumos(codigos_unicos)
                
                codigos_invalidos = [c for c in codigos_unicos if c not in codigos_validos]
                if codigos_invalidos:
                    if self.page:
                        self.page.snack_bar = ft.SnackBar(
                            ft.Text(f"Códigos no existen en catálogo: {', '.join(codigos_invalidos)}. Corrígelos en la tabla primero.", color="white"), 
                            bgcolor="red",
                            duration=8000
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                    return
            
            if compras_list:
                # 1. Eliminar datos viejos de esta misma página
                self.db.eliminar_compras_por_entradas(lista_eas_to_delete)
                
                # 2. Insertar los nuevos datos
                if self.db.insert_compras(compras_list):
                    self.page.snack_bar = ft.SnackBar(ft.Text("Página guardada exitosamente en BD."), bgcolor="green")
                    self.page.snack_bar.open = True
                    
                    # 3. Actualizar el estado local a Guardado
                    if grupo_key and str(pagina_origen) in self.cargas_data.get(grupo_key, {}):
                        self.cargas_data[grupo_key][str(pagina_origen)]["estado"] = "Guardado"
                        self._save_cargas()
                        
                    self.close_confirm_ui(None)
                    self._render_tabla_cargas()
                    self.load_data()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar en base de datos"), bgcolor="red")
                    self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("No hay datos para guardar."), bgcolor="orange")
                self.page.snack_bar.open = True
                    
        except ValueError:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico en cantidad, costo o IVA."), bgcolor="red")
                self.page.snack_bar.open = True
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            # 3. Restaurar interfaz incondicionalmente
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
                
            if self.page:
                self.page.update()
            
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        if self.page:
            self.update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        search_val = self.search_input_text.value or self.search_autocomplete.value or ""
        
        fact_filtro = getattr(self, 'filtro_factura_activo', None)
        prov_filtro = getattr(self, 'filtro_proveedor_activo', None)
        f_corte = getattr(self, 'fecha_corte', None)

        data, total = self.db.get_compras(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val,
            fecha_corte=f_corte,
            factura_filtro=fact_filtro,
            proveedor_filtro=prov_filtro
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        self.data_table.rows.clear()
        
        for item in data:
            fecha_raw = str(item.get('fecha', ''))
            # Cortar a 'YYYY-MM-DD' si viene con timestamp
            fecha_formateada = fecha_raw[:10] if len(fecha_raw) >= 10 else fecha_raw
            
            # El nombre viene del JOIN con catalogo_insumos: catalogo_insumos.nombre
            cat_info = item.get('catalogo_insumos') or {}
            nombre_insumo = cat_info.get('nombre', 'Desconocido')
            
            cantidad = int(item.get('cantidad', 0) or 0)
            costo_unit = float(item.get('costo_unitario', 0) or 0)
            costo_tot = float(item.get('costo_total', 0) or 0)
            
            iva_val = float(item.get('iva') or item.get('valor_iva') or 0)
            
            str_costo_unit = f"${costo_unit:,.2f}"
            str_iva = f"${iva_val:,.2f}"
            str_costo_tot = f"${costo_tot:,.2f}"
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(fecha_formateada)),
                    ft.DataCell(ft.Text(str(item.get('numero_factura') or 'N/A'))),
                    ft.DataCell(ft.Text(str(item.get('proveedor') or 'N/A'))),
                    ft.DataCell(ft.Text(str(item.get('codigo_insumo', '')))),
                    ft.DataCell(ft.Container(content=ft.Text(nombre_insumo), width=280)),
                    ft.DataCell(ft.Text(str(cantidad), weight="bold")),
                    ft.DataCell(ft.Text(str_costo_unit)),
                    ft.DataCell(ft.Text(str_iva)),
                    ft.DataCell(ft.Text(str_costo_tot, color="blue", weight="bold")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT_OUTLINED, icon_color="blue", tooltip="Editar", on_click=lambda e, i=item: self.abrir_modal_editar_compra(i)),
                            ft.IconButton(icon=ft.icons.DELETE_OUTLINED, icon_color="red", tooltip="Eliminar", on_click=lambda e, i=item: self.confirmar_eliminar_compra(i))
                        ], spacing=0)
                    ),
                ]
            )
            self.data_table.rows.append(row)
            
        self.update_pagination_ui()
        
    def update_pagination_ui(self):
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros en total"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        # Apagar indicador de carga al finalizar
        self.progress_bar.visible = False
        
        if self.page:
            self.update()
        
    def on_search(self, e):
        self.current_page = 1
        self.load_data()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()

    def on_extraer_todo_masivo(self, e):
        if getattr(self, "is_extraccion_activa", False):
            self.page.snack_bar = ft.SnackBar(ft.Text("Ya hay una extracción en curso."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        import threading
        threading.Thread(target=self._worker_extraccion_masiva, daemon=True).start()

    def _worker_extraccion_masiva(self):
        self.is_extraccion_activa = True

        # 1. Recopilar pendientes
        pendientes = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                if data.get("estado") in ["Nuevo", "Falló", "Sobreescrito"]:
                    pendientes.append(data)

        if not pendientes:
            self.is_extraccion_activa = False
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("No hay páginas pendientes por extraer."), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
            return

        # 2. Calcular Tiempos
        total_items = len(pendientes)
        # Estimado: 5 seg proceso + 20 seg enfriamiento por página (salvo la última)
        tiempo_estimado_segundos = (total_items * 25) - 20 

        # 3. Interfaz de Progreso Inmersiva
        lbl_estado_progreso = ft.Text(f"Páginas en cola: {total_items}", weight="bold", size=16)
        lbl_tiempo = ft.Text(f"Tiempo estimado total: ~{tiempo_estimado_segundos // 60} min {tiempo_estimado_segundos % 60} seg", color="grey")
        lbl_enfriamiento = ft.Text("", size=12, color="orange", weight="bold")
        barra_progreso = ft.ProgressBar(width=400, color="purple700", bgcolor="#eeeeee", value=0)

        dlg_progreso = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesamiento Masivo IA", color="purple700"),
            content=ft.Column([
                lbl_estado_progreso,
                lbl_tiempo,
                barra_progreso,
                lbl_enfriamiento,
                ft.Text("Por favor NO cierres esta ventana ni la aplicación.", size=11, color="red")
            ], tight=True, spacing=10)
        )

        if self.page:
            self.page.overlay.append(dlg_progreso)
            dlg_progreso.open = True
            self.page.update()

        exitos = 0
        fallos = 0
        import time

        # 4. Bucle de Procesamiento
        for idx, data in enumerate(pendientes):
            try:
                if self.page:
                    lbl_estado_progreso.value = f"Extrayendo página {idx + 1} de {total_items}..."
                    lbl_tiempo.value = f"Analizando estructura de {data.get('archivo', '')}..."
                    barra_progreso.value = idx / total_items
                    self.page.update()

                # Resolución dinámica según el módulo
                if hasattr(self.ai_parser, "parse_ventas_pdf_page") and "ventas" in str(self.__class__).lower():
                    extracted = self.ai_parser.parse_ventas_pdf_page(data["archivo"], 0, data.get("tipo", "Remisión"))
                else:
                    extracted = self.ai_parser.parse_compras_pdf_page(data["archivo"], 0)

                if extracted and isinstance(extracted, list) and len(extracted) > 0:
                    data["estado"] = "Procesado con éxito"
                    data["datos_extraidos"] = extracted
                    exitos += 1
                else:
                    data["estado"] = "Falló"
                    data["datos_extraidos"] = []
                    fallos += 1

                self._save_cargas()

                if self.page:
                    self._render_tabla_cargas()

                # 5. Enfriamiento de seguridad API (No se aplica al último registro)
                if idx < total_items - 1:
                    for i in range(20, 0, -1):
                        if self.page and dlg_progreso.open:
                            lbl_enfriamiento.value = f"Pausa anti-saturación de API: {i}s..."
                            self.page.update()
                        time.sleep(1)
                    if self.page:
                        lbl_enfriamiento.value = ""

            except Exception as ex:
                data["estado"] = "Falló"
                self._save_cargas()
                fallos += 1

        # 6. Finalización
        self.is_extraccion_activa = False
        if self.page:
            dlg_progreso.open = False
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Proceso masivo completado. Éxitos: {exitos}, Fallos: {fallos}"), 
                bgcolor="green" if fallos == 0 else "orange"
            )
            self.page.snack_bar.open = True
            barra_progreso.value = 1
            self.page.update()
            self._render_tabla_cargas()

    def copiar_historial_compras(self, e):
        """
        Obtiene las compras del día agrupadas por proveedor y construye
        un texto limpio formateado para el portapapeles del sistema.
        """
        if not self.page: return

        def worker():
            # Consultar desglose exacto por proveedor para la fecha activa
            items_prov = self.db.get_historial_compras_dia(self.fecha_historial_activa, "PROVEEDOR")

            tot_pesos = self.lbl_tot_compras_panel.value
            tot_unds = self.lbl_cant_compras_panel.value

            lineas_prov = []
            for item in items_prov:
                prov = item.get("proveedor", "Clientes Varios")
                total = item.get("total", 0)
                unds = item.get("unidades", 0)
                fact_cant = item.get("facturas_cant", 1)
                lineas_prov.append(f"  • {prov}: ${total:,.0f} COP ({unds:g} unds | {fact_cant} fact.)")

            prov_text = "\n".join(lineas_prov) if lineas_prov else "  (Sin registros de proveedores)"

            texto_copia = (
                f"🛍️ HISTÓRICO DE ENTRADAS / COMPRAS\n"
                f"📅 Fecha: {self.fecha_historial_activa}\n"
                f"💵 Total Compras del Día: {tot_pesos} ({tot_unds})\n"
                f"-----------------------------------------\n"
                f"🏢 DESGLOSE POR PROVEEDOR:\n"
                f"{prov_text}\n"
                f"-----------------------------------------"
            )

            self.page.set_clipboard(texto_copia)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="white", size=18),
                    ft.Text("Histórico de compras copiado al portapapeles exitosamente", color="white")
                ]),
                bgcolor="teal700"
            )
            self.page.snack_bar.open = True

            if hasattr(self, "safe_update"):
                self.safe_update()
            else:
                self.page.update()

        import threading
        threading.Thread(target=worker, daemon=True).start()

    # --- INICIO CRUD MANUAL COMPRAS ---
    def _construir_modal_crud(self):
        self.crud_codigo_insumo = CustomAutoComplete(
            hint_text="Buscar insumo (Código o Nombre)",
            on_select=self._on_insumo_crud_select
        )
        self.crud_codigo_insumo.width = 350
        self.crud_fecha = ft.TextField(label="Fecha (YYYY-MM-DD)", width=150)
        self.crud_ea = ft.TextField(label="N° Entrada (EA)", width=150)
        self.crud_factura = ft.TextField(label="N° Factura", width=150)
        self.crud_proveedor = ft.TextField(label="Proveedor", width=250)
        self.crud_cantidad = ft.TextField(label="Cantidad", width=120, on_change=self._calc_tot_crud)
        self.crud_costo_unit = ft.TextField(label="Costo Unit.", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_iva = ft.TextField(label="IVA", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_total_lbl = ft.Text("$ 0.00", size=20, weight="bold", color="blue700")
        self.crud_item_id = None
        
        self.dlg_crud = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar Compra"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    self.crud_codigo_insumo,
                    ft.Row([self.crud_fecha, self.crud_ea, self.crud_factura]),
                    self.crud_proveedor,
                    ft.Row([self.crud_cantidad, self.crud_costo_unit, self.crud_iva]),
                    ft.Divider(height=10),
                    ft.Row([ft.Text("Costo Total:", size=16, weight="bold"), self.crud_total_lbl])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_crud()),
                ft.ElevatedButton("Guardar", bgcolor="blue700", color="white", on_click=self.guardar_compra_formulario)
            ]
        )

    def _on_insumo_crud_select(self, e):
        pass

    def _calc_tot_crud(self, e=None):
        try:
            cant = float(self.crud_cantidad.value or 0)
            cost = float(self.crud_costo_unit.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * cost) + iva
            self.crud_total_lbl.value = f"$ {tot:,.2f}"
            self.safe_update()
        except ValueError:
            self.crud_total_lbl.value = "$ 0.00"
            self.safe_update()

    def _cerrar_crud(self):
        self.dlg_crud.open = False
        self.safe_update()

    def abrir_modal_crear_compra(self, e=None):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.suggestions = [{"key": i['codigo_insumo'], "value": f"[{i['codigo_insumo']}] {i['nombre']}"} for i in insumos]
        
        self.crud_item_id = None
        self.dlg_crud.title.value = "Registrar Nueva Compra"
        self.crud_codigo_insumo.value = ""
        self.crud_fecha.value = datetime.date.today().strftime("%Y-%m-%d")
        self.crud_ea.value = ""
        self.crud_factura.value = ""
        self.crud_proveedor.value = ""
        self.crud_cantidad.value = ""
        self.crud_costo_unit.value = ""
        self.crud_iva.value = "0"
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def abrir_modal_editar_compra(self, item):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.suggestions = [{"key": i['codigo_insumo'], "value": f"[{i['codigo_insumo']}] {i['nombre']}"} for i in insumos]
        
        self.crud_item_id = item.get("id_compra")
        self.dlg_crud.title.value = "Editar Compra"
        
        cod = item.get("codigo_insumo", "")
        nom = item.get("catalogo_insumos", {}).get("nombre", "")
        self.crud_codigo_insumo.value = f"[{cod}] {nom}" if cod else ""
        self.crud_fecha.value = str(item.get("fecha") or "")[:10]
        self.crud_ea.value = str(item.get("numero_entrada") or "")
        self.crud_factura.value = str(item.get("numero_factura") or "")
        self.crud_proveedor.value = str(item.get("proveedor") or "")
        self.crud_cantidad.value = str(item.get("cantidad") or 0)
        self.crud_costo_unit.value = str(item.get("costo_unitario") or 0)
        self.crud_iva.value = str(item.get("iva") or item.get("valor_iva") or 0)
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def guardar_compra_formulario(self, e):
        cod_raw = self.crud_codigo_insumo.value
        if not cod_raw or "[" not in cod_raw or "]" not in cod_raw:
            self.page.snack_bar = ft.SnackBar(ft.Text("Selecciona un insumo válido del listado."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        codigo_insumo = cod_raw.split("[")[1].split("]")[0]
        
        try:
            cant = float(self.crud_cantidad.value or 0)
            costo = float(self.crud_costo_unit.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * costo) + iva
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Revisa los valores numéricos ingresados."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        datos = {
            "fecha": self.crud_fecha.value,
            "numero_entrada": self.crud_ea.value,
            "numero_factura": self.crud_factura.value,
            "proveedor": self.crud_proveedor.value,
            "codigo_insumo": codigo_insumo,
            "cantidad": cant,
            "costo_unitario": costo,
            "iva": iva,
            "valor_iva": iva,
            "costo_total": tot
        }
        
        if self.crud_item_id:
            # Edit
            ok = self.db.update_compra_individual(self.crud_item_id, datos)
            msg = "Compra actualizada exitosamente."
        else:
            # Create
            datos["estado_registro"] = "VÁLIDO"
            ok = self.db.insert_compras([datos])
            msg = "Compra registrada exitosamente."
            
        if ok:
            self._cerrar_crud()
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green")
            self.page.snack_bar.open = True
            self.load_data()
            self.load_summary()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar la compra en la BD."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()

    def confirmar_eliminar_compra(self, item):
        id_compra = item.get("id_compra")
        cant = float(item.get("cantidad") or 0)
        insumo = item.get("catalogo_insumos", {}).get("nombre", "Desconocido")
        ea = item.get("numero_entrada") or item.get("numero_factura") or "S/D"
        tot = float(item.get("costo_total") or 0)
        
        def do_eliminar(e):
            dlg.open = False
            self.safe_update()
            if self.db.eliminar_compra_individual(id_compra):
                self.page.snack_bar = ft.SnackBar(ft.Text("Compra eliminada y stock revertido."), bgcolor="green")
                self.page.snack_bar.open = True
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar la compra en la BD."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                ft.Text("Eliminar Registro de Compra", color="red700")
            ]),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(f"Insumo: {insumo}", weight="bold"),
                    ft.Text(f"N° Documento: {ea}"),
                    ft.Text(f"Cantidad: {cant:g} unds"),
                    ft.Text(f"Costo Total: ${tot:,.2f}", color="blue700", weight="bold"),
                    ft.Divider(),
                    ft.Text(
                        f"⚠️ ADVERTENCIA: Al eliminar este registro de compra, se restarán {cant:g} unidades del inventario disponible y se ajustará el histórico financiero.",
                        color="red900", weight="bold"
                    )
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), self.safe_update())),
                ft.ElevatedButton("Eliminar Definitivamente", bgcolor="red700", color="white", on_click=do_eliminar)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()
    # --- FIN CRUD MANUAL COMPRAS ---
````

## File: ui/views/ventas.py
````python
import flet as ft
import threading
import time
import json
import os
from pypdf import PdfReader, PdfWriter
from config import Config
from core.supabase_client import SupabaseClient
from core.gemini_parser import GeminiParser
import math
import datetime
from ui.components.autocomplete import CustomAutoComplete

class VentasView(ft.Container):
    def safe_update(self):
        """Actualiza la UI de forma segura solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
        self.expand = True
        
        self.db = SupabaseClient()
        self.ai_parser = GeminiParser()
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        self.parsed_data = None # Para guardar temporalmente los datos extraídos
        
        # --- ESTADO PANEL HISTÓRICO VENTAS ---
        self.panel_abierto = False
        self.fecha_historial_activa = datetime.date.today().strftime("%Y-%m-%d")
        self.modo_agrupacion_ventas = "CATEGORIA" # "CATEGORIA" o "FACTURA"
        self.filtro_categoria_activo = None
        self.filtro_factura_activo = None

        self.date_picker_ventas_timeline = ft.DatePicker(on_change=self.on_date_ventas_timeline_change)
        # ---------------------------------------
        
        # Controles de Búsqueda
        def on_select_busqueda_ventas(e):
            texto = e.selection.value if hasattr(e, 'selection') and e.selection else str(e.control.value or "")
            if "[" in texto and "]" in texto:
                query = texto.split("]")[0].replace("[", "").strip()
            elif "Factura: " in texto:
                query = texto.replace("Factura: ", "").strip()
            else:
                query = texto.strip()
            self.search_input_text.value = query
            self.on_search(None)

        self.search_input_text = ft.TextField(visible=False)

        self.search_autocomplete = CustomAutoComplete(
            hint_text="Buscar por código, descripción o factura...",
            on_select=on_select_busqueda_ventas,
            text_size=12,
            expand=True
        )
        
        # Filtro de fecha
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )
        self.btn_date = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_OUTLINED,
            tooltip="Filtrar por Fecha",
            on_click=self.open_date_picker
        )
        
        self.btn_crear_manual = ft.ElevatedButton(
            text="Registrar Manual",
            icon=ft.icons.ADD_BOX,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=40,
            on_click=self.abrir_modal_crear_venta,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Dashboard Resumen
        self.lbl_ventas_hist = ft.Text("$0", size=20, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_ventas_hoy = ft.Text("$0", size=20, weight="bold", color="green")
        self.lbl_iva_hist = ft.Text("$0", size=20, weight="bold")
        self.lbl_iva_hoy = ft.Text("$0", size=20, weight="bold")
        
        self.summary_container = ft.Container(
            content=ft.Row([
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Ventas hasta la fecha"), self.lbl_ventas_hist]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Ventas realizadas hoy"), self.lbl_ventas_hoy]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("IVA Total Cobrado"), self.lbl_iva_hist]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("IVA Total en el día"), self.lbl_iva_hoy]), padding=5), expand=True),
            ])
        )
        
        self.btn_agregar = ft.ElevatedButton(
            text="Agregar Venta",
            icon=ft.icons.ADD,
            bgcolor=Config.COLOR_SECONDARY,
            color="white",
            height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # File Picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        
        # Diálogo de Carga
        self.lbl_loading_text = ft.Text("Preparando archivo...", text_align=ft.TextAlign.CENTER)
        self.dlg_loading = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesando con Inteligencia Artificial"),
            content=ft.Column([
                ft.ProgressRing(),
                self.lbl_loading_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
        )
        
        # Nuevo Diálogo de División PDF
        self.dlg_procesando_pdf = ft.AlertDialog(
            modal=True,
            content=ft.Row([
                ft.ProgressRing(),
                ft.Text("Dividiendo PDF en páginas locales...")
            ], alignment=ft.MainAxisAlignment.CENTER)
        )
        
        # Modal de Metadatos
        self.fecha_carga_actual = datetime.date.today().strftime("%Y-%m-%d")
        self.date_picker_cargas = ft.DatePicker(on_change=self.on_date_cargas_change)
        
        self.fecha_carga_btn = ft.OutlinedButton(
            text=self.fecha_carga_actual,
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_cargas.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=40,
            width=250
        )
        self.tipo_carga_dropdown = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Remisión"), ft.dropdown.Option("Factura POS")], dense=True, width=250)
        self.dlg_metadatos_pdf = ft.AlertDialog(
            modal=True,
            title=ft.Text("Metadatos del PDF"),
            content=ft.Column([
                ft.Text("Fecha de Documento:", size=12, color="grey", weight="bold"),
                self.fecha_carga_btn, 
                self.tipo_carga_dropdown
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cerrar_modal_metadatos),
                ft.ElevatedButton("Seleccionar Archivo", on_click=self._abrir_file_picker_desde_modal)
            ]
        )
        
        # Diálogo de Confirmación
        self.dlg_confirm = ft.AlertDialog(modal=True)
        
        # Tabla de Datos
        self.data_table = ft.DataTable(
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("Fecha", weight="bold")),
                ft.DataColumn(ft.Text("Factura", weight="bold")),
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Container(content=ft.Text("Nombre / Descripción", weight="bold"), width=250)),
                ft.DataColumn(ft.Text("Cantidad", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Precio Unit.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("IVA", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Ingreso Total", weight="bold"), numeric=True),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, tooltip="Página Anterior", on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, tooltip="Página Siguiente", on_click=self.on_next_page, disabled=True)
        
        # Inicializar memoria local
        self.cargas_file = "cargas_locales.json"
        self.cargas_data = {}
        self._load_cargas()
        
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        # --- FILTROS TAB GESTIÓN DE CARGAS ---
        self.fecha_filtro_cargas = None
        self.date_picker_filtro_cargas = ft.DatePicker(on_change=self.on_date_filtro_cargas_change)
        
        self.btn_filtro_fecha_cargas = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH_OUTLINED,
            tooltip="Filtrar por Fecha",
            on_click=lambda e: self.date_picker_filtro_cargas.pick_date()
        )
        self.btn_clear_filtro_cargas = ft.IconButton(
            icon=ft.icons.CLEAR, tooltip="Limpiar Fecha",
            on_click=self.clear_filtro_fecha_cargas, visible=False, icon_color="red"
        )
        
        # Dropdowns con height ajustado y content_padding para evitar que el label se corte
        self.drop_filtro_tipo_cargas = ft.Dropdown(
            options=[ft.dropdown.Option("Todas"), ft.dropdown.Option("Remisiones"), ft.dropdown.Option("Ventas POS")],
            value="Todas", label="Tipo", dense=True, width=160, border_radius=8, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8), height=38,
            on_change=lambda e: self._render_tabla_cargas()
        )
        self.drop_filtro_estado_cargas = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Procesado con éxito"), ft.dropdown.Option("Falló"), ft.dropdown.Option("Guardado"), ft.dropdown.Option("Sobreescrito")],
            value="Todos", label="Estado", dense=True, width=170, border_radius=8, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8), height=38,
            on_change=lambda e: self._render_tabla_cargas()
        )

        # --- NUEVA TABLA DE GESTIÓN DE CARGAS ---
        self.table_cargas = ft.DataTable(
            data_row_min_height=40,
            data_row_max_height=40,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("ID", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Página", weight="bold")),
                ft.DataColumn(ft.Text("Tipo de Documento", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )

        # --- PREPARACIÓN DE LAS PESTAÑAS (TABS) ---

        # 1. Contenido del Tab 1: Registro Ventas
        btn_nueva_venta = ft.ElevatedButton(
            text="Agregar Venta", icon=ft.icons.ADD, bgcolor=Config.COLOR_SECONDARY, color="white", height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        row_filtros_ventas = ft.Row([
            self.search_autocomplete,
            self.btn_date,
            self.btn_clear_date,
            btn_nueva_venta
        ])

        contenedor_tabla_ventas = ft.Container(
            content=ft.Row([ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )

        footer_paginacion = ft.Container(
            content=ft.Row([self.lbl_total, ft.Container(expand=True), self.btn_prev, self.lbl_page_info, self.btn_next], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=10)
        )

        layout_tab_ventas = ft.Container(
            content=ft.Column([row_filtros_ventas, contenedor_tabla_ventas, footer_paginacion], expand=True, spacing=10),
            padding=ft.padding.only(top=15),
            expand=True
        )

        self.btn_extraer_todo = ft.ElevatedButton(
            text="Extraer Todo",
            icon=ft.icons.AUTO_MODE,
            bgcolor="purple700",
            color="white",
            height=45,
            on_click=self.on_extraer_todo_masivo,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )

        # 2. Contenido del Tab 2: Gestión de Cargas
        layout_tab_cargas = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.btn_filtro_fecha_cargas,
                    self.btn_clear_filtro_cargas,
                    self.drop_filtro_tipo_cargas,
                    self.drop_filtro_estado_cargas,
                    ft.Container(expand=True),
                    self.btn_extraer_todo,
                    ft.ElevatedButton(
                        text="Subir PDF de Ventas",
                        icon=ft.icons.UPLOAD_FILE,
                        bgcolor=Config.COLOR_PRIMARY,
                        color="white",
                        height=45,
                        on_click=self._abrir_modal_metadatos,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(
                    content=ft.Column([self.table_cargas], scroll=ft.ScrollMode.ALWAYS),
                    expand=True,
                    border_radius=8,
                    border=ft.border.all(1, ft.colors.with_opacity(0.1, "black"))
                )
            ], expand=True, spacing=10),
            padding=ft.padding.only(top=15),
            expand=True
        )

        # 3. Definición del Contenedor de Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Registro Ventas", icon=ft.icons.LIST_ALT, content=layout_tab_ventas),
                ft.Tab(text="Gestión de Cargas", icon=ft.icons.DRIVE_FOLDER_UPLOAD, content=layout_tab_cargas)
            ],
            expand=True
        )

        # --- DISEÑO DEL PANEL HISTÓRICO ---
        self.lbl_tot_ventas_panel = ft.Text("$0 COP", size=14, weight="bold", color="blue800")
        self.lbl_cant_ventas_panel = ft.Text("0 unds", size=10, color="grey")

        kpi_ventas_panel = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.POINT_OF_SALE, color="blue700", size=20),
                ft.Column([
                    ft.Text("TOTAL VENTAS DEL DÍA", size=9, weight="bold", color="grey"),
                    self.lbl_tot_ventas_panel
                ], spacing=0, expand=True),
                self.lbl_cant_ventas_panel
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10, bgcolor="#e8f0fe", border_radius=8, border=ft.border.all(1, "#d2e3fc")
        )

        self.segment_agrupacion_ventas = ft.SegmentedButton(
            segments=[
                ft.Segment(value="CATEGORIA", label=ft.Text("Por Categoría", size=10)),
                ft.Segment(value="FACTURA", label=ft.Text("Por Factura", size=10)),
            ],
            selected={"CATEGORIA"},
            on_change=self.on_agrupacion_ventas_change,
            show_selected_icon=False
        )

        self.btn_fecha_ventas_panel = ft.OutlinedButton(
            self.fecha_historial_activa,
            icon=ft.icons.CALENDAR_TODAY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), padding=5),
            height=30,
            on_click=lambda e: self.date_picker_ventas_timeline.pick_date()
        )

        self.panel_ventas_list = ft.ListView(expand=True, spacing=6)

        # Botón para copiar histórico de ventas
        self.btn_copiar_ventas_panel = ft.IconButton(
            icon=ft.icons.COPY_ROUNDED,
            icon_size=16,
            icon_color=Config.COLOR_PRIMARY,
            tooltip="Copiar Histórico de Ventas al Portapapeles",
            on_click=self.copiar_historial_ventas
        )

        self.right_panel = ft.Container(
            width=0, visible=False, bgcolor="white", border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.with_opacity(0.05, "black")),
            animate=ft.animation.Animation(250, ft.AnimationCurve.EASE_OUT),
            content=ft.Column([
                # Cabecera Panel con el botón de copiar
                ft.Container(
                    content=ft.Row([
                        ft.Text("Histórico de Ventas", weight="bold", size=13, color=Config.COLOR_PRIMARY, expand=True),
                        self.btn_copiar_ventas_panel,
                        self.btn_fecha_ventas_panel,
                        ft.IconButton(ft.icons.CLOSE, icon_size=16, on_click=self.toggle_right_panel)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=10, bgcolor="#f4f6f8", border_radius=ft.border_radius.only(top_left=8, top_right=8)
                ),
                ft.Container(content=kpi_ventas_panel, padding=ft.padding.symmetric(horizontal=10)),
                ft.Container(content=self.segment_agrupacion_ventas, padding=ft.padding.symmetric(horizontal=10), alignment=ft.alignment.center),
                ft.Divider(height=1, color="#e0e0e0"),
                ft.Container(content=self.panel_ventas_list, expand=True, padding=10)
            ], spacing=8)
        )

        self.filtro_badge_ventas = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.FILTER_ALT, size=14, color="white"),
                ft.Text("Filtro Activo", color="white", weight="bold", size=11),
                ft.IconButton(
                    ft.icons.CLOSE, icon_size=14, icon_color="white",
                    on_click=self.limpiar_filtro_ventas,
                    style=ft.ButtonStyle(padding=0), width=20, height=20
                )
            ], tight=True),
            bgcolor="blue700", padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=12, visible=False
        )

        self.btn_toggle_panel = ft.IconButton(
            icon=ft.icons.HISTORY_TOGGLE_OFF,
            tooltip="Ver Histórico de Ventas del Día",
            on_click=self.toggle_right_panel
        )

        # --- ENSAMBLAJE FINAL DE LA VISTA ---
        self.lbl_titulo = ft.Text("Registro de Ventas (Salidas)", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        main_column = ft.Column([
            self.progress_bar,
            ft.Row([self.lbl_titulo, self.filtro_badge_ventas, ft.Container(expand=True), self.btn_toggle_panel, self.btn_fullscreen]),
            self.summary_container,
            self.tabs
        ], expand=True, spacing=10)

        self.content = ft.Row([
            main_column,
            self.right_panel
        ], expand=True, spacing=10)

        # Llamar al método de renderizado en lugar del mock
        self._render_tabla_cargas()

    def toggle_right_panel(self, e):
        self.panel_abierto = not self.panel_abierto
        self.right_panel.width = 330 if self.panel_abierto else 0
        self.right_panel.visible = self.panel_abierto
        self.right_panel.padding = 0
        self.btn_toggle_panel.icon = ft.icons.HISTORY if self.panel_abierto else ft.icons.HISTORY_TOGGLE_OFF
        if self.panel_abierto:
            self.cargar_historial_panel()
        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def on_date_ventas_timeline_change(self, e):
        if self.date_picker_ventas_timeline.value:
            self.fecha_historial_activa = self.date_picker_ventas_timeline.value.strftime("%Y-%m-%d")
            self.btn_fecha_ventas_panel.text = self.fecha_historial_activa
            self.cargar_historial_panel()

    def on_agrupacion_ventas_change(self, e):
        if e.control.selected:
            self.modo_agrupacion_ventas = list(e.control.selected)[0]
            self.cargar_historial_panel()

    def cargar_historial_panel(self):
        if not self.page: return

        def worker():
            items = self.db.get_historial_ventas_dia(self.fecha_historial_activa, self.modo_agrupacion_ventas)

            tot_pesos = sum([item["total"] for item in items])
            tot_unds = sum([item["unidades"] for item in items])

            self.lbl_tot_ventas_panel.value = f"${tot_pesos:,.0f} COP"
            self.lbl_cant_ventas_panel.value = f"{tot_unds:g} unds"

            self.panel_ventas_list.controls.clear()

            for item in items:
                self.panel_ventas_list.controls.append(self._crear_card_item_ventas(item))

            if not self.panel_ventas_list.controls:
                self.panel_ventas_list.controls.append(
                    ft.Container(content=ft.Text("Sin ventas registradas en esta fecha.", size=11, color="grey"), padding=20, alignment=ft.alignment.center)
                )

            if hasattr(self, "safe_update"):
                self.safe_update()
            else:
                self.page.update()

        threading.Thread(target=worker, daemon=True).start()

    def _crear_card_item_ventas(self, item):
        tipo = item["tipo"]

        if tipo == "CATEGORIA_RESUMEN":
            badge_txt = f"CATEGORÍA: {item['categoria']}"
            badge_bg, badge_col = "#e8f0fe", "blue800"
            sub_txt = f"{item['items_count']} ítems vendidos"
            icon_mat = ft.icons.CATEGORY
        else:
            # FACTURA_VENTA
            subtipo = item.get("subtipo", "POS")
            badge_txt = f"DOC: {item['factura']} ({subtipo})"
            badge_bg, badge_col = "#e6f4ea" if "POS" in subtipo.upper() else "#f3e8fd", "teal800" if "POS" in subtipo.upper() else "purple800"
            sub_txt = f"Venta {subtipo}"
            icon_mat = ft.icons.RECEIPT_LONG

        badge = ft.Container(
            content=ft.Text(badge_txt, size=9, weight="bold", color=badge_col, no_wrap=True),
            padding=ft.padding.symmetric(horizontal=6, vertical=2), bgcolor=badge_bg, border_radius=10
        )

        card = ft.Container(
            content=ft.Row([
                ft.Icon(icon_mat, size=16, color="blue700"),
                ft.Column([
                    badge,
                    ft.Text(sub_txt, size=11, weight="bold", color="black87", no_wrap=True, tooltip=sub_txt),
                ], expand=True, spacing=2),
                ft.Column([
                    ft.Text(f"${item['total']:,.0f}", size=11, weight="bold", color="black87"),
                    ft.Text(f"{item['unidades']:g} unds", size=9, color="grey", text_align=ft.TextAlign.RIGHT)
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=1)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=8,
            border_radius=6,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#eeeeee"),
            on_click=lambda e, i=item: self.aplicar_filtro_cruzado_ventas(i),
            ink=True
        )
        return card

    def aplicar_filtro_cruzado_ventas(self, item):
        tipo = item["tipo"]
        self.progress_bar.visible = True
        if hasattr(self, "safe_update"):
            self.safe_update()
        else:
            self.page.update()

        if tipo == "CATEGORIA_RESUMEN":
            self.filtro_categoria_activo = item["categoria"]
            self.filtro_factura_activo = None
            desc = f"Categoría: {item['categoria']}"
        else:
            self.filtro_factura_activo = item["ref"]
            self.filtro_categoria_activo = None
            desc = f"Factura/Doc: {item['factura']}"

        lbl = self.filtro_badge_ventas.content.controls[1]
        lbl.value = desc
        self.filtro_badge_ventas.visible = True

        self.current_page = 1
        self.load_data()

    def limpiar_filtro_ventas(self, e=None):
        self.filtro_categoria_activo = None
        self.filtro_factura_activo = None
        self.filtro_badge_ventas.visible = False
        self.current_page = 1
        self.load_data()

    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

    def did_mount(self):
        if hasattr(self, "date_picker_ventas_timeline") and self.date_picker_ventas_timeline not in self.page.overlay:
            self.page.overlay.append(self.date_picker_ventas_timeline)
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        if hasattr(self, "dlg_loading") and self.dlg_loading not in self.page.overlay:
            self.page.overlay.append(self.dlg_loading)
        if hasattr(self, "dlg_confirm") and self.dlg_confirm not in self.page.overlay:
            self.page.overlay.append(self.dlg_confirm)
        if hasattr(self, "dlg_metadatos_pdf") and self.dlg_metadatos_pdf not in self.page.overlay:
            self.page.overlay.append(self.dlg_metadatos_pdf)
        if hasattr(self, "dlg_procesando_pdf") and self.dlg_procesando_pdf not in self.page.overlay:
            self.page.overlay.append(self.dlg_procesando_pdf)
        if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        if hasattr(self, "date_picker_cargas") and self.date_picker_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_cargas)
        if hasattr(self, "date_picker_filtro_cargas") and self.date_picker_filtro_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_filtro_cargas)
            
        self.page.update()
        self.load_summary()
        self.cargar_sugerencias_ventas()
        self.load_data()

    def cargar_sugerencias_ventas(self):
        ventas, _ = self.db.get_ventas(page=1, page_size=1000)
        sug_set = set()
        for v in ventas:
            cat_info = v.get("catalogo_insumos") or {}
            cod = v.get("codigo_insumo")
            nom = cat_info.get("nombre")
            fact = v.get("factura_no")
            
            if cod and nom: sug_set.add(f"[{cod}] {nom}")
            if fact and fact != "N/A": sug_set.add(f"Factura: {fact}")

        self.search_autocomplete.suggestions = [
            {"key": str(idx), "value": val}
            for idx, val in enumerate(sorted(sug_set))
        ]
        if hasattr(self, 'safe_update'):
            self.safe_update()
        elif self.page:
            self.page.update()
        self._render_tabla_cargas()

    def _abrir_modal_metadatos(self, e):
        self.dlg_metadatos_pdf.open = True
        self.page.update()

    def _cerrar_modal_metadatos(self, e=None):
        self.dlg_metadatos_pdf.open = False
        self.page.update()

    def on_date_filtro_cargas_change(self, e):
        if self.date_picker_filtro_cargas.value:
            self.fecha_filtro_cargas = self.date_picker_filtro_cargas.value.strftime("%Y-%m-%d")
            self.btn_filtro_fecha_cargas.tooltip = f"Fecha: {self.fecha_filtro_cargas}"
            self.btn_filtro_fecha_cargas.icon_color = "blue"
            self.btn_clear_filtro_cargas.visible = True
            if self.page:
                self.page.update()
            self._render_tabla_cargas()

    def clear_filtro_fecha_cargas(self, e):
        self.fecha_filtro_cargas = None
        self.date_picker_filtro_cargas.value = None
        self.btn_filtro_fecha_cargas.tooltip = "Filtrar por Fecha"
        self.btn_filtro_fecha_cargas.icon_color = None
        self.btn_clear_filtro_cargas.visible = False
        if self.page:
            self.page.update()
        self._render_tabla_cargas()

    def on_date_cargas_change(self, e):
        if self.date_picker_cargas.value:
            self.fecha_carga_actual = self.date_picker_cargas.value.strftime("%Y-%m-%d")
            self.fecha_carga_btn.text = self.fecha_carga_actual
            if self.page:
                self.page.update()

    def _load_cargas(self):
        if os.path.exists(self.cargas_file):
            try:
                with open(self.cargas_file, "r", encoding="utf-8") as f:
                    self.cargas_data = json.load(f)
            except Exception:
                self.cargas_data = {}

    def _save_cargas(self):
        with open(self.cargas_file, "w", encoding="utf-8") as f:
            json.dump(self.cargas_data, f, indent=4)

    def _render_tabla_cargas(self):
        if not hasattr(self, 'table_cargas'): return
        self.table_cargas.rows.clear()
        
        # Aplanar diccionario
        lista_cargas = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                lista_cargas.append(data)
                
        # Ordenar por ID descendente (más nuevos arriba)
        lista_cargas.sort(key=lambda x: x["id"], reverse=True)
        
        for data in lista_cargas:
            # --- Filtrado Visual ---
            if self.fecha_filtro_cargas and data.get("fecha") != self.fecha_filtro_cargas:
                continue
                
            if self.drop_filtro_tipo_cargas.value != "Todas":
                # Traducir los nombres de los filtros a los nombres internos guardados
                tipo_bd = "Remisión" if self.drop_filtro_tipo_cargas.value == "Remisiones" else "Factura POS"
                if data.get("tipo") != tipo_bd:
                    continue
                    
            if self.drop_filtro_estado_cargas.value != "Todos" and data.get("estado") != self.drop_filtro_estado_cargas.value:
                continue
            # -----------------------
            
            id_carga = data["id"]
            nombre = f"Página No. {data['pagina']} ({data['fecha']})"
            tipo = data["tipo"]
            estado = data["estado"]
            
            txt_crono = ft.Text("⏱️ 20s", color="red", weight="bold", visible=False)
            
            texto_btn = "Extraer Datos" if estado in ["Nuevo", "Falló", "Sobreescrito"] else "Ver"
            color_btn = Config.COLOR_PRIMARY if texto_btn == "Extraer Datos" else "grey"
            icon_btn = ft.icons.DOCUMENT_SCANNER if texto_btn == "Extraer Datos" else ft.icons.VISIBILITY
            
            btn_accion = ft.ElevatedButton(
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
                icon_color="red700",
                icon_size=18,
                tooltip="Eliminar Carga",
                on_click=lambda e, d=data: self.on_eliminar_carga(d)
            )
            acciones_row = ft.Row([btn_accion, txt_crono, btn_eliminar], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            color_estado = "black"
            if estado == "Procesado con éxito": color_estado = "green"
            elif estado == "Falló": color_estado = "red"
            elif estado == "Guardado": color_estado = "blue"
            elif estado == "Sobreescrito": color_estado = "orange"
            
            self.table_cargas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(id_carga))),
                        ft.DataCell(ft.Text(nombre, weight="bold")),
                        ft.DataCell(ft.Text(tipo)),
                        ft.DataCell(ft.Text(estado, color=color_estado, weight="bold")),
                        ft.DataCell(acciones_row),
                    ]
                )
            )
            
        if self.page:
            self.page.update()

    def on_eliminar_carga(self, data):
        estado = data.get("estado")
        id_carga = data["id"]
        
        # Encontrar grupo_key y num_pag en cargas_data
        grupo_key = None
        num_pag = str(data["pagina"])
        for g_k, pags in self.cargas_data.items():
            if num_pag in pags and pags[num_pag].get("id") == id_carga:
                grupo_key = g_k
                break
                
        if not grupo_key:
            grupo_key = f"{data['fecha']}_{data.get('tipo', 'Remisión')}"

        if estado == "Guardado":
            datos_ext = data.get("datos_extraidos", [])
            filas_resumen = []
            lista_facturas = []
            cant_tot = 0.0
            venta_tot = 0.0

            for inv in datos_ext:
                fact = inv.get("numero_factura") or ""
                if fact and fact not in lista_facturas:
                    lista_facturas.append(fact)
                    
                for p in inv.get("productos", []):
                    cod = p.get("codigo_item", "")
                    nom = getattr(self, 'nombres_insumos', {}).get(cod, f"Insumo [{cod}]")
                    cant = float(p.get("cantidad") or 0)
                    tot = float(p.get("costo_total") or p.get("subtotal") or 0)
                    
                    cant_tot += cant
                    venta_tot += tot
                    
                    filas_resumen.append(
                        ft.Row([
                            ft.Text(f"• [{cod}] {nom[:22]}", size=11, expand=True, weight="bold"),
                            ft.Text(f"{cant:g} unds", size=11, color="grey"),
                            ft.Text(f"${tot:,.0f}", size=11, weight="bold", color="blue700")
                        ])
                    )

            if not filas_resumen:
                filas_resumen.append(ft.Text("Sin detalle de insumos registrado.", size=11, color="grey"))

            def confirmar_eliminar_guardado(e):
                dlg.open = False
                self.safe_update()
                
                # 1. Eliminar en Supabase
                exito = self.db.eliminar_ventas_por_facturas(lista_facturas)
                if exito:
                    # 2. Remover localmente
                    if grupo_key in self.cargas_data and num_pag in self.cargas_data[grupo_key]:
                        del self.cargas_data[grupo_key][num_pag]
                        if not self.cargas_data[grupo_key]:
                            del self.cargas_data[grupo_key]
                    self._save_cargas()
                    
                    self.page.snack_bar = ft.SnackBar(ft.Text("Carga e inventario de ventas revertidos exitosamente."), bgcolor="orange700")
                    self.page.snack_bar.open = True
                    self.load_data()
                    self.load_summary()
                    self._render_tabla_cargas()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar registros en base de datos."), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.safe_update()

            def cerrar_dialogo_v_guardado(e):
                dlg.open = False
                self.safe_update()

            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                    ft.Text("Eliminar Carga Guardada (Afecta BD)", size=16, weight="bold", color="red700")
                ]),
                content=ft.Container(
                    width=450,
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(
                                "⚠️ ATENCIÓN: Esta carga ya fue guardada en el sistema. Al eliminarla se BORRARÁN DEFINITIVAMENTE las ventas de Supabase y se REVERTIRÁ EL STOCK DEL INVENTARIO (las unidades volverán al saldo disponible):",
                                size=11, color="red900", weight="bold"
                            ),
                            padding=10, bgcolor="#fde8e8", border_radius=6
                        ),
                        ft.Text("Insumos vendidos a revertir:", size=12, weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(
                            content=ft.Column(filas_resumen, scroll=ft.ScrollMode.AUTO),
                            height=180,
                            padding=8, bgcolor="#f8f9fa", border_radius=6, border=ft.border.all(1, "#e0e0e0")
                        ),
                        ft.Divider(height=5),
                        ft.Row([
                            ft.Text("Total Unidades:", size=11, color="grey"),
                            ft.Text(f"{cant_tot:g} unds", size=11, weight="bold"),
                            ft.Container(expand=True),
                            ft.Text("Total Venta a Revertir:", size=11, color="grey"),
                            ft.Text(f"${venta_tot:,.0f}", size=12, weight="bold", color="blue700")
                        ])
                    ], tight=True, spacing=10)
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo_v_guardado),
                    ft.ElevatedButton("Eliminar Definitivamente", bgcolor="red700", color="white", on_click=confirmar_eliminar_guardado)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.safe_update()

        else:
            # Carga No Guardada
            def confirmar_eliminar_simple(e):
                dlg.open = False
                self.safe_update()
                
                import os
                arch_local = data.get("archivo")
                if arch_local and os.path.exists(arch_local):
                    try: os.remove(arch_local)
                    except: pass
                    
                if grupo_key in self.cargas_data and num_pag in self.cargas_data[grupo_key]:
                    del self.cargas_data[grupo_key][num_pag]
                    if not self.cargas_data[grupo_key]:
                        del self.cargas_data[grupo_key]
                        
                self._save_cargas()
                self.page.snack_bar = ft.SnackBar(ft.Text("Página de carga eliminada de la lista."), bgcolor="green")
                self.page.snack_bar.open = True
                self._render_tabla_cargas()

            def cerrar_dialogo_v_simple(e):
                dlg.open = False
                self.safe_update()

            dlg = ft.AlertDialog(
                title=ft.Text("Eliminar Carga de la Lista"),
                content=ft.Text(f"¿Estás seguro de eliminar la Página No. {data['pagina']} ({data['fecha']})? Esta carga aún no ha afectado la base de datos."),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo_v_simple),
                    ft.ElevatedButton("Eliminar", bgcolor="red700", color="white", on_click=confirmar_eliminar_simple)
                ]
            )
            self.page.overlay.append(dlg)
            dlg.open = True
            self.safe_update()

    def on_accion_carga(self, e, data, txt_crono):
        btn = e.control
        if btn.text == "Ver":
            # Cargar los datos extraídos previamente en la memoria de la vista
            self.carga_activa = data
            self.parsed_data = data.get("datos_extraidos", [])
            
            # Recuperar nombres_insumos
            codigos_extraidos = set()
            for invoice in self.parsed_data:
                for p in invoice.get("productos", []):
                    codigos_extraidos.add(str(p.get("codigo_item", "")))
            if codigos_extraidos:
                self.nombres_insumos = self.db.get_nombres_insumos(list(codigos_extraidos))
            else:
                self.nombres_insumos = {}
                
            self.show_confirm_ui()
            return
            
        if getattr(self, "is_extraccion_activa", False):
            self.page.snack_bar = ft.SnackBar(ft.Text("Hay una extracción en proceso. Espere que termine el cronómetro."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Bloquear estado global
        self.is_extraccion_activa = True
        
        # Cambiar el texto del botón clickeado
        btn.text = "Extrayendo..."
        btn.icon = ft.icons.HOURGLASS_TOP
        
        # Deshabilitar TODOS los demás botones de extraer en la tabla
        for row in self.table_cargas.rows:
            accion_row = row.cells[-1].content
            b = accion_row.controls[0]
            if b.text == "Extraer Datos":
                b.disabled = True
                
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Analizando documento con Inteligencia Artificial..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()
        
        # Iniciar worker en segundo plano para no congelar la pantalla
        import threading
        threading.Thread(target=self._worker_extraccion, args=(data, btn, txt_crono), daemon=True).start()

    def _worker_extraccion(self, data, btn, txt_crono):
        try:
            # Como el archivo ya es de 1 página, pasamos el índice 0
            extracted = self.ai_parser.parse_ventas_pdf_page(data["archivo"], 0, data.get("tipo", "Remisión"))
            
            if extracted and isinstance(extracted, list) and len(extracted) > 0:
                data["estado"] = "Procesado con éxito"
                data["datos_extraidos"] = extracted
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("¡Extracción exitosa!"), bgcolor="green")
            else:
                data["estado"] = "Falló"
                data["datos_extraidos"] = []
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Fallo en la extracción. Revise el PDF o intente de nuevo."), bgcolor="red")
                    
            if self.page:
                self.page.snack_bar.open = True
            self._save_cargas()
            
            # --- INICIO DEL CRONÓMETRO DE ENFRIAMIENTO (COOLDOWN) ---
            txt_crono.visible = True
            btn.text = "Enfriando..."
            btn.icon = ft.icons.TIMER
            for i in range(20, 0, -1):
                txt_crono.value = f"⏱️ {i}s"
                if self.page:
                    self.page.update()
                import time
                time.sleep(1)
                
        except Exception as ex:
            data["estado"] = "Falló"
            self._save_cargas()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error en extracción: {ex}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            self.is_extraccion_activa = False
            # Renderizar la tabla reactiva los botones automáticamente según su estado
            self._render_tabla_cargas()
        
    def load_summary(self):
        res = self.db.get_ventas_summary()
        self.lbl_ventas_hist.value = f"${res.get('total_historico', 0):,.2f}"
        self.lbl_ventas_hoy.value = f"${res.get('total_hoy', 0):,.2f}"
        self.lbl_iva_hist.value = f"${res.get('iva_historico', 0):,.2f}"
        self.lbl_iva_hoy.value = f"${res.get('iva_hoy', 0):,.2f}"
        if self.page:
            self.update()
            
    def open_date_picker(self, e):
        self.date_picker.pick_date()
        
    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_date.tooltip = f"Fecha: {self.fecha_corte}"
            self.btn_date.icon_color = "blue"
            self.btn_clear_date.visible = True
            if self.page:
                self.page.update()
            self.current_page = 1
            self.load_data()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e):
        self.fecha_corte = None
        self.btn_date.tooltip = "Filtrar por Fecha"
        self.btn_date.icon_color = None
        self.btn_clear_date.visible = False
        self.date_picker.value = None
        if self.page:
            self.page.update()
        self.current_page = 1
        self.load_data()
        
    def _abrir_file_picker_desde_modal(self, e):
        self.fecha_seleccionada = self.fecha_carga_actual
        self.tipo_seleccionado = self.tipo_carga_dropdown.value
        self._cerrar_modal_metadatos()
        self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"], dialog_title="Selecciona el Reporte de Ventas")

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            pdf_path = e.files[0].path
            self.dlg_procesando_pdf.open = True
            self.page.update()
            
            threading.Thread(target=self._dividir_y_guardar_pdf, args=(pdf_path,), daemon=True).start()

    def _dividir_y_guardar_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            grupo_key = f"{self.fecha_seleccionada}_{self.tipo_seleccionado}"
            if grupo_key not in self.cargas_data:
                self.cargas_data[grupo_key] = {}
                
            paginas_existentes = [int(p) for p in self.cargas_data[grupo_key].keys()]
            max_pagina = max(paginas_existentes) if paginas_existentes else 0
            
            # Crear carpeta raíz para los PDFs temporales si no existe
            os.makedirs("pdfs_locales", exist_ok=True)
            
            paginas_procesadas = 0
            for i in range(total_pages):
                pagina_real = i + 1
                
                # Regla de Solapamiento: Ignorar páginas anteriores a la última cargada
                if max_pagina > 0 and pagina_real < max_pagina:
                    continue
                    
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                
                nombre_archivo = f"pdfs_locales/ventas_{self.fecha_seleccionada}_{self.tipo_seleccionado.replace(' ', '_')}_Pag_{pagina_real}.pdf"
                
                with open(nombre_archivo, "wb") as f:
                    writer.write(f)
                    
                estado = "Sobreescrito" if (max_pagina > 0 and pagina_real == max_pagina) else "Nuevo"
                
                # Asignación de ID único consecutivo
                nuevo_id = 1
                if self.cargas_data:
                    todos_ids = [item.get("id", 0) for g in self.cargas_data.values() for item in g.values()]
                    nuevo_id = max(todos_ids) + 1 if todos_ids else 1
                
                if str(pagina_real) in self.cargas_data[grupo_key]:
                    nuevo_id = self.cargas_data[grupo_key][str(pagina_real)]["id"]
                
                self.cargas_data[grupo_key][str(pagina_real)] = {
                    "id": nuevo_id,
                    "pagina": pagina_real,
                    "tipo": self.tipo_seleccionado,
                    "fecha": self.fecha_seleccionada,
                    "archivo": nombre_archivo,
                    "estado": estado
                }
                paginas_procesadas += 1
                
            self._save_cargas()
            self._render_tabla_cargas()
            
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Éxito: Se generaron {paginas_procesadas} páginas en local."), bgcolor="green")
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error fraccionando PDF: {ex}"), bgcolor="red")
        finally:
            self.dlg_procesando_pdf.open = False
            if self.page:
                self.page.snack_bar.open = True
                self.page.update()

    def animate_loading(self, base_msg):
        messages = [
            base_msg,
            "Puliendo datos para enviarlos...",
            "Generando el formato de carga...",
            "A unos pasos de finalizar..."
        ]
        idx = 0
        while getattr(self, "is_loading", False):
            if hasattr(self, "lbl_loading_text") and self.page:
                self.lbl_loading_text.value = messages[idx % len(messages)]
                try:
                    self.page.update()
                except Exception:
                    pass
            idx += 1
            time.sleep(5)

    def procesar_siguiente_pagina(self):
        if self.current_page_idx >= self.total_pages_pdf:
            self.page.snack_bar = ft.SnackBar(ft.Text("¡Proceso finalizado con éxito!", color="white"), bgcolor="green")
            self.page.snack_bar.open = True
            self.close_confirm_ui(None)
            self.load_data()
            return
            
        pagina_actual = self.current_page_idx + 1
        base_msg = f"Extrayendo datos de la página {pagina_actual} de {self.total_pages_pdf}..."
        self.lbl_loading_text.value = base_msg
        self.dlg_loading.open = True
        self.page.update()
        
        self.is_loading = True
        threading.Thread(target=self.animate_loading, args=(base_msg,), daemon=True).start()
        
        try:
            data = self.ai_parser.parse_ventas_pdf_page(self.current_pdf_path, self.current_page_idx)
            
            if data and isinstance(data, list):
                lista_facturas = [item.get("numero_factura") for item in data if item.get("numero_factura")]
                existentes = self.db.get_ventas_existentes(lista_facturas)
                
                data_nueva = []
                codigos_extraidos = set()
                for invoice in data:
                    factura = invoice.get("numero_factura")
                    if factura not in existentes:
                        data_nueva.append(invoice)
                        for p in invoice.get("productos", []):
                            codigos_extraidos.add(str(p.get("codigo_item", "")))
                
                self.parsed_data = data_nueva
                
                if codigos_extraidos:
                    self.nombres_insumos = self.db.get_nombres_insumos(list(codigos_extraidos))
                else:
                    self.nombres_insumos = {}
            else:
                self.parsed_data = []
                
            self.is_loading = False
            self.dlg_loading.open = False
            self.page.update()
            
            self.show_confirm_ui()
            
            if data and isinstance(data, list) and not self.parsed_data:
                self.page.snack_bar = ft.SnackBar(ft.Text("Todos los datos de esta página ya están registrados. Haz clic en Continuar.", color="white"), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
            elif not data:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al procesar la página o no se extrajo información.", color="white"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as e:
            self.is_loading = False
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ocurrió un error inesperado: {str(e)}", color="white"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
                
    def update_totals(self, e=None):
        gran_cant = 0.0
        gran_costo = 0.0
        gran_iva = 0.0
        gran_total = 0.0
        
        factura_totals = {}
        
        for item in self.productos_rows:
            if item["type"] == "product":
                try:
                    cant = float(item["cantidad_ctl"].value.replace(',', '.'))
                    subtotal = float(item["subtotal_ctl"].value.replace(',', '.'))
                    iva = float(item["iva_ctl"].value.replace(',', '.'))
                    
                    row_total = subtotal + iva
                    item["total_ctl"].value = f"${row_total:,.2f}"
                    
                    precio_u = subtotal / cant if cant > 0 else 0
                    item["costo_ctl"].value = f"${precio_u:,.2f}"
                    
                    factura_idx = item["factura_idx"]
                    factura_totals[factura_idx] = factura_totals.get(factura_idx, 0) + row_total
                    
                    gran_cant += cant
                    gran_costo += precio_u
                    gran_iva += iva
                    gran_total += row_total
                except:
                    item["total_ctl"].value = "Error"
                    
        for item in self.productos_rows:
            if item["type"] == "header":
                idx = item["factura_idx"]
                total = factura_totals.get(idx, 0)
                item["total_factura_ctl"].value = f"Total Factura: ${total:,.2f}"
                
        self.txt_gran_cant.value = f"{gran_cant:,.2f}"
        self.txt_gran_costo.value = f"${gran_costo:,.2f}"
        self.txt_gran_iva.value = f"${gran_iva:,.2f}"
        self.txt_gran_total.value = f"${gran_total:,.2f}"
        if self.page:
            self.page.update()

    def show_confirm_ui(self):
        if not hasattr(self, "main_content"):
            self.main_content = self.content
            
        self.productos_rows = []
        facturas_count = len(self.parsed_data)
        productos_count = 0
        
        for idx, invoice in enumerate(self.parsed_data):
            fecha = invoice.get("fecha", "")
            factura = invoice.get("numero_factura", "")
            
            total_factura_ctl = ft.Text("Total Factura: $0.00", weight="bold", color=Config.COLOR_PRIMARY)
            self.productos_rows.append({
                "type": "header",
                "factura_idx": idx,
                "total_factura_ctl": total_factura_ctl,
                "row_ctl": ft.Container(
                    content=ft.Row([
                        ft.Text(f"Factura No.: {factura} | Fecha: {fecha}", weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(expand=True),
                        total_factura_ctl
                    ]),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY),
                    padding=5,
                    border_radius=5
                )
            })
            
            for p in invoice.get("productos", []):
                productos_count += 1
                cod = str(p.get("codigo_item", ""))
                nombre = self.nombres_insumos.get(cod, "Desconocido")
                
                def get_codigo_change_handler(nombre_control):
                    def handler(e):
                        val = e.control.value
                        if val:
                            nombres = self.db.get_nombres_insumos([val])
                            nombre_control.value = nombres.get(val, "Desconocido")
                        else:
                            nombre_control.value = "Desconocido"
                        nombre_control.tooltip = nombre_control.value
                        if self.page: self.page.update()
                    return handler
                
                nombre_ctl = ft.Text(nombre[:25], width=180, no_wrap=True, tooltip=nombre)
                codigo_ctl = ft.TextField(label="Código", value=cod, width=90, dense=True, on_change=get_codigo_change_handler(nombre_ctl))
                
                # Calcular precio unitario exacto: subtotal / cantidad
                cantidad_val = float(p.get("cantidad", 0))
                subtotal_val = float(p.get("subtotal", 0))
                precio_unitario = subtotal_val / cantidad_val if cantidad_val > 0 else 0.0
                
                cantidad_ctl = ft.TextField(label="Cant.", value=str(p.get("cantidad", 0)), width=70, dense=True, on_change=self.update_totals)
                subtotal_ctl = ft.TextField(label="Subtotal", value=str(subtotal_val), width=80, dense=True, on_change=self.update_totals)
                costo_ctl = ft.Text(f"${precio_unitario:,.2f}", width=80)
                iva_ctl = ft.TextField(label="IVA", value=str(p.get("iva", 0)), width=80, dense=True, on_change=self.update_totals)
                total_ctl = ft.Text("$0.00", width=100, weight="bold")
                
                self.productos_rows.append({
                    "type": "product",
                    "factura_idx": idx,
                    "fecha": fecha,
                    "factura": factura,
                    "codigo_ctl": codigo_ctl,
                    "nombre_ctl": nombre_ctl,
                    "cantidad_ctl": cantidad_ctl,
                    "subtotal_ctl": subtotal_ctl,
                    "costo_ctl": costo_ctl,
                    "iva_ctl": iva_ctl,
                    "total_ctl": total_ctl,
                    "row_ctl": ft.Row([codigo_ctl, nombre_ctl, cantidad_ctl, costo_ctl, subtotal_ctl, iva_ctl, total_ctl])
                })
            
        if len(self.productos_rows) == 0:
            list_view = ft.Container(
                content=ft.Text(
                    "Todos los datos de esta página ya están registrados en la base de datos.\nHaz clic en el botón de Confirmar para saltar a la siguiente página.",
                    color="orange",
                    weight="bold",
                    text_align=ft.TextAlign.CENTER,
                    size=16
                ),
                padding=50,
                alignment=ft.alignment.center,
                expand=True
            )
        else:
            list_view = ft.ListView(
                controls=[item["row_ctl"] for item in self.productos_rows],
                expand=True,
                spacing=10
            )
        
        self.txt_gran_cant = ft.Text("0", weight="bold")
        self.txt_gran_costo = ft.Text("$0", weight="bold")
        self.txt_gran_iva = ft.Text("$0", weight="bold")
        self.txt_gran_total = ft.Text("$0", weight="bold", size=18, color=Config.COLOR_PRIMARY)
        
        # Lógica de Botones Footer
        is_last_page = not (hasattr(self, 'total_pages_pdf') and self.current_page_idx < self.total_pages_pdf - 1)
        
        botones_acciones = [ft.TextButton("Volver", on_click=self.close_confirm_ui)]
        if not is_last_page:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar", bgcolor="grey", color="white", on_click=self.on_guardar_venta_partial))
            botones_acciones.append(ft.ElevatedButton("Confirmar y Continuar", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_venta))
        else:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar Todo", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_venta))
        
        # --- NUEVO DISEÑO DEL FOOTER ---
        # 1. Fila de Información Financiera (Estilo Dashboard)
        info_row = ft.Row([
            ft.Text("RESUMEN TOTAL", weight="bold", size=18, color=Config.COLOR_PRIMARY),
            ft.Container(expand=True), # Empuja los totales hacia la derecha
            
            ft.Column([ft.Text("Cant. Total", size=12, color="grey"), self.txt_gran_cant], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("Costo Base", size=12, color="grey"), self.txt_gran_costo], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("IVA Total", size=12, color="grey"), self.txt_gran_iva], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("GRAN TOTAL", size=12, color="grey", weight="bold"), self.txt_gran_total], spacing=2, horizontal_alignment="end"),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 2. Fila de Botones de Acción
        buttons_row = ft.Row([
            ft.Container(expand=True), # Empuja los botones hacia el extremo derecho
            *botones_acciones # Desempaqueta la lista de botones dinámicos
        ], alignment=ft.MainAxisAlignment.END)

        # 3. Contenedor Principal del Footer
        footer = ft.Container(
            content=ft.Column([
                info_row,
                ft.Divider(height=15, color=ft.colors.with_opacity(0.1, "black")),
                buttons_row
            ], spacing=0),
            bgcolor=ft.colors.with_opacity(0.03, Config.COLOR_PRIMARY),
            padding=20,
            border_radius=8,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY)),
            margin=ft.padding.only(top=10)
        )
        
        if hasattr(self, 'total_pages_pdf'):
            titulo = f"Datos Extraídos - Pág. No. {self.current_page_idx + 1} de {self.total_pages_pdf}"
        elif hasattr(self, 'carga_activa'):
            titulo = f"Datos Extraídos - Pág. No. {self.carga_activa.get('pagina', 1)} ({self.carga_activa.get('tipo', '')})"
        else:
            titulo = "Revisión de Ventas (Modo Inmersivo)"
        header = ft.Row([
            ft.Text(titulo, size=24, weight="bold"),
            ft.Text(f"{facturas_count} Facturas extraídas | {productos_count} Productos en total", color="grey")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.content = ft.Column([
            header,
            ft.Divider(),
            ft.Row([
                ft.Container(width=90, content=ft.Text("Código", weight="bold")),
                ft.Container(width=180, content=ft.Text("Nombre (desde BD)", weight="bold")),
                ft.Container(width=70, content=ft.Text("Cantidad", weight="bold")),
                ft.Container(width=80, content=ft.Text("Precio U.", weight="bold")),
                ft.Container(width=80, content=ft.Text("Subtotal", weight="bold")),
                ft.Container(width=80, content=ft.Text("IVA", weight="bold")),
                ft.Container(width=100, content=ft.Text("Costo Total", weight="bold"))
            ]),
            list_view,
            footer
        ], expand=True)
        
        self.update_totals()
        self.page.update()
        
    def close_confirm_ui(self, e):
        self.content = self.main_content
        self.page.update()
        
    def on_guardar_venta_partial(self, e):
        # Engañar a la lógica para que crea que es la última página
        if hasattr(self, 'total_pages_pdf'):
            self.current_page_idx = self.total_pages_pdf
        self.on_guardar_venta(e)

    def on_guardar_venta(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if self.page:
            self.update()
            
        threading.Thread(target=self._on_guardar_venta_worker, args=(btn_control,), daemon=True).start()

    def _on_guardar_venta_worker(self, btn_control):
        try:
            ventas_list = []
            
            # Recuperar metadatos de la carga que estamos confirmando
            fecha_doc = self.carga_activa["fecha"]
            tipo_doc = self.carga_activa["tipo"]
            pagina_origen = self.carga_activa["pagina"]
            
            for item in self.productos_rows:
                if item["type"] == "product":
                    try:
                        cant_str = str(item["cantidad_ctl"].value).replace(',', '.')
                        subtotal_str = str(item["subtotal_ctl"].value).replace(',', '.')
                        iva_str = str(item["iva_ctl"].value).replace(',', '.')
                        
                        cantidad = float(cant_str)
                        subtotal = float(subtotal_str)
                        iva = float(iva_str)
                        total = subtotal + iva
                        
                        ventas_list.append({
                            "fecha": fecha_doc, # Forzar la fecha seleccionada en el modal
                            "numero_factura": item["factura"],
                            "codigo_item": item["codigo_ctl"].value,
                            "descripcion": item["nombre_ctl"].value,
                            "cantidad": cantidad,
                            "precio_unitario": subtotal,
                            "iva": iva,
                            "costo_total": total,
                            "tipo_documento": tipo_doc,
                            "pagina_origen": pagina_origen
                        })
                    except ValueError:
                        self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico en cantidad, costo o IVA."), bgcolor="red")
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
            
            if ventas_list:
                # 1. Eliminar datos viejos de esta misma página (si fue una sobreescritura)
                self.db.eliminar_ventas_origen(fecha_doc, tipo_doc, pagina_origen)
                
                # 2. Insertar los nuevos datos
                if self.db.insert_ventas(ventas_list):
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"Página guardada exitosamente en BD."), bgcolor="green")
                    self.page.snack_bar.open = True
                    
                    # 3. Actualizar el estado local a Guardado
                    grupo_key = f"{fecha_doc}_{tipo_doc}"
                    if grupo_key in self.cargas_data and str(pagina_origen) in self.cargas_data[grupo_key]:
                        self.cargas_data[grupo_key][str(pagina_origen)]["estado"] = "Guardado"
                        self._save_cargas()
                    
                    self.close_confirm_ui(None)
                    self._render_tabla_cargas()
                    self.load_data()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar en base de datos"), bgcolor="red")
                    self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("No hay datos para guardar."), bgcolor="orange")
                self.page.snack_bar.open = True
                
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.update()
            
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        if self.page:
            self.update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        search_val = self.search_input_text.value or self.search_autocomplete.value or ""
        
        cat_filtro = getattr(self, 'filtro_categoria_activo', None)
        fact_filtro = getattr(self, 'filtro_factura_activo', None)
        f_corte = getattr(self, 'fecha_corte', None)

        data, total = self.db.get_ventas(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val,
            fecha_corte=f_corte,
            categoria_filtro=cat_filtro,
            factura_filtro=fact_filtro
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        self.data_table.rows.clear()
        
        for item in data:
            fecha_raw = str(item.get('fecha', ''))
            fecha_formateada = fecha_raw[:10] if len(fecha_raw) >= 10 else fecha_raw
            
            cat_info = item.get('catalogo_insumos') or {}
            nombre_bd = cat_info.get('nombre')
            nombre_desc = item.get('descripcion')
            nombre_final = nombre_bd if nombre_bd else (nombre_desc if nombre_desc else 'Desconocido')
            
            cantidad = float(item.get('cantidad', 0) or 0)
            precio_unitario = float(item.get('subtotal', 0) or 0)
            iva = float(item.get('iva', 0) or 0)
            costo_total = float(item.get('total', 0) or 0)
            
            str_precio = f"${precio_unitario:,.2f}"
            str_iva = f"${iva:,.2f}"
            str_total = f"${costo_total:,.2f}"
            
            str_cantidad = str(int(cantidad)) if cantidad.is_integer() else str(cantidad)
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(fecha_formateada)),
                    ft.DataCell(ft.Text(str(item.get('factura_no') or 'N/A'))),
                    ft.DataCell(ft.Text(str(item.get('codigo_insumo', '')))),
                    ft.DataCell(ft.Container(content=ft.Text(nombre_final), width=300)),
                    ft.DataCell(ft.Text(str_cantidad, weight="bold")),
                    ft.DataCell(ft.Text(str_precio)),
                    ft.DataCell(ft.Text(str_iva, color="grey")),
                    ft.DataCell(ft.Text(str_total, color="green", weight="bold")),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT_OUTLINED, icon_color="blue", tooltip="Editar", on_click=lambda e, i=item: self.abrir_modal_editar_venta(i)),
                            ft.IconButton(icon=ft.icons.DELETE_OUTLINED, icon_color="red", tooltip="Eliminar", on_click=lambda e, i=item: self.confirmar_eliminar_venta(i))
                        ], spacing=0)
                    ),
                ]
            )
            self.data_table.rows.append(row)
            
        self.update_pagination_ui()
        
    def update_pagination_ui(self):
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros en total"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        # Apagar indicador de carga al finalizar
        self.progress_bar.visible = False
        
        if self.page:
            self.update()
        
    def on_search(self, e):
        self.current_page = 1
        self.load_data()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()

    def on_extraer_todo_masivo(self, e):
        if getattr(self, "is_extraccion_activa", False):
            self.page.snack_bar = ft.SnackBar(ft.Text("Ya hay una extracción en curso."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        import threading
        threading.Thread(target=self._worker_extraccion_masiva, daemon=True).start()

    def _worker_extraccion_masiva(self):
        self.is_extraccion_activa = True

        # 1. Recopilar pendientes
        pendientes = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                if data.get("estado") in ["Nuevo", "Falló", "Sobreescrito"]:
                    pendientes.append(data)

        if not pendientes:
            self.is_extraccion_activa = False
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("No hay páginas pendientes por extraer."), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
            return

        # 2. Calcular Tiempos
        total_items = len(pendientes)
        # Estimado: 5 seg proceso + 20 seg enfriamiento por página (salvo la última)
        tiempo_estimado_segundos = (total_items * 25) - 20 

        # 3. Interfaz de Progreso Inmersiva
        lbl_estado_progreso = ft.Text(f"Páginas en cola: {total_items}", weight="bold", size=16)
        lbl_tiempo = ft.Text(f"Tiempo estimado total: ~{tiempo_estimado_segundos // 60} min {tiempo_estimado_segundos % 60} seg", color="grey")
        lbl_enfriamiento = ft.Text("", size=12, color="orange", weight="bold")
        barra_progreso = ft.ProgressBar(width=400, color="purple700", bgcolor="#eeeeee", value=0)

        dlg_progreso = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesamiento Masivo IA", color="purple700"),
            content=ft.Column([
                lbl_estado_progreso,
                lbl_tiempo,
                barra_progreso,
                lbl_enfriamiento,
                ft.Text("Por favor NO cierres esta ventana ni la aplicación.", size=11, color="red")
            ], tight=True, spacing=10)
        )

        if self.page:
            self.page.overlay.append(dlg_progreso)
            dlg_progreso.open = True
            self.page.update()

        exitos = 0
        fallos = 0
        import time

        # 4. Bucle de Procesamiento
        for idx, data in enumerate(pendientes):
            try:
                if self.page:
                    lbl_estado_progreso.value = f"Extrayendo página {idx + 1} de {total_items}..."
                    lbl_tiempo.value = f"Analizando estructura de {data.get('archivo', '')}..."
                    barra_progreso.value = idx / total_items
                    self.page.update()

                # Resolución dinámica según el módulo
                if hasattr(self.ai_parser, "parse_ventas_pdf_page") and "ventas" in str(self.__class__).lower():
                    extracted = self.ai_parser.parse_ventas_pdf_page(data["archivo"], 0, data.get("tipo", "Remisión"))
                else:
                    extracted = self.ai_parser.parse_compras_pdf_page(data["archivo"], 0)

                if extracted and isinstance(extracted, list) and len(extracted) > 0:
                    data["estado"] = "Procesado con éxito"
                    data["datos_extraidos"] = extracted
                    exitos += 1
                else:
                    data["estado"] = "Falló"
                    data["datos_extraidos"] = []
                    fallos += 1

                self._save_cargas()

                if self.page:
                    self._render_tabla_cargas()

                # 5. Enfriamiento de seguridad API (No se aplica al último registro)
                if idx < total_items - 1:
                    for i in range(20, 0, -1):
                        if self.page and dlg_progreso.open:
                            lbl_enfriamiento.value = f"Pausa anti-saturación de API: {i}s..."
                            self.page.update()
                        time.sleep(1)
                    if self.page:
                        lbl_enfriamiento.value = ""

            except Exception as ex:
                data["estado"] = "Falló"
                self._save_cargas()
                fallos += 1

        # 6. Finalización
        self.is_extraccion_activa = False
        if self.page:
            dlg_progreso.open = False
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Proceso masivo completado. Éxitos: {exitos}, Fallos: {fallos}"), 
                bgcolor="green" if fallos == 0 else "orange"
            )
            self.page.snack_bar.open = True
            barra_progreso.value = 1
            self.page.update()
            self._render_tabla_cargas()

    def copiar_historial_ventas(self, e):
        """
        Obtiene las ventas del día agrupadas por categoría y construye
        un texto formateado para el portapapeles del sistema.
        """
        if not self.page: return

        def worker():
            # Consultar desglose por categoría para la fecha activa
            items_cat = self.db.get_historial_ventas_dia(self.fecha_historial_activa, "CATEGORIA")

            tot_pesos = self.lbl_tot_ventas_panel.value
            tot_unds = self.lbl_cant_ventas_panel.value

            lineas_cat = []
            for item in items_cat:
                cat = item.get("categoria", "SIN CATEGORÍA")
                total = item.get("total", 0)
                unds = item.get("unidades", 0)
                items_cant = item.get("items_count", 0)
                lineas_cat.append(f"  • {cat}: ${total:,.0f} COP ({unds:g} unds | {items_cant} ítems)")

            cat_text = "\n".join(lineas_cat) if lineas_cat else "  (Sin ventas registradas por categoría)"

            texto_copia = (
                f"📊 HISTÓRICO DE VENTAS / SALIDAS\n"
                f"📅 Fecha: {self.fecha_historial_activa}\n"
                f"💵 Total Ventas del Día: {tot_pesos} ({tot_unds})\n"
                f"-----------------------------------------\n"
                f"🏷️ DESGLOSE POR CATEGORÍA:\n"
                f"{cat_text}\n"
                f"-----------------------------------------"
            )

            self.page.set_clipboard(texto_copia)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="white", size=18),
                    ft.Text("Histórico de ventas copiado al portapapeles exitosamente", color="white")
                ]),
                bgcolor="blue800"
            )
            self.page.snack_bar.open = True

            if hasattr(self, "safe_update"):
                self.safe_update()
            else:
                self.page.update()

        import threading
        threading.Thread(target=worker, daemon=True).start()

    # --- INICIO CRUD MANUAL VENTAS ---
    def _construir_modal_crud(self):
        self.crud_codigo_insumo = CustomAutoComplete(
            hint_text="Buscar insumo (Código o Nombre)",
            on_select=self._on_insumo_crud_select
        )
        self.crud_codigo_insumo.width = 350
        self.crud_fecha = ft.TextField(label="Fecha (YYYY-MM-DD)", width=150)
        self.crud_factura = ft.TextField(label="N° Factura / Remisión", width=180)
        self.crud_tipo_doc = ft.Dropdown(label="Tipo Doc.", options=[ft.dropdown.Option("Remisión"), ft.dropdown.Option("Factura POS")], width=150)
        
        self.crud_cantidad = ft.TextField(label="Cantidad", width=120, on_change=self._calc_tot_crud)
        self.crud_precio_unit = ft.TextField(label="Precio Unit.", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_descuento = ft.TextField(label="Descuento", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        self.crud_iva = ft.TextField(label="IVA", width=120, prefix_text="$", on_change=self._calc_tot_crud)
        
        self.crud_total_lbl = ft.Text("$ 0.00", size=20, weight="bold", color="green700")
        self.crud_item_id = None
        
        self.dlg_crud = ft.AlertDialog(
            modal=True,
            title=ft.Text("Registrar Venta"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    self.crud_codigo_insumo,
                    ft.Row([self.crud_fecha, self.crud_factura, self.crud_tipo_doc]),
                    ft.Row([self.crud_cantidad, self.crud_precio_unit]),
                    ft.Row([self.crud_descuento, self.crud_iva]),
                    ft.Divider(height=10),
                    ft.Row([ft.Text("Total Venta:", size=16, weight="bold"), self.crud_total_lbl])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_crud()),
                ft.ElevatedButton("Guardar", bgcolor="green700", color="white", on_click=self.guardar_venta_formulario)
            ]
        )

    def _on_insumo_crud_select(self, e):
        pass

    def _calc_tot_crud(self, e=None):
        try:
            cant = float(self.crud_cantidad.value or 0)
            precio = float(self.crud_precio_unit.value or 0)
            desc = float(self.crud_descuento.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * precio) + iva - desc
            self.crud_total_lbl.value = f"$ {tot:,.2f}"
            self.safe_update()
        except ValueError:
            self.crud_total_lbl.value = "$ 0.00"
            self.safe_update()

    def _cerrar_crud(self):
        self.dlg_crud.open = False
        self.safe_update()

    def abrir_modal_crear_venta(self, e=None):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.suggestions = [{"key": i['codigo_insumo'], "value": f"[{i['codigo_insumo']}] {i['nombre']}"} for i in insumos]
        
        self.crud_item_id = None
        self.dlg_crud.title.value = "Registrar Nueva Venta"
        self.crud_codigo_insumo.value = ""
        self.crud_fecha.value = datetime.date.today().strftime("%Y-%m-%d")
        self.crud_factura.value = ""
        self.crud_tipo_doc.value = "Remisión"
        self.crud_cantidad.value = ""
        self.crud_precio_unit.value = ""
        self.crud_descuento.value = "0"
        self.crud_iva.value = "0"
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def abrir_modal_editar_venta(self, item):
        if not hasattr(self, 'dlg_crud'):
            self._construir_modal_crud()
            
        insumos, _ = self.db.get_insumos(page=1, page_size=99999)
        self.crud_codigo_insumo.suggestions = [{"key": i['codigo_insumo'], "value": f"[{i['codigo_insumo']}] {i['nombre']}"} for i in insumos]
        
        self.crud_item_id = item.get("id_venta")
        self.dlg_crud.title.value = "Editar Venta"
        
        cod = item.get("codigo_insumo", "")
        nom_bd = item.get("catalogo_insumos", {}).get("nombre", "")
        nom_desc = item.get("descripcion", "")
        nom_final = nom_bd if nom_bd else nom_desc
        
        self.crud_codigo_insumo.value = f"[{cod}] {nom_final}" if cod else ""
        self.crud_fecha.value = str(item.get("fecha") or "")[:10]
        self.crud_factura.value = str(item.get("factura_no") or "")
        self.crud_tipo_doc.value = str(item.get("tipo_documento") or "Remisión")
        
        cant = float(item.get("cantidad") or 0)
        self.crud_cantidad.value = str(int(cant)) if cant.is_integer() else str(cant)
        
        self.crud_precio_unit.value = str(item.get("subtotal") or 0)
        self.crud_descuento.value = str(item.get("descuento") or 0)
        self.crud_iva.value = str(item.get("iva") or 0)
        self._calc_tot_crud()
        
        self.page.overlay.append(self.dlg_crud)
        self.dlg_crud.open = True
        self.safe_update()

    def guardar_venta_formulario(self, e):
        cod_raw = self.crud_codigo_insumo.value
        if not cod_raw or "[" not in cod_raw or "]" not in cod_raw:
            self.page.snack_bar = ft.SnackBar(ft.Text("Selecciona un insumo válido del listado."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        codigo_insumo = cod_raw.split("[")[1].split("]")[0]
        
        try:
            cant = float(self.crud_cantidad.value or 0)
            precio = float(self.crud_precio_unit.value or 0)
            desc = float(self.crud_descuento.value or 0)
            iva = float(self.crud_iva.value or 0)
            tot = (cant * precio) + iva - desc
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Revisa los valores numéricos ingresados."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return
            
        datos = {
            "fecha": self.crud_fecha.value,
            "factura_no": self.crud_factura.value,
            "tipo_documento": self.crud_tipo_doc.value,
            "codigo_insumo": codigo_insumo,
            "cantidad": cant,
            "subtotal": precio,
            "descuento": desc,
            "iva": iva,
            "total": tot
        }
        
        if self.crud_item_id:
            # Edit
            ok = self.db.update_venta_individual(self.crud_item_id, datos)
            msg = "Venta actualizada exitosamente."
        else:
            # Create
            datos["estado_registro"] = "VÁLIDO"
            ok = self.db.insert_venta_individual(datos)
            msg = "Venta registrada exitosamente."
            
        if ok:
            self._cerrar_crud()
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green")
            self.page.snack_bar.open = True
            self.load_data()
            self.load_summary()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar la venta en la BD."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()

    def confirmar_eliminar_venta(self, item):
        id_venta = item.get("id_venta")
        cant = float(item.get("cantidad") or 0)
        
        cat_info = item.get("catalogo_insumos", {})
        nom_bd = cat_info.get("nombre") if isinstance(cat_info, dict) else None
        insumo = nom_bd or item.get("descripcion", "Desconocido")
        
        fact = item.get("factura_no") or "S/D"
        tot = float(item.get("total") or 0)
        
        def do_eliminar(e):
            dlg.open = False
            self.safe_update()
            if self.db.eliminar_venta_individual(id_venta):
                self.page.snack_bar = ft.SnackBar(ft.Text("Venta eliminada y stock reincorporado."), bgcolor="green")
                self.page.snack_bar.open = True
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al eliminar la venta en la BD."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="red700"),
                ft.Text("Eliminar Registro de Venta", color="red700")
            ]),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(f"Insumo: {insumo}", weight="bold"),
                    ft.Text(f"N° Factura: {fact}"),
                    ft.Text(f"Cantidad: {cant:g} unds"),
                    ft.Text(f"Total Venta: ${tot:,.2f}", color="green700", weight="bold"),
                    ft.Divider(),
                    ft.Text(
                        f"⚠️ ADVERTENCIA: Al eliminar este registro de venta, se devolverán {cant:g} unidades al inventario disponible (reincorporación de stock) y se restará del histórico de ingresos.",
                        color="red900", weight="bold"
                    )
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dlg, 'open', False), self.safe_update())),
                ft.ElevatedButton("Eliminar Definitivamente", bgcolor="red700", color="white", on_click=do_eliminar)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()
    # --- FIN CRUD MANUAL VENTAS ---
````

## File: cargas_locales.json
````json
{
    "2026-08-18_None": {},
    "2026-08-18_Remisi\u00f3n": {
        "1": {
            "id": 3,
            "pagina": 1,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-18",
            "archivo": "pdfs_locales/ventas_2026-08-18_Remisi\u00f3n_Pag_1.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37921",
                    "productos": [
                        {
                            "cantidad": 37,
                            "codigo_item": "0847",
                            "costo_total": 111000,
                            "iva": 17723,
                            "subtotal": 93277
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0658",
                            "costo_total": 37950,
                            "iva": 6059,
                            "subtotal": 31891
                        },
                        {
                            "cantidad": 50,
                            "codigo_item": "0331",
                            "costo_total": 20000,
                            "iva": 3193,
                            "subtotal": 16807
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0653",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0399",
                            "costo_total": 30500,
                            "iva": 4870,
                            "subtotal": 25630
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0424",
                            "costo_total": 9500,
                            "iva": 1517,
                            "subtotal": 7983
                        }
                    ]
                },
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37922",
                    "productos": [
                        {
                            "cantidad": 3,
                            "codigo_item": "1839",
                            "costo_total": 9300,
                            "iva": 1485,
                            "subtotal": 7815
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0681",
                            "costo_total": 8600,
                            "iva": 1373,
                            "subtotal": 7227
                        },
                        {
                            "cantidad": 50,
                            "codigo_item": "4860",
                            "costo_total": 25000,
                            "iva": 3992,
                            "subtotal": 21008
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0644",
                            "costo_total": 11400,
                            "iva": 1820,
                            "subtotal": 9580
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "4156",
                            "costo_total": 8950,
                            "iva": 1429,
                            "subtotal": 7521
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "2206",
                            "costo_total": 5300,
                            "iva": 846,
                            "subtotal": 4454
                        },
                        {
                            "cantidad": 40,
                            "codigo_item": "0571-1",
                            "costo_total": 22800,
                            "iva": 3640,
                            "subtotal": 19160
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0105",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "2016",
                            "costo_total": 7800,
                            "iva": 1245,
                            "subtotal": 6555
                        }
                    ]
                },
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37923",
                    "productos": [
                        {
                            "cantidad": 8,
                            "codigo_item": "0858",
                            "costo_total": 33200,
                            "iva": 5301,
                            "subtotal": 27899
                        },
                        {
                            "cantidad": 8,
                            "codigo_item": "0690",
                            "costo_total": 50000,
                            "iva": 7983,
                            "subtotal": 42017
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0304",
                            "costo_total": 20400,
                            "iva": 3257,
                            "subtotal": 17143
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0313",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0713",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0171",
                            "costo_total": 5850,
                            "iva": 934,
                            "subtotal": 4916
                        },
                        {
                            "cantidad": 12,
                            "codigo_item": "0250",
                            "costo_total": 114000,
                            "iva": 18202,
                            "subtotal": 95798
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0578",
                            "costo_total": 95000,
                            "iva": 15168,
                            "subtotal": 79832
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0649",
                            "costo_total": 30900,
                            "iva": 4934,
                            "subtotal": 25966
                        }
                    ]
                },
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37924",
                    "productos": [
                        {
                            "cantidad": 200,
                            "codigo_item": "0570",
                            "costo_total": 82800,
                            "iva": 13220,
                            "subtotal": 69580
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0572",
                            "costo_total": 50000,
                            "iva": 7983,
                            "subtotal": 42017
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0658",
                            "costo_total": 59500,
                            "iva": 9500,
                            "subtotal": 50000
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0563",
                            "costo_total": 32200,
                            "iva": 5141,
                            "subtotal": 27059
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "0560",
                            "costo_total": 30000,
                            "iva": 4790,
                            "subtotal": 25210
                        },
                        {
                            "cantidad": 7,
                            "codigo_item": "0558",
                            "costo_total": 32200,
                            "iva": 5141,
                            "subtotal": 27059
                        },
                        {
                            "cantidad": 12,
                            "codigo_item": "0554",
                            "costo_total": 26400,
                            "iva": 4215,
                            "subtotal": 22185
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0537",
                            "costo_total": 19998,
                            "iva": 3193,
                            "subtotal": 16805
                        }
                    ]
                }
            ]
        },
        "2": {
            "id": 4,
            "pagina": 2,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-18",
            "archivo": "pdfs_locales/ventas_2026-08-18_Remisi\u00f3n_Pag_2.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37924",
                    "productos": [
                        {
                            "cantidad": 7,
                            "codigo_item": "0385",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "2000",
                            "costo_total": 16500,
                            "iva": 2634,
                            "subtotal": 13866
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0449",
                            "costo_total": 741,
                            "iva": 118,
                            "subtotal": 623
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1039",
                            "costo_total": 950,
                            "iva": 152,
                            "subtotal": 798
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0262",
                            "costo_total": 2300,
                            "iva": 367,
                            "subtotal": 1933
                        }
                    ]
                },
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37925",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0609",
                            "costo_total": 30500,
                            "iva": 4870,
                            "subtotal": 25630
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0074",
                            "costo_total": 17250,
                            "iva": 2754,
                            "subtotal": 14496
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1665",
                            "costo_total": 4200,
                            "iva": 671,
                            "subtotal": 3529
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1079",
                            "costo_total": 11200,
                            "iva": 1788,
                            "subtotal": 9412
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1387",
                            "costo_total": 12200,
                            "iva": 1948,
                            "subtotal": 10252
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0304",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0313",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0713",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0174",
                            "costo_total": 3800,
                            "iva": 607,
                            "subtotal": 3193
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0849",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1004",
                            "costo_total": 5450,
                            "iva": 870,
                            "subtotal": 4580
                        }
                    ]
                },
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37926",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "1991",
                            "costo_total": 138000,
                            "iva": 22034,
                            "subtotal": 115966
                        }
                    ]
                },
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37927",
                    "productos": [
                        {
                            "cantidad": 5,
                            "codigo_item": "0882",
                            "costo_total": 59500,
                            "iva": 9500,
                            "subtotal": 50000
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1818",
                            "costo_total": 23000,
                            "iva": 3672,
                            "subtotal": 19328
                        },
                        {
                            "cantidad": 7,
                            "codigo_item": "0842",
                            "costo_total": 14000,
                            "iva": 2235,
                            "subtotal": 11765
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1976",
                            "costo_total": 22500,
                            "iva": 3592,
                            "subtotal": 18908
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0500",
                            "costo_total": 17400,
                            "iva": 2778,
                            "subtotal": 14622
                        }
                    ]
                },
                {
                    "fecha": "03/08/2026",
                    "numero_factura": "37928",
                    "productos": [
                        {
                            "cantidad": 200,
                            "codigo_item": "0578",
                            "costo_total": 92000,
                            "iva": 14689,
                            "subtotal": 77311
                        },
                        {
                            "cantidad": 100,
                            "codigo_item": "0572",
                            "costo_total": 25466,
                            "iva": 4066,
                            "subtotal": 21400
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0654",
                            "costo_total": 56000,
                            "iva": 8941,
                            "subtotal": 47059
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0657",
                            "costo_total": 50600,
                            "iva": 8079,
                            "subtotal": 42521
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "0855",
                            "costo_total": 14100,
                            "iva": 2251,
                            "subtotal": 11849
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0848",
                            "costo_total": 18500,
                            "iva": 2954,
                            "subtotal": 15546
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0688",
                            "costo_total": 12000,
                            "iva": 1916,
                            "subtotal": 10084
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0044",
                            "costo_total": 8000,
                            "iva": 381,
                            "subtotal": 7619
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "1241",
                            "costo_total": 8800,
                            "iva": 1405,
                            "subtotal": 7395
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1428",
                            "costo_total": 8400,
                            "iva": 1341,
                            "subtotal": 7059
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "5467",
                            "costo_total": 3800,
                            "iva": 607,
                            "subtotal": 3193
                        }
                    ]
                }
            ]
        },
        "3": {
            "id": 5,
            "pagina": 3,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-18",
            "archivo": "pdfs_locales/ventas_2026-08-18_Remisi\u00f3n_Pag_3.pdf",
            "estado": "Nuevo"
        }
    }
}
````

## File: core/supabase_client.py
````python
import requests
import datetime
import urllib.parse
from config import Config

_client_instance = None

def get_client():
    """Retorna la instancia singleton del cliente Supabase."""
    global _client_instance
    if _client_instance is None:
        _client_instance = SupabaseClient()
    return _client_instance

class SupabaseClient:
    def __init__(self):
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY
        
        if self.url and self.url.endswith('/'):
            self.url = self.url[:-1]
        if self.url and not self.url.endswith('/rest/v1'):
            self.url = self.url + "/rest/v1"
            
        # 1. Instanciar la sesión compartida para mantener viva la conexión TCP
        self.session = requests.Session()
        
        # 2. Configurar los encabezados globales directamente en la sesión
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }
        self.session.headers.update(self.headers)
        
    def check_connection(self):
        if not self.url or not self.key:
            return False, "Faltan credenciales"
        try:
            # Prueba simple a la tabla (limit 1)
            response = self.session.get(f"{self.url}/catalogo_insumos?limit=1", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return True, "Conexión exitosa"
            return False, f"Error: {response.text}"
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en check_connection: el servidor no responde")
        except Exception as e:
            return False, str(e)
            
    # --- CRUD Catálogo Insumos ---
    
    def get_categorias(self):
        """Obtiene una lista de categorías únicas usando RPC si existe, o extrayendo de todo (simplificado)"""
        # Para simplificar y dado que PostgREST soporta distinct
        url = f"{self.url}/catalogo_insumos?select=categoria"
        headers = self.headers.copy()
        # En PostgREST podemos usar un header o query para distintos, pero es más fácil
        # traerlos y filtrarlos en memoria (limitado a unos cientos si hay muchos, pero está bien).
        response = self.session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            categorias = set([item.get('categoria', 'SIN CATEGORIA') for item in data if item.get('categoria')])
            return sorted(list(categorias))
        return []

    def get_insumos(self, page=1, page_size=20, search="", categoria="", fecha_corte=None, sort_col="Insumo", sort_asc=True, codigos_filtro=None):
        """
        Obtiene los insumos con paginación, filtros y ordenamiento desde el servidor.
        Retorna (lista_datos, total_count)
        """
        if fecha_corte:
            url = f"{self.url}/rpc/obtener_inventario_por_fecha?select=*"
        else:
            url = f"{self.url}/vista_inventario_completo?select=*"
        
        filtros = []
        if codigos_filtro is not None:
            if not codigos_filtro:
                filtros.append("codigo_insumo=in.(INVALID_FORCE_EMPTY)")
            else:
                codigos_str = ",".join(codigos_filtro)
                filtros.append(f"codigo_insumo=in.({codigos_str})")
                
        if categoria and categoria != "Todas":
            filtros.append(f"categoria=eq.{categoria}")
            
        if search:
            filtros.append(f"or=(nombre.ilike.*{search}*,codigo_insumo.ilike.*{search}*)")
            
        if filtros:
            url += "&" + "&".join(filtros)
            
        # Mapeo de columnas de la interfaz a las columnas de la vista SQL
        db_col_stock = "stock_real" if fecha_corte else "stock_actual"
        map_columnas = {
            "Código": "codigo_insumo",
            "Insumo": "nombre",
            "Categoría": "categoria",
            "Ubicación": "ubicacion",
            "Stock Inicial": "stock_inicial",
            "Stock Mínimo": "stock_minimo",
            "Entradas": "entradas",
            "Salidas": "salidas",
            "Stock Real": db_col_stock
        }
        
        db_col = map_columnas.get(sort_col, "nombre")
        direccion = "asc" if sort_asc else "desc"
        
        offset = (page - 1) * page_size
        url += f"&order={db_col}.{direccion}&offset={offset}&limit={page_size}"
        
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            if fecha_corte:
                payload = {"p_fecha_corte": f"{fecha_corte} 23:59:59"}
                response = self.session.post(url, headers=headers, json=payload, timeout=10)
            else:
                response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code in (200, 201, 206):
                data = response.json()
                content_range = response.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                print(f"Error en consulta: {response.text}")
                return [], 0
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_insumos: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_insumos: {e}")
            return [], 0
        
    def insert_insumo(self, data: dict):
        url = f"{self.url}/catalogo_insumos"
        response = self.session.post(url, json=data, headers=self.headers, timeout=10)
        if response.status_code in (200, 201):
            return response.json()
        return None

    def update_insumo(self, codigo_insumo: str, datos_actualizados: dict) -> bool:
        """
        Actualiza un insumo existente en el catálogo.
        """
        url = f"{self.url}/catalogo_insumos?codigo_insumo=eq.{codigo_insumo}"
        try:
            response = self.session.patch(url, json=datos_actualizados, headers=self.headers, timeout=10)
            if response.status_code in (200, 204):
                return True
            else:
                print(f"Error al actualizar insumo: {response.text}")
                return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en update_insumo: el servidor no responde")
        except Exception as e:
            print(f"Excepción en update_insumo: {e}")
            return False

    def get_compras(self, page=1, page_size=15, search="", fecha_corte=None, factura_filtro=None, proveedor_filtro=None):
        try:
            offset = (page - 1) * page_size
            # Incluir 'iva' explícitamente en el select
            select_query = "id_compra,fecha,numero_entrada,numero_factura,proveedor,codigo_insumo,cantidad,costo_unitario,iva,valor_iva,costo_total,estado_registro,catalogo_insumos(nombre)"
            
            url = f"{self.url}/registro_compras?select={select_query}&estado_registro=eq.VÁLIDO&order=fecha.desc"
            
            if factura_filtro:
                url += f"&or=(numero_entrada.eq.{factura_filtro},numero_factura.eq.{factura_filtro})"
            if proveedor_filtro:
                url += f"&proveedor=eq.{proveedor_filtro}"
                
            res = self.session.get(url, headers=self.headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                
                # Filtrado por fecha_corte y búsqueda
                filtered = []
                for item in data:
                    f = str(item.get("fecha") or "")[:10]
                    if fecha_corte and f > fecha_corte:
                        continue
                        
                    nom = str(item.get("catalogo_insumos", {}).get("nombre", "") if item.get("catalogo_insumos") else "").lower()
                    cod = str(item.get("codigo_insumo") or "").lower()
                    prov = str(item.get("proveedor") or "").lower()
                    fact = str(item.get("numero_factura") or "").lower()
                    
                    if search:
                        s = search.lower()
                        if s not in nom and s not in cod and s not in prov and s not in fact:
                            continue
                            
                    filtered.append(item)
                    
                total_records = len(filtered)
                page_data = filtered[offset:offset + page_size]
                return page_data, total_records
                
            return [], 0
        except Exception as ex:
            print(f"Error en get_compras: {ex}")
            return [], 0

    def get_historial_compras_dia(self, fecha_dia: str, agrupar_por: str = "FACTURA") -> list:
        """
        Recupera todas las compras de un día (YYYY-MM-DD),
        agrupados por 'FACTURA' o por 'PROVEEDOR'.
        """
        items_resultado = []
        try:
            # Consulta exclusiva a compras del día
            url_c = f"{self.url}/registro_compras?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=numero_entrada,numero_factura,proveedor,costo_total,fecha,cantidad&order=fecha.desc"
            res_c = self.session.get(url_c, headers=self.headers, timeout=10)
    
            if res_c.status_code == 200:
                data_c = res_c.json()
    
                if agrupar_por == "FACTURA":
                    agrupado = {}
                    for r in data_c:
                        ref = r.get("numero_entrada") or r.get("numero_factura") or "S/N"
                        if ref not in agrupado:
                            agrupado[ref] = {
                                "tipo": "COMPRA",
                                "ref": ref,
                                "factura": r.get("numero_factura") or ref,
                                "proveedor": r.get("proveedor") or "Clientes Varios",
                                "total": 0.0,
                                "unidades": 0.0,
                                "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                            }
                        agrupado[ref]["total"] += float(r.get("costo_total") or 0)
                        agrupado[ref]["unidades"] += float(r.get("cantidad") or 0)
                    items_resultado.extend(list(agrupado.values()))
    
                elif agrupar_por == "PROVEEDOR":
                    agrupado = {}
                    for r in data_c:
                        prov = r.get("proveedor") or "Clientes Varios"
                        if prov not in agrupado:
                            agrupado[prov] = {
                                "tipo": "PROVEEDOR_RESUMEN",
                                "ref": prov,
                                "proveedor": prov,
                                "facturas_count": set(),
                                "total": 0.0,
                                "unidades": 0.0,
                                "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                            }
                        agrupado[prov]["facturas_count"].add(r.get("numero_factura") or r.get("numero_entrada"))
                        agrupado[prov]["total"] += float(r.get("costo_total") or 0)
                        agrupado[prov]["unidades"] += float(r.get("cantidad") or 0)
    
                    for p in agrupado.values():
                        p["facturas_cant"] = len(p["facturas_count"])
                        del p["facturas_count"]
                        items_resultado.append(p)
    
        except Exception as ex:
            print(f"Error en historial de compras del día: {ex}")
    
        # Ordenar por hora/valor descendente
        items_resultado.sort(key=lambda x: x["total"], reverse=True)
        return items_resultado


    def insert_compras(self, compras_list):
        if not compras_list: return True
        try:
            url = f"{self.url}/registro_compras"
            payload = []
            for item in compras_list:
                payload.append({
                    "numero_entrada": item.get("numero_entrada"),
                    "fecha": item.get("fecha"),
                    "numero_factura": item.get("numero_factura"),
                    "proveedor": item.get("proveedor"),
                    "codigo_insumo": item.get("codigo_insumo"),
                    "cantidad": float(item.get("cantidad") or 0),
                    "costo_unitario": float(item.get("costo_unitario") or 0),
                    "iva": float(item.get("iva") or item.get("valor_iva") or 0),
                    "valor_iva": float(item.get("iva") or item.get("valor_iva") or 0),
                    "costo_total": float(item.get("costo_total") or 0),
                    "estado_registro": "VÁLIDO"
                })
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            return res.status_code in (200, 201)
        except Exception as ex:
            print(f"Error en insert_compras: {ex}")
            return False

    def get_entradas_existentes(self, lista_eas: list) -> set:
        """
        Consulta cuáles de los 'numero_entrada' proveídos ya existen en registro_compras.
        """
        if not lista_eas:
            return set()
            
        url = f"{self.url}/registro_compras?select=numero_entrada"
        # Crear un filtro in.(EA-1,EA-2)
        eas_str = ",".join(lista_eas)
        url += f"&numero_entrada=in.({eas_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["numero_entrada"] for item in data if item.get("numero_entrada")}
            return set()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_entradas_existentes: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_entradas_existentes: {e}")
            return set()

    def eliminar_compras_por_entradas(self, lista_entradas):
        """Elimina registros de compras en Supabase por número de entrada o factura."""
        if not lista_entradas: return True
        try:
            for ref in lista_entradas:
                url = f"{self.url}/registro_compras?or=(numero_entrada.eq.{ref},numero_factura.eq.{ref})"
                self.session.delete(url, headers=self.headers, timeout=10)
            return True
        except Exception as ex:
            print(f"Error eliminando compras: {ex}")
            return False
            
    def get_nombres_insumos(self, lista_codigos: list) -> dict:
        """
        Devuelve un diccionario {codigo: nombre} buscando en catalogo_insumos.
        """
        if not lista_codigos:
            return {}
            
        url = f"{self.url}/catalogo_insumos?select=codigo_insumo,nombre"
        
        # Como los códigos pueden ser strings (ej "0471"), envolvemos en comillas simples para la API de supabase,
        # o usamos in. sin problemas si PostgREST lo maneja.
        # PostgREST maneja in.(a,b,c). Para strings con espacios podría requerir doble comilla, 
        # pero para códigos numéricos en string basta unirlos con coma.
        codigos_str = ",".join(lista_codigos)
        url += f"&codigo_insumo=in.({codigos_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["codigo_insumo"]: item["nombre"] for item in data if item.get("codigo_insumo")}
            return {}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_nombres_insumos: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_nombres_insumos: {e}")
            return {}


    def get_ventas(self, page=1, page_size=20, search="", fecha_corte=None, categoria_filtro=None, factura_filtro=None):
        # Si hay filtro de categoría, necesitamos !inner para que PostgREST aplique un INNER JOIN
        if categoria_filtro:
            url = f"{self.url}/registro_ventas?select=*,catalogo_insumos!inner(nombre,categoria)"
        else:
            url = f"{self.url}/registro_ventas?select=*,catalogo_insumos(nombre,categoria)"
        
        filtros = []
        
        # 1. Buscador por texto general
        if search:
            s_enc = urllib.parse.quote(search.strip())
            filtros.append(f"or=(codigo_insumo.ilike.*{s_enc}*,factura_no.ilike.*{s_enc}*,descripcion.ilike.*{s_enc}*)")
            
        # 2. Fecha
        if fecha_corte:
            filtros.append(f"fecha=gte.{fecha_corte}T00:00:00&fecha=lte.{fecha_corte}T23:59:59")

        # 3. Filtro por Categoría (Requiere catalogo_insumos.categoria)
        if categoria_filtro:
            cat_enc = urllib.parse.quote(str(categoria_filtro).strip())
            filtros.append(f"catalogo_insumos.categoria=eq.{cat_enc}")

        # 4. Filtro por Nro. Factura / Documento (Uso de ilike para coincidencia flexible)
        if factura_filtro:
            fact_enc = urllib.parse.quote(str(factura_filtro).strip())
            filtros.append(f"factura_no.ilike.*{fact_enc}*")
            
        if filtros:
            url += "&" + "&".join(filtros)
            
        offset = (page - 1) * page_size
        url += f"&order=fecha.desc,factura_no.desc&offset={offset}&limit={page_size}"
        
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code in (200, 206):
                data = response.json()
                content_range = response.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                print(f"Error HTTP {response.status_code} en get_ventas: {response.text}")
                return [], 0
        except Exception as e:
            print(f"Excepción en get_ventas: {e}")
            return [], 0

    def get_historial_ventas_dia(self, fecha_dia: str, agrupar_por: str = "CATEGORIA") -> list:
        """
        Recupera todas las ventas de un día (YYYY-MM-DD),
        agrupadas por 'CATEGORIA' o por 'FACTURA'.
        """
        items_resultado = []
        try:
            url_v = f"{self.url}/registro_ventas?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=factura_no,tipo_documento,descripcion,total,cantidad,codigo_insumo,fecha,catalogo_insumos(categoria,nombre)&order=fecha.desc"
            res_v = self.session.get(url_v, headers=self.headers, timeout=10)
            
            if res_v.status_code == 200:
                data_v = res_v.json()
                
                if agrupar_por == "CATEGORIA":
                    agrupado = {}
                    for r in data_v:
                        cat = r.get("catalogo_insumos", {}).get("categoria") if r.get("catalogo_insumos") else None
                        if not cat: cat = "SIN CATEGORÍA"
                        
                        if cat not in agrupado:
                            agrupado[cat] = {
                                "tipo": "CATEGORIA_RESUMEN",
                                "ref": cat,
                                "categoria": cat,
                                "total": 0.0,
                                "unidades": 0.0,
                                "items_count": 0
                            }
                        agrupado[cat]["total"] += float(r.get("total") or 0)
                        agrupado[cat]["unidades"] += float(r.get("cantidad") or 0)
                        agrupado[cat]["items_count"] += 1
                    items_resultado.extend(list(agrupado.values()))
    
                elif agrupar_por == "FACTURA":
                    agrupado = {}
                    for r in data_v:
                        ref = r.get("factura_no") or "S/N"
                        tipo_doc = r.get("tipo_documento") or "Factura POS"
                        if ref not in agrupado:
                            agrupado[ref] = {
                                "tipo": "FACTURA_VENTA",
                                "ref": ref,
                                "factura": ref,
                                "subtipo": tipo_doc,
                                "total": 0.0,
                                "unidades": 0.0
                            }
                        agrupado[ref]["total"] += float(r.get("total") or 0)
                        agrupado[ref]["unidades"] += float(r.get("cantidad") or 0)
                    items_resultado.extend(list(agrupado.values()))
    
        except Exception as ex:
            print(f"Error en historial de ventas del día: {ex}")
    
        items_resultado.sort(key=lambda x: x["total"], reverse=True)
        return items_resultado


    def get_ventas_existentes(self, lista_facturas: list) -> set:
        """
        Consulta cuáles de las facturas (factura_no) proveídas ya existen en registro_ventas.
        """
        if not lista_facturas:
            return set()
            
        url = f"{self.url}/registro_ventas?select=factura_no"
        facturas_str = ",".join(lista_facturas)
        url += f"&factura_no=in.({facturas_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["factura_no"] for item in data if item.get("factura_no")}
            return set()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_ventas_existentes: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_ventas_existentes: {e}")
            return set()

    def eliminar_ventas_origen(self, fecha: str, tipo_documento: str, pagina_origen: int) -> bool:
        """Elimina las ventas de una fecha, tipo y página específica para permitir sobreescritura limpia."""
        url = f"{self.url}/registro_ventas?fecha=gte.{fecha}T00:00:00&fecha=lte.{fecha}T23:59:59&tipo_documento=eq.{tipo_documento}&pagina_origen=eq.{pagina_origen}"
        try:
            response = self.session.delete(url, headers=self.headers, timeout=10)
            return response.status_code in (200, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en eliminar_ventas_origen: el servidor no responde")
        except Exception as e:
            print(f"Error al eliminar ventas por origen: {e}")
            return False

    def eliminar_ventas_por_facturas(self, lista_facturas):
        """Elimina registros de ventas en Supabase por número de factura."""
        if not lista_facturas: return True
        try:
            for fact in lista_facturas:
                url = f"{self.url}/registro_ventas?factura_no=eq.{fact}"
                self.session.delete(url, headers=self.headers, timeout=10)
            return True
        except Exception as ex:
            print(f"Error eliminando ventas: {ex}")
            return False

    def insert_ventas(self, ventas_list: list):
        """Inserta una lista de registros de ventas de forma masiva (bulk insert)."""
        url = f"{self.url}/registro_ventas"
        
        payload = []
        for v in ventas_list:
            venta = {
                "fecha": v.get("fecha"),
                "factura_no": str(v.get("numero_factura", "")),
                "codigo_insumo": str(v.get("codigo_item", "")),
                "descripcion": str(v.get("descripcion", "")),
                "cantidad": float(v.get("cantidad", 0) or 0),
                "subtotal": float(v.get("precio_unitario", 0) or 0),
                "iva": float(v.get("iva", 0) or 0),
                "total": float(v.get("costo_total", 0) or 0),
                "tipo_documento": str(v.get("tipo_documento", "Factura POS")),
                "pagina_origen": int(v.get("pagina_origen", 1))
            }
            payload.append(venta)
            
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201, 204):
                return True
            else:
                print(f"Error al insertar ventas: {response.text}")
                return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en insert_ventas: el servidor no responde")
        except Exception as e:
            print(f"Excepción en insert_ventas: {e}")
            return False



    def get_datos_conteo_inicial(self, mes_seleccionado: str) -> list:
        # mes_seleccionado is in format 'YYYY-MM'
        try:
            year, month = map(int, mes_seleccionado.split("-"))
            if month == 1:
                mes_anterior = f"{year - 1}-12"
            else:
                mes_anterior = f"{year}-{month - 1:02d}"
        except:
            return []
            
        # 1. Traer catalogo
        catalogo = []
        try:
            res_cat = self.session.get(f"{self.url}/catalogo_insumos?select=codigo_insumo,nombre,categoria", headers=self.headers, timeout=10)
            if res_cat.status_code == 200:
                catalogo = res_cat.json()
        except:
            pass
            
        # 2. Traer registros FINAL mes anterior
        cierre_anterior = {}
        try:
            url_ant = f"{self.url}/registro_auditorias_cierres?tipo_registro=eq.CIERRE_MENSUAL&fecha_cierre=gte.{mes_anterior}-01&fecha_cierre=lte.{mes_anterior}-31&select=codigo_insumo,cantidad_fisica"
            res_ant = self.session.get(url_ant, headers=self.headers, timeout=10)
            if res_ant.status_code == 200:
                for r in res_ant.json():
                    cierre_anterior[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except:
            pass
            
        # 3. Traer registros INICIAL mes seleccionado
        inicio_actual = {}
        try:
            url_act = f"{self.url}/registro_auditorias_cierres?tipo_registro=eq.INVENTARIO_INICIAL&fecha_cierre=gte.{mes_seleccionado}-01&fecha_cierre=lte.{mes_seleccionado}-31&select=codigo_insumo,cantidad_fisica"
            res_act = self.session.get(url_act, headers=self.headers, timeout=10)
            if res_act.status_code == 200:
                for r in res_act.json():
                    inicio_actual[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except:
            pass
            
        resultado = []
        for c in catalogo:
            codigo = c.get("codigo_insumo")
            if not codigo: continue
            
            resultado.append({
                "codigo_insumo": codigo,
                "nombre": c.get("nombre"),
                "categoria": c.get("categoria"),
                "cierre_mes_anterior": cierre_anterior.get(codigo, 0),
                "stock_inicial_actual": inicio_actual.get(codigo, 0),
            })
            
        return resultado

    def upsert_conteos_iniciales(self, registros: list) -> bool:
        if not registros: return True
        
        # Buscar IDs existentes para hacer merge por Primary Key (ya que no hay unique constraint compuesto)
        try:
            fecha_cierre = registros[0].get("fecha_cierre")
            tipo_registro = registros[0].get("tipo_registro")
            codigos = [r["codigo_insumo"] for r in registros]
            
            # Dividir en chunks si son muchos códigos para no exceder longitud de URL, o hacer query simple
            if len(codigos) > 0:
                codigos_str = ",".join(codigos)
                url_exist = f"{self.url}/registro_auditorias_cierres?fecha_cierre=eq.{fecha_cierre}&tipo_registro=eq.{tipo_registro}&codigo_insumo=in.({codigos_str})&select=id_auditoria,codigo_insumo"
                res_exist = self.session.get(url_exist, headers=self.headers, timeout=10)
                if res_exist.status_code == 200:
                    existentes = {item["codigo_insumo"]: item["id_auditoria"] for item in res_exist.json() if "id_auditoria" in item}
                    for r in registros:
                        if r["codigo_insumo"] in existentes:
                            r["id_auditoria"] = existentes[r["codigo_insumo"]]
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en upsert_conteos_iniciales: el servidor no responde")
        except Exception as e:
            print(f"Error al buscar existentes para upsert: {e}")
        
        url = f"{self.url}/registro_auditorias_cierres"
        
        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        
        try:
            res = self.session.post(url, json=registros, headers=headers, timeout=10)
            if res.status_code in (200, 201, 204):
                return True
            print(f"Error upsert_conteos: {res.text}")
            return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en upsert_conteos_iniciales: el servidor no responde")
        except Exception as e:
            print(f"Excepcion upsert_conteos: {e}")
            return False


    def get_top_costo_inventario(self, limit=10, fecha_corte=None) -> list:
        """
        Obtiene los insumos con mayor costo total de inventario acumulado hasta 'fecha_corte'.
        """
        try:
            insumos, _ = self.get_insumos(
                page=1, 
                page_size=limit, 
                fecha_corte=fecha_corte, 
                sort_col="Stock Real", 
                sort_asc=False
            )
            top = []
            for item in insumos:
                costo_tot = float(item.get("costo_total_insumo") or 0)
                ventas_tot = float(item.get("valor_ventas") or 0)
                rotacion = (ventas_tot / costo_tot) if costo_tot > 0 else 0.0
                
                top.append({
                    "codigo": item.get("codigo_insumo") or "S/C",
                    "producto": item.get("nombre") or "Desconocido",
                    "valor_inventario": costo_tot,
                    "rotacion": f"{rotacion:.2f}x"
                })
            return top
        except Exception as e:
            print(f"Error en get_top_costo_inventario: {e}")
            return []
        

    def get_compras_summary(self, fecha_corte=None):
        """
        Obtiene el resumen financiero acumulado de compras (total e IVA)
        para el mes en curso y para el día actual.
        """
        try:
            import datetime
            hoy = datetime.date.today().strftime("%Y-%m-%d")
            mes_actual = hoy[:7]
            
            url = f"{self.url}/registro_compras?select=fecha,cantidad,costo_total,iva,valor_iva,estado_registro&estado_registro=eq.VÁLIDO"
            res = self.session.get(url, headers=self.headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                total_mes = 0.0
                total_hoy = 0.0
                cant_tot = 0.0
                iva_mes = 0.0
                iva_hoy = 0.0
                
                for c in data:
                    f = str(c.get("fecha") or "")[:10]
                    if fecha_corte and f > fecha_corte:
                        continue
                        
                    monto = float(c.get("costo_total") or 0)
                    cant = float(c.get("cantidad") or 0)
                    
                    # Extracción segura de IVA blindando valores None/NULL
                    iva_val = float(c.get("iva") or c.get("valor_iva") or 0)
                    
                    if f.startswith(mes_actual):
                        total_mes += monto
                        iva_mes += iva_val
                        
                    if f == hoy:
                        total_hoy += monto
                        iva_hoy += iva_val
                        
                    cant_tot += cant
                    
                return {
                    "total_mes": total_mes,
                    "total_hoy": total_hoy,
                    "cantidad_total": cant_tot,
                    "iva_mes": iva_mes,
                    "iva_hoy": iva_hoy
                }
            return {"total_mes": 0, "total_hoy": 0, "cantidad_total": 0, "iva_mes": 0, "iva_hoy": 0}
        except Exception as ex:
            print(f"Error en get_compras_summary: {ex}")
            return {"total_mes": 0, "total_hoy": 0, "cantidad_total": 0, "iva_mes": 0, "iva_hoy": 0}

    def get_ventas_summary(self, fecha_corte=None):
        try:
            import datetime
            hoy = datetime.date.today().strftime("%Y-%m-%d")
            mes_actual = hoy[:7]
            
            url = f"{self.url}/registro_ventas?select=fecha,total,subtotal,iva,estado_registro&estado_registro=eq.VÁLIDO"
            res = self.session.get(url, headers=self.headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                tot_hist = 0.0
                tot_mes = 0.0
                tot_hoy = 0.0
                iva_hist = 0.0
                iva_mes = 0.0
                iva_hoy = 0.0
                
                for v in data:
                    f = str(v.get("fecha") or "")[:10]
                    if fecha_corte and f > fecha_corte:
                        continue
                        
                    monto = float(v.get("total") or 0)
                    iva_val = float(v.get("iva") or 0)
                    
                    tot_hist += monto
                    iva_hist += iva_val
                    
                    if f.startswith(mes_actual):
                        tot_mes += monto
                        iva_mes += iva_val
                        
                    if f == hoy:
                        tot_hoy += monto
                        iva_hoy += iva_val
                        
                return {
                    "total_historico": tot_hist,
                    "total_mes": tot_mes,
                    "total_hoy": tot_hoy,
                    "iva_historico": iva_hist,
                    "iva_mes": iva_mes,
                    "iva_hoy": iva_hoy
                }
            return {"total_historico": 0, "total_mes": 0, "total_hoy": 0, "iva_historico": 0, "iva_mes": 0, "iva_hoy": 0}
        except Exception as ex:
            print(f"Error en get_ventas_summary: {ex}")
            return {"total_historico": 0, "total_mes": 0, "total_hoy": 0, "iva_historico": 0, "iva_mes": 0, "iva_hoy": 0}

    def get_catalogo_summary(self, fecha_corte=None) -> dict:
        """Invoca RPC para compras totales y ventas totales en pesos"""
        url = f"{self.url}/rpc/get_catalogo_summary_rpc"
        try:
            payload = {}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload if payload else None, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_catalogo_summary: el servidor no responde")
        except Exception as e:
            print(f"Error RPC catalogo_summary: {e}")
        return {"total_compras": 0.0, "total_ventas": 0.0}

    def get_top_ventas_mes(self, limit=10, fecha_corte=None) -> list:
        hoy = fecha_corte if fecha_corte else datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        url = f"{self.url}/rpc/get_top_ventas_mes_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual, "limite": limit, "fecha_corte": fecha_corte} if fecha_corte else {"mes_actual": mes_actual, "limite": limit}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_top_ventas_mes: el servidor no responde")
        except Exception as e:
            print(f"Error RPC top_ventas: {e}")
        return []

    def get_tendencia_diaria(self, fecha_corte=None) -> dict:
        """Invoca RPC para obtener ventas y compras agrupadas por día"""
        if fecha_corte:
            hoy = datetime.datetime.strptime(fecha_corte, "%Y-%m-%d").date()
        else:
            hoy = datetime.date.today()
        mes_actual = hoy.strftime("%Y-%m")
        
        # Pre-poblar el diccionario con ceros para todos los días transcurridos
        tendencia = {f"{mes_actual}-{i:02d}": {"ventas": 0.0, "compras": 0.0} for i in range(1, hoy.day + 1)}
        
        url = f"{self.url}/rpc/get_tendencia_diaria_rpc"
        try:
            payload = {"mes_actual": mes_actual}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if res.status_code == 200:
                for row in res.json():
                    dia = row.get("dia")
                    if dia in tendencia:
                        tendencia[dia]["ventas"] = float(row.get("ventas", 0))
                        tendencia[dia]["compras"] = float(row.get("compras", 0))
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_tendencia_diaria: el servidor no responde")
        except Exception as e:
            print(f"Error RPC tendencia_diaria: {e}")
        return tendencia

    def get_inventario_kpis(self, fecha_corte=None) -> dict:
        """
        Obtiene los KPIs generales de valorización de inventario.
        """
        try:
            insumos, _ = self.get_insumos(page=1, page_size=99999, fecha_corte=fecha_corte)
            val_inv = sum([float(i.get("costo_total_insumo") or 0) for i in insumos])
            alertas = sum([1 for i in insumos if float(i.get("stock_actual") or i.get("stock_real") or 0) <= float(i.get("stock_minimo") or 5)])
            
            return {
                "valor_inventario": val_inv,
                "alertas_criticas": alertas
            }
        except Exception as e:
            print(f"Excepción controlada en get_inventario_kpis: {e}")
            return {"valor_inventario": 0, "alertas_criticas": 0}

    def get_kpis_por_categoria(self, fecha_corte=None) -> list:
        """Invoca RPC para extraer rendimiento y rotación agrupada por categoría."""
        url = f"{self.url}/rpc/get_kpis_por_categoria_rpc"
        try:
            payload = {}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload if payload else None, headers=self.headers, timeout=5)
            if res.status_code == 200:
                return res.json()
        except:
            pass
            
        # Fallback local para agrupar KPIs por categoría desde la vista principal
        try:
            url_vista = f"{self.url}/vista_inventario_completo?select=categoria,costo_total_insumo,valor_ventas"
            res_vista = self.session.get(url_vista, headers=self.headers, timeout=10)
            if res_vista.status_code == 200:
                data = res_vista.json()
                categorias = {}
                for item in data:
                    cat = item.get("categoria") or "SIN CATEGORIA"
                    if cat not in categorias:
                        categorias[cat] = {
                            "categoria": cat,
                            "costo_inventario": 0.0,
                            "ventas_totales": 0.0,
                            "rotacion": 0.0,
                            "rentabilidad": 0.0
                        }
                    categorias[cat]["costo_inventario"] += float(item.get("costo_total_insumo") or 0)
                    categorias[cat]["ventas_totales"] += float(item.get("valor_ventas") or 0)
                
                result = []
                for cat, vals in categorias.items():
                    costo_inv = vals["costo_inventario"]
                    vtas = vals["ventas_totales"]
                    if costo_inv > 0:
                        vals["rotacion"] = vtas / costo_inv
                    if vtas > 0:
                        vals["rentabilidad"] = 25.0 # Margen simulado 25% si hay ventas
                    result.append(vals)
                    
                result.sort(key=lambda x: x["ventas_totales"], reverse=True)
                return result
        except Exception as e:
            print(f"Error en get_kpis_por_categoria fallback: {e}")
            
        return []

    def iniciar_snapshot_cierre(self, mes_periodo: str) -> dict:
        """Invoca el RPC para generar el snapshot preliminar del mes."""
        url = f"{self.url}/rpc/fn_snapshot_cierre_mensual"
        try:
            res = self.session.post(url, json={"p_mes": mes_periodo}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en iniciar_snapshot_cierre: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def obtener_estado_cierre(self, mes_periodo: str) -> dict:
        """Obtiene el resumen y los insumos del período especificado."""
        url = f"{self.url}/rpc/fn_obtener_estado_cierre"
        try:
            res = self.session.post(url, json={"p_mes": mes_periodo}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else {}
            return {}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en obtener_estado_cierre: el servidor no responde")
        except Exception as e:
            print(f"Error en obtener_estado_cierre: {e}")
            return {}

    def registrar_conteo_fisico(self, id_auditoria: str, cantidad: float, costo: float = None, observacion: str = None) -> dict:
        """Registra el conteo físico y genera ajustes si existe diferencia."""
        url = f"{self.url}/rpc/fn_registrar_conteo_fisico"
        payload = {
            "p_id_auditoria": id_auditoria,
            "p_cantidad_fisica": cantidad
        }
        if costo is not None:
            payload["p_costo_ajuste"] = costo
        if observacion:
            payload["p_observacion"] = observacion
            
        try:
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en registrar_conteo_fisico: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aceptar_stock_sistema(self, id_auditoria: str) -> dict:
        """Acepta el stock calculado por el sistema sin conteo físico."""
        url = f"{self.url}/rpc/fn_aceptar_stock_sistema"
        try:
            res = self.session.post(url, json={"p_id_auditoria": id_auditoria}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en aceptar_stock_sistema: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aprobar_cierre_mes(self, id_periodo: str, aprobado_por: str) -> dict:
        """Cierra el período y consolida el inventario inicial del mes siguiente."""
        url = f"{self.url}/rpc/fn_aprobar_cierre_mes"
        try:
            res = self.session.post(url, json={"p_id_periodo": id_periodo, "p_aprobado_por": aprobado_por}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en aprobar_cierre_mes: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def get_catalogo_costos(self) -> dict:
        """Obtiene un diccionario con los costos actuales del catálogo de insumos"""
        url = f"{self.url}/catalogo_insumos?select=codigo_insumo,costo_unitario"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return {item.get('codigo_insumo'): float(item.get('costo_unitario') or 0) for item in res.json()}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_catalogo_costos: el servidor no responde")
        except Exception as e:
            print(f"Error get_catalogo_costos: {e}")
        return {}

    def get_insumo_detalle(self, codigo: str) -> dict:
        """Recupera el nombre, costo, precio y stock de un insumo específico para el autocompletado."""
        url = f"{self.url}/catalogo_insumos?codigo_insumo=eq.{codigo}&select=nombre,costo_unitario,precio_venta,stock_actual"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200 and len(res.json()) > 0:
                return res.json()[0]
        except Exception:
            pass
        return {}

    def get_ajustes_inventario(self) -> list:
        """Obtiene el historial de ajustes cruzado con el catálogo para extraer el nombre."""
        url = f"{self.url}/registro_ajustes_inventario?select=*,catalogo_insumos(nombre,categoria)&order=fecha_ajuste.desc"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_ajustes_inventario: el servidor no responde")
        except Exception as e:
            pass

    def get_historial_facturas_dia(self, fecha_dia: str) -> list:
        """
        Recupera todas las facturas y documentos cargados en un día específico (YYYY-MM-DD),
        agrupados por número de factura/entrada con su hora de registro y valor total.
        """
        facturas = []
        try:
            # 1. Compras del día
            url_c = f"{self.url}/registro_compras?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=numero_entrada,numero_factura,proveedor,costo_total,fecha&order=fecha.desc"
            res_c = self.session.get(url_c, headers=self.headers, timeout=10)
            if res_c.status_code == 200:
                agrupado_c = {}
                for r in res_c.json():
                    ref = r.get("numero_entrada") or r.get("numero_factura")
                    if not ref: continue
                    if ref not in agrupado_c:
                        agrupado_c[ref] = {
                            "tipo": "COMPRA",
                            "ref": ref,
                            "factura": r.get("numero_factura", "N/A"),
                            "proveedor": r.get("proveedor") or "Clientes Varios",
                            "total": 0.0,
                            "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                        }
                    agrupado_c[ref]["total"] += float(r.get("costo_total") or 0)
                facturas.extend(list(agrupado_c.values()))

            # 2. Ventas del día (Diferenciando POS y Remisión)
            url_v = f"{self.url}/registro_ventas?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=factura_no,tipo_documento,total,fecha&order=fecha.desc"
            res_v = self.session.get(url_v, headers=self.headers, timeout=10)
            if res_v.status_code == 200:
                agrupado_v = {}
                for r in res_v.json():
                    ref = r.get("factura_no")
                    if not ref: continue
                    if ref not in agrupado_v:
                        tipo_doc = r.get("tipo_documento") or "Factura POS"
                        agrupado_v[ref] = {
                            "tipo": f"VENTA_{'POS' if 'POS' in tipo_doc.upper() else 'REVISION'}",
                            "ref": ref,
                            "factura": ref,
                            "subtipo": tipo_doc,
                            "total": 0.0,
                            "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                        }
                    agrupado_v[ref]["total"] += float(r.get("total") or 0)
                facturas.extend(list(agrupado_v.values()))

            # 3. Ajustes del día
            url_a = f"{self.url}/registro_ajustes_inventario?fecha_ajuste=gte.{fecha_dia}T00:00:00&fecha_ajuste=lte.{fecha_dia}T23:59:59&select=id_ajuste,tipo_ajuste,motivo_observacion,costo_total_ajuste,fecha_ajuste&order=fecha_ajuste.desc"
            res_a = self.session.get(url_a, headers=self.headers, timeout=10)
            if res_a.status_code == 200:
                for r in res_a.json():
                    es_entrada = r.get("tipo_ajuste") in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
                    facturas.append({
                        "tipo": "AJUSTE_ENTRADA" if es_entrada else "AJUSTE_SALIDA",
                        "ref": r.get("id_ajuste"),
                        "factura": r.get("motivo_observacion") or "Ajuste Directo",
                        "total": float(r.get("costo_total_ajuste") or 0),
                        "hora": r.get("fecha_ajuste", "") if len(r.get("fecha_ajuste", "")) >= 16 else "12:00"
                    })

        except Exception as ex:
            print(f"Error cargando historial del día: {ex}")

        # Ordenar por hora descendente (más reciente arriba)
        facturas.sort(key=lambda x: x["hora"], reverse=True)
        return facturas

    def get_codigos_factura_especifica(self, tipo: str, ref: str) -> list:
        try:
            if tipo == "COMPRA":
                res = self.session.get(f"{self.url}/registro_compras?numero_entrada=eq.{ref}&select=codigo_insumo", headers=self.headers, timeout=5)
            elif tipo.startswith("VENTA"):
                res = self.session.get(f"{self.url}/registro_ventas?factura_no=eq.{ref}&select=codigo_insumo", headers=self.headers, timeout=5)
            else:
                res = self.session.get(f"{self.url}/registro_ajustes_inventario?id_ajuste=eq.{ref}&select=codigo_insumo", headers=self.headers, timeout=5)
            
            if res.status_code == 200:
                return list(set([r.get("codigo_insumo") for r in res.json() if r.get("codigo_insumo")]))
        except: pass
        return []
        return []

    def insert_ajuste_individual(self, datos: dict) -> bool:
        """Inserta un nuevo registro de ajuste operativo."""
        url = f"{self.url}/registro_ajustes_inventario"
        try:
            res = self.session.post(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 201, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en insert_ajuste_individual: el servidor no responde")
        except Exception as e:
            return False

    def anular_ajuste(self, id_ajuste: str) -> bool:
        """Cambia el estado del ajuste a ANULADO. El trigger en la BD revertirá el inventario."""
        url = f"{self.url}/registro_ajustes_inventario?id_ajuste=eq.{id_ajuste}"
        try:
            res = self.session.patch(url, json={"estado_registro": "ANULADO"}, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en anular_ajuste: el servidor no responde")
        except Exception as e:
            return False

    def get_periodos_inventario(self) -> list:
        """Obtiene la lista de periodos de inventario ordenados descendentemente."""
        url = f"{self.url}/periodos_inventario?select=*&order=mes_periodo.desc"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return []
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_periodos_inventario: el servidor no responde")
            return []
        except Exception as e:
            return []

    def get_proyeccion_ventas(self, fecha_corte=None) -> float:
        """Invoca RPC get_proyeccion_ventas_rpc"""
        url = f"{self.url}/rpc/get_proyeccion_ventas_rpc"
        try:
            payload = {}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload if payload else None, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return float(data) if data is not None else 0.0
            return 0.0
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_proyeccion_ventas: el servidor no responde")
            return 0.0
        except Exception:
            return 0.0

    def get_ajustes_mes(self, mes_actual: str, fecha_corte=None) -> list:
        """Invoca RPC get_ajustes_mes_rpc"""
        url = f"{self.url}/rpc/get_ajustes_mes_rpc"
        try:
            payload = {"mes_actual": mes_actual}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else []
            return []
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_ajustes_mes: el servidor no responde")
            return []
        except Exception:
            return []

    def aceptar_stock_sistema_masivo(self, ids_auditoria: list) -> dict:
        url = f"{self.url}/rpc/fn_aceptar_stock_sistema_masivo"
        try:
            res = self.session.post(url, json={"p_ids": ids_auditoria}, headers=self.headers, timeout=15)
            if res.status_code == 200: return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e: return {"exito": False, "error": str(e)}

    def eliminar_ajuste_cierre(self, id_auditoria: str) -> dict:
        url = f"{self.url}/rpc/fn_eliminar_ajuste_cierre"
        try:
            res = self.session.post(url, json={"p_id_auditoria": id_auditoria}, headers=self.headers, timeout=10)
            if res.status_code == 200: return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e: return {"exito": False, "error": str(e)}

    def get_rendimiento_categorias_periodo(self, fecha_inicio=None, fecha_fin=None) -> list:
        """
        Calcula el rendimiento y costo acumulado real por categoría hasta 'fecha_fin'
        usando la vista/RPC de inventario calculado.
        """
        categorias_map = {}
        try:
            # Obtener todos los insumos calculados hasta fecha_fin
            insumos, _ = self.get_insumos(page=1, page_size=99999, fecha_corte=fecha_fin)
            
            for item in insumos:
                cat_nombre = (item.get("categoria") or "SIN CATEGORÍA").strip().upper()
                
                # Stock real calculado por el servidor (vista o RPC)
                stock = float(item.get("stock_actual") or item.get("stock_real") or 0)
                costo_u = float(item.get("costo_unitario") or 0)
                precio_v = float(item.get("precio_venta") or 0)
                
                # Costo total calculado por la BD o fallback producto
                inv_costo_item = float(item.get("costo_total_insumo") or (stock * costo_u))
                proy_venta_item = stock * precio_v
                ventas_item = float(item.get("valor_ventas") or 0)
                cant_ventas = float(item.get("ventas") or 0)
                costo_vendido_item = cant_ventas * costo_u
    
                if cat_nombre not in categorias_map:
                    categorias_map[cat_nombre] = {
                        "categoria": cat_nombre,
                        "inventario_costo": 0.0,
                        "proyeccion_venta": 0.0,
                        "ventas_realizadas": 0.0,
                        "costo_vendido": 0.0
                    }
    
                categorias_map[cat_nombre]["inventario_costo"] += inv_costo_item
                categorias_map[cat_nombre]["proyeccion_venta"] += proy_venta_item
                categorias_map[cat_nombre]["ventas_realizadas"] += ventas_item
                categorias_map[cat_nombre]["costo_vendido"] += costo_vendido_item
    
        except Exception as ex:
            print(f"Error calculando rendimiento acumulado por categoría: {ex}")
    
        # Formatear lista final con indicadores matemáticos reales
        resultado = []
        for cat_nombre, d in categorias_map.items():
            inv_c = d["inventario_costo"]
            v_real = d["ventas_realizadas"]
            proy_v = d["proyeccion_venta"]
            c_vend = d["costo_vendido"]
    
            cumplimiento = (v_real / proy_v * 100) if proy_v > 0 else 0.0
            rotacion = (v_real / inv_c) if inv_c > 0 else 0.0
            rendimiento = ((v_real - c_vend) / v_real * 100) if v_real > 0 else (100.0 if v_real == 0 else 0.0)
    
            resultado.append({
                "categoria": cat_nombre,
                "inventario_costo": inv_c,
                "ventas_realizadas": v_real,
                "proyeccion_venta": proy_v,
                "cumplimiento_pct": cumplimiento,
                "rotacion": rotacion,
                "rendimiento_pct": rendimiento
            })
    
        # Ordenar por costo de inventario descendente
        resultado.sort(key=lambda x: (x["inventario_costo"], x["ventas_realizadas"]), reverse=True)
        return resultado


    # --- CRUD COMPRAS INDIVIDUALES ---
    def update_compra_individual(self, id_compra, datos):
        """Actualiza un registro de compra individual por su UUID."""
        try:
            url = f"{self.url}/registro_compras?id_compra=eq.{id_compra}"
            res = self.session.patch(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en update_compra_individual: {ex}")
            return False

    def eliminar_compra_individual(self, id_compra):
        """Elimina un registro de compra individual de Supabase."""
        try:
            url = f"{self.url}/registro_compras?id_compra=eq.{id_compra}"
            res = self.session.delete(url, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en eliminar_compra_individual: {ex}")
            return False

    # --- CRUD VENTAS INDIVIDUALES ---
    def insert_venta_individual(self, datos):
        """Crea un registro de venta individual en Supabase."""
        try:
            url = f"{self.url}/registro_ventas"
            res = self.session.post(url, json=[datos], headers=self.headers, timeout=10)
            return res.status_code in (200, 201)
        except Exception as ex:
            print(f"Error en insert_venta_individual: {ex}")
            return False

    def update_venta_individual(self, id_venta, datos):
        """Actualiza un registro de venta individual por su UUID."""
        try:
            url = f"{self.url}/registro_ventas?id_venta=eq.{id_venta}"
            res = self.session.patch(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en update_venta_individual: {ex}")
            return False

    def eliminar_venta_individual(self, id_venta):
        """Elimina un registro de venta individual de Supabase."""
        try:
            url = f"{self.url}/registro_ventas?id_venta=eq.{id_venta}"
            res = self.session.delete(url, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except Exception as ex:
            print(f"Error en eliminar_venta_individual: {ex}")
            return False
````
