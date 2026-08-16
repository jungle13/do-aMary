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
