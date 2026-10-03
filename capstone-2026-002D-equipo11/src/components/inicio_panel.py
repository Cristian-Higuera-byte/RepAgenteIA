"""
inicio_panel.py
---------------
Panel de inicio estilo XM (vista "Home"):
- Tarjeta de cuenta (gradiente) con selector de cuenta (▾), saldo/equity y
  botones Gestionar / Depositar.
- "Detalles de la cuenta" (P/G, margen, apalancamiento…).
- Accesos rápidos (Promociones, Recomendar, Bonos, Copy trading).
- Banners promocionales.
- "Cartera" con las posiciones abiertas.

Datos en vivo desde MetaTrader 5. El selector abre un modal "Seleccione cuenta"
con la cuenta conectada (MT5 expone solo la cuenta activa del terminal).
"""
import streamlit as st

from tools import mt5_bridge

inicializar_mt5 = mt5_bridge.inicializar_mt5
obtener_info_cuenta = mt5_bridge.obtener_info_cuenta


def obtener_posiciones():
    """Compatibilidad con diferentes nombres de funciones del bridge MT5."""
    for nombre in (
        "obtener_posiciones",
        "obtener_posiciones_abiertas",
        "consultar_posiciones",
        "obtener_cartera",
        "leer_posiciones",
    ):
        fn = getattr(mt5_bridge, nombre, None)
        if callable(fn):
            return fn()
    return []

_CSS = """
<style>
  /* Centrar el contenido con ancho máximo (como XM) */
  .st-key-ini_wrap { max-width:1120px; margin-left:auto; margin-right:auto; width:100%; }
  .ini-title { color:#e6edf3; font-size:22px; font-weight:800; margin:0 0 14px; }
  .ini-sub   { color:#e6edf3; font-size:18px; font-weight:700; margin:18px 0 8px; }

  /* Tarjeta de cuenta (gradiente) */
  .st-key-ini_cuenta {
    background:linear-gradient(135deg,#8b1fb0 0%,#4a1f96 48%,#1e3f9c 100%);
    border-radius:18px; padding:18px 20px 20px; height:100%; min-height:230px; box-sizing:border-box;
  }
  .st-key-ini_cuenta [data-testid="stVerticalBlock"]{ gap:.5rem !important; }
  .cta-badges span { background:rgba(255,255,255,0.16); color:#fff; font-size:11px;
      font-weight:600; padding:3px 10px; border-radius:8px; margin-right:6px; }
  .cta-bal { color:#fff; font-size:36px; font-weight:800; line-height:1; margin-top:6px; }
  .cta-bal small { font-size:15px; font-weight:600; opacity:.85; }
  .cta-sub { color:rgba(255,255,255,0.78); font-size:14px; margin-top:4px; }
  /* Botón selector de cuenta (pill translúcido) */
  [class*="st-key-ini_sel"] button {
    background:rgba(255,255,255,0.14) !important; border:none !important; color:#fff !important;
    border-radius:999px !important; font-weight:700 !important; justify-content:space-between !important;
    padding:7px 16px !important; box-shadow:none !important;
  }
  [class*="st-key-ini_sel"] button:hover { background:rgba(255,255,255,0.24) !important; }
  /* Gestionar (blanco) / Depositar (contorno) */
  [class*="st-key-ini_gest"] button {
    background:#ffffff !important; color:#20123a !important; border:none !important;
    border-radius:999px !important; font-weight:700 !important; box-shadow:none !important;
  }
  [class*="st-key-ini_dep"] button {
    background:rgba(0,0,0,0.25) !important; color:#fff !important;
    border:1px solid rgba(255,255,255,0.35) !important; border-radius:999px !important;
    font-weight:700 !important; box-shadow:none !important;
  }

  /* Detalles de la cuenta */
  .det-card { background:#0f1620; border:1px solid #202a37; border-radius:18px;
      padding:16px 22px; height:100%; min-height:230px; box-sizing:border-box; }
  .det-title { color:#e6edf3; font-size:16px; font-weight:700; margin:0 0 6px; }
  .det-row { display:flex; justify-content:space-between; padding:7px 0;
      border-bottom:1px solid #161b22; font-size:14px; }
  .det-row:last-child { border-bottom:none; }
  .det-row .k { color:#8b949e; }
  .det-row .v { color:#e6edf3; font-weight:600; font-family:ui-monospace,Consolas,monospace; }

  /* Accesos rápidos */
  .acc-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:16px 0 4px; }
  .acc-card { background:#0f1620; border:1px solid #202a37; border-radius:16px;
      padding:18px 10px; text-align:center; transition:border-color .15s ease; }
  .acc-card:hover { border-color:#2f3d4f; }
  .acc-ic { width:44px; height:44px; border-radius:50%; background:#161b22; margin:0 auto;
      display:flex; align-items:center; justify-content:center; font-size:20px; }
  .acc-lbl { color:#e6edf3; font-size:13px; margin-top:10px; }
  /* accesos rápidos clicables (overlay invisible) */
  [class*="st-key-accrow_"] { position:relative; }
  [class*="st-key-accsel_"] { position:absolute !important; top:0 !important; right:0 !important;
      bottom:0 !important; left:0 !important; width:100% !important; height:100% !important;
      margin:0 !important; padding:0 !important; z-index:3; }
  [class*="st-key-accsel_"] * { width:100% !important; height:100% !important; min-height:0 !important;
      margin:0 !important; padding:0 !important; }
  [class*="st-key-accsel_"] button { opacity:0; cursor:pointer; }

  /* Banners promo */
  .promo-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:6px; }
  .promo-card { border-radius:16px; padding:16px 18px; min-height:96px; color:#fff; }
  .promo-card h4 { margin:0 0 6px; font-size:15px; font-weight:800; }
  .promo-card p  { margin:0; font-size:12.5px; opacity:.85; }
  .promo-a { background:linear-gradient(135deg,#124e8c,#0a2e55); }
  .promo-b { background:linear-gradient(135deg,#5a2ea6,#36166b); }
  .promo-c { background:linear-gradient(135deg,#8c1024,#4d0a14); }

  /* Cartera */
  table.cartera { width:100%; border-collapse:collapse; font-size:13px; }
  table.cartera th { color:#8b949e; text-align:left; font-weight:600; font-size:12px;
      padding:8px 12px; border-bottom:1px solid #1f2630; }
  table.cartera th.r, table.cartera td.r { text-align:right;
      font-family:ui-monospace,Consolas,monospace; }
  table.cartera td { color:#e6edf3; padding:9px 12px; border-bottom:1px solid #141a22; }
  .car-up { color:#3fb950; font-weight:700; }
  .car-down { color:#f85149; font-weight:700; }
  .car-empty { color:#6e7681; font-size:13px; padding:16px 2px; }

  /* Modal selección de cuenta */
  .selc-card { background:#0f1620; border:1px solid #202a37; border-radius:14px;
      padding:14px 16px; margin-bottom:10px; }
  .selc-card.activa { border-color:#1f6feb; }
  .selc-top { display:flex; justify-content:space-between; align-items:flex-start; }
  .selc-tipo { font-size:11px; font-weight:700; padding:2px 10px; border-radius:8px; }
  .selc-real { color:#3fb950; border:1px solid #3fb950; }
  .selc-demo { color:#f0b429; border:1px solid #f0b429; }
  .selc-bal { color:#fff; font-size:22px; font-weight:800; margin:2px 0; }
  .selc-meta { color:#8b949e; font-size:12px; }
</style>
"""

_ACCIONES = [
    ("🚀", "Promociones", None), ("👥", "Recomendar", None),
    ("🎁", "Bonos", None), ("🧩", "Copy trading", "copytrading"),
]
_PROMOS = [
    ("promo-a", "Reintegros en cada activo", "Sin límites mientras dure la promoción."),
    ("promo-b", "Competiciones semanales", "Gana premios operando cada semana."),
    ("promo-c", "Programa de referidos", "Invita y gana con cada amigo."),
]


def _fmt(v, dec=2):
    try:
        return f"${float(v):,.{dec}f}"
    except Exception:
        return "—"


def _cerrar_modal_cuentas():
    st.session_state.ini_modal_cuentas = False


@st.dialog("Seleccione cuenta", on_dismiss=_cerrar_modal_cuentas)
def _modal_cuentas():
    info = obtener_info_cuenta()
    st.html(_CSS)
    if "error" in info:
        st.warning("No hay conexión con MetaTrader 5.")
        return
    tipo = info.get("tipo", "Demo")
    cls_tipo = "selc-real" if tipo == "Real" else "selc-demo"
    st.html(
        "<div class='selc-card activa'><div class='selc-top'>"
        "<div><div style='color:#e6edf3;font-weight:700;'>Standard</div>"
        f"<div class='selc-bal'>{_fmt(info.get('equity', 0))}</div>"
        f"<div class='selc-meta'>#{info.get('login','—')} · Standard · MT5 · "
        f"{info.get('servidor','')}</div></div>"
        f"<span class='selc-tipo {cls_tipo}'>{tipo}</span>"
        "</div></div>"
    )
    st.caption("MetaTrader 5 muestra solo la cuenta conectada en el terminal.")
    if st.button("＋ Crear nueva cuenta", width="stretch", key="selc_crear"):
        st.toast("Para agregar otra cuenta, inicia sesión con ella en el terminal MT5.")


def renderizar_panel_inicio(main=None):
    inicializar_mt5()
    st.html(_CSS)

    if "ini_ocultar" not in st.session_state:
        st.session_state.ini_ocultar = False

    # --- Cuenta + detalles (en vivo) ---
    @st.fragment(run_every="2s")
    def _cuenta_vivo():
        info = obtener_info_cuenta()
        if "error" in info:
            st.warning("No se pudo conectar con MetaTrader 5. Abre el terminal para ver tu cuenta.")
            return
        moneda = info.get("currency", "USD")
        login = info.get("login", "—")
        tipo = info.get("tipo", "Demo")
        equity = info.get("equity", 0.0)
        balance = info.get("balance", 0.0)
        profit = info.get("profit", 0.0)
        lev = info.get("leverage", 0)
        ml = info.get("margin_level", 0.0)
        oculto = st.session_state.get("ini_ocultar", False)
        pcolor = "#3fb950" if profit >= 0 else "#f85149"
        bal_txt = "••••••" if oculto else f"{_fmt(equity)} <small>{moneda}</small>"
        if oculto:
            sub_txt = "P/G sin realizar: ••••"
        else:
            sub_txt = (f"P/G sin realizar: <span style='color:{pcolor};font-weight:700;'>"
                       f"{profit:+,.2f} {moneda}</span>")

        c_cta, c_det = st.columns(2, gap="medium")
        with c_cta:
            with st.container(key="ini_cuenta"):
                if st.button(f"🇺🇸  Standard #{login}   ▾", key="ini_sel", width="stretch"):
                    st.session_state.ini_modal_cuentas = True
                    st.rerun()
                st.html(
                    "<div class='cta-badges'>"
                    f"<span>{tipo}</span><span>MT5 Standard</span></div>"
                    f"<div class='cta-bal'>{bal_txt}</div>"
                    f"<div class='cta-sub'>{sub_txt}</div>"
                )
                g1, g2 = st.columns(2)
                with g1:
                    if st.button("Gestionar", icon=":material/tune:", key="ini_gest", width="stretch"):
                        st.toast("Gestión de cuenta disponible próximamente.")
                with g2:
                    if st.button("Ocultar" if not oculto else "Mostrar",
                                 icon=":material/visibility_off:", key="ini_dep", width="stretch"):
                        st.session_state.ini_ocultar = not oculto
                        st.rerun(scope="fragment")
        with c_det:
            filas = [
                ("P/G sin realizar", f"<span style='color:{pcolor};'>{_fmt(profit)}</span>"),
                ("Saldo", _fmt(balance)),
                ("Margen", _fmt(info.get("margin", 0.0))),
                ("Margen Libre", _fmt(info.get("margin_free", 0.0))),
                ("Nivel de margen", f"{ml:,.2f}%" if ml else "—"),
                ("Crédito", _fmt(info.get("credit", 0.0))),
                ("Apalancamiento", f"{lev}:1" if lev else "—"),
            ]
            cuerpo = "".join(
                f"<div class='det-row'><span class='k'>{k}</span><span class='v'>{v}</span></div>"
                for k, v in filas
            )
            st.html(f"<div class='det-card'><div class='det-title'>Detalles de la cuenta</div>{cuerpo}</div>")

    # --- Cartera: posiciones abiertas (en vivo) ---
    @st.fragment(run_every="2s")
    def _cartera_vivo():
        pos = obtener_posiciones()
        if not pos:
            st.html("<div class='car-empty'>No tienes posiciones abiertas. "
                    "Las operaciones que abras en MetaTrader 5 aparecerán aquí.</div>")
            return
        filas = ""
        for p in pos:
            cls = "car-up" if p["profit"] >= 0 else "car-down"
            filas += (
                "<tr>"
                f"<td><b>{p['symbol']}</b></td>"
                f"<td>{p['tipo']}</td>"
                f"<td class='r'>{p['volumen']:,.2f}</td>"
                f"<td class='r'>{p['precio_apertura']:,.5f}</td>"
                f"<td class='r'>{p['precio_actual']:,.5f}</td>"
                f"<td class='r {cls}'>{p['profit']:+,.2f}</td>"
                "</tr>"
            )
        st.html(
            "<table class='cartera'><thead><tr>"
            "<th>Símbolo</th><th>Tipo</th><th class='r'>Volumen</th>"
            "<th class='r'>Apertura</th><th class='r'>Actual</th><th class='r'>P/G</th>"
            "</tr></thead><tbody>" + filas + "</tbody></table>"
        )

    # --- Contenido centrado con ancho máximo (estilo XM) ---
    with st.container(key="ini_wrap"):
        st.html("<div class='ini-title'>Inicio</div>")
        _cuenta_vivo()

        acc_cols = st.columns(len(_ACCIONES), gap="medium")
        for i, (ic, lbl, dest) in enumerate(_ACCIONES):
            with acc_cols[i]:
                with st.container(key=f"accrow_{i}"):
                    st.html(f"<div class='acc-card'><div class='acc-ic'>{ic}</div>"
                            f"<div class='acc-lbl'>{lbl}</div></div>")
                    if st.button("ir", key=f"accsel_{i}"):
                        if dest:
                            st.session_state.nav_activo = dest
                            st.rerun()
                        else:
                            st.toast(f"{lbl}: disponible próximamente.")

        banners = "".join(
            f"<div class='promo-card {c}'><h4>{t}</h4><p>{d}</p></div>"
            for c, t, d in _PROMOS
        )
        st.html(f"<div class='promo-grid'>{banners}</div>")

        st.html("<div class='ini-sub'>Cartera</div>")
        _cartera_vivo()

    # --- Modal selección de cuenta (fuera de los fragmentos en vivo) ---
    if st.session_state.get("ini_modal_cuentas"):
        _modal_cuentas()