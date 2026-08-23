"""
Herramienta de automatización para procesar carpetas con facturas PDF.
Clasifica, deduplica, extrae datos, envía al staging del sistema y archiva/renombra los PDFs por fecha.
"""
import os
import sys
import glob
import json
import argparse
from pypdf import PdfReader
from config import Config
from core.logger import get_logger, log_error
from core.supabase_client import get_client
from core.invoice_classifier import (
    detectar_tipo_documento,
    obtener_documentos_registrados,
    parsear_venta_pos,
    parsear_venta_remision,
    parsear_compras,
    organizar_y_reubicar_pdf,
    guardar_lote_en_staging
)

logger = get_logger("ProcesarCarpetaFacturas")

def extraer_texto_pdf(pdf_path: str) -> list[str]:
    """Extrae todas las líneas de texto del PDF."""
    lineas = []
    try:
        reader = PdfReader(pdf_path)
        for idx, page in enumerate(reader.pages):
            lineas.append(f"page {idx + 1}")
            text = page.extract_text()
            if text:
                for l in text.split('\n'):
                    if l.strip():
                        lineas.append(l.strip())
    except Exception as ex:
        log_error(f"extraer_texto_pdf: {pdf_path}", ex)
    return lineas

def procesar_carpeta(carpeta_path: str) -> dict:
    """
    Procesa todos los archivos PDF presentes en una carpeta.
    """
    if not os.path.exists(carpeta_path):
        print(f"❌ La carpeta '{carpeta_path}' no existe.")
        return {"error": "Carpeta no encontrada"}

    # Obtener únicamente los PDFs en la raíz de la carpeta (no entrar en subcarpetas de fechas ya archivadas)
    archivos_pdf = [
        os.path.join(carpeta_path, f)
        for f in os.listdir(carpeta_path)
        if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(carpeta_path, f))
    ]

    if not archivos_pdf:
        print(f"ℹ️ No se encontraron archivos PDF pendientes en: {carpeta_path}")
        return {"total_archivos": 0}

    print(f"\n📂 Iniciando procesamiento de {len(archivos_pdf)} archivos PDF en: {carpeta_path}")
    print("=" * 70)

    db = get_client()
    resumen_global = {
        "procesados": 0,
        "ventas_pos": 0,
        "ventas_remision": 0,
        "compras": 0,
        "facturas_nuevas": 0,
        "facturas_omitidas": 0,
        "detalles": []
    }

    for pdf_path in archivos_pdf:
        nombre_archivo = os.path.basename(pdf_path)
        print(f"\n📄 Analizando: {nombre_archivo}...")

        lineas = extraer_texto_pdf(pdf_path)
        if not lineas:
            print(f"  ⚠️ No se pudo extraer texto del archivo {nombre_archivo}.")
            continue

        texto_completo = "\n".join(lineas)
        tipo_doc = detectar_tipo_documento(texto_completo)
        print(f"  🔍 Formato detectado: {tipo_doc}")

        if tipo_doc == "DESCONOCIDO":
            print(f"  ❌ Formato no reconocido. Se omite.")
            continue

        # Obtener documentos existentes en BD para deduplicación
        docs_existentes = obtener_documentos_registrados(db, tipo_doc)

        # Parsear según el formato
        if tipo_doc == "VENTA_POS":
            resultado, nuevas, omitidas = parsear_venta_pos(lineas, docs_existentes)
            resumen_global["ventas_pos"] += 1
        elif tipo_doc == "VENTA_REMISION":
            resultado, nuevas, omitidas = parsear_venta_remision(lineas, docs_existentes)
            resumen_global["ventas_remision"] += 1
        elif tipo_doc == "COMPRA":
            resultado, nuevas, omitidas = parsear_compras(lineas, docs_existentes)
            resumen_global["compras"] += 1

        fecha_doc = resultado.get("fecha")
        print(f"  📅 Fecha documento: {fecha_doc}")
        print(f"  📊 Facturas en PDF: {nuevas + omitidas} (Nuevas: {nuevas}, Omitidas por duplicadas: {omitidas})")

        resultado["archivo_origen"] = nombre_archivo

        # Guardar en staging si hay facturas nuevas
        if nuevas > 0:
            guardar_lote_en_staging(resultado)
            print(f"  ✅ Lote registrado en Gestión de Cargas (Estado: EXTRAIDO_POR_AGENTE).")

        # Archivar y renombrar PDF
        nuevo_path = organizar_y_reubicar_pdf(pdf_path, tipo_doc, fecha_doc)
        print(f"  📁 Archivo movido a: {nuevo_path}")

        resumen_global["procesados"] += 1
        resumen_global["facturas_nuevas"] += nuevas
        resumen_global["facturas_omitidas"] += omitidas
        resumen_global["detalles"].append({
            "archivo": nombre_archivo,
            "tipo": tipo_doc,
            "fecha": fecha_doc,
            "nuevas": nuevas,
            "omitidas": omitidas,
            "destino": nuevo_path
        })

    print("\n" + "=" * 70)
    print("🎉 PROCESAMIENTO COMPLETADO CON ÉXITO")
    print(f"• Total PDFs procesados: {resumen_global['procesados']}")
    print(f"• Facturas nuevas listas en Gestión de Cargas: {resumen_global['facturas_nuevas']}")
    print(f"• Facturas repetidas omitidas automáticamente: {resumen_global['facturas_omitidas']}")
    print("=" * 70)
    return resumen_global

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesar carpeta con facturas PDF")
    parser.add_argument("carpeta", help="Ruta de la carpeta que contiene los PDFs")
    args = parser.parse_args()
    procesar_carpeta(args.carpeta)
