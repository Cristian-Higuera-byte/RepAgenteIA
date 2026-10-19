# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara mercados_panel .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada de la página Mercados.

Apunta al paquete `components/mercados/` (panel, secciones, ficha, gráfico, piezas, datos del bróker,
catálogo JSON y estilos) y reexporta de allí `renderizar_panel_mercados`, la función que dibuja la página. Existe
para que `from components.mercados_panel import renderizar_panel_mercados` (en `app.py`) siga
funcionando sin cambios. No contiene lógica propia.
"""
from components.mercados import renderizar_panel_mercados

__all__ = ["renderizar_panel_mercados"]


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara mercados_panel .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
