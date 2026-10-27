# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara ficha .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ficha del instrumento (modal): precio en vivo, Vender/Comprar, gráfico, rendimiento, estadísticas y contrato.

La ficha se abre cuando `st.session_state.mkt_detalle` contiene el instrumento elegido (lo fija
`secciones.abrir_ficha`) y se cierra al descartar el diálogo. Los estilos `fic-*` están en `estilos.css`.
"""
from datetime import datetime, timezone

import streamlit as st
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from components.iconografia import icono_activo
from components.flujo_precios import atributos as _en_vivo, intervalo
from components.mercados.broker import esta_abierto, leer_atributo, serie
from components.mercados.constantes import GRIS, ROJO, VERDE
from components.mercados.grafico import grafico
from components.mercados.piezas import pildora
from tools.puente_mt5 import MT5_LOCK


def cerrar_ficha():
    """Callback de cierre del diálogo: limpia `mkt_detalle` de la sesión para que la ficha no se reabra."""
    st.session_state.mkt_detalle = None


def ir_a_trading(real: str, lado: str | None = None):
    """Lleva al usuario a la página de trading con el instrumento seleccionado.

    Recibe el símbolo real y, opcionalmente, el lado de la orden ("BUY" o "SELL") que se precarga en el
    ticket. Escribe `activo_seleccionado`, `nav_activo` y `ord_side` en la sesión, cierra la ficha y relanza
    la aplicación."""
    st.session_state.activo_seleccionado = real
    st.session_state.nav_activo = "trading"
    if lado:
        st.session_state.ord_side = lado
    st.session_state.mkt_detalle = None
    st.rerun()


def html_rango(titulo, lo, hi, val, dig, nota="") -> str:
    """Devuelve el HTML de una barra de rango con título, nota opcional, mínimo, máximo y un punto en `val`.

    `dig` son los decimales a mostrar. Devuelve cadena vacía si el rango no es válido (faltan datos o hi <= lo)."""
    if lo is None or hi is None or hi <= lo:
        return ""
    # Posición del punto en porcentaje, limitada a la barra (0 a 100)
    pos = max(0, min(100, (val - lo) / (hi - lo) * 100))
    return (f"<div class='fic-rng'><div class='t'><span>{titulo}</span><span>{nota}</span></div>"
            f"<div class='bar'><div class='dot' style='left:{pos:.1f}%;'></div></div>"
            f"<div class='n'><span>{lo:,.{dig}f}</span><span>{hi:,.{dig}f}</span></div></div>")


def fila_ficha(k, v) -> str:
    """Devuelve el HTML de una fila "clave / valor" de los recuadros de estadísticas y especificaciones."""
    return f"<div class='fic-r'><span class='k'>{k}</span><span class='v'>{v}</span></div>"


@st.dialog(" ", width="large", on_dismiss=cerrar_ficha)
def mostrar_ficha():
    """Dibuja el modal con la ficha completa del instrumento guardado en `mkt_detalle`.

    Lee de MT5 la información estática del símbolo y las velas D1 y H1; calcula apertura, cierre anterior,
    rango de 52 semanas y ATR; y pinta cabecera, precio en vivo con caja Vender/Comprar, gráfico,
    rendimiento por periodo, estadísticas clave, especificaciones del contrato y botones de acción (operar,
    agregar a la lista, agregar a favoritos). Si no hay instrumento o MT5 no lo reconoce, muestra un aviso
    y termina. No devuelve nada."""
    # Instrumento elegido (símbolo real, nombre a mostrar y categoría)
    det = st.session_state.get("mkt_detalle") or {}
    real, label, cat = det.get("sym"), det.get("label", ""), det.get("cat", "")
    if not real:
        return
    with MT5_LOCK:
        mt5.symbol_select(real, True)
        info0 = mt5.symbol_info(real)    # campos estáticos (dígitos, contrato, swaps...)
    if info0 is None:
        st.warning("No se pudo cargar la información del instrumento.")
        return
    dig = int(leer_atributo(info0, "digits") or 2)
    punto = float(leer_atributo(info0, "point") or 10 ** -dig)

    # Velas diarias (260 ≈ un año de negociación) y horarias para el gráfico y las estadísticas
    df = serie(real, mt5.TIMEFRAME_D1, 260)
    h1 = serie(real, mt5.TIMEFRAME_H1, 120)
    open_hoy = prev_close = wk_hi = wk_lo = atr_pct = None
    if df is not None and len(df) > 1:
        # Apertura de hoy, cierre de ayer, extremos del periodo y ATR(14) como % del último cierre
        open_hoy = float(df["open"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        wk_hi, wk_lo = float(df["high"].max()), float(df["low"].min())
        tr = (df["high"] - df["low"]).tail(14)
        atr_pct = float(tr.mean()) / float(df["close"].iloc[-1]) * 100 if len(tr) else None

    with st.container(key="fic_root"):
        # --- Cabecera ---
        desc = getattr(info0, "description", "") or ""
        st.html(
            f"<div class='fic-head'><span class='mkt-ic'>{icono_activo(real, 46)}</span><div>"
            f"<div class='fic-nm'>{label}</div><div class='fic-chips'>"
            f"<span class='fic-chip'>{real}</span><span class='fic-chip'>{cat}</span>"
            + (f"<span class='fic-chip'>{desc}</span>" if desc and desc.lower() != label.lower() else "")
            + "</div></div></div>"
        )

        # --- EN VIVO: precio + caja Vender / Comprar ---
        @st.fragment(run_every=intervalo("2s"))
        def _precio_vivo():
            """Fragmento que se refresca solo: lee el tick de MT5 y repinta precio, cambio, estado del mercado,
            caja Vender/Comprar y spread. Los botones llevan a trading con el lado elegido."""
            # Tick e información actuales del símbolo
            with MT5_LOCK:
                tick = mt5.symbol_info_tick(real)
                info = mt5.symbol_info(real)
            bid = float(getattr(tick, "bid", 0) or leer_atributo(info, "bid") or 0)
            ask = float(getattr(tick, "ask", 0) or leer_atributo(info, "ask") or 0)
            t = int(getattr(tick, "time", 0) or 0)
            # Cambio y porcentaje contra el cierre anterior
            ch = (bid - prev_close) if prev_close else 0.0
            pct = (ch / prev_close * 100) if prev_close else 0.0
            f = {"sym": real, "ch": ch, "pct": pct}
            abierto = esta_abierto(t)
            hora = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%d-%m %H:%M:%S") if t else "—"
            # Spread en pips para símbolos de 3 o 5 decimales (forex) y en puntos para el resto
            pip = punto * 10 if dig in (3, 5) else punto
            spread = (ask - bid) / pip if pip else 0
            unidad = "pips" if dig in (3, 5) else "pts"
            c1, c2 = st.columns([1.25, 1], vertical_alignment="center")
            with c1:
                st.html(
                    f"<div class='fic-pxrow'><span class='fic-px' {_en_vivo(real, 'px', d=dig, flash=1)}>"
                    f"{bid:,.{dig}f}</span>{pildora(f)}"
                    f"<span class='mkt-num' style='color:{VERDE if ch >= 0 else ROJO};font-size:14px;"
                    f"font-weight:700;' {_en_vivo(real, 'ch', d=dig)}>{ch:+,.{dig}f}</span></div>"
                    f"<div class='fic-pxsub'><span class='mkt-dot{'' if abierto else ' off'}'></span>&nbsp; "
                    f"{'Mercado abierto' if abierto else 'Mercado cerrado'} · último tick {hora} (hora del servidor)"
                    + (f" · cierre anterior {prev_close:,.{dig}f}" if prev_close else "") + "</div>"
                )
            with c2:
                v, c = st.columns(2, gap="small")
                with v:
                    with st.container(key="ficsd_sell"):
                        st.html(f"<div class='fic-side fic-sell'><div class='k'>VENDER</div>"
                                f"<div class='v' {_en_vivo(real, 'bid', d=dig)}>{bid:,.{dig}f}</div></div>")
                        if st.button("Vender", key="ficov_sell"):
                            ir_a_trading(real, "SELL")
                with c:
                    with st.container(key="ficsd_buy"):
                        st.html(f"<div class='fic-side fic-buy'><div class='k'>COMPRAR</div>"
                                f"<div class='v' {_en_vivo(real, 'ask', d=dig)}>{ask:,.{dig}f}</div></div>")
                        if st.button("Comprar", key="ficov_buy"):
                            ir_a_trading(real, "BUY")
                st.html(f"<div style='text-align:center;color:{GRIS};font-size:11.5px;margin-top:-6px;'>"
                        f"Spread <b class='mkt-num' style='color:#e6edf3;' "
                        f"{_en_vivo(real, 'spr', pip=pip)}>{spread:,.1f}</b> {unidad}</div>")
        _precio_vivo()

        # --- Gráfico interactivo ---
        grafico(real, df, h1, serie(real, mt5.TIMEFRAME_M5, 288), dig)

        # --- Rendimiento por periodo ---
        if df is not None and len(df) > 1:
            closes = df["close"]
            last = float(closes.iloc[-1])

            def _rendimiento(n):
                """Devuelve el rendimiento porcentual del último cierre frente al de hace `n` velas diarias,
                o None si no hay suficiente historial."""
                return (last / float(closes.iloc[-n - 1]) - 1) * 100 if len(closes) > n else None
            # Periodos medidos en días de negociación (≈ 5 por semana, 22 por mes, 252 por año)
            perf = {"1 día": _rendimiento(1), "1 semana": _rendimiento(5), "1 mes": _rendimiento(22),
                    "3 meses": _rendimiento(66), "6 meses": _rendimiento(132), "1 año": _rendimiento(252)}
            # Mayor rendimiento absoluto: escala las barras de cada celda
            tope = max([abs(x) for x in perf.values() if x is not None] or [1]) or 1
            celdas = ""
            for k, v in perf.items():
                if v is None:
                    celdas += f"<div><div class='k'>{k}</div><div class='v' style='color:{GRIS};'>—</div></div>"
                    continue
                c = VERDE if v >= 0 else ROJO
                # La barra crece desde el centro: a la derecha si sube y a la izquierda si baja
                ancho = abs(v) / tope * 50
                lado = f"left:50%;width:{ancho:.1f}%" if v >= 0 else f"right:50%;width:{ancho:.1f}%"
                celdas += (f"<div><div class='k'>{k}</div><div class='v' style='color:{c};'>{v:+.2f}%</div>"
                           f"<div class='b'><span style='{lado};background:{c};'></span></div></div>")
            st.html(f"<div class='fic-perf'>{celdas}</div>")

        # --- Estadísticas clave + especificaciones del contrato ---
        with MT5_LOCK:
            info = mt5.symbol_info(real) or info0
        bid = float(leer_atributo(info, "bid"))
        hi = float(leer_atributo(info, "bidhigh") or bid)
        lo = float(leer_atributo(info, "bidlow") or bid)
        col1, col2 = st.columns(2, gap="small")
        with col1:
            # Recuadro de estadísticas: solo se agregan las filas para las que hay dato
            stats = ""
            if prev_close is not None:
                stats += fila_ficha("Cierre anterior", f"{prev_close:,.{dig}f}")
            if open_hoy is not None:
                stats += fila_ficha("Apertura", f"{open_hoy:,.{dig}f}")
            stats += html_rango("Rango del día", min(lo, bid), max(hi, bid), bid, dig)
            if wk_hi is not None:
                dist = (bid / wk_hi - 1) * 100 if wk_hi else 0
                stats += html_rango("Rango 52 semanas", wk_lo, wk_hi, bid, dig, f"{dist:+.1f}% del máximo")
            if atr_pct is not None:
                stats += fila_ficha("Volatilidad diaria (ATR 14)", f"{atr_pct:.2f}%")
            vol = leer_atributo(info, "volume") or leer_atributo(info, "volumereal")
            if vol:
                stats += fila_ficha("Volumen", f"{vol:,.0f}")
            st.html(f"<div class='fic-box'><h4>Estadísticas clave</h4>{stats}</div>")
        with col2:
            # Recuadro de especificaciones del contrato según la información estática del símbolo
            specs = ""
            contrato = leer_atributo(info0, "trade_contract_size")
            if contrato:
                specs += fila_ficha("Tamaño del contrato", f"{contrato:,.0f}")
            vmin, vstep, vmax = leer_atributo(info0, "volume_min"), leer_atributo(info0, "volume_step"), leer_atributo(info0, "volume_max")
            if vmin:
                specs += fila_ficha("Volumen mín. / paso", f"{vmin:g} / {vstep:g} lotes")
            if vmax:
                specs += fila_ficha("Volumen máximo", f"{vmax:,.0f} lotes")
            specs += fila_ficha("Tamaño del tick", f"{leer_atributo(info0, 'trade_tick_size') or punto:g}")
            base = getattr(info0, "currency_base", "") or ""
            prof = getattr(info0, "currency_profit", "") or ""
            marg = getattr(info0, "currency_margin", "") or ""
            if prof:
                specs += fila_ficha("Divisa de ganancia", prof)
            if marg or base:
                specs += fila_ficha("Divisa de margen", marg or base)
            sl, ss = leer_atributo(info0, "swap_long"), leer_atributo(info0, "swap_short")
            if sl or ss:
                specs += fila_ficha("Swap compra / venta", f"{sl:+.2f} / {ss:+.2f}")
            st.html(f"<div class='fic-box'><h4>Especificaciones del contrato</h4>{specs}</div>")

        # --- Acciones ---
        st.html("<div style='height:4px;'></div>")
        a1, a2, a3 = st.columns([1.4, 1, 1])
        with a1:
            with st.container(key="fic_operar"):
                if st.button("Operar " + label, icon=":material/candlestick_chart:", width="stretch"):
                    ir_a_trading(real)
        with a2:
            if st.button("Agregar a mi lista", icon=":material/playlist_add:", width="stretch"):
                # Importación diferida para evitar dependencias circulares con el buscador
                from components.buscador import _agregar_a_watchlist
                uid = (st.session_state.get("usuario_info") or {}).get("id")
                _agregar_a_watchlist(uid, {"name": real, "visible": real, "desc": label, "cat": cat})
                st.toast(f"{label} agregado a tu lista.")
        with a3:
            if st.button("Agregar a favoritos", icon=":material/star:", width="stretch"):
                # Importación diferida para evitar dependencias circulares con la barra de favoritos
                from components.favoritos import agregar_favorito
                agregar_favorito(real)


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara ficha .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
