import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Faltan credenciales de Supabase.")
    exit(1)

if SUPABASE_URL.endswith('/'):
    SUPABASE_URL = SUPABASE_URL[:-1]
if not SUPABASE_URL.endswith('/rest/v1'):
    SUPABASE_URL = SUPABASE_URL + "/rest/v1"

file_path = "BASE DE DATOS CONTEO FISICO AGOSTO 2026.xlsx"
sheet_name = "CATALOGO_COMPLETO"
print(f"Leyendo hoja '{sheet_name}' del archivo: {file_path}")

df = pd.read_excel(file_path, sheet_name=sheet_name)
df.columns = df.columns.str.strip()

records_to_insert = []
records_dict = {}

for index, row in df.iterrows():
    codigo = str(row.get("CODIGO", "")).strip()
    
    if not codigo or codigo == 'nan':
        continue
        
    nombre = str(row.get("INSUMO", "")).strip()
    categoria = str(row.get("CATEGORIA", "")).strip()
    
    precio_venta_raw = row.get("PRECIO VENTA", 0)
    try:
        precio_venta = float(precio_venta_raw)
    except:
        precio_venta = 0.0

    record = {
        "codigo": codigo,
        "nombre": nombre,
        "categoria": categoria if categoria and categoria != 'nan' else "SIN CATEGORIA",
        "descripcion": "",
        "precio_venta": precio_venta,
        # Dejamos que la base de datos ponga los valores por defecto
        # o los enviamos en 0 por seguridad
        "stock_actual": 0,
        "costo_unitario": 0,
        "stock_minimo": 5,
        "estado": True
    }
    
    # Prevenimos duplicados por si los hay en el catálogo
    records_dict[codigo] = record

records_to_insert = list(records_dict.values())
print(f"Se encontraron {len(records_to_insert)} registros únicos/válidos.")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

batch_size = 100
total_inserted = 0

print("Iniciando subida a Supabase mediante REST...")
for i in range(0, len(records_to_insert), batch_size):
    batch = records_to_insert[i:i+batch_size]
    url = f"{SUPABASE_URL}/catalogo_insumos?on_conflict=codigo"
    
    response = requests.post(url, json=batch, headers=headers)
    if response.status_code in [200, 201]:
        total_inserted += len(batch)
        print(f"Lote {i//batch_size + 1} subido. Progreso: {total_inserted}/{len(records_to_insert)}")
    else:
        print(f"Error subiendo lote {i//batch_size + 1}: {response.text}")

print(f"¡Subida completada! Total insertados: {total_inserted}")
