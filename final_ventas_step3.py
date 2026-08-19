import re

with open("ui/views/ventas.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update data_table.columns
match_cols = re.search(r'columns=\[\s*(.*?)\s*\],\s*rows=\[\]', content, re.DOTALL)
if match_cols:
    old_cols = match_cols.group(1)
    new_cols = """ft.DataColumn(ft.Text("Fecha", weight="bold")),
                ft.DataColumn(ft.Text("No. Factura", weight="bold")),
                ft.DataColumn(ft.Text("Tipo Doc.", weight="bold")),
                ft.DataColumn(ft.Text("Código Item", weight="bold")),
                ft.DataColumn(ft.Container(content=ft.Text("Nombre / Descripción", weight="bold"), width=250)),
                ft.DataColumn(ft.Text("Cantidad", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Precio Unit.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("IVA", weight="bold")),
                ft.DataColumn(ft.Text("Total", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Acciones", weight="bold"))"""
    
    # We replace the columns if it doesn't already have Acciones
    # Let's just do a direct replacement for the entire columns array of the FIRST datatable
    content = content.replace(f"columns=[\n{old_cols}\n              ],", f"columns=[\n                {new_cols}\n              ],", 1)
    content = content.replace(f"columns=[\n                  {old_cols}\n              ],", f"columns=[\n                {new_cols}\n              ],", 1)

# 2. Rewrite _fetch_data_worker to match user's variables and DataRow
old_fetch = re.search(r'def _fetch_data_worker\(self\):.*?self\.update_pagination_ui\(\)', content, re.DOTALL)
if old_fetch:
    new_fetch = """def _fetch_data_worker(self):
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
            str_fecha = fecha_raw[:10] if len(fecha_raw) >= 10 else fecha_raw
            
            str_factura = str(item.get('factura_no') or 'N/A')
            str_tipo_doc = str(item.get('tipo_documento') or 'Remisión')
            str_codigo = str(item.get('codigo_insumo', ''))
            
            cat_info = item.get('catalogo_insumos') or {}
            nombre_bd = cat_info.get('nombre')
            nombre_desc = item.get('descripcion')
            str_nombre = nombre_bd if nombre_bd else (nombre_desc if nombre_desc else 'Desconocido')
            
            cantidad = float(item.get('cantidad', 0) or 0)
            precio_unitario = float(item.get('subtotal', 0) or 0)
            iva = float(item.get('iva', 0) or 0)
            costo_total = float(item.get('total', 0) or 0)
            
            str_precio_unit = f"${precio_unitario:,.2f}"
            str_iva = f"${iva:,.2f}"
            str_total = f"${costo_total:,.2f}"
            
            str_cant = str(int(cantidad)) if cantidad.is_integer() else str(cantidad)
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str_fecha)),
                    ft.DataCell(ft.Text(str_factura)),
                    ft.DataCell(ft.Text(str_tipo_doc)),
                    ft.DataCell(ft.Text(str_codigo)),
                    ft.DataCell(ft.Container(content=ft.Text(str_nombre), width=250)),
                    ft.DataCell(ft.Text(str_cant)),
                    ft.DataCell(ft.Text(str_precio_unit)),
                    ft.DataCell(ft.Text(str_iva, color="grey")),
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
                ]
            )
            self.data_table.rows.append(row)
            
        self.update_pagination_ui()"""
    content = content.replace(old_fetch.group(0), new_fetch)

with open("ui/views/ventas.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Ventas updated for step 3")
