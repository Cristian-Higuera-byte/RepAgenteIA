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

"""Vista "Copy trading" estilo XM (MVP con datos SIMULADOS/mock mientras se define la fuente de datos real).
Dos vistas: listado de estrategias (tarjetas) y ficha de detalle de una estrategia. No ejecuta operaciones.
Referencias en referencias/copytrading/*.png.

La estrategia abierta se guarda en st.session_state.ct_estrategia (None = listado). Los
estilos están en estilos.css y las tarjetas son clicables mediante un botón invisible
superpuesto (claves ctsel_ y ctrow_).
"""
from pathlib import Path

import streamlit as st

from components import _estaticos
from components.copytrading.datos import CATEGORIAS, ESTRATEGIAS, ORDEN, TABS, por_id
from components.copytrading.ficha import ficha
from components.copytrading.tarjeta import tarjeta_html

# Ruta de la hoja de estilos de la vista (estilos.css, junto a este archivo).
_CSS = Path(__file__).parent / "estilos.css"


def renderizar_panel_copytrading(main=None):
    """Dibuja la vista de Copy trading: ficha de una estrategia o listado de tarjetas.

    Parámetro: main, sin uso actual (se conserva por compatibilidad con quien la invoca).
    Inyecta los estilos, y si hay una estrategia seleccionada muestra su ficha y termina;
    si no, dibuja el título, el orden por pestañas, el filtro de categoría y una cuadrícula
    de tarjetas de tres columnas. No devuelve nada; relanza la app al elegir una tarjeta.
    """
    # Estilos de la vista.
    st.html(_estaticos.estilos(_CSS))
    # Inicializa la estrategia seleccionada (None significa mostrar el listado).
    if "ct_estrategia" not in st.session_state:
        st.session_state.ct_estrategia = None

    # Contenedor con clave ct_wrap: limita el ancho máximo (ver estilos.css).
    with st.container(key="ct_wrap"):
        # --- Detalle ---
        sel = st.session_state.get("ct_estrategia")
        if sel:
            e = por_id(sel)
            if e:
                ficha(e)
                return

        # --- Listado ---
        st.html("<div class='ct-title'>Copy trading</div>")
        # Controles de ordenación y filtro; si se deseleccionan, se usan los valores por defecto.
        tab = st.segmented_control("Orden", TABS, default=TABS[0],
                                   label_visibility="collapsed", key="ct_tab") or TABS[0]
        cat = st.pills("Categoría", CATEGORIAS, default="Cualquiera",
                       label_visibility="collapsed", key="ct_cat") or "Cualquiera"

        # Filtra por categoría y ordena según la pestaña elegida.
        lista = [e for e in ESTRATEGIAS if cat == "Cualquiera" or e["cat"] == cat]
        lista = sorted(lista, key=ORDEN.get(tab, ORDEN["Destacadas"]))
        st.caption(f"{len(lista)} estrategias")

        # Cuadrícula de 3 columnas; cada tarjeta lleva un botón invisible encima para abrir su ficha.
        for fila in range(0, len(lista), 3):
            cols = st.columns(3, gap="medium")
            for j, e in enumerate(lista[fila:fila + 3]):
                with cols[j]:
                    with st.container(key=f"ctrow_{e['id']}"):
                        st.html(tarjeta_html(e))
                        if st.button("ver", key=f"ctsel_{e['id']}"):
                            st.session_state.ct_estrategia = e["id"]
                            st.rerun()


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
