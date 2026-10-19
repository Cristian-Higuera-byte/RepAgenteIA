# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara validacion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Validación de una apertura (la usan la propuesta y, de nuevo, la confirmación) y utilidades de la vigilancia.

Contiene las reglas de riesgo en código: símbolos permitidos, dirección de SL/TP, distancia mínima, tamaño del
lote, riesgo por operación y total, y margen. Ninguna de estas reglas depende del prompt del modelo."""
import math
from typing import Any

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from core.ordenes.limites import LIMITES, TOLERANCIA_RIESGO
from core.ordenes.mt5_utiles import (_con_lock, _normalizar, _preparar_mt5, _resolver_simbolo, _riesgo_expuesto)


def _evaluar_apertura(
    cuenta: Any,
    simbolo: str,
    lado: str,
    stop_loss: Any,
    take_profit: Any,
    riesgo_pct: float | None,
    volumen_fijo: float | None = None,
    incluir_pendientes: bool = True,
) -> dict[str, Any]:
    """Valida una apertura contra los límites de riesgo y calcula su tamaño.

    Recibe la cuenta de MT5, el símbolo, el lado ("compra"/"venta"), stop loss y take profit, el riesgo
    deseado en % del equity y, opcionalmente, un volumen fijo (se usa al confirmar para reevaluar el mismo
    lote) y si se suman las propuestas pendientes al riesgo total. Devuelve {"ok": False, "motivo"} al
    primer incumplimiento o {"ok": True, "datos": {...}} con símbolo real, volumen, precio, SL, TP, riesgo
    en dinero y en % y moneda. Efectos: selecciona el símbolo en MT5 y consulta precios, cálculo de
    ganancia y de margen; no envía nada."""
    def no(motivo: str) -> dict[str, Any]:
        """Construye la respuesta de rechazo con el motivo dado."""
        return {"ok": False, "motivo": motivo}

    # Paso 1: traducir el símbolo al nombre del bróker y comprobar lista blanca / lista negra.
    sym = _resolver_simbolo(simbolo)
    pedido = {sym.upper(), _normalizar(simbolo)}
    if LIMITES.simbolos_permitidos is not None and not (pedido & {s.upper() for s in LIMITES.simbolos_permitidos}):
        return no(f"'{sym}' no está entre los símbolos permitidos: {', '.join(LIMITES.simbolos_permitidos)}.")
    if pedido & {s.upper() for s in LIMITES.simbolos_bloqueados}:
        return no(f"'{sym}' está bloqueado para operar con el agente.")

    # Paso 2: normalizar el lado.
    lado = (lado or "").strip().lower()
    if lado not in ("compra", "venta"):
        return no("'lado' debe ser 'compra' o 'venta'.")
    es_compra = lado == "compra"

    # Paso 3: el stop loss es obligatorio; el take profit es opcional.
    try:
        sl = float(stop_loss)
    except (TypeError, ValueError):
        return no("El stop loss es obligatorio y debe ser un precio numérico.")
    tp: float | None = None
    if take_profit not in (None, "", 0):
        try:
            tp = float(take_profit)
        except (TypeError, ValueError):
            return no("El take profit debe ser un precio numérico.")

    # Paso 4: el símbolo debe existir y estar operable (se añade a la Observación de mercado).
    mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    if info is None:
        return no(f"El símbolo '{sym}' no existe en MetaTrader 5. Busca el nombre exacto con la búsqueda de "
                  "símbolos (mt5_buscar_simbolos) antes de volver a proponer.")
    if info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
        return no(f"'{sym}' no está disponible para operar en este momento (mercado cerrado o restringido).")

    # Precio de entrada: ask para comprar, bid para vender.
    tick = mt5.symbol_info_tick(sym)
    precio = (tick.ask if es_compra else tick.bid) if tick else 0.0
    if not precio:
        return no(f"No hay precio disponible para '{sym}' ahora mismo.")

    # Dirección de SL / TP respecto al precio (compra: SL abajo y TP arriba; venta: al revés).
    if es_compra and not sl < precio:
        return no(f"En una compra el stop loss debe estar por DEBAJO del precio ({precio}).")
    if not es_compra and not sl > precio:
        return no(f"En una venta el stop loss debe estar por ENCIMA del precio ({precio}).")
    if tp is not None:
        if es_compra and not tp > precio:
            return no(f"En una compra el take profit debe estar por ENCIMA del precio ({precio}).")
        if not es_compra and not tp < precio:
            return no(f"En una venta el take profit debe estar por DEBAJO del precio ({precio}).")

    # Distancia mínima que exige el broker (stops level en puntos).
    dist_min = info.trade_stops_level * info.point
    if abs(precio - sl) < dist_min or (tp is not None and abs(tp - precio) < dist_min):
        return no(f"SL/TP demasiado cerca del precio: el broker exige al menos {dist_min:.{info.digits}f} de distancia.")

    # Paso 5: pérdida en dinero de 1 lote si salta el SL (base para dimensionar el volumen).
    tipo = mt5.ORDER_TYPE_BUY if es_compra else mt5.ORDER_TYPE_SELL
    perdida_1_lote = mt5.order_calc_profit(tipo, sym, 1.0, precio, sl)
    if not perdida_1_lote:
        return no("No se pudo calcular el riesgo de la operación en MetaTrader 5.")
    perdida_1_lote = abs(perdida_1_lote)

    # Paso 6: volumen. Sin volumen fijo se calcula desde el riesgo pedido; con volumen fijo se respeta.
    if volumen_fijo is None:
        if riesgo_pct is None or riesgo_pct <= 0:
            return no("'riesgo_pct' debe ser mayor que 0.")
        if riesgo_pct > LIMITES.riesgo_max_por_operacion_pct:
            return no(
                f"El riesgo pedido ({riesgo_pct}%) supera el máximo permitido por operación "
                f"({LIMITES.riesgo_max_por_operacion_pct}%)."
            )
        # Se redondea hacia abajo al paso de volumen y se limita al máximo del bróker y de LIMITES.
        paso = info.volume_step or 0.01
        decimales = max(0, int(round(-math.log10(paso))))
        volumen = (cuenta.equity * riesgo_pct / 100) / perdida_1_lote
        volumen = math.floor(volumen / paso + 1e-9) * paso
        volumen = round(min(volumen, info.volume_max, LIMITES.volumen_max), decimales)
        if volumen < info.volume_min:
            return no(
                f"Con {riesgo_pct}% de riesgo y ese stop loss no alcanza ni el lote mínimo "
                f"({info.volume_min}). Acerca el stop loss o sube el riesgo (máx. "
                f"{LIMITES.riesgo_max_por_operacion_pct}%)."
            )
    else:
        volumen = float(volumen_fijo)

    # Paso 7: riesgo real de esta operación frente al máximo por operación (con tolerancia por movimiento de precio).
    riesgo_dinero = volumen * perdida_1_lote
    riesgo_pct_real = riesgo_dinero / cuenta.equity * 100
    if riesgo_pct_real > LIMITES.riesgo_max_por_operacion_pct * TOLERANCIA_RIESGO:
        return no(
            f"Con el precio actual el riesgo sería {riesgo_pct_real:.2f}%, sobre el máximo permitido "
            f"({LIMITES.riesgo_max_por_operacion_pct}%)."
        )

    # Paso 8: riesgo total en juego (abiertas + pendientes + esta) frente al máximo total.
    expuesto = _riesgo_expuesto(cuenta, incluir_pendientes)
    total_pct = (expuesto + riesgo_dinero) / cuenta.equity * 100
    if total_pct > LIMITES.riesgo_max_total_pct * TOLERANCIA_RIESGO:
        return no(
            f"Riesgo total demasiado alto: con esta operación quedaría {total_pct:.2f}% del equity en riesgo "
            f"(posiciones abiertas y propuestas pendientes incluidas; máximo {LIMITES.riesgo_max_total_pct}%). "
            "Cierra posiciones, rechaza propuestas pendientes o reduce el riesgo."
        )

    # Paso 9: margen libre suficiente.
    margen = mt5.order_calc_margin(tipo, sym, volumen, precio)
    if margen is not None and margen > cuenta.margin_free:
        return no(f"Margen libre insuficiente (se necesitan {margen:.2f}, hay {cuenta.margin_free:.2f}).")

    return {
        "ok": True,
        "datos": {
            "simbolo": sym, "lado": lado, "tipo": tipo, "volumen": volumen, "precio": precio,
            "sl": sl, "tp": tp, "riesgo_dinero": riesgo_dinero, "riesgo_pct": riesgo_pct_real,
            "moneda": cuenta.currency,
        },
    }


@_con_lock
def validar_simbolo(simbolo: str) -> dict[str, Any]:
    """Comprueba que un símbolo se puede operar: existe en MT5, está permitido (si hay lista) y no está
    bloqueado. Devuelve {"ok": True, "simbolo": nombre_real} o {"ok": False, "motivo": ...}.
    Mismas reglas que _evaluar_apertura; se usa para rechazar una vigilancia antes de crearla."""
    sym = _resolver_simbolo(simbolo)
    pedido = {sym.upper(), _normalizar(simbolo)}
    if not sym:
        return {"ok": False, "motivo": "Indica el símbolo del activo."}
    if LIMITES.simbolos_permitidos is not None and not (pedido & {s.upper() for s in LIMITES.simbolos_permitidos}):
        return {"ok": False, "motivo": f"'{sym}' no está entre los símbolos permitidos: {', '.join(LIMITES.simbolos_permitidos)}."}
    if pedido & {s.upper() for s in LIMITES.simbolos_bloqueados}:
        return {"ok": False, "motivo": f"'{sym}' está bloqueado para operar con el agente."}
    mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    if info is None:
        return {"ok": False, "motivo": f"El símbolo '{sym}' no existe en MetaTrader 5. Busca el nombre exacto "
                                       "con la búsqueda de símbolos (mt5_buscar_simbolos)."}
    if info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
        return {"ok": False, "motivo": f"'{sym}' no está disponible para operar en este momento (mercado cerrado o restringido)."}
    return {"ok": True, "simbolo": sym}


@_con_lock
def cuenta_demo() -> tuple[Any, str | None]:
    """Devuelve (cuenta, motivo). motivo es None solo si MT5 responde Y la cuenta es DEMO. La operación automática
    exige demo SIEMPRE, aunque LIMITES.solo_demo se relaje para las propuestas manuales."""
    error = _preparar_mt5()
    if error:
        return None, error
    cuenta = mt5.account_info()
    if cuenta is None:
        return None, "No se pudo leer la cuenta de MetaTrader 5."
    if cuenta.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        return cuenta, "La operación automática solo está permitida en cuenta DEMO y la cuenta conectada no lo es."
    return cuenta, None


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara validacion .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
