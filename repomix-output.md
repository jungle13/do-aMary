This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: **/*.md, **/*.txt, **/*.ps1, package.json, supabase/.temp/**
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
````
core/
  excel_manager.py
  gemini_parser.py
  supabase_client.py
scratch/
  refactor_layout.py
  refactor.py
supabase/
  .gitignore
  config.toml
ui/
  components/
    forms.py
  layout/
    sidebar.py
  views/
    ajustes_inventario.py
    cierre_inventario.py
    compras.py
    conteo_inicial.py
    dashboard.py
    inventario.py
    ventas.py
  app.py
.gitignore
append_methods.py
apply_closure_updates.py
apply_safe_update.py
cargas_compras_locales.json
cargas_locales.json
check_db.py
config.py
esquema_actualizado.sql
extract_schema.js
generate_schema_from_md.py
generate_schema.py
import_excel.py
main.py
openapi.json
patch_costs.py
refactor_cierre.py
refactor_kpi.py
refactor_panel.py
revert_plotly.py
Sistema_Dona_Mary.spec
supabase_schema.sql
update_dashboard_avanzado.sql
update_fn_obtener_estado_cierre.sql
update_insumos.py
update_kpis.py
update_plotly.py
update_rpc.js
update_supabase.py
````

# Files

## File: apply_safe_update.py
````python
import re

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    safe_update_code = """
    def safe_update(self):
        \"\"\"Actualiza la UI solo si el control sigue montado en la página.\"\"\"
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass
"""

    if "def safe_update" not in content:
        # Insert after did_mount or __init__
        if "def did_mount" in content:
            content = re.sub(r'(def did_mount.*?:\n(?: {8}.*\n)+)', r'\1' + safe_update_code, content)
        else:
            content = re.sub(r'(def __init__.*?:\n(?: {8}.*\n)+)', r'\1' + safe_update_code, content)
            
    # Replace if self.page:\n self.update() or self.page.update()
    content = re.sub(r'if self\.page:\s+self\.(?:page\.)?update\(\)', r'self.safe_update()', content)
    
    # Replace stray self.update() and self.page.update() calls
    content = re.sub(r'self\.update\(\)', r'self.safe_update()', content)
    # Be careful not to replace self.page.update() inside safe_update itself!
    # A safe way is to replace self.page.update() everywhere except in safe_update.
    # First, temporarily mask the one in safe_update
    content = content.replace("self.page.update()", "self.safe_update()")
    content = content.replace("""        try:
            if self.page and self.uid:
                self.safe_update()""", """        try:
            if self.page and self.uid:
                self.page.update()""")
                
    # Also fix action_bar.update(), column_visibles.update() which we might have broken?
    # Wait, the regex for `self.update()` only catches `self.update()`, not `self.action_bar.update()`.
    # But `self.page.update()` became `self.safe_update()`. Let's ensure we only caught `self.page.update()` and `self.update()`.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

refactor_file(r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\dashboard.py')
refactor_file(r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\inventario.py')
````

## File: core/excel_manager.py
````python
import pandas as pd
import os

class ExcelManager:
    def __init__(self, filepath="Sistema_Inventario_Abarrotes_Desechabes_Mary_v2_Procesado.xlsx"):
        self.filepath = filepath
        
    def verify_file(self):
        """Verifica si el archivo Excel existe."""
        return os.path.exists(self.filepath)
        
    # Aquí irán los métodos para leer hojas (Compras, Ventas, etc.) 
    # y escribir datos sincronizados desde Supabase.
````

## File: scratch/refactor_layout.py
````python
import sys
import re

path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update did_mount
content = content.replace('def did_mount(self):\n        self.load_data()', 'def did_mount(self):\n        self.load_lista_periodos()')

# 2. Rename load_data to load_data_detalle
content = re.sub(r'def load_data\(self\):', r'def load_data_detalle(self):', content)
content = content.replace('self.load_data()', 'self.load_data_detalle()')

# 3. Update __init__
init_replacement_start = 'self.content = ft.Column(['
idx_start = content.find(init_replacement_start)
idx_end = content.find('    def _crear_kpi_card')

new_layout = '''
        # Controles vista_lista (Maestro)
        self.month_dropdown.label = 'Mes a iniciar'
        self.dt_periodos = ft.DataTable(
            column_spacing=15,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text('Periodo', weight='bold')),
                ft.DataColumn(ft.Text('Mes', weight='bold')),
                ft.DataColumn(ft.Text('Año', weight='bold')),
                ft.DataColumn(ft.Text('Estado', weight='bold')),
                ft.DataColumn(ft.Text('Acción', weight='bold')),
            ],
            rows=[]
        )
        self.vista_lista = ft.Column([
            ft.Text('Historial de Periodos', size=24, weight='bold', color=Config.COLOR_PRIMARY),
            ft.Row([self.month_dropdown, self.btn_iniciar_snapshot]),
            ft.Container(
                content=ft.Column([self.dt_periodos], scroll=ft.ScrollMode.ALWAYS, expand=True),
                expand=True
            )
        ], visible=True, expand=True)

        # Controles vista_detalle (Detalle)
        self.btn_volver = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=self.on_volver_lista)
        self.lbl_titulo_detalle = ft.Text('Auditoría: ...', size=24, weight='bold', color=Config.COLOR_PRIMARY)
        
        self.vista_detalle = ft.Column([
            ft.Row([self.btn_volver, self.lbl_titulo_detalle]),
            self.summary_container,
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    ft.Column([self.txt_estado_periodo, self.txt_progreso], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                    self.btn_aprobar_cierre
                ]),
                padding=15,
                bgcolor='white',
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, 'black'))
            ),
            ft.Container(
                content=ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS, expand=True),
                bgcolor='white',
                padding=5,
                border_radius=10,
                expand=True,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, 'black'))
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.only(top=10)
            ),
            self.action_bar
        ], visible=False, expand=True, spacing=15)

        self.content = ft.Column([self.vista_lista, self.vista_detalle], expand=True)
'''

content = content[:idx_start] + new_layout.lstrip('\n') + '\n' + content[idx_end:]

# 4. Inject new methods
new_methods = '''
    def load_lista_periodos(self):
        periodos = self.db.get_periodos_inventario()
        self.dt_periodos.rows.clear()
        
        for p in periodos:
            mes_periodo = p.get('mes_periodo', '')
            if not mes_periodo: continue
            
            parts = mes_periodo.split('-')
            year = parts[0]
            month = parts[1] if len(parts)>1 else ''
            
            estado = p.get('estado', 'DESCONOCIDO')
            color_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
            
            row = ft.DataRow(cells=[
                ft.DataCell(ft.Text(mes_periodo)),
                ft.DataCell(ft.Text(month)),
                ft.DataCell(ft.Text(year)),
                ft.DataCell(ft.Text(estado, color=color_estado.get(estado, 'black'), weight='bold')),
                ft.DataCell(ft.ElevatedButton('Ver', on_click=lambda e, m=mes_periodo: self.mostrar_detalle(m)))
            ])
            self.dt_periodos.rows.append(row)
            
        if self.page:
            self.page.update()

    def mostrar_detalle(self, mes):
        self.vista_lista.visible = False
        self.vista_detalle.visible = True
        self.mes_seleccionado = mes
        self.lbl_titulo_detalle.value = f'Auditoría: {mes}'
        self.load_data_detalle()

    def on_volver_lista(self, e):
        self.cancelar_edicion()
        self.vista_detalle.visible = False
        self.vista_lista.visible = True
        self.load_lista_periodos()
'''
content = content + new_methods

# 5. Fix on_month_change
content = content.replace(
'''    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.month_dropdown.update()
        self.current_page = 1
        self.load_data_detalle()''',
'''    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.month_dropdown.update()'''
)

# 6. Fix _on_generar_snapshot_worker
content = content.replace(
'''            if res.get("exito"):
                self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
                self.current_page = 1
                self.load_data_detalle()''',
'''            if res.get("exito"):
                self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
                self.current_page = 1
                self.mostrar_detalle(self.mes_seleccionado)'''
)

# 7. Standardize updates
content = re.sub(r'if self\.page:\s+self\.update\(\)', 'if self.page:\n            self.page.update()', content)
content = re.sub(r'(?<!\.)self\.update\(\)', 'if self.page:\n            self.page.update()', content)
content = re.sub(r'(?<!\.)self\.page\.update\(\)', 'if self.page:\n            self.page.update()', content)
content = re.sub(r'if self\.page:\s*if self\.page:\s*self\.page\.update\(\)', 'if self.page:\n            self.page.update()', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done layout rewrite')
````

## File: scratch/refactor.py
````python
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
````

## File: supabase/.gitignore
````
# Supabase
.branches
.temp

# dotenvx
.env.keys
.env.local
.env.*.local
````

## File: supabase/config.toml
````toml
# For detailed configuration reference documentation, visit:
# https://supabase.com/docs/guides/local-development/cli/config
# A string used to distinguish different Supabase projects on the same host. Defaults to the
# working directory name when running `supabase init`.
project_id = "do-aMary"

[api]
enabled = true
# Port to use for the API URL.
port = 54321
# Schemas to expose in your API. Tables, views and stored procedures in this schema will get API
# endpoints. `public` and `graphql_public` schemas are included by default.
schemas = ["public", "graphql_public"]
# Extra schemas to add to the search_path of every request.
extra_search_path = ["public", "extensions"]
# The maximum number of rows returns from a view, table, or stored procedure. Limits payload size
# for accidental or malicious requests.
max_rows = 1000
# Controls whether new tables, views, sequences and functions created in the `public` schema by
# `postgres` are reachable through the Data API roles (`anon`, `authenticated`, `service_role`)
# without explicit GRANTs. When unset, new entities are NOT auto-exposed, matching the new cloud
# default. Set to `true` to keep the legacy behaviour of auto-exposing new entities; this is
# deprecated and the field is removed on 2026-10-30 once the always-revoked behaviour is permanent.
# auto_expose_new_tables = true

[api.tls]
# Enable HTTPS endpoints locally using a self-signed certificate.
enabled = false
# Paths to self-signed certificate pair.
# cert_path = "../certs/my-cert.pem"
# key_path = "../certs/my-key.pem"

[db]
# Port to use for the local database URL.
port = 54322
# Port used by db diff command to initialize the shadow database.
shadow_port = 54320
# Maximum amount of time to wait for health check when starting the local database.
health_timeout = "2m"
# The database major version to use. This has to be the same as your remote database's. Run `SHOW
# server_version;` on the remote database to check.
major_version = 17

[db.pooler]
enabled = false
# Port to use for the local connection pooler.
port = 54329
# Specifies when a server connection can be reused by other clients.
# Configure one of the supported pooler modes: `transaction`, `session`.
pool_mode = "transaction"
# How many server connections to allow per user/database pair.
default_pool_size = 20
# Maximum number of client connections allowed.
max_client_conn = 100

# [db.vault]
# secret_key = "env(SECRET_VALUE)"

[db.migrations]
# If disabled, migrations will be skipped during a db push or reset.
enabled = true
# Specifies an ordered list of schema files, directories, or glob patterns that describe your database.
# Supports paths relative to supabase directory: "./schemas/*.sql", "./database".
schema_paths = []

[db.seed]
# If enabled, seeds the database after migrations during a db reset.
enabled = true
# Specifies an ordered list of seed files to load during db reset.
# Supports glob patterns relative to supabase directory: "./seeds/*.sql"
sql_paths = ["./seed.sql"]

[db.network_restrictions]
# Enable management of network restrictions.
enabled = false
# List of IPv4 CIDR blocks allowed to connect to the database.
# Defaults to allow all IPv4 connections. Set empty array to block all IPs.
allowed_cidrs = ["0.0.0.0/0"]
# List of IPv6 CIDR blocks allowed to connect to the database.
# Defaults to allow all IPv6 connections. Set empty array to block all IPs.
allowed_cidrs_v6 = ["::/0"]

# Uncomment to reject non-secure connections to the database.
# [db.ssl_enforcement]
# enabled = true

[realtime]
enabled = true
# Bind realtime via either IPv4 or IPv6. (default: IPv4)
# ip_version = "IPv6"
# The maximum length in bytes of HTTP request headers. (default: 4096)
# max_header_length = 4096

[studio]
enabled = true
# Port to use for Supabase Studio.
port = 54323
# External URL of the API server that frontend connects to.
api_url = "http://127.0.0.1"
# OpenAI API Key to use for Supabase AI in the Supabase Studio.
openai_api_key = "env(OPENAI_API_KEY)"

# Email testing server. Emails sent with the local dev setup are not actually sent - rather, they
# are monitored, and you can view the emails that would have been sent from the web interface.
[local_smtp]
enabled = true
# Port to use for the email testing server web interface.
port = 54324
# Uncomment to expose additional ports for testing user applications that send emails.
# smtp_port = 54325
# pop3_port = 54326
# admin_email = "admin@email.com"
# sender_name = "Admin"

[storage]
enabled = true
# The maximum file size allowed (e.g. "5MB", "500KB").
file_size_limit = "50MiB"

# Uncomment to configure local storage buckets
# [storage.buckets.images]
# public = false
# file_size_limit = "50MiB"
# allowed_mime_types = ["image/png", "image/jpeg"]
# objects_path = "./images"

# Allow connections via S3 compatible clients
[storage.s3_protocol]
enabled = true

# Image transformation API is available to Supabase Pro plan.
# [storage.image_transformation]
# enabled = true

# Store analytical data in S3 for running ETL jobs over Iceberg Catalog
# This feature is only available on the hosted platform.
[storage.analytics]
enabled = false
max_namespaces = 5
max_tables = 10
max_catalogs = 2

# Analytics Buckets is available to Supabase Pro plan.
# [storage.analytics.buckets.my-warehouse]

# Store vector embeddings in S3 for large and durable datasets
[storage.vector]
enabled = true
max_buckets = 10
max_indexes = 5

# Vector Buckets is available to Supabase Pro plan.
# [storage.vector.buckets.documents-openai]

[auth]
enabled = true
# The base URL of your website. Used as an allow-list for redirects and for constructing URLs used
# in emails.
site_url = "http://127.0.0.1:3000"
# The public URL that Auth serves on. Defaults to the API external URL with `/auth/v1` appended.
# external_url = ""
# A list of *exact* URLs that auth providers are permitted to redirect to post authentication.
additional_redirect_urls = ["https://127.0.0.1:3000"]
# How long tokens are valid for, in seconds. Defaults to 3600 (1 hour), maximum 604,800 (1 week).
jwt_expiry = 3600
# JWT issuer URL. If not set, defaults to auth.external_url.
# jwt_issuer = ""
# Path to JWT signing key. DO NOT commit your signing keys file to git.
# signing_keys_path = "./signing_keys.json"
# If disabled, the refresh token will never expire.
enable_refresh_token_rotation = true
# Allows refresh tokens to be reused after expiry, up to the specified interval in seconds.
# Requires enable_refresh_token_rotation = true.
refresh_token_reuse_interval = 10
# Allow/disallow new user signups to your project.
enable_signup = true
# Allow/disallow anonymous sign-ins to your project.
enable_anonymous_sign_ins = false
# Allow/disallow testing manual linking of accounts
enable_manual_linking = false
# Passwords shorter than this value will be rejected as weak. Minimum 6, recommended 8 or more.
minimum_password_length = 6
# Passwords that do not meet the following requirements will be rejected as weak. Supported values
# are: `letters_digits`, `lower_upper_letters_digits`, `lower_upper_letters_digits_symbols`
password_requirements = ""

# Configure passkey sign-ins.
# [auth.passkey]
# enabled = false

# Configure WebAuthn relying party settings (required when passkey is enabled).
# [auth.webauthn]
# rp_display_name = "Supabase"
# rp_id = "localhost"
# rp_origins = ["http://127.0.0.1:3000"]

[auth.rate_limit]
# Number of emails that can be sent per hour. Requires auth.email.smtp to be enabled.
email_sent = 2
# Number of SMS messages that can be sent per hour. Requires auth.sms to be enabled.
sms_sent = 30
# Number of anonymous sign-ins that can be made per hour per IP address. Requires enable_anonymous_sign_ins = true.
anonymous_users = 30
# Number of sessions that can be refreshed in a 5 minute interval per IP address.
token_refresh = 150
# Number of sign up and sign-in requests that can be made in a 5 minute interval per IP address (excludes anonymous users).
sign_in_sign_ups = 30
# Number of OTP / Magic link verifications that can be made in a 5 minute interval per IP address.
token_verifications = 30
# Number of Web3 logins that can be made in a 5 minute interval per IP address.
web3 = 30

# Configure one of the supported captcha providers: `hcaptcha`, `turnstile`.
# [auth.captcha]
# enabled = true
# provider = "hcaptcha"
# secret = ""

[auth.email]
# Allow/disallow new user signups via email to your project.
enable_signup = true
# If enabled, a user will be required to confirm any email change on both the old, and new email
# addresses. If disabled, only the new email is required to confirm.
double_confirm_changes = true
# If enabled, users need to confirm their email address before signing in.
enable_confirmations = false
# If enabled, users will need to reauthenticate or have logged in recently to change their password.
secure_password_change = false
# Controls the minimum amount of time that must pass before sending another signup confirmation or password reset email.
max_frequency = "1s"
# Number of characters used in the email OTP.
otp_length = 6
# Number of seconds before the email OTP expires (defaults to 1 hour).
otp_expiry = 3600

# Use a production-ready SMTP server
# [auth.email.smtp]
# enabled = true
# host = "smtp.sendgrid.net"
# port = 587
# user = "apikey"
# pass = "env(SENDGRID_API_KEY)"
# admin_email = "admin@email.com"
# sender_name = "Admin"

# Uncomment to customize email template
# [auth.email.template.invite]
# subject = "You have been invited"
# content_path = "./supabase/templates/invite.html"

# Uncomment to customize notification email template
# [auth.email.notification.password_changed]
# enabled = true
# subject = "Your password has been changed"
# content_path = "./templates/password_changed_notification.html"

[auth.sms]
# Allow/disallow new user signups via SMS to your project.
enable_signup = false
# If enabled, users need to confirm their phone number before signing in.
enable_confirmations = false
# Template for sending OTP to users
template = "Your code is {{ .Code }}"
# Controls the minimum amount of time that must pass before sending another sms otp.
max_frequency = "5s"

# Use pre-defined map of phone number to OTP for testing.
# [auth.sms.test_otp]
# 4152127777 = "123456"

# Configure logged in session timeouts.
# [auth.sessions]
# Force log out after the specified duration.
# timebox = "24h"
# Force log out if the user has been inactive longer than the specified duration.
# inactivity_timeout = "8h"

# This hook runs before a new user is created and allows developers to reject the request based on the incoming user object.
# [auth.hook.before_user_created]
# enabled = true
# uri = "pg-functions://postgres/auth/before-user-created-hook"

# This hook runs before a token is issued and allows you to add additional claims based on the authentication method used.
# [auth.hook.custom_access_token]
# enabled = true
# uri = "pg-functions://<database>/<schema>/<hook_name>"

# Configure one of the supported SMS providers: `twilio`, `twilio_verify`, `messagebird`, `textlocal`, `vonage`.
[auth.sms.twilio]
enabled = false
account_sid = ""
message_service_sid = ""
# DO NOT commit your Twilio auth token to git. Use environment variable substitution instead:
auth_token = "env(SUPABASE_AUTH_SMS_TWILIO_AUTH_TOKEN)"

# Multi-factor-authentication is available to Supabase Pro plan.
[auth.mfa]
# Control how many MFA factors can be enrolled at once per user.
max_enrolled_factors = 10

# Control MFA via App Authenticator (TOTP)
[auth.mfa.totp]
enroll_enabled = false
verify_enabled = false

# Configure MFA via Phone Messaging
[auth.mfa.phone]
enroll_enabled = false
verify_enabled = false
otp_length = 6
template = "Your code is {{ .Code }}"
max_frequency = "5s"

# Configure MFA via WebAuthn
# [auth.mfa.web_authn]
# enroll_enabled = true
# verify_enabled = true

# Use an external OAuth provider. The full list of providers are: `apple`, `azure`, `bitbucket`,
# `discord`, `facebook`, `github`, `gitlab`, `google`, `keycloak`, `linkedin_oidc`, `notion`, `twitch`,
# `twitter`, `x`, `slack`, `spotify`, `workos`, `zoom`.
[auth.external.apple]
enabled = false
client_id = ""
# DO NOT commit your OAuth provider secret to git. Use environment variable substitution instead:
secret = "env(SUPABASE_AUTH_EXTERNAL_APPLE_SECRET)"
# Overrides the default auth callback URL derived from auth.external_url.
redirect_uri = ""
# Overrides the default auth provider URL. Used to support self-hosted gitlab, single-tenant Azure,
# or any other third-party OIDC providers.
url = ""
# If enabled, the nonce check will be skipped. Required for local sign in with Google auth.
skip_nonce_check = false
# If enabled, it will allow the user to successfully authenticate when the provider does not return an email address.
email_optional = false

# Allow Solana wallet holders to sign in to your project via the Sign in with Solana (SIWS, EIP-4361) standard.
# You can configure "web3" rate limit in the [auth.rate_limit] section and set up [auth.captcha] if self-hosting.
[auth.web3.solana]
enabled = false

# Use Firebase Auth as a third-party provider alongside Supabase Auth.
[auth.third_party.firebase]
enabled = false
# project_id = "my-firebase-project"

# Use Auth0 as a third-party provider alongside Supabase Auth.
[auth.third_party.auth0]
enabled = false
# tenant = "my-auth0-tenant"
# tenant_region = "us"

# Use AWS Cognito (Amplify) as a third-party provider alongside Supabase Auth.
[auth.third_party.aws_cognito]
enabled = false
# user_pool_id = "my-user-pool-id"
# user_pool_region = "us-east-1"

# Use Clerk as a third-party provider alongside Supabase Auth.
[auth.third_party.clerk]
enabled = false
# Obtain from https://clerk.com/setup/supabase
# domain = "example.clerk.accounts.dev"

# OAuth server configuration
[auth.oauth_server]
# Enable OAuth server functionality
enabled = false
# Path for OAuth consent flow UI
authorization_url_path = "/oauth/consent"
# Allow dynamic client registration
allow_dynamic_registration = false

[edge_runtime]
enabled = true
# Supported request policies: `oneshot`, `per_worker`.
# `per_worker` (default) — enables hot reload during local development.
# `oneshot` — fallback mode if hot reload causes issues (e.g. in large repos or with symlinks).
policy = "per_worker"
# Port to attach the Chrome inspector for debugging edge functions.
inspector_port = 8083
# The Deno major version to use.
deno_version = 2

# [edge_runtime.secrets]
# secret_key = "env(SECRET_VALUE)"

[analytics]
enabled = true
port = 54327
# Configure one of the supported backends: `postgres`, `bigquery`.
backend = "postgres"

# Experimental features may be deprecated any time
[experimental]
# Configures Postgres storage engine to use OrioleDB (S3)
orioledb_version = ""
# Configures S3 bucket URL, eg. <bucket_name>.s3-<region>.amazonaws.com
s3_host = "env(S3_HOST)"
# Configures S3 bucket region, eg. us-east-1
s3_region = "env(S3_REGION)"
# Configures AWS_ACCESS_KEY_ID for S3 bucket
s3_access_key = "env(S3_ACCESS_KEY)"
# Configures AWS_SECRET_ACCESS_KEY for S3 bucket
s3_secret_key = "env(S3_SECRET_KEY)"

# pg-delta is the schema diff engine for db diff / db pull / db remote commit.
# Set enabled = false to fall back to the legacy migra engine.
[experimental.pgdelta]
enabled = true
# Directory under `supabase/` where declarative files are written.
# declarative_schema_path = "./database"
# JSON string passed through to pg-delta SQL formatting.
# format_options = "{\"keywordCase\":\"upper\",\"indent\":2,\"maxWidth\":80,\"commaStyle\":\"trailing\"}"
````

## File: ui/components/forms.py
````python
import flet as ft
from config import Config

def crear_input_estandar(label, icon=None, password=False, multiline=False, on_change=None):
    """
    Fábrica (Factory) para crear campos de texto estandarizados en toda la app.
    Cualquier cambio global en bordes, colores o tamaño se hace aquí y afecta todo el sistema.
    """
    return ft.TextField(
        label=label,
        prefix_icon=icon,
        password=password,
        multiline=multiline,
        on_change=on_change,
        border_radius=8,
        border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
        focused_border_color=Config.COLOR_PRIMARY,
        cursor_color=Config.COLOR_PRIMARY,
        text_size=14,
        content_padding=15
    )

def crear_boton_primario(text, icon=None, on_click=None):
    """
    Fábrica para botones primarios con el tema Azul Oscuro.
    """
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=Config.COLOR_PRIMARY,
            color="white",
            padding=ft.padding.symmetric(horizontal=20, vertical=15)
        )
    )
````

## File: ui/views/conteo_inicial.py
````python
import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
import datetime
from dateutil.relativedelta import relativedelta

class ConteoInicialView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        
        # State
        self.data_completa = []
        self.cambios_pendientes = {} # {codigo: nuevo_valor}
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        # Generar meses para el Dropdown
        hoy = datetime.date.today()
        opciones_meses = []
        for i in range(12): # Últimos 12 meses
            m = hoy - relativedelta(months=i)
            # Formato YYYY-MM
            val = m.strftime("%Y-%m")
            # Label bonito
            nombre_mes = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][m.month - 1]
            opciones_meses.append(ft.dropdown.Option(key=val, text=f"{nombre_mes} {m.year}"))
            
        self.mes_seleccionado = hoy.strftime("%Y-%m")
        
        # UI Filters
        self.search_input = ft.TextField(
            hint_text="Buscar código o insumo...",
            prefix_icon=ft.icons.SEARCH,
            border_radius=8,
            expand=True,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_filter_change
        )
        
        self.category_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            label="Categoría",
            width=200,
            border_radius=8,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_filter_change
        )
        
        self.month_dropdown = ft.Dropdown(
            options=opciones_meses,
            value=self.mes_seleccionado,
            label="Mes de Conteo",
            width=200,
            border_radius=8,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_month_change
        )
        
        # Tabla
        self.data_table = ft.DataTable(
            column_spacing=15,
            data_row_min_height=45,
            data_row_max_height=45,
            heading_row_height=40,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Categoría", weight="bold")),
                ft.DataColumn(ft.Text("Cierre Mes Ant.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Stock Inicial Reg.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Nuevo Conteo", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[]
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        
        # Bulk Action Bar
        self.btn_guardar_masivo = ft.ElevatedButton("Guardar Todos los Registros", bgcolor="green", color="white", on_click=self.guardar_masivo)
        self.action_bar = ft.Container(
            content=ft.Row([
                ft.Text("Tienes cambios pendientes por guardar", color="white", weight="bold"),
                ft.Container(expand=True),
                ft.OutlinedButton("Cancelar Todas las Ediciones", style=ft.ButtonStyle(color="white"), on_click=self.cancelar_masivo),
                self.btn_guardar_masivo
            ]),
            bgcolor=Config.COLOR_PRIMARY,
            padding=15,
            border_radius=10,
            visible=False,
            margin=ft.padding.only(top=10)
        )
        
        self.content = ft.Column([
            ft.Text("Conteo Inicial del Mes", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            
            # Filtros
            ft.Container(
                content=ft.Row([
                    self.search_input,
                    self.category_dropdown,
                    self.month_dropdown,
                    ft.IconButton(icon=ft.icons.REFRESH, on_click=self.on_month_change, tooltip="Recargar")
                ]),
                bgcolor="white",
                padding=10,
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            # Tabla
            ft.Container(
                content=ft.Column(
                    [self.data_table],
                    scroll=ft.ScrollMode.ALWAYS,
                    expand=True
                ),
                bgcolor="white",
                padding=5,
                border_radius=10,
                expand=True,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            # Footer Paginación
            ft.Container(
                content=ft.Row([
                    self.lbl_total,
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(top=10)
            ),
            
            self.action_bar
            
        ], expand=True, spacing=15)

    def did_mount(self):
        self.load_categories()
        self.load_data()
        
    def load_categories(self):
        cats = self.db.get_categorias()
        opts = [ft.dropdown.Option("Todas")]
        for c in cats:
            if c: opts.append(ft.dropdown.Option(c))
        self.category_dropdown.options = opts
        if self.page:
            self.update()
            
    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.cambios_pendientes.clear()
        self.current_page = 1
        self.load_data()
        
    def on_filter_change(self, e):
        self.current_page = 1
        self.render_table()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_table()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_table()
        
    def load_data(self):
        self.data_completa = self.db.get_datos_conteo_inicial(self.mes_seleccionado)
        self.render_table()
        
    def render_table(self):
        import math
        search_val = (self.search_input.value or "").lower()
        cat_val = self.category_dropdown.value or "Todas"
        
        self.data_table.rows.clear()
        
        filtered_data = []
        for item in self.data_completa:
            # Filtros
            nombre = str(item.get("nombre", "")).lower()
            codigo = str(item.get("codigo_insumo", "")).lower()
            categoria = str(item.get("categoria", ""))
            
            if search_val and search_val not in nombre and search_val not in codigo:
                continue
            if cat_val != "Todas" and cat_val != categoria:
                continue
                
            filtered_data.append(item)
            
        self.total_records = len(filtered_data)
        self.total_pages = math.ceil(self.total_records / self.page_size) if self.total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        
        page_data = filtered_data[start_idx:end_idx]
        
        for item in page_data:
            self.data_table.rows.append(self.crear_fila(item))
            
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros filtrados"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
            
        self.actualizar_action_bar()
        if self.page:
            self.update()
            
    def crear_fila(self, item):
        codigo = item["codigo_insumo"]
        cierre_ant = item["cierre_mes_anterior"]
        stock_ini = item["stock_inicial_actual"]
        
        input_conteo = ft.TextField(
            value=str(stock_ini),
            dense=True,
            width=80,
            text_size=13,
            content_padding=10,
            border_color=ft.colors.with_opacity(0.2, "black"),
            bgcolor="white"
        )
        
        acciones_container = ft.Row(visible=False, spacing=0)
        
        def on_change(e):
            val = input_conteo.value
            try:
                numeric_val = float(val) if '.' in val else int(val)
                if numeric_val != stock_ini:
                    self.cambios_pendientes[codigo] = numeric_val
                    acciones_container.visible = True
                else:
                    if codigo in self.cambios_pendientes:
                        del self.cambios_pendientes[codigo]
                    acciones_container.visible = False
            except ValueError:
                if codigo in self.cambios_pendientes:
                    del self.cambios_pendientes[codigo]
                acciones_container.visible = False
                
            e.control.update()
            acciones_container.update()
            self.actualizar_action_bar()
            
        input_conteo.on_change = on_change
        
        # Si ya había un cambio pendiente de antes (al buscar/filtrar)
        if codigo in self.cambios_pendientes:
            input_conteo.value = str(self.cambios_pendientes[codigo])
            acciones_container.visible = True
            
        def guardar_individual(e):
            if codigo in self.cambios_pendientes:
                val = self.cambios_pendientes[codigo]
                registro = {
                    "fecha_cierre": f"{self.mes_seleccionado}-01",
                    "codigo_insumo": codigo,
                    "tipo_registro": "INVENTARIO_INICIAL",
                    "cantidad_fisica": val,
                    "estado": "APLICADO"
                }
                exito = self.db.upsert_conteos_iniciales([registro])
                if exito:
                    item["stock_inicial_actual"] = val
                    del self.cambios_pendientes[codigo]
                    acciones_container.visible = False
                    self.page.snack_bar = ft.SnackBar(ft.Text("Guardado exitoso"), bgcolor="green")
                    self.page.snack_bar.open = True
                    self.render_table()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar"), bgcolor="red")
                    self.page.snack_bar.open = True
                    self.page.update()
                    
        def cancelar_individual(e):
            if codigo in self.cambios_pendientes:
                del self.cambios_pendientes[codigo]
            input_conteo.value = str(item["stock_inicial_actual"])
            acciones_container.visible = False
            input_conteo.update()
            acciones_container.update()
            self.actualizar_action_bar()
            
        acciones_container.controls = [
            ft.IconButton(ft.icons.CHECK, icon_color="green", tooltip="Guardar", on_click=guardar_individual),
            ft.IconButton(ft.icons.CLOSE, icon_color="red", tooltip="Descartar", on_click=cancelar_individual)
        ]
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(codigo)),
                ft.DataCell(ft.Container(content=ft.Text(item["nombre"], no_wrap=True, tooltip=item["nombre"]), width=150)),
                ft.DataCell(ft.Text(item["categoria"])),
                ft.DataCell(ft.Text(str(cierre_ant))),
                ft.DataCell(ft.Text(str(stock_ini), weight="bold")),
                ft.DataCell(input_conteo),
                ft.DataCell(acciones_container),
            ]
        )
        
    def actualizar_action_bar(self):
        if len(self.cambios_pendientes) > 1:
            self.action_bar.visible = True
        else:
            self.action_bar.visible = False
        if self.page:
            self.action_bar.update()
            
    def cancelar_masivo(self, e):
        self.cambios_pendientes.clear()
        self.render_table()
        
    def guardar_masivo(self, e):
        if not self.cambios_pendientes:
            return
            
        registros = []
        for codigo, val in self.cambios_pendientes.items():
            registros.append({
                "fecha_cierre": f"{self.mes_seleccionado}-01",
                "codigo_insumo": codigo,
                "tipo_registro": "INVENTARIO_INICIAL",
                "cantidad_fisica": val,
                "estado": "APLICADO"
            })
            
        exito = self.db.upsert_conteos_iniciales(registros)
        if exito:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Se guardaron {len(registros)} registros exitosamente"), bgcolor="green")
            self.cambios_pendientes.clear()
            self.load_data() # Recargar todo de BD para asegurar sincronía
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar registros masivos"), bgcolor="red")
            
        self.page.snack_bar.open = True
        self.page.update()
````

## File: .gitignore
````
# Entornos virtuales
venv/
env/
.env

# Archivos de caché y logs
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.log

# Archivos pesados o temporales
*.pdf
*.xlsx
*.csv
~$*.xlsx

# Configuración del IDE/Sistema
.vscode/
.idea/
.DS_Store
.kiro/
````

## File: append_methods.py
````python
with open('c:\\Users\\Home\\.gemini\\antigravity-ide\\scratch\\do-aMary\\core\\supabase_client.py', 'a', encoding='utf-8') as f:
    f.write('''
    def get_proyeccion_ventas(self) -> float:
        """Invoca RPC get_proyeccion_ventas_rpc"""
        url = f"{self.url}/rpc/get_proyeccion_ventas_rpc"
        try:
            res = self.session.post(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return float(data) if data is not None else 0.0
            return 0.0
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_proyeccion_ventas: el servidor no responde")
            return 0.0
        except Exception:
            return 0.0

    def get_ajustes_mes(self, mes_actual: str) -> list:
        """Invoca RPC get_ajustes_mes_rpc"""
        url = f"{self.url}/rpc/get_ajustes_mes_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else []
            return []
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_ajustes_mes: el servidor no responde")
            return []
        except Exception:
            return []
''')
````

## File: apply_closure_updates.py
````python
import os

# 1. Actualizar core/supabase_client.py
client_file = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\core\supabase_client.py'
with open(client_file, 'r', encoding='utf-8') as f:
    client_code = f.read()

new_methods = """
    def iniciar_snapshot_cierre(self, mes_periodo: str) -> dict:
        \"\"\"Invoca el RPC para generar el snapshot preliminar del mes.\"\"\"
        url = f"{self.url}/rpc/fn_snapshot_cierre_mensual"
        try:
            import requests
            res = requests.post(url, json={"p_mes": mes_periodo}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def obtener_estado_cierre(self, mes_periodo: str) -> dict:
        \"\"\"Obtiene el resumen y los insumos del período especificado.\"\"\"
        url = f"{self.url}/rpc/fn_obtener_estado_cierre"
        try:
            import requests
            res = requests.post(url, json={"p_mes": mes_periodo}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {}
        except Exception as e:
            print(f"Error en obtener_estado_cierre: {e}")
            return {}

    def registrar_conteo_fisico(self, id_auditoria: str, cantidad: float, costo: float = None, observacion: str = None) -> dict:
        \"\"\"Registra el conteo físico y genera ajustes si existe diferencia.\"\"\"
        url = f"{self.url}/rpc/fn_registrar_conteo_fisico"
        payload = {
            "p_id_auditoria": id_auditoria,
            "p_cantidad_fisica": cantidad
        }
        if costo is not None:
            payload["p_costo_ajuste"] = costo
        if observacion:
            payload["p_observacion"] = observacion
            
        try:
            import requests
            res = requests.post(url, json=payload, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aceptar_stock_sistema(self, id_auditoria: str) -> dict:
        \"\"\"Acepta el stock calculado por el sistema sin conteo físico.\"\"\"
        url = f"{self.url}/rpc/fn_aceptar_stock_sistema"
        try:
            import requests
            res = requests.post(url, json={"p_id_auditoria": id_auditoria}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aprobar_cierre_mes(self, id_periodo: str, aprobado_por: str) -> dict:
        \"\"\"Cierra el período y consolida el inventario inicial del mes siguiente.\"\"\"
        url = f"{self.url}/rpc/fn_aprobar_cierre_mes"
        try:
            import requests
            res = requests.post(url, json={"p_id_periodo": id_periodo, "p_aprobado_por": aprobado_por}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}
"""

if "def iniciar_snapshot_cierre" not in client_code:
    client_code += new_methods
    with open(client_file, 'w', encoding='utf-8') as f:
        f.write(client_code)


# 2. Crear ui/views/cierre_inventario.py
view_file = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
view_code = """import flet as ft
from config import Config
from core.supabase_client import SupabaseClient
import datetime
from dateutil.relativedelta import relativedelta

class CierreInventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        self.datos_cierre = {}
        
        # Opciones de Meses
        hoy = datetime.date.today()
        opciones_meses = []
        for i in range(12):
            m = hoy - relativedelta(months=i)
            val = m.strftime("%Y-%m")
            nombre_mes = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][m.month - 1]
            opciones_meses.append(ft.dropdown.Option(key=val, text=f"{nombre_mes} {m.year}"))
            
        self.mes_seleccionado = hoy.strftime("%Y-%m")
        
        # Controles Superiores
        self.month_dropdown = ft.Dropdown(
            options=opciones_meses,
            value=self.mes_seleccionado,
            label="Período de Auditoría",
            width=200,
            border_radius=8,
            height=40,
            on_change=self.on_month_change
        )
        
        self.btn_iniciar_snapshot = ft.ElevatedButton(
            text="Generar Snapshot Preliminar",
            icon=ft.icons.CAMERA_ALT,
            bgcolor=Config.COLOR_SECONDARY,
            color="white",
            on_click=self.on_generar_snapshot
        )
        
        self.btn_aprobar_cierre = ft.ElevatedButton(
            text="Aprobar Cierre Definitivo",
            icon=ft.icons.CHECK_CIRCLE,
            bgcolor="green",
            color="white",
            disabled=True,
            on_click=self.on_aprobar_cierre
        )

        # Indicadores de Estado
        self.txt_estado_periodo = ft.Text("Estado: DESCONOCIDO", weight="bold")
        self.txt_progreso = ft.Text("Pendientes: 0 | Auditados: 0", color="grey")

        # Tabla de Auditoría
        self.data_table = ft.DataTable(
            column_spacing=15,
            data_row_min_height=50,
            data_row_max_height=50,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Stock Sist.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Físico", weight="bold")),
                ft.DataColumn(ft.Text("Diferencia", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acción", weight="bold")),
            ],
            rows=[]
        )

        self.content = ft.Column([
            ft.Text("Auditoría y Cierre de Período", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Container(
                content=ft.Row([
                    self.month_dropdown,
                    self.btn_iniciar_snapshot,
                    ft.Container(expand=True),
                    ft.Column([self.txt_estado_periodo, self.txt_progreso], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                    self.btn_aprobar_cierre
                ]),
                padding=15,
                bgcolor="white",
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            ft.Container(
                content=ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS, expand=True),
                bgcolor="white",
                padding=5,
                border_radius=10,
                expand=True,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
            )
        ], expand=True, spacing=15)

    def did_mount(self):
        self.load_data()

    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.load_data()

    def on_generar_snapshot(self, e):
        res = self.db.iniciar_snapshot_cierre(self.mes_seleccionado)
        if res.get("exito"):
            self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error', 'Desconocido')}"), bgcolor="red")
        self.page.snack_bar.open = True
        self.page.update()

    def on_aprobar_cierre(self, e):
        id_periodo = self.datos_cierre.get("periodo", {}).get("id_periodo")
        if not id_periodo:
            return
            
        res = self.db.aprobar_cierre_mes(id_periodo, "Administrador Sistema")
        if res.get("exito"):
            self.page.snack_bar = ft.SnackBar(ft.Text("Período cerrado y consolidado con éxito."), bgcolor="green")
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error', 'Desconocido')}"), bgcolor="red")
        self.page.snack_bar.open = True
        self.page.update()

    def load_data(self):
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.render_view()

    def render_view(self):
        self.data_table.rows.clear()
        
        if not self.datos_cierre or not self.datos_cierre.get("periodo"):
            self.txt_estado_periodo.value = "Estado: NO INICIALIZADO"
            self.txt_estado_periodo.color = "grey"
            self.txt_progreso.value = "Requiere generar snapshot"
            self.btn_iniciar_snapshot.disabled = False
            self.btn_aprobar_cierre.disabled = True
            if self.page: self.update()
            return

        periodo = self.datos_cierre["periodo"]
        resumen = self.datos_cierre.get("resumen", {})
        insumos = self.datos_cierre.get("insumos", [])

        estado_periodo = periodo.get("estado", "DESCONOCIDO")
        self.txt_estado_periodo.value = f"Estado: {estado_periodo}"
        
        color_estado = {"ABIERTO": "green", "PRELIMINAR": "orange", "EN_AUDITORIA": "blue", "CERRADO": "red"}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, "black")
        
        pendientes = resumen.get("pendientes", 0)
        self.txt_progreso.value = f"Pendientes: {pendientes} | Listos: {resumen.get('auditados', 0) + resumen.get('ajustados', 0)}"

        self.btn_iniciar_snapshot.disabled = estado_periodo in ["CERRADO", "PRELIMINAR", "EN_AUDITORIA"]
        self.btn_aprobar_cierre.disabled = estado_periodo == "CERRADO" or pendientes > 0

        for insumo in insumos:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))

        if self.page:
            self.update()

    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo["id_auditoria"]
        estado_insumo = insumo["estado"]
        cant_sistema = insumo["cantidad_sistema"]
        cant_fisica = insumo.get("cantidad_fisica")
        
        # Campo para ingresar conteo físico
        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else "",
            dense=True, width=80, text_size=13, content_padding=10,
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO")
        )

        btn_aceptar_sistema = ft.IconButton(
            icon=ft.icons.CHECK_BOX,
            icon_color="green",
            tooltip="Aceptar Stock del Sistema",
            disabled=(estado_periodo == "CERRADO" or estado_insumo != "PENDIENTE"),
            on_click=lambda e: self.procesar_aceptar_sistema(id_auditoria)
        )

        btn_guardar_conteo = ft.IconButton(
            icon=ft.icons.SAVE,
            icon_color="blue",
            tooltip="Guardar Conteo Físico",
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO"),
            on_click=lambda e: self.procesar_guardar_conteo(id_auditoria, txt_conteo.value)
        )

        acciones = ft.Row([btn_aceptar_sistema, btn_guardar_conteo], spacing=0)

        color_diferencia = "red" if insumo.get("diferencia", 0) != 0 else "black"

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(insumo["codigo_insumo"])),
                ft.DataCell(ft.Text(insumo["nombre"], width=200, no_wrap=True, tooltip=insumo["nombre"])),
                ft.DataCell(ft.Text(str(cant_sistema), weight="bold")),
                ft.DataCell(txt_conteo),
                ft.DataCell(ft.Text(str(insumo.get("diferencia", "")), color=color_diferencia)),
                ft.DataCell(ft.Text(estado_insumo, size=11, weight="bold", color="grey")),
                ft.DataCell(acciones),
            ]
        )

    def procesar_aceptar_sistema(self, id_auditoria):
        res = self.db.aceptar_stock_sistema(id_auditoria)
        if res.get("exito"):
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error')}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()

    def procesar_guardar_conteo(self, id_auditoria, valor_texto):
        try:
            cantidad = float(valor_texto)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Ingrese un valor numérico válido."), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return

        res = self.db.registrar_conteo_fisico(id_auditoria, cantidad)
        if res.get("exito"):
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error')}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
"""

with open(view_file, 'w', encoding='utf-8') as f:
    f.write(view_code)

print("Update script finished.")
````

## File: cargas_compras_locales.json
````json
{
    "2026-08-03": {
        "1": {
            "id": 1,
            "fecha": "2026-08-03",
            "pagina": 1,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-03_pag_1.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9273",
                    "numero_factura": "7957448",
                    "productos": [
                        {
                            "cantidad": 200.0,
                            "codigo_insumo": "0578",
                            "costo_unitario": 328.0,
                            "iva": 12464.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9274",
                    "numero_factura": "0174",
                    "productos": [
                        {
                            "cantidad": 16.5,
                            "codigo_insumo": "1347",
                            "costo_unitario": 13100.0,
                            "iva": 41069.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9275",
                    "numero_factura": "040826",
                    "productos": [
                        {
                            "cantidad": 145.0,
                            "codigo_insumo": "1893",
                            "costo_unitario": 1933.0,
                            "iva": 53248.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9276",
                    "numero_factura": "19284",
                    "productos": [
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "0471",
                            "costo_unitario": 7353.0,
                            "iva": 13971.0
                        },
                        {
                            "cantidad": 50.0,
                            "codigo_insumo": "4182",
                            "costo_unitario": 2815.0,
                            "iva": 26744.0
                        },
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "9104",
                            "costo_unitario": 5252.0,
                            "iva": 9979.0
                        },
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "9104",
                            "costo_unitario": 5252.0,
                            "iva": 9979.0
                        },
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "9104",
                            "costo_unitario": 5252.0,
                            "iva": 9979.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9277",
                    "numero_factura": "639921",
                    "productos": [
                        {
                            "cantidad": 4000.0,
                            "codigo_insumo": "0581",
                            "costo_unitario": 296.0,
                            "iva": 224960.0
                        },
                        {
                            "cantidad": 10000.0,
                            "codigo_insumo": "0572",
                            "costo_unitario": 180.0,
                            "iva": 341617.0
                        },
                        {
                            "cantidad": 4000.0,
                            "codigo_insumo": "0573",
                            "costo_unitario": 296.0,
                            "iva": 224960.0
                        },
                        {
                            "cantidad": 60.0,
                            "codigo_insumo": "1514",
                            "costo_unitario": 3643.0,
                            "iva": 41531.0
                        },
                        {
                            "cantidad": 60.0,
                            "codigo_insumo": "1164",
                            "costo_unitario": 6056.0,
                            "iva": 0.0
                        },
                        {
                            "cantidad": 180.0,
                            "codigo_insumo": "0855",
                            "costo_unitario": 1555.0,
                            "iva": 53168.0
                        },
                        {
                            "cantidad": 36.0,
                            "codigo_insumo": "2206",
                            "costo_unitario": 3536.0,
                            "iva": 24186.0
                        },
                        {
                            "cantidad": 370.0,
                            "codigo_insumo": "0847",
                            "costo_unitario": 2269.0,
                            "iva": 159504.0
                        },
                        {
                            "cantidad": 148.0,
                            "codigo_insumo": "0848",
                            "costo_unitario": 2563.0,
                            "iva": 72072.0
                        },
                        {
                            "cantidad": 80.0,
                            "codigo_insumo": "0688",
                            "costo_unitario": 2643.0,
                            "iva": 40168.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9278",
                    "numero_factura": "639914",
                    "productos": [
                        {
                            "cantidad": 600.0,
                            "codigo_insumo": "2152",
                            "costo_unitario": 1311.0,
                            "iva": 149503.0
                        },
                        {
                            "cantidad": 180.0,
                            "codigo_insumo": "0855",
                            "costo_unitario": 1487.0,
                            "iva": 50869.0
                        },
                        {
                            "cantidad": 185.0,
                            "codigo_insumo": "0847",
                            "costo_unitario": 2227.0,
                            "iva": 78275.0
                        }
                    ]
                }
            ]
        },
        "2": {
            "id": 2,
            "fecha": "2026-08-03",
            "pagina": 2,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-03_pag_2.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "numero_entrada": "EA-9279",
                    "numero_factura": "260803",
                    "productos": [
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "1415",
                            "costo_unitario": 6955.0,
                            "iva": 13214.0
                        },
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "0156",
                            "costo_unitario": 3803.0,
                            "iva": 7225.0
                        },
                        {
                            "cantidad": 10.0,
                            "codigo_insumo": "0157",
                            "costo_unitario": 4565.0,
                            "iva": 8674.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9280",
                    "numero_factura": "22618",
                    "productos": [
                        {
                            "cantidad": 40.0,
                            "codigo_insumo": "1850",
                            "costo_unitario": 5462.0,
                            "iva": 41513.0
                        },
                        {
                            "cantidad": 24.0,
                            "codigo_insumo": "4223",
                            "costo_unitario": 588.0,
                            "iva": 2682.0
                        },
                        {
                            "cantidad": 36.0,
                            "codigo_insumo": "1843",
                            "costo_unitario": 2773.0,
                            "iva": 18968.0
                        },
                        {
                            "cantidad": 150.0,
                            "codigo_insumo": "0663",
                            "costo_unitario": 4958.0,
                            "iva": 141303.0
                        },
                        {
                            "cantidad": 12.0,
                            "codigo_insumo": "1115",
                            "costo_unitario": 5798.0,
                            "iva": 13220.0
                        },
                        {
                            "cantidad": 12.0,
                            "codigo_insumo": "4206",
                            "costo_unitario": 5420.0,
                            "iva": 12358.0
                        },
                        {
                            "cantidad": 100.0,
                            "codigo_insumo": "1517",
                            "costo_unitario": 13866.0,
                            "iva": 263445.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-04",
                    "numero_entrada": "EA-9281",
                    "numero_factura": "41142",
                    "productos": [
                        {
                            "cantidad": 400.0,
                            "codigo_insumo": "4815",
                            "costo_unitario": 485.0,
                            "iva": 36860.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-04",
                    "numero_entrada": "EA-9282",
                    "numero_factura": "90042",
                    "productos": [
                        {
                            "cantidad": 300.0,
                            "codigo_insumo": "2256",
                            "costo_unitario": 787.0,
                            "iva": 44882.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-04",
                    "numero_entrada": "EA-9283",
                    "numero_factura": "25260",
                    "productos": [
                        {
                            "cantidad": 3.0,
                            "codigo_insumo": "1230",
                            "costo_unitario": 27731.0,
                            "iva": 15807.0
                        },
                        {
                            "cantidad": 12.0,
                            "codigo_insumo": "0462",
                            "costo_unitario": 15408.0,
                            "iva": 35130.0
                        },
                        {
                            "cantidad": 12.0,
                            "codigo_insumo": "0457",
                            "costo_unitario": 6060.0,
                            "iva": 13817.0
                        },
                        {
                            "cantidad": 12.0,
                            "codigo_insumo": "0458",
                            "costo_unitario": 7579.0,
                            "iva": 17280.0
                        },
                        {
                            "cantidad": 12.0,
                            "codigo_insumo": "0459",
                            "costo_unitario": 11026.0,
                            "iva": 25139.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-05",
                    "numero_entrada": "EA-9284",
                    "numero_factura": "68829",
                    "productos": [
                        {
                            "cantidad": 90.0,
                            "codigo_insumo": "0024",
                            "costo_unitario": 6133.0,
                            "iva": 104870.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-05",
                    "numero_entrada": "EA-9285",
                    "numero_factura": "90196",
                    "productos": [
                        {
                            "cantidad": 25.0,
                            "codigo_insumo": "0817",
                            "costo_unitario": 2857.0,
                            "iva": 13571.0
                        },
                        {
                            "cantidad": 20.0,
                            "codigo_insumo": "2258",
                            "costo_unitario": 3315.0,
                            "iva": 12597.0
                        }
                    ]
                },
                {
                    "fecha": "2026-08-05",
                    "numero_entrada": "EA-9286",
                    "numero_factura": "15400",
                    "productos": []
                }
            ]
        },
        "3": {
            "id": 3,
            "fecha": "2026-08-03",
            "pagina": 3,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-03_pag_3.pdf",
            "estado": "Nuevo"
        }
    }
}
````

## File: check_db.py
````python
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
````

## File: generate_schema_from_md.py
````python
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
````

## File: generate_schema.py
````python
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
````

## File: import_excel.py
````python
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
````

## File: openapi.json
````json
{"code": "PGRST125", "details": null, "hint": null, "message": "Invalid path specified in request URL"}
````

## File: patch_costs.py
````python
import os

file_client = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\core\supabase_client.py'
with open(file_client, 'r', encoding='utf-8') as f:
    content = f.read()

new_method = """
    def get_catalogo_costos(self) -> dict:
        \"\"\"Obtiene un diccionario con los costos actuales del catálogo de insumos\"\"\"
        url = f"{self.url}/catalogo_insumos?select=codigo_insumo,costo_unitario"
        try:
            import requests
            res = requests.get(url, headers=self.headers)
            if res.status_code == 200:
                return {item.get('codigo_insumo'): float(item.get('costo_unitario') or 0) for item in res.json()}
        except Exception as e:
            print(f"Error get_catalogo_costos: {e}")
        return {}
"""
with open(file_client, 'a', encoding='utf-8') as f:
    f.write(new_method)

file_view = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(file_view, 'r', encoding='utf-8') as f:
    content = f.read()

target = """    def load_data(self):
        import math
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.insumos_lista = self.datos_cierre.get("insumos", [])"""

repl = """    def load_data(self):
        import math
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.insumos_lista = self.datos_cierre.get("insumos", [])
        
        # Recuperar fallback de costos para los insumos que no tienen costo_unitario_snapshot
        costos_fallback = self.db.get_catalogo_costos()
        for ins in self.insumos_lista:
            if not ins.get("costo_unitario_snapshot"):
                ins["costo_unitario_snapshot"] = costos_fallback.get(ins.get("codigo_insumo"), 0)"""

content = content.replace(target, repl)

with open(file_view, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
````

## File: refactor_cierre.py
````python
import os

file_path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Variables de Paginación Interna
part1_target = """        self.datos_cierre = {}"""
part1_repl = """        self.datos_cierre = {}
        
        # Variables de Paginación Interna
        self.page_size = 50
        self.current_page = 1
        self.total_pages = 1
        self.insumos_lista = []"""
content = content.replace(part1_target, part1_repl)


# 2. Controles de Paginación Interfaz
part2_target = """        self.content = ft.Column(["""
part2_repl = """        # Controles Paginación Interfaz
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)

        self.content = ft.Column(["""
content = content.replace(part2_target, part2_repl)


# 3. Footer de paginación
part3_target = """        ], expand=True, spacing=15)"""
part3_repl = """        ], expand=True, spacing=15)
        
        self.content.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.only(top=10)
            )
        )"""
content = content.replace(part3_target, part3_repl)


# 4. Métodos on_month_change y on_generar_snapshot
part4_target = """    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.load_data()

    def on_generar_snapshot(self, e):
        res = self.db.iniciar_snapshot_cierre(self.mes_seleccionado)
        if res.get("exito"):
            self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error', 'Desconocido')}"), bgcolor="red")
        self.page.snack_bar.open = True
        self.page.update()"""

part4_repl = """    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_view()

    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_view()

    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.current_page = 1
        self.load_data()

    def on_generar_snapshot(self, e):
        res = self.db.iniciar_snapshot_cierre(self.mes_seleccionado)
        if res.get("exito"):
            self.page.snack_bar = ft.SnackBar(ft.Text("Snapshot generado correctamente."), bgcolor="green")
            self.current_page = 1
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error', 'Desconocido')}"), bgcolor="red")
        self.page.snack_bar.open = True
        self.page.update()"""
content = content.replace(part4_target, part4_repl)


# 5. Métodos load_data y render_view
part5_target = """    def load_data(self):
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.render_view()

    def render_view(self):
        self.data_table.rows.clear()
        
        if not self.datos_cierre or not self.datos_cierre.get("periodo"):
            self.txt_estado_periodo.value = "Estado: NO INICIALIZADO"
            self.txt_estado_periodo.color = "grey"
            self.txt_progreso.value = "Requiere generar snapshot"
            self.btn_iniciar_snapshot.disabled = False
            self.btn_aprobar_cierre.disabled = True
            if self.page: self.update()
            return

        periodo = self.datos_cierre["periodo"]
        resumen = self.datos_cierre.get("resumen", {})
        insumos = self.datos_cierre.get("insumos", [])

        estado_periodo = periodo.get("estado", "DESCONOCIDO")
        self.txt_estado_periodo.value = f"Estado: {estado_periodo}"
        
        color_estado = {"ABIERTO": "green", "PRELIMINAR": "orange", "EN_AUDITORIA": "blue", "CERRADO": "red"}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, "black")
        
        pendientes = resumen.get("pendientes", 0)
        self.txt_progreso.value = f"Pendientes: {pendientes} | Listos: {resumen.get('auditados', 0) + resumen.get('ajustados', 0)}"

        self.btn_iniciar_snapshot.disabled = estado_periodo in ["CERRADO", "PRELIMINAR", "EN_AUDITORIA"]
        self.btn_aprobar_cierre.disabled = estado_periodo == "CERRADO" or pendientes > 0

        for insumo in insumos:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))

        if self.page:
            self.update()"""

part5_repl = """    def load_data(self):
        import math
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado)
        self.insumos_lista = self.datos_cierre.get("insumos", [])
        
        # Calcular total de páginas
        total_records = len(self.insumos_lista)
        self.total_pages = math.ceil(total_records / self.page_size) if total_records > 0 else 1
        
        # Prevención de desbordamiento de índice
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        self.render_view()

    def render_view(self):
        self.data_table.rows.clear()
        
        if not self.datos_cierre or not self.datos_cierre.get("periodo"):
            self.txt_estado_periodo.value = "Estado: NO INICIALIZADO"
            self.txt_estado_periodo.color = "grey"
            self.txt_progreso.value = "Requiere generar snapshot"
            self.btn_iniciar_snapshot.disabled = False
            self.btn_aprobar_cierre.disabled = True
            if self.page: self.update()
            return

        periodo = self.datos_cierre["periodo"]
        resumen = self.datos_cierre.get("resumen", {})

        estado_periodo = periodo.get("estado", "DESCONOCIDO")
        self.txt_estado_periodo.value = f"Estado: {estado_periodo}"
        
        color_estado = {"ABIERTO": "green", "PRELIMINAR": "orange", "EN_AUDITORIA": "blue", "CERRADO": "red"}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, "black")
        
        pendientes = resumen.get("pendientes", 0)
        listos = resumen.get('auditados', 0) + resumen.get('ajustados', 0)
        self.txt_progreso.value = f"Pendientes: {pendientes} | Listos: {listos}"

        self.btn_iniciar_snapshot.disabled = estado_periodo in ["CERRADO", "PRELIMINAR", "EN_AUDITORIA"]
        self.btn_aprobar_cierre.disabled = estado_periodo == "CERRADO" or pendientes > 0

        # Lógica de segmentación para renderizado (Paginación O(N) optimizada)
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.insumos_lista[start_idx:end_idx]

        for insumo in page_data:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))

        # Actualizar UI de botones de paginación
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)

        if self.page:
            self.update()"""
            
content = content.replace(part5_target, part5_repl)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactor finished successfully.")
````

## File: refactor_kpi.py
````python
import os

file_path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()


# 1. Agregar helper de tarjeta (al inicio de los métodos o en __init__)
# Agregaremos _crear_kpi_card justo encima de did_mount

target1 = "    def did_mount(self):"
repl1 = """    def _crear_kpi_card(self, title, lbl_val, icon, lbl_sub=None):
        col_controls = [ft.Text(title, size=11, color="grey", weight="bold"), lbl_val]
        if lbl_sub: col_controls.append(lbl_sub)
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=Config.COLOR_SECONDARY, size=24),
                ft.Column(col_controls, spacing=0)
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor="white", padding=15, border_radius=8, expand=True,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
        )

    def did_mount(self):"""
content = content.replace(target1, repl1)


# 2. Inicializar los Controles del Resumen Financiero en __init__
# Buscamos self.content = ft.Column([
target2 = """        self.content = ft.Column(["""
repl2 = """        # Controles Dashboard Financiero
        self.lbl_valor_sistema = ft.Text("$0.00", size=16, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_ajustes_entrada = ft.Text("$0.00", size=16, weight="bold", color="green")
        self.lbl_cant_entrada = ft.Text("0 unds", size=10, color="grey")
        self.lbl_ajustes_salida = ft.Text("$0.00", size=16, weight="bold", color="red")
        self.lbl_cant_salida = ft.Text("0 unds", size=10, color="grey")
        self.lbl_neto_ajustes = ft.Text("$0.00", size=16, weight="bold")
        self.lbl_valor_fisico = ft.Text("$0.00", size=18, weight="bold", color=Config.COLOR_SECONDARY)
        
        self.summary_container = ft.Row([
            self._crear_kpi_card("Valor Sist.", self.lbl_valor_sistema, ft.icons.COMPUTER),
            self._crear_kpi_card("Sobrantes (+)", self.lbl_ajustes_entrada, ft.icons.ADD_CIRCLE_OUTLINE, self.lbl_cant_entrada),
            self._crear_kpi_card("Faltantes (-)", self.lbl_ajustes_salida, ft.icons.REMOVE_CIRCLE_OUTLINE, self.lbl_cant_salida),
            self._crear_kpi_card("Neto Ajustes", self.lbl_neto_ajustes, ft.icons.ACCOUNT_BALANCE_WALLET),
            self._crear_kpi_card("Valor Físico Proyectado", self.lbl_valor_fisico, ft.icons.FACT_CHECK)
        ], spacing=10)

        self.content = ft.Column(["""
content = content.replace(target2, repl2)


# Y luego agregamos self.summary_container a self.content
target2b = """            ft.Text("Auditoría y Cierre de Período", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Container("""
repl2b = """            ft.Text("Auditoría y Cierre de Período", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            self.summary_container,
            ft.Container("""
content = content.replace(target2b, repl2b)


# 3. Lógica matemática en render_view
target3 = """        # Lógica de segmentación para renderizado (Paginación O(N) optimizada)"""
repl3 = """        # --- Cálculo de KPIs Financieros Globales ---
        valor_sistema = 0.0
        valor_entrada = 0.0
        cant_entrada = 0.0
        valor_salida = 0.0
        cant_salida = 0.0

        for ins = self.insumos_lista:
            cant_sist = float(ins.get("cantidad_sistema") or 0)
            costo_u = float(ins.get("costo_unitario_snapshot") or 0)
            dif = ins.get("diferencia")

            valor_sistema += (cant_sist * costo_u)

            if dif is not None:
                dif_flt = float(dif)
                if dif_flt > 0:
                    valor_entrada += (dif_flt * costo_u)
                    cant_entrada += dif_flt
                elif dif_flt < 0:
                    valor_salida += (abs(dif_flt) * costo_u)
                    cant_salida += abs(dif_flt)

        valor_neto = valor_entrada - valor_salida
        valor_fisico = valor_sistema + valor_neto

        self.lbl_valor_sistema.value = f"${valor_sistema:,.2f}"
        self.lbl_ajustes_entrada.value = f"${valor_entrada:,.2f}"
        self.lbl_cant_entrada.value = f"+{cant_entrada:g} unds"
        self.lbl_ajustes_salida.value = f"${valor_salida:,.2f}"
        self.lbl_cant_salida.value = f"-{cant_salida:g} unds"
        self.lbl_neto_ajustes.value = f"${valor_neto:,.2f}"
        self.lbl_neto_ajustes.color = "green" if valor_neto >= 0 else "red"
        self.lbl_valor_fisico.value = f"${valor_fisico:,.2f}"
        # ---------------------------------------------

        # Lógica de segmentación para renderizado (Paginación O(N) optimizada)"""
content = content.replace(target3, repl3)


# 4. Reemplazar crear_fila_auditoria (y eliminar lo de costo_unit antiguo)
# Como la función llega hasta toggle_edit, lo usaremos para encontrar el final
target4_and_beyond = content[content.find("    def crear_fila_auditoria(self, insumo, estado_periodo):"):content.find("    def toggle_edit(self, e, insumo, row_ref):")]

repl4 = """    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo["id_auditoria"]
        estado_insumo = insumo["estado"]
        cant_sistema = insumo["cantidad_sistema"]
        cant_fisica = insumo.get("cantidad_fisica")
        diferencia = insumo.get("diferencia")
        observacion = insumo.get("observacion") or ""
        categoria = insumo.get("categoria") or ""
        
        costo_unit = float(insumo.get("costo_unitario_snapshot") or 0)
        
        # Corrección del texto "None" y cálculo riguroso del Costo Ajuste
        str_dif = ""
        str_costo_ajuste = ""
        color_diferencia = "black"

        if diferencia is not None:
            dif_flt = float(diferencia)
            str_dif = f"{dif_flt:g}"
            if dif_flt != 0:
                color_diferencia = "red"
                str_costo_ajuste = f"${(abs(dif_flt) * costo_unit):,.2f}"
        
        row_ref = ft.DataRow(cells=[])
        
        checkbox = ft.Checkbox(
            value=False, 
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO"),
            on_change=lambda e, i=insumo, r=row_ref: self.toggle_edit(e, i, r)
        )

        row_ref.cells = [
            ft.DataCell(ft.Container(content=checkbox, width=25, alignment=ft.alignment.center)),
            ft.DataCell(ft.Text(insumo["codigo_insumo"])),
            ft.DataCell(ft.Text(insumo["nombre"], width=180, no_wrap=True, tooltip=insumo["nombre"])),
            ft.DataCell(ft.Text(categoria, width=100, no_wrap=True, tooltip=categoria)),
            ft.DataCell(ft.Text(str(cant_sistema), weight="bold")),
            ft.DataCell(ft.Text(str(cant_fisica) if cant_fisica is not None else "")),
            ft.DataCell(ft.Text(str_dif, color=color_diferencia)),
            ft.DataCell(ft.Text(str_costo_ajuste)),
            ft.DataCell(ft.Text(observacion, width=150, no_wrap=True, tooltip=observacion)),
            ft.DataCell(ft.Text(estado_insumo, size=11, weight="bold", color="grey")),
        ]
        return row_ref

"""
content = content.replace(target4_and_beyond, repl4)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("KPI Panel refactor script finished.")
````

## File: refactor_panel.py
````python
import os

file_path = r'c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\cierre_inventario.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Corrección del Dropdown de Período
target1 = """    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.current_page = 1
        self.load_data()"""
repl1 = """    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.month_dropdown.update()
        self.current_page = 1
        self.load_data()"""
content = content.replace(target1, repl1)

# 2. Actualización de las Columnas del DataTable
target2 = """            columns=[
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Stock Sist.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Físico", weight="bold")),
                ft.DataColumn(ft.Text("Diferencia", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acción", weight="bold")),
            ],"""
repl2 = """            columns=[
                ft.DataColumn(ft.Container(width=25)), # Checkbox
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Text("Insumo", weight="bold")),
                ft.DataColumn(ft.Text("Categoría", weight="bold")),
                ft.DataColumn(ft.Text("Stock Sist.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Físico", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Diferencia", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Ajuste", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Observación", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
            ],"""
content = content.replace(target2, repl2)

# 3. Construcción del Panel Inferior Reactivo
target3 = """        # Controles Paginación Interfaz
        self.lbl_page_info = ft.Text("Página 1 de 1")"""
repl3 = """        self.current_edit_context = None
        
        # Controles del Panel de Edición
        self.edit_panel_title = ft.Text("Editando Insumo...", color="white", weight="bold", size=16)
        
        input_style = {"text_size": 13, "height": 40, "content_padding": 10, "bgcolor": "white", "color": "black", "border_color": ft.colors.with_opacity(0.3, "white")}
        
        self.edit_fisico = ft.TextField(label="Stock Físico", width=100, **input_style)
        self.edit_costo = ft.TextField(label="Costo Unitario", width=120, **input_style)
        self.edit_observacion = ft.TextField(label="Observación / Justificación", width=250, **input_style)
        
        self.lbl_diferencia = ft.Text("Dif: 0", color="white", weight="bold")
        self.lbl_tipo_ajuste = ft.Text("Tipo: N/A", color="white")
        self.lbl_costo_total = ft.Text("Total: $0", color="white", weight="bold")

        def calcular_totales_panel(e):
            if not self.current_edit_context: return
            try:
                stock_sist = float(self.current_edit_context['item']['cantidad_sistema'])
                fisico = float(self.edit_fisico.value) if self.edit_fisico.value else stock_sist
                costo_u = float(self.edit_costo.value) if self.edit_costo.value else 0.0
                
                diferencia = fisico - stock_sist
                costo_total = abs(diferencia) * costo_u
                
                self.lbl_diferencia.value = f"Dif: {diferencia:g}"
                self.lbl_diferencia.color = "red300" if diferencia != 0 else "white"
                
                if diferencia > 0:
                    self.lbl_tipo_ajuste.value = "Tipo: AJUSTE_ENTRADA"
                elif diferencia < 0:
                    self.lbl_tipo_ajuste.value = "Tipo: AJUSTE_SALIDA"
                else:
                    self.lbl_tipo_ajuste.value = "Tipo: NINGUNO"
                    
                self.lbl_costo_total.value = f"Total: ${costo_total:,.2f}"
            except ValueError:
                self.lbl_diferencia.value = "Dif: Error"
                self.lbl_costo_total.value = "Total: Error"
            self.action_bar.update()

        self.edit_fisico.on_change = calcular_totales_panel
        self.edit_costo.on_change = calcular_totales_panel

        self.btn_guardar_edicion = ft.ElevatedButton("Guardar Conteo", bgcolor="green", color="white", on_click=self.on_guardar_conteo_panel)
        
        self.action_bar = ft.Container(
            content=ft.Column([
                self.edit_panel_title,
                ft.Row([
                    self.edit_fisico,
                    self.edit_costo,
                    self.edit_observacion,
                    ft.Container(width=20),
                    ft.Column([self.lbl_diferencia, self.lbl_tipo_ajuste], spacing=2),
                    ft.Container(width=20),
                    self.lbl_costo_total,
                    ft.Container(expand=True),
                    ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color="white"), on_click=self.cancelar_edicion),
                    self.btn_guardar_edicion
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=10),
            bgcolor=Config.COLOR_PRIMARY,
            padding=15,
            border_radius=10,
            visible=False
        )

        # Controles Paginación Interfaz
        self.lbl_page_info = ft.Text("Página 1 de 1")"""
content = content.replace(target3, repl3)

target3b = """                padding=ft.padding.only(top=10)
            )
        )"""
repl3b = """                padding=ft.padding.only(top=10)
            )
        )
        self.content.controls.append(self.action_bar)"""
content = content.replace(target3b, repl3b)

# 4. Refactorización de la Creación de Filas
target4 = """    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo["id_auditoria"]
        estado_insumo = insumo["estado"]
        cant_sistema = insumo["cantidad_sistema"]
        cant_fisica = insumo.get("cantidad_fisica")
        
        # Campo para ingresar conteo físico
        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else "",
            dense=True, width=80, text_size=13, content_padding=10,
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO")
        )

        btn_aceptar_sistema = ft.IconButton(
            icon=ft.icons.CHECK_BOX,
            icon_color="green",
            tooltip="Aceptar Stock del Sistema",
            disabled=(estado_periodo == "CERRADO" or estado_insumo != "PENDIENTE"),
            on_click=lambda e: self.procesar_aceptar_sistema(id_auditoria)
        )

        btn_guardar_conteo = ft.IconButton(
            icon=ft.icons.SAVE,
            icon_color="blue",
            tooltip="Guardar Conteo Físico",
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO"),
            on_click=lambda e: self.procesar_guardar_conteo(id_auditoria, txt_conteo.value)
        )

        acciones = ft.Row([btn_aceptar_sistema, btn_guardar_conteo], spacing=0)

        color_diferencia = "red" if insumo.get("diferencia", 0) != 0 else "black"

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(insumo["codigo_insumo"])),
                ft.DataCell(ft.Text(insumo["nombre"], width=200, no_wrap=True, tooltip=insumo["nombre"])),
                ft.DataCell(ft.Text(str(cant_sistema), weight="bold")),
                ft.DataCell(txt_conteo),
                ft.DataCell(ft.Text(str(insumo.get("diferencia", "")), color=color_diferencia)),
                ft.DataCell(ft.Text(estado_insumo, size=11, weight="bold", color="grey")),
                ft.DataCell(acciones),
            ]
        )"""

# In the script replacement for target4, we'll replace everything from `def crear_fila_auditoria` to the end of the file.
# Then append the new `crear_fila_auditoria` and the new toggle methods.
target4_and_beyond = content[content.find("    def crear_fila_auditoria(self, insumo, estado_periodo):"):]

repl4 = """    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo["id_auditoria"]
        estado_insumo = insumo["estado"]
        cant_sistema = insumo["cantidad_sistema"]
        cant_fisica = insumo.get("cantidad_fisica")
        diferencia = insumo.get("diferencia", 0)
        observacion = insumo.get("observacion") or ""
        categoria = insumo.get("categoria") or ""
        
        # El costo del ajuste se puede derivar multiplicando diferencia por costo unitario
        costo_unit = insumo.get("costo_unitario_snapshot", 0)
        costo_ajuste_total = abs(diferencia) * costo_unit if diferencia else 0

        color_diferencia = "red" if diferencia != 0 else "black"
        
        row_ref = ft.DataRow(cells=[])
        
        checkbox = ft.Checkbox(
            value=False, 
            disabled=(estado_periodo == "CERRADO" or estado_insumo == "APROBADO"),
            on_change=lambda e, i=insumo, r=row_ref: self.toggle_edit(e, i, r)
        )

        row_ref.cells = [
            ft.DataCell(ft.Container(content=checkbox, width=25, alignment=ft.alignment.center)),
            ft.DataCell(ft.Text(insumo["codigo_insumo"])),
            ft.DataCell(ft.Text(insumo["nombre"], width=180, no_wrap=True, tooltip=insumo["nombre"])),
            ft.DataCell(ft.Text(categoria, width=100, no_wrap=True, tooltip=categoria)),
            ft.DataCell(ft.Text(str(cant_sistema), weight="bold")),
            ft.DataCell(ft.Text(str(cant_fisica) if cant_fisica is not None else "")),
            ft.DataCell(ft.Text(str(diferencia), color=color_diferencia)),
            ft.DataCell(ft.Text(f"${costo_ajuste_total:,.2f}" if costo_ajuste_total else "")),
            ft.DataCell(ft.Text(observacion, width=150, no_wrap=True, tooltip=observacion)),
            ft.DataCell(ft.Text(estado_insumo, size=11, weight="bold", color="grey")),
        ]
        return row_ref

    def toggle_edit(self, e, insumo, row_ref):
        if not e.control.value:
            self.cancelar_edicion()
            return
            
        if self.current_edit_context and self.current_edit_context['row'] != row_ref:
            prev_row = self.current_edit_context['row']
            if prev_row and len(prev_row.cells) > 0:
                prev_row.cells[0].content.content.value = False
                
        self.current_edit_context = {'item': insumo, 'row': row_ref}
        
        cod = insumo.get('codigo_insumo', '')
        nom = insumo.get('nombre', '')
        cat = insumo.get('categoria', '')
        stock_sist = insumo.get('cantidad_sistema', 0)
        costo_u = insumo.get('costo_unitario_snapshot', 0)
        
        self.edit_panel_title.value = f"Auditando: [{cod}] {nom} | Cat: {cat} | Stock Sistema: {stock_sist}"
        self.edit_fisico.value = str(insumo.get('cantidad_fisica')) if insumo.get('cantidad_fisica') is not None else str(stock_sist)
        self.edit_costo.value = str(costo_u)
        self.edit_observacion.value = insumo.get('observacion') or ""
        
        self.edit_fisico.on_change(None) # Disparar cálculo inicial
        self.action_bar.visible = True
        self.update()

    def cancelar_edicion(self, e=None):
        if self.current_edit_context:
            row_ref = self.current_edit_context['row']
            if row_ref and len(row_ref.cells) > 0:
                row_ref.cells[0].content.content.value = False
        self.current_edit_context = None
        self.action_bar.visible = False
        self.update()

    def on_guardar_conteo_panel(self, e):
        if not self.current_edit_context: return
        item = self.current_edit_context['item']
        id_auditoria = item['id_auditoria']
        stock_sist = float(item['cantidad_sistema'])
        
        try:
            fisico = float(self.edit_fisico.value)
            costo = float(self.edit_costo.value)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Valores numéricos inválidos."), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        obs = self.edit_observacion.value.strip()

        # Si el conteo físico es igual al del sistema y no hay observación obligatoria, usar aceptar_stock_sistema
        if fisico == stock_sist and not obs:
            res = self.db.aceptar_stock_sistema(id_auditoria)
        else:
            res = self.db.registrar_conteo_fisico(id_auditoria, fisico, costo, obs)
            
        if res.get("exito"):
            self.cancelar_edicion()
            self.load_data()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {res.get('error')}"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()"""

content = content.replace(target4_and_beyond, repl4)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactor UI panel finished successfully.")
````

## File: revert_plotly.py
````python
with open('ui/views/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove imports
content = content.replace("import plotly.graph_objects as go\n", "")
content = content.replace("from flet.plotly_chart import PlotlyChart\n", "")

# 2. Replace __init__ section
start_init = content.find("        # Contenedor preparado para Plotly")
end_init = content.find("        # Tables")

new_init = """        # Series de datos (Grosor y puntas redondeadas)
        self.chart_ventas = ft.LineChartData(
            data_points=[], 
            color=ft.colors.BLUE_400,
            stroke_width=4, 
            curved=True,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE_400)
        )
        self.chart_compras = ft.LineChartData(
            data_points=[], 
            color="#2ecca0", 
            stroke_width=4, 
            curved=True,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, "#2ecca0")
        )
        
        # Gráfico habilitando los ejes visuales
        self.line_chart = ft.LineChart(
            data_series=[self.chart_ventas, self.chart_compras],
            border=ft.border.all(1, ft.colors.with_opacity(0.2, "white")),
            min_y=0,
            min_x=0,
            expand=True,
            tooltip_bgcolor=ft.colors.BLUE_GREY_900,
            left_axis=ft.ChartAxis(labels_size=50), 
            bottom_axis=ft.ChartAxis(labels_size=40), 
        )
        
        # Leyenda adaptada a fondo oscuro
        leyenda = ft.Row([
            ft.Row([ft.Container(width=12, height=12, bgcolor=ft.colors.BLUE_400, border_radius=6), ft.Text("Ingresos", size=12, weight="bold", color="white")]),
            ft.Row([ft.Container(width=12, height=12, bgcolor="#2ecca0", border_radius=6), ft.Text("Costos", size=12, weight="bold", color="white")]),
        ], spacing=30, alignment=ft.MainAxisAlignment.CENTER)
        
        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Text("Tendencia Diaria: Ingresos vs Costo de Ventas", size=16, weight="bold", color="white"),
                leyenda,
                ft.Container(content=self.line_chart, height=320, expand=True, margin=ft.padding.only(top=10))
            ]),
            bgcolor="#111111", # Fondo negro estético
            padding=20,
            border_radius=10,
            border=ft.border.all(1, "#333333"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.2, "black"))
        )
        
"""

content = content[:start_init] + new_init + content[end_init:]

# 3. Replace load_data section
start_load = content.find("        # 2. Load Chart Data con Plotly")
end_load = content.find("        # 3. Load Tables Data")

new_load = """        # 2. Load Chart Data (Nativo Flet)
        try:
            tendencia = self.db.get_tendencia_diaria()
            dias_ordenados = sorted(tendencia.keys())
            max_val_y = 0
            
            pts_ventas = []
            pts_compras = []
            etiquetas_x = []
            
            for i, dia in enumerate(dias_ordenados):
                v = tendencia[dia]["ventas"]
                c = tendencia[dia]["compras"]
                if v > max_val_y: max_val_y = v
                if c > max_val_y: max_val_y = c
                
                tt_ventas = f"{dia}\\nIngresos: ${v:,.0f}         "
                tt_compras = f"{dia}\\nCostos: ${c:,.0f}         "
                estilo_tt = ft.TextStyle(size=14, weight="bold", color="white")
                
                pts_ventas.append(ft.LineChartDataPoint(i, v, tooltip=tt_ventas, tooltip_style=estilo_tt))
                pts_compras.append(ft.LineChartDataPoint(i, c, tooltip=tt_compras, tooltip_style=estilo_tt))
                
                # Densidad en Eje X: Mostrar la etiqueta cada 2 días
                if i % 2 == 0: 
                    dia_numero = dia[-2:] # Extrae solo el día (ej: "15")
                    etiquetas_x.append(
                        ft.ChartAxisLabel(
                            value=i, 
                            label=ft.Text(dia_numero, size=11, color="white70")
                        )
                    )
                
            if not pts_ventas:
                pts_ventas = [ft.LineChartDataPoint(0, 0)]
                pts_compras = [ft.LineChartDataPoint(0, 0)]
                
            self.chart_ventas.data_points = pts_ventas
            self.chart_compras.data_points = pts_compras
            
            self.line_chart.max_x = len(dias_ordenados) - 1 if dias_ordenados else 0
            max_y_calc = max_val_y * 1.15 if max_val_y > 0 else 1000
            self.line_chart.max_y = max_y_calc
            
            def formato_moneda_corta(valor):
                if valor >= 1000000: return f"${valor/1000000:.1f}M"
                if valor >= 1000: return f"${valor/1000:.0f}k"
                return f"${valor:.0f}"
                
            # Mayor densidad en Y: 8 divisiones en lugar de 5
            intervalo_y = max_y_calc / 8 if max_y_calc > 0 else 100
            etiquetas_y = [
                ft.ChartAxisLabel(value=step * intervalo_y, label=ft.Text(formato_moneda_corta(step * intervalo_y), size=11, color="white70"))
                for step in range(9)
            ]
            
            self.line_chart.left_axis.labels = etiquetas_y
            self.line_chart.bottom_axis.labels = etiquetas_x
            
            # Cuadrícula visible completa con efecto punteado
            self.line_chart.horizontal_grid_lines = ft.ChartGridLines(
                interval=intervalo_y,
                color=ft.colors.with_opacity(0.15, "white"),
                width=1,
                dash_pattern=[4, 4]
            )
            self.line_chart.vertical_grid_lines = ft.ChartGridLines(
                interval=2, # Línea vertical sincronizada con el eje X
                color=ft.colors.with_opacity(0.15, "white"),
                width=1,
                dash_pattern=[4, 4]
            )
            
        except Exception as e:
            print(f"Error crítico construyendo Chart Flet: {e}")
        
"""

content = content[:start_load] + new_load + content[end_load:]

with open('ui/views/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Reverted to native Flet chart")
````

## File: Sistema_Dona_Mary.spec
````
# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.')],
    hiddenimports=[],
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
    name='Sistema_Dona_Mary',
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
    version='C:/Users/Home/AppData/Local/Temp/8eefa800-9c76-474d-b9a1-33f4a3d6fe9b',
)
````

## File: supabase_schema.sql
````sql
-- Script de Creación de Base de Datos para Dashboard Abarrotes Mary
-- Ejecuta este script en el "SQL Editor" de tu panel de Supabase

-- 1. Tabla: Catalogo_Insumos (El Maestro de Productos)
CREATE TABLE IF NOT EXISTS public.Catalogo_Insumos (
    id_insumo UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    categoria TEXT,
    costo_unitario DECIMAL(10,2) DEFAULT 0,
    precio_venta DECIMAL(10,2) DEFAULT 0,
    stock_actual INTEGER DEFAULT 0,
    stock_minimo INTEGER DEFAULT 5,
    estado BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. Tabla: Registro_Compras (Entradas)
CREATE TABLE IF NOT EXISTS public.Registro_Compras (
    id_compra UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    id_insumo UUID REFERENCES public.Catalogo_Insumos(id_insumo),
    insumo TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    proveedor TEXT,
    estado_registro TEXT DEFAULT 'VÁLIDO' CHECK (estado_registro IN ('VÁLIDO', 'ANULADO'))
);

-- 3. Tabla: Registro_Ventas (Salidas)
CREATE TABLE IF NOT EXISTS public.Registro_Ventas (
    id_venta UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factura_no TEXT,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    codigo_item TEXT REFERENCES public.Catalogo_Insumos(codigo),
    descripcion TEXT,
    cantidad INTEGER NOT NULL,
    subtotal DECIMAL(10,2) DEFAULT 0,
    descuento DECIMAL(10,2) DEFAULT 0,
    iva DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) DEFAULT 0,
    estado_registro TEXT DEFAULT 'VÁLIDO' CHECK (estado_registro IN ('VÁLIDO', 'ANULADO'))
);

-- Configuración de Seguridad (Opcional por ahora, pero recomendado)
-- Desactivamos RLS para que la app pueda acceder fácilmente (al ser de escritorio admin)
ALTER TABLE public.Catalogo_Insumos DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.Registro_Compras DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.Registro_Ventas DISABLE ROW LEVEL SECURITY;
````

## File: update_dashboard_avanzado.sql
````sql
-- 1. Función para obtener la proyección de ventas total (Insumos activos con stock positivo)
CREATE OR REPLACE FUNCTION public.get_proyeccion_ventas_rpc()
RETURNS numeric
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_total numeric;
BEGIN
    SELECT COALESCE(SUM(stock_actual * precio_venta), 0)
    INTO v_total
    FROM public.vista_inventario_completo
    WHERE estado = true AND stock_actual > 0;
    
    RETURN v_total;
END;
$$;

-- 2. Función para obtener los ajustes del mes agrupados por tipo y motivo
CREATE OR REPLACE FUNCTION public.get_ajustes_mes_rpc(mes_actual text)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_resultado json;
BEGIN
    SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
    INTO v_resultado
    FROM (
        SELECT 
            tipo_ajuste,
            COALESCE(motivo_observacion, '') as motivo_observacion,
            COUNT(*) as conteo,
            SUM(cantidad) as cantidad_total,
            SUM(costo_total_ajuste) as costo_total
        FROM public.registro_ajustes_inventario
        WHERE estado_registro = 'VÁLIDO'
          AND TO_CHAR(fecha_ajuste, 'YYYY-MM') = mes_actual
        GROUP BY tipo_ajuste, motivo_observacion
    ) t;

    RETURN v_resultado;
END;
$$;
````

## File: update_fn_obtener_estado_cierre.sql
````sql
CREATE OR REPLACE FUNCTION public.fn_obtener_estado_cierre(p_mes text)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
AS $function$
    WITH periodo_info AS (
        SELECT * FROM public.periodos_inventario WHERE mes_periodo = p_mes LIMIT 1
    )
    SELECT jsonb_build_object(
        'periodo', row_to_json(pi.*),
        'resumen', jsonb_build_object(
            'total_insumos', COUNT(rac.id_auditoria),
            'pendientes',    COUNT(CASE WHEN rac.estado = 'PENDIENTE'  THEN 1 END),
            'auditados',     COUNT(CASE WHEN rac.estado = 'AUDITADO'   THEN 1 END),
            'ajustados',     COUNT(CASE WHEN rac.estado = 'AJUSTADO'   THEN 1 END),
            'aprobados',     COUNT(CASE WHEN rac.estado = 'APROBADO'   THEN 1 END)
        ),
        'insumos', COALESCE(jsonb_agg(
            jsonb_build_object(
                'id_auditoria',          rac.id_auditoria,
                'codigo_insumo',         vi.codigo_insumo,
                'nombre',                vi.nombre,
                'categoria',             vi.categoria,
                
                -- Live metrics
                'stock_inicial',         vi.stock_inicial,
                'entradas',              vi.entradas,
                'salidas',               vi.salidas,
                'ajustes',               vi.ajustes,
                
                -- Either snapshot quantity or live quantity
                'cantidad_sistema',      COALESCE(rac.cantidad_sistema, vi.stock_actual),
                'stock_actual',          vi.stock_actual,
                'cantidad_fisica',       rac.cantidad_fisica,
                'diferencia',            rac.diferencia,
                'costo_unitario_snapshot', COALESCE(rac.costo_unitario_snapshot, vi.costo_unitario),
                'estado',                COALESCE(rac.estado, CASE WHEN pi.estado = 'ABIERTO' THEN 'EN TRÁNSITO' ELSE 'SIN SNAPSHOT' END),
                'observacion',           rac.observacion
            ) ORDER BY vi.categoria, vi.nombre
        ), '[]'::jsonb)
    )
    FROM periodo_info pi
    LEFT JOIN public.vista_inventario_completo vi ON vi.estado = true
    LEFT JOIN public.registro_auditorias_cierres rac 
           ON rac.id_periodo = pi.id_periodo 
          AND rac.codigo_insumo = vi.codigo_insumo
          AND rac.tipo_registro = 'SNAPSHOT'
    GROUP BY pi.id_periodo, pi.mes_periodo, pi.estado, pi.fecha_corte,
             pi.origen_snapshot, pi.aprobado_por, pi.fecha_aprobacion,
             pi.observaciones, pi.total_costo_entradas,
             pi.total_ingreso_salidas, pi.created_at, pi.fecha_inicio;
$function$
;
````

## File: update_insumos.py
````python
import ast

with open('core/supabase_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_get_insumos = '''    def get_insumos(self, page=1, page_size=20, search="", categoria="", fecha_corte=None, sort_col="Insumo", sort_asc=True):
        """
        Obtiene los insumos con paginación, filtros y ordenamiento desde el servidor.
        Retorna (lista_datos, total_count)
        """
        if fecha_corte:
            url = f"{self.url}/rpc/obtener_inventario_por_fecha?select=*"
        else:
            url = f"{self.url}/vista_inventario_completo?select=*"
        
        filtros = []
        if categoria and categoria != "Todas":
            filtros.append(f"categoria=eq.{categoria}")
            
        if search:
            filtros.append(f"or=(nombre.ilike.*{search}*,codigo_insumo.ilike.*{search}*)")
            
        if filtros:
            url += "&" + "&".join(filtros)
            
        # Mapeo de columnas de la interfaz a las columnas de la vista SQL
        map_columnas = {
            "Código": "codigo_insumo",
            "Insumo": "nombre",
            "Categoría": "categoria",
            "Ubicación": "ubicacion",
            "Stock Inicial": "stock_inicial",
            "Stock Mínimo": "stock_minimo",
            "Entradas": "entradas",
            "Salidas": "salidas",
            "Stock Real": "stock_actual"
        }
        
        db_col = map_columnas.get(sort_col, "nombre")
        direccion = "asc" if sort_asc else "desc"
        
        offset = (page - 1) * page_size
        url += f"&order={db_col}.{direccion}&offset={offset}&limit={page_size}"
        
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            if fecha_corte:
                payload = {"p_fecha_corte": f"{fecha_corte} 23:59:59"}
                response = requests.post(url, headers=headers, json=payload)
            else:
                response = requests.get(url, headers=headers)
            
            if response.status_code in (200, 201, 206):
                data = response.json()
                content_range = response.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                print(f"Error en consulta: {response.text}")
                return [], 0
        except Exception as e:
            print(f"Excepción en get_insumos: {e}")
            return [], 0
'''

# We know get_insumos is at index 48 to 98
del lines[47:98]
lines.insert(47, new_get_insumos)

with open('core/supabase_client.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Updated core/supabase_client.py")
````

## File: update_kpis.py
````python
import os

# 1. Update supabase_client.py
client_path = r"c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\core\supabase_client.py"
with open(client_path, 'r', encoding='utf-8') as f:
    client_code = f.read()

new_method = """
    def get_kpis_por_categoria(self) -> list:
        \"\"\"Invoca RPC para extraer rendimiento y rotación agrupada por categoría.\"\"\"
        url = f"{self.url}/rpc/get_kpis_por_categoria_rpc"
        try:
            import requests
            res = requests.post(url, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC get_kpis_por_categoria: {e}")
        return []
"""

if "def get_kpis_por_categoria" not in client_code:
    client_code += new_method
    with open(client_path, 'w', encoding='utf-8') as f:
        f.write(client_code)


# 2. Update dashboard.py
dashboard_path = r"c:\Users\Home\.gemini\antigravity-ide\scratch\do-aMary\ui\views\dashboard.py"
with open(dashboard_path, 'r', encoding='utf-8') as f:
    dashboard_code = f.read()

init_target = "        self.kpi_row = ft.ResponsiveRow(["
init_end = dashboard_code.find("        # Gráfico habilitando los ejes visuales", dashboard_code.find(init_target))

new_container = """        # Contenedor de Categorías (Scroll Horizontal)
        self.categorias_row = ft.Row(wrap=False, scroll=ft.ScrollMode.ADAPTIVE, spacing=15)
        self.categorias_container = ft.Container(
            content=ft.Column([
                ft.Text("Rendimiento Detallado por Categoría", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.categorias_row
            ]),
            margin=ft.padding.only(top=10, bottom=10)
        )
"""
if "self.categorias_row = ft.Row" not in dashboard_code:
    # Insert right before "# Gráfico"
    dashboard_code = dashboard_code[:init_end] + new_container + "\n" + dashboard_code[init_end:]

# Insert into self.content
if "self.categorias_container," not in dashboard_code:
    dashboard_code = dashboard_code.replace(
        "            self.kpi_row,\n            ft.Divider(height=10, color=\"transparent\"),\n            self.chart_container,",
        "            self.kpi_row,\n            ft.Divider(height=10, color=\"transparent\"),\n            self.categorias_container,\n            ft.Divider(height=10, color=\"transparent\"),\n            self.chart_container,"
    )

# Add to load_data
load_target = """        if self.page:
            self.update()"""

new_load = """        try:
            kpis_cat = self.db.get_kpis_por_categoria()
            self.categorias_row.controls.clear()
            for cat in kpis_cat:
                self.categorias_row.controls.append(self._build_categoria_card(cat))
        except Exception as e:
            print(f"Error cargando KPIs por categoría: {e}")
            
        if self.page:
            self.update()"""

if "kpis_cat = self.db.get_kpis_por_categoria()" not in dashboard_code:
    dashboard_code = dashboard_code.replace(load_target, new_load)


# Add _build_categoria_card
card_method = """
    def _build_categoria_card(self, data):
        rentabilidad = data.get('rentabilidad', 0)
        return ft.Container(
            width=260,
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.CATEGORY, color=Config.COLOR_SECONDARY, size=20),
                    ft.Text(str(data.get("categoria", "N/A")).upper(), weight="bold", size=13, color=Config.COLOR_PRIMARY, expand=True)
                ]),
                ft.Divider(height=1, color="#f0f0f0"),
                ft.Row([ft.Text("Inventario:", size=11, color="grey"), ft.Text(f"${data.get('costo_inventario', 0):,.0f}", size=12, weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Ventas:", size=11, color="grey"), ft.Text(f"${data.get('ventas_totales', 0):,.0f}", size=12, weight="bold", color="green")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Rotación:", size=11, color="grey"), ft.Text(f"{data.get('rotacion', 0):.2f}x", size=12, weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Rendimiento:", size=11, color="grey"), ft.Text(f"{rentabilidad:.1f}%", size=12, weight="bold", color="#2ecca0" if rentabilidad >= 0 else "red")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=6)
        )
"""

if "def _build_categoria_card" not in dashboard_code:
    dashboard_code += card_method

with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(dashboard_code)

print("Update script finished.")
````

## File: update_plotly.py
````python
import ast

with open('requirements.txt', 'r') as f:
    reqs = f.read()
if 'plotly' not in reqs:
    with open('requirements.txt', 'a') as f:
        f.write('\nplotly\n')

with open('ui/views/dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Add imports at the top
lines.insert(4, "import plotly.graph_objects as go\nfrom flet.plotly_chart import PlotlyChart\n")

# 2. Re-read as single string to do simple targeted replacements
content = "".join(lines)

# Find the block for Chart in __init__
start_chart_init = content.find("        # Chart")
end_chart_init = content.find("        # Tables")

new_chart_init = """        # Contenedor preparado para Plotly
        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Text("Tendencia Diaria: Ingresos vs Costo de Ventas", size=16, weight="bold", color="white"),
                ft.Container(height=320, expand=True) # Placeholder que se llenará en load_data
            ]),
            bgcolor="#111111", # Fondo oscuro
            padding=20,
            border_radius=10,
            border=ft.border.all(1, "#333333"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.2, "black"))
        )
        
"""

content = content[:start_chart_init] + new_chart_init + content[end_chart_init:]


# 3. Find the block in load_data
start_load_data = content.find("        # 2. Load Chart Data")
end_load_data = content.find("        # 3. Load Tables Data")

new_load_data = """        # 2. Load Chart Data con Plotly
        try:
            tendencia = self.db.get_tendencia_diaria()
            dias_ordenados = sorted(tendencia.keys())
            
            x_data = []
            y_ventas = []
            y_compras = []
            
            for dia in dias_ordenados:
                # Formateo de fecha para mejor visualización en el eje X
                dia_formateado = dia[-2:] # Extrae el día
                x_data.append(dia_formateado)
                y_ventas.append(tendencia[dia]["ventas"])
                y_compras.append(tendencia[dia]["compras"])
                
            fig = go.Figure()
            
            # Serie: Ingresos por Ventas
            fig.add_trace(go.Scatter(
                x=x_data, y=y_ventas,
                mode='lines+markers',
                name='Ingresos',
                line=dict(color='#42a5f5', width=3, shape='spline'), # Azul claro para contraste en fondo oscuro
                fill='tozeroy',
                fillcolor='rgba(66, 165, 245, 0.1)',
                hovertemplate='Día: %{x}<br>Ingresos: $%{y:,.0f}<extra></extra>'
            ))
            
            # Serie: Costo de Ventas
            fig.add_trace(go.Scatter(
                x=x_data, y=y_compras,
                mode='lines+markers',
                name='Costos',
                line=dict(color='#2ecca0', width=3, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(46, 204, 160, 0.1)',
                hovertemplate='Día: %{x}<br>Costos: $%{y:,.0f}<extra></extra>'
            ))
            
            # Layout Dark Mode avanzado
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', # Transparente para que tome el color del contenedor Flet
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=10, b=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                xaxis=dict(
                    showgrid=True, gridcolor='#333333', gridwidth=1, griddash='dot',
                    tickmode='linear', dtick=2 # Muestra etiquetas en el eje X cada 2 días
                ),
                yaxis=dict(
                    showgrid=True, gridcolor='#333333', gridwidth=1, griddash='dot', 
                    tickprefix='$',
                    zeroline=True, zerolinecolor='#444444'
                ),
                hovermode="x unified", # Tooltip unificado que cruza ambas líneas verticalmente
                hoverlabel=dict(bgcolor="#222222", font_size=13, font_family="Inter")
            )
            
            # Inyectar la gráfica en el contenedor
            self.chart_container.content.controls[1] = PlotlyChart(fig, expand=True)
            
        except Exception as e:
            print(f"Error crítico construyendo Plotly Chart: {e}")
        
"""

content = content[:start_load_data] + new_load_data + content[end_load_data:]

with open('ui/views/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Update complete.")
````

## File: update_supabase.py
````python
import ast

with open('core/supabase_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

tree = ast.parse(''.join(lines))

methods_to_remove = [
    'get_compras_summary',
    'get_ventas_summary',
    'get_catalogo_summary',
    'get_top_ventas_mes',
    'get_tendencia_diaria',
    'get_inventario_kpis'
]

ranges_to_delete = []

class MethodVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        if node.name in methods_to_remove:
            ranges_to_delete.append((node.lineno, node.end_lineno))
        self.generic_visit(node)

visitor = MethodVisitor()
visitor.visit(tree)

# Sort ranges in reverse to delete from bottom up without messing up line indices
ranges_to_delete.sort(key=lambda x: x[0], reverse=True)

for start, end in ranges_to_delete:
    del lines[start-1:end]

# Append the new methods
new_methods = '''
    def get_compras_summary(self) -> dict:
        \"\"\"Invoca RPC para totales de compras\"\"\"
        import datetime
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        
        url = f"{self.url}/rpc/get_compras_summary_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual, "dia_hoy": hoy}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC compras_summary: {e}")
        return {"total_mes": 0.0, "total_hoy": 0.0, "cantidad_total": 0.0}

    def get_ventas_summary(self) -> dict:
        \"\"\"Invoca RPC para totales de ingresos e IVA\"\"\"
        import datetime
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        
        url = f"{self.url}/rpc/get_ventas_summary_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual, "dia_hoy": hoy}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC ventas_summary: {e}")
        return {"total_historico": 0.0, "total_mes": 0.0, "total_hoy": 0.0, "iva_historico": 0.0, "iva_hoy": 0.0}

    def get_catalogo_summary(self) -> dict:
        \"\"\"Invoca RPC para compras totales y ventas totales en pesos\"\"\"
        url = f"{self.url}/rpc/get_catalogo_summary_rpc"
        try:
            res = requests.post(url, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC catalogo_summary: {e}")
        return {"total_compras": 0.0, "total_ventas": 0.0}

    def get_top_ventas_mes(self, limit=10) -> list:
        import datetime
        mes_actual = datetime.date.today().strftime("%Y-%m")
        url = f"{self.url}/rpc/get_top_ventas_mes_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual, "limite": limit}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC top_ventas: {e}")
        return []

    def get_tendencia_diaria(self) -> dict:
        \"\"\"Invoca RPC para obtener ventas y compras agrupadas por día\"\"\"
        import datetime
        hoy = datetime.date.today()
        mes_actual = hoy.strftime("%Y-%m")
        
        # Pre-poblar el diccionario con ceros para todos los días transcurridos
        tendencia = {f"{mes_actual}-{i:02d}": {"ventas": 0.0, "compras": 0.0} for i in range(1, hoy.day + 1)}
        
        url = f"{self.url}/rpc/get_tendencia_diaria_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual}, headers=self.headers)
            if res.status_code == 200:
                for row in res.json():
                    dia = row.get("dia")
                    if dia in tendencia:
                        tendencia[dia]["ventas"] = float(row.get("ventas", 0))
                        tendencia[dia]["compras"] = float(row.get("compras", 0))
        except Exception as e:
            print(f"Error RPC tendencia_diaria: {e}")
        return tendencia

    def get_inventario_kpis(self) -> dict:
        import datetime
        mes_actual = datetime.date.today().strftime("%Y-%m")
        url = f"{self.url}/rpc/get_inventario_kpis_rpc"
        try:
            res = requests.post(url, json={"mes_actual": mes_actual}, headers=self.headers)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"Error RPC inventario_kpis: {e}")
        return {"valor_inventario": 0.0, "alertas_criticas": 0}
'''

lines.append(new_methods)

with open('core/supabase_client.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('File updated successfully.')
````

## File: core/gemini_parser.py
````python
import google.generativeai as genai
from config import Config
import json
import time
import re
from typing import TypedDict

class GeminiParser:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3.6-flash')

            
    def parse_invoice_pdf(self, pdf_path):
        """
        Envía un PDF a Gemini para extraer productos y cantidades.
        Retorna un diccionario con los datos extraídos o None si hay un error.
        """
        if not self.api_key:
            print("Error: No hay API key de Gemini configurada.")
            return None
            
        try:
            print(f"Subiendo archivo a Gemini: {pdf_path}")
            # 1. Subir archivo a la API de File de Gemini
            uploaded_file = genai.upload_file(path=pdf_path)
            
            # 2. Esperar a que el archivo se procese (opcional, recomendado para PDFs)
            while uploaded_file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            print("\nArchivo listo. Extrayendo datos...")
            
            # 3. Armar el prompt estricto
            prompt = """
            Extrae TODOS los datos de TODAS las páginas del reporte de entradas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas el nombre del proveedor ni la descripción del producto. Limítate a los datos numéricos y códigos.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada compra inicia en el extremo izquierdo con un código "EA-" (ej. EA-9273). Procesa TODOS los que encuentres.
            2. FECHA Y FACTURA: La "fecha" suele estar bajo el código EA (conviértela a YYYY-MM-DD). El "numero_factura" está junto a la palabra "Factura No.". Si no hay, pon null.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Totales de Entrada:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_insumo": Código de 4 dígitos al extremo izquierdo.
               - "cantidad": Dato bajo la columna 'Cant.'
               - "costo_unitario": Dato bajo la columna 'Costo'.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
            5. FORMATO NUMÉRICO ESTRICTO: Convierte puntos a miles y comas a decimales (ej. "13.100" -> 13100.0 y "16,50" -> 16.5).
            
            ESTRUCTURA EXACTA REQUERIDA (Sigue este patrón para todos los bloques e insumos):
            [
              {
                "numero_entrada": "EA-9276",
                "fecha": "2026-08-03",
                "numero_factura": "19284",
                "productos": [
                  {
                    "codigo_insumo": "0471",
                    "cantidad": 10.0,
                    "costo_unitario": 7353.0,
                    "iva": 13971.0
                  },
                  {
                    "codigo_insumo": "4182",
                    "cantidad": 50.0,
                    "costo_unitario": 2815.0,
                    "iva": 26744.0
                  }
                ]
              }
            ]
            """
            
            # 4. Enviar a Gemini forzando el motor JSON y maximizando los tokens
            response = self.model.generate_content(
                [uploaded_file, prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.0, # Temperatura cero para formato robótico y determinista
                    max_output_tokens=8192 # Darle el máximo espacio posible para PDFs grandes
                )
            )
            
            # Como forzamos el mime_type, la respuesta ya es un string JSON limpio
            text_response = response.text.strip()
            
            # Limpiar comas huérfanas (trailing commas) que la IA suele dejar por error antes de cerrar llaves o corchetes
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            # Parsear el JSON de forma segura
            data = json.loads(text_response)
            
            # --- Escudo de formato (Ahora esperamos una lista) ---
            if isinstance(data, dict):
                # Si Gemini se equivoca y devuelve un solo objeto, lo envolvemos en una lista
                data = [data]
            elif not isinstance(data, list):
                data = []
            # -------------------------------
            
            # Eliminar archivo subido
            genai.delete_file(uploaded_file.name)
            
            print("¡Extracción completada! Conexión con Gemini cerrada.")
            return data
            
        except Exception as e:
            print(f"Error procesando PDF con Gemini: {e}")
            return None

    def parse_compras_pdf_page(self, pdf_path, page_index):
        """
        Extrae datos de compras de una única página del PDF.
        """
        if not self.api_key:
            return None
            
        try:
            
            from pypdf import PdfReader, PdfWriter
            import os
            from typing import TypedDict
        except ImportError:
            return None
            
        try:
            reader = PdfReader(pdf_path)
            if page_index < 0 or page_index >= len(reader.pages):
                return None
                
            class ProductoCompra(TypedDict):
                codigo_insumo: str
                cantidad: float
                costo_unitario: float
                iva: float

            class FacturaCompra(TypedDict):
                numero_entrada: str
                fecha: str
                numero_factura: str
                productos: list[ProductoCompra]
                
            prompt = """
            Extrae TODOS los datos de TODAS las facturas en esta página del reporte de entradas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas el nombre del proveedor ni la descripción del producto. Limítate a los datos numéricos y códigos.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada compra inicia en el extremo izquierdo con un código "EA-" (ej. EA-9273). Procesa TODOS los que encuentres.
            2. FECHA Y FACTURA: La "fecha" suele estar bajo el código EA (conviértela a YYYY-MM-DD). El "numero_factura" está junto a la palabra "Factura No.". Si no hay, pon null.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Totales de Entrada:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_insumo": Código de 4 dígitos al extremo izquierdo.
               - "cantidad": Dato bajo la columna 'Cant.'
               - "costo_unitario": Dato bajo la columna 'Costo'.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
            5. FORMATO NUMÉRICO ESTRICTO: Convierte puntos a miles y comas a decimales (ej. "13.100" -> 13100.0 y "16,50" -> 16.5).
            
            ESTRUCTURA EXACTA REQUERIDA (Sigue este patrón para todos los bloques e insumos):
            [
              {
                "numero_entrada": "EA-9276",
                "fecha": "2026-08-03",
                "numero_factura": "19284",
                "productos": [
                  {
                    "codigo_insumo": "0471",
                    "cantidad": 10.0,
                    "costo_unitario": 7353.0,
                    "iva": 13971.0
                  }
                ]
              }
            ]
            """
            
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            
            temp_pdf_path = f"temp_compras_page_{page_index}.pdf"
            with open(temp_pdf_path, "wb") as f:
                writer.write(f)
            
            uploaded_file = genai.upload_file(path=temp_pdf_path)
            time.sleep(2)
            
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            intentos = 0
            max_intentos = 3
            response = None
            
            while intentos < max_intentos:
                try:
                    response = self.model.generate_content(
                        [uploaded_file, prompt],
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=list[FacturaCompra],
                            temperature=0.0,
                            max_output_tokens=8192
                        )
                    )
                    break
                except Exception as api_e:
                    error_str = str(api_e)
                    if "429" in error_str or "quota" in error_str.lower():
                        print(f"⚠️ Límite de Google alcanzado (429). Esperando 60s de forma invisible... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(60)
                        intentos += 1
                    elif "500" in error_str or "internal error" in error_str.lower():
                        print(f"⚠️ Error interno en Google (500). Reintentando en 15s... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(15)
                        intentos += 1
                    else:
                        raise api_e
                        
            if response is None:
                print("Error: Se superaron los intentos máximos o respuesta nula.")
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)
                return []
            
            text_response = response.text.strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            text_response = text_response.strip()
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            genai.delete_file(uploaded_file.name)
            os.remove(temp_pdf_path)
            
            try:
                data = json.loads(text_response)
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                return []
            except json.JSONDecodeError as je:
                print(f"Error parseando JSON en página {page_index + 1}. Error: {je}")
                print(f"Texto problemático:\n{text_response[:500]}...")
                return []
                
        except Exception as e:
            print(f"Error procesando página {page_index + 1} de compras con Gemini: {e}")
            return None

    def parse_ventas_pdf(self, pdf_path, progress_callback=None):
        """
        Envía un PDF de ventas a Gemini (en bloques) para evitar el límite de memoria.
        Retorna un arreglo con los datos extraídos o None si hay un error.
        """
        if not self.api_key:
            print("Error: No hay API key de Gemini configurada.")
            return None
            
        try:
            from pypdf import PdfReader, PdfWriter
            import os
        except ImportError:
            msg = "Error: Falta la librería pypdf. Ejecuta 'pip install pypdf' en la terminal."
            print(msg)
            if progress_callback: progress_callback(msg)
            return None
            
        try:
            msg = f"Preparando división automática para el PDF..."
            print(msg)
            if progress_callback: progress_callback(msg)
            
            reader = PdfReader(pdf_path)
            total_paginas = len(reader.pages)
            tamano_bloque = 1 # Procesar de a 1 página para máxima precisión y evitar errores de JSON
            todas_las_facturas = []
            
            # --- EL MOLDE ESTRICTO PARA VENTAS ---
            class ProductoVenta(TypedDict):
                codigo_item: str
                cantidad: float
                subtotal: float
                iva: float
                costo_total: float

            class FacturaVenta(TypedDict):
                fecha: str
                numero_factura: str
                productos: list[ProductoVenta]
            # --------------------------------------------
            
            prompt = """
            Extrae TODOS los datos de TODAS las páginas de este fragmento del reporte de facturas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas el nombre del cliente ni la descripción del producto. Limítate a los datos numéricos y códigos.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada bloque de venta inicia con "Fact.No." seguido del número de factura. Procesa TODOS los que encuentres en el documento.
            2. FECHA Y FACTURA: La "fecha" suele estar en la misma línea que el "Fact.No." (conviértela a YYYY-MM-DD). Extrae el número de factura.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Total Factura:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_item": Código al extremo izquierdo (ej. 0847, 0571-1).
               - "cantidad": Dato bajo la columna 'Cantidad'.
               - "subtotal": Dato bajo la columna 'Subtotal'. NO HAGAS NINGÚN CÁLCULO.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
               - "costo_total": Dato bajo la columna 'Total'.
            5. FORMATO NUMÉRICO ESTRICTO: Todo valor monetario o cantidad debe ser número (float). Usa puntos (.) solo para decimales. NO uses comas (,) para separar los miles dentro de los números (ej. "93,277" debe ser 93277.0).
            """
            
            # Ciclo para iterar el documento por pedazos
            for i in range(0, total_paginas, tamano_bloque):
                rango_inicio = i + 1
                rango_fin = min(i + tamano_bloque, total_paginas)
                msg = f"Extrayendo datos: Página {rango_inicio} de {total_paginas}..." if tamano_bloque == 1 else f"Extrayendo datos: Páginas {rango_inicio} a {rango_fin} de {total_paginas}..."
                print(msg)
                if progress_callback: progress_callback(msg)
                
                # 1. Crear PDF temporal con solo un bloque de páginas
                writer = PdfWriter()
                for j in range(i, rango_fin):
                    writer.add_page(reader.pages[j])
                    
                temp_pdf_path = f"temp_ventas_chunk_{i}.pdf"
                with open(temp_pdf_path, "wb") as f:
                    writer.write(f)
                
                # 2. Subir el fragmento a Gemini
                uploaded_file = genai.upload_file(path=temp_pdf_path)
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(1)
                    uploaded_file = genai.get_file(uploaded_file.name)
                
                # 3. Extraer los datos forzando el motor JSON y el esquema
                response = self.model.generate_content(
                    [uploaded_file, prompt],
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=list[FacturaVenta],
                        temperature=0.0,
                        max_output_tokens=8192
                    )
                )
                
                text_response = response.text.strip()
                
                # Limpiar la basura residual y comas huérfanas
                if text_response.startswith("```json"):
                    text_response = text_response[7:]
                if text_response.startswith("```"):
                    text_response = text_response[3:]
                if text_response.endswith("```"):
                    text_response = text_response[:-3]
                
                text_response = text_response.strip()
                text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
                
                try:
                    data = json.loads(text_response)
                    # Agrupar los resultados
                    if isinstance(data, dict):
                        todas_las_facturas.append(data)
                    elif isinstance(data, list):
                        todas_las_facturas.extend(data)
                except json.JSONDecodeError as je:
                    print(f"Error parseando el JSON en página {rango_inicio}. Saltando bloque. Error: {je}")
                    print(f"JSON Problemático:\n{text_response[:500]}...")
                
                # 4. Limpiar los archivos temporales para no llenar el disco ni la nube
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)

            msg = "¡Extracción de todas las páginas completada!"
            print(msg)
            if progress_callback: progress_callback(msg)
            
            return todas_las_facturas
            
        except Exception as e:
            print(f"Error procesando PDF de ventas con Gemini: {e}")
            return None

    def parse_ventas_pdf_page(self, pdf_path, page_index):
        """
        Extrae datos de una única página del PDF.
        """
        if not self.api_key:
            return None
            
        try:
            from pypdf import PdfReader, PdfWriter
            import os
        except ImportError:
            return None
            
        try:
            reader = PdfReader(pdf_path)
            if page_index < 0 or page_index >= len(reader.pages):
                return None
                
            # --- EL MOLDE ESTRICTO PARA VENTAS ---
            class ProductoVenta(TypedDict):
                codigo_item: str
                cantidad: float
                subtotal: float
                iva: float
                costo_total: float

            class FacturaVenta(TypedDict):
                fecha: str
                numero_factura: str
                productos: list[ProductoVenta]
            
            prompt = """
            Extrae TODOS los datos de TODAS las páginas de este fragmento del reporte de facturas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas el nombre del cliente ni la descripción del producto. Limítate a los datos numéricos y códigos.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada bloque de venta inicia con "Fact.No." seguido del número de factura. Procesa TODOS los que encuentres en el documento.
            2. FECHA Y FACTURA: La "fecha" suele estar en la misma línea que el "Fact.No." (conviértela a YYYY-MM-DD). Extrae el número de factura.
            3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a la frase "Total Factura:".
            4. CAMPOS POR PRODUCTO:
               - "codigo_item": Código al extremo izquierdo (ej. 0847, 0571-1).
               - "cantidad": Dato bajo la columna 'Cantidad'.
               - "subtotal": Dato bajo la columna 'Subtotal'. NO HAGAS NINGÚN CÁLCULO.
               - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
               - "costo_total": Dato bajo la columna 'Total'.
            5. FORMATO NUMÉRICO ESTRICTO: Todo valor monetario o cantidad debe ser número (float). Usa puntos (.) solo para decimales. NO uses comas (,) para separar los miles dentro de los números (ej. "93,277" debe ser 93277.0).
            """
            
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])
            
            temp_pdf_path = f"temp_ventas_page_{page_index}.pdf"
            with open(temp_pdf_path, "wb") as f:
                writer.write(f)
            
            uploaded_file = genai.upload_file(path=temp_pdf_path)
            time.sleep(2) # Pausa inicial para dar respiro a la API
            
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5) # Preguntar solo cada 5 segundos
                uploaded_file = genai.get_file(uploaded_file.name)
            
            intentos = 0
            max_intentos = 3
            response = None
            
            while intentos < max_intentos:
                try:
                    response = self.model.generate_content(
                        [uploaded_file, prompt],
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=list[FacturaVenta],
                            temperature=0.0,
                            max_output_tokens=8192
                        )
                    )
                    break
                except Exception as api_e:
                    error_str = str(api_e)
                    if "429" in error_str or "quota" in error_str.lower():
                        print(f"⚠️ Límite de Google alcanzado (429). Esperando 60s de forma invisible... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(60)
                        intentos += 1
                    elif "500" in error_str or "internal error" in error_str.lower():
                        print(f"⚠️ Error interno en los servidores de Google (500). Reintentando en 15s... (Intento {intentos+1}/{max_intentos})")
                        time.sleep(15)
                        intentos += 1
                    else:
                        raise api_e
                        
            if response is None:
                print("Error: Se superaron los intentos máximos o la respuesta es nula.")
                genai.delete_file(uploaded_file.name)
                os.remove(temp_pdf_path)
                return []
            
            text_response = response.text.strip()
            
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
            
            text_response = text_response.strip()
            text_response = re.sub(r',\s*([\]}])', r'\1', text_response)
            
            genai.delete_file(uploaded_file.name)
            os.remove(temp_pdf_path)
            
            try:
                data = json.loads(text_response)
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                return []
            except json.JSONDecodeError as je:
                print(f"Error parseando el JSON de página {page_index + 1}. Error: {je}")
                return []
                
        except Exception as e:
            print(f"Error procesando página {page_index + 1} de ventas con Gemini: {e}")
            return None
````

## File: main.py
````python
import flet as ft
from ui.app import AppLayout
from config import Config

def main(page: ft.Page):
    # Configuración de la página principal
    page.title = "Abarrotes y Desechables Doña Mary"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.window_maximized = True
    page.fonts = {
        "Inter": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bslnt%2Cwght%5D.ttf"
    }
    
    # Sistema de Diseño Responsivo y Tema Global
    page.theme = ft.Theme(
        font_family="Inter",
        color_scheme=ft.ColorScheme(
            primary=Config.COLOR_PRIMARY,
            primary_container=Config.COLOR_SECONDARY,
            secondary=Config.COLOR_SECONDARY,
            background=Config.COLOR_BACKGROUND,
            surface="white",
            on_surface=Config.COLOR_TEXT,
        ),
        visual_density=ft.ThemeVisualDensity.COMFORTABLE,
    )

    # Inicializar el layout de la app
    app_layout = AppLayout(page)
    
    # Agregar a la página
    page.add(app_layout)
    page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
````

## File: config.py
````python
import os
import sys
from dotenv import load_dotenv

# Determinar la ruta base dependiendo de si se ejecuta como script o como .exe
if getattr(sys, 'frozen', False):
    # Si es un ejecutable empaquetado (flet pack / PyInstaller), usar la carpeta temporal _MEIPASS
    base_path = sys._MEIPASS
else:
    # Si es el código fuente normal, usar la carpeta actual
    base_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(base_path, '.env')

# Cargar variables de entorno apuntando explícitamente al archivo
load_dotenv(dotenv_path=env_path)
class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Colores de la aplicación (Tema)
    COLOR_PRIMARY = "#0B2447" # Azul Oscuro (Primario)
    COLOR_SECONDARY = "#19376D" # Azul Medio (Secundario)
    COLOR_BACKGROUND = "#F8F9FA" # Blanco/Gris claro (Fondo)
    COLOR_TEXT = "#333333"
````

## File: esquema_actualizado.sql
````sql
-- ESQUEMA ACTUALIZADO DE SUPABASE (Recuperado a partir de la documentación validada)

-- DROP SCHEMA public;

CREATE SCHEMA public AUTHORIZATION pg_database_owner;

COMMENT ON SCHEMA public IS 'standard public schema';
-- public.catalogo_insumos definition

-- Drop table

-- DROP TABLE public.catalogo_insumos;

CREATE TABLE public.catalogo_insumos ( id_insumo uuid DEFAULT gen_random_uuid() NOT NULL, codigo_insumo text NULL, nombre text NULL, descripcion text NULL, categoria text NULL, costo_unitario numeric(10, 2) NULL, precio_venta numeric(10, 2) NULL, stock_actual numeric(12, 2) DEFAULT 0 NULL, stock_minimo numeric(12, 2) DEFAULT 0 NULL, estado bool DEFAULT true NULL, zona text NULL, ubicacion text NULL, tipo_unidad text NULL, CONSTRAINT catalogo_insumos_codigo_insumo_key UNIQUE (codigo_insumo), CONSTRAINT catalogo_insumos_codigo_key UNIQUE (codigo_insumo), CONSTRAINT catalogo_insumos_pkey PRIMARY KEY (id_insumo));

-- Permissions

ALTER TABLE public.catalogo_insumos OWNER TO postgres;
GRANT ALL ON TABLE public.catalogo_insumos TO postgres;
GRANT ALL ON TABLE public.catalogo_insumos TO anon;
GRANT ALL ON TABLE public.catalogo_insumos TO authenticated;
GRANT ALL ON TABLE public.catalogo_insumos TO service_role;


-- public.periodos_inventario definition

-- Drop table

-- DROP TABLE public.periodos_inventario;

CREATE TABLE public.periodos_inventario ( id_periodo uuid DEFAULT gen_random_uuid() NOT NULL, mes_periodo text NOT NULL, fecha_inicio date NOT NULL, fecha_corte timestamptz NULL, estado text DEFAULT 'ABIERTO'::text NOT NULL, origen_snapshot text NULL, aprobado_por text NULL, fecha_aprobacion timestamptz NULL, observaciones text NULL, total_costo_entradas numeric DEFAULT 0 NULL, total_ingreso_salidas numeric DEFAULT 0 NULL, created_at timestamptz DEFAULT timezone('utc'::text, now()) NULL, CONSTRAINT periodos_inventario_estado_check CHECK ((estado = ANY (ARRAY['ABIERTO'::text, 'PRELIMINAR'::text, 'EN_AUDITORIA'::text, 'CERRADO'::text]))), CONSTRAINT periodos_inventario_mes_key UNIQUE (mes_periodo), CONSTRAINT periodos_inventario_origen_check CHECK ((origen_snapshot = ANY (ARRAY['AUTOMATICO'::text, 'MANUAL'::text]))), CONSTRAINT periodos_inventario_pkey PRIMARY KEY (id_periodo));

-- Permissions

ALTER TABLE public.periodos_inventario OWNER TO postgres;
GRANT ALL ON TABLE public.periodos_inventario TO postgres;
GRANT ALL ON TABLE public.periodos_inventario TO anon;
GRANT ALL ON TABLE public.periodos_inventario TO authenticated;
GRANT ALL ON TABLE public.periodos_inventario TO service_role;


-- public.conteo_fisico_relacionado definition

-- Drop table

-- DROP TABLE public.conteo_fisico_relacionado;

CREATE TABLE public.conteo_fisico_relacionado ( id_conteo uuid DEFAULT gen_random_uuid() NOT NULL, cod_insumo_fisico text NOT NULL, nombre_insumo_fisico text NOT NULL, codigo_sugerido text NULL, nombre_sugerido text NULL, categoria_sugerida text NULL, zona text NULL, ubicacion text NULL, tipo_unidad text NULL, cantidad_fisica int4 NOT NULL, fecha_registro timestamptz DEFAULT timezone('utc'::text, now()) NULL, CONSTRAINT conteo_fisico_relacionado_pkey PRIMARY KEY (id_conteo), CONSTRAINT conteo_fisico_relacionado_codigo_sugerido_fkey FOREIGN KEY (codigo_sugerido) REFERENCES public.catalogo_insumos(codigo_insumo));

-- Permissions

ALTER TABLE public.conteo_fisico_relacionado OWNER TO postgres;
GRANT ALL ON TABLE public.conteo_fisico_relacionado TO postgres;
GRANT ALL ON TABLE public.conteo_fisico_relacionado TO anon;
GRANT ALL ON TABLE public.conteo_fisico_relacionado TO authenticated;
GRANT ALL ON TABLE public.conteo_fisico_relacionado TO service_role;


-- public.registro_auditorias_cierres definition

-- Drop table

-- DROP TABLE public.registro_auditorias_cierres;

CREATE TABLE public.registro_auditorias_cierres ( id_auditoria uuid DEFAULT gen_random_uuid() NOT NULL, fecha_cierre timestamptz DEFAULT timezone('utc'::text, now()) NULL, codigo_insumo text NULL, tipo_registro text NULL, cantidad_sistema numeric(12, 2) DEFAULT 0 NULL, cantidad_fisica numeric(12, 2) NULL, diferencia numeric(12, 2) NULL, observacion text NULL, estado text DEFAULT 'APLICADO'::text NULL, costo_unitario_snapshot numeric DEFAULT 0 NULL, costo_entradas_mes numeric DEFAULT 0 NULL, ingreso_salidas_mes numeric DEFAULT 0 NULL, id_periodo uuid NULL, CONSTRAINT registro_auditorias_cierres_pkey PRIMARY KEY (id_auditoria), CONSTRAINT registro_auditorias_cierres_tipo_registro_check CHECK ((tipo_registro = ANY (ARRAY['SNAPSHOT'::text, 'INVENTARIO_INICIAL'::text, 'CIERRE_MENSUAL'::text, 'AJUSTE_ESPORADICO'::text]))), CONSTRAINT uq_insumo_tipo_periodo UNIQUE (id_periodo, codigo_insumo, tipo_registro), CONSTRAINT fk_auditorias_codigo_insumo FOREIGN KEY (codigo_insumo) REFERENCES public.catalogo_insumos(codigo_insumo), CONSTRAINT fk_auditorias_periodo FOREIGN KEY (id_periodo) REFERENCES public.periodos_inventario(id_periodo) ON DELETE CASCADE, CONSTRAINT registro_auditorias_cierres_codigo_insumo_fkey FOREIGN KEY (codigo_insumo) REFERENCES public.catalogo_insumos(codigo_insumo));

-- Permissions

ALTER TABLE public.registro_auditorias_cierres OWNER TO postgres;
GRANT ALL ON TABLE public.registro_auditorias_cierres TO postgres;
GRANT ALL ON TABLE public.registro_auditorias_cierres TO anon;
GRANT ALL ON TABLE public.registro_auditorias_cierres TO authenticated;
GRANT ALL ON TABLE public.registro_auditorias_cierres TO service_role;


-- public.registro_compras definition

-- Drop table

-- DROP TABLE public.registro_compras;

CREATE TABLE public.registro_compras ( id_compra uuid DEFAULT gen_random_uuid() NOT NULL, fecha timestamptz DEFAULT now() NULL, descripcion text NULL, cantidad numeric(12, 2) NULL, proveedor text NULL, estado_registro text DEFAULT 'VÁLIDO'::text NULL, codigo_insumo text NULL, numero_entrada text NULL, numero_factura text NULL, bodega text DEFAULT 'PRINCIPAL'::text NULL, costo_unitario numeric(12, 2) DEFAULT 0 NULL, valor_iva numeric(12, 2) DEFAULT 0 NULL, costo_total numeric(12, 2) DEFAULT 0 NULL, CONSTRAINT registro_compras_pkey PRIMARY KEY (id_compra), CONSTRAINT fk_compras_codigo_insumo FOREIGN KEY (codigo_insumo) REFERENCES public.catalogo_insumos(codigo_insumo));

-- Table Triggers

create trigger trigger_compras after
insert
    on
    public.registro_compras for each row execute function actualizar_stock_y_costo_compra();

-- Permissions

ALTER TABLE public.registro_compras OWNER TO postgres;
GRANT ALL ON TABLE public.registro_compras TO postgres;
GRANT ALL ON TABLE public.registro_compras TO anon;
GRANT ALL ON TABLE public.registro_compras TO authenticated;
GRANT ALL ON TABLE public.registro_compras TO service_role;


-- public.registro_ventas definition

-- Drop table

-- DROP TABLE public.registro_ventas;

CREATE TABLE public.registro_ventas ( id_venta uuid DEFAULT gen_random_uuid() NOT NULL, factura_no text NULL, fecha timestamptz DEFAULT now() NULL, descripcion text NULL, cantidad numeric(12, 2) NULL, subtotal numeric(12, 2) NULL, descuento numeric(12, 2) NULL, iva numeric(12, 2) NULL, total numeric(12, 2) NULL, estado_registro text DEFAULT 'VÁLIDO'::text NULL, codigo_insumo text NULL, CONSTRAINT registro_ventas_pkey PRIMARY KEY (id_venta), CONSTRAINT fk_ventas_codigo_insumo FOREIGN KEY (codigo_insumo) REFERENCES public.catalogo_insumos(codigo_insumo));

-- Table Triggers

create trigger trigger_ventas after
insert
    on
    public.registro_ventas for each row execute function actualizar_stock_venta();

-- Permissions

ALTER TABLE public.registro_ventas OWNER TO postgres;
GRANT ALL ON TABLE public.registro_ventas TO postgres;
GRANT ALL ON TABLE public.registro_ventas TO anon;
GRANT ALL ON TABLE public.registro_ventas TO authenticated;
GRANT ALL ON TABLE public.registro_ventas TO service_role;


-- public.registro_ajustes_inventario definition

-- Drop table

-- DROP TABLE public.registro_ajustes_inventario;

CREATE TABLE public.registro_ajustes_inventario ( id_ajuste uuid DEFAULT gen_random_uuid() NOT NULL, fecha_ajuste timestamptz DEFAULT timezone('utc'::text, now()) NULL, codigo_insumo text NULL, tipo_ajuste text NULL, cantidad numeric(12, 2) NOT NULL, costo_unitario_congelado numeric(12, 2) NOT NULL, costo_total_ajuste numeric(12, 2) NOT NULL, motivo_observacion text NULL, estado_registro text DEFAULT 'VÁLIDO'::text NULL, id_auditoria_origen uuid NULL, id_periodo uuid NULL, CONSTRAINT registro_ajustes_inventario_estado_registro_check CHECK ((estado_registro = ANY (ARRAY['VÁLIDO'::text, 'ANULADO'::text]))), CONSTRAINT registro_ajustes_inventario_pkey PRIMARY KEY (id_ajuste), CONSTRAINT registro_ajustes_inventario_tipo_ajuste_check CHECK ((tipo_ajuste = ANY (ARRAY['AJUSTE_ENTRADA'::text, 'AJUSTE_SALIDA'::text, 'ENTRADA_POR_SOBRANTE'::text, 'SALIDA_POR_FALTANTE'::text, 'BAJA_VENCIMIENTO'::text, 'CORRECCION_ADMIN'::text]))), CONSTRAINT fk_ajustes_auditoria_origen FOREIGN KEY (id_auditoria_origen) REFERENCES public.registro_auditorias_cierres(id_auditoria) ON DELETE SET NULL, CONSTRAINT fk_ajustes_codigo_insumo FOREIGN KEY (codigo_insumo) REFERENCES public.catalogo_insumos(codigo_insumo), CONSTRAINT registro_ajustes_inventario_codigo_item_fkey FOREIGN KEY (codigo_insumo) REFERENCES public.catalogo_insumos(codigo_insumo), CONSTRAINT registro_ajustes_inventario_id_periodo_fkey FOREIGN KEY (id_periodo) REFERENCES public.periodos_inventario(id_periodo) ON DELETE SET NULL);

-- Table Triggers

create trigger trigger_ajustes after
insert
    on
    public.registro_ajustes_inventario for each row execute function actualizar_stock_por_ajuste();

-- Permissions

ALTER TABLE public.registro_ajustes_inventario OWNER TO postgres;
GRANT ALL ON TABLE public.registro_ajustes_inventario TO postgres;
GRANT ALL ON TABLE public.registro_ajustes_inventario TO anon;
GRANT ALL ON TABLE public.registro_ajustes_inventario TO authenticated;
GRANT ALL ON TABLE public.registro_ajustes_inventario TO service_role;


-- public.vista_inventario_completo source

CREATE OR REPLACE VIEW public.vista_inventario_completo
AS WITH periodo_activo AS (
         SELECT periodos_inventario.id_periodo,
            periodos_inventario.mes_periodo
           FROM periodos_inventario
          WHERE periodos_inventario.mes_periodo = to_char(CURRENT_DATE::timestamp with time zone, 'YYYY-MM'::text)
         LIMIT 1
        ), stock_inicial_mes AS (
         SELECT DISTINCT ON (rac.codigo_insumo) rac.codigo_insumo,
            rac.cantidad_sistema AS cantidad_inicial,
            rac.costo_unitario_snapshot AS costo_snapshot
           FROM registro_auditorias_cierres rac
             JOIN periodo_activo pa ON rac.id_periodo = pa.id_periodo
          WHERE rac.tipo_registro = 'INVENTARIO_INICIAL'::text AND (rac.estado = ANY (ARRAY['APROBADO'::text, 'PROVISIONAL'::text]))
          ORDER BY rac.codigo_insumo, (
                CASE rac.estado
                    WHEN 'APROBADO'::text THEN 1
                    ELSE 2
                END)
        ), entradas_mes AS (
         SELECT registro_compras.codigo_insumo,
            COALESCE(sum(registro_compras.cantidad), 0::numeric) AS total_entradas,
            COALESCE(sum(registro_compras.costo_total), 0::numeric) AS total_costo_entradas
           FROM registro_compras
          WHERE registro_compras.estado_registro = 'VÁLIDO'::text AND to_char(registro_compras.fecha, 'YYYY-MM'::text) = (( SELECT periodo_activo.mes_periodo
                   FROM periodo_activo))
          GROUP BY registro_compras.codigo_insumo
        ), salidas_mes AS (
         SELECT registro_ventas.codigo_insumo,
            COALESCE(sum(registro_ventas.cantidad), 0::numeric) AS total_salidas,
            COALESCE(sum(registro_ventas.total), 0::numeric) AS total_ingreso_salidas
           FROM registro_ventas
          WHERE registro_ventas.estado_registro = 'VÁLIDO'::text AND to_char(registro_ventas.fecha, 'YYYY-MM'::text) = (( SELECT periodo_activo.mes_periodo
                   FROM periodo_activo))
          GROUP BY registro_ventas.codigo_insumo
        ), ajustes_mes AS (
         SELECT registro_ajustes_inventario.codigo_insumo,
            COALESCE(sum(
                CASE
                    WHEN registro_ajustes_inventario.tipo_ajuste = ANY (ARRAY['AJUSTE_ENTRADA'::text, 'ENTRADA_POR_SOBRANTE'::text]) THEN registro_ajustes_inventario.cantidad
                    WHEN registro_ajustes_inventario.tipo_ajuste = ANY (ARRAY['AJUSTE_SALIDA'::text, 'SALIDA_POR_FALTANTE'::text, 'BAJA_VENCIMIENTO'::text, 'CORRECCION_ADMIN'::text]) THEN - registro_ajustes_inventario.cantidad
                    ELSE 0::numeric
                END), 0::numeric) AS ajuste_neto
           FROM registro_ajustes_inventario
          WHERE registro_ajustes_inventario.estado_registro = 'VÁLIDO'::text AND to_char(registro_ajustes_inventario.fecha_ajuste, 'YYYY-MM'::text) = (( SELECT periodo_activo.mes_periodo
                   FROM periodo_activo))
          GROUP BY registro_ajustes_inventario.codigo_insumo
        )
 SELECT ci.codigo_insumo,
    ci.nombre,
    ci.categoria,
    ci.zona,
    ci.ubicacion,
    ci.tipo_unidad,
    COALESCE(sim.costo_snapshot, ci.costo_unitario, 0::numeric) AS costo_unitario,
    ci.precio_venta,
    COALESCE(sim.cantidad_inicial, 0::numeric) AS stock_inicial,
    COALESCE(em.total_entradas, 0::numeric) AS entradas,
    COALESCE(sm.total_salidas, 0::numeric) AS salidas,
    COALESCE(am.ajuste_neto, 0::numeric) AS ajustes,
    COALESCE(sim.cantidad_inicial, 0::numeric) + COALESCE(em.total_entradas, 0::numeric) - COALESCE(sm.total_salidas, 0::numeric) + COALESCE(am.ajuste_neto, 0::numeric) AS stock_actual,
    (COALESCE(sim.cantidad_inicial, 0::numeric) + COALESCE(em.total_entradas, 0::numeric) - COALESCE(sm.total_salidas, 0::numeric) + COALESCE(am.ajuste_neto, 0::numeric)) * COALESCE(sim.costo_snapshot, ci.costo_unitario, 0::numeric) AS costo_total_insumo,
    COALESCE(sm.total_ingreso_salidas, 0::numeric) AS venta_total_insumo,
    ci.stock_minimo,
    ci.descripcion,
    ci.estado
   FROM catalogo_insumos ci
     LEFT JOIN stock_inicial_mes sim ON sim.codigo_insumo = ci.codigo_insumo
     LEFT JOIN entradas_mes em ON em.codigo_insumo = ci.codigo_insumo
     LEFT JOIN salidas_mes sm ON sm.codigo_insumo = ci.codigo_insumo
     LEFT JOIN ajustes_mes am ON am.codigo_insumo = ci.codigo_insumo
  WHERE ci.estado = true;

-- Permissions

ALTER TABLE public.vista_inventario_completo OWNER TO postgres;
GRANT ALL ON TABLE public.vista_inventario_completo TO postgres;
GRANT ALL ON TABLE public.vista_inventario_completo TO anon;
GRANT ALL ON TABLE public.vista_inventario_completo TO authenticated;
GRANT ALL ON TABLE public.vista_inventario_completo TO service_role;



-- DROP FUNCTION public.actualizar_stock_por_ajuste();

CREATE OR REPLACE FUNCTION public.actualizar_stock_por_ajuste()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Solo procesa si el ajuste es válido
    IF NEW.estado_registro = 'VÁLIDO' THEN
        
        -- Si es un sobrante, suma al catálogo
        IF NEW.tipo_ajuste = 'ENTRADA_POR_SOBRANTE' THEN
            UPDATE public.catalogo_insumos
            SET stock_actual = stock_actual + NEW.cantidad
            WHERE codigo_insumo = NEW.codigo_insumo;
            
        -- Si es un faltante, resta del catálogo
        ELSIF NEW.tipo_ajuste = 'SALIDA_POR_FALTANTE' THEN
            UPDATE public.catalogo_insumos
            SET stock_actual = stock_actual - NEW.cantidad
            WHERE codigo_insumo = NEW.codigo_insumo;
        END IF;
        
    END IF;
    RETURN NEW;
END;
$function$
;

-- Permissions

ALTER FUNCTION public.actualizar_stock_por_ajuste() OWNER TO postgres;
GRANT ALL ON FUNCTION public.actualizar_stock_por_ajuste() TO public;
GRANT ALL ON FUNCTION public.actualizar_stock_por_ajuste() TO postgres;
GRANT ALL ON FUNCTION public.actualizar_stock_por_ajuste() TO anon;
GRANT ALL ON FUNCTION public.actualizar_stock_por_ajuste() TO authenticated;
GRANT ALL ON FUNCTION public.actualizar_stock_por_ajuste() TO service_role;

-- DROP FUNCTION public.actualizar_stock_venta();

CREATE OR REPLACE FUNCTION public.actualizar_stock_venta()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Solo aplica si el registro es válido
    IF NEW.estado_registro = 'VÁLIDO' THEN
        UPDATE public.catalogo_insumos
        SET 
            -- 1. Resta la mercancía del inventario
            stock_actual = stock_actual - NEW.cantidad,
            
            -- 2. Calcula el precio unitario final (Total con IVA / Cantidad)
            -- Usamos NULLIF para proteger el sistema de errores matemáticos si la cantidad fuera 0
            precio_venta = COALESCE((NEW.total / NULLIF(NEW.cantidad, 0)), precio_venta)
            
        WHERE codigo_insumo = NEW.codigo_insumo;
    END IF;
    RETURN NEW;
END;
$function$
;

-- Permissions

ALTER FUNCTION public.actualizar_stock_venta() OWNER TO postgres;
GRANT ALL ON FUNCTION public.actualizar_stock_venta() TO public;
GRANT ALL ON FUNCTION public.actualizar_stock_venta() TO postgres;
GRANT ALL ON FUNCTION public.actualizar_stock_venta() TO anon;
GRANT ALL ON FUNCTION public.actualizar_stock_venta() TO authenticated;
GRANT ALL ON FUNCTION public.actualizar_stock_venta() TO service_role;

-- DROP FUNCTION public.actualizar_stock_y_costo_compra();

CREATE OR REPLACE FUNCTION public.actualizar_stock_y_costo_compra()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Solo aplica si el registro es válido
    IF NEW.estado_registro = 'VÁLIDO' THEN
        UPDATE public.catalogo_insumos
        SET 
            stock_actual = stock_actual + NEW.cantidad,
            costo_unitario = NEW.costo_unitario
        WHERE codigo_insumo = NEW.codigo_insumo;
    END IF;
    RETURN NEW;
END;
$function$
;

-- Permissions

ALTER FUNCTION public.actualizar_stock_y_costo_compra() OWNER TO postgres;
GRANT ALL ON FUNCTION public.actualizar_stock_y_costo_compra() TO public;
GRANT ALL ON FUNCTION public.actualizar_stock_y_costo_compra() TO postgres;
GRANT ALL ON FUNCTION public.actualizar_stock_y_costo_compra() TO anon;
GRANT ALL ON FUNCTION public.actualizar_stock_y_costo_compra() TO authenticated;
GRANT ALL ON FUNCTION public.actualizar_stock_y_costo_compra() TO service_role;

-- DROP FUNCTION public.fn_aceptar_stock_sistema(uuid);

CREATE OR REPLACE FUNCTION public.fn_aceptar_stock_sistema(p_id_auditoria uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    v_cantidad_sistema NUMERIC;
    v_estado_actual    TEXT;
    v_codigo           TEXT;
BEGIN
    SELECT cantidad_sistema, estado, codigo_insumo
    INTO v_cantidad_sistema, v_estado_actual, v_codigo
    FROM public.registro_auditorias_cierres
    WHERE id_auditoria  = p_id_auditoria
      AND tipo_registro = 'SNAPSHOT';

    IF NOT FOUND THEN
        RETURN jsonb_build_object('exito', false, 'error', 'Snapshot no encontrado.');
    END IF;

    IF v_estado_actual = 'APROBADO' THEN
        RETURN jsonb_build_object('exito', false, 'error', 'Insumo ya aprobado.');
    END IF;

    UPDATE public.registro_auditorias_cierres SET
        cantidad_fisica = v_cantidad_sistema,
        diferencia      = 0,
        estado          = 'AUDITADO',
        observacion     = 'Stock del sistema aceptado sin conteo físico.'
    WHERE id_auditoria = p_id_auditoria;

    RETURN jsonb_build_object(
        'exito',             true,
        'codigo_insumo',     v_codigo,
        'cantidad_aceptada', v_cantidad_sistema
    );

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('exito', false, 'error', SQLERRM);
END;
$function$
;

-- Permissions

ALTER FUNCTION public.fn_aceptar_stock_sistema(uuid) OWNER TO postgres;
GRANT ALL ON FUNCTION public.fn_aceptar_stock_sistema(uuid) TO public;
GRANT ALL ON FUNCTION public.fn_aceptar_stock_sistema(uuid) TO postgres;
GRANT ALL ON FUNCTION public.fn_aceptar_stock_sistema(uuid) TO anon;
GRANT ALL ON FUNCTION public.fn_aceptar_stock_sistema(uuid) TO authenticated;
GRANT ALL ON FUNCTION public.fn_aceptar_stock_sistema(uuid) TO service_role;

-- DROP FUNCTION public.fn_aprobar_cierre_mes(uuid, text);

CREATE OR REPLACE FUNCTION public.fn_aprobar_cierre_mes(p_id_periodo uuid, p_aprobado_por text DEFAULT 'Administrador'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    v_pendientes       INT;
    v_mes_periodo      TEXT;
    v_mes_siguiente    TEXT;
    v_id_sig           UUID;
    v_fecha_inicio_sig DATE;
    v_registro         RECORD;
BEGIN
    -- Verificar que el período existe y está en estado auditable
    SELECT mes_periodo INTO v_mes_periodo
    FROM public.periodos_inventario
    WHERE id_periodo = p_id_periodo
      AND estado IN ('PRELIMINAR', 'EN_AUDITORIA');

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'exito', false,
            'error', 'Período no encontrado o no está en estado auditable.'
        );
    END IF;

    -- Verificar que no quedan insumos PENDIENTES
    SELECT COUNT(*) INTO v_pendientes
    FROM public.registro_auditorias_cierres
    WHERE id_periodo    = p_id_periodo
      AND tipo_registro = 'SNAPSHOT'
      AND estado        = 'PENDIENTE';

    IF v_pendientes > 0 THEN
        RETURN jsonb_build_object(
            'exito',      false,
            'pendientes', v_pendientes,
            'error', format(
                '%s insumo(s) sin auditar. Usa fn_aceptar_stock_sistema para cada uno o registra el conteo físico.',
                v_pendientes
            )
        );
    END IF;

    -- Cerrar el período
    UPDATE public.periodos_inventario SET
        estado           = 'CERRADO',
        aprobado_por     = p_aprobado_por,
        fecha_aprobacion = now()
    WHERE id_periodo = p_id_periodo;

    -- Calcular mes siguiente
    v_mes_siguiente    := TO_CHAR(
        (v_mes_periodo || '-01')::DATE + INTERVAL '1 month',
        'YYYY-MM'
    );
    v_fecha_inicio_sig := (v_mes_siguiente || '-01')::DATE;

    -- Crear período siguiente si no existe
    INSERT INTO public.periodos_inventario (mes_periodo, fecha_inicio, estado)
    VALUES (v_mes_siguiente, v_fecha_inicio_sig, 'ABIERTO')
    ON CONFLICT (mes_periodo) DO NOTHING;

    SELECT id_periodo INTO v_id_sig
    FROM public.periodos_inventario
    WHERE mes_periodo = v_mes_siguiente;

    -- Consolidar INVENTARIO_INICIAL del mes siguiente con datos reales
    FOR v_registro IN
        SELECT
            codigo_insumo,
            COALESCE(cantidad_fisica, cantidad_sistema) AS cantidad_real,
            costo_unitario_snapshot
        FROM public.registro_auditorias_cierres
        WHERE id_periodo    = p_id_periodo
          AND tipo_registro = 'SNAPSHOT'
    LOOP
        INSERT INTO public.registro_auditorias_cierres (
            id_periodo,
            codigo_insumo,
            tipo_registro,
            fecha_cierre,
            cantidad_sistema,
            cantidad_fisica,
            diferencia,
            costo_unitario_snapshot,
            estado,
            observacion
        ) VALUES (
            v_id_sig,
            v_registro.codigo_insumo,
            'INVENTARIO_INICIAL',
            v_fecha_inicio_sig::TIMESTAMPTZ,
            v_registro.cantidad_real,
            v_registro.cantidad_real,
            0,
            v_registro.costo_unitario_snapshot,
            'APROBADO',
            'Inventario inicial consolidado desde cierre de ' || v_mes_periodo
        )
        ON CONFLICT (id_periodo, codigo_insumo, tipo_registro) DO UPDATE SET
            cantidad_sistema        = EXCLUDED.cantidad_sistema,
            cantidad_fisica         = EXCLUDED.cantidad_fisica,
            costo_unitario_snapshot = EXCLUDED.costo_unitario_snapshot,
            estado                  = 'APROBADO',
            observacion             = EXCLUDED.observacion;
    END LOOP;

    RETURN jsonb_build_object(
        'exito',           true,
        'periodo_cerrado', v_mes_periodo,
        'mes_siguiente',   v_mes_siguiente,
        'aprobado_por',    p_aprobado_por,
        'timestamp',       now()
    );

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('exito', false, 'error', SQLERRM);
END;
$function$
;

-- Permissions

ALTER FUNCTION public.fn_aprobar_cierre_mes(uuid, text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.fn_aprobar_cierre_mes(uuid, text) TO public;
GRANT ALL ON FUNCTION public.fn_aprobar_cierre_mes(uuid, text) TO postgres;
GRANT ALL ON FUNCTION public.fn_aprobar_cierre_mes(uuid, text) TO anon;
GRANT ALL ON FUNCTION public.fn_aprobar_cierre_mes(uuid, text) TO authenticated;
GRANT ALL ON FUNCTION public.fn_aprobar_cierre_mes(uuid, text) TO service_role;

-- DROP FUNCTION public.fn_crear_inventario_inicial_provisional(text, uuid);

CREATE OR REPLACE FUNCTION public.fn_crear_inventario_inicial_provisional(p_mes_siguiente text, p_id_periodo_origen uuid)
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    v_id_periodo_siguiente UUID;
    v_fecha_inicio         DATE;
    v_registro             RECORD;
BEGIN
    v_fecha_inicio := (p_mes_siguiente || '-01')::DATE;

    -- Crear el período del mes siguiente si no existe
    INSERT INTO public.periodos_inventario (
        mes_periodo, fecha_inicio, estado
    )
    VALUES (p_mes_siguiente, v_fecha_inicio, 'ABIERTO')
    ON CONFLICT (mes_periodo) DO NOTHING;

    SELECT id_periodo INTO v_id_periodo_siguiente
    FROM public.periodos_inventario
    WHERE mes_periodo = p_mes_siguiente;

    -- Por cada insumo del snapshot, crear su INVENTARIO_INICIAL provisional
    FOR v_registro IN
        SELECT
            codigo_insumo,
            COALESCE(cantidad_fisica, cantidad_sistema) AS cantidad_inicial,
            costo_unitario_snapshot
        FROM public.registro_auditorias_cierres
        WHERE id_periodo    = p_id_periodo_origen
          AND tipo_registro = 'SNAPSHOT'
    LOOP
        INSERT INTO public.registro_auditorias_cierres (
            id_periodo,
            codigo_insumo,
            tipo_registro,
            fecha_cierre,
            cantidad_sistema,
            cantidad_fisica,
            diferencia,
            costo_unitario_snapshot,
            estado,
            observacion
        ) VALUES (
            v_id_periodo_siguiente,
            v_registro.codigo_insumo,
            'INVENTARIO_INICIAL',
            v_fecha_inicio::TIMESTAMPTZ,
            v_registro.cantidad_inicial,
            v_registro.cantidad_inicial,
            0,
            v_registro.costo_unitario_snapshot,
            'PROVISIONAL',
            'Inventario inicial provisional. Pendiente consolidación del cierre anterior.'
        )
        ON CONFLICT (id_periodo, codigo_insumo, tipo_registro) DO UPDATE SET
            cantidad_sistema        = EXCLUDED.cantidad_sistema,
            cantidad_fisica         = EXCLUDED.cantidad_fisica,
            costo_unitario_snapshot = EXCLUDED.costo_unitario_snapshot
        -- Solo actualizar si sigue siendo PROVISIONAL
        WHERE registro_auditorias_cierres.estado = 'PROVISIONAL';
    END LOOP;
END;
$function$
;

-- Permissions

ALTER FUNCTION public.fn_crear_inventario_inicial_provisional(text, uuid) OWNER TO postgres;
GRANT ALL ON FUNCTION public.fn_crear_inventario_inicial_provisional(text, uuid) TO public;
GRANT ALL ON FUNCTION public.fn_crear_inventario_inicial_provisional(text, uuid) TO postgres;
GRANT ALL ON FUNCTION public.fn_crear_inventario_inicial_provisional(text, uuid) TO anon;
GRANT ALL ON FUNCTION public.fn_crear_inventario_inicial_provisional(text, uuid) TO authenticated;
GRANT ALL ON FUNCTION public.fn_crear_inventario_inicial_provisional(text, uuid) TO service_role;

-- DROP FUNCTION public.fn_obtener_estado_cierre(text);

CREATE OR REPLACE FUNCTION public.fn_obtener_estado_cierre(p_mes text)
 RETURNS jsonb
 LANGUAGE sql
 STABLE SECURITY DEFINER
AS $function$
    SELECT jsonb_build_object(
        'periodo',   row_to_json(pi.*),
        'resumen', jsonb_build_object(
            'total_insumos', COUNT(rac.id_auditoria),
            'pendientes',    COUNT(CASE WHEN rac.estado = 'PENDIENTE'  THEN 1 END),
            'auditados',     COUNT(CASE WHEN rac.estado = 'AUDITADO'   THEN 1 END),
            'ajustados',     COUNT(CASE WHEN rac.estado = 'AJUSTADO'   THEN 1 END),
            'aprobados',     COUNT(CASE WHEN rac.estado = 'APROBADO'   THEN 1 END)
        ),
        'insumos', COALESCE(jsonb_agg(
            jsonb_build_object(
                'id_auditoria',          rac.id_auditoria,
                'codigo_insumo',         rac.codigo_insumo,
                'nombre',                ci.nombre,
                'categoria',             ci.categoria,
                'cantidad_sistema',      rac.cantidad_sistema,
                'cantidad_fisica',       rac.cantidad_fisica,
                'diferencia',            rac.diferencia,
                'costo_unitario_snapshot', rac.costo_unitario_snapshot,
                'costo_entradas_mes',    rac.costo_entradas_mes,
                'ingreso_salidas_mes',   rac.ingreso_salidas_mes,
                'estado',                rac.estado,
                'observacion',           rac.observacion
            ) ORDER BY ci.categoria, ci.nombre
        ), '[]'::jsonb)
    )
    FROM public.periodos_inventario pi
    LEFT JOIN public.registro_auditorias_cierres rac
           ON rac.id_periodo    = pi.id_periodo
          AND rac.tipo_registro = 'SNAPSHOT'
    LEFT JOIN public.catalogo_insumos ci
           ON ci.codigo_insumo = rac.codigo_insumo
    WHERE pi.mes_periodo = p_mes
    GROUP BY pi.id_periodo, pi.mes_periodo, pi.estado, pi.fecha_corte,
             pi.origen_snapshot, pi.aprobado_por, pi.fecha_aprobacion,
             pi.observaciones, pi.total_costo_entradas,
             pi.total_ingreso_salidas, pi.created_at, pi.fecha_inicio;
$function$
;

-- Permissions

ALTER FUNCTION public.fn_obtener_estado_cierre(text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.fn_obtener_estado_cierre(text) TO public;
GRANT ALL ON FUNCTION public.fn_obtener_estado_cierre(text) TO postgres;
GRANT ALL ON FUNCTION public.fn_obtener_estado_cierre(text) TO anon;
GRANT ALL ON FUNCTION public.fn_obtener_estado_cierre(text) TO authenticated;
GRANT ALL ON FUNCTION public.fn_obtener_estado_cierre(text) TO service_role;

-- DROP FUNCTION public.fn_registrar_conteo_fisico(uuid, numeric, numeric, text);

CREATE OR REPLACE FUNCTION public.fn_registrar_conteo_fisico(p_id_auditoria uuid, p_cantidad_fisica numeric, p_costo_ajuste numeric DEFAULT NULL::numeric, p_observacion text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    v_snap         RECORD;
    v_diferencia   NUMERIC;
    v_costo_real   NUMERIC;
    v_tipo_ajuste  TEXT;
    v_id_ajuste    UUID;
BEGIN
    -- Obtener el snapshot
    SELECT
        rac.id_auditoria,
        rac.id_periodo,
        rac.codigo_insumo,
        rac.cantidad_sistema,
        rac.costo_unitario_snapshot,
        rac.estado,
        pi.mes_periodo
    INTO v_snap
    FROM public.registro_auditorias_cierres rac
    JOIN public.periodos_inventario pi ON rac.id_periodo = pi.id_periodo
    WHERE rac.id_auditoria  = p_id_auditoria
      AND rac.tipo_registro = 'SNAPSHOT';

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'exito', false,
            'error', 'Snapshot no encontrado para el id proporcionado.'
        );
    END IF;

    IF v_snap.estado = 'APROBADO' THEN
        RETURN jsonb_build_object(
            'exito', false,
            'error', 'Este insumo ya fue aprobado y no puede modificarse.'
        );
    END IF;

    v_diferencia := p_cantidad_fisica - v_snap.cantidad_sistema;

    -- Actualizar el registro de auditoría
    UPDATE public.registro_auditorias_cierres SET
        cantidad_fisica = p_cantidad_fisica,
        diferencia      = v_diferencia,
        observacion     = COALESCE(p_observacion, observacion),
        estado          = CASE
                            WHEN v_diferencia = 0 THEN 'AUDITADO'
                            ELSE 'AJUSTADO'
                          END
    WHERE id_auditoria = p_id_auditoria;

    -- Si hay diferencia, crear el ajuste
    IF v_diferencia <> 0 THEN
        v_costo_real := COALESCE(
            NULLIF(p_costo_ajuste, 0),
            v_snap.costo_unitario_snapshot,
            public.fn_ultimo_costo_compra(v_snap.codigo_insumo),
            0
        );

        v_tipo_ajuste := CASE
            WHEN v_diferencia < 0 THEN 'AJUSTE_SALIDA'
            ELSE 'AJUSTE_ENTRADA'
        END;

        INSERT INTO public.registro_ajustes_inventario (
            fecha_ajuste,
            codigo_insumo,
            tipo_ajuste,
            cantidad,
            costo_unitario_congelado,
            costo_total_ajuste,
            motivo_observacion,
            estado_registro,
            id_periodo,
            id_auditoria_origen
        ) VALUES (
            now(),
            v_snap.codigo_insumo,
            v_tipo_ajuste,
            ABS(v_diferencia),
            v_costo_real,
            ABS(v_diferencia) * v_costo_real,
            COALESCE(
                p_observacion,
                'Ajuste por auditoría física - Cierre ' || v_snap.mes_periodo
            ),
            'VÁLIDO',
            v_snap.id_periodo,
            p_id_auditoria
        )
        RETURNING id_ajuste INTO v_id_ajuste;
    END IF;

    RETURN jsonb_build_object(
        'exito',            true,
        'codigo_insumo',    v_snap.codigo_insumo,
        'cantidad_sistema', v_snap.cantidad_sistema,
        'cantidad_fisica',  p_cantidad_fisica,
        'diferencia',       v_diferencia,
        'tipo_ajuste',      v_tipo_ajuste,
        'id_ajuste',        v_id_ajuste,
        'costo_ajuste',     v_costo_real
    );

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('exito', false, 'error', SQLERRM);
END;
$function$
;

-- Permissions

ALTER FUNCTION public.fn_registrar_conteo_fisico(uuid, numeric, numeric, text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.fn_registrar_conteo_fisico(uuid, numeric, numeric, text) TO public;
GRANT ALL ON FUNCTION public.fn_registrar_conteo_fisico(uuid, numeric, numeric, text) TO postgres;
GRANT ALL ON FUNCTION public.fn_registrar_conteo_fisico(uuid, numeric, numeric, text) TO anon;
GRANT ALL ON FUNCTION public.fn_registrar_conteo_fisico(uuid, numeric, numeric, text) TO authenticated;
GRANT ALL ON FUNCTION public.fn_registrar_conteo_fisico(uuid, numeric, numeric, text) TO service_role;

-- DROP FUNCTION public.fn_snapshot_cierre_mensual(text);

CREATE OR REPLACE FUNCTION public.fn_snapshot_cierre_mensual(p_mes text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
    v_id_periodo      UUID;
    v_fecha_corte     TIMESTAMPTZ := now();
    v_mes_siguiente   TEXT;
    v_fecha_inicio    DATE;
    v_insumo          RECORD;
    v_stock_calc      NUMERIC;
    v_costo_ultimo    NUMERIC;
    v_costo_entradas  NUMERIC;
    v_ingreso_salidas NUMERIC;
    v_count           INT := 0;
BEGIN
    -- Validar formato del parámetro
    BEGIN
        v_fecha_inicio := (p_mes || '-01')::DATE;
    EXCEPTION WHEN OTHERS THEN
        RETURN jsonb_build_object(
            'exito', false,
            'error', 'Formato inválido. Use YYYY-MM. Ejemplo: 2026-08'
        );
    END;

    -- -------------------------------------------------------
    -- 1. Crear o actualizar el período en estado PRELIMINAR
    -- -------------------------------------------------------
    INSERT INTO public.periodos_inventario (
        mes_periodo, fecha_inicio, fecha_corte, estado, origen_snapshot
    )
    VALUES (
        p_mes, v_fecha_inicio, v_fecha_corte, 'PRELIMINAR', 'AUTOMATICO'
    )
    ON CONFLICT (mes_periodo) DO UPDATE SET
        fecha_corte     = v_fecha_corte,
        estado          = 'PRELIMINAR',
        origen_snapshot = 'AUTOMATICO'
    WHERE periodos_inventario.estado IN ('ABIERTO', 'PRELIMINAR')
    RETURNING id_periodo INTO v_id_periodo;

    -- Si no retornó id el período ya está en auditoría o cerrado
    IF v_id_periodo IS NULL THEN
        RETURN jsonb_build_object(
            'exito', false,
            'error', 'El período ' || p_mes || ' ya está en proceso o cerrado.',
            'estado_actual', (
                SELECT estado FROM public.periodos_inventario
                WHERE mes_periodo = p_mes
            )
        );
    END IF;

    -- -------------------------------------------------------
    -- 2. Snapshot por insumo activo
    -- -------------------------------------------------------
    FOR v_insumo IN
        SELECT codigo_insumo
        FROM public.catalogo_insumos
        WHERE estado = true
    LOOP
        -- Stock calculado desde la vista (fuente de verdad)
        SELECT stock_actual INTO v_stock_calc
        FROM public.vista_inventario_completo
        WHERE codigo_insumo = v_insumo.codigo_insumo;

        -- Último costo real de compra
        v_costo_ultimo := public.fn_ultimo_costo_compra(v_insumo.codigo_insumo);

        -- Total invertido en compras de este insumo en el mes
        SELECT COALESCE(SUM(costo_total), 0)
        INTO v_costo_entradas
        FROM public.registro_compras
        WHERE codigo_insumo  = v_insumo.codigo_insumo
          AND estado_registro = 'VÁLIDO'
          AND TO_CHAR(fecha, 'YYYY-MM') = p_mes;

        -- Total generado en ventas de este insumo en el mes
        SELECT COALESCE(SUM(total), 0)
        INTO v_ingreso_salidas
        FROM public.registro_ventas
        WHERE codigo_insumo  = v_insumo.codigo_insumo
          AND estado_registro = 'VÁLIDO'
          AND TO_CHAR(fecha, 'YYYY-MM') = p_mes;

        INSERT INTO public.registro_auditorias_cierres (
            id_periodo,
            codigo_insumo,
            tipo_registro,
            fecha_cierre,
            cantidad_sistema,
            cantidad_fisica,
            diferencia,
            costo_unitario_snapshot,
            costo_entradas_mes,
            ingreso_salidas_mes,
            estado,
            observacion
        ) VALUES (
            v_id_periodo,
            v_insumo.codigo_insumo,
            'SNAPSHOT',
            v_fecha_corte,
            COALESCE(v_stock_calc, 0),
            NULL,       -- el admin la completa durante la auditoría
            NULL,
            v_costo_ultimo,
            v_costo_entradas,
            v_ingreso_salidas,
            'PENDIENTE',
            NULL
        )
        ON CONFLICT (id_periodo, codigo_insumo, tipo_registro) DO UPDATE SET
            cantidad_sistema        = EXCLUDED.cantidad_sistema,
            costo_unitario_snapshot = EXCLUDED.costo_unitario_snapshot,
            costo_entradas_mes      = EXCLUDED.costo_entradas_mes,
            ingreso_salidas_mes     = EXCLUDED.ingreso_salidas_mes,
            fecha_cierre            = EXCLUDED.fecha_cierre;

        v_count := v_count + 1;
    END LOOP;

    -- -------------------------------------------------------
    -- 3. Totales financieros del período completo
    -- -------------------------------------------------------
    UPDATE public.periodos_inventario SET
        total_costo_entradas = (
            SELECT COALESCE(SUM(costo_total), 0)
            FROM public.registro_compras
            WHERE estado_registro = 'VÁLIDO'
              AND TO_CHAR(fecha, 'YYYY-MM') = p_mes
        ),
        total_ingreso_salidas = (
            SELECT COALESCE(SUM(total), 0)
            FROM public.registro_ventas
            WHERE estado_registro = 'VÁLIDO'
              AND TO_CHAR(fecha, 'YYYY-MM') = p_mes
        )
    WHERE id_periodo = v_id_periodo;

    -- -------------------------------------------------------
    -- 4. Crear INVENTARIO_INICIAL provisional del mes siguiente
    -- -------------------------------------------------------
    v_mes_siguiente := TO_CHAR(v_fecha_inicio + INTERVAL '1 month', 'YYYY-MM');

    PERFORM public.fn_crear_inventario_inicial_provisional(
        v_mes_siguiente,
        v_id_periodo
    );

    RETURN jsonb_build_object(
        'exito',               true,
        'periodo',             p_mes,
        'id_periodo',          v_id_periodo,
        'insumos_procesados',  v_count,
        'mes_siguiente_listo', v_mes_siguiente,
        'timestamp',           v_fecha_corte
    );

EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'exito',   false,
        'error',   SQLERRM,
        'detalle', SQLSTATE
    );
END;
$function$
;

-- Permissions

ALTER FUNCTION public.fn_snapshot_cierre_mensual(text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.fn_snapshot_cierre_mensual(text) TO public;
GRANT ALL ON FUNCTION public.fn_snapshot_cierre_mensual(text) TO postgres;
GRANT ALL ON FUNCTION public.fn_snapshot_cierre_mensual(text) TO anon;
GRANT ALL ON FUNCTION public.fn_snapshot_cierre_mensual(text) TO authenticated;
GRANT ALL ON FUNCTION public.fn_snapshot_cierre_mensual(text) TO service_role;

-- DROP FUNCTION public.fn_ultimo_costo_compra(text);

CREATE OR REPLACE FUNCTION public.fn_ultimo_costo_compra(p_codigo text)
 RETURNS numeric
 LANGUAGE sql
 STABLE SECURITY DEFINER
AS $function$
    SELECT costo_unitario
    FROM public.registro_compras
    WHERE codigo_insumo  = p_codigo
      AND estado_registro = 'VÁLIDO'
      AND costo_unitario IS NOT NULL
      AND costo_unitario  > 0
    ORDER BY fecha DESC
    LIMIT 1;
$function$
;

-- Permissions

ALTER FUNCTION public.fn_ultimo_costo_compra(text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.fn_ultimo_costo_compra(text) TO public;
GRANT ALL ON FUNCTION public.fn_ultimo_costo_compra(text) TO postgres;
GRANT ALL ON FUNCTION public.fn_ultimo_costo_compra(text) TO anon;
GRANT ALL ON FUNCTION public.fn_ultimo_costo_compra(text) TO authenticated;
GRANT ALL ON FUNCTION public.fn_ultimo_costo_compra(text) TO service_role;

-- DROP FUNCTION public.get_catalogo_summary_rpc();

CREATE OR REPLACE FUNCTION public.get_catalogo_summary_rpc()
 RETURNS jsonb
 LANGUAGE sql
 STABLE
AS $function$
    SELECT jsonb_build_object(
        'total_compras', COALESCE(
            (SELECT SUM(costo_total) FROM public.registro_compras
             WHERE estado_registro = 'VÁLIDO'), 0),
        'total_ventas', COALESCE(
            (SELECT SUM(total) FROM public.registro_ventas
             WHERE estado_registro = 'VÁLIDO'), 0)
    );
$function$
;

-- Permissions

ALTER FUNCTION public.get_catalogo_summary_rpc() OWNER TO postgres;
GRANT ALL ON FUNCTION public.get_catalogo_summary_rpc() TO public;
GRANT ALL ON FUNCTION public.get_catalogo_summary_rpc() TO postgres;
GRANT ALL ON FUNCTION public.get_catalogo_summary_rpc() TO anon;
GRANT ALL ON FUNCTION public.get_catalogo_summary_rpc() TO authenticated;
GRANT ALL ON FUNCTION public.get_catalogo_summary_rpc() TO service_role;

-- DROP FUNCTION public.get_compras_summary_rpc(text, text);

CREATE OR REPLACE FUNCTION public.get_compras_summary_rpc(mes_actual text, dia_hoy text)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
AS $function$
    SELECT jsonb_build_object(
        'total_mes',      COALESCE(SUM(
            CASE WHEN TO_CHAR(fecha, 'YYYY-MM') = mes_actual
                 THEN costo_total ELSE 0 END), 0),
        'total_hoy',      COALESCE(SUM(
            CASE WHEN fecha::DATE = dia_hoy::DATE
                 THEN costo_total ELSE 0 END), 0),
        'cantidad_total', COALESCE(SUM(cantidad), 0)
    )
    FROM public.registro_compras
    WHERE estado_registro = 'VÁLIDO';
$function$
;

-- Permissions

ALTER FUNCTION public.get_compras_summary_rpc(text, text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.get_compras_summary_rpc(text, text) TO public;
GRANT ALL ON FUNCTION public.get_compras_summary_rpc(text, text) TO postgres;
GRANT ALL ON FUNCTION public.get_compras_summary_rpc(text, text) TO anon;
GRANT ALL ON FUNCTION public.get_compras_summary_rpc(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.get_compras_summary_rpc(text, text) TO service_role;

-- DROP FUNCTION public.get_inventario_kpis_rpc(text);

CREATE OR REPLACE FUNCTION public.get_inventario_kpis_rpc(mes_actual text)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
AS $function$
    SELECT jsonb_build_object(
        'valor_inventario', COALESCE(SUM(costo_total_insumo), 0),
        'alertas_criticas', COUNT(
            CASE WHEN stock_actual <= stock_minimo
                  AND stock_actual >= 0
                 THEN 1 END
        )
    )
    FROM public.vista_inventario_completo;
$function$
;

-- Permissions

ALTER FUNCTION public.get_inventario_kpis_rpc(text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.get_inventario_kpis_rpc(text) TO public;
GRANT ALL ON FUNCTION public.get_inventario_kpis_rpc(text) TO postgres;
GRANT ALL ON FUNCTION public.get_inventario_kpis_rpc(text) TO anon;
GRANT ALL ON FUNCTION public.get_inventario_kpis_rpc(text) TO authenticated;
GRANT ALL ON FUNCTION public.get_inventario_kpis_rpc(text) TO service_role;

-- DROP FUNCTION public.get_kpis_por_categoria_rpc();

CREATE OR REPLACE FUNCTION public.get_kpis_por_categoria_rpc()
 RETURNS jsonb
 LANGUAGE sql
 STABLE
AS $function$
    SELECT COALESCE(jsonb_agg(sub), '[]'::jsonb)
    FROM (
        SELECT
            categoria,
            COALESCE(SUM(costo_total_insumo), 0)  AS costo_inventario,
            COALESCE(SUM(venta_total_insumo), 0)   AS ventas_totales,
            CASE
                WHEN SUM(costo_total_insumo) > 0
                THEN ROUND(
                    (SUM(venta_total_insumo) - SUM(costo_total_insumo))
                    / SUM(costo_total_insumo) * 100, 2
                )
                ELSE 0
            END AS rentabilidad,
            CASE
                WHEN SUM(costo_total_insumo) > 0
                THEN ROUND(
                    SUM(venta_total_insumo) / SUM(costo_total_insumo), 2
                )
                ELSE 0
            END AS rotacion
        FROM public.vista_inventario_completo
        WHERE categoria IS NOT NULL
        GROUP BY categoria
        ORDER BY costo_inventario DESC
    ) sub;
$function$
;

-- Permissions

ALTER FUNCTION public.get_kpis_por_categoria_rpc() OWNER TO postgres;
GRANT ALL ON FUNCTION public.get_kpis_por_categoria_rpc() TO public;
GRANT ALL ON FUNCTION public.get_kpis_por_categoria_rpc() TO postgres;
GRANT ALL ON FUNCTION public.get_kpis_por_categoria_rpc() TO anon;
GRANT ALL ON FUNCTION public.get_kpis_por_categoria_rpc() TO authenticated;
GRANT ALL ON FUNCTION public.get_kpis_por_categoria_rpc() TO service_role;

-- DROP FUNCTION public.get_tendencia_diaria_rpc(text);

CREATE OR REPLACE FUNCTION public.get_tendencia_diaria_rpc(mes_actual text)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
AS $function$
    SELECT COALESCE(jsonb_agg(sub ORDER BY sub.dia), '[]'::jsonb)
    FROM (
        SELECT
            dia::TEXT AS dia,
            SUM(ventas)  AS ventas,
            SUM(compras) AS compras
        FROM (
            SELECT fecha::DATE AS dia,
                   SUM(total)       AS ventas,
                   0                AS compras
            FROM public.registro_ventas
            WHERE estado_registro = 'VÁLIDO'
              AND TO_CHAR(fecha, 'YYYY-MM') = mes_actual
            GROUP BY fecha::DATE

            UNION ALL

            SELECT fecha::DATE AS dia,
                   0                AS ventas,
                   SUM(costo_total) AS compras
            FROM public.registro_compras
            WHERE estado_registro = 'VÁLIDO'
              AND TO_CHAR(fecha, 'YYYY-MM') = mes_actual
            GROUP BY fecha::DATE
        ) mov
        GROUP BY dia
    ) sub;
$function$
;

-- Permissions

ALTER FUNCTION public.get_tendencia_diaria_rpc(text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.get_tendencia_diaria_rpc(text) TO public;
GRANT ALL ON FUNCTION public.get_tendencia_diaria_rpc(text) TO postgres;
GRANT ALL ON FUNCTION public.get_tendencia_diaria_rpc(text) TO anon;
GRANT ALL ON FUNCTION public.get_tendencia_diaria_rpc(text) TO authenticated;
GRANT ALL ON FUNCTION public.get_tendencia_diaria_rpc(text) TO service_role;

-- DROP FUNCTION public.get_top_ventas_mes_rpc(text, int4);

CREATE OR REPLACE FUNCTION public.get_top_ventas_mes_rpc(mes_actual text, limite integer DEFAULT 10)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
AS $function$
    SELECT COALESCE(jsonb_agg(sub), '[]'::jsonb)
    FROM (
        SELECT
            rv.codigo_insumo          AS codigo,
            ci.nombre                 AS producto,
            SUM(rv.total)             AS ingreso_total,
            SUM(rv.cantidad)          AS unidades_vendidas
        FROM public.registro_ventas rv
        LEFT JOIN public.catalogo_insumos ci
               ON ci.codigo_insumo = rv.codigo_insumo
        WHERE rv.estado_registro = 'VÁLIDO'
          AND TO_CHAR(rv.fecha, 'YYYY-MM') = mes_actual
        GROUP BY rv.codigo_insumo, ci.nombre
        ORDER BY ingreso_total DESC
        LIMIT limite
    ) sub;
$function$
;

-- Permissions

ALTER FUNCTION public.get_top_ventas_mes_rpc(text, int4) OWNER TO postgres;
GRANT ALL ON FUNCTION public.get_top_ventas_mes_rpc(text, int4) TO public;
GRANT ALL ON FUNCTION public.get_top_ventas_mes_rpc(text, int4) TO postgres;
GRANT ALL ON FUNCTION public.get_top_ventas_mes_rpc(text, int4) TO anon;
GRANT ALL ON FUNCTION public.get_top_ventas_mes_rpc(text, int4) TO authenticated;
GRANT ALL ON FUNCTION public.get_top_ventas_mes_rpc(text, int4) TO service_role;

-- DROP FUNCTION public.get_ventas_summary_rpc(text, text);

CREATE OR REPLACE FUNCTION public.get_ventas_summary_rpc(mes_actual text, dia_hoy text)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
AS $function$
    SELECT jsonb_build_object(
        'total_historico', COALESCE(SUM(total), 0),
        'total_mes',       COALESCE(SUM(
            CASE WHEN TO_CHAR(fecha, 'YYYY-MM') = mes_actual
                 THEN total ELSE 0 END), 0),
        'total_hoy',       COALESCE(SUM(
            CASE WHEN fecha::DATE = dia_hoy::DATE
                 THEN total ELSE 0 END), 0),
        'iva_historico',   COALESCE(SUM(iva), 0),
        'iva_hoy',         COALESCE(SUM(
            CASE WHEN fecha::DATE = dia_hoy::DATE
                 THEN iva ELSE 0 END), 0)
    )
    FROM public.registro_ventas
    WHERE estado_registro = 'VÁLIDO';
$function$
;

-- Permissions

ALTER FUNCTION public.get_ventas_summary_rpc(text, text) OWNER TO postgres;
GRANT ALL ON FUNCTION public.get_ventas_summary_rpc(text, text) TO public;
GRANT ALL ON FUNCTION public.get_ventas_summary_rpc(text, text) TO postgres;
GRANT ALL ON FUNCTION public.get_ventas_summary_rpc(text, text) TO anon;
GRANT ALL ON FUNCTION public.get_ventas_summary_rpc(text, text) TO authenticated;
GRANT ALL ON FUNCTION public.get_ventas_summary_rpc(text, text) TO service_role;

-- DROP FUNCTION public.obtener_inventario_por_fecha(timestamptz);

CREATE OR REPLACE FUNCTION public.obtener_inventario_por_fecha(p_fecha_corte timestamp with time zone)
 RETURNS TABLE(codigo_insumo text, nombre text, categoria text, stock_inicial bigint, entradas bigint, salidas bigint, stock_real bigint)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT 
        c.codigo_insumo,
        c.nombre,
        c.categoria,
        COALESCE(inv.cantidad_inicial, 0)::BIGINT AS stock_inicial,
        COALESCE(comp.entradas, 0)::BIGINT AS entradas,
        COALESCE(ven.salidas, 0)::BIGINT AS salidas,
        (COALESCE(inv.cantidad_inicial, 0) + 
         COALESCE(comp.entradas, 0) - 
         COALESCE(ven.salidas, 0) + 
         COALESCE(ajustes.neto_ajustes, 0))::BIGINT AS stock_real
    FROM public.catalogo_insumos c
    LEFT JOIN (
        -- Filtra el inventario inicial validado hasta esa fecha
        SELECT a.codigo_insumo, SUM(a.cantidad_fisica) AS cantidad_inicial 
        FROM public.registro_auditorias_cierres a
        WHERE a.tipo_registro = 'INVENTARIO_INICIAL' AND a.estado = 'APLICADO' AND a.fecha_cierre <= p_fecha_corte
        GROUP BY a.codigo_insumo
    ) inv ON c.codigo_insumo = inv.codigo_insumo
    LEFT JOIN (
        -- Suma compras hasta esa fecha
        SELECT r.codigo_insumo, SUM(r.cantidad) AS entradas 
        FROM public.registro_compras r
        WHERE r.estado_registro = 'VÁLIDO' AND r.fecha <= p_fecha_corte
        GROUP BY r.codigo_insumo
    ) comp ON c.codigo_insumo = comp.codigo_insumo
    LEFT JOIN (
        -- Suma ventas hasta esa fecha
        SELECT v.codigo_insumo, SUM(v.cantidad) AS salidas 
        FROM public.registro_ventas v
        WHERE v.estado_registro = 'VÁLIDO' AND v.fecha <= p_fecha_corte
        GROUP BY v.codigo_insumo
    ) ven ON c.codigo_insumo = ven.codigo_insumo
    LEFT JOIN (
        -- Suma/Resta ajustes hasta esa fecha
        SELECT aj.codigo_insumo, 
               SUM(CASE 
                   WHEN aj.tipo_ajuste = 'ENTRADA_POR_SOBRANTE' THEN aj.cantidad 
                   WHEN aj.tipo_ajuste = 'SALIDA_POR_FALTANTE' THEN -aj.cantidad 
                   ELSE 0 
               END) AS neto_ajustes
        FROM public.registro_ajustes_inventario aj
        WHERE aj.estado_registro = 'VÁLIDO' AND aj.fecha_ajuste <= p_fecha_corte
        GROUP BY aj.codigo_insumo
    ) ajustes ON c.codigo_insumo = ajustes.codigo_insumo;
END;
$function$
;

-- Permissions

ALTER FUNCTION public.obtener_inventario_por_fecha(timestamptz) OWNER TO postgres;
GRANT ALL ON FUNCTION public.obtener_inventario_por_fecha(timestamptz) TO public;
GRANT ALL ON FUNCTION public.obtener_inventario_por_fecha(timestamptz) TO postgres;
GRANT ALL ON FUNCTION public.obtener_inventario_por_fecha(timestamptz) TO anon;
GRANT ALL ON FUNCTION public.obtener_inventario_por_fecha(timestamptz) TO authenticated;
GRANT ALL ON FUNCTION public.obtener_inventario_por_fecha(timestamptz) TO service_role;

-- DROP FUNCTION public.rls_auto_enable();

CREATE OR REPLACE FUNCTION public.rls_auto_enable()
 RETURNS event_trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$function$
;

-- Permissions

ALTER FUNCTION public.rls_auto_enable() OWNER TO postgres;
GRANT ALL ON FUNCTION public.rls_auto_enable() TO public;
GRANT ALL ON FUNCTION public.rls_auto_enable() TO postgres;
GRANT ALL ON FUNCTION public.rls_auto_enable() TO anon;
GRANT ALL ON FUNCTION public.rls_auto_enable() TO authenticated;
GRANT ALL ON FUNCTION public.rls_auto_enable() TO service_role;


-- Permissions

GRANT ALL ON SCHEMA public TO pg_database_owner;
GRANT USAGE ON SCHEMA public TO public;
GRANT USAGE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT TRUNCATE, REFERENCES, MAINTAIN, UPDATE, SELECT, INSERT, DELETE, TRIGGER ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT TRUNCATE, REFERENCES, MAINTAIN, UPDATE, SELECT, INSERT, DELETE, TRIGGER ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT TRUNCATE, REFERENCES, MAINTAIN, UPDATE, SELECT, INSERT, DELETE, TRIGGER ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT TRUNCATE, REFERENCES, MAINTAIN, UPDATE, SELECT, INSERT, DELETE, TRIGGER ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT UPDATE, SELECT, USAGE ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT UPDATE, SELECT, USAGE ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT UPDATE, SELECT, USAGE ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT UPDATE, SELECT, USAGE ON SEQUENCES TO service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT UPDATE, SELECT, USAGE ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT UPDATE, SELECT, USAGE ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT UPDATE, SELECT, USAGE ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT UPDATE, SELECT, USAGE ON SEQUENCES TO service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT TRUNCATE, REFERENCES, MAINTAIN, UPDATE, SELECT, INSERT, DELETE, TRIGGER ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT TRUNCATE, REFERENCES, MAINTAIN, UPDATE, SELECT, INSERT, DELETE, TRIGGER ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT TRUNCATE, REFERENCES, MAINTAIN, UPDATE, SELECT, INSERT, DELETE, TRIGGER ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT TRUNCATE, REFERENCES, MAINTAIN, UPDATE, SELECT, INSERT, DELETE, TRIGGER ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO service_role;
````

## File: ui/layout/sidebar.py
````python
import flet as ft
from config import Config

class Sidebar(ft.Container):
    def __init__(self, on_route_change):
        super().__init__()
        self.on_route_change = on_route_change
        self.is_expanded = True
        
        # Propiedades dinámicas del contenedor
        self.width = 250
        self.bgcolor = Config.COLOR_PRIMARY
        self.padding = 15
        self.border_radius = ft.border_radius.only(top_right=15, bottom_right=15)
        self.animate = ft.animation.Animation(300, ft.AnimationCurve.DECELERATE)
        
        # Botón para colapsar/expandir
        self.toggle_btn = ft.IconButton(
            icon=ft.icons.MENU,
            icon_color="white",
            on_click=self.toggle_sidebar,
            tooltip="Ocultar/Mostrar Menú"
        )
        
        # Logo y textos
        self.logo_icon = ft.Icon(ft.icons.STOREFRONT, color="white", size=40)
        self.logo_title = ft.Text("Doña Mary", color="white", size=24, weight="bold")
        self.logo_subtitle = ft.Text("Abarrotes & Desechables", color="white70", size=12)
        
        self.header_content = ft.Column([
            self.logo_icon,
            self.logo_title,
            self.logo_subtitle,
        ], horizontal_alignment="center", spacing=5)

        self.toggle_row = ft.Row([self.toggle_btn], alignment=ft.MainAxisAlignment.END)

        # Almacenar referencias de los botones del menú
        self.menu_items = {}
        
        self.footer_text = ft.Text("Elaborado por: Eliana Garces 2026", color="white54", size=10, text_align=ft.TextAlign.CENTER)
        
        self.content = ft.Column(
            controls=[
                # Cabecera con botón de toggle
                self.toggle_row,
                ft.Container(
                    content=self.header_content,
                    padding=ft.padding.only(bottom=20),
                    alignment=ft.alignment.center
                ),
                
                # Menú
                self._create_menu_item("Dashboard", ft.icons.DASHBOARD, "dashboard"),
                self._create_menu_item("Inventario", ft.icons.INVENTORY_2, "inventario"),
                self._create_menu_item("Compras", ft.icons.ADD_SHOPPING_CART, "compras"),
                self._create_menu_item("Ventas", ft.icons.POINT_OF_SALE, "ventas"),
                self._create_menu_item("Ajustes de Inventario", ft.icons.TUNE, "ajustes_inventario"),
                self._create_menu_item("Cierre de Mes", ft.icons.FACT_CHECK, "cierre_mes"),
                
                ft.Container(expand=True), # Spacer
                
                self._create_menu_item("Configuración", ft.icons.SETTINGS, "settings"),
                
                # Footer Copyright
                ft.Container(
                    content=self.footer_text,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=10, bottom=5)
                )
            ],
            spacing=5
        )
        
    def _create_menu_item(self, text, icon, route, is_sub_item=False):
        icon_size = 20 if is_sub_item else 24
        text_size = 13 if is_sub_item else 14
        pad_left = 35 if is_sub_item else 15
        
        item = ft.ListTile(
            leading=ft.Icon(icon, color="white70", size=icon_size),
            title=ft.Text(text, color="white70", size=text_size),
            hover_color=ft.colors.with_opacity(0.1, "white"),
            content_padding=ft.padding.only(left=pad_left, right=15),
            on_click=lambda _: self.on_route_change(route),
            data={"is_sub_item": is_sub_item, "pad_left": pad_left}
        )
        self.menu_items[route] = item
        return item
        
    def update_active_route(self, route_name):
        for route, item in self.menu_items.items():
            is_active = (route == route_name)
            item.bgcolor = ft.colors.with_opacity(0.2, "white") if is_active else None
            item.leading.color = "white" if is_active else "white70"
            item.title.color = "white" if is_active else "white70"
            item.title.weight = "bold" if is_active else "normal"
        self.update()

    def toggle_sidebar(self, e):
        """Alterna el ancho del sidebar y oculta/muestra los textos."""
        self.is_expanded = not self.is_expanded
        
        # Ajustar ancho
        self.width = 250 if self.is_expanded else 70
        
        # Mostrar u ocultar elementos del header según el estado
        self.logo_title.visible = self.is_expanded
        self.logo_subtitle.visible = self.is_expanded
        self.logo_icon.size = 40 if self.is_expanded else 24
        
        # Mostrar u ocultar el footer
        self.footer_text.visible = self.is_expanded
        
        self.toggle_row.alignment = ft.MainAxisAlignment.END if self.is_expanded else ft.MainAxisAlignment.CENTER
        
        # Mostrar u ocultar el texto de los ListTile
        for control in self.content.controls:
            if isinstance(control, ft.ListTile):
                control.title.visible = self.is_expanded
                pad_left = control.data["pad_left"] if self.is_expanded else 8
                control.content_padding = ft.padding.only(left=pad_left, right=15 if self.is_expanded else 8)
                
        self.update()
````

## File: ui/views/ajustes_inventario.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient

class AjustesInventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        self.tipo_ajuste_actual = "ENTRADA"
        
        # Mapeo estricto contra restricciones de BD
        self.mapa_motivos = {
            "Sobrante de Inventario": "ENTRADA_POR_SOBRANTE",
            "Donación Entrante": "AJUSTE_ENTRADA",
            "Devolución Cliente": "AJUSTE_ENTRADA",
            "Daño / Merma": "AJUSTE_SALIDA",
            "Vencimiento": "BAJA_VENCIMIENTO",
            "Pérdida": "SALIDA_POR_FALTANTE",
            "Consumo Familiar": "AJUSTE_SALIDA",
            "Consumo Cliente (Cortesía)": "AJUSTE_SALIDA",
            "Donación Saliente": "AJUSTE_SALIDA",
            "Otro (Entrada)": "AJUSTE_ENTRADA",
            "Otro (Salida)": "AJUSTE_SALIDA"
        }

        # --- Labels reactivos de Resumen ---
        self.lbl_ent_actual = ft.Text("$0.00", weight="bold")
        self.lbl_ent_pos = ft.Text("$0.00", weight="bold", color="green")
        self.lbl_sal_neg = ft.Text("$0.00", weight="bold", color="red")
        self.lbl_ent_neto = ft.Text("$0.00", weight="bold")
        self.lbl_ent_proyectado = ft.Text("$0.00", weight="bold", color=Config.COLOR_PRIMARY)

        # --- Paginación y Filtros ---
        self.data_completa = []
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0

        self.search_input = ft.TextField(
            hint_text="Buscar código o nombre...",
            prefix_icon=ft.icons.SEARCH,
            height=40,
            expand=2,
            content_padding=10,
            on_change=lambda e: self._on_filter_change()
        )
        
        self.date_picker = ft.DatePicker(on_change=lambda e: self._on_filter_change())
        self.btn_date = ft.OutlinedButton(
            text="Filtro Fecha",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=40,
            width=150
        )
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            icon_color="red",
            visible=False,
            on_click=self._clear_date
        )

        self.drop_tipo = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Entrada"), ft.dropdown.Option("Salida")],
            value="Todos", label="Tipo", dense=True, width=150, height=40, content_padding=10, on_change=lambda e: self._on_filter_change()
        )
        
        motivos_combinados = ["Todos"] + list(self.mapa_motivos.keys())
        self.drop_motivo = ft.Dropdown(
            options=[ft.dropdown.Option(m) for m in motivos_combinados],
            value="Todos", label="Motivo", dense=True, width=200, height=40, content_padding=10, on_change=lambda e: self._on_filter_change()
        )

        self.btn_prev = ft.IconButton(icon=ft.icons.ARROW_BACK_IOS, on_click=self._prev_page, disabled=True)
        self.btn_next = ft.IconButton(icon=ft.icons.ARROW_FORWARD_IOS, on_click=self._next_page, disabled=True)
        self.lbl_page_info = ft.Text("Pág 1 de 1", weight="bold")

        # --- Vista de Tarjetas (Lista) ---
        self.lista_ajustes = ft.ListView(expand=True, spacing=10, auto_scroll=False)
        self.btn_agregar_ajuste = ft.ElevatedButton("Registrar Ajuste", icon=ft.icons.ADD, bgcolor=Config.COLOR_PRIMARY, color="white", on_click=lambda e: self.abrir_modal_ajuste())

        # --- Modal ---
        self.modal_ajuste = self._crear_modal_formulario()

        # --- Layout Principal Unificado ---
        kpi_bar = ft.Container(
            content=ft.Row([
                ft.Column([ft.Text("Valor Inventario Base:", size=11, color="grey"), self.lbl_ent_actual], spacing=0),
                ft.Container(width=1, height=30, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Valor Entradas (+):", size=11, color="grey"), self.lbl_ent_pos], spacing=0),
                ft.Container(width=1, height=30, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Valor Salidas (-):", size=11, color="grey"), self.lbl_sal_neg], spacing=0),
                ft.Container(width=1, height=30, bgcolor="#eeeeee"),
                ft.Column([ft.Text("Impacto Neto:", size=11, color="grey"), self.lbl_ent_neto], spacing=0),
                ft.Container(expand=True),
                ft.Column([ft.Text("Inventario Proyectado:", size=11, color="grey"), self.lbl_ent_proyectado], spacing=0, horizontal_alignment="end"),
            ], alignment=ft.MainAxisAlignment.START),
            padding=15, bgcolor="#fafafa", border_radius=8, border=ft.border.all(1, "#eeeeee")
        )
        
        filtros_row = ft.Row([
            self.search_input,
            self.btn_date,
            self.btn_clear_date,
            self.drop_tipo,
            self.drop_motivo,
            ft.Container(expand=True),
            self.btn_agregar_ajuste
        ], spacing=10)
        
        paginacion_row = ft.Row([
            ft.Container(expand=True),
            self.btn_prev,
            self.lbl_page_info,
            self.btn_next
        ], alignment=ft.MainAxisAlignment.END)

        self.content = ft.Column([
            ft.Text("Gestión y Ajustes de Inventario", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            kpi_bar,
            filtros_row,
            ft.Container(content=self.lista_ajustes, expand=True, bgcolor="#f5f5f5", border_radius=10, padding=10, shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))),
            paginacion_row
        ], expand=True)

    def _crear_modal_formulario(self):
        def on_tipo_change(e):
            tipo = self.form_tipo_ajuste.value
            if tipo == "ENTRADA":
                self.form_motivo.options = [ft.dropdown.Option(x) for x in ["Sobrante de Inventario", "Donación Entrante", "Devolución Cliente", "Otro (Entrada)"]]
            elif tipo == "SALIDA":
                self.form_motivo.options = [ft.dropdown.Option(x) for x in ["Daño / Merma", "Vencimiento", "Pérdida", "Consumo Familiar", "Consumo Cliente (Cortesía)", "Donación Saliente", "Otro (Salida)"]]
            else:
                self.form_motivo.options = []
            self.form_motivo.value = None
            if self.page: self.page.update()

        self.form_tipo_ajuste = ft.Dropdown(label="Tipo de Movimiento", options=[ft.dropdown.Option("ENTRADA"), ft.dropdown.Option("SALIDA")], dense=True, expand=True, content_padding=10, border_radius=8, on_change=on_tipo_change)
        
        self.form_codigo = ft.TextField(label="Código Insumo", width=120, dense=True, content_padding=10, border_radius=8, on_blur=self.buscar_detalle_insumo)
        self.form_nombre = ft.Text("Nombre del Insumo...", color="grey", italic=True)
        self.form_motivo = ft.Dropdown(label="Motivo del Ajuste", dense=True, expand=True, content_padding=10, border_radius=8)
        self.form_cant = ft.TextField(label="Cantidad", expand=True, dense=True, content_padding=10, border_radius=8)
        self.form_costo = ft.TextField(label="Costo Unitario", expand=True, dense=True, content_padding=10, border_radius=8)
        self.form_obs = ft.TextField(label="Observación (Opcional)", expand=True, dense=True, multiline=True, min_lines=2, content_padding=10, border_radius=8)
        
        return ft.AlertDialog(
            title=ft.Text("Registrar Ajuste"),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Row([self.form_codigo, ft.Container(content=self.form_nombre, expand=True, padding=10, bgcolor="#f5f5f5", border_radius=8)]),
                    ft.Row([self.form_tipo_ajuste, self.form_motivo]),
                    ft.Row([self.form_cant, self.form_costo]),
                    ft.Row([self.form_obs])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cerrar_modal()),
                ft.ElevatedButton("Guardar Ajuste", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=self.on_guardar_ajuste)
            ]
        )

    # --- Lógica de Negocio ---
    def did_mount(self):
        if self.modal_ajuste not in self.page.overlay:
            self.page.overlay.append(self.modal_ajuste)
        if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        self.load_data()

    def buscar_detalle_insumo(self, e):
        codigo = self.form_codigo.value.strip()
        if not codigo: return
        detalle = self.db.get_insumo_detalle(codigo)
        if detalle:
            self.form_nombre.value = detalle.get("nombre", "")
            self.form_nombre.color = "black"
            self.form_costo.value = str(detalle.get("costo_unitario", 0))
        else:
            self.form_nombre.value = "Insumo no encontrado."
            self.form_nombre.color = "red"
        self.page.update()

    def abrir_modal_ajuste(self):
        self.modal_ajuste.title.value = "Registrar Ajuste de Inventario"
        
        # Limpiar valores y errores visuales
        self.form_tipo_ajuste.value = None
        self.form_tipo_ajuste.error_text = None
        
        self.form_motivo.options = []
        self.form_motivo.value = None
        self.form_motivo.error_text = None
        
        self.form_codigo.value = ""
        self.form_codigo.error_text = None
        
        self.form_nombre.value = "Nombre del Insumo..."
        self.form_nombre.color = "grey"
        
        self.form_cant.value = ""
        self.form_cant.error_text = None
        
        self.form_costo.value = ""
        self.form_costo.error_text = None
        
        self.form_obs.value = ""
        self.form_obs.error_text = None
        
        self.modal_ajuste.open = True
        self.page.update()

    def cerrar_modal(self):
        self.modal_ajuste.open = False
        self.page.update()

    def on_guardar_ajuste(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if self.page:
            self.update()
            
        threading.Thread(target=self._on_guardar_ajuste_worker, args=(btn_control,), daemon=True).start()

    def _on_guardar_ajuste_worker(self, btn_control):
        try:
            self.form_codigo.error_text = None
            self.form_cant.error_text = None
            self.form_costo.error_text = None
            if self.page:
                self.page.update()
                
            try:
                codigo = self.form_codigo.value.strip()
                motivo_ui = self.form_motivo.value
                cant = float(self.form_cant.value.replace(',', '.'))
                costo = float(self.form_costo.value.replace(',', '.'))
                obs = self.form_obs.value.strip()
            except ValueError:
                self.mostrar_alerta("Error en los formatos numéricos. Usa números válidos para cantidad y costo.", "red")
                return

            if not codigo or not motivo_ui or cant <= 0:
                self.mostrar_alerta("Completa los campos obligatorios y asegúrate que la cantidad sea mayor a cero.", "red")
                return

            tipo_bd = self.mapa_motivos.get(motivo_ui)
            if not tipo_bd: return

            datos = {
                "codigo_insumo": codigo,
                "tipo_ajuste": tipo_bd,
                "cantidad": cant,
                "costo_unitario_congelado": costo,
                "costo_total_ajuste": cant * costo,
                "motivo_observacion": obs if obs else motivo_ui,
                "estado_registro": "VÁLIDO"
            }

            if self.db.insert_ajuste_individual(datos):
                self.mostrar_alerta("Ajuste registrado exitosamente.", "green")
                self.cerrar_modal()
                self.load_data()
            else:
                self.mostrar_alerta("Error al registrar en la base de datos.", "red")
        except Exception as ex:
            if self.page:
                self.mostrar_alerta(f"Error interno: {str(ex)}", "red")
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.page.update()

    def anular_registro(self, id_ajuste):
        if self.db.anular_ajuste(id_ajuste):
            self.mostrar_alerta("Registro anulado. El stock ha sido revertido.", "orange")
            self.load_data()
        else:
            self.mostrar_alerta("Error al anular.", "red")

    def mostrar_alerta(self, msj, color):
        self.page.snack_bar = ft.SnackBar(ft.Text(msj), bgcolor=color)
        self.page.snack_bar.open = True

    def _clear_date(self, e):
        self.date_picker.value = None
        self.btn_date.text = "Filtro Fecha"
        self.btn_clear_date.visible = False
        self._on_filter_change()
        
    def _on_filter_change(self):
        self.current_page = 1
        if self.date_picker.value:
            self.btn_date.text = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_clear_date.visible = True
        self.render_table()
        
    def _prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_table()
            
    def _next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_table()

    def load_data(self):
        # Actualizar resúmenes globales
        kpis_inv = self.db.get_inventario_kpis()
        val_inv_base = kpis_inv.get('valor_inventario', 0)
        self.lbl_ent_actual.value = f"${val_inv_base:,.2f}"

        self.data_completa = self.db.get_ajustes_inventario()
        self.render_table(val_inv_base)

    def render_table(self, val_inv_base=None):
        if val_inv_base is None:
            # Recuperar el valor base desde el label si no se provee (eliminando caracteres de moneda)
            try:
                val_inv_base = float(self.lbl_ent_actual.value.replace('$', '').replace(',', ''))
            except:
                val_inv_base = 0.0

        self.lista_ajustes.controls.clear()
        
        filtro_texto = self.search_input.value.lower().strip() if self.search_input.value else ""
        filtro_fecha = self.date_picker.value.strftime("%Y-%m-%d") if self.date_picker.value else None
        filtro_tipo = self.drop_tipo.value
        filtro_motivo = self.drop_motivo.value
        
        filtered_data = []
        total_ent_pos = 0.0
        total_sal_neg = 0.0

        for aj in self.data_completa:
            es_entrada = aj["tipo_ajuste"] in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
            cat_info = aj.get("catalogo_insumos", {})
            nombre = cat_info.get("nombre", "Desconocido") if isinstance(cat_info, dict) else "Desconocido"
            
            # Reglas de coincidencia
            match_texto = filtro_texto in aj["codigo_insumo"].lower() or filtro_texto in nombre.lower()
            match_fecha = filtro_fecha is None or aj["fecha_ajuste"][:10] == filtro_fecha
            
            tipo_ajuste_str = "Entrada" if es_entrada else "Salida"
            match_tipo = filtro_tipo == "Todos" or filtro_tipo == tipo_ajuste_str
            match_motivo = filtro_motivo == "Todos" or filtro_motivo == aj["motivo_observacion"]
            
            if match_texto and match_fecha and match_tipo and match_motivo:
                filtered_data.append(aj)

            # Acumular KPIs sobre todos los datos VÁLIDOS del historial general, sin importar los filtros visuales.
            # (El usuario quiere ver el total global de impacto)
            if aj["estado_registro"] == "VÁLIDO":
                val_total = float(aj["costo_total_ajuste"])
                if es_entrada: total_ent_pos += val_total
                else: total_sal_neg += val_total

        import math
        self.total_records = len(filtered_data)
        self.total_pages = math.ceil(self.total_records / self.page_size) if self.total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = filtered_data[start_idx:end_idx]

        for aj in page_data:
            es_entrada = aj["tipo_ajuste"] in ('AJUSTE_ENTRADA', 'ENTRADA_POR_SOBRANTE')
            val_total = float(aj["costo_total_ajuste"])
            val_total_str = f"${val_total:,.2f}"
            
            cat_info = aj.get("catalogo_insumos", {})
            nombre = cat_info.get("nombre", "Desconocido") if isinstance(cat_info, dict) else "Desconocido"

            # Tarjeta de Ajuste (Card UI)
            tipo_bg = "#e8f5e9" if es_entrada else "#ffebee"
            tipo_color = "green" if es_entrada else "red"
            badge_tipo = ft.Container(
                content=ft.Text("Entrada" if es_entrada else "Salida", color=tipo_color, weight="bold", size=12),
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                bgcolor=tipo_bg,
                border_radius=15
            )

            fila1_cabecera = ft.Row([
                ft.Row([ft.Icon(ft.icons.CALENDAR_MONTH, size=16, color="grey"), ft.Text(aj["fecha_ajuste"][:10], color="grey")]),
                badge_tipo
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            fila2_principal = ft.Row([
                ft.Container(content=ft.Text(f"[{aj['codigo_insumo']}] {nombre}", size=16, weight="bold"), expand=True),
                ft.Text(val_total_str, size=16, weight="bold", color=tipo_color)
            ])

            fila3_detalles = ft.Row([
                ft.Container(content=ft.Text(f"Motivo: {aj['motivo_observacion']}", size=13, color="grey"), expand=True),
                ft.Text(f"Cant: {aj['cantidad']}", size=13, color="grey", weight="bold"),
                ft.Text(f"Costo U: ${aj['costo_unitario_congelado']:,.2f}", size=13, color="grey")
            ], alignment=ft.MainAxisAlignment.START, spacing=20)

            tarjeta_content = [fila1_cabecera, fila2_principal, fila3_detalles]

            if aj["estado_registro"] == "VÁLIDO":
                fila4_acciones = ft.Column([
                    ft.Divider(height=1, color="#f0f0f0"),
                    ft.Row([
                        ft.TextButton("Anular Registro", icon=ft.icons.CANCEL, icon_color="red", style=ft.ButtonStyle(color="red"), on_click=lambda e, id_aj=aj["id_ajuste"]: self.anular_registro(id_aj))
                    ], alignment=ft.MainAxisAlignment.END)
                ])
                tarjeta_content.append(fila4_acciones)
            else:
                fila4_acciones = ft.Column([
                    ft.Divider(height=1, color="#f0f0f0"),
                    ft.Row([
                        ft.Text("Registro Anulado", color="grey", italic=True)
                    ], alignment=ft.MainAxisAlignment.END)
                ])
                tarjeta_content.append(fila4_acciones)

            tarjeta = ft.Container(
                content=ft.Column(tarjeta_content, spacing=8),
                bgcolor="white",
                padding=15,
                border_radius=8,
                border=ft.border.all(1, "#e0e0e0")
            )
            self.lista_ajustes.controls.append(tarjeta)
            
        # Actualización UI
        self.btn_prev.disabled = self.current_page <= 1
        self.btn_next.disabled = self.current_page >= self.total_pages
        self.lbl_page_info.value = f"Pág {self.current_page} de {self.total_pages} ({self.total_records} reg.)"

        # Configuración de KPIs Dinámicos
        self.lbl_ent_pos.value = f"+${total_ent_pos:,.2f}"
        self.lbl_sal_neg.value = f"-${total_sal_neg:,.2f}"
        
        impacto_neto = total_ent_pos - total_sal_neg
        self.lbl_ent_neto.value = f"{'+' if impacto_neto >= 0 else '-'}${abs(impacto_neto):,.2f}"
        
        self.lbl_ent_proyectado.value = f"${(val_inv_base + impacto_neto):,.2f}"

        if self.page:
            self.page.update()
````

## File: cargas_locales.json
````json
{
    "2026-08-05_Remisi\u00f3n": {
        "1": {
            "id": 1,
            "pagina": 1,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-05",
            "archivo": "pdfs_locales/ventas_2026-08-05_Remisi\u00f3n_Pag_1.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37921",
                    "productos": [
                        {
                            "cantidad": 37,
                            "codigo_item": "0847",
                            "costo_total": 111000,
                            "iva": 17723,
                            "subtotal": 93277
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0658",
                            "costo_total": 37950,
                            "iva": 6059,
                            "subtotal": 31891
                        },
                        {
                            "cantidad": 50,
                            "codigo_item": "0331",
                            "costo_total": 20000,
                            "iva": 3193,
                            "subtotal": 16807
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0653",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0399",
                            "costo_total": 30500,
                            "iva": 4870,
                            "subtotal": 25630
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0424",
                            "costo_total": 9500,
                            "iva": 1517,
                            "subtotal": 7983
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37922",
                    "productos": [
                        {
                            "cantidad": 3,
                            "codigo_item": "1839",
                            "costo_total": 9300,
                            "iva": 1485,
                            "subtotal": 7815
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0681",
                            "costo_total": 8600,
                            "iva": 1373,
                            "subtotal": 7227
                        },
                        {
                            "cantidad": 50,
                            "codigo_item": "4860",
                            "costo_total": 25000,
                            "iva": 3992,
                            "subtotal": 21008
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0644",
                            "costo_total": 11400,
                            "iva": 1820,
                            "subtotal": 9580
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "4156",
                            "costo_total": 8950,
                            "iva": 1429,
                            "subtotal": 7521
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "2206",
                            "costo_total": 5300,
                            "iva": 846,
                            "subtotal": 4454
                        },
                        {
                            "cantidad": 40,
                            "codigo_item": "0571-1",
                            "costo_total": 22800,
                            "iva": 3640,
                            "subtotal": 19160
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0105",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "2016",
                            "costo_total": 7800,
                            "iva": 1245,
                            "subtotal": 6555
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37923",
                    "productos": [
                        {
                            "cantidad": 8,
                            "codigo_item": "0858",
                            "costo_total": 33200,
                            "iva": 5301,
                            "subtotal": 27899
                        },
                        {
                            "cantidad": 8,
                            "codigo_item": "0690",
                            "costo_total": 50000,
                            "iva": 7983,
                            "subtotal": 42017
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0304",
                            "costo_total": 20400,
                            "iva": 3257,
                            "subtotal": 17143
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0313",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0713",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0171",
                            "costo_total": 5850,
                            "iva": 934,
                            "subtotal": 4916
                        },
                        {
                            "cantidad": 12,
                            "codigo_item": "0250",
                            "costo_total": 114000,
                            "iva": 18202,
                            "subtotal": 95798
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0578",
                            "costo_total": 95000,
                            "iva": 15168,
                            "subtotal": 79832
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0649",
                            "costo_total": 30900,
                            "iva": 4934,
                            "subtotal": 25966
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37924",
                    "productos": [
                        {
                            "cantidad": 200,
                            "codigo_item": "0570",
                            "costo_total": 82800,
                            "iva": 13220,
                            "subtotal": 69580
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0572",
                            "costo_total": 50000,
                            "iva": 7983,
                            "subtotal": 42017
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0658",
                            "costo_total": 59500,
                            "iva": 9500,
                            "subtotal": 50000
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0563",
                            "costo_total": 32200,
                            "iva": 5141,
                            "subtotal": 27059
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "0560",
                            "costo_total": 30000,
                            "iva": 4790,
                            "subtotal": 25210
                        },
                        {
                            "cantidad": 7,
                            "codigo_item": "0558",
                            "costo_total": 32200,
                            "iva": 5141,
                            "subtotal": 27059
                        },
                        {
                            "cantidad": 12,
                            "codigo_item": "0554",
                            "costo_total": 26400,
                            "iva": 4215,
                            "subtotal": 22185
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0537",
                            "costo_total": 19998,
                            "iva": 3193,
                            "subtotal": 16805
                        }
                    ]
                }
            ]
        },
        "2": {
            "id": 2,
            "pagina": 2,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-05",
            "archivo": "pdfs_locales/ventas_2026-08-05_Remisi\u00f3n_Pag_2.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37924",
                    "productos": [
                        {
                            "cantidad": 7,
                            "codigo_item": "0385",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "2000",
                            "costo_total": 16500,
                            "iva": 2634,
                            "subtotal": 13866
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0449",
                            "costo_total": 741,
                            "iva": 118,
                            "subtotal": 623
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1039",
                            "costo_total": 950,
                            "iva": 152,
                            "subtotal": 798
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0262",
                            "costo_total": 2300,
                            "iva": 367,
                            "subtotal": 1933
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37925",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0609",
                            "costo_total": 30500,
                            "iva": 4870,
                            "subtotal": 25630
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0074",
                            "costo_total": 17250,
                            "iva": 2754,
                            "subtotal": 14496
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1665",
                            "costo_total": 4200,
                            "iva": 671,
                            "subtotal": 3529
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1079",
                            "costo_total": 11200,
                            "iva": 1788,
                            "subtotal": 9412
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1387",
                            "costo_total": 12200,
                            "iva": 1948,
                            "subtotal": 10252
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0304",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0313",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0713",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0174",
                            "costo_total": 3800,
                            "iva": 607,
                            "subtotal": 3193
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0849",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1004",
                            "costo_total": 5450,
                            "iva": 870,
                            "subtotal": 4580
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37926",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "1991",
                            "costo_total": 138000,
                            "iva": 22034,
                            "subtotal": 115966
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37927",
                    "productos": [
                        {
                            "cantidad": 5,
                            "codigo_item": "0882",
                            "costo_total": 59500,
                            "iva": 9500,
                            "subtotal": 50000
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1818",
                            "costo_total": 23000,
                            "iva": 3672,
                            "subtotal": 19328
                        },
                        {
                            "cantidad": 7,
                            "codigo_item": "0842",
                            "costo_total": 14000,
                            "iva": 2235,
                            "subtotal": 11765
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1976",
                            "costo_total": 22500,
                            "iva": 3592,
                            "subtotal": 18908
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0500",
                            "costo_total": 17400,
                            "iva": 2778,
                            "subtotal": 14622
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37928",
                    "productos": [
                        {
                            "cantidad": 200,
                            "codigo_item": "0578",
                            "costo_total": 92000,
                            "iva": 14689,
                            "subtotal": 77311
                        },
                        {
                            "cantidad": 100,
                            "codigo_item": "0572",
                            "costo_total": 25466,
                            "iva": 4066,
                            "subtotal": 21400
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0654",
                            "costo_total": 56000,
                            "iva": 8941,
                            "subtotal": 47059
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0657",
                            "costo_total": 50600,
                            "iva": 8079,
                            "subtotal": 42521
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "0855",
                            "costo_total": 14100,
                            "iva": 2251,
                            "subtotal": 11849
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0848",
                            "costo_total": 18500,
                            "iva": 2954,
                            "subtotal": 15546
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0688",
                            "costo_total": 12000,
                            "iva": 1916,
                            "subtotal": 10084
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0044",
                            "costo_total": 8000,
                            "iva": 381,
                            "subtotal": 7619
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "1241",
                            "costo_total": 8800,
                            "iva": 1405,
                            "subtotal": 7395
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1428",
                            "costo_total": 8400,
                            "iva": 1341,
                            "subtotal": 7059
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "5467",
                            "costo_total": 3800,
                            "iva": 607,
                            "subtotal": 3193
                        }
                    ]
                }
            ]
        },
        "3": {
            "id": 3,
            "pagina": 3,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-05",
            "archivo": "pdfs_locales/ventas_2026-08-05_Remisi\u00f3n_Pag_3.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37928",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0629",
                            "costo_total": 18200,
                            "iva": 2906,
                            "subtotal": 15294
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0605",
                            "costo_total": 8850,
                            "iva": 1413,
                            "subtotal": 7437
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0626",
                            "costo_total": 35200,
                            "iva": 5620,
                            "subtotal": 29580
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0622",
                            "costo_total": 9950,
                            "iva": 1589,
                            "subtotal": 8361
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0170",
                            "costo_total": 5400,
                            "iva": 862,
                            "subtotal": 4538
                        },
                        {
                            "cantidad": 20,
                            "codigo_item": "0108",
                            "costo_total": 17000,
                            "iva": 2714,
                            "subtotal": 14286
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0105",
                            "costo_total": 6000,
                            "iva": 958,
                            "subtotal": 5042
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37929",
                    "productos": [
                        {
                            "cantidad": 5,
                            "codigo_item": "1402",
                            "costo_total": 17250,
                            "iva": 2754,
                            "subtotal": 14496
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1518",
                            "costo_total": 23000,
                            "iva": 3672,
                            "subtotal": 19328
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1428",
                            "costo_total": 30000,
                            "iva": 4790,
                            "subtotal": 25210
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0105",
                            "costo_total": 6000,
                            "iva": 958,
                            "subtotal": 5042
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0130",
                            "costo_total": 9000,
                            "iva": 1437,
                            "subtotal": 7563
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1664",
                            "costo_total": 13000,
                            "iva": 2076,
                            "subtotal": 10924
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0187",
                            "costo_total": 8700,
                            "iva": 1389,
                            "subtotal": 7311
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0581",
                            "costo_total": 88000,
                            "iva": 14050,
                            "subtotal": 73950
                        },
                        {
                            "cantidad": 50,
                            "codigo_item": "0572",
                            "costo_total": 13500,
                            "iva": 2155,
                            "subtotal": 11345
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1764",
                            "costo_total": 5200,
                            "iva": 830,
                            "subtotal": 4370
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0654",
                            "costo_total": 112000,
                            "iva": 17882,
                            "subtotal": 94118
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0283",
                            "costo_total": 7500,
                            "iva": 1197,
                            "subtotal": 6303
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0668",
                            "costo_total": 2400,
                            "iva": 383,
                            "subtotal": 2017
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0304",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0313",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0917",
                            "costo_total": 4100,
                            "iva": 655,
                            "subtotal": 3445
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0477",
                            "costo_total": 2400,
                            "iva": 383,
                            "subtotal": 2017
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "965",
                            "costo_total": 13500,
                            "iva": 2155,
                            "subtotal": 11345
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0713",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0438",
                            "costo_total": 9000,
                            "iva": 1437,
                            "subtotal": 7563
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0629",
                            "costo_total": 18600,
                            "iva": 2970,
                            "subtotal": 15630
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0781",
                            "costo_total": 72000,
                            "iva": 11496,
                            "subtotal": 60504
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0959",
                            "costo_total": 4950,
                            "iva": 790,
                            "subtotal": 4160
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0263",
                            "costo_total": 8250,
                            "iva": 1317,
                            "subtotal": 6933
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1974",
                            "costo_total": 63000,
                            "iva": 10059,
                            "subtotal": 52941
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0852",
                            "costo_total": 13500,
                            "iva": 2155,
                            "subtotal": 11345
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0659",
                            "costo_total": 21000,
                            "iva": 3353,
                            "subtotal": 17647
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0774",
                            "costo_total": 95000,
                            "iva": 15168,
                            "subtotal": 79832
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0961",
                            "costo_total": 21400,
                            "iva": 3417,
                            "subtotal": 17983
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37930",
                    "productos": [
                        {
                            "cantidad": 2,
                            "codigo_item": "0484",
                            "costo_total": 22800,
                            "iva": 3640,
                            "subtotal": 19160
                        }
                    ]
                }
            ]
        }
    },
    "2026-08-13_Remisi\u00f3n": {
        "1": {
            "id": 4,
            "pagina": 1,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_1.pdf",
            "estado": "Procesado con \u00e9xito",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37921",
                    "productos": [
                        {
                            "cantidad": 37,
                            "codigo_item": "0847",
                            "costo_total": 111000,
                            "iva": 17723,
                            "subtotal": 93277
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0658",
                            "costo_total": 37950,
                            "iva": 6059,
                            "subtotal": 31891
                        },
                        {
                            "cantidad": 50,
                            "codigo_item": "0331",
                            "costo_total": 20000,
                            "iva": 3193,
                            "subtotal": 16807
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0653",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0399",
                            "costo_total": 30500,
                            "iva": 4870,
                            "subtotal": 25630
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0424",
                            "costo_total": 9500,
                            "iva": 1517,
                            "subtotal": 7983
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37922",
                    "productos": [
                        {
                            "cantidad": 3,
                            "codigo_item": "1839",
                            "costo_total": 9300,
                            "iva": 1485,
                            "subtotal": 7815
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0681",
                            "costo_total": 8600,
                            "iva": 1373,
                            "subtotal": 7227
                        },
                        {
                            "cantidad": 50,
                            "codigo_item": "4860",
                            "costo_total": 25000,
                            "iva": 3992,
                            "subtotal": 21008
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0644",
                            "costo_total": 11400,
                            "iva": 1820,
                            "subtotal": 9580
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "4156",
                            "costo_total": 8950,
                            "iva": 1429,
                            "subtotal": 7521
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "2206",
                            "costo_total": 5300,
                            "iva": 846,
                            "subtotal": 4454
                        },
                        {
                            "cantidad": 40,
                            "codigo_item": "0571-1",
                            "costo_total": 22800,
                            "iva": 3640,
                            "subtotal": 19160
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0105",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "2016",
                            "costo_total": 7800,
                            "iva": 1245,
                            "subtotal": 6555
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37923",
                    "productos": [
                        {
                            "cantidad": 8,
                            "codigo_item": "0858",
                            "costo_total": 33200,
                            "iva": 5301,
                            "subtotal": 27899
                        },
                        {
                            "cantidad": 8,
                            "codigo_item": "0690",
                            "costo_total": 50000,
                            "iva": 7983,
                            "subtotal": 42017
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0304",
                            "costo_total": 20400,
                            "iva": 3257,
                            "subtotal": 17143
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0313",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0713",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0171",
                            "costo_total": 5850,
                            "iva": 934,
                            "subtotal": 4916
                        },
                        {
                            "cantidad": 12,
                            "codigo_item": "0250",
                            "costo_total": 114000,
                            "iva": 18202,
                            "subtotal": 95798
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0578",
                            "costo_total": 95000,
                            "iva": 15168,
                            "subtotal": 79832
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0649",
                            "costo_total": 30900,
                            "iva": 4934,
                            "subtotal": 25966
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37924",
                    "productos": [
                        {
                            "cantidad": 200,
                            "codigo_item": "0570",
                            "costo_total": 82800,
                            "iva": 13220,
                            "subtotal": 69580
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0572",
                            "costo_total": 50000,
                            "iva": 7983,
                            "subtotal": 42017
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0658",
                            "costo_total": 59500,
                            "iva": 9500,
                            "subtotal": 50000
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0563",
                            "costo_total": 32200,
                            "iva": 5141,
                            "subtotal": 27059
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "0560",
                            "costo_total": 30000,
                            "iva": 4790,
                            "subtotal": 25210
                        },
                        {
                            "cantidad": 7,
                            "codigo_item": "0558",
                            "costo_total": 32200,
                            "iva": 5141,
                            "subtotal": 27059
                        },
                        {
                            "cantidad": 12,
                            "codigo_item": "0554",
                            "costo_total": 26400,
                            "iva": 4215,
                            "subtotal": 22185
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0537",
                            "costo_total": 19998,
                            "iva": 3193,
                            "subtotal": 16805
                        }
                    ]
                }
            ]
        },
        "2": {
            "id": 5,
            "pagina": 2,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_2.pdf",
            "estado": "Procesado con \u00e9xito",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37924",
                    "productos": [
                        {
                            "cantidad": 7,
                            "codigo_item": "0385",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "2000",
                            "costo_total": 16500,
                            "iva": 2634,
                            "subtotal": 13866
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0449",
                            "costo_total": 741,
                            "iva": 118,
                            "subtotal": 623
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1039",
                            "costo_total": 950,
                            "iva": 152,
                            "subtotal": 798
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0262",
                            "costo_total": 2300,
                            "iva": 367,
                            "subtotal": 1933
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37925",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0609",
                            "costo_total": 30500,
                            "iva": 4870,
                            "subtotal": 25630
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0074",
                            "costo_total": 17250,
                            "iva": 2754,
                            "subtotal": 14496
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1665",
                            "costo_total": 4200,
                            "iva": 671,
                            "subtotal": 3529
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1079",
                            "costo_total": 11200,
                            "iva": 1788,
                            "subtotal": 9412
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1387",
                            "costo_total": 12200,
                            "iva": 1948,
                            "subtotal": 10252
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0304",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0313",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0713",
                            "costo_total": 12600,
                            "iva": 2012,
                            "subtotal": 10588
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0174",
                            "costo_total": 3800,
                            "iva": 607,
                            "subtotal": 3193
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0849",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1004",
                            "costo_total": 5450,
                            "iva": 870,
                            "subtotal": 4580
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37926",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "1991",
                            "costo_total": 138000,
                            "iva": 22034,
                            "subtotal": 115966
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37927",
                    "productos": [
                        {
                            "cantidad": 5,
                            "codigo_item": "0882",
                            "costo_total": 59500,
                            "iva": 9500,
                            "subtotal": 50000
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1818",
                            "costo_total": 23000,
                            "iva": 3672,
                            "subtotal": 19328
                        },
                        {
                            "cantidad": 7,
                            "codigo_item": "0842",
                            "costo_total": 14000,
                            "iva": 2235,
                            "subtotal": 11765
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1976",
                            "costo_total": 22500,
                            "iva": 3592,
                            "subtotal": 18908
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0500",
                            "costo_total": 17400,
                            "iva": 2778,
                            "subtotal": 14622
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37928",
                    "productos": [
                        {
                            "cantidad": 200,
                            "codigo_item": "0578",
                            "costo_total": 92000,
                            "iva": 14689,
                            "subtotal": 77311
                        },
                        {
                            "cantidad": 100,
                            "codigo_item": "0572",
                            "costo_total": 25466,
                            "iva": 4066,
                            "subtotal": 21400
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0654",
                            "costo_total": 56000,
                            "iva": 8941,
                            "subtotal": 47059
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0657",
                            "costo_total": 50600,
                            "iva": 8079,
                            "subtotal": 42521
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "0855",
                            "costo_total": 14100,
                            "iva": 2251,
                            "subtotal": 11849
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0848",
                            "costo_total": 18500,
                            "iva": 2954,
                            "subtotal": 15546
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0688",
                            "costo_total": 12000,
                            "iva": 1916,
                            "subtotal": 10084
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0044",
                            "costo_total": 8000,
                            "iva": 381,
                            "subtotal": 7619
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "1241",
                            "costo_total": 8800,
                            "iva": 1405,
                            "subtotal": 7395
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1428",
                            "costo_total": 8400,
                            "iva": 1341,
                            "subtotal": 7059
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "5467",
                            "costo_total": 3800,
                            "iva": 607,
                            "subtotal": 3193
                        }
                    ]
                }
            ]
        },
        "3": {
            "id": 6,
            "pagina": 3,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_3.pdf",
            "estado": "Procesado con \u00e9xito",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37928",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0629",
                            "costo_total": 18200,
                            "iva": 2906,
                            "subtotal": 15294
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0605",
                            "costo_total": 8850,
                            "iva": 1413,
                            "subtotal": 7437
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0626",
                            "costo_total": 35200,
                            "iva": 5620,
                            "subtotal": 29580
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0622",
                            "costo_total": 9950,
                            "iva": 1589,
                            "subtotal": 8361
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0170",
                            "costo_total": 5400,
                            "iva": 862,
                            "subtotal": 4538
                        },
                        {
                            "cantidad": 20,
                            "codigo_item": "0108",
                            "costo_total": 17000,
                            "iva": 2714,
                            "subtotal": 14286
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0105",
                            "costo_total": 6000,
                            "iva": 958,
                            "subtotal": 5042
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37929",
                    "productos": [
                        {
                            "cantidad": 5,
                            "codigo_item": "1402",
                            "costo_total": 17250,
                            "iva": 2754,
                            "subtotal": 14496
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1518",
                            "costo_total": 23000,
                            "iva": 3672,
                            "subtotal": 19328
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1428",
                            "costo_total": 30000,
                            "iva": 4790,
                            "subtotal": 25210
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0105",
                            "costo_total": 6000,
                            "iva": 958,
                            "subtotal": 5042
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0130",
                            "costo_total": 9000,
                            "iva": 1437,
                            "subtotal": 7563
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1664",
                            "costo_total": 13000,
                            "iva": 2076,
                            "subtotal": 10924
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0187",
                            "costo_total": 8700,
                            "iva": 1389,
                            "subtotal": 7311
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0581",
                            "costo_total": 88000,
                            "iva": 14050,
                            "subtotal": 73950
                        },
                        {
                            "cantidad": 50,
                            "codigo_item": "0572",
                            "costo_total": 13500,
                            "iva": 2155,
                            "subtotal": 11345
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1764",
                            "costo_total": 5200,
                            "iva": 830,
                            "subtotal": 4370
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0654",
                            "costo_total": 112000,
                            "iva": 17882,
                            "subtotal": 94118
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0283",
                            "costo_total": 7500,
                            "iva": 1197,
                            "subtotal": 6303
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0668",
                            "costo_total": 2400,
                            "iva": 383,
                            "subtotal": 2017
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0304",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0313",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0917",
                            "costo_total": 4100,
                            "iva": 655,
                            "subtotal": 3445
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0477",
                            "costo_total": 2400,
                            "iva": 383,
                            "subtotal": 2017
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "965",
                            "costo_total": 13500,
                            "iva": 2155,
                            "subtotal": 11345
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0713",
                            "costo_total": 19500,
                            "iva": 3113,
                            "subtotal": 16387
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0438",
                            "costo_total": 9000,
                            "iva": 1437,
                            "subtotal": 7563
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0629",
                            "costo_total": 18600,
                            "iva": 2970,
                            "subtotal": 15630
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0781",
                            "costo_total": 72000,
                            "iva": 11496,
                            "subtotal": 60504
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0959",
                            "costo_total": 4950,
                            "iva": 790,
                            "subtotal": 4160
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0263",
                            "costo_total": 8250,
                            "iva": 1317,
                            "subtotal": 6933
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1974",
                            "costo_total": 63000,
                            "iva": 10059,
                            "subtotal": 52941
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0852",
                            "costo_total": 13500,
                            "iva": 2155,
                            "subtotal": 11345
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0659",
                            "costo_total": 21000,
                            "iva": 3353,
                            "subtotal": 17647
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0774",
                            "costo_total": 95000,
                            "iva": 15168,
                            "subtotal": 79832
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0961",
                            "costo_total": 21400,
                            "iva": 3417,
                            "subtotal": 17983
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37930",
                    "productos": [
                        {
                            "cantidad": 2,
                            "codigo_item": "0484",
                            "costo_total": 22800,
                            "iva": 3640,
                            "subtotal": 19160
                        }
                    ]
                }
            ]
        },
        "4": {
            "id": 7,
            "pagina": 4,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_4.pdf",
            "estado": "Procesado con \u00e9xito",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37930",
                    "productos": [
                        {
                            "cantidad": 15,
                            "codigo_item": "0644",
                            "costo_total": 57000,
                            "iva": 9101,
                            "subtotal": 47899
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0313",
                            "costo_total": 34000,
                            "iva": 5429,
                            "subtotal": 28571
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1770",
                            "costo_total": 23700,
                            "iva": 3784,
                            "subtotal": 19916
                        },
                        {
                            "cantidad": 7,
                            "codigo_item": "0858",
                            "costo_total": 29050,
                            "iva": 4638,
                            "subtotal": 24412
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0298",
                            "costo_total": 19200,
                            "iva": 3066,
                            "subtotal": 16134
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1665",
                            "costo_total": 4600,
                            "iva": 734,
                            "subtotal": 3866
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1852",
                            "costo_total": 9700,
                            "iva": 1549,
                            "subtotal": 8151
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "5467",
                            "costo_total": 11700,
                            "iva": 1868,
                            "subtotal": 9832
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0725",
                            "costo_total": 17100,
                            "iva": 2730,
                            "subtotal": 14370
                        },
                        {
                            "cantidad": 30,
                            "codigo_item": "0263",
                            "costo_total": 16500,
                            "iva": 2634,
                            "subtotal": 13866
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0678",
                            "costo_total": 32500,
                            "iva": 5189,
                            "subtotal": 27311
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1336",
                            "costo_total": 15000,
                            "iva": 2395,
                            "subtotal": 12605
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37931",
                    "productos": [
                        {
                            "cantidad": 5,
                            "codigo_item": "0519",
                            "costo_total": 71000,
                            "iva": 11336,
                            "subtotal": 59664
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "965",
                            "costo_total": 54800,
                            "iva": 8750,
                            "subtotal": 46050
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37932",
                    "productos": [
                        {
                            "cantidad": 40,
                            "codigo_item": "0106",
                            "costo_total": 8800,
                            "iva": 1405,
                            "subtotal": 7395
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0411",
                            "costo_total": 8600,
                            "iva": 1373,
                            "subtotal": 7227
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0029",
                            "costo_total": 15950,
                            "iva": 2547,
                            "subtotal": 13403
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "4880",
                            "costo_total": 4500,
                            "iva": 718,
                            "subtotal": 3782
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "4883",
                            "costo_total": 4500,
                            "iva": 718,
                            "subtotal": 3782
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0841",
                            "costo_total": 11250,
                            "iva": 1796,
                            "subtotal": 9454
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1149",
                            "costo_total": 27450,
                            "iva": 4383,
                            "subtotal": 23067
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "4879",
                            "costo_total": 4500,
                            "iva": 718,
                            "subtotal": 3782
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0105",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37933",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0029",
                            "costo_total": 16000,
                            "iva": 2555,
                            "subtotal": 13445
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0033",
                            "costo_total": 7500,
                            "iva": 1197,
                            "subtotal": 6303
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0646",
                            "costo_total": 14900,
                            "iva": 2379,
                            "subtotal": 12521
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0849",
                            "costo_total": 4200,
                            "iva": 671,
                            "subtotal": 3529
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "1075",
                            "costo_total": 21600,
                            "iva": 3449,
                            "subtotal": 18151
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1369",
                            "costo_total": 4600,
                            "iva": 734,
                            "subtotal": 3866
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0044",
                            "costo_total": 16000,
                            "iva": 762,
                            "subtotal": 15238
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37934",
                    "productos": [
                        {
                            "cantidad": 30,
                            "codigo_item": "0644",
                            "costo_total": 120000,
                            "iva": 19160,
                            "subtotal": 100840
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1402",
                            "costo_total": 6400,
                            "iva": 1022,
                            "subtotal": 5378
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "1778",
                            "costo_total": 18000,
                            "iva": 2874,
                            "subtotal": 15126
                        }
                    ]
                }
            ]
        },
        "5": {
            "id": 8,
            "pagina": 5,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_5.pdf",
            "estado": "Procesado con \u00e9xito",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37934",
                    "productos": [
                        {
                            "cantidad": 6,
                            "codigo_item": "0848",
                            "costo_total": 23100,
                            "iva": 3688,
                            "subtotal": 19412
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37935",
                    "productos": [
                        {
                            "cantidad": 200,
                            "codigo_item": "4860",
                            "costo_total": 106000,
                            "iva": 16924,
                            "subtotal": 89076
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37936",
                    "productos": [
                        {
                            "cantidad": 17,
                            "codigo_item": "1347",
                            "costo_total": 303600,
                            "iva": 48474,
                            "subtotal": 255126
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37937",
                    "productos": [
                        {
                            "cantidad": 50,
                            "codigo_item": "0385",
                            "costo_total": 82500,
                            "iva": 13172,
                            "subtotal": 69328
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1722",
                            "costo_total": 35245,
                            "iva": 5627,
                            "subtotal": 29618
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0847",
                            "costo_total": 17000,
                            "iva": 2714,
                            "subtotal": 14286
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0688",
                            "costo_total": 20000,
                            "iva": 3193,
                            "subtotal": 16807
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0394",
                            "costo_total": 15500,
                            "iva": 2475,
                            "subtotal": 13025
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37938",
                    "productos": [
                        {
                            "cantidad": 145,
                            "codigo_item": "1893",
                            "costo_total": 362500,
                            "iva": 57878,
                            "subtotal": 304622
                        },
                        {
                            "cantidad": 60,
                            "codigo_item": "0098",
                            "costo_total": 174000,
                            "iva": 27782,
                            "subtotal": 146218
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0990",
                            "costo_total": 38550,
                            "iva": 6155,
                            "subtotal": 32395
                        },
                        {
                            "cantidad": 24,
                            "codigo_item": "0555",
                            "costo_total": 57600,
                            "iva": 9197,
                            "subtotal": 48403
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37939",
                    "productos": [
                        {
                            "cantidad": 10,
                            "codigo_item": "0074",
                            "costo_total": 36000,
                            "iva": 5748,
                            "subtotal": 30252
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0250",
                            "costo_total": 36000,
                            "iva": 5748,
                            "subtotal": 30252
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0280",
                            "costo_total": 19000,
                            "iva": 3034,
                            "subtotal": 15966
                        },
                        {
                            "cantidad": 200,
                            "codigo_item": "0572",
                            "costo_total": 51000,
                            "iva": 8143,
                            "subtotal": 42857
                        },
                        {
                            "cantidad": 4,
                            "codigo_item": "0654",
                            "costo_total": 42400,
                            "iva": 6770,
                            "subtotal": 35630
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0846",
                            "costo_total": 55000,
                            "iva": 8782,
                            "subtotal": 46218
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0849",
                            "costo_total": 42000,
                            "iva": 6706,
                            "subtotal": 35294
                        },
                        {
                            "cantidad": 20,
                            "codigo_item": "1089",
                            "costo_total": 76000,
                            "iva": 12134,
                            "subtotal": 63866
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "0688",
                            "costo_total": 18500,
                            "iva": 2954,
                            "subtotal": 15546
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0674",
                            "costo_total": 14200,
                            "iva": 2267,
                            "subtotal": 11933
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "0644",
                            "costo_total": 57000,
                            "iva": 9101,
                            "subtotal": 47899
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37940",
                    "productos": [
                        {
                            "cantidad": 10,
                            "codigo_item": "1665",
                            "costo_total": 18000,
                            "iva": 2874,
                            "subtotal": 15126
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "1667",
                            "costo_total": 26700,
                            "iva": 4263,
                            "subtotal": 22437
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "1079",
                            "costo_total": 44000,
                            "iva": 7025,
                            "subtotal": 36975
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "1666",
                            "costo_total": 46000,
                            "iva": 7345,
                            "subtotal": 38655
                        },
                        {
                            "cantidad": 5,
                            "codigo_item": "1172",
                            "costo_total": 24750,
                            "iva": 3952,
                            "subtotal": 20798
                        }
                    ]
                }
            ]
        },
        "6": {
            "id": 9,
            "pagina": 6,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_6.pdf",
            "estado": "Procesado con \u00e9xito",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37940",
                    "productos": [
                        {
                            "cantidad": 5,
                            "codigo_item": "1174",
                            "costo_total": 33600,
                            "iva": 5365,
                            "subtotal": 28235
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37941",
                    "productos": [
                        {
                            "cantidad": 100,
                            "codigo_item": "0578",
                            "costo_total": 46000,
                            "iva": 7345,
                            "subtotal": 38655
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0056",
                            "costo_total": 3400,
                            "iva": 543,
                            "subtotal": 2857
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "0847",
                            "costo_total": 18000,
                            "iva": 2874,
                            "subtotal": 15126
                        },
                        {
                            "cantidad": 6,
                            "codigo_item": "0688",
                            "costo_total": 22200,
                            "iva": 3545,
                            "subtotal": 18655
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1089",
                            "costo_total": 3800,
                            "iva": 607,
                            "subtotal": 3193
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0007",
                            "costo_total": 6500,
                            "iva": 1038,
                            "subtotal": 5462
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1784",
                            "costo_total": 7500,
                            "iva": 1197,
                            "subtotal": 6303
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0386",
                            "costo_total": 3600,
                            "iva": 171,
                            "subtotal": 3429
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0001",
                            "costo_total": 23000,
                            "iva": 3672,
                            "subtotal": 19328
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0594",
                            "costo_total": 3300,
                            "iva": 0,
                            "subtotal": 3300
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1451",
                            "costo_total": 8000,
                            "iva": 0,
                            "subtotal": 8000
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0070",
                            "costo_total": 4500,
                            "iva": 718,
                            "subtotal": 3782
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1272",
                            "costo_total": 23700,
                            "iva": 3784,
                            "subtotal": 19916
                        },
                        {
                            "cantidad": 20,
                            "codigo_item": "0108",
                            "costo_total": 17000,
                            "iva": 2714,
                            "subtotal": 14286
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1818",
                            "costo_total": 9200,
                            "iva": 1469,
                            "subtotal": 7731
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1817",
                            "costo_total": 9200,
                            "iva": 1469,
                            "subtotal": 7731
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "1591",
                            "costo_total": 9200,
                            "iva": 1469,
                            "subtotal": 7731
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0170",
                            "costo_total": 3000,
                            "iva": 479,
                            "subtotal": 2521
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0653",
                            "costo_total": 4000,
                            "iva": 639,
                            "subtotal": 3361
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1297",
                            "costo_total": 4500,
                            "iva": 718,
                            "subtotal": 3782
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37942",
                    "productos": [
                        {
                            "cantidad": 15,
                            "codigo_item": "9104",
                            "costo_total": 135000,
                            "iva": 21555,
                            "subtotal": 113445
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "9103",
                            "costo_total": 58550,
                            "iva": 9348,
                            "subtotal": 49202
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37943",
                    "productos": [
                        {
                            "cantidad": 10,
                            "codigo_item": "2315",
                            "costo_total": 24000,
                            "iva": 3832,
                            "subtotal": 20168
                        },
                        {
                            "cantidad": 15,
                            "codigo_item": "1953",
                            "costo_total": 56250,
                            "iva": 8981,
                            "subtotal": 47269
                        },
                        {
                            "cantidad": 10,
                            "codigo_item": "0523",
                            "costo_total": 76500,
                            "iva": 12214,
                            "subtotal": 64286
                        },
                        {
                            "cantidad": 3,
                            "codigo_item": "0471",
                            "costo_total": 31500,
                            "iva": 5029,
                            "subtotal": 26471
                        }
                    ]
                },
                {
                    "fecha": "2026-08-03",
                    "numero_factura": "37944",
                    "productos": [
                        {
                            "cantidad": 90,
                            "codigo_item": "0659",
                            "costo_total": 409500,
                            "iva": 65382,
                            "subtotal": 344118
                        }
                    ]
                },
                {
                    "fecha": "2026-08-04",
                    "numero_factura": "37946",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0250",
                            "costo_total": 9500,
                            "iva": 1517,
                            "subtotal": 7983
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1227",
                            "costo_total": 19149,
                            "iva": 3057,
                            "subtotal": 16092
                        }
                    ]
                }
            ]
        },
        "7": {
            "id": 10,
            "pagina": 7,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_7.pdf",
            "estado": "Nuevo"
        },
        "8": {
            "id": 11,
            "pagina": 8,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_8.pdf",
            "estado": "Nuevo"
        },
        "9": {
            "id": 12,
            "pagina": 9,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_9.pdf",
            "estado": "Nuevo"
        },
        "10": {
            "id": 13,
            "pagina": 10,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_10.pdf",
            "estado": "Nuevo"
        },
        "11": {
            "id": 14,
            "pagina": 11,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_11.pdf",
            "estado": "Nuevo"
        },
        "12": {
            "id": 15,
            "pagina": 12,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_12.pdf",
            "estado": "Nuevo"
        },
        "13": {
            "id": 16,
            "pagina": 13,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_13.pdf",
            "estado": "Nuevo"
        },
        "14": {
            "id": 17,
            "pagina": 14,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_14.pdf",
            "estado": "Nuevo"
        },
        "15": {
            "id": 18,
            "pagina": 15,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_15.pdf",
            "estado": "Nuevo"
        },
        "16": {
            "id": 19,
            "pagina": 16,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_16.pdf",
            "estado": "Nuevo"
        },
        "17": {
            "id": 20,
            "pagina": 17,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_17.pdf",
            "estado": "Nuevo"
        },
        "18": {
            "id": 21,
            "pagina": 18,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_18.pdf",
            "estado": "Nuevo"
        },
        "19": {
            "id": 22,
            "pagina": 19,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_19.pdf",
            "estado": "Nuevo"
        },
        "20": {
            "id": 23,
            "pagina": 20,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_20.pdf",
            "estado": "Nuevo"
        },
        "21": {
            "id": 24,
            "pagina": 21,
            "tipo": "Remisi\u00f3n",
            "fecha": "2026-08-13",
            "archivo": "pdfs_locales/ventas_2026-08-13_Remisi\u00f3n_Pag_21.pdf",
            "estado": "Nuevo"
        }
    }
}
````

## File: ui/views/dashboard.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import datetime

class DashboardView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        
        header_row = ft.Row([
            ft.Column([
                ft.Text("Dashboard General", size=28, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Resumen ejecutivo del sistema", size=14, color="grey"),
            ], spacing=2)
        ], alignment=ft.MainAxisAlignment.START)
        
        # Tarjetas de KPIs (Valores Iniciales) - SECCIÓN COSTOS
        self.val_inventario = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_compras = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_rotacion = ft.Text("N/D", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_compras_hoy = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        
        self.kpi_costos_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Costo Inventario Actual", self.val_inventario, ft.icons.INVENTORY_2), col={"xs": 12, "sm": 6, "md": 3}),
            ft.Container(content=self._build_kpi_card("Total Compras (Mes)", self.val_compras, ft.icons.SHOPPING_BAG), col={"xs": 12, "sm": 6, "md": 3}),
            ft.Container(content=self._build_kpi_card("Rotación Inventario", self.val_rotacion, ft.icons.SYNC), col={"xs": 12, "sm": 6, "md": 3}),
            ft.Container(content=self._build_kpi_card("Costos de Compras (Hoy)", self.val_compras_hoy, ft.icons.MONEY_OFF), col={"xs": 12, "sm": 6, "md": 3}),
        ], spacing=15, run_spacing=15)
        
        # SECCIÓN VENTAS
        self.val_ingresos = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_ventas_hoy = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_rentabilidad = ft.Text("0.0%", size=24, weight="bold", color="#2ecca0")
        self.val_proyeccion_ventas = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_proyeccion_rentabilidad = ft.Text("0.0%", size=24, weight="bold", color="#2ecca0")
        
        self.kpi_ventas_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Total Ventas (Mes)", self.val_ingresos, ft.icons.TRENDING_UP), col={"xs": 12, "sm": 6, "md": 2.4}),
            ft.Container(content=self._build_kpi_card("Total Ventas (Hoy)", self.val_ventas_hoy, ft.icons.ATTACH_MONEY), col={"xs": 12, "sm": 6, "md": 2.4}),
            ft.Container(content=self._build_kpi_card("Rentabilidad Bruta", self.val_rentabilidad, ft.icons.PIE_CHART_OUTLINE), col={"xs": 12, "sm": 6, "md": 2.4}),
            ft.Container(content=self._build_kpi_card("Proyección de Ventas", self.val_proyeccion_ventas, ft.icons.SHOW_CHART), col={"xs": 12, "sm": 6, "md": 2.4}),
            ft.Container(content=self._build_kpi_card("Proy. de Rentabilidad", self.val_proyeccion_rentabilidad, ft.icons.STAR_BORDER), col={"xs": 12, "sm": 6, "md": 2.4}),
        ], spacing=15, run_spacing=15)

        # SECCIÓN AJUSTES
        self.col_ajustes_salida = ft.Column(spacing=5)
        self.col_ajustes_entrada = ft.Column(spacing=5)
        
        self.lbl_neto_ajustes_header = ft.Text("NETO: $0", weight="bold", size=16)
        header_ajustes = ft.Row([
            ft.Text("Impacto de Ajustes de Inventario (Mes Actual)", size=16, weight="bold", color=Config.COLOR_PRIMARY),
            self.lbl_neto_ajustes_header
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.panel_ajustes = ft.Row([
            # Panel Salida
            ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes de Salida (-)", size=16, weight="bold", color="red"),
                    ft.Divider(height=1),
                    self.col_ajustes_salida
                ]),
                bgcolor="#fff3f3",
                padding=15,
                border_radius=8,
                expand=True
            ),
            # Panel Entrada
            ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes de Entrada (+)", size=16, weight="bold", color="green"),
                    ft.Divider(height=1),
                    self.col_ajustes_entrada
                ]),
                bgcolor="#f3fff4",
                padding=15,
                border_radius=8,
                expand=True
            )
        ], spacing=15)

        self.seccion_costos = ft.Column([
            ft.Text("Costos y Valorización", size=20, weight="bold", color=Config.COLOR_PRIMARY),
            self.kpi_costos_row
        ], spacing=10)

        self.seccion_ventas = ft.Column([
            ft.Text("Ingresos y Proyecciones", size=20, weight="bold", color=Config.COLOR_PRIMARY),
            self.kpi_ventas_row
        ], spacing=10)

        self.seccion_ajustes = ft.Column([
            header_ajustes,
            self.panel_ajustes
        ], spacing=10)

        # Gráficos y Tablas
        # Series de datos (Grosor y puntas redondeadas)
        self.chart_ventas = ft.LineChartData(
            data_points=[], 
            color=ft.colors.BLUE_400,
            stroke_width=4, 
            curved=False,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE_400)
        )
        self.chart_compras = ft.LineChartData(
            data_points=[], 
            color="#2ecca0", 
            stroke_width=4, 
            curved=False,
            stroke_cap_round=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, "#2ecca0")
        )
        
        # Contenedor de Categorías (Grilla Responsiva)
        self.categorias_row = ft.ResponsiveRow(columns=12, spacing=15, run_spacing=15)
        self.categorias_container = ft.Container(
            content=ft.Column([
                ft.Text("Rendimiento Detallado por Categoría", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.categorias_row
            ]),
            margin=ft.padding.only(top=10, bottom=10)
        )

        # Gráfico habilitando los ejes visuales
        self.line_chart = ft.LineChart(
            data_series=[self.chart_ventas, self.chart_compras],
            border=ft.border.all(1, "#f0f0f0"),
            min_y=0,
            min_x=0,
            expand=True,
            tooltip_bgcolor="white",
            left_axis=ft.ChartAxis(labels_size=50), 
            bottom_axis=ft.ChartAxis(labels_size=40), 
        )
        
        # Leyenda adaptada a fondo claro
        leyenda = ft.Row([
            ft.Row([ft.Container(width=12, height=12, bgcolor=ft.colors.BLUE_400, border_radius=6), ft.Text("Ingresos", size=12, weight="bold", color="black87")]),
            ft.Row([ft.Container(width=12, height=12, bgcolor="#2ecca0", border_radius=6), ft.Text("Costos", size=12, weight="bold", color="black87")]),
        ], spacing=30, alignment=ft.MainAxisAlignment.CENTER)
        
        self.chart_container = ft.Container(
            content=ft.Column([
                ft.Text("Tendencia Diaria: Ingresos vs Costo de Ventas", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                leyenda,
                ft.Container(content=self.line_chart, height=320, margin=ft.padding.only(top=10))
            ]),
            bgcolor="white",
            padding=20,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        # Tables
        self.dt_ventas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", size=12)),
                ft.DataColumn(ft.Text("Producto", size=12)),
                ft.DataColumn(ft.Text("Unidades", size=12), numeric=True),
                ft.DataColumn(ft.Text("Ingreso Total", size=12), numeric=True)
            ],
            rows=[],
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            column_spacing=15,
        )
        
        self.dt_costos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código", size=12)),
                ft.DataColumn(ft.Text("Producto", size=12)),
                ft.DataColumn(ft.Text("Valor Inv.", size=12), numeric=True),
                ft.DataColumn(ft.Text("Rotación", size=12))
            ],
            rows=[],
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            column_spacing=15,
        )
        
        table_ventas_container = ft.Container(
            content=ft.Column([
                ft.Text("Top 10 Productos con Mayor Ingreso", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.dt_ventas
            ], scroll=ft.ScrollMode.AUTO),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            col={"xs": 12, "md": 6}
        )
        
        table_costos_container = ft.Container(
            content=ft.Column([
                ft.Text("Top 10 Productos con Mayor Costo", size=16, weight="bold", color=Config.COLOR_PRIMARY),
                self.dt_costos
            ], scroll=ft.ScrollMode.AUTO),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            col={"xs": 12, "md": 6}
        )
        
        self.tables_row = ft.ResponsiveRow([
            table_ventas_container,
            table_costos_container
        ], spacing=15, run_spacing=15)
        
        # Indicador de carga superior
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)

        # 2. Main content Column
        self.content = ft.Column([
            self.progress_bar, 
            header_row,
            ft.Divider(height=10, color="transparent"),
            self.seccion_costos,
            ft.Divider(height=10, color="transparent"),
            self.seccion_ventas,
            ft.Divider(height=10, color="transparent"),
            self.seccion_ajustes,
            ft.Divider(height=10, color="transparent"),
            self.categorias_container,
            ft.Divider(height=10, color="transparent"),
            self.chart_container,
            ft.Divider(height=10, color="transparent"),
            self.tables_row,
            ft.Container(height=30) # Bottom padding
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def did_mount(self):
        self.load_data()

    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        self.safe_update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        """Ejecuta todas las llamadas HTTP síncronas sin congelar la ventana."""
        # 1. Load KPIs
        res_cat = self.db.get_catalogo_summary()
        res_ven = self.db.get_ventas_summary()
        res_com = self.db.get_compras_summary()
        
        val_inv = float(res_cat.get('total_compras') or 0) - float(res_cat.get('total_ventas') or 0)
        self.val_inventario.value = f"$ {val_inv:,.0f}"
        
        ingresos = float(res_ven.get('total_mes') or 0)
        compras = float(res_com.get('total_mes') or 0)
        
        ventas_hoy = float(res_ven.get('total_hoy') or 0)
        compras_hoy = float(res_com.get('total_hoy') or 0)
        
        self.val_ingresos.value = f"$ {ingresos:,.0f}"
        self.val_ventas_hoy.value = f"$ {ventas_hoy:,.0f}"
        self.val_compras.value = f"$ {compras:,.0f}"
        self.val_compras_hoy.value = f"$ {compras_hoy:,.0f}"
        
        rentabilidad = 0
        if ingresos > 0:
            rentabilidad = ((ingresos - compras) / ingresos) * 100
            
        self.val_rentabilidad.value = f"{rentabilidad:.1f}%"
        self.val_rentabilidad.color = "#2ecca0" if rentabilidad >= 0 else "#f26c61"
        
        # Basic rotacion (Ventas / Inventario)
        if val_inv > 0:
            rotacion_global = ingresos / val_inv
            self.val_rotacion.value = f"{rotacion_global:.2f}x"
        else:
            self.val_rotacion.value = "N/D"

        # Nuevos KPIs y Ajustes
        proyeccion_ventas = self.db.get_proyeccion_ventas()
        self.val_proyeccion_ventas.value = f"$ {proyeccion_ventas:,.0f}"
        
        proy_rent = 0
        if proyeccion_ventas > 0:
            proy_rent = ((proyeccion_ventas - val_inv) / proyeccion_ventas) * 100
        
        self.val_proyeccion_rentabilidad.value = f"{proy_rent:.1f}%"
        self.val_proyeccion_rentabilidad.color = "#2ecca0" if proy_rent >= 0 else "#f26c61"

        mes_actual = datetime.date.today().strftime("%Y-%m")
        ajustes_bd = self.db.get_ajustes_mes(mes_actual)
        
        tipos_salida = {
            "Daño / Merma": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Vencimiento": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Pérdida": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Consumo Familiar": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Consumo Cliente (Cortesía)": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Donación Saliente": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Otro (Salida)": {"conteo": 0, "cantidad": 0, "costo": 0.0}
        }

        tipos_entrada = {
            "Sobrante de Inventario": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Donación Entrante": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Devolución Cliente": {"conteo": 0, "cantidad": 0, "costo": 0.0},
            "Otro (Entrada)": {"conteo": 0, "cantidad": 0, "costo": 0.0}
        }
        
        for fila in ajustes_bd:
            tipo_bd = fila.get("tipo_ajuste", "")
            motivo_bd = fila.get("motivo_observacion", "")
            cant = float(fila.get("cantidad_total") or 0)
            costo = float(fila.get("costo_total") or 0)
            conteo = int(fila.get("conteo") or 0)
            
            asignado = False
            if tipo_bd in ("AJUSTE_ENTRADA", "ENTRADA_POR_SOBRANTE"):
                for key in tipos_entrada.keys():
                    if key.lower() in motivo_bd.lower():
                        tipos_entrada[key]["conteo"] += conteo
                        tipos_entrada[key]["cantidad"] += cant
                        tipos_entrada[key]["costo"] += costo
                        asignado = True
                        break
                if not asignado:
                    tipos_entrada["Otro (Entrada)"]["conteo"] += conteo
                    tipos_entrada["Otro (Entrada)"]["cantidad"] += cant
                    tipos_entrada["Otro (Entrada)"]["costo"] += costo
            else:
                for key in tipos_salida.keys():
                    if key.lower() in motivo_bd.lower():
                        tipos_salida[key]["conteo"] += conteo
                        tipos_salida[key]["cantidad"] += cant
                        tipos_salida[key]["costo"] += costo
                        asignado = True
                        break
                if not asignado:
                    # Fallback por tipo
                    if tipo_bd == "BAJA_VENCIMIENTO": k = "Vencimiento"
                    elif tipo_bd == "SALIDA_POR_FALTANTE": k = "Pérdida"
                    else: k = "Otro (Salida)"
                    tipos_salida[k]["conteo"] += conteo
                    tipos_salida[k]["cantidad"] += cant
                    tipos_salida[k]["costo"] += costo

        total_costo_entradas = sum([d["costo"] for d in tipos_entrada.values()])
        total_costo_salidas = sum([d["costo"] for d in tipos_salida.values()])
        
        total_cant_entradas = sum([d["cantidad"] for d in tipos_entrada.values()])
        total_cant_salidas = sum([d["cantidad"] for d in tipos_salida.values()])
        
        neto = total_costo_entradas - total_costo_salidas
        if neto > 0:
            self.lbl_neto_ajustes_header.value = f"NETO (POSITIVO): +${neto:,.0f}"
            self.lbl_neto_ajustes_header.color = "#2ecca0"
        elif neto < 0:
            self.lbl_neto_ajustes_header.value = f"NETO (NEGATIVO): -${abs(neto):,.0f}"
            self.lbl_neto_ajustes_header.color = "#f26c61"
        else:
            self.lbl_neto_ajustes_header.value = f"NETO: $0"
            self.lbl_neto_ajustes_header.color = "grey"

        # Limpiar columnas
        self.col_ajustes_entrada.controls.clear()
        self.col_ajustes_salida.controls.clear()

        # Render Entrada
        for key, datos in tipos_entrada.items():
            self.col_ajustes_entrada.controls.append(
                ft.Row([
                    ft.Text(f"{key} ({datos['conteo']})", size=12, color="black87", expand=True),
                    ft.Text(f"{datos['cantidad']:.0f} unds", size=12, color="grey"),
                    ft.Text(f"${datos['costo']:,.0f}", size=12, weight="bold", color="#2ecca0")
                ])
            )
        self.col_ajustes_entrada.controls.append(ft.Divider(color="black12", height=10))
        self.col_ajustes_entrada.controls.append(
            ft.Row([
                ft.Text("TOTAL ENTRADAS", size=12, weight="bold"),
                ft.Text(f"{total_cant_entradas:.0f} unds", size=12, weight="bold", color="grey", expand=True, text_align=ft.TextAlign.CENTER),
                ft.Text(f"${total_costo_entradas:,.0f}", size=12, weight="bold", color="#2ecca0")
            ])
        )
        
        # Render Salida
        for key, datos in tipos_salida.items():
            self.col_ajustes_salida.controls.append(
                ft.Row([
                    ft.Text(f"{key} ({datos['conteo']})", size=12, color="black87", expand=True),
                    ft.Text(f"{datos['cantidad']:.0f} unds", size=12, color="grey"),
                    ft.Text(f"${datos['costo']:,.0f}", size=12, weight="bold", color="#f26c61")
                ])
            )
        self.col_ajustes_salida.controls.append(ft.Divider(color="black12", height=10))
        self.col_ajustes_salida.controls.append(
            ft.Row([
                ft.Text("TOTAL SALIDAS", size=12, weight="bold"),
                ft.Text(f"{total_cant_salidas:.0f} unds", size=12, weight="bold", color="grey", expand=True, text_align=ft.TextAlign.CENTER),
                ft.Text(f"${total_costo_salidas:,.0f}", size=12, weight="bold", color="#f26c61")
            ])
        )

        # 2. Load Chart Data (Nativo Flet)
        try:
            tendencia = self.db.get_tendencia_diaria()
            dias_ordenados = sorted(tendencia.keys())
            max_val_y = 0
            
            pts_ventas = []
            pts_compras = []
            etiquetas_x = []
            
            for i, dia in enumerate(dias_ordenados):
                v = float(tendencia[dia]["ventas"])
                c = float(tendencia[dia]["compras"])
                if v > max_val_y: max_val_y = v
                if c > max_val_y: max_val_y = c
                # Poner la fecha SOLO en el tooltip de arriba (compras) para que Flet no la duplique al apilar
                tt_compras = f"{dia}\nCostos: ${c:,.0f}"
                tt_ventas = f"Ingresos: ${v:,.0f}"
                estilo_tt = ft.TextStyle(size=12, weight="bold", color="black87")
                
                pts_ventas.append(ft.LineChartDataPoint(i, v, tooltip=tt_ventas, tooltip_style=estilo_tt))
                pts_compras.append(ft.LineChartDataPoint(i, c, tooltip=tt_compras, tooltip_style=estilo_tt))
                
                # Densidad en Eje X: Mostrar todos los días con la fecha completa rotada
                etiquetas_x.append(
                    ft.ChartAxisLabel(
                        value=i, 
                        label=ft.Container(
                            content=ft.Text(dia, size=9, color="grey"),
                            padding=ft.padding.only(top=10),
                            rotate=-0.5
                        )
                    )
                )
                
            if not pts_ventas:
                pts_ventas = [ft.LineChartDataPoint(0, 0)]
                pts_compras = [ft.LineChartDataPoint(0, 0)]
                
            self.chart_ventas.data_points = pts_ventas
            self.chart_compras.data_points = pts_compras
            
            self.line_chart.max_x = len(dias_ordenados) - 1 if dias_ordenados else 0
            max_y_calc = max_val_y * 1.15 if max_val_y > 0 else 1000
            self.line_chart.max_y = max_y_calc
            
            def formato_moneda_corta(valor):
                if valor >= 1000000: return f"${valor/1000000:.1f}M"
                if valor >= 1000: return f"${valor/1000:.0f}k"
                return f"${valor:.0f}"
                
            # Mayor densidad en Y: 8 divisiones en lugar de 5
            intervalo_y = max_y_calc / 8 if max_y_calc > 0 else 100
            etiquetas_y = [
                ft.ChartAxisLabel(value=step * intervalo_y, label=ft.Text(formato_moneda_corta(step * intervalo_y), size=11, color="grey"))
                for step in range(9)
            ]
            
            self.line_chart.left_axis.labels = etiquetas_y
            self.line_chart.left_axis.labels_interval = intervalo_y
            self.line_chart.bottom_axis.labels = etiquetas_x
            self.line_chart.bottom_axis.labels_interval = 1
            
            # Cuadrícula visible completa con efecto punteado
            self.line_chart.horizontal_grid_lines = ft.ChartGridLines(
                interval=intervalo_y,
                color=ft.colors.with_opacity(0.05, "black"),
                width=1,
                dash_pattern=[4, 4]
            )
            self.line_chart.vertical_grid_lines = ft.ChartGridLines(
                interval=2, # Línea vertical sincronizada con el eje X
                color=ft.colors.with_opacity(0.05, "black"),
                width=1,
                dash_pattern=[4, 4]
            )
            
        except Exception as e:
            print(f"Error crítico construyendo Chart Flet: {e}")
        
        # 3. Load Tables Data (A prueba de fallos)
        try:
            top_ventas = self.db.get_top_ventas_mes(limit=10)
            self.dt_ventas.rows.clear()
            for item in top_ventas:
                self.dt_ventas.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(item.get('codigo') or ''), size=11)),
                        ft.DataCell(ft.Container(content=ft.Text(str(item.get('producto') or ''), size=11, no_wrap=True), width=120)),
                        ft.DataCell(ft.Text(str(item.get('unidades_vendidas') or 0), size=11)),
                        ft.DataCell(ft.Text(f"${float(item.get('ingreso_total') or 0):,.2f}", size=11))
                    ])
                )
        except Exception as e:
            print(f"Error crítico en tabla ventas: {e}")
            
        try:
            top_costos = self.db.get_top_costo_inventario(limit=10)
            self.dt_costos.rows.clear()
            for item in top_costos:
                self.dt_costos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(item.get('codigo') or ''), size=11)),
                        ft.DataCell(ft.Container(content=ft.Text(str(item.get('producto') or ''), size=11, no_wrap=True), width=120)),
                        ft.DataCell(ft.Text(f"${float(item.get('valor_inventario') or 0):,.2f}", size=11)),
                        ft.DataCell(ft.Text(str(item.get('rotacion') or ''), size=11))
                    ])
                )
        except Exception as e:
            print(f"Error crítico en tabla costos: {e}")
            
        try:
            kpis_cat = self.db.get_kpis_por_categoria()
            self.categorias_row.controls.clear()
            for cat in kpis_cat:
                self.categorias_row.controls.append(self._build_categoria_card(cat))
        except Exception as e:
            print(f"Error cargando KPIs por categoría: {e}")
            
        # Apagar indicador de carga al finalizar todo el trabajo
        self.progress_bar.visible = False
        
        self.safe_update()

    def _build_kpi_card(self, title, value_control, icon, subtext_control=None):
        column_controls = [
            ft.Row([
                ft.Text(title, size=12, color="grey", weight="w500", expand=True),
                ft.Icon(ft.icons.HELP_OUTLINE, size=12, color="grey")
            ], spacing=5),
            value_control,
        ]
        if subtext_control:
            column_controls.append(subtext_control)
            
        value_control.size = 20
            
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=Config.COLOR_SECONDARY, size=24),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_SECONDARY),
                    padding=10,
                    border_radius=8
                ),
                ft.Column(column_controls, spacing=2, expand=True)
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
        )

    def _build_categoria_card(self, data):
        rentabilidad = float(data.get('rentabilidad') or 0)
        costo_inv = float(data.get('costo_inventario') or 0)
        vtas_tot = float(data.get('ventas_totales') or 0)
        rot = float(data.get('rotacion') or 0)
        return ft.Container(
            col={"sm": 12, "md": 6, "lg": 4},
            bgcolor="white",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#f0f0f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black")),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.CATEGORY, color=Config.COLOR_SECONDARY, size=20),
                    ft.Text(str(data.get("categoria") or "N/A").upper(), weight="bold", size=13, color=Config.COLOR_PRIMARY, expand=True)
                ]),
                ft.Divider(height=1, color="#f0f0f0"),
                ft.Row([ft.Text("Inventario:", size=11, color="grey"), ft.Text(f"${costo_inv:,.0f}", size=12, weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Ventas:", size=11, color="grey"), ft.Text(f"${vtas_tot:,.0f}", size=12, weight="bold", color="green")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Rotación:", size=11, color="grey"), ft.Text(f"{rot:.2f}x", size=12, weight="bold")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Rendimiento:", size=11, color="grey"), ft.Text(f"{rentabilidad:.1f}%", size=12, weight="bold", color="#2ecca0" if rentabilidad >= 0 else "red")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=6)
        )
````

## File: ui/views/ventas.py
````python
import flet as ft
import threading
import time
import json
import os
from pypdf import PdfReader, PdfWriter
from config import Config
from core.supabase_client import SupabaseClient
from core.gemini_parser import GeminiParser
import math
import datetime

class VentasView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.db = SupabaseClient()
        self.ai_parser = GeminiParser()
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        self.parsed_data = None # Para guardar temporalmente los datos extraídos
        
        # Controles de Búsqueda
        self.search_input = ft.TextField(
            hint_text="Buscar por código, descripción o factura...", 
            prefix_icon=ft.icons.SEARCH,
            border_radius=8,
            expand=True,
            bgcolor="white",
            height=40,
            on_submit=self.on_search
        )
        
        # Filtro de fecha
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )
        self.btn_date = ft.OutlinedButton(
            text="Filtrar por Fecha",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=self.open_date_picker,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=40
        )
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Dashboard Resumen
        self.lbl_ventas_hist = ft.Text("$0", size=20, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_ventas_hoy = ft.Text("$0", size=20, weight="bold", color="green")
        self.lbl_iva_hist = ft.Text("$0", size=20, weight="bold")
        self.lbl_iva_hoy = ft.Text("$0", size=20, weight="bold")
        
        self.summary_container = ft.Container(
            content=ft.Row([
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Ventas hasta la fecha"), self.lbl_ventas_hist]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Ventas realizadas hoy"), self.lbl_ventas_hoy]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("IVA Total Cobrado"), self.lbl_iva_hist]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("IVA Total en el día"), self.lbl_iva_hoy]), padding=5), expand=True),
            ])
        )
        
        self.btn_agregar = ft.ElevatedButton(
            text="Agregar Venta",
            icon=ft.icons.ADD,
            bgcolor=Config.COLOR_SECONDARY,
            color="white",
            height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # File Picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        
        # Diálogo de Carga
        self.lbl_loading_text = ft.Text("Preparando archivo...", text_align=ft.TextAlign.CENTER)
        self.dlg_loading = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesando con Inteligencia Artificial"),
            content=ft.Column([
                ft.ProgressRing(),
                self.lbl_loading_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
        )
        
        # Nuevo Diálogo de División PDF
        self.dlg_procesando_pdf = ft.AlertDialog(
            modal=True,
            content=ft.Row([
                ft.ProgressRing(),
                ft.Text("Dividiendo PDF en páginas locales...")
            ], alignment=ft.MainAxisAlignment.CENTER)
        )
        
        # Modal de Metadatos
        self.fecha_carga_actual = datetime.date.today().strftime("%Y-%m-%d")
        self.date_picker_cargas = ft.DatePicker(on_change=self.on_date_cargas_change)
        
        self.fecha_carga_btn = ft.OutlinedButton(
            text=self.fecha_carga_actual,
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_cargas.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=40,
            width=250
        )
        self.tipo_carga_dropdown = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Remisión"), ft.dropdown.Option("Factura POS")], dense=True, width=250)
        self.dlg_metadatos_pdf = ft.AlertDialog(
            modal=True,
            title=ft.Text("Metadatos del PDF"),
            content=ft.Column([
                ft.Text("Fecha de Documento:", size=12, color="grey", weight="bold"),
                self.fecha_carga_btn, 
                self.tipo_carga_dropdown
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cerrar_modal_metadatos),
                ft.ElevatedButton("Seleccionar Archivo", on_click=self._abrir_file_picker_desde_modal)
            ]
        )
        
        # Diálogo de Confirmación
        self.dlg_confirm = ft.AlertDialog(modal=True)
        
        # Tabla de Datos
        self.data_table = ft.DataTable(
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("Fecha", weight="bold")),
                ft.DataColumn(ft.Text("Factura", weight="bold")),
                ft.DataColumn(ft.Text("Código", weight="bold")),
                ft.DataColumn(ft.Container(content=ft.Text("Nombre / Descripción", weight="bold"), width=300)),
                ft.DataColumn(ft.Text("Cantidad", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Precio Unit.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("IVA", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Ingreso Total", weight="bold"), numeric=True),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        
        # Inicializar memoria local
        self.cargas_file = "cargas_locales.json"
        self.cargas_data = {}
        self._load_cargas()
        
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        # --- FILTROS TAB GESTIÓN DE CARGAS ---
        self.fecha_filtro_cargas = None
        self.date_picker_filtro_cargas = ft.DatePicker(on_change=self.on_date_filtro_cargas_change)
        
        self.btn_filtro_fecha_cargas = ft.OutlinedButton(
            text="Filtrar por Fecha",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_filtro_cargas.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=45
        )
        self.btn_clear_filtro_cargas = ft.IconButton(
            icon=ft.icons.CLEAR, tooltip="Limpiar Fecha",
            on_click=self.clear_filtro_fecha_cargas, visible=False, icon_color="red"
        )
        
        # Dropdowns con height ajustado y content_padding para evitar que el label se corte
        self.drop_filtro_tipo_cargas = ft.Dropdown(
            options=[ft.dropdown.Option("Todas"), ft.dropdown.Option("Remisiones"), ft.dropdown.Option("Ventas POS")],
            value="Todas", label="Tipo", dense=True, width=160, border_radius=8, content_padding=10, height=45,
            on_change=lambda e: self._render_tabla_cargas()
        )
        self.drop_filtro_estado_cargas = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Procesado con éxito"), ft.dropdown.Option("Falló"), ft.dropdown.Option("Guardado"), ft.dropdown.Option("Sobreescrito")],
            value="Todos", label="Estado", dense=True, width=170, border_radius=8, content_padding=10, height=45,
            on_change=lambda e: self._render_tabla_cargas()
        )

        # --- NUEVA TABLA DE GESTIÓN DE CARGAS ---
        self.table_cargas = ft.DataTable(
            data_row_min_height=40,
            data_row_max_height=40,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("ID", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Página", weight="bold")),
                ft.DataColumn(ft.Text("Tipo de Documento", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )

        # --- PREPARACIÓN DE LAS PESTAÑAS (TABS) ---

        # 1. Contenido del Tab 1: Registro Ventas
        btn_nueva_venta = ft.ElevatedButton(
            text="Agregar Venta", icon=ft.icons.ADD, bgcolor=Config.COLOR_SECONDARY, color="white", height=40,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        row_filtros_ventas = ft.Row([
            self.search_input,
            self.btn_date,
            self.btn_clear_date,
            ft.ElevatedButton(
                text="Buscar", icon=ft.icons.SEARCH, bgcolor=Config.COLOR_PRIMARY, color="white", height=40,
                on_click=self.on_search, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
            btn_nueva_venta
        ])

        contenedor_tabla_ventas = ft.Container(
            content=ft.Row([ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )

        footer_paginacion = ft.Container(
            content=ft.Row([self.lbl_total, ft.Container(expand=True), self.btn_prev, self.lbl_page_info, self.btn_next], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=10)
        )

        layout_tab_ventas = ft.Container(
            content=ft.Column([row_filtros_ventas, contenedor_tabla_ventas, footer_paginacion], expand=True, spacing=10),
            padding=ft.padding.only(top=15),
            expand=True
        )

        # 2. Contenido del Tab 2: Gestión de Cargas
        layout_tab_cargas = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.btn_filtro_fecha_cargas,
                    self.btn_clear_filtro_cargas,
                    self.drop_filtro_tipo_cargas,
                    self.drop_filtro_estado_cargas,
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        text="Subir PDF de Ventas",
                        icon=ft.icons.UPLOAD_FILE,
                        bgcolor=Config.COLOR_PRIMARY,
                        color="white",
                        height=45,
                        on_click=self._abrir_modal_metadatos,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    )
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(
                    content=ft.Column([self.table_cargas], scroll=ft.ScrollMode.ALWAYS),
                    expand=True,
                    border_radius=8,
                    border=ft.border.all(1, ft.colors.with_opacity(0.1, "black"))
                )
            ], expand=True, spacing=10),
            padding=ft.padding.only(top=15),
            expand=True
        )

        # 3. Definición del Contenedor de Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Registro Ventas", icon=ft.icons.LIST_ALT, content=layout_tab_ventas),
                ft.Tab(text="Gestión de Cargas", icon=ft.icons.DRIVE_FOLDER_UPLOAD, content=layout_tab_cargas)
            ],
            expand=True
        )

        # --- ENSAMBLAJE FINAL DE LA VISTA ---
        self.content = ft.Column([
            self.progress_bar,
            ft.Text("Registro de Ventas (Salidas)", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            self.summary_container,
            self.tabs
        ], expand=True, spacing=10)

        # Llamar al método de renderizado en lugar del mock
        self._render_tabla_cargas()

    def did_mount(self):
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        if hasattr(self, "dlg_loading") and self.dlg_loading not in self.page.overlay:
            self.page.overlay.append(self.dlg_loading)
        if hasattr(self, "dlg_confirm") and self.dlg_confirm not in self.page.overlay:
            self.page.overlay.append(self.dlg_confirm)
        if hasattr(self, "dlg_metadatos_pdf") and self.dlg_metadatos_pdf not in self.page.overlay:
            self.page.overlay.append(self.dlg_metadatos_pdf)
        if hasattr(self, "dlg_procesando_pdf") and self.dlg_procesando_pdf not in self.page.overlay:
            self.page.overlay.append(self.dlg_procesando_pdf)
        if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
        if hasattr(self, "date_picker_cargas") and self.date_picker_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_cargas)
        if hasattr(self, "date_picker_filtro_cargas") and self.date_picker_filtro_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_filtro_cargas)
            
        self.page.update()
        self.load_summary()
        self.load_data()
        self._render_tabla_cargas()

    def _abrir_modal_metadatos(self, e):
        self.dlg_metadatos_pdf.open = True
        self.page.update()

    def _cerrar_modal_metadatos(self, e=None):
        self.dlg_metadatos_pdf.open = False
        self.page.update()

    def on_date_filtro_cargas_change(self, e):
        if self.date_picker_filtro_cargas.value:
            self.fecha_filtro_cargas = self.date_picker_filtro_cargas.value.strftime("%Y-%m-%d")
            self.btn_filtro_fecha_cargas.text = self.fecha_filtro_cargas
            self.btn_clear_filtro_cargas.visible = True
            if self.page:
                self.page.update()
            self._render_tabla_cargas()

    def clear_filtro_fecha_cargas(self, e):
        self.fecha_filtro_cargas = None
        self.date_picker_filtro_cargas.value = None
        self.btn_filtro_fecha_cargas.text = "Filtrar por Fecha"
        self.btn_clear_filtro_cargas.visible = False
        if self.page:
            self.page.update()
        self._render_tabla_cargas()

    def on_date_cargas_change(self, e):
        if self.date_picker_cargas.value:
            self.fecha_carga_actual = self.date_picker_cargas.value.strftime("%Y-%m-%d")
            self.fecha_carga_btn.text = self.fecha_carga_actual
            if self.page:
                self.page.update()

    def _load_cargas(self):
        if os.path.exists(self.cargas_file):
            try:
                with open(self.cargas_file, "r", encoding="utf-8") as f:
                    self.cargas_data = json.load(f)
            except Exception:
                self.cargas_data = {}

    def _save_cargas(self):
        with open(self.cargas_file, "w", encoding="utf-8") as f:
            json.dump(self.cargas_data, f, indent=4)

    def _render_tabla_cargas(self):
        if not hasattr(self, 'table_cargas'): return
        self.table_cargas.rows.clear()
        
        # Aplanar diccionario
        lista_cargas = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                lista_cargas.append(data)
                
        # Ordenar por ID descendente (más nuevos arriba)
        lista_cargas.sort(key=lambda x: x["id"], reverse=True)
        
        for data in lista_cargas:
            # --- Filtrado Visual ---
            if self.fecha_filtro_cargas and data.get("fecha") != self.fecha_filtro_cargas:
                continue
                
            if self.drop_filtro_tipo_cargas.value != "Todas":
                # Traducir los nombres de los filtros a los nombres internos guardados
                tipo_bd = "Remisión" if self.drop_filtro_tipo_cargas.value == "Remisiones" else "Factura POS"
                if data.get("tipo") != tipo_bd:
                    continue
                    
            if self.drop_filtro_estado_cargas.value != "Todos" and data.get("estado") != self.drop_filtro_estado_cargas.value:
                continue
            # -----------------------
            
            id_carga = data["id"]
            nombre = f"Página No. {data['pagina']} ({data['fecha']})"
            tipo = data["tipo"]
            estado = data["estado"]
            
            txt_crono = ft.Text("⏱️ 20s", color="red", weight="bold", visible=False)
            
            texto_btn = "Extraer Datos" if estado in ["Nuevo", "Falló", "Sobreescrito"] else "Ver"
            color_btn = Config.COLOR_PRIMARY if texto_btn == "Extraer Datos" else "grey"
            icon_btn = ft.icons.DOCUMENT_SCANNER if texto_btn == "Extraer Datos" else ft.icons.VISIBILITY
            
            btn_accion = ft.ElevatedButton(
                text=texto_btn,
                icon=icon_btn,
                bgcolor=color_btn,
                color="white",
                height=30,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                on_click=lambda e, d=data, txt=txt_crono: self.on_accion_carga(e, d, txt)
            )
            
            acciones_row = ft.Row([btn_accion, txt_crono], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            color_estado = "black"
            if estado == "Procesado con éxito": color_estado = "green"
            elif estado == "Falló": color_estado = "red"
            elif estado == "Guardado": color_estado = "blue"
            elif estado == "Sobreescrito": color_estado = "orange"
            
            self.table_cargas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(id_carga))),
                        ft.DataCell(ft.Text(nombre, weight="bold")),
                        ft.DataCell(ft.Text(tipo)),
                        ft.DataCell(ft.Text(estado, color=color_estado, weight="bold")),
                        ft.DataCell(acciones_row),
                    ]
                )
            )
            
        if self.page:
            self.page.update()

    def on_accion_carga(self, e, data, txt_crono):
        btn = e.control
        if btn.text == "Ver":
            # Cargar los datos extraídos previamente en la memoria de la vista
            self.carga_activa = data
            self.parsed_data = data.get("datos_extraidos", [])
            
            # Recuperar nombres_insumos
            codigos_extraidos = set()
            for invoice in self.parsed_data:
                for p in invoice.get("productos", []):
                    codigos_extraidos.add(str(p.get("codigo_item", "")))
            if codigos_extraidos:
                self.nombres_insumos = self.db.get_nombres_insumos(list(codigos_extraidos))
            else:
                self.nombres_insumos = {}
                
            self.show_confirm_ui()
            return
            
        if getattr(self, "is_extraccion_activa", False):
            self.page.snack_bar = ft.SnackBar(ft.Text("Hay una extracción en proceso. Espere que termine el cronómetro."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Bloquear estado global
        self.is_extraccion_activa = True
        
        # Cambiar el texto del botón clickeado
        btn.text = "Extrayendo..."
        btn.icon = ft.icons.HOURGLASS_TOP
        
        # Deshabilitar TODOS los demás botones de extraer en la tabla
        for row in self.table_cargas.rows:
            accion_row = row.cells[-1].content
            b = accion_row.controls[0]
            if b.text == "Extraer Datos":
                b.disabled = True
                
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Analizando documento con Inteligencia Artificial..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()
        
        # Iniciar worker en segundo plano para no congelar la pantalla
        import threading
        threading.Thread(target=self._worker_extraccion, args=(data, btn, txt_crono), daemon=True).start()

    def _worker_extraccion(self, data, btn, txt_crono):
        try:
            # Como el archivo ya es de 1 página, pasamos el índice 0
            extracted = self.ai_parser.parse_ventas_pdf_page(data["archivo"], 0)
            
            if extracted and isinstance(extracted, list) and len(extracted) > 0:
                data["estado"] = "Procesado con éxito"
                data["datos_extraidos"] = extracted
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("¡Extracción exitosa!"), bgcolor="green")
            else:
                data["estado"] = "Falló"
                data["datos_extraidos"] = []
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Fallo en la extracción. Revise el PDF o intente de nuevo."), bgcolor="red")
                    
            if self.page:
                self.page.snack_bar.open = True
            self._save_cargas()
            
            # --- INICIO DEL CRONÓMETRO DE ENFRIAMIENTO (COOLDOWN) ---
            txt_crono.visible = True
            btn.text = "Enfriando..."
            btn.icon = ft.icons.TIMER
            for i in range(20, 0, -1):
                txt_crono.value = f"⏱️ {i}s"
                if self.page:
                    self.page.update()
                import time
                time.sleep(1)
                
        except Exception as ex:
            data["estado"] = "Falló"
            self._save_cargas()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error en extracción: {ex}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            self.is_extraccion_activa = False
            # Renderizar la tabla reactiva los botones automáticamente según su estado
            self._render_tabla_cargas()
        
    def load_summary(self):
        res = self.db.get_ventas_summary()
        self.lbl_ventas_hist.value = f"${res.get('total_historico', 0):,.2f}"
        self.lbl_ventas_hoy.value = f"${res.get('total_hoy', 0):,.2f}"
        self.lbl_iva_hist.value = f"${res.get('iva_historico', 0):,.2f}"
        self.lbl_iva_hoy.value = f"${res.get('iva_hoy', 0):,.2f}"
        if self.page:
            self.update()
            
    def open_date_picker(self, e):
        self.date_picker.pick_date()
        
    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_date.text = self.fecha_corte
            self.btn_clear_date.visible = True
            if self.page:
                self.page.update()
            self.current_page = 1
            self.load_data()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e):
        self.fecha_corte = None
        self.btn_date.text = "Filtrar por Fecha"
        self.btn_clear_date.visible = False
        self.date_picker.value = None
        if self.page:
            self.page.update()
        self.current_page = 1
        self.load_data()
        
    def _abrir_file_picker_desde_modal(self, e):
        self.fecha_seleccionada = self.fecha_carga_actual
        self.tipo_seleccionado = self.tipo_carga_dropdown.value
        self._cerrar_modal_metadatos()
        self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"], dialog_title="Selecciona el Reporte de Ventas")

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            pdf_path = e.files[0].path
            self.dlg_procesando_pdf.open = True
            self.page.update()
            
            threading.Thread(target=self._dividir_y_guardar_pdf, args=(pdf_path,), daemon=True).start()

    def _dividir_y_guardar_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            grupo_key = f"{self.fecha_seleccionada}_{self.tipo_seleccionado}"
            if grupo_key not in self.cargas_data:
                self.cargas_data[grupo_key] = {}
                
            paginas_existentes = [int(p) for p in self.cargas_data[grupo_key].keys()]
            max_pagina = max(paginas_existentes) if paginas_existentes else 0
            
            # Crear carpeta raíz para los PDFs temporales si no existe
            os.makedirs("pdfs_locales", exist_ok=True)
            
            paginas_procesadas = 0
            for i in range(total_pages):
                pagina_real = i + 1
                
                # Regla de Solapamiento: Ignorar páginas anteriores a la última cargada
                if max_pagina > 0 and pagina_real < max_pagina:
                    continue
                    
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                
                nombre_archivo = f"pdfs_locales/ventas_{self.fecha_seleccionada}_{self.tipo_seleccionado.replace(' ', '_')}_Pag_{pagina_real}.pdf"
                
                with open(nombre_archivo, "wb") as f:
                    writer.write(f)
                    
                estado = "Sobreescrito" if (max_pagina > 0 and pagina_real == max_pagina) else "Nuevo"
                
                # Asignación de ID único consecutivo
                nuevo_id = 1
                if self.cargas_data:
                    todos_ids = [item.get("id", 0) for g in self.cargas_data.values() for item in g.values()]
                    nuevo_id = max(todos_ids) + 1 if todos_ids else 1
                
                if str(pagina_real) in self.cargas_data[grupo_key]:
                    nuevo_id = self.cargas_data[grupo_key][str(pagina_real)]["id"]
                
                self.cargas_data[grupo_key][str(pagina_real)] = {
                    "id": nuevo_id,
                    "pagina": pagina_real,
                    "tipo": self.tipo_seleccionado,
                    "fecha": self.fecha_seleccionada,
                    "archivo": nombre_archivo,
                    "estado": estado
                }
                paginas_procesadas += 1
                
            self._save_cargas()
            self._render_tabla_cargas()
            
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Éxito: Se generaron {paginas_procesadas} páginas en local."), bgcolor="green")
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error fraccionando PDF: {ex}"), bgcolor="red")
        finally:
            self.dlg_procesando_pdf.open = False
            if self.page:
                self.page.snack_bar.open = True
                self.page.update()

    def animate_loading(self, base_msg):
        messages = [
            base_msg,
            "Puliendo datos para enviarlos...",
            "Generando el formato de carga...",
            "A unos pasos de finalizar..."
        ]
        idx = 0
        while getattr(self, "is_loading", False):
            if hasattr(self, "lbl_loading_text") and self.page:
                self.lbl_loading_text.value = messages[idx % len(messages)]
                try:
                    self.page.update()
                except Exception:
                    pass
            idx += 1
            time.sleep(5)

    def procesar_siguiente_pagina(self):
        if self.current_page_idx >= self.total_pages_pdf:
            self.page.snack_bar = ft.SnackBar(ft.Text("¡Proceso finalizado con éxito!", color="white"), bgcolor="green")
            self.page.snack_bar.open = True
            self.close_confirm_ui(None)
            self.load_data()
            return
            
        pagina_actual = self.current_page_idx + 1
        base_msg = f"Extrayendo datos de la página {pagina_actual} de {self.total_pages_pdf}..."
        self.lbl_loading_text.value = base_msg
        self.dlg_loading.open = True
        self.page.update()
        
        self.is_loading = True
        threading.Thread(target=self.animate_loading, args=(base_msg,), daemon=True).start()
        
        try:
            data = self.ai_parser.parse_ventas_pdf_page(self.current_pdf_path, self.current_page_idx)
            
            if data and isinstance(data, list):
                lista_facturas = [item.get("numero_factura") for item in data if item.get("numero_factura")]
                existentes = self.db.get_ventas_existentes(lista_facturas)
                
                data_nueva = []
                codigos_extraidos = set()
                for invoice in data:
                    factura = invoice.get("numero_factura")
                    if factura not in existentes:
                        data_nueva.append(invoice)
                        for p in invoice.get("productos", []):
                            codigos_extraidos.add(str(p.get("codigo_item", "")))
                
                self.parsed_data = data_nueva
                
                if codigos_extraidos:
                    self.nombres_insumos = self.db.get_nombres_insumos(list(codigos_extraidos))
                else:
                    self.nombres_insumos = {}
            else:
                self.parsed_data = []
                
            self.is_loading = False
            self.dlg_loading.open = False
            self.page.update()
            
            self.show_confirm_ui()
            
            if data and isinstance(data, list) and not self.parsed_data:
                self.page.snack_bar = ft.SnackBar(ft.Text("Todos los datos de esta página ya están registrados. Haz clic en Continuar.", color="white"), bgcolor="orange")
                self.page.snack_bar.open = True
                self.page.update()
            elif not data:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al procesar la página o no se extrajo información.", color="white"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as e:
            self.is_loading = False
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ocurrió un error inesperado: {str(e)}", color="white"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
                
    def update_totals(self, e=None):
        gran_cant = 0.0
        gran_costo = 0.0
        gran_iva = 0.0
        gran_total = 0.0
        
        factura_totals = {}
        
        for item in self.productos_rows:
            if item["type"] == "product":
                try:
                    cant = float(item["cantidad_ctl"].value.replace(',', '.'))
                    subtotal = float(item["subtotal_ctl"].value.replace(',', '.'))
                    iva = float(item["iva_ctl"].value.replace(',', '.'))
                    
                    row_total = subtotal + iva
                    item["total_ctl"].value = f"${row_total:,.2f}"
                    
                    precio_u = subtotal / cant if cant > 0 else 0
                    item["costo_ctl"].value = f"${precio_u:,.2f}"
                    
                    factura_idx = item["factura_idx"]
                    factura_totals[factura_idx] = factura_totals.get(factura_idx, 0) + row_total
                    
                    gran_cant += cant
                    gran_costo += precio_u
                    gran_iva += iva
                    gran_total += row_total
                except:
                    item["total_ctl"].value = "Error"
                    
        for item in self.productos_rows:
            if item["type"] == "header":
                idx = item["factura_idx"]
                total = factura_totals.get(idx, 0)
                item["total_factura_ctl"].value = f"Total Factura: ${total:,.2f}"
                
        self.txt_gran_cant.value = f"{gran_cant:,.2f}"
        self.txt_gran_costo.value = f"${gran_costo:,.2f}"
        self.txt_gran_iva.value = f"${gran_iva:,.2f}"
        self.txt_gran_total.value = f"${gran_total:,.2f}"
        if self.page:
            self.page.update()

    def show_confirm_ui(self):
        if not hasattr(self, "main_content"):
            self.main_content = self.content
            
        self.productos_rows = []
        facturas_count = len(self.parsed_data)
        productos_count = 0
        
        for idx, invoice in enumerate(self.parsed_data):
            fecha = invoice.get("fecha", "")
            factura = invoice.get("numero_factura", "")
            
            total_factura_ctl = ft.Text("Total Factura: $0.00", weight="bold", color=Config.COLOR_PRIMARY)
            self.productos_rows.append({
                "type": "header",
                "factura_idx": idx,
                "total_factura_ctl": total_factura_ctl,
                "row_ctl": ft.Container(
                    content=ft.Row([
                        ft.Text(f"Factura No.: {factura} | Fecha: {fecha}", weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(expand=True),
                        total_factura_ctl
                    ]),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY),
                    padding=5,
                    border_radius=5
                )
            })
            
            for p in invoice.get("productos", []):
                productos_count += 1
                cod = str(p.get("codigo_item", ""))
                nombre = self.nombres_insumos.get(cod, "Desconocido")
                
                def get_codigo_change_handler(nombre_control):
                    def handler(e):
                        val = e.control.value
                        if val:
                            nombres = self.db.get_nombres_insumos([val])
                            nombre_control.value = nombres.get(val, "Desconocido")
                        else:
                            nombre_control.value = "Desconocido"
                        nombre_control.tooltip = nombre_control.value
                        if self.page: self.page.update()
                    return handler
                
                nombre_ctl = ft.Text(nombre[:25], width=180, no_wrap=True, tooltip=nombre)
                codigo_ctl = ft.TextField(label="Código", value=cod, width=90, dense=True, on_change=get_codigo_change_handler(nombre_ctl))
                
                # Calcular precio unitario exacto: subtotal / cantidad
                cantidad_val = float(p.get("cantidad", 0))
                subtotal_val = float(p.get("subtotal", 0))
                precio_unitario = subtotal_val / cantidad_val if cantidad_val > 0 else 0.0
                
                cantidad_ctl = ft.TextField(label="Cant.", value=str(p.get("cantidad", 0)), width=70, dense=True, on_change=self.update_totals)
                subtotal_ctl = ft.TextField(label="Subtotal", value=str(subtotal_val), width=80, dense=True, on_change=self.update_totals)
                costo_ctl = ft.Text(f"${precio_unitario:,.2f}", width=80)
                iva_ctl = ft.TextField(label="IVA", value=str(p.get("iva", 0)), width=80, dense=True, on_change=self.update_totals)
                total_ctl = ft.Text("$0.00", width=100, weight="bold")
                
                self.productos_rows.append({
                    "type": "product",
                    "factura_idx": idx,
                    "fecha": fecha,
                    "factura": factura,
                    "codigo_ctl": codigo_ctl,
                    "nombre_ctl": nombre_ctl,
                    "cantidad_ctl": cantidad_ctl,
                    "subtotal_ctl": subtotal_ctl,
                    "costo_ctl": costo_ctl,
                    "iva_ctl": iva_ctl,
                    "total_ctl": total_ctl,
                    "row_ctl": ft.Row([codigo_ctl, nombre_ctl, cantidad_ctl, costo_ctl, subtotal_ctl, iva_ctl, total_ctl])
                })
            
        if len(self.productos_rows) == 0:
            list_view = ft.Container(
                content=ft.Text(
                    "Todos los datos de esta página ya están registrados en la base de datos.\nHaz clic en el botón de Confirmar para saltar a la siguiente página.",
                    color="orange",
                    weight="bold",
                    text_align=ft.TextAlign.CENTER,
                    size=16
                ),
                padding=50,
                alignment=ft.alignment.center,
                expand=True
            )
        else:
            list_view = ft.ListView(
                controls=[item["row_ctl"] for item in self.productos_rows],
                expand=True,
                spacing=10
            )
        
        self.txt_gran_cant = ft.Text("0", weight="bold")
        self.txt_gran_costo = ft.Text("$0", weight="bold")
        self.txt_gran_iva = ft.Text("$0", weight="bold")
        self.txt_gran_total = ft.Text("$0", weight="bold", size=18, color=Config.COLOR_PRIMARY)
        
        # Lógica de Botones Footer
        is_last_page = not (hasattr(self, 'total_pages_pdf') and self.current_page_idx < self.total_pages_pdf - 1)
        
        botones_acciones = [ft.TextButton("Volver", on_click=self.close_confirm_ui)]
        if not is_last_page:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar", bgcolor="grey", color="white", on_click=self.on_guardar_venta_partial))
            botones_acciones.append(ft.ElevatedButton("Confirmar y Continuar", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_venta))
        else:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar Todo", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_venta))
        
        # --- NUEVO DISEÑO DEL FOOTER ---
        # 1. Fila de Información Financiera (Estilo Dashboard)
        info_row = ft.Row([
            ft.Text("RESUMEN TOTAL", weight="bold", size=18, color=Config.COLOR_PRIMARY),
            ft.Container(expand=True), # Empuja los totales hacia la derecha
            
            ft.Column([ft.Text("Cant. Total", size=12, color="grey"), self.txt_gran_cant], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("Costo Base", size=12, color="grey"), self.txt_gran_costo], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("IVA Total", size=12, color="grey"), self.txt_gran_iva], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("GRAN TOTAL", size=12, color="grey", weight="bold"), self.txt_gran_total], spacing=2, horizontal_alignment="end"),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 2. Fila de Botones de Acción
        buttons_row = ft.Row([
            ft.Container(expand=True), # Empuja los botones hacia el extremo derecho
            *botones_acciones # Desempaqueta la lista de botones dinámicos
        ], alignment=ft.MainAxisAlignment.END)

        # 3. Contenedor Principal del Footer
        footer = ft.Container(
            content=ft.Column([
                info_row,
                ft.Divider(height=15, color=ft.colors.with_opacity(0.1, "black")),
                buttons_row
            ], spacing=0),
            bgcolor=ft.colors.with_opacity(0.03, Config.COLOR_PRIMARY),
            padding=20,
            border_radius=8,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY)),
            margin=ft.padding.only(top=10)
        )
        
        if hasattr(self, 'total_pages_pdf'):
            titulo = f"Datos Extraídos - Pág. No. {self.current_page_idx + 1} de {self.total_pages_pdf}"
        elif hasattr(self, 'carga_activa'):
            titulo = f"Datos Extraídos - Pág. No. {self.carga_activa.get('pagina', 1)} ({self.carga_activa.get('tipo', '')})"
        else:
            titulo = "Revisión de Ventas (Modo Inmersivo)"
        header = ft.Row([
            ft.Text(titulo, size=24, weight="bold"),
            ft.Text(f"{facturas_count} Facturas extraídas | {productos_count} Productos en total", color="grey")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.content = ft.Column([
            header,
            ft.Divider(),
            ft.Row([
                ft.Container(width=90, content=ft.Text("Código", weight="bold")),
                ft.Container(width=180, content=ft.Text("Nombre (desde BD)", weight="bold")),
                ft.Container(width=70, content=ft.Text("Cantidad", weight="bold")),
                ft.Container(width=80, content=ft.Text("Precio U.", weight="bold")),
                ft.Container(width=80, content=ft.Text("Subtotal", weight="bold")),
                ft.Container(width=80, content=ft.Text("IVA", weight="bold")),
                ft.Container(width=100, content=ft.Text("Costo Total", weight="bold"))
            ]),
            list_view,
            footer
        ], expand=True)
        
        self.update_totals()
        self.page.update()
        
    def close_confirm_ui(self, e):
        self.content = self.main_content
        self.page.update()
        
    def on_guardar_venta_partial(self, e):
        # Engañar a la lógica para que crea que es la última página
        if hasattr(self, 'total_pages_pdf'):
            self.current_page_idx = self.total_pages_pdf
        self.on_guardar_venta(e)

    def on_guardar_venta(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if self.page:
            self.update()
            
        threading.Thread(target=self._on_guardar_venta_worker, args=(btn_control,), daemon=True).start()

    def _on_guardar_venta_worker(self, btn_control):
        try:
            ventas_list = []
            
            # Recuperar metadatos de la carga que estamos confirmando
            fecha_doc = self.carga_activa["fecha"]
            tipo_doc = self.carga_activa["tipo"]
            pagina_origen = self.carga_activa["pagina"]
            
            for item in self.productos_rows:
                if item["type"] == "product":
                    try:
                        cant_str = str(item["cantidad_ctl"].value).replace(',', '.')
                        subtotal_str = str(item["subtotal_ctl"].value).replace(',', '.')
                        iva_str = str(item["iva_ctl"].value).replace(',', '.')
                        
                        cantidad = float(cant_str)
                        subtotal = float(subtotal_str)
                        iva = float(iva_str)
                        total = subtotal + iva
                        
                        ventas_list.append({
                            "fecha": fecha_doc, # Forzar la fecha seleccionada en el modal
                            "numero_factura": item["factura"],
                            "codigo_item": item["codigo_ctl"].value,
                            "descripcion": item["nombre_ctl"].value,
                            "cantidad": cantidad,
                            "precio_unitario": subtotal,
                            "iva": iva,
                            "costo_total": total,
                            "tipo_documento": tipo_doc,
                            "pagina_origen": pagina_origen
                        })
                    except ValueError:
                        self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico en cantidad, costo o IVA."), bgcolor="red")
                        self.page.snack_bar.open = True
                        self.page.update()
                        return
            
            if ventas_list:
                # 1. Eliminar datos viejos de esta misma página (si fue una sobreescritura)
                self.db.eliminar_ventas_origen(fecha_doc, tipo_doc, pagina_origen)
                
                # 2. Insertar los nuevos datos
                if self.db.insert_ventas(ventas_list):
                    self.page.snack_bar = ft.SnackBar(ft.Text(f"Página guardada exitosamente en BD."), bgcolor="green")
                    self.page.snack_bar.open = True
                    
                    # 3. Actualizar el estado local a Guardado
                    grupo_key = f"{fecha_doc}_{tipo_doc}"
                    if grupo_key in self.cargas_data and str(pagina_origen) in self.cargas_data[grupo_key]:
                        self.cargas_data[grupo_key][str(pagina_origen)]["estado"] = "Guardado"
                        self._save_cargas()
                    
                    self.close_confirm_ui(None)
                    self._render_tabla_cargas()
                    self.load_data()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar en base de datos"), bgcolor="red")
                    self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("No hay datos para guardar."), bgcolor="orange")
                self.page.snack_bar.open = True
                
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.update()
            
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        if self.page:
            self.update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        search_val = self.search_input.value or ""
        
        data, total = self.db.get_ventas(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val,
            fecha_corte=getattr(self, 'fecha_corte', None)
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        self.data_table.rows.clear()
        
        for item in data:
            fecha_raw = str(item.get('fecha', ''))
            fecha_formateada = fecha_raw[:10] if len(fecha_raw) >= 10 else fecha_raw
            
            cat_info = item.get('catalogo_insumos') or {}
            nombre_bd = cat_info.get('nombre')
            nombre_desc = item.get('descripcion')
            nombre_final = nombre_bd if nombre_bd else (nombre_desc if nombre_desc else 'Desconocido')
            
            cantidad = float(item.get('cantidad', 0) or 0)
            precio_unitario = float(item.get('subtotal', 0) or 0)
            iva = float(item.get('iva', 0) or 0)
            costo_total = float(item.get('total', 0) or 0)
            
            str_precio = f"${precio_unitario:,.2f}"
            str_iva = f"${iva:,.2f}"
            str_total = f"${costo_total:,.2f}"
            
            str_cantidad = str(int(cantidad)) if cantidad.is_integer() else str(cantidad)
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(fecha_formateada)),
                    ft.DataCell(ft.Text(str(item.get('factura_no') or 'N/A'))),
                    ft.DataCell(ft.Text(str(item.get('codigo_insumo', '')))),
                    ft.DataCell(ft.Container(content=ft.Text(nombre_final), width=300)),
                    ft.DataCell(ft.Text(str_cantidad, weight="bold")),
                    ft.DataCell(ft.Text(str_precio)),
                    ft.DataCell(ft.Text(str_iva, color="grey")),
                    ft.DataCell(ft.Text(str_total, color="green", weight="bold")),
                ]
            )
            self.data_table.rows.append(row)
            
        self.update_pagination_ui()
        
    def update_pagination_ui(self):
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros en total"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        # Apagar indicador de carga al finalizar
        self.progress_bar.visible = False
        
        if self.page:
            self.update()
        
    def on_search(self, e):
        self.current_page = 1
        self.load_data()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()
````

## File: ui/app.py
````python
import flet as ft
import threading
from ui.layout.sidebar import Sidebar
from ui.views.dashboard import DashboardView
from ui.views.inventario import InventarioView
from ui.views.compras import ComprasView
from ui.views.ventas import VentasView
from ui.views.cierre_inventario import CierreInventarioView
from ui.views.ajustes_inventario import AjustesInventarioView
class AppLayout(ft.Row):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.expand = True
        self.spacing = 0
        
        # Vistas
        self.views = {
            "dashboard": DashboardView(),
            "inventario": InventarioView(),
            "compras": ComprasView(),
            "ventas": VentasView(),
            "ajustes_inventario": AjustesInventarioView(),
            "cierre_mes": CierreInventarioView(),
        }
        
        # Contenedor principal de la vista activa
        self.active_view = ft.Container(
            content=self.views["dashboard"],
            expand=True,
            bgcolor="#F4F6F7",
            padding=15,
            alignment=ft.alignment.top_left
        )
        
        # Sidebar
        self.sidebar = Sidebar(self.on_route_change)
        
        # Componentes del Row
        self.controls = [
            self.sidebar,
            self.active_view
        ]
        
    def on_route_change(self, route_name):
        # Cambiar el contenido del contenedor principal
        if route_name in self.views:
            vista = self.views[route_name]
            self.active_view.content = vista
            self.active_view.update()
            
            # Resaltar la ruta activa en el menú lateral
            self.sidebar.update_active_route(route_name)
            
            # Forzar recarga de datos al navegar para evitar caché estancada
            # Se ejecuta en hilo secundario para evitar congelar la interfaz
            def load_data_bg():
                if hasattr(vista, 'load_data'):
                    try:
                        vista.load_data()
                    except Exception as e:
                        print(f"Error reload load_data en {route_name}: {e}")
                        
                if hasattr(vista, 'load_summary'):
                    try:
                        vista.load_summary()
                    except Exception as e:
                        print(f"Error reload load_summary en {route_name}: {e}")
            
            threading.Thread(target=load_data_bg, daemon=True).start()
````

## File: ui/views/cierre_inventario.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import datetime
from dateutil.relativedelta import relativedelta

class CierreInventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.db = SupabaseClient()
        self.datos_cierre = {}
        
        # Variables de Paginación Interna
        self.page_size = 50
        self.current_page = 1
        self.total_pages = 1
        self.insumos_lista = []
        
        # Opciones de Meses
        hoy = datetime.date.today()
        opciones_meses = []
        for i in range(12):
            m = hoy - relativedelta(months=i)
            val = m.strftime('%Y-%m')
            nombre_mes = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][m.month - 1]
            opciones_meses.append(ft.dropdown.Option(key=val, text=f'{nombre_mes} {m.year}'))
            
        self.mes_seleccionado = hoy.strftime('%Y-%m')
        
        # Controles Superiores
        self.month_dropdown = ft.Dropdown(
            options=opciones_meses,
            value=self.mes_seleccionado,
            label='Mes a iniciar',
            width=200,
            border_radius=8,
            height=40,
            on_change=self.on_month_change
        )
        
        self.btn_iniciar_snapshot = ft.ElevatedButton(
            text='Generar Preliminar',
            icon=ft.icons.CAMERA_ALT,
            bgcolor=Config.COLOR_SECONDARY,
            color='white',
            on_click=self.on_generar_snapshot
        )
        
        self.btn_aprobar_cierre = ft.ElevatedButton(
            text='Aprobar Cierre Definitivo',
            icon=ft.icons.CHECK_CIRCLE,
            bgcolor='green',
            color='white',
            disabled=True,
            on_click=self.on_aprobar_cierre
        )

        # Indicadores de Estado
        self.txt_estado_periodo = ft.Text('Estado: DESCONOCIDO', weight='bold')
        self.txt_progreso = ft.Text('Pendientes: 0 | Auditados: 0', color='grey')

        # Tabla de Auditoría
        self.data_table = ft.DataTable(
            column_spacing=15,
            data_row_min_height=50,
            data_row_max_height=50,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Container(width=25)), # Checkbox (vacio)
                ft.DataColumn(ft.Text('Código', weight='bold')),
                ft.DataColumn(ft.Text('Insumo', weight='bold')),
                ft.DataColumn(ft.Text('Inicial', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Entradas', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Salidas', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Ajustes', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Stock Actual', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Físico', weight='bold')),
                ft.DataColumn(ft.Text('Diferencia', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Costo Ajuste', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Observación', weight='bold')),
                ft.DataColumn(ft.Text('Estado', weight='bold')),
                ft.DataColumn(ft.Text('Acción', weight='bold')),
            ],
            rows=[]
        )

        self.current_auditoria_id = None
        self.current_fisico = 0
        
        # Modal de Ajuste
        self.form_codigo = ft.TextField(label='Cód. Insumo', width=120, disabled=True)
        self.form_nombre = ft.Text('Nombre del Insumo...', color='grey', size=14, weight='bold')
        self.form_tipo_ajuste = ft.Dropdown(
            label='Tipo',
            options=[ft.dropdown.Option('ENTRADA'), ft.dropdown.Option('SALIDA')],
            width=150,
            disabled=True
        )
        self.form_motivo = ft.Dropdown(label='Motivo Específico', width=250)
        self.form_cant = ft.TextField(label='Cantidad Ajuste', width=150, disabled=True)
        self.form_costo = ft.TextField(label='Costo Unitario ($)', width=150)
        self.form_obs = ft.TextField(label='Observaciones (Opcional)', expand=True)

        self.modal_ajuste = ft.AlertDialog(
            title=ft.Text('Ingresar Ajuste de Cierre'),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Row([self.form_codigo, ft.Container(content=self.form_nombre, expand=True, padding=10, bgcolor='#f5f5f5', border_radius=8)]),
                    ft.Row([self.form_tipo_ajuste, self.form_motivo]),
                    ft.Row([self.form_cant, self.form_costo]),
                    ft.Row([self.form_obs])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton('Cancelar', on_click=lambda e: self.cerrar_modal_ajuste()),
                ft.ElevatedButton('Guardar Ajuste', bgcolor=Config.COLOR_PRIMARY, color='white', on_click=self.on_guardar_ajuste_modal)
            ]
        )

        # Controles Paginación Interfaz
        self.lbl_page_info = ft.Text('Página 1 de 1')
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)

        # Controles Dashboard Financiero
        self.lbl_valor_sistema = ft.Text('$0.00', size=16, weight='bold', color=Config.COLOR_PRIMARY)
        self.lbl_ajustes_entrada = ft.Text('$0.00', size=16, weight='bold', color='green')
        self.lbl_cant_entrada = ft.Text('0 unds', size=10, color='grey')
        self.lbl_ajustes_salida = ft.Text('$0.00', size=16, weight='bold', color='red')
        self.lbl_cant_salida = ft.Text('0 unds', size=10, color='grey')
        self.lbl_neto_ajustes = ft.Text('$0.00', size=16, weight='bold')
        self.lbl_valor_fisico = ft.Text('$0.00', size=18, weight='bold', color=Config.COLOR_SECONDARY)
        
        self.summary_container = ft.Row([
            self._crear_kpi_card('Valor Sist.', self.lbl_valor_sistema, ft.icons.COMPUTER),
            self._crear_kpi_card('Sobrantes (+)', self.lbl_ajustes_entrada, ft.icons.ADD_CIRCLE_OUTLINE, self.lbl_cant_entrada),
            self._crear_kpi_card('Faltantes (-)', self.lbl_ajustes_salida, ft.icons.REMOVE_CIRCLE_OUTLINE, self.lbl_cant_salida),
            self._crear_kpi_card('Neto Ajustes', self.lbl_neto_ajustes, ft.icons.ACCOUNT_BALANCE_WALLET),
            self._crear_kpi_card('Valor Físico Proyectado', self.lbl_valor_fisico, ft.icons.FACT_CHECK)
        ], spacing=10)

        # Controles vista_lista (Maestro)
        self.dt_periodos = ft.DataTable(
            column_spacing=15,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Text('Periodo', weight='bold')),
                ft.DataColumn(ft.Text('Mes', weight='bold')),
                ft.DataColumn(ft.Text('Año', weight='bold')),
                ft.DataColumn(ft.Text('Estado', weight='bold')),
                ft.DataColumn(ft.Text('Acción', weight='bold')),
            ],
            rows=[]
        )
        self.vista_lista = ft.Column([
            ft.Text('Historial de Periodos', size=24, weight='bold', color=Config.COLOR_PRIMARY),
            ft.Row([self.month_dropdown, self.btn_iniciar_snapshot]),
            ft.Container(
                content=ft.Column([self.dt_periodos], scroll=ft.ScrollMode.ALWAYS, expand=True),
                expand=True
            )
        ], visible=True, expand=True)

        # Controles vista_detalle (Detalle)
        self.btn_volver = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=self.on_volver_lista)
        self.lbl_titulo_detalle = ft.Text('Auditoría: ...', size=24, weight='bold', color=Config.COLOR_PRIMARY)
        
        self.vista_detalle = ft.Column([
            ft.Row([self.btn_volver, self.lbl_titulo_detalle]),
            self.summary_container,
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    ft.Column([self.txt_estado_periodo, self.txt_progreso], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                    self.btn_aprobar_cierre
                ]),
                padding=15,
                bgcolor='white',
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, 'black'))
            ),
            ft.Container(
                content=ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS, expand=True),
                bgcolor='white',
                padding=5,
                border_radius=10,
                expand=True,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, 'black'))
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.only(top=10)
            )
        ], visible=False, expand=True, spacing=15)

        self.content = ft.Column([self.vista_lista, self.vista_detalle], expand=True)

    def _crear_kpi_card(self, title, lbl_val, icon, lbl_sub=None):
        col_controls = [ft.Text(title, size=11, color='grey', weight='bold'), lbl_val]
        if lbl_sub: col_controls.append(lbl_sub)
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=Config.COLOR_SECONDARY, size=24),
                ft.Column(col_controls, spacing=0)
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor='white', padding=15, border_radius=8, expand=True,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, 'black'))
        )

    def did_mount(self):
        if self.modal_ajuste not in self.page.overlay:
            self.page.overlay.append(self.modal_ajuste)
        self.load_lista_periodos()

    def load_lista_periodos(self):
        periodos = self.db.get_periodos_inventario()
        self.dt_periodos.rows.clear()
        
        for p in periodos:
            mes_periodo = p.get('mes_periodo', '')
            if not mes_periodo: continue
            
            parts = mes_periodo.split('-')
            year = parts[0]
            month = parts[1] if len(parts)>1 else ''
            
            estado = p.get('estado', 'DESCONOCIDO')
            color_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
            
            row = ft.DataRow(cells=[
                ft.DataCell(ft.Text(mes_periodo)),
                ft.DataCell(ft.Text(month)),
                ft.DataCell(ft.Text(year)),
                ft.DataCell(ft.Text(estado, color=color_estado.get(estado, 'black'), weight='bold')),
                ft.DataCell(ft.ElevatedButton('Ver', on_click=lambda e, m=mes_periodo: self.mostrar_detalle(m)))
            ])
            self.dt_periodos.rows.append(row)
            
        if self.page:
            self.page.update()

    def mostrar_detalle(self, mes):
        self.vista_lista.visible = False
        self.vista_detalle.visible = True
        self.mes_seleccionado = mes
        self.lbl_titulo_detalle.value = f'Auditoría: {mes}'
        self.current_page = 1
        self.load_data_detalle()

    def on_volver_lista(self, e):
        self.vista_detalle.visible = False
        self.vista_lista.visible = True
        self.load_lista_periodos()

    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.render_view()

    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.render_view()

    def on_month_change(self, e):
        self.mes_seleccionado = self.month_dropdown.value
        self.month_dropdown.update()

    def on_generar_snapshot(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        self.btn_aprobar_cierre.disabled = True
            
        if self.page:
            self.page.update()
            
        threading.Thread(target=self._on_generar_snapshot_worker, args=(btn_control,), daemon=True).start()

    def _on_generar_snapshot_worker(self, btn_control):
        try:
            res = self.db.iniciar_snapshot_cierre(self.mes_seleccionado)
            if res.get('exito'):
                self.page.snack_bar = ft.SnackBar(ft.Text('Preliminar generado correctamente.'), bgcolor='green')
                self.mostrar_detalle(self.mes_seleccionado)
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {res.get("error", "Desconocido")}'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page:
                self.page.update()
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f'Error interno: {str(ex)}'), bgcolor='red')
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.page.update()

    def on_aprobar_cierre(self, e):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        self.btn_iniciar_snapshot.disabled = True
            
        if self.page:
            self.page.update()
            
        threading.Thread(target=self._on_aprobar_cierre_worker, args=(btn_control,), daemon=True).start()

    def _on_aprobar_cierre_worker(self, btn_control):
        try:
            id_periodo = self.datos_cierre.get('periodo', {}).get('id_periodo')
            if not id_periodo:
                return
                
            res = self.db.aprobar_cierre_mes(id_periodo, 'Administrador Sistema')
            if res.get('exito'):
                self.page.snack_bar = ft.SnackBar(ft.Text('Período cerrado y consolidado con éxito.'), bgcolor='green')
                self.load_data_detalle()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {res.get("error", "Desconocido")}'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page:
                self.page.update()
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f'Error interno: {str(ex)}'), bgcolor='red')
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
            if self.page:
                self.page.update()

    def load_data_detalle(self):
        import math
        self.datos_cierre = self.db.obtener_estado_cierre(self.mes_seleccionado) or {}
        self.insumos_lista = self.datos_cierre.get('insumos', [])
        
        costos_fallback = self.db.get_catalogo_costos()
        for ins in self.insumos_lista:
            if not ins.get('costo_unitario_snapshot'):
                ins['costo_unitario_snapshot'] = costos_fallback.get(ins.get('codigo_insumo'), 0)
        
        total_records = len(self.insumos_lista)
        self.total_pages = math.ceil(total_records / self.page_size) if total_records > 0 else 1
        
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            
        self.render_view()

    def render_view(self):
        self.data_table.rows.clear()
        
        periodo = self.datos_cierre.get('periodo', {})
        resumen = self.datos_cierre.get('resumen', {})
        estado_periodo = periodo.get('estado', 'ABIERTO')
        
        # Validar fecha para Generar Preliminar
        hoy = datetime.date.today()
        partes_mes = self.mes_seleccionado.split('-')
        año_sel = int(partes_mes[0])
        mes_sel = int(partes_mes[1])
        mes_sig = mes_sel + 1
        año_sig = año_sel
        if mes_sig > 12:
            mes_sig = 1
            año_sig += 1
        fecha_habilitacion = datetime.date(año_sig, mes_sig, 1)
        
        if estado_periodo == 'ABIERTO' and hoy >= fecha_habilitacion:
            self.btn_iniciar_snapshot.disabled = False
            self.btn_iniciar_snapshot.tooltip = None
        else:
            self.btn_iniciar_snapshot.disabled = True
            if estado_periodo == 'ABIERTO':
                self.btn_iniciar_snapshot.tooltip = f'Disponible a partir del {fecha_habilitacion.strftime("%Y-%m-%d")}'
            else:
                self.btn_iniciar_snapshot.tooltip = 'Ya se generó el preliminar'

        if not self.datos_cierre or not self.datos_cierre.get('periodo'):
            self.txt_estado_periodo.value = 'Estado: NO INICIALIZADO'
            self.txt_estado_periodo.color = 'grey'
            self.txt_progreso.value = 'Requiere generar preliminar'
            self.btn_aprobar_cierre.disabled = True
            if self.page:
                self.page.update()
            return

        self.txt_estado_periodo.value = f'Estado: {estado_periodo}'
        color_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, 'black')
        
        pendientes = resumen.get('pendientes', 0)
        listos = resumen.get('auditados', 0) + resumen.get('ajustados', 0)
        self.txt_progreso.value = f'Pendientes: {pendientes} | Listos: {listos}'

        self.btn_aprobar_cierre.disabled = estado_periodo == 'CERRADO' or pendientes > 0

        # KPIs Financieros
        valor_sistema = 0.0
        valor_entrada = 0.0
        cant_entrada = 0.0
        valor_salida = 0.0
        cant_salida = 0.0

        for ins in self.insumos_lista:
            cant_sist = float(ins.get('cantidad_sistema') or 0)
            costo_u = float(ins.get('costo_unitario_snapshot') or 0)
            dif = ins.get('diferencia')

            valor_sistema += (cant_sist * costo_u)

            if dif is not None:
                dif_flt = float(dif)
                if dif_flt > 0:
                    valor_entrada += (dif_flt * costo_u)
                    cant_entrada += dif_flt
                elif dif_flt < 0:
                    valor_salida += (abs(dif_flt) * costo_u)
                    cant_salida += abs(dif_flt)

        valor_neto = valor_entrada - valor_salida
        valor_fisico = valor_sistema + valor_neto

        self.lbl_valor_sistema.value = f'${valor_sistema:,.2f}'
        self.lbl_ajustes_entrada.value = f'${valor_entrada:,.2f}'
        self.lbl_cant_entrada.value = f'+{cant_entrada:g} unds'
        self.lbl_ajustes_salida.value = f'${valor_salida:,.2f}'
        self.lbl_cant_salida.value = f'-{cant_salida:g} unds'
        self.lbl_neto_ajustes.value = f'${valor_neto:,.2f}'
        self.lbl_neto_ajustes.color = 'green' if valor_neto >= 0 else 'red'
        self.lbl_valor_fisico.value = f'${valor_fisico:,.2f}'

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.insumos_lista[start_idx:end_idx]

        for insumo in page_data:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))

        self.lbl_page_info.value = f'Página {self.current_page} de {self.total_pages}'
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)

        if self.page:
            self.page.update()

    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo.get('id_auditoria')
        estado_insumo = insumo.get('estado', 'PENDIENTE')
        cant_sistema = insumo.get('cantidad_sistema')
        cant_fisica = insumo.get('cantidad_fisica')
        diferencia = insumo.get('diferencia')
        observacion = insumo.get('observacion') or ''
        
        # Nuevas variables del Monitor en Tiempo Real
        stock_inicial = insumo.get('stock_inicial', 0)
        entradas = insumo.get('entradas', 0)
        salidas = insumo.get('salidas', 0)
        ajustes = insumo.get('ajustes', 0)
        stock_actual = insumo.get('stock_actual', 0)
        
        costo_unit = float(insumo.get('costo_unitario_snapshot') or 0)
        
        str_dif = ''
        str_costo_ajuste = ''
        color_diferencia = 'black'

        if diferencia is not None:
            dif_flt = float(diferencia)
            str_dif = f'{dif_flt:g}'
            if dif_flt != 0:
                color_diferencia = 'red'
                str_costo_ajuste = f'${(abs(dif_flt) * costo_unit):,.2f}'
        
        habilitar_txt_ajuste = estado_periodo == "PRELIMINAR" and estado_insumo != "APROBADO"
        habilitar_aceptar = estado_periodo == "PRELIMINAR" and estado_insumo == "PENDIENTE"
        
        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else '',
            dense=True, width=80, text_size=13, content_padding=10,
            disabled=not habilitar_txt_ajuste
        )

        btn_ajuste = ft.ElevatedButton(
            'Ingresar Ajuste', 
            icon=ft.icons.TUNE, 
            disabled=not habilitar_txt_ajuste,
            on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value)
        )

        btn_aceptar_sistema = ft.TextButton(
            text="Aceptar",
            icon=ft.icons.CHECK,
            icon_color="green",
            tooltip="Aceptar Stock del Sistema",
            style=ft.ButtonStyle(padding=ft.padding.all(5)),
            disabled=not habilitar_aceptar,
            on_click=lambda e, i_id=id_auditoria: self.procesar_aceptar_sistema(i_id)
        )

        acciones = ft.Row([btn_aceptar_sistema, btn_ajuste], spacing=5)

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Container(width=25)), # Checkbox (vacio)
                ft.DataCell(ft.Text(insumo.get('codigo_insumo', ''))),
                ft.DataCell(ft.Text(insumo.get('nombre', ''), width=150, no_wrap=True, tooltip=insumo.get('nombre'))),
                ft.DataCell(ft.Text(str(stock_inicial))),
                ft.DataCell(ft.Text(str(entradas), color='green')),
                ft.DataCell(ft.Text(str(salidas), color='red')),
                ft.DataCell(ft.Text(str(ajustes), color='orange')),
                ft.DataCell(ft.Text(str(stock_actual), weight='bold', color='blue')),
                ft.DataCell(txt_conteo),
                ft.DataCell(ft.Text(str_dif, color=color_diferencia)),
                ft.DataCell(ft.Text(str_costo_ajuste)),
                ft.DataCell(ft.Text(observacion, width=150, no_wrap=True, tooltip=observacion)),
                ft.DataCell(ft.Text(estado_insumo, size=11, weight='bold', color='grey')),
                ft.DataCell(acciones),
            ]
        )

    def abrir_modal_ajuste_cierre(self, insumo, fisico_txt):
        if not fisico_txt or str(fisico_txt).strip() == '':
            self.page.snack_bar = ft.SnackBar(ft.Text('Debe ingresar primero el conteo físico en la tabla'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()
            return
            
        try:
            fisico = float(fisico_txt)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text('El conteo físico no es un número válido'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()
            return
            
        stock_actual = float(insumo.get('cantidad_sistema') or insumo.get('stock_actual') or 0)
        diferencia = fisico - stock_actual
        
        self.form_codigo.value = insumo.get('codigo_insumo', '')
        self.form_nombre.value = insumo.get('nombre', '')
        self.form_nombre.color = 'black'
        self.form_costo.value = str(insumo.get('costo_unitario_snapshot', 0))
        self.form_cant.value = str(abs(diferencia))
        
        if diferencia > 0:
            self.form_tipo_ajuste.value = 'ENTRADA'
            self.form_motivo.options = [ft.dropdown.Option('SOBRANTE')]
            self.form_motivo.value = 'SOBRANTE'
        elif diferencia < 0:
            self.form_tipo_ajuste.value = 'SALIDA'
            self.form_motivo.options = [ft.dropdown.Option('FALTANTE')]
            self.form_motivo.value = 'FALTANTE'
        else:
            self.procesar_aceptar_sistema(insumo.get('id_auditoria'))
            return
            
        self.current_auditoria_id = insumo.get('id_auditoria')
        self.current_fisico = fisico
        self.modal_ajuste.open = True
        if self.page:
            self.page.update()

    def cerrar_modal_ajuste(self):
        self.modal_ajuste.open = False
        if self.page:
            self.page.update()

    def on_guardar_ajuste_modal(self, e):
        try:
            costo = float(self.form_costo.value)
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text('Costo inválido'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()
            return
            
        obs = self.form_obs.value.strip()
        motivo = self.form_motivo.value
        obs_final = f"[{motivo}] {obs}" if obs else f"[{motivo}]"
        
        fisico = self.current_fisico 
        
        res = self.db.registrar_conteo_fisico(self.current_auditoria_id, fisico, costo, obs_final)
        if res.get('exito'):
            self.cerrar_modal_ajuste()
            self.load_data_detalle()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {res.get("error")}'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()

    def procesar_aceptar_sistema(self, id_auditoria):
        if not id_auditoria: return
        res = self.db.aceptar_stock_sistema(id_auditoria)
        if res.get('exito'):
            self.load_data_detalle()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f'Error: {res.get("error")}'), bgcolor='red')
            self.page.snack_bar.open = True
            if self.page: self.page.update()
````

## File: ui/views/compras.py
````python
import flet as ft
import threading
import time
import json
import os
import datetime
from pypdf import PdfReader, PdfWriter
from config import Config
from core.supabase_client import SupabaseClient
from core.gemini_parser import GeminiParser
import math

class ComprasView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.db = SupabaseClient()
        self.ai_parser = GeminiParser()
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        self.parsed_data = None # Para guardar temporalmente los datos extraídos
        
        # Controles de Búsqueda
        self.search_input = ft.TextField(
            hint_text="Buscar por código, proveedor o factura...", 
            prefix_icon=ft.icons.SEARCH,
            border_radius=8,
            expand=True,
            bgcolor="white",
            height=40,
            on_submit=self.on_search
        )
        
        # Filtro de fecha
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )
        self.btn_date = ft.OutlinedButton(
            text="Filtrar por Fecha",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=self.open_date_picker,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=40
        )
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Dashboard Resumen
        self.lbl_compras_mes = ft.Text("$0", size=20, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_compras_hoy = ft.Text("$0", size=20, weight="bold", color="green")
        self.lbl_cantidad = ft.Text("0", size=20, weight="bold")
        
        self.summary_container = ft.Container(
            content=ft.Row([
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Total Compras en el Mes"), self.lbl_compras_mes]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Total Compras Hoy"), self.lbl_compras_hoy]), padding=5), expand=True),
                ft.Card(content=ft.Container(content=ft.Column([ft.Text("Cantidad Productos Comprados"), self.lbl_cantidad]), padding=5), expand=True),
            ])
        )
        
        self.btn_agregar = ft.ElevatedButton(
            text="Agregar Compra",
            icon=ft.icons.ADD,
            bgcolor=Config.COLOR_SECONDARY,
            color="white",
            height=40,
            on_click=self.on_agregar_click,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        
        # File Picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        
        # Diálogo de Carga
        self.lbl_loading_text = ft.Text("Preparando archivo...", text_align=ft.TextAlign.CENTER)
        self.dlg_loading = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesando con Inteligencia Artificial"),
            content=ft.Column([
                ft.ProgressRing(),
                self.lbl_loading_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
        )
        
        # Diálogo de Confirmación (se construirá dinámicamente)
        self.dlg_confirm = ft.AlertDialog(modal=True)
        
        # Tabla de Datos
        self.data_table = ft.DataTable(
            data_row_min_height=30,
            data_row_max_height=30,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("Fecha", weight="bold")),
                ft.DataColumn(ft.Text("No. Factura", weight="bold")),
                ft.DataColumn(ft.Text("Proveedor", weight="bold")),
                ft.DataColumn(ft.Text("Código Item", weight="bold")),
                ft.DataColumn(ft.Container(content=ft.Text("Nombre", weight="bold"), width=300)),
                ft.DataColumn(ft.Text("Cantidad", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Unit.", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Costo Total", weight="bold"), numeric=True),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        # --- TAB 2: GESTIÓN DE CARGAS ---
        self.cargas_file = "cargas_compras_locales.json"
        self.cargas_data = {}
        self._load_cargas()
        
        self.fecha_filtro_cargas = None
        self.date_picker_filtro_cargas = ft.DatePicker(on_change=self.on_date_filtro_cargas_change)
        
        self.btn_filtro_fecha_cargas = ft.OutlinedButton(
            text="Filtrar por Fecha",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_filtro_cargas.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=45
        )
        self.btn_clear_filtro_cargas = ft.IconButton(
            icon=ft.icons.CLEAR, tooltip="Limpiar Fecha",
            on_click=self.clear_filtro_fecha_cargas, visible=False, icon_color="red"
        )
        
        self.drop_filtro_estado_cargas = ft.Dropdown(
            options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Nuevo"), ft.dropdown.Option("Procesado con éxito"), ft.dropdown.Option("Falló"), ft.dropdown.Option("Guardado"), ft.dropdown.Option("Sobreescrito")],
            value="Todos", label="Estado", dense=True, width=170, border_radius=8, content_padding=10, height=45,
            on_change=lambda e: self._render_tabla_cargas()
        )
        
        self.table_cargas = ft.DataTable(
            data_row_min_height=40,
            data_row_max_height=40,
            heading_row_height=40,
            columns=[
                ft.DataColumn(ft.Text("ID", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Página", weight="bold")),
                ft.DataColumn(ft.Text("Archivo Original", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        # --- NUEVO MODAL DE METADATOS ---
        self.fecha_carga_actual = datetime.date.today().strftime("%Y-%m-%d")
        self.date_picker_cargas = ft.DatePicker(on_change=self.on_date_cargas_change)
        self.fecha_carga_btn = ft.OutlinedButton(
            text=self.fecha_carga_actual, icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda e: self.date_picker_cargas.pick_date(),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=40, width=250
        )
        self.dlg_metadatos_pdf = ft.AlertDialog(
            modal=True,
            title=ft.Text("Selecciona la Fecha de la Carga"),
            content=ft.Column([
                ft.Text("Fecha asignada a las compras del PDF:", size=12, color="grey", weight="bold"),
                self.fecha_carga_btn
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cerrar_modal_metadatos),
                ft.ElevatedButton("Seleccionar Archivo PDF", on_click=self._abrir_file_picker_desde_modal)
            ]
        )
        
        # --- PREPARACIÓN DE LAS PESTAÑAS (TABS) ---
        
        # 1. Contenido Tab 1: Registro Compras
        row_filtros_compras = ft.Row([
            self.search_input,
            self.btn_date,
            self.btn_clear_date,
            ft.ElevatedButton(
                text="Buscar", icon=ft.icons.SEARCH, bgcolor=Config.COLOR_PRIMARY, color="white", height=40,
                on_click=self.on_search, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
        ])
        
        contenedor_tabla_compras = ft.Container(
            content=ft.Row([ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        footer_paginacion = ft.Container(
            content=ft.Row([self.lbl_total, ft.Container(expand=True), self.btn_prev, self.lbl_page_info, self.btn_next], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=10)
        )
        
        layout_tab_compras = ft.Container(
            content=ft.Column([row_filtros_compras, contenedor_tabla_compras, footer_paginacion], expand=True, spacing=10),
            padding=10
        )
        
        # 2. Contenido Tab 2: Gestión de Cargas
        row_filtros_tab_cargas = ft.Row([
            self.btn_filtro_fecha_cargas,
            self.btn_clear_filtro_cargas,
            self.drop_filtro_estado_cargas,
            ft.Container(expand=True),
            ft.ElevatedButton(
                text="Subir PDF de Compras", icon=ft.icons.CLOUD_UPLOAD, bgcolor=Config.COLOR_SECONDARY, color="white", height=40,
                on_click=self.on_agregar_click, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            )
        ])
        
        contenedor_tabla_cargas = ft.Container(
            content=ft.Row([ft.Column([self.table_cargas], scroll=ft.ScrollMode.ALWAYS)], scroll=ft.ScrollMode.ALWAYS, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor="white", padding=5, border_radius=10, expand=True, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black"))
        )
        
        layout_tab_cargas = ft.Container(
            content=ft.Column([row_filtros_tab_cargas, contenedor_tabla_cargas], expand=True, spacing=10),
            padding=10
        )
        
        # Integrar las Pestañas
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Registro de Compras", content=layout_tab_compras, icon=ft.icons.SHOPPING_CART),
                ft.Tab(text="Gestión de Cargas", content=layout_tab_cargas, icon=ft.icons.FILE_UPLOAD),
            ],
            expand=True
        )

        self.content = ft.Column([
            self.progress_bar,
            ft.Text("Módulo de Compras", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            self.summary_container,
            self.tabs
        ], expand=True, spacing=10)
        
        self.load_data()
        self._render_tabla_cargas()

    def _load_cargas(self):
        if os.path.exists(self.cargas_file):
            try:
                with open(self.cargas_file, "r", encoding="utf-8") as f:
                    self.cargas_data = json.load(f)
            except Exception:
                self.cargas_data = {}
        else:
            self.cargas_data = {}

    def _save_cargas(self):
        try:
            with open(self.cargas_file, "w", encoding="utf-8") as f:
                json.dump(self.cargas_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error guardando cargas: {e}")

    def on_date_cargas_change(self, e):
        if self.date_picker_cargas.value:
            self.fecha_carga_actual = self.date_picker_cargas.value.strftime("%Y-%m-%d")
            self.fecha_carga_btn.text = self.fecha_carga_actual
            if self.page:
                self.page.update()

    def on_date_filtro_cargas_change(self, e):
        if self.date_picker_filtro_cargas.value:
            self.fecha_filtro_cargas = self.date_picker_filtro_cargas.value.strftime("%Y-%m-%d")
            self.btn_filtro_fecha_cargas.text = self.fecha_filtro_cargas
            self.btn_clear_filtro_cargas.visible = True
            if self.page:
                self.page.update()
            self._render_tabla_cargas()

    def clear_filtro_fecha_cargas(self, e):
        self.fecha_filtro_cargas = None
        self.btn_filtro_fecha_cargas.text = "Filtrar por Fecha"
        self.btn_clear_filtro_cargas.visible = False
        self.date_picker_filtro_cargas.value = None
        if self.page:
            self.page.update()
        self._render_tabla_cargas()

    def _render_tabla_cargas(self):
        self.table_cargas.rows.clear()
        
        lista_cargas = []
        for grupo_key, paginas in self.cargas_data.items():
            for num_pag, data in paginas.items():
                lista_cargas.append(data)
                
        # Ordenar por ID descendente (más nuevos arriba)
        lista_cargas.sort(key=lambda x: x["id"], reverse=True)
        
        for data in lista_cargas:
            # --- Filtrado Visual ---
            if self.fecha_filtro_cargas and data.get("fecha") != self.fecha_filtro_cargas:
                continue
                    
            if self.drop_filtro_estado_cargas.value != "Todos" and data.get("estado") != self.drop_filtro_estado_cargas.value:
                continue
            # -----------------------
            
            id_carga = data["id"]
            nombre = f"Página No. {data['pagina']} ({data['fecha']})"
            archivo_orig = os.path.basename(data.get("archivo_original", "Desconocido"))
            estado = data["estado"]
            
            txt_crono = ft.Text("⏱️ 20s", color="red", weight="bold", visible=False)
            
            texto_btn = "Extraer Datos" if estado in ["Nuevo", "Falló", "Sobreescrito"] else "Ver"
            color_btn = Config.COLOR_PRIMARY if texto_btn == "Extraer Datos" else "grey"
            icon_btn = ft.icons.DOCUMENT_SCANNER if texto_btn == "Extraer Datos" else ft.icons.VISIBILITY
            
            btn_accion = ft.ElevatedButton(
                text=texto_btn,
                icon=icon_btn,
                bgcolor=color_btn,
                color="white",
                height=30,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                on_click=lambda e, d=data, txt=txt_crono: self.on_accion_carga(e, d, txt)
            )
            
            acciones_row = ft.Row([btn_accion, txt_crono], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            color_estado = "black"
            if estado == "Procesado con éxito": color_estado = "green"
            elif estado == "Falló": color_estado = "red"
            elif estado == "Guardado": color_estado = "blue"
            elif estado == "Sobreescrito": color_estado = "orange"
            
            self.table_cargas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(id_carga))),
                        ft.DataCell(ft.Text(nombre, weight="bold")),
                        ft.DataCell(ft.Text(archivo_orig[:20] + "..." if len(archivo_orig) > 20 else archivo_orig, tooltip=archivo_orig)),
                        ft.DataCell(ft.Text(estado, color=color_estado, weight="bold")),
                        ft.DataCell(acciones_row),
                    ]
                )
            )
            
        if self.page:
            self.page.update()

    def on_accion_carga(self, e, data, txt_crono):
        btn = e.control
        if btn.text == "Ver":
            self.carga_activa = data
            self.parsed_data = data.get("datos_extraidos", [])
            
            codigos_extraidos = set()
            for invoice in self.parsed_data:
                for p in invoice.get("productos", []):
                    codigos_extraidos.add(str(p.get("codigo_insumo", "")))
            if codigos_extraidos:
                self.nombres_insumos = self.db.get_nombres_insumos(list(codigos_extraidos))
            else:
                self.nombres_insumos = {}
                
            self.show_confirm_ui()
            return
            
        if getattr(self, "is_extraccion_activa", False):
            self.page.snack_bar = ft.SnackBar(ft.Text("Hay una extracción en proceso. Espere que termine el cronómetro."), bgcolor="orange")
            self.page.snack_bar.open = True
            self.page.update()
            return

        self.is_extraccion_activa = True
        btn.text = "Extrayendo..."
        btn.icon = ft.icons.HOURGLASS_TOP
        
        for row in self.table_cargas.rows:
            accion_row = row.cells[-1].content
            b = accion_row.controls[0]
            if b.text == "Extraer Datos":
                b.disabled = True
                
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Analizando documento con Inteligencia Artificial..."), bgcolor="blue")
        self.page.snack_bar.open = True
        self.page.update()
        
        threading.Thread(target=self._worker_extraccion, args=(data, btn, txt_crono), daemon=True).start()

    def _worker_extraccion(self, data, btn, txt_crono):
        try:
            extracted = self.ai_parser.parse_compras_pdf_page(data["archivo"], 0)
            
            if extracted and isinstance(extracted, list) and len(extracted) > 0:
                data["estado"] = "Procesado con éxito"
                data["datos_extraidos"] = extracted
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("¡Extracción exitosa!"), bgcolor="green")
            else:
                data["estado"] = "Falló"
                data["datos_extraidos"] = []
                if self.page:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Fallo en la extracción. Revise el PDF o intente de nuevo."), bgcolor="red")
                    
            if self.page:
                self.page.snack_bar.open = True
            self._save_cargas()
            
            txt_crono.visible = True
            btn.text = "Enfriando..."
            btn.icon = ft.icons.TIMER
            for i in range(20, 0, -1):
                txt_crono.value = f"⏱️ {i}s"
                if self.page:
                    self.page.update()
                time.sleep(1)
                
        except Exception as ex:
            data["estado"] = "Falló"
            self._save_cargas()
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error en extracción: {ex}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            self.is_extraccion_activa = False
            self._render_tabla_cargas()
    def did_mount(self):
        # Agregar los overlays a la página principal
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
        if self.dlg_loading not in self.page.overlay:
            self.page.overlay.append(self.dlg_loading)
        if self.dlg_confirm not in self.page.overlay:
            self.page.overlay.append(self.dlg_confirm)
        if hasattr(self, "date_picker") and self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
            
        # Nuevos overlays para Cargas
        if hasattr(self, "dlg_metadatos_pdf") and self.dlg_metadatos_pdf not in self.page.overlay:
            self.page.overlay.append(self.dlg_metadatos_pdf)
        if hasattr(self, "date_picker_cargas") and self.date_picker_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_cargas)
        if hasattr(self, "date_picker_filtro_cargas") and self.date_picker_filtro_cargas not in self.page.overlay:
            self.page.overlay.append(self.date_picker_filtro_cargas)
            
        self.page.update()
        self.load_summary()
        self.load_data()
        
    def load_summary(self):
        res = self.db.get_compras_summary()
        self.lbl_compras_mes.value = f"${res.get('total_mes', 0):,.2f}"
        self.lbl_compras_hoy.value = f"${res.get('total_hoy', 0):,.2f}"
        self.lbl_cantidad.value = f"{res.get('cantidad_total', 0):,.2f}"
        if self.page:
            self.update()
            
    def open_date_picker(self, e):
        self.date_picker.pick_date()
        
    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_date.text = self.fecha_corte
            self.btn_clear_date.visible = True
            if self.page:
                self.page.update()
            self.current_page = 1
            self.load_data()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e):
        self.fecha_corte = None
        self.btn_date.text = "Filtrar por Fecha"
        self.btn_clear_date.visible = False
        self.date_picker.value = None
        if self.page:
            self.page.update()
        self.current_page = 1
        self.load_data()
        
    def on_agregar_click(self, e):
        # En lugar de abrir file_picker, abrimos el modal de metadatos
        self.dlg_metadatos_pdf.open = True
        if self.page:
            self.page.update()

    def _cerrar_modal_metadatos(self, e=None):
        self.dlg_metadatos_pdf.open = False
        if self.page:
            self.page.update()

    def _abrir_file_picker_desde_modal(self, e):
        self.fecha_seleccionada = self.fecha_carga_actual
        self._cerrar_modal_metadatos()
        self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"], dialog_title="Selecciona el Reporte de Compras")

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            pdf_path = e.files[0].path
            
            self.lbl_loading_text.value = "Dividiendo PDF en páginas..."
            self.dlg_loading.open = True
            self.page.update()
            
            threading.Thread(target=self._dividir_y_guardar_pdf, args=(pdf_path,), daemon=True).start()

    def _dividir_y_guardar_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            grupo_key = self.fecha_seleccionada
            if grupo_key not in self.cargas_data:
                self.cargas_data[grupo_key] = {}
                
            paginas_existentes = [int(p) for p in self.cargas_data[grupo_key].keys()]
            max_pagina = max(paginas_existentes) if paginas_existentes else 0
            
            max_id = 0
            for k, pags in self.cargas_data.items():
                for p_num, d in pags.items():
                    if d.get("id", 0) > max_id:
                        max_id = d["id"]
            
            os.makedirs("pdfs_locales", exist_ok=True)
            
            for p_idx in range(total_pages):
                num_pag = max_pagina + p_idx + 1
                id_carga = max_id + p_idx + 1
                
                writer = PdfWriter()
                writer.add_page(reader.pages[p_idx])
                
                nombre_archivo = f"compra_{grupo_key}_pag_{num_pag}.pdf"
                ruta_local = os.path.join("pdfs_locales", nombre_archivo)
                
                with open(ruta_local, "wb") as f:
                    writer.write(f)
                    
                self.cargas_data[grupo_key][str(num_pag)] = {
                    "id": id_carga,
                    "fecha": grupo_key,
                    "pagina": num_pag,
                    "archivo_original": pdf_path,
                    "archivo": ruta_local,
                    "estado": "Nuevo"
                }
                
            self._save_cargas()
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Se dividió el PDF en {total_pages} páginas exitosamente."), bgcolor="green")
            self.page.snack_bar.open = True
            
        except Exception as e:
            self.dlg_loading.open = False
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error procesando PDF: {e}"), bgcolor="red")
            self.page.snack_bar.open = True
            
        finally:
            if self.page:
                self.page.update()
                self._render_tabla_cargas()

    def animate_loading(self, base_msg):
        messages = [
            base_msg,
            "Puliendo datos para enviarlos...",
            "Generando el formato de carga...",
            "A unos pasos de finalizar..."
        ]
        idx = 0
        while getattr(self, "is_loading", False):
            if hasattr(self, "lbl_loading_text") and self.page:
                self.lbl_loading_text.value = messages[idx % len(messages)]
                try:
                    self.page.update()
                except Exception:
                    pass
            idx += 1
            time.sleep(5)
            self.is_loading = False
            self.dlg_loading.open = False
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Ocurrió un error inesperado: {str(e)}", color="white"), bgcolor="red")
                self.page.snack_bar.open = True
                self.page.update()
    def update_totals(self, e=None):
        gran_cant = 0.0
        gran_costo = 0.0
        gran_iva = 0.0
        gran_total = 0.0
        
        factura_totals = {}
        
        for item in self.productos_rows:
            if item["type"] == "product":
                try:
                    cant = float(item["cantidad_ctl"].value.replace(',', '.'))
                    costo = float(item["costo_ctl"].value.replace(',', '.'))
                    iva = float(item["iva_ctl"].value.replace(',', '.'))
                    
                    row_total = (cant * costo) + iva
                    item["total_ctl"].value = f"${row_total:,.2f}"
                    
                    factura_idx = item["factura_idx"]
                    factura_totals[factura_idx] = factura_totals.get(factura_idx, 0) + row_total
                    
                    gran_cant += cant
                    gran_costo += costo
                    gran_iva += iva
                    gran_total += row_total
                except:
                    item["total_ctl"].value = "Error"
                    
        for item in self.productos_rows:
            if item["type"] == "header":
                idx = item["factura_idx"]
                total = factura_totals.get(idx, 0)
                item["total_factura_ctl"].value = f"Total Factura: ${total:,.2f}"
                    
        self.txt_gran_cant.value = f"{gran_cant:,.2f}"
        self.txt_gran_costo.value = f"${gran_costo:,.2f}"
        self.txt_gran_iva.value = f"${gran_iva:,.2f}"
        self.txt_gran_total.value = f"${gran_total:,.2f}"
        if self.page:
            self.page.update()

    def show_confirm_ui(self):
        # Guardar el contenido original de la vista para poder volver a él
        if not hasattr(self, "main_content"):
            self.main_content = self.content
            
        self.productos_rows = []
        facturas_count = len(self.parsed_data)
        productos_count = 0
        
        # Como ahora parsed_data es una lista de facturas, las iteramos todas
        for idx, invoice in enumerate(self.parsed_data):
            ea = invoice.get("numero_entrada", "")
            fecha = invoice.get("fecha", "")
            factura = invoice.get("numero_factura", "")
            proveedor = invoice.get("proveedor", "")
            
            total_factura_ctl = ft.Text("Total Factura: $0.00", weight="bold", color=Config.COLOR_PRIMARY)
            self.productos_rows.append({
                "type": "header",
                "factura_idx": idx,
                "total_factura_ctl": total_factura_ctl,
                "row_ctl": ft.Container(
                    content=ft.Row([
                        ft.Text(f"EA: {ea} | Factura: {factura} | Fecha: {fecha}", weight="bold", color=Config.COLOR_PRIMARY),
                        ft.Container(expand=True),
                        total_factura_ctl
                    ]),
                    bgcolor=ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY),
                    padding=5,
                    border_radius=5
                )
            })
            
            # Productos de esta factura
            for p in invoice.get("productos", []):
                productos_count += 1
                cod = str(p.get("codigo_insumo", ""))
                # Extraemos el nombre de la BD si existe, sino lo dejamos como "Desconocido"
                nombre = self.nombres_insumos.get(cod, "Desconocido")
                
                def get_codigo_change_handler(nombre_control):
                    def handler(e):
                        val = e.control.value
                        if val:
                            nombres = self.db.get_nombres_insumos([val])
                            nombre_control.value = nombres.get(val, "Desconocido")
                        else:
                            nombre_control.value = "Desconocido"
                        nombre_control.tooltip = nombre_control.value
                        if self.page: self.page.update()
                    return handler
                
                nombre_ctl = ft.Text(nombre[:25], width=180, no_wrap=True, tooltip=nombre)
                codigo_ctl = ft.TextField(label="Código", value=cod, width=90, dense=True, on_change=get_codigo_change_handler(nombre_ctl))
                cantidad_ctl = ft.TextField(label="Cant.", value=str(p.get("cantidad", 0)), width=70, dense=True, on_change=self.update_totals)
                costo_ctl = ft.TextField(label="Costo U.", value=str(p.get("costo_unitario", 0)), width=80, dense=True, on_change=self.update_totals)
                iva_ctl = ft.TextField(label="IVA", value=str(p.get("iva", 0)), width=80, dense=True, on_change=self.update_totals)
                total_ctl = ft.Text("$0.00", width=100, weight="bold")
                
                self.productos_rows.append({
                    "type": "product",
                    "factura_idx": idx,
                    "ea": ea,
                    "fecha": fecha,
                    "factura": factura,
                    "proveedor": proveedor,
                    "codigo_ctl": codigo_ctl,
                    "nombre_ctl": nombre_ctl,
                    "cantidad_ctl": cantidad_ctl,
                    "costo_ctl": costo_ctl,
                    "iva_ctl": iva_ctl,
                    "total_ctl": total_ctl,
                    "row_ctl": ft.Row([codigo_ctl, nombre_ctl, cantidad_ctl, costo_ctl, iva_ctl, total_ctl])
                })
            
        list_view = ft.ListView(
            controls=[item["row_ctl"] for item in self.productos_rows],
            expand=True,
            spacing=10
        )
        
        # Resumen Visual y Controles de Totales
        self.txt_gran_cant = ft.Text("0", weight="bold")
        self.txt_gran_costo = ft.Text("$0", weight="bold")
        self.txt_gran_iva = ft.Text("$0", weight="bold")
        self.txt_gran_total = ft.Text("$0", weight="bold", size=18, color=Config.COLOR_PRIMARY)
        
        is_last_page = not (hasattr(self, 'total_pages_pdf') and self.current_page_idx < self.total_pages_pdf - 1)
        botones_acciones = [ft.TextButton("Volver", on_click=self.close_confirm_ui)]
        
        if not is_last_page:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar", bgcolor="grey", color="white", on_click=self.on_guardar_compra_partial))
            botones_acciones.append(ft.ElevatedButton("Confirmar y Continuar", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_compra))
        else:
            botones_acciones.append(ft.ElevatedButton("Confirmar y Guardar Todo", bgcolor=Config.COLOR_SECONDARY, color="white", on_click=self.on_guardar_compra))
            
        # --- NUEVO DISEÑO DEL FOOTER ---
        # 1. Fila de Información Financiera (Estilo Dashboard)
        info_row = ft.Row([
            ft.Text("RESUMEN TOTAL", weight="bold", size=18, color=Config.COLOR_PRIMARY),
            ft.Container(expand=True), # Empuja los totales hacia la derecha
            
            ft.Column([ft.Text("Cant. Total", size=12, color="grey"), self.txt_gran_cant], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("Costo Base", size=12, color="grey"), self.txt_gran_costo], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("IVA Total", size=12, color="grey"), self.txt_gran_iva], spacing=2, horizontal_alignment="end"),
            ft.Container(width=1, height=30, bgcolor=ft.colors.with_opacity(0.2, "grey"), margin=ft.padding.symmetric(horizontal=10)),
            
            ft.Column([ft.Text("GRAN TOTAL", size=12, color="grey", weight="bold"), self.txt_gran_total], spacing=2, horizontal_alignment="end"),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 2. Fila de Botones de Acción
        buttons_row = ft.Row([
            ft.Container(expand=True), # Empuja los botones hacia el extremo derecho
            *botones_acciones # Desempaqueta la lista de botones dinámicos
        ], alignment=ft.MainAxisAlignment.END)

        # 3. Contenedor Principal del Footer
        footer = ft.Container(
            content=ft.Column([
                info_row,
                ft.Divider(height=15, color=ft.colors.with_opacity(0.1, "black")),
                buttons_row
            ], spacing=0),
            bgcolor=ft.colors.with_opacity(0.03, Config.COLOR_PRIMARY),
            padding=20,
            border_radius=8,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, Config.COLOR_PRIMARY)),
            margin=ft.padding.only(top=10)
        )
        
        if hasattr(self, 'total_pages_pdf'):
            titulo = f"Datos Extraídos - Pág. No. {self.current_page_idx + 1} de {self.total_pages_pdf}"
        elif hasattr(self, 'carga_activa'):
            titulo = f"Datos Extraídos - Pág. No. {self.carga_activa.get('pagina', 1)}"
        else:
            titulo = "Revisión de Compras (Modo Inmersivo)"
        header = ft.Row([
            ft.Text(titulo, size=24, weight="bold"),
            ft.Text(f"{facturas_count} Facturas extraídas | {productos_count} Productos en total", color="grey")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Reemplazamos el contenido actual por el modo Inmersivo/Fullscreen
        self.content = ft.Column([
            header,
            ft.Divider(),
            ft.Row([
                ft.Container(width=90, content=ft.Text("Código", weight="bold")),
                ft.Container(width=180, content=ft.Text("Nombre (desde BD)", weight="bold")),
                ft.Container(width=70, content=ft.Text("Cantidad", weight="bold")),
                ft.Container(width=80, content=ft.Text("Costo U.", weight="bold")),
                ft.Container(width=80, content=ft.Text("IVA", weight="bold")),
                ft.Container(width=100, content=ft.Text("Costo Total", weight="bold"))
            ]),
            list_view,
            footer
        ], expand=True)
        
        self.update_totals()
        self.page.update()
        
    def close_confirm_ui(self, e):
        # Volver al diseño principal
        self.content = self.main_content
        self.page.update()
        
    def on_guardar_compra_partial(self, e):
        if hasattr(self, 'total_pages_pdf'):
            self.current_page_idx = self.total_pages_pdf
        self.on_guardar_compra(e)

    def on_guardar_compra(self, e):
        # 1. Bloquear interfaz y mostrar carga
        btn_control = e.control if e else None
        if btn_control:
            btn_control.disabled = True
            
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        if self.page:
            self.page.update()
            
        # 2. Lanzar worker de guardado
        import threading
        threading.Thread(target=self._guardar_compra_worker, args=(btn_control,), daemon=True).start()

    def _guardar_compra_worker(self, btn_control):
        try:
            compras_list = []
            lista_eas_to_delete = []
            
            # Si venimos del flujo nuevo de carga_activa:
            grupo_key = None
            pagina_origen = None
            if hasattr(self, 'carga_activa'):
                grupo_key = self.carga_activa["fecha"]
                pagina_origen = self.carga_activa["pagina"]

            for item in self.productos_rows:
                if item["type"] == "product":
                    cant_str = str(item["cantidad_ctl"].value).replace(',', '.')
                    costo_str = str(item["costo_ctl"].value).replace(',', '.')
                    iva_str = str(item["iva_ctl"].value).replace(',', '.')
                    
                    cantidad = float(cant_str)
                    costo = float(costo_str)
                    iva = float(iva_str)
                    total = (cantidad * costo) + iva
                    
                    fecha_val = grupo_key if grupo_key else item["fecha"]
                    if not fecha_val:
                        import datetime
                        fecha_val = datetime.date.today().strftime("%Y-%m-%d")
                        
                    compras_list.append({
                        "numero_entrada": item["ea"],
                        "fecha": fecha_val,
                        "numero_factura": item["factura"],
                        "proveedor": item["proveedor"],
                        "codigo_insumo": item["codigo_ctl"].value,
                        "cantidad": cantidad,
                        "costo_unitario": costo,
                        "iva": iva,
                        "costo_total": total
                    })
                    
                    if item["ea"] not in lista_eas_to_delete:
                        lista_eas_to_delete.append(item["ea"])
                        
            if compras_list:
                codigos_unicos = list(set([c["codigo_insumo"] for c in compras_list]))
                codigos_validos = self.db.get_nombres_insumos(codigos_unicos)
                
                codigos_invalidos = [c for c in codigos_unicos if c not in codigos_validos]
                if codigos_invalidos:
                    if self.page:
                        self.page.snack_bar = ft.SnackBar(
                            ft.Text(f"Códigos no existen en catálogo: {', '.join(codigos_invalidos)}. Corrígelos en la tabla primero.", color="white"), 
                            bgcolor="red",
                            duration=8000
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                    return
            
            if compras_list:
                # 1. Eliminar datos viejos de esta misma página
                self.db.eliminar_compras_por_entradas(lista_eas_to_delete)
                
                # 2. Insertar los nuevos datos
                if self.db.insert_compras(compras_list):
                    self.page.snack_bar = ft.SnackBar(ft.Text("Página guardada exitosamente en BD."), bgcolor="green")
                    self.page.snack_bar.open = True
                    
                    # 3. Actualizar el estado local a Guardado
                    if grupo_key and str(pagina_origen) in self.cargas_data.get(grupo_key, {}):
                        self.cargas_data[grupo_key][str(pagina_origen)]["estado"] = "Guardado"
                        self._save_cargas()
                        
                    self.close_confirm_ui(None)
                    self._render_tabla_cargas()
                    self.load_data()
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar en base de datos"), bgcolor="red")
                    self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("No hay datos para guardar."), bgcolor="orange")
                self.page.snack_bar.open = True
                    
        except ValueError:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico en cantidad, costo o IVA."), bgcolor="red")
                self.page.snack_bar.open = True
        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            # 3. Restaurar interfaz incondicionalmente
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            if btn_control:
                btn_control.disabled = False
                
            if self.page:
                self.page.update()
            
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        if self.page:
            self.update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        search_val = self.search_input.value or ""
        
        data, total = self.db.get_compras(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val,
            fecha_corte=getattr(self, 'fecha_corte', None)
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        self.data_table.rows.clear()
        
        for item in data:
            fecha_raw = str(item.get('fecha', ''))
            # Cortar a 'YYYY-MM-DD' si viene con timestamp
            fecha_formateada = fecha_raw[:10] if len(fecha_raw) >= 10 else fecha_raw
            
            # El nombre viene del JOIN con catalogo_insumos: catalogo_insumos.nombre
            cat_info = item.get('catalogo_insumos') or {}
            nombre_insumo = cat_info.get('nombre', 'Desconocido')
            
            cantidad = int(item.get('cantidad', 0) or 0)
            costo_unit = float(item.get('costo_unitario', 0) or 0)
            costo_tot = float(item.get('costo_total', 0) or 0)
            
            str_costo_unit = f"${costo_unit:,.2f}"
            str_costo_tot = f"${costo_tot:,.2f}"
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(fecha_formateada)),
                    ft.DataCell(ft.Text(str(item.get('numero_factura') or 'N/A'))),
                    ft.DataCell(ft.Text(str(item.get('proveedor') or 'N/A'))),
                    ft.DataCell(ft.Text(str(item.get('codigo_insumo', '')))),
                    ft.DataCell(ft.Container(content=ft.Text(nombre_insumo), width=300)),
                    ft.DataCell(ft.Text(str(cantidad), weight="bold")),
                    ft.DataCell(ft.Text(str_costo_unit)),
                    ft.DataCell(ft.Text(str_costo_tot, color="blue", weight="bold")),
                ]
            )
            self.data_table.rows.append(row)
            
        self.update_pagination_ui()
        
    def update_pagination_ui(self):
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros en total"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        # Apagar indicador de carga al finalizar
        self.progress_bar.visible = False
        
        if self.page:
            self.update()
        
    def on_search(self, e):
        self.current_page = 1
        self.load_data()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()
````

## File: ui/views/inventario.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import math
from datetime import datetime

class InventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.db = SupabaseClient()
        self.page_size = 15
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        # Variables de Ordenamiento por Servidor
        self.sort_col_name = "Insumo"
        self.sort_is_asc = True
        
        self.view_mode = "table"
        self.btn_toggle_view = ft.IconButton(
            icon=ft.icons.GRID_VIEW,
            tooltip="Cambiar a vista de Tarjetas",
            on_click=self.toggle_view
        )
        
        # Controles de Búsqueda
        self.search_input = ft.TextField(
            hint_text="Buscar por código o nombre...", 
            prefix_icon=ft.icons.SEARCH,
            border_radius=8,
            expand=True,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_submit=self.on_search
        )
        
        self.category_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Todas")],
            value="Todas",
            label="Categoría",
            width=220,
            border_radius=8,
            bgcolor="white",
            height=40,
            border_color=ft.colors.with_opacity(0.2, Config.COLOR_PRIMARY),
            content_padding=10,
            on_change=self.on_search
        )
        
        self.fecha_corte = None
        self.date_picker = ft.DatePicker(
            on_change=self.on_date_change,
            on_dismiss=self.on_date_dismiss,
        )
        self.btn_date = ft.OutlinedButton(
            text="Filtrar por Fecha",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=self.open_date_picker,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            height=40,
            width=200
        )
        self.btn_clear_date = ft.IconButton(
            icon=ft.icons.CLEAR,
            tooltip="Limpiar Fecha",
            on_click=self.clear_date,
            visible=False,
            icon_color="red"
        )
        
        # Diccionario base de columnas
        self.columnas_def = {
            "": ft.DataColumn(ft.Container(width=25)),
            "Código": ft.DataColumn(ft.Text("Código", weight="bold"), on_sort=self.on_sort_table),
            "Insumo": ft.DataColumn(ft.Container(content=ft.Text("Insumo", weight="bold"), width=250), on_sort=self.on_sort_table),
            "Categoría": ft.DataColumn(ft.Text("Categoría", weight="bold"), on_sort=self.on_sort_table),
            "Ubicación": ft.DataColumn(ft.Text("Ubicación", weight="bold")),
            "Stock Inicial": ft.DataColumn(ft.Container(content=ft.Text("Stock Ini.", weight="bold", size=11, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True),
            "Stock Mínimo": ft.DataColumn(ft.Container(content=ft.Text("Stock Mín.", weight="bold", size=11, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True),
            "Entradas": ft.DataColumn(ft.Container(content=ft.Text("Entradas", weight="bold", size=11, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
            "Salidas": ft.DataColumn(ft.Container(content=ft.Text("Salidas", weight="bold", size=11, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
            "Stock Real": ft.DataColumn(ft.Container(content=ft.Text("Stock Real", weight="bold", size=11, no_wrap=True), width=60, alignment=ft.alignment.center), numeric=True, on_sort=self.on_sort_table),
            "Costo Unit.": ft.DataColumn(ft.Text("Costo Unit.", weight="bold"), numeric=True),
            "Costo Total": ft.DataColumn(ft.Text("Costo Total", weight="bold"), numeric=True),
            "Precio Venta": ft.DataColumn(ft.Text("Precio Venta", weight="bold"), numeric=True),
            "Venta Total": ft.DataColumn(ft.Text("Venta Total", weight="bold"), numeric=True),
        }
        self.columnas_visibles = {k: True for k in self.columnas_def.keys()}
        
        self.btn_columns = ft.PopupMenuButton(
            icon=ft.icons.VIEW_COLUMN,
            tooltip="Mostrar/Ocultar Columnas",
            items=[]
        )
        
        # Definición de la Tabla de Datos (Ajuste de espacios y ordenamiento)
        self.data_table = ft.DataTable(
            column_spacing=10, # Reduce el espacio entre columnas
            horizontal_margin=10,
            data_row_min_height=30, # Reduce la altura de las filas
            data_row_max_height=30,
            heading_row_height=40,
            sort_column_index=0,
            sort_ascending=True,
            columns=[],
            rows=[],
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black")),
            border_radius=8,
            vertical_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
            horizontal_lines=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "black")),
        )
        
        self.table_container = ft.Container(
            content=ft.Column(
                [self.data_table],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            )
        )
        
        self.table_wrapper = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [self.table_container],
                        scroll=ft.ScrollMode.ALWAYS
                    )
                ],
                scroll=ft.ScrollMode.ALWAYS,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            bgcolor="white",
            padding=5,
            border_radius=10,
            expand=True,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.colors.with_opacity(0.05, "black")),
            visible=True
        )
        
        self.card_list_view = ft.ListView(expand=True, spacing=10, visible=False)
        
        # Controles Paginación
        self.lbl_page_info = ft.Text("Página 1 de 1")
        self.lbl_total = ft.Text("0 registros en total", color="grey")
        self.btn_prev = ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.on_prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.on_next_page, disabled=True)
        
        self.current_edit_context = None
        
        self.edit_panel_title = ft.Text("Editando Insumo", color="white", weight="bold", size=16)
        
        input_style = {
            "text_size": 13,
            "height": 40,
            "content_padding": 10,
            "bgcolor": "white",
            "color": "black",
            "border_color": ft.colors.with_opacity(0.3, "white"),
        }
        
        self.edit_stock_minimo = ft.TextField(width=120, **input_style)
        self.edit_costo = ft.TextField(width=120, **input_style)
        self.edit_precio = ft.TextField(width=120, **input_style)
        
        self.edit_categoria = ft.Dropdown(width=200, bgcolor="white", color="black", border_color=ft.colors.with_opacity(0.3, "white"), height=40, text_size=13)
        
        def verificar_cambios_panel(e):
            if not self.current_edit_context: return
            item = self.current_edit_context['item']
            cambiado = False
            try:
                if str(int(self.edit_stock_minimo.value)) != str(int(item.get('stock_minimo', 5) or 5)): cambiado = True
                if str(float(self.edit_costo.value)) != str(float(item.get('costo_unitario') or 0)): cambiado = True
                if str(float(self.edit_precio.value)) != str(float(item.get('precio_venta') or 0)): cambiado = True
                if self.edit_categoria.value != str(item.get('categoria', '')): cambiado = True
            except ValueError:
                cambiado = False
                
            self.btn_guardar_edicion.disabled = not cambiado
            self.action_bar.update()

        self.edit_stock_minimo.on_change = verificar_cambios_panel
        self.edit_costo.on_change = verificar_cambios_panel
        self.edit_precio.on_change = verificar_cambios_panel
        self.edit_categoria.on_change = verificar_cambios_panel
        
        self.btn_guardar_edicion = ft.ElevatedButton(
            "Guardar Cambios",
            disabled=True,
            on_click=self.on_guardar_global,
            style=ft.ButtonStyle(
                bgcolor={ft.MaterialState.DISABLED: "#495057", ft.MaterialState.DEFAULT: "green"},
                color={ft.MaterialState.DISABLED: "white70", ft.MaterialState.DEFAULT: "white"},
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )
        
        self.btn_gestionar_ajustes = ft.OutlinedButton(
            "Gestionar Ajustes",
            icon=ft.icons.TUNE,
            style=ft.ButtonStyle(color="white"),
            on_click=self.on_gestionar_ajustes
        )
        
        self.action_bar = ft.Container(
            content=ft.Column([
                ft.Row([self.edit_panel_title, self.btn_gestionar_ajustes], alignment=ft.MainAxisAlignment.START, spacing=15),
                ft.Row([
                    ft.Column([
                        ft.Text("Stock Mínimo", color="white70", size=11, weight="bold"),
                        self.edit_stock_minimo
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Costo Unit.", color="white70", size=11, weight="bold"),
                        self.edit_costo
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Precio Venta", color="white70", size=11, weight="bold"),
                        self.edit_precio
                    ], spacing=4),
                    ft.Column([
                        ft.Text("Categoría", color="white70", size=11, weight="bold"),
                        self.edit_categoria
                    ], spacing=4),
                    ft.Container(expand=True),
                    ft.OutlinedButton("Cancelar", style=ft.ButtonStyle(color="white"), on_click=self.on_cancelar_global),
                    self.btn_guardar_edicion
                ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=10),
            bgcolor=Config.COLOR_PRIMARY,
            padding=15,
            border_radius=10,
            visible=False,
            margin=ft.padding.only(top=10)
        )
        
        # Dashboard Resumen
        self.lbl_valor_inventario = ft.Text("$0", size=20, weight="bold", color="blue")
        self.lbl_ventas_total = ft.Text("$0", size=20, weight="bold", color="green")
        self.lbl_proyeccion_ventas = ft.Text("$0", size=20, weight="bold", color="blue")
        
        self.summary_container = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.INVENTORY, color="blue", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "blue"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Valorización del Inventario", size=12, color="grey", weight="bold"),
                        self.lbl_valor_inventario
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.ATTACH_MONEY, color="green", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "green"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Ingreso Total (Ventas)", size=12, color="grey", weight="bold"),
                        self.lbl_ventas_total
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.icons.MONETIZATION_ON, color="blue", size=24),
                        padding=15,
                        bgcolor=ft.colors.with_opacity(0.1, "blue"),
                        border_radius=10
                    ),
                    ft.Column([
                        ft.Text("Proyección de Ventas", size=12, color="grey", weight="bold"),
                        self.lbl_proyeccion_ventas
                    ], spacing=2)
                ]),
                bgcolor="white",
                padding=15,
                border_radius=10,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black")),
                expand=True
            )
        ], alignment=ft.MainAxisAlignment.START, spacing=20)
        
        self.progress_bar = ft.ProgressBar(color=Config.COLOR_SECONDARY, bgcolor="#eeeeee", visible=False)
        
        self.content = ft.Column([
            self.progress_bar,
            ft.Text("Catálogo de Insumos", size=24, weight="bold", color=Config.COLOR_PRIMARY),
            self.summary_container,
            
            # Toolbar de Filtros
            ft.Container(
                content=ft.Row([
                    self.search_input,
                    self.category_dropdown,
                    self.btn_date,
                    self.btn_clear_date,
                    ft.ElevatedButton(
                        text="Buscar", 
                        icon=ft.icons.SEARCH,
                        bgcolor=Config.COLOR_PRIMARY,
                        color="white",
                        height=40,
                        on_click=self.on_search,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    self.btn_toggle_view,
                    self.btn_columns
                ]),
                bgcolor="white",
                padding=10,
                border_radius=8,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.colors.with_opacity(0.05, "black"))
            ),
            
            # Contenedores de Vista Dual
            self.table_wrapper,
            self.card_list_view,
            
            # Footer Paginación
            ft.Container(
                content=ft.Row([
                    self.lbl_total,
                    ft.Container(expand=True),
                    self.btn_prev,
                    self.lbl_page_info,
                    self.btn_next,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.only(top=10)
            ),
            self.action_bar
        ], expand=True, spacing=10)
        
        # No llamamos a los métodos aquí porque el control no está en la página todavía
        
    def did_mount(self):
        """Se ejecuta cuando la vista se agrega a la pantalla."""
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
            self.safe_update()
            
        # Cargar configuración de columnas guardada
        if self.page.client_storage.contains_key("inventario_columnas"):
            stored_cols = self.page.client_storage.get("inventario_columnas")
            if stored_cols and isinstance(stored_cols, dict):
                self.columnas_visibles.update(stored_cols)
        self.update_columns_ui()
            
        # Lógica responsiva para la tabla
        def handle_resize(e):
            if getattr(self, "page", None) and getattr(self, "table_container", None):
                available = self.page.width - 320
                self.table_container.width = max(1300, available)
                try:
                    self.table_container.update()
                except Exception:
                    pass
                
        self.handle_resize = handle_resize
        
        # Suscribir de manera segura según la versión de Flet
        if hasattr(self.page.on_resize, "subscribe"):
            self.page.on_resize.subscribe(self.handle_resize)
        else:
            self.original_on_resize = self.page.on_resize
            self.page.on_resize = self.handle_resize
            
        handle_resize(None) # Ejecutar una vez para inicializar tamaño
            
        self.load_categories()
        self.load_summary()
        self.load_data()
        

    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass
    def load_summary(self):
        res_v = self.db.get_ventas_summary()
        res_i = self.db.get_inventario_kpis()
        self.lbl_valor_inventario.value = f"${res_i.get('valor_inventario', 0):,.2f}"
        self.lbl_ventas_total.value = f"${res_v.get('total_mes', 0):,.2f}"
        # La proyección se calcula localmente en _fetch_data_worker
        self.safe_update()
            
    def will_unmount(self):
        """Se ejecuta cuando se destruye la vista."""
        if hasattr(self.page, "on_resize") and hasattr(self.page.on_resize, "unsubscribe") and hasattr(self, "handle_resize"):
            self.page.on_resize.unsubscribe(self.handle_resize)
        elif hasattr(self, "original_on_resize"):
            self.page.on_resize = self.original_on_resize
        
    def load_categories(self):
        cats = self.db.get_categorias()
        options = [ft.dropdown.Option("Todas")]
        for c in cats:
            if c: options.append(ft.dropdown.Option(c))
        self.category_dropdown.options = options
        
    def update_columns_ui(self):
        # Actualiza las columnas de la tabla
        self.data_table.columns = [col for name, col in self.columnas_def.items() if self.columnas_visibles.get(name, True)]
        
        # Reconstruye el menú del Popup
        items = []
        for name in self.columnas_def.keys():
            is_visible = self.columnas_visibles.get(name, True)
            items.append(
                ft.PopupMenuItem(
                    text=name,
                    checked=is_visible,
                    on_click=lambda e, n=name: self.toggle_column(n)
                )
            )
        self.btn_columns.items = items
        
    def toggle_column(self, name):
        self.columnas_visibles[name] = not self.columnas_visibles.get(name, True)
        self.page.client_storage.set("inventario_columnas", self.columnas_visibles)
        self.update_columns_ui()
        self.load_data()
        
    def toggle_view(self, e):
        if self.view_mode == "table":
            self.view_mode = "cards"
            self.btn_toggle_view.icon = ft.icons.TABLE_ROWS
            self.btn_toggle_view.tooltip = "Cambiar a vista de Tabla"
            self.table_wrapper.visible = False
            self.card_list_view.visible = True
        else:
            self.view_mode = "table"
            self.btn_toggle_view.icon = ft.icons.GRID_VIEW
            self.btn_toggle_view.tooltip = "Cambiar a vista de Tarjetas"
            self.table_wrapper.visible = True
            self.card_list_view.visible = False
        self.safe_update()
        
    def load_data(self):
        """Enciende la interfaz de carga y lanza el hilo en segundo plano."""
        self.progress_bar.visible = True
        self.safe_update()
            
        threading.Thread(target=self._fetch_data_worker, daemon=True).start()

    def _fetch_data_worker(self):
        search_val = self.search_input.value or ""
        cat_val = self.category_dropdown.value or "Todas"
        
        data, total = self.db.get_insumos(
            page=self.current_page, 
            page_size=self.page_size, 
            search=search_val, 
            categoria=cat_val,
            fecha_corte=self.fecha_corte,
            sort_col=self.sort_col_name,
            sort_asc=self.sort_is_asc
        )
        
        self.total_records = total
        self.total_pages = math.ceil(total / self.page_size) if total > 0 else 1
        
        # Limpiar filas previas
        self.data_table.rows.clear()
        self.card_list_view.controls.clear()
        
        # Calcular Totales Globales
        proyeccion_total = 0.0
        self.valor_total_inventario = 0.0
        
        for insumo in data:
            stock = float(insumo.get("stock_actual") or 0)
            p_venta = float(insumo.get("precio_venta") or 0)
            costo_tot = float(insumo.get("costo_total_insumo") or 0)
            
            if stock > 0:
                proyeccion_total += (stock * p_venta)
            self.valor_total_inventario += costo_tot
            
        self.lbl_proyeccion_ventas.value = f"${proyeccion_total:,.0f}"
        self.safe_update()
        
        # Llenar tabla y tarjetas
        total_entradas = 0
        total_salidas = 0
        
        for item in data:
            row = self._crear_fila_inventario(item)
            self.data_table.rows.append(row)
            self.card_list_view.controls.append(self._crear_tarjeta_inventario(item, row))
            
            
        self.update_pagination_ui()


    def crear_celdas_fila(self, item, row_ref, edit_mode=False):
        stock_inicial = int(item.get('stock_inicial', 0) or 0)
        stock_minimo = int(item.get('stock_minimo', 5) or 5)
        entradas = int(item.get('entradas', 0) or 0)
        salidas = int(item.get('salidas', 0) or 0)
        
        stock_final = int(item.get('stock_real', item.get('stock_actual', 0)) or 0)
        
        costo_unit = float(item.get('costo_unitario') or 0)
        precio_venta = float(item.get('precio_venta') or 0)
        costo_total = float(item.get('costo_total_insumo') or 0)
        venta_total = float(item.get('venta_total_insumo') or 0)
        
        str_costo_unit = f"${costo_unit:,.2f}"
        str_precio_venta = f"${precio_venta:,.2f}"
        str_costo_total = f"${costo_total:,.2f}"
        str_venta_total = f"${venta_total:,.2f}"
        
        color_entradas = "green" if entradas > 0 else "black"
        color_salidas = "red" if salidas > 0 else "black"
        color_stock = "blue" if stock_final > 0 else "red"
        
        codigo = str(item.get('codigo_insumo', ''))
        nombre = str(item.get('nombre', ''))
        categoria = str(item.get('categoria', ''))
        ubicacion = str(item.get('ubicacion') or 'N/A')

        checkbox = ft.Checkbox(value=False, on_change=lambda e, i=item, r=row_ref: self.toggle_edit(e, i, r))
        
        cells_data = {
            "": ft.DataCell(ft.Container(content=checkbox, width=25, alignment=ft.alignment.center)),
            "Código": ft.DataCell(ft.Text(codigo)),
            "Insumo": ft.DataCell(ft.Container(content=ft.Text(nombre, no_wrap=True, tooltip=nombre), width=250)),
            "Categoría": ft.DataCell(ft.Text(categoria)),
            "Ubicación": ft.DataCell(ft.Text(ubicacion)),
            "Stock Inicial": ft.DataCell(ft.Container(content=ft.Text(str(stock_inicial)), width=60, alignment=ft.alignment.center_right)),
            "Stock Mínimo": ft.DataCell(ft.Container(content=ft.Text(str(stock_minimo)), width=60, alignment=ft.alignment.center_right)),
            "Entradas": ft.DataCell(ft.Container(content=ft.Text(str(entradas), color=color_entradas, weight="bold"), width=60, alignment=ft.alignment.center_right)),
            "Salidas": ft.DataCell(ft.Container(content=ft.Text(str(salidas), color=color_salidas, weight="bold"), width=60, alignment=ft.alignment.center_right)),
            "Stock Real": ft.DataCell(ft.Container(content=ft.Text(str(stock_final), color=color_stock, weight="bold"), width=60, alignment=ft.alignment.center_right)),
            "Costo Unit.": ft.DataCell(ft.Text(str_costo_unit)),
            "Costo Total": ft.DataCell(ft.Text(str_costo_total, color="blue")),
            "Precio Venta": ft.DataCell(ft.Text(str_precio_venta)),
            "Venta Total": ft.DataCell(ft.Text(str_venta_total, color="green")),
        }
            
        return [cells_data[name] for name in self.columnas_def.keys() if self.columnas_visibles.get(name, True)]

    def abrir_edicion_desde_tarjeta(self, item, row_ref):
        # Simular que se marcó el checkbox de la tabla para mantener sincronía
        if len(row_ref.cells) > 0:
            cb = row_ref.cells[0].content.content
            if isinstance(cb, ft.Checkbox):
                cb.value = True
                self.safe_update()
                    
        class DummyEvent:
            class DummyControl:
                value = True
            control = DummyControl()
            
        self.toggle_edit(DummyEvent(), item, row_ref)

    def toggle_edit(self, e, item, row_ref):
        if not e.control.value:
            self.cancelar_edicion()
            return
            
        if self.current_edit_context and self.current_edit_context['row'] != row_ref:
            prev_row = self.current_edit_context['row']
            if prev_row and len(prev_row.cells) > 0:
                cb = prev_row.cells[0].content.content
                if isinstance(cb, ft.Checkbox):
                    cb.value = False
                    
        self.current_edit_context = {
            'item': item,
            'row': row_ref
        }
        
        codigo = item.get('codigo_insumo')
        nombre = item.get('nombre')
        
        self.edit_panel_title.value = f"Editando: [{codigo}] {nombre}"
        self.edit_stock_minimo.value = str(int(item.get('stock_minimo', 5) or 5))
        self.edit_costo.value = str(float(item.get('costo_unitario') or 0))
        self.edit_precio.value = str(float(item.get('precio_venta') or 0))
        
        opts = [ft.dropdown.Option(c) for c in self.db.get_categorias()] if hasattr(self.db, 'get_categorias') else []
        self.edit_categoria.options = opts
        
        cat_val = item.get('categoria', '')
        self.edit_categoria.value = cat_val if any(o.key == cat_val or getattr(o, 'text', '') == cat_val for o in opts) else (opts[0].key if opts else "")
        
        self.btn_guardar_edicion.disabled = True
        self.action_bar.visible = True
        self.safe_update()

    def cancelar_edicion(self, e=None):
        if self.current_edit_context:
            row_ref = self.current_edit_context['row']
            if row_ref and len(row_ref.cells) > 0:
                cb = row_ref.cells[0].content.content
                if isinstance(cb, ft.Checkbox):
                    cb.value = False
        self.current_edit_context = None
        self.action_bar.visible = False
        self.safe_update()

    def abrir_dialogo_confirmacion(self):
        if not self.current_edit_context: return
        item = self.current_edit_context['item']
        
        cambios = []
        try:
            nuevo_stock_min = int(self.edit_stock_minimo.value)
            if nuevo_stock_min != int(item.get('stock_minimo', 5) or 5):
                cambios.append(f"Stock Mínimo: {int(item.get('stock_minimo', 5) or 5)} -> {nuevo_stock_min}")
                
            nuevo_costo = float(self.edit_costo.value)
            if nuevo_costo != float(item.get('costo_unitario') or 0):
                cambios.append(f"Costo Unitario: ${float(item.get('costo_unitario') or 0):.2f} -> ${nuevo_costo:.2f}")
                
            nuevo_precio = float(self.edit_precio.value)
            if nuevo_precio != float(item.get('precio_venta') or 0):
                cambios.append(f"Precio Venta: ${float(item.get('precio_venta') or 0):.2f} -> ${nuevo_precio:.2f}")
                
            nueva_cat = self.edit_categoria.value
            if nueva_cat != str(item.get('categoria', '')):
                cambios.append(f"Categoría: {item.get('categoria', '')} -> {nueva_cat}")
        except ValueError:
            self.page.snack_bar = ft.SnackBar(ft.Text("Error: Asegúrate de ingresar números válidos."), bgcolor="red")
            self.page.snack_bar.open = True
            self.safe_update()
            return

        if not cambios:
            self.cancelar_edicion()
            return

        resumen = "\n".join(cambios)
        
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Actualización"),
            content=ft.Text(f"Estás a punto de modificar el insumo: {item.get('codigo_insumo')} - {item.get('nombre')}.\n\nCambios detectados:\n{resumen}"),
        )
        
        def on_cancel(e):
            dlg.open = False
            self.safe_update()
            
        def on_save(e):
            self.ejecutar_guardado(dlg)
            
        dlg.actions = [
            ft.TextButton("Cancelar", on_click=on_cancel),
            ft.ElevatedButton("Guardar", bgcolor="green", color="white", on_click=on_save)
        ]
        
        self.page.overlay.append(dlg)
        dlg.open = True
        self.safe_update()

    def ejecutar_guardado(self, dialog=None):
        if dialog:
            dialog.open = False
            
        if hasattr(self, 'progress_bar'):
            self.progress_bar.visible = True
            
        self.safe_update()
            
        threading.Thread(target=self._ejecutar_guardado_worker, daemon=True).start()

    def _ejecutar_guardado_worker(self):
        try:
            if not self.current_edit_context: return
            item = self.current_edit_context['item']
            
            try:
                datos_actualizados = {
                    "stock_minimo": int(self.edit_stock_minimo.value),
                    "costo_unitario": float(self.edit_costo.value),
                    "precio_venta": float(self.edit_precio.value),
                    "categoria": self.edit_categoria.value
                }
            except ValueError:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error numérico al guardar."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()
                return
                
            codigo = item.get('codigo_insumo')
            exito = self.db.update_insumo(codigo, datos_actualizados)
            
            if exito:
                self.cancelar_edicion()
                
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Insumo {codigo} actualizado exitosamente."), bgcolor="green")
                self.page.snack_bar.open = True
                self.safe_update()
                
                self.load_data()
                self.load_summary()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error al actualizar en Base de Datos."), bgcolor="red")
                self.page.snack_bar.open = True
                self.safe_update()
                
            self.update_pagination_ui()

        except Exception as ex:
            if self.page:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {str(ex)}"), bgcolor="red")
                self.page.snack_bar.open = True
        finally:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.visible = False
            self.safe_update()
        
    def update_pagination_ui(self):
        self.lbl_page_info.value = f"Página {self.current_page} de {self.total_pages}"
        self.lbl_total.value = f"{self.total_records} registros en total"
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        # Apagar indicador de carga al finalizar
        self.progress_bar.visible = False
        
        self.safe_update()
        
    def on_search(self, e):
        self.current_page = 1
        self.load_data()
        
    def on_prev_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()
            
    def on_next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()
            
    def close_notification(self, e):
        self.notification_banner.visible = False
        self.safe_update()
        
    def open_date_picker(self, e):
        self.date_picker.pick_date()
        
    def on_date_change(self, e):
        if self.date_picker.value:
            self.fecha_corte = self.date_picker.value.strftime("%Y-%m-%d")
            self.btn_date.text = f"Fecha: {self.fecha_corte}"
            self.btn_clear_date.visible = True
            self.current_page = 1
            self.load_data()
            self.safe_update()
            
    def on_date_dismiss(self, e):
        pass
        
    def clear_date(self, e):
        self.fecha_corte = None
        self.date_picker.value = None
        self.btn_date.text = "Filtrar por Fecha"
        self.btn_clear_date.visible = False
        self.current_page = 1
        self.load_data()
        self.safe_update()

    def on_sort_table(self, e: ft.DataColumnSortEvent):
        """Delega el ordenamiento a la base de datos solicitando una nueva carga de datos."""
        self.data_table.sort_column_index = e.column_index
        self.data_table.sort_ascending = e.ascending
        
        # Identificar qué columna se hizo clic basándose en el diccionario
        column_keys = list(self.columnas_def.keys())
        
        # Descontar las columnas que estén ocultas para encontrar el índice real
        visible_keys = [k for k in column_keys if self.columnas_visibles.get(k, True)]
        
        if e.column_index < len(visible_keys):
            self.sort_col_name = visible_keys[e.column_index]
        
        self.sort_is_asc = e.ascending
        self.current_page = 1 # Volver a la primera página tras ordenar
        self.load_data()

    def on_guardar_global(self, e):
        self.abrir_dialogo_confirmacion()

    def on_cancelar_global(self, e):
        self.cancelar_edicion()

    def on_gestionar_ajustes(self, e):
        # Placeholder para enviar el código del insumo seleccionado al futuro módulo de ajustes
        if self.current_edit_context:
            codigo = self.current_edit_context['item'].get('codigo_insumo')
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Redirigiendo a gestión de ajustes para el insumo {codigo}..."), bgcolor="blue")
            self.page.snack_bar.open = True
            self.safe_update()

    def _crear_fila_inventario(self, item):
        row = ft.DataRow(cells=[])
        row.cells = self.crear_celdas_fila(item, row, edit_mode=False)
        return row

    def _crear_tarjeta_inventario(self, item, row):
        codigo = str(item.get('codigo_insumo') or '')
        nombre = str(item.get('nombre') or '')
        categoria = str(item.get('categoria') or '')
        ubicacion = str(item.get('ubicacion') or 'N/A')
        
        # Extracción Segura Paso 1
        costo_u = float(item.get("costo_unitario") or 0)
        p_venta = float(item.get("precio_venta") or 0)
        
        qty_ini = float(item.get("stock_inicial") or 0)
        val_ini = qty_ini * costo_u
        
        qty_comp = float(item.get("entradas") or 0)
        val_comp = float(item.get("costo_compras") or 0)
        
        qty_vent = float(item.get("salidas") or 0)
        val_vent = float(item.get("venta_total_insumo") or 0)
        
        qty_aj_ent = float(item.get("ajustes_entrada") or 0)
        val_aj_ent = qty_aj_ent * costo_u
        
        qty_aj_sal = float(item.get("ajustes_salida") or 0)
        val_aj_sal = qty_aj_sal * costo_u
        
        qty_aj_neto = float(item.get("ajustes") or 0)
        val_aj_neto = qty_aj_neto * costo_u
        
        stock_actual = float(item.get('stock_real', item.get('stock_actual', 0)) or 0)
        stock_minimo = float(item.get('stock_minimo') or 5)
        costo_total = float(item.get('costo_total_insumo') or 0)
        
        alerta = stock_actual <= stock_minimo
        badge_bg = "#ffebee" if alerta else "#f5f5f5"
        badge_color = "red" if alerta else ("green" if stock_actual > 0 else "black")
        
        proyeccion_venta = stock_actual * p_venta if stock_actual > 0 else 0
        participacion = (costo_total / self.valor_total_inventario) * 100 if getattr(self, 'valor_total_inventario', 0) > 0 else 0
        
        badge_costo = ft.Container(content=ft.Text(f"Costo U: ${costo_u:,.0f}", size=11, weight="bold", color="blue_grey_800"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="blue_grey_50", border_radius=15)
        badge_pventa = ft.Container(content=ft.Text(f"P. Venta: ${p_venta:,.0f}", size=11, weight="bold", color="teal_900"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="teal_50", border_radius=15)
        
        badge_proyeccion = ft.Container(
            content=ft.Text(f"Proy. Venta: ${proyeccion_venta:,.0f}", size=11, weight="bold", color="blue900"),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor="blue100",
            border_radius=15
        )
        
        badge_participacion = ft.Container(
            content=ft.Text(f"Peso Inv: {participacion:.1f}%", size=11, weight="bold", color="purple900"),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor="purple100",
            border_radius=15
        )
        
        badge_stock_actual = ft.Container(
            content=ft.Text(f"Stock Real: {stock_actual:g}", weight="bold", color=badge_color),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=badge_bg,
            border_radius=15
        )
        
        contenedor_badges = ft.Row(
            [badge_costo, badge_pventa, badge_participacion, badge_proyeccion, badge_stock_actual], 
            spacing=5, 
            alignment=ft.MainAxisAlignment.END,
            wrap=True
        )
        
        def crear_bloque_metricas(titulo, cantidad, valor, color_destacado):
            return ft.Column([
                ft.Text(titulo.upper(), size=10, color="grey", weight="bold"),
                ft.Text(f"{cantidad:g} unds", size=12, weight="bold", color="black87"),
                ft.Text(f"${valor:,.0f}", size=12, weight="bold", color=color_destacado)
            ], spacing=2, alignment=ft.MainAxisAlignment.START)
            
        color_neto = "red" if val_aj_neto < 0 else ("green" if val_aj_neto > 0 else "grey")
            
        fila_resultados = ft.Row([
            crear_bloque_metricas("Inicial", qty_ini, val_ini, "grey"),
            crear_bloque_metricas("Compras", qty_comp, val_comp, "#2ecca0"),
            crear_bloque_metricas("Ventas", qty_vent, val_vent, "#42a5f5"),
            crear_bloque_metricas("Ajustes Ent.", qty_aj_ent, val_aj_ent, "green"),
            crear_bloque_metricas("Ajustes Sal.", qty_aj_sal, val_aj_sal, "red"),
            crear_bloque_metricas("Neto Aj.", qty_aj_neto, val_aj_neto, color_neto)
        ], spacing=20, wrap=True)
        
        tarjeta = ft.Container(
            bgcolor="white",
            padding=15,
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            content=ft.Column([
                ft.Row([
                    ft.Text(f"{categoria} | {ubicacion}", size=12, color="grey"),
                    contenedor_badges
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(f"[{codigo}] {nombre}", size=15, weight="bold", expand=True),
                    ft.IconButton(icon=ft.icons.EDIT, icon_color="blue", tooltip="Editar Insumo", on_click=lambda e, i=item, r=row: self.abrir_edicion_desde_tarjeta(i, r))
                ]),
                fila_resultados
            ], spacing=8)
        )
        return tarjeta
````

## File: core/supabase_client.py
````python
import requests
import datetime
from config import Config

_client_instance = None

def get_client():
    """Retorna la instancia singleton del cliente Supabase."""
    global _client_instance
    if _client_instance is None:
        _client_instance = SupabaseClient()
    return _client_instance

class SupabaseClient:
    def __init__(self):
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY
        
        if self.url and self.url.endswith('/'):
            self.url = self.url[:-1]
        if self.url and not self.url.endswith('/rest/v1'):
            self.url = self.url + "/rest/v1"
            
        # 1. Instanciar la sesión compartida para mantener viva la conexión TCP
        self.session = requests.Session()
        
        # 2. Configurar los encabezados globales directamente en la sesión
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }
        self.session.headers.update(self.headers)
        
    def check_connection(self):
        if not self.url or not self.key:
            return False, "Faltan credenciales"
        try:
            # Prueba simple a la tabla (limit 1)
            response = self.session.get(f"{self.url}/catalogo_insumos?limit=1", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return True, "Conexión exitosa"
            return False, f"Error: {response.text}"
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en check_connection: el servidor no responde")
        except Exception as e:
            return False, str(e)
            
    # --- CRUD Catálogo Insumos ---
    
    def get_categorias(self):
        """Obtiene una lista de categorías únicas usando RPC si existe, o extrayendo de todo (simplificado)"""
        # Para simplificar y dado que PostgREST soporta distinct
        url = f"{self.url}/catalogo_insumos?select=categoria"
        headers = self.headers.copy()
        # En PostgREST podemos usar un header o query para distintos, pero es más fácil
        # traerlos y filtrarlos en memoria (limitado a unos cientos si hay muchos, pero está bien).
        response = self.session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            categorias = set([item.get('categoria', 'SIN CATEGORIA') for item in data if item.get('categoria')])
            return sorted(list(categorias))
        return []

    def get_insumos(self, page=1, page_size=20, search="", categoria="", fecha_corte=None, sort_col="Insumo", sort_asc=True):
        """
        Obtiene los insumos con paginación, filtros y ordenamiento desde el servidor.
        Retorna (lista_datos, total_count)
        """
        if fecha_corte:
            url = f"{self.url}/rpc/obtener_inventario_por_fecha?select=*"
        else:
            url = f"{self.url}/vista_inventario_completo?select=*"
        
        filtros = []
        if categoria and categoria != "Todas":
            filtros.append(f"categoria=eq.{categoria}")
            
        if search:
            filtros.append(f"or=(nombre.ilike.*{search}*,codigo_insumo.ilike.*{search}*)")
            
        if filtros:
            url += "&" + "&".join(filtros)
            
        # Mapeo de columnas de la interfaz a las columnas de la vista SQL
        db_col_stock = "stock_real" if fecha_corte else "stock_actual"
        map_columnas = {
            "Código": "codigo_insumo",
            "Insumo": "nombre",
            "Categoría": "categoria",
            "Ubicación": "ubicacion",
            "Stock Inicial": "stock_inicial",
            "Stock Mínimo": "stock_minimo",
            "Entradas": "entradas",
            "Salidas": "salidas",
            "Stock Real": db_col_stock
        }
        
        db_col = map_columnas.get(sort_col, "nombre")
        direccion = "asc" if sort_asc else "desc"
        
        offset = (page - 1) * page_size
        url += f"&order={db_col}.{direccion}&offset={offset}&limit={page_size}"
        
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            if fecha_corte:
                payload = {"p_fecha_corte": f"{fecha_corte} 23:59:59"}
                response = self.session.post(url, headers=headers, json=payload, timeout=10)
            else:
                response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code in (200, 201, 206):
                data = response.json()
                content_range = response.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                print(f"Error en consulta: {response.text}")
                return [], 0
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_insumos: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_insumos: {e}")
            return [], 0
        
    def insert_insumo(self, data: dict):
        url = f"{self.url}/catalogo_insumos"
        response = self.session.post(url, json=data, headers=self.headers, timeout=10)
        if response.status_code in (200, 201):
            return response.json()
        return None

    def update_insumo(self, codigo_insumo: str, datos_actualizados: dict) -> bool:
        """
        Actualiza un insumo existente en el catálogo.
        """
        url = f"{self.url}/catalogo_insumos?codigo_insumo=eq.{codigo_insumo}"
        try:
            response = self.session.patch(url, json=datos_actualizados, headers=self.headers, timeout=10)
            if response.status_code in (200, 204):
                return True
            else:
                print(f"Error al actualizar insumo: {response.text}")
                return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en update_insumo: el servidor no responde")
        except Exception as e:
            print(f"Excepción en update_insumo: {e}")
            return False

    def get_compras(self, page=1, page_size=20, search="", fecha_corte=None):
        url = f"{self.url}/registro_compras?select=*,catalogo_insumos(nombre)"
        
        filtros = []
        if search:
            filtros.append(f"or=(codigo_insumo.ilike.*{search}*,proveedor.ilike.*{search}*,numero_factura.ilike.*{search}*)")
        
        if fecha_corte:
            filtros.append(f"fecha=eq.{fecha_corte}")
            
        if filtros:
            url += "&" + "&".join(filtros)
            
        offset = (page - 1) * page_size
        url += f"&order=fecha.desc&offset={offset}&limit={page_size}"
        
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code in (200, 206):
                data = response.json()
                content_range = response.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                print(f"Error en consulta compras: {response.text}")
                return [], 0
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_compras: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_compras: {e}")
            return [], 0


    def insert_compras(self, compras_list: list):
        """
        Inserta una lista de registros de compras de forma masiva (bulk insert).
        """
        url = f"{self.url}/registro_compras"
        
        payload = []
        for c in compras_list:
            compra = {
                "fecha": c.get("fecha"),
                "numero_entrada": str(c.get("numero_entrada", "")),
                "numero_factura": str(c.get("numero_factura", "")),
                "proveedor": str(c.get("proveedor", "")),
                "codigo_insumo": str(c.get("codigo_insumo", "")),
                "cantidad": float(c.get("cantidad", 0) or 0),
                "costo_unitario": float(c.get("costo_unitario", 0) or 0),
                "valor_iva": float(c.get("iva", 0) or 0),
                "costo_total": float(c.get("costo_total", 0) or 0),
                "estado_registro": "VÁLIDO"
            }
            payload.append(compra)
            
        try:
            # PostgREST permite inserción masiva enviando una lista de diccionarios JSON
            response = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201, 204):
                return True
            else:
                print(f"Error al insertar compras: {response.text}")
                return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en insert_compras: el servidor no responde")
        except Exception as e:
            print(f"Excepción en insert_compras: {e}")
            return False

    def get_entradas_existentes(self, lista_eas: list) -> set:
        """
        Consulta cuáles de los 'numero_entrada' proveídos ya existen en registro_compras.
        """
        if not lista_eas:
            return set()
            
        url = f"{self.url}/registro_compras?select=numero_entrada"
        # Crear un filtro in.(EA-1,EA-2)
        eas_str = ",".join(lista_eas)
        url += f"&numero_entrada=in.({eas_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["numero_entrada"] for item in data if item.get("numero_entrada")}
            return set()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_entradas_existentes: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_entradas_existentes: {e}")
            return set()

    def eliminar_compras_por_entradas(self, lista_eas: list) -> bool:
        """
        Elimina las compras que coincidan con los numero_entrada dados para permitir sobreescritura.
        """
        if not lista_eas:
            return True
            
        url = f"{self.url}/registro_compras"
        eas_str = ",".join(lista_eas)
        url += f"?numero_entrada=in.({eas_str})"
        
        try:
            response = self.session.delete(url, headers=self.headers, timeout=10)
            if response.status_code in (200, 204):
                return True
            else:
                print(f"Error al eliminar compras por entradas: {response.text}")
                return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en eliminar_compras_por_entradas: el servidor no responde")
        except Exception as e:
            print(f"Excepción en eliminar_compras_por_entradas: {e}")
            return False
            
    def get_nombres_insumos(self, lista_codigos: list) -> dict:
        """
        Devuelve un diccionario {codigo: nombre} buscando en catalogo_insumos.
        """
        if not lista_codigos:
            return {}
            
        url = f"{self.url}/catalogo_insumos?select=codigo_insumo,nombre"
        
        # Como los códigos pueden ser strings (ej "0471"), envolvemos en comillas simples para la API de supabase,
        # o usamos in. sin problemas si PostgREST lo maneja.
        # PostgREST maneja in.(a,b,c). Para strings con espacios podría requerir doble comilla, 
        # pero para códigos numéricos en string basta unirlos con coma.
        codigos_str = ",".join(lista_codigos)
        url += f"&codigo_insumo=in.({codigos_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["codigo_insumo"]: item["nombre"] for item in data if item.get("codigo_insumo")}
            return {}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_nombres_insumos: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_nombres_insumos: {e}")
            return {}


    def get_ventas(self, page=1, page_size=20, search="", fecha_corte=None):
        """
        Obtiene el historial de ventas con paginación y búsqueda.
        Cruza con catalogo_insumos para obtener el nombre real del producto.
        """
        url = f"{self.url}/registro_ventas?select=*,catalogo_insumos(nombre)"
        
        filtros = []
        if search:
            filtros.append(f"or=(codigo_insumo.ilike.*{search}*,factura_no.ilike.*{search}*,descripcion.ilike.*{search}*)")
            
        if fecha_corte:
            filtros.append(f"fecha=eq.{fecha_corte}")
            
        if filtros:
            url += "&" + "&".join(filtros)
            
        offset = (page - 1) * page_size
        url += f"&order=fecha.desc&offset={offset}&limit={page_size}"
        
        headers = self.headers.copy()
        headers["Prefer"] = "count=exact"
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code in (200, 206):
                data = response.json()
                content_range = response.headers.get("Content-Range", "")
                total_count = 0
                if "/" in content_range:
                    total_count = int(content_range.split("/")[1])
                return data, total_count
            else:
                print(f"Error en consulta ventas: {response.text}")
                return [], 0
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_ventas: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_ventas: {e}")
            return [], 0


    def get_ventas_existentes(self, lista_facturas: list) -> set:
        """
        Consulta cuáles de las facturas (factura_no) proveídas ya existen en registro_ventas.
        """
        if not lista_facturas:
            return set()
            
        url = f"{self.url}/registro_ventas?select=factura_no"
        facturas_str = ",".join(lista_facturas)
        url += f"&factura_no=in.({facturas_str})"
        
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {item["factura_no"] for item in data if item.get("factura_no")}
            return set()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_ventas_existentes: el servidor no responde")
        except Exception as e:
            print(f"Excepción en get_ventas_existentes: {e}")
            return set()

    def eliminar_ventas_origen(self, fecha: str, tipo_documento: str, pagina_origen: int) -> bool:
        """Elimina las ventas de una fecha, tipo y página específica para permitir sobreescritura limpia."""
        url = f"{self.url}/registro_ventas?fecha=gte.{fecha}T00:00:00&fecha=lte.{fecha}T23:59:59&tipo_documento=eq.{tipo_documento}&pagina_origen=eq.{pagina_origen}"
        try:
            response = self.session.delete(url, headers=self.headers, timeout=10)
            return response.status_code in (200, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en eliminar_ventas_origen: el servidor no responde")
        except Exception as e:
            print(f"Error al eliminar ventas por origen: {e}")
            return False

    def insert_ventas(self, ventas_list: list):
        """Inserta una lista de registros de ventas de forma masiva (bulk insert)."""
        url = f"{self.url}/registro_ventas"
        
        payload = []
        for v in ventas_list:
            venta = {
                "fecha": v.get("fecha"),
                "factura_no": str(v.get("numero_factura", "")),
                "codigo_insumo": str(v.get("codigo_item", "")),
                "descripcion": str(v.get("descripcion", "")),
                "cantidad": float(v.get("cantidad", 0) or 0),
                "subtotal": float(v.get("precio_unitario", 0) or 0),
                "iva": float(v.get("iva", 0) or 0),
                "total": float(v.get("costo_total", 0) or 0),
                "tipo_documento": str(v.get("tipo_documento", "Factura POS")),
                "pagina_origen": int(v.get("pagina_origen", 1))
            }
            payload.append(venta)
            
        try:
            response = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201, 204):
                return True
            else:
                print(f"Error al insertar ventas: {response.text}")
                return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en insert_ventas: el servidor no responde")
        except Exception as e:
            print(f"Excepción en insert_ventas: {e}")
            return False



    def get_datos_conteo_inicial(self, mes_seleccionado: str) -> list:
        # mes_seleccionado is in format 'YYYY-MM'
        try:
            year, month = map(int, mes_seleccionado.split("-"))
            if month == 1:
                mes_anterior = f"{year - 1}-12"
            else:
                mes_anterior = f"{year}-{month - 1:02d}"
        except:
            return []
            
        # 1. Traer catalogo
        catalogo = []
        try:
            res_cat = self.session.get(f"{self.url}/catalogo_insumos?select=codigo_insumo,nombre,categoria", headers=self.headers, timeout=10)
            if res_cat.status_code == 200:
                catalogo = res_cat.json()
        except:
            pass
            
        # 2. Traer registros FINAL mes anterior
        cierre_anterior = {}
        try:
            url_ant = f"{self.url}/registro_auditorias_cierres?tipo_registro=eq.CIERRE_MENSUAL&fecha_cierre=gte.{mes_anterior}-01&fecha_cierre=lte.{mes_anterior}-31&select=codigo_insumo,cantidad_fisica"
            res_ant = self.session.get(url_ant, headers=self.headers, timeout=10)
            if res_ant.status_code == 200:
                for r in res_ant.json():
                    cierre_anterior[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except:
            pass
            
        # 3. Traer registros INICIAL mes seleccionado
        inicio_actual = {}
        try:
            url_act = f"{self.url}/registro_auditorias_cierres?tipo_registro=eq.INVENTARIO_INICIAL&fecha_cierre=gte.{mes_seleccionado}-01&fecha_cierre=lte.{mes_seleccionado}-31&select=codigo_insumo,cantidad_fisica"
            res_act = self.session.get(url_act, headers=self.headers, timeout=10)
            if res_act.status_code == 200:
                for r in res_act.json():
                    inicio_actual[r.get("codigo_insumo")] = r.get("cantidad_fisica")
        except:
            pass
            
        resultado = []
        for c in catalogo:
            codigo = c.get("codigo_insumo")
            if not codigo: continue
            
            resultado.append({
                "codigo_insumo": codigo,
                "nombre": c.get("nombre"),
                "categoria": c.get("categoria"),
                "cierre_mes_anterior": cierre_anterior.get(codigo, 0),
                "stock_inicial_actual": inicio_actual.get(codigo, 0),
            })
            
        return resultado

    def upsert_conteos_iniciales(self, registros: list) -> bool:
        if not registros: return True
        
        # Buscar IDs existentes para hacer merge por Primary Key (ya que no hay unique constraint compuesto)
        try:
            fecha_cierre = registros[0].get("fecha_cierre")
            tipo_registro = registros[0].get("tipo_registro")
            codigos = [r["codigo_insumo"] for r in registros]
            
            # Dividir en chunks si son muchos códigos para no exceder longitud de URL, o hacer query simple
            if len(codigos) > 0:
                codigos_str = ",".join(codigos)
                url_exist = f"{self.url}/registro_auditorias_cierres?fecha_cierre=eq.{fecha_cierre}&tipo_registro=eq.{tipo_registro}&codigo_insumo=in.({codigos_str})&select=id_auditoria,codigo_insumo"
                res_exist = self.session.get(url_exist, headers=self.headers, timeout=10)
                if res_exist.status_code == 200:
                    existentes = {item["codigo_insumo"]: item["id_auditoria"] for item in res_exist.json() if "id_auditoria" in item}
                    for r in registros:
                        if r["codigo_insumo"] in existentes:
                            r["id_auditoria"] = existentes[r["codigo_insumo"]]
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en upsert_conteos_iniciales: el servidor no responde")
        except Exception as e:
            print(f"Error al buscar existentes para upsert: {e}")
        
        url = f"{self.url}/registro_auditorias_cierres"
        
        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        
        try:
            res = self.session.post(url, json=registros, headers=headers, timeout=10)
            if res.status_code in (200, 201, 204):
                return True
            print(f"Error upsert_conteos: {res.text}")
            return False
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en upsert_conteos_iniciales: el servidor no responde")
        except Exception as e:
            print(f"Excepcion upsert_conteos: {e}")
            return False


    def get_top_costo_inventario(self, limit=10) -> list:
        # Cross reference with vista_inventario_completo to get rotacion (salidas)
        url = f"{self.url}/vista_inventario_completo?select=codigo_insumo,nombre,stock_actual,costo_unitario,salidas"
        resultado = []
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                for row in res.json():
                    stock = int(row.get("stock_actual", 0) or 0)
                    costo = float(row.get("costo_unitario", 0) or 0)
                    salidas = int(row.get("salidas", 0) or 0)
                    valor = stock * costo
                    
                    rotacion = f"{(salidas / stock):.1f}x" if stock > 0 else ("Alta" if salidas > 0 else "0.0x")
                    
                    resultado.append({
                        "codigo": row.get("codigo_insumo"),
                        "producto": row.get("nombre"),
                        "valor_inventario": valor,
                        "rotacion": rotacion
                    })
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_top_costo_inventario: el servidor no responde")
        except Exception as e:
            print(f"Error get_top_costo: {e}")
            return []
            
        resultado.sort(key=lambda x: x["valor_inventario"], reverse=True)
        return resultado[:limit]
        

    def get_compras_summary(self) -> dict:
        """Invoca RPC para totales de compras"""
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        
        url = f"{self.url}/rpc/get_compras_summary_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual, "dia_hoy": hoy}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_compras_summary: el servidor no responde")
        except Exception as e:
            print(f"Error RPC compras_summary: {e}")
        return {"total_mes": 0.0, "total_hoy": 0.0, "cantidad_total": 0.0}

    def get_ventas_summary(self) -> dict:
        """Invoca RPC para totales de ingresos e IVA"""
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        mes_actual = hoy[:7]
        
        url = f"{self.url}/rpc/get_ventas_summary_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual, "dia_hoy": hoy}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_ventas_summary: el servidor no responde")
        except Exception as e:
            print(f"Error RPC ventas_summary: {e}")
        return {"total_historico": 0.0, "total_mes": 0.0, "total_hoy": 0.0, "iva_historico": 0.0, "iva_hoy": 0.0}

    def get_catalogo_summary(self) -> dict:
        """Invoca RPC para compras totales y ventas totales en pesos"""
        url = f"{self.url}/rpc/get_catalogo_summary_rpc"
        try:
            res = self.session.post(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_catalogo_summary: el servidor no responde")
        except Exception as e:
            print(f"Error RPC catalogo_summary: {e}")
        return {"total_compras": 0.0, "total_ventas": 0.0}

    def get_top_ventas_mes(self, limit=10) -> list:
        mes_actual = datetime.date.today().strftime("%Y-%m")
        url = f"{self.url}/rpc/get_top_ventas_mes_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual, "limite": limit}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_top_ventas_mes: el servidor no responde")
        except Exception as e:
            print(f"Error RPC top_ventas: {e}")
        return []

    def get_tendencia_diaria(self) -> dict:
        """Invoca RPC para obtener ventas y compras agrupadas por día"""
        hoy = datetime.date.today()
        mes_actual = hoy.strftime("%Y-%m")
        
        # Pre-poblar el diccionario con ceros para todos los días transcurridos
        tendencia = {f"{mes_actual}-{i:02d}": {"ventas": 0.0, "compras": 0.0} for i in range(1, hoy.day + 1)}
        
        url = f"{self.url}/rpc/get_tendencia_diaria_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                for row in res.json():
                    dia = row.get("dia")
                    if dia in tendencia:
                        tendencia[dia]["ventas"] = float(row.get("ventas", 0))
                        tendencia[dia]["compras"] = float(row.get("compras", 0))
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_tendencia_diaria: el servidor no responde")
        except Exception as e:
            print(f"Error RPC tendencia_diaria: {e}")
        return tendencia

    def get_inventario_kpis(self) -> dict:
        mes_actual = datetime.date.today().strftime("%Y-%m")
        url = f"{self.url}/rpc/get_inventario_kpis_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_inventario_kpis: el servidor no responde")
        except Exception as e:
            print(f"Error RPC inventario_kpis: {e}")
        return {"valor_inventario": 0.0, "alertas_criticas": 0}

    def get_kpis_por_categoria(self) -> list:
        """Invoca RPC para extraer rendimiento y rotación agrupada por categoría."""
        url = f"{self.url}/rpc/get_kpis_por_categoria_rpc"
        try:
            res = self.session.post(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_kpis_por_categoria: el servidor no responde")
        except Exception as e:
            print(f"Error RPC get_kpis_por_categoria: {e}")
        return []

    def iniciar_snapshot_cierre(self, mes_periodo: str) -> dict:
        """Invoca el RPC para generar el snapshot preliminar del mes."""
        url = f"{self.url}/rpc/fn_snapshot_cierre_mensual"
        try:
            res = self.session.post(url, json={"p_mes": mes_periodo}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en iniciar_snapshot_cierre: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def obtener_estado_cierre(self, mes_periodo: str) -> dict:
        """Obtiene el resumen y los insumos del período especificado."""
        url = f"{self.url}/rpc/fn_obtener_estado_cierre"
        try:
            res = self.session.post(url, json={"p_mes": mes_periodo}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else {}
            return {}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en obtener_estado_cierre: el servidor no responde")
        except Exception as e:
            print(f"Error en obtener_estado_cierre: {e}")
            return {}

    def registrar_conteo_fisico(self, id_auditoria: str, cantidad: float, costo: float = None, observacion: str = None) -> dict:
        """Registra el conteo físico y genera ajustes si existe diferencia."""
        url = f"{self.url}/rpc/fn_registrar_conteo_fisico"
        payload = {
            "p_id_auditoria": id_auditoria,
            "p_cantidad_fisica": cantidad
        }
        if costo is not None:
            payload["p_costo_ajuste"] = costo
        if observacion:
            payload["p_observacion"] = observacion
            
        try:
            res = self.session.post(url, json=payload, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en registrar_conteo_fisico: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aceptar_stock_sistema(self, id_auditoria: str) -> dict:
        """Acepta el stock calculado por el sistema sin conteo físico."""
        url = f"{self.url}/rpc/fn_aceptar_stock_sistema"
        try:
            res = self.session.post(url, json={"p_id_auditoria": id_auditoria}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en aceptar_stock_sistema: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def aprobar_cierre_mes(self, id_periodo: str, aprobado_por: str) -> dict:
        """Cierra el período y consolida el inventario inicial del mes siguiente."""
        url = f"{self.url}/rpc/fn_aprobar_cierre_mes"
        try:
            res = self.session.post(url, json={"p_id_periodo": id_periodo, "p_aprobado_por": aprobado_por}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return {"exito": False, "error": res.text}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en aprobar_cierre_mes: el servidor no responde")
        except Exception as e:
            return {"exito": False, "error": str(e)}

    def get_catalogo_costos(self) -> dict:
        """Obtiene un diccionario con los costos actuales del catálogo de insumos"""
        url = f"{self.url}/catalogo_insumos?select=codigo_insumo,costo_unitario"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return {item.get('codigo_insumo'): float(item.get('costo_unitario') or 0) for item in res.json()}
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_catalogo_costos: el servidor no responde")
        except Exception as e:
            print(f"Error get_catalogo_costos: {e}")
        return {}

    def get_insumo_detalle(self, codigo: str) -> dict:
        """Recupera el nombre y costo de un insumo específico para el autocompletado."""
        url = f"{self.url}/catalogo_insumos?codigo_insumo=eq.{codigo}&select=nombre,costo_unitario"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200 and len(res.json()) > 0:
                return res.json()[0]
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_insumo_detalle: el servidor no responde")
        except Exception as e:
            pass
        return {}

    def get_ajustes_inventario(self) -> list:
        """Obtiene el historial de ajustes cruzado con el catálogo para extraer el nombre."""
        url = f"{self.url}/registro_ajustes_inventario?select=*,catalogo_insumos(nombre)&order=fecha_ajuste.desc"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_ajustes_inventario: el servidor no responde")
        except Exception as e:
            pass
        return []

    def insert_ajuste_individual(self, datos: dict) -> bool:
        """Inserta un nuevo registro de ajuste operativo."""
        url = f"{self.url}/registro_ajustes_inventario"
        try:
            res = self.session.post(url, json=datos, headers=self.headers, timeout=10)
            return res.status_code in (200, 201, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en insert_ajuste_individual: el servidor no responde")
        except Exception as e:
            return False

    def anular_ajuste(self, id_ajuste: str) -> bool:
        """Cambia el estado del ajuste a ANULADO. El trigger en la BD revertirá el inventario."""
        url = f"{self.url}/registro_ajustes_inventario?id_ajuste=eq.{id_ajuste}"
        try:
            res = self.session.patch(url, json={"estado_registro": "ANULADO"}, headers=self.headers, timeout=10)
            return res.status_code in (200, 204)
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en anular_ajuste: el servidor no responde")
        except Exception as e:
            return False

    def get_periodos_inventario(self) -> list:
        """Obtiene la lista de periodos de inventario ordenados descendentemente."""
        url = f"{self.url}/periodos_inventario?select=*&order=mes_periodo.desc"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return []
        except requests.exceptions.RequestException as req_e:
            print(f"Error de conexión con Supabase en get_periodos_inventario: el servidor no responde")
            return []
        except Exception as e:
            return []

    def get_proyeccion_ventas(self) -> float:
        """Invoca RPC get_proyeccion_ventas_rpc"""
        url = f"{self.url}/rpc/get_proyeccion_ventas_rpc"
        try:
            res = self.session.post(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return float(data) if data is not None else 0.0
            return 0.0
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_proyeccion_ventas: el servidor no responde")
            return 0.0
        except Exception:
            return 0.0

    def get_ajustes_mes(self, mes_actual: str) -> list:
        """Invoca RPC get_ajustes_mes_rpc"""
        url = f"{self.url}/rpc/get_ajustes_mes_rpc"
        try:
            res = self.session.post(url, json={"mes_actual": mes_actual}, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data if data is not None else []
            return []
        except requests.exceptions.RequestException:
            print(f"Error de conexión con Supabase en get_ajustes_mes: el servidor no responde")
            return []
        except Exception:
            return []
````
