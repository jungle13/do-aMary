"""
Vista de Conteo e Inventario Inicial de Mes.
Permite registrar y calibrar existencias físicas y costos unitarios,
lanzar el modal de Conteo Móvil QR, y sincronizar con Supabase en tiempo real.
"""
import flet as ft
import datetime
import threading
from config import Config
from core.supabase_client import get_client
from core.mobile_service import MobileCountingService
from core.mobile_server import iniciar_servidor_en_hilo
from core.logger import get_logger, log_error

logger = get_logger("ConteoInicialView")

class ConteoInicialView(ft.Container):
    def __init__(self, mes_periodo: str = "2026-08", on_volver = None):
        super().__init__()
        self.expand = True
        self.db = get_client()
        self.mobile_service = MobileCountingService()

        # Estado
        self.mes_seleccionado = mes_periodo
        self.on_volver = on_volver
        self.periodo_activo_id = None
        self.periodos_map = {}
        self.catalogo_completo = []
        self.compras_recientes_cache = {}
        self.datos_tabla = []
        self.datos_filtrados = []
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.insumo_seleccionado = None

        # 1. Header
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        partes = self.mes_seleccionado.split('-')
        mes_idx = int(partes[1]) - 1 if len(partes) > 1 and partes[1].isdigit() else 7
        nombre_mes = meses[mes_idx] if 0 <= mes_idx < 12 else self.mes_seleccionado
        year_str = partes[0] if partes else "2026"

        self.lbl_titulo = ft.Text(f"Conteo y Stock Inicial • {nombre_mes} {year_str}", size=18, weight="bold", color=Config.COLOR_PRIMARY)

        self.badge_estado_periodo = ft.Container(
            content=ft.Row([
                ft.Container(width=8, height=8, bgcolor=Config.COLOR_SUCCESS, border_radius=4),
                ft.Text("ABIERTO", size=11, weight="bold", color=Config.COLOR_SUCCESS)
            ], spacing=6, tight=True),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            bgcolor=Config.COLOR_SUCCESS_BG,
            border_radius=12,
            border=ft.border.all(1, ft.colors.with_opacity(0.3, Config.COLOR_SUCCESS))
        )

        self.btn_qr_movil = ft.ElevatedButton(
            "📱 Conteo Móvil (QR)",
            icon=ft.icons.QR_CODE_SCANNER_ROUNDED,
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            height=32,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=7),
                padding=ft.padding.symmetric(horizontal=10, vertical=0)
            ),
            on_click=self.abrir_modal_qr
        )

        # 2. Tarjetas de Resumen KPI Compactas
        self.lbl_insumos_contados = ft.Text("0", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_total_stock = ft.Text("0 unds", size=14, weight="bold", color=Config.COLOR_ACCENT)
        self.lbl_valor_total = ft.Text("$0", size=14, weight="bold", color=Config.COLOR_SUCCESS)

        # 3. Formulario de Registro Rápido Compacto
        self.txt_buscar_insumo = ft.TextField(
            hint_text="Escribe código o nombre del insumo a registrar...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            bgcolor="white",
            border_radius=7,
            height=34,
            text_size=11.5,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            expand=True,
            on_change=self.on_buscar_sugerencias
        )

        self.lv_sugerencias = ft.ListView(
            spacing=2,
            height=110,
            visible=False
        )

        self.lbl_info_seleccionado = ft.Text("Ningún insumo seleccionado", size=10.5, color=Config.COLOR_TEXT_MUTED, weight="w500")
        
        self.txt_cantidad = ft.TextField(
            label="Cantidad Físico",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=7,
            height=34,
            text_size=11.5,
            width=135,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            text_align=ft.TextAlign.RIGHT
        )

        self.txt_costo = ft.TextField(
            label="Costo Unit. ($)",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor="white",
            border_radius=7,
            height=34,
            text_size=11.5,
            width=130,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            text_align=ft.TextAlign.RIGHT
        )

        self.lbl_fuente_costo = ft.Text("", size=9.5, color=Config.COLOR_ACCENT, weight="w600")

        self.btn_guardar_conteo = ft.ElevatedButton(
            "✓ Guardar Conteo",
            bgcolor=Config.COLOR_SUCCESS,
            color="white",
            height=34,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=7),
                padding=ft.padding.symmetric(horizontal=12, vertical=0)
            ),
            on_click=self.guardar_conteo_manual
        )

        # 4. Filtro de Tabla Compacto
        self.txt_filtro_tabla = ft.TextField(
            hint_text="Filtrar tabla por nombre o código...",
            prefix_icon=ft.icons.FILTER_ALT_ROUNDED,
            bgcolor="white",
            border_radius=7,
            height=34,
            text_size=11.5,
            expand=True,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=self.on_filtro_tabla_change
        )

        self.dd_categoria_tabla = ft.Dropdown(
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            label="Categoría",
            width=140,
            border_radius=7,
            bgcolor="white",
            height=34,
            text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_change=self.on_filtro_tabla_change
        )

        # 5. Tabla de Conteo Compacta
        self.tabla = ft.DataTable(
            column_spacing=10,
            data_row_min_height=32,
            data_row_max_height=36,
            heading_row_height=30,
            heading_row_color="#f1f5f9",
            border=ft.border.all(1, ft.colors.with_opacity(0.08, "black")),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Insumo", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Categoría", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Costo Unitario", weight="bold", size=11), numeric=True),
                ft.DataColumn(ft.Text("Stock Inicial", weight="bold", size=11), numeric=True),
                ft.DataColumn(ft.Text("Valor Total", weight="bold", size=11), numeric=True),
                ft.DataColumn(ft.Text("Estado", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Acciones", weight="bold", size=11)),
            ],
            rows=[]
        )

        # Paginador
        self.lbl_paginacion = ft.Text("Página 1 de 1 (0 insumos)", size=11, color=Config.COLOR_TEXT_MUTED)
        self.btn_ant = ft.IconButton(icon=ft.icons.CHEVRON_LEFT_ROUNDED, on_click=self.pagina_anterior)
        self.btn_sig = ft.IconButton(icon=ft.icons.CHEVRON_RIGHT_ROUNDED, on_click=self.pagina_siguiente)

        self.construir_interfaz()

    def set_mes_periodo(self, mes: str):
        self.mes_seleccionado = mes
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        partes = self.mes_seleccionado.split('-')
        mes_idx = int(partes[1]) - 1 if len(partes) > 1 and partes[1].isdigit() else 7
        nombre_mes = meses[mes_idx] if 0 <= mes_idx < 12 else self.mes_seleccionado
        year_str = partes[0] if partes else "2026"
        self.lbl_titulo.value = f"Conteo y Stock Inicial • {nombre_mes} {year_str}"
        self.load_data()

    def construir_interfaz(self):
        # Header
        left_controls = []
        if self.on_volver:
            left_controls.append(ft.IconButton(icon=ft.icons.ARROW_BACK_ROUNDED, tooltip="Volver al Historial de Periodos", on_click=lambda e: self.on_volver()))

        left_controls.extend([
            ft.Container(
                content=ft.Icon(ft.icons.CHECKLIST_RTL_ROUNDED, color="white", size=20),
                bgcolor=Config.COLOR_PRIMARY,
                padding=8,
                border_radius=8
            ),
            ft.Column([
                self.lbl_titulo,
                ft.Text("Calibración y registro físico de existencias y costos del periodo", size=11, color=Config.COLOR_TEXT_MUTED)
            ], spacing=1)
        ])

        header_row = ft.Row([
            ft.Row(left_controls, spacing=10),
            ft.Row([
                self.badge_estado_periodo,
                self.btn_qr_movil
            ], spacing=10)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # KPI Cards
        def metric_box(titulo, control, icon_name, color):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon_name, color=color, size=20),
                        padding=10,
                        bgcolor=ft.colors.with_opacity(0.1, color),
                        border_radius=8
                    ),
                    ft.Column([
                        ft.Text(titulo, size=10, color=Config.COLOR_TEXT_MUTED, weight="bold"),
                        control
                    ], spacing=1)
                ], spacing=10),
                padding=12,
                bgcolor="white",
                border=ft.border.all(1, Config.COLOR_BORDER),
                border_radius=10,
                expand=True
            )

        kpis_row = ft.Row([
            metric_box("Insumos con Conteo", self.lbl_insumos_contados, ft.icons.CHECK_CIRCLE_OUTLINE_ROUNDED, Config.COLOR_PRIMARY),
            metric_box("Total Unidades Físicas", self.lbl_total_stock, ft.icons.INVENTORY_2_ROUNDED, Config.COLOR_ACCENT),
            metric_box("Valorización Inicial", self.lbl_valor_total, ft.icons.MONETIZATION_ON_ROUNDED, Config.COLOR_SUCCESS),
        ], spacing=12)

        # Card de Registro Rápido
        registro_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.ADD_TASK_ROUNDED, size=16, color=Config.COLOR_PRIMARY),
                    ft.Text("Registro Rápido de Conteo", size=13, weight="bold", color=Config.COLOR_PRIMARY)
                ], spacing=6),
                ft.Row([
                    self.txt_buscar_insumo,
                    self.txt_cantidad,
                    ft.Column([
                        self.txt_costo,
                        self.lbl_fuente_costo
                    ], spacing=1),
                    self.btn_guardar_conteo
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
                self.lbl_info_seleccionado,
                self.lv_sugerencias
            ], spacing=6),
            padding=14,
            bgcolor="white",
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=10
        )

        # Barra de Filtros de Tabla
        filtros_tabla_row = ft.Row([
            self.txt_filtro_tabla,
            self.dd_categoria_tabla,
            ft.IconButton(icon=ft.icons.REFRESH_ROUNDED, tooltip="Recargar datos", on_click=lambda e: self.load_data())
        ], spacing=10)

        # Tabla Container
        tabla_container = ft.Container(
            content=ft.Column([
                filtros_tabla_row,
                ft.Container(content=self.tabla, border_radius=8),
                ft.Row([
                    self.lbl_paginacion,
                    ft.Row([self.btn_ant, self.btn_sig], spacing=4)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=10),
            padding=14,
            bgcolor="white",
            border=ft.border.all(1, Config.COLOR_BORDER),
            border_radius=10
        )

        self.content = ft.ListView([
            header_row,
            ft.Container(height=4),
            kpis_row,
            ft.Container(height=4),
            registro_card,
            ft.Container(height=4),
            tabla_container
        ], spacing=10, expand=True)

    def did_mount(self):
        self.load_data()

    def load_data(self):
        def worker():
            try:
                # 1. Obtener Periodos
                res_p = self.db.cierres_repo.get_periodos_inventario()
                self.periodos_map = {p.get("mes_periodo"): p for p in res_p}
                
                # Periodo seleccionado
                p_actual = self.periodos_map.get(self.mes_seleccionado)
                if p_actual:
                    self.periodo_activo_id = p_actual.get("id_periodo")
                    estado = p_actual.get("estado", "ABIERTO")
                    is_abierto = (estado == "ABIERTO")
                    self.badge_estado_periodo.content.controls[0].bgcolor = Config.COLOR_SUCCESS if is_abierto else Config.COLOR_DANGER
                    self.badge_estado_periodo.content.controls[1].value = estado
                    self.badge_estado_periodo.content.controls[1].color = Config.COLOR_SUCCESS if is_abierto else Config.COLOR_DANGER
                    self.badge_estado_periodo.bgcolor = Config.COLOR_SUCCESS_BG if is_abierto else Config.COLOR_DANGER_BG
                else:
                    self.periodo_activo_id = self.mobile_service.obtener_periodo_agosto()

                # 2. Obtener Catálogo
                self.catalogo_completo = self.db.insumos_repo.get_insumos(page=1, page_size=3000)[0]

                # Categorias
                cats = sorted(list(set([i.get("categoria") or "SIN CATEGORIA" for i in self.catalogo_completo])))
                self.dd_categoria_tabla.options = [ft.dropdown.Option("Todas")] + [ft.dropdown.Option(c) for c in cats]

                # 3. Obtener Auditorías / Conteos Iniciales del Periodo
                endpoint_aud = f"registro_auditorias_cierres?id_periodo=eq.{self.periodo_activo_id}&tipo_registro=eq.INVENTARIO_INICIAL&select=*"
                res_aud = self.db._db.get(endpoint_aud, timeout=10)
                aud_map = {}
                if res_aud and res_aud.status_code == 200:
                    aud_map = {item.get("codigo_insumo"): item for item in res_aud.json()}

                # Combinar Catálogo con Auditoría
                filas = []
                for item in self.catalogo_completo:
                    cod = str(item.get("codigo_insumo"))
                    nom = item.get("nombre") or ""
                    cat = item.get("categoria") or "GENERAL"
                    costo_cat = float(item.get("costo_unitario") or 0)
                    
                    aud = aud_map.get(cod)
                    if aud:
                        cant = float(aud.get("cantidad_fisica") or aud.get("cantidad_sistema") or 0)
                        costo = float(aud.get("costo_unitario_snapshot") or costo_cat)
                        estado = aud.get("estado", "APROBADO")
                        tiene_conteo = True
                    else:
                        cant = float(item.get("stock_actual") or 0)
                        costo = costo_cat
                        estado = "PENDIENTE"
                        tiene_conteo = False

                    filas.append({
                        "codigo_insumo": cod,
                        "nombre": nom,
                        "categoria": cat,
                        "costo_unitario": costo,
                        "cantidad_fisica": cant,
                        "valor_total": cant * costo,
                        "estado": estado,
                        "tiene_conteo": tiene_conteo
                    })

                self.datos_tabla = filas
                self.aplicar_filtros_tabla()
                self.actualizar_kpis()

            except Exception as ex:
                log_error("ConteoInicialView.load_data", ex)

        threading.Thread(target=worker, daemon=True).start()

    def actualizar_kpis(self):
        contados = [d for d in self.datos_tabla if d.get("cantidad_fisica", 0) > 0]
        total_cant = sum([d.get("cantidad_fisica", 0) for d in self.datos_tabla])
        total_val = sum([d.get("valor_total", 0) for d in self.datos_tabla])

        self.lbl_insumos_contados.value = f"{len(contados)} / {len(self.datos_tabla)}"
        self.lbl_total_stock.value = f"{total_cant:,.0f} unds"
        self.lbl_valor_total.value = f"${total_val:,.0f}"
        if self.page:
            self.page.update()

    def on_buscar_sugerencias(self, e):
        q = (self.txt_buscar_insumo.value or "").strip().lower()
        if not q or len(q) < 2:
            self.lv_sugerencias.visible = False
            self.lv_sugerencias.controls.clear()
            if self.insumo_seleccionado:
                self.insumo_seleccionado = None
                self.txt_cantidad.value = "0"
                self.txt_costo.value = "0"
                self.lbl_info_seleccionado.value = "Ningún insumo seleccionado"
                self.lbl_fuente_costo.value = ""
            if self.page: self.page.update()
            return

        if self.insumo_seleccionado:
            cod_s = str(self.insumo_seleccionado.get("codigo_insumo") or "").lower()
            nom_s = str(self.insumo_seleccionado.get("nombre") or "").lower()
            if q not in cod_s and q not in nom_s:
                self.insumo_seleccionado = None
                self.txt_cantidad.value = "0"
                self.txt_costo.value = "0"
                self.lbl_info_seleccionado.value = "Buscando insumo..."
                self.lbl_fuente_costo.value = ""

        tokens = q.split()
        matches = []
        for item in self.catalogo_completo:
            cod = str(item.get("codigo_insumo") or "").lower()
            nom = str(item.get("nombre") or "").lower()
            texto = f"{cod} {nom}"
            if all(t in texto for t in tokens):
                matches.append(item)
                if len(matches) >= 8:
                    break

        self.lv_sugerencias.controls.clear()
        for m in matches:
            cod_m = str(m.get("codigo_insumo"))
            nom_m = str(m.get("nombre"))
            costo_m = float(m.get("costo_unitario") or 0)
            
            btn = ft.Container(
                content=ft.Row([
                    ft.Text(f"[{cod_m}]", size=11, weight="bold", color=Config.COLOR_PRIMARY),
                    ft.Text(nom_m, size=11, weight="w500", expand=True, color="black87"),
                    ft.Text(f"Costo: ${costo_m:,.0f}", size=10, color=Config.COLOR_TEXT_MUTED)
                ], spacing=6),
                padding=ft.padding.symmetric(horizontal=8, vertical=5),
                bgcolor="#f8fafc",
                border_radius=6,
                border=ft.border.all(1, "#e2e8f0"),
                on_click=lambda ev, it=m: self.seleccionar_insumo_registro(it)
            )
            self.lv_sugerencias.controls.append(btn)

        self.lv_sugerencias.visible = (len(matches) > 0)
        if self.page: self.page.update()

    def seleccionar_insumo_registro(self, item):
        self.insumo_seleccionado = item
        self.lv_sugerencias.visible = False
        cod = str(item.get("codigo_insumo"))
        nom = item.get("nombre")
        cat = item.get("categoria") or "GENERAL"
        
        self.txt_buscar_insumo.value = f"[{cod}] {nom}"
        self.lbl_info_seleccionado.value = f"Insumo activo: [{cod}] {nom} • Categoría: {cat}"
        
        # 1. Resolver costo automáticamente
        costo = float(item.get("costo_unitario") or 0)
        fuente = "Catálogo Maestro"
        if costo <= 0:
            try:
                res_c = self.db._db.get(f"registro_compras?codigo_insumo=eq.{cod}&order=fecha.desc&limit=1&select=costo_unitario", timeout=5)
                if res_c and res_c.status_code == 200 and res_c.json():
                    costo = float(res_c.json()[0].get("costo_unitario") or 0)
                    fuente = "Última Compra Registrada"
            except Exception:
                pass

        self.txt_costo.value = str(int(costo) if costo.is_integer() else costo)
        self.lbl_fuente_costo.value = f"Fuente: {fuente}"
        
        # 2. Cantidad actual
        stock_actual = float(item.get("stock_actual") or 0)
        self.txt_cantidad.value = str(int(stock_actual) if stock_actual.is_integer() else stock_actual)
        
        if self.page: self.page.update()

    def guardar_conteo_manual(self, e):
        if not self.insumo_seleccionado:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Por favor busca y selecciona un insumo primero"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
            return

        try:
            cod = str(self.insumo_seleccionado.get("codigo_insumo"))
            cant = float(self.txt_cantidad.value or 0)
            costo = float(self.txt_costo.value or 0)

            res = self.mobile_service.guardar_stock_inicial(
                codigo_insumo=cod,
                cantidad=cant,
                costo_unitario=costo,
                usuario="Admin Local"
            )

            if res.get("exito"):
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"✓ Conteo guardado: [{cod}] {cant} unds ($ {costo:,.0f})"), bgcolor=Config.COLOR_SUCCESS)
                    self.page.snack_bar.open = True
                
                # Limpiar formulario
                self.insumo_seleccionado = None
                self.txt_buscar_insumo.value = ""
                self.txt_cantidad.value = "0"
                self.txt_costo.value = "0"
                self.lbl_fuente_costo.value = ""
                self.lbl_info_seleccionado.value = "Ningún insumo seleccionado"
                
                self.load_data()
            else:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"Error al guardar: {res.get('error')}"), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.page.update()

        except Exception as ex:
            log_error("guardar_conteo_manual", ex)

    def on_filtro_tabla_change(self, e):
        self.aplicar_filtros_tabla()

    def aplicar_filtros_tabla(self):
        q = (self.txt_filtro_tabla.value or "").strip().lower()
        cat = self.dd_categoria_tabla.value

        filtrados = self.datos_tabla
        if cat and cat != "Todas":
            filtrados = [d for d in filtrados if d.get("categoria") == cat]

        if q:
            tokens = q.split()
            filtrados = [d for d in filtrados if all(t in f"{d.get('codigo_insumo','').lower()} {d.get('nombre','').lower()}" for t in tokens)]

        self.datos_filtrados = filtrados
        self.total_pages = max(1, (len(filtrados) + self.page_size - 1) // self.page_size)
        self.current_page = 1
        self.renderizar_tabla()

    def renderizar_tabla(self):
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        pagina_items = self.datos_filtrados[start:end]

        rows = []
        for item in pagina_items:
            cod = item.get("codigo_insumo")
            nom = item.get("nombre")
            cat = item.get("categoria")
            costo = item.get("costo_unitario", 0)
            cant = item.get("cantidad_fisica", 0)
            val_tot = item.get("valor_total", 0)
            estado = item.get("estado", "APROBADO")

            is_aprobado = (estado == "APROBADO" and item.get("tiene_conteo"))

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Container(content=ft.Text(cod, size=11, weight="bold", color="white"), bgcolor=Config.COLOR_PRIMARY, padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4)),
                        ft.DataCell(ft.Text(nom, size=11, weight="w600", color="black87")),
                        ft.DataCell(ft.Text(cat, size=10, color=Config.COLOR_TEXT_MUTED)),
                        ft.DataCell(ft.Text(f"${costo:,.0f}", size=11, weight="bold", color="grey800")),
                        ft.DataCell(ft.Text(f"{cant:g} unds", size=12, weight="extrabold", color=Config.COLOR_SUCCESS if cant > 0 else "grey500")),
                        ft.DataCell(ft.Text(f"${val_tot:,.0f}", size=11, weight="bold", color=Config.COLOR_PRIMARY)),
                        ft.DataCell(ft.Container(content=ft.Text(estado, size=9, weight="bold", color=Config.COLOR_SUCCESS if is_aprobado else "amber800"), bgcolor=Config.COLOR_SUCCESS_BG if is_aprobado else "#fffbe8", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=8)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.EDIT_ROUNDED,
                                icon_size=16,
                                tooltip="Cargar en Registro Rápido",
                                on_click=lambda e, it=item: self.cargar_en_formulario(it)
                            )
                        )
                    ]
                )
            )

        self.tabla.rows = rows
        self.lbl_paginacion.value = f"Página {self.current_page} de {self.total_pages} ({len(self.datos_filtrados)} insumos)"
        if self.page:
            self.page.update()

    def cargar_en_formulario(self, item):
        cod = item.get("codigo_insumo")
        orig = next((i for i in self.catalogo_completo if str(i.get("codigo_insumo")) == str(cod)), item)
        self.seleccionar_insumo_registro(orig)

    def pagina_anterior(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.renderizar_tabla()

    def pagina_siguiente(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.renderizar_tabla()

    def abrir_modal_qr(self, e):
        iniciar_servidor_en_hilo(port=8550)
        url = self.mobile_service.get_server_url(port=8550)
        qr_b64 = self.mobile_service.get_qr_base64(port=8550)

        def copiar_url(ev):
            if self.page:
                self.page.set_clipboard(url)
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Enlace copiado al portapapeles: {url}"), bgcolor=Config.COLOR_SUCCESS)
                self.page.snack_bar.open = True
                self.page.update()

        def cerrar_dialogo(dlg):
            if self.page:
                if hasattr(self.page, "close"):
                    self.page.close(dlg)
                else:
                    dlg.open = False
                    self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.PHONE_ANDROID_ROUNDED, color=Config.COLOR_ACCENT),
                ft.Text("Conteo Móvil Wi-Fi (Bodega)", size=16, weight="bold", color=Config.COLOR_PRIMARY)
            ]),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(width=8, height=8, bgcolor=Config.COLOR_SUCCESS, border_radius=4),
                            ft.Text("Servidor Activo en Red Local", size=11, weight="bold", color=Config.COLOR_SUCCESS)
                        ], spacing=6),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=Config.COLOR_SUCCESS_BG,
                        border_radius=12,
                        border=ft.border.all(1, ft.colors.with_opacity(0.3, Config.COLOR_SUCCESS))
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(
                    content=ft.Image(src_base64=qr_b64, width=190, height=190, fit=ft.ImageFit.CONTAIN),
                    alignment=ft.alignment.center,
                    padding=10,
                    bgcolor="white",
                    border=ft.border.all(1, Config.COLOR_BORDER),
                    border_radius=12
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.LINK_ROUNDED, size=16, color=Config.COLOR_ACCENT),
                        ft.Text(url, size=13, weight="bold", color=Config.COLOR_ACCENT, selectable=True),
                        ft.IconButton(icon=ft.icons.COPY_ALL_ROUNDED, icon_size=18, tooltip="Copiar enlace", on_click=copiar_url)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    bgcolor=Config.COLOR_BACKGROUND,
                    border=ft.border.all(1, Config.COLOR_BORDER),
                    border_radius=8
                ),
                ft.Text(
                    f"Apunta con la cámara de cualquier teléfono conectado al Wi-Fi para registrar el stock inicial de {self.mes_seleccionado} sin cables.",
                    size=11, color=Config.COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER
                )
            ], tight=True, spacing=10, width=380, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Copiar Enlace", on_click=copiar_url),
                ft.ElevatedButton("Cerrar", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=lambda e: cerrar_dialogo(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=14)
        )
        if self.page:
            if hasattr(self.page, "open"):
                self.page.open(dlg)
            else:
                self.page.overlay.append(dlg)
                dlg.open = True
                self.page.update()
