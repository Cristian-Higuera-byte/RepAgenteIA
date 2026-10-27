# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara chat_agente .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada del chat del agente de IA.

Apunta al paquete `components/chat/` (sesión, historial, turno en vivo y panel) y reexporta de allí
`renderizar_chat_agente`, la función que dibuja el chat del agente. Existe para que
`from components.chat_agente import renderizar_chat_agente` (usado por `central_panel.py` y
`app.py`) siga funcionando sin cambios. No contiene lógica propia.
"""
from components.chat import renderizar_chat_agente

__all__ = ["renderizar_chat_agente"]


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara chat_agente .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
