# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara noticias_panel .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada del panel de noticias.

Apunta al paquete `components/noticias/` (panel, secciones, modal, RSS, datos y estilos) y reexporta de
allí `renderizar_panel_noticias`, la función que dibuja la vista. Existe para que
`from components.noticias_panel import renderizar_panel_noticias` (en `app.py`) siga
funcionando sin cambios. No contiene lógica propia.
"""
from components.noticias import renderizar_panel_noticias

__all__ = ["renderizar_panel_noticias"]


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara noticias_panel .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
