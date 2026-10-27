# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara mercado .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Consultas de mercado: precio, velas, búsqueda de símbolos, especificación y riesgo de una posición.

Todas son de SOLO LECTURA: abren una sesión con candado (`_sesion`), resuelven
el símbolo (alias) y lo activan temporalmente en Market Watch si hace falta.
Devuelven diccionarios simples y lanzan ErrorMT5 ante cualquier fallo."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database.scripts.fuentes.mt5_fuentes.conexion import _sesion
from database.scripts.fuentes.mt5_fuentes.constantes import TIMEFRAMES
from database.scripts.fuentes.mt5_fuentes.errores import ErrorMT5
from database.scripts.fuentes.mt5_fuentes.utiles import (_como_tupla, _fecha_utc, _hora_utc, _num, _resolver, _simbolo_temporal,
                                        _tamano_pip, _tipo_orden)


def precio(simbolo: str) -> dict[str, Any]:
    """Devuelve el precio en tiempo real de un símbolo desde MT5.

    Recibe el símbolo (con alias). Devuelve bid, ask, spread en pips, máximo y
    mínimo del día, variación porcentual respecto a la apertura de la sesión y
    la hora del tick en UTC. Lanza ErrorMT5 si no se puede obtener el tick."""
    with _sesion() as mt5:
        sym = _resolver(mt5, simbolo)
        with _simbolo_temporal(mt5, sym) as info:
            tick = mt5.symbol_info_tick(sym)
            if tick is None or info is None:
                raise ErrorMT5(f"No fue posible obtener el precio en tiempo real para '{sym}'.")

            bid = tick.bid
            ask = tick.ask
            # Spread como diferencia de precios; 0 si falta alguno de los dos lados.
            spread = (ask - bid) if (ask and bid) else 0.0
            # Se usa el punto del símbolo (con valor por defecto) para expresar el spread en puntos.
            point = getattr(info, "point", 0.00001) or 0.00001
            spread_pips = round(spread / point, 1) if point > 0 else 0.0

            # Variación diaria respecto a la apertura de la sesión (o al bid si MT5 no la informa).
            open_price = getattr(info, "session_open", 0.0) or bid
            var_pct = round(((bid - open_price) / open_price * 100), 2) if open_price else 0.0

            return {
                "fuente": "MetaTrader 5",
                "simbolo": sym,
                "bid": _num(bid),
                "ask": _num(ask),
                "spread_pips": spread_pips,
                "maximo_dia": _num(getattr(info, "high", None)),
                "minimo_dia": _num(getattr(info, "low", None)),
                "variacion_pct": var_pct,
                "fecha_utc": _hora_utc(tick.time, mt5),
            }


def resultado_si_precio(simbolo: str, tipo: str, lotes: float, desde: float, hasta: float) -> float | None:
    """Ganancia (+) o pérdida (-) en la moneda de la cuenta si el precio pasa de `desde` a `hasta`.

    Lo calcula el propio MT5 (order_calc_profit), así que respeta el tamaño de contrato, el valor del
    tick y la conversión de divisas de cada activo. None si MT5 no puede calcularlo.
    """
    with _sesion() as mt5:
        sym = _resolver(mt5, simbolo)
        with _simbolo_temporal(mt5, sym):
            # tipo se traduce a ORDER_TYPE_BUY/SELL; los números se fuerzan a float por seguridad.
            valor = mt5.order_calc_profit(_tipo_orden(mt5, tipo), sym, float(lotes), float(desde), float(hasta))
    return _num(valor, 2) if valor is not None else None


def especificacion_simbolo(simbolo: str) -> dict[str, Any]:
    """Tamaño de pip, valor de 1 pip por lote (moneda de la cuenta) y límites de lotaje del símbolo.

    Recibe el símbolo (con alias). El valor del pip se calcula pidiendo a MT5 la
    ganancia de 1 lote de compra al moverse un pip desde el bid actual; es None
    si no hay precio de referencia. Devuelve también dígitos, lote mínimo,
    máximo y paso de lote."""
    with _sesion() as mt5:
        sym = _resolver(mt5, simbolo)
        with _simbolo_temporal(mt5, sym) as info:
            tick = mt5.symbol_info_tick(sym)
            # Precio de referencia: bid del tick o, si no hay, el bid de la información del símbolo.
            ref = float(getattr(tick, "bid", 0) or getattr(info, "bid", 0) or 0)
            pip = _tamano_pip(info)
            valor_pip = None
            if ref > 0 and pip > 0:
                v = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, sym, 1.0, ref, ref + pip)
                valor_pip = _num(v, 4) if v is not None else None
            return {
                "simbolo": sym,
                "tamano_pip": pip,
                "digitos": getattr(info, "digits", None),
                "valor_pip_por_lote": valor_pip,
                "lote_minimo": getattr(info, "volume_min", None),
                "lote_maximo": getattr(info, "volume_max", None),
                "paso_lote": getattr(info, "volume_step", None),
            }


def distancias_y_riesgo(
    simbolo: str, tipo: str, lotes: float, precio_apertura: float, precio_actual: float,
    sl: float | None, tp: float | None,
) -> dict[str, Any]:
    """Distancia al stop/objetivo (en pips, desde la apertura y desde el precio actual) y su valor en dinero.

    `riesgo_usd` es lo que se pierde si salta el SL (0 si el SL ya asegura ganancia, que se informa en
    `ganancia_asegurada_usd`). Todo en la moneda de la cuenta, calculado por MT5.
    """
    esp = especificacion_simbolo(simbolo)
    pip = esp["tamano_pip"] or 0.0
    out: dict[str, Any] = {"tamano_pip": pip, "valor_pip_por_lote": esp["valor_pip_por_lote"]}

    def pips(a: float, b: float) -> float | None:
        """Distancia absoluta entre dos precios expresada en pips (1 decimal); None si el pip es 0."""
        return round(abs(a - b) / pip, 1) if pip else None

    # Bloque del stop loss: solo si hay SL definido (0 o None significa "sin SL").
    if sl:
        out["distancia_sl_desde_apertura_pips"] = pips(precio_apertura, sl)
        out["distancia_sl_desde_precio_actual_pips"] = pips(precio_actual, sl)
        out["distancia_sl_desde_precio_actual_pct"] = (
            round(abs(precio_actual - sl) / precio_actual * 100, 3) if precio_actual else None
        )
        # Resultado en dinero de ir de la apertura al SL: negativo = pérdida (riesgo), positivo = ganancia asegurada.
        r = resultado_si_precio(simbolo, tipo, lotes, precio_apertura, sl)
        out["riesgo_usd"] = round(max(0.0, -r), 2) if r is not None else None
        out["ganancia_asegurada_usd"] = round(max(0.0, r), 2) if r is not None else None
    # Bloque del take profit: solo si hay TP definido.
    if tp:
        out["distancia_tp_desde_apertura_pips"] = pips(precio_apertura, tp)
        out["distancia_tp_desde_precio_actual_pips"] = pips(precio_actual, tp)
        b = resultado_si_precio(simbolo, tipo, lotes, precio_apertura, tp)
        out["beneficio_objetivo_usd"] = round(max(0.0, b), 2) if b is not None else None
    return out


def velas(
    simbolo: str,
    timeframe: str = "H1",
    cantidad: int = 100,
    ultimas_velas: int = 20,
    desde: str | None = None,
    hasta: str | None = None,
) -> dict[str, Any]:
    """Obtiene velas históricas de MT5 y devuelve un resumen del rango más el detalle de las últimas.

    Recibe el símbolo, la temporalidad (clave de `TIMEFRAMES`, p. ej. 'H1'), la
    cantidad de velas a evaluar (modo "últimas N"), cuántas velas recientes
    detallar (`ultimas_velas`, 0 = ninguna) y, opcionalmente, un rango de fechas
    'AAAA-MM-DD' (`desde`/`hasta`; si hay `desde` se ignora `cantidad`; `hasta`
    por defecto es ahora). Devuelve total evaluado, precio inicial/final,
    máximo, mínimo, variación % del rango y el detalle OHLC con volumen. Lanza
    ErrorMT5 si la temporalidad es inválida o no hay datos."""
    if timeframe not in TIMEFRAMES:
        raise ErrorMT5(f"Timeframe inválido '{timeframe}'. Opciones: {list(TIMEFRAMES.keys())}")

    tf_val = TIMEFRAMES[timeframe]
    with _sesion() as mt5:
        sym = _resolver(mt5, simbolo)
        with _simbolo_temporal(mt5, sym):
            # Dos modos de consulta: por rango de fechas o por las últimas N velas desde la posición 0.
            if desde:
                dt_desde = _fecha_utc(desde, "desde")
                dt_hasta = _fecha_utc(hasta, "hasta") if hasta else datetime.now(timezone.utc)
                rates = mt5.copy_rates_range(sym, tf_val, dt_desde, dt_hasta)
            else:
                rates = mt5.copy_rates_from_pos(sym, tf_val, 0, max(1, cantidad))

            rates = _como_tupla(mt5, rates, "obtener velas")
            if len(rates) == 0:
                raise ErrorMT5(f"No hay datos de velas para {sym}.")

            # Cada vela es (tiempo, open, high, low, close, volumen, ...): se extraen cierres, máximos y mínimos.
            precios_cierre = [float(r[4]) for r in rates]
            maximos = [float(r[2]) for r in rates]
            minimos = [float(r[3]) for r in rates]

            # Variación del rango: del primer al último cierre.
            primer_cierre = precios_cierre[0]
            ultimo_cierre = precios_cierre[-1]
            var_pct = ((ultimo_cierre - primer_cierre) / primer_cierre * 100) if primer_cierre else 0.0

            # Solo se detallan las últimas velas para no inundar el contexto del modelo.
            detalle = []
            if ultimas_velas > 0:
                for r in rates[-ultimas_velas:]:
                    detalle.append({
                        "fecha_utc": _hora_utc(r[0], mt5),
                        "open": _num(r[1]),
                        "high": _num(r[2]),
                        "low": _num(r[3]),
                        "close": _num(r[4]),
                        "volumen": int(r[5]),
                    })

            return {
                "fuente": "MetaTrader 5",
                "simbolo": sym,
                "timeframe": timeframe,
                "total_velas_evaluadas": len(rates),
                "resumen_rango": {
                    "precio_inicial": primer_cierre,
                    "precio_ultimo": ultimo_cierre,
                    "maximo_periodo": max(maximos),
                    "minimo_periodo": min(minimos),
                    "variacion_total_pct": round(var_pct, 2),
                },
                "ultimas_velas": detalle,
                "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }


def buscar_simbolos(texto: str, max_resultados: int = 15) -> dict[str, Any]:
    """Busca símbolos del broker cuyo nombre o descripción contengan el texto dado.

    Recibe el texto (sin distinguir mayúsculas; vacío coincide con todos) y el
    máximo de resultados. Recorre `symbols_get()` de MT5 y devuelve, por
    coincidencia, símbolo, descripción y categoría (ruta en el árbol del
    broker), junto con el total encontrado."""
    with _sesion() as mt5:
        query = (texto or "").strip().upper()
        crudos = _como_tupla(mt5, mt5.symbols_get(), "listar los símbolos")

        coincidencias = []
        for s in crudos:
            sym = getattr(s, "name", "")
            desc = getattr(s, "description", "")
            # Coincidencia por subcadena en el nombre o en la descripción.
            if query in sym.upper() or query in desc.upper():
                coincidencias.append({
                    "simbolo": sym,
                    "descripcion": desc,
                    "categoria": getattr(s, "path", ""),
                })
                if len(coincidencias) >= max_resultados:
                    break

        return {
            "fuente": "MetaTrader 5",
            "busqueda": texto,
            "coincidencias_encontradas": len(coincidencias),
            "resultados": coincidencias,
        }


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara mercado .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
