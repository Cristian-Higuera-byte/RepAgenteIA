# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara secciones .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Secciones de la página de noticias: noticia principal, carrusel paginado y "Más noticias".

Cada noticia lleva un botón "abrir" invisible superpuesto (estilos.css) que guarda la noticia en
`st.session_state.noticia_abierta` para que `panel.py` abra su modal.
"""
import math
import time

import streamlit as st

from componentes_plataforma.noticias.datos import MAX_CARRUSEL, MAX_EXTERNAS, POR_PAGINA
from componentes_plataforma.noticias.estilos import CSS_CARRUSEL
from componentes_plataforma.noticias.rss import cargar_mas_noticias, cargar_noticias, hay_datos
from componentes_plataforma.noticias.tarjetas import tarjeta_externa_html, tarjeta_html


# Opciones del selector de idioma y el código de idioma que filtra cada una (None = sin filtro).
_IDIOMAS = {"Español": "ES", "English": "EN", "Todos": None}


# TITULO FILTRAR

def _filtrar(lista: list, idioma: str | None) -> list:
    """Deja solo las noticias del idioma indicado ("ES" o "EN"); con None devuelve la lista sin cambios."""
    return lista if idioma is None else [n for n in lista if n.get("idioma") == idioma]


# TITULO AVISO NOVEDADES

def _aviso_novedades(noticias: list) -> None:
    """Dibuja la línea de estado: hora de la última revisión y, si llegaron noticias desde que se abrió la página, cuántas.

    Recuerda en la sesión qué noticias ya se habían visto (`noticias_vistos`) y cuándo se abrió la página (`noticias_apertura`);
    una noticia es nueva si no estaba al abrir y su fecha de publicación es posterior. El botón «Marcar como vistas»
    reinicia el conteo. No devuelve nada."""
    ids = {n["id"] for n in noticias}
    if "noticias_vistos" not in st.session_state:
        st.session_state.noticias_vistos = ids
        st.session_state.noticias_apertura = time.time()
    nuevas = [n for n in noticias if n["id"] not in st.session_state.noticias_vistos
              and n["_ts"] >= st.session_state.noticias_apertura]
    c_est, c_boton = st.columns([8, 2], vertical_alignment="center")
    with c_est:
        punto = "<span style='color:#22c55e;'>●</span> " if not nuevas else "<span style='color:#f59e0b;'>●</span> "
        extra = f" · <b style='color:#f59e0b;'>{len(nuevas)} noticia{'s' if len(nuevas) != 1 else ''} nueva{'s' if len(nuevas) != 1 else ''}</b>" if nuevas else ""
        st.markdown(f"<div style='color:#586174; font-size:12px; margin:-6px 0 8px;'>{punto}Actualizado {time.strftime('%H:%M:%S')} · se revisa cada 10 s{extra}</div>",
                    unsafe_allow_html=True)
    with c_boton:
        if nuevas and st.button("Marcar como vistas", key="noticias_vistas_aceptar", width="stretch"):
            st.session_state.noticias_vistos = ids
            st.rerun(scope="fragment")


# Alto en píxeles del panel lateral «Otras fuentes» (con desplazamiento propio) y máximo total de noticias que muestra.
_ALTO_PANEL = 820
_MAX_EXTERNAS_TOTAL = 40


# TITULO EXTERNAS

def _externas(todas: list, idioma: str | None) -> list:
    """Noticias de las fuentes que no se pueden leer dentro de la plataforma, del idioma elegido.

    Une las de todas las listas recibidas, quita las repetidas por id y toma como máximo `MAX_EXTERNAS` de cada fuente (las
    más nuevas), para que una fuente con muchos feeds, como Investing, no tape a las demás. El resultado va de la más nueva
    a la más vieja."""
    vistas: set = set()
    por_fuente: dict = {}
    salida = []
    for n in sorted(_filtrar(todas, idioma), key=lambda x: x["_ts"], reverse=True):
        if n["lectura"] or n["id"] in vistas:
            continue
        if por_fuente.get(n["fuente"], 0) >= MAX_EXTERNAS:
            continue
        vistas.add(n["id"])
        por_fuente[n["fuente"]] = por_fuente.get(n["fuente"], 0) + 1
        salida.append(n)
    return salida


# TITULO PANEL EXTERNAS

def _panel_externas(externas: list) -> None:
    """Dibuja el panel lateral «Otras fuentes»: noticias cuyo artículo no se puede leer aquí.

    Cada una muestra su imagen, el titular y la fuente con la fecha, y un botón que abre la noticia en su sitio en una
    pestaña nueva. La lista tiene desplazamiento propio y muestra como máximo `_MAX_EXTERNAS_TOTAL` noticias. No devuelve nada."""
    st.markdown(
        "<div style='border-top:1px solid #1f2937; padding-top:12px; margin:0 0 10px;'>"
        "<span style='font-size:18px; font-weight:800; color:#e6edf3;'>Otras fuentes</span>"
        "<div style='color:#8b949e; font-size:12px; margin-top:4px;'>Estas noticias se leen en el sitio de cada medio.</div></div>",
        unsafe_allow_html=True,
    )
    with st.container(height=_ALTO_PANEL, key="noticias_ext"):
        if not externas:
            st.caption("Sin noticias de otras fuentes por ahora.")
        for n in externas[:_MAX_EXTERNAS_TOTAL]:
            st.html(tarjeta_externa_html(n))
            st.link_button(f"Leer en {n['fuente']} ↗", n["link"], width="stretch")


# TITULO RENDERIZAR CONTENIDO

def renderizar_contenido():
    """Dibuja el contenido completo de la página de noticias.

    Carga las noticias de todas las fuentes y las filtra por el idioma elegido en el selector (`noticias_idioma`, por
    defecto Español); si no hay ninguna, muestra un aviso. Si hay, inyecta el CSS, pinta el título con el selector, la línea
    de estado con las novedades y dos columnas: a la izquierda las noticias que se pueden leer aquí (noticia principal,
    carrusel paginado de 4 en 4 con flechas y vuelta al inicio, y «Más noticias»); a la derecha el panel «Otras fuentes»
    con las que solo se abren en su sitio. Usa `noticias_pagina` de la sesión para recordar la página del carrusel.
    No devuelve nada; se ejecuta dentro de un fragmento con auto-refresco."""
    todas_principal = cargar_noticias()
    if not todas_principal:
        if hay_datos():
            st.info("No se pudieron cargar las noticias en este momento. Reintenta en unos minutos.")
        else:
            st.info("Cargando noticias…")      # primera visita: las fuentes se están leyendo; la página se actualiza sola
        return

    st.markdown(CSS_CARRUSEL, unsafe_allow_html=True)

    # Título de la sección (con línea superior, igual que "Más noticias") y selector de idioma a la derecha
    c_titulo, c_idioma = st.columns([7, 3], vertical_alignment="center")
    with c_titulo:
        st.markdown(
            "<div style='border-top:1px solid #1f2937; padding-top:12px; margin:-22px 0 14px;'>"
            "<span class='noticias-titulo' style='font-size:24px; font-weight:800; color:#e6edf3;'>Noticias</span>"
            "<span style='color:#8b949e; font-size:13px; margin-left:8px;'>"
            "· Bolsa, divisas y economía de varias fuentes</span></div>",
            unsafe_allow_html=True,
        )
    with c_idioma:
        eleccion = st.segmented_control("Idioma", list(_IDIOMAS), default="Español", key="noticias_idioma",
                                        label_visibility="collapsed")
    idioma = _IDIOMAS.get(eleccion)

    _aviso_novedades(todas_principal)

    # Legibles: se exploran en la página y se abren en la ventana propia. Externas: su texto no se puede leer aquí, van al panel.
    noticias = [n for n in _filtrar(todas_principal, idioma) if n["lectura"]]
    externas = _externas(todas_principal + cargar_mas_noticias(), idioma)

    # Columna izquierda: lo que se puede leer aquí. Columna derecha: las noticias que solo se pueden abrir en su sitio.
    c_main, c_ext = st.columns([8, 3.2], gap="medium")
    with c_main:
        if noticias:
            _columna_principal(noticias, idioma)
        else:
            st.info("No hay noticias para leer en este idioma por ahora. Prueba con «Todos».")
    with c_ext:
        _panel_externas(externas)


# TITULO COLUMNA PRINCIPAL

def _columna_principal(noticias: list, idioma: str | None) -> None:
    """Dibuja la columna izquierda de la página: noticia principal, carrusel paginado y «Más noticias».

    Recibe las noticias legibles (ya filtradas por idioma, de la más nueva a la más vieja) y el idioma elegido, que se pasa a
    «Más noticias». No devuelve nada."""
    # --- Noticia PRINCIPAL (clic -> modal) ---
    # La más reciente; se centra con columnas laterales vacías y se envuelve en un contenedor con key para el CSS
    destacado = noticias[0]
    _, c_destacado, _ = st.columns([0.6, 11, 0.6])
    with c_destacado:
        with st.container(key="noticia_destacada"):
            st.html(f"""
                <div style="display:flex; gap:22px; align-items:flex-start; margin-bottom:22px; flex-wrap:wrap;">
                  <img src="{destacado['img']}" referrerpolicy="no-referrer"
                       style="width:360px; height:220px; object-fit:cover; border-radius:10px;
                              flex:0 0 360px; background:#161b22;">
                  <div style="flex:1; min-width:280px;">
                    <h2 style="color:#ffffff; font-size:26px; font-weight:800; line-height:1.25; margin:0 0 12px;">{destacado['title']}</h2>
                    <p style="color:#c9d1d9; font-size:15px; line-height:1.6; margin:0 0 10px;">
                       {destacado['desc'][:320]}</p>
                    <span style="color:#586174; font-size:12px;">{destacado.get('fuente', '')} &nbsp;·&nbsp; {destacado['fecha']} &nbsp;·&nbsp; Ver noticia</span>
                  </div>
                </div>
            """)
            if st.button("abrir", key="noticia_destacada_boton"):
                st.session_state.noticia_abierta = destacado
                st.rerun()

    # --- CARRUSEL paginado (4 por página, hasta 20, loop) ---
    # `pool` son las noticias del carrusel (sin la principal); `pag` la página actual con vuelta al inicio
    pool = noticias[1:1 + MAX_CARRUSEL]
    if not pool:
        renderizar_mas_noticias(idioma, {destacado["id"]})
        return
    numero_pagina = max(1, math.ceil(len(pool) / POR_PAGINA))
    if "noticias_pagina" not in st.session_state:
        st.session_state.noticias_pagina = 0
    pagina = st.session_state.noticias_pagina % numero_pagina
    ventana = pool[pagina * POR_PAGINA: pagina * POR_PAGINA + POR_PAGINA]

    # Flecha izquierda, tarjetas y flecha derecha en una sola fila
    c_anterior, c_tarjetas, c_next = st.columns([0.6, 11, 0.6], vertical_alignment="center")

    with c_anterior:
        if st.button("‹", key="noticias_anterior"):
            st.session_state.noticias_pagina = (pagina - 1) % numero_pagina
            st.rerun(scope="fragment")

    with c_tarjetas:
        columnas = st.columns(POR_PAGINA)
        for posicion, (columna, n) in enumerate(zip(columnas, ventana)):
            with columna:
                with st.container(key=f"nc_{posicion}"):
                    st.html(tarjeta_html(n))
                    if st.button("abrir", key=f"ncb_{posicion}"):
                        st.session_state.noticia_abierta = n
                        st.rerun()

    with c_next:
        if st.button("›", key="noticias_siguiente"):
            st.session_state.noticias_pagina = (pagina + 1) % numero_pagina
            st.rerun(scope="fragment")

    # --- Apartado "Más noticias" (sin repetir las que ya salen arriba) ---
    renderizar_mas_noticias(idioma, {destacado["id"]} | {n["id"] for n in pool})


# TITULO RENDERIZAR MAS NOTICIAS

def renderizar_mas_noticias(idioma: str | None = None, excluir: set | None = None):
    """Dibuja el apartado "Más noticias" (otras fuentes y categorías) en una cuadrícula de 4 columnas.

    Recibe el idioma por el que filtrar (None = todos) y el conjunto de ids de noticias que ya se muestran arriba para no
    repetirlas.

    Muestra al inicio 8 noticias y un botón "Ver más noticias" que revela 8 más (estado `mas_mostrar` en la
    sesión); cuando ya se mostró todo aparece "Ver menos". No dibuja nada si no hay noticias. No devuelve
    nada."""
    todas = [n for n in _filtrar(cargar_mas_noticias(), idioma) if n["lectura"] and n["id"] not in (excluir or set())]
    if not todas:
        return

    st.markdown(
        "<div style='margin:30px 0 16px; border-top:1px solid #1f2937; padding-top:20px;'>"
        "<span style='font-size:22px; font-weight:800; color:#e6edf3;'>Más noticias</span>"
        "<span style='color:#8b949e; font-size:13px; margin-left:8px;'>· Más fuentes y categorías</span></div>",
        unsafe_allow_html=True,
    )

    # "Ver más" progresivo: empieza en 8 y revela de a 8.
    mostrar = st.session_state.get("mas_mostrar", 8)
    ns = todas[:mostrar]

    _, c_cuadricula, _ = st.columns([0.6, 11, 0.6])
    with c_cuadricula:
        # Filas de 4 tarjetas; cada una en un contenedor con key único (ync_N) para su botón invisible
        for fila in range(0, len(ns), 4):
            columnas = st.columns(4)
            for k, (columna, n) in enumerate(zip(columnas, ns[fila:fila + 4])):
                with columna:
                    with st.container(key=f"ync_{fila + k}"):
                        st.html(tarjeta_html(n))
                        if st.button("abrir", key=f"yncb_{fila + k}"):
                            st.session_state.noticia_abierta = n
                            st.rerun()

        # Botón Ver más / Ver menos (centrado)
        _, c_boton, _ = st.columns([1, 1.4, 1])
        with c_boton:
            if mostrar < len(todas):
                restantes = len(todas) - mostrar
                if st.button(f"Ver más noticias ({restantes})", key="mas_ver", width="stretch"):
                    st.session_state.mas_mostrar = mostrar + 8
                    st.rerun(scope="fragment")
            elif mostrar > 8:
                if st.button("Ver menos", key="mas_menos", width="stretch"):
                    st.session_state.mas_mostrar = 8
                    st.rerun(scope="fragment")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara secciones .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
