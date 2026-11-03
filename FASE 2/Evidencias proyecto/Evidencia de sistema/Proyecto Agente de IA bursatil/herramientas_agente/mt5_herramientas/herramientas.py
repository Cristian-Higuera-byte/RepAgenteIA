# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara herramientas .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Herramientas registradas para el agente que consultan MetaTrader 5 (los esquemas viven en esquemas.json).

Son de solo lectura y delegan en ``fuentes.mt5_fuentes``.
"""
from pathlib import Path

from fuentes import mt5_fuentes as fuente
from herramientas_agente.base import cargar_json, herramienta
from herramientas_agente.mt5_herramientas.auxiliares import _SIMBOLO

# Esquemas (descripción y parámetros) de las herramientas, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


# TITULO MT5 BUSCAR SIMBOLOS

@herramienta(**_ESQ["mt5_buscar_simbolos"])
def mt5_buscar_simbolos(texto: str, max_resultados: int = 15) -> dict:
    """Busca símbolos del broker cuyo nombre o descripción contenga ``texto`` (hasta ``max_resultados``)."""
    return fuente.buscar_simbolos(texto, max_resultados)


# TITULO MT5 PRECIO

@herramienta(**_ESQ["mt5_precio"])
def mt5_precio(simbolo: str) -> dict:
    """Devuelve el precio actual (bid/ask) del símbolo desde el terminal MT5."""
    return fuente.precio(simbolo)


# TITULO MT5 VELAS

@herramienta(
    descripcion=(
        "Velas (OHLC + volumen) del broker (Capital.com o MT5). Devuelve resumen estadístico de las velas solicitadas "
        "y el detalle de las últimas N. Timeframes válidos: M1, M5, M15, M30, H1, H4, D1, W1, MN1."
    ),
    parametros={
        "simbolo": _SIMBOLO,
        "timeframe": {
            "type": "string",
            "enum": list(fuente.TIMEFRAMES),
            "description": "Temporalidad de cada vela. Por defecto H1.",
        },
        "cantidad": {"type": "integer", "description": "Cuántas velas recientes analizar (1-5000). Por defecto 100."},
        "ultimas_velas": {
            "type": "integer",
            "description": "Cuántas velas recientes devolver en detalle (0-200). Por defecto 20.",
        },
        "desde": {"type": "string", "description": "Fecha inicial AAAA-MM-DD (opcional)."},
        "hasta": {"type": "string", "description": "Fecha final AAAA-MM-DD (opcional)."},
    },
    requeridos=["simbolo"],
    nombre="mt5_velas",
)
def mt5_velas(
    simbolo: str,
    timeframe: str = "H1",
    cantidad: int = 100,
    ultimas_velas: int = 20,
    desde: str | None = None,
    hasta: str | None = None,
) -> dict:
    """Devuelve velas OHLC del símbolo: resumen estadístico de ``cantidad`` velas y detalle de las últimas ``ultimas_velas``.

    Admite un rango opcional ``desde``/``hasta`` (AAAA-MM-DD). Consulta el terminal MT5.
    Esta herramienta define su esquema aquí (no en esquemas.json) porque reutiliza ``_SIMBOLO`` y ``TIMEFRAMES``.
    """
    return fuente.velas(simbolo, timeframe, cantidad, ultimas_velas, desde, hasta)


# TITULO MT5 CUENTA

@herramienta(**_ESQ["mt5_cuenta"])
def mt5_cuenta() -> dict:
    """Devuelve el estado de la cuenta de MT5 (balance, equidad, margen, etc.)."""
    return fuente.cuenta()


# TITULO MT5 POSICIONES

@herramienta(**_ESQ["mt5_posiciones"])
def mt5_posiciones(simbolo: str | None = None) -> dict:
    """Lista las posiciones abiertas en MT5, opcionalmente filtradas por símbolo."""
    return fuente.posiciones(simbolo)


# TITULO MT5 ORDENES PENDIENTES

@herramienta(**_ESQ["mt5_ordenes_pendientes"])
def mt5_ordenes_pendientes(simbolo: str | None = None) -> dict:
    """Lista las órdenes pendientes (límite/stop) de MT5, opcionalmente filtradas por símbolo."""
    return fuente.ordenes_pendientes(simbolo)


# TITULO MT5 HISTORIAL OPERACIONES

@herramienta(**_ESQ["mt5_historial_operaciones"])
def mt5_historial_operaciones(dias: int = 30, simbolo: str | None = None, ultimas: int = 15) -> dict:
    """Devuelve el historial de operaciones cerradas de los últimos ``dias`` días (máximo ``ultimas`` registros, filtro opcional por símbolo)."""
    return fuente.historial_operaciones(dias, simbolo, ultimas)


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara herramientas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
