"""
copytrading_panel.py
--------------------
Vista "Copy trading" estilo XM (MVP con datos SIMULADOS/mock mientras se define
la fuente de datos real). Dos vistas:
  - Listado de estrategias (tarjetas con sparkline y métricas).
  - Ficha de detalle de una estrategia (al hacer clic en una tarjeta).

Nota: datos ficticios solo para la interfaz. No ejecuta operaciones.
Referencias en referencias/copytrading/*.png.
"""
import base64
import math
import random

import streamlit as st

# ---------------------------------------------------------------------------
# Datos simulados de estrategias
# ---------------------------------------------------------------------------
_ESTRATEGIAS = [
    dict(id="smartgrid", nombre="SmartGrid PRO", gestor="GoldenPulse", riesgo="medio",
         cat="Forex", rent=365.20, fondos=1129, invertido=66978, inv_min=200,
         comision=10, inversores=207, drawdown=41, apalancamiento=500, ops=1044, win=71,
         tipo="Algorítmico supervisado",
         bio="Trading the Forex market with strategy, discipline, and professional risk management.",
         desc="Grid advisor que opera según el RSI y reduce el drawdown superponiendo órdenes."),
    dict(id="helium3", nombre="Helium-3", gestor="Turion", riesgo="bajo",
         cat="Índices", rent=35.38, fondos=1600, invertido=120806, inv_min=300,
         comision=15, inversores=201, drawdown=27, apalancamiento=200, ops=612, win=68,
         tipo="Algorítmico",
         bio="Operativa cuantitativa sobre índices con control de riesgo estricto.",
         desc="Modelo de reversión a la media en índices principales con stops dinámicos."),
    dict(id="winbot", nombre="WINBOT Gold", gestor="WINBOT", riesgo="bajo",
         cat="Materias primas", rent=30.50, fondos=10090, invertido=139141, inv_min=1000,
         comision=30, inversores=24, drawdown=28, apalancamiento=100, ops=430, win=64,
         tipo="Algorítmico",
         bio="Especialista en oro (XAUUSD) con gestión de capital conservadora.",
         desc="Estrategia tendencial sobre oro con filtros de volatilidad."),
    dict(id="goldgod", nombre="Gold God Trader", gestor="Jakkapong", riesgo="bajo",
         cat="Materias primas", rent=18.53, fondos=3000, invertido=299991, inv_min=350,
         comision=20, inversores=512, drawdown=19, apalancamiento=200, ops=880, win=73,
         tipo="Manual",
         bio="Trader discrecional de metales con 8 años de experiencia.",
         desc="Operativa intradía en oro y plata siguiendo estructura de mercado."),
    dict(id="greenatm", nombre="Green ATM 01", gestor="WRITED", riesgo="bajo",
         cat="Forex", rent=14.58, fondos=1124, invertido=5901, inv_min=100,
         comision=12, inversores=98, drawdown=16, apalancamiento=500, ops=1510, win=76,
         tipo="Algorítmico",
         bio="Sistema automático de scalping en pares mayores.",
         desc="Scalper de baja exposición con objetivo de ganancias pequeñas y constantes."),
    dict(id="giaphat", nombre="GIAPHAT No1", gestor="2zUJs", riesgo="medio",
         cat="Forex", rent=12.53, fondos=5215, invertido=5587, inv_min=50,
         comision=18, inversores=140, drawdown=33, apalancamiento=500, ops=720, win=61,
         tipo="Algorítmico supervisado",
         bio="Portafolio multi-par con rebalanceo semanal.",
         desc="Combina tendencia y rango en varios pares para suavizar la curva."),
    dict(id="cryptomomentum", nombre="Crypto Momentum", gestor="BlockEdge", riesgo="alto",
         cat="Criptomonedas", rent=88.14, fondos=4200, invertido=52310, inv_min=250,
         comision=25, inversores=156, drawdown=52, apalancamiento=20, ops=390, win=58,
         tipo="Algorítmico",
         bio="Momentum en las principales criptomonedas.",
         desc="Captura tendencias fuertes en BTC/ETH con salidas por volatilidad."),
    dict(id="indexsteady", nombre="Index Steady", gestor="MacroDesk", riesgo="bajo",
         cat="Índices", rent=9.87, fondos=8800, invertido=410200, inv_min=500,
         comision=10, inversores=640, drawdown=11, apalancamiento=100, ops=300, win=70,
         tipo="Manual",
         bio="Enfoque macro de baja frecuencia en índices.",
         desc="Posiciones de swing en índices guiadas por el ciclo económico."),
    dict(id="algoquant", nombre="AlgoQuant X", gestor="QuantLab", riesgo="medio",
         cat="Algorítmico", rent=42.10, fondos=6400, invertido=98750, inv_min=400,
         comision=20, inversores=310, drawdown=24, apalancamiento=200, ops=1320, win=66,
         tipo="Algorítmico",
         bio="Cartera de modelos cuantitativos diversificados.",
         desc="Ensamble de estrategias (tendencia, reversión, breakout) con control de riesgo."),
]

_CATEGORIAS = ["Cualquiera", "Forex", "Índices", "Criptomonedas", "Materias primas", "Algorítmico"]
_TABS = ["Destacadas", "Mejores resultados", "Ratio de victorias alto", "Fondos propios altos",
         "Riesgo bajo", "Drawdown bajo", "Comisiones bajas", "Más populares"]
_ORDEN = {
    "Destacadas": lambda e: -e["rent"],
    "Mejores resultados": lambda e: -e["rent"],
    "Ratio de victorias alto": lambda e: -e["win"],
    "Fondos propios altos": lambda e: -e["fondos"],
    "Riesgo bajo": lambda e: {"bajo": 0, "medio": 1, "alto": 2}[e["riesgo"]],
    "Drawdown bajo": lambda e: e["drawdown"],
    "Comisiones bajas": lambda e: e["comision"],
    "Más populares": lambda e: -e["inversores"],
}
_RIESGO_CLS = {"bajo": "rb", "medio": "rm", "alto": "ra"}
_RIESGO_TXT = {"bajo": "Riesgo bajo", "medio": "Riesgo medio", "alto": "Riesgo alto"}

_CSS = """
<style>
  .st-key-ct_wrap { max-width:1180px; margin-left:auto; margin-right:auto; width:100%; }
  .ct-title { color:#e6edf3; font-size:22px; font-weight:800; margin:0 0 10px; }
  .ct-card { background:#0f1620; border:1px solid #202a37; border-radius:16px;
             padding:16px 18px; height:100%; box-sizing:border-box; transition:border-color .15s; }
  [class*="st-key-ctrow_"]:hover .ct-card { border-color:#2f3d4f; }
  .ct-head { display:flex; align-items:center; gap:10px; }
  .ct-av { width:40px; height:40px; border-radius:50%; background:#1b2430; flex:0 0 auto;
           display:flex; align-items:center; justify-content:center; font-weight:800; color:#a78bfa; }
  .ct-nm { color:#e6edf3; font-weight:800; font-size:15px; line-height:1.1; }
  .ct-gs { color:#8b949e; font-size:12px; }
  .ct-badge { margin-left:auto; font-size:11px; font-weight:700; padding:3px 10px; border-radius:8px; }
  .ct-badge.rb { color:#3fb950; border:1px solid #2ea043; }
  .ct-badge.rm { color:#f0b429; border:1px solid #d29922; }
  .ct-badge.ra { color:#f85149; border:1px solid #da3633; }
  .ct-mid { display:flex; justify-content:space-between; align-items:flex-end; margin:14px 0; }
  .ct-rent-lbl { color:#8b949e; font-size:12px; }
  .ct-rent { color:#3fb950; font-size:22px; font-weight:800; font-variant-numeric:tabular-nums; }
  .ct-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px 8px; }
  .ct-grid .k { color:#8b949e; font-size:11px; }
  .ct-grid .v { color:#e6edf3; font-size:14px; font-weight:700; font-variant-numeric:tabular-nums; }
  /* overlay clic en toda la tarjeta */
  [class*="st-key-ctrow_"] { position:relative; }
  [class*="st-key-ctsel_"] { position:absolute !important; top:0 !important; right:0 !important;
      bottom:0 !important; left:0 !important; width:100% !important; height:100% !important;
      margin:0 !important; padding:0 !important; z-index:3; }
  [class*="st-key-ctsel_"] * { width:100% !important; height:100% !important; min-height:0 !important;
      margin:0 !important; padding:0 !important; }
  [class*="st-key-ctsel_"] button { opacity:0; cursor:pointer; }

  /* Ficha */
  .fic-av { width:84px; height:84px; border-radius:50%; background:#1b2430; margin:0 auto;
            display:flex; align-items:center; justify-content:center; font-weight:800;
            font-size:28px; color:#a78bfa; }
  .fic-nm { color:#e6edf3; font-size:24px; font-weight:800; text-align:center; margin-top:8px; }
  .fic-gs { color:#8b949e; font-size:13px; text-align:center; }
  .fic-chip { display:inline-block; background:#161b22; border:1px solid #30363d; color:#c9d1d9;
              font-size:12px; padding:5px 12px; border-radius:10px; margin:0 6px 6px 0; }
  .fic-sec { color:#8b949e; font-size:12px; margin:12px 0 2px; }
  .fic-txt { color:#e6edf3; font-size:14px; }
  .fic-rent { color:#3fb950; font-size:26px; font-weight:800; text-align:right; }
  .don-center { text-align:center; margin-top:-128px; margin-bottom:70px; }
  .don-center .n { color:#e6edf3; font-size:26px; font-weight:800; }
  .don-center .l { color:#8b949e; font-size:12px; }
</style>
"""


def _spark(seed: str, w=150, h=44):
    rnd = random.Random(seed)
    n = 30
    v = 100.0
    pts = []
    for i in range(n):
        v += rnd.uniform(-1.5, 2.6)  # sesgo alcista
        pts.append(v)
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1
    coords = []
    for i, p in enumerate(pts):
        x = i * (w / (n - 1))
        y = h - 3 - (p - lo) / rng * (h - 6)
        coords.append(f"{x:.1f},{y:.1f}")
    linea = " ".join(coords)
    area = f"0,{h} " + linea + f" {w},{h}"
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' "
           f"preserveAspectRatio='none'><defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'>"
           f"<stop offset='0' stop-color='#3fb950' stop-opacity='0.30'/>"
           f"<stop offset='1' stop-color='#3fb950' stop-opacity='0'/></linearGradient></defs>"
           f"<polygon points='{area}' fill='url(#g)'/>"
           f"<polyline points='{linea}' fill='none' stroke='#3fb950' stroke-width='1.6'/></svg>")
    b64 = base64.b64encode(svg.encode()).decode()
    return f"<img src='data:image/svg+xml;base64,{b64}' width='{w}' height='{h}'>"


def _donut(win_pct: float, size=180):
    r = size / 2 - 16
    cx = cy = size / 2
    circ = 2 * math.pi * r
    gan = circ * win_pct / 100
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}'>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#f85149' stroke-width='22'/>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#3fb950' stroke-width='22' "
        f"stroke-dasharray='{gan:.1f} {circ - gan:.1f}' stroke-dashoffset='{circ/4:.1f}' "
        f"transform='rotate(-90 {cx} {cy})' stroke-linecap='round'/></svg>"
    )
    b64 = base64.b64encode(svg.encode()).decode()
    return f"<img src='data:image/svg+xml;base64,{b64}' width='{size}' height='{size}'>"


def _avatar(nombre: str) -> str:
    return "".join(p[0] for p in nombre.split()[:2]).upper()


def _tarjeta_html(e: dict) -> str:
    rcls = _RIESGO_CLS[e["riesgo"]]
    return (
        "<div class='ct-card'>"
        "<div class='ct-head'>"
        f"<span class='ct-av'>{_avatar(e['nombre'])}</span>"
        f"<div><div class='ct-nm'>{e['nombre']}</div><div class='ct-gs'>@{e['gestor']}</div></div>"
        f"<span class='ct-badge {rcls}'>{_RIESGO_TXT[e['riesgo']]}</span>"
        "</div>"
        "<div class='ct-mid'>"
        f"{_spark(e['id'])}"
        f"<div style='text-align:right;'><div class='ct-rent-lbl'>Rentabilidad 1 mes</div>"
        f"<div class='ct-rent'>{e['rent']:.2f}%</div></div>"
        "</div>"
        "<div class='ct-grid'>"
        f"<div><div class='k'>Fondos propios</div><div class='v'>${e['fondos']:,}</div></div>"
        f"<div><div class='k'>Invertido</div><div class='v'>${e['invertido']:,}</div></div>"
        f"<div><div class='k'>Inversión mín.</div><div class='v'>${e['inv_min']:,}</div></div>"
        f"<div><div class='k'>Comisión</div><div class='v'>{e['comision']}%</div></div>"
        f"<div><div class='k'>Inversores</div><div class='v'>{e['inversores']}</div></div>"
        f"<div><div class='k'>Drawdown</div><div class='v'>{e['drawdown']}%</div></div>"
        "</div></div>"
    )


def _por_id(eid):
    return next((e for e in _ESTRATEGIAS if e["id"] == eid), None)


# ---------------------------------------------------------------------------
# Vista de detalle (ficha)
# ---------------------------------------------------------------------------
def _ficha(e: dict):
    if st.button("← Atrás", key="ct_atras"):
        st.session_state.ct_estrategia = None
        st.rerun()

    c_av, c_rent = st.columns([3, 1], vertical_alignment="center")
    with c_av:
        st.html(
            f"<div class='fic-av'>{_avatar(e['nombre'])}</div>"
            f"<div class='fic-nm'>{e['nombre']}</div><div class='fic-gs'>@{e['gestor']}</div>"
        )
    with c_rent:
        st.html(f"<div class='fic-sec' style='text-align:right;'>Rentabilidad 1 mes</div>"
                f"<div class='fic-rent'>{e['rent']:.2f}%</div>")

    st.html(
        f"<div style='margin-top:8px;'><span class='fic-chip'>👥 {e['tipo']}</span>"
        f"<span class='fic-chip'>Ⓢ {e['cat']}</span></div>"
        f"<div class='fic-sec'>Biografía del gestor</div><div class='fic-txt'>{e['bio']}</div>"
        f"<div class='fic-sec'>Descripción</div><div class='fic-txt'>{e['desc']}</div>"
        f"<div class='fic-sec'>Información importante</div><div style='margin-top:4px;'>"
        f"<span class='fic-chip'>Apalancamiento: {e['apalancamiento']}</span>"
        f"<span class='fic-chip'>Comisiones: {e['comision']}%</span>"
        f"<span class='fic-chip'>Inversores: {e['inversores']}</span>"
        f"<span class='fic-chip'>Inversión mínima: ${e['inv_min']:,}</span>"
        f"<span class='fic-chip'>Invertido: ${e['invertido']:,}</span></div>"
    )

    if st.button("＋ Cuenta de inversor  ·  Copiar estrategia", key="ct_copiar",
                 type="primary", width="stretch"):
        st.toast("Copy trading en modo demostración (UI). La copia real se habilitará "
                 "cuando conectemos la fuente de datos.")

    tab_rend, tab_riesgo, tab_cart = st.tabs(["Rendimiento", "Riesgo", "Cartera"])
    with tab_rend:
        c_graf, c_don = st.columns([2, 1], vertical_alignment="center")
        with c_graf:
            rnd = random.Random(e["id"] + "perf")
            serie = []
            base = 1000.0
            for _ in range(30):
                base *= 1 + rnd.uniform(-0.01, 0.045)
                serie.append(base)
            st.area_chart(serie, height=230, color="#3fb950")
        with c_don:
            st.html(_donut(e["win"]))
            st.html(f"<div class='don-center'><div class='n'>{e['ops']:,}</div>"
                    f"<div class='l'>Operaciones totales</div></div>")
        g1, g2, g3 = st.columns(3)
        g1.metric("Rentabilidad 1 mes", f"{e['rent']:.2f}%")
        g2.metric("Ratio de victorias", f"{e['win']}%")
        g3.metric("Operaciones", f"{e['ops']:,}")
    with tab_riesgo:
        r1, r2, r3 = st.columns(3)
        r1.metric("Drawdown máx.", f"{e['drawdown']}%")
        r2.metric("Apalancamiento", f"{e['apalancamiento']}:1")
        nivel = {"bajo": "Bajo", "medio": "Medio", "alto": "Alto"}[e["riesgo"]]
        r3.metric("Nivel de riesgo", nivel)
        st.caption("Métricas de riesgo simuladas (MVP).")
    with tab_cart:
        st.caption("Distribución simulada de la cartera de la estrategia.")
        st.bar_chart({"Peso %": {"Forex": 45, "Índices": 25, "Materias primas": 20, "Cripto": 10}})


# ---------------------------------------------------------------------------
# Vista de listado
# ---------------------------------------------------------------------------
def renderizar_panel_copytrading(main=None):
    st.html(_CSS)
    if "ct_estrategia" not in st.session_state:
        st.session_state.ct_estrategia = None

    with st.container(key="ct_wrap"):
        # --- Detalle ---
        sel = st.session_state.get("ct_estrategia")
        if sel:
            e = _por_id(sel)
            if e:
                _ficha(e)
                return

        # --- Listado ---
        st.html("<div class='ct-title'>Copy trading</div>")
        tab = st.segmented_control("Orden", _TABS, default=_TABS[0],
                                   label_visibility="collapsed", key="ct_tab") or _TABS[0]
        cat = st.pills("Categoría", _CATEGORIAS, default="Cualquiera",
                       label_visibility="collapsed", key="ct_cat") or "Cualquiera"

        lista = [e for e in _ESTRATEGIAS if cat == "Cualquiera" or e["cat"] == cat]
        lista = sorted(lista, key=_ORDEN.get(tab, _ORDEN["Destacadas"]))
        st.caption(f"{len(lista)} estrategias")

        # grid de 3 columnas
        for fila in range(0, len(lista), 3):
            cols = st.columns(3, gap="medium")
            for j, e in enumerate(lista[fila:fila + 3]):
                with cols[j]:
                    with st.container(key=f"ctrow_{e['id']}"):
                        st.html(_tarjeta_html(e))
                        if st.button("ver", key=f"ctsel_{e['id']}"):
                            st.session_state.ct_estrategia = e["id"]
                            st.rerun()