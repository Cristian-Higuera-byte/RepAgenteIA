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
modal de cierre de Cartera. Cubre la orden simple (`ord_confirm`) y el OCO
(`ord_oco_confirm`). Se renderiza DENTRO del fragmento del ticket, así que sus botones
usan rerun de fragmento (instantáneo, sin recargar el gráfico).
"""
import streamlit as st

from components.flujo_precios import atributos as _en_vivo

from .cuenta import margen, margen_libre
from .ejecucion import ejecutar, ejecutar_oco, registrar_resultado


def renderizar_confirmacion():
    """Dibuja la tarjeta de confirmación si hay una orden (`ord_confirm`) o un OCO (`ord_oco_confirm`) pendiente.

    No recibe parámetros ni devuelve nada. Si no hay confirmación pendiente, termina sin dibujar. Para la
    orden simple muestra el resumen (lado, volumen, símbolo, precio y SL/TP) y los botones "Colocar orden"
    (revisa el margen libre antes de ejecutar) y "Cancelar"; para el OCO, el resumen de las dos patas y los
    botones "Colocar OCO" y "Cancelar". Al pulsar cualquier botón limpia la confirmación y relanza solo el
    fragmento."""
    cf = st.session_state.get("ord_confirm")
    cfo = st.session_state.get("ord_oco_confirm")
    if not (cf or cfo):
        return
    # Contenedor con key ord_cfm: el CSS lo coloca flotando abajo a la derecha
    with st.container(key="ord_cfm"):
        if cf:
            # --- Confirmación de orden simple ---
            d, dig = cf, cf["dig"]
            if d["pend"]:
                modo = (f"Orden pendiente en <b>{d['price']:,.{dig}f}</b>"
                        + (" · GTC" if d["gtc"] else " · DAY"))
            else:
                # Orden a mercado: el precio se actualiza EN VIVO con el feed (como el ticket).
                _px = _en_vivo(d["real"], "side", d=dig, side=d["side"])
                modo = f"A mercado, ~<b {_px}>{d['price']:,.{dig}f}</b>"
            # Líneas opcionales de Stop Loss y Take Profit, solo si se definieron
            extra = ((f"<br>Stop Loss: <b>{d['sl']:,.{dig}f}</b>" if d["sl"] else "")
                     + (f"<br>Take Profit: <b>{d['tp']:,.{dig}f}</b>" if d["tp"] else ""))
            st.html(f"<div class='ord-cfm-t'>Confirmar orden</div>"
                    f"<div class='ord-cfm-d'><b>{d['side']}</b> de <b>{d['vol']:.2f}</b> lote(s) "
                    f"de <b>{d['visible']}</b><br>{modo}{extra}</div>")
            if st.button("Colocar orden", key="ord_cfm_ok", width="stretch"):
                # Se vuelve a validar el margen justo antes de enviar, por si cambió desde que se preparó la orden
                m2, libre2 = margen(d["real"], d["vol"], d["price"], d["side"]), margen_libre()
                if m2 and libre2 is not None and m2 > libre2:
                    registrar_resultado("error", "No tiene margen suficiente para colocar esta orden.")
                else:
                    ejecutar(d["real"], d["visible"], d["side"], d["vol"], d["sl"],
                             d["tp"], d["pend"], d["gtc"])
                st.session_state.ord_confirm = None
                st.rerun(scope="fragment")
            if st.button("Cancelar", key="ord_cfm_cancel", width="stretch"):
                st.session_state.ord_confirm = None
                st.rerun(scope="fragment")
        else:
            # --- Confirmación de OCO (dos órdenes pendientes vinculadas) ---
            d, dig = cfo, cfo["dig"]
            st.html(
                f"<div class='ord-cfm-t'>Confirmar OCO</div>"
                f"<div class='ord-cfm-d'>Dos órdenes de <b>{d['vol']:.2f}</b> lote(s) de "
                f"<b>{d['visible']}</b>{' · GTC' if d['gtc'] else ' · DAY'}:<br>"
                f"A: <b>{d['ta']} · {d['ladoA']}</b> @ <b>{d['pa']:,.{dig}f}</b><br>"
                f"B: <b>{d['tb']} · {d['ladoB']}</b> @ <b>{d['pb']:,.{dig}f}</b><br>"
                f"<span style='color:#8b949e'>Cuando una se ejecute, la otra se cancela sola.</span></div>")
            if st.button("Colocar OCO", key="ord_cfm_ok", width="stretch"):
                ejecutar_oco(d["real"], d["visible"], d["ladoA"], d["ladoB"],
                             d["pa"], d["pb"], d["vol"], d["gtc"])
                st.session_state.ord_oco_confirm = None
                st.rerun(scope="fragment")
            if st.button("Cancelar", key="ord_cfm_cancel", width="stretch"):
                st.session_state.ord_oco_confirm = None
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
