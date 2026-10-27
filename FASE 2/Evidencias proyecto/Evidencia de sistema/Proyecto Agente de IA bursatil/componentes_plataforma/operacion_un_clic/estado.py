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

Claves de `st.session_state` que usa: `orden_un_clic` (interruptor), `terminos_un_clic_terminos` (mostrar la ventana) y
`_terminos_un_clic_pedir` (marca de un solo uso para relanzar la app).
"""
import streamlit as st

from componentes_plataforma.operacion_un_clic.registro import aceptado, registrar


# TITULO AL CAMBIAR

def al_cambiar():
    """on_change del interruptor: si se activa sin haber aceptado, se apaga y se
    pide aceptar los términos (el modal lo abre aplicacion.py en el rerun completo).

    Efectos: puede poner `orden_un_clic` en False y `terminos_un_clic_terminos` y `_terminos_un_clic_pedir` en True."""
    if st.session_state.get("orden_un_clic") and not aceptado():
        st.session_state.orden_un_clic = False
        st.session_state.terminos_un_clic_terminos = True
        st.session_state._terminos_un_clic_pedir = True     # una sola vez: rerun de app para abrir el modal


# TITULO PEDIR TERMINOS SI CORRESPONDE

def pedir_terminos_si_corresponde():
    """Llamar dentro del fragmento del ticket, tras el interruptor: si hay que
    mostrar los términos, rerun de la app (el modal se dibuja fuera del fragmento).

    Consume (pop) la marca `_terminos_un_clic_pedir` para que el rerun ocurra una sola vez."""
    if st.session_state.pop("_terminos_un_clic_pedir", False):
        st.rerun(scope="app")


# TITULO ACEPTAR

def aceptar():
    """Callback del botón "Acepto": registra la aceptación en disco, activa el interruptor y cierra la ventana."""
    registrar()
    st.session_state.orden_un_clic = True
    st.session_state.terminos_un_clic_terminos = False


# TITULO CANCELAR

def cancelar():
    """Callback de Cancelar o de cierre del diálogo: solo oculta la ventana (el interruptor sigue apagado)."""
    st.session_state.terminos_un_clic_terminos = False


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
