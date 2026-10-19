# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara panel .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Panel del chat del agente: tarjeta con selector de perfil, «Nueva conversación», historial y caja de texto.

Compone los módulos hermanos: sesion (usuario y agente), historial (mensajes) y
turno_vivo (burbuja en curso). Es lo que importa la fachada del paquete chat.
"""
from __future__ import annotations

import streamlit as st

import configuracion
from components.chat.historial import (iniciar_conversacion, pintar_mensajes, reiniciar_conversacion,
                                       sincronizar_turno)
from components.chat.sesion import cambiar_perfil, obtener_agente, usuario_id
from components.panel_ordenes import cabecera_agente
from core import turnos


def renderizar_chat_agente() -> None:
    """Chat del agente. Va en la fila de abajo de app.py, junto al historial y las propuestas.

    Dibuja la tarjeta (contenedor agc_panel) con la cabecera común de los paneles del
    agente y el cuerpo del chat. No recibe parámetros ni devuelve nada.
    """
    with st.container(key="agc_panel"):   # tarjeta con el mismo estilo que el historial y las propuestas
        st.html(cabecera_agente(
            "smart_toy", "Agente IA Analítico",
            "Consola, gráficos e imágenes · mantiene el contexto y usa las herramientas de MT5",
        ))
        _chat_agente()


def _controles(agente, en_curso: bool) -> None:
    """Fila superior: selector de perfil y botón «Nueva conversación».

    Recibe el agente (o None si no se pudo crear) y `en_curso`, que deshabilita ambos
    controles mientras el agente responde. Al reiniciar, limpia la memoria del agente y
    la conversación visible, y relanza la app.
    """
    # Tres columnas: perfil, reinicio y un relleno que mantiene los controles compactos.
    col_perfil, col_reset, _relleno = st.columns([2, 2, 4])
    with col_perfil:
        # Perfiles disponibles definidos en configuracion.py.
        perfiles = list(getattr(configuracion, "PERFILES", []) or [])
        if agente is not None and perfiles:
            # Si el valor guardado no es válido, se parte del perfil del agente o del predeterminado.
            if st.session_state.get("perfil_agente") not in perfiles:
                actual = agente.perfil or getattr(configuracion, "PERFIL_POR_DEFECTO", None)
                st.session_state["perfil_agente"] = actual if actual in perfiles else perfiles[0]
            # Al cambiar la selección se aplica al agente mediante sesion.cambiar_perfil.
            st.selectbox(
                "Perfil", perfiles, key="perfil_agente", on_change=cambiar_perfil,
                label_visibility="collapsed", help="Perfil activo del agente", disabled=en_curso,
            )
    with col_reset:
        if st.button("Nueva conversación", icon=":material/refresh:", key="agc_nueva", width="stretch",
                     disabled=en_curso):
            if agente is not None:
                agente.reiniciar()
            reiniciar_conversacion()
            st.rerun()


def _entrada(uid: str, agente, error_agente: str, en_curso: bool, vistos) -> None:
    """Caja de texto: lanza el turno en segundo plano (o muestra el error si no hay agente).

    Parámetros: uid (id del usuario), agente (o None), error_agente (mensaje a mostrar si
    no hay agente), en_curso (deshabilita la caja) y vistos (conjunto de ids de turnos
    conocidos por la sesión). Efectos: añade mensajes a la conversación, inicia el turno en
    segundo plano con turnos.iniciar y relanza la app completa.
    """
    # Texto de ayuda de la caja según el estado.
    texto_guia = (
        "El agente está respondiendo… puedes moverte por la plataforma, te avisaremos"
        if en_curso else "Escribe tu consulta o pide un gráfico en imagen..."
    )
    if prompt_usuario := st.chat_input(texto_guia, disabled=en_curso):
        # Sin agente: se muestra la pregunta y el motivo del fallo como respuesta.
        if agente is None:
            st.session_state.mensajes_ui.append({"role": "user", "content": prompt_usuario})
            st.session_state.mensajes_ui.append({"role": "assistant", "content": error_agente})
        else:
            nuevo = turnos.iniciar(uid, agente, prompt_usuario)
            if nuevo is not None:   # None = ya había un turno en curso: no se duplica el mensaje
                st.session_state.mensajes_ui.append({"role": "user", "content": prompt_usuario})
                vistos.add(nuevo.id)
        st.rerun(scope="app")


def _chat_agente() -> None:
    """Cuerpo del chat: prepara usuario, agente y turno, y dibuja controles, mensajes y caja de texto.

    No recibe parámetros ni devuelve nada. El orden importa: primero se sincroniza el turno
    en segundo plano (puede añadir mensajes) y luego se dibujan los controles y el historial.
    """
    # --- ZONA DE CHAT INFERIOR: AGENTE (core.agente.Agente) ---
    # Identificación del usuario y conversación inicial.
    uid = usuario_id()
    iniciar_conversacion()
    agente, error_agente = obtener_agente()
    # Trae a la conversación lo ocurrido en segundo plano y dibuja cada bloque.
    turno, en_curso, vistos = sincronizar_turno(uid)
    _controles(agente, en_curso)
    pintar_mensajes(uid, turno, en_curso)
    _entrada(uid, agente, error_agente, en_curso, vistos)


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
