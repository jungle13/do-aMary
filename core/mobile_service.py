"""
Servicio central para el módulo de conteo móvil y servidor Web local.
Maneja detección de IP, generación de QR, búsqueda difusa, autenticación de operarios,
registro multi-usuario (reemplazo o suma colaborativa) y sincronización de auditoría.
"""
import socket
import io
import base64
import threading
import datetime
import urllib.parse
import qrcode
from config import Config
from core.database import BaseDatabase
from core.logger import get_logger, log_error

logger = get_logger("MobileService")

class MobileCountingService:
    _instance = None
    _server_thread = None
    _server_running = False
    _server_instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MobileCountingService, cls).__new__(cls)
            cls._instance.db = BaseDatabase()
            cls._instance.catalogo_cache = []
            cls._instance.last_cache_update = None
            cls._instance.historial_reciente = []
        return cls._instance

    def get_local_ip(self) -> str:
        """Obtiene la IP privada del equipo en la red Wi-Fi / Ethernet local."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_server_url(self, port: int = 8550) -> str:
        return f"http://{self.get_local_ip()}:{port}"

    def get_qr_base64(self, port: int = 8550) -> str:
        """Genera un código QR en base64 de la URL local para escanear con el celular."""
        url = self.get_server_url(port)
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        
        buf = io.BytesIO()
        img.save(buf)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    def autenticar_operario(self, usuario: str, clave: str) -> dict | None:
        """Verifica credenciales del usuario para acceso a la Web Móvil."""
        try:
            from core.repositories.usuarios_repo import UsuariosRepository
            repo = UsuariosRepository(self.db)
            u = repo.autenticar(usuario.strip().lower(), clave.strip())
            if not u:
                return None

            raw_rol = (u.get("rol") or "OPERADOR").upper()
            user_str = (u.get("usuario") or "").lower()

            # Normalizar rol para la UI Móvil:
            # Si es admin o aux -> AUXILIAR (ve stock sistema y diferencias)
            # Si es bodeguero o operador -> BODEGUERO (conteo ciego)
            if "ADMIN" in raw_rol or user_str.startswith("admin") or user_str.startswith("aux") or user_str in ("mary", "eliana"):
                rol_ui = "AUXILIAR" if not "ADMIN" in raw_rol else "ADMINISTRADOR"
            else:
                rol_ui = "BODEGUERO"

            return {
                "id_usuario": u.get("id_usuario"),
                "usuario": u.get("usuario"),
                "nombre_completo": u.get("nombre_completo") or u.get("usuario"),
                "rol": rol_ui
            }
        except Exception as ex:
            log_error(f"MobileService.autenticar_operario({usuario})", ex)
            return None

    def refrescar_catalogo(self, forzar: bool = False, mes_periodo: str = "2026-08"):
        """Mantiene en memoria el catálogo completo (2700+ insumos) enriquecido con datos de auditoría."""
        ahora = datetime.datetime.now()
        if not forzar and self.catalogo_cache and self.last_cache_update:
            if (ahora - self.last_cache_update).total_seconds() < 60:
                return

        try:
            # 1. Obtener catálogo completo (hasta 3500 insumos)
            res = self.db.get("catalogo_insumos?select=codigo_insumo,nombre,categoria,costo_unitario,precio_venta,stock_actual,tipo_unidad&estado=eq.true&order=nombre.asc&limit=3500", timeout=20)
            if not (res and res.status_code == 200):
                return

            items = res.json()

            # 2. Obtener conteos de auditoría de cierre del periodo
            aud_map = {}
            try:
                res_aud = self.db.get("registro_auditorias_cierres?select=codigo_insumo,cantidad_fisica,cantidad_sistema,costo_unitario_snapshot,observacion,fecha_cierre&limit=3500", timeout=15)
                if res_aud and res_aud.status_code == 200:
                    for a in res_aud.json():
                        cod = str(a.get("codigo_insumo"))
                        aud_map[cod] = a
            except Exception as e_aud:
                log_error("refrescar_catalogo (auditorias)", e_aud)

            # 3. Enriquecer cada insumo
            for it in items:
                cod = str(it.get("codigo_insumo"))
                aud = aud_map.get(cod)
                if aud:
                    it["cantidad_fisica"] = aud.get("cantidad_fisica")
                    it["cantidad_sistema"] = aud.get("cantidad_sistema") or it.get("stock_actual") or 0.0
                    it["observacion_conteo"] = aud.get("observacion") or ""
                    it["fecha_conteo"] = aud.get("fecha_cierre") or ""
                else:
                    it["cantidad_fisica"] = None
                    it["cantidad_sistema"] = float(it.get("stock_actual") or 0.0)
                    it["observacion_conteo"] = ""
                    it["fecha_conteo"] = ""

            self.catalogo_cache = items
            self.last_cache_update = ahora
            logger.info(f"Catálogo móvil actualizado con {len(self.catalogo_cache)} insumos y {len(aud_map)} conteos vinculados.")
        except Exception as ex:
            log_error("refrescar_catalogo", ex)

    def buscar_insumos(self, query: str, mes_periodo: str = "2026-08", limit: int = 0) -> list:
        """Búsqueda multi-palabra sobre el catálogo completo enriquecido."""
        self.refrescar_catalogo(mes_periodo=mes_periodo)
        if not query or not query.strip():
            if limit and limit > 0:
                return self.catalogo_cache[:limit]
            return self.catalogo_cache

        tokens = [t.lower().strip() for t in query.strip().split() if t.strip()]
        candidatos = []
        for item in self.catalogo_cache:
            codigo = str(item.get("codigo_insumo") or "").lower()
            nombre = str(item.get("nombre") or "").lower()
            categoria = str(item.get("categoria") or "").lower()
            texto_completo = f"{codigo} {nombre} {categoria}"
            if all(t in texto_completo for t in tokens):
                candidatos.append(item)
                if limit and limit > 0 and len(candidatos) >= limit:
                    break

        return candidatos

    def guardar_conteo_movil(
        self,
        codigo_insumo: str,
        cantidad: float,
        modo_registro: str = "REEMPLAZAR",  # 'REEMPLAZAR' o 'SUMAR'
        costo: float | None = None,
        usuario: str = "Móvil Bodega",
        rol: str = "BODEGUERO",
        observacion: str = "",
        mes_periodo: str = "2026-08"
    ) -> dict:
        """
        Registra conteo desde la Web Móvil soportando reemplazo o acumulación colaborativa.
        Actualiza registro_auditorias_cierres, catalogo_insumos y genera traza de auditoría.
        """
        try:
            codigo = str(codigo_insumo).strip()
            cant_ingresada = float(cantidad)

            # 1. Obtener datos del insumo
            costo_final = float(costo) if costo is not None and float(costo) > 0 else 0.0
            nombre_insumo = ""
            stock_sistema = 0.0
            for item in self.catalogo_cache:
                if str(item.get("codigo_insumo")) == codigo:
                    if costo_final == 0.0:
                        costo_final = float(item.get("costo_unitario") or 0.0)
                    nombre_insumo = item.get("nombre") or ""
                    stock_sistema = float(item.get("stock_actual") or 0.0)
                    break

            # 2. Obtener periodo
            endpoint_per = f"periodos_inventario?mes_periodo=eq.{mes_periodo}&select=id_periodo"
            res_p = self.db.get(endpoint_per, timeout=10)
            id_periodo = res_p.json()[0]["id_periodo"] if res_p and res_p.status_code == 200 and res_p.json() else None

            # 3. Consultar conteo actual previo
            endpoint_aud = f"registro_auditorias_cierres?codigo_insumo=eq.{codigo}&select=id_auditoria,cantidad_fisica,costo_unitario_snapshot,observacion"
            if id_periodo:
                endpoint_aud += f"&id_periodo=eq.{id_periodo}"
            
            res_aud = self.db.get(endpoint_aud, timeout=10)
            cant_previa = 0.0
            id_aud = None
            if res_aud and res_aud.status_code == 200 and res_aud.json():
                aud_row = res_aud.json()[0]
                id_aud = aud_row.get("id_auditoria")
                if aud_row.get("cantidad_fisica") is not None:
                    cant_previa = float(aud_row.get("cantidad_fisica"))
                if costo_final == 0.0 and aud_row.get("costo_unitario_snapshot"):
                    costo_final = float(aud_row.get("costo_unitario_snapshot"))

            # 4. Calcular cantidad final según el modo
            if modo_registro == "SUMAR":
                cant_final = cant_previa + cant_ingresada
                detalle_accion = f"Suma de {cant_ingresada:g} unds (Previa: {cant_previa:g} -> Total: {cant_final:g})"
            else:
                cant_final = cant_ingresada
                detalle_accion = f"Conteo directo establecido en {cant_final:g} unds"

            if observacion:
                detalle_accion += f" - Nota: {observacion}"

            from core.fecha_utils import get_ahora_iso
            ahora_iso = get_ahora_iso()
            payload = {
                "codigo_insumo": codigo,
                "cantidad_fisica": cant_final,
                "costo_unitario_snapshot": costo_final,
                "estado": "AUDITADO",
                "fecha_cierre": ahora_iso,
                "observacion": f"[{usuario} ({rol})] {detalle_accion}"
            }
            if id_periodo:
                payload["id_periodo"] = id_periodo
                payload["tipo_registro"] = "CIERRE_MENSUAL"

            if id_aud:
                self.db.patch(f"registro_auditorias_cierres?id_auditoria=eq.{id_aud}", json_data=payload, timeout=10)
            else:
                headers = {"Prefer": "resolution=merge-duplicates"}
                self.db.post("registro_auditorias_cierres", json_data=[payload], custom_headers=headers, timeout=10)

            # Sincronizar catálogo local (cantidad_fisica y costo) y en Supabase (solo costo si aplica)
            for item in self.catalogo_cache:
                if str(item.get("codigo_insumo")) == codigo:
                    item["cantidad_fisica"] = cant_final
                    if costo_final > 0:
                        item["costo_unitario"] = costo_final
                    break

            if costo_final > 0:
                try:
                    self.db.patch(f"catalogo_insumos?codigo_insumo=eq.{codigo}", json_data={"costo_unitario": costo_final}, timeout=8)
                except Exception:
                    pass

            # 5. Registrar en Historial de Auditoría (Traza completa)
            from core.audit_logger import registrar_accion
            registrar_accion(
                accion=f"Conteo físico para [{codigo}] {nombre_insumo}: {detalle_accion}",
                modulo="CONTEO_MOVIL",
                usuario=usuario,
                detalles={
                    "codigo_insumo": codigo,
                    "nombre_insumo": nombre_insumo,
                    "cantidad_ingresada": cant_ingresada,
                    "cantidad_total": cant_final,
                    "modo": modo_registro,
                    "rol": rol,
                    "dispositivo": "WEB_MOVIL",
                    "observacion": observacion,
                    "timestamp": ahora_iso
                }
            )

            logger.info(f"[MOVIL] Conteo guardado: [{codigo}] {nombre_insumo} -> {cant_final:g} unds ({usuario})")
            return {
                "exito": True,
                "codigo_insumo": codigo,
                "nombre": nombre_insumo,
                "cantidad_ingresada": cant_ingresada,
                "cantidad_total": cant_final,
                "modo": modo_registro,
                "mensaje": f"Guardado: {cant_final:g} unidades totales"
            }
        except Exception as ex:
            log_error(f"guardar_conteo_movil({codigo_insumo})", ex)
            return {"exito": False, "error": str(ex)}

    def obtener_historial_insumo(self, codigo_insumo: str) -> list:
        """Obtiene la traza histórica de conteos y ediciones de un insumo."""
        try:
            from core.audit_logger import obtener_historial_acciones
            from core.fecha_utils import parsear_a_fecha_local, formatear_fecha_hora_local
            acciones = obtener_historial_acciones(limit=200, modulo="CONTEO_MOVIL")
            acciones_desktop = obtener_historial_acciones(limit=200, modulo="CONTEO")
            todas = (acciones or []) + (acciones_desktop or [])

            # Eliminar duplicados por ID de acción
            vistas_ids = set()
            filtradas = []
            for a in todas:
                aid = a.get("id_accion") or f"{a.get('fecha')}_{a.get('hora')}_{a.get('accion')}"
                if aid in vistas_ids:
                    continue
                vistas_ids.add(aid)

                det = a.get("detalles") or {}
                # Solo procesar si pertenece a este insumo y es una acción de conteo real
                es_mismo_insumo = str(det.get("codigo_insumo")) == str(codigo_insumo) or f"[{codigo_insumo}]" in a.get("accion", "")
                cant = det.get("cantidad_ingresada") if det.get("cantidad_ingresada") is not None else det.get("cantidad")
                
                if es_mismo_insumo and cant is not None:
                    filtradas.append({
                        "fecha": a.get("fecha"),
                        "hora": a.get("hora"),
                        "usuario": a.get("nombre_usuario") or a.get("usuario") or "Operario",
                        "rol": det.get("rol") or "OPERADOR",
                        "dispositivo": det.get("dispositivo") or ("WEB_MOVIL" if a.get("modulo") == "CONTEO_MOVIL" else "ESCRITORIO"),
                        "cantidad_ingresada": cant,
                        "cantidad_total": det.get("cantidad_total") if det.get("cantidad_total") is not None else cant,
                        "modo": det.get("modo") or "REEMPLAZAR",
                        "observacion": det.get("observacion") or a.get("accion")
                    })

            # Si no hay traza en logs pero sí en registro_auditorias_cierres, agregar registro
            if not filtradas:
                cod_enc = urllib.parse.quote(str(codigo_insumo).strip())
                res_aud = self.db.get(f"registro_auditorias_cierres?codigo_insumo=eq.{cod_enc}", timeout=5)
                for r in (res_aud.json() if res_aud and res_aud.status_code == 200 else []):
                    if r.get("cantidad_fisica") is not None:
                        obs = r.get("observacion") or "Conteo registrado en periodo"
                        user = "Operario"
                        rol = "OPERADOR"
                        if "[" in obs and "]" in obs:
                            user_part = obs.split("]")[0].replace("[", "")
                            if "(" in user_part:
                                user = user_part.split("(")[0].strip()
                                rol = user_part.split("(")[1].replace(")", "").strip()
                            else:
                                user = user_part
                        f_raw = r.get("fecha_cierre")
                        filtradas.append({
                            "fecha": parsear_a_fecha_local(f_raw),
                            "hora": formatear_fecha_hora_local(f_raw, "%H:%M:%S") if f_raw else "00:00:00",
                            "usuario": user,
                            "rol": rol,
                            "dispositivo": "SISTEMA",
                            "cantidad_ingresada": r.get("cantidad_fisica"),
                            "cantidad_total": r.get("cantidad_fisica"),
                            "modo": "REGISTRO",
                            "observacion": obs
                        })

            filtradas.sort(key=lambda x: f"{x.get('fecha')} {x.get('hora')}", reverse=True)
            return filtradas
        except Exception as ex:
            log_error(f"obtener_historial_insumo({codigo_insumo})", ex)
            return []


# Instancia singleton y alias de compatibilidad
mobile_service = MobileCountingService()
MobileService = MobileCountingService
