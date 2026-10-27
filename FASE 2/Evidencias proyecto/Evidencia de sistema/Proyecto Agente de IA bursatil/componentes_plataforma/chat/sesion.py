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

Guarda en st.session_state: usuario_informacion (datos del login), agente_ia (instancia del
Agente) y perfil_agente (perfil elegido en el selector). El agente se registra además en
nucleo_agente.turnos para que sobreviva a recargas de la página.
"""
from __future__ import annotations

import streamlit as st

from herramientas import permisos_plan
from nucleo_agente import turnos
from nucleo_agente.agente import Agente  # type: ignore[import-untyped]

# Mensaje inicial del asistente al abrir o reiniciar la conversación.
SALUDO = (
    "¡Hola! Estoy listo. Pregúntame sobre cualquier activo, mercado o "
    "pídeme gráficos y su respectiva imagen renderizada."
)


# TITULO USUARIO ID

def usuario_id() -> str:
    """Id del usuario con sesión iniciada: clave del turno en segundo plano y de las notificaciones.

    Devuelve el id como texto, o "local" si no hay sesión iniciada.
    """
    return str((st.session_state.get("usuario_informacion") or {}).get("id") or "local")


# TITULO OBTENER AGENTE

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


# TITULO CAMBIAR PERFIL

def cambiar_perfil():
    """Callback del selector de perfil: aplica al agente el perfil elegido en st.session_state.perfil_agente.

    Si el perfil elegido no lo incluye el plan del usuario, lo devuelve al anterior y deja en `bloqueo_pendiente` la función bloqueada para que
    el panel abra el aviso con el acceso a Planes. No hace nada si todavía no hay agente en la sesión.
    """
    agente = st.session_state.get("agente_ia")
    # Un perfil con candado (que el plan no incluye) no se aplica: se vuelve al anterior y se pide abrir el aviso del plan.
    elegido = st.session_state["perfil_agente"]
    permitidos = permisos_plan.valor("perfiles_ia")
    if permitidos and elegido not in permitidos:
        st.session_state["perfil_agente"] = agente.perfil if agente is not None and agente.perfil in permitidos else permitidos[0]
        st.session_state["bloqueo_pendiente"] = "perfiles_ia"
        return
    if agente is not None:
        agente.perfil = elegido


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
