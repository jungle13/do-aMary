"""
Repositorio para el catálogo de insumos, stock y ajustes de inventario.
"""
import urllib.parse
from core.database import BaseDatabase
from core.logger import get_logger, log_error

logger = get_logger("InsumosRepo")


class InsumosRepository:
    def __init__(self, db: BaseDatabase | None = None):
        self.db = db or BaseDatabase()

    def get_categorias(self) -> list[str]:
        """Obtiene la lista de categorías únicas de insumos optimizada con RPC."""
        try:
            res = self.db.post("rpc/get_categorias_unicas_rpc", json_data={}, timeout=8)
            if res and res.status_code == 200:
                data = res.json()
                cats = [str(item["categoria"]).strip() for item in data if item.get("categoria")]
                if cats:
                    return sorted(cats)
        except Exception:
            pass

        # Fallback estándar
        try:
            res = self.db.get("catalogo_insumos?select=categoria", timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                categorias = set([item.get("categoria", "SIN CATEGORIA") for item in data if item.get("categoria")])
                return sorted(list(categorias))
            return []
        except Exception as ex:
            log_error("get_categorias", ex)
            return []

    def get_insumos(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = "",
        categoria: str = "",
        fecha_corte: str | None = None,
        sort_col: str = "Insumo",
        sort_asc: bool = True,
        codigos_filtro: list | None = None
    ) -> tuple[list, int]:
        """Obtiene insumos con paginación, filtros y ordenamiento sanitizado."""
        endpoint = "rpc/obtener_inventario_por_fecha?select=*" if fecha_corte else "vista_inventario_completo?select=*"
        filtros = []

        if codigos_filtro is not None:
            if not codigos_filtro:
                filtros.append("codigo_insumo=in.(INVALID_FORCE_EMPTY)")
            else:
                codigos_str = ",".join([urllib.parse.quote(str(c).strip()) for c in codigos_filtro if str(c).strip()])
                filtros.append(f"codigo_insumo=in.({codigos_str})")

        if categoria and categoria != "Todas":
            cat_enc = urllib.parse.quote(str(categoria).strip())
            filtros.append(f"categoria=eq.{cat_enc}")

        if search and search.strip():
            s_enc = urllib.parse.quote(search.strip())
            filtros.append(f"or=(nombre.ilike.*{s_enc}*,codigo_insumo.ilike.*{s_enc}*)")

        if filtros:
            endpoint += "&" + "&".join(filtros)

        db_col_stock = "stock_real" if fecha_corte else "stock_actual"
        map_columnas = {
            "Código": "codigo_insumo",
            "Insumo": "nombre",
            "Categoría": "categoria",
            "Ubicación": "ubicacion",
            "Stock Inicial": "stock_inicial",
            "Stock Mínimo": "stock_minimo",
            "Entradas": "entradas",
            "Salidas": "salidas",
            "Stock Real": db_col_stock,
            # Métricas superiores de tarjetas
            "Costo s/IVA": "costo_unitario",
            "Costo U": "costo_unitario",
            "P. Venta": "precio_venta",
            "Stock Actual": db_col_stock,
            "Valor Costo": "costo_total_insumo",
            "Objetivo Venta": "precio_venta",
            # Métricas inferiores de tarjetas
            "INICIAL": "stock_inicial",
            "COMPRAS": "compras",
            "VENTAS": "ventas",
            "AJUSTES (+)": "ajustes_entrantes",
            "AJUSTES (-)": "ajustes_salientes",
            "NETO": "neto_ajustes"
        }

        db_col = map_columnas.get(sort_col, "nombre")
        direccion = "asc" if sort_asc else "desc"
        offset = (page - 1) * page_size
        endpoint += f"&order={db_col}.{direccion}&offset={offset}&limit={page_size}"

        headers = {"Prefer": "count=exact"}
        try:
            if fecha_corte:
                payload = {"p_fecha_corte": f"{fecha_corte} 23:59:59"}
                res = self.db.post(endpoint, json_data=payload, custom_headers=headers, timeout=10)
            else:
                res = self.db.get(endpoint, custom_headers=headers, timeout=10)

            if res and res.status_code in (200, 201, 206):
                data = res.json()
                content_range = res.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                err_text = res.text if res else "No response"
                logger.warning(f"Error consultando insumos: {err_text}")
                return [], 0
        except Exception as ex:
            log_error("get_insumos", ex)
            return [], 0

    def insert_insumo(self, data: dict):
        """Inserta un nuevo insumo en el catálogo."""
        try:
            res = self.db.post("catalogo_insumos", json_data=data, timeout=10)
            if res and res.status_code in (200, 201):
                from core.audit_logger import registrar_accion
                registrar_accion(
                    accion=f"Creación de nuevo insumo en catálogo: [{data.get('codigo_insumo')}] {data.get('nombre')}",
                    modulo="INVENTARIO",
                    detalles=data
                )
                return res.json()
            return None
        except Exception as ex:
            log_error("insert_insumo", ex, {"data": data})
            return None

    def update_insumo(self, codigo_insumo: str, datos_actualizados: dict) -> bool:
        """Actualiza un insumo existente en el catálogo."""
        try:
            endpoint = f"catalogo_insumos?codigo_insumo=eq.{codigo_insumo}"
            res = self.db.patch(endpoint, json_data=datos_actualizados, timeout=10)
            if res and res.status_code in (200, 204):
                from core.audit_logger import registrar_accion
                cambios_str = ", ".join([f"{k}={v}" for k, v in datos_actualizados.items()])
                registrar_accion(
                    accion=f"Modificación de insumo [{codigo_insumo}]: {cambios_str}",
                    modulo="INVENTARIO",
                    detalles={"codigo_insumo": codigo_insumo, "cambios": datos_actualizados}
                )
                return True
            return False
        except Exception as ex:
            log_error("update_insumo", ex, {"codigo": codigo_insumo})
            return False

    def get_nombres_insumos(self, lista_codigos: list) -> dict:
        """Devuelve un diccionario {codigo: nombre} buscando en catalogo_insumos."""
        if not lista_codigos:
            return {}
        try:
            codigos_str = ",".join(lista_codigos)
            endpoint = f"catalogo_insumos?select=codigo_insumo,nombre&codigo_insumo=in.({codigos_str})"
            res = self.db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                return {item["codigo_insumo"]: item["nombre"] for item in data if item.get("codigo_insumo")}
            return {}
        except Exception as ex:
            log_error("get_nombres_insumos", ex)
            return {}

    def get_catalogo_costos(self) -> dict:
        """Obtiene un diccionario {codigo: costo_unitario}."""
        try:
            endpoint = "catalogo_insumos?select=codigo_insumo,costo_unitario"
            res = self.db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                return {item.get('codigo_insumo'): float(item.get('costo_unitario') or 0) for item in res.json()}
            return {}
        except Exception as ex:
            log_error("get_catalogo_costos", ex)
            return {}

    def get_insumo_detalle(self, codigo: str) -> dict:
        """Recupera el nombre, costo, precio y stock de un insumo específico."""
        try:
            endpoint = f"catalogo_insumos?codigo_insumo=eq.{codigo}&select=nombre,costo_unitario,precio_venta,stock_actual"
            res = self.db.get(endpoint, timeout=10)
            if res and res.status_code == 200 and len(res.json()) > 0:
                return res.json()[0]
        except Exception as ex:
            log_error("get_insumo_detalle", ex, {"codigo": codigo})
        return {}

    def get_catalogo_summary(self, fecha_corte=None) -> dict:
        """Invoca RPC para compras totales y ventas totales en pesos."""
        try:
            payload = {"fecha_corte": fecha_corte} if fecha_corte else {}
            res = self.db.post("rpc/get_catalogo_summary_rpc", json_data=payload if payload else None, timeout=10)
            if res and res.status_code == 200:
                return res.json()
        except Exception as ex:
            log_error("get_catalogo_summary", ex)
        return {"total_compras": 0.0, "total_ventas": 0.0}

    def get_top_costo_inventario(self, limit: int = 10, fecha_corte=None) -> list:
        """Obtiene los insumos con mayor costo total de inventario acumulado."""
        try:
            insumos, _ = self.get_insumos(
                page=1,
                page_size=limit,
                fecha_corte=fecha_corte,
                sort_col="Stock Real",
                sort_asc=False
            )
            top = []
            for item in insumos:
                costo_tot = float(item.get("costo_total_insumo") or 0)
                ventas_tot = float(item.get("valor_ventas") or 0)
                rotacion = (ventas_tot / costo_tot) if costo_tot > 0 else 0.0
                top.append({
                    "codigo": item.get("codigo_insumo") or "S/C",
                    "producto": item.get("nombre") or "Desconocido",
                    "valor_inventario": costo_tot,
                    "rotacion": f"{rotacion:.2f}x"
                })
            return top
        except Exception as ex:
            log_error("get_top_costo_inventario", ex)
            return []

    def get_inventario_kpis(self, fecha_corte: str | None = None) -> dict:
        """Obtiene los KPIs generales de valorización de inventario y alertas utilizando la función RPC en BD."""
        try:
            payload = {"p_fecha_corte": fecha_corte} if fecha_corte else {}
            res = self.db.post("rpc/get_inventario_kpis_rpc", json_data=payload, timeout=8)
            if res and res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    return {
                        "valor_inventario": float(data.get("valor_inventario") or 0.0),
                        "alertas_criticas": int(data.get("alertas_criticas") or 0)
                    }
        except Exception as ex:
            logger.warning(f"Fallback local para get_inventario_kpis: {ex}")

        # Fallback local
        try:
            res_c = self.db.get("registro_compras?select=codigo_insumo,costo_unitario,fecha&estado_registro=eq.VÁLIDO&order=fecha.desc&limit=5000", timeout=10)
            costos_compras = {}
            if res_c and res_c.status_code == 200:
                for r in res_c.json():
                    cod = str(r.get("codigo_insumo") or "").strip()
                    cu = float(r.get("costo_unitario") or 0)
                    if cod and cod not in costos_compras and cu > 0:
                        costos_compras[cod] = cu

            insumos, _ = self.get_insumos(page=1, page_size=99999, fecha_corte=fecha_corte)
            val_inv = 0.0
            alertas = 0
            for i in insumos:
                stk = float(i.get("stock_actual") or i.get("stock_real") or 0)
                if stk > 0:
                    cod = str(i.get("codigo_insumo") or "").strip()
                    cu = costos_compras.get(cod) or float(i.get("costo_unitario") or 0)
                    val_inv += (stk * cu)
                if stk <= float(i.get("stock_minimo") or 5):
                    alertas += 1

            return {
                "valor_inventario": val_inv,
                "alertas_criticas": alertas
            }
        except Exception as ex:
            log_error("get_inventario_kpis", ex)
            return {"valor_inventario": 0.0, "alertas_criticas": 0}

    def get_kpis_por_categoria(self, fecha_corte=None) -> list:
        """Invoca RPC para extraer rendimiento y rotación agrupada por categoría."""
        try:
            payload = {"fecha_corte": fecha_corte} if fecha_corte else {}
            res = self.db.post("rpc/get_kpis_por_categoria_rpc", json_data=payload if payload else None, timeout=5)
            if res and res.status_code == 200:
                return res.json()
        except Exception:
            pass

        # Fallback local
        try:
            res_vista = self.db.get("vista_inventario_completo?select=categoria,costo_total_insumo,valor_ventas", timeout=10)
            if res_vista and res_vista.status_code == 200:
                data = res_vista.json()
                categorias = {}
                for item in data:
                    cat = item.get("categoria") or "SIN CATEGORIA"
                    if cat not in categorias:
                        categorias[cat] = {
                            "categoria": cat,
                            "costo_inventario": 0.0,
                            "ventas_totales": 0.0,
                            "rotacion": 0.0,
                            "rentabilidad": 0.0
                        }
                    categorias[cat]["costo_inventario"] += float(item.get("costo_total_insumo") or 0)
                    categorias[cat]["ventas_totales"] += float(item.get("valor_ventas") or 0)

                result = []
                for cat, vals in categorias.items():
                    costo_inv = vals["costo_inventario"]
                    vtas = vals["ventas_totales"]
                    if costo_inv > 0:
                        vals["rotacion"] = vtas / costo_inv
                    if vtas > 0:
                        vals["rentabilidad"] = 25.0
                    result.append(vals)

                result.sort(key=lambda x: x["ventas_totales"], reverse=True)
                return result
        except Exception as ex:
            log_error("get_kpis_por_categoria fallback", ex)

        return []

    def get_ajustes_inventario(self) -> list:
        """Obtiene el historial de ajustes cruzado con el catálogo y los períodos de cierre."""
        try:
            endpoint = "registro_ajustes_inventario?select=*,catalogo_insumos(nombre,categoria),periodos_inventario(mes_periodo)&order=fecha_ajuste.desc"
            res = self.db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                return res.json()
            return []
        except Exception as ex:
            log_error("get_ajustes_inventario", ex)
            return []

    def get_ajustes_mes(self, mes_actual: str, fecha_corte=None) -> list:
        """Invoca RPC get_ajustes_mes_rpc."""
        try:
            payload = {"mes_actual": mes_actual}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.db.post("rpc/get_ajustes_mes_rpc", json_data=payload, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                return data if data is not None else []
            return []
        except Exception as ex:
            log_error("get_ajustes_mes", ex)
            return []

    def insert_ajuste_individual(self, datos: dict | None = None, **kwargs) -> bool:
        """Inserta un nuevo registro de ajuste operativo."""
        try:
            payload = dict(datos or {})
            if kwargs:
                # Mapear posibles nombres de campos alternativos
                if "tipo_ajuste" in kwargs and "tipo_ajuste" not in payload: payload["tipo_ajuste"] = kwargs["tipo_ajuste"]
                if "codigo_insumo" in kwargs and "codigo_insumo" not in payload: payload["codigo_insumo"] = kwargs["codigo_insumo"]
                if "cantidad" in kwargs and "cantidad" not in payload: payload["cantidad"] = kwargs["cantidad"]
                if "costo_unitario" in kwargs and "costo_unitario_congelado" not in payload: payload["costo_unitario_congelado"] = kwargs["costo_unitario"]
                if "costo_total" in kwargs and "costo_total_ajuste" not in payload: payload["costo_total_ajuste"] = kwargs["costo_total"]
                if "motivo" in kwargs and "motivo_observacion" not in payload: payload["motivo_observacion"] = kwargs["motivo"]
                payload.update(kwargs)

            if "estado_registro" not in payload:
                payload["estado_registro"] = "VÁLIDO"

            res = self.db.post("registro_ajustes_inventario", json_data=payload, timeout=10)
            if res and res.status_code in (200, 201, 204):
                from core.audit_logger import registrar_accion
                tipo = payload.get("tipo_ajuste", "AJUSTE")
                cod = payload.get("codigo_insumo", "")
                cant = payload.get("cantidad", 0)
                motivo = payload.get("motivo_observacion", "Sin motivo")
                registrar_accion(
                    accion=f"Registro de ajuste de inventario ({tipo}) para insumo [{cod}]: {cant} unds (Motivo: {motivo})",
                    modulo="AJUSTES",
                    detalles=payload
                )
                return True
            return False
        except Exception as ex:
            log_error("insert_ajuste_individual", ex, {"datos": datos or kwargs})
            return False

    def anular_ajuste(self, id_ajuste: str) -> bool:
        """Cambia el estado del ajuste a ANULADO."""
        try:
            endpoint = f"registro_ajustes_inventario?id_ajuste=eq.{id_ajuste}"
            res = self.db.patch(endpoint, json_data={"estado_registro": "ANULADO"}, timeout=10)
            if res and res.status_code in (200, 204):
                from core.audit_logger import registrar_accion
                registrar_accion(
                    accion=f"Anulación de ajuste de inventario ID {id_ajuste}",
                    modulo="AJUSTES",
                    detalles={"id_ajuste": id_ajuste}
                )
                return True
            return False
        except Exception as ex:
            log_error("anular_ajuste", ex, {"id_ajuste": id_ajuste})
            return False

    def asegurar_insumos_existen(self, items_list: list):
        """Verifica la existencia de insumos en el catálogo y auto-registra los faltantes de manera centralizada."""
        if not items_list:
            return
        import urllib.parse
        codigos_entrantes = {
            str(x.get("codigo_insumo") or x.get("codigo_item") or "").strip()
            for x in items_list
            if str(x.get("codigo_insumo") or x.get("codigo_item") or "").strip()
        }
        if not codigos_entrantes:
            return

        existentes = set()
        chunk_size = 50
        codigos_arr = list(codigos_entrantes)
        for i in range(0, len(codigos_arr), chunk_size):
            chk = codigos_arr[i:i + chunk_size]
            c_str = ",".join([urllib.parse.quote(c) for c in chk])
            try:
                res = self.db.get(f"catalogo_insumos?select=codigo_insumo&codigo_insumo=in.({c_str})", timeout=8)
                if res and res.status_code == 200:
                    for row in res.json():
                        existentes.add(str(row["codigo_insumo"]).strip())
            except Exception as ex:
                logger.warning(f"Error consultando existencia de insumos chunk {i}: {ex}")

        faltantes = codigos_entrantes - existentes
        if faltantes:
            nuevos = []
            for cod in faltantes:
                nom = "INSUMO AUTO-REGISTRADO"
                for item in items_list:
                    if str(item.get("codigo_insumo") or item.get("codigo_item") or "").strip() == cod:
                        nom = item.get("descripcion") or item.get("nombre") or nom
                        break
                nuevos.append({
                    "codigo_insumo": cod,
                    "nombre": nom[:100],
                    "categoria": "DESECHABLES",
                    "costo_unitario": 0.0,
                    "precio_venta": 0.0,
                    "stock_actual": 0.0,
                    "stock_minimo": 5.0,
                    "estado": True,
                    "zona": "NO UBICADO",
                    "ubicacion": "BODEGA",
                    "tipo_unidad": "und"
                })
            try:
                res_post = self.db.post("catalogo_insumos", json_data=nuevos, timeout=10)
                if not (res_post and res_post.status_code in (200, 201, 204)):
                    logger.error(f"Fallo al auto-registrar insumos faltantes: {res_post.text if res_post else 'Sin respuesta'}")
                else:
                    logger.info(f"Auto-registrados {len(nuevos)} insumos nuevos en catálogo exitosamente")
            except Exception as ex:
                log_error("Error auto-registrando nuevos insumos", ex)
