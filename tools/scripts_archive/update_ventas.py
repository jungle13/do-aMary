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
