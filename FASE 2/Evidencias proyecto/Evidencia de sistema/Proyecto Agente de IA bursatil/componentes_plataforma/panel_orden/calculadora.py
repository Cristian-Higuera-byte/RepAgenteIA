# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara calculadora .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""
panel_orden/calculadora.py
--------------------------
Calculadora de riesgo (Risk Manager) del ticket: sugiere cuántos lotes operar para no
arriesgar más de un % (o monto) del capital, y el Take Profit por relación
riesgo/beneficio (R/R). "Aplicar" vuelca volumen, Stop Loss y Take Profit al ticket
dejándolos en session_state['_calculadora_riesgo_aplicar'] (el ticket los consume antes de crear sus
widgets). No envía órdenes.
"""
import streamlit as st

from .cuenta import margen, capital_cuenta
from .interfaz import campo


# TITULO RENDERIZAR CALCULADORA

def renderizar_calculadora(info, real, lado, compra, precio, digitos, punto, vmin, vstep, oco_encendido):
    """Dibuja la tarjeta de la Calculadora de riesgo dentro del ticket.

    Recibe: `info` (symbol_info de MT5 o None), `real` (símbolo), `side` ("BUY"/"SELL"), `compra` (True si es
    compra), `price` (precio actual), `dig` (decimales), `point` (tamaño del punto), `vmin` y `vstep`
    (volumen mínimo y paso en lotes) y `oco_on` (si el modo OCO está activo; entonces "Aplicar" no toca
    SL/TP). Si el interruptor está apagado, solo dibuja el interruptor. Si está encendido, pide capital,
    riesgo, entrada, stop y R/R, calcula el tamaño recomendado y muestra el resultado con un botón
    "Aplicar al ticket" que deja los valores en `st.session_state._calculadora_riesgo_aplicar` y relanza el fragmento. No
    devuelve nada."""
    with st.container(key="orden_tarjeta_calculadora_riesgo"):
        with st.container(key="orden_interruptor_calculadora_riesgo"):
            usar_calculadora_riesgo = st.toggle(
                "Calculadora de riesgo", key="orden_calculadora_riesgo",
                help="Sugiere cuántos lotes operar para no arriesgar más de un % de tu "
                     "capital, y el Take Profit por relación riesgo/beneficio (R/R). "
                     "'Aplicar' rellena volumen, Stop Loss y Take Profit en el ticket.")
        if not usar_calculadora_riesgo:
            return

        # Datos del contrato del símbolo (con valores neutros si no hay info): tamaño y valor del tick,
        # tamaño del contrato y volumen máximo
        tsize = float(getattr(info, "trade_tick_size", 0) or 0) if info else 0.0
        tval = float(getattr(info, "trade_tick_value", 0) or 0) if info else 0.0
        kval = (tval / tsize) if tsize else 0.0        # valor de 1 unidad de precio por lote
        contract = float(getattr(info, "trade_contract_size", 1) or 1) if info else 1.0
        vmax = float(getattr(info, "volume_max", 100) or 100) if info else 100.0
        # Capital base: equity de la cuenta conectada (editable en el campo siguiente)
        equity, moneda = capital_cuenta()
        with campo("rmcap", "Capital", moneda):
            capital = st.number_input("Capital", min_value=0.0,
                                  value=float(round(equity or 0.0, 2)), step=100.0,
                                  format="%.2f", key="orden_calculadora_riesgo_capital", label_visibility="collapsed")
        # Selector de si el riesgo se expresa en % del capital o en dinero
        modo_r = st.segmented_control("Riesgo en", ["%", moneda], default="%",
                                      label_visibility="collapsed", key="orden_calculadora_riesgo_modo",
                                      width="stretch") or "%"
        if modo_r == "%":
            with campo("rmpct", "Riesgo por operación", "%"):
                rpct = st.number_input("Riesgo %", min_value=0.0, max_value=100.0, value=1.0,
                                       step=0.25, format="%.2f", key="orden_calculadora_riesgo_porcentaje",
                                       label_visibility="collapsed")
            riesgo = capital * rpct / 100.0
        else:
            with campo("rmusd", "Riesgo por operación", moneda):
                riesgo = st.number_input("Riesgo", min_value=0.0,
                                         value=float(round((capital or 0.0) * 0.01, 2)), step=50.0,
                                         format="%.2f", key="orden_calculadora_riesgo_usd",
                                         label_visibility="collapsed")
        # Entrada, Stop y R/R objetivo; las claves de entrada y stop incluyen símbolo y lado para reiniciarse al cambiar
        with campo("rment", "Entrada"):
            entrada = st.number_input("Entrada", min_value=0.0,
                                      value=float(round(precio, digitos)),
                                      step=(punto * 10) or 0.0001, format=f"%.{digitos}f",
                                      key=f"orden_calculadora_riesgo_entrada_{real}_{lado}", label_visibility="collapsed")
        with campo("rmstop", "Stop Loss"):
            stop_calculadora_riesgo = st.number_input("Stop", min_value=0.0, value=0.0,
                                      step=(punto * 10) or 0.0001, format=f"%.{digitos}f",
                                      key=f"orden_calculadora_riesgo_stop_{real}_{lado}", label_visibility="collapsed")
        with campo("rmrr", "R/R objetivo", ": 1"):
            riesgo_beneficio = st.number_input("R/R", min_value=0.1, value=2.0, step=0.5, format="%.1f",
                                 key="orden_calculadora_riesgo_riesgo_beneficio", label_visibility="collapsed")
        # Distancia entrada-stop y validación del lado del stop (bajo la entrada en compra, sobre en venta)
        distancia = abs(entrada - stop_calculadora_riesgo) if (entrada > 0 and stop_calculadora_riesgo > 0) else 0.0
        lado_correcto = (stop_calculadora_riesgo < entrada) if compra else (stop_calculadora_riesgo > entrada)
        # Mensaje de ayuda según el primer problema detectado; sin problemas queda vacío y se calcula
        mensaje = ""
        if kval <= 0:
            mensaje = "Este símbolo no entrega el valor por punto; no se puede calcular."
        elif entrada <= 0 or stop_calculadora_riesgo <= 0:
            mensaje = "Indica la Entrada y el Stop para calcular el tamaño."
        elif not lado_correcto:
            mensaje = ("En una compra el Stop va bajo la entrada." if compra
                   else "En una venta el Stop va sobre la entrada.")
        elif distancia <= 0 or riesgo <= 0:
            mensaje = "Indica un riesgo y una distancia de stop válidos."
        if mensaje:
            st.html(f"<div class='orden-pista' style='color:#8b949e'>{mensaje}</div>")
            return

        # Cálculo: pérdida por lote al stop, lotes que caben en el riesgo (redondeados al paso, entre mínimo y
        # máximo), pérdida real, Take Profit sugerido por R/R, ganancia potencial, unidades y margen
        perdida_lote = distancia * kval
        lotes_raw = riesgo / perdida_lote if perdida_lote else 0.0
        lotes = max(vmin, round(lotes_raw / vstep) * vstep) if vstep else max(vmin, lotes_raw)
        lotes = round(min(lotes, vmax), 2)
        perdida_real = lotes * distancia * kval
        take_profit_sug = round(entrada + (riesgo_beneficio * distancia) * (1 if compra else -1), digitos)
        gan = lotes * (riesgo_beneficio * distancia) * kval
        unidades = lotes * contract
        m_calculadora_riesgo = margen(real, lotes, entrada, lado)
        # Aviso si el riesgo elegido es menor que el lote mínimo (se opera con el mínimo y se arriesga más)
        riesgo_bajo = lotes_raw < vmin
        st.html(
            "<div class='orden-separador'></div>"
            f"<div class='orden-margen'><span>Riesgo máximo</span>"
            f"<b>{riesgo:,.2f} {moneda}</b></div>"
            f"<div class='orden-margen'><span>Tamaño recomendado</span>"
            f"<b>{lotes:,.2f} lote(s) · {unidades:,.0f} u.</b></div>"
            f"<div class='orden-margen'><span>Pérdida al stop</span>"
            f"<b style='color:#f85149'>-{perdida_real:,.2f} {moneda}</b></div>"
            f"<div class='orden-margen'><span>Take Profit ({riesgo_beneficio:.1f}:1)</span>"
            f"<b>{take_profit_sug:,.{digitos}f}</b></div>"
            f"<div class='orden-margen'><span>Ganancia potencial</span>"
            f"<b style='color:#3fb950'>+{gan:,.2f} {moneda}</b></div>"
            + (f"<div class='orden-margen'><span>Margen requerido</span>"
               f"<b>{m_calculadora_riesgo:,.2f} {moneda}</b></div>" if m_calculadora_riesgo else "")
            + (f"<div class='orden-pista' style='color:#d29922;margin-top:4px'>El riesgo "
               f"elegido es menor al lote mínimo ({vmin:g}); con {vmin:g} lote(s) la "
               f"pérdida sería {vmin * distancia * kval:,.2f} {moneda}.</div>" if riesgo_bajo else "")
        )
        # "Aplicar" deja los valores en la sesión; el ticket los consume antes de crear sus widgets.
        # Con OCO activo no se aplican SL/TP porque las patas del OCO van sin ellos.
        if st.button("Aplicar al ticket", key="orden_calculadora_riesgo_aplicar", width="stretch",
                     icon=":material/check:"):
            st.session_state._calculadora_riesgo_aplicar = {
                "vol": lotes,
                "sl": None if oco_encendido else round(stop_calculadora_riesgo, digitos),
                "tp": None if oco_encendido else take_profit_sug,
            }
            st.rerun(scope="fragment")


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara calculadora .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
