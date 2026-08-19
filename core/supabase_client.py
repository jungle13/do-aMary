import requests
import datetime
import urllib.parse
from config import Config

_client_instance = None

def get_client():
    """Retorna la instancia singleton del cliente Supabase."""
    global _client_instance
    if _client_instance is None:
        _client_instance = SupabaseClient()
    return _client_instance

class SupabaseClient:
    def __init__(self):
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY
        
        if self.url and self.url.endswith('/'):
            self.url = self.url[:-1]
        if self.url and not self.url.endswith('/rest/v1'):
            self.url = self.url + "/rest/v1"
            
        # 1. Instanciar la sesión compartida para mantener viva la conexión TCP
        self.session = requests.Session()
        
        # 2. Configurar los encabezados globales directamente en la sesión
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }
        self.session.headers.update(self.headers)
        
    def check_connection(self):
        if not self.url or not self.key:
            return False, "Faltan credenciales"
        try:
            # Prueba simple a la tabla (limit 1)
            response = self.session.get(f"{self.url}/catalogo_insumos?limit=1", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return True, "Conexión exitosa"
            return False, f"Error: {response.text}"
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en check_connection: el servidor no responde")
        except Exception as e:
            return False, str(e)
            
    # --- CRUD Catálogo Insumos ---
    
    def get_categorias(self):
        """Obtiene una lista de categorías únicas usando RPC si existe, o extrayendo de todo (simplificado)"""
        # Para simplificar y dado que PostgREST soporta distinct
        url = f"{self.url}/catalogo_insumos?select=categoria"
        headers = self.headers.copy()
        # En PostgREST podemos usar un header o query para distintos, pero es más fácil
        # traerlos y filtrarlos en memoria (limitado a unos cientos si hay muchos, pero está bien).
        response = self.session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            categorias = set([item.get('categoria', 'SIN CATEGORIA') for item in data if item.get('categoria')])
            return sorted(list(categorias))
        return []

    def get_insumos(self, page=1, page_size=20, search="", categoria="", fecha_corte=None, sort_col="Insumo", sort_asc=True, codigos_filtro=None):
        """
        Obtiene los insumos con paginación, filtros y ordenamiento desde el servidor.
        Retorna (lista_datos, total_count)
        """
        if fecha_corte:
            url = f"{self.url}/rpc/obtener_inventario_por_fecha?select=*"
        else:
            url = f"{self.url}/vista_inventario_completo?select=*"
        
        filtros = []
        if codigos_filtro is not None:
            if not codigos_filtro:
                filtros.append("codigo_insumo=in.(INVALID_FORCE_EMPTY)")
            else:
                codigos_str = ",".join(codigos_filtro)
                filtros.append(f"codigo_insumo=in.({codigos_str})")
                
        if categoria and categoria != "Todas":
            filtros.append(f"categoria=eq.{categoria}")
            
        if search:
            filtros.append(f"or=(nombre.ilike.*{search}*,codigo_insumo.ilike.*{search}*)")
            
        if filtros:
            url += "&" + "&".join(filtros)
            
        # Mapeo de columnas de la interfaz a las columnas de la vista SQL
        db_col_stock = "stock_real" if fecha_corte else "stock_actual"
        map_columnas = {
            "Código": "codigo_insumo",
            "Insumo": "nombre",
            "Categoría": "categoria",
            "Ubicación": "ubicacion",
            "Stock Inicial": "stock_inicial",
            "Stock Mínimo": "stock_minimo",
            "Entradas": "entradas",
            "Salidas": "salidas",
            "Stock Real": db_col_stock
        }
        
        db_col = map_columnas.get(sort_col, "nombre")
        direccion = "asc" if sort_asc else "desc"
        
        offset = (page - 1) * page_size
        url += f"&order={db_col}.{direccion}&offset={offset}&limit={page_size}"
        
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            if fecha_corte:
                payload = {"p_fecha_corte": f"{fecha_corte} 23:59:59"}
                response = self.session.post(url, headers=headers, json=payload, timeout=10)
            else:
                response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code in (200, 201, 206):
                data = response.json()
                content_range = response.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                print(f"Error en consulta: {response.text}")
                return [], 0
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_insumos: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_insumos: {e}")
            return [], 0
        
    def insert_insumo(self, data: dict):
        url = f"{self.url}/catalogo_insumos"
        response = self.session.post(url, json=data, headers=self.headers, timeout=10)
        if response.status_code in (200, 201):
            return response.json()
        return None

    def update_insumo(self, codigo_insumo: str, datos_actualizados: dict) -> bool:
        """
        Actualiza un insumo existente en el catálogo.
        """
        url = f"{self.url}/catalogo_insumos?codigo_insumo=eq.{codigo_insumo}"
        try:
            response = self.session.patch(url, json=datos_actualizados, headers=self.headers, timeout=10)
            if response.status_code in (200, 204):
                return True
            else:
                print(f"Error al actualizar insumo: {response.text}")
                return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en update_insumo: el servidor no responde")
        except Exception as e:
            print(f"Excepción en update_insumo: {e}")
            return False

    def get_compras(self, page=1, page_size=15, search="", fecha_corte=None, factura_filtro=None, proveedor_filtro=None):
        try:
            offset = (page - 1) * page_size
            # Incluir 'iva' explícitamente en el select
            select_query = "id_compra,fecha,numero_entrada,numero_factura,proveedor,codigo_insumo,cantidad,costo_unitario,iva,valor_iva,costo_total,estado_registro,catalogo_insumos(nombre)"
            
            url = f"{self.url}/registro_compras?select={select_query}&estado_registro=eq.VÁLIDO&order=fecha.desc"
            
            if factura_filtro:
                url += f"&or=(numero_entrada.eq.{factura_filtro},numero_factura.eq.{factura_filtro})"
            if proveedor_filtro:
                url += f"&proveedor=eq.{proveedor_filtro}"
                
            res = self.session.get(url, headers=self.headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                
                # Filtrado por fecha_corte y búsqueda
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
            print(f"Error en get_compras: {ex}")
            return [], 0

    def get_historial_compras_dia(self, fecha_dia: str, agrupar_por: str = "FACTURA") -> list:
        """
        Recupera todas las compras de un día (YYYY-MM-DD),
        agrupados por 'FACTURA' o por 'PROVEEDOR'.
        """
        items_resultado = []
        try:
            # Consulta exclusiva a compras del día
            url_c = f"{self.url}/registro_compras?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=numero_entrada,numero_factura,proveedor,costo_total,fecha,cantidad&order=fecha.desc"
            res_c = self.session.get(url_c, headers=self.headers, timeout=10)
    
            if res_c.status_code == 200:
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
                    for r in data_c:
                        prov = r.get("proveedor") or "Clientes Varios"
                        if prov not in agrupado:
                            agrupado[prov] = {
                                "tipo": "PROVEEDOR_RESUMEN",
                                "ref": prov,
                                "proveedor": prov,
                                "facturas_count": set(),
                                "total": 0.0,
                                "unidades": 0.0,
                                "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                            }
                        agrupado[prov]["facturas_count"].add(r.get("numero_factura") or r.get("numero_entrada"))
                        agrupado[prov]["total"] += float(r.get("costo_total") or 0)
                        agrupado[prov]["unidades"] += float(r.get("cantidad") or 0)
    
                    for p in agrupado.values():
                        p["facturas_cant"] = len(p["facturas_count"])
                        del p["facturas_count"]
                        items_resultado.append(p)
    
        except Exception as ex:
            print(f"Error en historial de compras del día: {ex}")
    
        # Ordenar por hora/valor descendente
        items_resultado.sort(key=lambda x: x["total"], reverse=True)
        return items_resultado


    def insert_compras(self, compras_list):
        if not compras_list: return True
        try:
            url = f"{self.url}/registro_compras"
            payload = []
            for item in compras_list:
                payload.append({
                    "numero_entrada": item.get("numero_entrada"),
                    "fecha": item.get("fecha"),
                    "numero_factura": item.get("numero_factura"),
                    "proveedor": item.get("proveedor"),
                    "codigo_insumo": item.get("codigo_insumo"),
                    "cantidad": float(item.get("cantidad") or 0),
                    "costo_unitario": float(item.get("costo_unitario") or 0),
                    "iva": float(item.get("iva") or item.get("valor_iva") or 0),
                    "valor_iva": float(item.get("iva") or item.get("valor_iva") or 0),
                    "costo_total": float(item.get("costo_total") or 0),
                    "estado_registro": "VÁLIDO"
                })
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            return res.status_code in (200, 201)
        except Exception as ex:
            print(f"Error en insert_compras: {ex}")
            return False

    def get_entradas_existentes(self, lista_eas: list) -> set:
        """
        Consulta cuáles de los 'numero_entrada' proveídos ya existen en registro_compras.
        """
        if not lista_eas:
            return set()
            
        url = f"{self.url}/registro_compras?select=numero_entrada"
        # Crear un filtro in.(EA-1,EA-2)
        eas_str = ",".join(lista_eas)
        url += f"&numero_entrada=in.({eas_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["numero_entrada"] for item in data if item.get("numero_entrada")}
            return set()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_entradas_existentes: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_entradas_existentes: {e}")
            return set()

    def eliminar_compras_por_entradas(self, lista_entradas):
        """Elimina registros de compras en Supabase por número de entrada o factura."""
        if not lista_entradas: return True
        try:
            for ref in lista_entradas:
                url = f"{self.url}/registro_compras?or=(numero_entrada.eq.{ref},numero_factura.eq.{ref})"
                self.session.delete(url, headers=self.headers, timeout=10)
            return True
        except Exception as ex:
            print(f"Error eliminando compras: {ex}")
            return False
            
    def get_nombres_insumos(self, lista_codigos: list) -> dict:
        """
        Devuelve un diccionario {codigo: nombre} buscando en catalogo_insumos.
        """
        if not lista_codigos:
            return {}
            
        url = f"{self.url}/catalogo_insumos?select=codigo_insumo,nombre"
        
        # Como los códigos pueden ser strings (ej "0471"), envolvemos en comillas simples para la API de supabase,
        # o usamos in. sin problemas si PostgREST lo maneja.
        # PostgREST maneja in.(a,b,c). Para strings con espacios podría requerir doble comilla, 
        # pero para códigos numéricos en string basta unirlos con coma.
        codigos_str = ",".join(lista_codigos)
        url += f"&codigo_insumo=in.({codigos_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["codigo_insumo"]: item["nombre"] for item in data if item.get("codigo_insumo")}
            return {}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_nombres_insumos: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_nombres_insumos: {e}")
            return {}


    def get_ventas(self, page=1, page_size=20, search="", fecha_corte=None, categoria_filtro=None, factura_filtro=None):
        # Si hay filtro de categoría, necesitamos !inner para que PostgREST aplique un INNER JOIN
        if categoria_filtro:
            url = f"{self.url}/registro_ventas?select=*,catalogo_insumos!inner(nombre,categoria)"
        else:
            url = f"{self.url}/registro_ventas?select=*,catalogo_insumos(nombre,categoria)"
        
        filtros = []
        
        # 1. Buscador por texto general
        if search:
            s_enc = urllib.parse.quote(search.strip())
            filtros.append(f"or=(codigo_insumo.ilike.*{s_enc}*,factura_no.ilike.*{s_enc}*,descripcion.ilike.*{s_enc}*)")
            
        # 2. Fecha
        if fecha_corte:
            filtros.append(f"fecha=gte.{fecha_corte}T00:00:00&fecha=lte.{fecha_corte}T23:59:59")

        # 3. Filtro por Categoría (Requiere catalogo_insumos.categoria)
        if categoria_filtro:
            cat_enc = urllib.parse.quote(str(categoria_filtro).strip())
            filtros.append(f"catalogo_insumos.categoria=eq.{cat_enc}")

        # 4. Filtro por Nro. Factura / Documento (Uso de ilike para coincidencia flexible)
        if factura_filtro:
            fact_enc = urllib.parse.quote(str(factura_filtro).strip())
            filtros.append(f"factura_no.ilike.*{fact_enc}*")
            
        if filtros:
            url += "&" + "&".join(filtros)
            
        offset = (page - 1) * page_size
        url += f"&order=fecha.desc,factura_no.desc&offset={offset}&limit={page_size}"
        
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code in (200, 206):
                data = response.json()
                content_range = response.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                print(f"Error HTTP {response.status_code} en get_ventas: {response.text}")
                return [], 0
        except Exception as e:
            print(f"Excepción en get_ventas: {e}")
            return [], 0

    def get_historial_ventas_dia(self, fecha_dia: str, agrupar_por: str = "CATEGORIA") -> list:
        """
        Recupera todas las ventas de un día (YYYY-MM-DD),
        agrupadas por 'CATEGORIA' o por 'FACTURA'.
        """
        items_resultado = []
        try:
            url_v = f"{self.url}/registro_ventas?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=factura_no,tipo_documento,descripcion,total,cantidad,codigo_insumo,fecha,catalogo_insumos(categoria,nombre)&order=fecha.desc"
            res_v = self.session.get(url_v, headers=self.headers, timeout=10)
            
            if res_v.status_code == 200:
                data_v = res_v.json()
                
                if agrupar_por == "CATEGORIA":
                    agrupado = {}
                    for r in data_v:
                        cat = r.get("catalogo_insumos", {}).get("categoria") if r.get("catalogo_insumos") else None
                        if not cat: cat = "SIN CATEGORÍA"
                        
                        if cat not in agrupado:
                            agrupado[cat] = {
                                "tipo": "CATEGORIA_RESUMEN",
                                "ref": cat,
                                "categoria": cat,
                                "total": 0.0,
                                "unidades": 0.0,
                                "items_count": 0
                            }
                        agrupado[cat]["total"] += float(r.get("total") or 0)
                        agrupado[cat]["unidades"] += float(r.get("cantidad") or 0)
                        agrupado[cat]["items_count"] += 1
                    items_resultado.extend(list(agrupado.values()))
    
                elif agrupar_por == "FACTURA":
                    agrupado = {}
                    for r in data_v:
                        ref = r.get("factura_no") or "S/N"
                        tipo_doc = r.get("tipo_documento") or "Factura POS"
                        if ref not in agrupado:
                            agrupado[ref] = {
                                "tipo": "FACTURA_VENTA",
                                "ref": ref,
                                "factura": ref,
                                "subtipo": tipo_doc,
                                "total": 0.0,
                                "unidades": 0.0
                            }
                        agrupado[ref]["total"] += float(r.get("total") or 0)
                        agrupado[ref]["unidades"] += float(r.get("cantidad") or 0)
                    items_resultado.extend(list(agrupado.values()))
    
        except Exception as ex:
            print(f"Error en historial de ventas del día: {ex}")
    
        items_resultado.sort(key=lambda x: x["total"], reverse=True)
        return items_resultado


    def get_ventas_existentes(self, lista_facturas: list) -> set:
        """
        Consulta cuáles de las facturas (factura_no) proveídas ya existen en registro_ventas.
        """
        if not lista_facturas:
            return set()
            
        url = f"{self.url}/registro_ventas?select=factura_no"
        facturas_str = ",".join(lista_facturas)
        url += f"&factura_no=in.({facturas_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["factura_no"] for item in data if item.get("factura_no")}
            return set()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_ventas_existentes: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_ventas_existentes: {e}")
            return set()

    def eliminar_ventas_origen(self, fecha: str, tipo_documento: str, pagina_origen: int) -> bool:
        """Elimina las ventas de una fecha, tipo y página específica para permitir sobreescritura limpia."""
        url = f"{self.url}/registro_ventas?fecha=gte.{fecha}T00:00:00&fecha=lte.{fecha}T23:59:59&tipo_documento=eq.{tipo_documento}&pagina_origen=eq.{pagina_origen}"
        try:
            response = self.session.delete(url, headers=self.headers, timeout=10)
            return response.status_code in (200, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en eliminar_ventas_origen: el servidor no responde")
        except Exception as e:
            print(f"Error al eliminar ventas por origen: {e}")
            return False

    def eliminar_ventas_por_facturas(self, lista_facturas):
        """Elimina registros de ventas en Supabase por número de factura."""
        if not lista_facturas: return True
        try:
            for fact in lista_facturas:
                url = f"{self.url}/registro_ventas?factura_no=eq.{fact}"
                self.session.delete(url, headers=self.headers, timeout=10)
            return True
        except Exception as ex:
            print(f"Error eliminando ventas: {ex}")
            return False

    def insert_ventas(self, ventas_list: list):
        """Inserta una lista de registros de ventas de forma masiva (bulk insert)."""
        url = f"{self.url}/registro_ventas"
        
        payload = []
        for v in ventas_list:
            venta = {
                "fecha": v.get("fecha"),
                "factura_no": str(v.get("numero_factura", "")),
                "codigo_insumo": str(v.get("codigo_item", "")),
                "descripcion": str(v.get("descripcion", "")),
                "cantidad": float(v.get("cantidad", 0) or 0),
                "subtotal": float(v.get("precio_unitario", 0) or 0),
                "iva": float(v.get("iva", 0) or 0),
                "total": float(v.get("costo_total", 0) or 0),
                "tipo_documento": str(v.get("tipo_documento", "Factura POS")),
                "pagina_origen": int(v.get("pagina_origen", 1))
            }
            payload.append(venta)
            
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201, 204):
                return True
            else:
                print(f"Error al insertar ventas: {response.text}")
                return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en insert_ventas: el servidor no responde")
        except Exception as e:
            print(f"Excepción en insert_ventas: {e}")
            return False



    def get_datos_conteo_inicial(self, mes_seleccionado: str) -> list:
        # mes_seleccionado is in format 'YYYY-MM'
        try:
            year, month = map(int, mes_seleccionado.split("-"))
            if month == 1:
                mes_anterior = f"{year - 1}-12"
            else:
                mes_anterior = f"{year}-{month - 1:02d}"
        except:
            return []
            
        # 1. Traer catalogo
        catalogo = []
        try:
            res_cat = self.session.get(f"{self.url}/catalogo_insumos?select=codigo_insumo,nombre,categoria", headers=self.headers, timeout=10)
            if res_cat.status_code == 200:
                catalogo = res_cat.json()
        except:
            pass
            
        # 2. Traer registros FINAL mes anterior
        cierre_anterior = {}
        try:
            url_ant = f"{self.url}/registro_auditorias_cierres?tipo_registro=eq.CIERRE_MENSUAL&fecha_cierre=gte.{mes_anterior}-01&fecha_cierre=lte.{mes_anterior}-31&select=codigo_insumo,cantidad_fisica"
            res_ant = self.session.get(url_ant, headers=self.headers, timeout=10)
            if res_ant.status_code == 200:
                for r in res_ant.json():
                    cierre_anterior[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except:
            pass
            
        # 3. Traer registros INICIAL mes seleccionado
        inicio_actual = {}
        try:
            url_act = f"{self.url}/registro_auditorias_cierres?tipo_registro=eq.INVENTARIO_INICIAL&fecha_cierre=gte.{mes_seleccionado}-01&fecha_cierre=lte.{mes_seleccionado}-31&select=codigo_insumo,cantidad_fisica"
            res_act = self.session.get(url_act, headers=self.headers, timeout=10)
            if res_act.status_code == 200:
                for r in res_act.json():
                    inicio_actual[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except:
            pass
            
        resultado = []
        for c in catalogo:
            codigo = c.get("codigo_insumo")
            if not codigo: continue
            
            resultado.append({
                "codigo_insumo": codigo,
                "nombre": c.get("nombre"),
                "categoria": c.get("categoria"),
                "cierre_mes_anterior": cierre_anterior.get(codigo, 0),
                "stock_inicial_actual": inicio_actual.get(codigo, 0),
            })
            
        return resultado

    def upsert_conteos_iniciales(self, registros: list) -> bool:
        if not registros: return True
        
        # Buscar IDs existentes para hacer merge por Primary Key (ya que no hay unique constraint compuesto)
        try:
            fecha_cierre = registros[0].get("fecha_cierre")
            tipo_registro = registros[0].get("tipo_registro")
            codigos = [r["codigo_insumo"] for r in registros]
            
            # Dividir en chunks si son muchos códigos para no exceder longitud de URL, o hacer query simple
            if len(codigos) > 0:
                codigos_str = ",".join(codigos)
                url_exist = f"{self.url}/registro_auditorias_cierres?fecha_cierre=eq.{fecha_cierre}&tipo_registro=eq.{tipo_registro}&codigo_insumo=in.({codigos_str})&select=id_auditoria,codigo_insumo"
                res_exist = self.session.get(url_exist, headers=self.headers, timeout=10)
                if res_exist.status_code == 200:
                    existentes = {item["codigo_insumo"]: item["id_auditoria"] for item in res_exist.json() if "id_auditoria" in item}
                    for r in registros:
                        if r["codigo_insumo"] in existentes:
                            r["id_auditoria"] = existentes[r["codigo_insumo"]]
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en upsert_conteos_iniciales: el servidor no responde")
        except Exception as e:
            print(f"Error al buscar existentes para upsert: {e}")
        
        url = f"{self.url}/registro_auditorias_cierres"
        
        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        
        try:
            res = self.session.post(url, json=registros, headers=headers, timeout=10)
            if res.status_code in (200, 201, 204):
                return True
            print(f"Error upsert_conteos: {res.text}")
            return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en upsert_conteos_iniciales: el servidor no responde")
        except Exception as e:
            print(f"Excepcion upsert_conteos: {e}")
            return False


    def get_top_costo_inventario(self, limit=10, fecha_corte=None) -> list:
        """
        Obtiene los insumos con mayor costo total de inventario acumulado hasta 'fecha_corte'.
        """
        try:
            insumos, _ = self.get_insumos(
                page=1, 
                page_size=limit, 
                fecha_corte=fecha_corte, 
                sort_col="Stock Real", 
                sort_asc=False
            )
            top = []
            for item in insumos:
                costo_tot = float(item.get("costo_total_insumo") or 0)
                ventas_tot = float(item.get("valor_ventas") or 0)
                rotacion = (ventas_tot / costo_tot) if costo_tot > 0 else 0.0
                
                top.append({
                    "codigo": item.get("codigo_insumo") or "S/C",
                    "producto": item.get("nombre") or "Desconocido",
                    "valor_inventario": costo_tot,
                    "rotacion": f"{rotacion:.2f}x"
                })
            return top
        except Exception as e:
            print(f"Error en get_top_costo_inventario: {e}")
            return []
        

    def get_compras_summary(self, fecha_corte=None):
        """
        Obtiene el resumen financiero acumulado de compras (total e IVA)
        para el mes en curso y para el día actual.
        """
        try:
            import datetime
            hoy = datetime.date.today().strftime("%Y-%m-%d")
            mes_actual = hoy[:7]
            
            url = f"{self.url}/registro_compras?select=fecha,cantidad,costo_total,iva,valor_iva,estado_registro&estado_registro=eq.VÁLIDO"
            res = self.session.get(url, headers=self.headers, timeout=10)
            
            if res.status_code == 200:
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
                    
                    # Extracción segura de IVA blindando valores None/NULL
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
            print(f"Error en get_compras_summary: {ex}")
            return {"total_mes": 0, "total_hoy": 0, "cantidad_total": 0, "iva_mes": 0, "iva_hoy": 0}

    def get_ventas_summary(self, fecha_corte=None):
        try:
            import datetime
            hoy = datetime.date.today().strftime("%Y-%m-%d")
            mes_actual = hoy[:7]
            
            url = f"{self.url}/registro_ventas?select=fecha,total,subtotal,iva,estado_registro&estado_registro=eq.VÁLIDO"
            res = self.session.get(url, headers=self.headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                tot_hist = 0.0
                tot_mes = 0.0
                tot_hoy = 0.0
                iva_hist = 0.0
                iva_mes = 0.0
                iva_hoy = 0.0
                
                for v in data:
                    f = str(v.get("fecha") or "")[:10]
                    if fecha_corte and f > fecha_corte:
                        continue
                        
                    monto = float(v.get("total") or 0)
                    iva_val = float(v.get("iva") or 0)
                    
                    tot_hist += monto
                    iva_hist += iva_val
                    
                    if f.startswith(mes_actual):
                        tot_mes += monto
                        iva_mes += iva_val
                        
                    if f == hoy:
                        tot_hoy += monto
                        iva_hoy += iva_val
                        
                return {
                    "total_historico": tot_hist,
                    "total_mes": tot_mes,
                    "total_hoy": tot_hoy,
                    "iva_historico": iva_hist,
                    "iva_mes": iva_mes,
                    "iva_hoy": iva_hoy
                }
            return {"total_historico": 0, "total_mes": 0, "total_hoy": 0, "iva_historico": 0, "iva_mes": 0, "iva_hoy": 0}
        except Exception as ex:
            print(f"Error en get_ventas_summary: {ex}")
            return {"total_historico": 0, "total_mes": 0, "total_hoy": 0, "iva_historico": 0, "iva_mes": 0, "iva_hoy": 0}

    def get_catalogo_summary(self, fecha_corte=None) -> dict:
        """Invoca RPC para compras totales y ventas totales en pesos"""
        url = f"{self.url}/rpc/get_catalogo_summary_rpc"
        try:
            payload = {}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload if payload else None, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_catalogo_summary: el servidor no responde")
        except Exception as e:
            print(f"Error RPC catalogo_summary: {e}")
        return {"total_compras": 0.0, "total_ventas": 0.0}

    def get_top_ventas_mes(self, limit=10, fecha_corte=None) -> list:
        hoy = fecha_corte if fecha_corte else datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        url = f"{self.url}/rpc/get_top_ventas_mes_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual, "limite": limit, "fecha_corte": fecha_corte} if fecha_corte else {"mes_actual": mes_actual, "limite": limit}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_top_ventas_mes: el servidor no responde")
        except Exception as e:
            print(f"Error RPC top_ventas: {e}")
        return []

    def get_tendencia_diaria(self, fecha_corte=None) -> dict:
        """Invoca RPC para obtener ventas y compras agrupadas por día"""
        if fecha_corte:
            hoy = datetime.datetime.strptime(fecha_corte, "%Y-%m-%d").date()
        else:
            hoy = datetime.date.today()
        mes_actual = hoy.strftime("%Y-%m")
        
        # Pre-poblar el diccionario con ceros para todos los días transcurridos
        tendencia = {f"{mes_actual}-{i:02d}": {"ventas": 0.0, "compras": 0.0} for i in range(1, hoy.day + 1)}
        
        url = f"{self.url}/rpc/get_tendencia_diaria_rpc"
        try:
            payload = {"mes_actual": mes_actual}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if res.status_code == 200:
                for row in res.json():
                    dia = row.get("dia")
                    if dia in tendencia:
                        tendencia[dia]["ventas"] = float(row.get("ventas", 0))
                        tendencia[dia]["compras"] = float(row.get("compras", 0))
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_tendencia_diaria: el servidor no responde")
        except Exception as e:
            print(f"Error RPC tendencia_diaria: {e}")
        return tendencia

    def get_inventario_kpis(self, fecha_corte=None) -> dict:
        """
        Obtiene los KPIs generales de valorización de inventario.
        """
        try:
            insumos, _ = self.get_insumos(page=1, page_size=99999, fecha_corte=fecha_corte)
            val_inv = sum([float(i.get("costo_total_insumo") or 0) for i in insumos])
            alertas = sum([1 for i in insumos if float(i.get("stock_actual") or i.get("stock_real") or 0) <= float(i.get("stock_minimo") or 5)])
            
            return {
                "valor_inventario": val_inv,
                "alertas_criticas": alertas
            }
        except Exception as e:
            print(f"Excepción controlada en get_inventario_kpis: {e}")
            return {"valor_inventario": 0, "alertas_criticas": 0}

    def get_kpis_por_categoria(self, fecha_corte=None) -> list:
        """Invoca RPC para extraer rendimiento y rotación agrupada por categoría."""
        url = f"{self.url}/rpc/get_kpis_por_categoria_rpc"
        try:
            payload = {}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload if payload else None, headers=self.headers, timeout=5)
            if res.status_code == 200:
                return res.json()
        except:
            pass
            
        # Fallback local para agrupar KPIs por categoría desde la vista principal
        try:
            url_vista = f"{self.url}/vista_inventario_completo?select=categoria,costo_total_insumo,valor_ventas"
            res_vista = self.session.get(url_vista, headers=self.headers, timeout=10)
            if res_vista.status_code == 200:
                data = res_vista.json()
                categorias = {}
                for item in data:
                    cat = item.get("categoria") or "SIN CATEGORIA"
                    if cat not in categorias:
                        categorias[cat] = {
                            "categoria": cat,
                            "costo_inventario": 0.0,
                            "ventas_totales": 0.0,
                            "rotacion": 0.0,
                            "rentabilidad": 0.0
                        }
                    categorias[cat]["costo_inventario"] += float(item.get("costo_total_insumo") or 0)
                    categorias[cat]["ventas_totales"] += float(item.get("valor_ventas") or 0)
                
                result = []
                for cat, vals in categorias.items():
                    costo_inv = vals["costo_inventario"]
                    vtas = vals["ventas_totales"]
                    if costo_inv > 0:
                        vals["rotacion"] = vtas / costo_inv
                    if vtas > 0:
                        vals["rentabilidad"] = 25.0 # Margen simulado 25% si hay ventas
                    result.append(vals)
                    
                result.sort(key=lambda x: x["ventas_totales"], reverse=True)
                return result
        except Exception as e:
            print(f"Error en get_kpis_por_categoria fallback: {e}")
            
        return []

    def iniciar_snapshot_cierre(self, mes_periodo: str) -> dict:
        """Invoca el RPC para generar el snapshot preliminar del mes."""
        url = f"{self.url}/rpc/fn_snapshot_cierre_mensual"
        try:
            res = self.session.post(url, json={"p_mes": mes_periodo}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en iniciar_snapshot_cierre: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def obtener_estado_cierre(self, mes_periodo: str) -> dict:
        """Obtiene el resumen y los insumos del período especificado."""
        url = f"{self.url}/rpc/fn_obtener_estado_cierre"
        try:
            res = self.session.post(url, json={"p_mes": mes_periodo}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else {}
            return {}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en obtener_estado_cierre: el servidor no responde")
        except Exception as e:
            print(f"Error en obtener_estado_cierre: {e}")
            return {}

    def registrar_conteo_fisico(self, id_auditoria: str, cantidad: float, costo: float = None, observacion: str = None) -> dict:
        """Registra el conteo físico y genera ajustes si existe diferencia."""
        url = f"{self.url}/rpc/fn_registrar_conteo_fisico"
        payload = {
            "p_id_auditoria": id_auditoria,
            "p_cantidad_fisica": cantidad
        }
        if costo is not None:
            payload["p_costo_ajuste"] = costo
        if observacion:
            payload["p_observacion"] = observacion
            
        try:
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en registrar_conteo_fisico: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aceptar_stock_sistema(self, id_auditoria: str) -> dict:
        """Acepta el stock calculado por el sistema sin conteo físico."""
        url = f"{self.url}/rpc/fn_aceptar_stock_sistema"
        try:
            res = self.session.post(url, json={"p_id_auditoria": id_auditoria}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en aceptar_stock_sistema: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aprobar_cierre_mes(self, id_periodo: str, aprobado_por: str) -> dict:
        """Cierra el período y consolida el inventario inicial del mes siguiente."""
        url = f"{self.url}/rpc/fn_aprobar_cierre_mes"
        try:
            res = self.session.post(url, json={"p_id_periodo": id_periodo, "p_aprobado_por": aprobado_por}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en aprobar_cierre_mes: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def get_catalogo_costos(self) -> dict:
        """Obtiene un diccionario con los costos actuales del catálogo de insumos"""
        url = f"{self.url}/catalogo_insumos?select=codigo_insumo,costo_unitario"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return {item.get('codigo_insumo'): float(item.get('costo_unitario') or 0) for item in res.json()}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_catalogo_costos: el servidor no responde")
        except Exception as e:
            print(f"Error get_catalogo_costos: {e}")
        return {}

    def get_insumo_detalle(self, codigo: str) -> dict:
        """Recupera el nombre, costo, precio y stock de un insumo específico para el autocompletado."""
        url = f"{self.url}/catalogo_insumos?codigo_insumo=eq.{codigo}&select=nombre,costo_unitario,precio_venta,stock_actual"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200 and len(res.json()) > 0:
                return res.json()[0]
        except Exception:
            pass
        return {}

    def get_ajustes_inventario(self) -> list:
        """Obtiene el historial de ajustes cruzado con el catálogo para extraer el nombre."""
        url = f"{self.url}/registro_ajustes_inventario?select=*,catalogo_insumos(nombre,categoria)&order=fecha_ajuste.desc"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_ajustes_inventario: el servidor no responde")
        except Exception as e:
            pass

    def get_historial_facturas_dia(self, fecha_dia: str) -> list:
        """
        Recupera todas las facturas y documentos cargados en un día específico (YYYY-MM-DD),
        agrupados por número de factura/entrada con su hora de registro y valor total.
        """
        facturas = []
        try:
            # 1. Compras del día
            url_c = f"{self.url}/registro_compras?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=numero_entrada,numero_factura,proveedor,costo_total,fecha&order=fecha.desc"
            res_c = self.session.get(url_c, headers=self.headers, timeout=10)
            if res_c.status_code == 200:
                agrupado_c = {}
                for r in res_c.json():
                    ref = r.get("numero_entrada") or r.get("numero_factura")
                    if not ref: continue
                    if ref not in agrupado_c:
                        agrupado_c[ref] = {
                            "tipo": "COMPRA",
                            "ref": ref,
                            "factura": r.get("numero_factura", "N/A"),
                            "proveedor": r.get("proveedor") or "Clientes Varios",
                            "total": 0.0,
                            "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                        }
                    agrupado_c[ref]["total"] += float(r.get("costo_total") or 0)
                facturas.extend(list(agrupado_c.values()))

            # 2. Ventas del día (Diferenciando POS y Remisión)
            url_v = f"{self.url}/registro_ventas?fecha=gte.{fecha_dia}T00:00:00&fecha=lte.{fecha_dia}T23:59:59&select=factura_no,tipo_documento,total,fecha&order=fecha.desc"
            res_v = self.session.get(url_v, headers=self.headers, timeout=10)
            if res_v.status_code == 200:
                agrupado_v = {}
                for r in res_v.json():
                    ref = r.get("factura_no")
                    if not ref: continue
                    if ref not in agrupado_v:
                        tipo_doc = r.get("tipo_documento") or "Factura POS"
                        agrupado_v[ref] = {
                            "tipo": f"VENTA_{'POS' if 'POS' in tipo_doc.upper() else 'REVISION'}",
                            "ref": ref,
                            "factura": ref,
                            "subtipo": tipo_doc,
                            "total": 0.0,
                            "hora": r.get("fecha", "") if len(r.get("fecha", "")) >= 16 else "12:00"
                        }
                    agrupado_v[ref]["total"] += float(r.get("total") or 0)
                facturas.extend(list(agrupado_v.values()))

            # 3. Ajustes del día
            url_a = f"{self.url}/registro_ajustes_inventario?fecha_ajuste=gte.{fecha_dia}T00:00:00&fecha_ajuste=lte.{fecha_dia}T23:59:59&select=id_ajuste,tipo_ajuste,motivo_observacion,costo_total_ajuste,fecha_ajuste&order=fecha_ajuste.desc"
            res_a = self.session.get(url_a, headers=self.headers, timeout=10)
            if res_a.status_code == 200:
                for r in res_a.json():
                    es_entrada = r.get("tipo_ajuste") in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
                    facturas.append({
                        "tipo": "AJUSTE_ENTRADA" if es_entrada else "AJUSTE_SALIDA",
                        "ref": r.get("id_ajuste"),
                        "factura": r.get("motivo_observacion") or "Ajuste Directo",
                        "total": float(r.get("costo_total_ajuste") or 0),
                        "hora": r.get("fecha_ajuste", "") if len(r.get("fecha_ajuste", "")) >= 16 else "12:00"
                    })

        except Exception as ex:
            print(f"Error cargando historial del día: {ex}")

        # Ordenar por hora descendente (más reciente arriba)
        facturas.sort(key=lambda x: x["hora"], reverse=True)
        return facturas

    def get_codigos_factura_especifica(self, tipo: str, ref: str) -> list:
        try:
            if tipo == "COMPRA":
                res = self.session.get(f"{self.url}/registro_compras?numero_entrada=eq.{ref}&select=codigo_insumo", headers=self.headers, timeout=5)
            elif tipo.startswith("VENTA"):
                res = self.session.get(f"{self.url}/registro_ventas?factura_no=eq.{ref}&select=codigo_insumo", headers=self.headers, timeout=5)
            else:
                res = self.session.get(f"{self.url}/registro_ajustes_inventario?id_ajuste=eq.{ref}&select=codigo_insumo", headers=self.headers, timeout=5)
            
            if res.status_code == 200:
                return list(set([r.get("codigo_insumo") for r in res.json() if r.get("codigo_insumo")]))
        except: pass
        return []
        return []

    def insert_ajuste_individual(self, datos: dict) -> bool:
        """Inserta un nuevo registro de ajuste operativo."""
        url = f"{self.url}/registro_ajustes_inventario"
        try:
            res = self.session.post(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 201, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en insert_ajuste_individual: el servidor no responde")
        except Exception as e:
            return False

    def anular_ajuste(self, id_ajuste: str) -> bool:
        """Cambia el estado del ajuste a ANULADO. El trigger en la BD revertirá el inventario."""
        url = f"{self.url}/registro_ajustes_inventario?id_ajuste=eq.{id_ajuste}"
        try:
            res = self.session.patch(url, json={"estado_registro": "ANULADO"}, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en anular_ajuste: el servidor no responde")
        except Exception as e:
            return False

    def get_periodos_inventario(self) -> list:
        """Obtiene la lista de periodos de inventario ordenados descendentemente."""
        url = f"{self.url}/periodos_inventario?select=*&order=mes_periodo.desc"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return []
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_periodos_inventario: el servidor no responde")
            return []
        except Exception as e:
            return []

    def get_proyeccion_ventas(self, fecha_corte=None) -> float:
        """Invoca RPC get_proyeccion_ventas_rpc"""
        url = f"{self.url}/rpc/get_proyeccion_ventas_rpc"
        try:
            payload = {}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload if payload else None, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return float(data) if data is not None else 0.0
            return 0.0
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_proyeccion_ventas: el servidor no responde")
            return 0.0
        except Exception:
            return 0.0

    def get_ajustes_mes(self, mes_actual: str, fecha_corte=None) -> list:
        """Invoca RPC get_ajustes_mes_rpc"""
        url = f"{self.url}/rpc/get_ajustes_mes_rpc"
        try:
            payload = {"mes_actual": mes_actual}
            if fecha_corte:
                payload["fecha_corte"] = fecha_corte
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else []
            return []
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_ajustes_mes: el servidor no responde")
            return []
        except Exception:
            return []

    def aceptar_stock_sistema_masivo(self, ids_auditoria: list) -> dict:
        url = f"{self.url}/rpc/fn_aceptar_stock_sistema_masivo"
        try:
            res = self.session.post(url, json={"p_ids": ids_auditoria}, headers=self.headers, timeout=15)
            if res.status_code == 200: return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e: return {"exito": False, "error": str(e)}

    def eliminar_ajuste_cierre(self, id_auditoria: str) -> dict:
        url = f"{self.url}/rpc/fn_eliminar_ajuste_cierre"
        try:
            res = self.session.post(url, json={"p_id_auditoria": id_auditoria}, headers=self.headers, timeout=10)
            if res.status_code == 200: return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e: return {"exito": False, "error": str(e)}

    def get_rendimiento_categorias_periodo(self, fecha_inicio=None, fecha_fin=None) -> list:
        """
        Calcula el rendimiento y costo acumulado real por categoría hasta 'fecha_fin'
        usando la vista/RPC de inventario calculado.
        """
        categorias_map = {}
        try:
            # Obtener todos los insumos calculados hasta fecha_fin
            insumos, _ = self.get_insumos(page=1, page_size=99999, fecha_corte=fecha_fin)
            
            for item in insumos:
                cat_nombre = (item.get("categoria") or "SIN CATEGORÍA").strip().upper()
                
                # Stock real calculado por el servidor (vista o RPC)
                stock = float(item.get("stock_actual") or item.get("stock_real") or 0)
                costo_u = float(item.get("costo_unitario") or 0)
                precio_v = float(item.get("precio_venta") or 0)
                
                # Costo total calculado por la BD o fallback producto
                inv_costo_item = float(item.get("costo_total_insumo") or (stock * costo_u))
                proy_venta_item = stock * precio_v
                ventas_item = float(item.get("valor_ventas") or 0)
                cant_ventas = float(item.get("ventas") or 0)
                costo_vendido_item = cant_ventas * costo_u
    
                if cat_nombre not in categorias_map:
                    categorias_map[cat_nombre] = {
                        "categoria": cat_nombre,
                        "inventario_costo": 0.0,
                        "proyeccion_venta": 0.0,
                        "ventas_realizadas": 0.0,
                        "costo_vendido": 0.0
                    }
    
                categorias_map[cat_nombre]["inventario_costo"] += inv_costo_item
                categorias_map[cat_nombre]["proyeccion_venta"] += proy_venta_item
                categorias_map[cat_nombre]["ventas_realizadas"] += ventas_item
                categorias_map[cat_nombre]["costo_vendido"] += costo_vendido_item
    
        except Exception as ex:
            print(f"Error calculando rendimiento acumulado por categoría: {ex}")
    
        # Formatear lista final con indicadores matemáticos reales
        resultado = []
        for cat_nombre, d in categorias_map.items():
            inv_c = d["inventario_costo"]
            v_real = d["ventas_realizadas"]
            proy_v = d["proyeccion_venta"]
            c_vend = d["costo_vendido"]
    
            cumplimiento = (v_real / proy_v * 100) if proy_v > 0 else 0.0
            rotacion = (v_real / inv_c) if inv_c > 0 else 0.0
            rendimiento = ((v_real - c_vend) / v_real * 100) if v_real > 0 else (100.0 if v_real == 0 else 0.0)
    
            resultado.append({
                "categoria": cat_nombre,
                "inventario_costo": inv_c,
                "ventas_realizadas": v_real,
                "proyeccion_venta": proy_v,
                "cumplimiento_pct": cumplimiento,
                "rotacion": rotacion,
                "rendimiento_pct": rendimiento
            })
    
        # Ordenar por costo de inventario descendente
        resultado.sort(key=lambda x: (x["inventario_costo"], x["ventas_realizadas"]), reverse=True)
        return resultado
