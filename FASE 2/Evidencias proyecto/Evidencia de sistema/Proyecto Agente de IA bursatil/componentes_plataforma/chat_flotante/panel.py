# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara panel .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Dibujo del chat flotante: burbuja inferior derecha, panel del chat y el script que los abre y cierra.

Contenedores con clave que el CSS y el JS buscan: `pj_chat_burbuja` (el botón redondo), `pj_chat_flotante` (el panel) y `pj_chat_js` (el script). La clase `pj-chat-abierto` en <html>
abre el panel como ventana flotante; en Trading y Cartera la clase `pj-panel-agente` (del rail) lo acopla al panel derecho (ver riel/estilos.css).
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from componentes_plataforma._estaticos import estilos, texto
from componentes_plataforma.chat import renderizar_chat_agente
from componentes_plataforma.chat.sesion import usuario_id
from componentes_plataforma.refresco_fragmentos import botones_refresco
from nucleo_agente import turnos

# Sufijo de las claves del chat de este panel: distingue sus widgets de los del chat de la fila de abajo de Trading y Cartera.
SUFIJO = "_flot"
# Alto de la zona de mensajes cuando el CSS no la ajusta (el CSS la estira al alto del panel).
ALTURA_BASE = 320
# Vistas donde ya se inyectó el CSS de los paneles del agente (lo hace la vista de operar).
_VISTAS_CON_ESTILOS = ("trading", "portafolio")

# Script ya envuelto en script, listo para `components.html`; se lee al importar el módulo.
_JS = "\n<script>\n" + texto(Path(__file__).parent / "flotante.js") + "</script>\n"


# TITULO RENDERIZAR CHAT FLOTANTE

def renderizar_chat_flotante() -> None:
    """Dibuja la burbuja del agente y su panel de chat. Se llama una vez por ejecución, al final de la página, para todas las vistas.

    Efectos: escribe el CSS del chat flotante (y el de los paneles del agente si la vista no lo trajo ya), el botón de la burbuja, el panel con el chat completo y el script que
    lo abre y cierra. No recibe parámetros ni devuelve nada."""
    st.markdown(estilos(Path(__file__).parent / "estilos.css"), unsafe_allow_html=True)
    if st.session_state.get("navegacion_activo") not in _VISTAS_CON_ESTILOS:
        from componentes_plataforma.agente_paneles import inyectar_estilos_agente
        inyectar_estilos_agente()
    # Turno del agente en curso: la burbuja pulsa mientras responde, aunque el panel esté cerrado.
    turno = turnos.turno_de(usuario_id())
    ocupado = turno is not None and not turno.terminado
    with st.container(key="pj_chat_burbuja"):
        st.button(":material/smart_toy:", key="chat_burbuja_abrir")
        if ocupado:
            st.html("<span class='pj-chat-ocupado'></span>")
    with st.container(key="pj_chat_flotante"):
        st.html("<div class='pj-chat-titulo'><span class='agente-icono-material'>smart_toy</span><b>Agente IA</b></div>")
        st.button(":material/close:", key="chat_cerrar")
        renderizar_chat_agente(SUFIJO, altura=ALTURA_BASE, compacto=True)
    with st.container(key="pj_chat_js"):
        components.html(_JS, height=0, width=0)
    botones_refresco()   # botones sin presencia con los que el agente refresca el chat, sus paneles y la campana sin reiniciar la página


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara panel .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
