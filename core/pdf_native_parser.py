"""
core/pdf_native_parser.py
Motor de extraccion determinista y de alto rendimiento en Python puro (pypdf en modo layout)
para los reportes contables PDF de Dona Mary:
  1. Compras / Entradas de Almacen (EA / ES)
  2. Ventas POS Detalladas (Facturas FV)
  3. Ventas Diarias / Remisiones (Tipo PP)
"""
import io
import re
import pypdf
from typing import Union, List, Dict, Any, Optional

SPECIAL_3DIGIT_CODES = {'964', '965', '966', '967', '968', '969', '970', '971', '972', '973'}

def parse_colombian_number(val: Any) -> float:
    """Convierte un string numerico con formato colombiano a float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    s = str(val).strip().replace('$', '').replace(' ', '')
    if not s or s == '-' or s.lower() == 'nan':
        return 0.0
    
    if '.' in s and ',' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = parts[0] + '.' + parts[1]
        else:
            s = s.replace(',', '')
    elif '.' in s:
        parts = s.split('.')
        if len(parts) == 2 and len(parts[1]) == 2 and float(parts[0] or 0) < 1000:
            s = parts[0] + '.' + parts[1]
        else:
            s = s.replace('.', '')
            
    try:
        return float(s)
    except Exception:
        return 0.0

def clean_text(s: Any) -> str:
    """Limpia caracteres especiales, signos corruptos y espacios extra."""
    if not s or str(s).lower() == 'nan':
        return ''
    txt = str(s)
    txt = txt.replace(chr(0xa5), 'Ñ').replace('¥', 'Ñ')
    txt = ' '.join(txt.split()).strip()
    return txt

def format_codigo_insumo(raw_cod: str) -> str:
    """Aplica las reglas de 4 digitos y las excepciones de 3 digitos."""
    cod = clean_text(raw_cod)
    if '-' in cod:
        return cod
    if cod.isdigit():
        num = int(cod)
        cod_str = str(num)
        if cod_str in SPECIAL_3DIGIT_CODES:
            return cod_str
        return cod_str.zfill(4)
    return cod

def get_pdf_reader(pdf_source: Union[str, bytes, io.BytesIO]) -> pypdf.PdfReader:
    if isinstance(pdf_source, (bytes, bytearray)):
        return pypdf.PdfReader(io.BytesIO(pdf_source))
    elif isinstance(pdf_source, io.BytesIO):
        return pypdf.PdfReader(pdf_source)
    else:
        return pypdf.PdfReader(pdf_source)


# ==============================================================================
# 1. PARSER DE VENTAS POS DETALLADAS (Reporte Detallado de Facturas FV)
# ==============================================================================
def parse_ventas_pos_detallado(pdf_source: Union[str, bytes, io.BytesIO]) -> Dict[str, Any]:
    reader = get_pdf_reader(pdf_source)
    total_pages = len(reader.pages)
    facturas_dict: Dict[str, Dict[str, Any]] = {}
    facturas_order: List[str] = []
    current_fact_num: Optional[str] = None
    
    rango_desde = ''
    rango_hasta = ''
    total_reporte_pie = 0.0
    
    for p_idx, page in enumerate(reader.pages):
        page_num = p_idx + 1
        text = page.extract_text(extraction_mode='layout')
        lines = text.split('\n')
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            if not rango_desde:
                m_rango = re.search(r'Desde\s+Hasta\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})', line_str, re.IGNORECASE)
                if m_rango:
                    rango_desde = m_rango.group(1)
                    rango_hasta = m_rango.group(2)
                else:
                    m_fec = re.findall(r'(\d{2}/\d{2}/\d{4})', line_str)
                    if len(m_fec) >= 2:
                        rango_desde = m_fec[0]
                        rango_hasta = m_fec[1]

            m_fact = re.search(r'Fact\.No\.\s*([\w-]+)\s+Fecha:\s*(\d{2}/\d{2}/\d{4})\s+Cliente:\s*(.+)', line_str, re.IGNORECASE)
            if m_fact:
                num_fact = clean_text(m_fact.group(1))
                fecha_fact = m_fact.group(2).strip()
                cliente = clean_text(m_fact.group(3))
                
                parts_f = fecha_fact.split('/')
                fecha_iso = f"{parts_f[2]}-{parts_f[1]}-{parts_f[0]}" if len(parts_f) == 3 else fecha_fact
                
                if num_fact not in facturas_dict:
                    facturas_dict[num_fact] = {
                        'id_temporal': f"remi_{num_fact}_{fecha_iso}",
                        'factura_no': num_fact,
                        'fecha': fecha_iso,
                        'fecha_display': fecha_fact,
                        'cliente': cliente,
                        'tipo_documento': 'Remisión',
                        'pagina_origen': page_num,
                        'items': [],
                        'total_factura': 0.0,
                        'subtotal_factura': 0.0,
                        'iva_factura': 0.0
                    }
                    facturas_order.append(num_fact)
                current_fact_num = num_fact
                continue
                
            m_tot = re.search(r'Total Factura:\s*([\d.,]+)', line_str, re.IGNORECASE)
            if m_tot and current_fact_num:
                val_tot = parse_colombian_number(m_tot.group(1))
                facturas_dict[current_fact_num]['total_factura'] = val_tot
                continue
                
            m_pie = re.search(r'TOTAL\s+([\d.,]+)', line_str, re.IGNORECASE)
            if m_pie:
                total_reporte_pie = parse_colombian_number(m_pie.group(1))
                continue

            m_item = re.match(r'^(\d{3,5}(?:-\d+)?)\s+(.+?)\s+([\d.,]+)\s+([\d.,]+)(?:\s+([\d.,]+))?(?:\s+([\d.,]+))?$', line_str)
            if m_item and current_fact_num:
                raw_cod = m_item.group(1)
                cod_final = format_codigo_insumo(raw_cod)
                desc = clean_text(m_item.group(2))
                cant = parse_colombian_number(m_item.group(3))
                
                nums = [m_item.group(4), m_item.group(5), m_item.group(6)]
                valid_nums = [parse_colombian_number(x) for x in nums if x is not None]
                
                if len(valid_nums) == 1:
                    subtot_val = valid_nums[0]
                    iva_val = 0.0
                    tot_val = subtot_val
                elif len(valid_nums) == 2:
                    subtot_val = valid_nums[0]
                    iva_val = 0.0
                    tot_val = valid_nums[1]
                else:
                    subtot_val = valid_nums[0]
                    iva_val = valid_nums[1]
                    tot_val = valid_nums[2]
                    
                facturas_dict[current_fact_num]['items'].append({
                    'codigo_insumo': cod_final,
                    'descripcion': desc,
                    'cantidad': cant,
                    'subtotal': subtot_val,
                    'iva': iva_val,
                    'total': tot_val
                })
            elif current_fact_num and facturas_dict[current_fact_num]['items'] and not any(k in line_str for k in ['**', 'REPORTE', 'Desde', 'ITEM', 'TIPO', 'Total', 'Fecha:', 'Hora:', 'Pagina:']):
                if len(line_str) < 45 and not re.search(r'\d{3,}', line_str):
                    facturas_dict[current_fact_num]['items'][-1]['descripcion'] = clean_text(facturas_dict[current_fact_num]['items'][-1]['descripcion'] + ' ' + line_str)

    facturas = [facturas_dict[k] for k in facturas_order]
    for f in facturas:
        calc_subtot = sum(it.get('subtotal', 0.0) for it in f['items'])
        calc_iva = sum(it.get('iva', 0.0) for it in f['items'])
        calc_tot = sum(it.get('total', 0.0) for it in f['items'])
        f['subtotal_factura'] = calc_subtot
        f['iva_factura'] = calc_iva
        if f['total_factura'] == 0.0:
            f['total_factura'] = calc_tot

    total_calculado = sum(f['total_factura'] for f in facturas)
    
    return {
        'tipo_reporte': 'VENTAS_REMISIÓN',
        'rango_desde': rango_desde,
        'rango_hasta': rango_hasta,
        'total_paginas': total_pages,
        'total_facturas': len(facturas),
        'total_insumos': sum(len(f['items']) for f in facturas),
        'total_general': total_calculado,
        'total_reporte_pie': total_reporte_pie if total_reporte_pie > 0 else total_calculado,
        'facturas': facturas
    }


# ==============================================================================
# 2. PARSER DE VENTAS DIARIAS / REMISIONES (WXMANAGER - Tipo PP)
# ==============================================================================
def parse_ventas_remisiones_diarias(pdf_source: Union[str, bytes, io.BytesIO]) -> Dict[str, Any]:
    reader = get_pdf_reader(pdf_source)
    total_pages = len(reader.pages)
    facturas_dict: Dict[str, Dict[str, Any]] = {}
    facturas_order: List[str] = []
    current_rem_num: Optional[str] = None
    
    fecha_reporte = ''
    total_reporte_pie = 0.0
    
    for p_idx, page in enumerate(reader.pages):
        page_num = p_idx + 1
        text = page.extract_text(extraction_mode='layout')
        lines = text.split('\n')
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            if not fecha_reporte:
                m_fec = re.search(r'(\d{2}/\d{2}/\d{4})', line_str)
                if m_fec:
                    fecha_reporte = m_fec.group(1)

            m_pp = re.search(r'^(?:TIPO\s+NUMERO\s+)?(?:PP|PE|FE|POS)\s+(\d+)\s*(.*)$', line_str, re.IGNORECASE)
            if not m_pp:
                m_pp = re.search(r'\b(?:PP|PE)\s+(\d+)\s*(.*)$', line_str, re.IGNORECASE)

            if m_pp:
                num_rem = m_pp.group(1).strip()
                cliente_cand = clean_text(m_pp.group(2))
                cliente_rem = cliente_cand or 'CONSUMIDOR FINAL'
                
                parts_f = fecha_reporte.split('/') if fecha_reporte else []
                fecha_iso = f"{parts_f[2]}-{parts_f[1]}-{parts_f[0]}" if len(parts_f) == 3 else fecha_reporte
                
                if num_rem not in facturas_dict:
                    facturas_dict[num_rem] = {
                        'id_temporal': f"pos_{num_rem}_{fecha_iso}",
                        'factura_no': num_rem,
                        'fecha': fecha_iso,
                        'fecha_display': fecha_reporte,
                        'cliente': cliente_rem,
                        'tipo_documento': 'Factura POS',
                        'pagina_origen': page_num,
                        'items': [],
                        'total_factura': 0.0,
                        'subtotal_factura': 0.0,
                        'iva_factura': 0.0
                    }
                    facturas_order.append(num_rem)
                current_rem_num = num_rem
                continue
                
            m_tot = re.search(r'TOTAL:\s*([\d.,]+)', line_str, re.IGNORECASE)
            if m_tot and current_rem_num:
                val_tot = parse_colombian_number(m_tot.group(1))
                facturas_dict[current_rem_num]['total_factura'] = val_tot
                continue

            if current_rem_num and facturas_dict[current_rem_num]['cliente'] in ('', 'Clientes Varios', 'CONSUMIDOR FINAL'):
                if not re.search(r'^(?:COD:|TOTAL:|SUBTOTAL|TIPO\s+NUMERO|PP\s+\d+|PE\s+\d+|DES/NTO)', line_str, re.IGNORECASE) and not re.match(r'^\d{3,5}', line_str):
                    c_cand = clean_text(line_str)
                    if c_cand and len(c_cand) > 2 and not any(kw in c_cand.upper() for kw in ('VALOR', 'PRECIO', 'CANTIDAD', 'PAGINA', 'FECHA', 'DES/NTO')):
                        facturas_dict[current_rem_num]['cliente'] = c_cand
                
            m_subt = re.search(r'SUBTOTAL\s+([\d.,]+)', line_str, re.IGNORECASE)
            if m_subt:
                total_reporte_pie = parse_colombian_number(m_subt.group(1))
                continue

            m_cod = re.search(r'COD:\s*(\d{3,5}(?:-\d+)?)', line_str, re.IGNORECASE)
            if m_cod and current_rem_num:
                raw_cod = m_cod.group(1)
                cod_final = format_codigo_insumo(raw_cod)
                
                nums_match = re.findall(r'([\d]+(?:[.,]\d+)?)', line_str.replace(f"COD: {raw_cod}", "").replace(f"COD:{raw_cod}", ""))
                cant = 1.0
                tot = 0.0
                if len(nums_match) >= 2:
                    cant = parse_colombian_number(nums_match[0])
                    tot = parse_colombian_number(nums_match[1])
                elif len(nums_match) == 1:
                    tot = parse_colombian_number(nums_match[0])
                    
                facturas_dict[current_rem_num]['items'].append({
                    'codigo_insumo': cod_final,
                    'descripcion': '',
                    'cantidad': cant,
                    'subtotal': tot,
                    'iva': 0.0,
                    'total': tot
                })
                continue

            m_item_tab = re.match(r'^(\d{3,5}(?:-\d+)?)\s+(.+?)\s+([\d.,]+)\s+([\d.,]+)$', line_str)
            if m_item_tab and current_rem_num and not re.search(r'^(?:PP|PE|TOTAL|SUBTOTAL|DES/NTO|TIPO)', line_str, re.IGNORECASE):
                raw_cod = m_item_tab.group(1)
                cod_final = format_codigo_insumo(raw_cod)
                desc_item = clean_text(m_item_tab.group(2))
                cant = parse_colombian_number(m_item_tab.group(3))
                tot = parse_colombian_number(m_item_tab.group(4))
                facturas_dict[current_rem_num]['items'].append({
                    'codigo_insumo': cod_final,
                    'descripcion': desc_item,
                    'cantidad': cant,
                    'subtotal': tot,
                    'iva': 0.0,
                    'total': tot
                })
                continue
                
            if current_rem_num and facturas_dict[current_rem_num]['items'] and not facturas_dict[current_rem_num]['items'][-1]['descripcion']:
                if not any(k in line_str.upper() for k in ['TIPO', 'NUMERO', 'PP', 'PE', 'DES/NTO', 'TOTAL:', 'WXMANAGER', 'COD:']):
                    facturas_dict[current_rem_num]['items'][-1]['descripcion'] = clean_text(line_str)
                    
    facturas = [facturas_dict[k] for k in facturas_order]
    for f in facturas:
        calc_tot = sum(it.get('total', 0.0) for it in f['items'])
        f['subtotal_factura'] = calc_tot
        if f['total_factura'] == 0.0:
            f['total_factura'] = calc_tot

    total_calculado = sum(f['total_factura'] for f in facturas)
    
    return {
        'tipo_reporte': 'VENTAS_POS',
        'rango_desde': fecha_reporte,
        'rango_hasta': fecha_reporte,
        'total_paginas': total_pages,
        'total_facturas': len(facturas),
        'total_insumos': sum(len(f['items']) for f in facturas),
        'total_general': total_calculado,
        'total_reporte_pie': total_reporte_pie if total_reporte_pie > 0 else total_calculado,
        'facturas': facturas
    }


# ==============================================================================
# 3. PARSER DE COMPRAS / ENTRADAS DE ALMACÉN (Reporte Detallado de Entradas EA)
# ==============================================================================
def parse_compras_entradas(pdf_source: Union[str, bytes, io.BytesIO]) -> Dict[str, Any]:
    reader = get_pdf_reader(pdf_source)
    total_pages = len(reader.pages)
    entradas_dict: Dict[str, Dict[str, Any]] = {}
    entradas_order: List[str] = []
    current_entry_key: Optional[str] = None
    
    rango_desde = ''
    rango_hasta = ''
    total_reporte_pie = 0.0
    
    for p_idx, page in enumerate(reader.pages):
        page_num = p_idx + 1
        text = page.extract_text(extraction_mode='layout')
        lines = text.split('\n')
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            if not rango_desde:
                m_fec = re.findall(r'(\d{2}/\d{2}/\d{4})', line_str)
                if len(m_fec) >= 2:
                    rango_desde = m_fec[0]
                    rango_hasta = m_fec[1]

            # Detectar Cabecera de Entrada: EA - 9269 01/08/2026 Factura No.89832 DISDECOL SAS
            m_ea = re.search(r'^(E[AS]\s*-\s*\d+)\s+(\d{2}/\d{2}/\d{4})\s+(?:Factura\s*(?:No\.([\w-]+))?)?\s*(.+)?$', line_str, re.IGNORECASE)
            if m_ea:
                num_ea = clean_text(m_ea.group(1)).replace(' ', '')
                fecha_ea = m_ea.group(2).strip()
                fact_no = clean_text(m_ea.group(3)) if m_ea.group(3) else ''
                prov = clean_text(m_ea.group(4)) or 'Proveedor General'
                
                parts_f = fecha_ea.split('/')
                fecha_iso = f"{parts_f[2]}-{parts_f[1]}-{parts_f[0]}" if len(parts_f) == 3 else fecha_ea
                
                if num_ea not in entradas_dict:
                    entradas_dict[num_ea] = {
                        'id_temporal': f"compra_{num_ea}_{fact_no}_{fecha_iso}",
                        'numero_entrada': num_ea,
                        'numero_factura': fact_no or num_ea,
                        'fecha': fecha_iso,
                        'fecha_display': fecha_ea,
                        'proveedor': prov,
                        'pagina_origen': page_num,
                        'items': [],
                        'total_entrada': 0.0,
                        'iva_entrada': 0.0,
                        'subtotal_entrada': 0.0
                    }
                    entradas_order.append(num_ea)
                elif fact_no and not entradas_dict[num_ea]['numero_factura']:
                    entradas_dict[num_ea]['numero_factura'] = fact_no
                if prov and entradas_dict[num_ea]['proveedor'] == 'Proveedor General':
                    entradas_dict[num_ea]['proveedor'] = prov
                    
                current_entry_key = num_ea
                continue
                
            m_tot_ea = re.search(r'Totales de Entrada:\s*([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)', line_str, re.IGNORECASE)
            if m_tot_ea and current_entry_key:
                entradas_dict[current_entry_key]['subtotal_entrada'] = parse_colombian_number(m_tot_ea.group(2))
                entradas_dict[current_entry_key]['iva_entrada'] = parse_colombian_number(m_tot_ea.group(3))
                entradas_dict[current_entry_key]['total_entrada'] = parse_colombian_number(m_tot_ea.group(4))
                continue
                
            m_pie = re.search(r'TOTAL:\s*([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)', line_str, re.IGNORECASE)
            if m_pie:
                total_reporte_pie = parse_colombian_number(m_pie.group(3))
                continue

            m_item = re.match(r'^(\d{3,5}(?:-\d+)?)\s+(.+?)\s+(\d+)\s+([\d.,]+)\s+([\d.,]+)(?:\s+([\d.,]+))?\s+([\d.,]+)$', line_str)
            if m_item and current_entry_key:
                raw_cod = m_item.group(1)
                cod_final = format_codigo_insumo(raw_cod)
                desc = clean_text(m_item.group(2))
                bodega = m_item.group(3).strip()
                cant = parse_colombian_number(m_item.group(4))
                costo_u = parse_colombian_number(m_item.group(5))
                iva_val = parse_colombian_number(m_item.group(6)) if m_item.group(6) else 0.0
                tot_val = parse_colombian_number(m_item.group(7))
                
                entradas_dict[current_entry_key]['items'].append({
                    'codigo_insumo': cod_final,
                    'descripcion': desc,
                    'bodega': f"Bodega {bodega}",
                    'cantidad': cant,
                    'costo_unitario': costo_u,
                    'valor_iva': iva_val,
                    'costo_total': tot_val
                })
            elif current_entry_key and entradas_dict[current_entry_key]['items'] and not any(k in line_str for k in ['**', 'REPORTE', 'Desde', 'Item', 'Totales de Entrada', 'TOTAL:', 'Fecha:']):
                if len(line_str) < 45 and not re.search(r'\d{3,}', line_str):
                    entradas_dict[current_entry_key]['items'][-1]['descripcion'] = clean_text(entradas_dict[current_entry_key]['items'][-1]['descripcion'] + ' ' + line_str)

    entradas = [entradas_dict[k] for k in entradas_order]
    for e in entradas:
        calc_tot = sum(it.get('costo_total', 0.0) for it in e['items'])
        calc_iva = sum(it.get('valor_iva', 0.0) for it in e['items'])
        calc_subtot = calc_tot - calc_iva
        e['subtotal_entrada'] = calc_subtot
        e['iva_entrada'] = calc_iva
        if e['total_entrada'] == 0.0:
            e['total_entrada'] = calc_tot

    total_calculado = sum(e['total_entrada'] for e in entradas)
    
    return {
        'tipo_reporte': 'COMPRAS_ENTRADAS',
        'rango_desde': rango_desde,
        'rango_hasta': rango_hasta,
        'total_paginas': total_pages,
        'total_facturas': len(entradas),
        'total_insumos': sum(len(e['items']) for e in entradas),
        'total_general': total_calculado,
        'total_reporte_pie': total_reporte_pie if total_reporte_pie > 0 else total_calculado,
        'facturas': entradas
    }


# ==============================================================================
# 4. AUTODETECTAR Y PARSEAR CUALQUIER PDF
# ==============================================================================
def detectar_y_parsear_pdf(pdf_source: Union[str, bytes, io.BytesIO]) -> Dict[str, Any]:
    """Detecta automaticamente el tipo de reporte contable y ejecuta el parser adecuado."""
    reader = get_pdf_reader(pdf_source)
    if not reader.pages:
        raise ValueError('El archivo PDF esta vacio o no contiene paginas legibles.')
        
    sample_text = reader.pages[0].extract_text() or ''
    sample_upper = sample_text.upper()
    
    if 'ENTRADAS DE ALMACEN' in sample_upper or 'EA -' in sample_upper or 'ES -' in sample_upper:
        return parse_compras_entradas(pdf_source)
    elif 'WXMANAGER' in sample_upper or 'RELACION DE VENTAS DIARIAS' in sample_upper or 'TIPO NUMERO' in sample_upper or 'TIPO PE' in sample_upper or 'TIPO PP' in sample_upper or 'CONSUMIDOR FINAL' in sample_upper or re.search(r'\b(?:PE|PP)\s+\d+', sample_upper):
        return parse_ventas_remisiones_diarias(pdf_source)
    elif 'REPORTE DETALLADO DE FACTURAS' in sample_upper or 'TIPO FV' in sample_upper:
        return parse_ventas_pos_detallado(pdf_source)
    else:
        try:
            res = parse_ventas_remisiones_diarias(pdf_source)
            if res.get('total_facturas', 0) > 0:
                return res
        except Exception:
            pass
        try:
            res = parse_ventas_pos_detallado(pdf_source)
            if res.get('total_facturas', 0) > 0:
                return res
        except Exception:
            pass
        return parse_compras_entradas(pdf_source)
