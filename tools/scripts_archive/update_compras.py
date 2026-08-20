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
