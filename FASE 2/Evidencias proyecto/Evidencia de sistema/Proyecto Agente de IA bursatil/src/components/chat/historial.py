# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara historial .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Historial del chat: une el turno en segundo plano con la conversación de la sesión y pinta los mensajes.

La conversación visible vive en st.session_state.mensajes_ui (lista de diccionarios con
role, content y opcionalmente herramientas, imagenes y pie). El turno del agente corre en
un hilo aparte (core.turnos); este módulo sincroniza ambos y dibuja el resultado.
"""
from __future__ import annotations

import os

import streamlit as st

from components.chat.sesion import SALUDO
from components.chat.turno_vivo import burbuja_en_vivo
from core import turnos


def iniciar_conversacion() -> None:
    """Crea la conversación de la sesión con el saludo inicial si todavía no existe.

    Efecto: inicializa st.session_state.mensajes_ui. No hace nada si ya está creada.
    """
    # Solo se siembra el saludo la primera vez que se abre el chat en esta sesión.
    if "mensajes_ui" not in st.session_state:
        st.session_state.mensajes_ui = [{"role": "assistant", "content": SALUDO}]


def reiniciar_conversacion() -> None:
    """Descarta los mensajes de la sesión y deja solo el saludo inicial (botón "Nueva conversación")."""
    st.session_state.mensajes_ui = [{"role": "assistant", "content": SALUDO}]


def sincronizar_turno(uid: str):
    """El turno del agente corre en segundo plano (core/turnos.py): no se corta al cambiar de sección.
    Trae a la conversación lo que pasó mientras no mirabas. Devuelve (turno, en_curso, vistos).

    Parámetro: uid, el id del usuario con el que se registró el turno. Devuelve una tupla
    con el turno del usuario (o None), un booleano que indica si sigue en curso y el
    conjunto de ids de turnos ya vistos por esta sesión. Efectos: puede añadir mensajes a
    st.session_state.mensajes_ui y marcar el turno como recogido en core.turnos.
    """
    # Turno actual del usuario y estado; "vistos" evita duplicar la pregunta en la conversación.
    turno = turnos.turno_de(uid)
    en_curso = turno is not None and not turno.terminado
    vistos = st.session_state.setdefault("_turnos_vistos", set())
    # Caso 1: turno desconocido para esta sesión (recarga de página): se repone la pregunta.
    if turno is not None and turno.id not in vistos and (en_curso or not turno.recogido):
        # Turno que esta sesión no conocía (p. ej. recargaste la página): se muestra su pregunta.
        st.session_state.mensajes_ui.append({"role": "user", "content": turno.prompt})
        vistos.add(turno.id)
    # Caso 2: el turno terminó y su respuesta aún no se incorporó a la conversación.
    if turno is not None and turno.terminado and not turno.recogido:
        # Terminó mientras estabas en otra sección: la respuesta pasa al chat y su aviso queda leído.
        st.session_state.mensajes_ui.append({
            "role": "assistant", "content": turno.respuesta_final(),
            "herramientas": list(turno.herramientas), "imagenes": list(turno.imagenes), "pie": turno.pie,
        })
        turnos.recoger(uid, turno.id)
    return turno, en_curso, vistos


def pintar_mensajes(uid: str, turno, en_curso: bool) -> None:
    """Zona con scroll: mensajes guardados y, si hay un turno en curso, su burbuja en vivo.

    Parámetros: uid (id del usuario), turno (turno actual o None) y en_curso (si el agente
    sigue respondiendo). Dibuja cada mensaje con texto, imágenes existentes en disco y pie.
    No devuelve nada.
    """
    # Contenedor de altura fija con scroll (clave agc_scroll, estilizada en el CSS del chat).
    contenedor_chat_central = st.container(height=450, border=False, key="agc_scroll")
    with contenedor_chat_central:
        # Mensajes ya guardados, con sus imágenes (solo si el archivo todavía existe) y pie.
        for mensaje in st.session_state.mensajes_ui:
            with st.chat_message(mensaje["role"]):
                st.markdown(mensaje["content"])
                for ruta in mensaje.get("imagenes", []):
                    if os.path.isfile(ruta):
                        st.image(ruta, use_container_width=True)
                if mensaje.get("pie"):
                    st.caption(mensaje["pie"])
        # Respuesta en construcción, que se refresca sola cada segundo.
        if en_curso and turno is not None:
            burbuja_en_vivo(uid, turno.id)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara historial .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
