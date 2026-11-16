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
Paquete del ticket de órdenes (Order Entry). La API pública es `renderizar_panel_orden`,
que importa componentes_plataforma/riel/; el resto son submódulos internos del paquete:
  panel · cuenta · ejecucion · confirmacion · calculadora · avisos · interfaz (+ estatico/).

Este `__init__` es una fachada: reexporta `renderizar_panel_orden` para que se importe directamente
desde `componentes_plataforma.panel_orden`.
"""
# Fachada: reexporta la función que dibuja el ticket completo
from .panel import renderizar_panel_orden

# Nombres públicos del paquete
__all__ = ["renderizar_panel_orden"]


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
