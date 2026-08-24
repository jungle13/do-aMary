"""
Repositorio para cierres mensuales, auditorías, snapshots y conteos físicos.
"""
from core.database import BaseDatabase
from core.logger import get_logger, log_error

logger = get_logger("CierresRepo")

class CierresRepository:
    def __init__(self, db: BaseDatabase | None = None):
        self.db = db or BaseDatabase()

    def get_periodos_inventario(self) -> list:
        try:
            res = self.db.get("periodos_inventario?select=*&order=mes_periodo.desc", timeout=10)
            if res and res.status_code == 200:
                return res.json()
            return []
        except Exception as ex:
            log_error("get_periodos_inventario", ex)
            return []

    def get_datos_conteo_inicial(self, mes_seleccionado: str) -> list:
        try:
            year, month = map(int, mes_seleccionado.split("-"))
            if month == 1:
                mes_anterior = f"{year - 1}-12"
            else:
                mes_anterior = f"{year}-{month - 1:02d}"
        except Exception as ex:
            log_error(f"get_datos_conteo_inicial parsing {mes_seleccionado}", ex)
            return []

        # 1. Catálogo
        catalogo = []
        try:
            res_cat = self.db.get("catalogo_insumos?select=codigo_insumo,nombre,categoria", timeout=10)
            if res_cat and res_cat.status_code == 200:
                catalogo = res_cat.json()
        except Exception as ex:
            log_error("get_datos_conteo_inicial (catalogo)", ex)

        # 2. Cierre mes anterior
        cierre_anterior = {}
        try:
            endpoint_ant = f"registro_auditorias_cierres?tipo_registro=eq.CIERRE_MENSUAL&fecha_cierre=gte.{mes_anterior}-01&fecha_cierre=lte.{mes_anterior}-31&select=codigo_insumo,cantidad_fisica"
            res_ant = self.db.get(endpoint_ant, timeout=10)
            if res_ant and res_ant.status_code == 200:
                for r in res_ant.json():
                    cierre_anterior[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except Exception as ex:
            log_error("get_datos_conteo_inicial (cierre_anterior)", ex)

        # 3. Inicial mes actual
        inicio_actual = {}
        try:
            endpoint_act = f"registro_auditorias_cierres?tipo_registro=eq.INVENTARIO_INICIAL&fecha_cierre=gte.{mes_seleccionado}-01&fecha_cierre=lte.{mes_seleccionado}-31&select=codigo_insumo,cantidad_fisica"
            res_act = self.db.get(endpoint_act, timeout=10)
            if res_act and res_act.status_code == 200:
                for r in res_act.json():
                    inicio_actual[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except Exception as ex:
            log_error("get_datos_conteo_inicial (inicio_actual)", ex)

        resultado = []
        for c in catalogo:
            codigo = c.get("codigo_insumo")
            if not codigo:
                continue
            resultado.append({
                "codigo_insumo": codigo,
                "nombre": c.get("nombre"),
                "categoria": c.get("categoria"),
                "cierre_mes_anterior": cierre_anterior.get(codigo, 0),
                "stock_inicial_actual": inicio_actual.get(codigo, 0),
            })
        return resultado

    def upsert_conteos_iniciales(self, registros: list) -> bool:
        if not registros:
            return True
        try:
            fecha_cierre = registros[0].get("fecha_cierre")
            tipo_registro = registros[0].get("tipo_registro")
            codigos = [r["codigo_insumo"] for r in registros if "codigo_insumo" in r]

            if codigos:
                codigos_str = ",".join(codigos)
                endpoint_exist = f"registro_auditorias_cierres?fecha_cierre=eq.{fecha_cierre}&tipo_registro=eq.{tipo_registro}&codigo_insumo=in.({codigos_str})&select=id_auditoria,codigo_insumo"
                res_exist = self.db.get(endpoint_exist, timeout=10)
                if res_exist and res_exist.status_code == 200:
                    existentes = {item["codigo_insumo"]: item["id_auditoria"] for item in res_exist.json() if "id_auditoria" in item}
                    for r in registros:
                        if r["codigo_insumo"] in existentes:
                            r["id_auditoria"] = existentes[r["codigo_insumo"]]
        except Exception as ex:
            log_error("upsert_conteos_iniciales (busqueda existentes)", ex)

        headers = {"Prefer": "resolution=merge-duplicates"}
        try:
            res = self.db.post("registro_auditorias_cierres", json_data=registros, custom_headers=headers, timeout=10)
            return bool(res and res.status_code in (200, 201, 204))
        except Exception as ex:
            log_error("upsert_conteos_iniciales", ex)
            return False

    def iniciar_snapshot_cierre(self, mes_periodo: str) -> dict:
        try:
            res = self.db.post("rpc/fn_snapshot_cierre_mensual", json_data={"p_mes": mes_periodo}, timeout=10)
            if res and res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text if res else "No response"}
        except Exception as ex:
            log_error(f"iniciar_snapshot_cierre({mes_periodo})", ex)
            return {"exito": False, "error": str(ex)}

    def obtener_estado_cierre(self, mes_periodo: str) -> dict:
        """Obtiene el estado completo y consolidado del periodo con los conteos físicos y diferencias en tiempo real."""
        try:
            # 1. Obtener Periodo
            res_p = self.db.get(f"periodos_inventario?mes_periodo=eq.{mes_periodo}", timeout=10)
            periodo = res_p.json()[0] if res_p and res_p.status_code == 200 and res_p.json() else {}
            id_periodo = periodo.get("id_periodo")

            # 2. Obtener Catálogo Completo
            res_cat = self.db.get("catalogo_insumos?select=codigo_insumo,nombre,categoria,stock_actual,costo_unitario,precio_venta,tipo_unidad&estado=eq.true&order=nombre.asc&limit=3500", timeout=15)
            catalogo = res_cat.json() if res_cat and res_cat.status_code == 200 else []

            # 3. Obtener Conteos Físicos de Auditoría
            endpoint_aud = "registro_auditorias_cierres?limit=3500"
            if id_periodo:
                endpoint_aud = f"registro_auditorias_cierres?id_periodo=eq.{id_periodo}&limit=3500"
            res_aud = self.db.get(endpoint_aud, timeout=15)
            aud_list = res_aud.json() if res_aud and res_aud.status_code == 200 else []

            # 3.5. Obtener Ajustes válidos para el periodo
            endpoint_ajustes = "registro_ajustes_inventario?estado_registro=eq.VÁLIDO&limit=3500"
            if id_periodo:
                endpoint_ajustes = f"registro_ajustes_inventario?id_periodo=eq.{id_periodo}&estado_registro=eq.VÁLIDO&limit=3500"
            res_ajustes = self.db.get(endpoint_ajustes, timeout=10)
            ajustes_list = res_ajustes.json() if res_ajustes and res_ajustes.status_code == 200 else []
            ajustados_cods = {str(a.get("codigo_insumo")) for a in ajustes_list if a.get("codigo_insumo")}

            aud_map = {}
            for a in aud_list:
                cod = str(a.get("codigo_insumo"))
                if cod not in aud_map or a.get("tipo_registro") == "CIERRE_MENSUAL":
                    aud_map[cod] = a

            # 4. Consolidar insumos con conteo
            insumos_res = []
            for c in catalogo:
                cod = str(c.get("codigo_insumo"))
                aud = aud_map.get(cod)
                item = dict(c)
                costo_cat = float(c.get("costo_unitario") or 0.0)

                if aud:
                    costo_snap = float(aud.get("costo_unitario_snapshot") or 0.0)
                    costo_final = costo_snap if costo_snap > 0 else costo_cat

                    item["id_auditoria"] = aud.get("id_auditoria")
                    item["cantidad_fisica"] = aud.get("cantidad_fisica")
                    item["cantidad_sistema"] = aud.get("cantidad_sistema") if aud.get("cantidad_sistema") is not None else float(c.get("stock_actual") or 0.0)
                    item["costo_unitario_snapshot"] = costo_final
                    item["costo_unitario"] = costo_final

                    estado_aud = aud.get("estado", "PENDIENTE")
                    if cod in ajustados_cods or estado_aud == "AJUSTADO":
                        item["estado"] = "AJUSTADO"
                    else:
                        item["estado"] = estado_aud

                    item["observacion"] = aud.get("observacion")
                    item["fecha_cierre"] = aud.get("fecha_cierre")
                    if item["cantidad_fisica"] is not None:
                        item["diferencia"] = float(item["cantidad_fisica"]) - float(item["cantidad_sistema"])
                    else:
                        item["diferencia"] = None
                else:
                    item["id_auditoria"] = None
                    item["cantidad_fisica"] = None
                    item["cantidad_sistema"] = float(c.get("stock_actual") or 0.0)
                    item["costo_unitario_snapshot"] = costo_cat
                    item["costo_unitario"] = costo_cat
                    item["estado"] = "AJUSTADO" if cod in ajustados_cods else "PENDIENTE"
                    item["observacion"] = None
                    item["fecha_cierre"] = None
                    item["diferencia"] = None
                insumos_res.append(item)

            return {
                "periodo": periodo,
                "insumos": insumos_res,
                "resumen": {
                    "total_insumos": len(insumos_res),
                    "total_auditados": sum(1 for i in insumos_res if i["cantidad_fisica"] is not None)
                }
            }
        except Exception as ex:
            log_error(f"obtener_estado_cierre({mes_periodo})", ex)
            return {}

    def registrar_conteo_fisico(self, id_auditoria: str, cantidad: float, costo: float | None = None, observacion: str | None = None) -> dict:
        payload = {
            "p_id_auditoria": id_auditoria,
            "p_cantidad_fisica": cantidad
        }
        if costo is not None:
            payload["p_costo_ajuste"] = costo
        if observacion:
            payload["p_observacion"] = observacion

        try:
            res = self.db.post("rpc/fn_registrar_conteo_fisico", json_data=payload, timeout=10)
            if res and res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text if res else "No response"}
        except Exception as ex:
            log_error(f"registrar_conteo_fisico({id_auditoria})", ex)
            return {"exito": False, "error": str(ex)}

    def aceptar_stock_sistema(self, id_auditoria: str) -> dict:
        try:
            res = self.db.post("rpc/fn_aceptar_stock_sistema", json_data={"p_id_auditoria": id_auditoria}, timeout=10)
            if res and res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text if res else "No response"}
        except Exception as ex:
            log_error(f"aceptar_stock_sistema({id_auditoria})", ex)
            return {"exito": False, "error": str(ex)}

    def aceptar_stock_sistema_masivo(self, ids_auditoria: list) -> dict:
        try:
            res = self.db.post("rpc/fn_aceptar_stock_sistema_masivo", json_data={"p_ids": ids_auditoria}, timeout=15)
            if res and res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text if res else "No response"}
        except Exception as ex:
            log_error("aceptar_stock_sistema_masivo", ex)
            return {"exito": False, "error": str(ex)}

    def eliminar_ajuste_cierre(self, id_auditoria: str) -> dict:
        try:
            res = self.db.post("rpc/fn_eliminar_ajuste_cierre", json_data={"p_id_auditoria": id_auditoria}, timeout=10)
            if res and res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text if res else "No response"}
        except Exception as ex:
            log_error(f"eliminar_ajuste_cierre({id_auditoria})", ex)
            return {"exito": False, "error": str(ex)}

    def aprobar_cierre_mes(self, id_periodo: str, aprobado_por: str) -> dict:
        try:
            res = self.db.post("rpc/fn_aprobar_cierre_mes", json_data={"p_id_periodo": id_periodo, "p_aprobado_por": aprobado_por}, timeout=10)
            if res and res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text if res else "No response"}
        except Exception as ex:
            log_error(f"aprobar_cierre_mes({id_periodo})", ex)
            return {"exito": False, "error": str(ex)}
