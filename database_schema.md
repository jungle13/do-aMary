# Estructura y Reglas de la Base de Datos (Supabase)

## Restricciones y Reglas (Constraints & Keys)

| nombre_tabla                | nombre_regla                                      | definicion_exacta                                                                                                    |
| --------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| catalogo_insumos            | catalogo_insumos_codigo_key                       | UNIQUE (codigo_insumo)                                                                                               |
| catalogo_insumos            | catalogo_insumos_codigo_insumo_key                | UNIQUE (codigo_insumo)                                                                                               |
| catalogo_insumos            | catalogo_insumos_pkey                             | PRIMARY KEY (id_insumo)                                                                                              |
| registro_compras            | registro_compras_pkey                             | PRIMARY KEY (id_compra)                                                                                              |
| registro_compras            | fk_compras_codigo_insumo                          | FOREIGN KEY (codigo_insumo) REFERENCES catalogo_insumos(codigo_insumo)                                               |
| registro_ventas             | registro_ventas_pkey                              | PRIMARY KEY (id_venta)                                                                                               |
| registro_ventas             | fk_ventas_codigo_insumo                           | FOREIGN KEY (codigo_insumo) REFERENCES catalogo_insumos(codigo_insumo)                                               |
| conteo_fisico_relacionado   | conteo_fisico_relacionado_codigo_sugerido_fkey    | FOREIGN KEY (codigo_sugerido) REFERENCES catalogo_insumos(codigo_insumo)                                             |
| conteo_fisico_relacionado   | conteo_fisico_relacionado_pkey                    | PRIMARY KEY (id_conteo)                                                                                              |
| registro_auditorias_cierres | fk_auditorias_codigo_insumo                       | FOREIGN KEY (codigo_insumo) REFERENCES catalogo_insumos(codigo_insumo)                                               |
| registro_auditorias_cierres | registro_auditorias_cierres_tipo_registro_check   | CHECK ((tipo_registro = ANY (ARRAY['INVENTARIO_INICIAL'::text, 'CIERRE_MENSUAL'::text, 'AJUSTE_ESPORADICO'::text]))) |
| registro_auditorias_cierres | registro_auditorias_cierres_pkey                  | PRIMARY KEY (id_auditoria)                                                                                           |
| registro_auditorias_cierres | registro_auditorias_cierres_codigo_insumo_fkey    | FOREIGN KEY (codigo_insumo) REFERENCES catalogo_insumos(codigo_insumo)                                               |
| registro_ajustes_inventario | registro_ajustes_inventario_codigo_item_fkey      | FOREIGN KEY (codigo_insumo) REFERENCES catalogo_insumos(codigo_insumo)                                               |
| registro_ajustes_inventario | registro_ajustes_inventario_pkey                  | PRIMARY KEY (id_ajuste)                                                                                              |
| registro_ajustes_inventario | registro_ajustes_inventario_estado_registro_check | CHECK ((estado_registro = ANY (ARRAY['VÁLIDO'::text, 'ANULADO'::text])))                                             |
| registro_ajustes_inventario | fk_ajustes_codigo_insumo                          | FOREIGN KEY (codigo_insumo) REFERENCES catalogo_insumos(codigo_insumo)                                               |
| registro_ajustes_inventario | registro_ajustes_inventario_tipo_ajuste_check     | CHECK ((tipo_ajuste = ANY (ARRAY['ENTRADA_POR_SOBRANTE'::text, 'SALIDA_POR_FALTANTE'::text])))                       |

## Columnas y Tipos de Datos

| tabla                       | columna                  | tipo_dato                | permite_nulos | valor_por_defecto            |
| --------------------------- | ------------------------ | ------------------------ | ------------- | ---------------------------- |
| catalogo_insumos            | id_insumo                | uuid                     | NO            | gen_random_uuid()            |
| catalogo_insumos            | codigo_insumo            | text                     | YES           | null                         |
| catalogo_insumos            | nombre                   | text                     | YES           | null                         |
| catalogo_insumos            | descripcion              | text                     | YES           | null                         |
| catalogo_insumos            | categoria                | text                     | YES           | null                         |
| catalogo_insumos            | costo_unitario           | numeric                  | YES           | null                         |
| catalogo_insumos            | precio_venta             | numeric                  | YES           | null                         |
| catalogo_insumos            | stock_actual             | numeric                  | YES           | 0                            |
| catalogo_insumos            | stock_minimo             | numeric                  | YES           | 0                            |
| catalogo_insumos            | estado                   | boolean                  | YES           | true                         |
| catalogo_insumos            | zona                     | text                     | YES           | null                         |
| catalogo_insumos            | ubicacion                | text                     | YES           | null                         |
| catalogo_insumos            | tipo_unidad              | text                     | YES           | null                         |
| conteo_fisico_relacionado   | id_conteo                | uuid                     | NO            | gen_random_uuid()            |
| conteo_fisico_relacionado   | cod_insumo_fisico        | text                     | NO            | null                         |
| conteo_fisico_relacionado   | nombre_insumo_fisico     | text                     | NO            | null                         |
| conteo_fisico_relacionado   | codigo_sugerido          | text                     | YES           | null                         |
| conteo_fisico_relacionado   | nombre_sugerido          | text                     | YES           | null                         |
| conteo_fisico_relacionado   | categoria_sugerida       | text                     | YES           | null                         |
| conteo_fisico_relacionado   | zona                     | text                     | YES           | null                         |
| conteo_fisico_relacionado   | ubicacion                | text                     | YES           | null                         |
| conteo_fisico_relacionado   | tipo_unidad              | text                     | YES           | null                         |
| conteo_fisico_relacionado   | cantidad_fisica          | integer                  | NO            | null                         |
| conteo_fisico_relacionado   | fecha_registro           | timestamp with time zone | YES           | timezone('utc'::text, now()) |
| registro_ajustes_inventario | id_ajuste                | uuid                     | NO            | gen_random_uuid()            |
| registro_ajustes_inventario | fecha_ajuste             | timestamp with time zone | YES           | timezone('utc'::text, now()) |
| registro_ajustes_inventario | codigo_insumo            | text                     | YES           | null                         |
| registro_ajustes_inventario | tipo_ajuste              | text                     | YES           | null                         |
| registro_ajustes_inventario | cantidad                 | numeric                  | NO            | null                         |
| registro_ajustes_inventario | costo_unitario_congelado | numeric                  | NO            | null                         |
| registro_ajustes_inventario | costo_total_ajuste       | numeric                  | NO            | null                         |
| registro_ajustes_inventario | motivo_observacion       | text                     | YES           | null                         |
| registro_ajustes_inventario | estado_registro          | text                     | YES           | 'VÁLIDO'::text               |
| registro_auditorias_cierres | id_auditoria             | uuid                     | NO            | gen_random_uuid()            |
| registro_auditorias_cierres | fecha_cierre             | timestamp with time zone | YES           | timezone('utc'::text, now()) |
| registro_auditorias_cierres | codigo_insumo            | text                     | YES           | null                         |
| registro_auditorias_cierres | tipo_registro            | text                     | YES           | null                         |
| registro_auditorias_cierres | cantidad_sistema         | numeric                  | YES           | 0                            |
| registro_auditorias_cierres | cantidad_fisica          | numeric                  | NO            | null                         |
| registro_auditorias_cierres | diferencia               | numeric                  | YES           | null                         |
| registro_auditorias_cierres | observacion              | text                     | YES           | null                         |
| registro_auditorias_cierres | estado                   | text                     | YES           | 'APLICADO'::text             |
| registro_compras            | id_compra                | uuid                     | NO            | gen_random_uuid()            |
| registro_compras            | fecha                    | timestamp with time zone | YES           | now()                        |
| registro_compras            | descripcion              | text                     | YES           | null                         |
| registro_compras            | cantidad                 | numeric                  | YES           | null                         |
| registro_compras            | proveedor                | text                     | YES           | null                         |
| registro_compras            | estado_registro          | text                     | YES           | 'VÁLIDO'::text               |
| registro_compras            | codigo_insumo            | text                     | YES           | null                         |
| registro_compras            | numero_entrada           | text                     | YES           | null                         |
| registro_compras            | numero_factura           | text                     | YES           | null                         |
| registro_compras            | bodega                   | text                     | YES           | 'PRINCIPAL'::text            |
| registro_compras            | costo_unitario           | numeric                  | YES           | 0                            |
| registro_compras            | valor_iva                | numeric                  | YES           | 0                            |
| registro_compras            | costo_total              | numeric                  | YES           | 0                            |
| registro_ventas             | id_venta                 | uuid                     | NO            | gen_random_uuid()            |
| registro_ventas             | factura_no               | text                     | YES           | null                         |
| registro_ventas             | fecha                    | timestamp with time zone | YES           | now()                        |
| registro_ventas             | descripcion              | text                     | YES           | null                         |
| registro_ventas             | cantidad                 | numeric                  | YES           | null                         |
| registro_ventas             | subtotal                 | numeric                  | YES           | null                         |
| registro_ventas             | descuento                | numeric                  | YES           | null                         |
| registro_ventas             | iva                      | numeric                  | YES           | null                         |
| registro_ventas             | total                    | numeric                  | YES           | null                         |
| registro_ventas             | estado_registro          | text                     | YES           | 'VÁLIDO'::text               |
| registro_ventas             | codigo_insumo            | text                     | YES           | null                         |
| vista_inventario_completo   | codigo_insumo            | text                     | YES           | null                         |
| vista_inventario_completo   | nombre                   | text                     | YES           | null                         |
| vista_inventario_completo   | categoria                | text                     | YES           | null                         |
| vista_inventario_completo   | zona                     | text                     | YES           | null                         |
| vista_inventario_completo   | ubicacion                | text                     | YES           | null                         |
| vista_inventario_completo   | tipo_unidad              | text                     | YES           | null                         |
| vista_inventario_completo   | costo_unitario           | numeric                  | YES           | null                         |
| vista_inventario_completo   | precio_venta             | numeric                  | YES           | null                         |
| vista_inventario_completo   | stock_inicial            | numeric                  | YES           | null                         |
| vista_inventario_completo   | entradas                 | numeric                  | YES           | null                         |
| vista_inventario_completo   | salidas                  | numeric                  | YES           | null                         |
| vista_inventario_completo   | ajustes                  | numeric                  | YES           | null                         |
| vista_inventario_completo   | stock_actual             | numeric                  | YES           | null                         |
| vista_inventario_completo   | costo_total_insumo       | numeric                  | YES           | null                         |
| vista_inventario_completo   | venta_total_insumo       | numeric                  | YES           | null                         |
