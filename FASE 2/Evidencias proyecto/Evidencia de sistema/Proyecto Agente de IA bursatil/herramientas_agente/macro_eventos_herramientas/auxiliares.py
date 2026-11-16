# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara auxiliares .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Constantes auxiliares del riesgo macro por noticias (sin registrar nada).

Carga desde ``datos.json`` las palabras clave que identifican eventos macro de
alto impacto y su relación con cada divisa, y define las categorías de
Investing.com que se revisan.
"""
from __future__ import annotations

from pathlib import Path

from herramientas_agente.base import cargar_json


# Contenido de datos.json (listas de palabras clave editables sin tocar código).
_DATOS = cargar_json(Path(__file__).parent / "datos.json")


# Categorías de noticias de Investing.com que se consultan para buscar titulares.
CATEGORIAS = ("economia", "forex", "mercados")


# Palabras (minúsculas) que delatan un evento macro de alto impacto en un titular.
_EVENTOS = tuple(_DATOS["_EVENTOS"])


# Palabras que vinculan un titular con una divisa.
_DIVISAS = {k: tuple(v) for k, v in _DATOS["_DIVISAS"].items()}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara auxiliares .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
