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

"""Estado del interruptor One-Click y de la ventana de términos (callbacks de Streamlit).

Claves de `st.session_state` que usa: `ord_oc` (interruptor), `oct_terminos` (mostrar la ventana) y
`_oct_pedir` (marca de un solo uso para relanzar la app).
"""
import streamlit as st

from components.operacion_un_clic.registro import aceptado, registrar


def al_cambiar():
    """on_change del interruptor: si se activa sin haber aceptado, se apaga y se
    pide aceptar los términos (el modal lo abre app.py en el rerun completo).

    Efectos: puede poner `ord_oc` en False y `oct_terminos` y `_oct_pedir` en True."""
    if st.session_state.get("ord_oc") and not aceptado():
        st.session_state.ord_oc = False
        st.session_state.oct_terminos = True
        st.session_state._oct_pedir = True     # una sola vez: rerun de app para abrir el modal


def pedir_terminos_si_corresponde():
    """Llamar dentro del fragmento del ticket, tras el interruptor: si hay que
    mostrar los términos, rerun de la app (el modal se dibuja fuera del fragmento).

    Consume (pop) la marca `_oct_pedir` para que el rerun ocurra una sola vez."""
    if st.session_state.pop("_oct_pedir", False):
        st.rerun(scope="app")


def aceptar():
    """Callback del botón "Acepto": registra la aceptación en disco, activa el interruptor y cierra la ventana."""
    registrar()
    st.session_state.ord_oc = True
    st.session_state.oct_terminos = False


def cancelar():
    """Callback de Cancelar o de cierre del diálogo: solo oculta la ventana (el interruptor sigue apagado)."""
    st.session_state.oct_terminos = False


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
