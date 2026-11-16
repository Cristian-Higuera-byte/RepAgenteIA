# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara detalle .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
cartera_panel/detalle.py
------------------------
Detalle desplegable de una posición (acordeón inline bajo su fila, como XM): al tocar
una posición se despliega toda la info, el botón de cierre, "Mostrar gráfico" y los
editores de Take Profit / Stop Loss y Stop dinámico (trailing). El P/G y el precio
actual se pintan en vivo por el feed; mientras una fila está desplegada, aplicacion.py pausa el
auto-refresco del fragmento (cartera_editando).

Funciones: detalle_inline (punto de entrada), _grid_y_editores (tabla de datos y
editores), _editor_nivel (Take Profit / Stop Loss), _editor_trailing (stop dinámico) y
los validadores _resolver_nivel / _resolver_distancia. Las modificaciones se envían a
MT5 con modificar_sltp y la configuración del stop dinámico se guarda con
almacen_stop_dinamico.
"""
import html
import time
from datetime import datetime, timezone

import streamlit as st

from herramientas.puente_mt5 import modificar_sltp, especs_posicion
from herramientas import almacen_stop_dinamico
from herramientas.tickets import ticket as _tk
from herramientas import gestor_lista_activos as wl

from .comun import neto


# TITULO RESOLVER NIVEL

def _resolver_nivel(clave, modo, valor, e, apertura, actual, compra):
    """Devuelve (precio, error). clave='tp'|'sl'; modo='Precio'|'Cantidad'.
    'Cantidad' convierte un objetivo en dinero a precio usando k (valor de 1
    unidad de precio por lote) desde el precio de apertura. Valida lado y la
    distancia mínima del bróker respecto del precio actual.

    Parámetros: clave ("tp" o "sl"), modo ("Precio" o "Cantidad"), valor (texto escrito
    por el usuario), e (especificaciones del símbolo: digitos, k, volumen, stops_level,
    point), ap (precio de apertura), ac (precio actual) y compra (True si es Compra).
    Devuelve (precio, None) si es válido, (None, mensaje) si hay error de validación o
    (None, None) si el campo está vacío.
    """
    # Normaliza el texto: sin espacios ni separadores de miles; vacío significa "sin nivel".
    valor = (valor or "").strip().replace(",", "")
    if not valor:
        return None, None
    try:
        x = float(valor)
    except ValueError:
        return None, "Ingresa un número."
    # Especificaciones del símbolo: decimales, valor por unidad de precio y lote.
    digitos = e.get("digitos", 5)
    k = e.get("k", 0.0)
    volumen = e.get("volumen", 0.0) or 1.0
    # Modo Cantidad: convierte el monto en dinero a un movimiento de precio desde la apertura.
    if (modo or "Precio") == "Cantidad":
        if k <= 0 or volumen <= 0:
            return None, "No se puede convertir el monto a precio."
        movimiento = abs(x) / (k * volumen)
        if clave == "tp":
            precio = apertura + movimiento if compra else apertura - movimiento          # objetivo favorable
        else:
            precio = apertura - movimiento if compra else apertura + movimiento          # pérdida tolerada
    else:
        precio = x
    # Redondea a los decimales del símbolo y calcula la distancia mínima exigida por el bróker.
    precio = round(precio, digitos)
    distancia = e.get("stops_level", 0) * e.get("point", 0.0)
    # Valida que el nivel quede del lado correcto y respete la distancia mínima.
    if clave == "tp":
        if compra and precio <= actual + distancia:
            return None, f"El take profit debe estar sobre {actual + distancia:,.{digitos}f}."
        if (not compra) and precio >= actual - distancia:
            return None, f"El take profit debe estar bajo {actual - distancia:,.{digitos}f}."
    else:
        if compra and precio >= actual - distancia:
            return None, f"El stop loss debe estar bajo {actual - distancia:,.{digitos}f}."
        if (not compra) and precio <= actual + distancia:
            return None, f"El stop loss debe estar sobre {actual + distancia:,.{digitos}f}."
    return precio, None


# TITULO EDITOR NIVEL

def _editor_nivel(clave, titulo, ticket, p, e, apertura, actual, compra, bloqueado=False):
    """Toggle Take profit / Stop loss con el editor desplegable (Precio/Cantidad,
    input, Cancelar/Guardar), igual que XM. Aplica con modificar_sltp.
    `bloqueado`: el nivel lo gestiona el stop dinámico → se muestra en gris, sin editar.

    Parámetros: clave ("tp"/"sl"), titulo (texto del toggle), ticket, p (posición), e
    (especificaciones), ap/ac (precio de apertura y actual) y compra. No devuelve nada;
    escribe en st.session_state (cartera_editando mientras hay un input abierto, cartera_detalle_fb) y
    relanza el fragmento tras quitar, guardar o cancelar.
    """
    # Nivel actual en MT5 (0 significa que no existe) y decimales del símbolo.
    existe = float(p.get(clave, 0.0) or 0.0)
    digitos = e.get("digitos", 5)
    # Nivel controlado por el stop dinámico: solo se muestra, sin permitir edición.
    if bloqueado:
        st.toggle(titulo, value=True, key=f"cartera_detalle_{clave}_blk_{ticket}", disabled=True)
        st.markdown("<div class='cartera-detalle-nota'>Gestionado por el stop dinámico. Para cambiarlo, "
                    "edita la distancia o quita el stop dinámico.</div>", unsafe_allow_html=True)
        return
    # Toggle principal: encendido si el nivel ya existe.
    encendido = st.toggle(titulo, value=existe > 0, key=f"cartera_detalle_{clave}_encendido_{ticket}")
    if not encendido:
        if existe > 0:
            if st.button(f"Quitar {titulo.lower()}", key=f"cartera_detalle_{clave}_quitar_{ticket}",
                         width="stretch"):
                resultado = modificar_sltp(ticket, **{clave: 0.0})
                _retroalimentacion_stop_loss_take_profit(resultado, titulo, "quitado")
                st.rerun(scope="fragment")
        return
    # Formulario de edición (selector Precio/Cantidad, input y botones).
    st.session_state.cartera_editando = True   # hay un input abierto: pausa el auto-refresco
    modo = st.segmented_control(
        "modo", ["Precio", "Cantidad"], default="Precio",
        key=f"cartera_detalle_{clave}_modo_{ticket}", label_visibility="collapsed")
    st.markdown("<div class='cartera-detalle-nota'>Las cantidades finales pueden diferir de los "
                "valores introducidos.</div>", unsafe_allow_html=True)
    marcador = f"Nivel de {titulo.lower()}"
    pre = f"{existe:.{digitos}f}" if (existe > 0 and (modo or "Precio") == "Precio") else ""
    valor = st.text_input(marcador, value=pre, placeholder=marcador,
                          key=f"cartera_detalle_{clave}_valor_{ticket}", label_visibility="collapsed")
    # Valida en cada reejecución lo escrito; Guardar solo se habilita con un precio válido.
    precio, error = _resolver_nivel(clave, modo, valor, e, apertura, actual, compra)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", key=f"cartera_detalle_{clave}_cancelar_{ticket}", width="stretch"):
            st.session_state[f"cartera_detalle_{clave}_encendido_{ticket}"] = False
            st.rerun(scope="fragment")
    with c2:
        if st.button("Guardar", key=f"cartera_detalle_{clave}_guardar_{ticket}", width="stretch",
                     type="primary", disabled=(precio is None)):
            resultado = modificar_sltp(ticket, **{clave: precio})
            _retroalimentacion_stop_loss_take_profit(resultado, titulo, "guardado")
            st.rerun(scope="fragment")
    if valor and error:
        st.markdown(f"<div class='cartera-detalle-error'>{html.escape(error)}</div>", unsafe_allow_html=True)


# TITULO RETROALIMENTACION STOP LOSS TAKE PROFIT

def _retroalimentacion_stop_loss_take_profit(res, titulo, verbo):
    """Guarda en st.session_state.cartera_detalle_fb el mensaje de resultado de modificar_sltp.

    Recibe la respuesta de MT5 (`res`, con clave "error" si falló), el título del nivel
    y el verbo en participio ("guardado"/"quitado"). El detalle muestra y borra el mensaje.
    """
    if isinstance(res, dict) and "error" in res:
        st.session_state.cartera_detalle_fb = ("err", f"No se pudo guardar: {res['error']}")
    else:
        st.session_state.cartera_detalle_fb = ("ok", f"{titulo} {verbo}.")


# TITULO RESOLVER DISTANCIA

def _resolver_distancia(valor, sm, digitos, precio=0.0):
    """Valida la distancia (en precio) del Stop dinámico: número > 0, no menor
    que la distancia mínima del bróker (stops_level × point) y menor que el precio
    actual (si no, el stop de una compra quedaría en negativo y el motor nunca lo
    colocaría: parecía que "el stop dinámico no aparece").

    Recibe el texto escrito, `sm` (distancia mínima en precio), `dig` (decimales) y
    `precio` (precio actual del activo, 0 si no se conoce).
    Devuelve (distancia, None) si es válida, (None, mensaje) si no, o (None, None) si el
    campo está vacío.
    """
    # Normaliza el texto; vacío significa "sin valor todavía".
    valor = (valor or "").strip().replace(",", "")
    if not valor:
        return None, None
    try:
        x = float(valor)
    except ValueError:
        return None, "Ingresa un número."
    if x <= 0:
        return None, "La distancia debe ser mayor que cero."
    x = round(x, digitos)
    if sm > 0 and x < sm:
        return None, f"La distancia mínima del bróker es {sm:,.{digitos}f}."
    if precio > 0 and x > precio * 0.25:
        sugerida = round(precio * 0.002, digitos)
        return None, (f"La distancia ({x:,.{digitos}f}) es más del 25 % del precio actual ({precio:,.{digitos}f}): "
                      f"el stop quedaría lejísimos (fuera del gráfico) o bajo cero. Se escribe en precio, "
                      f"p. ej. {sugerida:,.{digitos}f} (0,2 %).")
    return x, None


# TITULO EDITOR TRAILING

def _editor_trailing(ticket, p, e):
    """Toggle 'Stop dinámico (trailing)': el SL sigue al precio a una distancia
    fija cuando la operación va a favor y nunca retrocede. La config se guarda en
    data/trailing.json; el motor de servidor_datos.py la aplica en vivo (por eso
    requiere ese proceso encendido).

    Estados: activado sin guardar -> formulario; ya guardado -> resumen + Editar;
    toggle apagado con config -> botón Quitar.

    Parámetros: ticket de la posición, p (posición) y e (especificaciones del símbolo).
    No devuelve nada; lee y escribe data/trailing.json mediante almacen_stop_dinamico,
    puede quitar el SL en MT5 con modificar_sltp y relanza la app tras cada acción.
    """
    # Configuración guardada (si existe), distancia mínima del bróker y clave del modo edición.
    configuracion = almacen_stop_dinamico.leer().get(_tk(ticket))
    digitos = e.get("digitos", 5)
    sm = e.get("stops_level", 0) * e.get("point", 0.0)
    editar_key = f"cartera_detalle_trail_edit_{ticket}"

    # Toggle principal: encendido si ya hay configuración guardada.
    encendido = st.toggle("Stop dinámico (trailing)", value=configuracion is not None, key=f"cartera_detalle_trail_on_{ticket}")
    if not encendido:
        if configuracion is not None:
            if st.button("Quitar stop dinámico", key=f"cartera_detalle_trail_quitar_{ticket}", width="stretch"):
                almacen_stop_dinamico.quitar(ticket)
                # El stop dinámico ERA el stop: al quitarlo se quita también el SL que
                # el motor había puesto (si no, el "Stop loss" manual quedaría activo solo).
                modificar_sltp(ticket, stop_loss=0.0)
                st.session_state.pop(editar_key, None)
                st.session_state.cartera_detalle_fb = ("ok", "Stop dinámico quitado.")
                st.rerun()
        return

    # Estado GUARDADO (hay config y no se está editando): resumen + "Editar".
    if configuracion is not None and not st.session_state.get(editar_key, False):
        st.markdown(
            "<div class='cartera-detalle-trailing-encendido'>"
            "<span class='k'>Stop dinámico activo</span>"
            f"<span class='v'>Distancia {configuracion['dist']:,.{digitos}f}</span></div>"
            "<div class='cartera-detalle-nota'>El stop loss sigue al precio y solo se mueve a tu favor. "
            "Requiere el servidor de datos encendido.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Editar distancia", key=f"cartera_detalle_trail_editar_{ticket}", width="stretch"):
            st.session_state[editar_key] = True
            st.rerun()
        return

    # Estado FORMULARIO (recién activado o editando). Hay un input: se pausa el
    # auto-refresco de la lista para no perder el foco mientras se escribe.
    st.session_state.cartera_editando = True
    st.markdown("<div class='cartera-detalle-nota'>El stop loss seguirá al precio a la distancia indicada y "
                "solo se moverá a tu favor. Requiere el servidor de datos encendido.</div>",
                unsafe_allow_html=True)
    pre = f"{configuracion['dist']:.{digitos}f}" if configuracion else ""
    marcador = "Distancia (en precio)"
    valor = st.text_input(marcador, value=pre, placeholder=marcador, key=f"cartera_detalle_trail_val_{ticket}",
                          label_visibility="collapsed")
    precio_referencia = float(e.get("bid") or e.get("ask") or p.get("precio_actual") or 0.0)
    distancia, error = _resolver_distancia(valor, sm, digitos, precio_referencia)
    if sm > 0:
        st.markdown(f"<div class='cartera-detalle-nota'>Distancia mínima del bróker: {sm:,.{digitos}f}.</div>",
                    unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Cancelar", key=f"cartera_detalle_trail_cancelar_{ticket}", width="stretch"):
            if configuracion is not None:
                st.session_state[editar_key] = False       # vuelve al resumen
            else:
                st.session_state[f"cartera_detalle_trail_on_{ticket}"] = False   # apaga el toggle
            st.rerun()
    with c2:
        if st.button("Guardar", key=f"cartera_detalle_trail_guardar_{ticket}", width="stretch",
                     type="primary", disabled=(distancia is None)):
            almacen_stop_dinamico.fijar(ticket, distancia)
            st.session_state[editar_key] = False
            st.session_state.cartera_detalle_fb = ("ok", "Stop dinámico activado.")
            st.rerun()
    if valor and error:
        st.markdown(f"<div class='cartera-detalle-error'>{html.escape(error)}</div>", unsafe_allow_html=True)


# TITULO DETALLE INLINE

def detalle_inline(ticket, p):
    """Detalle de la posición desplegado inline, justo bajo su fila (acordeón, XM).
    `p` llega fresco de obtener_posiciones() desde el bucle de la lista.

    Muestra el botón "Cerrar operación" (abre el modal de confirmación), "Mostrar
    gráfico" (selecciona el símbolo en el gráfico central), el feedback de la última
    acción y la tabla con editores (_grid_y_editores). No devuelve nada.
    """
    # Contenedor con clave propia: detalle.css lo estiliza como panel unido a la fila.
    with st.container(key=f"cartera_detalle_contenedor_{ticket}"):
        # La posición pudo cerrarse entre refrescos.
        if not p:
            st.markdown("<div class='cartera-detalle-vacio'>La posición ya no está abierta.</div>",
                        unsafe_allow_html=True)
            return
        # Especificaciones del símbolo y datos básicos de la posición.
        e = especs_posicion(ticket) or {}
        simbolo = p["symbol"]
        base = wl.nombre_visible(simbolo)
        lado = p.get("tipo", "")
        compra = (lado == "Compra")
        neto_ganancia_perdida = neto(p)
        apertura = float(p.get("precio_apertura", 0.0) or 0.0)
        actual = float(p.get("precio_actual", 0.0) or 0.0)
        digitos = e.get("digitos", 5)
        variacion = (((actual - apertura) if compra else (apertura - actual)) / apertura * 100.0) if apertura else 0.0

        # Mensaje de resultado de la última acción (se muestra una sola vez).
        fb = st.session_state.pop("cartera_detalle_fb", None)
        if fb:
            st.markdown(f"<div class='cartera-detalle-retroalimentacion-{'ok' if fb[0]=='ok' else 'err'}'>"
                        f"{html.escape(fb[1])}</div>", unsafe_allow_html=True)

        # Botón de cierre (texto con el monto en vivo por el feed): abre el MISMO
        # modal de confirmación que la ✕ de la lista (evita cierres accidentales).
        signo = "-" if neto_ganancia_perdida < 0 else ""
        with st.container(key=f"cartera_detalle_cerrar_{ticket}"):
            if st.button(f"Cerrar operación: {signo}${abs(neto_ganancia_perdida):,.2f}", key=f"cartera_detalle_boton_cerrar_{ticket}",
                         type="primary", width="stretch"):
                st.session_state.cartera_cerrar = {
                    "ticket": ticket, "symbol": base, "profit": neto_ganancia_perdida,
                    "tipo": lado, "volumen": p.get("volumen", 0),
                }
                st.session_state.pop("cartera_resultado", None)
                st.rerun(scope="app")
        if st.button("Mostrar gráfico", key=f"cartera_detalle_grafico_{ticket}", width="stretch"):
            st.session_state.activo_seleccionado = simbolo
            # Se mantiene el desplegable abierto (no se limpia cartera_detalle).
            st.rerun()

        _grid_y_editores(ticket, p, e, simbolo, lado, compra, neto_ganancia_perdida, apertura, actual, digitos, variacion)


# TITULO GRID Y EDITORES

def _grid_y_editores(ticket, p, e, simbolo, lado, compra, neto_ganancia_perdida, apertura, actual, digitos, var):
    """Dibuja la tabla de datos de la posición y los editores de TP, SL y stop dinámico.

    Recibe el ticket, la posición `p`, las especificaciones `e`, el símbolo, el lado, la
    bandera `compra`, el P/G neto, los precios de apertura y actual, los decimales `dig` y
    la variación porcentual `var`. Los campos con atributos data-pj-* los repinta el feed
    en vivo. No devuelve nada.
    """
    # Horas: p['tiempo'] es epoch del servidor (XM GMT+3). La local se obtiene
    # restando el desfase (servidor ahora − hora real), redondeado a 15 min.
    tsrv = int(p.get("tiempo", 0) or 0)
    apagado = e.get("srv_now", 0.0) - time.time() if e.get("srv_now") else 0.0
    apagado = round(apagado / 900) * 900
    f_srv = datetime.fromtimestamp(tsrv, timezone.utc).strftime("%d/%m/%y, %H:%M:%S") if tsrv else "—"
    # Hora local real: el epoch ya sin desfase es UTC; se muestra en la zona horaria del equipo.
    f_loc = datetime.fromtimestamp(max(0, tsrv - apagado), timezone.utc).astimezone().strftime("%d/%m/%y, %H:%M:%S") if tsrv else "—"
    take_profit = float(p.get("tp", 0.0) or 0.0)
    stop_loss = float(p.get("sl", 0.0) or 0.0)
    take_profit_texto = f"{take_profit:,.{digitos}f}" if take_profit > 0 else "–"
    stop_loss_texto = f"{stop_loss:,.{digitos}f}" if stop_loss > 0 else "–"
    # Pares (etiqueta, valor HTML) que se muestran en la tabla.
    filas = [
        ("ID de orden", str(ticket)),
        ("Instrumento", html.escape(simbolo)),
        ("Cantidad", f"{p.get('volumen', 0):,.2f} lotes"),
        ("Dirección", html.escape(lado.upper())),
        ("Precio de apertura", f"{apertura:,.{digitos}f}"),
        ("Precio actual", f"<span data-pj-posc='{ticket}' data-pj-d='{digitos}'>{actual:,.{digitos}f}</span>"),
        ("PnL", f"<span class='{'cartera-detalle-sube' if neto_ganancia_perdida >= 0 else 'cartera-detalle-baja'}' data-pj-pos='{ticket}' "
                f"data-pj-up='#2ebd85' data-pj-dn='#f6465d'>{neto_ganancia_perdida:+,.2f}</span>"),
        ("Variación del precio", f"{var:+.4f}%"),
        ("Swaps", f"${p.get('swap', 0.0):,.2f}"),
        ("Hora de apertura", f_loc),
        ("Hora apertura (servidor)", f_srv),
        ("Take profit / Stop loss", f"{take_profit_texto} / {stop_loss_texto}"),
    ]
    # Tabla de datos (estilos .cartera-detalle-cuadricula en detalle.css).
    st.markdown(
        "<div class='cartera-detalle-cuadricula'>" + "".join(
            f"<div class='row'><span class='k'>{k}</span><span class='v'>{v}</span></div>"
            for k, v in filas) + "</div>",
        unsafe_allow_html=True,
    )

    # Editores Take Profit / Stop Loss (toggle + Precio/Cantidad + Cancelar/Guardar).
    # Si el stop dinámico está activo, el Stop loss manual queda deshabilitado (el
    # auto gestiona ese mismo SL): no se puede editar ni quitar desde aquí.
    trailing_activo = _tk(ticket) in almacen_stop_dinamico.leer()
    with st.container(key=f"cartera_detalle_tpbox_{ticket}"):
        _editor_nivel("tp", "Take profit", ticket, p, e, apertura, actual, compra)
    with st.container(key=f"cartera_detalle_slbox_{ticket}"):
        _editor_nivel("sl", "Stop loss", ticket, p, e, apertura, actual, compra, bloqueado=trailing_activo)
    with st.container(key=f"cartera_detalle_trailbox_{ticket}"):
        _editor_trailing(ticket, p, e)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara detalle .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
