# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.'), ('assets', 'assets')],
    hiddenimports=['core', 'core.fecha_utils', 'core.supabase_client', 'core.database', 'core.audit_logger', 'core.logger', 'core.excel_manager', 'core.gemini_parser', 'core.mobile_server', 'core.mobile_service', 'core.tunnel_manager', 'zoneinfo', 'tzdata', 'core.repositories.compras_repo', 'core.repositories.ventas_repo', 'core.repositories.insumos_repo', 'core.repositories.usuarios_repo', 'core.repositories.cierres_repo', 'core.repositories.clientes_repo', 'core.repositories.cartera_repo', 'ui.app', 'ui.layout.sidebar', 'ui.views.login', 'ui.views.inventario', 'ui.views.compras', 'ui.views.ventas', 'ui.views.cartera', 'ui.views.ajustes_inventario', 'ui.views.cierre_inventario', 'ui.views.conteo_inicial', 'ui.views.dashboard', 'ui.views.informes', 'ui.components.autocomplete', 'ui.components.forms', 'ui.components.metric_card', 'supabase', 'postgrest', 'gotrue', 'realtime', 'storage3', 'httpx', 'pandas', 'openpyxl', 'google.generativeai', 'dotenv', 'requests', 'pypdf', 'plotly', 'fastapi', 'fastapi.responses', 'fastapi.routing', 'fastapi.middleware', 'fastapi.middleware.cors', 'starlette', 'starlette.responses', 'starlette.routing', 'starlette.middleware', 'starlette.middleware.cors', 'pydantic', 'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.loops.asyncio', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.off', 'uvicorn.lifespan.on', 'h11', 'anyio', 'anyio._backends._asyncio', 'sniffio', 'qrcode', 'qrcode.image.pil', 'PIL', 'PIL.Image', 'fpdf'],
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
    version='C:/Users/Home/AppData/Local/Temp/2cbd3ffb-1099-4fb8-b10a-fb9eb999aba2',
    icon=['assets/icon.ico'],
)
