# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara sesion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Sesión del chat: quién es el usuario, qué agente usa y con qué perfil.

Guarda en st.session_state: usuario_info (datos del login), agente_ia (instancia del
Agente) y perfil_agente (perfil elegido en el selector). El agente se registra además en
core.turnos para que sobreviva a recargas de la página.
"""
from __future__ import annotations

import streamlit as st

from core import turnos
from core.agente import Agente  # type: ignore[import-untyped]

# Mensaje inicial del asistente al abrir o reiniciar la conversación.
SALUDO = (
    "¡Hola! Estoy listo. Pregúntame sobre cualquier activo, mercado o "
    "pídeme gráficos y su respectiva imagen renderizada."
)


def usuario_id() -> str:
    """Id del usuario con sesión iniciada: clave del turno en segundo plano y de las notificaciones.

    Devuelve el id como texto, o "local" si no hay sesión iniciada.
    """
    return str((st.session_state.get("usuario_info") or {}).get("id") or "local")


def obtener_agente():
    """Devuelve (agente, mensaje_error). Un agente por usuario: sobrevive a recargas de la página,
    así un turno en curso y la conversación no se pierden.

    Primero busca el agente en la sesión; si no está, lo recupera del registro de turnos y,
    en último caso, crea uno nuevo y lo registra. Devuelve una tupla (agente, mensaje_error):
    el mensaje es cadena vacía si todo salió bien, y el agente es None si no se pudo crear.
    """
    # 1) Agente ya asociado a esta sesión.
    agente = st.session_state.get("agente_ia")
    if agente is not None:
        return agente, ""
    # 2) Agente del usuario registrado antes (por ejemplo, tras recargar la página).
    uid = usuario_id()
    agente = turnos.agente_de(uid)
    # 3) Ninguno existe: se crea uno nuevo.
    if agente is None:
        try:
            agente = Agente(usuario_id="local")  # cambiar si el dashboard tiene login
        except Exception as e:
            return None, f"No se pudo iniciar el agente: {e}"
        turnos.registrar_agente(uid, agente)
    st.session_state["agente_ia"] = agente
    return agente, ""


def cambiar_perfil():
    """Callback del selector de perfil: aplica al agente el perfil elegido en st.session_state.perfil_agente.

    No hace nada si todavía no hay agente en la sesión.
    """
    agente = st.session_state.get("agente_ia")
    if agente is not None:
        agente.perfil = st.session_state["perfil_agente"]


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara sesion .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
