"""
Script para restaurar la base de datos de Supabase a un estado previo respaldado en JSON.
Uso: python scripts/restaurar_backup.py [ruta_al_archivo_json_o_dejar_vacio_para_default]
"""
import os
import sys
import json

# Asegurar que el directorio raíz esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import SupabaseClient

def restaurar_base_datos(archivo_backup: str = "backups/backup_estado_actual.json"):
    if not os.path.exists(archivo_backup):
        print(f"ERROR: El archivo de respaldo '{archivo_backup}' no existe.")
        return False
        
    with open(archivo_backup, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    db = SupabaseClient()
    
    # 1. Mapeo de tablas y llaves primarias
    table_pks = {
        "detalle_pagos_cartera": "id_detalle",
        "cuotas_cartera": "id_cuota",
        "pagos_cartera": "id_pago",
        "registro_auditorias_cierres": "id_auditoria",
        "registro_ajustes_inventario": "id_ajuste",
        "registro_ventas": "id_venta",
        "registro_compras": "id_compra",
        "periodos_inventario": "id_periodo",
        "conteo_fisico_relacionado": "id_conteo",
        "historial_acciones_usuario": "id_accion",
        "registro_errores_sistema": "id_error",
        "catalogo_insumos": "id_insumo",
        "clientes": "id_cliente",
        "usuarios": "id_usuario"
    }

    # Orden de eliminación (hijos primero para respetar llaves foráneas)
    delete_order = [
        "detalle_pagos_cartera",
        "cuotas_cartera",
        "pagos_cartera",
        "registro_auditorias_cierres",
        "registro_ajustes_inventario",
        "registro_ventas",
        "registro_compras",
        "conteo_fisico_relacionado",
        "periodos_inventario",
        "catalogo_insumos",
        "clientes",
        "historial_acciones_usuario",
        "registro_errores_sistema",
        "usuarios"
    ]
    
    # 2. Orden de inserción (padres primero)
    insert_order = [
        "usuarios",
        "clientes",
        "catalogo_insumos",
        "periodos_inventario",
        "registro_compras",
        "registro_ventas",
        "pagos_cartera",
        "cuotas_cartera",
        "detalle_pagos_cartera",
        "registro_ajustes_inventario",
        "registro_auditorias_cierres",
        "conteo_fisico_relacionado",
        "historial_acciones_usuario",
        "registro_errores_sistema"
    ]
    
    print("=" * 60)
    print(f"INICIANDO RESTAURACIÓN DESDE: {archivo_backup}")
    print("=" * 60)
    
    print("\n--- PASO 1: LIMPIANDO TABLAS ACTUALES ---")
    for t in delete_order:
        pk = table_pks.get(t, "id")
        res = db._db.delete(f"{t}?{pk}=not.is.null")
        status = res.status_code if res else "Error"
        print(f" -> Tabla '{t}': Limpieza enviada (Status: {status})")
        
    print("\n--- PASO 2: INSERTANDO REGISTROS DEL RESPALDO ---")
    for t in insert_order:
        rows = data.get(t, [])
        if not rows:
            print(f" -> Tabla '{t}': 0 registros para insertar.")
            continue
            
        chunk_size = 200
        total_insertados = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i + chunk_size]
            res = db._db.post(t, json_data=chunk, timeout=20)
            if res and res.status_code in (200, 201, 204):
                total_insertados += len(chunk)
            else:
                err_msg = res.text if res else "No response"
                print(f"    [ADVERTENCIA] Error en lote de {t} ({i}-{i+len(chunk)}): {err_msg[:120]}")
                
        print(f" -> Tabla '{t}': {total_insertados}/{len(rows)} registros restaurados.")
        
    print("=" * 60)
    print("[OK] RESTAURACION COMPLETADA EXITOSAMENTE.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    archivo = sys.argv[1] if len(sys.argv) > 1 else "backups/backup_estado_actual.json"
    restaurar_base_datos(archivo)
