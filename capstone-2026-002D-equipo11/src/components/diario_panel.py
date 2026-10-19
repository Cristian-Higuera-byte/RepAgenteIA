# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara diario_panel .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada de la vista Diario (journal de operaciones).

Apunta al paquete `components/diario/` (tabla, ficha, mini-gráfico, datos y estilos) y reexporta de allí
`renderizar_panel_journal`, la función que dibuja la vista. Existe para que
`from components.diario_panel import renderizar_panel_journal` (en `app.py`) siga funcionando
sin cambios. No contiene lógica propia.
"""
from components.diario import renderizar_panel_journal

__all__ = ["renderizar_panel_journal"]


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara diario_panel .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
