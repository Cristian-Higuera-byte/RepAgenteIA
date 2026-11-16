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
componentes_plataforma/chat_flotante
------------------------------------
Chat del agente siempre a mano: una burbuja fija en la esquina inferior derecha, visible en TODAS las secciones (Inicio, Trading, Cartera, Noticias…), que al tocarla
abre el chat del agente con todas sus funciones (perfil, nueva conversación, límites, cuota, historial, imágenes y botón Detener).

Es la misma conversación, el mismo agente y el mismo turno en segundo plano que el chat de la fila de abajo de Trading y Cartera (componentes_plataforma/chat); solo cambian
las claves de los widgets (sufijo «_flot»). En Trading y Cartera el mismo panel también se acopla al rail derecho con su botón «Agente IA» (ver riel/).

El panel se dibuja SIEMPRE y se abre o se cierra con una clase en <html> (`pj-chat-abierto`) puesta por `flotante.js`, sin reejecutar Python: aparece al instante, como los
paneles del rail.

Archivos: panel.py (dibuja burbuja, panel y script), estilos.css (los 8 cortes de pantalla de la empresa), flotante.js (abre, cierra y baja el scroll).
"""
from componentes_plataforma.chat_flotante.panel import renderizar_chat_flotante

__all__ = ["renderizar_chat_flotante"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara __init__ .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
