"""
Repositorio para cierres mensuales, auditorías, snapshots y conteos físicos.
"""
import calendar
import urllib.parse
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
                prev_year, prev_month = year - 1, 12
            else:
                prev_year, prev_month = year, month - 1
            mes_anterior = f"{prev_year}-{prev_month:02d}"

            last_day_prev = calendar.monthrange(prev_year, prev_month)[1]
            last_day_curr = calendar.monthrange(year, month)[1]
        except Exception as ex:
            log_error(f"get_datos_conteo_inicial parsing {mes_seleccionado}", ex)
            return []

        # 1. Catálogo
        catalogo = []
        try:
            res_cat = self.db.get("catalogo_insumos?select=codigo_insumo,nombre,categoria&estado=eq.true&order=nombre.asc", timeout=12)
            if res_cat and res_cat.status_code == 200:
                catalogo = res_cat.json()
        except Exception as ex:
            log_error("get_datos_conteo_inicial (catalogo)", ex)

        # 2. Cierre mes anterior con rango exacto
        cierre_anterior = {}
        try:
            endpoint_ant = (
                f"registro_auditorias_cierres?tipo_registro=eq.CIERRE_MENSUAL"
                f"&fecha_cierre=gte.{mes_anterior}-01T00:00:00"
                f"&fecha_cierre=lte.{mes_anterior}-{last_day_prev:02d}T23:59:59"
                f"&select=codigo_insumo,cantidad_fisica"
            )
            res_ant = self.db.get(endpoint_ant, timeout=10)
            if res_ant and res_ant.status_code == 200:
                for r in res_ant.json():
                    cierre_anterior[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except Exception as ex:
            log_error("get_datos_conteo_inicial (cierre_anterior)", ex)

        # 3. Inicial mes actual con rango exacto
        inicio_actual = {}
        try:
            endpoint_act = (
                f"registro_auditorias_cierres?tipo_registro=eq.INVENTARIO_INICIAL"
                f"&fecha_cierre=gte.{mes_seleccionado}-01T00:00:00"
                f"&fecha_cierre=lte.{mes_seleccionado}-{last_day_curr:02d}T23:59:59"
                f"&select=codigo_insumo,cantidad_fisica"
            )
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

            existentes = {}
            if codigos:
                fc_enc = urllib.parse.quote(str(fecha_cierre).strip()) if fecha_cierre else ""
                tr_enc = urllib.parse.quote(str(tipo_registro).strip()) if tipo_registro else ""
                chunk_size = 50
                for i in range(0, len(codigos), chunk_size):
                    chunk = codigos[i:i + chunk_size]
                    codigos_str = ",".join([urllib.parse.quote(str(c).strip()) for c in chunk if str(c).strip()])
                    endpoint_exist = (
                        f"registro_auditorias_cierres?fecha_cierre=eq.{fc_enc}"
                        f"&tipo_registro=eq.{tr_enc}"
                        f"&codigo_insumo=in.({codigos_str})"
                        f"&select=id_auditoria,codigo_insumo"
                    )
                    res_exist = self.db.get(endpoint_exist, timeout=10)
                    if res_exist and res_exist.status_code == 200:
                        for item in res_exist.json():
                            if "id_auditoria" in item:
                                existentes[item["codigo_insumo"]] = item["id_auditoria"]

                for r in registros:
                    if r.get("codigo_insumo") in existentes:
                        r["id_auditoria"] = existentes[r["codigo_insumo"]]
        except Exception as ex:
            log_error("upsert_conteos_iniciales (busqueda existentes)", ex)

        headers = {"Prefer": "resolution=merge-duplicates"}
        try:
            # Enviar en bloques de 100 para evitar payloads excesivos
            chunk_save = 100
            for i in range(0, len(registros), chunk_save):
                chunk = registros[i:i + chunk_save]
                res = self.db.post("registro_auditorias_cierres", json_data=chunk, custom_headers=headers, timeout=15)
                if not (res and res.status_code in (200, 201, 204)):
                    return False
            return True
        except Exception as ex:
            log_error("upsert_conteos_iniciales", ex)
            return False

    def _fetch_all_rows(self, endpoint: str, page_size: int = 2500, timeout: int = 12) -> list:
        """Descarga todos los registros de un endpoint usando paginación por bloques Range."""
        all_data = []
        offset = 0
        while True:
            headers = {"Range": f"{offset}-{offset + page_size - 1}"}
            res = self.db.get(endpoint, custom_headers=headers, timeout=timeout)
            if not res or res.status_code not in (200, 206):
                break
            chunk = res.json()
            if not chunk:
                break
            all_data.extend(chunk)
            if len(chunk) < page_size:
                break
            offset += page_size
        return all_data

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
            mes_periodo_enc = urllib.parse.quote(str(mes_periodo).strip())
            res_p = self.db.get(f"periodos_inventario?mes_periodo=eq.{mes_periodo_enc}", timeout=10)
            periodo = res_p.json()[0] if res_p and res_p.status_code == 200 and res_p.json() else {}
            id_periodo = periodo.get("id_periodo")

            # 2. Obtener Catálogo Completo con Stock en Vivo desde vista_inventario_completo
            catalogo = self._fetch_all_rows("vista_inventario_completo?select=codigo_insumo,nombre,categoria,stock_inicial,stock_actual,costo_unitario,precio_venta,tipo_unidad&estado=eq.true&order=nombre.asc")

            # 3. Obtener Conteos Físicos de Auditoría
            endpoint_aud = "registro_auditorias_cierres"
            if id_periodo:
                id_p_enc = urllib.parse.quote(str(id_periodo).strip())
                endpoint_aud = f"registro_auditorias_cierres?id_periodo=eq.{id_p_enc}"
            aud_list = self._fetch_all_rows(endpoint_aud)

            # 3.5. Obtener Ajustes válidos para el periodo
            endpoint_ajustes = "registro_ajustes_inventario?estado_registro=eq.VÁLIDO"
            if id_periodo:
                id_p_enc = urllib.parse.quote(str(id_periodo).strip())
                endpoint_ajustes = f"registro_ajustes_inventario?id_periodo=eq.{id_p_enc}&estado_registro=eq.VÁLIDO"
            ajustes_list = self._fetch_all_rows(endpoint_ajustes)
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
                item["stock_inicial"] = float(c.get("stock_inicial") or 0.0)
                item["stock_actual"] = float(c.get("stock_actual") or 0.0)

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

    def actualizar_auditoria_ajustada(self, codigo_insumo: str, datos: dict, id_periodo: str | None = None) -> bool:
        """Actualiza el estado y costo de la auditoría tras aplicar un ajuste individual."""
        try:
            cod_enc = urllib.parse.quote(str(codigo_insumo).strip())
            if id_periodo:
                id_p_enc = urllib.parse.quote(str(id_periodo).strip())
                endpoint = f"registro_auditorias_cierres?id_periodo=eq.{id_p_enc}&codigo_insumo=eq.{cod_enc}"
            else:
                endpoint = f"registro_auditorias_cierres?codigo_insumo=eq.{cod_enc}"
            res = self.db.patch(endpoint, json_data=datos, timeout=8)
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error(f"actualizar_auditoria_ajustada({codigo_insumo})", ex)
            return False

    def sellar_periodo_cierre(self, mes_periodo: str, id_periodo: str | None = None, aprobado_por: str = "Usuario Actual") -> bool:
        """Sella y aprueba el periodo de inventario en base de datos."""
        try:
            from core.fecha_utils import get_ahora_iso
            if id_periodo:
                res = self.aprobar_cierre_mes(id_periodo, aprobado_por)
                if isinstance(res, dict) and (res.get("exito") or res.get("status") == "success" or res.get("estado") == "CERRADO"):
                    return True
            mes_enc = urllib.parse.quote(str(mes_periodo).strip())
            res = self.db.patch(
                f"periodos_inventario?mes_periodo=eq.{mes_enc}",
                json_data={"estado": "CERRADO", "fecha_aprobacion": get_ahora_iso(), "aprobado_por": aprobado_por},
                timeout=10
            )
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error(f"sellar_periodo_cierre({mes_periodo})", ex)
            return False
