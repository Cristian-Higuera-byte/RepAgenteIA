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
from componentes_plataforma.legal import nota_agente
from componentes_plataforma.refresco_fragmentos import fragmento_con_refresco, pedir_refresco
from componentes_plataforma.chat.limites import limites_agente
from componentes_plataforma.planes.panel import dialogo_bloqueo
from herramientas import cuota_ia, permisos_plan
from nucleo_agente import turnos


# TITULO RENDERIZAR CHAT AGENTE

def renderizar_chat_agente(sufijo: str = "", altura: int = 450, compacto: bool = False) -> None:
    """Chat del agente. Va en la fila de abajo de la vista de operar (sin parámetros) y, con sufijo, en el chat lateral y flotante.

    Dibuja la tarjeta (contenedor agente_chat_panel) con la cabecera común de los paneles del
    agente y el cuerpo del chat. Todas las copias comparten la misma conversación, el mismo agente y el mismo turno en curso; solo cambian las claves de los widgets.

    Parámetros: `sufijo` (texto que se suma a todas las claves; vacío en el chat de la fila de abajo, «_flot» en el lateral y flotante), `altura` (alto en px de la zona de
    mensajes) y `compacto` (controles en dos filas y sin la leyenda de la cabecera, para los paneles angostos). No devuelve nada.
    """
    with st.container(key=f"agente_chat_panel{sufijo}"):   # tarjeta con el mismo estilo que el historial y las propuestas
        if not compacto:
            st.html(cabecera_agente(
                "smart_toy", "Agente IA Analítico",
                f"Consola, gráficos e imágenes · mantiene el contexto y usa los datos de {NOMBRE_BROKER}",
            ))
        nota_agente()   # las respuestas no son asesoría financiera
        # El chat es un fragmento: escribir, enviar, detener o reiniciar solo reejecutan el chat, no la página. Su clave («chat» o «chat_flot») permite refrescarlo desde fuera.
        fragmento_con_refresco(f"chat{sufijo}", _chat_agente, sufijo, altura, compacto)


# TITULO CONTROLES

def _controles(agente, en_curso: bool, sufijo: str = "", compacto: bool = False) -> None:
    """Fila superior: selector de perfil, botón «Nueva conversación» y límites del agente.

    Recibe el agente (o None si no se pudo crear) y `en_curso`, que deshabilita ambos
    controles mientras el agente responde. Al reiniciar, limpia la memoria del agente y
    la conversación visible, y relanza la app. `sufijo` se suma a las claves de los widgets y `compacto` los reparte en dos filas (perfil arriba; reinicio y límites
    abajo), porque en el chat lateral y flotante no caben en una sola.
    """
    clave_perfil = f"perfil_agente{sufijo}"
    if compacto:
        # Dos filas: el selector de perfil solo, y debajo «Nueva conversación» y «Límites».
        columna_perfil = st.columns(1)[0]   # una columna, para que el selector tenga el mismo margen lateral que las demás filas
        columna_reiniciar, columna_limites = st.columns(2)
    else:
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
            if st.session_state.get(clave_perfil) not in validos:
                actual = agente.perfil or getattr(configuracion, "PERFIL_POR_DEFECTO", None)
                st.session_state[clave_perfil] = actual if actual in validos else validos[0]
            # Si el agente quedó con un perfil que el plan ya no incluye (por ejemplo tras bajar de plan), pasa al elegido.
            if agente.perfil not in validos:
                agente.perfil = st.session_state[clave_perfil]
            # Las copias del chat comparten agente: si otra copia cambió el perfil, este selector lo refleja.
            elif st.session_state[clave_perfil] != agente.perfil:
                st.session_state[clave_perfil] = agente.perfil
            # Al cambiar la selección se aplica al agente mediante sesion.cambiar_perfil.
            st.selectbox(
                "Perfil", perfiles, key=clave_perfil, on_change=cambiar_perfil, args=(clave_perfil,),
                format_func=lambda p: p if p in validos else f"🔒 {p}",
                label_visibility="collapsed", help="Perfil activo del agente", disabled=en_curso,
            )
    with columna_limites:
        limites_agente(sufijo)
    with columna_reiniciar:
        if st.button("Nueva conversación", icon=":material/refresh:", key=f"agente_chat_nueva{sufijo}", width="stretch",
                     disabled=en_curso):
            if agente is not None:
                agente.reiniciar()
            reiniciar_conversacion()
            st.session_state["_chat_sincronizar"] = True   # las demás copias del chat se ponen al día en la próxima pasada
            _reejecutar()


# TITULO ENTRADA

def _entrada(uid: str, agente, error_agente: str, en_curso: bool, vistos, agotada: bool = False, sufijo: str = "") -> None:
    """Caja de texto: lanza el turno en segundo plano (o muestra el error si no hay agente).

    Parámetros: uid (id del usuario), agente (o None), error_agente (mensaje a mostrar si
    no hay agente), en_curso (deshabilita la caja), vistos (conjunto de ids de turnos
    conocidos por la sesión) y agotada (la cuota de tokens del mes se acabó: la caja queda deshabilitada y lo dice). Efectos: añade mensajes a la conversación, inicia el turno en
    segundo plano con turnos.iniciar y relanza la app completa. `sufijo` da clave propia a la caja de texto de las copias del chat que no son la de la fila de abajo.
    """
    # Texto de ayuda de la caja según el estado.
    texto_guia = (
        "Alcanzaste el límite de tokens de tu plan esta semana" if agotada else
        "El agente está respondiendo… puedes moverte por la plataforma, te avisaremos"
        if en_curso else "Escribe tu consulta o pide un gráfico en imagen..."
    )
    # La caja de la fila de abajo no lleva clave (como siempre); las demás copias necesitan una propia para no repetir el id del widget.
    opciones = {"key": f"agente_chat_entrada{sufijo}"} if sufijo else {}
    if prompt_usuario := st.chat_input(texto_guia, disabled=en_curso or agotada, **opciones):
        # Sin agente: se muestra la pregunta y el motivo del fallo como respuesta.
        if agente is None:
            st.session_state.mensajes_ui.append({"role": "user", "content": prompt_usuario})
            st.session_state.mensajes_ui.append({"role": "assistant", "content": error_agente})
        else:
            nuevo = turnos.iniciar(uid, agente, prompt_usuario)
            if nuevo is not None:   # None = ya había un turno en curso: no se duplica el mensaje
                st.session_state.mensajes_ui.append({"role": "user", "content": prompt_usuario})
                vistos.add(nuevo.id)
        st.session_state["_chat_sincronizar"] = True       # las demás copias del chat se ponen al día en la próxima pasada
        _reejecutar()


# TITULO REEJECUTAR

def _reejecutar() -> None:
    """Vuelve a dibujar SOLO el chat (su fragmento) después de enviar un mensaje o reiniciar la conversación; si por alguna razón no corre como fragmento, reejecuta la
    página completa como antes."""
    try:
        st.rerun(scope="fragment")
    except st.errors.StreamlitAPIException:
        st.rerun(scope="app")


# TITULO CHAT AGENTE

def _chat_agente(sufijo: str = "", altura: int = 450, compacto: bool = False) -> None:
    """Cuerpo del chat: prepara usuario, agente y turno, y dibuja controles, mensajes y caja de texto.

    Recibe el sufijo de las claves, el alto de la zona de mensajes y si los controles van compactos. No devuelve nada. El orden importa: primero se sincroniza el turno
    en segundo plano (puede añadir mensajes) y luego se dibujan los controles y el historial.
    """
    # Si otra pasada pidió poner al día las demás copias del chat (se envió un mensaje o se reinició la conversación), se les pide su refresco.
    if st.session_state.pop("_chat_sincronizar", False):
        pedir_refresco("chat_flot" if not sufijo else "chat")
    # --- ZONA DE CHAT INFERIOR: AGENTE (nucleo_agente.agente.Agente) ---
    # Identificación del usuario y conversación inicial.
    uid = usuario_id()
    iniciar_conversacion()
    agente, error_agente = obtener_agente()
    # Trae a la conversación lo ocurrido en segundo plano y dibuja cada bloque.
    turno, en_curso, vistos = sincronizar_turno(uid)
    cuota = cuota_ia.estado()      # tokens gastados este mes sobre el total del plan (se actualiza al terminar cada consulta)
    barra_cuota(cuota, sufijo)
    _controles(agente, en_curso, sufijo, compacto)
    pintar_mensajes(uid, turno, en_curso, sufijo, altura)
    _entrada(uid, agente, error_agente, en_curso, vistos, cuota["agotada"], sufijo)


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
