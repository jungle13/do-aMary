"""
Fachada centralizada de base de datos (Supabase) para Sistema Doña Mary.
Delega las operaciones en repositorios especializados manteniendo total compatibilidad hacia atrás.
"""
from core.database import BaseDatabase
from core.logger import get_logger, log_error
from core.repositories.insumos_repo import InsumosRepository
from core.repositories.compras_repo import ComprasRepository
from core.repositories.ventas_repo import VentasRepository
from core.repositories.cierres_repo import CierresRepository
from core.repositories.usuarios_repo import UsuariosRepository
from core.repositories.clientes_repo import ClientesRepository
from core.repositories.cartera_repo import CarteraRepository

logger = get_logger("SupabaseClient")

_client_instance = None

def get_client():
    """Retorna la instancia singleton del cliente Supabase."""
    global _client_instance
    if _client_instance is None:
        _client_instance = SupabaseClient()
    return _client_instance

class SupabaseClient:
    """
    Fachada unificada que agrupa los repositorios por dominio.
    Mantiene compatibilidad total con todas las llamadas existentes.
    """
    def __init__(self):
        self._db = BaseDatabase()
        self.url = self._db.url
        self.key = self._db.key
        self.headers = self._db.headers
        self.session = self._db.session

        # Instancias de repositorios
        self.insumos_repo = InsumosRepository(self._db)
        self.compras_repo = ComprasRepository(self._db)
        self.ventas_repo = VentasRepository(self._db)
        self.cierres_repo = CierresRepository(self._db)
        self.usuarios_repo = UsuariosRepository(self._db)
        self.clientes_repo = ClientesRepository(self._db)
        self.cartera_repo = CarteraRepository(self._db)

    def check_connection(self):
        return self._db.check_connection()

    # --- USUARIOS & AUTENTICACIÓN ---
    def autenticar_usuario(self, usuario: str, clave: str) -> dict | None:
        return self.usuarios_repo.autenticar(usuario, clave)

    # --- CATÁLOGO DE INSUMOS & STOCK ---
    def get_categorias(self):
        return self.insumos_repo.get_categorias()

    def get_insumos(self, page=1, page_size=20, search="", categoria="", fecha_corte=None, sort_col="Insumo", sort_asc=True, codigos_filtro=None):
        return self.insumos_repo.get_insumos(page, page_size, search, categoria, fecha_corte, sort_col, sort_asc, codigos_filtro)

    def insert_insumo(self, data: dict):
        return self.insumos_repo.insert_insumo(data)

    def update_insumo(self, codigo_insumo: str, datos_actualizados: dict) -> bool:
        return self.insumos_repo.update_insumo(codigo_insumo, datos_actualizados)

    def get_nombres_insumos(self, lista_codigos: list) -> dict:
        return self.insumos_repo.get_nombres_insumos(lista_codigos)

    def get_catalogo_costos(self) -> dict:
        return self.insumos_repo.get_catalogo_costos()

    def get_insumo_detalle(self, codigo: str) -> dict:
        return self.insumos_repo.get_insumo_detalle(codigo)

    def get_catalogo_summary(self, fecha_corte=None) -> dict:
        return self.insumos_repo.get_catalogo_summary(fecha_corte)

    def get_top_costo_inventario(self, limit=10, fecha_corte=None) -> list:
        return self.insumos_repo.get_top_costo_inventario(limit, fecha_corte)

    def get_inventario_kpis(self, fecha_corte=None) -> dict:
        return self.insumos_repo.get_inventario_kpis(fecha_corte)

    def get_kpis_por_categoria(self, fecha_corte=None) -> list:
        return self.insumos_repo.get_kpis_por_categoria(fecha_corte)

    def get_ajustes_inventario(self) -> list:
        return self.insumos_repo.get_ajustes_inventario()

    def get_ajustes_mes(self, mes_actual: str, fecha_corte=None) -> list:
        return self.insumos_repo.get_ajustes_mes(mes_actual, fecha_corte)

    def insert_ajuste_individual(self, datos: dict) -> bool:
        return self.insumos_repo.insert_ajuste_individual(datos)

    def anular_ajuste(self, id_ajuste: str) -> bool:
        return self.insumos_repo.anular_ajuste(id_ajuste)

    # --- COMPRAS ---
    def get_compras(self, page=1, page_size=15, search="", fecha_corte=None, factura_filtro=None, proveedor_filtro=None):
        return self.compras_repo.get_compras(page, page_size, search, fecha_corte, factura_filtro, proveedor_filtro)

    def get_historial_compras_dia(self, fecha_dia: str, agrupar_por: str = "FACTURA") -> list:
        return self.compras_repo.get_historial_compras_dia(fecha_dia, agrupar_por)

    def insert_compras(self, compras_list: list):
        return self.compras_repo.insert_compras(compras_list)

    def get_entradas_existentes(self, lista_eas: list, lista_facturas: list = None) -> set:
        return self.compras_repo.get_entradas_existentes(lista_eas, lista_facturas)

    def eliminar_compras_por_entradas(self, lista_entradas: list):
        return self.compras_repo.eliminar_compras_por_entradas(lista_entradas)

    def get_compras_summary(self, fecha_corte=None):
        return self.compras_repo.get_compras_summary(fecha_corte)

    def get_proveedores_unicos(self):
        return self.compras_repo.get_proveedores_unicos()

    def get_historial_compras_dia(self, fecha_dia=None, agrupar_por="FACTURA", proveedor_filtro=None) -> list:
        return self.compras_repo.get_historial_compras_dia(fecha_dia, agrupar_por, proveedor_filtro)

    def update_compra_individual(self, id_compra: str, datos: dict):
        return self.compras_repo.update_compra_individual(id_compra, datos)

    def eliminar_compra_individual(self, id_compra: str):
        return self.compras_repo.eliminar_compra_individual(id_compra)

    # --- VENTAS ---
    def get_ventas(self, page=1, page_size=20, search="", fecha_corte=None, categoria_filtro=None, factura_filtro=None, tipo_documento_filtro=None):
        return self.ventas_repo.get_ventas(page, page_size, search, fecha_corte, categoria_filtro, factura_filtro, tipo_documento_filtro)

    def get_historial_ventas_dia(self, fecha_dia=None, agrupar_por="CATEGORIA", tipo_documento=None) -> list:
        return self.ventas_repo.get_historial_ventas_dia(fecha_dia, agrupar_por, tipo_documento)

    def get_ventas_existentes(self, lista_facturas: list) -> set:
        return self.ventas_repo.get_ventas_existentes(lista_facturas)

    def eliminar_ventas_origen(self, fecha: str, tipo_documento: str, pagina_origen: int) -> bool:
        return self.ventas_repo.eliminar_ventas_origen(fecha, tipo_documento, pagina_origen)

    def eliminar_ventas_por_facturas(self, lista_facturas: list):
        return self.ventas_repo.eliminar_ventas_por_facturas(lista_facturas)

    def insert_ventas(self, ventas_list: list):
        return self.ventas_repo.insert_ventas(ventas_list)

    def get_ventas_summary(self, fecha_corte=None):
        return self.ventas_repo.get_ventas_summary(fecha_corte)

    def get_top_ventas_mes(self, limit=10, fecha_corte=None) -> list:
        return self.ventas_repo.get_top_ventas_mes(limit, fecha_corte)

    def get_tendencia_diaria(self, fecha_corte=None) -> dict:
        return self.ventas_repo.get_tendencia_diaria(fecha_corte)

    def get_proyeccion_ventas(self, fecha_corte=None) -> float:
        return self.ventas_repo.get_proyeccion_ventas(fecha_corte)

    def insert_venta_individual(self, datos: dict):
        return self.ventas_repo.insert_venta_individual(datos)

    def update_venta_individual(self, id_venta: str, datos: dict):
        return self.ventas_repo.update_venta_individual(id_venta, datos)

    def eliminar_venta_individual(self, id_venta: str):
        return self.ventas_repo.eliminar_venta_individual(id_venta)

    def get_historial_facturas_dia(self, fecha_dia: str) -> list:
        return self.ventas_repo.get_historial_facturas_dia(fecha_dia)

    def get_codigos_factura_especifica(self, tipo: str, ref: str) -> list:
        return self.ventas_repo.get_codigos_factura_especifica(tipo, ref)

    def get_rendimiento_categorias_periodo(self, fecha_inicio=None, fecha_fin=None) -> list:
        """Calcula el rendimiento y costo acumulado real por categoría hasta 'fecha_fin' considerando insumos con stock > 0 y costos reales de compra."""
        categorias_map = {}
        try:
            # 1. Obtener mapa de últimos costos unitarios reales de compras
            res_c = self._db.get("registro_compras?select=codigo_insumo,costo_unitario,fecha&estado_registro=eq.VÁLIDO&order=fecha.desc&limit=5000", timeout=10)
            costos_compras = {}
            if res_c and res_c.status_code == 200:
                for r in res_c.json():
                    cod = str(r.get("codigo_insumo") or "").strip()
                    cu = float(r.get("costo_unitario") or 0)
                    if cod and cod not in costos_compras and cu > 0:
                        costos_compras[cod] = cu

            # 2. Consultar catálogo de insumos / vista de inventario
            insumos, _ = self.insumos_repo.get_insumos(page=1, page_size=99999, fecha_corte=fecha_fin)
            for item in insumos:
                cat_nombre = (item.get("categoria") or "SIN CATEGORÍA").strip().upper()
                stock = float(item.get("stock_actual") or item.get("stock_real") or 0)
                cod_insumo = str(item.get("codigo_insumo") or "").strip()

                costo_u_real = costos_compras.get(cod_insumo, float(item.get("costo_unitario") or 0))
                precio_v = float(item.get("precio_venta") or 0)

                # Solo stock positivo suma al costo de inventario actual y proyecciones
                stock_pos = max(0.0, stock)
                inv_costo_item = stock_pos * costo_u_real
                proy_venta_item = stock_pos * precio_v

                ventas_item = float(item.get("valor_ventas") or 0)
                cant_ventas = float(item.get("ventas") or 0)
                costo_vendido_item = cant_ventas * costo_u_real

                if cat_nombre not in categorias_map:
                    categorias_map[cat_nombre] = {
                        "categoria": cat_nombre,
                        "inventario_costo": 0.0,
                        "proyeccion_venta": 0.0,
                        "ventas_realizadas": 0.0,
                        "costo_vendido": 0.0
                    }

                categorias_map[cat_nombre]["inventario_costo"] += inv_costo_item
                categorias_map[cat_nombre]["proyeccion_venta"] += proy_venta_item
                categorias_map[cat_nombre]["ventas_realizadas"] += ventas_item
                categorias_map[cat_nombre]["costo_vendido"] += costo_vendido_item
        except Exception as ex:
            log_error("get_rendimiento_categorias_periodo", ex)

        resultado = []
        for cat_nombre, d in categorias_map.items():
            inv_c = d["inventario_costo"]
            v_real = d["ventas_realizadas"]
            proy_v = d["proyeccion_venta"]
            c_vend = d["costo_vendido"]

            meta_cat = v_real + proy_v
            cumplimiento = (v_real / meta_cat * 100) if meta_cat > 0 else 0.0
            rotacion = (v_real / inv_c) if inv_c > 0 else 0.0
            rendimiento = ((v_real - c_vend) / v_real * 100) if v_real > 0 else 0.0

            resultado.append({
                "categoria": cat_nombre,
                "inventario_costo": inv_c,
                "ventas_realizadas": v_real,
                "proyeccion_venta": proy_v,
                "cumplimiento_pct": cumplimiento,
                "rotacion": rotacion,
                "rendimiento_pct": rendimiento
            })

        resultado.sort(key=lambda x: (x["inventario_costo"], x["ventas_realizadas"]), reverse=True)
        return resultado

    # --- CIERRES & AUDITORÍAS ---
    def get_periodos_inventario(self) -> list:
        return self.cierres_repo.get_periodos_inventario()

    def get_datos_conteo_inicial(self, mes_seleccionado: str) -> list:
        return self.cierres_repo.get_datos_conteo_inicial(mes_seleccionado)

    def upsert_conteos_iniciales(self, registros: list) -> bool:
        return self.cierres_repo.upsert_conteos_iniciales(registros)

    def iniciar_snapshot_cierre(self, mes_periodo: str) -> dict:
        return self.cierres_repo.iniciar_snapshot_cierre(mes_periodo)

    def obtener_estado_cierre(self, mes_periodo: str) -> dict:
        return self.cierres_repo.obtener_estado_cierre(mes_periodo)

    def registrar_conteo_fisico(self, id_auditoria: str, cantidad: float, costo: float = None, observacion: str = None) -> dict:
        return self.cierres_repo.registrar_conteo_fisico(id_auditoria, cantidad, costo, observacion)

    def aceptar_stock_sistema(self, id_auditoria: str) -> dict:
        return self.cierres_repo.aceptar_stock_sistema(id_auditoria)

    def aceptar_stock_sistema_masivo(self, ids_auditoria: list) -> dict:
        return self.cierres_repo.aceptar_stock_sistema_masivo(ids_auditoria)

    def eliminar_ajuste_cierre(self, id_auditoria: str) -> dict:
        return self.cierres_repo.eliminar_ajuste_cierre(id_auditoria)

    def aprobar_cierre_mes(self, id_periodo: str, aprobado_por: str) -> dict:
        return self.cierres_repo.aprobar_cierre_mes(id_periodo, aprobado_por)

    def get_detalle_diario_mes(self, mes: str) -> dict:
        """
        Descarga en paralelo los registros del mes para construir la vista
        de Resumen Financiero por Día del Dashboard.

        Retorna un dict con claves por día 'YYYY-MM-DD', cada una con:
        {
            'ventas_total': float,
            'ventas_pos': float,
            'ventas_remision': float,
            'iva_ventas': float,
            'compras': float,
            'iva_compras': float,
            'recaudado': float,
            'recaudado_efectivo': float,
            'recaudado_banco': float,
            'ajustes_entrada_costo': float,
            'ajustes_salida_costo': float,
            'ajustes_entrada_count': int,
            'ajustes_salida_count': int,
        }

        Args:
            mes: Periodo en formato 'YYYY-MM'.

        Returns:
            Diccionario de días con KPIs financieros diarios.
        """
        from concurrent.futures import ThreadPoolExecutor
        resultado: dict = {}

        def _fetch_ventas():
            try:
                res = self._db.get_all(
                    f"registro_ventas?select=fecha,total,iva,tipo_documento,estado_registro"
                    f"&fecha=gte.{mes}-01&fecha=lt.{_mes_siguiente(mes)}-01"
                    f"&estado_registro=neq.ANULADO"
                )
                return res or []
            except Exception as ex:
                log_error("get_detalle_diario_mes._fetch_ventas", ex)
                return []

        def _fetch_compras():
            try:
                res = self._db.get_all(
                    f"registro_compras?select=fecha,costo_total,iva,valor_iva,estado_registro"
                    f"&fecha=gte.{mes}-01&fecha=lt.{_mes_siguiente(mes)}-01"
                    f"&estado_registro=neq.ANULADO"
                )
                return res or []
            except Exception as ex:
                log_error("get_detalle_diario_mes._fetch_compras", ex)
                return []

        def _fetch_pagos():
            try:
                res = self._db.get_all(
                    f"pagos_cartera?select=fecha_pago,monto_total,metodo_pago,estado_registro"
                    f"&fecha_pago=gte.{mes}-01&fecha_pago=lt.{_mes_siguiente(mes)}-01"
                    f"&estado_registro=neq.ANULADO"
                )
                return res or []
            except Exception as ex:
                log_error("get_detalle_diario_mes._fetch_pagos", ex)
                return []

        def _fetch_ajustes():
            try:
                res = self._db.get_all(
                    f"registro_ajustes_inventario"
                    f"?select=fecha_ajuste,tipo_ajuste,costo_total_ajuste,estado_registro"
                    f"&fecha_ajuste=gte.{mes}-01&fecha_ajuste=lt.{_mes_siguiente(mes)}-01"
                    f"&estado_registro=neq.ANULADO"
                )
                return res or []
            except Exception as ex:
                log_error("get_detalle_diario_mes._fetch_ajustes", ex)
                return []

        def _mes_siguiente(m: str) -> str:
            anio, mon = int(m[:4]), int(m[5:7])
            if mon == 12:
                return f"{anio + 1}-01"
            return f"{anio}-{mon + 1:02d}"

        with ThreadPoolExecutor(max_workers=4) as ex:
            f_v = ex.submit(_fetch_ventas)
            f_c = ex.submit(_fetch_compras)
            f_p = ex.submit(_fetch_pagos)
            f_a = ex.submit(_fetch_ajustes)
            ventas_raw = f_v.result()
            compras_raw = f_c.result()
            pagos_raw = f_p.result()
            ajustes_raw = f_a.result()

        _vacio = lambda: {
            "ventas_total": 0.0, "ventas_pos": 0.0, "ventas_remision": 0.0,
            "iva_ventas": 0.0, "compras": 0.0, "iva_compras": 0.0,
            "recaudado": 0.0, "recaudado_efectivo": 0.0, "recaudado_banco": 0.0,
            "ajustes_entrada_costo": 0.0, "ajustes_salida_costo": 0.0,
            "ajustes_entrada_count": 0, "ajustes_salida_count": 0,
        }

        def _dia_key(fecha_str: str) -> str:
            """Extrae la parte de fecha 'YYYY-MM-DD' de un timestamp."""
            return str(fecha_str or "")[:10]

        for v in ventas_raw:
            dia = _dia_key(v.get("fecha", ""))
            if not dia or not dia.startswith(mes):
                continue
            if dia not in resultado:
                resultado[dia] = _vacio()
            total = float(v.get("total") or 0.0)
            iva = float(v.get("iva") or 0.0)
            tipo = str(v.get("tipo_documento") or "").upper()
            resultado[dia]["ventas_total"] += total
            resultado[dia]["iva_ventas"] += iva
            if "POS" in tipo:
                resultado[dia]["ventas_pos"] += total
            else:
                resultado[dia]["ventas_remision"] += total

        for c in compras_raw:
            dia = _dia_key(c.get("fecha", ""))
            if not dia or not dia.startswith(mes):
                continue
            if dia not in resultado:
                resultado[dia] = _vacio()
            costo = float(c.get("costo_total") or 0.0)
            iva = float(c.get("valor_iva") or c.get("iva") or 0.0)
            resultado[dia]["compras"] += costo
            resultado[dia]["iva_compras"] += iva

        for p in pagos_raw:
            dia = _dia_key(p.get("fecha_pago", ""))
            if not dia or not dia.startswith(mes):
                continue
            if dia not in resultado:
                resultado[dia] = _vacio()
            monto = float(p.get("monto_total") or 0.0)
            metodo = str(p.get("metodo_pago") or "").upper()
            resultado[dia]["recaudado"] += monto
            if "EFECTIVO" in metodo or "CASH" in metodo:
                resultado[dia]["recaudado_efectivo"] += monto
            else:
                resultado[dia]["recaudado_banco"] += monto

        for a in ajustes_raw:
            dia = _dia_key(a.get("fecha_ajuste", ""))
            if not dia or not dia.startswith(mes):
                continue
            if dia not in resultado:
                resultado[dia] = _vacio()
            costo = float(a.get("costo_total_ajuste") or 0.0)
            tipo = str(a.get("tipo_ajuste") or "").upper()
            if "ENTRADA" in tipo or "SOBRANTE" in tipo:
                resultado[dia]["ajustes_entrada_costo"] += costo
                resultado[dia]["ajustes_entrada_count"] += 1
            else:
                resultado[dia]["ajustes_salida_costo"] += costo
                resultado[dia]["ajustes_salida_count"] += 1

        return resultado
