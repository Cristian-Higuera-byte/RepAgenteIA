# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara profundidad_panel .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada del panel de PROFUNDIDAD DE MERCADO (DOM).

Apunta al paquete `components/profundidad_mercado/` (panel, escalera y estilos) y reexporta de allí
`renderizar_panel_dom`, la función que dibuja el panel. Existe para que
`from components.profundidad_panel import renderizar_panel_dom` siga funcionando sin cambios. No
contiene lógica propia.
"""
from components.profundidad_mercado import renderizar_panel_dom

__all__ = ["renderizar_panel_dom"]


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara profundidad_panel .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
