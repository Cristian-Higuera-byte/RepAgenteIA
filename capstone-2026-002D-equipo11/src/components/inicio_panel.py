"""
inicio_panel.py
---------------
Panel de Inicio (vista "Home") con diseño de panel de bróker profesional:
- Encabezado: saludo + selector de cuenta (chip) + botón "Operar".
- Tarjeta principal: equity grande, P/G flotante (pastilla) y 3 indicadores
  (Saldo, Margen libre, Margen usado). Botón de ojo para ocultar los montos.
- "Salud de la cuenta": nivel de margen con semáforo, barra de margen usado y
  datos técnicos (apalancamiento, crédito, tipo, servidor).
- Accesos rápidos (tarjetas con ícono, título, subtítulo y flecha).
- Promociones (banners sobrios) y Posiciones abiertas (tabla con íconos).

Datos en vivo: los números llevan atributos data-pj-* y los pinta el feed
(components/live_feed.py) con el MISMO dato que la barra superior.
El selector de cuenta abre el modal "Seleccione cuenta" (MT5 expone solo la
cuenta conectada en el terminal).
"""
import streamlit as st

from components.iconos import icono_activo
from components.live_feed import intervalo as _intervalo
from tools.mt5_bridge import inicializar_mt5, obtener_info_cuenta, obtener_posiciones

# OJO: no escribir etiquetas HTML dentro de este CSS (ni en comentarios):
# st.html descarta el bloque de estilos completo.
_CSS = """
<style>
  .st-key-ini_wrap { max-width:1180px; margin-left:auto; margin-right:auto; width:100%; }
  .st-key-ini_wrap [data-testid="stVerticalBlock"] { gap:18px; }
  .mi { font-family:'Material Symbols Rounded'; font-weight:400; font-style:normal;
        line-height:1; letter-spacing:normal; text-transform:none; white-space:nowrap;
        direction:ltr; -webkit-font-smoothing:antialiased; font-feature-settings:'liga'; }

  /* ===== Encabezado ===== */
  .ini-hola { color:#8b949e; font-size:14px; margin:0; }
  .ini-title { color:#e6edf3; font-size:26px; font-weight:800; margin:2px 0 0; letter-spacing:-.3px; }
  .st-key-ini_sel button { background:#161b22 !important; border:1px solid #30363d !important;
      border-radius:999px !important; color:#e6edf3 !important; padding:6px 16px !important;
      min-height:40px !important; box-shadow:none !important; }
  .st-key-ini_sel button p { font-size:13px !important; font-weight:600 !important; }
  .st-key-ini_sel button:hover { border-color:#58a6ff !important; }
  .st-key-ini_operar button { background:linear-gradient(135deg,#3fb950,#2ea043) !important;
      border:none !important; border-radius:999px !important; min-height:40px !important;
      box-shadow:0 4px 14px rgba(46,160,67,.25) !important; }
  .st-key-ini_operar button p { color:#fff !important; font-weight:700 !important; font-size:14px !important; }

  /* ===== Tarjetas base ===== */
  .st-key-ini_hero, .st-key-ini_salud {
      background:#0f1620; border:1px solid #202a37; border-radius:18px;
      padding:22px 24px; height:100%; box-sizing:border-box; position:relative; overflow:hidden; }
  .st-key-ini_hero::before { content:""; position:absolute; left:0; top:0; right:0; height:3px;
      background:linear-gradient(90deg,#ff4b4b,#ff8f00); }
  .st-key-ini_hero [data-testid="stVerticalBlock"],
  .st-key-ini_salud [data-testid="stVerticalBlock"] { gap:10px; }

  /* Equity */
  .hero-top { display:flex; align-items:center; gap:10px; }
  .hero-lbl { color:#8b949e; font-size:13px; font-weight:600; letter-spacing:.3px; text-transform:uppercase; }
  .hero-badge { background:rgba(240,180,41,.12); color:#f0b429; border:1px solid rgba(240,180,41,.35);
      font-size:11px; font-weight:700; padding:2px 9px; border-radius:999px; }
  .hero-eq { color:#ffffff; font-size:44px; font-weight:800; line-height:1.05; margin-top:4px;
      letter-spacing:-1px; font-variant-numeric:tabular-nums; }
  .hero-eq small { font-size:16px; font-weight:600; color:#8b949e; margin-left:6px; letter-spacing:0; }
  .hero-pl { display:inline-flex; align-items:center; gap:6px; margin-top:10px;
      padding:5px 12px; border-radius:999px; font-size:13px; font-weight:700; }
  .hero-pl.up { background:rgba(63,185,80,.12); color:#3fb950; }
  .hero-pl.dn { background:rgba(248,81,73,.12); color:#f85149; }
  .hero-pl .t { color:#8b949e; font-weight:500; }
  .kpis { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:18px; }
  .kpi { background:#151c27; border:1px solid #252f3d; border-radius:12px; padding:12px 14px; }
  .kpi .k { color:#8b949e; font-size:12px; }
  .kpi .v { color:#e6edf3; font-size:17px; font-weight:700; margin-top:4px;
      font-family:ui-monospace,Consolas,monospace; white-space:nowrap; }
  /* Ojo (ocultar montos) arriba a la derecha de la tarjeta */
  .st-key-ini_hero .st-key-ini_ojo { position:absolute !important; top:16px; right:16px;
      width:auto !important; z-index:3; }
  .st-key-ini_ojo button { background:#151c27 !important; border:1px solid #252f3d !important;
      border-radius:10px !important; min-height:34px !important; padding:0 10px !important; }
  .st-key-ini_ojo button:hover { border-color:#58a6ff !important; }

  /* ===== Salud de la cuenta ===== */
  .sal-title { color:#e6edf3; font-size:15px; font-weight:700; }
  .sal-nivel { display:flex; align-items:baseline; justify-content:space-between; margin-top:6px; }
  .sal-nivel .k { color:#8b949e; font-size:13px; }
  .sal-nivel .v { font-size:28px; font-weight:800; font-variant-numeric:tabular-nums; }
  .sal-estado { font-size:12px; font-weight:700; padding:2px 10px; border-radius:999px; }
  .sal-bar-lbl { display:flex; justify-content:space-between; color:#8b949e; font-size:12px; margin-top:12px; }
  .sal-bar-lbl b { color:#e6edf3; }
  .sal-bar { height:8px; border-radius:8px; background:#21262d; overflow:hidden; margin-top:6px; }
  .sal-bar > div { height:100%; border-radius:8px; background:linear-gradient(90deg,#2f81f7,#58a6ff);
      transition:width .3s ease; }
  .sal-rows { margin-top:14px; }
  .sal-row { display:flex; justify-content:space-between; padding:8px 0; border-top:1px solid #1b2430;
      font-size:13px; }
  .sal-row .k { color:#8b949e; }
  .sal-row .v { color:#e6edf3; font-weight:600; font-family:ui-monospace,Consolas,monospace; }

  /* ===== Secciones ===== */
  .ini-sec { display:flex; align-items:center; justify-content:space-between; margin:8px 0 -4px; }
  .ini-sec h3 { color:#e6edf3; font-size:17px !important; font-weight:700 !important; margin:0; padding:0; }
  .ini-sec .s { color:#8b949e; font-size:13px; }

  /* ===== Accesos rápidos ===== */
  .acc-card { display:flex; align-items:center; gap:14px; background:#0f1620; border:1px solid #202a37;
      border-radius:14px; padding:16px; transition:border-color .15s ease, transform .15s ease; }
  [class*="st-key-accrow_"]:hover .acc-card { border-color:#2f3d4f; transform:translateY(-1px); }
  .acc-ic { flex:0 0 42px; width:42px; height:42px; border-radius:12px; display:flex;
      align-items:center; justify-content:center; font-size:22px; }
  .acc-tx { flex:1 1 auto; min-width:0; }
  .acc-t { color:#e6edf3; font-size:14px; font-weight:700; }
  .acc-s { color:#8b949e; font-size:12px; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .acc-go { color:#586174; font-size:20px; }
  [class*="st-key-accrow_"] { position:relative; }
  [class*="st-key-accsel_"] { position:absolute !important; inset:0 !important; width:100% !important;
      height:100% !important; margin:0 !important; padding:0 !important; z-index:3; }
  [class*="st-key-accsel_"] * { width:100% !important; height:100% !important; min-height:0 !important;
      margin:0 !important; padding:0 !important; }
  [class*="st-key-accsel_"] button { opacity:0; cursor:pointer; }

  /* ===== Promociones ===== */
  .promo-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
  .promo-card { position:relative; overflow:hidden; border-radius:14px; padding:16px 18px;
      background:#0f1620; border:1px solid #202a37; }
  .promo-card::before { content:""; position:absolute; inset:0; opacity:.18; }
  .promo-card.a::before { background:linear-gradient(135deg,#2f81f7,transparent 70%); }
  .promo-card.b::before { background:linear-gradient(135deg,#a371f7,transparent 70%); }
  .promo-card.c::before { background:linear-gradient(135deg,#ff8f00,transparent 70%); }
  .promo-card h4 { position:relative; margin:0 0 4px; color:#e6edf3; font-size:14px; font-weight:700; }
  .promo-card p { position:relative; margin:0; color:#8b949e; font-size:12.5px; }
  .promo-card .mi { position:relative; font-size:22px; margin-bottom:8px; display:block; }

  /* ===== Posiciones abiertas ===== */
  .st-key-ini_cartera { background:#0f1620; border:1px solid #202a37; border-radius:18px; padding:6px 0; }
  table.pos { width:100%; border-collapse:collapse; font-size:13px; }
  table.pos th { color:#8b949e; text-align:left; font-weight:600; font-size:12px;
      padding:12px 18px; border-bottom:1px solid #1b2430; }
  table.pos td { color:#e6edf3; padding:12px 18px; border-bottom:1px solid #141a22; }
  table.pos tr:last-child td { border-bottom:none; }
  table.pos .r { text-align:right; font-family:ui-monospace,Consolas,monospace; }
  .pos-sym { display:flex; align-items:center; gap:10px; font-weight:700; }
  .pos-side { font-size:11px; font-weight:700; padding:3px 10px; border-radius:999px; }
  .pos-side.buy { background:rgba(63,185,80,.12); color:#3fb950; }
  .pos-side.sell { background:rgba(248,81,73,.12); color:#f85149; }
  .car-up { color:#3fb950; font-weight:700; }
  .car-down { color:#f85149; font-weight:700; }
  .pos-empty { display:flex; flex-direction:column; align-items:center; gap:6px; padding:28px 10px;
      color:#8b949e; font-size:13px; text-align:center; }
  .pos-empty .mi { font-size:30px; color:#586174; }
  .st-key-ini_vercartera button { background:transparent !important; border:1px solid #30363d !important;
      border-radius:999px !important; min-height:32px !important; padding:2px 14px !important; }
  .st-key-ini_vercartera button p { font-size:12.5px !important; color:#c9d1d9 !important; }

  /* ===== Modal selección de cuenta ===== */
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

# (ícono Material, color, título, subtítulo, destino o None)
_ACCIONES = [
    ("candlestick_chart", "#3fb950", "Operar", "Gráfico y ticket de órdenes", "trading"),
    ("content_copy", "#a371f7", "Copy trading", "Sigue estrategias", "copytrading"),
    ("table_rows", "#2f81f7", "Cotizaciones", "Mercados en vivo", "cotizaciones"),
    ("newspaper", "#ff8f00", "Noticias", "Lo último del mercado", "noticias"),
]
_PROMOS = [
    ("a", "redeem", "#2f81f7", "Reintegros en cada activo", "Sin límites mientras dure la promoción."),
    ("b", "emoji_events", "#a371f7", "Competiciones semanales", "Gana premios operando cada semana."),
    ("c", "group_add", "#ff8f00", "Programa de referidos", "Invita y gana con cada amigo."),
]


def _fmt(v, dec=2):
    try:
        return f"${float(v):,.{dec}f}"
    except Exception:
        return "—"


def _mi(nombre: str, color: str = "", size: int = 0) -> str:
    estilo = (f"color:{color};" if color else "") + (f"font-size:{size}px;" if size else "")
    return f"<span class='mi' style='{estilo}'>{nombre}</span>"


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
    if st.button("Crear nueva cuenta", icon=":material/add:", width="stretch", key="selc_crear"):
        st.toast("Para agregar otra cuenta, inicia sesión con ella en el terminal MT5.")


def _estado_margen(ml: float) -> tuple:
    """(texto, color) del semáforo del nivel de margen."""
    if not ml:
        return "Sin posiciones", "#8b949e"
    if ml >= 300:
        return "Saludable", "#3fb950"
    if ml >= 150:
        return "Atención", "#d29922"
    return "Riesgo", "#f85149"


def renderizar_panel_inicio(main=None):
    inicializar_mt5()
    st.html(_CSS)

    if "ini_ocultar" not in st.session_state:
        st.session_state.ini_ocultar = False
    usuario = st.session_state.get("usuario_info") or {}
    nombre = (usuario.get("nombre") if isinstance(usuario, dict) else "") or ""

    # --- Cuenta (en vivo vía feed; sin recarga periódica si hay feed) ---
    @st.fragment(run_every=_intervalo("2s"))
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
        margin = info.get("margin", 0.0)
        libre = info.get("margin_free", 0.0)
        ml = info.get("margin_level", 0.0)
        lev = info.get("leverage", 0)
        uso = (margin / equity * 100) if equity else 0.0
        oculto = st.session_state.get("ini_ocultar", False)

        # Encabezado: saludo + chip de cuenta + Operar
        h1, h2, h3 = st.columns([3, 1.6, 0.8], vertical_alignment="bottom")
        with h1:
            st.html(f"<p class='ini-hola'>Hola{', ' + nombre.split()[0] if nombre else ''}</p>"
                    "<div class='ini-title'>Resumen de tu cuenta</div>")
        with h2:
            if st.button(f"{tipo} · #{login}", key="ini_sel", icon=":material/account_balance_wallet:",
                         width="stretch"):
                st.session_state.ini_modal_cuentas = True
                st.rerun()
        with h3:
            if st.button("Operar", key="ini_operar", icon=":material/trending_up:", width="stretch"):
                st.session_state.nav_activo = "trading"
                st.rerun()

        def vivo(campo, texto, fmt="usd", extra=""):
            if oculto:
                return "••••"
            return f"<span data-pj-acc='{campo}' data-pj-fmt='{fmt}' {extra}>{texto}</span>"

        c_hero, c_sal = st.columns([1.75, 1], gap="medium")
        with c_hero:
            with st.container(key="ini_hero"):
                if st.button("", key="ini_ojo", help="Mostrar montos" if oculto else "Ocultar montos",
                             icon=":material/visibility:" if oculto else ":material/visibility_off:"):
                    st.session_state.ini_ocultar = not oculto
                    st.rerun(scope="fragment")
                up = profit >= 0
                # La moneda va FUERA del número en vivo (con el sufijo en un atributo
                # el espacio se perdía y se veía "-4,492.00USD").
                pl_html = ("••••" if oculto else
                           f"<span data-pj-acc='profit' data-pj-fmt='signed'>{profit:+,.2f}</span>"
                           f"<span style='margin-left:4px;'>{moneda}</span>")
                st.html(
                    "<div class='hero-top'><span class='hero-lbl'>Equity</span>"
                    f"<span class='hero-badge'>{tipo}</span></div>"
                    f"<div class='hero-eq'>{vivo('equity', _fmt(equity))}<small>{moneda}</small></div>"
                    f"<div class='hero-pl {'up' if up else 'dn'}'>"
                    f"{_mi('trending_up' if up else 'trending_down', size=18)}{pl_html}"
                    "<span class='t'>P/G flotante</span></div>"
                    "<div class='kpis'>"
                    f"<div class='kpi'><div class='k'>Saldo</div><div class='v'>{vivo('balance', _fmt(balance))}</div></div>"
                    f"<div class='kpi'><div class='k'>Margen libre</div><div class='v'>{vivo('margin_free', _fmt(libre))}</div></div>"
                    f"<div class='kpi'><div class='k'>Margen usado</div><div class='v'>{vivo('margin', _fmt(margin))}</div></div>"
                    "</div>"
                )
        with c_sal:
            with st.container(key="ini_salud"):
                estado, col = _estado_margen(ml)
                st.html(
                    "<div class='sal-title'>Salud de la cuenta</div>"
                    "<div class='sal-nivel'><span class='k'>Nivel de margen</span>"
                    f"<span class='sal-estado' style='color:{col};background:{col}1f;'>{estado}</span></div>"
                    f"<div class='sal-nivel' style='margin-top:0'><span class='v' style='color:{col};'>"
                    f"<span data-pj-acc='margin_level' data-pj-fmt='pct'>{(f'{ml:,.2f}%' if ml else '—')}</span>"
                    "</span></div>"
                    "<div class='sal-bar-lbl'><span>Margen usado del equity</span>"
                    f"<b><span data-pj-acc='uso_margen' data-pj-fmt='pct'>{uso:,.2f}%</span></b></div>"
                    f"<div class='sal-bar'><div data-pj-bar='uso_margen' style='width:{min(uso, 100):.1f}%;'></div></div>"
                    "<div class='sal-rows'>"
                    f"<div class='sal-row'><span class='k'>Apalancamiento</span><span class='v'>{f'{lev}:1' if lev else '—'}</span></div>"
                    f"<div class='sal-row'><span class='k'>Crédito</span><span class='v'>"
                    f"<span data-pj-acc='credit' data-pj-fmt='usd'>{_fmt(info.get('credit', 0.0))}</span></span></div>"
                    f"<div class='sal-row'><span class='k'>Servidor</span><span class='v'>{info.get('servidor', '—')}</span></div>"
                    "</div>"
                )

    # --- Posiciones abiertas (precio y P/G en vivo por el feed) ---
    @st.fragment(run_every=_intervalo("2s", "5s"))
    def _posiciones_vivo():
        pos = obtener_posiciones()
        s1, s2 = st.columns([4, 1], vertical_alignment="center")
        with s1:
            st.html(f"<div class='ini-sec'><h3>Posiciones abiertas</h3>"
                    f"<span class='s'>{len(pos)} {'posición' if len(pos) == 1 else 'posiciones'}</span></div>")
        with s2:
            if st.button("Ver cartera", key="ini_vercartera", icon=":material/arrow_forward:",
                         width="stretch"):
                st.session_state.nav_activo = "portafolio"
                st.rerun()
        with st.container(key="ini_cartera"):
            if not pos:
                st.html("<div class='pos-empty'>" + _mi("inventory_2") +
                        "No tienes posiciones abiertas.<br>Las operaciones que abras aparecerán aquí.</div>")
                return
            filas = ""
            for p in pos:
                neto = p["profit"] + p.get("swap", 0.0)     # igual que Cartera y la barra superior
                tk = p.get("ticket")
                compra = p["tipo"] == "Compra"
                sym = p["symbol"].replace("...", "")
                filas += (
                    "<tr>"
                    f"<td><div class='pos-sym'>{icono_activo(p['symbol'], 26)}{sym}</div></td>"
                    f"<td><span class='pos-side {'buy' if compra else 'sell'}'>{p['tipo']}</span></td>"
                    f"<td class='r'>{p['volumen']:,.2f}</td>"
                    f"<td class='r'>{p['precio_apertura']:,.5f}</td>"
                    f"<td class='r' data-pj-posc='{tk}' data-pj-d='5'>{p['precio_actual']:,.5f}</td>"
                    f"<td class='r {'car-up' if neto >= 0 else 'car-down'}' data-pj-pos='{tk}'>{neto:+,.2f}</td>"
                    "</tr>"
                )
            st.html(
                "<table class='pos'><thead><tr>"
                "<th>Activo</th><th>Tipo</th><th class='r'>Volumen</th>"
                "<th class='r'>Apertura</th><th class='r'>Actual</th><th class='r'>P/G</th>"
                "</tr></thead><tbody>" + filas + "</tbody></table>"
            )

    # --- Contenido centrado con ancho máximo ---
    with st.container(key="ini_wrap"):
        _cuenta_vivo()

        st.html("<div class='ini-sec'><h3>Accesos rápidos</h3></div>")
        acc_cols = st.columns(len(_ACCIONES), gap="medium")
        for i, (ic, color, titulo, sub, dest) in enumerate(_ACCIONES):
            with acc_cols[i]:
                with st.container(key=f"accrow_{i}"):
                    st.html(
                        f"<div class='acc-card'><div class='acc-ic' style='background:{color}1f;'>"
                        f"{_mi(ic, color)}</div><div class='acc-tx'><div class='acc-t'>{titulo}</div>"
                        f"<div class='acc-s'>{sub}</div></div>{_mi('chevron_right')}</div>"
                    )
                    if st.button(titulo, key=f"accsel_{i}"):
                        if dest:
                            st.session_state.nav_activo = dest
                            st.rerun()
                        else:
                            st.toast(f"{titulo}: disponible próximamente.")

        _posiciones_vivo()

        st.html("<div class='ini-sec'><h3>Promociones</h3></div>")
        st.html("<div class='promo-grid'>" + "".join(
            f"<div class='promo-card {c}'>{_mi(ic, color)}<h4>{t}</h4><p>{d}</p></div>"
            for c, ic, color, t, d in _PROMOS) + "</div>")

    # --- Modal selección de cuenta (fuera de los fragmentos en vivo) ---
    if st.session_state.get("ini_modal_cuentas"):
        _modal_cuentas()