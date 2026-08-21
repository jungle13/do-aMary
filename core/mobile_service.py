"""
Servicio central para el módulo de conteo móvil y servidor Web local.
Maneja detección de IP, generación de QR, búsqueda difusa y sincronización con Supabase.
"""
import socket
import io
import base64
import threading
import datetime
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

    def refrescar_catalogo(self, forzar: bool = False):
        """Mantiene en memoria el catálogo con nombres, códigos y stock para búsqueda ultra-rápida."""
        ahora = datetime.datetime.now()
        if not forzar and self.catalogo_cache and self.last_cache_update:
            if (ahora - self.last_cache_update).total_seconds() < 300: # 5 minutos
                return

        try:
            res = self.db.get("catalogo_insumos?select=codigo_insumo,nombre,categoria,costo_unitario,precio_venta,stock_actual,tipo_unidad&estado=eq.true&order=nombre.asc", timeout=15)
            if res and res.status_code == 200:
                self.catalogo_cache = res.json()
                self.last_cache_update = ahora
                logger.info(f"Catálogo móvil actualizado con {len(self.catalogo_cache)} insumos.")
        except Exception as ex:
            log_error("refrescar_catalogo", ex)

    def buscar_insumos(self, query: str, limit: int = 30) -> list:
        """Búsqueda multi-palabra (multi-token fuzzy) sobre el catálogo de insumos."""
        self.refrescar_catalogo()
        if not query or not query.strip():
            return self.catalogo_cache[:limit]

        tokens = [t.lower().strip() for t in query.strip().split() if t.strip()]
        resultados = []

        for item in self.catalogo_cache:
            codigo = str(item.get("codigo_insumo") or "").lower()
            nombre = str(item.get("nombre") or "").lower()
            categoria = str(item.get("categoria") or "").lower()
            texto_completo = f"{codigo} {nombre} {categoria}"

            # Debe contener todos los tokens buscados
            if all(t in texto_completo for t in tokens):
                resultados.append(item)
                if len(resultados) >= limit:
                    break

        return resultados

    def obtener_periodo_agosto(self) -> str:
        """Obtiene o asegura la existencia del periodo 2026-08."""
        try:
            res = self.db.get("periodos_inventario?mes_periodo=eq.2026-08&select=id_periodo", timeout=10)
            if res and res.status_code == 200 and res.json():
                return res.json()[0]["id_periodo"]
            
            # Si no existe, crearlo
            payload = {
                "mes_periodo": "2026-08",
                "fecha_inicio": "2026-08-01",
                "estado": "ABIERTO"
            }
            res_post = self.db.post("periodos_inventario", json_data=payload, timeout=10)
            if res_post and res_post.status_code in (200, 201):
                data = res_post.json()
                return data[0]["id_periodo"] if isinstance(data, list) else data.get("id_periodo")
        except Exception as ex:
            log_error("obtener_periodo_agosto", ex)
        
        return "cf024d27-7a47-4354-9c49-c0c348d7cf5f" # Fallback al ID de Agosto existente en BD

    def guardar_stock_inicial(self, codigo_insumo: str, cantidad: float, costo_unitario: float | None = None, usuario: str = "Móvil Bodega") -> dict:
        """
        Registra o actualiza el stock inicial de Agosto en Supabase.
        Escribe en registro_auditorias_cierres y sincroniza catalogo_insumos.
        """
        try:
            id_periodo = self.obtener_periodo_agosto()
            codigo = str(codigo_insumo).strip()
            cant = float(cantidad)

            # 1. Obtener costo del insumo
            costo = float(costo_unitario) if costo_unitario is not None and float(costo_unitario) > 0 else 0.0
            nombre_insumo = ""
            for item in self.catalogo_cache:
                if str(item.get("codigo_insumo")) == codigo:
                    if costo <= 0:
                        costo = float(item.get("costo_unitario") or 0.0)
                    nombre_insumo = item.get("nombre") or ""
                    # Actualizar en caché local
                    item["stock_actual"] = cant
                    if costo > 0:
                        item["costo_unitario"] = costo
                    break

            # Si sigue en 0, consultar última compra registrada
            if costo <= 0:
                try:
                    res_c = self.db.get(f"registro_compras?codigo_insumo=eq.{codigo}&order=fecha.desc&limit=1&select=costo_unitario", timeout=5)
                    if res_c and res_c.status_code == 200 and res_c.json():
                        costo = float(res_c.json()[0].get("costo_unitario") or 0.0)
                except Exception:
                    pass

            # 2. Buscar si ya existe el registro de auditoría para Agosto
            endpoint_aud = f"registro_auditorias_cierres?id_periodo=eq.{id_periodo}&codigo_insumo=eq.{codigo}&tipo_registro=eq.INVENTARIO_INICIAL&select=id_auditoria"
            res_aud = self.db.get(endpoint_aud, timeout=10)
            
            payload = {
                "id_periodo": id_periodo,
                "codigo_insumo": codigo,
                "tipo_registro": "INVENTARIO_INICIAL",
                "fecha_cierre": "2026-08-01T00:00:00+00:00",
                "cantidad_sistema": cant,
                "cantidad_fisica": cant,
                "diferencia": 0.0,
                "costo_unitario_snapshot": costo,
                "estado": "APROBADO",
                "observacion": f"Conteo inicial Agosto - Registrado por {usuario} a las {datetime.datetime.now().strftime('%H:%M:%S')}"
            }

            if res_aud and res_aud.status_code == 200 and res_aud.json():
                id_aud = res_aud.json()[0]["id_auditoria"]
                res_save = self.db.patch(f"registro_auditorias_cierres?id_auditoria=eq.{id_aud}", json_data=payload, timeout=10)
            else:
                headers = {"Prefer": "resolution=merge-duplicates"}
                res_save = self.db.post("registro_auditorias_cierres", json_data=payload, custom_headers=headers, timeout=10)

            # 3. Actualizar catalogo_insumos.stock_actual y costo_unitario
            datos_cat = {"stock_actual": cant}
            if costo > 0:
                datos_cat["costo_unitario"] = costo
            self.db.patch(f"catalogo_insumos?codigo_insumo=eq.{codigo}", json_data=datos_cat, timeout=10)

            registro_historial = {
                "codigo": codigo,
                "nombre": nombre_insumo,
                "cantidad": cant,
                "costo": costo,
                "hora": datetime.datetime.now().strftime("%H:%M:%S"),
                "usuario": usuario
            }
            from core.audit_logger import registrar_accion
            registrar_accion(
                accion=f"Registro / Guardado de Conteo Inicial para insumo [{codigo}] {nombre_insumo}: {cant} unds (Costo U: ${costo:,.0f})",
                modulo="CONTEO",
                usuario=usuario,
                detalles={"codigo_insumo": codigo, "nombre": nombre_insumo, "cantidad": cant, "costo": costo}
            )

            logger.info(f"Stock Inicial Agosto guardado: [{codigo}] {nombre_insumo} -> {cant} unds (Costo: ${costo:,.0f})")
            return {
                "exito": True,
                "codigo_insumo": codigo,
                "nombre": nombre_insumo,
                "cantidad": cant,
                "costo_unitario": costo,
                "mensaje": f"Guardado con éxito: {cant} unidades ($ {costo:,.0f})"
            }

        except Exception as ex:
            log_error(f"guardar_stock_inicial({codigo_insumo}, {cantidad})", ex)
            return {"exito": False, "error": str(ex)}

    def get_historial(self) -> list:
        return self.historial_reciente
