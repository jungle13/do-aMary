import re

path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\core\supabase_client.py'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
current_method = 'unknown'

for line in lines:
    # Update current method
    m_def = re.match(r'^\s*def\s+([a-zA-Z0-9_]+)\(', line)
    if m_def:
        current_method = m_def.group(1)
        
    # Inject timeout
    new_line = line
    if 'self.session.' in new_line and ('get(' in new_line or 'post(' in new_line or 'patch(' in new_line or 'delete(' in new_line or 'put(' in new_line):
        if 'timeout=' not in new_line:
            # Reemplazar la última ocurrencia de ')' con ', timeout=10)'
            # Dado que hay una llamada por línea, podemos hacer rsplit
            parts = new_line.rsplit(')', 1)
            if len(parts) == 2:
                new_line = parts[0] + ', timeout=10)' + parts[1]

    # Inject exception
    m_exc = re.match(r'^(\s*)except Exception as e:', new_line)
    if m_exc:
        indent = m_exc.group(1)
        new_lines.append(f'{indent}except requests.exceptions.RequestException as req_e:\n')
        new_lines.append(f'{indent}    print(f"Error de conexión con Supabase en {current_method}: el servidor no responde")\n')
        
    new_lines.append(new_line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done!')
