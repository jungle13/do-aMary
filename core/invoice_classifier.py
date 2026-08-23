"""
Módulo clasificador, extractor inteligente y organizador de facturas PDF.
Identifica y extrae 3 formatos:
  1. Venta POS (TIPO PP - Relación de Ventas Diarias)
  2. Venta Remisión (TIPO FV - Reporte Detallado de Facturas)
  3. Compra (EA - Reporte Detallado de Entradas de Almacén)

Incluye deduplicación automática y archivo por fecha.
"""
import os
import re
import shutil
import datetime
import json
import requests
from config import Config
from core.logger import get_logger, log_error
from core.supabase_client import get_client

logger = get_logger("InvoiceClassifier")

def parse_num(s):
    if not s or s == '-': return 0.0
    s = str(s).strip().replace('$', '')
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            s = parts[0].replace('.', '') + '.' + parts[1]
        else:
            s = s.replace(',', '')
    elif '.' in s:
        parts = s.split('.')
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            s = s
        else:
            s = s.replace('.', '')
    try:
        return float(s)
    except:
        return 0.0

def parse_fecha(f_str):
    if not f_str: return datetime.date.today().strftime("%Y-%m-%d")
    f_str = f_str.strip().replace('-', '/')
    parts = f_str.split('/')
    if len(parts) == 3:
        if len(parts[2]) == 4:
            return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        elif len(parts[0]) == 4:
            return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
    return f_str

def detectar_tipo_documento(texto: str) -> str:
    """
    Analiza el texto de un PDF para clasificar su formato exacto.
    Retorna: 'VENTA_POS' | 'VENTA_REMISION' | 'COMPRA' | 'DESCONOCIDO'
    """
    t = texto.upper()
    if "ENTRADAS DE ALMACEN" in t or "EA -" in t or "EA-" in t or "BODEGA" in t and "COSTO" in t:
        return "COMPRA"
    elif "RELACION DE VENTAS DIARIAS" in t or "TIPO PP" in t or "VENTAS DEL DIA" in t or "INVERIONES B&G" in t:
        return "VENTA_POS"
    elif "REPORTE DETALLADO DE FACTURAS" in t or "TIPO FV" in t or "DOÑA MARY" in t:
        return "VENTA_REMISION"
    return "DESCONOCIDO"

def obtener_documentos_registrados(db, tipo: str, fecha: str | None = None) -> set:
    """
    Obtiene los números de factura o entrada ya existentes en la BD.
    """
    registrados = set()
    try:
        if tipo in ("VENTA_POS", "VENTA_REMISION"):
            endpoint = "registro_ventas?select=factura_no"
            if fecha:
                endpoint += f"&fecha=gte.{fecha}T00:00:00&fecha=lte.{fecha}T23:59:59"
            res = db._db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                for item in res.json():
                    if item.get("factura_no"):
                        registrados.add(str(item["factura_no"]).strip())
        elif tipo == "COMPRA":
            endpoint = "registro_compras?select=numero_entrada,numero_factura"
            if fecha:
                endpoint += f"&fecha=gte.{fecha}T00:00:00&fecha=lte.{fecha}T23:59:59"
            res = db._db.get(endpoint, timeout=10)
            if res and res.status_code == 200:
                for item in res.json():
                    if item.get("numero_entrada"):
                        registrados.add(str(item["numero_entrada"]).strip())
                    if item.get("numero_factura"):
                        registrados.add(str(item["numero_factura"]).strip())
    except Exception as ex:
        log_error("obtener_documentos_registrados", ex)
    return registrados

def parsear_venta_pos(lineas: list[str], docs_existentes: set) -> tuple[dict, int, int]:
    """
    Parsea formato VENTA POS (TIPO PP).
    Retorna: (datos_extraidos, facturas_nuevas, facturas_omitidas)
    """
    invoices = []
    curr_factura = None
    curr_fecha = None
    curr_cliente = "Clientes Varios"
    facturas_omitidas = 0
    facturas_procesadas = set()
    
    # Buscar fecha general
    for l in lineas[:15]:
        m_f = re.search(r'(\d{2}/\d{2}/\d{4})', l)
        if m_f:
            curr_fecha = parse_fecha(m_f.group(1))
            break
    if not curr_fecha:
        curr_fecha = datetime.date.today().strftime("%Y-%m-%d")

    curr_invoice_data = None

    for l in lineas:
        line = l.strip()
        if not line: continue
        if line.startswith("TOTAL DIA") or line.startswith("RELACION") or line.startswith("INVERIONES"):
            continue

        # Detectar inicio de documento: PP 26396 Clientes Varios
        m_pp = re.search(r'PP\s+(\d+)\s*(.*)', line)
        if m_pp:
            if curr_invoice_data and curr_invoice_data["productos"]:
                invoices.append(curr_invoice_data)
                curr_invoice_data = None

            fact_num = m_pp.group(1).strip()
            facturas_procesadas.add(fact_num)

            # Verificar deduplicación
            if fact_num in docs_existentes:
                facturas_omitidas += 1
                curr_factura = None
                continue

            curr_factura = fact_num
            cli = m_pp.group(2).strip() or "Clientes Varios"
            curr_invoice_data = {
                "factura": curr_factura,
                "fecha": curr_fecha,
                "cliente": cli,
                "tipo_doc": "Factura POS",
                "productos": []
            }
            continue

        # Si estamos dentro de una factura nueva válida, extraer items
        if curr_invoice_data and curr_factura:
            parts = line.split()
            if len(parts) >= 2:
                cod_token = parts[0]
                if (cod_token.isdigit() and len(cod_token) in (3, 4)) or ('-' in cod_token and len(cod_token) <= 7):
                    cod = cod_token.zfill(4) if cod_token.isdigit() else cod_token
                    nums = [p for p in parts[1:] if any(c.isdigit() for c in p)]
                    if len(nums) >= 2:
                        cant = parse_num(nums[0])
                        p_unit = parse_num(nums[1])
                        tot = cant * p_unit if len(nums) == 2 else parse_num(nums[-1])
                        curr_invoice_data["productos"].append({
                            "codigo_item": cod,
                            "descripcion": f"INSUMO {cod}",
                            "cantidad": cant,
                            "subtotal": tot,
                            "iva": 0.0,
                            "total": tot
                        })

    if curr_invoice_data and curr_invoice_data["productos"]:
        invoices.append(curr_invoice_data)

    return {
        "tipo": "VENTAS_POS",
        "fecha": curr_fecha,
        "invoices": invoices
    }, len(invoices), facturas_omitidas

def parsear_venta_remision(lineas: list[str], docs_existentes: set) -> tuple[dict, int, int]:
    """
    Parsea formato VENTA REMISIÓN (TIPO FV).
    """
    invoices = []
    curr_factura = None
    curr_fecha = None
    curr_cliente = None
    curr_page = 1
    facturas_omitidas = 0
    curr_invoice_data = None

    for l in lineas:
        line = l.strip()
        if not line: continue
        if line.startswith("page "):
            p_m = re.search(r'page\s+(\d+)', line)
            if p_m: curr_page = int(p_m.group(1))
            continue

        if line.startswith("Fact.No."):
            if curr_invoice_data and curr_invoice_data["productos"]:
                invoices.append(curr_invoice_data)
                curr_invoice_data = None

            m_fact = re.search(r'Fact\.No\.\s*([^\s]+)', line)
            m_fec = re.search(r'Fecha:\s*(\d{2}/\d{2}/\d{4})', line)
            m_cli = re.search(r'Cliente:\s*(.*)', line)

            fact_num = m_fact.group(1).strip() if m_fact else "S/N"
            fec_str = parse_fecha(m_fec.group(1)) if m_fec else datetime.date.today().strftime("%Y-%m-%d")
            cli_str = m_cli.group(1).strip() if m_cli else "Clientes Varios"

            if fact_num in docs_existentes:
                facturas_omitidas += 1
                curr_factura = None
                continue

            curr_factura = fact_num
            curr_fecha = fec_str
            curr_cliente = cli_str
            curr_invoice_data = {
                "factura": curr_factura,
                "fecha": curr_fecha,
                "cliente": curr_cliente,
                "tipo_doc": "Remisión",
                "pagina_origen": curr_page,
                "productos": []
            }
            continue

        if curr_invoice_data and curr_factura:
            if line.startswith("Total Factura:") or line.startswith("Total Tipo:") or line.startswith("TOTAL"):
                continue

            parts = line.split()
            if len(parts) >= 4:
                cod_token = parts[0]
                if (cod_token.isdigit() and len(cod_token) in (3, 4)) or ('-' in cod_token and len(cod_token) <= 7):
                    cod = cod_token.zfill(4) if cod_token.isdigit() else cod_token
                    nums = []
                    words = []
                    for token in reversed(parts[1:]):
                        cleaned = token.replace('.', '').replace(',', '')
                        if cleaned.isdigit() and len(nums) < 4:
                            nums.insert(0, token)
                        else:
                            words.insert(0, token)

                    desc = ' '.join(words)
                    if len(nums) >= 2:
                        cant = parse_num(nums[0])
                        subt = parse_num(nums[1])
                        iva = parse_num(nums[2]) if len(nums) >= 3 else 0.0
                        tot = parse_num(nums[3]) if len(nums) == 4 else subt + iva
                        curr_invoice_data["productos"].append({
                            "codigo_item": cod,
                            "descripcion": desc,
                            "cantidad": cant,
                            "subtotal": subt,
                            "iva": iva,
                            "total": tot
                        })

    if curr_invoice_data and curr_invoice_data["productos"]:
        invoices.append(curr_invoice_data)

    return {
        "tipo": "VENTAS_REMISION",
        "fecha": curr_fecha or datetime.date.today().strftime("%Y-%m-%d"),
        "invoices": invoices
    }, len(invoices), facturas_omitidas

def parsear_compras(lineas: list[str], docs_existentes: set) -> tuple[dict, int, int]:
    """
    Parsea formato COMPRAS (EA - Entradas de Almacén).
    """
    invoices = []
    curr_ea = None
    curr_factura = None
    curr_fecha = None
    curr_prov = None
    facturas_omitidas = 0
    curr_invoice_data = None

    for l in lineas:
        line = l.strip()
        if not line: continue
        if line.startswith("EA -") or line.startswith("EA-"):
            if curr_invoice_data and curr_invoice_data["productos"]:
                invoices.append(curr_invoice_data)
                curr_invoice_data = None

            m_ea = re.search(r'EA\s*-\s*(\d+)', line)
            m_fec = re.search(r'(\d{2}/\d{2}/\d{4})', line)
            m_fac = re.search(r'Factura\s*No\.?\s*([^\s]+)', line, re.IGNORECASE)
            m_prov = re.search(r'Factura\s*No\.?[^\s]+\s+(.*)', line, re.IGNORECASE)

            ea_num = f"EA - {m_ea.group(1)}" if m_ea else "EA - S/N"
            fac_num = m_fac.group(1).strip() if m_fac else "S/N"
            fec_str = parse_fecha(m_fec.group(1)) if m_fec else datetime.date.today().strftime("%Y-%m-%d")
            prov_str = m_prov.group(1).strip() if m_prov else "Proveedor Varios"

            if ea_num in docs_existentes or fac_num in docs_existentes:
                facturas_omitidas += 1
                curr_ea = None
                continue

            curr_ea = ea_num
            curr_factura = fac_num
            curr_fecha = fec_str
            curr_prov = prov_str
            curr_invoice_data = {
                "numero_entrada": curr_ea,
                "numero_factura": curr_factura,
                "fecha": curr_fecha,
                "proveedor": curr_prov,
                "bodega": "1",
                "productos": []
            }
            continue

        if curr_invoice_data and curr_ea:
            if line.startswith("Totales de Entrada:") or line.startswith("TOTAL:") or line.startswith("Nota:"):
                continue

            parts = line.split()
            if len(parts) >= 4:
                cod_token = parts[0]
                if (cod_token.isdigit() and len(cod_token) in (3, 4)) or ('-' in cod_token and len(cod_token) <= 7):
                    cod = cod_token.zfill(4) if cod_token.isdigit() else cod_token
                    nums = []
                    words = []
                    for token in reversed(parts[1:]):
                        cleaned = token.replace('.', '').replace(',', '')
                        if cleaned.isdigit() and len(nums) < 4:
                            nums.insert(0, token)
                        else:
                            words.insert(0, token)

                    desc = ' '.join(words)
                    if len(nums) >= 3:
                        cant = parse_num(nums[0])
                        costo = parse_num(nums[1])
                        iva = parse_num(nums[2]) if len(nums) == 4 else 0.0
                        tot = parse_num(nums[3]) if len(nums) == 4 else parse_num(nums[2])
                        curr_invoice_data["productos"].append({
                            "codigo_insumo": cod,
                            "descripcion": desc,
                            "cantidad": cant,
                            "costo_unitario": costo,
                            "iva": iva,
                            "costo_total": tot
                        })

    if curr_invoice_data and curr_invoice_data["productos"]:
        invoices.append(curr_invoice_data)

    return {
        "tipo": "COMPRAS",
        "fecha": curr_fecha or datetime.date.today().strftime("%Y-%m-%d"),
        "invoices": invoices
    }, len(invoices), facturas_omitidas

def organizar_y_reubicar_pdf(archivo_path: str, tipo_doc: str, fecha_doc: str) -> str:
    """
    Crea la carpeta con la fecha del documento, renombra el archivo y lo reubica.
    """
    dir_origen = os.path.dirname(os.path.abspath(archivo_path))
    carpeta_destino = os.path.join(dir_origen, fecha_doc)
    os.makedirs(carpeta_destino, exist_ok=True)

    prefijo = {
        "VENTA_POS": "VENTA_POS",
        "VENTAS_POS": "VENTA_POS",
        "VENTA_REMISION": "VENTA_REMISION",
        "VENTAS_REMISION": "VENTA_REMISION",
        "COMPRA": "COMPRA",
        "COMPRAS": "COMPRA"
    }.get(tipo_doc, "FACTURA")

    timestamp_sec = datetime.datetime.now().strftime("%H%M%S")
    nuevo_nombre = f"{prefijo}_{fecha_doc}_{timestamp_sec}.pdf"
    destino_final = os.path.join(carpeta_destino, nuevo_nombre)

    try:
        shutil.move(archivo_path, destino_final)
        logger.info(f"PDF reubicado exitosamente a: {destino_final}")
        return destino_final
    except Exception as ex:
        log_error("organizar_y_reubicar_pdf", ex)
        return archivo_path

def guardar_lote_en_staging(carga_data: dict) -> bool:
    """
    Registra el lote extraído en cargas_locales.json con estado EXTRAIDO_POR_AGENTE
    respetando la estructura de grupos y páginas para la interfaz Flet.
    """
    cargas_file = "cargas_locales.json"
    try:
        if os.path.exists(cargas_file):
            with open(cargas_file, "r", encoding="utf-8") as f:
                cargas = json.load(f)
        else:
            cargas = {}

        # Calcular max_id existente
        max_id = 0
        for g_k, pags in cargas.items():
            if isinstance(pags, dict):
                for num_p, d in pags.items():
                    if isinstance(d, dict) and "id" in d:
                        try: max_id = max(max_id, int(d["id"]))
                        except: pass
            elif isinstance(pags, dict) and "id" in pags:
                try: max_id = max(max_id, int(pags["id"]))
                except: pass

        nuevo_id = max_id + 1
        tipo_raw = str(carga_data.get("tipo", "VENTAS_REMISION")).upper()
        if "POS" in tipo_raw:
            tipo_ui = "Factura POS"
        elif "COMPRA" in tipo_raw:
            tipo_ui = "Compra"
        else:
            tipo_ui = "Remisión"

        fecha = carga_data.get("fecha", datetime.date.today().strftime("%Y-%m-%d"))
        grupo_key = f"{fecha}_{tipo_ui}"
        if grupo_key not in cargas:
            cargas[grupo_key] = {}

        num_pag = str(len(cargas[grupo_key]) + 1)
        invoices = carga_data.get("invoices", [])

        cargas[grupo_key][num_pag] = {
            "id": nuevo_id,
            "pagina": int(num_pag),
            "tipo": tipo_ui,
            "fecha": fecha,
            "estado": "EXTRAIDO_POR_AGENTE",
            "archivo": carga_data.get("archivo_origen", ""),
            "total_facturas": len(invoices),
            "datos_extraidos": invoices,
            "created_at": datetime.datetime.now().isoformat()
        }

        with open(cargas_file, "w", encoding="utf-8") as f:
            json.dump(cargas, f, indent=4, ensure_ascii=False)

        logger.info(f"Carga {nuevo_id} ({tipo_ui}) guardada exitosamente en Staging: {cargas_file}")
        return True
    except Exception as ex:
        log_error("guardar_lote_en_staging", ex)
        return False

