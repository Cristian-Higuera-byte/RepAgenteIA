"""Herramientas del agente basadas en MetaTrader 5 (XM).

Todas llevan el prefijo mt5_ para que el modelo distinga claramente la fuente.
La lógica de conexión y lectura vive en fuentes/Mt5_fuentes.py.
"""

from fuentes import Mt5_fuentes as fuente
from herramientas.base import herramienta

_SIMBOLO = {
    "type": "string",
    "description": (
        "Símbolo o ticker en MetaTrader 5 (ej. EURUSD, XAUUSD, US30, AAPL). "
        "Si no conoces el nombre exacto de tu broker, usa mt5_buscar_simbolos."
    ),
}


@herramienta(
    descripcion=(
        "Busca símbolos disponibles en el terminal MT5 de XM por nombre o descripción "
        "(ej. 'eurusd', 'gold', 'petroleo'). Devuelve el nombre exacto del broker."
    ),
    parametros={
        "texto": {"type": "string", "description": "Texto o concepto a buscar."},
        "max_resultados": {
            "type": "integer",
            "description": "Máximo de coincidencias (1-40). Por defecto 15.",
        },
    },
    requeridos=["texto"],
    nombre="mt5_buscar_simbolos",
)
def mt5_buscar_simbolos(texto: str, max_resultados: int = 15) -> dict:
    return fuente.buscar_simbolos(texto, max_resultados)


@herramienta(
    descripcion=(
        "Cotización en tiempo real de un activo desde el terminal MT5: bid, ask, spread, "
        "variación del día, máximo/mínimo y horario del servidor."
    ),
    parametros={"simbolo": _SIMBOLO},
    requeridos=["simbolo"],
    nombre="mt5_precio",
)
def mt5_precio(simbolo: str) -> dict:
    return fuente.precio(simbolo)


@herramienta(
    descripcion=(
        "Histórico de velas (OHLCV) desde MT5. Devuelve un resumen estadístico del rango "
        "completo (variación %, rango promedio, volatilidad) y las últimas N velas en detalle. "
        "Timeframes válidos: M1, M5, M15, M30, H1, H4, D1, W1, MN1."
    ),
    parametros={
        "simbolo": _SIMBOLO,
        "timeframe": {
            "type": "string",
            "enum": list(fuente.TIMEFRAMES),
            "description": "Temporalidad de las velas. Por defecto H1.",
        },
        "cantidad": {
            "type": "integer",
            "description": "Velas totales para el resumen estadístico (1-5000). Por defecto 100.",
        },
        "ultimas_velas": {
            "type": "integer",
            "description": "Cuántas velas detallar al final (0-200). Por defecto 20.",
        },
        "desde": {
            "type": "string",
            "description": "Fecha inicial AAAA-MM-DD (opcional).",
        },
        "hasta": {
            "type": "string",
            "description": "Fecha final AAAA-MM-DD (opcional).",
        },
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
    return fuente.velas(
        simbolo=simbolo,
        timeframe=timeframe,
        cantidad=cantidad,
        ultimas_velas=ultimas_velas,
        desde=desde,
        hasta=hasta,
    )


@herramienta(
    descripcion=(
        "Obtiene las métricas financieras de la cuenta de trading en MT5: "
        "balance, equidad (equity), beneficio flotante, margen usado, margen libre y nivel de margen."
    ),
    parametros={},
    requeridos=[],
    nombre="mt5_cuenta",
)
def mt5_cuenta() -> dict:
    return fuente.cuenta()


@herramienta(
    descripcion=(
        "Lista las posiciones (operaciones) actualmente abiertas en la cuenta de MT5: "
        "ticket, tipo (compra/venta), volumen, precio de apertura, P/G flotante y swap."
    ),
    parametros={
        "simbolo": {
            "type": "string",
            "description": "Filtrar posiciones por un símbolo específico (opcional).",
        }
    },
    requeridos=[],
    nombre="mt5_posiciones",
)
def mt5_posiciones(simbolo: str | None = None) -> dict:
    return fuente.posiciones(simbolo=simbolo)


@herramienta(
    descripcion=(
        "Muestra las órdenes pendientes activas en la cuenta de MT5 (Buy Limit, Sell Limit, Stop Loss, etc.)."
    ),
    parametros={
        "simbolo": {
            "type": "string",
            "description": "Filtrar por un símbolo específico (opcional).",
        }
    },
    requeridos=[],
    nombre="mt5_ordenes_pendientes",
)
def mt5_ordenes_pendientes(simbolo: str | None = None) -> dict:
    return fuente.ordenes_pendientes(simbolo=simbolo)


@herramienta(
    descripcion=(
        "Obtiene el historial de operaciones CERRADAS en MT5 en los últimos N días. "
        "Devuelve métricas globales (tasa de acierto, profit factor, mejor/peor operación) "
        "y el desglose de las últimas operaciones."
    ),
    parametros={
        "dias": {
            "type": "integer",
            "description": "Días hacia atrás a consultar (1-365). Por defecto 30.",
        },
        "simbolo": {
            "type": "string",
            "description": "Filtrar por un símbolo específico (opcional).",
        },
        "ultimas": {
            "type": "integer",
            "description": "Número de operaciones recientes a detallar (0-100). Por defecto 15.",
        },
    },
    requeridos=[],
    nombre="mt5_historial",
)
def mt5_historial(
    dias: int = 30, simbolo: str | None = None, ultimas: int = 15
) -> dict:
    return fuente.historial_operaciones(dias=dias, simbolo=simbolo, ultimas=ultimas)