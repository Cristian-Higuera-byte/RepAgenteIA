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

"""Página "Mercados": cabecera, pulso del mercado, pestañas por categoría con buscador y orden, tabla en vivo y
ficha del instrumento (modal).

Es el punto de entrada del paquete: ensambla las secciones de `secciones.py`, el modal de `ficha.py` y los
estilos de `estilos.css`.
"""
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from componentes_plataforma.flujo_precios import intervalo
from componentes_plataforma.mercados.broker import elementos_en_cache
from componentes_plataforma.mercados.cargando import JS_CARGANDO
from componentes_plataforma.mercados.constantes import CATALOGO, ORDENES
from componentes_plataforma.mercados.estilos import CSS
from componentes_plataforma.mercados.ficha import mostrar_ficha
from componentes_plataforma.mercados.secciones import (categoria_lista, precargar_todas_las_categorias, pulso_listo, renderizar_tabla,
                                                         resumen)
from herramientas.puente_mt5 import NOMBRE_PROVEEDOR, inicializar_mt5


# TITULO RENDERIZAR PANEL MERCADOS

def renderizar_panel_mercados(main=None):
    """Dibuja la página Mercados completa.

    El parámetro `main` se acepta por compatibilidad con la firma de las demás páginas y no se usa.
    Inicializa MT5, inyecta el CSS, pinta la cabecera, el pulso del mercado y la tabla (ambos en fragmentos
    que se refrescan solos), los controles de categoría, búsqueda y orden, el script del indicador
    "cargando" y, si hay un instrumento seleccionado en `mercados_detalle`, abre su ficha. No devuelve nada."""
    inicializar_mt5()
    precargar_todas_las_categorias()    # (ya lanzada al iniciar la sesión; aquí solo se asegura) las demás pestañas se preparan en segundo plano
    st.html(CSS)
    # intervalo("x") es None cuando el feed SSE en vivo está activo; si no, se refresca por sondeo
    en_vivo = intervalo("x") is None
    st.html(
        "<div class='mercados-encabezado'><div><div class='mercados-titulo'>Mercados</div>"
        f"<div class='mercados-subtitulo'>Cotizaciones de {NOMBRE_PROVEEDOR} · variación respecto del cierre "
        "anterior · haz clic en un instrumento para ver su ficha</div></div>"
        f"<span class='mercados-live'><span class='mercados-dot{'' if en_vivo else ' off'}'></span>"
        f"{'Datos en tiempo real' if en_vivo else 'Actualización cada 3 s'}</span></div>"
    )

    # Mientras los datos se están cargando (primera visita sin precarga lista) el fragmento se revisa cada 2 s; en cuanto están, se
    # redibuja la página para volver al ritmo normal.
    pulso_frio = not pulso_listo()

    @st.fragment(run_every="2s" if pulso_frio else intervalo("3s", "30s"))
    def _resumen_vivo():
        """Fragmento que repinta las tarjetas del pulso del mercado en cada refresco."""
        resumen()
        if pulso_frio and pulso_listo():
            st.rerun(scope="app")
    _resumen_vivo()
    st.html("<div style='height:6px;'></div>")

    # Controles: pestañas por categoría (con cantidad de instrumentos), buscador y selector de orden
    categorias = list(CATALOGO.keys())
    # Cantidad de instrumentos por categoría: solo las que ya se resolvieron (no se espera a las demás; el número aparece cuando están listas).
    conteo = {c: len(x) for c in categorias if (x := elementos_en_cache(c)) is not None}
    c_pestanas, c_q, c_orden = st.columns([3.2, 1.3, 0.9], vertical_alignment="bottom")
    with c_pestanas:
        with st.container(key="mercados_pestanas"):
            st.segmented_control(
                "Categoría", categorias, default=categorias[0], key="mercados_categoria",
                format_func=lambda c: f"{c}  {conteo[c]}" if c in conteo else c, label_visibility="collapsed",
            ) or categorias[0]
    with c_q:
        st.text_input("Buscar", key="mercados_q", placeholder="Filtrar instrumentos…",
                      label_visibility="collapsed", icon=":material/search:")
    with c_orden:
        st.selectbox("Ordenar", ORDENES, key="mercados_orden", label_visibility="collapsed")

    categoria_frio = categoria_actual = st.session_state.get("mercados_categoria") or categorias[0]
    categoria_frio = not categoria_lista(categoria_actual)

    @st.fragment(run_every="2s" if categoria_frio else intervalo("3s", "30s"))
    def _tabla_en_vivo():
        """Fragmento que repinta la nota, la tabla de la categoría activa y el pie con la hora de actualización."""
        categoria = st.session_state.get("mercados_categoria") or categorias[0]
        n = len(elementos_en_cache(categoria) or [])
        if n:
            st.html(f"<div class='mercados-nota'><span class='ico'>local_fire_department</span>"
                    f"<span>Mostrando <b>los {n} {categoria.lower()} más seguidos del mercado</b></span></div>")
        total, mostrados = renderizar_tabla(categoria)
        if total is not None:
            st.html(f"<div class='mercados-pie'>{mostrados} de {total} instrumentos · {categoria} · "
                    f"actualizado {datetime.now().strftime('%H:%M:%S')}</div>")
        if categoria_frio and categoria_lista(categoria):
            st.rerun(scope="app")
    _tabla_en_vivo()

    # Script del indicador "cargando" (fuera del flujo, no ocupa espacio)
    with st.container(key="mercados_carga_js"):
        components.html(JS_CARGANDO, height=0)

    # El modal se abre con la bandera y se renderiza AQUÍ (fuera de los fragmentos en
    # vivo) para no chocar con su auto-refresco (evita pantallas en blanco).
    if st.session_state.get("mercados_detalle"):
        mostrar_ficha()


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
