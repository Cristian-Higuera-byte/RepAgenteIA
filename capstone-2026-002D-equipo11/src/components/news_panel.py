"""
news_panel.py
-------------
Panel de noticias estilo Investing.com:
  - Recuadro superior (Agente Piña y Jara) con reloj EN VIVO (refresca cada 1 s).
  - Noticia PRINCIPAL grande + CARRUSEL paginado (‹ ›, de 4 en 4 hasta 20, loop).
  - Al hacer clic en cualquier noticia se abre un MODAL con foto, título, un
    resumen/análisis del agente (IA, bajo demanda y cacheado) y el enlace a la
    fuente. (Investing bloquea traer el texto completo del artículo — 403 —,
    por eso el modal muestra un resumen del agente en vez del artículo crudo.)
Fuente: RSS de Investing.com en español (título, enlace, imagen, fecha).
"""
import re
import math
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from types import ModuleType
from typing import Optional

import streamlit as st

_FUENTES = [
    "https://es.investing.com/rss/news_25.rss",
    "https://es.investing.com/rss/news.rss",
    "https://es.investing.com/rss/news_285.rss",
]

_PLACEHOLDER = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&q=60"
_POR_PAGINA = 4
_MAX_CARRUSEL = 20


def _limpiar(texto: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", texto or "")).strip()


def _fecha_a_ts(pubdate: str) -> float:
    pubdate = (pubdate or "").strip()
    if not pubdate:
        return 0.0
    try:
        return parsedate_to_datetime(pubdate).timestamp()
    except Exception:
        pass
    txt = pubdate[:19].replace("T", " ")
    try:
        return datetime.strptime(txt, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return 0.0


def _fecha_local(ts: float, raw: str) -> str:
    try:
        return datetime.fromtimestamp(ts).strftime("%d-%m-%Y %H:%M") if ts else raw
    except Exception:
        return raw


@st.cache_data(ttl=30, show_spinner=False)
def _cargar_noticias() -> list[dict]:
    vistos: set[str] = set()
    todas: list[dict] = []
    for url in _FUENTES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = r.read()
            root = ET.fromstring(data)
            for it in root.findall(".//item"):
                titulo = _limpiar(it.findtext("title") or "")
                link = (it.findtext("link") or "").strip()
                if not titulo or not link or link in vistos:
                    continue
                vistos.add(link)
                enc = it.find("enclosure")
                media = it.find("{http://search.yahoo.com/mrss/}content")
                img = (enc.get("url") if enc is not None and enc.get("url")
                       else media.get("url") if media is not None and media.get("url")
                       else _PLACEHOLDER)
                ts = _fecha_a_ts((it.findtext("pubDate") or "").strip())
                todas.append({
                    "title": titulo,
                    "link": link,
                    "desc": _limpiar(it.findtext("description") or ""),
                    "img": img,
                    "_ts": ts,
                    "fecha": _fecha_local(ts, (it.findtext("pubDate") or "")[:16]),
                })
        except Exception:
            continue
    todas.sort(key=lambda n: n["_ts"], reverse=True)
    return todas


# Feeds adicionales (Investing en español, actuales y con foto): otras categorías
_FUENTES_MAS = [
    "https://es.investing.com/rss/news_301.rss",  # Criptomonedas
    "https://es.investing.com/rss/news_1.rss",     # Economía / Forex
    "https://es.investing.com/rss/news_95.rss",    # Forex / Mercados
]


@st.cache_data(ttl=60, show_spinner=False)
def _cargar_mas_noticias() -> list[dict]:
    """'Más noticias': otras categorías de Investing en español (actuales, con foto)."""
    vistos: set[str] = set()
    out: list[dict] = []
    for url in _FUENTES_MAS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                root = ET.fromstring(r.read())
            for it in root.findall(".//item"):
                titulo = _limpiar(it.findtext("title") or "")
                link = (it.findtext("link") or "").strip()
                if not titulo or not link or link in vistos:
                    continue
                vistos.add(link)
                enc = it.find("enclosure")
                media = it.find("{http://search.yahoo.com/mrss/}content")
                img = (enc.get("url") if enc is not None and enc.get("url")
                       else media.get("url") if media is not None and media.get("url")
                       else _PLACEHOLDER)
                ts = _fecha_a_ts((it.findtext("pubDate") or "").strip())
                out.append({
                    "title": titulo,
                    "link": link,
                    "desc": _limpiar(it.findtext("description") or ""),
                    "img": img,
                    "_ts": ts,
                    "fecha": _fecha_local(ts, (it.findtext("pubDate") or "")[:16]),
                })
        except Exception:
            continue
    out.sort(key=lambda n: n["_ts"], reverse=True)
    return out


# ---------------------------------------------------------------- Resumen IA
def _resumen_agente(n: dict, main) -> str:
    """Genera (y cachea por enlace) un resumen del agente para la noticia."""
    cache = st.session_state.setdefault("_resumenes_noticias", {})
    if n["link"] in cache:
        return cache[n["link"]]

    texto = ""
    if main is not None and hasattr(main, "chat_agente"):
        try:
            detalle = f" Detalle: {n['desc']}" if n.get("desc") else ""
            prompt = (
                "Actúa como analista financiero. En español y en máximo 3 párrafos, "
                f"resume y explica el posible impacto de esta noticia. Título: '{n['title']}'.{detalle}"
            )
            resp, _ = main.chat_agente(prompt, historial=[])
            texto = (resp or "").strip()
        except Exception:
            texto = ""
    if not texto:
        texto = (n.get("desc") or
                 "No hay más detalle disponible desde la fuente. Usa el botón para leer "
                 "la noticia completa en Investing.com.")
    cache[n["link"]] = texto
    return texto


def _contenido_modal(n: dict, main):
    st.html(f"""
        <img src="{n['img']}" referrerpolicy="no-referrer"
             style="width:100%; height:260px; object-fit:cover; border-radius:10px; background:#161b22;">
        <h2 style="color:#ffffff; font-size:24px; font-weight:800; line-height:1.3; margin:14px 0 6px;">{n['title']}</h2>
        <p style="color:#586174; font-size:12px; margin:0 0 12px;">{n['fecha']}</p>
    """)
    st.markdown("<span style='color:#58a6ff; font-weight:700;'>📝 Resumen del agente</span>",
                unsafe_allow_html=True)
    with st.spinner("Generando resumen de la noticia…"):
        resumen = _resumen_agente(n, main)
    st.markdown(f"<div style='font-size:15px; line-height:1.6; color:#c9d1d9;'>{resumen}</div>",
                unsafe_allow_html=True)
    st.markdown("---")
    st.link_button("Leer la noticia completa en la fuente ↗", n["link"])


def _abrir_modal(n: dict, main):
    def _al_cerrar():
        st.session_state.noticia_abierta = None

    @st.dialog("Noticia", width="large", on_dismiss=_al_cerrar)
    def _dlg():
        _contenido_modal(n, main)

    _dlg()


# ---------------------------------------------------------------- Render
def renderizar_panel_noticias(main: Optional[ModuleType] = None):
    # Si hay una noticia seleccionada, se abre el modal desde el flujo principal
    # (no desde un fragmento) para que funcione correctamente.
    if st.session_state.get("noticia_abierta") is not None:
        _abrir_modal(st.session_state["noticia_abierta"], main)

    @st.fragment(run_every="1s")
    def _cabecera_live():
        _render_cabecera()
    _cabecera_live()

    @st.fragment(run_every="30s")
    def _contenido():
        _render_contenido()
    _contenido()


def _render_cabecera():
    hora = datetime.now().strftime("%H:%M:%S")
    st.html(f"""
        <div style='background-color:#161b22; padding:12px 14px; border-radius:8px;
                    border:1px solid #30363d; margin-bottom:14px;'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <p style='margin:0; font-weight:bold; font-size:20px;'>🤖 Agente Piña y Jara</p>
                    <p style='margin:0; font-size:12px; color:#8b949e;'>Modo de Análisis Inteligente</p>
                </div>
                <span style='font-size:12px; color:#3fb950; font-weight:bold;'>● En vivo · {hora}</span>
            </div>
            <hr style='border-color:#30363d; margin:8px 0;'>
            <p style='margin:0; font-size:13px; color:#3fb950; font-weight:bold;'>● Sistema Activo y Sincronizado</p>
        </div>
    """)


_CSS_CARRUSEL = """
<style>
    [class*="st-key-news_prev"] button, [class*="st-key-news_next"] button {
        background:#161b22 !important; border:1px solid #30363d !important;
        color:#e6edf3 !important; border-radius:50% !important;
        width:40px !important; height:40px !important; min-height:40px !important;
        font-size:20px !important; padding:0 !important;
    }
    [class*="st-key-news_prev"] button:hover, [class*="st-key-news_next"] button:hover {
        border-color:#58a6ff !important; color:#58a6ff !important;
    }
    /* Tarjeta / principal clicables: botón invisible que cubre todo.
       Se fijan los 4 bordes explícitos (no el shorthand inset) — igual que en
       watchlist.py — porque con inset el área clicable no se activa bien. */
    .st-key-nhero, [class*="st-key-nc_"], [class*="st-key-ync_"] { position:relative; }
    [class*="st-key-nhero_btn"], [class*="st-key-ncb_"], [class*="st-key-yncb_"] {
        position:absolute !important;
        top:0 !important; right:0 !important; bottom:0 !important; left:0 !important;
        width:100% !important; height:100% !important;
        margin:0 !important; padding:0 !important; z-index:2;
    }
    [class*="st-key-nhero_btn"] *, [class*="st-key-ncb_"] *, [class*="st-key-yncb_"] * {
        width:100% !important; height:100% !important; min-height:0 !important;
        margin:0 !important; padding:0 !important;
    }
    [class*="st-key-nhero_btn"] button, [class*="st-key-ncb_"] button, [class*="st-key-yncb_"] button {
        opacity:0 !important; cursor:pointer !important;
    }
</style>
"""


def _tarjeta_html(n: dict) -> str:
    return f"""
      <div style="display:flex; flex-direction:column;">
        <img src="{n['img']}" referrerpolicy="no-referrer"
             style="width:100%; height:130px; object-fit:cover; border-radius:10px; background:#161b22;">
        <p style="color:#e6edf3; font-size:14px; font-weight:600; line-height:1.3;
                  margin:9px 0 4px; display:-webkit-box; -webkit-line-clamp:2;
                  -webkit-box-orient:vertical; overflow:hidden;">{n['title']}</p>
        <p style="color:#8b949e; font-size:12px; line-height:1.4; margin:0 0 6px;
                  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
                  overflow:hidden;">{n['desc'][:110]}</p>
        <span style="color:#586174; font-size:11px;">{n['fecha']}</span>
      </div>
    """


def _render_contenido():
    noticias = _cargar_noticias()
    if not noticias:
        st.info("No se pudieron cargar las noticias en este momento. Reintenta en unos minutos.")
        return

    st.markdown(_CSS_CARRUSEL, unsafe_allow_html=True)

    # Título de la sección (con línea superior, igual que "Más noticias")
    st.markdown(
        "<div style='border-top:1px solid #1f2937; padding-top:12px; margin:-22px 0 14px;'>"
        "<span style='font-size:24px; font-weight:800; color:#e6edf3;'>Noticias</span>"
        "<span style='color:#8b949e; font-size:13px; margin-left:8px;'>"
        "· Mercado de valores, Últimas noticias y Economía</span></div>",
        unsafe_allow_html=True,
    )

    # --- Noticia PRINCIPAL (clic -> modal) ---
    hero = noticias[0]
    _, c_hero, _ = st.columns([0.6, 11, 0.6])
    with c_hero:
        with st.container(key="nhero"):
            st.html(f"""
                <div style="display:flex; gap:22px; align-items:flex-start; margin-bottom:22px; flex-wrap:wrap;">
                  <img src="{hero['img']}" referrerpolicy="no-referrer"
                       style="width:360px; height:220px; object-fit:cover; border-radius:10px;
                              flex:0 0 360px; background:#161b22;">
                  <div style="flex:1; min-width:280px;">
                    <h2 style="color:#ffffff; font-size:26px; font-weight:800; line-height:1.25; margin:0 0 12px;">{hero['title']}</h2>
                    <p style="color:#c9d1d9; font-size:15px; line-height:1.6; margin:0 0 10px;">
                       {hero['desc'][:320]}</p>
                    <span style="color:#586174; font-size:12px;">{hero['fecha']} &nbsp;·&nbsp; Ver noticia</span>
                  </div>
                </div>
            """)
            if st.button("abrir", key="nhero_btn"):
                st.session_state.noticia_abierta = hero
                st.rerun()

    # --- CARRUSEL paginado (4 por página, hasta 20, loop) ---
    pool = noticias[1:1 + _MAX_CARRUSEL]
    if not pool:
        return
    num_pag = max(1, math.ceil(len(pool) / _POR_PAGINA))
    if "news_pag" not in st.session_state:
        st.session_state.news_pag = 0
    pag = st.session_state.news_pag % num_pag
    ventana = pool[pag * _POR_PAGINA: pag * _POR_PAGINA + _POR_PAGINA]

    c_prev, c_cards, c_next = st.columns([0.6, 11, 0.6], vertical_alignment="center")

    with c_prev:
        if st.button("‹", key="news_prev"):
            st.session_state.news_pag = (pag - 1) % num_pag
            st.rerun(scope="fragment")

    with c_cards:
        cols = st.columns(_POR_PAGINA)
        for pos, (col, n) in enumerate(zip(cols, ventana)):
            with col:
                with st.container(key=f"nc_{pos}"):
                    st.html(_tarjeta_html(n))
                    if st.button("abrir", key=f"ncb_{pos}"):
                        st.session_state.noticia_abierta = n
                        st.rerun()

    with c_next:
        if st.button("›", key="news_next"):
            st.session_state.news_pag = (pag + 1) % num_pag
            st.rerun(scope="fragment")

    # --- Apartado "Más noticias" (Yahoo Finance) ---
    _render_mas_noticias()


def _render_mas_noticias():
    todas = _cargar_mas_noticias()
    if not todas:
        return

    st.markdown(
        "<div style='margin:30px 0 16px; border-top:1px solid #1f2937; padding-top:20px;'>"
        "<span style='font-size:22px; font-weight:800; color:#e6edf3;'>Más noticias</span>"
        "<span style='color:#8b949e; font-size:13px; margin-left:8px;'>· Cripto, Forex y Economía</span></div>",
        unsafe_allow_html=True,
    )

    # "Ver más" progresivo: empieza en 8 y revela de a 8.
    mostrar = st.session_state.get("mas_mostrar", 8)
    ns = todas[:mostrar]

    _, c_grid, _ = st.columns([0.6, 11, 0.6])
    with c_grid:
        for fila in range(0, len(ns), 4):
            cols = st.columns(4)
            for k, (col, n) in enumerate(zip(cols, ns[fila:fila + 4])):
                with col:
                    with st.container(key=f"ync_{fila + k}"):
                        st.html(_tarjeta_html(n))
                        if st.button("abrir", key=f"yncb_{fila + k}"):
                            st.session_state.noticia_abierta = n
                            st.rerun()

        # Botón Ver más / Ver menos (centrado)
        _, c_btn, _ = st.columns([1, 1.4, 1])
        with c_btn:
            if mostrar < len(todas):
                restantes = len(todas) - mostrar
                if st.button(f"Ver más noticias ({restantes})", key="mas_ver", width="stretch"):
                    st.session_state.mas_mostrar = mostrar + 8
                    st.rerun(scope="fragment")
            elif mostrar > 8:
                if st.button("Ver menos", key="mas_menos", width="stretch"):
                    st.session_state.mas_mostrar = 8
                    st.rerun(scope="fragment")