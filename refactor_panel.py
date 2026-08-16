import os

file_path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Corrección del Dropdown de Período
target1 = """    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.current_page = 1
        self.load_data()"""
repl1 = """    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.month_dropdown.update()
        self.current_page = 1
        self.load_data()"""
content = content.replace(target1, repl1)

# 2. Actualización de las Columnas del DataTable
target2 = """            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Stock Sist.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Físico", weight="bold")),
                ft.DataColumn(ft.Text("Diferencia", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acción", weight="bold")),
            ],"""
repl2 = """            columns=[
                ft.DataColumn(ft.Container(width=25)), # Checkbox
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Categoría", weight="bold")),
                ft.DataColumn(ft.Text("Stock Sist.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Físico", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Diferencia", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Ajuste", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Observación", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
            ],"""
content = content.replace(target2, repl2)

# 3. Construcción del Panel Inferior Reactivo
target3 = """        # Controles Paginación Interfaz
        self.lbl_page_info = ft.Text("Página 1 de 1")"""
repl3 = """        self.current_edit_context = None
        
        # Controles del Panel de Edición
        self.edit_panel_title = ft.Text("Editando Insumo...", color="white", weight="bold", size=16)
        
        input_style = {"text_size": 13, "height": 40, "content_padding": 10, "bgcolor": "white", "color": "black", "border_color": ft.colors.with_opacity(0.3, "white")}
        
        self.edit_fisico = ft.TextField(label="Stock Físico", width=100, **input_style)
        self.edit_costo = ft.TextField(label="Costo Unitario", width=120, **input_style)
        self.edit_observacion = ft.TextField(label="Observación / Justificación", width=250, **input_style)
        
        self.lbl_diferencia = ft.Text("Dif: 0", color="white", weight="bold")
        self.lbl_tipo_ajuste = ft.Text("Tipo: N/A", color="white")
        self.lbl_costo_total = ft.Text("Total: $0", color="white", weight="bold")

        def calcular_totales_panel(e):
            if not self.current_edit_context: return
            try:
                stock_sist = float(self.current_edit_context['item']['cantidad_sistema'])
                fisico = float(self.edit_fisico.value) if self.edit_fisico.value else stock_sist
                costo_u = float(self.edit_costo.value) if self.edit_costo.value else 0.0
                
                diferencia = fisico - stock_sist
                costo_total = abs(diferencia) * costo_u
                
                self.lbl_diferencia.value = f"Dif: {diferencia:g}"
                self.lbl_diferencia.color = "red300" if diferencia != 0 else "white"
                
                if diferencia > 0:
                    self.lbl_tipo_ajuste.value = "Tipo: AJUSTE_ENTRADA"
                elif diferencia < 0:
                    self.lbl_tipo_ajuste.value = "Tipo: AJUSTE_SALIDA"
                else:
                    self.lbl_tipo_ajuste.value = "Tipo: NINGUNO"
                    
                self.lbl_costo_total.value = f"Total: ${costo_total:,.2f}"
            except ValueError:
                self.lbl_diferencia.value = "Dif: Error"
                self.lbl_costo_total.value = "Total: Error"
            self.action_bar.update()

        self.edit_fisico.on_change = calcular_totales_panel
        self.edit_costo.on_change = calcular_totales_panel

        self.btn_guardar_edicion = ft.ElevatedButton("Guardar Conteo", bgcolor="green", color="white", on_click=self.on_guardar_conteo_panel)
        
        self.action_bar = ft.Container(
            content=ft.Column([
                self.edit_panel_title,
                ft.Row([
                    self.edit_fisico,
                    self.edit_costo,
                    self.edit_observacion,
                    ft.Container(width=20),
                    ft.Column([self.lbl_diferencia, self.lbl_tipo_ajuste], spacing=2),
                    ft.Container(width=20),
                    self.lbl_costo_total,
                    ft.Container(expand=True),
                    ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color="white"), on_click=self.cancelar_edicion),
                    self.btn_guardar_edicion
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=10),
            bgcolor=Config.COLOR_PRIMARY,
            padding=15,
            border_radius=10,
            visible=False
        )

        # Controles Paginación Interfaz
        self.lbl_page_info = ft.Text("Página 1 de 1")"""
content = content.replace(target3, repl3)

target3b = """                padding=ft.padding.only(top=10)
            )
        )"""
repl3b = """                padding=ft.padding.only(top=10)
            )
        )
        self.content.controls.append(self.action_bar)"""
content = content.replace(target3b, repl3b)

# 4. Refactorización de la Creación de Filas
target4 = """    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo["id_auditoria"]
        estado_insumo = insumo["estado"]
        cant_sistema = insumo["cantidad_sistema"]
        cant_fisica = insumo.get("cantidad_fisica")
        
        # Campo para ingresar conteo físico
        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else "",
            dense=True, width=80, text_size=13, content_padding=10,
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO")
        )

        btn_aceptar_sistema = ft.IconButton(
            icon=ft.icons.CHECK_BOX,
            icon_color="green",
            tooltip="Aceptar Stock del Sistema",
            disabled=(estado_periodo == "CERRADO" or estado_insumo != "PENDIENTE"),
            on_click=lambda e: self.procesar_aceptar_sistema(id_auditoria)
        )

        btn_guardar_conteo = ft.IconButton(
            icon=ft.icons.SAVE,
            icon_color="blue",
            tooltip="Guardar Conteo Físico",
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO"),
            on_click=lambda e: self.procesar_guardar_conteo(id_auditoria, txt_conteo.value)
        )

        acciones = ft.Row([btn_aceptar_sistema, btn_guardar_conteo], spacing=0)

        color_diferencia = "red" if insumo.get("diferencia", 0) != 0 else "black"

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(insumo["codigo_insumo"])),
                ft.DataCell(ft.Text(insumo["nombre"], width=200, no_wrap=True, tooltip=insumo["nombre"])),
                ft.DataCell(ft.Text(str(cant_sistema), weight="bold")),
                ft.DataCell(txt_conteo),
                ft.DataCell(ft.Text(str(insumo.get("diferencia", "")), color=color_diferencia)),
                ft.DataCell(ft.Text(estado_insumo, size=11, weight="bold", color="grey")),
                ft.DataCell(acciones),
            ]
        )"""

# In the script replacement for target4, we'll replace everything from `def crear_fila_auditoria` to the end of the file.
# Then append the new `crear_fila_auditoria` and the new toggle methods.
target4_and_beyond = content[content.find("    def crear_fila_auditoria(self, insumo, estado_periodo):"):]

repl4 = """    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo["id_auditoria"]
        estado_insumo = insumo["estado"]
        cant_sistema = insumo["cantidad_sistema"]
        cant_fisica = insumo.get("cantidad_fisica")
        diferencia = insumo.get("diferencia", 0)
        observacion = insumo.get("observacion") or ""
        categoria = insumo.get("categoria") or ""
        
        # El costo del ajuste se puede derivar multiplicando diferencia por costo unitario
        costo_unit = insumo.get("costo_unitario_snapshot", 0)
        costo_ajuste_total = abs(diferencia) * costo_unit if diferencia else 0

        color_diferencia = "red" if diferencia != 0 else "black"
        
        row_ref = ft.DataRow(cells=[])
        
        checkbox = ft.Checkbox(
            value=False, 
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO"),
            on_change=lambda e, i=insumo, r=row_ref: self.toggle_edit(e, i, r)
        )

        row_ref.cells = [
            ft.DataCell(ft.Container(content=checkbox, width=25, alignment=ft.alignment.center)),
            ft.DataCell(ft.Text(insumo["codigo_insumo"])),
            ft.DataCell(ft.Text(insumo["nombre"], width=180, no_wrap=True, tooltip=insumo["nombre"])),
            ft.DataCell(ft.Text(categoria, width=100, no_wrap=True, tooltip=categoria)),
            ft.DataCell(ft.Text(str(cant_sistema), weight="bold")),
            ft.DataCell(ft.Text(str(cant_fisica) if cant_fisica is not None else "")),
            ft.DataCell(ft.Text(str(diferencia), color=color_diferencia)),
            ft.DataCell(ft.Text(f"${costo_ajuste_total:,.2f}" if costo_ajuste_total else "")),
            ft.DataCell(ft.Text(observacion, width=150, no_wrap=True, tooltip=observacion)),
            ft.DataCell(ft.Text(estado_insumo, size=11, weight="bold", color="grey")),
        ]
        return row_ref

    def toggle_edit(self, e, insumo, row_ref):
        if not e.control.value:
            self.cancelar_edicion()
            return
            
        if self.current_edit_context and self.current_edit_context['row'] != row_ref:
            prev_row = self.current_edit_context['row']
            if prev_row and len(prev_row.cells) > 0:
                prev_row.cells[0].content.content.value = False
                
        self.current_edit_context = {'item': insumo, 'row': row_ref}
        
        cod = insumo.get('codigo_insumo', '')
        nom = insumo.get('nombre', '')
        cat = insumo.get('categoria', '')
        stock_sist = insumo.get('cantidad_sistema', 0)
        costo_u = insumo.get('costo_unitario_snapshot', 0)
        
        self.edit_panel_title.value = f"Auditando: [{cod}] {nom} | Cat: {cat} | Stock Sistema: {stock_sist}"
        self.edit_fisico.value = str(insumo.get('cantidad_fisica')) if insumo.get('cantidad_fisica') is not None else str(stock_sist)
        self.edit_costo.value = str(costo_u)
        self.edit_observacion.value = insumo.get('observacion') or ""
        
        self.edit_fisico.on_change(None) # Disparar cálculo inicial
        self.action_bar.visible = True
        self.update()

    def cancelar_edicion(self, e=None):
        if self.current_edit_context:
            row_ref = self.current_edit_context['row']
            if row_ref and len(row_ref.cells) > 0:
                row_ref.cells[0].content.content.value = False
        self.current_edit_context = None
        self.action_bar.visible = False
        self.update()

    def on_guardar_conteo_panel(self, e):
        if not self.current_edit_context: return
        item = self.current_edit_context['item']
        id_auditoria = item['id_auditoria']
        stock_sist = float(item['cantidad_sistema'])
        
        try:
            fisico = float(self.edit_fisico.value)
            costo = float(self.edit_costo.value)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Valores numéricos inválidos."), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        obs = self.edit_observacion.value.strip()

        # Si el conteo físico es igual al del sistema y no hay observación obligatoria, usar aceptar_stock_sistema
        if fisico == stock_sist and not obs:
            res = self.db.aceptar_stock_sistema(id_auditoria)
        else:
            res = self.db.registrar_conteo_fisico(id_auditoria, fisico, costo, obs)
            
        if res.get("exito"):
            self.cancelar_edicion()
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error')}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()"""

content = content.replace(target4_and_beyond, repl4)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactor UI panel finished successfully.")
