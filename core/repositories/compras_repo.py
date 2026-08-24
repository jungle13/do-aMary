"""
Repositorio para la gestión de compras y entradas de insumos.
"""
import datetime
from core.database import BaseDatabase
from core.logger import get_logger, log_error

logger = get_logger("ComprasRepo")

class ComprasRepository:
    def __init__(self, db: BaseDatabase | None = None):
        self.db = db or BaseDatabase()

    def get_compras(
        self,
        page: int = 1,
        page_size: int = 15,
        search: str = "",
        fecha_corte: str | None = None,
        factura_filtro: str | None = None,
        proveedor_filtro: str | None = None
    ) -> tuple[list, int]:
        try:
            offset = (page - 1) * page_size
            select_query = "id_compra,fecha,numero_entrada,numero_factura,proveedor,codigo_insumo,cantidad,costo_unitario,iva,valor_iva,costo_total,estado_registro,catalogo_insumos(nombre)"
            endpoint = f"registro_compras?select={select_query}&estado_registro=eq.VÁLIDO&order=fecha.desc"

            if factura_filtro:
                endpoint += f"&or=(numero_entrada.eq.{factura_filtro},numero_factura.eq.{factura_filtro})"
            if proveedor_filtro:
                endpoint += f"&proveedor=eq.{proveedor_filtro}"

            res = self.db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                filtered = []
                for item in data:
                    f = str(item.get("fecha") or "")[:10]
                    if fecha_corte and f > fecha_corte:
                        continue

                    nom = str(item.get("catalogo_insumos", {}).get("nombre", "") if item.get("catalogo_insumos") else "").lower()
                    cod = str(item.get("codigo_insumo") or "").lower()
                    prov = str(item.get("proveedor") or "").lower()
                    fact = str(item.get("numero_factura") or "").lower()

                    if search:
                        s = search.lower()
                        if s not in nom and s not in cod and s not in prov and s not in fact:
                            continue

                    filtered.append(item)

                total_records = len(filtered)
                page_data = filtered[offset:offset + page_size]
                return page_data, total_records
            return [], 0
        except Exception as ex:
            log_error("get_compras", ex)
            return [], 0

    def get_historial_compras_dia(self, fecha_dia: str, agrupar_por: str = "FACTURA") -> list:
        items_resultado = []
        try:
            endpoint = f"registro_compras?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=numero_entrada,numero_factura,proveedor,costo_total,fecha,cantidad&order=fecha.desc"
            res_c = self.db.get(endpoint, timeout=10)
            if res_c and res_c.status_code == 200:
                data_c = res_c.json()
                if agrupar_por == "FACTURA":
                    agrupado = {}
                    for r in data_c:
                        ref = r.get("numero_entrada") or r.get("numero_factura") or "S/N"
                        if ref not in agrupado:
                            agrupado[ref] = {
                                "tipo": "COMPRA",
                                "ref": ref,
                                "factura": r.get("numero_factura") or ref,
                                "proveedor": r.get("proveedor") or "Clientes Varios",
                                "total": 0.0,
                                "unidades": 0.0,
                                "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                            }
                        agrupado[ref]["total"] += float(r.get("costo_total") or 0)
                        agrupado[ref]["unidades"] += float(r.get("cantidad") or 0)
                    items_resultado.extend(list(agrupado.values()))

                elif agrupar_por == "PROVEEDOR":
                    agrupado = {}
                    facturas_por_prov = {}
                    for r in data_c:
                        prov = r.get("proveedor") or "Clientes Varios"
                        ref_f = r.get("numero_factura") or r.get("numero_entrada") or "S/N"
                        if prov not in agrupado:
                            agrupado[prov] = {
                                "tipo": "PROVEEDOR_RESUMEN",
                                "ref": prov,
                                "proveedor": prov,
                                "facturas_cant": 0,
                                "total": 0.0,
                                "unidades": 0.0,
                                "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                            }
                            facturas_por_prov[prov] = set()
                        facturas_por_prov[prov].add(ref_f)
                        agrupado[prov]["total"] += float(r.get("costo_total") or 0)
                        agrupado[prov]["unidades"] += float(r.get("cantidad") or 0)

                    for prov in agrupado:
                        agrupado[prov]["facturas_cant"] = len(facturas_por_prov[prov])

                    items_resultado.extend(list(agrupado.values()))

            items_resultado.sort(key=lambda x: x["hora"], reverse=True)
            return items_resultado
        except Exception as ex:
            log_error(f"get_historial_compras_dia({fecha_dia})", ex)
            return []

    def _asegurar_insumos_existen(self, items_list: list):
        if not items_list:
            return
        codigos_entrantes = {str(x.get("codigo_insumo") or "").strip() for x in items_list if str(x.get("codigo_insumo") or "").strip()}
        if not codigos_entrantes:
            return
        existentes = set()
        chunk_size = 50
        codigos_arr = list(codigos_entrantes)
        for i in range(0, len(codigos_arr), chunk_size):
            chk = codigos_arr[i:i+chunk_size]
            c_str = ",".join(chk)
            try:
                res = self.db.get(f"catalogo_insumos?select=codigo_insumo&codigo_insumo=in.({c_str})", timeout=5)
                if res and res.status_code == 200:
                    for row in res.json():
                        existentes.add(str(row["codigo_insumo"]).strip())
            except Exception:
                pass
        
        faltantes = codigos_entrantes - existentes
        if faltantes:
            nuevos = []
            for cod in faltantes:
                nom = "INSUMO AUTO-REGISTRADO"
                for item in items_list:
                    if str(item.get("codigo_insumo") or "").strip() == cod:
                        nom = item.get("descripcion") or nom
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
                self.db.post("catalogo_insumos", json_data=nuevos, timeout=10)
            except Exception:
                pass

    def insert_compras(self, compras_list: list) -> bool:
        if not compras_list:
            return True
        try:
            self._asegurar_insumos_existen(compras_list)
            # Chunking para inserciones grandes
            chunk_size = 100
            for i in range(0, len(compras_list), chunk_size):
                chunk = compras_list[i:i + chunk_size]
                res = self.db.post("registro_compras", json_data=chunk, timeout=30)
                if not (res and res.status_code in (200, 201, 204)):
                    err = res.text if res else "No response"
                    logger.error(f"Error en insert_compras chunk {i}: {err}")
                    return False
            # Desduplicar y actualizar costo_unitario en catalogo_insumos en segundo plano
            costos_map = {}
            for c in compras_list:
                cod = str(c.get("codigo_insumo") or "").strip()
                costo_u = float(c.get("costo_unitario") or 0)
                if cod and costo_u > 0:
                    costos_map[cod] = costo_u

            def _actualizar_costos_async(c_map):
                for cod, cost in c_map.items():
                    try:
                        self.db.patch(f"catalogo_insumos?codigo_insumo=eq.{cod}", json_data={"costo_unitario": cost}, timeout=5)
                    except Exception:
                        pass

            if costos_map:
                import threading
                threading.Thread(target=_actualizar_costos_async, args=(costos_map,), daemon=True).start()

            from core.audit_logger import registrar_accion
            facs = list(set([str(c.get("numero_factura") or c.get("numero_entrada") or "") for c in compras_list if (c.get("numero_factura") or c.get("numero_entrada"))]))
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
        existentes = set()
        if lista_eas:
            chunk_size = 50
            for i in range(0, len(lista_eas), chunk_size):
                chunk = lista_eas[i:i + chunk_size]
                try:
                    eas_str = ",".join([str(x).strip() for x in chunk if str(x).strip()])
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
                    fac_str = ",".join([str(x).strip() for x in chunk if str(x).strip()])
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
        if not lista_entradas:
            return True
        try:
            for ref in lista_entradas:
                endpoint = f"registro_compras?or=(numero_entrada.eq.{ref},numero_factura.eq.{ref})"
                self.db.delete(endpoint, timeout=10)
            from core.audit_logger import registrar_accion
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
        try:
            hoy = datetime.date.today().strftime("%Y-%m-%d")
            mes_actual = hoy[:7]
            
            data = []
            offset = 0
            limit = 2500
            while True:
                headers = {"Range": f"{offset}-{offset + limit - 1}"}
                res = self.db.get("registro_compras?select=fecha,cantidad,costo_total,iva,valor_iva,estado_registro&estado_registro=eq.VÁLIDO", custom_headers=headers, timeout=15)
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
                if f == hoy:
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
            log_error("get_compras_summary", ex)
            return {"total_mes": 0, "total_hoy": 0, "cantidad_total": 0, "iva_mes": 0, "iva_hoy": 0}

    def update_compra_individual(self, id_compra: str, datos: dict) -> bool:
        try:
            endpoint = f"registro_compras?id_compra=eq.{id_compra}"
            res = self.db.patch(endpoint, json_data=datos, timeout=10)
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error(f"update_compra_individual({id_compra})", ex)
            return False

    def eliminar_compra_individual(self, id_compra: str) -> bool:
        try:
            endpoint = f"registro_compras?id_compra=eq.{id_compra}"
            res = self.db.delete(endpoint, timeout=10)
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error(f"eliminar_compra_individual({id_compra})", ex)
            return False
