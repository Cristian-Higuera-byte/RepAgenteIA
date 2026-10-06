"""
order_panel.py
--------------
Ticket de orden (comprar / vender) a la derecha del gráfico, con el diseño de XM:
- "Orden con un clic" con el interruptor a la derecha (si está apagado, pide confirmación).
- VENTA | COMPRA unidos (el lado elegido se pinta en rojo/verde) + spread al centro.
- Cantidad / Lotes a todo el ancho y el volumen en una tarjeta con la etiqueta
  DENTRO y el número grande (como XM).
- Margen requerido + barra con el % del margen libre que usaría la orden.
- Tarjeta "Compra/Venta al llegar a este precio" (orden pendiente Limit/Stop) con
  "Válida hasta cancelar", y tarjeta de Tomar ganancia / Limitar pérdida.
- Botón grande "Colocar orden en {precio}" del color del lado elegido.

Las órdenes se envían a la cuenta CONECTADA en MetaTrader 5 (demo en desarrollo)
vía tools.mt5_bridge. El usuario confirma cada operación (salvo "orden con un clic").
El estilo usa CSS acotado a las claves de este panel (.st-key-ord_*); el ancho del
panel lo define app.py (no se toca aquí).
"""
import streamlit as st
import MetaTrader5 as mt5  # type: ignore[import-untyped]

from components.live_feed import attrs as _live, intervalo as _intervalo

from tools.mt5_bridge import (
    MT5_LOCK, inicializar_mt5, obtener_precio_actual, resolver_simbolo,
    ejecutar_orden_mercado, colocar_orden_pendiente,
)

_CSS = """
<style>
  /* ====== Tarjeta del panel ====== */
  .st-key-ord_panel { background:#0f1620; border:1px solid #202a37; border-radius:14px;
      padding:16px 14px 16px; }
  .st-key-ord_panel [data-testid="stVerticalBlock"] { gap:12px; }
  .ord-h { color:#e6edf3; font-weight:800; font-size:16px; margin:0 0 2px; }
  .ord-sub { color:#8b949e; font-size:12px; margin:0; }

  /* ====== Interruptores: texto a la izquierda, switch a la derecha, verde ======
     Estructura de Streamlit 1.64 (medida en el navegador): stCheckbox > label >
     [span con el input oculto] + [div = riel del switch] + [div = texto]. El
     contenedor viene con width="fit-content", por eso se fuerza al 100 %. */
  [class*="st-key-ord_tg_"] [data-testid="stElementContainer"],
  [class*="st-key-ord_tg_"] [data-testid="stCheckbox"] { width:100% !important; }
  [class*="st-key-ord_tg_"] [data-testid="stCheckbox"] label {
      display:flex !important; flex-direction:row-reverse; justify-content:space-between;
      align-items:center; width:100%; gap:12px; }
  [class*="st-key-ord_tg_"] [data-testid="stCheckbox"] label p {
      color:#e6edf3 !important; font-size:14px !important; font-weight:600 !important;
      line-height:1.3 !important; }
  [class*="st-key-ord_tg_"] [data-testid="stCheckbox"] label:has(input:checked) > span + div {
      background:#2ea043 !important; }
  [class*="st-key-ord_tg_"] [data-testid="stTooltipIcon"] { display:none !important; }

  /* ====== VENTA | COMPRA unidos (como XM) ====== */
  .ord-join { position:relative; display:flex; border-radius:12px; overflow:hidden;
      border:1px solid #252f3d; }
  .ord-half { flex:1; min-width:0; overflow:hidden; padding:10px 12px; box-sizing:border-box;
      background:#151c27; transition:background .12s ease; }
  .ord-half .ord-lbl { font-size:11px; font-weight:700; letter-spacing:.4px; white-space:nowrap;
      color:#8b949e; }
  .ord-half .ord-px { font-size:15px; font-weight:800; margin-top:2px; white-space:nowrap;
      overflow:hidden; text-overflow:ellipsis; color:#8b949e;
      font-family:ui-monospace,Consolas,monospace; }
  .ord-sell { text-align:left; }
  .ord-buy { text-align:right; }
  .ord-sell.sel { background:linear-gradient(135deg,#f85149,#da3633); }
  .ord-buy.sel  { background:linear-gradient(135deg,#3fb950,#2ea043); }
  .ord-half.sel .ord-lbl, .ord-half.sel .ord-px { color:#ffffff; }
  .ord-spread { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
      background:#e9edf2; color:#111820; font-size:12px; font-weight:800;
      border-radius:8px; padding:3px 8px; font-family:ui-monospace,Consolas,monospace;
      pointer-events:none; z-index:4; box-shadow:0 1px 4px rgba(0,0,0,.35); }

  /* Botones invisibles que hacen clicable cada mitad / el botón grande */
  [class*="st-key-ord_bx"] { position:relative; }
  [class*="st-key-ord_ov"] { position:absolute !important; inset:0 !important;
      width:100% !important; height:100% !important; margin:0 !important;
      padding:0 !important; z-index:3; }
  [class*="st-key-ord_ov"] * { width:100% !important; height:100% !important;
      min-height:0 !important; margin:0 !important; padding:0 !important; }
  [class*="st-key-ord_ov"] button { opacity:0; cursor:pointer; }
  [class*="st-key-ord_ovsell"] { right:auto !important; width:50% !important; }
  [class*="st-key-ord_ovbuy"]  { left:auto !important;  width:50% !important; }

  /* ====== Cantidad | Lotes (segmentado a todo el ancho) ====== */
  .st-key-ord_modo [data-testid="stButtonGroup"] { width:100%; }
  .st-key-ord_modo [role="radiogroup"] { width:100%; display:flex;
      background:#0d1117; border:1px solid #252f3d; border-radius:10px; padding:3px; gap:3px; }
  .st-key-ord_modo button { flex:1 1 0; border:none !important; border-radius:8px !important;
      background:transparent !important; min-height:36px !important; box-shadow:none !important; }
  .st-key-ord_modo button p { color:#c9d1d9 !important; font-size:14px !important;
      font-weight:700 !important; }
  .st-key-ord_modo button[aria-checked="true"] { background:#2a3342 !important; }
  .st-key-ord_modo button[aria-checked="true"] p { color:#ffffff !important; }

  /* ====== Campos tipo tarjeta: etiqueta DENTRO + número grande ====== */
  [class*="st-key-ord_box_"] { position:relative; }
  [class*="st-key-ord_box_"] [data-testid="stVerticalBlock"] { gap:0 !important; }
  [class*="st-key-ord_box_"] [data-testid="stElementContainer"]:has(.ord-box-lbl) {
      position:absolute !important; inset:0; z-index:2; pointer-events:none; }
  .ord-box-lbl { position:absolute; top:9px; left:15px; color:#8b949e; font-size:12px; }
  .ord-box-suf { position:absolute; right:15px; bottom:13px; color:#8b949e; font-size:14px;
      font-weight:600; }
  [class*="st-key-ord_box_"] [data-testid="stNumberInputContainer"] {
      background:#0d1117 !important; border:1px solid #2b3546 !important;
      border-radius:12px !important; height:62px; }
  [class*="st-key-ord_box_"] [data-testid="stNumberInputContainer"]:focus-within {
      border-color:#2f81f7 !important; box-shadow:0 0 0 1px #2f81f7 !important; }
  [class*="st-key-ord_box_"] input {
      font-size:20px !important; font-weight:700 !important; color:#ffffff !important;
      padding:22px 15px 6px !important; background:transparent !important;
      font-family:ui-monospace,Consolas,monospace !important; }
  /* + / − como en XM: apilados a la derecha y visibles SOLO al pasar el mouse.
     En Streamlit 1.64 van en un div después del input: [StepDown][StepUp];
     OJO: no escribir etiquetas HTML dentro de este CSS (ni en comentarios):
     el sanitizador de st.html elimina el bloque de estilos completo.
     column-reverse deja el + arriba. */
  [class*="st-key-ord_box_"] [data-testid="stNumberInputContainer"] { position:relative; }
  [class*="st-key-ord_box_"] [data-testid="stNumberInputContainer"] > div {
      position:absolute; right:8px; top:50%; transform:translateY(-50%); z-index:3;
      display:flex; flex-direction:column-reverse; gap:3px;
      opacity:0; pointer-events:none; transition:opacity .15s ease; }
  [class*="st-key-ord_box_"]:hover [data-testid="stNumberInputContainer"] > div,
  [class*="st-key-ord_box_"] [data-testid="stNumberInputContainer"]:focus-within > div {
      opacity:1; pointer-events:auto; }
  [class*="st-key-ord_box_"] [data-testid="stNumberInputStepUp"],
  [class*="st-key-ord_box_"] [data-testid="stNumberInputStepDown"] {
      width:26px !important; height:23px !important; min-height:0 !important; padding:0 !important;
      background:#2a3342 !important; border:none !important; border-radius:6px !important;
      color:#e6edf3 !important; display:flex; align-items:center; justify-content:center; }
  [class*="st-key-ord_box_"] [data-testid="stNumberInputStepUp"]:hover,
  [class*="st-key-ord_box_"] [data-testid="stNumberInputStepDown"]:hover { background:#3a4558 !important; }
  [class*="st-key-ord_box_"] [data-testid="stNumberInputStepDown"]:disabled { opacity:.35; }
  .ord-box-suf { transition:right .15s ease; }
  [class*="st-key-ord_box_"]:hover .ord-box-suf,
  [class*="st-key-ord_box_"]:focus-within .ord-box-suf { right:44px; }

  /* ====== Margen ====== */
  .ord-margen { color:#8b949e; font-size:13px; display:flex; gap:6px; align-items:baseline; }
  .ord-margen b { color:#e6edf3; font-weight:700; }
  .ord-mbar-row { display:flex; align-items:center; gap:12px; margin-top:8px; }
  .ord-mbar { flex:1; height:6px; border-radius:6px; background:#2b3546; overflow:hidden; }
  .ord-mbar > div { height:100%; border-radius:6px; transition:width .2s ease; }
  .ord-mbar-pct { font-size:14px; font-weight:700; color:#e6edf3; min-width:58px;
      text-align:right; }
  .ord-sin-margen { color:#f85149; font-size:13px; font-weight:600; margin-top:6px; }
  .ord-hint { color:#8b949e; font-size:12px; }
  .ord-hint b { display:block; color:#e6edf3; font-size:14px; margin-top:2px;
      font-family:ui-monospace,Consolas,monospace; }

  /* ====== Tarjetas agrupadas (orden pendiente / TP-SL) ====== */
  [class*="st-key-ord_card_"] { background:#151c27; border:1px solid #252f3d;
      border-radius:12px; padding:12px 14px; }
  [class*="st-key-ord_card_"] [data-testid="stVerticalBlock"] { gap:10px; }
  .ord-sep { height:1px; background:#252f3d; margin:2px -14px; }

  /* ====== Botón grande "Colocar orden en" ====== */
  .ord-place { display:flex; align-items:center; justify-content:space-between;
      border-radius:12px; padding:13px 18px; min-height:64px; }
  .ord-place .pl-lbl { font-size:13px; color:rgba(255,255,255,.92); }
  .ord-place .pl-px { font-size:22px; font-weight:800; color:#fff; line-height:1.15;
      white-space:nowrap; font-family:ui-monospace,Consolas,monospace; }
  .ord-place .pl-arrow { font-size:24px; color:#fff; font-weight:700; }
  .ord-place-buy  { background:linear-gradient(135deg,#3fb950,#2ea043); }
  .ord-place-sell { background:linear-gradient(135deg,#f85149,#da3633); }
  .ord-place-off { background:#1c2a24 !important; opacity:.6; }
  .ord-place-off .pl-lbl, .ord-place-off .pl-px, .ord-place-off .pl-arrow { color:#8b949e !important; }

  /* ====== Confirmación ====== */
  .ord-conf { background:#151c27; border:1px solid #2b3546; border-radius:12px;
      padding:12px 14px; color:#c9d1d9; font-size:13px; line-height:1.45; }
  .ord-conf b { color:#ffffff; }
  .ord-conf .t { color:#8b949e; font-size:12px; margin-bottom:4px; }
  .st-key-ord_ok button { background:#2ea043 !important; border:none !important; }
  .st-key-ord_ok button p { color:#fff !important; font-weight:700 !important; }
</style>
"""


def _info_simbolo(real):
    try:
        with MT5_LOCK:
            mt5.symbol_select(real, True)
            return mt5.symbol_info(real)
    except Exception:
        return None


def _margen(real, volumen, precio, tipo):
    try:
        action = mt5.ORDER_TYPE_BUY if tipo == "BUY" else mt5.ORDER_TYPE_SELL
        with MT5_LOCK:
            return mt5.order_calc_margin(action, real, float(volumen), float(precio))
    except Exception:
        return None


def _margen_libre():
    """Margen libre de la cuenta (account_info().margin_free) o None."""
    try:
        with MT5_LOCK:
            cuenta = mt5.account_info()
        return float(cuenta.margin_free) if cuenta is not None else None
    except Exception:
        return None


def _ejecutar(real, visible, tipo, vol, sl, tp, pendiente=None, gtc=True):
    """Envía la orden a MT5: a mercado, o pendiente si `pendiente` trae un precio."""
    verbo = "Compra" if tipo == "BUY" else "Venta"
    if pendiente:
        res = colocar_orden_pendiente(real, tipo, vol, pendiente, sl, tp, hasta_cancelar=gtc)
        ok = (f"Orden pendiente {res.get('tipo', '')} colocada: {vol:.2f} lotes de {visible} "
              f"@ {res.get('price')}" + ("" if gtc else " (solo hoy)"))
    else:
        res = ejecutar_orden_mercado(real, tipo, vol, sl, tp)
        ok = f"{verbo} ejecutada: {res.get('volume')} lotes de {visible} @ {res.get('price')}"
    st.session_state.ord_result = ("error", res["error"]) if "error" in res else ("ok", ok)
    st.session_state.ord_confirm = None


def _campo(clave: str, etiqueta: str, sufijo: str = ""):
    """Contenedor de un campo tipo tarjeta: etiqueta dentro (arriba) + sufijo."""
    cont = st.container(key=f"ord_box_{clave}")
    cont.html(f"<div class='ord-box-lbl'>{etiqueta}</div>"
              + (f"<div class='ord-box-suf'>{sufijo}</div>" if sufijo else ""))
    return cont


def renderizar_panel_orden(main=None):
    inicializar_mt5()
    activo = st.session_state.get("activo_seleccionado", "EURUSD...")
    real = resolver_simbolo(activo)
    visible = activo.replace("...", "").strip()
    info = _info_simbolo(real)
    dig = int(getattr(info, "digits", 5) or 5) if info else 5
    vmin = float(getattr(info, "volume_min", 0.01) or 0.01) if info else 0.01
    vstep = float(getattr(info, "volume_step", 0.01) or 0.01) if info else 0.01
    point = getattr(info, "point", 0.0) if info else 0.0

    if "ord_side" not in st.session_state:
        st.session_state.ord_side = "BUY"

    st.html(_CSS)
    with st.container(key="ord_panel"):
        st.html(f"<div class='ord-h'>Operar · {visible}</div>"
                f"<div class='ord-sub'>Cuenta conectada en MT5 (demo)</div>")

        # TODO el ticket va dentro de UN fragmento cuyas acciones usan
        # scope="fragment" (nunca rerun de app desde aquí → sin parpadeo).
        @st.fragment(run_every=_intervalo("2s"))   # con feed: precios/spread por live_feed.py
        def _ticket():
            t = obtener_precio_actual(real)
            if "error" in t:
                st.caption("Sin precio en vivo. ¿Está abierto MetaTrader 5?")
                return
            bid, ask = t.get("bid", 0), t.get("ask", 0)
            side = st.session_state.get("ord_side", "BUY")
            compra = side == "BUY"

            # --- Orden con un clic (interruptor a la derecha) ---
            with st.container(key="ord_tg_oc"):
                oc = st.toggle("Orden con un clic", key="ord_oc", value=False,
                               help="Si está activo, la orden se envía sin confirmación.")

            # --- VENTA | COMPRA unidos + spread (selección por mitades) ---
            pip = (point * 10) if dig in (3, 5) else (point or 1)
            spr_val = (ask - bid) / pip if pip else 0
            spr = f"{spr_val:,.1f}" if spr_val < 100 else f"{spr_val:,.0f}"
            with st.container(key="ord_bxrow"):
                st.html(
                    "<div class='ord-join'>"
                    f"<div class='ord-half ord-sell {'' if compra else 'sel'}'><div class='ord-lbl'>VENTA</div>"
                    f"<div class='ord-px' {_live(real, 'bid', d=dig)}>{bid:,.{dig}f}</div></div>"
                    f"<div class='ord-half ord-buy {'sel' if compra else ''}'><div class='ord-lbl'>COMPRA</div>"
                    f"<div class='ord-px' {_live(real, 'ask', d=dig)}>{ask:,.{dig}f}</div></div>"
                    f"<div class='ord-spread' {_live(real, 'spr', pip=pip)}>{spr}</div>"
                    "</div>"
                )
                if st.button("Vender", key="ord_ovsell"):
                    st.session_state.ord_side = "SELL"
                    st.rerun(scope="fragment")
                if st.button("Comprar", key="ord_ovbuy"):
                    st.session_state.ord_side = "BUY"
                    st.rerun(scope="fragment")

            # --- Cantidad | Lotes + volumen (tarjeta con número grande) ---
            contract = float(getattr(info, "trade_contract_size", 1) or 1)
            modo = st.segmented_control("Tipo de volumen", ["Cantidad", "Lotes"], default="Lotes",
                                        label_visibility="collapsed", key="ord_modo",
                                        width="stretch") or "Lotes"
            if modo == "Lotes":
                with _campo("qty", "Volumen", "lote(s)"):
                    vol = st.number_input("Volumen (lotes)", min_value=vmin, value=vmin,
                                          step=vstep, format="%.2f", key="ord_vol",
                                          label_visibility="collapsed")
            else:
                with _campo("qty", "Cantidad", "unidades"):
                    cant = st.number_input("Cantidad (unidades)", min_value=1.0, value=1.0,
                                           step=1.0, format="%.0f", key="ord_cant",
                                           label_visibility="collapsed")
                vol = (cant / contract) if contract else cant
                vol = max(vmin, round(vol / vstep) * vstep) if vstep else max(vmin, vol)

            # Hueco del margen ANTES de la orden pendiente (orden visual de XM);
            # se llena más abajo porque depende del precio pendiente.
            slot_margen = st.container()

            # --- Compra/Venta al llegar a este precio (orden pendiente) ---
            ref = ask if compra else bid
            pendiente, gtc = None, True
            with st.container(key="ord_card_pend"):
                with st.container(key="ord_tg_pend"):
                    usar_pend = st.toggle(
                        f"{'Compra' if compra else 'Venta'} al llegar a este precio", key="ord_pend",
                        help="Orden pendiente: se ejecuta cuando el mercado llega al precio indicado.")
                if usar_pend:
                    with _campo("pxp", "Precio"):
                        pendiente = st.number_input(
                            "Precio de la orden pendiente", min_value=0.0, value=round(float(ref), dig),
                            step=(point * 10) or 0.0001, format=f"%.{dig}f",
                            key=f"ord_pxp_{real}_{side}", label_visibility="collapsed")
                    st.html(f"<div class='ord-hint'>Precio actual de {'compra' if compra else 'venta'}:"
                            f"<b {_live(real, 'side', d=dig, side=side)}>{ref:,.{dig}f}</b></div>"
                            "<div class='ord-sep'></div>")
                    with st.container(key="ord_tg_gtc"):
                        gtc = st.toggle("Válida hasta cancelar", value=True, key="ord_gtc",
                                        help="Apagado: la orden pendiente vence al final del día.")

            # --- Margen requerido + % del margen libre (como XM) ---
            price = pendiente if pendiente else ref
            m = _margen(real, vol, price, side)
            libre = _margen_libre()
            sin_margen = bool(m and libre is not None and m > libre)
            if m:
                pct = (m / libre * 100) if libre and libre > 0 else 100.0
                color = "#f85149" if sin_margen else ("#d29922" if pct >= 90 else "#2f81f7")
                slot_margen.html(
                    f"<div class='ord-margen'><span>Margen requerido</span><b>${m:,.2f}</b></div>"
                    f"<div class='ord-mbar-row'><div class='ord-mbar'>"
                    f"<div style='width:{min(pct, 100):.1f}%; background:{color};'></div></div>"
                    f"<span class='ord-mbar-pct' style='color:{color if sin_margen else '#e6edf3'};'>"
                    f"{pct:,.2f}%</span></div>"
                    + ("<div class='ord-sin-margen'>No tiene margen suficiente para colocar "
                       "esta orden.</div><style>.st-key-ord_box_qty [data-testid='stNumberInputContainer'] "
                       "{ border-color:#f85149 !important; box-shadow:0 0 0 1px #f85149 !important; }"
                       "</style>" if sin_margen else "")
                )

            # --- Tomar ganancia / Limitar pérdida ---
            sl = tp = 0.0
            with st.container(key="ord_card_tpsl"):
                with st.container(key="ord_tg_tpsl"):
                    usar_tpsl = st.toggle("Tomar ganancia / Limitar pérdida", key="ord_tpsl")
                if usar_tpsl:
                    with _campo("sl", "Limitar pérdida"):
                        sl = st.number_input("Limitar pérdida", min_value=0.0, value=0.0,
                                             step=point or 0.0001, format=f"%.{dig}f",
                                             key="ord_sl", label_visibility="collapsed")
                    with _campo("tp", "Tomar ganancia"):
                        tp = st.number_input("Tomar ganancia", min_value=0.0, value=0.0,
                                             step=point or 0.0001, format=f"%.{dig}f",
                                             key="ord_tp", label_visibility="collapsed")

            # --- Botón grande "Colocar orden en {precio}" ---
            cls = ("ord-place-buy" if compra else "ord-place-sell") + (" ord-place-off" if sin_margen else "")
            # Pendiente: precio fijo elegido; a mercado: precio en vivo (feed)
            px_attr = "" if pendiente else _live(real, "side", d=dig, side=side)
            with st.container(key="ord_bxplace"):
                st.html(
                    f"<div class='ord-place {cls}'>"
                    f"<div><div class='pl-lbl'>Colocar orden en</div>"
                    f"<div class='pl-px' {px_attr}>{price:,.{dig}f}</div></div>"
                    f"<div class='pl-arrow'>{'↗' if compra else '↘'}</div></div>"
                )
                if not sin_margen and st.button("Colocar orden", key="ord_ovplace"):
                    st.session_state.pop("ord_result", None)  # limpia resultado previo
                    if oc:
                        _ejecutar(real, visible, side, vol, sl, tp, pendiente, gtc)
                    else:
                        st.session_state.ord_confirm = (side, vol, sl, tp, price, pendiente, gtc)
                    st.rerun(scope="fragment")

            # --- Confirmación ---
            cf = st.session_state.get("ord_confirm")
            if cf:
                tipo, v, s, tpv, px, pend, g = cf
                verbo2 = "COMPRA" if tipo == "BUY" else "VENTA"
                modo_txt = (f"Orden pendiente al llegar a <b>{px:,.{dig}f}</b>"
                            + ("" if g else " · solo hoy")) if pend else f"A mercado, ~<b>{px:,.{dig}f}</b>"
                extra = ((f"<br>Limitar pérdida: <b>{s:,.{dig}f}</b>" if s else "")
                         + (f"<br>Tomar ganancia: <b>{tpv:,.{dig}f}</b>" if tpv else ""))
                st.html(f"<div class='ord-conf'><div class='t'>Confirmar operación</div>"
                        f"<b>{verbo2}</b> de <b>{v:.2f}</b> lotes de <b>{visible}</b><br>"
                        f"{modo_txt}{extra}</div>")
                cc1, cc2 = st.columns(2)
                if cc1.button("Confirmar", key="ord_ok", icon=":material/check:", width="stretch"):
                    m2, libre2 = _margen(real, v, px, tipo), _margen_libre()
                    if m2 and libre2 is not None and m2 > libre2:
                        st.session_state.ord_result = (
                            "error", "No tiene margen suficiente para colocar esta orden.")
                        st.session_state.ord_confirm = None
                    else:
                        _ejecutar(real, visible, tipo, v, s, tpv, pend, g)
                    st.rerun(scope="fragment")
                if cc2.button("Cancelar", key="ord_cancel", width="stretch"):
                    st.session_state.ord_confirm = None
                    st.rerun(scope="fragment")

            # Resultado (persiste hasta colocar una orden nueva)
            r = st.session_state.get("ord_result")
            if r:
                if r[0] == "ok":
                    st.success(r[1], icon=":material/check_circle:")
                else:
                    st.error(f"No se pudo operar: {r[1]}", icon=":material/error:")

        _ticket()