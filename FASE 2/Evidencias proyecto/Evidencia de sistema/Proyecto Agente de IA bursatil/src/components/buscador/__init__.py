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
Paquete del buscador de activos. API pública:
  - abrir_buscador / renderizar_buscador (patrón bandera + render en app.py).
  - _agregar_a_watchlist: lo reutiliza mercados_panel.py.
La lógica/datos viven en datos.py y el modal en dialogo.py.

Este __init__ es una fachada: reexporta esos nombres para que barra_superior, app.py
y mercados_panel.py importen todo desde `components.buscador`.
"""
from .dialogo import abrir_buscador, renderizar_buscador
from .datos import _agregar_a_watchlist, cargar_simbolos_broker

# Nombres públicos del paquete
__all__ = ["abrir_buscador", "renderizar_buscador", "_agregar_a_watchlist",
           "cargar_simbolos_broker"]


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
