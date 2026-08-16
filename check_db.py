from core.supabase_client import SupabaseClient
c = SupabaseClient()
import requests
import datetime
mes = datetime.date.today().strftime("%Y-%m")
res = requests.post(f'{c.url}/rpc/fn_obtener_estado_cierre', json={'p_mes': mes}, headers=c.headers)
data = res.json()
print(f"Total insumos: {len(data.get('insumos', []))}")
for i in data.get('insumos', []):
    if i.get('diferencia') is not None and float(i['diferencia']) != 0:
        print(f"Insumo: {i['nombre']}, Dif: {i['diferencia']}, Costo Snap: {i['costo_unitario_snapshot']}")
