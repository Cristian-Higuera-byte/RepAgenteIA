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
componentes_plataforma/lista_activos
------------------------
Lista de activos (watchlist) del panel izquierdo: tarjetas con ícono, precio y variación en vivo (feed),
selección de activo, favoritos y quitar de la lista.
Archivos: panel.py, fila.py, acciones.py, estilos.py + estilos.css.

Este `__init__` es una fachada: reexporta `renderizar_watchlist` (dibuja el panel) y `ALTURA_LISTA`
(altura en píxeles de la zona con scroll) para que el resto del dashboard importe desde
`componentes_plataforma.lista_activos`.
"""
# Función de dibujo del panel y constante de altura.
from componentes_plataforma.lista_activos.panel import ALTURA_LISTA, renderizar_watchlist

# API pública del paquete.
__all__ = ["renderizar_watchlist", "ALTURA_LISTA"]


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
