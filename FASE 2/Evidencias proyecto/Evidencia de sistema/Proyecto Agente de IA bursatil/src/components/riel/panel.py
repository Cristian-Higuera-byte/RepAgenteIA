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

"""Rail de iconos FIJO a la derecha: dibuja los paneles (Operar, DOM, Favoritos), el rail y el script que los alterna.

El CSS (`estilos.css`) decide qué panel se ve según una clase en el elemento html; `riel.js` cambia esa clase al
pulsar los botones, sin reejecutar Python. Este módulo crea los contenedores con clave que el CSS y el JS buscan:
`pj_panel_order`, `pj_panel_dom`, `pj_panel_fav`, `pj_rail` y `pj_railjs`.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from components._estaticos import texto
from components.riel.datos import BOTONES
from components.riel.estilos import css

# Script del rail ya envuelto en script, listo para `components.html`; se lee al importar el módulo.
_JS = "\n<script>\n" + texto(Path(__file__).parent / "riel.js") + "</script>\n"


def inyectar_css_riel():
    """Inyecta el CSS del rail. Debe llamarse ANTES de dibujar el gráfico, para que
    éste se mida con el espacio ya reservado a la derecha (si no, queda recortado).

    No recibe parámetros ni devuelve nada; escribe el estilo en la página con `st.markdown`."""
    st.markdown(css(), unsafe_allow_html=True)


def renderizar_panel_favoritos(contenido) -> None:
    """Dibuja el panel «Favoritos» del rail derecho y llama a `contenido()` dentro de él.

    `contenido` es la función que pinta los favoritos (el fragmento en vivo de aplicacion_principal/fragmentos.py).
    Se separa de `renderizar_riel_y_paneles` porque debe ejecutarse al PRINCIPIO de la vista operativa: el fragmento
    también refresca los precios de mercado que usa la lista de activos, que se dibuja después. El contenedor
    `pj_panel_fav` va fijo a la derecha por CSS, así que su posición en el código no importa visualmente."""
    with st.container(key="pj_panel_fav"):
        contenido()


def renderizar_riel_y_paneles(main=None):
    """Dibuja los paneles Operar y DOM, el rail de botones y el script que los alterna.

    Recibe `main`, que se pasa tal cual al panel de órdenes. Los imports de los paneles son locales para evitar
    importaciones circulares al cargar el paquete. No devuelve nada."""
    # Paneles: se dibujan SIEMPRE (el CSS muestra el activo y oculta el resto).
    with st.container(key="pj_panel_order"):
        from components.panel_orden import renderizar_panel_orden
        renderizar_panel_orden(main)
    with st.container(key="pj_panel_dom"):
        from components.profundidad_panel import renderizar_panel_dom
        renderizar_panel_dom()

    # Rail de iconos (mismo estilo que el nav izquierdo: solo el ícono).
    with st.container(key="pj_rail"):
        for icono, pid, _nom in BOTONES:
            st.button(icono, key=f"rail_{pid}")

    # Script que alterna los paneles sin reejecutar Python.
    with st.container(key="pj_railjs"):
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
