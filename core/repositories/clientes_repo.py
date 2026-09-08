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
        """Retorna la lista de vendedores/encargados únicos y activos registrados en encargados_cartera."""
        try:
            res_e = self.db.get("encargados_cartera?activo=eq.true&order=nombre.asc", timeout=6)
            if res_e and res_e.status_code == 200 and res_e.json():
                vendedores = []
                for r in res_e.json():
                    v = (r.get("nombre") or "").strip()
                    if v and v not in vendedores:
                        vendedores.append(v)
                return sorted(vendedores)
            return []
        except Exception as ex:
            log_error("get_vendedores_disponibles", ex)
            return []

    def get_encargados_completos(self, mes_periodo: str | None = None) -> list[dict]:
        """
        Retorna la lista de encargados activos con su porcentaje de comisión y el total
        recaudado en el periodo seleccionado (o histórico si no hay mes).
        """
        try:
            res_e = self.db.get("encargados_cartera?activo=eq.true&order=nombre.asc", timeout=8)
            encargados = res_e.json() if res_e and res_e.status_code == 200 and res_e.json() else []

            # Consultar pagos para totalizar lo recaudado por encargado
            endpoint_p = "pagos_cartera?estado_registro=neq.ANULADO&select=vendedor_encargado,monto_total,fecha_pago,id_pago,nombre_cliente,metodo_pago"
            pagos = self.db.get_all(endpoint_p, page_size=2000, timeout=15) or []

            recaudo_periodo_map: dict[str, float] = {}
            recaudo_historico_map: dict[str, float] = {}
            cant_pagos_periodo_map: dict[str, int] = {}
            cant_pagos_historico_map: dict[str, int] = {}
            pagos_por_encargado: dict[str, list[dict]] = {}

            for p in pagos:
                v_enc = (p.get("vendedor_encargado") or "").strip()
                if not v_enc:
                    continue
                monto = float(p.get("monto_total") or 0.0)
                fec = str(p.get("fecha_pago") or "")[:7]

                recaudo_historico_map[v_enc] = recaudo_historico_map.get(v_enc, 0.0) + monto
                cant_pagos_historico_map[v_enc] = cant_pagos_historico_map.get(v_enc, 0) + 1
                pagos_por_encargado.setdefault(v_enc, []).append(p)

                if mes_periodo and fec == mes_periodo:
                    recaudo_periodo_map[v_enc] = recaudo_periodo_map.get(v_enc, 0.0) + monto
                    cant_pagos_periodo_map[v_enc] = cant_pagos_periodo_map.get(v_enc, 0) + 1

            for e in encargados:
                nom = e.get("nombre") or ""
                com_pct = float(e.get("porcentaje_comision") or 0.0)
                tot_per = recaudo_periodo_map.get(nom, 0.0) if mes_periodo else recaudo_historico_map.get(nom, 0.0)
                cant_per = cant_pagos_periodo_map.get(nom, 0) if mes_periodo else cant_pagos_historico_map.get(nom, 0)
                tot_hist = recaudo_historico_map.get(nom, 0.0)

                e["porcentaje_comision"] = com_pct
                e["total_recaudado_periodo"] = round(tot_per, 2)
                e["cantidad_pagos_periodo"] = cant_per
                e["total_recaudado_historico"] = round(tot_hist, 2)
                e["comision_estimada_periodo"] = round(tot_per * (com_pct / 100.0), 2)
                e["pagos_lista"] = pagos_por_encargado.get(nom, [])

            return encargados
        except Exception as ex:
            log_error("get_encargados_completos", ex)
            return []

    def crear_encargado(self, nombre: str, porcentaje_comision: float = 0.0, telefono: str = "") -> dict | None:
        """Crea un nuevo encargado en la base de datos."""
        import uuid
        nom_clean = nombre.strip()
        if not nom_clean:
            return None
        try:
            payload = {
                "id_encargado": str(uuid.uuid4()),
                "nombre": nom_clean,
                "porcentaje_comision": round(float(porcentaje_comision or 0.0), 2),
                "telefono": telefono.strip() if telefono else None,
                "activo": True
            }
            res = self.db.post("encargados_cartera", json_data=payload, timeout=8)
            if res and res.status_code in (200, 201):
                return payload
            elif res and res.status_code == 409:
                nom_q = urllib.parse.quote(nom_clean)
                self.db.patch(f"encargados_cartera?nombre=eq.{nom_q}", json_data={"activo": True, "porcentaje_comision": payload["porcentaje_comision"]}, timeout=8)
                return payload
        except Exception as ex:
            log_error(f"crear_encargado({nom_clean})", ex)
        return None

    def actualizar_encargado(self, id_encargado: str, nombre_anterior: str, nombre_nuevo: str, porcentaje_comision: float, telefono: str = "") -> bool:
        """Actualiza un encargado y propaga el cambio de nombre a clientes y pagos si cambió."""
        nom_ant = nombre_anterior.strip()
        nom_nue = nombre_nuevo.strip()
        if not nom_nue:
            return False
        try:
            payload = {
                "nombre": nom_nue,
                "porcentaje_comision": round(float(porcentaje_comision or 0.0), 2),
                "telefono": telefono.strip() if telefono else None
            }
            res = self.db.patch(f"encargados_cartera?id_encargado=eq.{id_encargado}", json_data=payload, timeout=8)
            ok = bool(res and res.status_code in (200, 204))

            if ok and nom_ant and nom_ant != nom_nue:
                try:
                    nom_q = urllib.parse.quote(nom_ant)
                    self.db.patch(f"clientes?vendedor_encargado=eq.{nom_q}", json_data={"vendedor_encargado": nom_nue, "porcentaje_comision": payload["porcentaje_comision"]}, timeout=8)
                except Exception:
                    pass
                try:
                    nom_q = urllib.parse.quote(nom_ant)
                    self.db.patch(f"pagos_cartera?vendedor_encargado=eq.{nom_q}", json_data={"vendedor_encargado": nom_nue}, timeout=8)
                except Exception:
                    pass

            return ok
        except Exception as ex:
            log_error(f"actualizar_encargado({id_encargado})", ex)
            return False

    def eliminar_encargado(self, id_encargado: str | None = None, nombre: str = "") -> bool:
        """Elimina o desactiva un encargado de la cartera por ID o por Nombre."""
        nom_clean = (nombre or "").strip()
        ok = False
        try:
            if id_encargado:
                res = self.db.patch(f"encargados_cartera?id_encargado=eq.{id_encargado}", json_data={"activo": False}, timeout=8)
                ok = bool(res and res.status_code in (200, 204))
                if not ok:
                    res_d = self.db.delete(f"encargados_cartera?id_encargado=eq.{id_encargado}", timeout=8)
                    ok = bool(res_d and res_d.status_code in (200, 204))

            if not ok and nom_clean:
                nom_q = urllib.parse.quote(nom_clean)
                res_n = self.db.patch(f"encargados_cartera?nombre=eq.{nom_q}", json_data={"activo": False}, timeout=8)
                ok = bool(res_n and res_n.status_code in (200, 204))
                if not ok:
                    res_nd = self.db.delete(f"encargados_cartera?nombre=eq.{nom_q}", timeout=8)
                    ok = bool(res_nd and res_nd.status_code in (200, 204))

            if nom_clean:
                try:
                    nom_q = urllib.parse.quote(nom_clean)
                    self.db.patch(f"clientes?vendedor_encargado=eq.{nom_q}", json_data={"vendedor_encargado": None, "porcentaje_comision": 0.0}, timeout=8)
                except Exception:
                    pass

            return ok
        except Exception as ex:
            log_error(f"eliminar_encargado({id_encargado}, {nom_clean})", ex)
            return False
