import flet as ft
import threading
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
        
        # Variables de Paginación Interna
        self.page_size = 50
        self.current_page = 1
        self.total_pages = 1
        self.insumos_lista = []
        
        # Opciones de Meses
        hoy = datetime.date.today()
        opciones_meses = []
        for i in range(12):
            m = hoy - relativedelta(months=i)
            val = m.strftime('%Y-%m')
            nombre_mes = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][m.month - 1]
            opciones_meses.append(ft.dropdown.Option(key=val, text=f'{nombre_mes} {m.year}'))
            
        self.mes_seleccionado = hoy.strftime('%Y-%m')
        
        # Controles Superiores
        self.month_dropdown = ft.Dropdown(
            options=opciones_meses,
            value=self.mes_seleccionado,
            label='Mes a iniciar',
            width=200,
            border_radius=8,
            height=40,
            on_change=self.on_month_change
        )
        
        self.btn_iniciar_snapshot = ft.ElevatedButton(
            text='Generar Preliminar',
            icon=ft.icons.CAMERA_ALT,
            bgcolor=Config.COLOR_SECONDARY,
            color='white',
            on_click=self.on_generar_snapshot
        )
        
        self.btn_aprobar_cierre = ft.ElevatedButton(
            text='Aprobar Cierre Definitivo',
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
            column_spacing=15,
            data_row_min_height=50,
            data_row_max_height=50,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Container(width=25)), # Checkbox (vacio)
                ft.DataColumn(ft.Text('Código', weight='bold')),
                ft.DataColumn(ft.Text('Insumo', weight='bold')),
                ft.DataColumn(ft.Text('Inicial', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Entradas', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Salidas', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Ajustes', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Stock Actual', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Físico', weight='bold')),
                ft.DataColumn(ft.Text('Diferencia', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Costo Ajuste', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Observación', weight='bold')),
                ft.DataColumn(ft.Text('Estado', weight='bold')),
                ft.DataColumn(ft.Text('Acción', weight='bold')),
            ],
            rows=[]
        )

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
        
        self.summary_container = ft.Row([
            self._crear_kpi_card('Valor Sist.', self.lbl_valor_sistema, ft.icons.COMPUTER),
            self._crear_kpi_card('Sobrantes (+)', self.lbl_ajustes_entrada, ft.icons.ADD_CIRCLE_OUTLINE, self.lbl_cant_entrada),
            self._crear_kpi_card('Faltantes (-)', self.lbl_ajustes_salida, ft.icons.REMOVE_CIRCLE_OUTLINE, self.lbl_cant_salida),
            self._crear_kpi_card('Neto Ajustes', self.lbl_neto_ajustes, ft.icons.ACCOUNT_BALANCE_WALLET),
            self._crear_kpi_card('Valor Físico Proyectado', self.lbl_valor_fisico, ft.icons.FACT_CHECK)
        ], spacing=10)

        # Controles vista_lista (Maestro)
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
            )
        ], visible=False, expand=True, spacing=15)

        self.content = ft.Column([self.vista_lista, self.vista_detalle], expand=True)

    def _crear_kpi_card(self, title, lbl_val, icon, lbl_sub=None):
        col_controls = [ft.Text(title, size=11, color='grey', weight='bold'), lbl_val]
        if lbl_sub: col_controls.append(lbl_sub)
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=Config.COLOR_SECONDARY, size=24),
                ft.Column(col_controls, spacing=0)
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor='white', padding=15, border_radius=8, expand=True,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, 'black'))
        )

    def did_mount(self):
        if self.modal_ajuste not in self.page.overlay:
            self.page.overlay.append(self.modal_ajuste)
        self.load_lista_periodos()

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
            self.btn_aprobar_cierre.disabled = True
            if self.page:
                self.page.update()
            return

        self.txt_estado_periodo.value = f'Estado: {estado_periodo}'
        color_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, 'black')
        
        pendientes = resumen.get('pendientes', 0)
        listos = resumen.get('auditados', 0) + resumen.get('ajustados', 0)
        self.txt_progreso.value = f'Pendientes: {pendientes} | Listos: {listos}'

        self.btn_aprobar_cierre.disabled = estado_periodo == 'CERRADO' or pendientes > 0

        # KPIs Financieros
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

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.insumos_lista[start_idx:end_idx]

        for insumo in page_data:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))

        self.lbl_page_info.value = f'Página {self.current_page} de {self.total_pages}'
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)

        if self.page:
            self.page.update()

    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo.get('id_auditoria')
        estado_insumo = insumo.get('estado', 'PENDIENTE')
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
        habilitar_aceptar = estado_periodo == "PRELIMINAR" and estado_insumo == "PENDIENTE"
        
        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else '',
            dense=True, width=80, text_size=13, content_padding=10,
            disabled=not habilitar_txt_ajuste
        )

        btn_ajuste = ft.ElevatedButton(
            'Ingresar Ajuste', 
            icon=ft.icons.TUNE, 
            disabled=not habilitar_txt_ajuste,
            on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value)
        )

        btn_aceptar_sistema = ft.TextButton(
            text="Aceptar",
            icon=ft.icons.CHECK,
            icon_color="green",
            tooltip="Aceptar Stock del Sistema",
            style=ft.ButtonStyle(padding=ft.padding.all(5)),
            disabled=not habilitar_aceptar,
            on_click=lambda e, i_id=id_auditoria: self.procesar_aceptar_sistema(i_id)
        )

        acciones = ft.Row([btn_aceptar_sistema, btn_ajuste], spacing=5)

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Container(width=25)), # Checkbox (vacio)
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
