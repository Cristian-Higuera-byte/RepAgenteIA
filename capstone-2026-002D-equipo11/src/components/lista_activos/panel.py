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

"""Lista de activos del USUARIO (los de su watchlist de Supabase) con scroll, favoritos y botón para agregar.

Lee `datos_mercado_real` y `watchlist_simbolos` de session_state y dibuja una fila por activo con
`dibujar_fila`. Los estilos se inyectan una vez por render con `st.markdown`.
"""
import streamlit as st

# Estilos del panel y dibujo de cada fila.

from components.lista_activos.estilos import CSS
from components.lista_activos.fila import dibujar_fila

# Altura (px) de la zona con scroll de la lista
ALTURA_LISTA = 640


def renderizar_watchlist():
    """Dibuja el panel «Lista de activos»: encabezado, zona con scroll con las filas y botón «Agregar activo».

    No recibe parámetros ni devuelve nada. Si no hay activo seleccionado fija EURUSD... por defecto. El
    botón «Agregar activo» abre el buscador y relanza la app para que app.py muestre el diálogo.
    """
    # Lista de activos del USUARIO (los que tenga en su watchlist de Supabase)
    info_activos_real = st.session_state.get("datos_mercado_real", {})
    tickers_watchlist = st.session_state.get("watchlist_simbolos") or list(info_activos_real.keys())

    # Inyecta los estilos del panel.
    st.markdown(CSS, unsafe_allow_html=True)

    # Activo por defecto en la primera carga.
    if "activo_seleccionado" not in st.session_state:
        st.session_state.activo_seleccionado = "EURUSD..."

    with st.container(key="wl_panel"):
        # Encabezado
        st.markdown(
            """
            <div class='wl-head'>
                <div class='ic'><span class='wl-mi'>show_chart</span></div>
                <div>
                    <div class='wl-title'>Lista de activos</div>
                    <div class='wl-sub'>Precios de activos en tiempo real</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Contenedor con altura fija y scroll vertical individual
        with st.container(height=ALTURA_LISTA, border=False, key="wl_scroll"):
            # Si un ticker aún no tiene datos de mercado se usa un item neutro.
            for ticker in tickers_watchlist:
                item = info_activos_real.get(ticker, {
                    "nombre": ticker,
                    "precio": 1.0000,
                    "var": "+0.00 (0.00%)",
                    "sube": True
                })
                dibujar_fila(ticker, item)

        # Botón de agregar activo, en un contenedor con clave para estilizarlo.
        with st.container(key="wl_add"):
            if st.button("Agregar activo", icon=":material/add:", width="stretch"):
                # Importación diferida del buscador (diálogo de búsqueda de activos).
                from components.buscador import abrir_buscador
                abrir_buscador()
                st.rerun()  # app scope: para que app.py renderice el diálogo


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
