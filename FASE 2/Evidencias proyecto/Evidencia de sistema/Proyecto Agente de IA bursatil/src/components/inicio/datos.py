# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara datos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Accesos rápidos y promociones de la vista Inicio (viven en datos.json).

Lee el JSON una vez al importar (con la caché de `_estaticos`) y expone dos listas de tuplas listas para
iterar en panel.py.
"""
from pathlib import Path

# Lector de JSON con caché.
from components._estaticos import datos_json

# Contenido completo de datos.json (claves "acciones" y "promos").
_D = datos_json(Path(__file__).parent / "datos.json")

# (ícono Material, color, título, subtítulo, destino o None)
ACCIONES = [tuple(a) for a in _D["acciones"]]
# (clase, ícono Material, color, título, descripción)
PROMOS = [tuple(p) for p in _D["promos"]]


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara datos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
