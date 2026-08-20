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
            if not texto or not texto.strip():
                self.search_input_text.value = ""
            elif "[" in texto and "]" in texto:
                self.search_input_text.value = texto.split("]")[0].replace("[", "").strip()
            else:
                self.search_input_text.value = texto.strip()
            self.current_page = 1
            self._on_filter_change()

        self.search_input_text = ft.TextField(visible=False)

        self.search_filter_autocomplete = CustomAutoComplete(
            hint_text="Buscar por código o nombre...",
            on_select=on_select_filtro_ajustes,
            text_size=12,
            height=40,
            expand=True
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
            ft.Container(content=self.search_filter_autocomplete, expand=True),
            self.btn_date,
            self.btn_clear_date,
            self.drop_tipo,
            self.drop_motivo,
            self.btn_agregar_ajuste
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
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

        # Cargar catálogo para sugerencias inteligentes en el buscador desde el inicio
        try:
            insumos, _ = self.db.get_insumos(page=1, page_size=99999)
            self.catalogo_cache = {i["codigo_insumo"]: i for i in insumos}
            suggs = [
                {"key": i["codigo_insumo"], "value": f"[{i['codigo_insumo']}] {i['nombre']}"}
                for i in insumos
            ]
            self.txt_buscador_insumo.suggestions = suggs
            self.search_filter_autocomplete.suggestions = suggs
        except Exception:
            pass

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
        
        raw_auto = (self.search_filter_autocomplete.value or "").strip()
        if not raw_auto:
            filtro_texto = ""
            self.search_input_text.value = ""
        else:
            filtro_texto = (self.search_input_text.value or raw_auto).lower().strip()
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
