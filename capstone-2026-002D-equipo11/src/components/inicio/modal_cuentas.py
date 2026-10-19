# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara modal_cuentas .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Modal "Seleccione cuenta" (MT5 expone solo la cuenta conectada en el terminal).

Diálogo de Streamlit que muestra la cuenta activa y recuerda cómo agregar otra. Su visibilidad se
controla con `st.session_state.ini_modal_cuentas`.
"""
import streamlit as st

# Estilos de Inicio (las clases selc-* del diálogo viven en estilos.css).

from components.inicio.estilos import CSS
# Formato de dinero del equity.
from components.inicio.formato import formatear_dinero
# Datos de la cuenta conectada en MT5.
from tools.puente_mt5 import obtener_info_cuenta


def _cerrar_modal_cuentas():
    """Callback `on_dismiss` del diálogo: apaga la bandera `ini_modal_cuentas` para que no se reabra en el próximo rerun."""
    st.session_state.ini_modal_cuentas = False


@st.dialog("Seleccione cuenta", on_dismiss=_cerrar_modal_cuentas)
def modal_cuentas():
    """Diálogo «Seleccione cuenta»: muestra la cuenta conectada (equity, login, servidor, tipo Demo/Real).

    Decorada con `st.dialog`. Sin conexión a MT5 muestra una advertencia. El botón «Crear nueva cuenta»
    solo informa por toast que hay que iniciar sesión con otra cuenta en el terminal MT5.
    """
    # Datos de la cuenta conectada.
    info = obtener_info_cuenta()
    # Los diálogos se montan fuera del flujo normal, por eso necesitan su propia inyección de estilos.
    st.html(CSS)
    if "error" in info:
        st.warning("No hay conexión con MetaTrader 5.")
        return
    tipo = info.get("tipo", "Demo")
    # Clase de color de la etiqueta Real/Demo.
    cls_tipo = "selc-real" if tipo == "Real" else "selc-demo"
    # Tarjeta de la cuenta activa.
    st.html(
        "<div class='selc-card activa'><div class='selc-top'>"
        "<div><div style='color:#e6edf3;font-weight:700;'>Standard</div>"
        f"<div class='selc-bal'>{formatear_dinero(info.get('equity', 0))}</div>"
        f"<div class='selc-meta'>#{info.get('login','—')} · Standard · MT5 · "
        f"{info.get('servidor','')}</div></div>"
        f"<span class='selc-tipo {cls_tipo}'>{tipo}</span>"
        "</div></div>"
    )
    st.caption("MetaTrader 5 muestra solo la cuenta conectada en el terminal.")
    if st.button("Crear nueva cuenta", icon=":material/add:", width="stretch", key="selc_crear"):
        st.toast("Para agregar otra cuenta, inicia sesión con ella en el terminal MT5.")


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara modal_cuentas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
