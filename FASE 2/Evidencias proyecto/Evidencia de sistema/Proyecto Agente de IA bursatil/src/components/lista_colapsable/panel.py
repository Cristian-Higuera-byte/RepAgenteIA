"""Lista colapsable: marca la columna de la lista (watchlist / historial) y dibuja la pestaña ocultable + el script."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from components._estaticos import texto
from components.lista_colapsable.estilos import css

_JS = "\n<script>\n" + texto(Path(__file__).parent / "lista.js") + "</script>\n"
_MARCA = "<div class='pj-wl-colmark'></div>"


def inyectar_css_lista_colapsable():
    """Inyecta el CSS del colapso y de la pestaña. Debe ir ANTES del gráfico, para que
    éste se mida con el ancho ya definido (y crezca al colapsar la columna de la lista)."""
    st.markdown(css(), unsafe_allow_html=True)


def marca_columna():
    """Marca la columna ACTUAL como colapsable (va dentro del `with col:` de la lista y
    del historial). Al ocultar, estas columnas colapsan a 0 y sus hermanas se ensanchan."""
    st.markdown(_MARCA, unsafe_allow_html=True)


def renderizar_toggle_lista():
    """Pestaña (solo el botón) + script que la oculta/muestra sin reejecutar Python."""
    with st.container(key="pj_wl_tab"):
        st.button(":material/chevron_left:", key="wl_toggle", help="Ocultar / mostrar la lista")
    with st.container(key="pj_wl_js"):
        components.html(_JS, height=0, width=0)
