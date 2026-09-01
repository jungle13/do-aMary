"""
Script para generar una copia de seguridad (backup) completa del estado actual de la base de datos Supabase.
Uso: python scripts/crear_backup.py [nombre_opcional]
"""
import os
import sys
import json
import datetime

# Asegurar que el directorio raíz esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import SupabaseClient

def crear_copia_seguridad(nombre_sufijo: str = "pre_pruebas"):
    db = SupabaseClient()
    
    tables = [
        "usuarios",
        "clientes",
        "catalogo_insumos",
        "periodos_inventario",
        "registro_compras",
        "registro_ventas",
        "cuotas_cartera",
        "pagos_cartera",
        "detalle_pagos_cartera",
        "registro_ajustes_inventario",
        "registro_auditorias_cierres",
        "conteo_fisico_relacionado",
        "historial_acciones_usuario",
        "registro_errores_sistema"
    ]
    
    backup_data = {}
    print("=" * 60)
    print("INICIANDO RESPALDO DE BASE DE DATOS SUPABASE")
    print("=" * 60)
    
    for t in tables:
        all_rows = []
        offset = 0
        page_size = 2500
        while True:
            headers = {"Range": f"{offset}-{offset + page_size - 1}"}
            res = db._db.get(f"{t}?select=*", custom_headers=headers, timeout=15)
            if not res or res.status_code not in (200, 206):
                break
            chunk = res.json()
            if not chunk:
                break
            all_rows.extend(chunk)
            if len(chunk) < page_size:
                break
            offset += page_size
        backup_data[t] = all_rows
        print(f" -> Tabla '{t}': {len(all_rows)} registros respaldados.")

    os.makedirs("backups", exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join("backups", f"backup_{nombre_sufijo}_{stamp}.json")
    default_filename = os.path.join("backups", "backup_estado_actual.json")
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
    with open(default_filename, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print(f"[OK] RESPALDO EXITOSO:")
    print(f"  - Archivo fechado: {filename}")
    print(f"  - Archivo default: {default_filename}")
    print("=" * 60)
    return filename

if __name__ == "__main__":
    import sys
    sufijo = sys.argv[1] if len(sys.argv) > 1 else "pre_pruebas"
    crear_copia_seguridad(sufijo)
