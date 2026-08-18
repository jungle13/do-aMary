import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
import datetime
from calendar import monthrange
import threading

class InformesView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        self.save_pdf_picker = ft.FilePicker(on_result=self._save_pdf_result)
        self.save_excel_picker = ft.FilePicker(on_result=self._save_excel_result)
        
        # --- PANEL IZQUIERDO: CONSTRUCTOR DE INFORMES ---
        self.drop_tipo_informe = ft.Dropdown(
            label="Tipo de Informe",
            options=[
                ft.dropdown.Option("Valorización de Inventario"),
                ft.dropdown.Option("Informe de Compras"),
                ft.dropdown.Option("Informe de Ventas"),
                ft.dropdown.Option("Historial de Ajustes"),
                ft.dropdown.Option("Resumen de KPIs")
            ],
            value="Valorización de Inventario",
            dense=True, border_radius=8,
            height=38, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8)
        )
        
        self.drop_filtro_fecha = ft.Dropdown(
            label="Periodo",
            options=[
                ft.dropdown.Option("Día de Hoy"),
                ft.dropdown.Option("Mes Actual"),
                ft.dropdown.Option("Histórico Completo")
            ],
            value="Histórico Completo",
            dense=True, border_radius=8,
            height=38, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8)
        )
        
        self.opcion_detalle = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="Completo", label="Completo"),
                ft.Radio(value="Resumido", label="Resumido")
            ]),
            value="Completo"
        )
        
        self.btn_generar = ft.ElevatedButton(
            "Generar Previsualización", 
            icon=ft.icons.PLAY_ARROW, 
            bgcolor=Config.COLOR_PRIMARY, 
            color="white",
            on_click=self.generar_informe,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        self.btn_pdf = ft.OutlinedButton("Exportar a PDF", icon=ft.icons.PICTURE_AS_PDF, icon_color="red", on_click=self.exportar_pdf)
        self.btn_excel = ft.OutlinedButton("Exportar a Excel", icon=ft.icons.TABLE_VIEW, icon_color="green", on_click=self.exportar_excel)
        
        panel_controles = ft.Container(
            content=ft.Column([
                ft.Text("Parámetros del Informe", weight="bold", color=Config.COLOR_PRIMARY),
                ft.Divider(height=1, color="#eeeeee"),
                self.drop_tipo_informe,
                self.drop_filtro_fecha,
                ft.Text("Nivel de Detalle", size=12, color="grey"),
                self.opcion_detalle,
                ft.Container(height=10),
                self.btn_generar,
                ft.Divider(height=20, color="transparent"),
                ft.Text("Exportación", weight="bold", color=Config.COLOR_PRIMARY),
                ft.Divider(height=1, color="#eeeeee"),
                self.btn_pdf,
                self.btn_excel
            ], spacing=15),
            bgcolor="white", padding=20, border_radius=8, width=300,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        # --- PANEL DERECHO: LIENZO DEL DOCUMENTO (A4) ---
        self.doc_header_empresa = ft.Text("TIENDA Y ABARROTES LOS DESECHABLES DE DOÑA MARY SAS", weight="bold", size=16, text_align=ft.TextAlign.CENTER)
        self.doc_header_titulo = ft.Text("INFORME DE VALORIZACIÓN DE INVENTARIO", weight="bold", size=14, text_align=ft.TextAlign.CENTER)
        self.doc_header_periodo = ft.Text("Periodo: Histórico Completo", size=11, color="grey", text_align=ft.TextAlign.CENTER)
        self.doc_header_fecha = ft.Text(f"Fecha de Generación: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", size=11, color="grey", text_align=ft.TextAlign.CENTER)
        
        self.doc_cuerpo = ft.Column(spacing=5)
        
        self.lienzo_documento = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        self.doc_header_empresa,
                        self.doc_header_titulo,
                        self.doc_header_periodo,
                        self.doc_header_fecha
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=20)
                ),
                ft.Divider(height=2, color="black"),
                self.doc_cuerpo
            ]),
            bgcolor="white",
            padding=40,
            border_radius=5,
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=10, color=ft.colors.with_opacity(0.1, "black"))
        )
        
        scroll_lienzo = ft.Column([self.lienzo_documento], scroll=ft.ScrollMode.ALWAYS, expand=True)
        
        # --- ENSAMBLAJE FINAL ---
        self.content = ft.Row([
            panel_controles,
            scroll_lienzo
        ], expand=True, spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)

    def did_mount(self):
        if self.save_pdf_picker not in self.page.overlay:
            self.page.overlay.append(self.save_pdf_picker)
        if self.save_excel_picker not in self.page.overlay:
            self.page.overlay.append(self.save_excel_picker)

    def generar_informe(self, e):
        self.doc_cuerpo.controls.clear()
        self.doc_cuerpo.controls.append(ft.Container(content=ft.ProgressRing(), alignment=ft.alignment.center, padding=50))
        if self.page: self.page.update()
        threading.Thread(target=self._worker_generar_informe, daemon=True).start()

    def _worker_generar_informe(self):
        tipo_informe = self.drop_tipo_informe.value
        detalle = self.opcion_detalle.value
        periodo_filtro = self.drop_filtro_fecha.value

        # 1. Cálculo del Rango de Fechas
        hoy = datetime.date.today()
        if periodo_filtro == "Día de Hoy":
            fecha_inicio = hoy.strftime("%Y-%m-%d")
            fecha_fin = hoy.strftime("%Y-%m-%d")
        elif periodo_filtro == "Mes Actual":
            fecha_inicio = hoy.replace(day=1).strftime("%Y-%m-%d")
            ultimo_dia = monthrange(hoy.year, hoy.month)[1]
            fecha_fin = hoy.replace(day=ultimo_dia).strftime("%Y-%m-%d")
        else:
            # Histórico Completo
            fecha_inicio = "2000-01-01"
            fecha_fin = "2100-12-31"

        # 2. Actualizar Cabecera del Documento
        self.doc_header_titulo.value = f"INFORME DE {tipo_informe.upper()}"
        self.doc_header_periodo.value = f"Periodo: {fecha_inicio} al {fecha_fin} | Tipo: {detalle}"
        self.doc_header_fecha.value = f"Fecha de Generación: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}"

        self.doc_cuerpo.controls.clear()

        # 3. Enrutador según el tipo de informe
        if tipo_informe == "Valorización de Inventario":
            self._generar_valorizacion(detalle, fecha_corte=fecha_fin if periodo_filtro != "Histórico Completo" else None)
        elif tipo_informe == "Informe de Compras":
            self._generar_compras(fecha_inicio, fecha_fin, detalle)
        elif tipo_informe == "Informe de Ventas":
            self._generar_ventas(fecha_inicio, fecha_fin, detalle)
        elif tipo_informe == "Historial de Ajustes":
            self._generar_ajustes(fecha_inicio, fecha_fin, detalle)
        elif tipo_informe == "Resumen de KPIs":
            self._generar_kpis(fecha_inicio, fecha_fin)

        if self.page:
            self.page.update()

    def _generar_valorizacion(self, detalle, fecha_corte=None):
        # Obtener datos calculados desde la base de datos
        data, _ = self.db.get_insumos(page=1, page_size=100000, fecha_corte=fecha_corte)

        if not data:
            self.doc_cuerpo.controls.append(
                ft.Container(content=ft.Text("No hay datos para los filtros seleccionados.", size=14, color="grey"), padding=30, alignment=ft.alignment.center)
            )
            self.current_data = {}
            self.current_total = 0
            return

        agrupacion = {}
        gran_total_costo = 0.0
        gran_total_cant = 0.0

        for item in data:
            cat = (item.get("categoria") or "SIN CATEGORIA").strip().upper()
            stock_real = float(item.get("stock_actual") or item.get("stock_real") or 0)
            costo_u = float(item.get("costo_unitario") or 0)
            
            # REGLA DE NEGOCIO: Un informe de valorización evalúa existencias reales.
            # Saldos negativos (ventas sin compra ingresada) se evalúan en 0 para evitar cantidades negativas y '$-0.00'.
            stock_val = max(0.0, stock_real)
            costo_total = stock_val * costo_u

            # Solo se valoran ítems con existencia disponible real
            if stock_val > 0 and costo_total > 0:
                if cat not in agrupacion:
                    agrupacion[cat] = {"items": [], "subtotal": 0.0, "cant_total": 0.0}

                agrupacion[cat]["items"].append({
                    "codigo": item.get("codigo_insumo"),
                    "nombre": item.get("nombre"),
                    "stock": stock_val,
                    "costo_u": costo_u,
                    "total": costo_total
                })
                agrupacion[cat]["subtotal"] += costo_total
                agrupacion[cat]["cant_total"] += stock_val
                gran_total_costo += costo_total
                gran_total_cant += stock_val

        # Guardar en memoria para exportación PDF/Excel
        self.current_data = agrupacion
        self.current_total = gran_total_costo
        self.current_periodo = self.doc_header_periodo.value

        if detalle == "Resumido":
            self._dibujar_resumido(agrupacion, "CATEGORÍA", gran_total_costo, gran_total_cant, "GRAN TOTAL VALORIZACIÓN")
        else:
            self.doc_cuerpo.controls.append(
                ft.Row([
                    ft.Text("CÓDIGO", weight="bold", size=11, width=60),
                    ft.Text("INSUMO", weight="bold", size=11, expand=True),
                    ft.Text("CANT.", weight="bold", size=11, width=60, text_align=ft.TextAlign.RIGHT),
                    ft.Text("COSTO U.", weight="bold", size=11, width=80, text_align=ft.TextAlign.RIGHT),
                    ft.Text("TOTAL", weight="bold", size=11, width=100, text_align=ft.TextAlign.RIGHT),
                ])
            )
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))

            for cat, datos_cat in sorted(agrupacion.items()):
                self.doc_cuerpo.controls.append(
                    ft.Container(content=ft.Text(f"GRUPO: {cat.upper()}", weight="bold", size=12, color=Config.COLOR_PRIMARY), padding=ft.padding.only(top=10, bottom=5))
                )
                for i in sorted(datos_cat["items"], key=lambda x: x["nombre"]):
                    self.doc_cuerpo.controls.append(
                        ft.Row([
                            ft.Text(i['codigo'], size=11, width=60),
                            ft.Text(i['nombre'], size=11, expand=True, no_wrap=True),
                            ft.Text(f"{i['stock']:g}", size=11, width=60, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"${i['costo_u']:,.2f}", size=11, width=80, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"${i['total']:,.2f}", size=11, width=100, text_align=ft.TextAlign.RIGHT),
                        ])
                    )
                self.doc_cuerpo.controls.append(
                    ft.Row([
                        ft.Text(f"Total {cat}:", weight="bold", size=11, expand=True, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"${datos_cat['subtotal']:,.2f}", weight="bold", size=12, width=100, text_align=ft.TextAlign.RIGHT),
                    ])
                )
                self.doc_cuerpo.controls.append(ft.Divider(height=1, color="#eeeeee"))

            self.doc_cuerpo.controls.append(ft.Divider(height=2, color="black"))
            self.doc_cuerpo.controls.append(
                ft.Row([
                    ft.Text("GRAN TOTAL VALORIZACIÓN:", weight="bold", size=14, expand=True, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"${gran_total_costo:,.2f}", weight="bold", size=14, width=150, text_align=ft.TextAlign.RIGHT),
                ])
            )
            self.doc_cuerpo.controls.append(ft.Divider(height=4, color="black"))

    def _generar_compras(self, fecha_inicio, fecha_fin, detalle):
        data, _ = self.db.get_compras(page=1, page_size=10000)
        agrupacion = {}
        gran_total = 0.0
        gran_total_cant = 0.0

        for item in data:
            fecha = item.get("fecha", "")[:10]
            if not (fecha_inicio <= fecha <= fecha_fin): continue

            proveedor = item.get("proveedor", "Desconocido")
            costo_total = float(item.get("costo_total") or 0)
            cant = float(item.get("cantidad", 0))

            if proveedor not in agrupacion:
                agrupacion[proveedor] = {"items": [], "subtotal": 0.0, "cant_total": 0.0}

            agrupacion[proveedor]["items"].append({
                "fecha": fecha,
                "factura": item.get("numero_factura", ""),
                "insumo": item.get("catalogo_insumos", {}).get("nombre", ""),
                "cant": cant,
                "total": costo_total
            })
            agrupacion[proveedor]["subtotal"] += costo_total
            agrupacion[proveedor]["cant_total"] += cant
            gran_total += costo_total
            gran_total_cant += cant

        self.current_data = agrupacion
        self.current_total = gran_total
        self.current_periodo = self.doc_header_periodo.value

        if detalle == "Resumido":
            self._dibujar_resumido(agrupacion, "PROVEEDOR", gran_total, gran_total_cant)
        else:
            self._dibujar_tabla_financiera(agrupacion, "PROVEEDOR", gran_total, ["FECHA", "FACTURA", "INSUMO", "CANT.", "TOTAL"])

    def _generar_ventas(self, fecha_inicio, fecha_fin, detalle):
        data, _ = self.db.get_ventas(page=1, page_size=10000)
        agrupacion = {}
        gran_total = 0.0
        gran_total_cant = 0.0

        for item in data:
            fecha = item.get("fecha", "")[:10]
            if not (fecha_inicio <= fecha <= fecha_fin): continue

            cat = item.get("catalogo_insumos", {}).get("categoria", "SIN CATEGORIA")
            
            if cat not in agrupacion:
                agrupacion[cat] = {"items": [], "subtotal": 0.0, "cant_total": 0.0}

            total = float(item.get("total") or 0)
            cant = float(item.get("cantidad", 0))
            agrupacion[cat]["items"].append({
                "fecha": fecha,
                "factura": item.get("factura_no", ""),
                "insumo": item.get("descripcion") or item.get("catalogo_insumos", {}).get("nombre", ""),
                "cant": cant,
                "total": total
            })
            agrupacion[cat]["subtotal"] += total
            agrupacion[cat]["cant_total"] += cant
            gran_total += total
            gran_total_cant += cant

        self.current_data = agrupacion
        self.current_total = gran_total
        self.current_periodo = self.doc_header_periodo.value

        if detalle == "Resumido":
            self._dibujar_resumido(agrupacion, "CATEGORÍA", gran_total, gran_total_cant)
        else:
            self._dibujar_tabla_financiera(agrupacion, "CATEGORÍA", gran_total, ["FECHA", "FACTURA", "INSUMO", "CANT.", "INGRESOS"])

    def _generar_ajustes(self, fecha_inicio, fecha_fin, detalle):
        data = self.db.get_ajustes_inventario()
        agrupacion = {}
        gran_total_neto = 0.0
        gran_total_cant = 0.0

        for item in data:
            if item.get("estado_registro") != "VÁLIDO": continue

            fecha = item.get("fecha_ajuste", "")[:10]
            if not (fecha_inicio <= fecha <= fecha_fin): continue

            tipo = "ENTRADAS (+)" if item.get("tipo_ajuste") in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE') else "SALIDAS (-)"
            if tipo not in agrupacion:
                agrupacion[tipo] = {"items": [], "subtotal": 0.0, "cant_total": 0.0}

            costo = float(item.get("costo_total_ajuste") or 0)
            cant = float(item.get("cantidad", 0))

            raw_motivo = item.get("motivo", "")
            raw_obs = item.get("observacion", "") or item.get("observaciones", "")
            if not raw_motivo and item.get("motivo_observacion"):
                partes = item.get("motivo_observacion").split("]", 1)
                raw_motivo = partes[0].replace("[", "").strip() if len(partes) > 1 else item.get("motivo_observacion")
                raw_obs = partes[1].strip() if len(partes) > 1 else ""

            agrupacion[tipo]["items"].append({
                "fecha": fecha,
                "motivo": raw_motivo,
                "obs": raw_obs,
                "insumo": item.get("catalogo_insumos", {}).get("nombre", ""),
                "cant": cant,
                "total": costo
            })
            agrupacion[tipo]["subtotal"] += costo
            agrupacion[tipo]["cant_total"] += cant
            gran_total_neto += costo if tipo == "ENTRADAS (+)" else -costo
            gran_total_cant += cant if tipo == "ENTRADAS (+)" else -cant

        self.current_data = agrupacion
        self.current_total = gran_total_neto
        self.current_periodo = self.doc_header_periodo.value

        if detalle == "Resumido":
            self._dibujar_resumido(agrupacion, "TIPO DE AJUSTE", gran_total_neto, gran_total_cant, "IMPACTO NETO")
        else:
            self._dibujar_tabla_financiera(agrupacion, "TIPO DE AJUSTE", gran_total_neto, ["FECHA", "MOTIVO", "OBSERVACIÓN", "INSUMO", "CANT.", "COSTO TOTAL"], label_gran_total="IMPACTO NETO", is_ajuste=True)

    def _dibujar_resumido(self, agrupacion, label_grupo, gran_total_val, gran_total_cant=0, label_gran_total="GRAN TOTAL"):
        self.doc_cuerpo.controls.append(ft.Row([
            ft.Text(label_grupo, weight="bold", size=11, expand=True),
            ft.Text("CANT. TOTAL", weight="bold", size=11, width=100, text_align=ft.TextAlign.RIGHT),
            ft.Text("VALOR TOTAL", weight="bold", size=11, width=120, text_align=ft.TextAlign.RIGHT),
        ]))
        self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))

        for grupo, datos in sorted(agrupacion.items()):
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text(grupo.upper(), size=11, expand=True, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text(f"{datos.get('cant_total', 0):g}", size=11, width=100, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"${datos['subtotal']:,.2f}", size=11, width=120, text_align=ft.TextAlign.RIGHT),
            ]))
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="#eeeeee"))

        self.doc_cuerpo.controls.append(ft.Divider(height=2, color="black"))
        color_total = "red" if gran_total_val < 0 else "black"
        self.doc_cuerpo.controls.append(ft.Row([
            ft.Text(f"{label_gran_total}:", weight="bold", size=14, expand=True, text_align=ft.TextAlign.RIGHT),
            ft.Text(f"{gran_total_cant:g}", weight="bold", size=14, width=100, text_align=ft.TextAlign.RIGHT),
            ft.Text(f"${gran_total_val:,.2f}", weight="bold", size=14, width=120, text_align=ft.TextAlign.RIGHT, color=color_total),
        ]))

    def _dibujar_tabla_financiera(self, agrupacion, label_grupo, gran_total, headers, label_gran_total="GRAN TOTAL", is_ajuste=False):
        if not agrupacion:
            self.doc_cuerpo.controls.append(ft.Container(content=ft.Text("No hay datos para los filtros seleccionados.", size=14, color="grey"), padding=30, alignment=ft.alignment.center))
            return

        # Cabeceras
        if is_ajuste:
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text(headers[0], weight="bold", size=11, width=65),
                ft.Text(headers[1], weight="bold", size=11, width=90),
                ft.Text(headers[2], weight="bold", size=11, expand=True),
                ft.Text(headers[3], weight="bold", size=11, width=100),
                ft.Text(headers[4], weight="bold", size=11, width=45, text_align=ft.TextAlign.RIGHT),
                ft.Text(headers[5], weight="bold", size=11, width=70, text_align=ft.TextAlign.RIGHT),
            ]))
        else:
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text(headers[0], weight="bold", size=11, width=70),
                ft.Text(headers[1], weight="bold", size=11, width=90),
                ft.Text(headers[2], weight="bold", size=11, expand=True),
                ft.Text(headers[3], weight="bold", size=11, width=60, text_align=ft.TextAlign.RIGHT),
                ft.Text(headers[4], weight="bold", size=11, width=100, text_align=ft.TextAlign.RIGHT),
            ]))
        self.doc_cuerpo.controls.append(ft.Divider(height=1, color="black"))

        for grupo, datos in sorted(agrupacion.items()):
            self.doc_cuerpo.controls.append(ft.Container(content=ft.Text(f"{label_grupo}: {grupo.upper()}", weight="bold", size=12, color=Config.COLOR_PRIMARY), padding=ft.padding.only(top=10, bottom=5)))
            for i in datos["items"]:
                if is_ajuste:
                    fila_ui = ft.Row([
                        ft.Text(i['fecha'], size=11, width=65),
                        ft.Text(i['motivo'], size=11, width=90, no_wrap=True, weight="bold"),
                        ft.Text(i['obs'], size=11, expand=True), # Observación toma el espacio restante
                        ft.Text(i['insumo'], size=11, width=100, no_wrap=True),
                        ft.Text(f"{i['cant']:g}", size=11, width=45, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"${i['total']:,.2f}", size=11, width=70, text_align=ft.TextAlign.RIGHT),
                    ])
                else:
                    fila_ui = ft.Row([
                        ft.Text(i['fecha'], size=11, width=70),
                        ft.Text(i['factura'], size=11, width=90, no_wrap=True),
                        ft.Text(i['insumo'], size=11, expand=True, no_wrap=True),
                        ft.Text(f"{i['cant']:g}", size=11, width=60, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"${i['total']:,.2f}", size=11, width=100, text_align=ft.TextAlign.RIGHT),
                    ])
                self.doc_cuerpo.controls.append(fila_ui)
            self.doc_cuerpo.controls.append(ft.Row([
                ft.Text(f"Total {grupo}:", weight="bold", size=11, expand=True, text_align=ft.TextAlign.RIGHT),
                ft.Text(f"${datos['subtotal']:,.2f}", weight="bold", size=12, width=100, text_align=ft.TextAlign.RIGHT),
            ]))
            self.doc_cuerpo.controls.append(ft.Divider(height=1, color="#eeeeee"))

        self.doc_cuerpo.controls.append(ft.Divider(height=2, color="black"))
        color_total = "red" if gran_total < 0 else "black"
        self.doc_cuerpo.controls.append(ft.Row([
            ft.Text(f"{label_gran_total}:", weight="bold", size=14, expand=True, text_align=ft.TextAlign.RIGHT),
            ft.Text(f"${gran_total:,.2f}", weight="bold", size=14, width=150, text_align=ft.TextAlign.RIGHT, color=color_total),
        ]))
        self.doc_cuerpo.controls.append(ft.Divider(height=4, color="black"))

    def _generar_kpis(self, fecha_inicio, fecha_fin):
        # Como los KPIs son un resumen global dictado por los métodos SQL actuales (que operan por mes/hoy)
        # Mostraremos la foto actual del sistema independientemente del filtro de fechas (con una advertencia visual)

        res_cat = self.db.get_catalogo_summary()
        res_ven = self.db.get_ventas_summary()
        res_com = self.db.get_compras_summary()
        kpis_inv = self.db.get_inventario_kpis()

        val_inv = kpis_inv.get('valor_inventario', 0)
        ingresos = float(res_ven.get('total_mes') or 0)
        compras = float(res_com.get('total_mes') or 0)

        rentabilidad = ((ingresos - compras) / ingresos) * 100 if ingresos > 0 else 0
        rotacion = ingresos / val_inv if val_inv > 0 else 0

        def _crear_kpi_fila(label, valor, color="black"):
            return ft.Row([
                ft.Text(label, size=13, expand=True),
                ft.Text(valor, size=14, weight="bold", color=color, width=150, text_align=ft.TextAlign.RIGHT)
            ])

        self.doc_cuerpo.controls.extend([
            ft.Container(content=ft.Text("NOTA: Este resumen muestra el estado actual del MES EN CURSO según las métricas del Dashboard, independientemente del filtro de fechas seleccionado.", size=10, color="orange", italic=True), padding=10, bgcolor="#fff3cd", border_radius=5),
            ft.Divider(height=10, color="transparent"),
            ft.Text("MÉTRICAS DE INVENTARIO Y COSTOS", weight="bold", size=14, color=Config.COLOR_PRIMARY),
            ft.Divider(height=1, color="black"),
            _crear_kpi_fila("Valorización Actual del Inventario", f"${val_inv:,.2f}"),
            _crear_kpi_fila("Total Compras (Mes Actual)", f"${compras:,.2f}"),
            ft.Divider(height=20, color="transparent"),
            ft.Text("MÉTRICAS DE VENTAS E INGRESOS", weight="bold", size=14, color=Config.COLOR_PRIMARY),
            ft.Divider(height=1, color="black"),
            _crear_kpi_fila("Total Ventas (Mes Actual)", f"${ingresos:,.2f}", "green"),
            _crear_kpi_fila("IVA Recaudado (Mes Actual)", f"${res_ven.get('iva_mes', 0):,.2f}"),
            ft.Divider(height=20, color="transparent"),
            ft.Text("RENDIMIENTO FINANCIERO (MES ACTUAL)", weight="bold", size=14, color=Config.COLOR_PRIMARY),
            ft.Divider(height=1, color="black"),
            _crear_kpi_fila("Margen de Rentabilidad Bruta", f"{rentabilidad:.1f}%", "green" if rentabilidad >= 0 else "red"),
            _crear_kpi_fila("Índice de Rotación", f"{rotacion:.2f}x"),
            ft.Divider(height=4, color="black")
        ])

    def exportar_pdf(self, e):
        if not hasattr(self, 'current_data') or not self.current_data:
            self.page.snack_bar = ft.SnackBar(ft.Text("Primero genera la previsualización del informe."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        nombre_sugerido = f"{self.drop_tipo_informe.value.replace(' ', '_')}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
        self.save_pdf_picker.save_file(
            dialog_title="Guardar Informe PDF",
            file_name=nombre_sugerido,
            allowed_extensions=["pdf"]
        )

    def _save_pdf_result(self, e: ft.FilePickerResultEvent):
        if not e.path:
            return
            
        try:
            from fpdf import FPDF
            
            class PDFReport(FPDF):
                def header(instance):
                    instance.set_font("Arial", 'B', 12)
                    instance.cell(0, 6, "TIENDA Y ABARROTES LOS DESECHABLES DE DOÑA MARY SAS", ln=True, align='C')
                    instance.set_font("Arial", 'B', 10)
                    instance.cell(0, 5, "REPORTE OFICIAL DE INVENTARIOS Y OPERACIONES", ln=True, align='C')
                    instance.set_font("Arial", '', 8)
                    instance.cell(0, 4, f"Generado el: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}", ln=True, align='C')
                    instance.ln(4)
                    instance.line(10, instance.get_y(), 200, instance.get_y())
                    instance.ln(4)

                def footer(instance):
                    instance.set_y(-15)
                    instance.set_font("Arial", 'I', 8)
                    instance.cell(0, 10, f"Página {instance.page_no()}/{{nb}}", align='C')

            pdf = PDFReport()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Título del Informe
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 6, str(self.doc_header_titulo.value).encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 5, str(self.doc_header_periodo.value).encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.ln(4)

            es_resumido = self.opcion_detalle.value == "Resumido"
            es_ajuste = self.drop_tipo_informe.value == "Historial de Ajustes"

            if es_resumido:
                # Tabla Resumida
                pdf.set_font("Arial", 'B', 8)
                pdf.cell(110, 6, "GRUPO / CATEGORIA", border=1)
                pdf.cell(35, 6, "CANT. TOTAL", border=1, align='R')
                pdf.cell(45, 6, "VALOR TOTAL", border=1, align='R')
                pdf.ln()

                pdf.set_font("Arial", '', 8)
                for grupo, datos in sorted(self.current_data.items()):
                    g_nombre = str(grupo).upper().encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(110, 6, g_nombre, border="L,R,B")
                    pdf.cell(35, 6, f"{datos.get('cant_total', 0):g}", border="L,R,B", align='R')
                    pdf.cell(45, 6, f"${datos['subtotal']:,.2f}", border="L,R,B", align='R', ln=True)

                pdf.ln(4)
                pdf.set_font("Arial", 'B', 9)
                pdf.cell(145, 7, "TOTAL GENERAL:", align='R')
                pdf.cell(45, 7, f"${self.current_total:,.2f}", border=1, align='R', ln=True)

            else:
                # Tabla Completa
                pdf.set_font("Arial", 'B', 8)
                if es_ajuste:
                    pdf.cell(20, 6, "FECHA", border=1)
                    pdf.cell(30, 6, "MOTIVO", border=1)
                    pdf.cell(50, 6, "OBSERVACION", border=1)
                    pdf.cell(45, 6, "INSUMO", border=1)
                    pdf.cell(20, 6, "CANT.", border=1, align='R')
                    pdf.cell(25, 6, "COSTO TOT.", border=1, align='R')
                else:
                    pdf.cell(20, 6, "FECHA/COD", border=1)
                    pdf.cell(30, 6, "DOC/FACT", border=1)
                    pdf.cell(75, 6, "INSUMO / DESCRIPCION", border=1)
                    pdf.cell(20, 6, "CANT.", border=1, align='R')
                    pdf.cell(20, 6, "COSTO U.", border=1, align='R')
                    pdf.cell(25, 6, "TOTAL", border=1, align='R')
                pdf.ln()

                for grupo, datos in sorted(self.current_data.items()):
                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(0, 6, f"  GRUPO: {str(grupo).upper().encode('latin-1', 'replace').decode('latin-1')}", border="L,R,B", ln=True)
                    pdf.set_font("Arial", '', 7)

                    for i in datos["items"]:
                        insumo_txt = str(i.get('insumo') or i.get('nombre', '')).encode('latin-1', 'replace').decode('latin-1')[:35]
                        
                        if es_ajuste:
                            motivo_txt = str(i.get('motivo', '')).encode('latin-1', 'replace').decode('latin-1')[:18]
                            obs_txt = str(i.get('obs', '')).encode('latin-1', 'replace').decode('latin-1')[:30]
                            pdf.cell(20, 5, str(i.get('fecha', '')), border="L")
                            pdf.cell(30, 5, motivo_txt)
                            pdf.cell(50, 5, obs_txt)
                            pdf.cell(45, 5, insumo_txt)
                            pdf.cell(20, 5, f"{i.get('cant', 0):g}", align='R')
                            pdf.cell(25, 5, f"${i.get('total', 0):,.2f}", border="R", align='R', ln=True)
                        else:
                            c_code = str(i.get('codigo') or i.get('fecha', ''))
                            c_doc = str(i.get('factura', ''))[:15]
                            c_u = f"${i.get('costo_u', 0):,.2f}" if 'costo_u' in i else "-"
                            pdf.cell(20, 5, c_code, border="L")
                            pdf.cell(30, 5, c_doc)
                            pdf.cell(75, 5, insumo_txt)
                            pdf.cell(20, 5, f"{i.get('stock', i.get('cant', 0)):g}", align='R')
                            pdf.cell(20, 5, c_u, align='R')
                            pdf.cell(25, 5, f"${i.get('total', 0):,.2f}", border="R", align='R', ln=True)

                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(165, 5, f"Subtotal {grupo}:", border="L,B", align='R')
                    pdf.cell(25, 5, f"${datos['subtotal']:,.2f}", border="R,B", align='R', ln=True)

                pdf.ln(4)
                pdf.set_font("Arial", 'B', 9)
                pdf.cell(165, 7, "TOTAL GENERAL:", align='R')
                pdf.cell(25, 7, f"${self.current_total:,.2f}", border=1, align='R', ln=True)

            pdf.output(e.path)
            self.page.snack_bar = ft.SnackBar(ft.Text("¡PDF exportado con éxito!"), bgcolor="green")
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error al generar PDF: {ex}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    def exportar_excel(self, e):
        nombre_sugerido = f"Inventario_Consolidado_Dona_Mary_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
        self.save_excel_picker.save_file(
            dialog_title="Guardar Consolidado Excel",
            file_name=nombre_sugerido,
            allowed_extensions=["xlsx"]
        )

    def _save_excel_result(self, e: ft.FilePickerResultEvent):
        if not e.path:
            return
            
        self.page.snack_bar = ft.SnackBar(ft.Text("Generando consolidado Excel en segundo plano..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()
        
        threading.Thread(target=self._worker_generar_excel, args=(e.path,), daemon=True).start()

    def _worker_generar_excel(self, file_path):
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            # 1. Obtener datos completos de la base de datos sin filtros
            raw_inv, _ = self.db.get_insumos(page=1, page_size=999999)
            raw_compras, _ = self.db.get_compras(page=1, page_size=999999)
            raw_ventas, _ = self.db.get_ventas(page=1, page_size=999999)
            raw_ajustes = self.db.get_ajustes_inventario() or []

            wb = openpyxl.Workbook()
            wb.remove(wb.active) # Eliminar hoja por defecto

            # Estilos generales
            fill_header = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
            font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            font_title = Font(name="Calibri", size=14, bold=True, color="1B365D")
            font_sub = Font(name="Calibri", size=10, italic=True, color="555555")
            border_thin = Border(
                left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
                top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC')
            )
            num_fmt_curr = '"$"#,##0.00'
            num_fmt_qty = '#,##0'

            fecha_emision = datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p")
            nombre_empresa = "TIENDA Y ABARROTES LOS DESECHABLES DE DOÑA MARY SAS"

            def agregar_encabezado(ws, titulo):
                ws['A1'] = nombre_empresa
                ws['A1'].font = font_title
                ws['A2'] = f"CONSOLIDADO SISTEMA: {titulo.upper()}"
                ws['A2'].font = Font(name="Calibri", size=12, bold=True)
                ws['A3'] = f"Fecha de emisión: {fecha_emision} | Datos acumulados sin filtros"
                ws['A3'].font = font_sub

            # ----------------------------------------------------
            # HOJA 1: COMPRAS
            # ----------------------------------------------------
            ws_c = wb.create_sheet(title="Compras")
            agregar_encabezado(ws_c, "Detalle de Registro de Compras")
            ws_c.append([])
            ws_c.append(["Fecha", "Código Insumo", "Nombre Insumo", "Factura / Documento", "Cantidad", "Costo Total"])

            for r_idx, c in enumerate(raw_compras, start=6):
                cat_i = c.get("catalogo_insumos") or {}
                ws_c.cell(row=r_idx, column=1, value=str(c.get("fecha", ""))[:10])
                ws_c.cell(row=r_idx, column=2, value=str(c.get("codigo_insumo", "")))
                ws_c.cell(row=r_idx, column=3, value=cat_i.get("nombre", "Desconocido"))
                ws_c.cell(row=r_idx, column=4, value=str(c.get("numero_factura") or c.get("numero_entrada") or ""))
                ws_c.cell(row=r_idx, column=5, value=float(c.get("cantidad") or 0))
                ws_c.cell(row=r_idx, column=6, value=float(c.get("costo_total") or 0))

            # ----------------------------------------------------
            # HOJA 2: VENTAS
            # ----------------------------------------------------
            ws_v = wb.create_sheet(title="Ventas")
            agregar_encabezado(ws_v, "Detalle de Registro de Ventas")
            ws_v.append([])
            ws_v.append(["Fecha", "Código Insumo", "Nombre Insumo", "Comprobante / Pedido", "Cantidad", "Ingreso Total"])

            for r_idx, v in enumerate(raw_ventas, start=6):
                cat_i = v.get("catalogo_insumos") or {}
                ws_v.cell(row=r_idx, column=1, value=str(v.get("fecha", ""))[:10])
                ws_v.cell(row=r_idx, column=2, value=str(v.get("codigo_insumo", "")))
                ws_v.cell(row=r_idx, column=3, value=cat_i.get("nombre") or v.get("descripcion") or "Desconocido")
                ws_v.cell(row=r_idx, column=4, value=str(v.get("factura_no", "")))
                ws_v.cell(row=r_idx, column=5, value=float(v.get("cantidad") or 0))
                ws_v.cell(row=r_idx, column=6, value=float(v.get("total") or 0))

            # ----------------------------------------------------
            # HOJA 3: AJUSTES
            # ----------------------------------------------------
            ws_a = wb.create_sheet(title="Ajustes")
            agregar_encabezado(ws_a, "Detalle de Ajustes de Inventario")
            ws_a.append([])
            ws_a.append(["Fecha", "Código Insumo", "Nombre Insumo", "Tipo", "Cantidad", "Motivo"])

            for r_idx, a in enumerate(raw_ajustes, start=6):
                if a.get("estado_registro") != "VÁLIDO": continue
                cat_i = a.get("catalogo_insumos") or {}
                es_ent = a.get("tipo_ajuste") in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
                
                ws_a.cell(row=r_idx, column=1, value=str(a.get("fecha_ajuste", ""))[:10])
                ws_a.cell(row=r_idx, column=2, value=str(a.get("codigo_insumo", "")))
                ws_a.cell(row=r_idx, column=3, value=cat_i.get("nombre", "Desconocido"))
                ws_a.cell(row=r_idx, column=4, value="Entrada" if es_ent else "Salida")
                ws_a.cell(row=r_idx, column=5, value=float(a.get("cantidad") or 0))
                ws_a.cell(row=r_idx, column=6, value=str(a.get("motivo_observacion", "")))

            # ----------------------------------------------------
            # HOJA 4: INVENTARIO (HOJA MAESTRA CON FÓRMULAS)
            # ----------------------------------------------------
            ws_inv = wb.create_sheet(title="Inventario")
            agregar_encabezado(ws_inv, "Catálogo General de Inventario y Valorización Formulado")
            ws_inv.append([])
            
            headers_inv = [
                "Código", "Nombre", "Categoría", "Ubicación", "Stock Inicial",
                "Entradas", "Costo Entradas", "Salidas", "Ingresos por Salidas",
                "Stock Actual", "Costo del Stock Actual", "Proyección Ingresos Stock Actual",
                "Precio de Venta del Sistema", "Costo Unitario del Sistema",
                "Ajustes Entradas", "Ajustes Salidas", "Costo Ajustes Entradas", "Ingresos Ajustes Salidas"
            ]
            ws_inv.append(headers_inv)

            for idx, i in enumerate(raw_inv, start=6):
                code = str(i.get("codigo_insumo", ""))
                
                # Datos estáticos base
                ws_inv.cell(row=idx, column=1, value=code) # A
                ws_inv.cell(row=idx, column=2, value=str(i.get("nombre", ""))) # B
                ws_inv.cell(row=idx, column=3, value=str(i.get("categoria", ""))) # C
                ws_inv.cell(row=idx, column=4, value=str(i.get("ubicacion") or "N/A")) # D
                ws_inv.cell(row=idx, column=5, value=float(i.get("stock_inicial") or 0)) # E

                # Fórmulas SUMIF sobre Compras y Ventas
                ws_inv.cell(row=idx, column=6, value=f'=SUMIF(Compras!B:B, A{idx}, Compras!E:E)') # F: Entradas
                ws_inv.cell(row=idx, column=7, value=f'=SUMIF(Compras!B:B, A{idx}, Compras!F:F)') # G: Costo Entradas
                ws_inv.cell(row=idx, column=8, value=f'=SUMIF(Ventas!B:B, A{idx}, Ventas!E:E)') # H: Salidas
                ws_inv.cell(row=idx, column=9, value=f'=SUMIF(Ventas!B:B, A{idx}, Ventas!F:F)') # I: Ingresos Salidas

                # Precios/Costos Unitarios Maestros
                ws_inv.cell(row=idx, column=13, value=float(i.get("precio_venta") or 0)) # M: Precio Venta
                ws_inv.cell(row=idx, column=14, value=float(i.get("costo_unitario") or 0)) # N: Costo Unitario

                # Fórmulas SUMIFS sobre Ajustes
                ws_inv.cell(row=idx, column=15, value=f'=SUMIFS(Ajustes!E:E, Ajustes!B:B, A{idx}, Ajustes!D:D, "Entrada")') # O: Ajustes Entradas
                ws_inv.cell(row=idx, column=16, value=f'=SUMIFS(Ajustes!E:E, Ajustes!B:B, A{idx}, Ajustes!D:D, "Salida")') # P: Ajustes Salidas

                # Fórmulas de Totales en Inventario
                ws_inv.cell(row=idx, column=10, value=f'=E{idx}+F{idx}-H{idx}+O{idx}-P{idx}') # J: Stock Actual
                ws_inv.cell(row=idx, column=11, value=f'=J{idx}*N{idx}') # K: Costo Stock Actual
                ws_inv.cell(row=idx, column=12, value=f'=J{idx}*M{idx}') # L: Proyección Ingresos
                ws_inv.cell(row=idx, column=17, value=f'=O{idx}*N{idx}') # Q: Costo Ajustes Entradas
                ws_inv.cell(row=idx, column=18, value=f'=P{idx}*M{idx}') # R: Ingresos Ajustes Salidas

            # ----------------------------------------------------
            # APLICAR FORMATOS Y AUTOFIT A TODAS LAS HOJAS
            # ----------------------------------------------------
            for sheet in wb.worksheets:
                for cell in sheet[5]:
                    cell.fill = fill_header
                    cell.font = font_header
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

                for col in sheet.columns:
                    max_len = 0
                    col_letter = get_column_letter(col[0].column)
                    for cell in col:
                        if cell.row >= 5 and cell.value is not None:
                            max_len = max(max_len, len(str(cell.value)))
                            cell.border = border_thin

                        # Formatear números en la hoja Inventario
                        if sheet.title == "Inventario" and cell.row >= 6:
                            if col_letter in ["G", "I", "K", "L", "M", "N", "Q", "R"]:
                                cell.number_format = num_fmt_curr
                            elif col_letter in ["E", "F", "H", "J", "O", "P"]:
                                cell.number_format = num_fmt_qty
                        elif sheet.title in ["Compras", "Ventas"] and cell.row >= 6:
                            if col_letter == "F": cell.number_format = num_fmt_curr
                            elif col_letter == "E": cell.number_format = num_fmt_qty

                    sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

            wb.save(file_path)

            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("¡Consolidado Excel generado y formulado con éxito!"), bgcolor="green")
                self.page.snack_bar.open = True
                self.page.update()

        except Exception as ex:
            print(f"Error generando Excel: {ex}")
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error al generar Excel: {ex}"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
