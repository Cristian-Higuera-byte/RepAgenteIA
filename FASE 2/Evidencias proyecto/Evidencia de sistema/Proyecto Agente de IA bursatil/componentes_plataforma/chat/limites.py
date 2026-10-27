# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara limites .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Límites del agente: ventana donde el usuario decide con cuánto riesgo puede operar el agente.

Muestra los límites que el usuario puede definir (riesgo máximo por operación y total, pérdida diaria máxima, volumen máximo por orden, apalancamiento máximo y posiciones
abiertas máximas) y los guarda con `nucleo_agente.ordenes.guardar_limites`. Un valor en 0 significa «sin límite», que es lo que hay por defecto: el agente opera con el riesgo que el
usuario le pida y la responsabilidad de ese riesgo es del usuario. El agente y las vigilancias automáticas respetan los límites que haya definido. Solo se opera en cuenta demo.
"""
import streamlit as st

from nucleo_agente import ordenes

# Aviso de la última acción (se muestra una vez)
_CLAVE_AVISO = "agente_limites_aviso"
# Texto de ayuda de cada límite
_AYUDAS = {
    "riesgo_max_por_operacion_pct": "Lo máximo que puedes perder en una operación si salta el stop loss, como % de tu equity.",
    "riesgo_max_total_pct": "Lo máximo que puedes tener en riesgo sumando todas las posiciones abiertas y las propuestas pendientes, como % de tu equity.",
    "perdida_max_diaria_pct": "Si las pérdidas del día llegan a este % de tu balance, el agente no abre más operaciones ese día.",
    "volumen_max": "Lotes máximos por orden (además del máximo del bróker).",
    "apalancamiento_max": "Valor total de tus posiciones dividido por tu equity; por ejemplo, 5 = el agente no deja que tus posiciones valgan más de 5 veces tu equity.",
    "max_posiciones_abiertas": "Cantidad máxima de posiciones abiertas a la vez.",
}


# TITULO GUARDAR

def _guardar() -> None:
    """Guarda los valores de la ventana en los límites del usuario y deja el aviso. Sirve de `on_click`."""
    valores = {c: st.session_state.get(f"agente_limite_{c}") for c in ordenes.CAMPOS_EDITABLES}
    try:
        ordenes.guardar_limites(valores)
        st.session_state[_CLAVE_AVISO] = ("ok", "Límites guardados. El agente los respeta desde ahora.")
    except Exception:  # noqa: BLE001
        st.session_state[_CLAVE_AVISO] = ("error", "No se pudieron guardar los límites. Inténtalo de nuevo.")


# TITULO LIMITES DEL AGENTE

def limites_agente() -> None:
    """Dibuja el botón «Límites» con la ventana para definir los límites del agente (0 = sin límite). No devuelve nada."""
    with st.popover("Límites", icon=":material/tune:", width="stretch", help="Decide con cuánto riesgo puede operar el agente"):
        st.markdown("**Límites del agente**")
        st.caption("Tú decides el riesgo que asumes: con 0 no hay límite. El agente y las vigilancias respetan lo que definas aquí. Operar con límites altos o sin ellos "
                   "puede causar pérdidas grandes; el agente solo opera en cuenta demo.")
        aviso = st.session_state.pop(_CLAVE_AVISO, None)
        if aviso:
            (st.success if aviso[0] == "ok" else st.error)(aviso[1])
        actuales = ordenes.limites_actuales()
        for campo, (texto, unidad, tipo) in ordenes.CAMPOS_EDITABLES.items():
            valor = getattr(actuales, campo)
            st.number_input(f"{texto} ({unidad}; 0 = sin límite)", min_value=0 if tipo is int else 0.0, value=int(valor or 0) if tipo is int else float(valor or 0.0), step=1 if tipo is int else 0.5,
                            key=f"agente_limite_{campo}", help=_AYUDAS.get(campo))
        st.button("Guardar límites", type="primary", width="stretch", key="agente_limites_guardar", on_click=_guardar)



# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara limites .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
