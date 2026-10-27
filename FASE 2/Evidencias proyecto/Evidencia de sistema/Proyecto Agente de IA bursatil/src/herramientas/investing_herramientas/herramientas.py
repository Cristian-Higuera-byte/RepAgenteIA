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

"""Herramientas registradas para el agente sobre noticias de Investing.com (los esquemas viven en esquemas.json).

Son envoltorios delgados: delegan en ``database.scripts.fuentes.investing_fuente``.
"""
from pathlib import Path

from database.scripts.fuentes import investing_fuente as fuente
from herramientas.base import cargar_json, herramienta

# Esquemas (descripción y parámetros) de las herramientas, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


@herramienta(**_ESQ["inv_noticias"])
def inv_noticias(categoria: str = "general", cantidad: int = 10) -> dict:
    """Devuelve las últimas noticias de Investing.com de una categoría (general por defecto) y la cantidad indicada, desde la fuente (red)."""
    return fuente.noticias(categoria=categoria, cantidad=cantidad)


@herramienta(**_ESQ["inv_buscar_noticias"])
def inv_buscar_noticias(
    busqueda: str, categoria: str = "general", cantidad: int = 10
) -> dict:
    """Busca noticias de Investing.com cuyo texto contenga ``busqueda`` dentro de una categoría y devuelve hasta ``cantidad`` (consulta de red)."""
    return fuente.buscar_noticias(
        busqueda=busqueda, categoria=categoria, cantidad=cantidad
    )


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
