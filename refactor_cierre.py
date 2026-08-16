import os

file_path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Variables de Paginación Interna
part1_target = """        self.datos_cierre = {}"""
part1_repl = """        self.datos_cierre = {}
        
        # Variables de Paginación Interna
        self.page_size = 50
        self.current_page = 1
        self.total_pages = 1
        self.insumos_lista = []"""
content = content.replace(part1_target, part1_repl)


# 2. Controles de Paginación Interfaz
part2_target = """        self.content = ft.Column(["""
part2_repl = """        # Controles Paginación Interfaz
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)

        self.content = ft.Column(["""
content = content.replace(part2_target, part2_repl)


# 3. Footer de paginación
part3_target = """        ], expand=True, spacing=15)"""
part3_repl = """        ], expand=True, spacing=15)
        
        self.content.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.only(top=10)
            )
        )"""
content = content.replace(part3_target, part3_repl)


# 4. Métodos on_month_change y on_generar_snapshot
part4_target = """    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.load_data()

    def on_generar_snapshot(self, e):
        res = self.db.iniciar_snapshot_cierre(self.mes_seleccionado)
        if res.get("exito"):
            self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error', 'Desconocido')}"), bgcolor="red")
        self.page.snack_bar.open = True
        self.page.update()"""

part4_repl = """    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_view()

    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_view()

    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.current_page = 1
        self.load_data()

    def on_generar_snapshot(self, e):
        res = self.db.iniciar_snapshot_cierre(self.mes_seleccionado)
        if res.get("exito"):
            self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
            self.current_page = 1
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error', 'Desconocido')}"), bgcolor="red")
        self.page.snack_bar.open = True
        self.page.update()"""
content = content.replace(part4_target, part4_repl)


# 5. Métodos load_data y render_view
part5_target = """    def load_data(self):
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.render_view()

    def render_view(self):
        self.data_table.rows.clear()
        
        if not self.datos_cierre or not self.datos_cierre.get("periodo"):
            self.txt_estado_periodo.value = "Estado: NO INICIALIZADO"
            self.txt_estado_periodo.color = "grey"
            self.txt_progreso.value = "Requiere generar snapshot"
            self.btn_iniciar_snapshot.disabled = False
            self.btn_aprobar_cierre.disabled = True
            if self.page: self.update()
            return

        periodo = self.datos_cierre["periodo"]
        resumen = self.datos_cierre.get("resumen", {})
        insumos = self.datos_cierre.get("insumos", [])

        estado_periodo = periodo.get("estado", "DESCONOCIDO")
        self.txt_estado_periodo.value = f"Estado: {estado_periodo}"
        
        color_estado = {"ABIERTO": "green", "PRELIMINAR": "orange", "EN_AUDITORIA": "blue", "CERRADO": "red"}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, "black")
        
        pendientes = resumen.get("pendientes", 0)
        self.txt_progreso.value = f"Pendientes: {pendientes} | Listos: {resumen.get('auditados', 0) + resumen.get('ajustados', 0)}"

        self.btn_iniciar_snapshot.disabled = estado_periodo in ["CERRADO", "PRELIMINAR", "EN_AUDITORIA"]
        self.btn_aprobar_cierre.disabled = estado_periodo == "CERRADO" or pendientes > 0

        for insumo in insumos:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))

        if self.page:
            self.update()"""

part5_repl = """    def load_data(self):
        import math
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.insumos_lista = self.datos_cierre.get("insumos", [])
        
        # Calcular total de páginas
        total_records = len(self.insumos_lista)
        self.total_pages = math.ceil(total_records / self.page_size) if total_records > 0 else 1
        
        # Prevención de desbordamiento de índice
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        self.render_view()

    def render_view(self):
        self.data_table.rows.clear()
        
        if not self.datos_cierre or not self.datos_cierre.get("periodo"):
            self.txt_estado_periodo.value = "Estado: NO INICIALIZADO"
            self.txt_estado_periodo.color = "grey"
            self.txt_progreso.value = "Requiere generar snapshot"
            self.btn_iniciar_snapshot.disabled = False
            self.btn_aprobar_cierre.disabled = True
            if self.page: self.update()
            return

        periodo = self.datos_cierre["periodo"]
        resumen = self.datos_cierre.get("resumen", {})

        estado_periodo = periodo.get("estado", "DESCONOCIDO")
        self.txt_estado_periodo.value = f"Estado: {estado_periodo}"
        
        color_estado = {"ABIERTO": "green", "PRELIMINAR": "orange", "EN_AUDITORIA": "blue", "CERRADO": "red"}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, "black")
        
        pendientes = resumen.get("pendientes", 0)
        listos = resumen.get('auditados', 0) + resumen.get('ajustados', 0)
        self.txt_progreso.value = f"Pendientes: {pendientes} | Listos: {listos}"

        self.btn_iniciar_snapshot.disabled = estado_periodo in ["CERRADO", "PRELIMINAR", "EN_AUDITORIA"]
        self.btn_aprobar_cierre.disabled = estado_periodo == "CERRADO" or pendientes > 0

        # Lógica de segmentación para renderizado (Paginación O(N) optimizada)
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.insumos_lista[start_idx:end_idx]

        for insumo in page_data:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))

        # Actualizar UI de botones de paginación
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)

        if self.page:
            self.update()"""
            
content = content.replace(part5_target, part5_repl)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactor finished successfully.")
