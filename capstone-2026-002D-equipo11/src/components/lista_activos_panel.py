# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara lista_activos_panel .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada de la lista de activos (watchlist).

Apunta al paquete `components/lista_activos/` (panel, fila, acciones y estilos) y reexporta de allí
`renderizar_watchlist` (dibuja la lista) y `ALTURA_LISTA` (altura fija de la lista en píxeles). Existe para que
`from components.lista_activos_panel import renderizar_watchlist` (en `app.py`) siga
funcionando sin cambios. No contiene lógica propia.
"""
from components.lista_activos import ALTURA_LISTA, renderizar_watchlist

__all__ = ["renderizar_watchlist", "ALTURA_LISTA"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara lista_activos_panel .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
