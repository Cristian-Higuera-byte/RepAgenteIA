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
Paquete de la Cartera (posiciones abiertas). API pública (la importa app.py):
  - renderizar_cartera_lista: la lista (va dentro de un fragmento en vivo).
  - renderizar_modal_cerrar: el modal de confirmación de cierre (fuera de los fragmentos).
Submódulos internos: comun (helpers + CSS) · lista · modal · detalle (+ estatico/).

Este archivo es la fachada del paquete: reexporta únicamente las dos funciones que
necesita el resto de la plataforma, de modo que quien importe el paquete no dependa
de la organización interna en submódulos.
"""
# Reexporta la lista de posiciones abiertas (definida en lista.py).
from .lista import renderizar_cartera_lista
# Reexporta el modal de confirmación de cierre (definido en modal.py).
from .modal import renderizar_modal_cerrar

# Nombres públicos del paquete (lo que expone "from cartera_panel import *").
__all__ = ["renderizar_cartera_lista", "renderizar_modal_cerrar"]


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
