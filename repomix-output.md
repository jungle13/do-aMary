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
cargas_compras_locales.json
cargas_locales.json
config.py
main.py
openapi.json
Sistema_Dona_Mary.spec
supabase_schema.sql
````

# Files

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

# Carpetas de dependencias y compilación
build/
dist/
node_modules/
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

## File: openapi.json
````json
{"code": "PGRST125", "details": null, "hint": null, "message": "Invalid path specified in request URL"}
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
                proveedor: str
                productos: list[ProductoCompra]
                
            prompt = """
            Extrae TODOS los datos de TODAS las facturas en esta página del reporte de entradas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
            NO extraigas la descripción del producto. Limítate a los datos solicitados.
            
            REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
            1. BLOQUES: Cada compra inicia en el extremo izquierdo con un código "EA-" (ej. EA-9273). Procesa TODOS los que encuentres.
            2. CABECERA DEL BLOQUE (Fecha, Factura y Proveedor): 
               En la misma línea que el "EA-" (o en la línea inmediatamente inferior):
               - La "fecha" suele estar a continuación del EA (conviértela a YYYY-MM-DD).
               - El "numero_factura" está precedido por la palabra "Factura No." o "Factura". Si no hay número, pon null.
               - El "proveedor" se encuentra AL LADO DERECHO de la palabra "Factura" o del número de factura. Extrae SOLO el nombre comercial (ej. "DISTRIBUCIONES PUNTO CHEVERE SAS", "AJOVER SAS"). 
               - REGLA ESTRICTA PARA PROVEEDOR: ESTÁ TOTALMENTE PROHIBIDO incluir explicaciones, razonamientos internos, notas de OCR o caracteres asiáticos en este campo. El valor debe ser ÚNICAMENTE el nombre de la empresa.
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
                "proveedor": "NOMBRE DEL PROVEEDOR SAS",
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

    def parse_ventas_pdf_page(self, pdf_path, page_index, tipo_documento="Remisión"):
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
            
            if tipo_documento == "Factura POS":
                prompt = """
                Extrae los datos de ventas formato POS de este documento y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
                Solo se requiere el numero de factura, codigo insumo, cantidad y precio unitario.
                NO extraigas fechas (el sistema las asignará), ni nombres de clientes.
                
                REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
                1. BLOQUES DE FACTURA: Cada factura inicia debajo de la palabra "TIPO NUMERO" con el prefijo "PP" seguido del número (ej. "PP 26396"). Extrae SOLO los números.
                2. PRODUCTOS: Debajo de "Clientes Varios", cada línea de producto tiene 3 valores separados por espacios. 
                   - "codigo_item": El primer número de la línea (ej. 2151).
                   - "cantidad": El segundo número (ej. 50.00).
                   - "precio_unitario": El tercer número (ej. 1900.00).
                3. CÁLCULOS OBLIGATORIOS PARA EL JSON:
                   - "subtotal": DEBES multiplicar la "cantidad" por el "precio_unitario".
                   - "iva": Siempre será 0.0 para este formato.
                   - "costo_total": Será exactamente igual al "subtotal".
                4. FORMATO NUMÉRICO: Todo valor monetario o cantidad debe ser número (float). Usa puntos (.) solo para decimales. NO uses comas.
                """
            else:
                prompt = """
                Extrae TODOS los datos de TODAS las páginas de este fragmento del reporte de facturas y devuelve EXCLUSIVAMENTE un arreglo JSON válido.
                NO extraigas el nombre del cliente ni la descripción del producto. Limítate a los datos numéricos y códigos.
                
                REGLAS DE EXTRACCIÓN (Ubicaciones espaciales obligatorias):
                1. BLOQUES: Cada bloque de venta inicia con "Fact.No." seguido del número de factura. Procesa TODOS los que encuentres.
                2. FECHA Y FACTURA: La "fecha" suele estar en la misma línea que el "Fact.No.". Extrae el número de factura.
                3. PRODUCTOS: Extrae cada línea de insumo hasta llegar a "Total Factura:".
                4. CAMPOS POR PRODUCTO:
                   - "codigo_item": Código al extremo izquierdo.
                   - "cantidad": Dato bajo la columna 'Cantidad'.
                   - "subtotal": Dato bajo la columna 'Subtotal'. NO HAGAS NINGÚN CÁLCULO.
                   - "iva": Dato bajo la columna 'IVA' (Si está vacía, pon 0.0).
                   - "costo_total": Dato bajo la columna 'Total'.
                5. FORMATO NUMÉRICO: Usa puntos (.) solo para decimales. NO uses comas (,).
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

## File: ui/views/ajustes_inventario.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient

class AjustesInventarioView(ft.Container):
    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
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
            if self.form_codigo.value:
                self.buscar_detalle_insumo(None)
            self.safe_update()

        def on_costo_change(e):
            try:
                nuevo_costo = float(self.form_costo.value.replace(',', '.') or 0)
                valor_inv = nuevo_costo * getattr(self, 'current_stock_modal', 0)
                self.lbl_valor_inv_modal.value = f"Valor del Inv: ${valor_inv:,.0f}"
            except ValueError:
                self.lbl_valor_inv_modal.value = "Valor del Inv: $0"
            self.safe_update()

        self.form_tipo_ajuste = ft.Dropdown(label="Tipo de Movimiento", options=[ft.dropdown.Option("ENTRADA"), ft.dropdown.Option("SALIDA")], dense=True, expand=True, border_radius=8, on_change=on_tipo_change)

        self.form_codigo = ft.TextField(label="Código Insumo", width=120, dense=True, border_radius=8, on_blur=self.buscar_detalle_insumo)
        self.form_nombre = ft.Text("Nombre del Insumo...", color="grey", italic=True, size=13)
        self.lbl_stock_actual = ft.Text("Stock Sist: 0", weight="bold", color=Config.COLOR_PRIMARY, size=12)

        self.form_motivo = ft.Dropdown(label="Motivo del Ajuste", dense=True, expand=True, border_radius=8)
        self.form_cant = ft.TextField(label="Cantidad", expand=True, dense=True, border_radius=8)

        # Eliminamos el expand=True para evitar el desbordamiento vertical en la columna
        self.form_costo = ft.TextField(label="Costo Unitario ($)", dense=True, border_radius=8, on_change=on_costo_change)
        self.lbl_valor_inv_modal = ft.Text("Valor del Inv: $0", size=11, color="grey")

        self.form_obs = ft.TextField(label="Observación (Opcional)", expand=True, dense=True, multiline=True, min_lines=2, border_radius=8)

        return ft.AlertDialog(
            title=ft.Text("Registrar Ajuste de Inventario"),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Row([
                        self.form_codigo, 
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.INVENTORY_2, size=16, color="grey"),
                                ft.Column([self.form_nombre, self.lbl_stock_actual], spacing=0, expand=True)
                            ]), 
                            expand=True, padding=10, bgcolor="#f5f5f5", border_radius=8
                        )
                    ]),
                    ft.Row([self.form_tipo_ajuste, self.form_motivo]),
                    ft.Row([
                        self.form_cant, 
                        ft.Column([self.form_costo, self.lbl_valor_inv_modal], expand=True, spacing=2)
                    ]),
                    ft.Row([self.form_obs])
                ], tight=True, spacing=15)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.cerrar_modal()),
                ft.ElevatedButton("Guardar Ajuste", bgcolor=Config.COLOR_PRIMARY, color="white", on_click=self.on_guardar_ajuste)
            ]
        )

    # --- Lógica de Negocio ---
    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

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
            self.current_stock_modal = float(detalle.get('stock_actual') or 0)
            self.lbl_stock_actual.value = f"Stock Sist: {self.current_stock_modal:g} unds"

            tipo = self.form_tipo_ajuste.value
            nuevo_costo = 0
            if tipo == "ENTRADA":
                nuevo_costo = float(detalle.get("costo_unitario") or 0)
                self.form_costo.value = str(nuevo_costo)
            elif tipo == "SALIDA":
                nuevo_costo = float(detalle.get("precio_venta") or 0)
                self.form_costo.value = str(nuevo_costo)
            else:
                nuevo_costo = float(detalle.get("costo_unitario") or 0)
                self.form_costo.value = str(nuevo_costo)

            valor_inv = nuevo_costo * self.current_stock_modal
            self.lbl_valor_inv_modal.value = f"Valor del Inv: ${valor_inv:,.0f}"
        else:
            self.form_nombre.value = "Insumo no encontrado."
            self.form_nombre.color = "red"
            self.current_stock_modal = 0
            self.lbl_stock_actual.value = "Stock Sist: 0"
            self.lbl_valor_inv_modal.value = "Valor del Inv: $0"
        self.safe_update()

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
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
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

        self.lbl_titulo = ft.Text("Módulo de Compras", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.content = ft.Column([
            self.progress_bar,
            self.lbl_titulo,
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
    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

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
                        ft.Text(f"EA: {ea} | Factura: {factura} | Proveedor: {proveedor} | Fecha: {fecha}", weight="bold", color=Config.COLOR_PRIMARY),
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
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
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
            self.lbl_titulo,
            
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

    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

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
        
        self.lbl_periodo_dash = ft.Text("Periodo: ...", size=13, weight="bold", color=Config.COLOR_PRIMARY)
        self.lbl_estado_dash = ft.Text("Estado: ...", size=13, weight="bold")
        self.lbl_fecha_hora = ft.Text("...", size=12, color="grey")

        badge_info = ft.Container(
            content=ft.Column([
                ft.Row([self.lbl_periodo_dash, ft.Text("|", color="grey", size=13), self.lbl_estado_dash], spacing=5),
                ft.Row([ft.Icon(ft.icons.ACCESS_TIME, size=14, color="grey"), self.lbl_fecha_hora], spacing=5)
            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor="white",
            border_radius=8,
            border=ft.border.all(1, "#e0e0e0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
        )

        header_row = ft.Row([
            ft.Column([
                ft.Text("Dashboard General", size=28, weight="bold", color=Config.COLOR_PRIMARY),
                ft.Text("Resumen ejecutivo del sistema", size=14, color="grey"),
            ], spacing=2),
            badge_info
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # Tarjetas de KPIs (Valores Iniciales) - SECCIÓN COSTOS
        self.val_inventario = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_compras = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_rotacion = ft.Text("N/D", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_compras_hoy = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        
        # SECCIÓN VENTAS
        self.val_ingresos = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_ventas_hoy = ft.Text("$ 0", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_rentabilidad = ft.Text("0.0%", size=14, weight="bold", color="#2ecca0")
        self.val_proyeccion_ventas = ft.Text("$ 0", size=14, weight="bold", color=Config.COLOR_PRIMARY)
        self.val_proyeccion_rentabilidad = ft.Text("0.0%", size=14, weight="bold", color="#2ecca0")
        
        self.kpi_costos_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Costo Inv. Actual", self.val_inventario, ft.icons.INVENTORY_2), col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(content=self._build_kpi_card("Total Compras (Mes)", self.val_compras, ft.icons.SHOPPING_BAG), col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(content=self._build_kpi_card("Compras (Hoy)", self.val_compras_hoy, ft.icons.MONEY_OFF), col={"xs": 12, "sm": 6, "md": 4}),
        ], spacing=10, run_spacing=10)

        self.kpi_ventas_row = ft.ResponsiveRow([
            ft.Container(content=self._build_kpi_card("Total Ventas (Mes)", self.val_ingresos, ft.icons.TRENDING_UP), col={"xs": 12, "sm": 6, "md": 6}),
            ft.Container(content=self._build_kpi_card("Ventas (Hoy)", self.val_ventas_hoy, ft.icons.ATTACH_MONEY), col={"xs": 12, "sm": 6, "md": 6}),
        ], spacing=10, run_spacing=10)
        
        # Paso 3: Crear la Barra de Métricas Secundarias
        self.kpi_secundarios = ft.Container(
            content=ft.Row([
                ft.Text("Métricas Secundarias:", weight="bold", color="grey", size=12),
                ft.Text("Rotación:", size=12, color="grey"), self.val_rotacion,
                ft.Text(" | Rentabilidad:", size=12, color="grey"), self.val_rentabilidad,
                ft.Text(" | Proy. Ventas:", size=12, color="grey"), self.val_proyeccion_ventas,
                ft.Text(" | Proy. Rentabilidad:", size=12, color="grey"), self.val_proyeccion_rentabilidad,
            ], spacing=5, wrap=True),
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            bgcolor="#f8f9fa", border_radius=8, border=ft.border.all(1, "#e0e0e0")
        )

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
                bgcolor="white",
                padding=15,
                border_radius=8,
                expand=True,
                border=ft.border.all(1, "#f0f0f0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
            ),
            # Panel Entrada
            ft.Container(
                content=ft.Column([
                    ft.Text("Ajustes de Entrada (+)", size=16, weight="bold", color="green"),
                    ft.Divider(height=1),
                    self.col_ajustes_entrada
                ]),
                bgcolor="white",
                padding=15,
                border_radius=8,
                expand=True,
                border=ft.border.all(1, "#f0f0f0"),
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=3, color=ft.colors.with_opacity(0.05, "black"))
            )
        ], spacing=15)

        # Ensamblaje del Layout
        self.seccion_kpis = ft.Column([
            ft.Text("Resumen Financiero y Operativo", size=20, weight="bold", color=Config.COLOR_PRIMARY),
            self.kpi_costos_row,
            self.kpi_ventas_row,
            self.kpi_secundarios
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
            self.seccion_kpis,
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
        # Cargar contexto temporal
        mes_actual = datetime.date.today().strftime("%Y-%m")
        datos_cierre = self.db.obtener_estado_cierre(mes_actual)
        estado_periodo = datos_cierre.get('periodo', {}).get('estado', 'ABIERTO') if datos_cierre and datos_cierre.get('periodo') else 'ABIERTO'

        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        partes = mes_actual.split('-')
        nombre_mes = f"{meses[int(partes[1]) - 1]} {partes[0]}"

        self.lbl_periodo_dash.value = f"Periodo: {nombre_mes}"
        self.lbl_estado_dash.value = f"Estado: {estado_periodo}"

        colores_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
        self.lbl_estado_dash.color = colores_estado.get(estado_periodo, 'black')

        ahora = datetime.datetime.now()
        self.lbl_fecha_hora.value = ahora.strftime("%d/%m/%Y - %I:%M %p")

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
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
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
        self.edit_margen = ft.Dropdown(
            width=100, 
            options=[ft.dropdown.Option(f"{p}%") for p in [10, 15, 20, 25, 30, 35]],
            **input_style
        )
        self.edit_precio = ft.TextField(width=120, **input_style)
        
        self.edit_categoria = ft.Dropdown(
            width=200, 
            **input_style
        )
        
        def calcular_precio(e):
            try:
                costo = float(self.edit_costo.value.replace(',', '.') or 0)
                if self.edit_margen.value:
                    margen_str = self.edit_margen.value.replace('%', '')
                    margen_dec = float(margen_str) / 100.0
                    if margen_dec < 1 and costo > 0:
                        # Fórmula financiera de margen sobre precio de venta
                        precio_calculado = costo / (1 - margen_dec)
                        self.edit_precio.value = f"{precio_calculado:.2f}"
            except ValueError:
                pass
            verificar_cambios_panel(e)

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

        self.edit_margen.on_change = calcular_precio
        self.edit_costo.on_change = calcular_precio
        self.edit_precio.on_change = verificar_cambios_panel
        self.edit_stock_minimo.on_change = verificar_cambios_panel
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
                        ft.Text("Ganancia", color="white70", size=11, weight="bold"),
                        self.edit_margen
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
        
        self.lbl_titulo = ft.Text("Catálogo de Insumos", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.content = ft.Column([
            self.progress_bar,
            self.lbl_titulo,
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
                    self.btn_columns,
                    self.btn_fullscreen
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
        
    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

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
        
        # Calcular Totales Globales iterando la lista completa sin paginación
        data_completa, _ = self.db.get_insumos(
            page=1, 
            page_size=999999, 
            search=search_val, 
            categoria=cat_val,
            fecha_corte=self.fecha_corte,
            sort_col=self.sort_col_name,
            sort_asc=self.sort_is_asc
        )

        proyeccion_global = 0.0
        self.valor_total_inventario = 0.0
        
        for insumo in data_completa:
            stock = float(insumo.get("stock_actual") or insumo.get("stock_real") or 0)
            p_venta = float(insumo.get("precio_venta") or 0)
            
            if stock > 0:
                proyeccion_global += (stock * p_venta)
                
            self.valor_total_inventario += float(insumo.get("costo_total_insumo") or 0)
            
        self.lbl_proyeccion_ventas.value = f"${proyeccion_global:,.0f}"
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
        
        # Recargar opciones frescas
        categorias_bd = self.db.get_categorias() if hasattr(self.db, 'get_categorias') else []
        opts = [ft.dropdown.Option(c) for c in categorias_bd if c]
        self.edit_categoria.options = opts

        # Limpiar dropdowns
        self.edit_margen.value = None

        # Asignar categoría exacta
        cat_val = str(item.get('categoria') or '').strip()
        if any(o.key == cat_val for o in opts):
            self.edit_categoria.value = cat_val
        elif opts:
            self.edit_categoria.value = opts[0].key
        else:
            self.edit_categoria.value = None
        
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
        
        # Extracción Segura
        stock_inicial = float(item.get("stock_inicial") or 0)
        valor_inicial = float(item.get("valor_inicial") or 0)
        compras = float(item.get("compras") or 0)
        valor_compras = float(item.get("valor_compras") or 0)
        ventas = float(item.get("ventas") or 0)
        valor_ventas = float(item.get("valor_ventas") or 0)
        ajustes_entrantes = float(item.get("ajustes_entrantes") or 0)
        valor_ajustes_entrantes = float(item.get("valor_ajustes_entrantes") or 0)
        ajustes_salientes = float(item.get("ajustes_salientes") or 0)
        valor_ajustes_salientes = float(item.get("valor_ajustes_salientes") or 0)
        neto_ajustes = float(item.get("neto_ajustes") or 0)
        valor_neto_ajustes = float(item.get("valor_neto_ajustes") or 0)
        
        stock_actual = float(item.get('stock_actual') or item.get('stock_real') or 0)
        costo_total_insumo = float(item.get('costo_total_insumo') or 0)
        costo_u = float(item.get('costo_unitario') or 0)
        p_venta = float(item.get('precio_venta') or 0)
        
        proyeccion_venta = stock_actual * p_venta if stock_actual > 0 else 0
        participacion = (costo_total_insumo / self.valor_total_inventario) * 100 if getattr(self, 'valor_total_inventario', 0) > 0 else 0
        
        # Badges
        badge_costo = ft.Container(content=ft.Text(f"Costo U: ${costo_u:,.0f}", size=11, weight="bold", color="black87"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="grey100", border_radius=15)
        badge_pventa = ft.Container(content=ft.Text(f"Precio de Venta: ${p_venta:,.0f}", size=11, weight="bold", color="black87"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="grey100", border_radius=15)
        badge_peso = ft.Container(content=ft.Text(f"Peso Inv: {participacion:.1f}%", size=11, weight="bold", color="purple900"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="#f3e5f5", border_radius=15)
        badge_proy = ft.Container(content=ft.Text(f"Proyección de Venta: ${proyeccion_venta:,.0f}", size=11, weight="bold", color="blue900"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="#e3f2fd", border_radius=15)
        badge_stock = ft.Container(content=ft.Text(f"Stock Actual: {stock_actual:g} unds ($ {costo_total_insumo:,.0f})", size=11, weight="bold", color="green900"), padding=ft.padding.symmetric(horizontal=8, vertical=4), bgcolor="#e8f5e9", border_radius=15)
        
        contenedor_badges = ft.Row(
            [badge_costo, badge_pventa, badge_peso, badge_proy, badge_stock], 
            spacing=5, 
            alignment=ft.MainAxisAlignment.END,
            wrap=True
        )
        
        def crear_bloque_metricas(titulo, cantidad, valor, color_cant, color_valor):
            return ft.Column([
                ft.Text(titulo, size=10, color="grey", weight="bold"),
                ft.Text(f"{cantidad:g} unds", size=12, weight="bold", color=color_cant),
                ft.Text(f"${valor:,.0f}", size=12, color=color_valor)
            ], spacing=2, alignment=ft.MainAxisAlignment.START)
            
        color_neto = "red" if valor_neto_ajustes < 0 else ("green" if valor_neto_ajustes > 0 else "grey")
            
        fila_resultados = ft.Row([
            crear_bloque_metricas("INICIAL", stock_inicial, valor_inicial, "grey", "grey"),
            crear_bloque_metricas("COMPRAS", compras, valor_compras, "#2ecca0", "black87"),
            crear_bloque_metricas("VENTAS", ventas, valor_ventas, "#42a5f5", "black87"),
            crear_bloque_metricas("AJUSTES ENTRANTES", ajustes_entrantes, valor_ajustes_entrantes, "green", "green"),
            crear_bloque_metricas("AJUSTES SALIENTES", ajustes_salientes, valor_ajustes_salientes, "red", "red"),
            crear_bloque_metricas("NETO DEL AJUSTE", neto_ajustes, valor_neto_ajustes, color_neto, color_neto)
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
                    ft.OutlinedButton(text="Editar Insumo", icon=ft.icons.EDIT, on_click=lambda e, i=item, r=row: self.abrir_edicion_desde_tarjeta(i, r))
                ]),
                fila_resultados
            ], spacing=8)
        )
        return tarjeta
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
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
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
        self.lbl_titulo = ft.Text("Registro de Ventas (Salidas)", size=24, weight="bold", color=Config.COLOR_PRIMARY)
        self.content = ft.Column([
            self.progress_bar,
            self.lbl_titulo,
            self.summary_container,
            self.tabs
        ], expand=True, spacing=10)

        # Llamar al método de renderizado en lugar del mock
        self._render_tabla_cargas()

    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)
        visibilidad = not self.is_fullscreen

        # Ocultar o mostrar elementos superiores si existen en la vista
        if hasattr(self, "lbl_titulo"): self.lbl_titulo.visible = visibilidad
        if hasattr(self, "summary_container"): self.summary_container.visible = visibilidad
        if hasattr(self, "kpi_bar"): self.kpi_bar.visible = visibilidad

        # Cambiar icono y tooltip
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        if hasattr(self, "safe_update"):
            self.safe_update()
        elif self.page:
            self.page.update()

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
            extracted = self.ai_parser.parse_ventas_pdf_page(data["archivo"], 0, data.get("tipo", "Remisión"))
            
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

## File: cargas_compras_locales.json
````json
{
    "2026-08-17": {
        "1": {
            "id": 1,
            "fecha": "2026-08-17",
            "pagina": 1,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-17_pag_1.pdf",
            "estado": "Procesado con éxito",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
                    "numero_entrada": "EA-9273",
                    "numero_factura": "7957448",
                    "proveedor": "AJOVER SAS塑造 Exact matches depend on exact header text, OCR has Factura No.7957448, let's check image closely: actually no number is on header, but OCR has it. Wait, rules say 'Si no hay, pon null'. Let's check image for EA-9273: 'Factura AJOVER SAS'. No number. So null."
                }
            ]
        },
        "2": {
            "id": 2,
            "fecha": "2026-08-17",
            "pagina": 2,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-17_pag_2.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "fecha": "2026-08-03",
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
                    ],
                    "proveedor": "Clientes Varios"
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
                    ],
                    "proveedor": "MEGA DISTRIBUCIONES AMERICA SAS"
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
                    ],
                    "proveedor": "Clientes Varios"
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
                    ],
                    "proveedor": "DISDECOL SAS"
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
                    ],
                    "proveedor": "FOAMTECK SAS"
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
                    ],
                    "proveedor": "ARIAS Y CIA SAS"
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
                    ],
                    "proveedor": "DISDECOL SAS"
                },
                {
                    "fecha": "2026-08-05",
                    "numero_entrada": "EA-9286",
                    "numero_factura": "15400",
                    "productos": [],
                    "proveedor": "BONNIPLAST SAS"
                }
            ]
        },
        "3": {
            "id": 3,
            "fecha": "2026-08-17",
            "pagina": 3,
            "archivo_original": "C:\\Users\\Home\\Downloads\\REPORTE ENTRADAS DE ALMACEN AGOSTO.pdf",
            "archivo": "pdfs_locales\\compra_2026-08-17_pag_3.pdf",
            "estado": "Nuevo"
        }
    }
}
````

## File: cargas_locales.json
````json
{
    "2026-08-17_Factura POS": {
        "1": {
            "id": 1,
            "pagina": 1,
            "tipo": "Factura POS",
            "fecha": "2026-08-17",
            "archivo": "pdfs_locales/ventas_2026-08-17_Factura_POS_Pag_1.pdf",
            "estado": "Guardado",
            "datos_extraidos": [
                {
                    "numero_factura": "26396",
                    "productos": [
                        {
                            "cantidad": 50,
                            "codigo_item": "2151",
                            "costo_total": 95000,
                            "iva": 0,
                            "subtotal": 95000
                        }
                    ]
                },
                {
                    "numero_factura": "26397",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0105",
                            "costo_total": 400,
                            "iva": 0,
                            "subtotal": 400
                        }
                    ]
                },
                {
                    "numero_factura": "26398",
                    "productos": [
                        {
                            "cantidad": 100,
                            "codigo_item": "0573",
                            "costo_total": 41500,
                            "iva": 0,
                            "subtotal": 41500
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0174",
                            "costo_total": 2100,
                            "iva": 0,
                            "subtotal": 2100
                        }
                    ]
                },
                {
                    "numero_factura": "26399",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0615",
                            "costo_total": 14600,
                            "iva": 0,
                            "subtotal": 14600
                        }
                    ]
                },
                {
                    "numero_factura": "26400",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "2333",
                            "costo_total": 3500,
                            "iva": 0,
                            "subtotal": 3500
                        }
                    ]
                },
                {
                    "numero_factura": "26401",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0022",
                            "costo_total": 2200,
                            "iva": 0,
                            "subtotal": 2200
                        }
                    ]
                },
                {
                    "numero_factura": "26402",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "2036",
                            "costo_total": 4000,
                            "iva": 0,
                            "subtotal": 4000
                        }
                    ]
                },
                {
                    "numero_factura": "26403",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0726",
                            "costo_total": 12500,
                            "iva": 0,
                            "subtotal": 12500
                        }
                    ]
                },
                {
                    "numero_factura": "26404",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0483",
                            "costo_total": 21900,
                            "iva": 0,
                            "subtotal": 21900
                        },
                        {
                            "cantidad": 20,
                            "codigo_item": "0108",
                            "costo_total": 17000,
                            "iva": 0,
                            "subtotal": 17000
                        }
                    ]
                },
                {
                    "numero_factura": "26405",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "0165",
                            "costo_total": 7800,
                            "iva": 0,
                            "subtotal": 7800
                        }
                    ]
                },
                {
                    "numero_factura": "26406",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "1591",
                            "costo_total": 4600,
                            "iva": 0,
                            "subtotal": 4600
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0024",
                            "costo_total": 8850,
                            "iva": 0,
                            "subtotal": 8850
                        },
                        {
                            "cantidad": 2,
                            "codigo_item": "0644",
                            "costo_total": 7600,
                            "iva": 0,
                            "subtotal": 7600
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1664",
                            "costo_total": 2600,
                            "iva": 0,
                            "subtotal": 2600
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0655",
                            "costo_total": 11200,
                            "iva": 0,
                            "subtotal": 11200
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "0178",
                            "costo_total": 2800,
                            "iva": 0,
                            "subtotal": 2800
                        },
                        {
                            "cantidad": 1,
                            "codigo_item": "1639",
                            "costo_total": 5600,
                            "iva": 0,
                            "subtotal": 5600
                        }
                    ]
                },
                {
                    "numero_factura": "26407",
                    "productos": [
                        {
                            "cantidad": 20,
                            "codigo_item": "0573",
                            "costo_total": 8800,
                            "iva": 0,
                            "subtotal": 8800
                        }
                    ]
                },
                {
                    "numero_factura": "26408",
                    "productos": [
                        {
                            "cantidad": 1,
                            "codigo_item": "1176",
                            "costo_total": 15900,
                            "iva": 0,
                            "subtotal": 15900
                        }
                    ]
                },
                {
                    "numero_factura": "26409",
                    "productos": [
                        {
                            "cantidad": 20,
                            "codigo_item": "0355",
                            "costo_total": 19600,
                            "iva": 0,
                            "subtotal": 19600
                        }
                    ]
                }
            ]
        },
        "2": {
            "id": 2,
            "pagina": 2,
            "tipo": "Factura POS",
            "fecha": "2026-08-17",
            "archivo": "pdfs_locales/ventas_2026-08-17_Factura_POS_Pag_2.pdf",
            "estado": "Nuevo"
        }
    }
}
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
        url += f"&order=fecha.desc,numero_entrada.desc&offset={offset}&limit={page_size}"
        
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
        url += f"&order=fecha.desc,factura_no.desc&offset={offset}&limit={page_size}"
        
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
            res = self.session.post(url, headers=self.headers, timeout=5)
            if res.status_code == 200:
                return res.json()
        except:
            pass
            
        # Fallback local para agrupar KPIs por categoría desde la vista principal
        try:
            url_vista = f"{self.url}/vista_inventario_completo?select=categoria,costo_total_insumo,valor_ventas"
            res_vista = self.session.get(url_vista, headers=self.headers, timeout=10)
            if res_vista.status_code == 200:
                data = res_vista.json()
                categorias = {}
                for item in data:
                    cat = item.get("categoria") or "SIN CATEGORIA"
                    if cat not in categorias:
                        categorias[cat] = {
                            "categoria": cat,
                            "costo_inventario": 0.0,
                            "ventas_totales": 0.0,
                            "rotacion": 0.0,
                            "rentabilidad": 0.0
                        }
                    categorias[cat]["costo_inventario"] += float(item.get("costo_total_insumo") or 0)
                    categorias[cat]["ventas_totales"] += float(item.get("valor_ventas") or 0)
                
                result = []
                for cat, vals in categorias.items():
                    costo_inv = vals["costo_inventario"]
                    vtas = vals["ventas_totales"]
                    if costo_inv > 0:
                        vals["rotacion"] = vtas / costo_inv
                    if vtas > 0:
                        vals["rentabilidad"] = 25.0 # Margen simulado 25% si hay ventas
                    result.append(vals)
                    
                result.sort(key=lambda x: x["ventas_totales"], reverse=True)
                return result
        except Exception as e:
            print(f"Error en get_kpis_por_categoria fallback: {e}")
            
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
        """Recupera el nombre, costo, precio y stock de un insumo específico para el autocompletado."""
        url = f"{self.url}/catalogo_insumos?codigo_insumo=eq.{codigo}&select=nombre,costo_unitario,precio_venta,stock_actual"
        try:
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200 and len(res.json()) > 0:
                return res.json()[0]
        except Exception:
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

    def aceptar_stock_sistema_masivo(self, ids_auditoria: list) -> dict:
        url = f"{self.url}/rpc/fn_aceptar_stock_sistema_masivo"
        try:
            res = self.session.post(url, json={"p_ids": ids_auditoria}, headers=self.headers, timeout=15)
            if res.status_code == 200: return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e: return {"exito": False, "error": str(e)}

    def eliminar_ajuste_cierre(self, id_auditoria: str) -> dict:
        url = f"{self.url}/rpc/fn_eliminar_ajuste_cierre"
        try:
            res = self.session.post(url, json={"p_id_auditoria": id_auditoria}, headers=self.headers, timeout=10)
            if res.status_code == 200: return res.json()
            return {"exito": False, "error": res.text}
        except Exception as e: return {"exito": False, "error": str(e)}
````

## File: ui/views/cierre_inventario.py
````python
import flet as ft
import threading
from config import Config
from core.supabase_client import SupabaseClient
import datetime
import math
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
        
        self.selected_items = set()
        self.filtro_busqueda = ""
        self.filtro_categoria = "Todas"
        self.filtro_estado = "Todos"
        
        # Filtros Visuales
        self.input_search = ft.TextField(hint_text="Buscar código o nombre...", prefix_icon=ft.icons.SEARCH, height=40, expand=True, on_change=self.on_filter_change)
        self.drop_categoria = ft.Dropdown(label="Categoría", options=[ft.dropdown.Option("Todas")], height=40, width=150, on_change=self.on_filter_change)
        self.drop_estado = ft.Dropdown(label="Estado", options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("PENDIENTE"), ft.dropdown.Option("AUDITADO"), ft.dropdown.Option("AJUSTADO")], value="Todos", height=40, width=150, on_change=self.on_filter_change)
        
        self.btn_masivo = ft.ElevatedButton("Aceptar Stock Seleccionado", icon=ft.icons.CHECK_BOX, bgcolor="green", color="white", on_click=self.abrir_modal_masivo)
        self.action_bar_masiva = ft.Row([self.btn_masivo], visible=False)
        
        # Mes Seleccionado por defecto (se actualiza al ver detalle)
        hoy = datetime.date.today()
        self.mes_seleccionado = hoy.strftime('%Y-%m')
        
        self.btn_iniciar_snapshot = ft.ElevatedButton(
            text='1. Generar Preliminar',
            icon=ft.icons.CAMERA_ALT,
            bgcolor=Config.COLOR_SECONDARY,
            color='white',
            on_click=self.on_generar_snapshot
        )
        
        self.btn_aprobar_cierre = ft.ElevatedButton(
            text='3. Aprobar Cierre',
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
            column_spacing=20,
            data_row_min_height=50,
            data_row_max_height=50,
            heading_row_color=ft.colors.with_opacity(0.05, Config.COLOR_PRIMARY),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, 'black')),
            border_radius=8,
            columns=[
                ft.DataColumn(ft.Checkbox(on_change=self.on_select_all_change)),
                ft.DataColumn(ft.Text('Código', weight='bold')),
                ft.DataColumn(ft.Text('Insumo', weight='bold')),
                ft.DataColumn(ft.Text('Inicial', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Entradas', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Salidas', weight='bold'), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text('Ajustes', weight='bold'), width=60), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text('Stock Actual', weight='bold'), width=80), numeric=True),
                ft.DataColumn(ft.Container(content=ft.Text('Físico', weight='bold'), width=80)),
                ft.DataColumn(ft.Text('Diferencia', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Costo Ajuste', weight='bold'), numeric=True),
                ft.DataColumn(ft.Text('Observación', weight='bold')),
                ft.DataColumn(ft.Text('Estado', weight='bold')),
                ft.DataColumn(ft.Text('Acción', weight='bold')),
            ],
            rows=[]
        )

        self.table_wrapper = ft.Container(content=ft.Row([ft.Column([self.data_table], scroll=ft.ScrollMode.ALWAYS, expand=True)], scroll=ft.ScrollMode.ALWAYS, expand=True), expand=True)
        self.card_list_view = ft.ListView(expand=True, spacing=10, visible=False)
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
        
        self.kpi_compacto = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Valor del Sistema:", weight="bold", color="grey"), self.lbl_valor_sistema,
                    ft.Text(" | Valor Físico Proyectado:", weight="bold", color="grey"), self.lbl_valor_fisico,
                ]),
                ft.Row([
                    ft.Text("Sobrantes (+):", weight="bold", color="grey"), self.lbl_ajustes_entrada,
                    ft.Text(" | Faltantes (-):", weight="bold", color="grey"), self.lbl_ajustes_salida,
                    ft.Text(" | Neto Ajustes:", weight="bold", color="grey"), self.lbl_neto_ajustes,
                ])
            ], spacing=2),
            bgcolor="#f8f9fa", padding=10, border_radius=8, border=ft.border.all(1, "#e0e0e0")
        )

        # Controles vista_lista (Maestro)
        self.dt_periodos = ft.DataTable(
            column_spacing=20,
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
            ft.Container(
                content=ft.Column([self.dt_periodos], scroll=ft.ScrollMode.ALWAYS, expand=True),
                expand=True
            )
        ], visible=True, expand=True)

        # Controles vista_detalle (Detalle)
        self.view_mode = "table"
        self.btn_toggle_view = ft.IconButton(icon=ft.icons.GRID_VIEW, tooltip="Cambiar a Tarjetas", on_click=self.toggle_view)
        
        self.is_fullscreen = False
        self.btn_fullscreen = ft.IconButton(
            icon=ft.icons.FULLSCREEN,
            tooltip="Expandir Tabla (Modo Enfoque)",
            on_click=self.toggle_fullscreen
        )
        
        self.filtro_container = ft.Container(
            content=ft.Row([self.input_search, self.drop_categoria, self.drop_estado, self.btn_toggle_view, self.btn_fullscreen]),
            bgcolor="white", padding=10, border_radius=8,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black"))
        )
        self.btn_volver = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=self.on_volver_lista)
        self.lbl_titulo_detalle = ft.Text('Auditoría: ...', size=24, weight='bold', color=Config.COLOR_PRIMARY)
        
        self.btn_aceptar_stock_masivo = ft.ElevatedButton("Aceptar Stock de Cierre", bgcolor="green", color="white", on_click=self.abrir_modal_masivo)
        
        self.row_pasos_cierre = ft.ResponsiveRow([
            self._crear_tarjeta_paso(1, "Generar Preliminar", "Congela el stock actual para compararlo con el físico.", self.btn_iniciar_snapshot),
            self._crear_tarjeta_paso(2, "Ajustar y Aceptar", "Ingresa ajustes o acepta el stock del sistema.", self.btn_aceptar_stock_masivo),
            self._crear_tarjeta_paso(3, "Aprobar Cierre", "Consolida ajustes y finaliza el mes.", self.btn_aprobar_cierre)
        ], spacing=15)
        
        self.row_filtros = self.filtro_container
        
        self.header_row = ft.Row([
            self.btn_volver, 
            self.lbl_titulo_detalle, 
            ft.Container(expand=True), 
            self.txt_estado_periodo, 
            self.txt_progreso
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        self.vista_detalle = ft.Column([
            self.header_row,
            self.row_pasos_cierre,
            self.kpi_compacto,
            self.row_filtros,
            self.table_wrapper,
            self.card_list_view,
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


    def _crear_tarjeta_paso(self, numero, titulo, descripcion, control_accion):
        return ft.Container(
            col={"xs": 12, "md": 4},
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(str(numero), color="white", weight="bold", size=12), bgcolor=Config.COLOR_PRIMARY, width=22, height=22, border_radius=11, alignment=ft.alignment.center),
                    ft.Text(titulo, weight="bold", size=14, color=Config.COLOR_PRIMARY)
                ]),
                ft.Text(descripcion, size=11, color="grey"),
                ft.Container(content=control_accion, alignment=ft.alignment.center_right)
            ], spacing=5),
            bgcolor="white", padding=12, border_radius=10,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "black"))
        )


    def safe_update(self):
        """Actualiza la UI solo si el control sigue montado en la página."""
        try:
            if self.page and self.uid:
                self.page.update()
        except Exception:
            pass

    def mostrar_alerta(self, msj, color="red"):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msj, color="white"), bgcolor=color)
            self.page.snack_bar.open = True
            self.safe_update()

    def did_mount(self):
        if self.modal_ajuste not in self.page.overlay:
            self.page.overlay.append(self.modal_ajuste)
        self.load_lista_periodos()


    # --- Nuevos Métodos de Filtro y Selección ---
    def on_filter_change(self, e):
        self.filtro_busqueda = self.input_search.value or ""
        self.filtro_categoria = self.drop_categoria.value or "Todas"
        self.filtro_estado = self.drop_estado.value or "Todos"
        self.current_page = 1
        self.render_view()
        self.safe_update()

    def actualizar_boton_masivo(self):
        cantidad = len(self.selected_items)
        if cantidad > 0:
            self.btn_aceptar_stock_masivo.text = f"Aceptar Stock Seleccionado ({cantidad})"
        else:
            self.btn_aceptar_stock_masivo.text = "Aceptar Stock de Cierre"
        self.safe_update()

    def on_select_all_change(self, e):
        is_checked = e.control.value
        estado_periodo = self.datos_cierre.get('estado', '')
        if is_checked:
            for item in self.insumos_lista:
                if estado_periodo != 'CERRADO' and item.get('estado') != 'APROBADO':
                    self.selected_items.add(item.get('id_auditoria'))
        else:
            self.selected_items.clear()
        self.actualizar_boton_masivo()
        self.render_view()
        self.safe_update()

    def on_item_select(self, e, id_auditoria):
        if e.control.value:
            self.selected_items.add(id_auditoria)
        else:
            self.selected_items.discard(id_auditoria)
        self.actualizar_boton_masivo()
        self.safe_update()

    def abrir_modal_masivo(self, e):
        ids_a_procesar = []
        is_global = False
        if len(self.selected_items) > 0:
            ids_a_procesar = list(self.selected_items)
            mensaje_principal = f"¿Deseas aceptar el stock del sistema para los {len(ids_a_procesar)} insumos seleccionados?"
        else:
            ids_a_procesar = [i['id_auditoria'] for i in self.insumos_lista if i.get('estado') == 'PENDIENTE']
            if not ids_a_procesar:
                self.mostrar_alerta("No hay insumos PENDIENTES para aceptar globalmente.", "orange")
                return
            is_global = True
            mensaje_principal = f"¿Deseas aceptar globalmente el stock para TODOS los {len(ids_a_procesar)} insumos pendientes?"
            
        try:
            val_sist = self.lbl_valor_sistema.value
            val_ent = self.lbl_ajustes_entrada.value
            val_sal = self.lbl_ajustes_salida.value
            val_neto = self.lbl_neto_ajustes.value
            val_proy = self.lbl_valor_fisico.value
        except:
            val_sist, val_ent, val_sal, val_neto, val_proy = "$0", "$0", "$0", "$0", "$0"
                
        def confirm_masivo(e):
            dialog.open = False
            self.safe_update()
            
            if hasattr(self, 'progress_bar'): self.progress_bar.visible = True
            self.safe_update()
            
            res = self.db.aceptar_stock_sistema_masivo(ids_a_procesar)
            if res.get("exito"):
                self.mostrar_alerta("Aceptación masiva completada con éxito.", "green")
                self.selected_items.clear()
                self.actualizar_boton_masivo()
                self.mostrar_detalle(self.mes_seleccionado) # Reload
            else:
                self.mostrar_alerta(f"Error masivo: {res.get('error')}", "red")
                if hasattr(self, 'progress_bar'): self.progress_bar.visible = False
                self.safe_update()

        resumen_ui = ft.Column([
            ft.Text(mensaje_principal, weight="bold", color="red" if is_global else "black"),
            ft.Text("Esto significa que declaras que la cantidad física coincide exactamente con la del sistema (Ajuste de $0).", size=11, color="grey"),
            ft.Divider(height=10),
            ft.Text("Estado Global de la Auditoría:", size=12, weight="bold", color=Config.COLOR_PRIMARY),
            ft.Row([ft.Text("Valor del Sistema:", size=12), ft.Text(val_sist, size=12, weight="bold")]),
            ft.Row([ft.Text("Sobrantes Registrados:", size=12), ft.Text(val_ent, size=12, weight="bold", color="green")]),
            ft.Row([ft.Text("Faltantes Registrados:", size=12), ft.Text(val_sal, size=12, weight="bold", color="red")]),
            ft.Row([ft.Text("Impacto Neto Acumulado:", size=12), ft.Text(val_neto, size=12, weight="bold")]),
            ft.Row([ft.Text("Valor Físico Proyectado Final:", size=12), ft.Text(val_proy, size=13, weight="bold", color="blue")], spacing=5)
        ], spacing=5, tight=True)

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmación Global" if is_global else "Confirmación Masiva"),
            content=ft.Container(width=450, content=resumen_ui),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or self.safe_update()),
                ft.ElevatedButton("Confirmar y Aceptar", bgcolor="green", color="white", on_click=confirm_masivo)
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.safe_update()


    def procesar_eliminar_ajuste(self, id_auditoria):
        def confirm_eliminar(e):
            dialog.open = False
            self.safe_update()
            
            if hasattr(self, 'progress_bar'): self.progress_bar.visible = True
            self.safe_update()
            
            res = self.db.eliminar_ajuste_cierre(id_auditoria)
            if res.get("exito"):
                self.mostrar_alerta("Ajuste eliminado correctamente.", "green")
                self.mostrar_detalle(self.mes_seleccionado) # Reload
            else:
                self.mostrar_alerta(f"Error al eliminar: {res.get('error')}", "red")
                if hasattr(self, 'progress_bar'): self.progress_bar.visible = False
                self.safe_update()

        dialog = ft.AlertDialog(
            title=ft.Text("Eliminar Ajuste"),
            content=ft.Text("¿Estás seguro de eliminar este ajuste? El insumo volverá a PENDIENTE."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or self.safe_update()),
                ft.ElevatedButton("Eliminar", bgcolor="red", color="white", on_click=confirm_eliminar)
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.safe_update()

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
        
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        partes = mes.split('-')
        nombre_mes = meses[int(partes[1]) - 1]
        self.lbl_titulo_detalle.value = f"Auditoría: {nombre_mes} {partes[0]}"
        
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
            self.btn_aceptar_stock_masivo.disabled = True
            self.btn_aprobar_cierre.disabled = True
            self.btn_aprobar_cierre.bgcolor = "grey"
            if self.page:
                self.page.update()
            return

        self.txt_estado_periodo.value = f'Estado: {estado_periodo} | '
        color_estado = {'ABIERTO': 'green', 'PRELIMINAR': 'orange', 'EN_AUDITORIA': 'blue', 'CERRADO': 'red'}
        self.txt_estado_periodo.color = color_estado.get(estado_periodo, 'black')
        
        pendientes = resumen.get('pendientes', 0)
        listos = resumen.get('auditados', 0) + resumen.get('ajustados', 0)
        self.txt_progreso.value = f'Pendientes: {pendientes} | Listos: {listos}'

        if estado_periodo == "CERRADO":
            self.btn_aceptar_stock_masivo.disabled = True
            self.btn_aprobar_cierre.text = "3. Cierre Exitoso"
            self.btn_aprobar_cierre.icon = ft.icons.VERIFIED
            self.btn_aprobar_cierre.disabled = True
            self.btn_aprobar_cierre.bgcolor = "green900"
        elif estado_periodo == "ABIERTO":
            self.btn_aceptar_stock_masivo.disabled = True
            self.btn_aprobar_cierre.text = "3. Aprobar Cierre"
            self.btn_aprobar_cierre.icon = ft.icons.CHECK_CIRCLE
            self.btn_aprobar_cierre.disabled = True
            self.btn_aprobar_cierre.bgcolor = "grey"
        else:
            # PRELIMINAR o EN_AUDITORIA
            self.btn_aceptar_stock_masivo.disabled = False
            self.btn_aprobar_cierre.text = "3. Aprobar Cierre"
            self.btn_aprobar_cierre.icon = ft.icons.CHECK_CIRCLE
            self.btn_aprobar_cierre.disabled = (pendientes > 0)
            self.btn_aprobar_cierre.bgcolor = "grey" if pendientes > 0 else "green" 

        # Update category options
        categorias = set([item.get('categoria', 'Sin Categoría') for item in self.insumos_lista])
        opciones_cat = [ft.dropdown.Option("Todas")] + [ft.dropdown.Option(cat) for cat in sorted(list(categorias))]
        self.drop_categoria.options = opciones_cat

        # Apply filters
        filtered_data = []
        q = self.filtro_busqueda.lower()
        for item in self.insumos_lista:
            if q and q not in str(item.get('codigo_insumo','')).lower() and q not in str(item.get('nombre','')).lower():
                continue
            if self.filtro_categoria != "Todas" and item.get('categoria') != self.filtro_categoria:
                continue
            if self.filtro_estado != "Todos" and item.get('estado') != self.filtro_estado:
                continue
            filtered_data.append(item)

        # KPIs Financieros sobre datos filtrados o sobre todos? Sobre TODOS (insumos_lista)
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

        # Paginacion sobre filtered_data
        total_filtered = len(filtered_data)
        self.total_pages = math.ceil(total_filtered / self.page_size) if total_filtered > 0 else 1
        
        if self.current_page > self.total_pages and self.total_pages > 0:
            self.current_page = self.total_pages

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_data = filtered_data[start_idx:end_idx]

        self.card_list_view.controls.clear()
        for insumo in page_data:
            self.data_table.rows.append(self.crear_fila_auditoria(insumo, estado_periodo))
            self.card_list_view.controls.append(self._crear_tarjeta_auditoria(insumo, estado_periodo))

        self.lbl_page_info.value = f'Página {self.current_page} de {self.total_pages}'
        self.btn_prev.disabled = (self.current_page <= 1)
        self.btn_next.disabled = (self.current_page >= self.total_pages)
        
        self.actualizar_boton_masivo()

        if self.page:
            self.page.update()



    def toggle_fullscreen(self, e):
        self.is_fullscreen = not getattr(self, "is_fullscreen", False)

        # Ocultar o mostrar las secciones superiores
        visibilidad = not self.is_fullscreen
        if hasattr(self, "header_row"): self.header_row.visible = visibilidad
        if hasattr(self, "row_pasos_cierre"): self.row_pasos_cierre.visible = visibilidad
        if hasattr(self, "kpi_compacto"): self.kpi_compacto.visible = visibilidad

        # Cambiar el icono y el tooltip del botón
        self.btn_fullscreen.icon = ft.icons.FULLSCREEN_EXIT if self.is_fullscreen else ft.icons.FULLSCREEN
        self.btn_fullscreen.tooltip = "Contraer Vista" if self.is_fullscreen else "Expandir Tabla (Modo Enfoque)"

        self.safe_update()

    def toggle_view(self, e):
        if self.view_mode == "table":
            self.view_mode = "cards"
            self.table_wrapper.visible = False
            self.card_list_view.visible = True
            self.btn_toggle_view.icon = ft.icons.TABLE_ROWS
            self.btn_toggle_view.tooltip = "Cambiar a Tabla"
        else:
            self.view_mode = "table"
            self.table_wrapper.visible = True
            self.card_list_view.visible = False
            self.btn_toggle_view.icon = ft.icons.GRID_VIEW
            self.btn_toggle_view.tooltip = "Cambiar a Tarjetas"
        self.safe_update()

    def _crear_tarjeta_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo.get('id_auditoria')
        estado_insumo = insumo.get('estado', 'PENDIENTE')
        observacion = insumo.get('observacion') or ''
        cant_sistema = insumo.get('cantidad_sistema')
        cant_fisica = insumo.get('cantidad_fisica')
        diferencia = insumo.get('diferencia')
        
        stock_inicial = insumo.get('stock_inicial', 0)
        entradas = insumo.get('entradas', 0)
        salidas = insumo.get('salidas', 0)
        ajustes = insumo.get('ajustes', 0)
        stock_actual = insumo.get('stock_actual', 0)
        
        habilitar_txt_ajuste = estado_periodo == "PRELIMINAR" and estado_insumo != "APROBADO"
        
        check_row = ft.Checkbox(
            value=id_auditoria in self.selected_items,
            disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO'),
            on_change=lambda e: self.on_item_select(e, id_auditoria)
        )
        
        def on_txt_conteo_change(e):
            try:
                if e.control.value.strip() == "":
                    btn_ajuste.disabled = True
                else:
                    val = float(e.control.value.replace(',', '.'))
                    btn_ajuste.disabled = (val == cant_sistema)
            except ValueError:
                btn_ajuste.disabled = True
            self.safe_update()

        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else '',
            dense=True, width=80, text_size=13, content_padding=10, label="Conteo",
            disabled=not habilitar_txt_ajuste,
            on_change=on_txt_conteo_change
        )
        
        colores_estado = {"PENDIENTE": "grey", "AUDITADO": "green", "AJUSTADO": "orange", "APROBADO": "blue"}
        color_badge = colores_estado.get(estado_insumo, "black")
        badge_estado = ft.Container(
            content=ft.Text(estado_insumo, size=10, weight="bold", color="white"),
            bgcolor=color_badge, padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=10
        )
        
        txt_obs = ft.Container(
            content=ft.Text(f"Obs: {observacion}" if observacion else "Sin observaciones", size=11, color="grey", italic=True, no_wrap=True, tooltip=observacion),
            expand=True, padding=ft.padding.only(left=10)
        )
        
        botones_accion = []
        if estado_insumo == "PENDIENTE":
            botones_accion.append(ft.ElevatedButton("Aceptar", icon=ft.icons.CHECK, bgcolor="green50", color="green900", on_click=lambda e, i_id=id_auditoria: self.procesar_aceptar_sistema(i_id), scale=0.85, disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO')))
            btn_ajuste_pendiente = ft.OutlinedButton("Ingresar Ajuste", icon=ft.icons.TUNE, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=True)
            botones_accion.append(btn_ajuste_pendiente)
            if txt_conteo.value:
                try:
                    if float(txt_conteo.value.replace(',', '.')) != cant_sistema:
                        btn_ajuste_pendiente.disabled = False
                except ValueError:
                    pass
            # Update the original btn_ajuste reference used by on_txt_conteo_change closure
            btn_ajuste = btn_ajuste_pendiente
        elif estado_insumo == "AUDITADO":
            btn_ajuste = ft.OutlinedButton("Editar Ajuste", icon=ft.icons.EDIT, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=(estado_periodo == 'CERRADO'))
            botones_accion.append(btn_ajuste)
            btn_ajuste.disabled = False if txt_conteo.value else True
        elif estado_insumo == "AJUSTADO":
            btn_ajuste = ft.OutlinedButton("Editar Ajuste", icon=ft.icons.EDIT, on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value), scale=0.85, disabled=(estado_periodo == 'CERRADO'))
            botones_accion.append(btn_ajuste)
            botones_accion.append(ft.OutlinedButton("Eliminar Ajuste", icon=ft.icons.DELETE, icon_color="red", style=ft.ButtonStyle(color="red"), on_click=lambda e, i_id=id_auditoria: self.procesar_eliminar_ajuste(i_id), scale=0.85, disabled=(estado_periodo == 'CERRADO')))
            btn_ajuste.disabled = False if txt_conteo.value else True
        else:
            # Fallback (e.g., APROBADO) - disabled buttons or none
            btn_ajuste = ft.OutlinedButton("Bloqueado", disabled=True, scale=0.85)
            botones_accion.append(btn_ajuste)

        cant_final = float(insumo.get("cantidad_fisica") if insumo.get("cantidad_fisica") is not None else insumo.get("cantidad_sistema", 0))
        costo_u = float(insumo.get("costo_unitario_snapshot") or 0)
        valor_total = cant_final * costo_u

        column_controls = [
            ft.Row([check_row, ft.Text(insumo.get('codigo_insumo', ''), weight="bold", color=Config.COLOR_PRIMARY), ft.Text(insumo.get('nombre', ''), expand=True, weight="bold")], alignment=ft.MainAxisAlignment.START),
            ft.Row([
                ft.Text(f"Inicial: {stock_inicial}", size=12),
                ft.Text(f"Entradas: {entradas}", size=12, color="green"),
                ft.Text(f"Salidas: {salidas}", size=12, color="red"),
                ft.Text(f"Ajustes: {ajustes}", size=12, color="orange"),
                ft.Text(f"Stock Sist: {stock_actual}", size=12, weight="bold", color="blue"),
            ], wrap=True),
            ft.Divider(height=1, color="#f0f0f0")
        ]

        if estado_periodo == "CERRADO":
            for btn in botones_accion:
                btn.disabled = True
            check_row.disabled = True
            
            label_cierre = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.LOCK, size=16, color="green900"),
                    ft.Text(f"Stock Cierre: {cant_final:g} unds", size=14, weight="bold", color="green900"),
                    ft.Text(f" | Costo Total: ${valor_total:,.2f}", size=14, weight="bold", color="green900")
                ]),
                bgcolor="#e8f5e9", padding=10, border_radius=8, margin=ft.padding.only(bottom=10, top=5)
            )
            column_controls.append(label_cierre)

        column_controls.append(
            ft.Row([
                txt_conteo,
                badge_estado,
                txt_obs,
                *botones_accion
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        return ft.Container(
            content=ft.Column(column_controls),
            bgcolor="#f8f9fa", padding=15, border_radius=8,
            border=ft.border.all(1, "#e9ecef")
        )

    def crear_fila_auditoria(self, insumo, estado_periodo):
        id_auditoria = insumo.get('id_auditoria')
        estado_insumo = insumo.get('estado', 'PENDIENTE')
        observacion = insumo.get('observacion') or ''
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
        
        def on_txt_conteo_change(e):
            try:
                if e.control.value.strip() == "":
                    btn_ajuste.disabled = True
                else:
                    val = float(e.control.value.replace(',', '.'))
                    btn_ajuste.disabled = (val == cant_sistema)
            except ValueError:
                btn_ajuste.disabled = True
            self.safe_update()

        txt_conteo = ft.TextField(
            value=str(cant_fisica) if cant_fisica is not None else '',
            dense=True, width=80, text_size=13, content_padding=10,
            disabled=not habilitar_txt_ajuste,
            on_change=on_txt_conteo_change
        )

        check_row = ft.Checkbox(
            value=id_auditoria in self.selected_items,
            disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO'),
            on_change=lambda e: self.on_item_select(e, id_auditoria)
        )

        if estado_insumo == "AJUSTADO":
            btn_ajuste = ft.ElevatedButton(
                'Editar Ajuste',
                icon=ft.icons.EDIT,
                on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value),
                scale=0.85,
                disabled=(estado_periodo == 'CERRADO')
            )
            btn_eliminar = ft.IconButton(
                icon=ft.icons.DELETE,
                icon_color="red",
                on_click=lambda e, i_id=id_auditoria: self.procesar_eliminar_ajuste(i_id),
                scale=0.85,
                disabled=(estado_periodo == 'CERRADO')
            )
            acciones = ft.Row([btn_ajuste, btn_eliminar], spacing=2)
            
            # Initial validation hack
            btn_ajuste.disabled = False if txt_conteo.value else True
            
        else:
            btn_aceptar_sistema = ft.ElevatedButton(
                text="Aceptar",
                icon=ft.icons.CHECK,
                bgcolor="green50",
                color="green900",
                on_click=lambda e, i_id=id_auditoria: self.procesar_aceptar_sistema(i_id),
                scale=0.85,
                disabled=(estado_periodo == 'CERRADO' or estado_insumo == 'APROBADO')
            )
            btn_ajuste = ft.ElevatedButton(
                'Ingresar Ajuste',
                icon=ft.icons.TUNE,
                on_click=lambda e, i=insumo, tc=txt_conteo: self.abrir_modal_ajuste_cierre(i, tc.value),
                scale=0.85,
                disabled=True
            )
            acciones = ft.Row([btn_aceptar_sistema, btn_ajuste], spacing=2)
            
            # Trigger validation manually on start if value is pre-filled
            if txt_conteo.value:
                try:
                    if float(txt_conteo.value.replace(',', '.')) != cant_sistema:
                        btn_ajuste.disabled = False
                except ValueError:
                    pass

        return ft.DataRow(
            cells=[
                ft.DataCell(check_row),
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
