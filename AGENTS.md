# AGENTS.md — Inventario App (Flet + Supabase)

> Archivo de contexto para el agente Gemini en Antigravity IDE.
> Léelo completamente antes de planificar o escribir cualquier código.

---

## 1. Visión General del Proyecto

Aplicación de escritorio de **gestión de inventario** construida con:

- **UI**: [Flet](https://flet.dev/) (Python — framework Flutter para desktop)
- **Base de datos**: [Supabase](https://supabase.com/) (PostgreSQL en la nube, acceso vía cliente Python)
- **Lenguaje**: Python 3.11+
- **IDE / Agente**: Google Antigravity con Gemini 3.1 Pro

El proyecto está en fase **mediana con varios módulos activos**. Antes de crear o modificar cualquier archivo, el agente DEBE explorar la estructura existente del proyecto.

---

## 2. Estructura de Directorios

```
inventario-app/
├── AGENTS.md                  ← este archivo
├── main.py                    ← punto de entrada, inicializa Flet app
├── config.py                  ← variables de configuración y entorno
├── .env                       ← variables de entorno (NO modificar, NO leer en código)
├── requirements.txt
│
├── core/                      ← núcleo de lógica y conexión a datos
│   ├── supabase_client.py     ← instancia y métodos de Supabase
│   ├── gemini_parser.py       ← IA para extracción de facturas y PDFs
│   └── excel_manager.py       ← utilidades para manejo de Excel
│
├── ui/                        ← vistas y componentes Flet
│   ├── layout/
│   │   └── sidebar.py         ← barra lateral principal
│   └── views/                 ← páginas completas de Flet
│       ├── inventario.py
│       ├── compras.py
│       ├── ventas.py
│       ├── ajustes_inventario.py
│       ├── cierre_inventario.py
│       ├── conteo_inicial.py
│       └── dashboard.py
```

> ⚠️ Si la estructura real del proyecto difiere, respeta lo que existe. Esta es la estructura objetivo, no una orden de recrearla.

---

## 3. Estándares de Código Python

### 3.1 Reglas generales

- Python **3.11+**. Usar f-strings, type hints en todas las funciones y métodos.
- Seguir **PEP 8**: nombres en `snake_case` para variables/funciones, `PascalCase` para clases.
- Máximo **80 caracteres por línea** en lógica, 120 en comentarios o docstrings.
- Cada módulo debe tener un docstring breve al inicio explicando su propósito.
- No usar `print()` para debug — usar `logging` del módulo estándar.

### 3.2 Imports

```python
# Orden obligatorio:
# 1. stdlib
# 2. terceros (flet, supabase, pydantic)
# 3. módulos internos del proyecto

import logging
from dataclasses import dataclass
from typing import Optional, List

import flet as ft
from supabase import create_client, Client

from core.supabase_client import get_client
```

### 3.3 Type hints obligatorios

```python
# ✅ Correcto
def obtener_insumo(codigo_insumo: str) -> Optional[dict]:
    ...

# ❌ Incorrecto
def obtener_insumo(codigo):
    ...
```

### 3.4 Docstrings

```python
def crear_insumo(codigo: str, nombre: str, costo: float) -> dict:
    """
    Crea un nuevo insumo en Supabase y retorna el diccionario creado.

    Args:
        codigo: Código único del insumo.
        nombre: Nombre descriptivo.
        costo: Costo unitario en COP. Debe ser >= 0.

    Returns:
        Diccionario con los datos del insumo recién creado.

    Raises:
        ValueError: Si costo < 0.
        Exception: Si falla la conexión a la base de datos.
    """
```

---

## 4. Patrones de Conexión a Supabase

### 4.1 Cliente Singleton y Rutas

**Nunca** crear el cliente Supabase directamente en las vistas. Siempre usar el cliente centralizado ubicado en `core/supabase_client.py`. 

```python
# core/supabase_client.py
from supabase import create_client, Client
import config

class DatabaseClient:
    def __init__(self):
        self.url = config.SUPABASE_URL
        self.key = config.SUPABASE_KEY
        self.client: Client = create_client(self.url, self.key)
```

### 4.2 Estructura del Core y Lógica de Negocio

El directorio `core/` debe mantenerse estrictamente para integraciones y clientes crudos, sin inflarlo con lógica de negocio compleja:
- `core/supabase_client.py` ← Solo conexión y queries crudas a la base de datos.
- `core/gemini_parser.py` ← Solo integración con la IA de extracción.
- `core/excel_manager.py` ← Solo generación y lectura de Excel.

Las reglas de negocio (ej. cálculos de inventario, validaciones complejas de auditorías) deben vivir en las vistas dentro de `ui/views/` o en funciones auxiliares claramente nombradas dentro de esos módulos. No están permitidos los servicios intermedios (`services/` o `models/`) por ahora para evitar sobreingeniería. Si en el futuro el proyecto crece, se discutirá su migración.

### 4.3 Variables de entorno

- Las credenciales de Supabase van **solo** en `.env` y se cargan en el archivo `config.py` en la raíz del proyecto.
- **NUNCA** hardcodear `SUPABASE_URL` o `SUPABASE_KEY` en ningún archivo de código.
- El agente no debe modificar `.env`.

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
```

### 4.4 Manejo de respuestas Supabase

```python
# ✅ Siempre verificar que response.data no sea None ni vacío
response = db.table("productos").select("*").eq("id", producto_id).execute()
if not response.data:
    return None
return Producto(**response.data[0])
```

---

## 5. Estructura de Vistas y Componentes Flet

### 5.1 Separación Vista / Componente

- **`ui/views/`**: páginas completas con lógica local de negocio, acceso a la DB, navegación y estado de la página.
- **`ui/layout/`**: elementos estructurales como la barra lateral de navegación.

### 5.2 Patrón de vista

```python
# ui/views/inventario.py
import flet as ft
from core.supabase_client import get_client

class InventarioView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.db = get_client()
        self.productos = []
        
    def load_data(self):
        self.productos = self.db.get_catalogo_insumos()
        self.page.update()
        
    def build(self) -> ft.View:
        return ft.View(
            route="/inventario",
            controls=[
                ft.AppBar(title=ft.Text("Inventario")),
                # Aquí iría el contenedor con las tablas
            ],
        )
```

### 5.4 Reglas Flet obligatorias

- Siempre llamar `page.update()` después de modificar controles existentes.
- Usar `page.go(route)` para navegación — nunca manipular `page.views` directamente sin actualizar.
- Los diálogos se añaden a `page.overlay` antes de mostrarlos:
  ```python
  page.overlay.append(dialogo)
  dialogo.open = True
  page.update()
  ```
- No bloquear el hilo principal de Flet con operaciones lentas (Supabase, IO). Usar `asyncio` o `threading` cuando sea necesario.

---

## 6. Manejo de Errores y Validaciones en UI

Las validaciones y el manejo de errores se realizan en su mayoría directamente en las vistas, atrapando excepciones antes de ejecutar operaciones críticas.

### 6.1 Feedback al usuario (Snackbar)

Siempre debes proveer feedback visual al usuario tras una acción de modificación de datos:

```python
# En ui/views/alguna_vista.py
def guardar_datos(self, e):
    try:
        if not self.campo_nombre.value:
            self.page.snack_bar = ft.SnackBar(ft.Text("El nombre es obligatorio"), bgcolor="red")
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        # Lógica de guardado a través de core/supabase_client.py...
        self.page.snack_bar = ft.SnackBar(ft.Text("Datos guardados exitosamente"), bgcolor="green")
        self.page.snack_bar.open = True
        self.page.update()
        
    except Exception as ex:
        self.page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {ex}"), bgcolor="red")
        self.page.snack_bar.open = True
        self.page.update()
```

---

## 7. Pruebas y Verificación (Manuales)

Actualmente el proyecto prescinde de una suite estricta de tests automatizados generalizados. En su lugar, el agente debe verificar de forma rigurosa la base de datos (con queries temporales o scripts) o mediante logs controlados que los cálculos financieros y las consultas de Supabase funcionan de manera esperada. 

Sin embargo, se deben mantener **tests mínimos sobre funciones críticas** (ej. cálculos financieros complejos o parseo de PDFs) si existen.

### 7.3 Comando de verificación para el agente

Después de cualquier cambio crítico, si aplica, el agente DEBE ejecutar:

```bash
# Verificación de formato
python -m flake8 . --max-line-length=120 --exclude=.env,__pycache__

# Tests mínimos (si existen tests para el módulo modificado)
python -m pytest tests/ -v

# Verificación de imports y tipos (si mypy está instalado)
python -m mypy . --ignore-missing-imports
```

> El agente NO debe marcar una tarea como completada si introdujo errores de sintaxis detectables.

---

## 8. Restricciones Absolutas para el Agente

El agente **NUNCA** debe:

- ❌ Modificar o leer el archivo `.env`
- ❌ Hardcodear credenciales, URLs de Supabase o API keys en el código
- ❌ Crear el cliente Supabase fuera de `core/supabase_client.py`
- ❌ Inventar o recrear directorios como `services/`, `models/` o `utils/`. La lógica va en las vistas o en helpers locales.
- ❌ Usar `print()` indiscriminado en código final (usar solo para pruebas o limpiar al terminar).
- ❌ Hacer commits de git sin que el usuario lo solicite explícitamente
- ❌ Instalar dependencias sin mostrárselas primero al usuario para aprobación
- ❌ Modificar `requirements.txt` sin avisar qué se añade y por qué

---

## 9. Dependencias del Proyecto

```txt
flet==0.21.2
supabase==2.3.4
pandas==2.2.1
openpyxl==3.1.2
python-dotenv==1.0.1
google-generativeai==0.8.3
plotly
```

Para instalar: `pip install -r requirements.txt`

---

## 10. Contexto de Datos (Tablas Supabase)

> El agente debe respetar estos nombres de tabla y columnas exactamente como están definidos.

### `catalogo_insumos`
| Columna          | Tipo            | Descripción                              |
|------------------|-----------------|------------------------------------------|
| `id_insumo`      | `uuid`          | PK generada automáticamente              |
| `codigo_insumo`  | `text`          | Unique Key, código maestro del insumo    |
| `nombre`         | `text`          | Nombre del insumo/producto               |
| `descripcion`    | `text`          | Descripción opcional                     |
| `categoria`      | `text`          | Categoría a la que pertenece             |
| `costo_unitario` | `numeric(10,2)` | Último costo unitario (promedio/compra)  |
| `precio_venta`   | `numeric(10,2)` | Precio de venta sugerido                 |
| `stock_actual`   | `numeric(12,2)` | Inventario actual en el sistema (por UI o trigger) |
| `stock_minimo`   | `numeric(12,2)` | Límite de alerta mínimo                  |
| `estado`         | `bool`          | Activo/inactivo (default true)           |
| `zona`           | `text`          | Zona de almacenamiento                   |
| `ubicacion`      | `text`          | Ubicación en la zona                     |
| `tipo_unidad`    | `text`          | Unidad de medida                         |

### `registro_compras`
| Columna           | Tipo            | Descripción                              |
|-------------------|-----------------|------------------------------------------|
| `id_compra`       | `uuid`          | PK                                       |
| `fecha`           | `timestamptz`   | Fecha de la compra                       |
| `descripcion`     | `text`          | Detalles de compra                       |
| `cantidad`        | `numeric(12,2)` | Cantidad comprada                        |
| `proveedor`       | `text`          | Nombre del proveedor                     |
| `estado_registro` | `text`          | 'VÁLIDO' o 'ANULADO'                     |
| `codigo_insumo`   | `text`          | FK hacia `catalogo_insumos`              |
| `numero_entrada`  | `text`          | Documento interno                        |
| `numero_factura`  | `text`          | Documento del proveedor                  |
| `bodega`          | `text`          | Bodega de destino                        |
| `costo_unitario`  | `numeric(12,2)` | Costo por unidad                         |
| `valor_iva`       | `numeric(12,2)` | IVA total de la línea                    |
| `costo_total`     | `numeric(12,2)` | Cantidad * Costo Unitario + IVA          |

### `registro_ventas`
| Columna           | Tipo            | Descripción                              |
|-------------------|-----------------|------------------------------------------|
| `id_venta`        | `uuid`          | PK                                       |
| `factura_no`      | `text`          | Número de factura de venta/remisión      |
| `fecha`           | `timestamptz`   | Fecha de la venta                        |
| `descripcion`     | `text`          | Nombre extraído o nota                   |
| `cantidad`        | `numeric(12,2)` | Unidades vendidas                        |
| `subtotal`        | `numeric(12,2)` | Valor sin IVA de la línea                |
| `descuento`       | `numeric(12,2)` | Descuento aplicado                       |
| `iva`             | `numeric(12,2)` | IVA aplicado                             |
| `total`           | `numeric(12,2)` | Total cobrado en la línea                |
| `estado_registro` | `text`          | 'VÁLIDO' o 'ANULADO'                     |
| `codigo_insumo`   | `text`          | FK hacia `catalogo_insumos`              |
| `tipo_documento`  | `text`          | Ej: 'Remisión' o 'Factura POS'           |
| `pagina_origen`   | `int4`          | Página del PDF del cual fue extraído     |

### `registro_ajustes_inventario`
| Columna                    | Tipo            | Descripción                              |
|----------------------------|-----------------|------------------------------------------|
| `id_ajuste`                | `uuid`          | PK                                       |
| `fecha_ajuste`             | `timestamptz`   | Fecha de registro del ajuste             |
| `codigo_insumo`            | `text`          | FK a `catalogo_insumos`                  |
| `tipo_ajuste`              | `text`          | Ej. 'AJUSTE_ENTRADA', 'AJUSTE_SALIDA'    |
| `cantidad`                 | `numeric(12,2)` | Cantidad ajustada                        |
| `costo_unitario_congelado` | `numeric(12,2)` | Costo del momento en que se hizo         |
| `costo_total_ajuste`       | `numeric(12,2)` | Total financiero del ajuste              |
| `motivo_observacion`       | `text`          | Notas del ajuste                         |
| `estado_registro`          | `text`          | 'VÁLIDO' o 'ANULADO'                     |
| `id_auditoria_origen`      | `uuid`          | FK opcional al registro_auditorias_cierres |
| `id_periodo`               | `uuid`          | FK opcional a periodos_inventario        |

### `periodos_inventario`
| Columna                 | Tipo            | Descripción                              |
|-------------------------|-----------------|------------------------------------------|
| `id_periodo`            | `uuid`          | PK                                       |
| `mes_periodo`           | `text`          | YYYY-MM                                  |
| `fecha_inicio`          | `date`          | Inicio del mes                           |
| `fecha_corte`           | `timestamptz`   | Instante en que se generó snapshot       |
| `estado`                | `text`          | ABIERTO, PRELIMINAR, EN_AUDITORIA, CERRADO |
| `origen_snapshot`       | `text`          | AUTOMATICO o MANUAL                      |
| `aprobado_por`          | `text`          | Firma del usuario que cerró              |
| `fecha_aprobacion`      | `timestamptz`   | Timestamp del cierre                     |
| `total_costo_entradas`  | `numeric`       | KPIs financieros del mes                 |
| `total_ingreso_salidas` | `numeric`       | KPIs financieros del mes                 |

### `registro_auditorias_cierres` (Cierre Mensual)
| Columna                   | Tipo            | Descripción                              |
|---------------------------|-----------------|------------------------------------------|
| `id_auditoria`            | `uuid`          | PK                                       |
| `id_periodo`              | `uuid`          | FK a `periodos_inventario`               |
| `fecha_cierre`            | `timestamptz`   | Fecha del snapshot o conteo              |
| `codigo_insumo`           | `text`          | FK a `catalogo_insumos`                  |
| `tipo_registro`           | `text`          | SNAPSHOT, INVENTARIO_INICIAL             |
| `cantidad_sistema`        | `numeric(12,2)` | Cantidad teórica al momento de cierre    |
| `cantidad_fisica`         | `numeric(12,2)` | Cantidad contada por usuario             |
| `diferencia`              | `numeric(12,2)` | Fisica - Sistema                         |
| `estado`                  | `text`          | PENDIENTE, AUDITADO, AJUSTADO, APROBADO  |
| `costo_unitario_snapshot` | `numeric`       | Costo al momento del snapshot            |

### `conteo_fisico_relacionado`
Tabla temporal/alterna para capturar conteos desde dispositivos u OCR y luego procesarlos:
| Columna                  | Tipo   | Descripción                               |
|--------------------------|--------|-------------------------------------------|
| `id_conteo`              | `uuid` | PK                                        |
| `cod_insumo_fisico`      | `text` | Código original ingresado/escaneado       |
| `codigo_sugerido`        | `text` | FK opcional sugerido en `catalogo_insumos`|
| `cantidad_fisica`        | `int4` | Cantidad digitada                         |

> ⚠️ Si las tablas reales difieren, el agente debe preguntar antes de asumir o modificar.

---

## 11. Instrucciones de Flujo para el Agente

1. **Explorar antes de actuar**: lee los archivos relevantes antes de escribir código.
2. **Planificar primero**: presenta el plan de cambios antes de ejecutar (usar Planning mode).
3. **Cambios atómicos**: un PR/tarea = una funcionalidad. No mezclar refactors con features.
4. **Verificar siempre**: ejecutar los comandos de verificación del punto 7.3 antes de terminar.
5. **Preguntar si hay ambigüedad**: si un requisito no está claro, preguntar antes de asumir.
6. **Respetar lo existente**: no reescribir código que ya funciona a menos que se solicite explícitamente.
