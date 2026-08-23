# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.')],
    hiddenimports=['core', 'core.supabase_client', 'core.database', 'core.audit_logger', 'core.logger', 'core.excel_manager', 'core.gemini_parser', 'core.mobile_server', 'core.mobile_service', 'core.repositories.compras_repo', 'core.repositories.ventas_repo', 'core.repositories.insumos_repo', 'core.repositories.usuarios_repo', 'core.repositories.cierres_repo', 'ui.app', 'ui.layout.sidebar', 'ui.views.login', 'ui.views.inventario', 'ui.views.compras', 'ui.views.ventas', 'ui.views.ajustes_inventario', 'ui.views.cierre_inventario', 'ui.views.conteo_inicial', 'ui.views.dashboard', 'ui.views.informes', 'ui.components.autocomplete', 'ui.components.forms', 'ui.components.metric_card', 'supabase', 'postgrest', 'gotrue', 'realtime', 'storage3', 'httpx', 'pandas', 'openpyxl', 'google.generativeai', 'dotenv', 'requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='InventarioDonaMary',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:/Users/Home/AppData/Local/Temp/f9f8fe3c-7151-4d14-b1c7-de1eb9d046a1',
)
