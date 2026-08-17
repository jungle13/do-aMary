import google.generativeai as genai
from config import Config
import json
import time
import re
from typing import TypedDict

class GeminiParser:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3.6-flash')

            
    def parse_invoice_pdf(self, pdf_path):
        """
        Envía un PDF a Gemini para extraer productos y cantidades.
        Retorna un diccionario con los datos extraídos o None si hay un error.
        """
        if not self.api_key:
            print("Error: No hay API key de Gemini configurada.")
            return None
            
        try:
            print(f"Subiendo archivo a Gemini: {pdf_path}")
            # 1. Subir archivo a la API de File de Gemini
            uploaded_file = genai.upload_file(path=pdf_path)
            
            # 2. Esperar a que el archivo se procese (opcional, recomendado para PDFs)
            while uploaded_file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            print("\nArchivo listo. Extrayendo datos...")
            
            # 3. Armar el prompt estricto
            prompt = """
            Extrae TODOS los datos de TODAS las páginas del reporte de entradas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas el nombre del proveedor ni la descripción del producto. Limítate a los datos numéricos y códigos.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada compra inicia en el extremo izquierdo con un código "EA-" (ej. EA-9273). Procesa TODOS los que encuentres.
            2. FECHA Y FACTURA: La "fecha" suele estar bajo el código EA (conviértela a YYYY-MM-DD). El "numero_factura" está junto a la palabra "Factura No.". Si no hay, pon null.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Totales de Entrada:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_insumo": Código de 4 dígitos al extremo izquierdo.
               - "cantidad": Dato bajo la columna 'Cant.'
               - "costo_unitario": Dato bajo la columna 'Costo'.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
            5. FORMATO NUMÉRICO ESTRICTO: Convierte puntos a miles y comas a decimales (ej. "13.100" -> 13100.0 y "16,50" -> 16.5).
            
            ESTRUCTURA EXACTA REQUERIDA (Sigue este patrón para todos los bloques e insumos):
            [
              {
                "numero_entrada": "EA-9276",
                "fecha": "2026-08-03",
                "numero_factura": "19284",
                "productos": [
                  {
                    "codigo_insumo": "0471",
                    "cantidad": 10.0,
                    "costo_unitario": 7353.0,
                    "iva": 13971.0
                  },
                  {
                    "codigo_insumo": "4182",
                    "cantidad": 50.0,
                    "costo_unitario": 2815.0,
                    "iva": 26744.0
                  }
                ]
              }
            ]
            """
            
            # 4. Enviar a Gemini forzando el motor JSON y maximizando los tokens
            response = self.model.generate_content(
                [uploaded_file, prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.0, # Temperatura cero para formato robótico y determinista
                    max_output_tokens=8192 # Darle el máximo espacio posible para PDFs grandes
                )
            )
            
            # Como forzamos el mime_type, la respuesta ya es un string JSON limpio
            text_response = response.text.strip()
            
            # Limpiar comas huérfanas (trailing commas) que la IA suele dejar por error antes de cerrar llaves o corchetes
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            # Parsear el JSON de forma segura
            data = json.loads(text_response)
            
            # --- Escudo de formato (Ahora esperamos una lista) ---
            if isinstance(data, dict):
                # Si Gemini se equivoca y devuelve un solo objeto, lo envolvemos en una lista
                data = [data]
            elif not isinstance(data, list):
                data = []
            # -------------------------------
            
            # Eliminar archivo subido
            genai.delete_file(uploaded_file.name)
            
            print("¡Extracción completada! Conexión con Gemini cerrada.")
            return data
            
        except Exception as e:
            print(f"Error procesando PDF con Gemini: {e}")
            return None

    def parse_compras_pdf_page(self, pdf_path, page_index):
        """
        Extrae datos de compras de una única página del PDF.
        """
        if not self.api_key:
            return None
            
        try:
            
            from pypdf import PdfReader, PdfWriter
            import os
            from typing import TypedDict
        except ImportError:
            return None
            
        try:
            reader = PdfReader(pdf_path)
            if page_index < 0 or page_index >= len(reader.pages):
                return None
                
            class ProductoCompra(TypedDict):
                codigo_insumo: str
                cantidad: float
                costo_unitario: float
                iva: float

            class FacturaCompra(TypedDict):
                numero_entrada: str
                fecha: str
                numero_factura: str
                proveedor: str
                productos: list[ProductoCompra]
                
            prompt = """
            Extrae TODOS los datos de TODAS las facturas en esta página del reporte de entradas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas la descripción del producto. Limítate a los datos solicitados.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada compra inicia en el extremo izquierdo con un código "EA-" (ej. EA-9273). Procesa TODOS los que encuentres.
            2. CABECERA DEL BLOQUE (Fecha, Factura y Proveedor): 
               En la misma línea que el "EA-" (o en la línea inmediatamente inferior):
               - La "fecha" suele estar a continuación del EA (conviértela a YYYY-MM-DD).
               - El "numero_factura" está precedido por la palabra "Factura No." o "Factura". Si no hay número, pon null.
               - El "proveedor" se encuentra AL LADO DERECHO de la palabra "Factura" o del número de factura. Extrae SOLO el nombre comercial (ej. "DISTRIBUCIONES PUNTO CHEVERE SAS", "AJOVER SAS"). 
               - REGLA ESTRICTA PARA PROVEEDOR: ESTÁ TOTALMENTE PROHIBIDO incluir explicaciones, razonamientos internos, notas de OCR o caracteres asiáticos en este campo. El valor debe ser ÚNICAMENTE el nombre de la empresa.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Totales de Entrada:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_insumo": Código de 4 dígitos al extremo izquierdo.
               - "cantidad": Dato bajo la columna 'Cant.'
               - "costo_unitario": Dato bajo la columna 'Costo'.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
            5. FORMATO NUMÉRICO ESTRICTO: Convierte puntos a miles y comas a decimales (ej. "13.100" -> 13100.0 y "16,50" -> 16.5).
            
            ESTRUCTURA EXACTA REQUERIDA (Sigue este patrón para todos los bloques e insumos):
            [
              {
                "numero_entrada": "EA-9276",
                "fecha": "2026-08-03",
                "numero_factura": "19284",
                "proveedor": "NOMBRE DEL PROVEEDOR SAS",
                "productos": [
                  {
                    "codigo_insumo": "0471",
                    "cantidad": 10.0,
                    "costo_unitario": 7353.0,
                    "iva": 13971.0
                  }
                ]
              }
            ]
            """
            
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            
            temp_pdf_path = f"temp_compras_page_{page_index}.pdf"
            with open(temp_pdf_path, "wb") as f:
                writer.write(f)
            
            uploaded_file = genai.upload_file(path=temp_pdf_path)
            time.sleep(2)
            
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            intentos = 0
            max_intentos = 3
            response = None
            
            while intentos < max_intentos:
                try:
                    response = self.model.generate_content(
                        [uploaded_file, prompt],
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=list[FacturaCompra],
                            temperature=0.0,
                            max_output_tokens=8192
                        )
                    )
                    break
                except Exception as api_e:
                    error_str = str(api_e)
                    if "429" in error_str or "quota" in error_str.lower():
                        print(f"⚠️ Límite de Google alcanzado (429). Esperando 60s de forma invisible... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(60)
                        intentos += 1
                    elif "500" in error_str or "internal error" in error_str.lower():
                        print(f"⚠️ Error interno en Google (500). Reintentando en 15s... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(15)
                        intentos += 1
                    else:
                        raise api_e
                        
            if response is None:
                print("Error: Se superaron los intentos máximos o respuesta nula.")
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)
                return []
            
            text_response = response.text.strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            text_response = text_response.strip()
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            genai.delete_file(uploaded_file.name)
            os.remove(temp_pdf_path)
            
            try:
                data = json.loads(text_response)
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                return []
            except json.JSONDecodeError as je:
                print(f"Error parseando JSON en página {page_index + 1}. Error: {je}")
                print(f"Texto problemático:\n{text_response[:500]}...")
                return []
                
        except Exception as e:
            print(f"Error procesando página {page_index + 1} de compras con Gemini: {e}")
            return None

    def parse_ventas_pdf(self, pdf_path, progress_callback=None):
        """
        Envía un PDF de ventas a Gemini (en bloques) para evitar el límite de memoria.
        Retorna un arreglo con los datos extraídos o None si hay un error.
        """
        if not self.api_key:
            print("Error: No hay API key de Gemini configurada.")
            return None
            
        try:
            from pypdf import PdfReader, PdfWriter
            import os
        except ImportError:
            msg = "Error: Falta la librería pypdf. Ejecuta 'pip install pypdf' en la terminal."
            print(msg)
            if progress_callback: progress_callback(msg)
            return None
            
        try:
            msg = f"Preparando división automática para el PDF..."
            print(msg)
            if progress_callback: progress_callback(msg)
            
            reader = PdfReader(pdf_path)
            total_paginas = len(reader.pages)
            tamano_bloque = 1 # Procesar de a 1 página para máxima precisión y evitar errores de JSON
            todas_las_facturas = []
            
            # --- EL MOLDE ESTRICTO PARA VENTAS ---
            class ProductoVenta(TypedDict):
                codigo_item: str
                cantidad: float
                subtotal: float
                iva: float
                costo_total: float

            class FacturaVenta(TypedDict):
                fecha: str
                numero_factura: str
                productos: list[ProductoVenta]
            # --------------------------------------------
            
            prompt = """
            Extrae TODOS los datos de TODAS las páginas de este fragmento del reporte de facturas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas el nombre del cliente ni la descripción del producto. Limítate a los datos numéricos y códigos.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada bloque de venta inicia con "Fact.No." seguido del número de factura. Procesa TODOS los que encuentres en el documento.
            2. FECHA Y FACTURA: La "fecha" suele estar en la misma línea que el "Fact.No." (conviértela a YYYY-MM-DD). Extrae el número de factura.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Total Factura:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_item": Código al extremo izquierdo (ej. 0847, 0571-1).
               - "cantidad": Dato bajo la columna 'Cantidad'.
               - "subtotal": Dato bajo la columna 'Subtotal'. NO HAGAS NINGÚN CÁLCULO.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
               - "costo_total": Dato bajo la columna 'Total'.
            5. FORMATO NUMÉRICO ESTRICTO: Todo valor monetario o cantidad debe ser número (float). Usa puntos (.) solo para decimales. NO uses comas (,) para separar los miles dentro de los números (ej. "93,277" debe ser 93277.0).
            """
            
            # Ciclo para iterar el documento por pedazos
            for i in range(0, total_paginas, tamano_bloque):
                rango_inicio = i + 1
                rango_fin = min(i + tamano_bloque, total_paginas)
                msg = f"Extrayendo datos: Página {rango_inicio} de {total_paginas}..." if tamano_bloque == 1 else f"Extrayendo datos: Páginas {rango_inicio} a {rango_fin} de {total_paginas}..."
                print(msg)
                if progress_callback: progress_callback(msg)
                
                # 1. Crear PDF temporal con solo un bloque de páginas
                writer = PdfWriter()
                for j in range(i, rango_fin):
                    writer.add_page(reader.pages[j])
                    
                temp_pdf_path = f"temp_ventas_chunk_{i}.pdf"
                with open(temp_pdf_path, "wb") as f:
                    writer.write(f)
                
                # 2. Subir el fragmento a Gemini
                uploaded_file = genai.upload_file(path=temp_pdf_path)
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(1)
                    uploaded_file = genai.get_file(uploaded_file.name)
                
                # 3. Extraer los datos forzando el motor JSON y el esquema
                response = self.model.generate_content(
                    [uploaded_file, prompt],
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=list[FacturaVenta],
                        temperature=0.0,
                        max_output_tokens=8192
                    )
                )
                
                text_response = response.text.strip()
                
                # Limpiar la basura residual y comas huérfanas
                if text_response.startswith("```json"):
                    text_response = text_response[7:]
                if text_response.startswith("```"):
                    text_response = text_response[3:]
                if text_response.endswith("```"):
                    text_response = text_response[:-3]
                
                text_response = text_response.strip()
                text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
                
                try:
                    data = json.loads(text_response)
                    # Agrupar los resultados
                    if isinstance(data, dict):
                        todas_las_facturas.append(data)
                    elif isinstance(data, list):
                        todas_las_facturas.extend(data)
                except json.JSONDecodeError as je:
                    print(f"Error parseando el JSON en página {rango_inicio}. Saltando bloque. Error: {je}")
                    print(f"JSON Problemático:\n{text_response[:500]}...")
                
                # 4. Limpiar los archivos temporales para no llenar el disco ni la nube
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)

            msg = "¡Extracción de todas las páginas completada!"
            print(msg)
            if progress_callback: progress_callback(msg)
            
            return todas_las_facturas
            
        except Exception as e:
            print(f"Error procesando PDF de ventas con Gemini: {e}")
            return None

    def parse_ventas_pdf_page(self, pdf_path, page_index, tipo_documento="Remisión"):
        """
        Extrae datos de una única página del PDF.
        """
        if not self.api_key:
            return None
            
        try:
            from pypdf import PdfReader, PdfWriter
            import os
        except ImportError:
            return None
            
        try:
            reader = PdfReader(pdf_path)
            if page_index < 0 or page_index >= len(reader.pages):
                return None
                
            # --- EL MOLDE ESTRICTO PARA VENTAS ---
            class ProductoVenta(TypedDict):
                codigo_item: str
                cantidad: float
                subtotal: float
                iva: float
                costo_total: float

            class FacturaVenta(TypedDict):
                fecha: str
                numero_factura: str
                productos: list[ProductoVenta]
            
            if tipo_documento == "Factura POS":
                prompt = """
                Extrae los datos de ventas formato POS de este documento y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
                Solo se requiere el numero de factura, codigo insumo, cantidad y precio unitario.
                NO extraigas fechas (el sistema las asignará), ni nombres de clientes.
                
                REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
                1. BLOQUES DE FACTURA: Cada factura inicia debajo de la palabra "TIPO NUMERO" con el prefijo "PP" seguido del número (ej. "PP 26396"). Extrae SOLO los números.
                2. PRODUCTOS: Debajo de "Clientes Varios", cada línea de producto tiene 3 valores separados por espacios. 
                   - "codigo_item": El primer número de la línea (ej. 2151).
                   - "cantidad": El segundo número (ej. 50.00).
                   - "precio_unitario": El tercer número (ej. 1900.00).
                3. CÁLCULOS OBLIGATORIOS PARA EL JSON:
                   - "subtotal": DEBES multiplicar la "cantidad" por el "precio_unitario".
                   - "iva": Siempre será 0.0 para este formato.
                   - "costo_total": Será exactamente igual al "subtotal".
                4. FORMATO NUMÉRICO: Todo valor monetario o cantidad debe ser número (float). Usa puntos (.) solo para decimales. NO uses comas.
                """
            else:
                prompt = """
                Extrae TODOS los datos de TODAS las páginas de este fragmento del reporte de facturas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
                NO extraigas el nombre del cliente ni la descripción del producto. Limítate a los datos numéricos y códigos.
                
                REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
                1. BLOQUES: Cada bloque de venta inicia con "Fact.No." seguido del número de factura. Procesa TODOS los que encuentres.
                2. FECHA Y FACTURA: La "fecha" suele estar en la misma línea que el "Fact.No.". Extrae el número de factura.
                3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a "Total Factura:".
                4. CAMPOS POR PRODUCTO:
                   - "codigo_item": Código al extremo izquierdo.
                   - "cantidad": Dato bajo la columna 'Cantidad'.
                   - "subtotal": Dato bajo la columna 'Subtotal'. NO HAGAS NINGÚN CÁLCULO.
                   - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
                   - "costo_total": Dato bajo la columna 'Total'.
                5. FORMATO NUMÉRICO: Usa puntos (.) solo para decimales. NO uses comas (,).
                """
            
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            
            temp_pdf_path = f"temp_ventas_page_{page_index}.pdf"
            with open(temp_pdf_path, "wb") as f:
                writer.write(f)
            
            uploaded_file = genai.upload_file(path=temp_pdf_path)
            time.sleep(2) # Pausa inicial para dar respiro a la API
            
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5) # Preguntar solo cada 5 segundos
                uploaded_file = genai.get_file(uploaded_file.name)
            
            intentos = 0
            max_intentos = 3
            response = None
            
            while intentos < max_intentos:
                try:
                    response = self.model.generate_content(
                        [uploaded_file, prompt],
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=list[FacturaVenta],
                            temperature=0.0,
                            max_output_tokens=8192
                        )
                    )
                    break
                except Exception as api_e:
                    error_str = str(api_e)
                    if "429" in error_str or "quota" in error_str.lower():
                        print(f"⚠️ Límite de Google alcanzado (429). Esperando 60s de forma invisible... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(60)
                        intentos += 1
                    elif "500" in error_str or "internal error" in error_str.lower():
                        print(f"⚠️ Error interno en los servidores de Google (500). Reintentando en 15s... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(15)
                        intentos += 1
                    else:
                        raise api_e
                        
            if response is None:
                print("Error: Se superaron los intentos máximos o la respuesta es nula.")
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)
                return []
            
            text_response = response.text.strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
            
            text_response = text_response.strip()
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            genai.delete_file(uploaded_file.name)
            os.remove(temp_pdf_path)
            
            try:
                data = json.loads(text_response)
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                return []
            except json.JSONDecodeError as je:
                print(f"Error parseando el JSON de página {page_index + 1}. Error: {je}")
                return []
                
        except Exception as e:
            print(f"Error procesando página {page_index + 1} de ventas con Gemini: {e}")
            return None
