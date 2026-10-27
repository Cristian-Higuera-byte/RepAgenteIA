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

"""Chat del agente de IA (core.agente.Agente): conversación, turno en segundo plano y botón de detener.

Va en la fila de abajo de app.py, junto al historial y las órdenes propuestas.

    sesion.py        id de usuario, creación/recuperación del agente, cambio de perfil, saludo inicial
    historial.py     sincroniza el turno en curso con la conversación y pinta los mensajes
    turno_vivo.py    burbuja de la respuesta que se está escribiendo (cronómetro + botón Detener)
    panel.py         renderizar_chat_agente(): tarjeta con controles, historial y caja de texto

Este archivo es la fachada del paquete: reexporta solo renderizar_chat_agente (definida
en panel.py) para que app.py importe el chat con una sola línea sin conocer los
submódulos internos.
"""
# Reexporta la función pública del panel del chat.
from components.chat.panel import renderizar_chat_agente

# Nombres públicos del paquete.
__all__ = ["renderizar_chat_agente"]


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
