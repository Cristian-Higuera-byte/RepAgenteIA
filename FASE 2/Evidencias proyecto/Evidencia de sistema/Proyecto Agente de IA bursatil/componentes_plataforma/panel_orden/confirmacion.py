# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara confirmacion .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""
panel_orden/confirmacion.py
---------------------------
Tarjeta de confirmación flotante (abajo-derecha del panel), formato naranja como el
modal de cierre de Cartera. Cubre la orden simple (`orden_confirmacion`) y el OCO
(`orden_oco_confirmacion`). Se renderiza DENTRO del fragmento del ticket, así que sus botones
usan rerun de fragmento (instantáneo, sin recargar el gráfico).
"""
import streamlit as st

from componentes_plataforma.flujo_precios import atributos as _en_vivo

from .cuenta import margen, margen_libre
from .ejecucion import ejecutar, ejecutar_oco, registrar_resultado


# TITULO RENDERIZAR CONFIRMACION

def renderizar_confirmacion():
    """Dibuja la tarjeta de confirmación si hay una orden (`orden_confirmacion`) o un OCO (`orden_oco_confirmacion`) pendiente.

    No recibe parámetros ni devuelve nada. Si no hay confirmación pendiente, termina sin dibujar. Para la
    orden simple muestra el resumen (lado, volumen, símbolo, precio y SL/TP) y los botones "Colocar orden"
    (revisa el margen libre antes de ejecutar) y "Cancelar"; para el OCO, el resumen de las dos patas y los
    botones "Colocar OCO" y "Cancelar". Al pulsar cualquier botón limpia la confirmación y relanza solo el
    fragmento."""
    confirmacion = st.session_state.get("orden_confirmacion")
    confirmacion_oco = st.session_state.get("orden_oco_confirmacion")
    if not (confirmacion or confirmacion_oco):
        return
    # Contenedor con key orden_confirmacion_tarjeta: el CSS lo coloca flotando abajo a la derecha
    with st.container(key="orden_confirmacion_tarjeta"):
        if confirmacion:
            # --- Confirmación de orden simple ---
            d, digitos = confirmacion, confirmacion["dig"]
            if d["pend"]:
                modo = (f"Orden pendiente en <b>{d['price']:,.{digitos}f}</b>"
                        + (" · GTC" if d["gtc"] else " · DAY"))
            else:
                # Orden a mercado: el precio se actualiza EN VIVO con el feed (como el ticket).
                _precio = _en_vivo(d["real"], "side", d=digitos, side=d["side"])
                modo = f"A mercado, ~<b {_precio}>{d['price']:,.{digitos}f}</b>"
            # Líneas opcionales de Stop Loss y Take Profit, solo si se definieron
            extra = ((f"<br>Stop Loss: <b>{d['sl']:,.{digitos}f}</b>" if d["sl"] else "")
                     + (f"<br>Take Profit: <b>{d['tp']:,.{digitos}f}</b>" if d["tp"] else ""))
            st.html(f"<div class='orden-confirmacion-t'>Confirmar orden</div>"
                    f"<div class='orden-confirmacion-d'><b>{d['side']}</b> de <b>{d['vol']:.2f}</b> lote(s) "
                    f"de <b>{d['visible']}</b><br>{modo}{extra}</div>")
            if st.button("Colocar orden", key="orden_confirmacion_aceptar", width="stretch"):
                # Se vuelve a validar el margen justo antes de enviar, por si cambió desde que se preparó la orden
                m2, libre2 = margen(d["real"], d["vol"], d["price"], d["side"]), margen_libre()
                if m2 and libre2 is not None and m2 > libre2:
                    registrar_resultado("error", "No tiene margen suficiente para colocar esta orden.")
                else:
                    ejecutar(d["real"], d["visible"], d["side"], d["vol"], d["sl"],
                             d["tp"], d["pend"], d["gtc"])
                st.session_state.orden_confirmacion = None
                st.rerun(scope="fragment")
            if st.button("Cancelar", key="orden_confirmacion_cancelar", width="stretch"):
                st.session_state.orden_confirmacion = None
                st.rerun(scope="fragment")
        else:
            # --- Confirmación de OCO (dos órdenes pendientes vinculadas) ---
            d, digitos = confirmacion_oco, confirmacion_oco["dig"]
            st.html(
                f"<div class='orden-confirmacion-t'>Confirmar OCO</div>"
                f"<div class='orden-confirmacion-d'>Dos órdenes de <b>{d['vol']:.2f}</b> lote(s) de "
                f"<b>{d['visible']}</b>{' · GTC' if d['gtc'] else ' · DAY'}:<br>"
                f"A: <b>{d['ta']} · {d['ladoA']}</b> @ <b>{d['pa']:,.{digitos}f}</b><br>"
                f"B: <b>{d['tb']} · {d['ladoB']}</b> @ <b>{d['pb']:,.{digitos}f}</b><br>"
                f"<span style='color:#8b949e'>Cuando una se ejecute, la otra se cancela sola.</span></div>")
            if st.button("Colocar OCO", key="orden_confirmacion_aceptar", width="stretch"):
                ejecutar_oco(d["real"], d["visible"], d["ladoA"], d["ladoB"],
                             d["pa"], d["pb"], d["vol"], d["gtc"])
                st.session_state.orden_oco_confirmacion = None
                st.rerun(scope="fragment")
            if st.button("Cancelar", key="orden_confirmacion_cancelar", width="stretch"):
                st.session_state.orden_oco_confirmacion = None
                st.rerun(scope="fragment")


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara confirmacion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
