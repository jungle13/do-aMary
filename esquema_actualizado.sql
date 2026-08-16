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