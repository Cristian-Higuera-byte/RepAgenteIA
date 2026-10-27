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

"""Herramientas registradas para el agente que consultan Yahoo Finance (los esquemas viven en esquemas.json).

Son envoltorios delgados que delegan en ``fuentes.yfinance_fuente`` (red).
"""
from pathlib import Path

from fuentes import yfinance_fuente as fuente
from herramientas_agente.base import cargar_json, herramienta
from herramientas_agente.yfinance_herramientas.auxiliares import _SIMBOLO

# Esquemas (descripción y parámetros) de las herramientas, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


# TITULO YF BUSCAR SIMBOLO

@herramienta(**_ESQ["yf_buscar_simbolo"])
def yf_buscar_simbolo(consulta: str, max_resultados: int = 8) -> list:
    """Busca símbolos de Yahoo Finance que coincidan con ``consulta`` (hasta ``max_resultados``)."""
    return fuente.buscar(consulta, max_resultados)


# TITULO YF COTIZACION

@herramienta(**_ESQ["yf_cotizacion"])
def yf_cotizacion(simbolo: str) -> dict:
    """Devuelve la cotización actual del símbolo en Yahoo Finance."""
    return fuente.cotizacion(simbolo)


# TITULO YF HISTORICO

@herramienta(
    descripcion=(
        "Histórico de precios (OHLCV) de Yahoo Finance. Devuelve un resumen estadístico de TODO "
        "el rango (variación %, máximo, mínimo, volatilidad) más las últimas N velas. "
        "Usa 'periodo' o bien 'inicio'/'fin' (si das 'inicio', se ignora 'periodo'). "
        "Los intervalos intradía solo tienen datos recientes (1m: 7 días; el resto: ~60 días)."
    ),
    parametros={
        "simbolo": _SIMBOLO,
        "periodo": {
            "type": "string",
            "enum": list(fuente.PERIODOS),
            "description": "Rango hacia atrás desde hoy. Por defecto 3mo.",
        },
        "intervalo": {
            "type": "string",
            "enum": list(fuente.INTERVALOS),
            "description": "Tamaño de cada vela. Por defecto 1d.",
        },
        "inicio": {"type": "string", "description": "Fecha inicial AAAA-MM-DD (opcional)."},
        "fin": {"type": "string", "description": "Fecha final AAAA-MM-DD (opcional; por defecto hoy)."},
        "ultimas_velas": {
            "type": "integer",
            "description": "Cuántas velas recientes incluir en detalle (0-200). Por defecto 20.",
        },
    },
    requeridos=["simbolo"],
    nombre="yf_historico",
)
def yf_historico(
    simbolo: str,
    periodo: str = "3mo",
    intervalo: str = "1d",
    inicio: str | None = None,
    fin: str | None = None,
    ultimas_velas: int = 20,
) -> dict:
    """Devuelve el histórico OHLCV: resumen estadístico de todo el rango y el detalle de las últimas ``ultimas_velas``.

    Usa ``periodo`` o, si se da ``inicio``, el rango ``inicio``/``fin``. Consulta Yahoo Finance.
    Define su esquema aquí (no en esquemas.json) porque reutiliza ``_SIMBOLO``, ``PERIODOS`` e ``INTERVALOS``.
    """
    return fuente.historico(simbolo, periodo, intervalo, inicio, fin, ultimas_velas)


# TITULO YF FUNDAMENTALES

@herramienta(**_ESQ["yf_fundamentales"])
def yf_fundamentales(simbolo: str) -> dict:
    """Devuelve datos fundamentales de la empresa (valoración, márgenes, etc.) desde Yahoo Finance."""
    return fuente.fundamentales(simbolo)


# TITULO YF ESTADOS FINANCIEROS

@herramienta(**_ESQ["yf_estados_financieros"])
def yf_estados_financieros(
    simbolo: str, tipo: str = "resultados", frecuencia: str = "anual", periodos: int = 4
) -> dict:
    """Devuelve estados financieros (``tipo``: resultados, balance o flujo) con la ``frecuencia`` y el número de ``periodos`` pedidos."""
    return fuente.estados_financieros(simbolo, tipo, frecuencia, periodos)


# TITULO YF NOTICIAS

@herramienta(**_ESQ["yf_noticias"])
def yf_noticias(simbolo: str, cantidad: int = 8) -> list:
    """Devuelve las últimas ``cantidad`` noticias de Yahoo Finance sobre el símbolo."""
    return fuente.noticias(simbolo, cantidad)


# TITULO YF CONSENSO ANALISTAS

@herramienta(**_ESQ["yf_consenso_analistas"])
def yf_consenso_analistas(simbolo: str) -> dict:
    """Devuelve el consenso de analistas (recomendación y precios objetivo) del símbolo desde Yahoo Finance."""
    return fuente.consenso_analistas(simbolo)


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
