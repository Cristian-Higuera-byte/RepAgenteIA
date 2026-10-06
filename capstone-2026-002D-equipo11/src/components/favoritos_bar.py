"""
favoritos_bar.py
----------------
Barra superior de activos favoritos del dashboard, estilo terminal de trading
(mockup): panel con encabezado "Mis Favoritos" + contador, paginación con
flechas, "Ver todos" y un engranaje para gestionar. Cada tarjeta muestra ícono,
nombre, precio en vivo, variación y un mini-gráfico (sparkline).

Los favoritos se guardan por usuario en Supabase (columna `favorito` de
watchlist_usuario, vía tools/watchlist_manager).
"""
import base64
import re

import streamlit as st

from components.live_feed import attrs as _live
from components.iconos import icono_activo as _icono
from tools import watchlist_manager as wl

FAVORITOS_MAX = 6       # tope de favoritos por usuario (solo caben 6 en una fila)
_VISIBLES = 6           # tarjetas visibles

FAVORITOS_DEFAULT = wl.FAVORITOS_DEFAULT


_CSS = """
<style>
  .st-key-fav_panel {
    background:#0d1117; border:1px solid #1f2630; border-radius:14px;
    padding:8px 16px 10px; margin-bottom:10px;
  }
  /* Menos espacio entre el encabezado y las tarjetas */
  .st-key-fav_panel [data-testid="stVerticalBlock"] { gap:.3rem !important; }
  .st-key-fav_panel [data-testid="stHorizontalBlock"] { gap:10px !important; }
  .fav-head { display:flex; align-items:center; gap:10px; margin:0; }
  .fav-star { color:#f0b429; font-size:18px; line-height:1; }
  .fav-title { color:#e6edf3; font-weight:700; font-size:15px; }
  .fav-badge { background:#1f2937; color:#9aa4b2; font-size:12px; font-weight:600;
               padding:1px 9px; border-radius:10px; }
  .fav-card { width:100%; box-sizing:border-box; display:flex; justify-content:space-between;
              align-items:center; gap:10px; background:#0f1620; border:1px solid #202a37;
              border-radius:12px; padding:10px 14px; transition:border-color .15s ease; }
  .fav-card:hover { border-color:#2f3d4f; }
  .fav-l { display:flex; flex-direction:column; gap:2px; min-width:0; }
  .fav-top { display:flex; align-items:center; gap:8px; }
  .fav-ic { display:inline-flex; align-items:center; flex:0 0 auto; }
  .fav-tk { color:#e6edf3; font-weight:700; font-size:13px; white-space:nowrap; }
  .fav-px { color:#ffffff; font-family:ui-monospace,Consolas,monospace;
            font-weight:700; font-size:16px; line-height:1.15; }
  .fav-var { font-size:11px; font-weight:600; white-space:nowrap; }
  .fav-spark { flex:0 0 auto; display:flex; align-items:center; }
  .fav-empty { color:#6e7681; font-size:13px; padding:14px 2px; }

  /* Cada slot es contenedor relativo para posicionar la ✕ sobre la tarjeta */
  [class*="st-key-favslot_"] { position:relative; }

  /* Tarjeta del activo que está en el gráfico (como la fila .sel de la watchlist) */
  /* Sutil: mismo fondo que la fila seleccionada de la watchlist (.wl-row.sel),
     borde apenas más claro que el normal (#202a37) — sin azul llamativo. */
  .fav-card.sel { border-color:#2f3d4f; background:#1a2236; }

  /* Botón invisible que cubre TODA la tarjeta -> selecciona el activo
     (mismo patrón que wlsel_ en watchlist.py). Queda bajo la ✕ (z-index 6). */
  [class*="st-key-favsel_"] {
    position:absolute !important; inset:0 !important;
    width:100% !important; height:100% !important;
    margin:0 !important; padding:0 !important; z-index:1;
  }
  [class*="st-key-favsel_"] * {
    width:100% !important; height:100% !important; min-height:0 !important;
    margin:0 !important; padding:0 !important;
  }
  [class*="st-key-favsel_"] button { opacity:0; cursor:pointer; }
  [class*="st-key-favx_"] { position:absolute !important; top:3px; right:3px;
                            z-index:6; width:auto !important; min-width:0 !important; }
  [class*="st-key-favx_"] button {
    background:transparent !important; border:none !important; box-shadow:none !important;
    color:#5c636e !important; padding:0 5px !important; min-height:0 !important;
    height:20px !important; line-height:1 !important; font-size:13px !important;
  }
  [class*="st-key-favx_"] button:hover {
    color:#f85149 !important; background:transparent !important; border:none !important;
  }
  /* Botón "+" en el espacio libre: tarjeta punteada del mismo alto */
  [class*="st-key-favadd"] button {
    width:100% !important; min-height:74px !important; background:transparent !important;
    border:1px dashed #2f3d4f !important; color:#8b949e !important; border-radius:12px !important;
    font-size:20px !important;
  }
  [class*="st-key-favadd"] button:hover { border-color:#3fb950 !important; color:#e6edf3 !important; }
</style>
"""


def icono_activo(ticker: str, size: int = 30) -> str:
    """Ícono del activo (estilo XM). Lo define components/iconos.py para todo el
    dashboard; se mantiene aquí por compatibilidad con quien lo importa."""
    return _icono(ticker, size)


def _sparkline_svg(vals: list, color: str, w: int = 92, h: int = 40) -> str:
    """Mini-gráfico SVG (línea + área con degradado) a partir de una lista de precios."""
    vals = [v for v in (vals or []) if v is not None]
    if len(vals) < 2:
        base = vals[0] if vals else 0.0
        vals = [base, base]
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    n = len(vals)
    pad = 3
    pts = []
    for i, v in enumerate(vals):
        x = (i * (w / (n - 1))) if n > 1 else 0
        y = h - pad - ((v - lo) / rng) * (h - 2 * pad)
        pts.append(f"{x:.1f},{y:.1f}")
    linea = " ".join(pts)
    area = f"0,{h} " + linea + f" {w},{h}"
    gid = "sp" + str(abs(hash((color, n, vals[-1]))) % 100000)
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
        f"viewBox='0 0 {w} {h}' preserveAspectRatio='none'>"
        f"<defs><linearGradient id='{gid}' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0' stop-color='{color}' stop-opacity='0.30'/>"
        f"<stop offset='1' stop-color='{color}' stop-opacity='0'/></linearGradient></defs>"
        f"<polygon points='{area}' fill='url(#{gid})'/>"
        f"<polyline points='{linea}' fill='none' stroke='{color}' stroke-width='1.6' "
        f"stroke-linejoin='round' stroke-linecap='round'/></svg>"
    )
    # st.html sanea el SVG en línea → se incrusta como imagen data-URI (sí renderiza)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"<img src='data:image/svg+xml;base64,{b64}' width='{w}' height='{h}' style='display:block;'>"


def _fmt_precio(precio: float) -> str:
    if precio >= 100:
        return f"{precio:,.2f}"
    return f"{precio:,.5f}"


def _uid():
    usuario = st.session_state.get("usuario_info") or {}
    return usuario.get("id") if isinstance(usuario, dict) else None


def _init_favoritos():
    """Carga los favoritos del usuario desde Supabase (una vez por sesión)."""
    if "favoritos" not in st.session_state:
        favs = wl.obtener_favoritos(_uid())
        st.session_state.favoritos = favs if favs else list(FAVORITOS_DEFAULT)


def agregar_favorito(ticker: str):
    """Agrega un activo a favoritos (respetando el máximo y sin duplicar)."""
    _init_favoritos()
    limpio = ticker.replace("...", "")
    if ticker in st.session_state.favoritos:
        st.toast(f"⭐ {limpio} ya está en tus favoritos")
        return
    if len(st.session_state.favoritos) >= FAVORITOS_MAX:
        st.toast(f"⚠️ Máximo {FAVORITOS_MAX} favoritos. Quita uno primero.")
        return
    st.session_state.favoritos.append(ticker)
    wl.marcar_favorito(_uid(), ticker, True)
    st.toast(f"⭐ {limpio} agregado a favoritos")


def quitar_favorito(ticker: str):
    _init_favoritos()
    if ticker in st.session_state.favoritos:
        st.session_state.favoritos.remove(ticker)
        wl.marcar_favorito(_uid(), ticker, False)


def _tarjeta_html(tk: str, datos: dict) -> str:
    item = datos.get(tk, {"precio": 0.0, "var": "", "sube": True})
    sube = item.get("sube", True)
    color = "#3fb950" if sube else "#f85149"
    precio = item.get("precio", 0.0)
    var = item.get("var", "") or "0.00 (0.00%)"
    nombre = tk.replace("...", "")
    spark_vals = st.session_state.get("_spark", {}).get(tk, [])
    spark = _sparkline_svg(spark_vals, color)
    sel = " sel" if st.session_state.get("activo_seleccionado") == tk else ""
    return (
        f"<div class='fav-card{sel}'>"
        "<div class='fav-l'>"
        f"<div class='fav-top'><span class='fav-ic'>{icono_activo(tk)}</span>"
        f"<span class='fav-tk'>{nombre}</span></div>"
        f"<div class='fav-px' {_live(tk, 'px')}>{_fmt_precio(precio)}</div>"
        f"<div class='fav-var' {_live(tk, 'var')} style='color:{color};'>{var}</div>"
        "</div>"
        # data-pj-spark: el feed en vivo (live_feed.py) redibuja este mini-gráfico
        # en el navegador con cada tick; data-pj-vals = semilla del histórico.
        f"<span class='fav-spark' data-pj-spark='{tk}' "
        f"data-pj-vals='{','.join(f'{v:.6g}' for v in spark_vals)}'>{spark}</span>"
        "</div>"
    )


def _slot_agregar(disponibles):
    """Tarjeta '+' en el hueco libre: popover con selector para agregar favorito."""
    with st.container(key="favadd"):
        with st.popover("＋", help="Agregar favorito", use_container_width=True):
            sel = st.selectbox(
                "Agregar activo", options=[""] + disponibles,
                format_func=lambda x: "Elegir activo…" if x == "" else x.replace("...", ""),
                label_visibility="collapsed", key="fav_add_sel",
            )
            if sel:
                agregar_favorito(sel)
                st.rerun(scope="fragment")


def renderizar_barra_favoritos():
    _init_favoritos()
    datos = st.session_state.get("datos_mercado_real", {})
    favs = list(st.session_state.favoritos)
    lista = st.session_state.get("watchlist_simbolos") or list(datos.keys())
    disponibles = [t for t in lista if t not in favs]
    total = len(favs)
    puede_agregar = bool(disponibles) and total < FAVORITOS_MAX

    with st.container(key="fav_panel"):
        st.html(_CSS)

        # --- Encabezado: solo título + contador ---
        st.html(
            "<div class='fav-head'><span class='fav-star'>★</span>"
            "<span class='fav-title'>Mis Favoritos</span>"
            f"<span class='fav-badge'>{total}</span></div>"
        )

        # --- 6 slots: favorito (con ✕), '+' en el primer hueco libre, o vacío ---
        cols = st.columns(_VISIBLES, gap="small")
        for i in range(_VISIBLES):
            with cols[i]:
                with st.container(key=f"favslot_{i}"):
                    if i < total:
                        tk = favs[i]
                        st.html(_tarjeta_html(tk, datos))
                        # Clic en la tarjeta -> carga el activo en el gráfico, el
                        # ticket y la cabecera (igual que la watchlist). scope="app"
                        # porque esos paneles están fuera de este fragmento. Sin
                        # st.toast antes del rerun (error "Cannot set a node at a
                        # delta path", ver watchlist.py).
                        slug = re.sub(r"\W", "", tk)
                        if st.button("Seleccionar", key=f"favsel_{slug}"):
                            st.session_state.activo_seleccionado = tk
                            st.rerun(scope="app")
                        if st.button("✕", key=f"favx_{tk}", help="Quitar de favoritos"):
                            quitar_favorito(tk)
                            st.rerun(scope="fragment")
                    elif i == total and puede_agregar:
                        _slot_agregar(disponibles)
                    else:
                        st.html("<div class='fav-card' style='visibility:hidden;'></div>")