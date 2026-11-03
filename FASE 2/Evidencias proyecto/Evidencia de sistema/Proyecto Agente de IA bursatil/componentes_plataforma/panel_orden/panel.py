# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara panel .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
panel_orden/panel.py
--------------------
Ticket de orden (comprar / vender) a la derecha del gráfico, con el diseño de XM:
- "One-Click Trading" con el interruptor a la derecha (si está apagado, pide confirmación;
  la primera vez que se activa exige aceptar los términos: componentes_plataforma/operacion_un_clic/).
- SELL | BUY unidos (el lado elegido se pinta en rojo/verde) + spread al centro.
- Cantidad / Lotes a todo el ancho y el volumen en una tarjeta con la etiqueta
  DENTRO y el número grande (como XM).
- Margen requerido + barra con el % del margen libre que usaría la orden.
- Tarjeta "Pending order" (Buy/Sell Limit o Stop según el precio) con
  "Good till cancelled (GTC)", y tarjeta de Take Profit / Stop Loss.
Términos de trading en INGLÉS (decisión del equipo, 06-10-2026); el resto en español.
- Botón grande "Colocar orden en {precio}" del color del lado elegido.

Este módulo orquesta el render; la lógica vive en los submódulos del paquete:
  cuenta.py (lecturas MT5) · ejecucion.py (envío) · confirmacion.py (confirmación) ·
  calculadora.py (Risk Manager) · avisos.py (aviso) · interfaz.py (CSS + campo).
Las órdenes se envían a la cuenta CONECTADA en MetaTrader 5 (demo en desarrollo). El
usuario confirma cada operación (salvo One-Click Trading).
"""
import streamlit as st
import streamlit.components.v1 as components

from componentes_plataforma.flujo_precios import atributos as _en_vivo, intervalo as _intervalo
from componentes_plataforma.operacion_un_clic import al_cambiar as _oc_cambiar, pedir_terminos_si_corresponde
from herramientas.puente_mt5 import NOMBRE_PROVEEDOR, inicializar_mt5, obtener_precio_actual, resolver_simbolo

from .cuenta import info_simbolo, margen, margen_libre
from .ejecucion import ejecutar, ejecutar_oco
from .confirmacion import renderizar_confirmacion
from .calculadora import renderizar_calculadora
from .avisos import aviso_js
from .interfaz import cargar_css, campo


# TITULO RENDERIZAR PANEL ORDEN

def renderizar_panel_orden(main=None):
    """Dibuja el ticket de órdenes completo (comprar / vender) del activo seleccionado.

    El parámetro `main` se acepta por compatibilidad con las demás páginas y no se usa. Lee el activo de
    `st.session_state.activo_seleccionado`, consulta a MT5 la información del símbolo (decimales, volumen
    mínimo y paso, punto), inyecta el CSS y pinta el encabezado y un único fragmento `_ticket` que se
    refresca solo. Todas las acciones del ticket relanzan solo el fragmento para evitar parpadeos. Las
    órdenes se envían a la cuenta conectada en MetaTrader 5. No devuelve nada."""
    # Conexión a MT5 y datos del símbolo: nombre real en este terminal, nombre visible y parámetros de volumen
    inicializar_mt5()
    activo =st.session_state.get("activo_seleccionado", "EURUSD...")
    real = resolver_simbolo(activo)
    visible = activo.replace("...", "").strip()
    info = info_simbolo(real)
    digitos = int(getattr(info, "digits", 5) or 5) if info else 5
    vmin = float(getattr(info, "volume_min", 0.01) or 0.01) if info else 0.01
    vstep = float(getattr(info, "volume_step", 0.01) or 0.01) if info else 0.01
    punto = getattr(info, "point", 0.0) if info else 0.0

    # Lado por defecto del ticket la primera vez
    if "orden_lado" not in st.session_state:
        st.session_state.orden_lado = "BUY"

    # CSS del ticket (estatico/ticket.css) y contenedor raíz con key orden_panel al que se acota
    cargar_css()
    with st.container(key="orden_panel"):
        st.html(f"<div class='orden-h'>Operar · {visible}</div>"
                f"<div class='orden-subtitulo'>Cuenta conectada en {NOMBRE_PROVEEDOR} (demo)</div>")

        # TODO el ticket va dentro de UN fragmento cuyas acciones usan
        # scope="fragment" (nunca rerun de app desde aquí → sin parpadeo).
        @st.fragment(run_every=_intervalo("2s"))   # con feed: precios/spread por flujo_precios/
        def _ticket():
            """Fragmento con auto-refresco que dibuja todo el ticket: One-Click, SELL/BUY con spread, volumen,
            orden pendiente y OCO, margen requerido, Take Profit / Stop Loss, calculadora de riesgo, botón
            de colocar orden, tarjeta de confirmación y aviso del resultado. Si no hay precio en vivo,
            muestra un aviso y termina."""
            # Precio en vivo del símbolo; si MT5 no responde se avisa y no se dibuja el ticket
            t = obtener_precio_actual(real)
            if "error" in t:
                st.caption("Sin precio en vivo. ¿Está abierto MetaTrader 5?")
                return
            # Bid (precio de venta), ask (precio de compra) y lado elegido en el ticket
            bid, ask = t.get("bid", 0), t.get("ask", 0)
            side = st.session_state.get("orden_lado", "BUY")
            compra = side == "BUY"

            # La Calculadora de riesgo pide "Aplicar" dejando los valores aquí; se vuelcan
            # a los widgets del ticket ANTES de crearlos (si no, Streamlit no deja cambiarlos).
            pendiente_calculadora_riesgo = st.session_state.pop("_calculadora_riesgo_aplicar", None)
            if pendiente_calculadora_riesgo:
                st.session_state["orden_modo"] = "Lotes"
                st.session_state["orden_volumen"] = pendiente_calculadora_riesgo["vol"]
                if pendiente_calculadora_riesgo.get("sl") or pendiente_calculadora_riesgo.get("tp"):
                    st.session_state["orden_take_profit_stop_loss"] = True
                    if pendiente_calculadora_riesgo.get("sl"):
                        st.session_state["orden_stop_loss"] = pendiente_calculadora_riesgo["sl"]
                    if pendiente_calculadora_riesgo.get("tp"):
                        st.session_state["orden_take_profit"] = pendiente_calculadora_riesgo["tp"]

            # --- One-Click Trading (interruptor a la derecha) ---
            with st.container(key="orden_interruptor_un_clic"):
                un_clic = st.toggle("One-Click Trading", key="orden_un_clic", on_change=_oc_cambiar,
                               help="Activo: las órdenes del ticket y del gráfico se envían sin "
                                    "confirmación. La primera vez pide aceptar los términos.")
            pedir_terminos_si_corresponde()

            # --- VENTA | COMPRA unidos + spread (selección por mitades) ---
            # Spread en pips (forex de 3 o 5 decimales) o en puntos; 1 decimal si es pequeño y entero si es grande
            pip = (punto * 10) if digitos in (3, 5) else (punto or 1)
            spr_valor = (ask - bid) / pip if pip else 0
            spr = f"{spr_valor:,.1f}" if spr_valor < 100 else f"{spr_valor:,.0f}"
            # Los botones Vender y Comprar van superpuestos e invisibles sobre cada mitad (CSS de orden_zona_fila)
            with st.container(key="orden_zona_fila"):
                st.html(
                    "<div class='orden-unir'>"
                    f"<div class='orden-mitad orden-sell {'' if compra else 'sel'}'><div class='orden-etiqueta'>SELL</div>"
                    f"<div class='orden-precio' {_en_vivo(real, 'bid', d=digitos)}>{bid:,.{digitos}f}</div></div>"
                    f"<div class='orden-mitad orden-buy {'sel' if compra else ''}'><div class='orden-etiqueta'>BUY</div>"
                    f"<div class='orden-precio' {_en_vivo(real, 'ask', d=digitos)}>{ask:,.{digitos}f}</div></div>"
                    f"<div class='orden-spread' {_en_vivo(real, 'spr', pip=pip)}>{spr}</div>"
                    "</div>"
                )
                if st.button("Vender", key="orden_superposicion_sell"):
                    st.session_state.orden_lado = "SELL"
                    st.rerun(scope="fragment")
                if st.button("Comprar", key="orden_superposicion_buy"):
                    st.session_state.orden_lado = "BUY"
                    st.rerun(scope="fragment")

            # --- Cantidad | Lotes + volumen (tarjeta con número grande) ---
            # En modo Cantidad se convierte a lotes dividiendo por el tamaño del contrato
            contract = float(getattr(info, "trade_contract_size", 1) or 1)
            modo = st.segmented_control("Tipo de volumen", ["Cantidad", "Lotes"], default="Lotes",
                                        label_visibility="collapsed", key="orden_modo",
                                        width="stretch") or "Lotes"
            if modo == "Lotes":
                with campo("qty", "Volumen", "lote(s)"):
                    volumen = st.number_input("Volumen (lotes)", min_value=vmin, value=vmin,
                                          step=vstep, format="%.2f", key="orden_volumen",
                                          label_visibility="collapsed")
            else:
                with campo("qty", "Cantidad", "unidades"):
                    cantidad = st.number_input("Cantidad (unidades)", min_value=1.0, value=1.0,
                                           step=1.0, format="%.0f", key="orden_cantidad",
                                           label_visibility="collapsed")
                # Se redondea al paso de volumen del símbolo y se respeta el mínimo
                volumen = (cantidad / contract) if contract else cantidad
                volumen = max(vmin, round(volumen / vstep) * vstep) if vstep else max(vmin, volumen)

            # Hueco del margen ANTES de la orden pendiente (orden visual de XM);
            # se llena más abajo porque depende del precio pendiente.
            ranura_margen = st.container()

            # --- Pending order: Buy/Sell Limit o Stop según el precio pedido ---
            # `ref` es el precio de referencia del lado (ask en compra, bid en venta); `pendiente` y `gtc`
            # guardan el precio y la vigencia de la orden pendiente; las variables oco_* describen la 2.ª pata
            referencia = ask if compra else bid
            pendiente, gtc = None, True
            oco_encendido,oco_lado_b, oco_precio_b, oco_tipo_b = False, None, None, ""
            with st.container(key="orden_tarjeta_pendiente"):
                with st.container(key="orden_interruptor_pendiente"):
                    usar_pendiente = st.toggle(
                        "Pending order", key="orden_pendiente",
                        help=("Se ejecuta cuando el mercado llega al precio indicado: "
                              + ("Buy Limit bajo el precio actual, Buy Stop sobre él." if compra
                                 else "Sell Limit sobre el precio actual, Sell Stop bajo él.")))
                if usar_pendiente:
                    with campo("pxp", "Precio"):
                        pendiente = st.number_input(
                            "Precio de la orden pendiente", min_value=0.0, value=round(float(referencia), digitos),
                            step=(punto * 10) or 0.0001, format=f"%.{digitos}f",
                            key=f"orden_precio_pendiente_{real}_{side}", label_visibility="collapsed")
                    # Tipo según el precio: compra bajo el actual es Limit, sobre el actual es Stop (al revés en venta)
                    if compra:
                        tipo_pendiente = "Buy Limit" if pendiente < referencia else "Buy Stop"
                    else:
                        tipo_pendiente = "Sell Limit" if pendiente > referencia else "Sell Stop"
                    st.html(f"<div class='orden-pista'>Precio actual ({'Ask' if compra else 'Bid'}):"
                            f"<b {_en_vivo(real, 'side', d=digitos, side=side)}>{referencia:,.{digitos}f}</b></div>"
                            f"<div class='orden-pista'>Tipo de orden:<b>{tipo_pendiente}</b></div>"
                            "<div class='orden-separador'></div>")
                    with st.container(key="orden_interruptor_gtc"):
                        gtc = st.toggle("Good till cancelled (GTC)", value=True, key="orden_gtc",
                                        help="Apagado: DAY, la orden vence al final del día.")

                    # --- OCO: segunda orden vinculada (One-Cancels-the-Other) ---
                    st.html("<div class='orden-separador'></div>")
                    with st.container(key="orden_interruptor_oco"):
                        oco_encendido = st.toggle(
                            "OCO (One-Cancels-the-Other)", key="orden_oco_interruptor",
                            help="Coloca DOS órdenes pendientes vinculadas: cuando una se ejecuta, "
                                 "la otra se cancela sola. Típico para un breakout (Buy Stop arriba + "
                                 "Sell Stop abajo). Necesita el servidor de datos en marcha.")
                    if oco_encendido:
                        # Segunda pata: lado (por defecto el opuesto), precio y tipo calculado igual que la primera
                        st.html("<div class='orden-subtitulo' style='margin-top:2px'>Segunda orden del par</div>")
                        lb = st.segmented_control(
                            "Lado de la segunda orden", ["Compra", "Venta"],
                            default=("Venta" if compra else "Compra"), label_visibility="collapsed",
                            key="orden_oco_lado", width="stretch") or ("Venta" if compra else "Compra")
                        oco_lado_b = "BUY" if lb == "Compra" else "SELL"
                        refb = ask if oco_lado_b == "BUY" else bid
                        with campo("pxb", "Segundo precio"):
                            oco_precio_b = st.number_input(
                                "Precio de la segunda orden", min_value=0.0,
                                value=round(float(refb), digitos), step=(punto * 10) or 0.0001,
                                format=f"%.{digitos}f", key=f"orden_precio_segundo_{real}_{side}",
                                label_visibility="collapsed")
                        if oco_lado_b == "BUY":
                            oco_tipo_b = "Buy Limit" if oco_precio_b < refb else "Buy Stop"
                        else:
                            oco_tipo_b = "Sell Limit" if oco_precio_b > refb else "Sell Stop"
                        st.html(
                            f"<div class='orden-pista'>Orden A (esta):"
                            f"<b>{tipo_pendiente} · {'BUY' if compra else 'SELL'} @ {pendiente:,.{digitos}f}</b></div>"
                            f"<div class='orden-pista'>Orden B:"
                            f"<b>{oco_tipo_b} · {oco_lado_b} @ {oco_precio_b:,.{digitos}f}</b></div>"
                            "<div class='orden-pista' style='margin-top:4px;color:#8b949e'>El Stop Loss / "
                            "Take Profit se define sobre la posición cuando una pata se ejecute.</div>")

            # --- Margen requerido + % del margen libre (como XM) ---
            # Se calcula con el precio pendiente si existe; `sin_margen` bloquea la orden si excede el margen libre
            precio = pendiente if pendiente else referencia
            m = margen(real, volumen, precio, side)
            libre = margen_libre()
            sin_margen = bool(m and libre is not None and m > libre)
            if m:
                # Porcentaje del margen libre que usaría la orden y color de la barra: rojo si no alcanza,
                # ámbar si pasa del 90 %, azul en el resto
                porcentaje = (m / libre * 100) if libre and libre > 0 else 100.0
                color ="#f85149" if sin_margen else ("#d29922" if porcentaje >= 90 else "#2f81f7")
                ranura_margen.html(
                    f"<div class='orden-margen'><span>Margen requerido</span><b>${m:,.2f}</b></div>"
                    f"<div class='orden-barra-margen-fila'><div class='orden-barra-margen'>"
                    f"<div style='width:{min(porcentaje, 100):.1f}%; background:{color};'></div></div>"
                    f"<span class='orden-barra-margen-porcentaje' style='color:{color if sin_margen else '#e6edf3'};'>"
                    f"{porcentaje:,.2f}%</span></div>"
                    + ("<div class='orden-sin-margen'>No tiene margen suficiente para colocar "
                       "esta orden.</div><style>.st-key-orden_caja_qty [data-testid='stNumberInputContainer'] "
                       "{ border-color:#f85149 !important; box-shadow:0 0 0 1px #f85149 !important; }"
                       "</style>" if sin_margen else "")
                )

            # --- Take Profit / Stop Loss (no aplica en OCO: patas en lados opuestos) ---
            stop_loss = take_profit = 0.0
            if not oco_encendido:
                with st.container(key="orden_tarjeta_take_profit_stop_loss"):
                    with st.container(key="orden_interruptor_take_profit_stop_loss"):
                        usar_take_profit_stop_loss = st.toggle("Take Profit / Stop Loss", key="orden_take_profit_stop_loss")
                    if usar_take_profit_stop_loss:
                        with campo("sl", "Stop Loss"):
                            stop_loss = st.number_input("Stop Loss", min_value=0.0, value=0.0,
                                                 step=punto or 0.0001, format=f"%.{digitos}f",
                                                 key="orden_stop_loss", label_visibility="collapsed")
                        with campo("tp", "Take Profit"):
                            take_profit = st.number_input("Take Profit", min_value=0.0, value=0.0,
                                                 step=punto or 0.0001, format=f"%.{digitos}f",
                                                 key="orden_take_profit", label_visibility="collapsed")

            # --- Calculadora de riesgo (Risk Manager): tamaño por riesgo + TP por R/R ---
            renderizar_calculadora(info, real, side, compra, precio, digitos, punto, vmin, vstep, oco_encendido)

            # --- Botón grande "Colocar orden en {precio}" (o "Colocar OCO") ---
            # `es_oco` indica que hay dos precios válidos para colocar un par OCO
            es_oco = bool(oco_encendido and pendiente and oco_precio_b)
            # OCO inválido: mismas patas (igual lado y prácticamente igual precio)
            oco_malo = bool(es_oco and oco_lado_b == ("BUY" if compra else "SELL")
                            and abs(oco_precio_b - pendiente) < (punto or 1e-9))
            # El botón se desactiva (clase orden-colocar-apagado y sin botón real) si falta margen o el OCO es inválido
            apagado = sin_margen or oco_malo
            cls =("orden-colocar-buy" if compra else "orden-colocar-sell") + (" orden-colocar-apagado" if apagado else "")
            if es_oco:
                ganancia_perdida_etiqueta, ganancia_perdida_precio, precio_attr, precio_estilo = "Colocar OCO · 2 órdenes", \
                    f"{pendiente:,.{digitos}f} / {oco_precio_b:,.{digitos}f}", "", "font-size:15px"
            else:
                # Pendiente: precio fijo elegido; a mercado: precio en vivo (feed)
                ganancia_perdida_etiqueta, ganancia_perdida_precio, precio_estilo = "Colocar orden en", f"{precio:,.{digitos}f}", ""
                precio_attr = "" if pendiente else _en_vivo(real, "side", d=digitos, side=side)
            # El botón real "Colocar orden" va invisible sobre el bloque HTML (CSS de orden_zona_colocar)
            with st.container(key="orden_zona_colocar"):
                st.html(
                    f"<div class='orden-colocar {cls}'>"
                    f"<div><div class='ganancia-perdida-etiqueta'>{ganancia_perdida_etiqueta}</div>"
                    f"<div class='ganancia-perdida-precio' style='{precio_estilo}' {precio_attr}>{ganancia_perdida_precio}</div></div>"
                    f"<div class='ganancia-perdida-arrow'>{'↗' if compra else '↘'}</div></div>"
                )
                if not apagado and st.button("Colocar orden", key="orden_superposicion_colocar"):
                    st.session_state.pop("orden_resultado", None)  # limpia resultado previo
                    st.session_state.orden_confirmacion = None
                    st.session_state.orden_oco_confirmacion = None
                    lado = "BUY" if compra else "SELL"
                    # Con One-Click activo se envía de inmediato; si no, se guarda la confirmación pendiente
                    if es_oco:
                        if un_clic:
                            ejecutar_oco(real, visible, lado, oco_lado_b,
                                         pendiente, oco_precio_b, volumen, gtc)
                            st.rerun(scope="fragment")
                        else:
                            st.session_state.orden_oco_confirmacion = {
                                "real": real, "visible": visible, "dig": digitos, "ladoA": lado,
                                "ladoB": oco_lado_b, "pa": pendiente, "pb": oco_precio_b,
                                "vol": volumen, "gtc": gtc, "ta": tipo_pendiente, "tb": oco_tipo_b}
                            st.rerun(scope="fragment")   # instantáneo (sin recargar el gráfico)
                    elif un_clic:
                        ejecutar(real, visible, side, volumen, stop_loss, take_profit, pendiente, gtc)
                        st.rerun(scope="fragment")
                    else:
                        st.session_state.orden_confirmacion = {
                            "real": real, "visible": visible, "dig": digitos, "side": side,
                            "vol": volumen, "sl": stop_loss, "tp": take_profit, "price": precio,
                            "pend": pendiente, "gtc": gtc}
                        st.rerun(scope="fragment")   # instantáneo (sin recargar el gráfico)

            # --- Confirmación (tarjeta flotante abajo-derecha, formato naranja como el
            #     cierre de Cartera). Inline en el fragmento → aparece al instante, sin
            #     oscurecer la pantalla ni recargar el gráfico. ---
            renderizar_confirmacion()

            # --- Aviso del resultado: toast naranja (éxito) / rojo (error), se cierra
            #     solo (~6 s) o con la ✕. Se inyecta en el documento padre una sola vez
            #     por resultado (el nonce evita que se repita en cada refresco). ---
            r = st.session_state.get("orden_resultado")
            if r:
                with st.container(key="orden_toastjs"):
                    _mensaje = r[1] if r[0] == "ok" else f"No se pudo operar: {r[1]}"
                    components.html(
                        aviso_js(_mensaje, r[0] != "ok",
                                 st.session_state.get("orden_resultado_nonce", "0")),
                        height=0)

        _ticket()


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara panel .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
