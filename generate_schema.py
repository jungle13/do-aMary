import json

with open('openapi.json', 'r') as f:
    spec = json.load(f)

output = []
output.append('-- ESQUEMA ACTUALIZADO DE SUPABASE (Generado via OpenAPI Rest)')
output.append('-- Fecha: Generado Automáticamente\n')

# Tables
output.append('-- ==========================================')
output.append('-- TABLAS Y VISTAS')
output.append('-- ==========================================\n')

for def_name, definition in spec.get('definitions', {}).items():
    if def_name.endswith('_response') or def_name.endswith('_request'): continue
    if definition.get('type') == 'object':
        output.append(f'CREATE TABLE public.{def_name} (')
        cols = []
        for prop_name, prop_details in definition.get('properties', {}).items():
            prop_type = prop_details.get('type', 'text')
            prop_format = prop_details.get('format', '')
            desc = prop_details.get('description', '')
            is_pk = 'Note: This is a Primary Key' in desc
            is_fk = 'Note: This is a Foreign Key' in desc
            
            sql_type = prop_type
            if prop_format: sql_type = prop_format
            
            line = f'    {prop_name} {sql_type}'
            if is_pk: line += ' PRIMARY KEY'
            if is_fk: 
                # extract FK target
                try:
                    target = desc.split('to `')[1].split('`')[0]
                    line += f' REFERENCES {target}'
                except:
                    pass
            cols.append(line)
            
        output.append(',\n'.join(cols))
        output.append(');\n')

# RPCs
output.append('-- ==========================================')
output.append('-- FUNCIONES RPC')
output.append('-- ==========================================\n')

for path, path_obj in spec.get('paths', {}).items():
    if path.startswith('/rpc/'):
        rpc_name = path.replace('/rpc/', '')
        post = path_obj.get('post', {})
        params = post.get('parameters', [])
        
        args = []
        for p in params:
            if p.get('in') == 'body':
                schema = p.get('schema', {}).get('$ref', '')
                if schema:
                    ref_name = schema.split('/')[-1]
                    ref_def = spec.get('definitions', {}).get(ref_name, {})
                    for p_name, p_details in ref_def.get('properties', {}).items():
                        ptype = p_details.get('type', 'text')
                        args.append(f'{p_name} {ptype}')
        
        args_str = ', '.join(args)
        resp_desc = post.get('responses', {}).get('200', {}).get('description', 'void')
        output.append(f'CREATE FUNCTION public.{rpc_name}({args_str})')
        output.append(f'RETURNS {resp_desc} AS $$')
        output.append('-- Lógica en Supabase --')
        output.append('$$ LANGUAGE plpgsql;\n')

with open('esquema_actualizado.sql', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('esquema_actualizado.sql generated')
