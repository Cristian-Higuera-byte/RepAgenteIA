# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara gatillos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Botones invisibles de Streamlit que el JavaScript del gráfico pulsa para comunicarse con Python.

Hay dos familias: `chcls_<ticket>` (uno por posición abierta; la ✕ de la etiqueta del gráfico lo pulsa y se abre el
modal de cierre de Cartera) y `chcls_sel_<i>` (uno por activo de la lista; el selector de activo del gráfico en
pantalla completa lo pulsa para cambiar el activo seleccionado). Se dibujan dentro de un fragmento que se refresca
solo y escriben en `st.session_state`.
"""
import streamlit as st

from components.flujo_precios import intervalo
from tools.puente_mt5 import obtener_posiciones


def neto(p: dict) -> float:
    """Devuelve el resultado neto (ganancia/pérdida más swap) de una posición, redondeado a 2 decimales.

    Recibe `p`, el diccionario de posición del puente MT5, con las claves opcionales `profit` y `swap`."""
    return round(float(p.get("profit", 0) or 0) + float(p.get("swap", 0) or 0), 2)


# Fragmento que se refresca solo (2 s sin feed, 5 s con feed) para reflejar altas y bajas de posiciones.
@st.fragment(run_every=intervalo("2s", "5s"))   # altas/bajas de posiciones
def gatillos_cierre():
    """Dibuja los botones invisibles del gráfico: uno por posición abierta y uno por activo de la lista.

    Efectos: al pulsarse un botón de posición guarda en `st.session_state.ca_cerrar` los datos de la posición
    (ticket, símbolo, resultado neto, tipo y volumen), borra `ca_result` y relanza la app para abrir el modal de
    cierre. Al pulsarse un botón de activo guarda `activo_seleccionado` y relanza la app. Si MT5 falla, no
    dibuja botones de posición."""
    # Posiciones abiertas actuales; ante cualquier error se asume lista vacía.
    try:
        posiciones = obtener_posiciones() or []
    except Exception:
        posiciones = []
    # El contenedor con clave permite ocultar todos los botones con CSS (`chcls_wrap`).
    with st.container(key="chcls_wrap"):
        # Un botón por posición: la ✕ del gráfico lo pulsa y se prepara el cierre de ese ticket.
        for p in posiciones:
            tk = p.get("ticket")
            if st.button("cerrar", key=f"chcls_{tk}"):
                st.session_state.ca_cerrar = {
                    "ticket": tk, "symbol": (p.get("symbol") or "").replace("...", ""),
                    "profit": neto(p), "tipo": p.get("tipo"), "volumen": p.get("volumen", 0),
                }
                st.session_state.pop("ca_result", None)
                st.rerun(scope="app")
        # Cambio de activo desde el gráfico en pantalla completa: la lista que muestra el gráfico (watchlist) la deja
        # components/grafico/panel.py en la sesión; el botón nº i la pulsa el JS del gráfico (selector de activo).
        for i, ticker in enumerate(st.session_state.get("_grafico_lista_activos", [])):
            if st.button("activo", key=f"chcls_sel_{i}"):
                st.session_state.activo_seleccionado = ticker
                st.rerun(scope="app")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara gatillos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
