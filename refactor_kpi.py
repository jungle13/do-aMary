import os

file_path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()


# 1. Agregar helper de tarjeta (al inicio de los métodos o en __init__)
# Agregaremos _crear_kpi_card justo encima de did_mount

target1 = "    def did_mount(self):"
repl1 = """    def _crear_kpi_card(self, title, lbl_val, icon, lbl_sub=None):
        col_controls = [ft.Text(title, size=11, color="grey", weight="bold"), lbl_val]
        if lbl_sub: col_controls.append(lbl_sub)
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=Config.COLOR_SECONDARY, size=24),
                ft.Column(col_controls, spacing=0)
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor="white", padding=15, border_radius=8, expand=True,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
        )

    def did_mount(self):"""
content = content.replace(target1, repl1)


# 2. Inicializar los Controles del Resumen Financiero en __init__
# Buscamos self.content = ft.Column([
target2 = """        self.content = ft.Column(["""
repl2 = """        # Controles Dashboard Financiero
        self.lbl_valor_sistema = ft.Text("$0.00", size=16, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_ajustes_entrada = ft.Text("$0.00", size=16, weight="bold", color="green")
        self.lbl_cant_entrada = ft.Text("0 unds", size=10, color="grey")
        self.lbl_ajustes_salida = ft.Text("$0.00", size=16, weight="bold", color="red")
        self.lbl_cant_salida = ft.Text("0 unds", size=10, color="grey")
        self.lbl_neto_ajustes = ft.Text("$0.00", size=16, weight="bold")
        self.lbl_valor_fisico = ft.Text("$0.00", size=18, weight="bold", color=Config.COLOR_SECONDARY)
        
        self.summary_container = ft.Row([
            self._crear_kpi_card("Valor Sist.", self.lbl_valor_sistema, ft.icons.COMPUTER),
            self._crear_kpi_card("Sobrantes (+)", self.lbl_ajustes_entrada, ft.icons.ADD_CIRCLE_OUTLINE, self.lbl_cant_entrada),
            self._crear_kpi_card("Faltantes (-)", self.lbl_ajustes_salida, ft.icons.REMOVE_CIRCLE_OUTLINE, self.lbl_cant_salida),
            self._crear_kpi_card("Neto Ajustes", self.lbl_neto_ajustes, ft.icons.ACCOUNT_BALANCE_WALLET),
            self._crear_kpi_card("Valor Físico Proyectado", self.lbl_valor_fisico, ft.icons.FACT_CHECK)
        ], spacing=10)

        self.content = ft.Column(["""
content = content.replace(target2, repl2)


# Y luego agregamos self.summary_container a self.content
target2b = """            ft.Text("Auditoría y Cierre de Período", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Container("""
repl2b = """            ft.Text("Auditoría y Cierre de Período", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            self.summary_container,
            ft.Container("""
content = content.replace(target2b, repl2b)


# 3. Lógica matemática en render_view
target3 = """        # Lógica de segmentación para renderizado (Paginación O(N) optimizada)"""
repl3 = """        # --- Cálculo de KPIs Financieros Globales ---
        valor_sistema = 0.0
        valor_entrada = 0.0
        cant_entrada = 0.0
        valor_salida = 0.0
        cant_salida = 0.0

        for ins = self.insumos_lista:
            cant_sist = float(ins.get("cantidad_sistema") or 0)
            costo_u = float(ins.get("costo_unitario_snapshot") or 0)
            dif = ins.get("diferencia")

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

        self.lbl_valor_sistema.value = f"${valor_sistema:,.2f}"
        self.lbl_ajustes_entrada.value = f"${valor_entrada:,.2f}"
        self.lbl_cant_entrada.value = f"+{cant_entrada:g} unds"
        self.lbl_ajustes_salida.value = f"${valor_salida:,.2f}"
        self.lbl_cant_salida.value = f"-{cant_salida:g} unds"
        self.lbl_neto_ajustes.value = f"${valor_neto:,.2f}"
        self.lbl_neto_ajustes.color = "green" if valor_neto >= 0 else "red"
        self.lbl_valor_fisico.value = f"${valor_fisico:,.2f}"
        # ---------------------------------------------

        # Lógica de segmentación para renderizado (Paginación O(N) optimizada)"""
content = content.replace(target3, repl3)


# 4. Reemplazar crear_fila_auditoria (y eliminar lo de costo_unit antiguo)
# Como la función llega hasta toggle_edit, lo usaremos para encontrar el final
target4_and_beyond = content[content.find("    def crear_fila_auditoria(self, insumo, estado_periodo):"):content.find("    def toggle_edit(self, e, insumo, row_ref):")]

repl4 = """    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo["id_auditoria"]
        estado_insumo = insumo["estado"]
        cant_sistema = insumo["cantidad_sistema"]
        cant_fisica = insumo.get("cantidad_fisica")
        diferencia = insumo.get("diferencia")
        observacion = insumo.get("observacion") or ""
        categoria = insumo.get("categoria") or ""
        
        costo_unit = float(insumo.get("costo_unitario_snapshot") or 0)
        
        # Corrección del texto "None" y cálculo riguroso del Costo Ajuste
        str_dif = ""
        str_costo_ajuste = ""
        color_diferencia = "black"

        if diferencia is not None:
            dif_flt = float(diferencia)
            str_dif = f"{dif_flt:g}"
            if dif_flt != 0:
                color_diferencia = "red"
                str_costo_ajuste = f"${(abs(dif_flt) * costo_unit):,.2f}"
        
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
            ft.DataCell(ft.Text(str_dif, color=color_diferencia)),
            ft.DataCell(ft.Text(str_costo_ajuste)),
            ft.DataCell(ft.Text(observacion, width=150, no_wrap=True, tooltip=observacion)),
            ft.DataCell(ft.Text(estado_insumo, size=11, weight="bold", color="grey")),
        ]
        return row_ref

"""
content = content.replace(target4_and_beyond, repl4)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("KPI Panel refactor script finished.")
