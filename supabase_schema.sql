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
