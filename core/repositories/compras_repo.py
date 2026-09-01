"""
Repositorio para la gestión de compras y entradas de insumos.
"""
import datetime
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from core.database import BaseDatabase
from core.logger import get_logger, log_error
from core.audit_logger import registrar_accion
from core.repositories.insumos_repo import InsumosRepository

logger = get_logger("ComprasRepo")


class ComprasRepository:
    def __init__(self, db: BaseDatabase | None = None):
        self.db = db or BaseDatabase()
        self.insumos_repo = InsumosRepository(self.db)

    def get_compras(
        self,
        page: int = 1,
        page_size: int = 15,
        search: str = "",
        fecha_corte: str | None = None,
        factura_filtro: str | None = None,
        proveedor_filtro: str | None = None
    ) -> tuple[list, int]:
        """
        Obtiene las compras paginadas y filtradas directamente en el motor de base de datos.
        """
        try:
            offset = max(0, (page - 1) * page_size)
            select_query = (
                "id_compra,fecha,numero_entrada,numero_factura,proveedor,"
                "codigo_insumo,cantidad,costo_unitario,iva,valor_iva,costo_total,"
                "estado_registro,catalogo_insumos(nombre)"
            )
            filtros = ["estado_registro=eq.VÁLIDO"]

            if fecha_corte:
                fc_clean = fecha_corte.strip()
                filtros.append(f"fecha=lte.{fc_clean}T23:59:59")

            if factura_filtro:
                fac_q = urllib.parse.quote(str(factura_filtro).strip())
                filtros.append(f"or=(numero_entrada.eq.{fac_q},numero_factura.eq.{fac_q})")

            if proveedor_filtro and proveedor_filtro != "TODOS":
                prov_q = urllib.parse.quote(str(proveedor_filtro).strip())
                filtros.append(f"proveedor=eq.{prov_q}")

            if search and search.strip():
                s_val = search.strip()
                s_q = urllib.parse.quote(f"*{s_val}*")
                filtros.append(
                    f"or=(codigo_insumo.ilike.{s_q},proveedor.ilike.{s_q},"
                    f"numero_factura.ilike.{s_q},numero_entrada.ilike.{s_q})"
                )

            query_filtros = "&" + "&".join(filtros)
            endpoint = f"registro_compras?select={select_query}{query_filtros}&order=fecha.desc"
            
            headers = {
                "Range": f"{offset}-{offset + page_size - 1}",
                "Prefer": "count=exact"
            }

            res = self.db.get(endpoint, custom_headers=headers, timeout=12)
            if res and res.status_code in (200, 206):
                data = res.json()
                total_records = len(data)
                
                # Extraer total exacto desde header Content-Range (ej. '0-14/1250')
                cr = res.headers.get("Content-Range") or res.headers.get("content-range")
                if cr and "/" in cr:
                    try:
                        total_records = int(cr.split("/")[-1])
                    except (ValueError, IndexError):
                        pass

                return data, total_records

            return [], 0
        except Exception as ex:
            log_error("get_compras", ex)
            return [], 0

    def get_compras_totales_filtrados(
        self,
        search: str = "",
        fecha_corte: str | None = None,
        factura_filtro: str | None = None,
        proveedor_filtro: str | None = None
    ) -> dict:
        """
        Calcula los totales acumulados (cantidad, iva, costo_total) para los filtros aplicados vía RPC.
        """
        try:
            payload = {
                "p_search": search.strip() if search else None,
                "p_fecha_corte": fecha_corte.strip() if fecha_corte else None,
                "p_factura": factura_filtro.strip() if factura_filtro else None,
                "p_proveedor": proveedor_filtro.strip() if (proveedor_filtro and proveedor_filtro != "TODOS") else None
            }
            res = self.db.post("rpc/fn_totales_compras", json_data=payload, timeout=8)
            if res and res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    return {
                        "total_cantidad": float(data.get("total_cantidad") or 0.0),
                        "total_iva": float(data.get("total_iva") or 0.0),
                        "total_costo": float(data.get("total_costo") or 0.0),
                        "total_registros": int(data.get("total_registros") or 0)
                    }
        except Exception as ex:
            log_error("get_compras_totales_filtrados", ex)

        return {"total_cantidad": 0.0, "total_iva": 0.0, "total_costo": 0.0, "total_registros": 0}

    def get_proveedores_unicos(self) -> list:
        try:
            res = self.db.get("registro_compras?select=proveedor&estado_registro=eq.VÁLIDO&limit=5000", timeout=10)
            if res and res.status_code == 200:
                provs = sorted(list({str(x.get("proveedor")).strip() for x in res.json() if x.get("proveedor") and str(x.get("proveedor")).strip()}))
                return provs
            return []
        except Exception as ex:
            log_error("get_proveedores_unicos", ex)
            return []

    def get_historial_compras_dia(
        self,
        fecha_dia: str | None = None,
        agrupar_por: str = "FACTURA",
        proveedor_filtro: str | None = None
    ) -> list:
        items_resultado = []
        try:
            filtros = ["estado_registro=eq.VÁLIDO"]
            if fecha_dia:
                filtros.append(f"fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59")
            if proveedor_filtro and proveedor_filtro != "TODOS":
                import urllib.parse
                filtros.append(f"proveedor=eq.{urllib.parse.quote(proveedor_filtro.strip())}")

            query_filtros = ("&" + "&".join(filtros)) if filtros else ""
            endpoint = f"registro_compras?select=numero_entrada,numero_factura,proveedor,costo_total,fecha,cantidad{query_filtros}&order=fecha.desc"
            
            data_c = []
            offset = 0
            limit = 2500
            while True:
                headers = {"Range": f"{offset}-{offset + limit - 1}"}
                res_c = self.db.get(endpoint, custom_headers=headers, timeout=10)
                if not res_c or res_c.status_code not in (200, 206):
                    break
                chunk = res_c.json()
                if not chunk:
                    break
                data_c.extend(chunk)
                if len(chunk) < limit:
                    break
                offset += limit

            if agrupar_por == "FACTURA":
                agrupado = {}
                for r in data_c:
                    ref = r.get("numero_entrada") or r.get("numero_factura") or "S/N"
                    if ref not in agrupado:
                        agrupado[ref] = {
                            "tipo": "COMPRA",
                            "ref": ref,
                            "factura": r.get("numero_factura") or ref,
                            "proveedor": r.get("proveedor") or "Varios",
                            "total": 0.0,
                            "unidades": 0.0,
                            "hora": r.get("fecha", "")[:10]
                        }
                    agrupado[ref]["total"] += float(r.get("costo_total") or 0)
                    agrupado[ref]["unidades"] += float(r.get("cantidad") or 0)
                items_resultado.extend(list(agrupado.values()))

            elif agrupar_por == "PROVEEDOR":
                agrupado = {}
                facturas_por_prov = {}
                for r in data_c:
                    prov = r.get("proveedor") or "Varios"
                    ref_f = r.get("numero_factura") or r.get("numero_entrada") or "S/N"
                    if prov not in agrupado:
                        agrupado[prov] = {
                            "tipo": "PROVEEDOR_RESUMEN",
                            "ref": prov,
                            "proveedor": prov,
                            "facturas_cant": 0,
                            "total": 0.0,
                            "unidades": 0.0,
                            "hora": r.get("fecha", "")[:10]
                        }
                        facturas_por_prov[prov] = set()
                    facturas_por_prov[prov].add(ref_f)
                    agrupado[prov]["total"] += float(r.get("costo_total") or 0)
                    agrupado[prov]["unidades"] += float(r.get("cantidad") or 0)

                for prov in agrupado:
                    agrupado[prov]["facturas_cant"] = len(facturas_por_prov[prov])

                items_resultado.extend(list(agrupado.values()))

            items_resultado.sort(key=lambda x: x["total"], reverse=True)
            return items_resultado
        except Exception as ex:
            log_error(f"get_historial_compras_dia({fecha_dia})", ex)
            return []

    def insert_compras(self, compras_list: list) -> bool:
        """Inserta compras por lotes y actualiza los costos del catálogo concurrentemente en background."""
        if not compras_list:
            return True
        try:
            self.insumos_repo.asegurar_insumos_existen(compras_list)

            # Chunking para inserciones grandes
            chunk_size = 100
            for i in range(0, len(compras_list), chunk_size):
                chunk = compras_list[i:i + chunk_size]
                res = self.db.post("registro_compras", json_data=chunk, timeout=30)
                if not (res and res.status_code in (200, 201, 204)):
                    err = res.text if res else "No response"
                    logger.error(f"Error en insert_compras chunk {i}: {err}")
                    return False

            # Desduplicar y actualizar costo_unitario en catalogo_insumos concurrentemente
            costos_map = {}
            for c in compras_list:
                cod = str(c.get("codigo_insumo") or "").strip()
                costo_u = float(c.get("costo_unitario") or 0)
                if cod and costo_u > 0:
                    costos_map[cod] = costo_u

            def _actualizar_costo_item(item_tuple):
                cod, cost = item_tuple
                try:
                    cod_q = urllib.parse.quote(cod)
                    self.db.patch(f"catalogo_insumos?codigo_insumo=eq.{cod_q}", json_data={"costo_unitario": cost}, timeout=5)
                except Exception as ex:
                    logger.warning(f"Error actualizando costo insumo {cod}: {ex}")

            def _actualizar_costos_worker(c_map):
                with ThreadPoolExecutor(max_workers=5) as executor:
                    executor.map(_actualizar_costo_item, c_map.items())

            if costos_map:
                threading.Thread(target=_actualizar_costos_worker, args=(costos_map,), daemon=True).start()

            facs = list(set([
                str(c.get("numero_factura") or c.get("numero_entrada") or "") 
                for c in compras_list 
                if (c.get("numero_factura") or c.get("numero_entrada"))
            ]))
            fac_txt = f" (Docs: {', '.join(facs[:3])}{'...' if len(facs)>3 else ''})" if facs else ""
            tot_monto = sum([float(c.get("costo_total") or 0) for c in compras_list])
            registrar_accion(
                accion=f"Guardado de compras en BD: {len(compras_list)} registros{fac_txt} por ${tot_monto:,.0f}",
                modulo="COMPRAS",
                detalles={"registros": len(compras_list), "total": tot_monto, "documentos": facs}
            )
            return True
        except Exception as ex:
            log_error("insert_compras", ex)
            return False

    def get_entradas_existentes(self, lista_eas: list, lista_facturas: list = None) -> set:
        """Consulta documentos de entrada y facturas ya registradas en la base de datos."""
        existentes = set()
        if lista_eas:
            chunk_size = 50
            for i in range(0, len(lista_eas), chunk_size):
                chunk = lista_eas[i:i + chunk_size]
                try:
                    eas_str = ",".join([urllib.parse.quote(str(x).strip()) for x in chunk if str(x).strip()])
                    endpoint = f"registro_compras?select=numero_entrada&numero_entrada=in.({eas_str})"
                    res = self.db.get(endpoint, timeout=10)
                    if res and res.status_code == 200:
                        data = res.json()
                        for item in data:
                            if item.get("numero_entrada"):
                                existentes.add(str(item["numero_entrada"]))
                except Exception as ex:
                    log_error("get_entradas_existentes", ex)

        if lista_facturas:
            chunk_size = 50
            for i in range(0, len(lista_facturas), chunk_size):
                chunk = lista_facturas[i:i + chunk_size]
                try:
                    fac_str = ",".join([urllib.parse.quote(str(x).strip()) for x in chunk if str(x).strip()])
                    endpoint = f"registro_compras?select=numero_factura&numero_factura=in.({fac_str})"
                    res = self.db.get(endpoint, timeout=10)
                    if res and res.status_code == 200:
                        data = res.json()
                        for item in data:
                            if item.get("numero_factura"):
                                existentes.add(str(item["numero_factura"]))
                except Exception as ex:
                    log_error("get_entradas_existentes_fac", ex)
        return existentes

    def eliminar_compras_por_entradas(self, lista_entradas: list) -> bool:
        """Elimina compras asociadas a los números de factura o entrada especificados."""
        if not lista_entradas:
            return True
        try:
            for ref in lista_entradas:
                ref_q = urllib.parse.quote(str(ref).strip())
                endpoint = f"registro_compras?or=(numero_entrada.eq.{ref_q},numero_factura.eq.{ref_q})"
                self.db.delete(endpoint, timeout=10)

            registrar_accion(
                accion=f"Eliminación / Anulación de compras para documentos: {', '.join(lista_entradas)}",
                modulo="COMPRAS",
                detalles={"referencias_eliminadas": lista_entradas}
            )
            return True
        except Exception as ex:
            log_error("eliminar_compras_por_entradas", ex)
            return False

    def get_compras_summary(self, fecha_corte=None) -> dict:
        """Calcula el resumen financiero de compras del mes y del día de corte."""
        try:
            payload = {"p_fecha_corte": fecha_corte} if fecha_corte else {}
            res = self.db.post("rpc/get_compras_summary_rpc", json_data=payload, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    return data
        except Exception as ex:
            log_error("get_compras_summary RPC", ex)

        # Fallback local
        try:
            corte_str = str(fecha_corte).strip()[:10] if fecha_corte else datetime.date.today().strftime("%Y-%m-%d")
            mes_actual = corte_str[:7]
            
            data = []
            offset = 0
            limit = 2500
            while True:
                headers = {"Range": f"{offset}-{offset + limit - 1}"}
                res = self.db.get(
                    "registro_compras?select=fecha,cantidad,costo_total,iva,valor_iva,estado_registro&estado_registro=eq.VÁLIDO", 
                    custom_headers=headers, 
                    timeout=15
                )
                if not res or res.status_code not in (200, 206):
                    break
                chunk = res.json()
                if not chunk:
                    break
                data.extend(chunk)
                if len(chunk) < limit:
                    break
                offset += limit

            total_mes = 0.0
            total_hoy = 0.0
            cant_tot = 0.0
            iva_mes = 0.0
            iva_hoy = 0.0

            for c in data:
                f = str(c.get("fecha") or "")[:10]
                if fecha_corte and f > fecha_corte:
                    continue
                monto = float(c.get("costo_total") or 0)
                cant = float(c.get("cantidad") or 0)
                iva_val = float(c.get("iva") or c.get("valor_iva") or 0)

                if f.startswith(mes_actual):
                    total_mes += monto
                    iva_mes += iva_val
                if f == corte_str:
                    total_hoy += monto
                    iva_hoy += iva_val
                cant_tot += cant

            return {
                "total_mes": total_mes,
                "total_hoy": total_hoy,
                "cantidad_total": cant_tot,
                "iva_mes": iva_mes,
                "iva_hoy": iva_hoy
            }
        except Exception as ex:
            log_error("get_compras_summary fallback", ex)
            return {"total_mes": 0, "total_hoy": 0, "cantidad_total": 0, "iva_mes": 0, "iva_hoy": 0}

    def update_compra_individual(self, id_compra: str, datos: dict) -> bool:
        """Actualiza un registro individual de compra."""
        try:
            id_q = urllib.parse.quote(str(id_compra).strip())
            endpoint = f"registro_compras?id_compra=eq.{id_q}"
            res = self.db.patch(endpoint, json_data=datos, timeout=10)
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error(f"update_compra_individual({id_compra})", ex)
            return False

    def eliminar_compra_individual(self, id_compra: str) -> bool:
        """Elimina un registro individual de compra por su ID único."""
        try:
            id_q = urllib.parse.quote(str(id_compra).strip())
            endpoint = f"registro_compras?id_compra=eq.{id_q}"
            res = self.db.delete(endpoint, timeout=10)
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error(f"eliminar_compra_individual({id_compra})", ex)
            return False

    def get_compras_documentos(
        self,
        page: int = 1,
        page_size: int = 15,
        search: str = "",
        fecha_corte: str | None = None,
        proveedor_filtro: str | None = None,
        tipo_doc_filtro: str | None = None,
    ) -> tuple[list, int]:
        """
        Obtiene las compras agrupadas a nivel de documento (Factura / Remisión / Entrada),
        con totales de insumos, costo total e IVA total.
        """
        try:
            filtros = ["estado_registro=neq.ANULADO"]
            if fecha_corte and fecha_corte.strip():
                filtros.append(f"fecha=lte.{fecha_corte.strip()}T23:59:59")
            if proveedor_filtro and proveedor_filtro != "TODOS":
                prov_q = urllib.parse.quote(str(proveedor_filtro).strip())
                filtros.append(f"proveedor=eq.{prov_q}")

            query_filtros = "&" + "&".join(filtros)
            endpoint = (
                f"registro_compras?select=id_compra,fecha,numero_entrada,numero_factura,"
                f"proveedor,codigo_insumo,cantidad,costo_unitario,iva,valor_iva,costo_total,"
                f"estado_registro,catalogo_insumos(nombre)"
                f"{query_filtros}&order=fecha.desc"
            )

            raw_compras = self.db.get_all(endpoint, page_size=2000, timeout=15)
            if not raw_compras:
                return [], 0

            agrupado = {}
            for r in raw_compras:
                ea = str(r.get("numero_entrada") or "").strip()
                fac = str(r.get("numero_factura") or "").strip()
                prov = str(r.get("proveedor") or "Varios").strip()
                fecha_str = str(r.get("fecha") or "")[:10]
                ref = ea if ea else (fac if fac else "S/N")
                tipo_doc = "EA" if ea else ("FAC" if fac else "S/D")

                # Filtro por tipo de documento si está activo
                if tipo_doc_filtro and tipo_doc_filtro != "TODOS":
                    if tipo_doc_filtro in ("EA", "REMISIÓN", "REMISIÓN (EA)") and tipo_doc != "EA":
                        continue
                    if tipo_doc_filtro in ("FAC", "FACTURA", "FACTURA POS (FAC)") and tipo_doc != "FAC":
                        continue

                key = f"{ref}_{prov}_{fecha_str}"
                if key not in agrupado:
                    agrupado[key] = {
                        "doc_key": key,
                        "ref": ref,
                        "tipo_doc": tipo_doc,
                        "numero_entrada": ea,
                        "numero_factura": fac,
                        "proveedor": prov,
                        "fecha": fecha_str,
                        "cant_insumos": 0,
                        "total_unidades": 0.0,
                        "costo_total": 0.0,
                        "iva_total": 0.0,
                        "insumos": [],
                    }

                cant = float(r.get("cantidad") or 0.0)
                costo = float(r.get("costo_total") or 0.0)
                iva = float(r.get("valor_iva") or r.get("iva") or 0.0)

                agrupado[key]["cant_insumos"] += 1
                agrupado[key]["total_unidades"] += cant
                agrupado[key]["costo_total"] += costo
                agrupado[key]["iva_total"] += iva
                agrupado[key]["insumos"].append(r)

            docs_list = list(agrupado.values())

            # Búsqueda textual sobre los documentos
            if search and search.strip():
                s = search.strip().lower()
                docs_list = [
                    d for d in docs_list
                    if s in d["ref"].lower()
                    or s in d["proveedor"].lower()
                    or s in d["numero_entrada"].lower()
                    or s in d["numero_factura"].lower()
                    or any(s in str(item.get("codigo_insumo") or "").lower() or
                           s in str(item.get("catalogo_insumos", {}).get("nombre") or "").lower()
                           for item in d["insumos"])
                ]

            total_records = len(docs_list)
            offset = max(0, (page - 1) * page_size)
            page_items = docs_list[offset:offset + page_size]

            return page_items, total_records
        except Exception as ex:
            log_error("get_compras_documentos", ex)
            return [], 0

    def get_insumos_de_documento(
        self,
        numero_entrada: str | None = None,
        numero_factura: str | None = None,
        proveedor: str | None = None,
    ) -> list:
        """Obtiene todas las líneas de insumos de una entrada o factura."""
        try:
            filtros = ["estado_registro=neq.ANULADO"]
            or_parts = []
            if numero_entrada and numero_entrada.strip():
                or_parts.append(f"numero_entrada.eq.{urllib.parse.quote(numero_entrada.strip())}")
            if numero_factura and numero_factura.strip():
                or_parts.append(f"numero_factura.eq.{urllib.parse.quote(numero_factura.strip())}")

            if or_parts:
                filtros.append(f"or=({','.join(or_parts)})")

            if proveedor and proveedor.strip() and proveedor != "TODOS":
                filtros.append(f"proveedor=eq.{urllib.parse.quote(proveedor.strip())}")

            query_filtros = "&" + "&".join(filtros)
            endpoint = (
                f"registro_compras?select=id_compra,fecha,numero_entrada,numero_factura,"
                f"proveedor,codigo_insumo,cantidad,costo_unitario,iva,valor_iva,costo_total,"
                f"estado_registro,catalogo_insumos(nombre,tipo_unidad)"
                f"{query_filtros}&order=fecha.desc"
            )

            res = self.db.get_all(endpoint, timeout=12)
            return res or []
        except Exception as ex:
            log_error("get_insumos_de_documento", ex)
            return []

    def eliminar_documento_compras_completo(
        self,
        numero_entrada: str | None = None,
        numero_factura: str | None = None,
        proveedor: str | None = None,
    ) -> bool:
        """Elimina todos los registros de compra pertenecientes a un documento."""
        try:
            insumos = self.get_insumos_de_documento(numero_entrada, numero_factura, proveedor)
            if not insumos:
                return True

            or_parts = []
            if numero_entrada and numero_entrada.strip():
                or_parts.append(f"numero_entrada.eq.{urllib.parse.quote(numero_entrada.strip())}")
            if numero_factura and numero_factura.strip():
                or_parts.append(f"numero_factura.eq.{urllib.parse.quote(numero_factura.strip())}")

            if not or_parts:
                return False

            filtros = [f"or=({','.join(or_parts)})"]
            if proveedor and proveedor.strip() and proveedor != "TODOS":
                filtros.append(f"proveedor=eq.{urllib.parse.quote(proveedor.strip())}")

            endpoint = f"registro_compras?{'&'.join(filtros)}"
            res = self.db.delete(endpoint, timeout=12)

            ref_doc = numero_entrada or numero_factura or "S/N"
            registrar_accion(
                accion=f"Eliminación de documento de compra completo: {ref_doc} ({len(insumos)} insumos)",
                modulo="COMPRAS",
                detalles={"documento": ref_doc, "proveedor": proveedor, "cantidad_insumos": len(insumos)}
            )
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error("eliminar_documento_compras_completo", ex)
            return False
