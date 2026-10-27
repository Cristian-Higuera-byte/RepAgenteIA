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

"""Vista "Copy trading" estilo XM. Muestra las estrategias reales publicadas por los gestores (métricas calculadas con sus operaciones registradas) y,
mientras no haya ninguna, estrategias de ejemplo. La sección «Cartera» (cartera.py) muestra las copias del usuario y «Área de gestor» (gestor.py) permite crear, publicar y administrar las propias.
Dos vistas: listado de estrategias (tarjetas) y ficha de detalle de una estrategia. No ejecuta operaciones.
Referencias en referencias/copytrading/*.png.

La estrategia abierta se guarda en st.session_state.copytrading_estrategia (None = listado). Los
estilos están en estilos.css y las tarjetas son clicables mediante un botón invisible
superpuesto (claves ctsel_ y ctrow_).
"""
from pathlib import Path

import streamlit as st

from componentes_plataforma import _estaticos
from componentes_plataforma.copytrading.cartera import renderizar_cartera_copias
from componentes_plataforma.copytrading.datos import CATEGORIAS, ORDEN, PESTANAS, estrategias, por_id
from componentes_plataforma.copytrading.ficha import ficha
from componentes_plataforma.copytrading.ficha_real import ficha_real
from componentes_plataforma.copytrading.gestor import renderizar_area_gestor
from componentes_plataforma.copytrading.tarjeta import tarjeta_html

# Ruta de la hoja de estilos de la vista (estilos.css, junto a este archivo).
_CSS = Path(__file__).parent / "estilos.css"


# TITULO RENDERIZAR PANEL COPYTRADING

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
    if "copytrading_estrategia" not in st.session_state:
        st.session_state.copytrading_estrategia = None

    # Contenedor con clave copytrading_contenedor: limita el ancho máximo (ver estilos.css).
    with st.container(key="copytrading_contenedor"):
        # --- Detalle ---
        seleccion = st.session_state.get("copytrading_estrategia")
        if seleccion:
            e = por_id(seleccion)
            if e:
                (ficha_real if e.get("real") else ficha)(e)
                return
            st.session_state.copytrading_estrategia = None     # la estrategia ya no está publicada: se vuelve al listado

        # --- Listado ---
        st.html("<div class='copytrading-titulo'>Copy trading</div>")
        # Secciones de la vista: el listado de estrategias y el área del gestor (solo se dibuja la elegida).
        seccion = st.segmented_control("Sección", ["Estrategias", "Cartera", "Área de gestor"], default="Estrategias", key="copytrading_seccion",
                                       label_visibility="collapsed") or "Estrategias"
        aviso = st.session_state.pop("copytrading_aviso", None)
        if aviso:
            st.success(aviso)
        if seccion == "Cartera":
            renderizar_cartera_copias()
            return
        if seccion == "Área de gestor":
            renderizar_area_gestor()
            return
        # Controles de ordenación y filtro; si se deseleccionan, se usan los valores por defecto.
        lista_total, es_ejemplo = estrategias()
        if es_ejemplo:
            st.info("Todavía no hay estrategias publicadas por gestores: estas son estrategias de ejemplo.")
        pestana = st.segmented_control("Orden", PESTANAS, default=PESTANAS[0],
                                   label_visibility="collapsed", key="copytrading_pestana") or PESTANAS[0]
        # Las estrategias reales traen sus propias categorías; las de ejemplo usan la lista fija.
        opciones = CATEGORIAS if es_ejemplo else ["Cualquiera"] + sorted({e["cat"] for e in lista_total})
        categoria = st.pills("Categoría", opciones, default="Cualquiera",
                       label_visibility="collapsed", key="copytrading_categoria") or "Cualquiera"

        # Filtra por categoría y ordena según la pestaña elegida.
        lista = [e for e in lista_total if categoria == "Cualquiera" or e["cat"] == categoria]
        lista = sorted(lista, key=ORDEN.get(pestana, ORDEN["Destacadas"]))
        st.caption(f"{len(lista)} estrategias")

        # Cuadrícula de 3 columnas; cada tarjeta lleva un botón invisible encima para abrir su ficha.
        for fila in range(0, len(lista), 3):
            columnas = st.columns(3, gap="medium")
            for j, e in enumerate(lista[fila:fila + 3]):
                with columnas[j]:
                    with st.container(key=f"ctrow_{e['id']}"):
                        st.html(tarjeta_html(e))
                        if st.button("ver", key=f"ctsel_{e['id']}"):
                            st.session_state.copytrading_estrategia = e["id"]
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
