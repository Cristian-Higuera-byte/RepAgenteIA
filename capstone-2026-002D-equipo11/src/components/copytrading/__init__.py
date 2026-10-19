# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Vista "Copy trading" (datos simulados).

    datos.py        estrategias (estrategias.json), categorías, pestañas de orden
    graficos.py     sparkline, dona y avatar en SVG
    tarjeta.py      tarjeta del listado
    ficha.py        ficha de detalle de una estrategia
    panel.py        renderizar_panel_copytrading(): listado + detalle
    estilos.css     estilos de la vista

Este archivo es la fachada del paquete: reexporta renderizar_panel_copytrading (definida
en panel.py) para que el resto de la plataforma muestre la vista con una sola importación.
La vista es una maqueta (MVP): no ejecuta operaciones reales de copia.
"""
# Reexporta la función pública de la vista.
from components.copytrading.panel import renderizar_panel_copytrading

# Nombres públicos del paquete.
__all__ = ["renderizar_panel_copytrading"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
