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

"""Lista colapsable: marca la columna de la lista (watchlist / historial) y dibuja la pestaña ocultable + el script."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from componentes_plataforma._estaticos import texto
from componentes_plataforma.lista_colapsable.estilos import css

_JS = "\n<script>\n" + texto(Path(__file__).parent / "lista.js") + "</script>\n"
_MARCA = "<div class='pj-lista-activos-colmark'></div>"


# TITULO INYECTAR CSS LISTA COLAPSABLE

def inyectar_css_lista_colapsable():
    """Inyecta el CSS del colapso y de la pestaña. Debe ir ANTES del gráfico, para que
    éste se mida con el ancho ya definido (y crezca al colapsar la columna de la lista)."""
    st.markdown(css(), unsafe_allow_html=True)


# TITULO MARCA COLUMNA

def marca_columna():
    """Marca la columna ACTUAL como colapsable (va dentro del `with col:` de la lista y
    del historial). Al ocultar, estas columnas colapsan a 0 y sus hermanas se ensanchan."""
    st.markdown(_MARCA, unsafe_allow_html=True)


# TITULO RENDERIZAR TOGGLE LISTA

def renderizar_toggle_lista():
    """Pestaña (solo el botón) + script que la oculta/muestra sin reejecutar Python."""
    with st.container(key="pj_lista_activos_pestana"):
        st.button(":material/chevron_left:", key="lista_activos_interruptor", help="Ocultar / mostrar la lista")
    with st.container(key="pj_lista_activos_js"):
        components.html(_JS, height=0, width=0)


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
