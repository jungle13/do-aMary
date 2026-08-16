import re

with open('database_schema.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

tables = {}
constraints = []

mode = None
for line in lines:
    line = line.strip()
    if line.startswith('## Restricciones'):
        mode = 'constraints'
        continue
    elif line.startswith('## Columnas'):
        mode = 'columns'
        continue
        
    if mode == 'constraints' and line.startswith('|') and not line.startswith('| nombre_tabla') and not line.startswith('| ---'):
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 3:
            table, cname, cdef = parts[0], parts[1], parts[2]
            constraints.append({'table': table, 'name': cname, 'def': cdef})
            
    elif mode == 'columns' and line.startswith('|') and not line.startswith('| tabla') and not line.startswith('| ---'):
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 5:
            table, col, dtype, nulls, default = parts[0], parts[1], parts[2], parts[3], parts[4]
            if table not in tables:
                tables[table] = []
            tables[table].append({'col': col, 'dtype': dtype, 'nulls': nulls, 'default': default})

output = []
output.append('-- ESQUEMA ACTUALIZADO DE SUPABASE (Recuperado a partir de la documentación validada)\n')

for table, cols in tables.items():
    output.append(f'CREATE TABLE public.{table} (')
    col_lines = []
    for c in cols:
        line = f"    {c['col']} {c['dtype']}"
        if c['nulls'] == 'NO':
            line += " NOT NULL"
        if c['default'] != 'null':
            line += f" DEFAULT {c['default']}"
        col_lines.append(line)
        
    # Append constraints for this table
    for cst in constraints:
        if cst['table'] == table:
            col_lines.append(f"    CONSTRAINT {cst['name']} {cst['def']}")
            
    output.append(',\n'.join(col_lines))
    output.append(');\n')

output.append('-- ==========================================')
output.append('-- FUNCIONES RPC')
output.append('-- ==========================================\n')

output.append("""CREATE OR REPLACE FUNCTION get_kpis_por_categoria_rpc()
RETURNS TABLE (
    categoria text,
    costo_inventario numeric,
    ventas_totales numeric,
    rentabilidad numeric,
    rotacion numeric
) AS $$
BEGIN
    RETURN QUERY
    WITH VentasCategoria AS (
        SELECT 
            ci.categoria,
            SUM(rv.total) AS ventas_totales,
            SUM(rv.cantidad * ci.costo_unitario) AS costo_ventas
        FROM public.registro_ventas rv
        JOIN public.catalogo_insumos ci ON rv.codigo_insumo = ci.codigo_insumo 
        WHERE rv.estado_registro = 'VÁLIDO'
        GROUP BY ci.categoria
    ),
    InventarioCategoria AS (
        SELECT 
            ci.categoria,
            SUM(CASE WHEN ci.stock_actual > 0 THEN ci.stock_actual * ci.costo_unitario ELSE 0 END) AS costo_inventario
        FROM public.catalogo_insumos ci
        GROUP BY ci.categoria
    )
    SELECT 
        COALESCE(i.categoria, v.categoria, 'SIN CATEGORIA') AS categoria,
        COALESCE(i.costo_inventario, 0) AS costo_inventario,
        COALESCE(v.ventas_totales, 0) AS ventas_totales,
        CASE WHEN COALESCE(v.ventas_totales, 0) > 0 
             THEN ((v.ventas_totales - v.costo_ventas) / v.ventas_totales) * 100 
             ELSE 0 END AS rentabilidad,
        CASE WHEN COALESCE(i.costo_inventario, 0) > 0 
             THEN COALESCE(v.ventas_totales, 0) / i.costo_inventario 
             ELSE 0 END AS rotacion
    FROM InventarioCategoria i
    FULL OUTER JOIN VentasCategoria v ON i.categoria = v.categoria
    WHERE COALESCE(i.categoria, v.categoria) IS NOT NULL;
END;
$$ LANGUAGE plpgsql;
""")

with open('esquema_actualizado.sql', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('esquema_actualizado.sql successfully generated from schema definition.')
