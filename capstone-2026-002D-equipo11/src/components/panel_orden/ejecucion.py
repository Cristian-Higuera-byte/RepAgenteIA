# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara ejecucion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
panel_orden/ejecucion.py
------------------------
Envío de órdenes a MetaTrader 5 desde el ticket: a mercado, pendiente y OCO
(One-Cancels-the-Other). Cada función deja el resultado en session_state
(`ord_result` + nonce) para que `avisos.py` lo muestre una sola vez, y limpia la
confirmación pendiente. No dibuja UI.
"""
import time

import streamlit as st

from tools.puente_mt5 import (colocar_orden_pendiente, ejecutar_orden_mercado,
                              eliminar_orden)
from tools import almacen_oco


def registrar_resultado(estado, msg):
    """Guarda el resultado de la orden + un nonce (para que el toast se muestre una vez).

    `estado` es "ok" o "error" y `msg` el texto a mostrar. Escribe `ord_result` y `ord_result_nonce` en la
    sesión; el nonce es la hora actual, distinta en cada resultado."""
    st.session_state.ord_result = (estado, msg)
    st.session_state.ord_result_nonce = f"{time.time()}"


def ejecutar(real, visible, tipo, vol, sl, tp, pendiente=None, gtc=True):
    """Envía la orden a MT5: a mercado, o pendiente si `pendiente` trae un precio.

    Recibe el símbolo real y el visible, el lado ("BUY"/"SELL"), el volumen en lotes, Stop Loss y Take
    Profit (o vacío), el precio de la pendiente y si es GTC (hasta cancelar) o DAY. Registra el resultado
    (éxito o error devuelto por MT5) con `registrar_resultado` y limpia `ord_confirm`. No devuelve nada."""
    if pendiente:
        # Orden pendiente: se coloca al precio indicado y se arma el mensaje de éxito
        res = colocar_orden_pendiente(real, tipo, vol, pendiente, sl, tp, hasta_cancelar=gtc)
        ok = (f"Pendiente colocada: {res.get('tipo', '')} de {vol:.2f} lote(s) de {visible} "
              f"a {res.get('price')}" + (" · GTC" if gtc else " · DAY (solo hoy)") + ".")
    else:
        # Orden a mercado: se ejecuta de inmediato al precio vigente
        res = ejecutar_orden_mercado(real, tipo, vol, sl, tp)
        verbo_es = "comprado" if tipo == "BUY" else "vendido"
        ok = (f"¡Listo! Has {verbo_es} {res.get('volume')} lote(s) de {visible} "
              f"a {res.get('price')}.")
    # Si el puente de MT5 devolvió un error, se muestra ese texto en lugar del mensaje de éxito
    if "error" in res:
        registrar_resultado("error", res["error"])
    else:
        registrar_resultado("ok", ok)
    st.session_state.ord_confirm = None


def ejecutar_oco(real, visible, lado_a, lado_b, precio_a, precio_b, vol, gtc=True):
    """Coloca las DOS patas de un OCO y las vincula en almacen_oco. Si falla la 2.ª,
    cancela la 1.ª para no dejar un par a medias. Las patas van sin SL/TP (suelen
    ir en lados opuestos: el SL/TP se define sobre la posición al ejecutarse).

    Recibe el símbolo real y el visible, el lado y el precio de cada pata, el volumen y si son GTC. Registra
    el resultado y limpia `ord_oco_confirm`. No devuelve nada."""
    # Primera pata: si falla, no hay nada que deshacer
    ra = colocar_orden_pendiente(real, lado_a, vol, precio_a, 0.0, 0.0, hasta_cancelar=gtc)
    if "error" in ra:
        registrar_resultado("error", f"OCO: no se pudo colocar la 1.ª orden · {ra['error']}")
        st.session_state.ord_oco_confirm = None
        return
    # Segunda pata: si falla se elimina la primera para no dejar el par a medias
    rb = colocar_orden_pendiente(real, lado_b, vol, precio_b, 0.0, 0.0, hasta_cancelar=gtc)
    if "error" in rb:
        und = eliminar_orden(int(ra["order"]))
        extra = "" if "error" not in und else " (no se pudo deshacer la 1.ª: revísala en el gráfico)"
        registrar_resultado(
            "error",
            f"OCO: no se pudo colocar la 2.ª orden · {rb['error']}. Se canceló la 1.ª{extra}.")
        st.session_state.ord_oco_confirm = None
        return
    # Ambas colocadas: se vinculan por número de orden para que, al ejecutarse una, se cancele la otra
    almacen_oco.fijar(int(ra["order"]), int(rb["order"]), real)
    ok = (f"¡Listo! OCO colocado en {visible}: {ra.get('tipo')} {vol:.2f} @ {ra.get('price')} · "
          f"{rb.get('tipo')} {vol:.2f} @ {rb.get('price')}"
          + (" · GTC" if gtc else " · DAY (solo hoy)")
          + ". Cuando una se ejecute, la otra se cancela sola.")
    registrar_resultado("ok", ok)
    st.session_state.ord_oco_confirm = None


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara ejecucion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
