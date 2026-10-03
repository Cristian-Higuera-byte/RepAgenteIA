"""
order_panel.py
--------------
Ticket de orden (comprar / vender) a la derecha del gráfico, estilo XM:
- Seleccionas VENTA (rojo) o COMPRA (verde) arriba; el centro muestra el spread.
- "Orden con un clic" (si está apagado, pide confirmación).
- Volumen en lotes, margen requerido, TP/SL opcional.
- Botón grande "Colocar orden" que toma el lado y color seleccionados.

Las órdenes se envían a la cuenta CONECTADA en MetaTrader 5 (demo en desarrollo)
vía tools.mt5_bridge.ejecutar_orden_mercado. El usuario confirma cada operación.
"""
import MetaTrader5 as mt5  # type: ignore[import-untyped]
import streamlit as st

try:
    from tools import mt5_bridge
except ImportError:  # pragma: no cover - graceful fallback
    mt5_bridge = None  # type: ignore[assignment]

if mt5_bridge is not None:
    MT5_LOCK = getattr(mt5_bridge, "MT5_LOCK", None)
    inicializar_mt5 = getattr(mt5_bridge, "inicializar_mt5", lambda: False)
    obtener_precio_actual = getattr(
        mt5_bridge,
        "obtener_precio_actual",
        lambda *_args, **_kwargs: {"error": "MetaTrader 5 bridge no disponible"},
    )
    resolver_simbolo = getattr(mt5_bridge, "resolver_simbolo", lambda simbolo: simbolo)
    ejecutar_orden_mercado = getattr(
        mt5_bridge,
        "ejecutar_orden_mercado",
        lambda *_args, **_kwargs: {"error": "MetaTrader 5 bridge no disponible"},
    )
else:
    MT5_LOCK = None

    def inicializar_mt5():
        return False

    def obtener_precio_actual(_real):
        return {"error": "MetaTrader 5 bridge no disponible"}

    def resolver_simbolo(simbolo):
        return simbolo

    def ejecutar_orden_mercado(*_args, **_kwargs):
        return {"error": "MetaTrader 5 bridge no disponible"}

_CSS = """
<style>
  .st-key-ord_panel { background:#0f1620; border:1px solid #202a37; border-radius:14px;
      padding:14px 14px 16px; }
  .ord-h { color:#e6edf3; font-weight:800; font-size:16px; margin:0 0 2px; }
  .ord-sub { color:#8b949e; font-size:12px; margin:0 0 10px; }
  /* Selector VENTA|COMPRA unido (como XM) */
  .ord-join { position:relative; display:flex; border-radius:14px; overflow:hidden; }
  .ord-half { flex:1; min-width:0; overflow:hidden; padding:9px 12px; box-sizing:border-box;
      transition:background .12s ease; }
  .ord-half .ord-lbl { font-size:10px; font-weight:700; letter-spacing:.5px; white-space:nowrap; }
  .ord-half .ord-px { font-size:15px; font-weight:800; margin-top:1px; white-space:nowrap;
      overflow:hidden; text-overflow:ellipsis; font-family:ui-monospace,Consolas,monospace; }
  .ord-sell { text-align:left; background:#161b22; }
  .ord-sell .ord-lbl, .ord-sell .ord-px { color:#f85149; }
  .ord-sell.sel { background:linear-gradient(135deg,#f85149,#da3633); }
  .ord-sell.sel .ord-lbl, .ord-sell.sel .ord-px { color:#ffffff; }
  .ord-buy { text-align:right; background:#161b22; }
  .ord-buy .ord-lbl, .ord-buy .ord-px { color:#3fb950; }
  .ord-buy.sel { background:linear-gradient(135deg,#3fb950,#2ea043); }
  .ord-buy.sel .ord-lbl, .ord-buy.sel .ord-px { color:#ffffff; }
  .ord-spread { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
      background:rgba(255,255,255,0.82); color:#111820; font-size:12px; font-weight:700;
      border-radius:9px; padding:4px 9px; font-family:ui-monospace,Consolas,monospace;
      pointer-events:none; z-index:4; box-shadow:0 1px 4px rgba(0,0,0,.3); }
  .ord-margen { color:#8b949e; font-size:12px; display:flex; justify-content:space-between;
      padding:8px 2px 2px; }
  .ord-margen b { color:#e6edf3; font-family:ui-monospace,Consolas,monospace; }
  /* Overlay invisible que hace clicable cada caja */
  [class*="st-key-ord_bx"] { position:relative; }
  [class*="st-key-ord_ov"] { position:absolute !important; top:0 !important; right:0 !important;
      bottom:0 !important; left:0 !important; width:100% !important; height:100% !important;
      margin:0 !important; padding:0 !important; z-index:3; }
  [class*="st-key-ord_ov"] * { width:100% !important; height:100% !important; min-height:0 !important;
      margin:0 !important; padding:0 !important; }
  [class*="st-key-ord_ov"] button { opacity:0; cursor:pointer; }
  /* overlays de selección por mitades (DESPUÉS de la genérica para que ganen) */
  [class*="st-key-ord_ovsell"] { right:auto !important; left:0 !important; width:50% !important; }
  [class*="st-key-ord_ovbuy"] { left:auto !important; right:0 !important; width:50% !important; }
  /* Botón "Colocar orden en" (2 líneas + flecha), estilo XM */
  .ord-place { display:flex; align-items:center; justify-content:space-between;
      border-radius:12px; padding:12px 18px; min-height:62px; }
  .ord-place .pl-lbl { font-size:13px; color:rgba(255,255,255,.9); }
  .ord-place .pl-px { font-size:22px; font-weight:800; color:#fff; line-height:1.1;
      white-space:nowrap; font-family:ui-monospace,Consolas,monospace; }
  .ord-place .pl-arrow { font-size:24px; color:#fff; font-weight:700; }
  .ord-place-buy  { background:linear-gradient(135deg,#3fb950,#2ea043); }
  .ord-place-sell { background:linear-gradient(135deg,#f85149,#da3633); }
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


def _ejecutar(real, visible, tipo, vol, sl, tp):
    res = ejecutar_orden_mercado(real, tipo, vol, sl, tp)
    if "error" in res:
        st.session_state.ord_result = ("error", res["error"])
    else:
        verbo = "Compra" if tipo == "BUY" else "Venta"
        st.session_state.ord_result = (
            "ok", f"{verbo} ejecutada: {res.get('volume')} lotes de {visible} @ {res.get('price')}")
    st.session_state.ord_confirm = None


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

        # TODO el ticket va dentro de UN fragmento que se refresca solo y cuyas
        # acciones usan scope="fragment" (nunca rerun de app desde aquí → evita el
        # parpadeo/pantalla en blanco).
        @st.fragment(run_every="2s")
        def _ticket():
            t = obtener_precio_actual(real)
            if "error" in t:
                st.caption("Sin precio en vivo. ¿Está abierto MetaTrader 5?")
                return
            bid, ask = t.get("bid", 0), t.get("ask", 0)
            side = st.session_state.get("ord_side", "BUY")

            oc = st.toggle("Orden con un clic", key="ord_oc", value=False,
                           help="Si está activo, la orden se envía sin confirmación.")

            # Caja VENTA|COMPRA unida + spread centrado (selección por mitades)
            pip = (point * 10) if dig in (3, 5) else (point or 1)
            spr_val = (ask - bid) / pip if pip else 0
            spr = f"{spr_val:,.1f}" if spr_val < 100 else f"{spr_val:,.0f}"
            sv = "sel" if side == "SELL" else ""
            sb = "sel" if side == "BUY" else ""
            with st.container(key="ord_bxrow"):
                st.html(
                    "<div class='ord-join'>"
                    f"<div class='ord-half ord-sell {sv}'><div class='ord-lbl'>VENTA</div>"
                    f"<div class='ord-px'>{bid:,.{dig}f}</div></div>"
                    f"<div class='ord-half ord-buy {sb}'><div class='ord-lbl'>COMPRA</div>"
                    f"<div class='ord-px'>{ask:,.{dig}f}</div></div>"
                    f"<div class='ord-spread'>{spr}</div>"
                    "</div>"
                )
                if st.button("v", key="ord_ovsell"):
                    st.session_state.ord_side = "SELL"
                    st.rerun(scope="fragment")
                if st.button("c", key="ord_ovbuy"):
                    st.session_state.ord_side = "BUY"
                    st.rerun(scope="fragment")

            # Cantidad / Lotes (como XM)
            contract = float(getattr(info, "trade_contract_size", 1) or 1)
            modo = st.segmented_control("Tipo", ["Cantidad", "Lotes"], default="Lotes",
                                        label_visibility="collapsed", key="ord_modo") or "Lotes"
            if modo == "Lotes":
                # Empieza en 0.01 y sube de 0.01 (o el mínimo/paso del símbolo)
                vol = st.number_input("Volumen (lotes)", min_value=vmin, value=vmin,
                                      step=vstep, format="%.2f", key="ord_vol")
            else:
                # Empieza en 1 y sube de 1 (unidades), se convierte a lotes
                cant = st.number_input("Cantidad (unidades)", min_value=1.0, value=1.0,
                                       step=1.0, format="%.0f", key="ord_cant")
                vol = (cant / contract) if contract else cant
                vol = max(vmin, round(vol / vstep) * vstep) if vstep else max(vmin, vol)
                st.caption(f"≈ {vol:.2f} lote(s)")

            # Margen del lado elegido
            price = bid if side == "SELL" else ask
            m = _margen(real, vol, price, "SELL" if side == "SELL" else "BUY")
            if m:
                st.html(f"<div class='ord-margen'><span>Margen requerido</span><b>${m:,.2f}</b></div>")

            # TP / SL opcional
            usar_tpsl = st.toggle("Take Profit / Stop Loss", key="ord_tpsl")
            sl = tp = 0.0
            if usar_tpsl:
                c_sl, c_tp = st.columns(2)
                sl = c_sl.number_input("Stop Loss", min_value=0.0, value=0.0,
                                       step=point or 0.0001, format=f"%.{dig}f", key="ord_sl")
                tp = c_tp.number_input("Take Profit", min_value=0.0, value=0.0,
                                       step=point or 0.0001, format=f"%.{dig}f", key="ord_tp")

            # Botón "Colocar orden en" (2 líneas + flecha, color/precio del lado)
            cls = "ord-place-sell" if side == "SELL" else "ord-place-buy"
            arrow = "↘" if side == "SELL" else "↗"
            with st.container(key="ord_bxplace"):
                st.html(
                    f"<div class='ord-place {cls}'>"
                    f"<div><div class='pl-lbl'>Colocar orden en</div>"
                    f"<div class='pl-px'>{price:,.{dig}f}</div></div>"
                    f"<div class='pl-arrow'>{arrow}</div></div>"
                )
                if st.button("ir", key="ord_ovplace"):
                    tipo = "SELL" if side == "SELL" else "BUY"
                    st.session_state.pop("ord_result", None)  # limpia resultado previo
                    if oc:
                        _ejecutar(real, visible, tipo, vol, sl, tp)
                    else:
                        st.session_state.ord_confirm = (tipo, vol, sl, tp, price)
                    st.rerun(scope="fragment")

            # Confirmación
            cf = st.session_state.get("ord_confirm")
            if cf:
                tipo, v, s, tpv, px = cf
                verbo2 = "COMPRA" if tipo == "BUY" else "VENTA"
                extra = (f" · SL {s:,.{dig}f}" if s else "") + (f" · TP {tpv:,.{dig}f}" if tpv else "")
                st.warning(f"Confirmar **{verbo2}** de **{v:.2f}** lotes de **{visible}** "
                           f"a ~{px:,.{dig}f}{extra}")
                cc1, cc2 = st.columns(2)
                if cc1.button("✓ Confirmar", key="ord_ok", type="primary", width="stretch"):
                    _ejecutar(real, visible, tipo, v, s, tpv)
                    st.rerun(scope="fragment")
                if cc2.button("Cancelar", key="ord_cancel", width="stretch"):
                    st.session_state.ord_confirm = None
                    st.rerun(scope="fragment")

            # Resultado (persiste entre refrescos de 2s; se limpia al colocar
            # una orden nueva). Antes se hacía pop() y el mensaje desaparecía al
            # instante con el auto-refresco -> parecía que "no compraba".
            r = st.session_state.get("ord_result")
            if r:
                if r[0] == "ok":
                    st.success(r[1], icon=":material/check_circle:")
                else:
                    st.error(f"No se pudo operar: {r[1]}", icon=":material/error:")

        _ticket()