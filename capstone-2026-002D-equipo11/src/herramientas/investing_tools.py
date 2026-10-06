"""Herramientas del agente basadas en Investing.com (en español).

Todas llevan el prefijo inv_ para que el modelo distinga claramente de qué
fuente proviene cada noticia. La lógica real vive en fuentes/investing_fuente.py.
"""

from fuentes import investing_fuente as fuente
from herramientas.base import herramienta

_CATEGORIAS = ["general", "mercados", "forex", "acciones", "cripto", "economia"]


@herramienta(
    descripcion=(
        "Obtiene las últimas noticias macroeconómicas y de mercados publicadas en "
        "Investing.com (en español). Útil para análisis de sentimiento, eventos "
        "globales, decisiones de bancos centrales o contexto económico general. "
        "Categorías disponibles: 'general', 'mercados', 'forex', 'acciones', "
        "'cripto', 'economia'."
    ),
    parametros={
        "categoria": {
            "type": "string",
            "enum": _CATEGORIAS,
            "description": "Categoría de las noticias. Por defecto 'general'.",
        },
        "cantidad": {
            "type": "integer",
            "description": "Cantidad de noticias a recuperar (1-30). Por defecto 10.",
        },
    },
    requeridos=[],
    nombre="inv_noticias",
)
def inv_noticias(categoria: str = "general", cantidad: int = 10) -> dict:
    return fuente.noticias(categoria=categoria, cantidad=cantidad)


@herramienta(
    descripcion=(
        "Busca y filtra noticias recientes en Investing.com por un término o palabra "
        "clave específica (ej. 'inflación', 'FED', 'petróleo', 'Powell')."
    ),
    parametros={
        "busqueda": {
            "type": "string",
            "description": "Término o palabra clave a buscar en los titulares/resúmenes.",
        },
        "categoria": {
            "type": "string",
            "enum": _CATEGORIAS,
            "description": "Categoría en la que buscar. Por defecto 'general'.",
        },
        "cantidad": {
            "type": "integer",
            "description": "Máximo de noticias coincidentes a devolver (1-30). Por defecto 10.",
        },
    },
    requeridos=["busqueda"],
    nombre="inv_buscar_noticias",
)
def inv_buscar_noticias(
    busqueda: str, categoria: str = "general", cantidad: int = 10
) -> dict:
    return fuente.buscar_noticias(
        busqueda=busqueda, categoria=categoria, cantidad=cantidad
    )