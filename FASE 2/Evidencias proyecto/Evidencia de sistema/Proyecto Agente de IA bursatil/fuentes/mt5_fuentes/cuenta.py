# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara cuenta .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Consultas de la cuenta: resumen, posiciones abiertas, órdenes pendientes e historial de operaciones.

Todas son de SOLO LECTURA: abren una sesión con candado (`_sesion`), consultan
MT5 y devuelven diccionarios simples listos para el modelo o el dashboard.
Lanzan ErrorMT5 ante fallos de conexión o de consulta."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fuentes.mt5_fuentes.conexion import _ES_CAPITAL, _sesion
from fuentes.mt5_fuentes.constantes import NOMBRE_FUENTE
from fuentes.mt5_fuentes.errores import ErrorMT5
from fuentes.mt5_fuentes.utiles import _como_tupla, _hora_utc, _nivel, _num, _resolver


# TITULO CUENTA

def cuenta() -> dict[str, Any]:
    """Devuelve el resumen de la cuenta abierta en el terminal de MT5.

    Incluye tipo (DEMO/REAL), moneda, balance, equidad, beneficio flotante,
    margen usado y libre, nivel de margen (%), apalancamiento y la hora de
    consulta en UTC. Lee `account_info()` de MT5; lanza ErrorMT5 si no hay
    cuenta iniciada. Nota: incluye datos sensibles; para entregarlos a un
    usuario hay que verificar antes que la cuenta le pertenece."""
    with _sesion() as mt5:
        c = mt5.account_info()
        if c is None:
            raise ErrorMT5(f"No hay una cuenta iniciada en {NOMBRE_FUENTE}.")
        return {
            "fuente": NOMBRE_FUENTE,
            # trade_mode 0 = cuenta demo; cualquier otro valor se informa como REAL.
            "tipo": "DEMO" if getattr(c, "trade_mode", 0) == 0 else "REAL",
            "moneda": getattr(c, "currency", "USD"),
            "balance": _num(getattr(c, "balance", None), 2),
            "equidad": _num(getattr(c, "equity", None), 2),
            "beneficio_flotante": _num(getattr(c, "profit", None), 2),
            "margen_usado": _num(getattr(c, "margin", None), 2),
            "margen_libre": _num(getattr(c, "margin_free", None), 2),
            "nivel_margen_pct": _num(getattr(c, "margin_level", None), 2),
            "apalancamiento": getattr(c, "leverage", None),
            "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


# TITULO POSICIONES

def posiciones(simbolo: str | None = None) -> dict[str, Any]:
    """Lista las posiciones abiertas, opcionalmente filtradas por símbolo.

    Recibe un símbolo (se resuelve con alias, p. ej. 'oro') o None para todas.
    Devuelve el total y, por posición: ticket, símbolo, tipo (COMPRA/VENTA),
    lotes, precio de apertura y actual, SL, TP (None si no hay), beneficio y
    swap. Consulta `positions_get` de MT5."""
    with _sesion() as mt5:
        # Si se pidió un símbolo, se traduce al nombre exacto que usa el broker.
        sym = _resolver(mt5, simbolo) if simbolo else None
        posicion_tuple = mt5.positions_get(symbol=sym) if sym else mt5.positions_get()
        # MT5 devuelve None cuando no hay posiciones; se normaliza a tupla vacía (o error real).
        posicion_tuple = _como_tupla(mt5, posicion_tuple, "obtener posiciones")

        resultado = []
        for p in posicion_tuple:
            resultado.append({
                "ticket": getattr(p, "ticket", None),
                "simbolo": getattr(p, "symbol", None),
                # En MT5, type 0 = compra y 1 = venta.
                "tipo": "COMPRA" if getattr(p, "type", 0) == 0 else "VENTA",
                "lotes": _num(getattr(p, "volume", None)),
                "precio_apertura": _num(getattr(p, "price_open", None)),
                "precio_actual": _num(getattr(p, "price_current", None)),
                "sl": _nivel(getattr(p, "sl", None)),
                "tp": _nivel(getattr(p, "tp", None)),
                "beneficio": _num(getattr(p, "profit", None)),
                "swap": _num(getattr(p, "swap", None)),
            })

        return {
            "fuente": NOMBRE_FUENTE,
            "total_posiciones": len(resultado),
            "posiciones": resultado,
            "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


# TITULO ORDENES PENDIENTES

def ordenes_pendientes(simbolo: str | None = None) -> dict[str, Any]:
    """Lista las órdenes pendientes (límite y stop), opcionalmente filtradas por símbolo.

    Recibe un símbolo (con resolución de alias) o None para todas. Devuelve el
    total y, por orden: ticket, símbolo, tipo (BUY LIMIT, SELL LIMIT, BUY STOP,
    SELL STOP o TIPO_n si es otro), lotes, precio de la orden, SL y TP. Consulta
    `orders_get` de MT5."""
    with _sesion() as mt5:
        sym = _resolver(mt5, simbolo) if simbolo else None
        ordenes = mt5.orders_get(symbol=sym) if sym else mt5.orders_get()
        ordenes = _como_tupla(mt5, ordenes, "obtener órdenes pendientes")

        resultado = []
        # Códigos ORDER_TYPE de MT5 para órdenes pendientes -> nombre legible.
        tipos_orden = {2: "BUY LIMIT", 3: "SELL LIMIT", 4: "BUY STOP", 5: "SELL STOP"}
        for o in ordenes:
            t = getattr(o, "type", -1)
            resultado.append({
                "ticket": getattr(o, "ticket", None),
                "simbolo": getattr(o, "symbol", None),
                "tipo": tipos_orden.get(t, f"TIPO_{t}"),
                "lotes": _num(getattr(o, "volume_initial", None)),
                "precio_orden": _num(getattr(o, "price_open", None)),
                "sl": _nivel(getattr(o, "sl", None)),
                "tp": _nivel(getattr(o, "tp", None)),
            })

        return {
            "fuente": NOMBRE_FUENTE,
            "total_ordenes": len(resultado),
            "ordenes": resultado,
            "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


# TITULO DETALLES CAPITAL

# Consultas nuevas a Capital.com por llamada para completar operaciones cerradas (cada una cuesta una petición).
_CONSULTAS_NUEVAS = 6


def _detalles_capital(deals: Any, cuantas: int) -> dict[Any, dict[str, Any]]:
    """Con Capital.com, completa las operaciones más recientes con símbolo, lado, lotes y precio de salida.

    El historial de Capital solo trae el nombre del instrumento en texto y el resultado; el detalle sale de la actividad de cada
    posición. Se completan las `cuantas` más recientes con el detalle ya guardado y, como mucho, `_CONSULTAS_NUEVAS` consultas nuevas por
    llamada (el resto se completa en las siguientes). Devuelve {id de la posición: detalle}; vacío con MetaTrader 5."""
    if not _ES_CAPITAL:
        return {}
    from herramientas.backends import capital as cap
    detalles: dict[Any, dict[str, Any]] = {}
    nuevas = 0
    for d in reversed(list(deals)[-max(1, cuantas):]):
        posicion, hora = getattr(d, "position_id", ""), getattr(d, "time", 0)
        detalle = cap.detalle_operacion(posicion, hora, consultar=False)
        if not detalle and nuevas < _CONSULTAS_NUEVAS:
            nuevas += 1
            detalle = cap.detalle_operacion(posicion, hora)
        if detalle:
            detalles[posicion] = detalle
    return detalles


# TITULO HISTORIAL OPERACIONES

def historial_operaciones(dias: int = 30, simbolo: str | None = None, ultimas: int = 15) -> dict[str, Any]:
    """Resume el historial de operaciones cerradas de los últimos `dias` días.

    Recibe los días a revisar (mínimo 1), un símbolo opcional para filtrar y
    cuántas operaciones recientes detallar (`ultimas`; 0 no devuelve detalle).
    Recorre los deals de MT5 (`history_deals_get`), considera solo los de
    salida y calcula total, ganadoras, perdedoras, tasa de acierto (%) y
    beneficio neto. Devuelve ese resumen más el detalle de las últimas
    operaciones."""
    with _sesion() as mt5:
        # Ventana de tiempo: desde (ahora - dias) hasta ahora, en UTC.
        hasta = datetime.now(timezone.utc)
        desde = hasta - timedelta(days=max(1, dias))
        simbolo_filter = _resolver(mt5, simbolo) if simbolo else None

        deals = mt5.history_deals_get(desde, hasta)
        deals = _como_tupla(mt5, deals, "obtener historial de operaciones")

        # Con Capital.com se completan primero las operaciones recientes (o todas si se filtra por símbolo, hasta 30).
        detalles = _detalles_capital(deals, 30 if simbolo_filter else ultimas)
        operaciones = []
        lucro_total = 0.0
        ganadoras = 0
        perdedoras = 0

        for d in deals:
            entry = getattr(d, "entry", None)
            deal_simbolo = getattr(d, "symbol", None)
            detalle = detalles.get(getattr(d, "position_id", ""))
            if detalle:
                deal_simbolo = detalle["epic"]
            # entry 1 = salida (OUT) y 2 = inversión (INOUT): son los deals que cierran una posición.
            if entry in (1, 2):
                if simbolo_filter and deal_simbolo != simbolo_filter:
                    continue

                profit = _num(getattr(d, "profit", 0.0)) or 0.0
                lucro_total += profit

                # Operaciones con beneficio exactamente 0 no cuentan como ganadoras ni perdedoras.
                if profit > 0:
                    ganadoras += 1
                elif profit < 0:
                    perdedoras += 1

                if _ES_CAPITAL and not detalle:
                    # Sin el detalle de Capital no se conoce el lado, los lotes ni el precio: se informa en vez de inventarlos.
                    operaciones.append({
                        "ticket": getattr(d, "ticket", None), "simbolo": deal_simbolo, "tipo": None, "lotes": None,
                        "precio": None, "beneficio": profit, "fecha_utc": _hora_utc(getattr(d, "time", 0), mt5),
                        "detalle_pendiente": True,
                    })
                    continue
                operaciones.append({
                    "ticket": getattr(d, "ticket", None),
                    "simbolo": deal_simbolo,
                    "tipo": ("COMPRA" if detalle["tipo"] == "Compra" else "VENTA") if detalle
                    else ("COMPRA" if getattr(d, "type", 0) == 0 else "VENTA"),
                    "lotes": _num(detalle["volumen"] if detalle else getattr(d, "volume", None)),
                    "precio": _num(detalle["salida"] if detalle else getattr(d, "price", None)),
                    "beneficio": profit,
                    "fecha_utc": _hora_utc(getattr(d, "time", 0), mt5),
                })

        # Tasa de acierto sobre las operaciones con resultado distinto de cero.
        total_operaciones = ganadoras + perdedoras
        win_rate = (ganadoras / total_operaciones * 100) if total_operaciones > 0 else 0.0

        return {
            "fuente": NOMBRE_FUENTE,
            "dias_consultados": dias,
            "resumen": {
                "total_operaciones": total_operaciones,
                "ganadoras": ganadoras,
                "perdedoras": perdedoras,
                "tasa_acierto_pct": round(win_rate, 2),
                "beneficio_neto_total": round(lucro_total, 2),
            },
            "ultimas_operaciones": operaciones[-ultimas:] if ultimas > 0 else [],
            "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara cuenta .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
