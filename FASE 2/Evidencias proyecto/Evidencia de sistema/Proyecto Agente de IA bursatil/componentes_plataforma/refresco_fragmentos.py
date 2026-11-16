# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara refresco_fragmentos .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

"""Refresco de un bloque de la página sin reejecutar toda la página.

Streamlit solo reejecuta un fragmento por una interacción dentro de él; desde un hilo, un temporizador u otro fragmento no hay forma directa. Aquí se resuelve con el
mecanismo oficial de la versión actual: cada fragmento lleva una clave y unos botones sin presencia (uno por grupo de fragmentos) cuyo `on_click` llama a `st.rerun(claves)`,
que reejecuta SOLO esos fragmentos y todos juntos en una misma pasada. Un pequeño script (`pedir_refresco`) pulsa el botón del grupo y el navegador lo trata como un clic del
usuario. Así el agente puede responder, proponer o avisar y los paneles se actualizan sin reiniciar la plataforma.

  * `fragmento_con_refresco(clave, funcion, *args, **opciones)`: dibuja `funcion` como fragmento con esa clave (y lo anota como presente en esta pasada).
  * `botones_refresco()`: dibuja los botones sin presencia de cada grupo; se llama una vez por pasada completa, al final de la página.
  * `pedir_refresco(grupo, marca="")`: pide el refresco de un grupo (`GRUPOS`) desde cualquier punto de la página.
El CSS que oculta los botones vive en chat_flotante/estilos.css (clases st-key-pj_refrescar_*)."""
import json
import time

import streamlit as st
import streamlit.components.v1 as components

# Grupos de fragmentos que se pueden refrescar: nombre -> claves. «todo_agente» es lo que se refresca al terminar un turno del agente: el chat de la fila de abajo, el chat
# flotante, el historial, las órdenes propuestas y la campana de avisos.
GRUPOS = {
    "chat": ("chat",),
    "chat_flot": ("chat_flot",),
    "campana": ("campana",),
    "todo_agente": ("chat", "chat_flot", "agente_historial", "agente_propuestas", "campana"),
}
# Clave de session_state con los fragmentos dibujados en la última pasada completa (se vacía al empezar cada una).
_VIVOS = "_fragmentos_vivos"


# TITULO INICIAR PASADA

def iniciar_pasada() -> None:
    """Vacía la lista de fragmentos presentes; se llama al empezar cada pasada completa de la página."""
    st.session_state[_VIVOS] = set()


# TITULO FRAGMENTO CON REFRESCO

def fragmento_con_refresco(clave: str, funcion, *args, **opciones) -> None:
    """Dibuja `funcion(*args, **opciones)` como fragmento con la clave `clave` y lo anota como presente en esta pasada.

    Las interacciones dentro del fragmento (escribir, pulsar) solo reejecutan el fragmento, no la página, y `pedir_refresco` puede reejecutarlo desde fuera."""
    st.session_state.setdefault(_VIVOS, set()).add(clave)
    st.fragment(key=clave)(lambda: funcion(*args, **opciones))()


# TITULO AL PULSAR

def _al_pulsar(grupo: str) -> None:
    """`on_click` del botón de un grupo: reejecuta solo los fragmentos del grupo que están en la página (si ninguno lo está, no hace nada)."""
    vivos = st.session_state.get(_VIVOS, set())
    claves = [c for c in GRUPOS[grupo] if c in vivos]
    if claves:
        st.rerun(claves)


# TITULO BOTONES REFRESCO

def botones_refresco() -> None:
    """Dibuja los botones sin presencia, uno por grupo (clave `pj_refrescar_<grupo>`). Va una vez por pasada completa, al final de la página, para que existan en todas las vistas."""
    for grupo in GRUPOS:
        st.button("↻", key=f"pj_refrescar_{grupo}", on_click=_al_pulsar, args=(grupo,))


# TITULO PEDIR REFRESCO

def pedir_refresco(grupo: str, marca: str = "") -> None:
    """Pide el refresco del grupo `grupo`: dibuja un script sin tamaño que pulsa su botón.

    `marca` distingue una petición de otra: con la misma marca el script no se vuelve a ejecutar (así un fragmento que se repite cada segundo no pide el refresco cada
    vez); sin marca se usa la hora, y cada llamada pulsa el botón. No devuelve nada."""
    marca = marca or str(time.time())
    selector = json.dumps(f".st-key-pj_refrescar_{grupo} button")
    components.html(
        f"<script>/*{marca}*/(function(){{var b=window.parent.document.querySelector({selector});if(b)b.click();}})();</script>",
        height=0, width=0,
    )


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara refresco_fragmentos .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
