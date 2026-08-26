-- =========================================================================
-- MÓDULO DE CARTERA Y CUENTAS POR COBRAR - SISTEMA DOÑA MARY
-- Ejecuta este script en el SQL Editor de tu panel de Supabase
-- =========================================================================

-- 1. Tabla de Clientes
CREATE TABLE IF NOT EXISTS public.clientes (
    id_cliente UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT UNIQUE NOT NULL,
    tipo_cliente TEXT DEFAULT 'REGULAR', -- 'REGULAR', 'CLIENTES_VARIOS'
    telefono TEXT,
    direccion TEXT,
    email TEXT,
    limite_credito NUMERIC(14,2) DEFAULT 0,
    notas TEXT,
    fecha_creacion TIMESTAMPTZ DEFAULT timezone('America/Bogota'::text, now())
);

-- Insertar cliente predeterminado para ventas generales
INSERT INTO public.clientes (nombre, tipo_cliente)
VALUES ('CLIENTES VARIOS', 'CLIENTES_VARIOS')
ON CONFLICT (nombre) DO NOTHING;

-- 2. Asegurar columnas de cliente en registro_ventas (Sintaxis nativa segura)
ALTER TABLE public.registro_ventas ADD COLUMN IF NOT EXISTS cliente TEXT DEFAULT 'CLIENTES VARIOS';
ALTER TABLE public.registro_ventas ADD COLUMN IF NOT EXISTS id_cliente UUID REFERENCES public.clientes(id_cliente);

-- 3. Tabla de Pagos / Recaudos de Cartera (Cabecera)
CREATE TABLE IF NOT EXISTS public.pagos_cartera (
    id_pago UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_cliente UUID REFERENCES public.clientes(id_cliente) ON DELETE SET NULL,
    nombre_cliente TEXT NOT NULL,
    fecha_pago TIMESTAMPTZ DEFAULT timezone('America/Bogota'::text, now()),
    monto_total NUMERIC(14,2) NOT NULL CHECK (monto_total > 0),
    metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('EFECTIVO', 'TRANSFERENCIA')),
    banco_origen TEXT, -- 'Bancolombia', 'Nequi', 'Daviplata', 'Davivienda', 'BBVA', 'Banco de Bogotá', 'Dale', 'Otro'
    referencia_comprobante TEXT,
    observaciones TEXT,
    usuario_registro TEXT DEFAULT 'admin',
    estado_registro TEXT DEFAULT 'VÁLIDO' CHECK (estado_registro IN ('VÁLIDO', 'ANULADO')),
    created_at TIMESTAMPTZ DEFAULT timezone('America/Bogota'::text, now())
);

-- 4. Tabla de Detalle de Pagos Aplicados a Facturas
CREATE TABLE IF NOT EXISTS public.detalle_pagos_cartera (
    id_detalle UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_pago UUID REFERENCES public.pagos_cartera(id_pago) ON DELETE CASCADE,
    factura_no TEXT NOT NULL,
    monto_aplicado NUMERIC(14,2) NOT NULL CHECK (monto_aplicado > 0),
    saldo_anterior NUMERIC(14,2) DEFAULT 0,
    saldo_restante NUMERIC(14,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT timezone('America/Bogota'::text, now())
);

-- 5. Tabla de Plan de Cuotas y Fechas de Cobro
CREATE TABLE IF NOT EXISTS public.cuotas_cartera (
    id_cuota UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_cliente UUID REFERENCES public.clientes(id_cliente) ON DELETE CASCADE,
    nombre_cliente TEXT NOT NULL,
    numero_cuota INT NOT NULL,
    total_cuotas INT NOT NULL,
    monto_cuota NUMERIC(14,2) NOT NULL,
    fecha_cobro_sugerida DATE NOT NULL,
    estado TEXT DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'COBRADO', 'ANULADO')),
    observacion TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('America/Bogota'::text, now())
);

-- 6. Desactivar RLS para acceso fluido de la app
ALTER TABLE public.clientes DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.pagos_cartera DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.detalle_pagos_cartera DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.cuotas_cartera DISABLE ROW LEVEL SECURITY;

-- 7. Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_registro_ventas_cliente ON public.registro_ventas (cliente);
CREATE INDEX IF NOT EXISTS idx_registro_ventas_factura ON public.registro_ventas (factura_no);
CREATE INDEX IF NOT EXISTS idx_pagos_cartera_cliente ON public.pagos_cartera (nombre_cliente);
CREATE INDEX IF NOT EXISTS idx_detalle_pagos_factura ON public.detalle_pagos_cartera (factura_no);
CREATE INDEX IF NOT EXISTS idx_cuotas_cartera_cliente ON public.cuotas_cartera (id_cliente);
