import sys
import os
import subprocess

def build():
    flet_exe = 'C:\\Users\\Home\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\flet.exe'
    if not os.path.exists(flet_exe):
        flet_exe = 'flet'

    print(f'Usando binario Flet pack: {flet_exe}')
    
    hidden_imports = [
        'core',
        'core.fecha_utils',
        'core.supabase_client',
        'core.database',
        'core.audit_logger',
        'core.logger',
        'core.excel_manager',
        'core.gemini_parser',
        'core.mobile_server',
        'core.mobile_service',
        'core.tunnel_manager',
        'zoneinfo',
        'tzdata',
        'core.repositories.compras_repo',
        'core.repositories.ventas_repo',
        'core.repositories.insumos_repo',
        'core.repositories.usuarios_repo',
        'core.repositories.cierres_repo',
        'core.repositories.clientes_repo',
        'core.repositories.cartera_repo',
        'ui.app',
        'ui.layout.sidebar',
        'ui.views.login',
        'ui.views.inventario',
        'ui.views.compras',
        'ui.views.ventas',
        'ui.views.cartera',
        'ui.views.ajustes_inventario',
        'ui.views.cierre_inventario',
        'ui.views.conteo_inicial',
        'ui.views.dashboard',
        'ui.views.informes',
        'ui.components.autocomplete',
        'ui.components.forms',
        'ui.components.metric_card',
        'supabase',
        'postgrest',
        'gotrue',
        'realtime',
        'storage3',
        'httpx',
        'pandas',
        'openpyxl',
        'google.generativeai',
        'dotenv',
        'requests',
        'pypdf',
        'plotly',
    ]

    cmd = [
        flet_exe,
        'pack',
        'main.py',
        '--name', 'InventarioDonaMary',
        '--add-data', '.env;.',
        '--product-name', 'Inventario Abarrotes y Desechables Dona Mary',
        '--file-description', 'Sistema de Gestion de Inventario y Ventas',
        '--product-version', '1.0.0.0',
        '--file-version', '1.0.0.0',
        '--company-name', 'Dona Mary SAS',
        '--yes'
    ]

    for h_imp in hidden_imports:
        cmd.extend(['--hidden-import', h_imp])

    print('Iniciando empaquetado...')
    
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("\n=======================================================")
        print("¡EMPAQUETADO EXITOSO!")
        print("Ejecutable generado en: dist/InventarioDonaMary.exe")
        print("=======================================================")
    else:
        print(f"\nError en el empaquetado. Código de salida: {result.returncode}")
        sys.exit(result.returncode)

if __name__ == '__main__':
    build()
