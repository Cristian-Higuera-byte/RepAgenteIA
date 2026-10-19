"""
capital_mt5_compat.py  —  Shim "MetaTrader5" respaldado por Capital.com  —  16-10-2026
---------------------------------------------------------------------------------------
Expone las MISMAS constantes y funciones de `MetaTrader5` que usa el proyecto, pero
resolviéndolas contra Capital.com (reutilizando el backend herramientas/backends/capital.py).
Así los ~24 archivos que hacen `import MetaTrader5 as mt5` siguen funcionando sin cambios
de lógica: solo cambian su línea de import por `from proveedores.selector_mt5 import mt5`.

Los objetos devueltos imitan los de MT5 por ATRIBUTOS (p. ej. `info.digits`, `tick.bid`,
`p.ticket`), que es como los leen esos archivos.

APROXIMACIONES (documentadas): order_calc_profit/margin se calculan con contractSize y
marginFactor de Capital (asumen cotización en USD); no hay DOM; `swap`=0; el P/G del
historial se lee de forma defensiva (validar con una operación cerrada real).

NOTA DE RENDIMIENTO: `symbol_info_tick` hace una llamada REST por símbolo. El motor de
precios lo invoca seguido; para producción conviene mover el motor al streaming WebSocket
de Capital. Para demo/validación, el sondeo REST a intervalo normal es suficiente.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from tools.backends import capital as cap

# ===========================================================================
# CONSTANTES (mismos valores enteros que MetaTrader5, para comparaciones iguales)
# ===========================================================================
TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 16385
TIMEFRAME_H4 = 16388
TIMEFRAME_D1 = 16408
TIMEFRAME_W1 = 32769
TIMEFRAME_MN1 = 49153

ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5

ORDER_TIME_GTC = 0
ORDER_TIME_DAY = 1
ORDER_TIME_SPECIFIED = 2

ORDER_FILLING_FOK = 0
ORDER_FILLING_IOC = 1
ORDER_FILLING_RETURN = 2

TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_SLTP = 6
TRADE_ACTION_MODIFY = 7
TRADE_ACTION_REMOVE = 8

TRADE_RETCODE_DONE = 10009
TRADE_RETCODE_DONE_PARTIAL = 10010

DEAL_ENTRY_IN = 0
DEAL_ENTRY_OUT = 1
DEAL_TYPE_BUY = 0
DEAL_TYPE_SELL = 1

POSITION_TYPE_BUY = 0
POSITION_TYPE_SELL = 1

BOOK_TYPE_SELL = 1
BOOK_TYPE_BUY = 2
BOOK_TYPE_SELL_MARKET = 3
BOOK_TYPE_BUY_MARKET = 4

SYMBOL_TRADE_MODE_FULL = 4
SYMBOL_CALC_MODE_FOREX = 0

ACCOUNT_TRADE_MODE_DEMO = 0
ACCOUNT_TRADE_MODE_CONTEST = 1
ACCOUNT_TRADE_MODE_REAL = 2

_ultimo_error = (0, "ok")

# TF entero -> resolución de Capital (reusa el mapa del backend)
_TF_A_RES = {1: "MINUTE", 5: "MINUTE_5", 15: "MINUTE_15", 30: "MINUTE_30",
             16385: "HOUR", 16388: "HOUR_4", 16408: "DAY", 32769: "WEEK", 49153: "WEEK"}


# ===========================================================================
# Conexión / estado
# ===========================================================================
def initialize(*args: Any, **kwargs: Any) -> bool:
    return cap.inicializar_mt5()


def shutdown() -> None:
    cap.cerrar_mt5()


def last_error():
    return _ultimo_error


def terminal_info():
    return SimpleNamespace(connected=True, community_account=False) if cap.inicializar_mt5() else None


# ===========================================================================
# Especificaciones de instrumento (cacheadas) y utilidades
# ===========================================================================
_cache_mercado: dict = {}
# Las specs (dígitos, contrato, margen, límites) son estáticas y el bid/ask para
# display llega por SSE/WebSocket; por eso se cachea el mercado 30 s y así el render
# del dashboard no hace una llamada REST por cada symbol_info.
_TTL_MERCADO = 30.0


def _mercado(epic: str) -> dict:
    """GET /markets/{epic} con caché breve. Devuelve el JSON crudo o {}."""
    ahora = time.time()
    hit = _cache_mercado.get(epic)
    if hit and (ahora - hit[0]) < _TTL_MERCADO:
        return hit[1]
    r = cap._pedir("GET", f"/markets/{epic}")
    data = r.json() if (r is not None and r.status_code == 200) else {}
    _cache_mercado[epic] = (ahora, data)
    return data


def _specs(epic: str) -> dict:
    d = _mercado(epic)
    inst = d.get("instrument", {}) or {}
    snap = d.get("snapshot", {}) or {}
    reglas = d.get("dealingRules", {}) or {}
    digitos = int(snap.get("decimalPlacesFactor", 2) or 2)
    point = 10 ** (-digitos)
    bid = float(snap.get("bid", 0.0) or 0.0)
    md = reglas.get("minStopOrProfitDistance", {}) or {}
    if md.get("unit") == "PERCENTAGE" and bid:
        stops_level = int((bid * float(md.get("value", 0.0) or 0.0) / 100.0) / point) if point else 0
    else:
        stops_level = int(float(md.get("value", 0.0) or 0.0) / point) if point else 0
    tick_size = float(d.get("tickSize", 0.0) or snap.get("scalingFactor", 0.0) or point)
    contract = float(inst.get("lotSize", 1.0) or 1.0)
    return {
        "digitos": digitos,
        "point": float(point),
        "bid": bid,
        "ask": float(snap.get("offer", 0.0) or 0.0),
        "tick_size": tick_size or point,
        "tick_value": contract * (tick_size or point),   # valor de 1 tick por 1 unidad (USD)
        "contract": contract,
        "margin_factor": float(inst.get("marginFactor", 0.0) or 0.0),
        "vmin": float((reglas.get("minDealSize", {}) or {}).get("value", 0.01) or 0.01),
        "vmax": float((reglas.get("maxDealSize", {}) or {}).get("value", 1e9) or 1e9),
        "vstep": float((reglas.get("minSizeIncrement", {}) or {}).get("value", 0.01) or 0.01),
        "stops_level": stops_level,
        "tradeable": snap.get("marketStatus") == "TRADEABLE",
        "high": float(snap.get("high", 0.0) or 0.0),
        "low": float(snap.get("low", 0.0) or 0.0),
        "session_open": float(snap.get("bid", 0.0) or 0.0),
        "tipo": inst.get("type", ""),   # CURRENCIES / COMMODITIES / INDICES / CRYPTOCURRENCIES
    }


# ===========================================================================
# Símbolos
# ===========================================================================
def symbol_select(symbol: str, enable: bool = True) -> bool:
    return True


def symbol_info(symbol: str):
    s = _specs(symbol)
    if not s or not (s["bid"] or s["ask"]):
        return None
    return SimpleNamespace(
        name=symbol, description=symbol, path=f"Capital\\{symbol}",
        bid=s["bid"], ask=s["ask"], last=s["bid"] or s["ask"],
        digits=s["digitos"], point=s["point"],
        trade_tick_size=s["tick_size"], trade_tick_value=s["tick_value"],
        trade_contract_size=s["contract"], trade_stops_level=s["stops_level"],
        volume_min=s["vmin"], volume_max=s["vmax"], volume_step=s["vstep"],
        filling_mode=2, spread=int((s["ask"] - s["bid"]) / s["point"]) if s["point"] else 0,
        visible=True, trade_mode=SYMBOL_TRADE_MODE_FULL if s["tradeable"] else 0,
        trade_calc_mode=SYMBOL_CALC_MODE_FOREX if s.get("tipo") == "CURRENCIES" else 1,
        session_open=s["session_open"], high=s["high"], low=s["low"],
    )


def symbol_info_tick(symbol: str):
    s = _specs(symbol)
    if not s or not (s["bid"] or s["ask"]):
        return None
    ahora = time.time()
    return SimpleNamespace(bid=s["bid"], ask=s["ask"], last=s["bid"] or s["ask"],
                           time=int(ahora), time_msc=int(ahora * 1000))


_CURADOS = ["GOLD", "SILVER", "US30", "US100", "US500", "BTCUSD", "ETHUSD",
            "EURUSD", "GBPUSD", "USDJPY"]
_catalogo_cache: dict = {"ts": 0.0, "items": []}
_TTL_CATALOGO = 600          # 10 min
_MAX_NAV_REQS = 60           # tope de llamadas de navegación por refresco
_MAX_EPICS = 1500

# Grupo de navegación -> categoría legible para el path (lo usa el buscador).
_GRUPO_CAT = {
    "forex": "Forex", "indices_group": "Índices", "commodities_group": "Materias primas",
    "oil_markets_group": "Materias primas", "crypto_currencies_group": "Cripto",
    "shares": "Acciones", "etf_group": "ETF", "bonds_group": "Bonos",
    "interest_rates_group": "Tasas", "commons_group": "Populares",
}


def _nombre_grupo(node_id: str, node_name: str) -> str:
    clave = (node_id or "").split(".")[-1]
    return _GRUPO_CAT.get(clave, node_name or "Otros")


# Caché en disco del catálogo: tras el primer arranque, el buscador abre al instante.
import configuracion  # rutas centrales del proyecto (database/data)
_CAT_DISCO = os.path.join(str(configuracion.DIR_DATOS), "catalogo_capital.json")
_TTL_DISCO = 24 * 3600   # 24 h


def _nav(node_id: str) -> dict:
    """GET /marketnavigation/{id} SIN el candado global, para poder paralelizar."""
    try:
        r = cap._HTTP.get(f"{cap.BASE}/marketnavigation/{node_id}",
                          headers=cap._cabeceras(), timeout=cap._TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


def _lista_desde_items(items: dict) -> list:
    if not items:
        items = {e: (e, "Populares") for e in _CURADOS}
    return [SimpleNamespace(name=ep, visible=True, description=nombre, path=f"{cat}\\{ep}")
            for ep, (nombre, cat) in items.items()]


def _catalogo() -> list:
    """Catálogo real de instrumentos de Capital (cacheado en memoria 10 min y en disco 24 h).
    La primera vez recorre /marketnavigation EN PARALELO (grupos + 1 nivel de subnodos)."""
    ahora = time.time()
    if _catalogo_cache["items"] and (ahora - _catalogo_cache["ts"]) < _TTL_CATALOGO:
        return _catalogo_cache["items"]
    # 1) caché en disco: instantáneo tras el primer arranque
    try:
        if os.path.exists(_CAT_DISCO) and (ahora - os.path.getmtime(_CAT_DISCO)) < _TTL_DISCO:
            with open(_CAT_DISCO, encoding="utf-8") as f:
                crudos = json.load(f)
            lista = [SimpleNamespace(**d) for d in crudos]
            if lista:
                _catalogo_cache.update(ts=ahora, items=lista)
                return lista
    except Exception:
        pass
    # 2) traer de la API en paralelo
    if not cap.inicializar_mt5():
        return _lista_desde_items({})
    items: dict = {}
    try:
        r = cap._pedir("GET", "/marketnavigation")
        grupos = r.json().get("nodes", []) if (r is not None and r.status_code == 200) else []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            # Nivel 2: los grupos, en paralelo
            datos_grupos = list(ex.map(lambda g: (g, _nav(g.get("id", ""))), grupos))
            subnodos = []
            for g, d in datos_grupos:
                cat = _nombre_grupo(g.get("id", ""), g.get("name", ""))
                for m in d.get("markets", []):
                    ep = m.get("epic")
                    if ep:
                        items.setdefault(ep, (m.get("instrumentName", ep), cat))
                for sn in d.get("nodes", []):
                    subnodos.append((sn, cat))
            subnodos = subnodos[:_MAX_NAV_REQS]
            # Nivel 3: los subnodos, en paralelo
            datos_sub = list(ex.map(lambda sc: (sc[1], _nav(sc[0].get("id", ""))), subnodos))
            vacios = [(sn, cat) for (sn, cat), (_c, d) in zip(subnodos, datos_sub)
                      if not d.get("markets")]
            for cat, d in datos_sub:
                for m in d.get("markets", []):
                    ep = m.get("epic")
                    if ep and len(items) < _MAX_EPICS:
                        items.setdefault(ep, (m.get("instrumentName", ep), cat))
            # Reintento EN PARALELO de los subnodos vacíos (fallos puntuales de concurrencia)
            if vacios and len(items) < _MAX_EPICS:
                datos_r = list(ex.map(lambda sc: (sc[1], _nav(sc[0].get("id", ""))), vacios))
                for cat, d in datos_r:
                    for m in d.get("markets", []):
                        ep = m.get("epic")
                        if ep and len(items) < _MAX_EPICS:
                            items.setdefault(ep, (m.get("instrumentName", ep), cat))
    except Exception as e:  # noqa: BLE001
        print(f"[CAPITAL shim] no se pudo cargar el catálogo: {e}")
    lista = _lista_desde_items(items)
    _catalogo_cache.update(ts=ahora, items=lista)
    # Guardar a disco para la próxima vez
    try:
        os.makedirs(os.path.dirname(_CAT_DISCO), exist_ok=True)
        with open(_CAT_DISCO, "w", encoding="utf-8") as f:
            json.dump([vars(x) for x in lista], f, ensure_ascii=False)
    except Exception:
        pass
    return lista


def symbols_get(*args: Any, **kwargs: Any) -> list:
    """Catálogo real de instrumentos de Capital (cacheado). Objetos con name/visible/
    description/path, como los símbolos de MT5."""
    return _catalogo()


# ===========================================================================
# Cuenta
# ===========================================================================
def account_info():
    c = cap.obtener_info_cuenta()
    if not c or "error" in c:
        return None
    return SimpleNamespace(
        login=c.get("login", 0), name=c.get("nombre", ""), server=c.get("servidor", ""),
        trade_mode=ACCOUNT_TRADE_MODE_DEMO if c.get("tipo") == "Demo" else ACCOUNT_TRADE_MODE_REAL,
        balance=c.get("balance", 0.0), equity=c.get("equity", 0.0), profit=c.get("profit", 0.0),
        margin=c.get("margin", 0.0), margin_free=c.get("margin_free", 0.0),
        margin_level=c.get("margin_level", 0.0), credit=c.get("credit", 0.0),
        leverage=c.get("leverage", 0), currency=c.get("currency", "USD"),
    )


# ===========================================================================
# Posiciones / órdenes / historial
# ===========================================================================
def positions_get(ticket: Any = None, symbol: str = None, **kwargs: Any) -> list:
    r = cap._pedir("GET", "/positions")
    if r is None or r.status_code != 200:
        return []
    out = []
    for item in r.json().get("positions", []):
        p = item.get("position", {}) or {}
        m = item.get("market", {}) or {}
        if ticket is not None and str(p.get("dealId")) != str(ticket):
            continue
        if symbol is not None and m.get("epic") != symbol:
            continue
        es_compra = p.get("direction", "").upper() == "BUY"
        out.append(SimpleNamespace(
            ticket=p.get("dealId", ""), symbol=m.get("epic", ""),
            type=POSITION_TYPE_BUY if es_compra else POSITION_TYPE_SELL,
            volume=float(p.get("size", 0.0) or 0.0),
            price_open=float(p.get("level", 0.0) or 0.0),
            price_current=float(m.get("bid", 0.0) or 0.0) if es_compra else float(m.get("offer", 0.0) or 0.0),
            profit=float(p.get("upl", 0.0) or 0.0), swap=0.0,
            sl=float(p.get("stopLevel", 0.0) or 0.0), tp=float(p.get("profitLevel", 0.0) or 0.0),
            time=cap._epoch_utc(p.get("createdDateUTC", "") or p.get("createdDate", "")),
        ))
    return out


def orders_get(ticket: Any = None, **kwargs: Any) -> list:
    """Órdenes pendientes. NOTA: los nombres de campo de /workingorders se leen de forma
    defensiva (no se pudo observar una orden real); validar con una pendiente creada."""
    r = cap._pedir("GET", "/workingorders")
    if r is None or r.status_code != 200:
        return []
    out = []
    for item in r.json().get("workingOrders", []):
        w = item.get("workingOrderData", item) or {}
        m = item.get("marketData", {}) or {}
        dealId = w.get("dealId", "")
        if ticket is not None and str(dealId) != str(ticket):
            continue
        es_compra = w.get("direction", "").upper() == "BUY"
        es_limit = str(w.get("orderType", "")).upper() == "LIMIT"
        if es_compra:
            tipo = ORDER_TYPE_BUY_LIMIT if es_limit else ORDER_TYPE_BUY_STOP
        else:
            tipo = ORDER_TYPE_SELL_LIMIT if es_limit else ORDER_TYPE_SELL_STOP
        gtd = w.get("goodTillDate")
        out.append(SimpleNamespace(
            ticket=dealId, symbol=m.get("epic", "") or w.get("epic", ""), type=tipo,
            volume=float(w.get("orderSize", 0.0) or 0.0),
            volume_current=float(w.get("orderSize", 0.0) or 0.0),
            price_open=float(w.get("orderLevel", 0.0) or 0.0),
            price_current=float(m.get("bid", 0.0) or 0.0),
            sl=float(w.get("stopLevel", 0.0) or 0.0), tp=float(w.get("profitLevel", 0.0) or 0.0),
            type_time=ORDER_TIME_GTC if not gtd else ORDER_TIME_SPECIFIED,
            time_expiration=cap._epoch_utc(gtd) if gtd else 0,
            time=0,
        ))
    return out


def history_deals_get(desde: Any = None, hasta: Any = None, **kwargs: Any) -> list:
    """Operaciones del historial. El campo de P/G realizado se lee de forma defensiva
    (validar con un cierre real). `entry` se marca OUT para que el cálculo de cerradas lo tome."""
    params = {}
    if isinstance(desde, datetime):
        params["from"] = desde.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")
    r = cap._pedir("GET", "/history/transactions", params=params or None)
    if r is None or r.status_code != 200:
        return []
    out = []
    for t in r.json().get("transactions", []):
        tipo_tx = str(t.get("transactionType", "")).upper()
        if "TRADE" not in tipo_tx and "DEAL" not in tipo_tx:
            continue
        # En Capital el monto del cierre (el P/L realizado) viene en `size` (el balance
        # se mueve exactamente ese monto). Se intenta primero profitAndLoss/pnl por si
        # alguna versión los trae.
        pg = (t.get("profitAndLoss") or t.get("pnl") or t.get("size") or 0)
        try:
            pg = float(str(pg).replace(t.get("currency", "") or "", "").strip() or 0)
        except ValueError:
            pg = 0.0
        out.append(SimpleNamespace(
            ticket=t.get("reference", ""), symbol=t.get("instrumentName", ""),
            type=DEAL_TYPE_BUY, entry=DEAL_ENTRY_OUT, volume=0.0, price=0.0,
            profit=pg, swap=0.0, commission=0.0, fee=0.0,
            time=cap._epoch_utc(t.get("dateUtc", "") or t.get("date", "")),
        ))
    return out


# ===========================================================================
# Velas
# ===========================================================================
def _velas_dicts(epic: str, timeframe, maximo: int = None, desde=None, hasta=None) -> list:
    res = _TF_A_RES.get(int(timeframe) if timeframe is not None else 16385, "HOUR")
    f = desde.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") if isinstance(desde, datetime) else None
    h = hasta.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") if isinstance(hasta, datetime) else None
    crudas = cap._velas_crudas(epic, res, maximo=maximo, desde=f, hasta=h)
    out = []
    for v in crudas:
        out.append({
            "time": cap._epoch_utc(v.get("snapshotTimeUTC") or v.get("snapshotTime")),
            "open": cap._mid(v.get("openPrice", {})), "high": cap._mid(v.get("highPrice", {})),
            "low": cap._mid(v.get("lowPrice", {})), "close": cap._mid(v.get("closePrice", {})),
            "tick_volume": v.get("lastTradedVolume", 0), "spread": 0, "real_volume": 0,
        })
    return out


def copy_rates_from_pos(symbol: str, timeframe, start: int, count: int) -> list:
    """Devuelve una lista de dicts indexables por nombre (rates[i]['close']), como el
    structured array de MT5; `pd.DataFrame(rates)` también funciona."""
    return _velas_dicts(symbol, timeframe, maximo=int(start) + int(count))[-int(count):]


def copy_rates_range(symbol: str, timeframe, date_from, date_to) -> list:
    return _velas_dicts(symbol, timeframe, maximo=1000, desde=date_from, hasta=date_to)


# ===========================================================================
# Cálculos de riesgo (aproximados con contractSize / marginFactor de Capital)
# ===========================================================================
def order_calc_profit(action: int, symbol: str, volume: float, price_open: float, price_close: float):
    s = _specs(symbol)
    if not s:
        return None
    signo = 1.0 if action == ORDER_TYPE_BUY else -1.0
    return signo * float(volume) * s["contract"] * (float(price_close) - float(price_open))


def order_calc_margin(action: int, symbol: str, volume: float, price: float):
    s = _specs(symbol)
    if not s:
        return None
    mf = s["margin_factor"] or 0.0
    return float(volume) * s["contract"] * float(price) * mf / 100.0


# ===========================================================================
# Envío de órdenes: enruta al backend Capital según la solicitud
# ===========================================================================
def order_send(solicitud: dict):
    """Interpreta la solicitud estilo MT5 y la enruta al backend Capital.
    Soporta las que arma el proyecto: DEAL de apertura y DEAL de cierre (con 'position')."""
    global _ultimo_error
    symbol = solicitud.get("symbol", "")
    volume = float(solicitud.get("volume", 0.0) or 0.0)
    if solicitud.get("position"):                     # cierre de una posición existente
        res = cap.cerrar_posicion(solicitud["position"])
    else:                                             # apertura a mercado
        tipo = "BUY" if solicitud.get("type") == ORDER_TYPE_BUY else "SELL"
        res = cap.ejecutar_orden_mercado(symbol, tipo, volume,
                                         sl=float(solicitud.get("sl", 0.0) or 0.0),
                                         tp=float(solicitud.get("tp", 0.0) or 0.0))
    if "error" in res:
        _ultimo_error = (1, res["error"])
        return SimpleNamespace(retcode=10013, comment=res["error"], order=0, price=0.0)
    return SimpleNamespace(retcode=TRADE_RETCODE_DONE, comment="Done",
                           order=res.get("order", solicitud.get("position", "")),
                           price=float(res.get("price", solicitud.get("price", 0.0)) or 0.0))


# ===========================================================================
# Totales / versión (los usa la capa del agente de solo lectura)
# ===========================================================================
def version():
    return (500, 0, "Capital.com shim")


def positions_total() -> int:
    return len(positions_get())


def orders_total() -> int:
    return len(orders_get())


def symbols_total() -> int:
    return len(symbols_get())


def history_deals_total(desde: Any = None, hasta: Any = None) -> int:
    return len(history_deals_get(desde, hasta))


def history_orders_get(desde: Any = None, hasta: Any = None, **kwargs: Any) -> list:
    return []


def history_orders_total(desde: Any = None, hasta: Any = None) -> int:
    return 0


# ===========================================================================
# Profundidad de mercado (DOM): no disponible por REST
# ===========================================================================
def market_book_add(symbol: str) -> bool:
    return False


def market_book_get(symbol: str):
    return []


def market_book_release(symbol: str) -> bool:
    return True
