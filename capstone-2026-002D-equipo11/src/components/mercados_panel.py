"""
mercados_panel.py
-----------------
Página "Mercados" (barra lateral), estilo es.investing.com:
- Selector de categoría + tabla con Último, Máx, Mín, Var., % Var., Hora.
- Cada fila es CLICABLE -> abre un modal (ficha del instrumento) con precio,
  rango del día / 52 semanas, apertura, cierre anterior, compra/venta,
  rendimiento (1d/1s/1m/3m/6m/1a), un gráfico y acciones rápidas.

Datos desde MetaTrader 5 usando el resolvedor de símbolos (funciona con o sin
el sufijo "..." del bróker).
"""
from datetime import datetime

import streamlit as st
import MetaTrader5 as mt5  # type: ignore[import-untyped]

from tools.mt5_bridge import (
    MT5_LOCK, inicializar_mt5, resolver_simbolo, obtener_datos_historicos,
)
from components.favoritos_bar import icono_activo

_LIMITE_DEFECTO = 8  # filas visibles antes de "Ver todos"

_CATALOGO = {
    "Índices": [
        ("US30", "Dow Jones"), ("US500", "S&P 500"), ("NAS100", "Nasdaq 100"),
        ("US2000", "Russell 2000"), ("VIX", "S&P 500 VIX"), ("DXY", "Índice Dólar"),
        ("GER40", "DAX (Alemania)"), ("UK100", "FTSE 100"), ("FRA40", "CAC 40"),
        ("ESP35", "IBEX 35"), ("EU50", "Euro Stoxx 50"), ("ITA40", "FTSE MIB"),
        ("NETH25", "AEX (Países Bajos)"), ("SWI20", "SMI (Suiza)"),
        ("JP225", "Nikkei 225"), ("AUS200", "ASX 200"), ("HK50", "Hang Seng"),
        ("CHINA50", "China A50"), ("INDIA50", "Nifty 50"),
    ],
    "Divisas": [
        ("EURUSD", "Euro / Dólar"), ("GBPUSD", "Libra / Dólar"),
        ("USDJPY", "Dólar / Yen"), ("USDCHF", "Dólar / Franco"),
        ("AUDUSD", "Dólar Aus. / Dólar"), ("USDCAD", "Dólar / Dólar Can."),
        ("NZDUSD", "Dólar NZ / Dólar"), ("EURJPY", "Euro / Yen"),
        ("EURGBP", "Euro / Libra"), ("GBPJPY", "Libra / Yen"),
        ("EURCHF", "Euro / Franco"), ("EURAUD", "Euro / Dólar Aus."),
        ("AUDJPY", "Dólar Aus. / Yen"), ("CADJPY", "Dólar Can. / Yen"),
        ("CHFJPY", "Franco / Yen"), ("NZDJPY", "Dólar NZ / Yen"),
        ("GBPAUD", "Libra / Dólar Aus."), ("USDMXN", "Dólar / Peso Mex."),
        ("USDZAR", "Dólar / Rand"), ("USDSGD", "Dólar / Dólar Sing."),
    ],
    "Materias primas": [
        ("XAUUSD", "Oro"), ("XAGUSD", "Plata"), ("USOIL", "Petróleo WTI"),
        ("UKOIL", "Petróleo Brent"), ("NGAS", "Gas Natural"),
        ("XPTUSD", "Platino"), ("XPDUSD", "Paladio"), ("XCUUSD", "Cobre"),
        ("COFFEE", "Café"), ("COCOA", "Cacao"), ("SUGAR", "Azúcar"),
        ("WHEAT", "Trigo"), ("CORN", "Maíz"), ("SOYBEAN", "Soja"),
    ],
    "Criptomonedas": [
        ("BTCUSD", "Bitcoin"), ("ETHUSD", "Ethereum"), ("XRPUSD", "XRP"),
        ("LTCUSD", "Litecoin"), ("SOLUSD", "Solana"), ("ADAUSD", "Cardano"),
        ("DOGUSD", "Dogecoin"), ("BNBUSD", "BNB"), ("BCHUSD", "Bitcoin Cash"),
        ("DOTUSD", "Polkadot"), ("LINKUSD", "Chainlink"), ("AVAXUSD", "Avalanche"),
        ("MATICUSD", "Polygon"), ("TRXUSD", "TRON"), ("UNIUSD", "Uniswap"),
    ],
    "Acciones": [
        ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("TSLA", "Tesla"),
        ("NVDA", "NVIDIA"), ("AMZN", "Amazon"), ("GOOGL", "Alphabet"),
        ("META", "Meta"), ("NFLX", "Netflix"), ("AMD", "AMD"), ("KO", "Coca-Cola"),
        ("JPM", "JPMorgan"), ("V", "Visa"), ("WMT", "Walmart"), ("DIS", "Disney"),
        ("BABA", "Alibaba"), ("INTC", "Intel"), ("BA", "Boeing"),
        ("ORCL", "Oracle"), ("CSCO", "Cisco"), ("PFE", "Pfizer"),
    ],
}

# plantilla de columnas de la "tabla" (grid) — header y filas comparten el mismo reparto
_GRID = "2.6fr 1.2fr 1.2fr 1.2fr 1.2fr 1.3fr 0.9fr"

_CSS = f"""
<style>
  .mkt-title {{ color:#e6edf3; font-size:22px; font-weight:800; margin:0; }}
  .mkt-sub {{ color:#8b949e; font-size:13px; margin:2px 0 12px; }}
  .mkt-head, .mkt-row {{ display:grid; grid-template-columns:{_GRID}; align-items:center; }}
  .mkt-head > div, .mkt-row > div {{ padding:9px 12px; }}
  .mkt-head {{ border-bottom:1px solid #1f2630; color:#8b949e; font-size:12px; }}
  .mkt-row {{ border-bottom:1px solid #141a22; font-size:13px; color:#e6edf3; }}
  .mkt-r {{ text-align:right; font-family:ui-monospace,Consolas,monospace;
            font-variant-numeric:tabular-nums; }}
  .mkt-nm {{ display:flex; align-items:center; gap:9px; }}
  .mkt-ic {{ width:22px; height:22px; border-radius:50%; background:#161b22;
             display:inline-flex; align-items:center; justify-content:center;
             overflow:hidden; flex:0 0 auto; }}
  .mkt-up {{ color:#3fb950 !important; font-weight:700; }}
  .mkt-down {{ color:#f85149 !important; font-weight:700; }}
  .mkt-arrow {{ font-size:10px; margin-right:2px; }}

  /* Sin separación entre filas y clic invisible que cubre TODA la fila
     (mismo patrón probado en watchlist.py: 4 bordes + '* {{100%}}' + opacity 0) */
  .st-key-mkt_tabla [data-testid="stVerticalBlock"] {{ gap:0 !important; }}
  [class*="st-key-mktrow_"] {{ position:relative; }}
  [class*="st-key-mktrow_"]:hover {{ background:#0f1620; border-radius:6px; }}
  [class*="st-key-mktclk_"] {{
      position:absolute !important;
      top:0 !important; right:0 !important; bottom:0 !important; left:0 !important;
      width:100% !important; height:100% !important;
      margin:0 !important; padding:0 !important; z-index:2;
  }}
  [class*="st-key-mktclk_"] * {{
      width:100% !important; height:100% !important; min-height:0 !important;
      margin:0 !important; padding:0 !important;
  }}
  [class*="st-key-mktclk_"] button {{ opacity:0; cursor:pointer; }}

  /* Ficha (modal) */
  .fic-px {{ font-size:34px; font-weight:800; line-height:1; font-family:ui-monospace,Consolas,monospace; }}
  .fic-var {{ font-size:15px; font-weight:700; margin-left:8px; }}
  .fic-meta {{ color:#8b949e; font-size:12px; margin-top:4px; }}
  .fic-rng-lbl {{ color:#8b949e; font-size:12px; display:flex; justify-content:space-between; }}
  .fic-rng {{ position:relative; height:6px; background:#20303f; border-radius:4px; margin:5px 0 2px; }}
  .fic-rng-dot {{ position:absolute; top:-2px; width:10px; height:10px; border-radius:50%;
                  background:#e6edf3; transform:translateX(-50%); }}
  .fic-chip {{ display:inline-block; background:#1f2937; color:#9aa4b2; font-size:11px;
               padding:2px 9px; border-radius:10px; margin:0 6px 6px 0; }}
  .fic-perf {{ display:grid; grid-template-columns:repeat(6,1fr); gap:6px; margin:6px 0; }}
  .fic-perf > div {{ background:#0f1620; border:1px solid #202a37; border-radius:8px;
                     padding:8px 6px; text-align:center; }}
  .fic-perf .k {{ color:#8b949e; font-size:11px; }}
  .fic-perf .v {{ font-weight:700; font-size:13px; }}
  .fic-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:4px 24px; margin-top:4px; }}
  .fic-grid .r {{ display:flex; justify-content:space-between; padding:6px 0;
                  border-bottom:1px solid #161b22; font-size:13px; }}
  .fic-grid .r .k {{ color:#8b949e; }}
  .fic-grid .r .v {{ font-family:ui-monospace,Consolas,monospace; }}
</style>
"""


def _g(info, attr):
    return getattr(info, attr, 0) or 0


def _fila(sym: str, label: str):
    """Fila de la tabla desde MT5, o None si el símbolo no existe en el bróker."""
    real = resolver_simbolo(sym)
    try:
        with MT5_LOCK:
            mt5.symbol_select(real, True)
            info = mt5.symbol_info(real)
            tick = mt5.symbol_info_tick(real) if info is not None else None
    except Exception:
        info = None
        tick = None
    if info is None:
        return None

    last = 0.0
    if tick is not None:
        last = tick.last if getattr(tick, "last", 0) > 0 else getattr(tick, "bid", 0)
    if last <= 0:
        last = _g(info, "bid") or _g(info, "last")
    if last <= 0:
        return None

    high = _g(info, "bidhigh") or _g(info, "lasthigh") or _g(info, "high")
    low = _g(info, "bidlow") or _g(info, "lastlow") or _g(info, "low")
    ref = _g(info, "session_open") or last
    var = last - ref
    pct = (var / ref * 100) if ref else 0.0
    dig = int(_g(info, "digits") or 2)
    t = int(_g(info, "time") or 0)
    hora = datetime.fromtimestamp(t).strftime("%H:%M:%S") if t else "—"

    return {"sym": real, "label": label, "last": last, "high": high or last,
            "low": low or last, "var": var, "pct": pct, "dig": dig, "hora": hora}


def _fila_html(f) -> str:
    d = f["dig"]
    cls = "mkt-up" if f["var"] >= 0 else "mkt-down"
    flecha = "▲" if f["var"] >= 0 else "▼"
    return (
        "<div class='mkt-row'>"
        f"<div><div class='mkt-nm'><span class='mkt-ic'>{icono_activo(f['sym'])}</span>"
        f"<b>{f['label']}</b></div></div>"
        f"<div class='mkt-r'>{f['last']:,.{d}f}</div>"
        f"<div class='mkt-r'>{f['high']:,.{d}f}</div>"
        f"<div class='mkt-r'>{f['low']:,.{d}f}</div>"
        f"<div class='mkt-r {cls}'>{f['var']:+,.{d}f}</div>"
        f"<div class='mkt-r {cls}'><span class='mkt-arrow'>{flecha}</span>{f['pct']:+.2f}%</div>"
        f"<div class='mkt-r' style='color:#8b949e;'>{f['hora']}</div>"
        "</div>"
    )


def _render_tabla(categoria: str, limite):
    """Renderiza header + filas clicables. Devuelve el total de filas disponibles."""
    filas = []
    for sym, label in _CATALOGO.get(categoria, []):
        f = _fila(sym, label)
        if f:
            filas.append(f)
    total = len(filas)

    st.html(
        "<div class='mkt-head'>"
        "<div>Nombre</div><div class='mkt-r'>Último</div><div class='mkt-r'>Máximo</div>"
        "<div class='mkt-r'>Mínimo</div><div class='mkt-r'>Var.</div>"
        "<div class='mkt-r'>% Var.</div><div class='mkt-r'>Hora</div></div>"
    )
    if not filas:
        st.html("<div style='color:#8b949e; padding:20px 4px;'>No hay datos para esta "
                "categoría. Verifica que MetaTrader 5 esté abierto y que el bróker tenga "
                "estos instrumentos.</div>")
        return 0

    visibles = filas if limite is None else filas[:limite]
    with st.container(key="mkt_tabla"):
        for i, f in enumerate(visibles):
            with st.container(key=f"mktrow_{i}"):
                st.html(_fila_html(f))
                if st.button("ver", key=f"mktclk_{f['sym']}"):
                    st.session_state.mkt_detalle = {"sym": f["sym"], "label": f["label"],
                                                    "cat": categoria}
                    st.rerun()
    return total


# ----------------------------- Ficha (modal) -----------------------------
@st.cache_data(ttl=30, show_spinner=False)
def _hist_d1(sym: str):
    try:
        return obtener_datos_historicos(sym, mt5.TIMEFRAME_D1, 260)
    except Exception:
        return None


def _fila_dato(k, v):
    return f"<div class='r'><span class='k'>{k}</span><span class='v'>{v}</span></div>"


def _cerrar_ficha():
    st.session_state.mkt_detalle = None


@st.dialog(" ", width="large", on_dismiss=_cerrar_ficha)
def _mostrar_ficha():
    det = st.session_state.get("mkt_detalle") or {}
    sym, label, cat = det.get("sym"), det.get("label", ""), det.get("cat", "")
    if not sym:
        return

    real = resolver_simbolo(sym)
    with MT5_LOCK:
        mt5.symbol_select(real, True)
        info0 = mt5.symbol_info(real)   # campos estáticos (dígitos, divisas, contrato)
    if info0 is None:
        st.warning("No se pudo cargar la información del instrumento.")
        return
    dig = int(_g(info0, "digits") or 2)

    # Histórico diario (estático, cacheado): apertura, cierre anterior, 52 semanas, gráfico
    df = _hist_d1(real)
    open_hoy = prev_close = wk_hi = wk_lo = None
    if df is not None and not df.empty and "close" in df.columns:
        open_hoy = float(df["open"].iloc[-1])
        prev_close = float(df["close"].iloc[-2]) if len(df) > 1 else None
        wk_hi = float(df["high"].max())
        wk_lo = float(df["low"].min())

    def _barra(titulo, lo, hi, val):
        if hi is None or lo is None or hi <= lo:
            return ""
        pos = max(0, min(100, (val - lo) / (hi - lo) * 100))
        return (f"<div style='margin-top:10px;'><div class='fic-rng-lbl'><span>{titulo}</span></div>"
                f"<div class='fic-rng-lbl'><span>{lo:,.{dig}f}</span><span>{hi:,.{dig}f}</span></div>"
                f"<div class='fic-rng'><div class='fic-rng-dot' style='left:{pos:.1f}%;'></div></div></div>")

    # --- Cabecera (nombre, estático) ---
    st.html(
        f"<div class='mkt-nm' style='gap:12px;'><span class='mkt-ic' style='width:34px;height:34px;'>"
        f"{icono_activo(real)}</span>"
        f"<div><div style='font-size:20px;font-weight:800;color:#e6edf3;'>{label}</div>"
        f"<div class='fic-meta'>{real} · {cat}</div></div></div>"
    )

    # --- EN VIVO: precio + rangos (se refresca cada 2s) ---
    @st.fragment(run_every="2s")
    def _precio_vivo():
        with MT5_LOCK:
            info = mt5.symbol_info(real)
            tick = mt5.symbol_info_tick(real)
        if info is None:
            return
        last = tick.last if (tick and getattr(tick, "last", 0) > 0) else (getattr(tick, "bid", 0) if tick else 0)
        if last <= 0:
            last = _g(info, "bid")
        high = _g(info, "bidhigh") or _g(info, "high") or last
        low = _g(info, "bidlow") or _g(info, "low") or last
        ref = open_hoy or prev_close or last
        var = last - ref
        pct = (var / ref * 100) if ref else 0.0
        color = "#3fb950" if var >= 0 else "#f85149"
        flecha = "▲" if var >= 0 else "▼"
        st.html(
            f"<div><span class='fic-px' style='color:{color};'>{last:,.{dig}f}</span>"
            f"<span class='fic-var' style='color:{color};'>{var:+,.{dig}f} ({pct:+.2f}%) {flecha}</span></div>"
            + _barra("Rango del día", low, high, last)
            + _barra("Rango 52 semanas", wk_lo, wk_hi, last)
        )
    _precio_vivo()

    # --- Gráfico (estático, cierres diarios) ---
    if df is not None and not df.empty:
        tend = "#3fb950" if float(df["close"].iloc[-1]) >= float(df["close"].tail(180).iloc[0]) else "#f85149"
        st.line_chart(df["close"].tail(180), height=220, color=tend)

    # --- EN VIVO: rendimiento + tabla (se refresca cada 2s) ---
    @st.fragment(run_every="2s")
    def _datos_vivo():
        with MT5_LOCK:
            info = mt5.symbol_info(real)
            tick = mt5.symbol_info_tick(real)
        if info is None:
            return
        last = tick.last if (tick and getattr(tick, "last", 0) > 0) else (getattr(tick, "bid", 0) if tick else 0)
        if last <= 0:
            last = _g(info, "bid")
        bid, ask = _g(info, "bid"), _g(info, "ask")
        high = _g(info, "bidhigh") or _g(info, "high") or last
        low = _g(info, "bidlow") or _g(info, "low") or last

        # Rendimiento por periodo (histórico estático + precio en vivo)
        if df is not None and not df.empty and "close" in df.columns:
            closes = df["close"]

            def _ret(n):
                if len(closes) > n and closes.iloc[-n - 1]:
                    return (last / float(closes.iloc[-n - 1]) - 1) * 100
                return None
            perf = {"1 día": (last / prev_close - 1) * 100 if prev_close else None,
                    "1 sem": _ret(5), "1 mes": _ret(22), "3 meses": _ret(66),
                    "6 meses": _ret(132), "1 año": _ret(252)}
            celdas = ""
            for k, v in perf.items():
                if v is None:
                    celdas += f"<div><div class='k'>{k}</div><div class='v' style='color:#8b949e;'>—</div></div>"
                else:
                    c = "#3fb950" if v >= 0 else "#f85149"
                    celdas += f"<div><div class='k'>{k}</div><div class='v' style='color:{c};'>{v:+.2f}%</div></div>"
            st.html(f"<div class='fic-perf'>{celdas}</div>")

        filas = ""
        if prev_close is not None:
            filas += _fila_dato("Último cierre", f"{prev_close:,.{dig}f}")
        if open_hoy is not None:
            filas += _fila_dato("Apertura", f"{open_hoy:,.{dig}f}")
        filas += _fila_dato("Compra (ask)", f"{ask:,.{dig}f}")
        filas += _fila_dato("Venta (bid)", f"{bid:,.{dig}f}")
        filas += _fila_dato("Rango día", f"{low:,.{dig}f} – {high:,.{dig}f}")
        if wk_lo is not None:
            filas += _fila_dato("52 semanas", f"{wk_lo:,.{dig}f} – {wk_hi:,.{dig}f}")
        spread = _g(info, "spread")
        if spread:
            filas += _fila_dato("Spread", f"{int(spread)} pts")
        vol = _g(info, "volume") or _g(info, "volumereal")
        if vol:
            filas += _fila_dato("Volumen", f"{vol:,.0f}")
        st.html(f"<div class='fic-grid'>{filas}</div>")
    _datos_vivo()

    # --- Chips descriptivos (estático) ---
    chips = ""
    base = getattr(info0, "currency_base", "") or ""
    prof = getattr(info0, "currency_profit", "") or ""
    contrato = _g(info0, "trade_contract_size")
    if cat:
        chips += f"<span class='fic-chip'>Tipo: {cat}</span>"
    if base:
        chips += f"<span class='fic-chip'>Base: {base}</span>"
    if prof:
        chips += f"<span class='fic-chip'>Cotizado en: {prof}</span>"
    if contrato:
        chips += f"<span class='fic-chip'>Contrato: {contrato:,.0f}</span>"
    if chips:
        st.html(f"<div style='margin-top:8px;'>{chips}</div>")

    # --- Acciones rápidas ---
    st.divider()
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("Ver en gráfico", icon=":material/show_chart:", width="stretch"):
            st.session_state.activo_seleccionado = real
            st.session_state.nav_activo = "trading"
            st.session_state.mkt_detalle = None
            st.rerun()
    with a2:
        if st.button("Agregar a mi lista", icon=":material/add:", width="stretch"):
            from components.buscador import _agregar_a_watchlist
            uid = (st.session_state.get("usuario_info") or {}).get("id")
            _agregar_a_watchlist(uid, {"name": real, "visible": real,
                                       "desc": label, "cat": cat})
            st.toast(f"{label} agregado a tu lista.")
    with a3:
        if st.button("Agregar a favoritos", icon=":material/star:", width="stretch"):
            from components.favoritos_bar import agregar_favorito
            agregar_favorito(real)


# ----------------------------- Página -----------------------------
def renderizar_panel_mercados(main=None):
    inicializar_mt5()
    st.html(_CSS)
    st.html(
        "<div class='mkt-title'>Mercados</div>"
        "<div class='mkt-sub'>Cotizaciones en tiempo real · haz clic en un activo "
        "para ver su ficha completa</div>"
    )

    categorias = list(_CATALOGO.keys())
    cat = st.segmented_control(
        "Categoría", categorias, default=categorias[0],
        label_visibility="collapsed", key="mkt_cat",
    ) or categorias[0]

    if st.session_state.get("_mkt_cat_prev") != cat:
        st.session_state._mkt_cat_prev = cat
        st.session_state.mkt_expandido = False

    @st.fragment(run_every="3s")
    def _tabla_en_vivo():
        categoria = st.session_state.get("mkt_cat") or categorias[0]
        expandido = st.session_state.get("mkt_expandido", False)
        limite = None if expandido else _LIMITE_DEFECTO
        total = _render_tabla(categoria, limite)

        c_info, c_btn = st.columns([3, 1.2], vertical_alignment="center")
        with c_info:
            mostrados = total if expandido else min(_LIMITE_DEFECTO, total)
            st.caption(f"Mostrando {mostrados} de {total} · actualizado "
                       f"{datetime.now().strftime('%H:%M:%S')}")
        with c_btn:
            if total > _LIMITE_DEFECTO:
                etiqueta = "Ver menos" if expandido else f"Ver todos ({total})"
                icono = ":material/expand_less:" if expandido else ":material/expand_more:"
                if st.button(etiqueta, icon=icono, key="mkt_ver_todos", width="stretch"):
                    st.session_state.mkt_expandido = not expandido
                    st.rerun(scope="fragment")

    _tabla_en_vivo()

    # El modal se abre con la bandera y se renderiza AQUÍ (fuera del fragmento en vivo)
    # para no chocar con el auto-refresco (evita pantallas en blanco).
    if st.session_state.get("mkt_detalle"):
        _mostrar_ficha()