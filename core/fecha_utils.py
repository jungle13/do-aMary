"""
Módulo centralizado para el manejo y estandarización de fechas y zonas horarias.
Asegura que todas las operaciones de la aplicación utilicen la zona horaria 'America/Bogota' (UTC-5).
"""
import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Union

# Zona horaria oficial del negocio
TZ_BOGOTA = ZoneInfo("America/Bogota")


def get_ahora_local() -> datetime.datetime:
    """Retorna la fecha y hora actual en la zona horaria de Colombia."""
    return datetime.datetime.now(TZ_BOGOTA)


def get_ahora_iso() -> str:
    """
    Retorna la fecha y hora actual en formato ISO 8601 con offset explícito.
    Ejemplo: '2026-08-24T20:34:00-05:00'
    """
    return datetime.datetime.now(TZ_BOGOTA).isoformat()


def get_hoy_local_str() -> str:
    """Retorna la fecha actual en formato 'YYYY-MM-DD' según la hora de Colombia."""
    return datetime.datetime.now(TZ_BOGOTA).strftime("%Y-%m-%d")


def get_mes_actual_str() -> str:
    """Retorna el mes actual en formato 'YYYY-MM' según la hora de Colombia."""
    return datetime.datetime.now(TZ_BOGOTA).strftime("%Y-%m")


def parsear_a_datetime_local(val: Union[str, datetime.datetime, datetime.date, None]) -> Optional[datetime.datetime]:
    """
    Convierte cualquier fecha/hora (string ISO, UTC, o datetime) a un objeto datetime
    localizado en 'America/Bogota'.
    """
    if val is None:
        return None

    if isinstance(val, datetime.datetime):
        if val.tzinfo is None:
            # Si no tiene zona horaria, asumimos que viene en UTC de la DB
            val = val.replace(tzinfo=datetime.timezone.utc)
        return val.astimezone(TZ_BOGOTA)

    if isinstance(val, datetime.date):
        return datetime.datetime.combine(val, datetime.time.min, tzinfo=TZ_BOGOTA)

    val_str = str(val).strip()
    if not val_str:
        return None

    try:
        # Reemplazar sufijo 'Z' por '+00:00' para compatibilidad ISO
        clean_str = val_str.replace("Z", "+00:00")
        
        # Caso 1: String ISO completo con fecha y hora
        if "T" in clean_str or " " in clean_str:
            dt = datetime.datetime.fromisoformat(clean_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(TZ_BOGOTA)

        # Caso 2: Solo fecha 'YYYY-MM-DD'
        if len(clean_str) == 10 and clean_str.count("-") == 2:
            parts = clean_str.split("-")
            return datetime.datetime(int(parts[0]), int(parts[1]), int(parts[2]), tzinfo=TZ_BOGOTA)

    except Exception:
        pass

    return None


def parsear_a_fecha_local(val: Union[str, datetime.datetime, datetime.date, None]) -> str:
    """
    Convierte cualquier timestamp o string UTC proveniente de Supabase
    (ej: '2026-08-25T01:34:00+00:00') a la fecha real en Colombia 'YYYY-MM-DD'.
    """
    if not val:
        return ""

    dt = parsear_a_datetime_local(val)
    if dt:
        return dt.strftime("%Y-%m-%d")

    # Fallback seguro
    val_str = str(val).strip()
    return val_str[:10] if len(val_str) >= 10 else val_str


def formatear_fecha_hora_local(
    val: Union[str, datetime.datetime, None],
    formato: str = "%Y-%m-%d %I:%M %p"
) -> str:
    """
    Formatea una fecha/hora para visualización en interfaz de usuario
    en la zona horaria de Colombia.
    """
    if not val:
        return ""

    dt = parsear_a_datetime_local(val)
    if dt:
        return dt.strftime(formato)

    return str(val)
