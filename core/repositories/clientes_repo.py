"""
Repositorio para la gestión de Clientes del Sistema Doña Mary.
Maneja normalización de nombres, búsqueda difusa, caché en memoria y auto-creación sin duplicados.
"""
import re
import urllib.parse
import threading
from core.database import BaseDatabase
from core.logger import get_logger, log_error

logger = get_logger("ClientesRepo")

class ClientesRepository:
    _cache_clientes = {}
    _cache_lock = threading.Lock()

    def __init__(self, db: BaseDatabase | None = None):
        self.db = db or BaseDatabase()

    @staticmethod
    def normalizar_nombre_cliente(nombre_raw: str | None) -> str:
        """
        Limpia y estandariza el nombre del cliente para evitar duplicaciones.
        - Elimina prefijos comunes (Cliente:, Señores:, etc.)
        - Colapsa espacios múltiples
        - Estandariza 'CLIENTES VARIOS' / 'CONSUMIDOR FINAL' / 'VARIOS'
        - Retorna texto en MAYÚSCULAS limpio.
        """
        if not nombre_raw:
            return "CLIENTES VARIOS"
        
        texto = str(nombre_raw).strip()
        # Quitar prefijos comunes
        texto = re.sub(r'^(cliente|se[ñn]ores|se[ñn]or\(a\)|sr\(a\)|razon social|r\.s\.|sr|sra)[\s:\.\-]+', '', texto, flags=re.IGNORECASE)
        # Quitar NITs o identificaciones pegadas al nombre si las hay
        texto = re.sub(r'\s+(nit|c\.c\.|cc|rut)[\s:\.\-]*\d+.*$', '', texto, flags=re.IGNORECASE)
        # Colapsar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto).strip().upper()

        if not texto or texto in ("VARIOS", "CLIENTE VARIOS", "CLIENTES VARIOS", "CONSUMIDOR FINAL", "PUBLICO GENERAL", "SIN NOMBRE"):
            return "CLIENTES VARIOS"

        return texto

    def asegurar_clientes_existen(self, items_or_names_list: list):
        """
        Verifica y auto-registra clientes en lote (batch) de forma hiper-optimizada.
        Reduce cientos de peticiones HTTP a solo 1 o 2 peticiones masivas.
        """
        if not items_or_names_list:
            return

        # 1. Extraer y normalizar nombres únicos entrantes
        nombres_entrantes = set()
        for item in items_or_names_list:
            if isinstance(item, str):
                nom = self.normalizar_nombre_cliente(item)
            elif isinstance(item, dict):
                nom = self.normalizar_nombre_cliente(item.get("cliente") or item.get("nombre_cliente") or item.get("nombre"))
            else:
                continue
            if nom:
                nombres_entrantes.add(nom)

        if not nombres_entrantes:
            return

        # 2. Filtrar los que ya están en caché local
        with self._cache_lock:
            faltan_en_cache = [nom for nom in nombres_entrantes if nom not in self._cache_clientes]

        if not faltan_en_cache:
            return

        # 3. Consultar en Supabase en lotes (chunks) de 50 nombres
        existentes_en_db = {}
        chunk_size = 50
        for i in range(0, len(faltan_en_cache), chunk_size):
            chk = faltan_en_cache[i:i + chunk_size]
            noms_str = ",".join([urllib.parse.quote(nom) for nom in chk])
            try:
                res = self.db.get(f"clientes?select=id_cliente,nombre,tipo_cliente&nombre=in.({noms_str})", timeout=10)
                if res and res.status_code == 200:
                    for row in res.json():
                        nom_db = row.get("nombre")
                        if nom_db:
                            existentes_en_db[nom_db] = row
            except Exception as ex:
                logger.warning(f"Error consultando clientes chunk {i}: {ex}")

        # Actualizar caché con los encontrados
        with self._cache_lock:
            for nom, c_data in existentes_en_db.items():
                self._cache_clientes[nom] = c_data

        # 4. Insertar en lote todos los clientes que realmente no existen en la base de datos
        nuevos_a_crear = [nom for nom in faltan_en_cache if nom not in existentes_en_db]
        if nuevos_a_crear:
            nuevos_payload = []
            for nom in nuevos_a_crear:
                es_varios = (nom == "CLIENTES VARIOS")
                nuevos_payload.append({
                    "nombre": nom,
                    "tipo_cliente": "CLIENTES_VARIOS" if es_varios else "REGULAR",
                    "limite_credito": 0.0
                })

            for i in range(0, len(nuevos_payload), chunk_size):
                sub_nuevos = nuevos_payload[i:i + chunk_size]
                try:
                    res_post = self.db.post("clientes", json_data=sub_nuevos, timeout=12)
                    if res_post and res_post.status_code in (200, 201, 204):
                        sub_noms = [x["nombre"] for x in sub_nuevos]
                        sub_noms_str = ",".join([urllib.parse.quote(nom) for nom in sub_noms])
                        res_get = self.db.get(f"clientes?select=id_cliente,nombre,tipo_cliente&nombre=in.({sub_noms_str})", timeout=10)
                        if res_get and res_get.status_code == 200:
                            with self._cache_lock:
                                for row in res_get.json():
                                    if row.get("nombre"):
                                        self._cache_clientes[row["nombre"]] = row
                    else:
                        with self._cache_lock:
                            for item in sub_nuevos:
                                self._cache_clientes[item["nombre"]] = {"id_cliente": None, "nombre": item["nombre"], "tipo_cliente": item["tipo_cliente"]}
                except Exception as ex:
                    logger.warning(f"Error insertando clientes nuevos en lote: {ex}")
                    with self._cache_lock:
                        for item in sub_nuevos:
                            self._cache_clientes[item["nombre"]] = {"id_cliente": None, "nombre": item["nombre"], "tipo_cliente": item["tipo_cliente"]}

            logger.info(f"Sincronizados en lote {len(nuevos_a_crear)} clientes nuevos en catálogo.")

    def get_or_create_cliente(self, nombre_raw: str | None) -> dict:
        """
        Busca un cliente por su nombre normalizado. Si no existe, lo crea automáticamente en Supabase.
        """
        nombre_clean = self.normalizar_nombre_cliente(nombre_raw)

        with self._cache_lock:
            if nombre_clean in self._cache_clientes:
                return self._cache_clientes[nombre_clean]

        try:
            nom_enc = urllib.parse.quote(nombre_clean)
            endpoint = f"clientes?nombre=eq.{nom_enc}&limit=1"
            res = self.db.get(endpoint, timeout=5)

            if res and res.status_code == 200 and res.json():
                cliente = res.json()[0]
                with self._cache_lock:
                    self._cache_clientes[nombre_clean] = cliente
                return cliente

            # Si no existe, crearlo
            es_varios = (nombre_clean == "CLIENTES VARIOS")
            nuevo_payload = {
                "nombre": nombre_clean,
                "tipo_cliente": "CLIENTES_VARIOS" if es_varios else "REGULAR",
                "limite_credito": 0.0
            }

            res_post = self.db.post("clientes", json_data=nuevo_payload, timeout=5)
            if res_post and res_post.status_code in (200, 201):
                res_get = self.db.get(f"clientes?nombre=eq.{nom_enc}&limit=1", timeout=5)
                if res_get and res_get.status_code == 200 and res_get.json():
                    cliente_creado = res_get.json()[0]
                    with self._cache_lock:
                        self._cache_clientes[nombre_clean] = cliente_creado
                    logger.info(f"Nuevo cliente registrado automáticamente: {nombre_clean}")
                    return cliente_creado

            fallback = {"id_cliente": None, "nombre": nombre_clean, "tipo_cliente": "REGULAR"}
            with self._cache_lock:
                self._cache_clientes[nombre_clean] = fallback
            return fallback

        except Exception as ex:
            log_error(f"get_or_create_cliente({nombre_clean})", ex)
            return {"id_cliente": None, "nombre": nombre_clean, "tipo_cliente": "REGULAR"}

    def get_clientes(self, search: str = "") -> list[dict]:
        """Retorna la lista de todos los clientes registrados."""
        try:
            endpoint = "clientes?order=nombre.asc"
            if search:
                s_clean = urllib.parse.quote(search.strip().upper())
                endpoint += f"&nombre=ilike.*{s_clean}*"
            
            res = self.db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                data = res.json()
                with self._cache_lock:
                    for c in data:
                        if c.get("nombre"):
                            self._cache_clientes[c["nombre"]] = c
                return data
            return []
        except Exception as ex:
            log_error("get_clientes", ex)
            return []

    def crear_cliente(self, datos: dict) -> dict | None:
        """Crea un cliente manual con todos sus datos."""
        try:
            nombre = self.normalizar_nombre_cliente(datos.get("nombre"))
            payload = {
                "nombre": nombre,
                "tipo_cliente": datos.get("tipo_cliente", "REGULAR"),
                "telefono": (datos.get("telefono") or "").strip(),
                "direccion": (datos.get("direccion") or "").strip(),
                "email": (datos.get("email") or "").strip(),
                "limite_credito": float(datos.get("limite_credito") or 0.0),
                "notas": (datos.get("notas") or "").strip()
            }
            res = self.db.post("clientes", json_data=payload, timeout=8)
            if res and res.status_code in (200, 201):
                nom_enc = urllib.parse.quote(nombre)
                res_get = self.db.get(f"clientes?nombre=eq.{nom_enc}&limit=1", timeout=5)
                if res_get and res_get.status_code == 200 and res_get.json():
                    created = res_get.json()[0]
                    with self._cache_lock:
                        self._cache_clientes[nombre] = created
                    return created
            return None
        except Exception as ex:
            log_error("crear_cliente", ex)
            return None

    def actualizar_cliente(self, id_cliente: str, datos: dict) -> bool:
        """Actualiza datos de un cliente existente."""
        try:
            id_enc = urllib.parse.quote(str(id_cliente))
            res = self.db.patch(f"clientes?id_cliente=eq.{id_enc}", json_data=datos, timeout=8)
            return bool(res and res.status_code in (200, 204))
        except Exception as ex:
            log_error(f"actualizar_cliente({id_cliente})", ex)
            return False

    def asignar_vendedor_cliente(self, nombre_cliente: str, vendedor: str | None, porcentaje_comision: float = 0.0) -> bool:
        """Asigna o actualiza el vendedor encargado y porcentaje de comisión a un cliente."""
        try:
            nombre_clean = self.normalizar_nombre_cliente(nombre_cliente)
            nom_enc = urllib.parse.quote(nombre_clean)
            v_val = (vendedor or "").strip()
            p_val = max(0.0, float(porcentaje_comision or 0.0))

            payload = {
                "vendedor_encargado": v_val if v_val else None,
                "porcentaje_comision": p_val
            }

            # Asegurar que el cliente existe primero
            cli = self.get_or_create_cliente(nombre_clean)
            if cli and cli.get("id_cliente"):
                id_enc = urllib.parse.quote(str(cli["id_cliente"]))
                res = self.db.patch(f"clientes?id_cliente=eq.{id_enc}", json_data=payload, timeout=8)
            else:
                res = self.db.patch(f"clientes?nombre=eq.{nom_enc}", json_data=payload, timeout=8)

            ok = bool(res and res.status_code in (200, 204))
            if ok:
                with self._cache_lock:
                    if nombre_clean in self._cache_clientes:
                        self._cache_clientes[nombre_clean]["vendedor_encargado"] = payload["vendedor_encargado"]
                        self._cache_clientes[nombre_clean]["porcentaje_comision"] = payload["porcentaje_comision"]
            return ok
        except Exception as ex:
            log_error(f"asignar_vendedor_cliente({nombre_cliente})", ex)
            return False

    def get_vendedores_disponibles(self) -> list[str]:
        """Retorna la lista de vendedores únicos registrados en el catálogo de clientes."""
        try:
            res = self.db.get("clientes?select=vendedor_encargado&vendedor_encargado=not.is.null", timeout=6)
            if res and res.status_code == 200 and res.json():
                vendedores = set()
                for r in res.json():
                    v = (r.get("vendedor_encargado") or "").strip()
                    if v:
                        vendedores.add(v)
                return sorted(list(vendedores))
            return []
        except Exception as ex:
            log_error("get_vendedores_disponibles", ex)
            return []
