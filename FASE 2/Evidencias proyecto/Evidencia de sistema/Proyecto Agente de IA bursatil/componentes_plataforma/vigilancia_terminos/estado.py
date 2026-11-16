# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara estado .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Estado de la ventana de términos de la vigilancia (callbacks de Streamlit).

Clave de `st.session_state` que usa: `vigilancia_terminos_id` (id de la vigilancia cuya ventana está abierta). Los callbacks
se ejecutan antes del siguiente ciclo de la app; el aviso del resultado va a `CLAVE_AVISO`, que el panel «Órdenes
propuestas» muestra y consume.
"""
import streamlit as st

from componentes_plataforma.agente_paneles.datos import CLAVE_AVISO
from componentes_plataforma.vigilancia_terminos.registro import registrar
from nucleo_agente import vigilancia

# Clave de session_state con el id de la vigilancia que espera aceptación; si no existe, no hay ventana abierta.
CLAVE_VIGILANCIA = "vigilancia_terminos_id"


# TITULO USUARIO ID

def _usuario_id() -> str:
    """Id del usuario en sesión como texto, o "local" si no hay usuario (igual que el panel de vigilancias)."""
    return str((st.session_state.get("usuario_informacion") or {}).get("id") or "local")


# TITULO PEDIR

def pedir(vid: str) -> None:
    """Marca la vigilancia `vid` para que la ventana de términos se abra en el próximo ciclo de la app."""
    st.session_state[CLAVE_VIGILANCIA] = vid


# TITULO CANCELAR

def cancelar() -> None:
    """Callback de cierre con la «X»: solo cierra la ventana; la vigilancia sigue pendiente de autorización."""
    st.session_state.pop(CLAVE_VIGILANCIA, None)


# TITULO ACEPTAR

def aceptar() -> None:
    """Callback de «Acepto los Términos y Condiciones»: registra la aceptación y autoriza la vigilancia.

    Primero deja constancia (usuario, fecha y condiciones) y luego llama a `vigilancia.autorizar`, que la activa y arranca el
    motor. Deja el resultado como aviso para el panel de propuestas."""
    vid = st.session_state.pop(CLAVE_VIGILANCIA, None)
    if not vid:
        return
    v = vigilancia.obtener(vid)
    if v:
        registrar(v)
    resultado = vigilancia.autorizar(vid, _usuario_id())
    st.session_state[CLAVE_AVISO] = ("ok" if resultado["ok"] else "error", resultado["mensaje"])


# TITULO RECHAZAR

def rechazar() -> None:
    """Callback de «Rechazar propuesta»: cancela la vigilancia pendiente; el agente no operará.

    Deja un aviso para el panel de propuestas (error si la vigilancia ya no estaba pendiente)."""
    vid = st.session_state.pop(CLAVE_VIGILANCIA, None)
    if not vid:
        return
    if vigilancia.rechazar(vid, _usuario_id()):
        st.session_state[CLAVE_AVISO] = ("ok", "Propuesta de vigilancia rechazada: el agente no operará.")
    else:
        st.session_state[CLAVE_AVISO] = ("error", "La vigilancia ya no estaba pendiente de autorización.")


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara estado .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
