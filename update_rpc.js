const { Client } = require('pg');

const client = new Client({
    connectionString: 'postgresql://postgres.do-amary:FsKQonYRTPZzYRbg@aws-0-us-east-2.pooler.supabase.com:6543/postgres'
});

const sql = `
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
                'costo_unitario_snapshot', COALESCE(rac.costo_unitario_snapshot, ci.costo_unitario, 0),
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
$function$;
`;

async function updateDB() {
    try {
        await client.connect();
        await client.query(sql);
        console.log("Database updated successfully.");
    } catch (err) {
        console.error("Error updating database:", err);
    } finally {
        await client.end();
    }
}

updateDB();
