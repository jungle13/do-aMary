"""
Repositorio para la gestión de ventas, remisiones y facturas POS.
"""
import datetime
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from core.database import BaseDatabase
from core.logger import get_logger, log_error
from core.audit_logger import registrar_accion
from core.repositories.insumos_repo import InsumosRepository
from core.repositories.clientes_repo import ClientesRepository

logger = get_logger("VentasRepo")


class VentasRepository:
    def __init__(self, db: BaseDatabase | None = None):
        self.db = db or BaseDatabase()
        self.insumos_repo = InsumosRepository(self.db)
        self.clientes_repo = ClientesRepository(self.db)

    def get_ventas(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str = "",
        fecha_corte: str | None = None,
        categoria_filtro: str | None = None,
        factura_filtro: str | None = None,
        tipo_documento_filtro: str | None = None,
        fecha_dia: str | None = None
    ) -> tuple[list, int]:
        if categoria_filtro:
            endpoint = "registro_ventas?select=*,catalogo_insumos!inner(nombre,categoria)"
        else:
            endpoint = "registro_ventas?select=*,catalogo_insumos(nombre,categoria)"

        filtros = []
        if search:
            s_enc = urllib.parse.quote(search.strip())
            filtros.append(f"or=(codigo_insumo.ilike.*{s_enc}*,factura_no.ilike.*{s_enc}*,descripcion.ilike.*{s_enc}*)")

        if fecha_dia:
            fd_clean = fecha_dia.strip()
            filtros.append(f"fecha=gte.{fd_clean}T00:00:00&fecha=lte.{fd_clean}T23:59:59")
        elif fecha_corte:
            fc_clean = fecha_corte.strip()
            filtros.append(f"fecha=lte.{fc_clean}T23:59:59")

        if categoria_filtro:
            cat_enc = urllib.parse.quote(str(categoria_filtro).strip())
            filtros.append(f"catalogo_insumos.categoria=eq.{cat_enc}")

        if factura_filtro:
            fact_enc = urllib.parse.quote(str(factura_filtro).strip())
            filtros.append(f"factura_no.ilike.*{fact_enc}*")

        if tipo_documento_filtro and tipo_documento_filtro != "TODOS":
            doc_enc = urllib.parse.quote(str(tipo_documento_filtro).strip())
            filtros.append(f"tipo_documento=eq.{doc_enc}")

        if filtros:
            endpoint += "&" + "&".join(filtros)

        offset = (page - 1) * page_size
        endpoint += f"&order=fecha.desc,factura_no.desc&offset={offset}&limit={page_size}"

        headers = {"Prefer": "count=exact"}
        try:
            res = self.db.get(endpoint, custom_headers=headers, timeout=10)
            if res and res.status_code in (200, 206):
                data = res.json()
                content_range = res.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                err = res.text if res else "No response"
                logger.warning(f"Error en get_ventas: {err}")
                return [], 0
        except Exception as ex:
            log_error("get_ventas", ex)
            return [], 0

    def get_historial_ventas_dia(
        self,
        fecha_dia: str | None = None,
        agrupar_por: str = "CATEGORIA",
        tipo_documento: str | None = None
    ) -> list:
        items_resultado = []
        try:
            filtros = []
            if fecha_dia:
                filtros.append(f"fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59")
            if tipo_documento and tipo_documento != "TODOS":
                filtros.append(f"tipo_documento=eq.{urllib.parse.quote(tipo_documento.strip())}")

            query_filtros = ("&" + "&".join(filtros)) if filtros else ""
            endpoint = f"registro_ventas?select=factura_no,tipo_documento,descripcion,total,cantidad,codigo_insumo,fecha,catalogo_insumos(categoria,nombre){query_filtros}&order=fecha.desc"
            
            data_v = []
            offset = 0
            limit = 2500
            while True:
                headers = {"Range": f"{offset}-{offset + limit - 1}"}
                res_v = self.db.get(endpoint, custom_headers=headers, timeout=10)
                if not res_v or res_v.status_code not in (200, 206):
                    break
                chunk = res_v.json()
                if not chunk:
                    break
                data_v.extend(chunk)
                if len(chunk) < limit:
                    break
                offset += limit

            if agrupar_por == "CATEGORIA":
                agrupado = {}
                for r in data_v:
                    cat = r.get("catalogo_insumos", {}).get("categoria") if r.get("catalogo_insumos") else None
                    if not cat:
                        cat = "SIN CATEGORÍA"
                    if cat not in agrupado:
                        agrupado[cat] = {
                            "tipo": "CATEGORIA_RESUMEN",
                            "ref": cat,
                            "categoria": cat,
                            "total": 0.0,
                            "unidades": 0.0,
                            "items_count": 0
                        }
                    agrupado[cat]["total"] += float(r.get("total") or 0)
                    agrupado[cat]["unidades"] += float(r.get("cantidad") or 0)
                    agrupado[cat]["items_count"] += 1
                items_resultado.extend(list(agrupado.values()))

            elif agrupar_por == "FACTURA":
                agrupado = {}
                for r in data_v:
                    ref = r.get("factura_no") or "S/N"
                    tipo_doc = r.get("tipo_documento") or "Factura POS"
                    if ref not in agrupado:
                        agrupado[ref] = {
                            "tipo": "FACTURA_VENTA",
                            "ref": ref,
                            "factura": ref,
                            "subtipo": tipo_doc,
                            "total": 0.0,
                            "unidades": 0.0,
                            "hora": r.get("fecha", "")[:10]
                        }
                    agrupado[ref]["total"] += float(r.get("total") or 0)
                    agrupado[ref]["unidades"] += float(r.get("cantidad") or 0)
                items_resultado.extend(list(agrupado.values()))

            elif agrupar_por in ("TIPO_DOCUMENTO", "TIPO_DOC"):
                agrupado = {}
                facturas_por_tipo = {}
                for r in data_v:
                    tipo_doc = r.get("tipo_documento") or "Factura POS"
                    ref = r.get("factura_no") or "S/N"
                    if tipo_doc not in agrupado:
                        agrupado[tipo_doc] = {
                            "tipo": "TIPO_DOC_RESUMEN",
                            "tipo_documento": tipo_doc,
                            "total": 0.0,
                            "unidades": 0.0,
                            "facturas_cant": 0
                        }
                        facturas_por_tipo[tipo_doc] = set()
                    agrupado[tipo_doc]["total"] += float(r.get("total") or 0)
                    agrupado[tipo_doc]["unidades"] += float(r.get("cantidad") or 0)
                    facturas_por_tipo[tipo_doc].add(ref)

                for t_doc, d in agrupado.items():
                    d["facturas_cant"] = len(facturas_por_tipo.get(t_doc, []))

                items_resultado.extend(list(agrupado.values()))

            items_resultado.sort(key=lambda x: x["total"], reverse=True)
            return items_resultado
        except Exception as ex:
            log_error(f"get_historial_ventas_dia({fecha_dia})", ex)
            return []

    def get_ventas_existentes(self, lista_facturas: list) -> set:
        if not lista_facturas:
            return set()
        existentes = set()
        chunk_size = 50
        for i in range(0, len(lista_facturas), chunk_size):
            chunk = lista_facturas[i:i + chunk_size]
            try:
                facturas_str = ",".join([str(x).strip() for x in chunk if str(x).strip()])
                endpoint = f"registro_ventas?select=factura_no&factura_no=in.({facturas_str})"
                res = self.db.get(endpoint, timeout=10)
                if res and res.status_code == 200:
                    data = res.json()
                    for item in data:
                        if item.get("factura_no"):
                            existentes.add(str(item["factura_no"]))
            except Exception as ex:
                log_error("get_ventas_existentes", ex)
        return existentes

    def eliminar_ventas_origen(self, fecha: str, tipo_documento: str, pagina_origen: int) -> bool:
        try:
            endpoint = f"registro_ventas?fecha=gte.{fecha}T00:00:00&fecha=lte.{fecha}T23:59:59&tipo_documento=eq.{tipo_documento}&pagina_origen=eq.{pagina_origen}"
            res = self.db.delete(endpoint, timeout=10)
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error("eliminar_ventas_origen", ex)
            return False

    def eliminar_ventas_por_facturas(self, lista_facturas: list) -> bool:
        """Elimina ventas asociadas a las facturas especificadas utilizando lotes optimizados."""
        if not lista_facturas:
            return True
        try:
            chunk_size = 50
            for i in range(0, len(lista_facturas), chunk_size):
                chunk = lista_facturas[i:i + chunk_size]
                facturas_str = ",".join([urllib.parse.quote(str(f).strip()) for f in chunk if str(f).strip()])
                endpoint = f"registro_ventas?factura_no=in.({facturas_str})"
                self.db.delete(endpoint, timeout=10)

            registrar_accion(
                accion=f"Eliminación / Anulación de ventas para facturas: {', '.join(lista_facturas)}",
                modulo="VENTAS",
                detalles={"facturas_eliminadas": lista_facturas}
            )
            return True
        except Exception as ex:
            log_error("eliminar_ventas_por_facturas", ex)
            return False

    def insert_ventas(self, ventas_list: list) -> bool:
        """Inserta ventas por lotes optimizados y sincroniza clientes y catálogo masivamente."""
        if not ventas_list:
            return True

        # 1. Asegurar y sincronizar todos los clientes de las ventas en 1 sola consulta batch
        self.clientes_repo.asegurar_clientes_existen(ventas_list)

        # 2. Construir payload en memoria ultrarrápido
        payload = []
        for v in ventas_list:
            nom_cli = self.clientes_repo.normalizar_nombre_cliente(v.get("cliente") or v.get("nombre_cliente"))
            cli_obj = self.clientes_repo.get_or_create_cliente(nom_cli)
            id_cli = cli_obj.get("id_cliente")

            venta = {
                "fecha": v.get("fecha"),
                "factura_no": str(v.get("factura_no") or v.get("numero_factura", "")),
                "codigo_insumo": str(v.get("codigo_insumo") or v.get("codigo_item", "")),
                "descripcion": str(v.get("descripcion", "")),
                "cantidad": float(v.get("cantidad", 0) or 0),
                "subtotal": float(v.get("subtotal") if v.get("subtotal") is not None else (v.get("precio_unitario", 0) or 0)),
                "iva": float(v.get("iva", 0) or 0),
                "total": float(v.get("total") if v.get("total") is not None else (v.get("costo_total", 0) or 0)),
                "tipo_documento": str(v.get("tipo_documento", "Factura POS")),
                "pagina_origen": int(v.get("pagina_origen", 1)),
                "cliente": nom_cli
            }
            if id_cli:
                venta["id_cliente"] = id_cli
            payload.append(venta)

        try:
            # 3. Asegurar existencia de insumos en lote
            self.insumos_repo.asegurar_insumos_existen(payload)

            # 4. Inserción masiva en chunks grandes de 500 registros
            chunk_size = 500
            for i in range(0, len(payload), chunk_size):
                chunk = payload[i:i + chunk_size]
                res = self.db.post("registro_ventas", json_data=chunk, timeout=40)
                if not (res and res.status_code in (200, 201, 204)):
                    # Si falla por columna cliente/id_cliente aún no presente en Supabase, reintentar sin ellas
                    err = res.text if res else "No response"
                    logger.warning(f"Error en chunk con cliente ({err}), reintentando formato base...")
                    chunk_fallback = []
                    for item in chunk:
                        c_copy = dict(item)
                        c_copy.pop("cliente", None)
                        c_copy.pop("id_cliente", None)
                        chunk_fallback.append(c_copy)
                    res_fb = self.db.post("registro_ventas", json_data=chunk_fallback, timeout=40)
                    if not (res_fb and res_fb.status_code in (200, 201, 204)):
                        logger.error(f"Error crítico en insert_ventas: {res_fb.text if res_fb else 'No res'}")
                        return False

            # Desduplicar y actualizar precio_venta en catalogo_insumos concurrentemente
            precios_map = {}
            for v in payload:
                cod = str(v.get("codigo_insumo") or "").strip()
                cant = float(v.get("cantidad") or 0)
                subt = float(v.get("subtotal") or 0)
                if cod and cant > 0 and subt > 0:
                    precios_map[cod] = round(subt / cant, 2)

            def _actualizar_precio_item(item_tuple):
                cod, p_unit = item_tuple
                try:
                    cod_q = urllib.parse.quote(cod)
                    self.db.patch(f"catalogo_insumos?codigo_insumo=eq.{cod_q}", json_data={"precio_venta": p_unit}, timeout=5)
                except Exception as ex:
                    logger.warning(f"Error actualizando precio insumo {cod}: {ex}")

            def _actualizar_precios_worker(p_map):
                with ThreadPoolExecutor(max_workers=5) as executor:
                    executor.map(_actualizar_precio_item, p_map.items())

            if precios_map:
                threading.Thread(target=_actualizar_precios_worker, args=(precios_map,), daemon=True).start()

            facs = list(set([v.get("factura_no", "") for v in payload if v.get("factura_no")]))
            fac_txt = f" (Docs: {', '.join(facs[:3])}{'...' if len(facs)>3 else ''})" if facs else ""
            tot_monto = sum([v.get("total", 0) for v in payload])
            registrar_accion(
                accion=f"Guardado de ventas en BD: {len(payload)} registros{fac_txt} por ${tot_monto:,.0f}",
                modulo="VENTAS",
                detalles={"registros": len(payload), "total": tot_monto, "documentos": facs}
            )
            return True
        except Exception as ex:
            log_error("insert_ventas", ex)
            return False

    def get_ventas_summary(self, fecha_corte: str | None = None) -> dict:
        """
        Calcula el resumen financiero de ventas del mes y del día delegando la agregación a PostgreSQL.
        """
        try:
            payload = {"p_fecha_corte": fecha_corte} if fecha_corte else {}
            res = self.db.post("rpc/get_ventas_summary_rpc", json_data=payload, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    return data
            return self._summary_default()
        except Exception as ex:
            log_error("get_ventas_summary", ex)
            return self._summary_default()

    @staticmethod
    def _summary_default() -> dict:
        return {
            "total_historico": 0.0,
            "total_pos": 0.0,
            "total_remi": 0.0,
            "total_mes": 0.0,
            "total_hoy": 0.0,
            "hoy_pos": 0.0,
            "hoy_remi": 0.0,
            "iva_historico": 0.0,
            "iva_mes": 0.0,
            "iva_hoy": 0.0
        }

    def get_top_ventas_mes(self, limit: int = 10, fecha_corte=None) -> list:
        hoy = fecha_corte if fecha_corte else datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        try:
            payload = {"mes_actual": mes_actual, "limite": limit}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.db.post("rpc/get_top_ventas_mes_rpc", json_data=payload, timeout=10)
            if res and res.status_code == 200:
                return res.json()
            return []
        except Exception as ex:
            log_error("get_top_ventas_mes", ex)
            return []

    def get_tendencia_diaria(self, fecha_corte=None) -> dict:
        if fecha_corte:
            hoy = datetime.datetime.strptime(fecha_corte, "%Y-%m-%d").date()
        else:
            hoy = datetime.date.today()
        mes_actual = hoy.strftime("%Y-%m")
        tendencia = {f"{mes_actual}-{i:02d}": {"ventas": 0.0, "compras": 0.0} for i in range(1, hoy.day + 1)}

        try:
            payload = {"mes_actual": mes_actual}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.db.post("rpc/get_tendencia_diaria_rpc", json_data=payload, timeout=10)
            if res and res.status_code == 200:
                for row in res.json():
                    dia = row.get("dia")
                    if dia in tendencia:
                        tendencia[dia]["ventas"] = float(row.get("ventas", 0))
                        tendencia[dia]["compras"] = float(row.get("compras", 0))
        except Exception as ex:
            log_error("get_tendencia_diaria", ex)
        return tendencia

    def get_proyeccion_ventas(self, fecha_corte=None) -> float:
        try:
            res = self.db.get("vista_inventario_completo?select=stock_actual,precio_venta&stock_actual=gt.0", timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                total = sum(max(0.0, float(r.get("stock_actual") or 0)) * float(r.get("precio_venta") or 0) for r in data)
                return total
            # Fallback RPC
            payload = {"fecha_corte": fecha_corte} if fecha_corte else {}
            res = self.db.post("rpc/get_proyeccion_ventas_rpc", json_data=payload if payload else None, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                return float(data) if data is not None else 0.0
            return 0.0
        except Exception as ex:
            log_error("get_proyeccion_ventas", ex)
            return 0.0

    def insert_venta_individual(self, datos: dict) -> bool:
        try:
            res = self.db.post("registro_ventas", json_data=datos, timeout=10)
            if res and res.status_code in (200, 201, 204):
                from core.audit_logger import registrar_accion
                registrar_accion(
                    accion=f"Registro manual de venta Factura #{datos.get('factura_no', 'S/N')} (Insumo: [{datos.get('codigo_insumo')}], {datos.get('cantidad', 0)} unds, ${datos.get('total', 0):,.0f})",
                    modulo="VENTAS",
                    detalles=datos
                )
                return True
            return False
        except Exception as ex:
            log_error("insert_venta_individual", ex)
            return False

    def update_venta_individual(self, id_venta: str, datos: dict) -> bool:
        try:
            endpoint = f"registro_ventas?id_venta=eq.{id_venta}"
            res = self.db.patch(endpoint, json_data=datos, timeout=10)
            if res and res.status_code in (200, 204):
                from core.audit_logger import registrar_accion
                registrar_accion(
                    accion=f"Edición de registro de venta ID {id_venta} (Campos actualizados: {', '.join(datos.keys())})",
                    modulo="VENTAS",
                    detalles={"id_venta": id_venta, "cambios": datos}
                )
                return True
            return False
        except Exception as ex:
            log_error(f"update_venta_individual({id_venta})", ex)
            return False

    def eliminar_venta_individual(self, id_venta: str) -> bool:
        try:
            endpoint = f"registro_ventas?id_venta=eq.{id_venta}"
            res = self.db.delete(endpoint, timeout=10)
            if res and res.status_code in (200, 204):
                from core.audit_logger import registrar_accion
                registrar_accion(
                    accion=f"Eliminación / Anulación de venta individual ID {id_venta}",
                    modulo="VENTAS",
                    detalles={"id_venta": id_venta}
                )
                return True
            return False
        except Exception as ex:
            log_error(f"eliminar_venta_individual({id_venta})", ex)
            return False

    def get_historial_facturas_dia(self, fecha_dia: str) -> list:
        facturas = []
        try:
            # 1. Compras del día
            endpoint_c = f"registro_compras?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=numero_entrada,numero_factura,proveedor,costo_total,fecha&order=fecha.desc"
            res_c = self.db.get(endpoint_c, timeout=10)
            if res_c and res_c.status_code == 200:
                agrupado_c = {}
                for r in res_c.json():
                    ref = r.get("numero_entrada") or r.get("numero_factura")
                    if not ref:
                        continue
                    if ref not in agrupado_c:
                        agrupado_c[ref] = {
                            "tipo": "COMPRA",
                            "ref": ref,
                            "factura": r.get("numero_factura", "N/A"),
                            "proveedor": r.get("proveedor") or "Clientes Varios",
                            "total": 0.0,
                            "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                        }
                    agrupado_c[ref]["total"] += float(r.get("costo_total") or 0)
                facturas.extend(list(agrupado_c.values()))

            # 2. Ventas del día
            endpoint_v = f"registro_ventas?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=factura_no,tipo_documento,total,fecha&order=fecha.desc"
            res_v = self.db.get(endpoint_v, timeout=10)
            if res_v and res_v.status_code == 200:
                agrupado_v = {}
                for r in res_v.json():
                    ref = r.get("factura_no")
                    if not ref:
                        continue
                    if ref not in agrupado_v:
                        tipo_doc = r.get("tipo_documento") or "Factura POS"
                        agrupado_v[ref] = {
                            "tipo": f"VENTA_{'POS' if 'POS' in tipo_doc.upper() else 'REVISION'}",
                            "ref": ref,
                            "factura": ref,
                            "subtipo": tipo_doc,
                            "total": 0.0,
                            "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                        }
                    agrupado_v[ref]["total"] += float(r.get("total") or 0)
                facturas.extend(list(agrupado_v.values()))

            # 3. Ajustes del día
            endpoint_a = f"registro_ajustes_inventario?fecha_ajuste=gte.{fecha_dia}T00:00:00&fecha_ajuste=lte.{fecha_dia}T23:59:59&select=id_ajuste,tipo_ajuste,motivo_observacion,costo_total_ajuste,fecha_ajuste&order=fecha_ajuste.desc"
            res_a = self.db.get(endpoint_a, timeout=10)
            if res_a and res_a.status_code == 200:
                for r in res_a.json():
                    es_entrada = r.get("tipo_ajuste") in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
                    facturas.append({
                        "tipo": "AJUSTE_ENTRADA" if es_entrada else "AJUSTE_SALIDA",
                        "ref": r.get("id_ajuste"),
                        "factura": r.get("motivo_observacion") or "Ajuste Directo",
                        "total": float(r.get("costo_total_ajuste") or 0),
                        "hora": r.get("fecha_ajuste", "") if len(r.get("fecha_ajuste", "")) >= 16 else "12:00"
                    })
        except Exception as ex:
            log_error(f"get_historial_facturas_dia({fecha_dia})", ex)

        facturas.sort(key=lambda x: x["hora"], reverse=True)
        return facturas

    def get_codigos_factura_especifica(self, tipo: str, ref: str) -> list:
        try:
            if tipo == "COMPRA":
                res = self.db.get(f"registro_compras?numero_entrada=eq.{ref}&select=codigo_insumo", timeout=5)
            elif tipo.startswith("VENTA"):
                res = self.db.get(f"registro_ventas?factura_no=eq.{ref}&select=codigo_insumo", timeout=5)
            else:
                res = self.db.get(f"registro_ajustes_inventario?id_ajuste=eq.{ref}&select=codigo_insumo", timeout=5)

            if res and res.status_code == 200:
                return list(set([r.get("codigo_insumo") for r in res.json() if r.get("codigo_insumo")]))
        except Exception as ex:
            log_error(f"get_codigos_factura_especifica({tipo}, {ref})", ex)
        return []

    def get_ventas_documentos(
        self,
        page: int = 1,
        page_size: int = 15,
        search: str = "",
        fecha_corte: str | None = None,
        tipo_documento_filtro: str | None = None,
    ) -> tuple[list, int]:
        """
        Obtiene las ventas agrupadas a nivel de documento (Factura POS / Remisión),
        con totales de insumos, cantidad de unidades, subtotal, IVA y total de venta.
        """
        try:
            filtros = ["estado_registro=neq.ANULADO"]
            if fecha_corte and fecha_corte.strip():
                filtros.append(f"fecha=lte.{fecha_corte.strip()}T23:59:59")
            if tipo_documento_filtro and tipo_documento_filtro != "TODOS":
                td_enc = urllib.parse.quote(str(tipo_documento_filtro).strip())
                filtros.append(f"tipo_documento=eq.{td_enc}")

            query_filtros = "&" + "&".join(filtros)
            endpoint = (
                f"registro_ventas?select=id_venta,fecha,factura_no,tipo_documento,"
                f"codigo_insumo,descripcion,cantidad,subtotal,descuento,iva,total,"
                f"estado_registro,catalogo_insumos(nombre,categoria,tipo_unidad)"
                f"{query_filtros}&order=fecha.desc,factura_no.desc"
            )

            raw_ventas = self.db.get_all(endpoint, page_size=2000, timeout=15)
            if not raw_ventas:
                return [], 0

            agrupado = {}
            for r in raw_ventas:
                fac = str(r.get("factura_no") or "").strip()
                tipo_doc = str(r.get("tipo_documento") or "Factura POS").strip()
                fecha_str = str(r.get("fecha") or "")[:10]
                ref = fac if fac else "S/N"

                key = f"{ref}_{fecha_str}_{tipo_doc}"
                if key not in agrupado:
                    agrupado[key] = {
                        "doc_key": key,
                        "ref": ref,
                        "factura_no": fac,
                        "tipo_documento": tipo_doc,
                        "fecha": fecha_str,
                        "cant_insumos": 0,
                        "total_unidades": 0.0,
                        "subtotal_total": 0.0,
                        "descuento_total": 0.0,
                        "iva_total": 0.0,
                        "total_venta": 0.0,
                        "insumos": [],
                    }

                cant = float(r.get("cantidad") or 0.0)
                subt = float(r.get("subtotal") or 0.0)
                desc = float(r.get("descuento") or 0.0)
                iva = float(r.get("iva") or 0.0)
                tot = float(r.get("total") or 0.0)

                agrupado[key]["cant_insumos"] += 1
                agrupado[key]["total_unidades"] += cant
                agrupado[key]["subtotal_total"] += subt
                agrupado[key]["descuento_total"] += desc
                agrupado[key]["iva_total"] += iva
                agrupado[key]["total_venta"] += tot
                agrupado[key]["insumos"].append(r)

            docs_list = list(agrupado.values())

            # Búsqueda textual sobre los documentos
            if search and search.strip():
                s = search.strip().lower()
                docs_list = [
                    d for d in docs_list
                    if s in d["ref"].lower()
                    or s in d["tipo_documento"].lower()
                    or s in d["factura_no"].lower()
                    or any(
                        s in str(item.get("codigo_insumo") or "").lower()
                        or s in str(item.get("catalogo_insumos", {}).get("nombre") or item.get("descripcion") or "").lower()
                        for item in d["insumos"]
                    )
                ]

            total_records = len(docs_list)
            offset = max(0, (page - 1) * page_size)
            page_items = docs_list[offset:offset + page_size]

            return page_items, total_records
        except Exception as ex:
            log_error("get_ventas_documentos", ex)
            return [], 0

    def get_insumos_de_factura_venta(
        self,
        factura_no: str | None = None,
        tipo_documento: str | None = None,
    ) -> list:
        """Obtiene todas las líneas de insumos de una factura de venta o remisión."""
        try:
            filtros = ["estado_registro=neq.ANULADO"]
            if factura_no and factura_no.strip():
                fac_enc = urllib.parse.quote(factura_no.strip())
                filtros.append(f"factura_no=eq.{fac_enc}")

            if tipo_documento and tipo_documento.strip() and tipo_documento != "TODOS":
                td_enc = urllib.parse.quote(tipo_documento.strip())
                filtros.append(f"tipo_documento=eq.{td_enc}")

            query_filtros = "&" + "&".join(filtros)
            endpoint = (
                f"registro_ventas?select=id_venta,fecha,factura_no,tipo_documento,"
                f"codigo_insumo,descripcion,cantidad,subtotal,descuento,iva,total,"
                f"estado_registro,catalogo_insumos(nombre,categoria,tipo_unidad)"
                f"{query_filtros}&order=fecha.desc"
            )

            res = self.db.get_all(endpoint, timeout=12)
            return res or []
        except Exception as ex:
            log_error("get_insumos_de_factura_venta", ex)
            return []

    def eliminar_documento_ventas_completo(
        self,
        factura_no: str | None = None,
        tipo_documento: str | None = None,
    ) -> bool:
        """
        Elimina todas las líneas de una venta o remisión y reincorpora el stock
        de cada insumo al inventario disponible.
        """
        try:
            items = self.get_insumos_de_factura_venta(factura_no, tipo_documento)
            if not items:
                return False

            exito = True
            for it in items:
                id_v = it.get("id_venta")
                if id_v:
                    ok = self.eliminar_venta_individual(id_v)
                    if not ok:
                        exito = False

            if exito:
                registrar_accion(
                    accion=f"Eliminación completa de documento de venta {factura_no} ({len(items)} líneas y stock reincorporado)",
                    modulo="VENTAS",
                    detalles={"factura_no": factura_no, "tipo_documento": tipo_documento, "lineas": len(items)}
                )
            return exito
        except Exception as ex:
            log_error("eliminar_documento_ventas_completo", ex)
            return False
