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

"""
Paquete de la barra lateral de navegación. API pública: `renderizar_barra_navegacion`
(la importa aplicacion.py). La lógica y los datos viven en barra.py; el CSS y el JS del toggle,
en estatico/ (barra_lateral.css / barra_lateral.js).

Este __init__ es una fachada: reexporta desde barra.py la función de dibujo, la lista de
ítems de navegación (`ITEMS`) y los anchos colapsado/expandido (`ANCHO_COLAPSADO`,
`ANCHO_EXPANDIDO`), para que otros módulos (p. ej. la barra superior y aplicacion.py)
los importen sin conocer la estructura interna del paquete.
"""
from .barra import ITEMS, ANCHO_COLAPSADO, ANCHO_EXPANDIDO, renderizar_barra_navegacion

# Nombres públicos del paquete
__all__ = ["renderizar_barra_navegacion", "ITEMS", "ANCHO_COLAPSADO", "ANCHO_EXPANDIDO"]


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
