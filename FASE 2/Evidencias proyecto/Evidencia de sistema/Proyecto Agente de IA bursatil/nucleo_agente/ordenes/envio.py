# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara envio .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Envío de órdenes a MetaTrader 5 (apertura y cierre) e interpretación del resultado. Solo lo llama confirmar_orden().

Aquí se vuelven a aplicar los chequeos de riesgo con el precio del momento de la confirmación, porque entre la
propuesta y el clic del usuario el mercado pudo moverse."""
from typing import Any

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from herramientas import registro_operaciones
from herramientas.tickets import ticket as _tk
from nucleo_agente.ordenes.limites import MAGIC, TOLERANCIA_VS_PROPUESTA
from nucleo_agente.ordenes.mt5_utiles import NOMBRE_BROKER, _chequeos_globales, _con_candado, _desviacion, _modo_llenado
from nucleo_agente.ordenes.validacion import _evaluar_apertura


# TITULO ENVIAR APERTURA

@_con_candado
def _enviar_apertura(o: dict[str, Any]) -> dict[str, Any]:
    """Revalida y envía a MT5 una orden de apertura a mercado.

    Recibe la fila de la orden (símbolo, lado, sl, tp, volumen, riesgo_dinero). Aplica los chequeos globales,
    reevalúa con el precio actual y el mismo volumen, y rechaza si el riesgo superó en más de
    TOLERANCIA_VS_PROPUESTA lo que aprobó el usuario. Devuelve el diccionario de _interpretar o un rechazo
    con estado RECHAZADA_RIESGO. Efecto: llamada order_send a MT5, bajo MT5_LOCK."""
    # Chequeos globales: MT5 listo, cuenta demo, interruptor, pérdida diaria y tope de posiciones.
    cuenta, motivo = _chequeos_globales(para_abrir=True)
    if motivo:
        return {"ok": False, "estado": "RECHAZADA_RIESGO", "mensaje": motivo}
    # Se revalida con el precio actual y el MISMO volumen propuesto.
    evento = _evaluar_apertura(cuenta, o["simbolo"], o["lado"], o["sl"], o["tp"], None, volumen_fijo=o["volumen"],
                           incluir_pendientes=False)
    if not evento["ok"]:
        return {"ok": False, "estado": "RECHAZADA_RIESGO", "mensaje": evento["motivo"]}

    d = evento["datos"]
    # Riesgo que el usuario vio al aprobar; si el precio lo disparó más de lo tolerado, no se envía.
    aprobado = o["riesgo_dinero"] or 0
    if aprobado and d["riesgo_dinero"] > aprobado * TOLERANCIA_VS_PROPUESTA:
        return {
            "ok": False, "estado": "RECHAZADA_RIESGO",
            "mensaje": (
                f"El precio se movió: el riesgo pasó de {aprobado:.2f} a {d['riesgo_dinero']:.2f} {d['moneda']}, "
                "más de lo que aprobaste. Pídele al agente una propuesta nueva."
            ),
        }
    # Solicitud de operación a mercado (DEAL) con SL, deslizamiento adaptado al activo y comentario trazable.
    info = mt5.symbol_info(d["simbolo"])
    solicitud = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": d["simbolo"], "volume": d["volumen"], "type": d["tipo"],
        "price": d["precio"], "sl": d["sl"], "deviation": _desviacion(info), "magic": MAGIC,
        "comment": f"agente-ia:{o['id']}", "type_time": mt5.ORDER_TIME_GTC, "type_filling": _modo_llenado(info),
    }
    # El take profit es opcional: solo se incluye si existe.
    if d["tp"] is not None:
        solicitud["tp"] = d["tp"]
    resultado = _interpretar(mt5.order_send(solicitud), f"{d['lado']} {d['volumen']} {d['simbolo']}")
    if resultado.get("ok"):
        # Se anota que esta posición la abrió el agente y se pide registrarla pronto (copy trading).
        registro_operaciones.anotar_origen(resultado.get("ticket"), "agente")
        registro_operaciones.sincronizar_en_segundo_plano(forzar=True)
    return resultado


# TITULO ENVIAR CIERRE

@_con_candado
def _enviar_cierre(o: dict[str, Any]) -> dict[str, Any]:
    """Envía a MT5 el cierre total de la posición indicada en `ticket_objetivo` de la orden.

    Cerrar solo exige MT5 listo y cuenta demo. Envía una operación contraria sobre la misma posición al precio
    bid (si era compra) o ask. Devuelve el diccionario de _interpretar o un error si la posición ya no existe
    o no hay precio. Efecto: llamada order_send a MT5, bajo MT5_LOCK."""
    # Cerrar no aplica los límites de apertura (interruptor, pérdida diaria, tope de posiciones).
    _, motivo = _chequeos_globales(para_abrir=False)
    if motivo:
        return {"ok": False, "estado": "RECHAZADA_RIESGO", "mensaje": motivo}
    posiciones = mt5.positions_get(ticket=_tk(o["ticket_objetivo"]))
    if not posiciones:
        return {"ok": False, "estado": "ERROR", "mensaje": "La posición ya no existe (¿se cerró antes?)."}
    # Para cerrar se opera en sentido contrario al de la posición.
    p = posiciones[0]
    es_compra = p.type == mt5.POSITION_TYPE_BUY
    tick = mt5.symbol_info_tick(p.symbol)
    if tick is None:
        return {"ok": False, "estado": "ERROR", "mensaje": f"Sin precio disponible para {p.symbol}."}
    info_cierre = mt5.symbol_info(p.symbol)
    solicitud = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume,
        "type": mt5.ORDER_TYPE_SELL if es_compra else mt5.ORDER_TYPE_BUY, "position": p.ticket,
        "price": tick.bid if es_compra else tick.ask, "deviation": _desviacion(info_cierre), "magic": MAGIC,
        "comment": f"agente-ia:{o['id']}", "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": _modo_llenado(info_cierre),
    }
    return _interpretar(mt5.order_send(solicitud), f"cierre de la posición de {p.symbol}")


# TITULO INTERPRETAR

def _interpretar(resultado: Any, descripcion: str) -> dict[str, Any]:
    """Traduce la respuesta de order_send a un diccionario {ok, mensaje, ticket | estado}.

    Recibe el resultado de MT5 (o None si no respondió) y un texto descriptivo de la operación. Considera éxito
    los códigos DONE y DONE_PARTIAL (este último se señala como ejecución parcial)."""
    if resultado is None:
        return {"ok": False, "estado": "ERROR", "mensaje": f"{NOMBRE_BROKER} no respondió: {mt5.last_error()}"}
    if resultado.retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_DONE_PARTIAL):
        return {
            "ok": False, "estado": "ERROR",
            "mensaje": f"{NOMBRE_BROKER} rechazó la orden (código {resultado.retcode}): {resultado.comment}",
        }
    parcial = " (ejecución parcial)" if resultado.retcode == mt5.TRADE_RETCODE_DONE_PARTIAL else ""
    # El ticket de Capital.com es un dealId largo: se muestra solo si es corto (número de MetaTrader 5).
    ticket = f" (ticket #{resultado.order})" if len(str(resultado.order)) <= 12 else ""
    return {
        "ok": True, "ticket": resultado.order,
        "mensaje": f"Ejecutado{parcial}: {descripcion} a {resultado.price}{ticket}.",
    }


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara envio .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
