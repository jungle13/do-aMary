import os

# 1. Actualizar core/supabase_client.py
client_file = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\core\supabase_client.py'
with open(client_file, 'r', encoding='utf-8') as f:
    client_code = f.read()

new_methods = """
    def iniciar_snapshot_cierre(self, mes_periodo: str) -> dict:
        \"\"\"Invoca el RPC para generar el snapshot preliminar del mes.\"\"\"
        url = f"{self.url}/rpc/fn_snapshot_cierre_mensual"
        try:
            import requests
            res = requests.post(url, json={"p_mes": mes_periodo}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def obtener_estado_cierre(self, mes_periodo: str) -> dict:
        \"\"\"Obtiene el resumen y los insumos del período especificado.\"\"\"
        url = f"{self.url}/rpc/fn_obtener_estado_cierre"
        try:
            import requests
            res = requests.post(url, json={"p_mes": mes_periodo}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {}
        except Exception as e:
            print(f"Error en obtener_estado_cierre: {e}")
            return {}

    def registrar_conteo_fisico(self, id_auditoria: str, cantidad: float, costo: float = None, observacion: str = None) -> dict:
        \"\"\"Registra el conteo físico y genera ajustes si existe diferencia.\"\"\"
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
            import requests
            res = requests.post(url, json=payload, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aceptar_stock_sistema(self, id_auditoria: str) -> dict:
        \"\"\"Acepta el stock calculado por el sistema sin conteo físico.\"\"\"
        url = f"{self.url}/rpc/fn_aceptar_stock_sistema"
        try:
            import requests
            res = requests.post(url, json={"p_id_auditoria": id_auditoria}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aprobar_cierre_mes(self, id_periodo: str, aprobado_por: str) -> dict:
        \"\"\"Cierra el período y consolida el inventario inicial del mes siguiente.\"\"\"
        url = f"{self.url}/rpc/fn_aprobar_cierre_mes"
        try:
            import requests
            res = requests.post(url, json={"p_id_periodo": id_periodo, "p_aprobado_por": aprobado_por}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}
"""

if "def iniciar_snapshot_cierre" not in client_code:
    client_code += new_methods
    with open(client_file, 'w', encoding='utf-8') as f:
        f.write(client_code)


# 2. Crear ui/views/cierre_inventario.py
view_file = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
view_code = """import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
import datetime
from dateutil.relativedelta import relativedelta

class CierreInventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        self.datos_cierre = {}
        
        # Opciones de Meses
        hoy = datetime.date.today()
        opciones_meses = []
        for i in range(12):
            m = hoy - relativedelta(months=i)
            val = m.strftime("%Y-%m")
            nombre_mes = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][m.month - 1]
            opciones_meses.append(ft.dropdown.Option(key=val, text=f"{nombre_mes} {m.year}"))
            
        self.mes_seleccionado = hoy.strftime("%Y-%m")
        
        # Controles Superiores
        self.month_dropdown = ft.Dropdown(
            options=opciones_meses,
            value=self.mes_seleccionado,
            label="Período de Auditoría",
            width=200,
            border_radius=8,
            height=40,
            on_change=self.on_month_change
        )
        
        self.btn_iniciar_snapshot = ft.ElevatedButton(
            text="Generar Snapshot Preliminar",
            icon=ft.icons.CAMERA_ALT,
            bgcolor=Config.COLOR_SECONDARY,
            color="white",
            on_click=self.on_generar_snapshot
        )
        
        self.btn_aprobar_cierre = ft.ElevatedButton(
            text="Aprobar Cierre Definitivo",
            icon=ft.icons.CHECK_CIRCLE,
            bgcolor="green",
            color="white",
            disabled=True,
            on_click=self.on_aprobar_cierre
        )

        # Indicadores de Estado
        self.txt_estado_periodo = ft.Text("Estado: DESCONOCIDO", weight="bold")
        self.txt_progreso = ft.Text("Pendientes: 0 | Auditados: 0", color="grey")

        # Tabla de Auditoría
        self.data_table = ft.DataTable(
            column_spacing=15,
            data_row_min_height=50,
            data_row_max_height=50,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Stock Sist.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Físico", weight="bold")),
                ft.DataColumn(ft.Text("Diferencia", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acción", weight="bold")),
            ],
            rows=[]
        )

        self.content = ft.Column([
            ft.Text("Auditoría y Cierre de Período", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Container(
                content=ft.Row([
                    self.month_dropdown,
                    self.btn_iniciar_snapshot,
                    ft.Container(expand=True),
                    ft.Column([self.txt_estado_periodo, self.txt_progreso], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                    self.btn_aprobar_cierre
                ]),
                padding=15,
                bgcolor="white",
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            ft.Container(
                content=ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS, expand=True),
                bgcolor="white",
                padding=5,
                border_radius=10,
                expand=True,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
            )
        ], expand=True, spacing=15)

    def did_mount(self):
        self.load_data()

    def on_month_change(self, e):
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
        self.page.update()

    def on_aprobar_cierre(self, e):
        id_periodo = self.datos_cierre.get("periodo", {}).get("id_periodo")
        if not id_periodo:
            return
            
        res = self.db.aprobar_cierre_mes(id_periodo, "Administrador Sistema")
        if res.get("exito"):
            self.page.snack_bar = ft.SnackBar(ft.Text("Período cerrado y consolidado con éxito."), bgcolor="green")
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error', 'Desconocido')}"), bgcolor="red")
        self.page.snack_bar.open = True
        self.page.update()

    def load_data(self):
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
            self.update()

    def crear_fila_auditoria(self, insumo, estado_periodo):
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
        )

    def procesar_aceptar_sistema(self, id_auditoria):
        res = self.db.aceptar_stock_sistema(id_auditoria)
        if res.get("exito"):
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error')}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    def procesar_guardar_conteo(self, id_auditoria, valor_texto):
        try:
            cantidad = float(valor_texto)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Ingrese un valor numérico válido."), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return

        res = self.db.registrar_conteo_fisico(id_auditoria, cantidad)
        if res.get("exito"):
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error')}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
"""

with open(view_file, 'w', encoding='utf-8') as f:
    f.write(view_code)

print("Update script finished.")
