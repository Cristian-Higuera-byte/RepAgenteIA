import html
import re

import streamlit as st
import MetaTrader5 as mt5  # type: ignore[import-untyped]
from typing import Any

from components.iconos import icono_activo
from components.live_feed import attrs as _live

try:
    from components.favoritos_bar import agregar_favorito, quitar_favorito
except ImportError:
    def agregar_favorito(ticker: str) -> Any:
        _ = ticker
        return None

    def quitar_favorito(ticker: str) -> Any:
        _ = ticker
        return None


# Altura (px) de la zona con scroll de la lista
ALTURA_LISTA = 640


_CSS = """
<style>
    /* Oculta el contenedor de este bloque de estilos (evita el hueco entre elementos) */
    div[data-testid="stElementContainer"]:has(.wl-css),
    div[data-testid="element-container"]:has(.wl-css) { display: none; }

    /* Panel general */
    .st-key-wl_panel {
        background: #0d1117;
        border: 1px solid #1f2937;
        border-radius: 10px;
        overflow: hidden;
    }
    .st-key-wl_panel,
    .st-key-wl_panel [data-testid="stVerticalBlock"],
    .st-key-wl_scroll { gap: 0 !important; }
    /* Barra de scroll fina y hueco simétrico en ambos lados: así el resaltado
       de la fila seleccionada queda centrado y nunca "sobresale" por la
       derecha (antes el gutter del scroll iba solo a la derecha). */
    .st-key-wl_scroll {
        scrollbar-gutter: stable both-edges;
        scrollbar-width: thin;
        scrollbar-color: #2b3550 transparent;
        padding-top: 6px;      /* separa la 1ª fila del encabezado */
        padding-bottom: 6px;   /* aire para la última fila */
    }
    .st-key-wl_scroll::-webkit-scrollbar { width: 6px; }
    .st-key-wl_scroll::-webkit-scrollbar-thumb {
        background: #2b3550; border-radius: 3px;
    }
    .st-key-wl_scroll::-webkit-scrollbar-track { background: transparent; }
    .st-key-wl_panel div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        border: none !important;
    }
    /* Anula el margin-bottom:-16px por defecto de los markdown (encabezado
       incluido) que montaba la lista sobre el encabezado. */
    .st-key-wl_panel div[data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }

    /* Encabezado (fondo opaco + por encima: evita que una fila resaltada se le
       monte por detrás) */
    .wl-head {
        padding: 14px 16px 12px; border-bottom: 1px solid #1f2937;
        background: #0d1117; position: relative; z-index: 2;
    }
    .wl-title {
        display: flex; align-items: center; gap: 8px;
        font-size: 16px; font-weight: 700; color: #ffffff;
    }
    .wl-sub { font-size: 12px; color: #8b949e; margin-top: 2px; }

    /* Scrollbar discreto */
    .st-key-wl_scroll ::-webkit-scrollbar { width: 6px; }
    .st-key-wl_scroll ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    .st-key-wl_scroll ::-webkit-scrollbar-track { background: transparent; }

    /* Fila de activo */
    [class*="st-key-wlrow_"] {
        position: relative;
        overflow: hidden;
        transition: background 0.15s ease;
    }
    /* Streamlit añade margen inferior por defecto a cada widget; lo anulamos
       en todos los hijos de la fila para que el overlay de selección y el
       cálculo de alto de la fila coincidan exactamente con el visual (.wl-row).
       CLAVE: stMarkdownContainer trae margin-bottom:-16px por defecto, que
       encogía el hueco de la fila (45px) respecto al contenido (.wl-row 61px),
       haciendo que cada fila se solapara 16px con la siguiente (redondeado
       cortado, resaltado montándose sobre el encabezado, overlay invadiendo). */
    [class*="st-key-wlrow_"] div[data-testid="stElementContainer"],
    [class*="st-key-wlrow_"] div[data-testid="element-container"],
    [class*="st-key-wlrow_"] div[data-testid="stMarkdownContainer"],
    [class*="st-key-wlrow_"] div[data-testid="stMarkdown"] {
        margin: 0 !important;
    }
    .wl-row {
        display: flex; align-items: center; gap: 10px;
        padding: 11px 74px 11px 12px;
        border-bottom: 1px solid #1a2130;
        box-sizing: border-box;
        line-height: 1.25;   /* evita que el interlineado infle la fila y el
                                contenido se salga del recuadro resaltado */
    }
    /* El resaltado se pinta en el CONTENEDOR exterior de la fila (no en el
       div interno), para que ocupe exactamente el mismo rectángulo que el
       área clicable/hover -- así queda perfectamente centrado, sin quedar
       "subido" respecto al contenido visible. */
    /* El resaltado se pinta sobre .wl-row (que envuelve EXACTO el contenido con
       su padding simétrico) y NO sobre el contenedor de Streamlit, que queda
       ~16px más corto que su contenido y descentraba/sobresalía el fondo.
       El hover se detecta en el contenedor (la fila entera es clicable). */
    [class*="st-key-wlrow_"]:hover .wl-row { background: rgba(255,255,255,0.04); border-radius: 8px; border-bottom-color: transparent; }
    .wl-row.sel { background: #1a2236; border-radius: 8px; border-bottom-color: transparent; }

    .wl-ico {
        flex: 0 0 32px; width: 32px; height: 32px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; font-weight: 800;
    }
    .wl-mid { flex: 1 1 auto; min-width: 0; overflow: hidden; }
    .wl-tk {
        font-size: 16px; font-weight: 700; color: #ffffff;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .wl-nm {
        font-size: 13px; color: #8b949e; margin-top: 2px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .wl-right { text-align: right; flex: 0 0 auto; white-space: nowrap; }
    .wl-px {
        font-size: 16px; font-weight: 700; color: #ffffff;
        font-variant-numeric: tabular-nums;
    }
    .wl-var { font-size: 13px; font-weight: 600; margin-top: 2px; font-variant-numeric: tabular-nums; }

    /* Botón "Seleccionar": invisible, cubre toda la fila (la fila entera es clicable).
       Se fijan los 4 bordes explícitos (no el shorthand "inset") y se anulan
       margin/padding con !important para que el área clicable llegue de
       verdad de borde a borde, sin importar los defaults de Streamlit. */
    [class*="st-key-wlsel_"] {
        position: absolute !important;
        top: 0 !important; right: 0 !important; bottom: 0 !important; left: 0 !important;
        width: 100% !important; height: 100% !important;
        margin: 0 !important; padding: 0 !important;
        z-index: 1;
    }
    [class*="st-key-wlsel_"] * {
        width: 100% !important;
        height: 100% !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [class*="st-key-wlsel_"] button {
        opacity: 0;
        cursor: pointer;
    }

    /* Botón de favorito: pequeño, a la derecha de la fila */
    [class*="st-key-wlfav_"] {
        position: absolute !important;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        width: 30px !important;
        margin: 0 !important;
        z-index: 3;
    }
    [class*="st-key-wlfav_"] button {
        width: 32px !important;
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #586174 !important;
        border-radius: 8px !important;
    }
    [class*="st-key-wlfav_"] button p { font-size: 20px !important; line-height: 1 !important; }
    [class*="st-key-wlfav_"] button:hover {
        background: rgba(255,255,255,0.08) !important;
        color: #f5c518 !important;
    }
    /* Favorito activo (type="primary") */
    [class*="st-key-wlfav_"] button[kind="primary"],
    [class*="st-key-wlfav_"] [data-testid="stBaseButton-primary"] {
        color: #f5c518 !important;
    }

    /* Botón ✕ (quitar de la lista): a la izquierda de la estrella */
    [class*="st-key-wlrm_"] {
        position: absolute !important;
        right: 40px;
        top: 50%;
        transform: translateY(-50%);
        width: 28px !important;
        margin: 0 !important;
        z-index: 3;
    }
    [class*="st-key-wlrm_"] button {
        width: 30px !important; height: 30px !important; min-height: 30px !important;
        padding: 0 !important; background: transparent !important; border: none !important;
        box-shadow: none !important; color: #586174 !important; border-radius: 8px !important;
    }
    [class*="st-key-wlrm_"] button p { font-size: 16px !important; line-height: 1 !important; }
    [class*="st-key-wlrm_"] button:hover {
        background: rgba(255,255,255,0.08) !important; color: #f85149 !important;
    }

    /* Botón inferior */
    .st-key-wl_add { padding: 12px 14px 14px; }
    .st-key-wl_add button {
        background: transparent !important;
        border: 1px dashed #30363d !important;
        color: #8b949e !important;
        border-radius: 8px !important;
        min-height: 38px !important;
    }
    .st-key-wl_add button:hover {
        border-color: #58a6ff !important;
        color: #ffffff !important;
    }
</style>
<span class="wl-css"></span>
"""


def _quitar_de_lista(ticker: str):
    """Quita un símbolo de la watchlist del usuario (Supabase + sesión)."""
    from tools import watchlist_manager as wl
    uid = (st.session_state.get("usuario_info") or {}).get("id")
    wl.quitar_simbolo(uid, ticker)
    st.session_state.get("datos_mercado_real", {}).pop(ticker, None)
    lst = st.session_state.get("watchlist_simbolos", [])
    if ticker in lst:
        lst.remove(ticker)
    favs = st.session_state.get("favoritos", [])
    if ticker in favs:
        favs.remove(ticker)
    if st.session_state.get("activo_seleccionado") == ticker:
        restantes = list(st.session_state.get("datos_mercado_real", {}).keys())
        st.session_state.activo_seleccionado = restantes[0] if restantes else "EURUSD..."


def renderizar_watchlist():
    from tools import watchlist_manager as wl

    # Lista de activos del USUARIO (los que tenga en su watchlist de Supabase)
    info_activos_real = st.session_state.get("datos_mercado_real", {})
    tickers_watchlist = st.session_state.get("watchlist_simbolos") or list(info_activos_real.keys())

    st.markdown(_CSS, unsafe_allow_html=True)

    if "activo_seleccionado" not in st.session_state:
        st.session_state.activo_seleccionado = "EURUSD..."

    with st.container(key="wl_panel"):
        # Encabezado
        st.markdown(
            """
            <div class='wl-head'>
                <div class='wl-title'><span>🔥</span><span>LISTA DE ACTIVOS</span></div>
                <div class='wl-sub'>Precios de activos en tiempo real</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Contenedor con altura fija y scroll vertical individual
        with st.container(height=ALTURA_LISTA, border=False, key="wl_scroll"):
            for ticker in tickers_watchlist:
                item = info_activos_real.get(ticker, {
                    "nombre": ticker,
                    "precio": 1.0000,
                    "var": "+0.00 (0.00%)",
                    "sube": True
                })

                base = wl.nombre_visible(ticker)
                slug = re.sub(r"\W", "", ticker)
                is_selected = (st.session_state.activo_seleccionado == ticker)
                color_var = "#2ebd85" if item.get("sube", True) else "#f6465d"

                precio_val = item.get('precio', 1.0)
                formato_precio = f"${precio_val:,.2f}" if precio_val > 100 else f"{precio_val:,.5f}"

                nombre = html.escape(str(item.get('nombre', ticker)))
                variacion = html.escape(str(item.get('var', '+0.00%')))
                clase_sel = " sel" if is_selected else ""

                es_favorito = ticker in st.session_state.get("favoritos", [])
                estrella = ":material/star:" if es_favorito else ":material/star_border:"
                ayuda = "Quitar de favoritos" if es_favorito else "Agregar a favoritos"

                with st.container(key=f"wlrow_{slug}"):
                    # Tarjeta visual del activo
                    st.markdown(f"""
                        <div class='wl-row{clase_sel}'>
                            {icono_activo(ticker, 34)}
                            <div class='wl-mid'>
                                <div class='wl-tk'>{html.escape(base)}</div>
                                <div class='wl-nm'>{nombre}</div>
                            </div>
                            <div class='wl-right'>
                                <div class='wl-px' {_live(ticker, 'px', pre='$' if precio_val > 100 else '')}>{formato_precio}</div>
                                <div class='wl-var' {_live(ticker, 'var', up='#2ebd85', dn='#f6465d')} style='color: {color_var};'>{variacion}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Botón invisible que cubre toda la fila -> selecciona el activo.
                    # scope="app" fuerza una reejecución de TODA la app (no solo de
                    # este fragmento), que es lo que hace que components/central_panel.py
                    # -- que lee este mismo st.session_state.activo_seleccionado --
                    # cambie de inmediato el precio, el símbolo y el gráfico en vivo.
                    if st.button("Seleccionar", key=f"wlsel_{slug}"):
                        # OJO: no mostrar elementos (st.toast) aquí dentro del
                        # fragmento justo antes de st.rerun(scope="app"): provoca
                        # el error de frontend "Cannot set a node at a delta path"
                        # y deja la app en blanco al cambiar de activo.
                        st.session_state.activo_seleccionado = ticker
                        st.rerun(scope="app")

                    # Estrella de favoritos
                    if st.button(
                        estrella,
                        key=f"wlfav_{slug}",
                        help=ayuda,
                        type="primary" if es_favorito else "secondary",
                    ):
                        if es_favorito:
                            quitar_favorito(ticker)
                        else:
                            agregar_favorito(ticker)
                        st.rerun(scope="app")

                    # Quitar de mi lista (✕)
                    if st.button(":material/close:", key=f"wlrm_{slug}", help="Quitar de mi lista"):
                        _quitar_de_lista(ticker)
                        st.rerun(scope="app")

        with st.container(key="wl_add"):
            if st.button("➕ Agregar activo", use_container_width=True):
                from components.buscador import abrir_buscador
                abrir_buscador()
                st.rerun()  # app scope: para que app.py renderice el diálogo