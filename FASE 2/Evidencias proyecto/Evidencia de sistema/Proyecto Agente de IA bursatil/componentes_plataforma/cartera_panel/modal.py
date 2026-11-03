# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara modal .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
cartera_panel/modal.py
----------------------
Modal de confirmación de cierre de posición (estilo XM): tarjeta azul oscuro, botón
grande con el monto (naranja P&J) y "Cancelar". Se renderiza FUERA del fragmento de la
lista (lo llama aplicacion.py vía renderizar_modal_cerrar), para no chocar con el auto-refresco. El
texto del botón lo actualiza el feed en vivo con el P/G neto de esa posición.

Estado de sesión usado: cartera_cerrar (datos de la posición a cerrar, o None), cartera_resultado
(mensaje de error tras un intento fallido) y cartera_ganancia_perdida_real (P/G exacto del cierre manual,
que consume lista._detectar_cierres para armar la tarjeta de cerrada).
"""
import streamlit as st

from herramientas.puente_mt5 import obtener_posiciones, cerrar_posicion

from .comun import neto, texto_cerrar, css_modal


# TITULO AL DESCARTAR

def _al_descartar():
    """Clic fuera del modal / Esc: se descarta la intención de cierre (si no,
    el modal reaparecería en la siguiente reejecución).

    Callback on_dismiss del diálogo: pone st.session_state.cartera_cerrar en None.
    """
    st.session_state.cartera_cerrar = None


# TITULO DIALOGO CERRAR

@st.dialog("¿Quiere cerrar su posición?", on_dismiss=_al_descartar)
def _dialogo_cerrar():
    """Diálogo de Streamlit que pide confirmar el cierre de una posición.

    Toma los datos de st.session_state.cartera_cerrar, refresca el P/G desde MT5, muestra el
    botón principal con el monto (cierra la posición con cerrar_posicion) y el botón
    "Cancelar". Tras cualquiera de las dos acciones limpia cartera_cerrar y relanza la app.
    Si el cierre falla guarda el motivo en cartera_resultado; si funciona guarda el P/G exacto
    en cartera_ganancia_perdida_real. No devuelve nada.
    """
    # Datos de la posición elegida por el usuario.
    c = st.session_state.get("cartera_cerrar") or {}
    ticket = c.get("ticket")
    # P/G FRESCO de MT5 al abrir (el de la fila podía tener hasta 5 s de atraso:
    # la fila la pinta el feed en vivo, pero el dato guardado era del último refresco).
    prof = c.get("profit", 0.0)
    # Si MT5 no responde se conserva el P/G que traía la fila.
    try:
        fresca = next((p for p in obtener_posiciones() if p.get("ticket") == ticket), None)
        if fresca:
            prof = neto(fresca)
    except Exception:
        pass
    # Estilos del diálogo y texto del botón principal.
    css_modal()
    etiqueta = texto_cerrar(prof)
    # El contenedor lleva el ticket en su clave: flujo_precios/ actualiza el texto
    # del botón en vivo con el P/G neto de esa posición (mismo dato que la fila).
    with st.container(key=f"cartera_boton_cerrar_{ticket}"):
        cerrar = st.button(etiqueta, type="primary", width="stretch", key="cartera_cerrar_aceptar")
    # Confirmación: se envía la orden de cierre a MT5.
    if cerrar:
        resultado = cerrar_posicion(c.get("ticket"))
        if "error" in resultado:
            st.session_state.cartera_resultado = ("error", f"No se pudo cerrar: {resultado['error']}")
        else:
            # P/G exacto para la tarjeta de posición cerrada (lo usa _detectar_cierres).
            st.session_state.setdefault("cartera_ganancia_perdida_real", {})[c.get("ticket")] = float(resultado.get("profit", prof))
            st.session_state.pop("cartera_resultado", None)
        st.session_state.cartera_cerrar = None
        st.rerun()
    # Cancelar: descarta la intención de cierre.
    if st.button("Cancelar", width="stretch", key="cartera_cerrar_cancelar"):
        st.session_state.cartera_cerrar = None
        st.rerun()


# TITULO RENDERIZAR MODAL CERRAR

def renderizar_modal_cerrar():
    """Llamar desde aplicacion.py (fuera de los fragmentos en vivo).

    Abre el diálogo de confirmación solo si hay una intención de cierre pendiente en
    st.session_state.cartera_cerrar. No recibe parámetros ni devuelve nada.
    """
    if st.session_state.get("cartera_cerrar"):
        _dialogo_cerrar()


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara modal .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
