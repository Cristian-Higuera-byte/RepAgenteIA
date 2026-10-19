# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara barra .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Barra de favoritos: panel con encabezado «Mis favoritos» + contador y 6 slots (favorito con ✕, «+» en el
primer hueco libre, o vacío).

Cada slot es un contenedor Streamlit con clave `favslot_<i>`; dentro se superponen (vía estilos.css)
la tarjeta HTML, un botón invisible que cubre toda la tarjeta (selecciona el activo) y una ✕ para
quitarlo. El módulo lee y escribe `st.session_state` (activo_seleccionado, favoritos) y está pensado
para ejecutarse dentro de un fragmento de Streamlit, de ahí los `st.rerun(scope="fragment")`.
"""
from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from components import _estaticos
from components.favoritos.estado import FAVORITOS_MAX, agregar_favorito, inicializar_favoritos, quitar_favorito
from components.favoritos.tarjeta import tarjeta_html

# Cantidad de slots (tarjetas) que se dibujan en la fila; coincide con FAVORITOS_MAX.
_VISIBLES = 6           # tarjetas visibles
# Ruta de la hoja de estilos de la barra (se inyecta con _estaticos.estilos).
_CSS = Path(__file__).parent / "estilos.css"


def _slot_agregar(disponibles):
    """Tarjeta '+' en el hueco libre: popover con selector para agregar favorito.

    Recibe `disponibles`, la lista de tickers que aún no son favoritos. Al elegir uno lo agrega
    (actualiza session_state y Supabase) y relanza solo el fragmento para dibujar la nueva tarjeta.
    """
    # El contenedor con clave "favadd" permite que estilos.css dé al botón el aspecto de tarjeta punteada.
    with st.container(key="favadd"):
        with st.popover("＋", help="Agregar favorito", use_container_width=True):
            # Selector de activo; la cadena vacía actúa como opción "sin selección".
            sel = st.selectbox(
                "Agregar activo", options=[""] + disponibles,
                format_func=lambda x: "Elegir activo…" if x == "" else x.replace("...", ""),
                label_visibility="collapsed", key="fav_add_sel",
            )
            if sel:
                # Se guarda el favorito y se redibuja solo este fragmento.
                agregar_favorito(sel)
                st.rerun(scope="fragment")


def _slot_favorito(tk: str, datos: dict):
    """Dibuja el slot de un favorito: tarjeta HTML, botón invisible de selección y botón ✕ de quitar.

    Recibe el ticker `tk` y el diccionario `datos` con los precios de mercado. Al pulsar la tarjeta
    fija `st.session_state.activo_seleccionado` y relanza toda la app; al pulsar ✕ quita el favorito
    y relanza solo el fragmento.
    """
    # Tarjeta visual con precio y variación (los números en vivo los repinta el feed del navegador).
    st.html(tarjeta_html(tk, datos))
    # Clic en la tarjeta -> carga el activo en el gráfico, el ticket y la cabecera (igual que la watchlist).
    # scope="app" porque esos paneles están fuera de este fragmento. Sin st.toast antes del rerun
    # (error "Cannot set a node at a delta path", ver watchlist.py).
    # Slug sin caracteres especiales para usarlo en la clave del botón (las claves de widget no admiten símbolos).
    slug = re.sub(r"\W", "", tk)
    if st.button("Seleccionar", key=f"favsel_{slug}"):
        st.session_state.activo_seleccionado = tk
        st.rerun(scope="app")
    # Botón de quitar; estilos.css lo coloca en la esquina superior derecha de la tarjeta.
    if st.button("✕", key=f"favx_{tk}", help="Quitar de favoritos"):
        quitar_favorito(tk)
        st.rerun(scope="fragment")


def renderizar_barra_favoritos(vertical: bool = False):
    """Dibuja el panel completo de favoritos: encabezado con contador y los 6 slots.

    Con `vertical=False` (por defecto) los slots van en una fila de 6 columnas; con `vertical=True` van apilados
    uno bajo otro, que es la disposición del panel «Favoritos» del rail derecho (riel/).

    Inicializa los favoritos del usuario (carga única desde Supabase), calcula qué activos de la
    watchlist siguen disponibles para agregar y reparte los 6 slots: favoritos existentes, un botón
    «+» en el primer hueco libre (si hay disponibles y no se alcanzó el máximo) y huecos invisibles
    para el resto. No devuelve nada; escribe directamente en la página de Streamlit.
    """
    # Carga los favoritos en session_state si es la primera vez en la sesión.
    inicializar_favoritos()
    # Precios de mercado más recientes por ticker (para pintar cada tarjeta).
    datos = st.session_state.get("datos_mercado_real", {})
    favs = list(st.session_state.favoritos)
    # Universo de activos candidatos: la watchlist del usuario o, si no existe, los símbolos con datos.
    lista = st.session_state.get("watchlist_simbolos") or list(datos.keys())
    disponibles = [t for t in lista if t not in favs]
    # Solo se ofrece «+» si queda algún activo por agregar y no se llegó al tope.
    total = len(favs)
    puede_agregar = bool(disponibles) and total < FAVORITOS_MAX

    with st.container(key="fav_panel"):
        # Inyecta la hoja de estilos de la barra dentro del panel.
        st.html(_estaticos.estilos(_CSS))

        # --- Encabezado: solo título + contador ---
        st.html(
            "<div class='fav-head'>"
            "<span class='fav-chip'><span class='fav-mi'>star</span></span>"
            "<span class='fav-title'>Mis favoritos</span>"
            f"<span class='fav-badge'>{total}</span></div>"
        )

        # --- 6 slots: favorito (con ✕), '+' en el primer hueco libre, o vacío ---
        # Una columna por slot; cada slot lleva su propia clave para que el CSS lo posicione.
        # En vertical no hay columnas: los slots se apilan y no se dibujan huecos vacíos.
        cols = None if vertical else st.columns(_VISIBLES, gap="small")
        for i in range(_VISIBLES):
            if vertical and (i > total or (i == total and not puede_agregar)):
                break   # en vertical se detiene tras el último favorito (o tras el «+»)
            with (st.container() if vertical else cols[i]):
                with st.container(key=f"favslot_{i}"):
                    if i < total:
                        _slot_favorito(favs[i], datos)
                    elif i == total and puede_agregar:
                        _slot_agregar(disponibles)
                    else:
                        # Hueco vacío invisible: conserva el ancho de la columna y la altura de la fila.
                        st.html("<div class='fav-card' style='visibility:hidden;'></div>")


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara barra .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
