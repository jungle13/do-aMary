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

    def insert_compras(self, compras_list: list) -> bool:
        if not compras_list:
            return True
        try:
            res = self.db.post("registro_compras", json_data=compras_list, timeout=15)
            if res and res.status_code in (200, 201, 204):
                return True
            err = res.text if res else "No response"
            logger.error(f"Error en insert_compras: {err}")
            return False
        except Exception as ex:
            log_error("insert_compras", ex)
            return False

    def get_entradas_existentes(self, lista_eas: list) -> set:
        if not lista_eas:
            return set()
        try:
            eas_str = ",".join(lista_eas)
            endpoint = f"registro_compras?select=numero_entrada&numero_entrada=in.({eas_str})"
            res = self.db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                return {item["numero_entrada"] for item in data if item.get("numero_entrada")}
            return set()
        except Exception as ex:
            log_error("get_entradas_existentes", ex)
            return set()

    def eliminar_compras_por_entradas(self, lista_entradas: list) -> bool:
        if not lista_entradas:
            return True
        try:
            for ref in lista_entradas:
                endpoint = f"registro_compras?or=(numero_entrada.eq.{ref},numero_factura.eq.{ref})"
                self.db.delete(endpoint, timeout=10)
            return True
        except Exception as ex:
            log_error("eliminar_compras_por_entradas", ex)
            return False

    def get_compras_summary(self, fecha_corte=None) -> dict:
        try:
            hoy = datetime.date.today().strftime("%Y-%m-%d")
            mes_actual = hoy[:7]
            endpoint = "registro_compras?select=fecha,cantidad,costo_total,iva,valor_iva,estado_registro&estado_registro=eq.VÁLIDO"
            res = self.db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
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
            return {"total_mes": 0, "total_hoy": 0, "cantidad_total": 0, "iva_mes": 0, "iva_hoy": 0}
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
