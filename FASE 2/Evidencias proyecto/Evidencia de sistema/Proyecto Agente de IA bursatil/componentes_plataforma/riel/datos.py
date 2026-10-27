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

"""Medidas del rail derecho y lista de sus botones.

Las medidas son constantes en píxeles que `estilos.py` sustituye en la plantilla `estilos.css`; los botones se leen
de `botones.json` (con el caché de `_estaticos`). Lo importan `estilos.py`, `panel.py` y la fachada `riel/`.
"""
from pathlib import Path

from componentes_plataforma._estaticos import datos_json

RAIL = 50        # ancho del rail (px) — angosto, como una barra de iconos
PANEL = 312      # ancho del panel desplegado (px)
TOP = 62         # alto de la barra superior (ajústalo si el panel queda alto/bajo)

# (icono material, id del panel, nombre del tooltip)
BOTONES = [tuple(b) for b in datos_json(Path(__file__).parent / "botones.json")]


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
