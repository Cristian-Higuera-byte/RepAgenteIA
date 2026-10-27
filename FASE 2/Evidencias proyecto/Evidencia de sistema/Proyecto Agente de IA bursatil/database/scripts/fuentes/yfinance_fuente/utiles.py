# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara utiles .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Utilidades de normalización: símbolos, números, campos, fechas.

Funciones puras (sin red) que dejan los datos de Yahoo listos y seguros para
serializar a JSON y enviar al modelo."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def _simbolo(texto: str) -> str:
    """Normaliza un símbolo de Yahoo (quita espacios y pasa a mayúsculas).

    Lanza ValueError con un mensaje claro si el texto está vacío o es None."""
    s = (texto or "").strip().upper()
    if not s:
        raise ValueError("Falta el símbolo.")
    return s


def _num(valor: Any, decimales: int = 4) -> float | None:
    """Convierte a float JSON-seguro (NaN/inf/None -> None).

    Recibe el valor y los decimales de redondeo (4 por defecto). Devuelve None
    si no se puede convertir a número o si es NaN o infinito."""
    try:
        f = float(valor)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, decimales)


def _entero(valor: Any) -> int | None:
    """Convierte un valor a entero (redondeando) o devuelve None si no es un número válido."""
    n = _num(valor, 0)
    return int(n) if n is not None else None


def _leer(obj: Any, nombre: str, texto: bool = False) -> Any:
    """Lee de forma segura el atributo `nombre` de un objeto de yfinance (p. ej. `fast_info`).

    Devuelve el valor tal cual si `texto` es True, o convertido con `_num` si es
    False (por defecto). Devuelve None si el atributo no existe o su lectura
    lanza cualquier excepción."""
    try:
        v = getattr(obj, nombre)
    except Exception:  # noqa: BLE001 - fast_info lanza KeyError/AttributeError si falta
        return None
    return v if texto else _num(v)


def _sin_nulos(d: dict[str, Any]) -> dict[str, Any]:
    """Devuelve una copia del diccionario sin las claves cuyo valor es None.

    Se usa para no enviar campos vacíos al modelo y ahorrar contexto. Los
    valores falsos distintos de None (0, '', listas vacías) se conservan."""
    return {k: v for k, v in d.items() if v is not None}


def _validar_fecha(texto: str, campo: str) -> str:
    """Comprueba que `texto` tenga formato 'AAAA-MM-DD' y lo devuelve sin cambios.

    `campo` es el nombre del parámetro ('inicio' o 'fin') y se usa en el mensaje
    de error. Lanza ValueError si el formato no es válido."""
    try:
        datetime.strptime(texto, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"'{campo}' debe tener formato AAAA-MM-DD (recibido: {texto!r}).") from None
    return texto


def _formatear_fecha(ts: Any, intradia: bool) -> str:
    """Formatea un timestamp de pandas como 'AAAA-MM-DD HH:MM' (intradía) o 'AAAA-MM-DD' (diario o mayor)."""
    return ts.strftime("%Y-%m-%d %H:%M" if intradia else "%Y-%m-%d")


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara utiles .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
