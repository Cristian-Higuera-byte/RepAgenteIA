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

La ficha se abre cuando `st.session_state.mercados_detalle` contiene el instrumento elegido (lo fija
`secciones.abrir_ficha`) y se cierra al descartar el diálogo. Los estilos `fic-*` están en `estilos.css`.
"""
from datetime import datetime, timezone

import streamlit as st
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from componentes_plataforma.iconografia import icono_activo
from componentes_plataforma.flujo_precios import atributos as _en_vivo, intervalo
from componentes_plataforma.mercados.broker import esta_abierto, leer_atributo, serie
from componentes_plataforma.mercados.constantes import GRIS, ROJO, VERDE
from componentes_plataforma.mercados.grafico import grafico
from componentes_plataforma.mercados.piezas import pildora
from herramientas.puente_mt5 import MT5_LOCK


# TITULO CERRAR FICHA

def cerrar_ficha():
    """Callback de cierre del diálogo: limpia `mercados_detalle` de la sesión para que la ficha no se reabra."""
    st.session_state.mercados_detalle = None


# TITULO IR A TRADING

def ir_a_trading(real: str, lado: str | None = None):
    """Lleva al usuario a la página de trading con el instrumento seleccionado.

    Recibe el símbolo real y, opcionalmente, el lado de la orden ("BUY" o "SELL") que se precarga en el
    ticket. Escribe `activo_seleccionado`, `navegacion_activo` y `orden_lado` en la sesión, cierra la ficha y relanza
    la aplicación."""
    st.session_state.activo_seleccionado = real
    st.session_state.navegacion_activo = "trading"
    if lado:
        st.session_state.orden_lado = lado
    st.session_state.mercados_detalle = None
    st.rerun()


# TITULO HTML RANGO

def html_rango(titulo, lo, hi, valor, digitos, nota="") -> str:
    """Devuelve el HTML de una barra de rango con título, nota opcional, mínimo, máximo y un punto en `val`.

    `dig` son los decimales a mostrar. Devuelve cadena vacía si el rango no es válido (faltan datos o hi <= lo)."""
    if lo is None or hi is None or hi <= lo:
        return ""
    # Posición del punto en porcentaje, limitada a la barra (0 a 100)
    posicion = max(0, min(100, (valor - lo) / (hi - lo) * 100))
    return (f"<div class='ficha-rango'><div class='t'><span>{titulo}</span><span>{nota}</span></div>"
            f"<div class='bar'><div class='dot' style='left:{posicion:.1f}%;'></div></div>"
            f"<div class='n'><span>{lo:,.{digitos}f}</span><span>{hi:,.{digitos}f}</span></div></div>")


# TITULO FILA FICHA

def fila_ficha(k, v) -> str:
    """Devuelve el HTML de una fila "clave / valor" de los recuadros de estadísticas y especificaciones."""
    return f"<div class='ficha-r'><span class='k'>{k}</span><span class='v'>{v}</span></div>"


# TITULO MOSTRAR FICHA

@st.dialog(" ", width="large", on_dismiss=cerrar_ficha)
def mostrar_ficha():
    """Dibuja el modal con la ficha completa del instrumento guardado en `mercados_detalle`.

    Lee de MT5 la información estática del símbolo y las velas D1 y H1; calcula apertura, cierre anterior,
    rango de 52 semanas y ATR; y pinta cabecera, precio en vivo con caja Vender/Comprar, gráfico,
    rendimiento por periodo, estadísticas clave, especificaciones del contrato y botones de acción (operar,
    agregar a la lista, agregar a favoritos). Si no hay instrumento o MT5 no lo reconoce, muestra un aviso
    y termina. No devuelve nada."""
    # Instrumento elegido (símbolo real, nombre a mostrar y categoría)
    detalle = st.session_state.get("mercados_detalle") or {}
    real, etiqueta, categoria = detalle.get("sym"), detalle.get("label", ""), detalle.get("cat", "")
    if not real:
        return
    with MT5_LOCK:
        mt5.symbol_select(real, True)
        info0 = mt5.symbol_info(real)    # campos estáticos (dígitos, contrato, swaps...)
    if info0 is None:
        st.warning("No se pudo cargar la información del instrumento.")
        return
    digitos = int(leer_atributo(info0, "digits") or 2)
    punto = float(leer_atributo(info0, "point") or 10 ** -digitos)

    # Velas diarias (260 ≈ un año de negociación) y horarias para el gráfico y las estadísticas
    tabla_datos = serie(real, mt5.TIMEFRAME_D1, 260)
    h1 = serie(real, mt5.TIMEFRAME_H1, 120)
    open_hoy = anterior_cerrar = semana_hi = semana_lo = atr_porcentaje = None
    if tabla_datos is not None and len(tabla_datos) > 1:
        # Apertura de hoy, cierre de ayer, extremos del periodo y ATR(14) como % del último cierre
        open_hoy = float(tabla_datos["open"].iloc[-1])
        anterior_cerrar = float(tabla_datos["close"].iloc[-2])
        semana_hi, semana_lo = float(tabla_datos["high"].max()), float(tabla_datos["low"].min())
        tr = (tabla_datos["high"] - tabla_datos["low"]).tail(14)
        atr_porcentaje = float(tr.mean()) / float(tabla_datos["close"].iloc[-1]) * 100 if len(tr) else None

    with st.container(key="ficha_raiz"):
        # --- Cabecera ---
        descripcion = getattr(info0, "description", "") or ""
        st.html(
            f"<div class='ficha-cabecera'><span class='mercados-icono'>{icono_activo(real, 46)}</span><div>"
            f"<div class='ficha-nombre'>{etiqueta}</div><div class='ficha-chips'>"
            f"<span class='ficha-chip'>{real}</span><span class='ficha-chip'>{categoria}</span>"
            + (f"<span class='ficha-chip'>{descripcion}</span>" if descripcion and descripcion.lower() != etiqueta.lower() else "")
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
            ch = (bid - anterior_cerrar) if anterior_cerrar else 0.0
            porcentaje = (ch / anterior_cerrar * 100) if anterior_cerrar else 0.0
            f = {"sym": real, "ch": ch, "pct": porcentaje}
            abierto = esta_abierto(t)
            hora = datetime.fromtimestamp(t, tz=timezone.utc).strftime("%d-%m %H:%M:%S") if t else "—"
            # Spread en pips para símbolos de 3 o 5 decimales (forex) y en puntos para el resto
            pip = punto * 10 if digitos in (3, 5) else punto
            spread = (ask - bid) / pip if pip else 0
            unidad = "pips" if digitos in (3, 5) else "pts"
            c1, c2 = st.columns([1.25, 1], vertical_alignment="center")
            with c1:
                st.html(
                    f"<div class='ficha-precio-fila'><span class='ficha-precio' {_en_vivo(real, 'px', d=digitos, flash=1)}>"
                    f"{bid:,.{digitos}f}</span>{pildora(f)}"
                    f"<span class='mercados-numero' style='color:{VERDE if ch >= 0 else ROJO};font-size:14px;"
                    f"font-weight:700;' {_en_vivo(real, 'ch', d=digitos)}>{ch:+,.{digitos}f}</span></div>"
                    f"<div class='ficha-precio-subtitulo'><span class='mercados-dot{'' if abierto else ' off'}'></span>&nbsp; "
                    f"{'Mercado abierto' if abierto else 'Mercado cerrado'} · último tick {hora} (hora del servidor)"
                    + (f" · cierre anterior {anterior_cerrar:,.{digitos}f}" if anterior_cerrar else "") + "</div>"
                )
            with c2:
                v, c = st.columns(2, gap="small")
                with v:
                    with st.container(key="ficsd_sell"):
                        st.html(f"<div class='ficha-lado ficha-sell'><div class='k'>VENDER</div>"
                                f"<div class='v' {_en_vivo(real, 'bid', d=digitos)}>{bid:,.{digitos}f}</div></div>")
                        if st.button("Vender", key="ficov_sell"):
                            ir_a_trading(real, "SELL")
                with c:
                    with st.container(key="ficsd_buy"):
                        st.html(f"<div class='ficha-lado ficha-buy'><div class='k'>COMPRAR</div>"
                                f"<div class='v' {_en_vivo(real, 'ask', d=digitos)}>{ask:,.{digitos}f}</div></div>")
                        if st.button("Comprar", key="ficov_buy"):
                            ir_a_trading(real, "BUY")
                st.html(f"<div style='text-align:center;color:{GRIS};font-size:11.5px;margin-top:-6px;'>"
                        f"Spread <b class='mercados-numero' style='color:#e6edf3;' "
                        f"{_en_vivo(real, 'spr', pip=pip)}>{spread:,.1f}</b> {unidad}</div>")
        _precio_vivo()

        # --- Gráfico interactivo ---
        grafico(real, tabla_datos, h1, serie(real, mt5.TIMEFRAME_M5, 288), digitos)

        # --- Rendimiento por periodo ---
        if tabla_datos is not None and len(tabla_datos) > 1:
            closes = tabla_datos["close"]
            ultimo = float(closes.iloc[-1])

            def _rendimiento(n):
                """Devuelve el rendimiento porcentual del último cierre frente al de hace `n` velas diarias,
                o None si no hay suficiente historial."""
                return (ultimo / float(closes.iloc[-n - 1]) - 1) * 100 if len(closes) > n else None
            # Periodos medidos en días de negociación (≈ 5 por semana, 22 por mes, 252 por año)
            rendimiento = {"1 día": _rendimiento(1), "1 semana": _rendimiento(5), "1 mes": _rendimiento(22),
                    "3 meses": _rendimiento(66), "6 meses": _rendimiento(132), "1 año": _rendimiento(252)}
            # Mayor rendimiento absoluto: escala las barras de cada celda
            tope = max([abs(x) for x in rendimiento.values() if x is not None] or [1]) or 1
            celdas = ""
            for k, v in rendimiento.items():
                if v is None:
                    celdas += f"<div><div class='k'>{k}</div><div class='v' style='color:{GRIS};'>—</div></div>"
                    continue
                c = VERDE if v >= 0 else ROJO
                # La barra crece desde el centro: a la derecha si sube y a la izquierda si baja
                ancho = abs(v) / tope * 50
                lado = f"left:50%;width:{ancho:.1f}%" if v >= 0 else f"right:50%;width:{ancho:.1f}%"
                celdas += (f"<div><div class='k'>{k}</div><div class='v' style='color:{c};'>{v:+.2f}%</div>"
                           f"<div class='b'><span style='{lado};background:{c};'></span></div></div>")
            st.html(f"<div class='ficha-rendimiento'>{celdas}</div>")

        # --- Estadísticas clave + especificaciones del contrato ---
        with MT5_LOCK:
            info = mt5.symbol_info(real) or info0
        bid = float(leer_atributo(info, "bid"))
        hi = float(leer_atributo(info, "bidhigh") or bid)
        lo = float(leer_atributo(info, "bidlow") or bid)
        col1, col2 = st.columns(2, gap="small")
        with col1:
            # Recuadro de estadísticas: solo se agregan las filas para las que hay dato
            estadisticas = ""
            if anterior_cerrar is not None:
                estadisticas += fila_ficha("Cierre anterior", f"{anterior_cerrar:,.{digitos}f}")
            if open_hoy is not None:
                estadisticas += fila_ficha("Apertura", f"{open_hoy:,.{digitos}f}")
            estadisticas += html_rango("Rango del día", min(lo, bid), max(hi, bid), bid, digitos)
            if semana_hi is not None:
                distancia = (bid / semana_hi - 1) * 100 if semana_hi else 0
                estadisticas += html_rango("Rango 52 semanas", semana_lo, semana_hi, bid, digitos, f"{distancia:+.1f}% del máximo")
            if atr_porcentaje is not None:
                estadisticas += fila_ficha("Volatilidad diaria (ATR 14)", f"{atr_porcentaje:.2f}%")
            volumen = leer_atributo(info, "volume") or leer_atributo(info, "volumereal")
            if volumen:
                estadisticas += fila_ficha("Volumen", f"{volumen:,.0f}")
            st.html(f"<div class='ficha-caja'><h4>Estadísticas clave</h4>{estadisticas}</div>")
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
            stop_loss, ss = leer_atributo(info0, "swap_long"), leer_atributo(info0, "swap_short")
            if stop_loss or ss:
                specs += fila_ficha("Swap compra / venta", f"{stop_loss:+.2f} / {ss:+.2f}")
            st.html(f"<div class='ficha-caja'><h4>Especificaciones del contrato</h4>{specs}</div>")

        # --- Acciones ---
        st.html("<div style='height:4px;'></div>")
        a1, a2, a3 = st.columns([1.4, 1, 1])
        with a1:
            with st.container(key="ficha_operar"):
                if st.button("Operar " + etiqueta, icon=":material/candlestick_chart:", width="stretch"):
                    ir_a_trading(real)
        with a2:
            if st.button("Agregar a mi lista", icon=":material/playlist_add:", width="stretch"):
                # Importación diferida para evitar dependencias circulares con el buscador
                from componentes_plataforma.buscador import _agregar_a_watchlist
                uid = (st.session_state.get("usuario_informacion") or {}).get("id")
                if _agregar_a_watchlist(uid, {"name": real, "visible": real, "desc": etiqueta, "cat": categoria}):
                    st.toast(f"{etiqueta} agregado a tu lista.")
        with a3:
            if st.button("Agregar a favoritos", icon=":material/star:", width="stretch"):
                # Importación diferida para evitar dependencias circulares con la barra de favoritos
                from componentes_plataforma.favoritos import agregar_favorito
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
