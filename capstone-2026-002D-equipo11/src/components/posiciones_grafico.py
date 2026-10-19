# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara posiciones_grafico .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada del trading desde el gráfico (posiciones, órdenes pendientes, TP/SL y clic derecho).

Apunta al paquete `components/posiciones/` (datos iniciales, gatillos y el JavaScript por fragmentos
en js/) y reexporta de allí `js_posiciones` (JS que se inserta dentro del gráfico) y `gatillos_cierre` (botones
invisibles que abren el modal de cierre). Existe para que
`from components.posiciones_grafico import gatillos_cierre, js_posiciones` de `grafico/panel.py` siga
funcionando sin cambios. No contiene lógica propia.
"""
from components.posiciones import gatillos_cierre, js_posiciones

__all__ = ["js_posiciones", "gatillos_cierre"]


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara posiciones_grafico .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
