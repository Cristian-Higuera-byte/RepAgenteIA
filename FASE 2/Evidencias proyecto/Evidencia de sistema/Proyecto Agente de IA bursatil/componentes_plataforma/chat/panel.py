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

"""Panel del chat del agente: tarjeta con selector de perfil, «Nueva conversación», límites del agente, historial y caja de texto.

Compone los módulos hermanos: sesion (usuario y agente), historial (mensajes),
turno_vivo (burbuja en curso) y cuota (barra del uso mensual de tokens). Es lo que importa la fachada del paquete chat.
"""
from __future__ import annotations

import streamlit as st

import configuracion
from herramientas.puente_mt5 import NOMBRE_BROKER
from componentes_plataforma.chat.historial import (iniciar_conversacion, pintar_mensajes, reiniciar_conversacion,
                                       sincronizar_turno)
from componentes_plataforma.chat.sesion import cambiar_perfil, obtener_agente, usuario_id
from componentes_plataforma.agente_paneles import cabecera_agente
from componentes_plataforma.chat.cuota import barra_cuota
from componentes_plataforma.chat.limites import limites_agente
from componentes_plataforma.planes.panel import dialogo_bloqueo
from herramientas import cuota_ia, permisos_plan
from nucleo_agente import turnos


# TITULO RENDERIZAR CHAT AGENTE

def renderizar_chat_agente() -> None:
    """Chat del agente. Va en la fila de abajo de aplicacion.py, junto al historial y las propuestas.

    Dibuja la tarjeta (contenedor agente_chat_panel) con la cabecera común de los paneles del
    agente y el cuerpo del chat. No recibe parámetros ni devuelve nada.
    """
    with st.container(key="agente_chat_panel"):   # tarjeta con el mismo estilo que el historial y las propuestas
        st.html(cabecera_agente(
            "smart_toy", "Agente IA Analítico",
            f"Consola, gráficos e imágenes · mantiene el contexto y usa los datos de {NOMBRE_BROKER}",
        ))
        _chat_agente()


# TITULO CONTROLES

def _controles(agente, en_curso: bool) -> None:
    """Fila superior: selector de perfil y botón «Nueva conversación».

    Recibe el agente (o None si no se pudo crear) y `en_curso`, que deshabilita ambos
    controles mientras el agente responde. Al reiniciar, limpia la memoria del agente y
    la conversación visible, y relanza la app.
    """
    # Cuatro columnas: perfil, reinicio, límites del agente y un relleno que mantiene los controles compactos.
    columna_perfil, columna_reiniciar, columna_limites, _relleno = st.columns([2, 2, 2, 2])
    with columna_perfil:
        # Perfiles disponibles definidos en configuracion.py.
        perfiles = list(getattr(configuracion, "PERFILES", []) or [])
        # Solo los perfiles que incluye el plan del usuario (el «profundo» usa el modelo avanzado y viene desde el plan Pro).
        permitidos = permisos_plan.valor("perfiles_ia")
        # Los perfiles que el plan no incluye se muestran con candado; al elegirlos, `cambiar_perfil` los rechaza y se abre el aviso.
        if permitidos:
            perfiles = [p for p in perfiles if p in permitidos] + [p for p in perfiles if p not in permitidos]
        validos = [p for p in perfiles if not permitidos or p in permitidos] or perfiles
        if st.session_state.pop("bloqueo_pendiente", None):
            dialogo_bloqueo("perfiles_ia")
        if agente is not None and perfiles:
            # Si el valor guardado no es válido, se parte del perfil del agente o del predeterminado.
            if st.session_state.get("perfil_agente") not in validos:
                actual = agente.perfil or getattr(configuracion, "PERFIL_POR_DEFECTO", None)
                st.session_state["perfil_agente"] = actual if actual in validos else validos[0]
            # Si el agente quedó con un perfil que el plan ya no incluye (por ejemplo tras bajar de plan), pasa al elegido.
            if agente.perfil not in validos:
                agente.perfil = st.session_state["perfil_agente"]
            # Al cambiar la selección se aplica al agente mediante sesion.cambiar_perfil.
            st.selectbox(
                "Perfil", perfiles, key="perfil_agente", on_change=cambiar_perfil,
                format_func=lambda p: p if p in validos else f"🔒 {p}",
                label_visibility="collapsed", help="Perfil activo del agente", disabled=en_curso,
            )
    with columna_limites:
        limites_agente()
    with columna_reiniciar:
        if st.button("Nueva conversación", icon=":material/refresh:", key="agente_chat_nueva", width="stretch",
                     disabled=en_curso):
            if agente is not None:
                agente.reiniciar()
            reiniciar_conversacion()
            st.rerun()


# TITULO ENTRADA

def _entrada(uid: str, agente, error_agente: str, en_curso: bool, vistos, agotada: bool = False) -> None:
    """Caja de texto: lanza el turno en segundo plano (o muestra el error si no hay agente).

    Parámetros: uid (id del usuario), agente (o None), error_agente (mensaje a mostrar si
    no hay agente), en_curso (deshabilita la caja), vistos (conjunto de ids de turnos
    conocidos por la sesión) y agotada (la cuota de tokens del mes se acabó: la caja queda deshabilitada y lo dice). Efectos: añade mensajes a la conversación, inicia el turno en
    segundo plano con turnos.iniciar y relanza la app completa.
    """
    # Texto de ayuda de la caja según el estado.
    texto_guia = (
        "Alcanzaste el límite de tokens de tu plan este mes" if agotada else
        "El agente está respondiendo… puedes moverte por la plataforma, te avisaremos"
        if en_curso else "Escribe tu consulta o pide un gráfico en imagen..."
    )
    if prompt_usuario := st.chat_input(texto_guia, disabled=en_curso or agotada):
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


# TITULO CHAT AGENTE

def _chat_agente() -> None:
    """Cuerpo del chat: prepara usuario, agente y turno, y dibuja controles, mensajes y caja de texto.

    No recibe parámetros ni devuelve nada. El orden importa: primero se sincroniza el turno
    en segundo plano (puede añadir mensajes) y luego se dibujan los controles y el historial.
    """
    # --- ZONA DE CHAT INFERIOR: AGENTE (nucleo_agente.agente.Agente) ---
    # Identificación del usuario y conversación inicial.
    uid = usuario_id()
    iniciar_conversacion()
    agente, error_agente = obtener_agente()
    # Trae a la conversación lo ocurrido en segundo plano y dibuja cada bloque.
    turno, en_curso, vistos = sincronizar_turno(uid)
    cuota = cuota_ia.estado()      # tokens gastados este mes sobre el total del plan (se actualiza al terminar cada consulta)
    barra_cuota(cuota)
    _controles(agente, en_curso)
    pintar_mensajes(uid, turno, en_curso)
    _entrada(uid, agente, error_agente, en_curso, vistos, cuota["agotada"])


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
