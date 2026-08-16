# Archivo para actualizar el esquema de la base de datos localmente

# 1. Vincular este directorio con tu proyecto remoto en Supabase
# NOTA: Este paso te pedirá que ingreses tu contraseña de la base de datos (Database Password)
npx supabase link --project-ref ffclvijngnaliiarmjpb

# 2. Descargar el esquema actualizado en formato SQL
npx supabase db dump --schema public > esquema_actualizado.sql

Write-Host "¡Esquema descargado exitosamente en esquema_actualizado.sql!"
