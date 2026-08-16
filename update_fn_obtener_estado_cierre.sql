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
