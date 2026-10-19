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

"""Utilidades de las consultas: números, fechas UTC, resolución de símbolos (alias) y símbolo temporal.

Funciones auxiliares compartidas por `cuenta.py` y `mercado.py`. Las que
reciben `mt5` esperan el envoltorio de solo lectura entregado por `_sesion()`."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from database.scripts.fuentes.mt5_fuentes.constantes import _ALIAS
from database.scripts.fuentes.mt5_fuentes.errores import ErrorMT5


def _num(v: Any, dec: int = 5) -> float | None:
    """Convierte un valor a float redondeado y seguro para JSON.

    Recibe el valor y los decimales (5 por defecto). Devuelve None si no es
    convertible, o si es NaN o infinito; así nunca se envían valores inválidos al modelo."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    # f != f solo es verdadero para NaN; también se descartan los infinitos.
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return round(f, dec)


def _nivel(v: Any) -> float | None:
    """Convierte un nivel de precio (SL/TP) a float, tratando 0 o vacío como "sin nivel" (None).

    MT5 informa 0.0 cuando una posición no tiene stop loss o take profit."""
    return _num(v) if v else None


def _hora_utc(ts: Any, mt5: Any) -> str:
    """Convierte un timestamp en segundos a texto 'AAAA-MM-DD HH:MM:SS UTC'.

    El parámetro `mt5` no se usa; se conserva para mantener la firma de quienes
    la llaman. Nota: MT5 entrega horas del servidor del broker, que aquí se
    interpretan como UTC sin aplicar desfase."""
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC"


def _fecha_utc(texto: str, campo: str) -> datetime:
    """Convierte un texto 'AAAA-MM-DD' a datetime a medianoche UTC.

    `campo` es el nombre del parámetro ('desde' o 'hasta') y se usa en el
    mensaje de error. Lanza ErrorMT5 si el formato no es válido."""
    try:
        return datetime.strptime(texto, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ErrorMT5(f"'{campo}' debe tener formato AAAA-MM-DD.") from None


def _como_tupla(mt5: Any, resultado: Any, accion: str) -> Any:
    """Normaliza el resultado de una consulta de MT5 que devuelve None cuando no hay datos.

    Si `resultado` es None consulta `last_error()`: si es un error real lanza
    ErrorMT5 ("MT5 falló al <accion>"); si no, devuelve una tupla vacía (simple
    ausencia de datos). Si hay resultado, lo devuelve sin cambios."""
    if resultado is None:
        err = mt5.last_error()
        # RES_S_OK (código 1) significa "sin error"; cualquier otro código es un fallo real.
        if err and err[0] != getattr(mt5, "RES_S_OK", 1):
            raise ErrorMT5(f"MT5 falló al {accion}: {err}")
        return ()
    return resultado


def _resolver(mt5: Any, texto: str) -> str:
    """Resuelve el nombre de un símbolo tal como lo llama el broker.

    Pasa el texto a mayúsculas; si el símbolo existe lo devuelve, y si no prueba
    los alias de `_ALIAS` (p. ej. oro -> XAUUSD o GOLD) y devuelve el primero
    que exista. Si nada coincide devuelve el texto normalizado para que la
    consulta posterior falle con un mensaje claro. Lanza ErrorMT5 si viene vacío."""
    bruto = (texto or "").strip().upper()
    if not bruto:
        raise ErrorMT5("Falta el símbolo.")
    info = mt5.symbol_info(bruto)
    if info is not None:
        return bruto
    # Prueba cada nombre alternativo registrado para este símbolo genérico.
    for alias in _ALIAS.get(bruto, []):
        if mt5.symbol_info(alias) is not None:
            return alias
    return bruto


@contextmanager
def _simbolo_temporal(mt5: Any, simbolo: str) -> Iterator[Any]:
    """Administrador de contexto que garantiza que un símbolo esté visible en Market Watch durante la consulta.

    Entrega la información del símbolo (`symbol_info`). Si el símbolo no estaba
    visible, lo activa con `symbol_select(True)` y, al terminar, lo vuelve a
    ocultar para dejar el terminal como estaba (efecto sobre el terminal). Lanza
    ErrorMT5 si el símbolo no existe."""
    info = mt5.symbol_info(simbolo)
    if info is None:
        raise ErrorMT5(f"El símbolo '{simbolo}' no existe en MT5.")
    estaba_visible = bool(info.visible)
    # MT5 solo entrega ticks y velas de símbolos visibles en Market Watch.
    if not estaba_visible:
        mt5.symbol_select(simbolo, True)
    try:
        yield info
    finally:
        # Restaura el estado original; un error al ocultar no debe ocultar el resultado de la consulta.
        if not estaba_visible:
            try:
                mt5.symbol_select(simbolo, False)
            except Exception:
                pass


def _tamano_pip(info: Any) -> float:
    """Tamaño de un 'pip' en precio: 10 puntos en símbolos de 3 o 5 decimales; el punto en el resto."""
    punto = float(getattr(info, "point", 0) or 0)
    return punto * 10 if getattr(info, "digits", 0) in (3, 5) else punto


def _tipo_orden(mt5: Any, tipo: str) -> int:
    """Traduce el tipo de operación en texto ('COMPRA'/'BUY' u otro) a la constante ORDER_TYPE de MT5.

    'COMPRA' o 'BUY' (sin distinguir mayúsculas) da ORDER_TYPE_BUY; cualquier
    otro valor se trata como venta (ORDER_TYPE_SELL)."""
    return mt5.ORDER_TYPE_BUY if str(tipo).upper() in ("COMPRA", "BUY") else mt5.ORDER_TYPE_SELL


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
