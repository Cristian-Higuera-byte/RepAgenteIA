# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara transicion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Inyecta la cortina de transición entre secciones: el CSS que oculta la vista mientras carga y el script que la gobierna.

`inyectar_transicion()` se llama una vez por ejecución, al principio de la página. El script vive en un iframe de altura
cero dentro del contenedor `pj_transicionjs`, que el CSS saca del flujo para que no sume separación entre elementos."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from componentes_plataforma._estaticos import texto

_AQUI = Path(__file__).parent
_JS = "\n<script>\n" + texto(_AQUI / "transicion.js") + "</script>\n"


# TITULO INYECTAR TRANSICION

def inyectar_transicion() -> None:
    """Escribe el CSS de la cortina y monta el script que la activa al pulsar un botón de navegación.

    No recibe parámetros ni devuelve nada. Lee `estilos.css` y `transicion.js` (con caché) y no escribe en disco."""
    # El estilo va dentro del mismo contenedor fuera de flujo: un elemento suelto en la página sumaría 16 px de separación.
    with st.container(key="pj_transicionjs"):
        st.markdown("\n<style>\n" + texto(_AQUI / "estilos.css") + "</style>\n", unsafe_allow_html=True)
        components.html(_JS, height=0, width=0)

# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara transicion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
