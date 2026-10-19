# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara propuestas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""API para el AGENTE: solo proponer / consultar. NADA se ejecuta aquí.

Las herramientas del agente (herramientas/ordenes_herramientas) llaman a estas funciones. Cada propuesta
válida queda PENDIENTE en SQLite hasta que el usuario la confirme; las rechazadas también se guardan como
auditoría. El motor de vigilancia las reutiliza con origen="automatica"."""
from dataclasses import asdict
from typing import Any

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from core.ordenes.base_datos import _ahora, _consultar, _insertar, kill_switch_activo
from core.ordenes.limites import LIMITES
from core.ordenes.mt5_utiles import (_chequeos_globales, _con_lock, _perdida_del_dia, _preparar_mt5,
                                     _resolver_simbolo, _riesgo_expuesto)
from core.ordenes.validacion import _evaluar_apertura


def _propuesta_pendiente(accion: str, **filtros: Any) -> str | None:
    """id de una propuesta PENDIENTE (no vencida) con esa acción y esos campos, o None."""
    condiciones = "".join(f" AND {campo} = ?" for campo in filtros)  # los nombres de campo son fijos, no vienen del agente
    filas = _consultar(
        f"SELECT id FROM ordenes WHERE estado = 'PENDIENTE' AND accion = ? AND expira > ?{condiciones} "
        "ORDER BY creada LIMIT 1",
        (accion, _ahora(), *filtros.values()),
    )
    return filas[0]["id"] if filas else None


def _respuesta_duplicada(id_: str) -> dict[str, Any]:
    """Construye la respuesta para el modelo cuando ya existe una propuesta pendiente igual (con su id)
    e instruye no volver a proponerla."""
    return {
        "estado": "PROPUESTA_DUPLICADA",
        "id": id_,
        "mensaje": (
            "Ya existe una propuesta pendiente igual (no se creó otra). No vuelvas a proponerla: dile al "
            "usuario que la confirme o la rechace en el panel de órdenes propuestas."
        ),
    }


@_con_lock
def proponer_apertura(
    simbolo: str, lado: str, stop_loss: Any, take_profit: Any, riesgo_pct: float, justificacion: str,
    origen: str = "agente", vigilancia_id: str | None = None,
) -> dict[str, Any]:
    """Registra una propuesta de apertura PENDIENTE de confirmación (no envía nada a MT5).

    Recibe símbolo, lado, SL, TP, riesgo en % del equity, justificación, el origen ("agente" o "automatica") y
    el id de la vigilancia si aplica. Aplica los chequeos globales, evita duplicados y valida con
    _evaluar_apertura. Si algo falla guarda la orden como RECHAZADA_RIESGO (auditoría) y devuelve
    {"estado": "RECHAZADA", "motivo"}; si todo va bien devuelve {"estado": "PROPUESTA_PENDIENTE", "id",
    "resumen", "mensaje"}. Efecto: inserta filas en SQLite y consulta MT5."""
    # Paso 1: chequeos globales y detección de propuesta duplicada (mismo símbolo y lado).
    cuenta, motivo = _chequeos_globales(para_abrir=True)
    if not motivo:
        previa = _propuesta_pendiente("abrir", simbolo=_resolver_simbolo(simbolo), lado=str(lado).strip().lower())
        if previa:
            return _respuesta_duplicada(previa)
    # Paso 2: validación completa de la apertura (solo si no hay motivo previo).
    ev: dict[str, Any] | None = None
    if not motivo:
        ev = _evaluar_apertura(cuenta, simbolo, lado, stop_loss, take_profit, riesgo_pct)
        if ev is not None and not ev["ok"]:
            motivo = ev["motivo"]

    # Rechazo: se guarda con su motivo para la auditoría y se informa al modelo.
    if motivo:
        _insertar(
            estado="RECHAZADA_RIESGO", accion="abrir", simbolo=_resolver_simbolo(simbolo), lado=str(lado).lower(),
            justificacion=justificacion, detalle=motivo, origen=origen, vigilancia_id=vigilancia_id,
        )
        return {"estado": "RECHAZADA", "motivo": motivo}

    # Paso 3: propuesta válida; se guarda PENDIENTE con los datos calculados (volumen, precio de referencia, riesgo).
    assert ev is not None and ev["ok"]
    d = ev["datos"]
    id_ = _insertar(
        estado="PENDIENTE", accion="abrir", simbolo=d["simbolo"], lado=d["lado"], volumen=d["volumen"],
        precio_ref=d["precio"], sl=d["sl"], tp=d["tp"], riesgo_dinero=d["riesgo_dinero"],
        riesgo_pct=d["riesgo_pct"], justificacion=justificacion, origen=origen, vigilancia_id=vigilancia_id,
    )
    return {
        "estado": "PROPUESTA_PENDIENTE",
        "id": id_,
        "resumen": {
            "simbolo": d["simbolo"], "lado": d["lado"], "volumen": d["volumen"],
            "precio_referencia": d["precio"], "stop_loss": d["sl"], "take_profit": d["tp"],
            "riesgo": f"{d['riesgo_dinero']:.2f} {d['moneda']} ({d['riesgo_pct']:.2f}% del equity)",
            "vigencia_minutos": LIMITES.vigencia_propuesta_min,
        },
        "mensaje": (
            "Propuesta registrada, pero NO está ejecutada: el usuario debe confirmarla con el botón del "
            "dashboard. No afirmes que la orden fue enviada o ejecutada; di que queda pendiente de su confirmación."
        ),
    }


@_con_lock
def proponer_cierre(
    ticket: Any, justificacion: str, origen: str = "agente", vigilancia_id: str | None = None,
) -> dict[str, Any]:
    """Registra una propuesta de cierre de una posición abierta, PENDIENTE de confirmación.

    Recibe el ticket (se convierte a entero), la justificación, el origen y la vigilancia. Comprueba MT5 y
    cuenta demo, evita duplicados y verifica que la posición exista. Devuelve {"estado": "RECHAZADA", "motivo"}
    (guardada como auditoría) o {"estado": "PROPUESTA_PENDIENTE", "id", "resumen", "mensaje"}.
    Efecto: inserta una fila en SQLite; no cierra nada."""
    cuenta, motivo = _chequeos_globales(para_abrir=False)

    def rechazo(txt: str) -> dict[str, Any]:
        """Guarda una orden de cierre RECHAZADA_RIESGO con el motivo y devuelve la respuesta de rechazo."""
        _insertar(estado="RECHAZADA_RIESGO", accion="cerrar", justificacion=justificacion, detalle=txt,
                  origen=origen, vigilancia_id=vigilancia_id)
        return {"estado": "RECHAZADA", "motivo": txt}

    if motivo:
        return rechazo(motivo)
    try:
        ticket = int(ticket)
    except (TypeError, ValueError):
        return rechazo("El ticket debe ser un número entero (usa ver_posiciones para consultarlo).")
    previa = _propuesta_pendiente("cerrar", ticket_objetivo=ticket)
    if previa:
        return _respuesta_duplicada(previa)
    posiciones = mt5.positions_get(ticket=ticket)
    if not posiciones:
        return rechazo(f"No existe una posición abierta con ticket {ticket}.")

    # Precio de referencia: el de cierre (bid para una compra, ask para una venta).
    p = posiciones[0]
    es_compra = p.type == mt5.POSITION_TYPE_BUY
    tick = mt5.symbol_info_tick(p.symbol)
    precio = (tick.bid if es_compra else tick.ask) if tick else p.price_current
    id_ = _insertar(
        estado="PENDIENTE", accion="cerrar", simbolo=p.symbol, lado="compra" if es_compra else "venta",
        volumen=p.volume, precio_ref=precio, sl=p.sl or None, tp=p.tp or None,
        riesgo_dinero=p.profit, ticket_objetivo=ticket, justificacion=justificacion,
        origen=origen, vigilancia_id=vigilancia_id,
    )
    return {
        "estado": "PROPUESTA_PENDIENTE",
        "id": id_,
        "resumen": {
            "accion": "cerrar posición", "ticket": ticket, "simbolo": p.symbol, "volumen": p.volume,
            "resultado_actual": f"{p.profit:.2f} {cuenta.currency}",
        },
        "mensaje": (
            "Propuesta de cierre registrada, pero NO está ejecutada: el usuario debe confirmarla con el botón "
            "del dashboard. No afirmes que la posición fue cerrada."
        ),
    }


@_con_lock
def resumen_posiciones() -> dict[str, Any]:
    """Devuelve el estado de la cuenta (tipo, balance, equity, margen libre, flotante) y las posiciones abiertas.

    Es solo lectura sobre MT5; si MT5 no está listo devuelve {"error": ...}."""
    error = _preparar_mt5()
    if error:
        return {"error": error}
    cuenta = mt5.account_info()
    if cuenta is None:
        return {"error": "No se pudo leer la cuenta de MetaTrader 5."}
    posiciones = [
        {
            "ticket": p.ticket, "simbolo": p.symbol,
            "tipo": "compra" if p.type == mt5.POSITION_TYPE_BUY else "venta",
            "volumen": p.volume, "precio_apertura": p.price_open, "precio_actual": p.price_current,
            "stop_loss": p.sl or None, "take_profit": p.tp or None, "resultado": round(p.profit, 2),
        }
        for p in (mt5.positions_get() or [])
    ]
    return {
        "cuenta": {
            "tipo": "demo" if cuenta.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else "REAL",
            "moneda": cuenta.currency, "balance": cuenta.balance, "equity": cuenta.equity,
            "margen_libre": cuenta.margin_free, "resultado_flotante": cuenta.profit,
        },
        "posiciones_abiertas": posiciones,
    }


@_con_lock
def estado_riesgo() -> dict[str, Any]:
    """Devuelve los límites de riesgo vigentes, el interruptor de emergencia y, si MT5 responde, la pérdida del día,
    el número de posiciones abiertas, el riesgo en juego (abiertas + pendientes) y la moneda."""
    out: dict[str, Any] = {"limites": asdict(LIMITES), "interruptor_emergencia": kill_switch_activo()}
    error = _preparar_mt5()
    cuenta = None if error else mt5.account_info()
    if cuenta is not None:
        out["perdida_del_dia"] = round(_perdida_del_dia(cuenta), 2)
        out["posiciones_abiertas"] = len(mt5.positions_get() or [])
        out["riesgo_en_juego"] = round(_riesgo_expuesto(cuenta, incluir_pendientes=True), 2)  # abiertas + pendientes
        out["moneda"] = cuenta.currency
    return out


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara propuestas .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
