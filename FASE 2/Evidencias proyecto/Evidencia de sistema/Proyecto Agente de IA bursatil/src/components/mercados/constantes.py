# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara constantes .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Catálogo de instrumentos, resumen, órdenes y colores de la página Mercados (los datos viven en datos.json)."""
from pathlib import Path

from components._estaticos import datos_json

# Contenido completo de datos.json (catálogo, resumen, órdenes y reparto de columnas)
_D = datos_json(Path(__file__).parent / "datos.json")

# {categoría: [(candidatos, nombre)]}. El primer candidato que exista en el bróker se usa.
CATALOGO = {cat: [(tuple(c), n) for c, n in items] for cat, items in _D["catalogo"].items()}

# "Pulso del mercado": la referencia más seguida de cada mercado
# (categoría, índice dentro del catálogo, qué representa)
RESUMEN = [tuple(x) for x in _D["resumen"]]

# Criterios de orden disponibles en el selector de la tabla; el primero es el valor por defecto
ORDENES = list(_D["ordenes"])

# Columnas de la tabla — cabecera y filas comparten el reparto
GRID = _D["grid"]

# Colores de la interfaz: verde (sube), rojo (baja) y gris (neutro/texto secundario)
VERDE, ROJO, GRIS = "#3fb950", "#f85149", "#8b949e"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara constantes .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
