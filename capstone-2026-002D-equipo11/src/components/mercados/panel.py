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

from components.flujo_precios import intervalo
from components.mercados.broker import elementos
from components.mercados.cargando import JS_CARGANDO
from components.mercados.constantes import CATALOGO, ORDENES
from components.mercados.estilos import CSS
from components.mercados.ficha import mostrar_ficha
from components.mercados.secciones import renderizar_tabla, resumen
from tools.puente_mt5 import inicializar_mt5


def renderizar_panel_mercados(main=None):
    """Dibuja la página Mercados completa.

    El parámetro `main` se acepta por compatibilidad con la firma de las demás páginas y no se usa.
    Inicializa MT5, inyecta el CSS, pinta la cabecera, el pulso del mercado y la tabla (ambos en fragmentos
    que se refrescan solos), los controles de categoría, búsqueda y orden, el script del indicador
    "cargando" y, si hay un instrumento seleccionado en `mkt_detalle`, abre su ficha. No devuelve nada."""
    inicializar_mt5()
    st.html(CSS)
    # intervalo("x") es None cuando el feed SSE en vivo está activo; si no, se refresca por sondeo
    en_vivo = intervalo("x") is None
    st.html(
        "<div class='mkt-hdr'><div><div class='mkt-title'>Mercados</div>"
        "<div class='mkt-sub'>Cotizaciones de MetaTrader 5 · variación respecto del cierre "
        "anterior · haz clic en un instrumento para ver su ficha</div></div>"
        f"<span class='mkt-live'><span class='mkt-dot{'' if en_vivo else ' off'}'></span>"
        f"{'Datos en tiempo real' if en_vivo else 'Actualización cada 3 s'}</span></div>"
    )

    @st.fragment(run_every=intervalo("3s", "30s"))
    def _resumen_vivo():
        """Fragmento que repinta las tarjetas del pulso del mercado en cada refresco."""
        resumen()
    _resumen_vivo()
    st.html("<div style='height:6px;'></div>")

    # Controles: pestañas por categoría (con cantidad de instrumentos), buscador y selector de orden
    categorias = list(CATALOGO.keys())
    conteo = {c: len(elementos(c)) for c in categorias}
    c_tabs, c_q, c_ord = st.columns([3.2, 1.3, 0.9], vertical_alignment="bottom")
    with c_tabs:
        with st.container(key="mkt_tabs"):
            st.segmented_control(
                "Categoría", categorias, default=categorias[0], key="mkt_cat",
                format_func=lambda c: f"{c}  {conteo.get(c, 0)}", label_visibility="collapsed",
            ) or categorias[0]
    with c_q:
        st.text_input("Buscar", key="mkt_q", placeholder="Filtrar instrumentos…",
                      label_visibility="collapsed", icon=":material/search:")
    with c_ord:
        st.selectbox("Ordenar", ORDENES, key="mkt_orden", label_visibility="collapsed")

    @st.fragment(run_every=intervalo("3s", "30s"))
    def _tabla_en_vivo():
        """Fragmento que repinta la nota, la tabla de la categoría activa y el pie con la hora de actualización."""
        categoria = st.session_state.get("mkt_cat") or categorias[0]
        n = len(elementos(categoria))
        st.html(f"<div class='mkt-nota'><span class='ico'>local_fire_department</span>"
                f"<span>Mostrando <b>los {n} {categoria.lower()} más seguidos del mercado</b></span></div>")
        total, mostrados = renderizar_tabla(categoria)
        st.html(f"<div class='mkt-pie'>{mostrados} de {total} instrumentos · {categoria} · "
                f"actualizado {datetime.now().strftime('%H:%M:%S')}</div>")
    _tabla_en_vivo()

    # Script del indicador "cargando" (fuera del flujo, no ocupa espacio)
    with st.container(key="mkt_loadjs"):
        components.html(JS_CARGANDO, height=0)

    # El modal se abre con la bandera y se renderiza AQUÍ (fuera de los fragmentos en
    # vivo) para no chocar con su auto-refresco (evita pantallas en blanco).
    if st.session_state.get("mkt_detalle"):
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
