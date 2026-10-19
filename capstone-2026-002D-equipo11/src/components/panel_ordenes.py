# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara panel_ordenes .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada de los paneles del agente (historial y órdenes propuestas).

Apunta al paquete `components/agente_paneles/` (historial, propuestas, vigilancias, formato, estados
JSON y estilos) y reexporta de allí: `inyectar_estilos_agente` (inserta el CSS de los paneles),
`renderizar_historial_agente` (historial del agente), `renderizar_ordenes_propuestas` (órdenes que propone el
agente) y `cabecera_agente` (cabecera común, usada por el chat). Existe para que los imports de `app.py` y
del chat sigan funcionando sin cambios. No contiene lógica propia.
"""
from components.agente_paneles import (cabecera_agente, inyectar_estilos_agente, renderizar_historial_agente,
                                       renderizar_ordenes_propuestas)

__all__ = ["inyectar_estilos_agente", "renderizar_historial_agente", "renderizar_ordenes_propuestas", "cabecera_agente"]


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara panel_ordenes .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
