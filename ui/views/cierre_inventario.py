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
        self.input_search = ft.TextField(hint_text="Buscar código o nombre...", prefix_icon=ft.icons.SEARCH, height=40, expand=True, on_change=self.on_filter_change)
        self.drop_categoria = ft.Dropdown(label="Categoría", options=[ft.dropdown.Option("Todas")], height=40, width=150, on_change=self.on_filter_change)
        self.drop_estado = ft.Dropdown(label="Estado", options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("PENDIENTE"), ft.dropdown.Option("AUDITADO"), ft.dropdown.Option("AJUSTADO")], value="Todos", height=40, width=150, on_change=self.on_filter_change)
        
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
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)

        # Controles Dashboard Financiero
        self.lbl_valor_sistema = ft.Text('$0.00', size=16, weight='bold', color=Config.COLOR_PRIMARY)
        self.lbl_ajustes_entrada = ft.Text('$0.00', size=16, weight='bold', color='green')
        self.lbl_cant_entrada = ft.Text('0 unds', size=10, color='grey')
        self.lbl_ajustes_salida = ft.Text('$0.00', size=16, weight='bold', color='red')
        self.lbl_cant_salida = ft.Text('0 unds', size=10, color='grey')
        self.lbl_neto_ajustes = ft.Text('$0.00', size=16, weight='bold')
        self.lbl_valor_fisico = ft.Text('$0.00', size=18, weight='bold', color=Config.COLOR_SECONDARY)
        
        self.kpi_compacto = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Valor del Sistema:", weight="bold", color="grey"), self.lbl_valor_sistema,
                    ft.Text(" | Valor Físico Proyectado:", weight="bold", color="grey"), self.lbl_valor_fisico,
                ]),
                ft.Row([
                    ft.Text("Sobrantes (+):", weight="bold", color="grey"), self.lbl_ajustes_entrada,
                    ft.Text(" | Faltantes (-):", weight="bold", color="grey"), self.lbl_ajustes_salida,
                    ft.Text(" | Neto Ajustes:", weight="bold", color="grey"), self.lbl_neto_ajustes,
                ])
            ], spacing=2),
            bgcolor="#f8f9fa", padding=10, border_radius=8, border=ft.border.all(1, "#e0e0e0")
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
                ft.DataCell(ft.ElevatedButton('Ver', on_click=lambda e, m=mes_periodo: self.mostrar_detalle(m)))
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
            botones_accion.append(ft.ElevatedButton("Aceptar", icon=ft.icons.CHECK, bgcolor="green50", color="green900", on_click=lambda e, i_id=id_auditoria: self.procesar_aceptar_sistema(i_id), scale=0.85, disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO')))
            btn_ajuste_pendiente = ft.OutlinedButton("Ingresar Ajuste", icon=ft.icons.TUNE, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=True)
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
            btn_ajuste = ft.OutlinedButton("Editar Ajuste", icon=ft.icons.EDIT, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=(estado_periodo == 'CERRADO'))
            botones_accion.append(btn_ajuste)
            btn_ajuste.disabled = False if txt_conteo.value else True
        elif estado_insumo == "AJUSTADO":
            btn_ajuste = ft.OutlinedButton("Editar Ajuste", icon=ft.icons.EDIT, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=(estado_periodo == 'CERRADO'))
            botones_accion.append(btn_ajuste)
            botones_accion.append(ft.OutlinedButton("Eliminar Ajuste", icon=ft.icons.DELETE, icon_color="red", style=ft.ButtonStyle(color="red"), on_click=lambda e, i_id=id_auditoria: self.procesar_eliminar_ajuste(i_id), scale=0.85, disabled=(estado_periodo == 'CERRADO')))
            btn_ajuste.disabled = False if txt_conteo.value else True
        else:
            # Fallback (e.g., APROBADO) - disabled buttons or none
            btn_ajuste = ft.OutlinedButton("Bloqueado", disabled=True, scale=0.85)
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
