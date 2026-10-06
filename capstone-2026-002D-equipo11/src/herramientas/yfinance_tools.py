"""Herramientas del agente basadas en Yahoo Finance.

Todas llevan el prefijo yf_ para que, cuando se sumen las de MT5 e
investing.com, el modelo distinga de qué fuente viene cada dato.
La lógica real vive en fuentes/yfinance_fuente.py; aquí solo se describe
cada herramienta para el modelo.
"""
from fuentes import yfinance_fuente as fuente
from herramientas.base import herramienta

_SIMBOLO = {
    "type": "string",
    "description": (
        "Símbolo de Yahoo Finance. Ejemplos: AAPL (acción), EURUSD=X (forex), "
        "^GSPC (índice S&P 500), BTC-USD (cripto), GC=F (oro). "
        "Si no conoces el símbolo, usa yf_buscar_simbolo primero."
    ),
}


@herramienta(
    descripcion=(
        "Busca símbolos de Yahoo Finance a partir de un nombre de empresa o activo "
        "(ej. 'apple', 'oro', 'bitcoin'). Devuelve símbolo, nombre, tipo y bolsa."
    ),
    parametros={
        "consulta": {"type": "string", "description": "Nombre o texto a buscar."},
        "max_resultados": {"type": "integer", "description": "Máximo de resultados (1-15). Por defecto 8."},
    },
    requeridos=["consulta"],
    nombre="yf_buscar_simbolo",
)
def yf_buscar_simbolo(consulta: str, max_resultados: int = 8) -> list:
    return fuente.buscar(consulta, max_resultados)


@herramienta(
    descripcion=(
        "Cotización actual de un activo según Yahoo Finance: precio, variación del día, "
        "rango del día y de 52 semanas, volumen, medias de 50 y 200 días y capitalización. "
        "Los datos pueden tener retraso de hasta ~15 min."
    ),
    parametros={"simbolo": _SIMBOLO},
    requeridos=["simbolo"],
    nombre="yf_cotizacion",
)
def yf_cotizacion(simbolo: str) -> dict:
    return fuente.cotizacion(simbolo)


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
    return fuente.historico(simbolo, periodo, intervalo, inicio, fin, ultimas_velas)


@herramienta(
    descripcion=(
        "Datos fundamentales de una empresa (solo acciones): sector, capitalización, PER, EPS, "
        "márgenes, ROE, deuda, caja, crecimiento de ingresos y beneficios, dividendo y beta."
    ),
    parametros={"simbolo": _SIMBOLO},
    requeridos=["simbolo"],
    nombre="yf_fundamentales",
)
def yf_fundamentales(simbolo: str) -> dict:
    return fuente.fundamentales(simbolo)


@herramienta(
    descripcion=(
        "Estados financieros de una empresa (solo acciones): estado de resultados, balance o "
        "flujo de caja, anual o trimestral, con las partidas clave de los últimos periodos."
    ),
    parametros={
        "simbolo": _SIMBOLO,
        "tipo": {
            "type": "string",
            "enum": ["resultados", "balance", "flujo_caja"],
            "description": "Estado a consultar. Por defecto resultados.",
        },
        "frecuencia": {
            "type": "string",
            "enum": ["anual", "trimestral"],
            "description": "Por defecto anual.",
        },
        "periodos": {"type": "integer", "description": "Cuántos periodos recientes (1-8). Por defecto 4."},
    },
    requeridos=["simbolo"],
    nombre="yf_estados_financieros",
)
def yf_estados_financieros(
    simbolo: str, tipo: str = "resultados", frecuencia: str = "anual", periodos: int = 4
) -> dict:
    return fuente.estados_financieros(simbolo, tipo, frecuencia, periodos)


@herramienta(
    descripcion=(
        "Últimas noticias de Yahoo Finance sobre un activo: titular, resumen breve, medio, "
        "fecha y enlace."
    ),
    parametros={
        "simbolo": _SIMBOLO,
        "cantidad": {"type": "integer", "description": "Cuántas noticias (1-20). Por defecto 8."},
    },
    requeridos=["simbolo"],
    nombre="yf_noticias",
)
def yf_noticias(simbolo: str, cantidad: int = 8) -> list:
    return fuente.noticias(simbolo, cantidad)


@herramienta(
    descripcion=(
        "Consenso de analistas sobre una acción: precio objetivo (actual, mínimo, máximo, media, "
        "mediana) y recomendaciones (compra fuerte, compra, mantener, venta, venta fuerte)."
    ),
    parametros={"simbolo": _SIMBOLO},
    requeridos=["simbolo"],
    nombre="yf_consenso_analistas",
)
def yf_consenso_analistas(simbolo: str) -> dict:
    return fuente.consenso_analistas(simbolo)