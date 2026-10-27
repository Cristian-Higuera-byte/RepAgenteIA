# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------- INICIO Piña y Jara estadisticas_portafolio .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""
estadisticas_portafolio.py
-------------------
Agregador de estadísticas del portafolio para la vista "Resumen" (dashboard F).

Hace UNA lectura de la cuenta + posiciones abiertas + historial de operaciones de
MT5 y devuelve TODO calculado, para que la UI solo pinte. Todo sale de datos
reales de MT5 (no se inventan números):

  - Capital:                account_info (equity, balance, margen libre).
  - P&L diario / mensual:   realizado (cierres de history_deals por fecha) + flotante
                            (posiciones abiertas).
  - Comisiones y swaps:     campos `commission`/`fee`/`swap` de cada deal.
  - Exposición:             notional por activo (volumen x contract_size x precio) y
                            margen usado; largos vs cortos.
  - Riesgo:                 nivel de margen + pérdida máxima DEFINIDA (posiciones con
                            SL) y aviso de las que no tienen SL (riesgo indefinido).
  - Drawdown (balance):     reconstruido desde la curva de balance de los cierres.
  - Dividendos:             ajustes de dividendo (operaciones de balance de MT5).
  - Rentabilidad acumulada: equity frente al depósito inicial.
  - Serie de balance:       para dibujar la curva de equity/balance.

Limitaciones honestas (ver bitácora):
  - El drawdown de EQUITY real necesita registrar snapshots (MT5 no los guarda);
    aquí se entrega el de BALANCE, que solo cambia en cada cierre. El de equity se
    alimentará del log que escribe servidor_datos.py.
  - Los dividendos dependen de que el bróker genere el evento; en demo puede no
    haber ninguno, en cuyo caso `dividendos_total` = 0 y la UI lo indica.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

from herramientas.puente_mt5 import (MT5_LOCK, inicializar_mt5, obtener_info_cuenta,
                              obtener_posiciones, resolver_simbolo)
from herramientas import gestor_lista_activos as wl
from herramientas import almacen_capital

# MetaTrader5 es opcional: si no se puede importar, `mt5` queda en None y las
# funciones devuelven valores neutros (cero/vacío) en lugar de fallar.
try:
    from proveedores.selector_mt5 import mt5
except Exception:                      # pragma: no cover - MT5 solo en Windows con terminal
    mt5 = None


# TITULO INICIO DIA

def _inicio_dia() -> float:
    """Devuelve el epoch (hora local) de las 00:00 de hoy."""
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return hoy.timestamp()


# TITULO INICIO MES

def _inicio_mes() -> float:
    """Devuelve el epoch (hora local) de las 00:00 del primer día del mes actual."""
    hoy = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return hoy.timestamp()


# TITULO NETO DEAL

def _neto_deal(d) -> float:
    """P/G neto de un deal: profit + swap + comisión + fee (igual que la Cartera)."""
    return (float(getattr(d, "profit", 0.0) or 0.0)
            + float(getattr(d, "swap", 0.0) or 0.0)
            + float(getattr(d, "commission", 0.0) or 0.0)
            + float(getattr(d, "fee", 0.0) or 0.0))


# TITULO TAMANO CONTRATO

def _tamano_contrato(symbol: str) -> float:
    """Devuelve el tamaño de contrato del símbolo (para el notional de la exposición); 0.0 si MT5 no responde."""
    if mt5 is None:
        return 0.0
    try:
        with MT5_LOCK:
            info = mt5.symbol_info(symbol)
        return float(getattr(info, "trade_contract_size", 0.0) or 0.0) if info else 0.0
    except Exception:
        return 0.0


# TITULO VALOR PUNTO

def _valor_punto(symbol: str) -> tuple[float, float]:
    """Devuelve (k, point): k = valor de 1 unidad de precio por lote en moneda de cuenta
    (tick_value/tick_size); point = tamaño del punto. Sirve para el riesgo definido.

    Consulta `symbol_info` bajo el candado de MT5; devuelve (0.0, 0.0) ante cualquier fallo.
    """
    if mt5 is None:
        return 0.0, 0.0
    try:
        with MT5_LOCK:
            info = mt5.symbol_info(symbol)
        if not info:
            return 0.0, 0.0
        tradingview = float(getattr(info, "trade_tick_value", 0.0) or 0.0)
        marca_tiempo = float(getattr(info, "trade_tick_size", 0.0) or 0.0)
        k = (tradingview / marca_tiempo) if marca_tiempo else 0.0
        return k, float(getattr(info, "point", 0.0) or 0.0)
    except Exception:
        return 0.0, 0.0


# TITULO LEER DEALS

def _leer_deals(dias: int = 400):
    """Devuelve todos los deals de los últimos `dias` días (cierres + operaciones de balance).

    Usa un rango amplio para reconstruir la curva de balance y el depósito inicial.
    Consulta MT5 bajo su candado; devuelve lista vacía si no hay conexión o hay error.
    """
    if mt5 is None:
        return []
    try:
        with MT5_LOCK:
            if not inicializar_mt5():
                return []
            deals = mt5.history_deals_get(datetime.now() - timedelta(days=dias),
                                          datetime.now() + timedelta(days=1))
        return list(deals or [])
    except Exception:
        return []


# TITULO CALCULAR

def calcular(dias_curva: int = 3650) -> dict:
    """Devuelve el diccionario completo de estadísticas del portafolio para la vista Resumen.

    Recibe `dias_curva`, los días de historial de deals usados para reconstruir la
    curva de balance y el depósito inicial. Lee la cuenta, las posiciones abiertas y
    los deals de MT5 (con su candado) y los snapshots de `almacen_capital`; no escribe.
    Devuelve {"error": ...} si no hay cuenta; si no, un dict con las claves moneda,
    capital, pnl, comisiones, exposicion, riesgo, drawdown, dividendos, rentabilidad y curva.
    """
    # Paso 1: datos base de la cuenta (si MT5 falla, se devuelve el error tal cual).
    cuenta = obtener_info_cuenta()
    if "error" in cuenta:
        return {"error": cuenta["error"]}

    moneda = cuenta.get("currency", "USD")
    equity = float(cuenta.get("equity", 0.0) or 0.0)
    balance = float(cuenta.get("balance", 0.0) or 0.0)
    margen = float(cuenta.get("margin", 0.0) or 0.0)
    margen_libre = float(cuenta.get("margin_free", 0.0) or 0.0)
    margin_level = float(cuenta.get("margin_level", 0.0) or 0.0)

    # Paso 2: posiciones abiertas, historial de deals y fronteras de día/mes.
    posiciones = obtener_posiciones() or []
    deals = _leer_deals(dias_curva)

    inicio_dia, inicio_mes = _inicio_dia(), _inicio_mes()

    # ----- Realizado (cierres) por período + comisiones/swaps -----
    real_hoy = real_mes = real_total = 0.0
    comision_hoy = comision_mes = comision_total = 0.0
    swap_hoy = swap_mes = swap_total = 0.0
    dividendos_total = 0.0
    dividendos_mes = 0.0
    n_dividendos = 0
    n_cierres_hoy = n_cierres_mes = 0

    # Constantes de MT5 con valores por defecto por si el módulo no está disponible.
    DEAL_OUT = getattr(mt5, "DEAL_ENTRY_OUT", 1) if mt5 else 1
    TYPE_BALANCE = getattr(mt5, "DEAL_TYPE_BALANCE", 2) if mt5 else 2
    # MT5 tiene tipos de deal DEDICADOS para dividendos de CFDs de acciones; XM los
    # usa (no como balance genérico). Detectarlos por tipo es lo correcto; además se
    # mantiene el fallback por comentario en operaciones de balance (otros brókers).
    TIPOS_DIVIDENDO = {getattr(mt5, "DEAL_TYPE_DIVIDEND", 16) if mt5 else 16,
                       getattr(mt5, "DEAL_TYPE_DIVIDEND_FRANKED", 17) if mt5 else 17}

    curva = []   # (epoch, balance_acumulado) para la curva y el drawdown
    bal_acum = 0.0

    # Paso 3: recorrer los deals en orden cronológico clasificándolos (dividendo,
    # balance o cierre) para acumular P/G, costos y la curva de balance.
    for d in sorted(deals, key=lambda x: getattr(x, "time", 0)):
        t = float(getattr(d, "time", 0) or 0)
        tipo = getattr(d, "type", None)
        entry = getattr(d, "entry", None)
        comentario = str(getattr(d, "comment", "") or "").lower()

        monto = float(getattr(d, "profit", 0.0) or 0.0)

        # Dividendos: tipos de deal dedicados de MT5 (lo que usa XM).
        if tipo in TIPOS_DIVIDENDO:
            dividendos_total += monto
            n_dividendos += 1
            if t >= inicio_mes:
                dividendos_mes += monto
            bal_acum += monto
            curva.append((t, bal_acum))
            continue

        # Operaciones de BALANCE: depósitos/retiros y (en algunos brókers) dividendos.
        if tipo == TYPE_BALANCE:
            if "div" in comentario:          # fallback: dividendo marcado en el comentario
                dividendos_total += monto
                n_dividendos += 1
                if t >= inicio_mes:
                    dividendos_mes += monto
            bal_acum += monto
            curva.append((t, bal_acum))
            continue

        # Cierres de posición: traen el P/G realizado.
        if entry != DEAL_OUT:
            continue
        neto = _neto_deal(d)
        comision = float(getattr(d, "commission", 0.0) or 0.0) + float(getattr(d, "fee", 0.0) or 0.0)
        sw = float(getattr(d, "swap", 0.0) or 0.0)
        bal_acum += neto
        curva.append((t, bal_acum))

        real_total += neto; comision_total += comision; swap_total += sw
        if t >= inicio_mes:
            real_mes += neto; comision_mes += comision; swap_mes += sw; n_cierres_mes += 1
        if t >= inicio_dia:
            real_hoy += neto; comision_hoy += comision; swap_hoy += sw; n_cierres_hoy += 1

    # Depósito inicial = monto de la primera operación de balance del historial
    # (0.0 si no hay ninguna en la ventana consultada).
    deposito_inicial = next((float(getattr(d, "profit", 0.0) or 0.0)
                             for d in sorted(deals, key=lambda x: getattr(x, "time", 0))
                             if getattr(d, "type", None) == TYPE_BALANCE), 0.0)
    # Capital no genera un "deal de balance" para el depósito, y su campo `deposit`
    # refleja el balance actual (no el inicial). El depósito inicial se reconstruye
    # como balance actual − P/L realizado acumulado (asume sin depósitos/retiros).
    if not deposito_inicial:
        if balance:
            deposito_inicial = balance - real_total
        else:
            deposito_inicial = float(cuenta.get("deposito", 0.0) or 0.0)

    # ----- Flotante (posiciones abiertas) -----
    flotante = sum(float(p.get("profit", 0.0) or 0.0) + float(p.get("swap", 0.0) or 0.0)
                   for p in posiciones)

    # ----- Exposición por activo + largos/cortos -----
    # Por cada posición: notional = volumen x tamaño de contrato x precio, agrupado por activo.
    exposicion = {}
    exposicion_largos = exposicion_cortos = 0.0
    for p in posiciones:
        simbolo = p["symbol"]
        volumen = float(p.get("volumen", 0.0) or 0.0)
        precio = float(p.get("precio_actual", 0.0) or 0.0) or float(p.get("precio_apertura", 0.0) or 0.0)
        cs = _tamano_contrato(resolver_simbolo(simbolo))
        notional = volumen * cs * precio
        es_compra = p.get("tipo") == "Compra"
        if es_compra:
            exposicion_largos += notional
        else:
            exposicion_cortos += notional
        fila = exposicion.setdefault(simbolo, {"nombre": wl.nombre_visible(simbolo), "notional": 0.0,
                                          "volumen": 0.0, "n": 0})
        fila["notional"] += notional
        fila["volumen"] += volumen
        fila["n"] += 1
    exposicion_lista = sorted(exposicion.values(), key=lambda r: r["notional"], reverse=True)
    exposicion_total = exposicion_largos + exposicion_cortos

    # ----- Riesgo: pérdida DEFINIDA (posiciones con SL) + sin SL -----
    # Para cada posición con SL: pérdida = distancia al stop x valor por unidad x lotes.
    riesgo_definido = 0.0
    sin_stop_loss = 0
    for p in posiciones:
        stop_loss = float(p.get("sl", 0.0) or 0.0)
        if stop_loss <= 0:
            sin_stop_loss += 1
            continue
        simbolo = resolver_simbolo(p["symbol"])
        k, _pt = _valor_punto(simbolo)
        actual = float(p.get("precio_actual", 0.0) or 0.0) or float(p.get("precio_apertura", 0.0) or 0.0)
        volumen = float(p.get("volumen", 0.0) or 0.0)
        compra = p.get("tipo") == "Compra"
        # Pérdida si salta el SL desde el precio actual (solo si el SL está en contra).
        perdida = (actual - stop_loss) if compra else (stop_loss - actual)
        if k > 0 and perdida > 0:
            riesgo_definido += perdida * k * volumen

    # Anclar la curva al balance ACTUAL: la reconstrucción acumula deltas desde 0,
    # pero si el depósito inicial quedó fuera de la ventana el origen estaría
    # desplazado (curva "falsa" en negativo). Se desplaza todo para que el último
    # punto coincida con el balance real; así la curva y el drawdown son correctos.
    if curva:
        offset = balance - curva[-1][1]
        curva = [(t, b + offset) for t, b in curva]

    # ----- Drawdown de balance (sobre la curva reconstruida) -----
    pico = -1e18
    drawdown_abs = 0.0
    drawdown_porcentaje = 0.0
    for _t, b in curva:
        pico = max(pico, b)
        if pico > 0:
            caida = pico - b
            if caida > drawdown_abs:
                drawdown_abs = caida
                drawdown_porcentaje = caida / pico * 100.0

    # ----- Drawdown de EQUITY real (snapshots de almacen_capital, Tanda 2) -----
    # Incluye el flotante de posiciones abiertas; MT5 no guarda esta serie, la va
    # registrando servidor_datos.py. Si aún no hay suficientes snapshots, la UI usa
    # el de balance y lo indica. Ver herramientas/almacen_capital.py (nota de escalado).
    equity_serie = almacen_capital.serie()
    drawdown_equity_abs = drawdown_equity_porcentaje = 0.0
    equity_disponible = len(equity_serie) >= 3
    if equity_disponible:
        pico_e = -1e18
        for p in equity_serie:
            e = p[1]
            pico_e = max(pico_e, e)
            if pico_e > 0:
                caida = pico_e - e
                if caida > drawdown_equity_abs:
                    drawdown_equity_abs = caida
                    drawdown_equity_porcentaje = caida / pico_e * 100.0

    # ----- Rentabilidad acumulada -----
    rentabilidad_abs = equity - deposito_inicial if deposito_inicial else 0.0
    rentabilidad_porcentaje = (rentabilidad_abs / deposito_inicial * 100.0) if deposito_inicial else 0.0

    # Estructura final que la UI solo pinta (sin más cálculos).
    return {
        "moneda": moneda,
        "capital": {"equity": equity, "balance": balance,
                    "margen": margen, "margen_libre": margen_libre,
                    "margin_level": margin_level, "deposito_inicial": deposito_inicial},
        "pnl": {
            "dia": {"realizado": real_hoy, "flotante": flotante, "total": real_hoy + flotante,
                    "cierres": n_cierres_hoy},
            "mes": {"realizado": real_mes, "flotante": flotante, "total": real_mes + flotante,
                    "cierres": n_cierres_mes},
            "realizado_total": real_total,
            "flotante": flotante,
        },
        "comisiones": {"hoy": comision_hoy, "mes": comision_mes, "total": comision_total,
                       "swap_hoy": swap_hoy, "swap_mes": swap_mes, "swap_total": swap_total},
        "exposicion": {"total": exposicion_total, "largos": exposicion_largos, "cortos": exposicion_cortos,
                       "por_activo": exposicion_lista, "n_posiciones": len(posiciones)},
        "riesgo": {"definido": riesgo_definido, "sin_sl": sin_stop_loss,
                   "margin_level": margin_level, "margen_usado": margen},
        "drawdown": {"balance_abs": drawdown_abs, "balance_pct": drawdown_porcentaje,
                     "equity_abs": drawdown_equity_abs, "equity_pct": drawdown_equity_porcentaje,
                     "equity_disponible": equity_disponible, "equity_puntos": len(equity_serie)},
        "dividendos": {"total": dividendos_total, "mes": dividendos_mes, "n": n_dividendos},
        "rentabilidad": {"abs": rentabilidad_abs, "pct": rentabilidad_porcentaje},
        "curva": curva,
    }


# ---------------------------------------------------------------------------
# Métricas LIGERAS para la barra superior (Riesgo · Drawdown · Mercado)
# ---------------------------------------------------------------------------
# A diferencia de calcular(), NO lee el historial de deals (400 días): solo mira
# la cuenta, las posiciones abiertas y los snapshots de almacen_capital. Por eso es
# barata y puede refrescarse seguido en la barra superior (aplicacion.py → barra_superior/).

# Estado del mercado por símbolo, detectado por AVANCE de tick (compara la hora
# del servidor contra sí misma → sin el desfase horario del bróker, ver puente_mt5).
# sym -> (ultimo_tick_servidor, hora_local_de_esa_lectura, abierto)
_mercado_cache: dict[str, tuple[float, float, bool]] = {}


# TITULO MERCADO ABIERTO

def _mercado_abierto(simbolo: str) -> bool | None:
    """True/False si el mercado del símbolo está abierto, o None si aún no hay certeza.
    Se basa en si llegan ticks nuevos: si el tick avanzó desde la última lectura →
    abierto; si no avanza por más de 3 min → cerrado. La primera lectura devuelve
    None (hace falta una segunda para comparar).

    Efecto: actualiza la caché `_mercado_cache`, suscribe el símbolo en MT5
    (`symbol_select`) y lee su último tick bajo el candado de MT5.
    """
    if mt5 is None or not simbolo:
        return None
    try:
        sym = resolver_simbolo(simbolo)
        if os.getenv("PROVEEDOR", "mt5").strip().lower() == "capital":
            # Capital.com informa el estado de sesión (marketStatus) y su tick siempre lleva la
            # hora actual, así que el método por avance de tick no sirve: se lee el estado directo.
            if not inicializar_mt5():
                return None
            info = mt5.symbol_info(sym)
            if info is None:
                return None
            return info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL
        with MT5_LOCK:
            if not inicializar_mt5():
                return None
            mt5.symbol_select(sym, True)
            tick = mt5.symbol_info_tick(sym)
        if tick is None:
            return None
        t_srv = float(getattr(tick, "time", 0.0) or 0.0)
    except Exception:
        return None

    # Compara contra la lectura anterior guardada en la caché del módulo.
    import time as _t
    ahora = _t.time()
    anterior = _mercado_cache.get(sym)
    if anterior is None:
        _mercado_cache[sym] = (t_srv, ahora, True)
        return None                      # sin baseline todavía
    anterior_srv, anterior_wall, anterior_estado = anterior
    if t_srv > anterior_srv:                 # llegó un tick nuevo → abierto
        estado = True
    elif ahora - anterior_wall > 180.0:      # 3 min sin ticks nuevos → cerrado
        estado = False
    else:
        estado = anterior_estado             # sin novedades recientes: mantener el último
    if t_srv > anterior_srv or ahora - anterior_wall > 180.0:
        _mercado_cache[sym] = (t_srv, ahora, estado)
    return estado


# TITULO METRICAS BARRA

def metricas_barra(simbolo_activo: str | None = None) -> dict:
    """Calcula Riesgo, Drawdown y Mercado para la barra superior, sin tocar el historial.

    Recibe el símbolo activo (opcional) para estimar si su mercado está abierto.
    Devuelve {"moneda", "riesgo", "drawdown", "mercado"}. Lee MT5 y `almacen_capital`; no escribe.

    - riesgo:   pérdida DEFINIDA si las posiciones con SL saltan su stop, en moneda
                de cuenta (`abs`) y como % del equity (`pct`); `sin_sl` = nº de
                posiciones sin Stop Loss (riesgo abierto, no acotado).
    - drawdown: caída máxima de EQUITY real (snapshots de almacen_capital), en %.
                `disponible` = hay suficientes snapshots para que el dato sea fiable.
    - mercado:  estado de sesión del símbolo activo (abierto/cerrado/desconocido).
    """
    info = obtener_info_cuenta()
    con_cuenta = "error" not in info
    equity = float(info.get("equity", 0.0) or 0.0) if con_cuenta else 0.0
    moneda = info.get("currency", "USD") if con_cuenta else "USD"

    # ----- Riesgo definido por SL (mismo cálculo que calcular(), sobre posiciones) -----
    riesgo_abs = 0.0
    sin_stop_loss = 0
    for p in obtener_posiciones():
        stop_loss = float(p.get("sl", 0.0) or 0.0)
        if stop_loss <= 0:
            sin_stop_loss += 1
            continue
        k, _pt = _valor_punto(resolver_simbolo(p["symbol"]))
        actual = float(p.get("precio_actual", 0.0) or 0.0) or float(p.get("precio_apertura", 0.0) or 0.0)
        volumen = float(p.get("volumen", 0.0) or 0.0)
        compra = p.get("tipo") == "Compra"
        perdida = (actual - stop_loss) if compra else (stop_loss - actual)   # solo si el SL está en contra
        if k > 0 and perdida > 0:
            riesgo_abs += perdida * k * volumen
    riesgo_porcentaje = (riesgo_abs / equity * 100.0) if equity > 0 else 0.0

    # ----- Drawdown de equity real (pico → valle sobre los snapshots) -----
    equity_serie = almacen_capital.serie()
    drawdown_porcentaje = 0.0
    drawdown_disponible = len(equity_serie) >= 3
    if drawdown_disponible:
        pico = -1e18
        for punto in equity_serie:
            e = punto[1]
            pico = max(pico, e)
            if pico > 0:
                caida = (pico - e) / pico * 100.0
                if caida > drawdown_porcentaje:
                    drawdown_porcentaje = caida

    return {
        "moneda": moneda,
        "riesgo": {"abs": riesgo_abs, "pct": riesgo_porcentaje, "sin_sl": sin_stop_loss},
        "drawdown": {"pct": drawdown_porcentaje, "disponible": drawdown_disponible},
        "mercado": {"abierto": _mercado_abierto(simbolo_activo), "simbolo": simbolo_activo},
    }


# -------------------------------------------------------------------------------------------------------
# ----------------------------- FIN Piña y Jara estadisticas_portafolio .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
