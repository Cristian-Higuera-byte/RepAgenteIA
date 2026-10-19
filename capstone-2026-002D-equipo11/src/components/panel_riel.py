# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara panel_riel .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada del riel de íconos de la derecha (Operar / DOM).

Apunta al paquete `components/riel/` (panel, estilos, botones y script) y reexporta de allí las
constantes de geometría `RAIL`, `PANEL` y `TOP`, la lista `BOTONES` del riel, `inyectar_css_riel` (inserta el CSS)
y `renderizar_riel_y_paneles` (dibuja el riel y sus paneles desplegables). Existe para que el import de
`app.py` siga funcionando sin cambios. No contiene lógica propia.
"""
from components.riel import (BOTONES, PANEL, RAIL, TOP, inyectar_css_riel, renderizar_panel_favoritos,
                                         renderizar_riel_y_paneles)

__all__ = ["RAIL", "PANEL", "TOP", "BOTONES", "inyectar_css_riel", "renderizar_panel_favoritos", "renderizar_riel_y_paneles"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara panel_riel .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
