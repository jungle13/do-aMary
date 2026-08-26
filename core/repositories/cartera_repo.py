"""
Repositorio para la gestión de Cartera, Cuentas por Cobrar, Recaudos y Planes de Cuotas.
Implementa motor de saldado automático FIFO, asignación manual de pagos, amortización dinámica de cuotas y métricas financieras.
Incluye persistencia híbrida (Supabase PostgreSQL + Respaldo Local Seguro) con deduplicación por UUID.
"""
import os
import json
import uuid
import datetime
import urllib.parse
from core.database import BaseDatabase
from core.logger import get_logger, log_error
from core.audit_logger import registrar_accion
from core.repositories.clientes_repo import ClientesRepository

logger = get_logger("CarteraRepo")

class CarteraRepository:
    def __init__(self, db: BaseDatabase | None = None):
        self.db = db or BaseDatabase()
        self.clientes_repo = ClientesRepository(self.db)
        
        # Archivo de persistencia local para asegurar funcionamiento ininterrumpido
        base_dir = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
        app_dir = os.path.join(base_dir, "DonaMaryApp")
        os.makedirs(app_dir, exist_ok=True)
        self.local_cache_file = os.path.join(app_dir, "cartera_local.json")
        self._init_local_cache()

    def _init_local_cache(self):
        if not os.path.exists(self.local_cache_file):
            try:
                with open(self.local_cache_file, "w", encoding="utf-8") as f:
                    json.dump({"pagos": [], "detalles": [], "cuotas": []}, f, indent=2)
            except Exception:
                pass

    def _read_local_cache(self) -> dict:
        try:
            if os.path.exists(self.local_cache_file):
                with open(self.local_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"pagos": [], "detalles": [], "cuotas": []}

    def _write_local_cache(self, data: dict):
        try:
            with open(self.local_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _get_todos_pagos_deduplicados(self, nombre_cliente: str | None = None) -> list[dict]:
        """Obtiene y deduplica todos los pagos de Supabase y caché local usando su id_pago."""
        pagos_map = {}
        try:
            endpoint = "pagos_cartera?estado_registro=eq.VÁLIDO"
            if nombre_cliente:
                nom_enc = urllib.parse.quote(self.clientes_repo.normalizar_nombre_cliente(nombre_cliente))
                endpoint += f"&nombre_cliente=eq.{nom_enc}"
            
            res_p = self.db.get(endpoint, timeout=10)
            if res_p and res_p.status_code == 200:
                for p in res_p.json():
                    p_id = p.get("id_pago") or str(uuid.uuid4())
                    pagos_map[p_id] = p
        except Exception:
            pass

        # Complementar con local solo si no existe en Supabase
        local_data = self._read_local_cache()
        for p in local_data.get("pagos", []):
            if p.get("estado_registro") == "VÁLIDO":
                if nombre_cliente:
                    if self.clientes_repo.normalizar_nombre_cliente(p.get("nombre_cliente")) != self.clientes_repo.normalizar_nombre_cliente(nombre_cliente):
                        continue
                p_id = p.get("id_pago")
                if p_id and p_id not in pagos_map:
                    pagos_map[p_id] = p

        return list(pagos_map.values())

    def _get_detalles_deduplicados(self, facturas_list: list[str] | None = None) -> list[dict]:
        """Obtiene y deduplica los detalles de pagos aplicados a facturas."""
        detalles_map = {}
        if facturas_list:
            try:
                facs_str = ",".join([urllib.parse.quote(str(f).strip()) for f in facturas_list if str(f).strip()])
                res_d = self.db.get(f"detalle_pagos_cartera?factura_no=in.({facs_str})&select=id_detalle,id_pago,factura_no,monto_aplicado,pagos_cartera(estado_registro)", timeout=10)
                if res_d and res_d.status_code == 200:
                    for d in res_d.json():
                        p_hdr = d.get("pagos_cartera") or {}
                        if p_hdr.get("estado_registro") != "ANULADO":
                            d_id = d.get("id_detalle") or str(uuid.uuid4())
                            detalles_map[d_id] = d
            except Exception:
                pass

            # Complementar con local
            local_data = self._read_local_cache()
            pagos_validos_local_ids = set(p["id_pago"] for p in local_data.get("pagos", []) if p.get("estado_registro") == "VÁLIDO")
            for d in local_data.get("detalles", []):
                if d.get("id_pago") in pagos_validos_local_ids and str(d.get("factura_no")) in facturas_list:
                    d_id = d.get("id_detalle")
                    if d_id and d_id not in detalles_map:
                        detalles_map[d_id] = d

        return list(detalles_map.values())

    def get_cartera_kpis(self) -> dict:
        """Calcula los indicadores globales de cartera y cuentas por cobrar."""
        try:
            # 1. Total ventas históricas
            res_v = self.db.get("registro_ventas?select=total", timeout=15)
            total_ventas = 0.0
            if res_v and res_v.status_code == 200:
                for v in res_v.json():
                    total_ventas += float(v.get("total") or 0.0)

            # 2. Total recaudado deduplicado
            pagos_data = self._get_todos_pagos_deduplicados()
            total_recaudado = 0.0
            total_efectivo = 0.0
            total_transferencias = 0.0
            pagos_por_cliente = {}

            for p in pagos_data:
                monto = float(p.get("monto_total") or 0.0)
                metodo = str(p.get("metodo_pago") or "EFECTIVO").upper()
                nom = self.clientes_repo.normalizar_nombre_cliente(p.get("nombre_cliente"))
                
                total_recaudado += monto
                if "TRANSFERENCIA" in metodo:
                    total_transferencias += monto
                else:
                    total_efectivo += monto
                
                pagos_por_cliente[nom] = pagos_por_cliente.get(nom, 0.0) + monto

            # 3. Calcular clientes con deuda
            res_clientes_v = self.db.get("registro_ventas?select=cliente,total", timeout=15)
            if not (res_clientes_v and res_clientes_v.status_code == 200):
                res_clientes_v = self.db.get("registro_ventas?select=total", timeout=15)

            ventas_por_cliente = {}
            if res_clientes_v and res_clientes_v.status_code == 200:
                for v in res_clientes_v.json():
                    nom = self.clientes_repo.normalizar_nombre_cliente(v.get("cliente"))
                    ventas_por_cliente[nom] = ventas_por_cliente.get(nom, 0.0) + float(v.get("total") or 0.0)

            clientes_con_deuda = 0
            for nom, total_cli in ventas_por_cliente.items():
                abonos_cli = pagos_por_cliente.get(nom, 0.0)
                if (total_cli - abonos_cli) > 1.0:
                    clientes_con_deuda += 1

            total_saldo_pendiente = max(0.0, total_ventas - total_recaudado)

            return {
                "total_ventas": round(total_ventas, 2),
                "total_recaudado": round(total_recaudado, 2),
                "total_efectivo": round(total_efectivo, 2),
                "total_transferencias": round(total_transferencias, 2),
                "total_saldo_pendiente": round(total_saldo_pendiente, 2),
                "clientes_con_deuda": clientes_con_deuda
            }
        except Exception as ex:
            log_error("get_cartera_kpis", ex)
            return {
                "total_ventas": 0.0,
                "total_recaudado": 0.0,
                "total_efectivo": 0.0,
                "total_transferencias": 0.0,
                "total_saldo_pendiente": 0.0,
                "clientes_con_deuda": 0
            }

    def get_estado_cuenta_clientes(
        self,
        search: str = "",
        filtro_saldo: str = "TODOS",
        fecha_filtro: str = "",
        fecha_desde: str = "",
        fecha_hasta: str = ""
    ) -> list[dict]:
        """
        Retorna la lista de clientes con su resumen financiero.
        Soporta búsqueda inteligente por Nombre de Cliente, Teléfono o Número de Factura/Documento,
        así como filtros por Fecha de Facturación.
        """
        try:
            # 1. Traer ventas (con fallback si no existe columna cliente)
            res_v = self.db.get("registro_ventas?select=cliente,factura_no,fecha,total", timeout=15)
            if not (res_v and res_v.status_code == 200):
                res_v = self.db.get("registro_ventas?select=factura_no,fecha,total", timeout=15)
            ventas_data = res_v.json() if (res_v and res_v.status_code == 200) else []

            # 2. Traer pagos deduplicados
            pagos_data = self._get_todos_pagos_deduplicados()

            # 3. Traer clientes registrados en catálogo
            res_c = self.db.get("clientes?select=id_cliente,nombre,telefono,direccion,limite_credito", timeout=10)
            clientes_catalogo = {c.get("nombre"): c for c in (res_c.json() if res_c and res_c.status_code == 200 else [])}

            # 4. Consolidar por cliente
            clientes_map = {}

            # Inicializar catálogo
            for nom, c_data in clientes_catalogo.items():
                clientes_map[nom] = {
                    "id_cliente": c_data.get("id_cliente"),
                    "nombre": nom,
                    "telefono": c_data.get("telefono") or "",
                    "direccion": c_data.get("direccion") or "",
                    "total_facturado": 0.0,
                    "total_abonado": 0.0,
                    "saldo_pendiente": 0.0,
                    "cantidad_facturas": 0,
                    "facturas_set": set(),
                    "ultima_fecha_venta": "",
                    "estado": "AL_DIA"
                }

            # Procesar ventas con filtro de fechas si aplica
            for v in ventas_data:
                fec = (v.get("fecha") or "")[:10]
                if fecha_filtro and fec != fecha_filtro:
                    continue
                if fecha_desde and fec and fec < fecha_desde:
                    continue
                if fecha_hasta and fec and fec > fecha_hasta:
                    continue

                nom = self.clientes_repo.normalizar_nombre_cliente(v.get("cliente"))
                if nom not in clientes_map:
                    clientes_map[nom] = {
                        "id_cliente": None,
                        "nombre": nom,
                        "telefono": "",
                        "direccion": "",
                        "total_facturado": 0.0,
                        "total_abonado": 0.0,
                        "saldo_pendiente": 0.0,
                        "cantidad_facturas": 0,
                        "facturas_set": set(),
                        "ultima_fecha_venta": "",
                        "estado": "AL_DIA"
                    }
                
                c_obj = clientes_map[nom]
                monto = float(v.get("total") or 0.0)
                fac = str(v.get("factura_no") or "").strip()

                c_obj["total_facturado"] += monto
                if fac:
                    c_obj["facturas_set"].add(fac)
                if fec and (not c_obj["ultima_fecha_venta"] or fec > c_obj["ultima_fecha_venta"]):
                    c_obj["ultima_fecha_venta"] = fec

            # Procesar pagos
            for p in pagos_data:
                nom = self.clientes_repo.normalizar_nombre_cliente(p.get("nombre_cliente"))
                if nom not in clientes_map:
                    clientes_map[nom] = {
                        "id_cliente": p.get("id_cliente"),
                        "nombre": nom,
                        "telefono": "",
                        "direccion": "",
                        "total_facturado": 0.0,
                        "total_abonado": 0.0,
                        "saldo_pendiente": 0.0,
                        "cantidad_facturas": 0,
                        "facturas_set": set(),
                        "ultima_fecha_venta": "",
                        "estado": "AL_DIA"
                    }
                clientes_map[nom]["total_abonado"] += float(p.get("monto_total") or 0.0)

            # Calcular saldos y filtros
            resultado = []
            s_upper = search.strip().upper()

            for nom, c_obj in clientes_map.items():
                facturas_list = list(c_obj.pop("facturas_set", set()))
                c_obj["facturas_list"] = facturas_list
                c_obj["cantidad_facturas"] = len(facturas_list)
                c_obj["total_facturado"] = round(c_obj["total_facturado"], 2)
                c_obj["total_abonado"] = round(c_obj["total_abonado"], 2)
                c_obj["saldo_pendiente"] = round(max(0.0, c_obj["total_facturado"] - c_obj["total_abonado"]), 2)
                c_obj["estado"] = "CON_DEUDA" if c_obj["saldo_pendiente"] > 0.01 else "AL_DIA"

                # Si filtramos por fecha y no tuvo movimientos en el rango, omitir
                if (fecha_desde or fecha_hasta) and c_obj["total_facturado"] == 0 and c_obj["total_abonado"] == 0:
                    continue

                # Búsqueda inteligente: Nombre de Cliente, Teléfono o Número de Factura
                if s_upper:
                    coincide_nombre = s_upper in nom
                    coincide_tel = s_upper in c_obj["telefono"].upper()
                    coincide_fac = any(s_upper in str(f).upper() for f in facturas_list)
                    if not (coincide_nombre or coincide_tel or coincide_fac):
                        continue

                # Filtrar estado
                if filtro_saldo == "CON_DEUDA" and c_obj["estado"] != "CON_DEUDA":
                    continue
                if filtro_saldo == "AL_DIA" and c_obj["estado"] != "AL_DIA":
                    continue

                resultado.append(c_obj)

            # Ordenar: primero los que tienen mayor saldo pendiente
            resultado.sort(key=lambda x: (x["saldo_pendiente"], x["total_facturado"]), reverse=True)
            return resultado

        except Exception as ex:
            log_error("get_estado_cuenta_clientes", ex)
            return []

    def get_facturas_cliente(self, nombre_cliente: str) -> list[dict]:
        """
        Retorna las facturas de un cliente con su total, monto abonado y saldo pendiente calculados con precisión FIFO.
        """
        nom_clean = self.clientes_repo.normalizar_nombre_cliente(nombre_cliente)
        try:
            nom_enc = urllib.parse.quote(nom_clean)
            # 1. Obtener todas las líneas de ventas de este cliente
            endpoint = f"registro_ventas?cliente=eq.{nom_enc}&select=id_venta,factura_no,fecha,descripcion,cantidad,total,tipo_documento"
            res_v = self.db.get(endpoint, timeout=12)
            if not (res_v and res_v.status_code == 200) and nom_clean == "CLIENTES VARIOS":
                res_v = self.db.get("registro_ventas?select=id_venta,factura_no,fecha,descripcion,cantidad,total,tipo_documento", timeout=12)
            ventas_items = res_v.json() if (res_v and res_v.status_code == 200) else []

            # 2. Agrupar por número de factura
            facturas_dict = {}
            for item in ventas_items:
                fac_no = str(item.get("factura_no") or "S/N").strip()
                if fac_no not in facturas_dict:
                    facturas_dict[fac_no] = {
                        "factura_no": fac_no,
                        "fecha": (item.get("fecha") or "")[:10],
                        "tipo_documento": item.get("tipo_documento") or "Factura POS",
                        "total_factura": 0.0,
                        "total_abonado": 0.0,
                        "saldo_pendiente": 0.0,
                        "items_cantidad": 0,
                        "estado_factura": "PENDIENTE"
                    }
                
                facturas_dict[fac_no]["total_factura"] += float(item.get("total") or 0.0)
                facturas_dict[fac_no]["items_cantidad"] += 1
                if item.get("fecha") and (not facturas_dict[fac_no]["fecha"] or item["fecha"][:10] < facturas_dict[fac_no]["fecha"]):
                    facturas_dict[fac_no]["fecha"] = item["fecha"][:10]

            facs_list = list(facturas_dict.keys())
            if not facs_list:
                return []

            # 3. Obtener detalles directos deduplicados
            detalles = self._get_detalles_deduplicados(facs_list)
            abonos_directos_por_factura = {f: 0.0 for f in facs_list}
            for d in detalles:
                f_no = str(d.get("factura_no"))
                if f_no in abonos_directos_por_factura:
                    abonos_directos_por_factura[f_no] += float(d.get("monto_aplicado") or 0.0)

            # 4. Obtener todos los pagos válidos deduplicados del cliente
            pagos_cliente = self._get_todos_pagos_deduplicados(nombre_cliente=nom_clean)
            total_pagos_cliente = sum(float(p.get("monto_total") or 0.0) for p in pagos_cliente)

            # Total asignado mediante detalles directos
            total_asignado_directo = sum(abonos_directos_por_factura.values())
            # Remanente para distribuir vía FIFO automático
            remanente_fifo = max(0.0, total_pagos_cliente - total_asignado_directo)

            # 5. Ordenar facturas cronológicamente para aplicar FIFO
            lista_facturas = list(facturas_dict.values())
            lista_facturas.sort(key=lambda x: (x["fecha"] or "9999-99-99", x["factura_no"]))

            for f_obj in lista_facturas:
                f_no = f_obj["factura_no"]
                f_obj["total_factura"] = round(f_obj["total_factura"], 2)
                abono_directo = abonos_directos_por_factura.get(f_no, 0.0)

                # Saldo pendiente antes de FIFO
                saldo_previo = max(0.0, f_obj["total_factura"] - abono_directo)
                abono_fifo = 0.0
                if remanente_fifo > 0 and saldo_previo > 0:
                    abono_fifo = min(remanente_fifo, saldo_previo)
                    remanente_fifo -= abono_fifo

                total_abono = abono_directo + abono_fifo
                f_obj["total_abonado"] = round(min(f_obj["total_factura"], total_abono), 2)
                f_obj["saldo_pendiente"] = round(max(0.0, f_obj["total_factura"] - f_obj["total_abonado"]), 2)

                if f_obj["saldo_pendiente"] <= 0.01:
                    f_obj["estado_factura"] = "PAGADA"
                elif f_obj["total_abonado"] > 0:
                    f_obj["estado_factura"] = "PARCIAL"
                else:
                    f_obj["estado_factura"] = "PENDIENTE"

            # Ordenar para presentación en pantalla: facturas pendientes primero, luego fecha descendente
            lista_facturas.sort(key=lambda x: (x["saldo_pendiente"] > 0.01, x["fecha"] or ""), reverse=True)
            return lista_facturas

        except Exception as ex:
            log_error(f"get_facturas_cliente({nom_clean})", ex)
            return []

    def get_historial_pagos_cliente(self, nombre_cliente: str) -> list[dict]:
        """Retorna el historial de pagos registrados para un cliente con sus facturas afectadas."""
        nom_clean = self.clientes_repo.normalizar_nombre_cliente(nombre_cliente)
        try:
            pagos = self._get_todos_pagos_deduplicados(nombre_cliente=nom_clean)
            pagos.sort(key=lambda x: x.get("fecha_pago", "") or x.get("created_at", ""), reverse=True)

            local_detalles = self._read_local_cache().get("detalles", [])

            for p in pagos:
                p_id = p.get("id_pago")
                p["monto_total"] = float(p.get("monto_total") or 0.0)
                p["fecha_formateada"] = (p.get("fecha_pago") or "")[:10]
                p["facturas_afectadas"] = []
                try:
                    res_d = self.db.get(f"detalle_pagos_cartera?id_pago=eq.{p_id}&select=factura_no,monto_aplicado", timeout=5)
                    if res_d and res_d.status_code == 200 and res_d.json():
                        p["facturas_afectadas"] = res_d.json()
                    else:
                        p["facturas_afectadas"] = [d for d in local_detalles if d.get("id_pago") == p_id]
                except Exception:
                    p["facturas_afectadas"] = [d for d in local_detalles if d.get("id_pago") == p_id]

            return pagos
        except Exception as ex:
            log_error(f"get_historial_pagos_cliente({nom_clean})", ex)
            return []

    def registrar_pago_cartera(
        self,
        id_cliente: str | None,
        nombre_cliente: str,
        monto_total: float,
        metodo_pago: str = "EFECTIVO",
        banco_origen: str | None = None,
        referencia: str = "",
        observaciones: str = "",
        facturas_seleccionadas: dict | None = None,
        usuario: str = "admin"
    ) -> bool:
        """
        Registra un pago de cartera y lo distribuye a las facturas correspondientes.
        Si facturas_seleccionadas es None: Aplica algoritmo FIFO (de más antigua a más nueva).
        """
        nom_clean = self.clientes_repo.normalizar_nombre_cliente(nombre_cliente)
        monto_float = round(float(monto_total or 0.0), 2)
        if monto_float <= 0:
            return False

        try:
            if not id_cliente:
                cli = self.clientes_repo.get_or_create_cliente(nom_clean)
                id_cliente = cli.get("id_cliente")

            id_pago_gen = str(uuid.uuid4())
            ahora_iso = datetime.datetime.now().isoformat()

            pago_payload = {
                "id_pago": id_pago_gen,
                "id_cliente": id_cliente,
                "nombre_cliente": nom_clean,
                "monto_total": monto_float,
                "metodo_pago": metodo_pago.upper(),
                "banco_origen": banco_origen if metodo_pago.upper() == "TRANSFERENCIA" else None,
                "referencia_comprobante": referencia.strip() if referencia else None,
                "observaciones": observaciones.strip() if observaciones else None,
                "usuario_registro": usuario,
                "estado_registro": "VÁLIDO",
                "fecha_pago": ahora_iso
            }

            pago_en_db = False
            res_pago = self.db.post("pagos_cartera", json_data=pago_payload, timeout=8)
            if res_pago and res_pago.status_code in (200, 201):
                pago_en_db = True

            local_cache = self._read_local_cache()
            local_cache.setdefault("pagos", []).append(pago_payload)

            # Calcular distribución de facturas
            detalles_payload = []
            if facturas_seleccionadas:
                for fac_no, monto_aplicar in facturas_seleccionadas.items():
                    m_ap = round(float(monto_aplicar or 0), 2)
                    if m_ap > 0:
                        detalles_payload.append({
                            "id_detalle": str(uuid.uuid4()),
                            "id_pago": id_pago_gen,
                            "factura_no": str(fac_no),
                            "monto_aplicado": m_ap
                        })
            else:
                facturas_cliente = self.get_facturas_cliente(nom_clean)
                pendientes = [f for f in facturas_cliente if f["saldo_pendiente"] > 0]
                pendientes.sort(key=lambda x: (x["fecha"] or "9999-99-99", x["factura_no"]))

                monto_restante = monto_float
                for f_item in pendientes:
                    if monto_restante <= 0:
                        break
                    saldo_f = f_item["saldo_pendiente"]
                    aplicar = min(monto_restante, saldo_f)
                    detalles_payload.append({
                        "id_detalle": str(uuid.uuid4()),
                        "id_pago": id_pago_gen,
                        "factura_no": str(f_item["factura_no"]),
                        "monto_aplicado": round(aplicar, 2),
                        "saldo_anterior": saldo_f,
                        "saldo_restante": round(max(0.0, saldo_f - aplicar), 2)
                    })
                    monto_restante -= aplicar

            if detalles_payload:
                if pago_en_db:
                    self.db.post("detalle_pagos_cartera", json_data=detalles_payload, timeout=8)
                local_cache.setdefault("detalles", []).extend(detalles_payload)

            self._write_local_cache(local_cache)

            registrar_accion(
                accion=f"Recaudo Cartera: ${monto_float:,.0f} ({metodo_pago}) a cliente {nom_clean}",
                modulo="CARTERA",
                detalles={
                    "cliente": nom_clean,
                    "monto": monto_float,
                    "metodo": metodo_pago,
                    "banco": banco_origen,
                    "facturas_afectadas": len(detalles_payload)
                }
            )
            return True

        except Exception as ex:
            log_error(f"registrar_pago_cartera({nom_clean})", ex)
            return False

    def anular_pago_cartera(self, id_pago: str) -> bool:
        """Marca un pago como ANULADO revirtiendo su impacto en la cartera."""
        try:
            id_enc = urllib.parse.quote(str(id_pago))
            self.db.patch(f"pagos_cartera?id_pago=eq.{id_enc}", json_data={"estado_registro": "ANULADO"}, timeout=8)
            
            local_cache = self._read_local_cache()
            for p in local_cache.get("pagos", []):
                if p.get("id_pago") == id_pago:
                    p["estado_registro"] = "ANULADO"
            self._write_local_cache(local_cache)

            registrar_accion(
                accion=f"Anulación de pago de cartera {id_pago}",
                modulo="CARTERA",
                detalles={"id_pago": id_pago}
            )
            return True
        except Exception as ex:
            log_error(f"anular_pago_cartera({id_pago})", ex)
            return False

    def crear_plan_cuotas(
        self,
        id_cliente: str | None,
        nombre_cliente: str,
        saldo_a_diferir: float,
        num_cuotas: int,
        periodicidad: str = "MENSUAL",
        fecha_inicio: str | None = None,
        observacion: str = ""
    ) -> bool:
        """
        Genera y almacena un cronograma de cuotas con fechas automáticas de cobro.
        """
        nom_clean = self.clientes_repo.normalizar_nombre_cliente(nombre_cliente)
        try:
            if not id_cliente:
                cli = self.clientes_repo.get_or_create_cliente(nom_clean)
                id_cliente = cli.get("id_cliente")

            num_cuotas = max(1, int(num_cuotas or 1))
            monto_cuota = round(float(saldo_a_diferir) / num_cuotas, 2)

            f_base = datetime.date.today()
            if fecha_inicio:
                try:
                    f_base = datetime.date.fromisoformat(fecha_inicio[:10])
                except Exception:
                    pass

            dias_delta = 30
            if periodicidad.upper() == "SEMANAL":
                dias_delta = 7
            elif periodicidad.upper() == "QUINCENAL":
                dias_delta = 15

            cuotas_payload = []
            for i in range(1, num_cuotas + 1):
                f_cobro = f_base + datetime.timedelta(days=(i - 1) * dias_delta)
                cuotas_payload.append({
                    "id_cuota": str(uuid.uuid4()),
                    "id_cliente": id_cliente,
                    "nombre_cliente": nom_clean,
                    "numero_cuota": i,
                    "total_cuotas": num_cuotas,
                    "monto_cuota": monto_cuota,
                    "fecha_cobro_sugerida": f_cobro.isoformat(),
                    "estado": "PENDIENTE",
                    "observacion": observacion or f"Cuota {i} de {num_cuotas} ({periodicidad})"
                })

            # Reemplazar cuotas activas previas para este cliente
            try:
                nom_enc = urllib.parse.quote(nom_clean)
                self.db.delete(f"cuotas_cartera?nombre_cliente=eq.{nom_enc}", timeout=5)
            except Exception:
                pass

            self.db.post("cuotas_cartera", json_data=cuotas_payload, timeout=8)
            
            local_cache = self._read_local_cache()
            local_cache["cuotas"] = [c for c in local_cache.get("cuotas", []) if self.clientes_repo.normalizar_nombre_cliente(c.get("nombre_cliente")) != nom_clean]
            local_cache["cuotas"].extend(cuotas_payload)
            self._write_local_cache(local_cache)

            registrar_accion(
                accion=f"Plan de Cuotas Cartera: {num_cuotas} cuotas de ${monto_cuota:,.0f} a {nom_clean}",
                modulo="CARTERA",
                detalles={"cliente": nom_clean, "cuotas": num_cuotas, "monto_total": saldo_a_diferir}
            )
            return True

        except Exception as ex:
            log_error(f"crear_plan_cuotas({nom_clean})", ex)
            return False

    def get_cuotas_cliente(self, nombre_cliente: str, saldo_actual_cliente: float | None = None) -> list[dict]:
        """
        Obtiene el cronograma de cuotas programadas para un cliente,
        amortizando dinámicamente los pagos realizados contra las cuotas más cercanas.
        """
        nom_clean = self.clientes_repo.normalizar_nombre_cliente(nombre_cliente)
        try:
            nom_enc = urllib.parse.quote(nom_clean)
            cuotas_map = {}
            res = self.db.get(f"cuotas_cartera?nombre_cliente=eq.{nom_enc}&order=fecha_cobro_sugerida.asc", timeout=8)
            if res and res.status_code == 200 and res.json():
                for c in res.json():
                    c_id = c.get("id_cuota") or str(uuid.uuid4())
                    cuotas_map[c_id] = c
            else:
                local_cuotas = [c for c in self._read_local_cache().get("cuotas", []) if self.clientes_repo.normalizar_nombre_cliente(c.get("nombre_cliente")) == nom_clean]
                for c in local_cuotas:
                    c_id = c.get("id_cuota") or str(uuid.uuid4())
                    cuotas_map[c_id] = c

            cuotas = list(cuotas_map.values())
            if not cuotas:
                return []

            cuotas.sort(key=lambda x: (x.get("fecha_cobro_sugerida") or "9999-99-99", x.get("numero_cuota", 1)))

            # Calcular amortización de cuotas:
            # Si no viene saldo_actual_cliente, calcularlo
            if saldo_actual_cliente is None:
                estados = self.get_estado_cuenta_clientes(search=nom_clean)
                cli_info = next((c for c in estados if c["nombre"] == nom_clean), None)
                saldo_actual_cliente = cli_info.get("saldo_pendiente", 0.0) if cli_info else 0.0

            total_plan_cuotas = sum(float(c.get("monto_cuota") or 0.0) for c in cuotas)
            # El valor amortizado sobre el plan es la diferencia entre el total del plan y el saldo restante
            total_amortizado_plan = max(0.0, total_plan_cuotas - saldo_actual_cliente)

            remanente_amortizar = total_amortizado_plan

            for c in cuotas:
                monto_c = float(c.get("monto_cuota") or 0.0)
                c["monto_cuota"] = monto_c
                c["fecha_cobro"] = (c.get("fecha_cobro_sugerida") or "")[:10]

                abono_c = 0.0
                if remanente_amortizar > 0 and monto_c > 0:
                    abono_c = min(remanente_amortizar, monto_c)
                    remanente_amortizar -= abono_c

                c["monto_abonado"] = round(abono_c, 2)
                c["saldo_cuota"] = round(max(0.0, monto_c - abono_c), 2)

                if c["saldo_cuota"] <= 0.01:
                    c["estado"] = "COBRADO"
                elif c["monto_abonado"] > 0:
                    c["estado"] = "PARCIAL"
                else:
                    c["estado"] = "PENDIENTE"

            return cuotas
        except Exception as ex:
            log_error(f"get_cuotas_cliente({nom_clean})", ex)
            return []
