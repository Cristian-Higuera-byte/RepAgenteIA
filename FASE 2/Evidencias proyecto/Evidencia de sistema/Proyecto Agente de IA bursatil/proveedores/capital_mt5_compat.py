# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara capital_mt5_compat .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

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
marginFactor de Capital y se convierten a la moneda de la cuenta con el par de divisas
correspondiente (EURUSD, USDJPY...); no hay DOM; `swap`=0; el P/G del historial se lee
de forma defensiva (validar con una operación cerrada real). Las velas (`copy_rates_*`) se
entregan como filas que se leen por nombre (`v["close"]`) o por posición (`v[4]`), como las de
MT5, con el spread de cada vela en puntos.

NOTA DE RENDIMIENTO: `symbol_info_tick` hace una llamada REST por símbolo. El motor de
precios lo invoca seguido; para producción conviene mover el motor al streaming WebSocket
de Capital. Para demo/validación, el sondeo REST a intervalo normal es suficiente.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import threading
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from herramientas.backends import capital as cap
from herramientas.hilos import con_usuario

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

# Último error de orden, POR HILO: así el mensaje de un usuario nunca lo lee otro (cada petición corre en su propio hilo)
_estado_error = threading.local()

# TF entero -> resolución de Capital (reusa el mapa del backend)
_TF_A_RES = {1: "MINUTE", 5: "MINUTE_5", 15: "MINUTE_15", 30: "MINUTE_30",
             16385: "HOUR", 16388: "HOUR_4", 16408: "DAY", 32769: "WEEK", 49153: "WEEK"}


# TITULO INITIALIZE

# ===========================================================================
# Conexión / estado
# ===========================================================================
def initialize(*args: Any, **kwargs: Any) -> bool:
    """Equivale a `mt5.initialize`: abre (o reutiliza) la sesión con Capital.com. Ignora los argumentos de MT5 y devuelve True si hay sesión."""
    return cap.inicializar_mt5()


# TITULO SHUTDOWN

def shutdown() -> None:
    """Equivale a `mt5.shutdown`: cierra la sesión con Capital.com. No devuelve nada."""
    cap.cerrar_mt5()


# TITULO LAST ERROR

def last_error():
    """Equivale a `mt5.last_error`: devuelve la tupla (código, mensaje) del último error de una orden enviada con `order_send`."""
    return getattr(_estado_error, "valor", (0, "ok"))


# TITULO TERMINAL INFO

def terminal_info():
    """Equivale a `mt5.terminal_info`: informa que el terminal está "conectado" y que el trading automático está permitido. Sirve para que el código que revisa MT5 no falle con Capital."""
    return SimpleNamespace(connected=True, community_account=False) if cap.inicializar_mt5() else None


# ===========================================================================
# Especificaciones de instrumento (cacheadas) y utilidades
# ===========================================================================
_cache_mercado: dict = {}
# Las specs (dígitos, contrato, margen, límites) son estáticas y el bid/ask para
# display llega por SSE/WebSocket; por eso se cachea el mercado 30 s y así el render
# del dashboard no hace una llamada REST por cada symbol_info.
_TTL_MERCADO = 30.0
_refrescando_mercado: set = set()


# TITULO MERCADO

def _mercado(epic: str) -> dict:
    """GET /markets/{epic} compartido y cacheado con el backend (ver capital.obtener_mercado)."""
    return cap.obtener_mercado(epic)


# TITULO MONEDA COTIZACION

def _moneda_cotizacion(epic: str, inst: dict) -> str:
    """Moneda en que cotiza el instrumento: las tres últimas letras en un par de divisas (EURJPY -> JPY); en el resto, la moneda
    que informa Capital y, si no la informa, USD."""
    if str(inst.get("type", "")).upper() == "CURRENCIES" and len(epic) == 6 and epic.isalpha():
        return epic[3:].upper()
    for c in inst.get("currencies") or []:
        if isinstance(c, dict) and c.get("isDefault") and c.get("code"):
            return str(c["code"]).upper()
    return str(inst.get("currency") or "USD").upper()


# TITULO HORA PRECIO

def _hora_precio(snap: dict) -> int:
    """Epoch (UTC) de la última actualización del precio según Capital (`updateTimeUTC` o `updateTime`); 0 si no la informa o no
    se entiende (por ejemplo, solo la hora del día)."""
    for campo in ("updateTimeUTC", "updateTime"):
        texto = str(snap.get(campo) or "")
        if len(texto) >= 16 and "T" in texto:
            return cap._epoch_utc(texto)
    return 0


_tasas: dict = {}
_TTL_TASA = 60.0


# TITULO TASA A CUENTA

def _tasa_a_cuenta(moneda: str) -> float:
    """Cuántas unidades de la moneda de la cuenta vale 1 unidad de `moneda`; 1.0 si es la misma o no se puede saber.

    Usa el par de divisas exacto (EURUSD para EUR, USDJPY para JPY, con su inverso) leído del mercado de Capital, y recuerda el
    resultado 60 s. Sirve para que el riesgo y el margen salgan en la moneda de la cuenta y no en la de cotización."""
    cuenta = str((cap.obtener_info_cuenta() or {}).get("currency") or "USD").upper()
    if not moneda or moneda == cuenta:
        return 1.0
    clave = (moneda, cuenta)
    guardada = _tasas.get(clave)
    if guardada and time.time() - guardada[0] < _TTL_TASA:
        return guardada[1]
    tasa = 1.0
    for epic, invertir in ((moneda + cuenta, False), (cuenta + moneda, True)):
        snap = (cap.obtener_mercado(epic) or {}).get("snapshot", {}) or {}
        precio = float(snap.get("bid") or 0.0)
        if precio > 0:
            tasa = 1.0 / precio if invertir else precio
            break
    _tasas[clave] = (time.time(), tasa)
    return tasa


# TITULO SPECS

def _specs(epic: str) -> dict:
    """Reúne las especificaciones de un instrumento (decimales, punto, contrato, margen, volumen mínimo/máximo/paso, distancia mínima de stops, tipo y nombre) leyéndolas del mercado de Capital.

    Recibe el epic y devuelve un diccionario; si Capital no responde, los valores quedan en cero.
    """
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
    fl = cap.factor_lote(inst.get("type", ""))
    contract = float(inst.get("lotSize", 1.0) or 1.0) * fl
    return {
        "digitos": digitos,
        "point": float(point),
        "bid": bid,
        "ask": float(snap.get("offer", 0.0) or 0.0),
        "tick_size": tick_size or point,
        "tick_value": contract * (tick_size or point),   # valor de 1 tick por 1 unidad (USD)
        "contract": contract,
        "margin_factor": float(inst.get("marginFactor", 0.0) or 0.0),
        "vmin": float((reglas.get("minDealSize", {}) or {}).get("value", 0.01) or 0.01) / fl,
        "vmax": float((reglas.get("maxDealSize", {}) or {}).get("value", 1e9) or 1e9) / fl,
        "vstep": float((reglas.get("minSizeIncrement", {}) or {}).get("value", 0.01) or 0.01) / fl,
        "stops_level": stops_level,
        "tradeable": snap.get("marketStatus") == "TRADEABLE",
        "high": float(snap.get("high", 0.0) or 0.0),
        "low": float(snap.get("low", 0.0) or 0.0),
        "session_open": float(snap.get("bid", 0.0) or 0.0),
        "tipo": inst.get("type", ""),   # CURRENCIES / COMMODITIES / INDICES / CRYPTOCURRENCIES / SHARES
        "nombre": inst.get("name", "") or "",
        "moneda": _moneda_cotizacion(epic, inst),
        "hora_precio": _hora_precio(snap),
    }


# TITULO SYMBOL SELECT

# ===========================================================================
# Símbolos
# ===========================================================================
def symbol_select(symbol: str, enable: bool = True) -> bool:
    """Equivale a `mt5.symbol_select`: en Capital no hay que seleccionar símbolos, así que siempre devuelve True."""
    return True


_CARPETA_TIPO = {"SHARES": "Stocks", "CRYPTOCURRENCIES": "Cryptocurrencies", "ETFS": "ETF", "ETF": "ETF"}


# TITULO RUTA

def _ruta(symbol: str, s: dict) -> str:
    """Ruta tipo MT5 (Stocks, AAPL): el primer nivel indica la clase de activo; la UI de iconos lo usa
    para decidir si busca el logo de la empresa."""
    tipo = str(s.get("tipo", "")).upper()
    return (_CARPETA_TIPO.get(tipo) or _CARPETA_CATALOGO.get(tipo) or "Capital") + chr(92) + symbol


# TITULO DESCRIPCION

def _descripcion(symbol: str, s: dict) -> str:
    """"Apple Inc (AAPL)": en acciones el ticker va entre parentesis al final, como en las descripciones de MT5,
    porque de ahi se saca el codigo para el logo."""
    nombre = s.get("nombre") or symbol
    return f"{nombre} ({symbol})" if str(s.get("tipo", "")).upper() in ("SHARES", "ETFS", "ETF") else symbol


# TITULO SYMBOL INFO

def symbol_info(symbol: str):
    """Equivale a `mt5.symbol_info`: devuelve un objeto con los datos del instrumento (bid, ask, decimales, volumen, ruta, descripción, etc.) con los nombres de campo de MT5, o None si no hay precio.

    La ruta y la descripción indican la clase de activo (Stocks, Cryptocurrencies, ETF) para que la interfaz decida el ícono.
    """
    s = _specs(symbol)
    if not s or not (s["bid"] or s["ask"]):
        return None
    return SimpleNamespace(
        name=symbol, description=_descripcion(symbol, s), path=_ruta(symbol, s),
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


# TITULO SYMBOL INFO TICK

def symbol_info_tick(symbol: str):
    """Equivale a `mt5.symbol_info_tick`: devuelve el último bid/ask del instrumento con la hora de su última actualización (la hora actual si Capital no la informa), o None si no hay precio."""
    s = _specs(symbol)
    if not s or not (s["bid"] or s["ask"]):
        return None
    ahora = time.time()
    hora = s["hora_precio"] or int(ahora)    # la hora real del último precio permite saber si el mercado se movió
    return SimpleNamespace(bid=s["bid"], ask=s["ask"], last=s["bid"] or s["ask"],
                           time=hora, time_msc=hora * 1000)


_CURADOS = ["GOLD", "SILVER", "US30", "US100", "US500", "BTCUSD", "ETHUSD",
            "EURUSD", "GBPUSD", "USDJPY"]
# Estado del catálogo, compartido por todo el proceso: instrumentos conocidos, marca de tiempo, si el recorrido terminó sin fallos
# (`completo`), si hay un recorrido en curso (`cargando`), cuántos nodos del árbol van leídos (para mostrar avance) y desde
# cuándo (`proximo`) toca rehacer el recorrido en segundo plano.
_cat: dict = {"proximo": 0.0, "items": [], "completo": False, "cargando": False, "nodos": 0}
_CAT_CANDADO = threading.Lock()
_REINTENTO_CATALOGO_S = 60   # tras un recorrido con fallos se reintenta pronto
_MAX_NODOS = 5000            # tope de seguridad del recorrido del árbol (un árbol normal tiene cientos)
_MAX_EPICS = 60000           # tope de seguridad de instrumentos
_TIEMPO_RECORRIDO_S = 300    # el recorrido se corta (y queda como incompleto) pasado este tiempo
_HILOS_RECORRIDO = 6
_FORMATO_DISCO = 2           # distingue el archivo nuevo del antiguo, que podía guardar solo 10 instrumentos por un fallo

# Grupo de navegación -> categoría legible para el path (lo usa el buscador).
_GRUPO_CAT = {
    "forex": "Forex", "indices_group": "Índices", "commodities_group": "Materias primas",
    "oil_markets_group": "Materias primas", "crypto_currencies_group": "Cripto",
    "shares": "Acciones", "etf_group": "ETF", "bonds_group": "Bonos",
    "interest_rates_group": "Tasas", "commons_group": "Populares",
}

# Tipo de instrumento de Capital -> carpeta del path. Las tres primeras son las mismas que usa `_ruta` (de ellas depende
# el ícono); el resto permite clasificar el instrumento sin depender de palabras sueltas.
_CARPETA_CATALOGO = {
    "SHARES": "Stocks", "CRYPTOCURRENCIES": "Cryptocurrencies", "ETFS": "ETF", "ETF": "ETF",
    "CURRENCIES": "Forex", "INDICES": "Indices", "COMMODITIES": "Commodities",
    "BONDS": "Bonds", "INTEREST_RATES": "Rates",
}


# TITULO NOMBRE GRUPO

def _nombre_grupo(node_id: str, node_name: str) -> str:
    """Traduce el nombre de un grupo de Capital (por ejemplo "Shares") a la carpeta equivalente de MT5 que usa la interfaz.

    Recibe el id y el nombre del nodo del árbol de mercados y devuelve el nombre de carpeta.
    """
    clave = (node_id or "").split(".")[-1]
    return _GRUPO_CAT.get(clave, node_name or "Otros")


# Caché en disco del catálogo: tras el primer arranque, el buscador abre al instante.
_CAT_DISCO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "catalogo_capital.json")
_TTL_DISCO = 24 * 3600   # 24 h: pasado ese tiempo el catálogo se sigue usando mientras se rehace en segundo plano


# TITULO NAV

def _nav(node_id: str):
    """GET /marketnavigation/{id} con el límite de ritmo del backend. Devuelve el JSON del nodo, o None si no se pudo leer
    (para distinguir un nodo realmente vacío de un fallo y no dar por completo un catálogo al que le faltan partes)."""
    try:
        r = cap._pedir("GET", f"/marketnavigation/{node_id}" if node_id else "/marketnavigation")
    except Exception:  # noqa: BLE001
        return None
    if r is not None and r.status_code == 200:
        try:
            return r.json()
        except ValueError:
            return None
    return None


# TITULO CARPETA CATALOGO

def _carpeta_catalogo(tipo: str, grupo: str) -> str:
    """Carpeta (primer nivel del path) de un instrumento del catálogo: la que corresponde a su tipo en Capital y, si el tipo es
    desconocido, el nombre del grupo del árbol en que apareció."""
    return _CARPETA_CATALOGO.get(str(tipo or "").upper()) or grupo


# TITULO LISTA DESDE ITEMS

def _lista_desde_items(items: dict) -> list:
    """Convierte el catálogo guardado (diccionario `epic -> (nombre, grupo, tipo)`) en la lista de símbolos con forma de objeto
    MT5 (`name`, `description`, `path`, `visible`)."""
    if not items:
        items = {e: (e, "Populares", "") for e in _CURADOS}
    return [SimpleNamespace(name=ep, visible=True, description=nombre, path=f"{_carpeta_catalogo(tipo, grupo)}\\{ep}")
            for ep, (nombre, grupo, tipo) in items.items()]


# TITULO CATALOGO DESDE DISCO

def _catalogo_desde_disco():
    """Lee el catálogo guardado en disco. Devuelve `(lista, marca_de_tiempo)` o `([], 0.0)` si no existe, está dañado o es de un
    formato antiguo (el anterior pudo guardar una lista de solo 10 instrumentos tras un fallo de red)."""
    try:
        with open(_CAT_DISCO, encoding="utf-8") as f:
            datos = json.load(f)
        if not isinstance(datos, dict) or datos.get("formato") != _FORMATO_DISCO:
            return [], 0.0
        lista = [SimpleNamespace(**d) for d in datos.get("items", [])]
        return (lista, os.path.getmtime(_CAT_DISCO)) if lista else ([], 0.0)
    except Exception:  # noqa: BLE001
        return [], 0.0


# TITULO GUARDAR CATALOGO EN DISCO

def _guardar_catalogo_en_disco(lista: list) -> None:
    """Guarda el catálogo completo en disco (se escribe a un archivo temporal y se renombra, para no dejar un archivo a medias)."""
    try:
        os.makedirs(os.path.dirname(_CAT_DISCO), exist_ok=True)
        temporal = _CAT_DISCO + ".tmp"
        with open(temporal, "w", encoding="utf-8") as f:
            json.dump({"formato": _FORMATO_DISCO, "items": [vars(x) for x in lista]}, f, ensure_ascii=False)
        os.replace(temporal, _CAT_DISCO)
    except Exception:  # noqa: BLE001
        pass


# TITULO RECORRER ARBOL

def _recorrer_arbol(fondo: bool) -> None:
    """Recorre TODO el árbol /marketnavigation de Capital, nivel por nivel y sin límite de profundidad, y va publicando los
    instrumentos en `_cat` a medida que los encuentra (así el buscador ya puede usar lo leído mientras sigue el recorrido).

    Antes solo se leían dos niveles y 60 nodos, y se cortaba a 1500 instrumentos: las acciones agotaban esos topes y quedaban
    fuera instrumentos como SILVER. Si algún nodo no se puede leer, el catálogo queda marcado como incompleto (no se guarda
    en disco y se reintenta pronto). `fondo` hace que las peticiones usen solo la mitad del cupo, para no frenar al usuario."""
    items: dict = {}
    fallos = 0
    leidos = 0
    inicio = time.time()
    try:
        if fondo:
            cap.marcar_hilo_fondo()
        raiz = _nav("")
        if raiz is None:
            fallos += 1
            nivel = []
        else:
            nivel = [(n.get("id", ""), _nombre_grupo(n.get("id", ""), n.get("name", ""))) for n in raiz.get("nodes", []) if n.get("id")]
        vistos = {nid for nid, _g in nivel}
        def leer_nodo(ng):
            """Lee un nodo en un hilo del grupo, marcándolo como de segundo plano (el marcado es por hilo y por cuenta)."""
            if fondo:
                cap.marcar_hilo_fondo()
            return ng[1], _nav(ng[0])

        with concurrent.futures.ThreadPoolExecutor(max_workers=_HILOS_RECORRIDO) as ex:
            while nivel and leidos < _MAX_NODOS and (time.time() - inicio) < _TIEMPO_RECORRIDO_S:
                resultados = list(ex.map(con_usuario(leer_nodo), nivel))
                siguiente = []
                for grupo, datos in resultados:
                    leidos += 1
                    if datos is None:
                        fallos += 1
                        continue
                    for m in datos.get("markets", []) or []:
                        ep = m.get("epic")
                        if ep and len(items) < _MAX_EPICS:
                            items.setdefault(ep, (m.get("instrumentName", ep), grupo, m.get("instrumentType", "")))
                    for sn in datos.get("nodes", []) or []:
                        sid = sn.get("id", "")
                        if sid and sid not in vistos:
                            vistos.add(sid)
                            siguiente.append((sid, grupo))
                nivel = siguiente
                with _CAT_CANDADO:
                    _cat.update(items=_lista_desde_items(items) if items else _cat["items"], nodos=leidos)
            if nivel:
                fallos += 1      # quedaron nodos sin leer por los topes
    except Exception as e:  # noqa: BLE001
        fallos += 1
        print(f"[CAPITAL shim] no se pudo cargar el catálogo: {e}")
    completo = fallos == 0 and len(items) > 0
    with _CAT_CANDADO:
        if items:
            _cat.update(items=_lista_desde_items(items))
        # Un recorrido fallido no pisa la marca de "catálogo completo" anterior y se reintenta pronto.
        _cat.update(proximo=time.time() + (_TTL_DISCO if completo else _REINTENTO_CATALOGO_S),
                    completo=completo or _cat["completo"], cargando=False, nodos=leidos)
    if completo:
        _guardar_catalogo_en_disco(_cat["items"])


# TITULO ACTUALIZAR CATALOGO

def _actualizar_catalogo(fondo: bool) -> None:
    """Lanza el recorrido del árbol en un hilo aparte si no hay otro en curso. No espera ni devuelve nada."""
    from herramientas.hilos import lanzar_hilo
    with _CAT_CANDADO:
        if _cat["cargando"]:
            return
        _cat["cargando"] = True
    lanzar_hilo(_recorrer_arbol, fondo, nombre="pj-catalogo-capital")


# TITULO CATALOGO ACTUAL

def catalogo_actual() -> tuple:
    """Devuelve `(lista, listo)` SIN esperar: `lista` es lo que se conoce del catálogo ahora mismo (puede estar incompleta
    mientras se recorre el árbol) y `listo` indica si ya se conoce el catálogo completo.

    La primera vez toma el archivo de disco (aunque tenga más de 24 h) y, si ya toca, rehace el recorrido en segundo plano.
    Nunca bloquea un clic del usuario."""
    with _CAT_CANDADO:
        vacio = not _cat["items"]
    if vacio:
        lista, marca = _catalogo_desde_disco()
        if lista:
            with _CAT_CANDADO:
                if not _cat["items"]:
                    _cat.update(items=lista, completo=True, proximo=marca + _TTL_DISCO)
    with _CAT_CANDADO:
        hay = bool(_cat["items"])
        toca = time.time() >= _cat["proximo"] and not _cat["cargando"]
    if toca:
        _actualizar_catalogo(fondo=hay)      # con catálogo previo es un refresco de fondo; sin él, es prioritario
    with _CAT_CANDADO:
        return list(_cat["items"]), bool(_cat["completo"])


# TITULO CATALOGO

def _catalogo(esperar_s: float = 60.0) -> list:
    """Catálogo de instrumentos de Capital para quien necesita la lista (Mercados, servidor de precios, agente).

    Si ya se conoce algo del catálogo (del disco o de un recorrido en curso) lo devuelve al instante. Si no hay nada todavía,
    espera (hasta `esperar_s`) a que el recorrido publique los primeros instrumentos, que llegan en pocos segundos. Si el
    recorrido falla devuelve, en último caso, los instrumentos más populares."""
    lista, _listo = catalogo_actual()
    fin = time.time() + esperar_s
    while not lista and time.time() < fin:
        with _CAT_CANDADO:
            en_curso = _cat["cargando"]
        if not en_curso:
            break
        time.sleep(0.25)
        lista, _listo = catalogo_actual()
    return lista or _lista_desde_items({})


# TITULO CATALOGO LISTO

def catalogo_listo() -> bool:
    """True si ya se conoce el catálogo completo de Capital (de disco o de un recorrido terminado)."""
    return catalogo_actual()[1]


# TITULO PROGRESO CATALOGO

def progreso_catalogo() -> tuple:
    """Devuelve `(instrumentos_conocidos, nodos_leidos)` del recorrido en curso, para mostrar avance mientras se carga."""
    with _CAT_CANDADO:
        return len(_cat["items"]), _cat["nodos"]


# Búsquedas ya hechas al servidor de Capital: texto en mayúsculas -> (momento, resultados).
_busquedas: dict = {}
_TTL_BUSQUEDA = 300


# TITULO BUSCAR SIMBOLOS

def buscar_simbolos(texto: str) -> list:
    """Busca instrumentos por texto DIRECTAMENTE en Capital (`GET /markets?searchTerm=`), con el mismo formato de objeto que
    `symbols_get`. Sirve de respaldo del catálogo: encuentra cualquier instrumento aunque el catálogo aún esté cargándose o no
    lo incluya. Guarda cada búsqueda 5 minutos y devuelve lista vacía si no hay conexión o el texto tiene menos de 2 letras."""
    t = (texto or "").strip()
    if len(t) < 2:
        return []
    clave = t.upper()
    previo = _busquedas.get(clave)
    if previo and (time.time() - previo[0]) < _TTL_BUSQUEDA:
        return previo[1]
    try:
        r = cap._pedir("GET", "/markets", parametros={"searchTerm": t})
        datos = r.json().get("markets", []) if (r is not None and r.status_code == 200) else None
    except Exception:  # noqa: BLE001
        datos = None
    if datos is None:
        return []            # fallo de red: no se guarda, para reintentar en la próxima búsqueda
    lista = [SimpleNamespace(name=m["epic"], visible=True, description=m.get("instrumentName") or m["epic"],
                             path=f"{_carpeta_catalogo(m.get('instrumentType'), 'Otros')}\\{m['epic']}")
             for m in datos if m.get("epic")]
    if len(_busquedas) > 500:
        _busquedas.clear()
    _busquedas[clave] = (time.time(), lista)
    return lista


# TITULO SYMBOLS GET

def symbols_get(*args: Any, **kwargs: Any) -> list:
    """Catálogo real de instrumentos de Capital (cacheado). Objetos con name/visible/
    description/path, como los símbolos de MT5."""
    return _catalogo()


# TITULO ACCOUNT INFO

# ===========================================================================
# Cuenta
# ===========================================================================
def account_info():
    """Equivale a `mt5.account_info`: devuelve balance, equity, margen y moneda de la cuenta de Capital con los nombres de campo de MT5, o None si no hay conexión."""
    c = cap.obtener_info_cuenta()
    if not c or "error" in c:
        return None
    return SimpleNamespace(
        login=c.get("login", 0), name=c.get("nombre", ""), server=c.get("servidor", ""),
        trade_mode=ACCOUNT_TRADE_MODE_DEMO if c.get("tipo") == "Demo" else ACCOUNT_TRADE_MODE_REAL,
        balance=c.get("balance", 0.0), equity=c.get("equity", 0.0), profit=c.get("profit", 0.0),
        margin=c.get("margin", 0.0), margin_free=c.get("margin_free", 0.0),
        margin_level=c.get("margin_level", 0.0), credit=c.get("credit", 0.0),
        leverage=c.get("leverage") or None, currency=c.get("currency", "USD"),
    )


# TITULO POSITIONS GET

# ===========================================================================
# Posiciones / órdenes / historial
# ===========================================================================
def positions_get(ticket: Any = None, symbol: str = None, **kwargs: Any) -> list:
    """Equivale a `mt5.positions_get`: devuelve las posiciones abiertas (ticket, símbolo, tipo, volumen en lotes, precios, SL/TP y hora), con filtro opcional por ticket o símbolo.

    El ticket es el dealId de Capital (texto) y `identifier` guarda el id de la orden pendiente que la abrió (lo usa el OCO).
    """
    datos = cap.leer_json("/positions")
    if datos is None:
        return []
    out = []
    for item in datos.get("positions", []):
        p = item.get("position", {}) or {}
        m = item.get("market", {}) or {}
        if ticket is not None and str(p.get("dealId")) != str(ticket):
            continue
        if symbol is not None and m.get("epic") != symbol:
            continue
        es_compra = p.get("direction", "").upper() == "BUY"
        out.append(SimpleNamespace(
            ticket=p.get("dealId", ""), symbol=m.get("epic", ""),
            identifier=p.get("workingOrderId") or p.get("dealId", ""),   # id de la pendiente que la abrió (OCO)
            type=POSITION_TYPE_BUY if es_compra else POSITION_TYPE_SELL,
            volume=float(p.get("size", 0.0) or 0.0) / cap.factor_lote(m.get("instrumentType", "")),
            price_open=float(p.get("level", 0.0) or 0.0),
            price_current=float(m.get("bid", 0.0) or 0.0) if es_compra else float(m.get("offer", 0.0) or 0.0),
            profit=float(p.get("upl", 0.0) or 0.0), swap=0.0,
            sl=float(p.get("stopLevel", 0.0) or 0.0), tp=float(p.get("profitLevel", 0.0) or 0.0),
            time=cap._epoch_utc(p.get("createdDateUTC", "") or p.get("createdDate", "")),
            comment="", magic=0,    # Capital no guarda comentario ni magic: el agente enlaza sus posiciones por ticket
        ))
    return out


# TITULO ORDERS GET

def orders_get(ticket: Any = None, **kwargs: Any) -> list:
    """Órdenes pendientes. NOTA: los nombres de campo de /workingorders se leen de forma
    defensiva (no se pudo observar una orden real); validar con una pendiente creada."""
    datos = cap.leer_json("/workingorders")
    if datos is None:
        return []
    out = []
    for item in datos.get("workingOrders", []):
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
            volume=float(w.get("orderSize", 0.0) or 0.0) / cap.factor_lote_epic(w.get("epic") or m.get("epic", "")),
            volume_current=float(w.get("orderSize", 0.0) or 0.0) / cap.factor_lote_epic(w.get("epic") or m.get("epic", "")),
            volume_initial=float(w.get("orderSize", 0.0) or 0.0) / cap.factor_lote_epic(w.get("epic") or m.get("epic", "")),
            price_open=float(w.get("orderLevel", 0.0) or 0.0),
            price_current=float(m.get("bid", 0.0) or 0.0),
            sl=float(w.get("stopLevel", 0.0) or 0.0), tp=float(w.get("profitLevel", 0.0) or 0.0),
            type_time=ORDER_TIME_GTC if not gtd else ORDER_TIME_SPECIFIED,
            time_expiration=cap._epoch_utc(gtd) if gtd else 0,
            time=0, comment="", magic=0,
        ))
    return out


# TITULO HISTORY DEALS GET

def history_deals_get(desde: Any = None, hasta: Any = None, **kwargs: Any) -> list:
    """Operaciones del historial. El campo de P/G realizado se lee de forma defensiva
    (validar con un cierre real). `entry` se marca OUT para que el cálculo de cerradas lo tome."""
    params = {}
    if isinstance(desde, datetime):
        params["from"] = desde.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")
    datos = cap.leer_json("/history/transactions", 15.0, params or None)
    if datos is None:
        return []
    out = []
    for t in datos.get("transactions", []):
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
            position_id=t.get("dealId", ""),    # id de la posición: con él `cap.detalle_operacion` trae símbolo, lado, lotes y precio
        ))
    out.sort(key=lambda d: d.time)    # MT5 las entrega de la más antigua a la más reciente
    return out


# TITULO FILA VELA

_CAMPOS_VELA = ("time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume")


class _FilaVela(dict):
    """Vela que se lee por nombre (`v["close"]`) o por posición (`v[4]`), como una fila del arreglo de MetaTrader 5.

    Las herramientas del agente leen las velas por posición (tiempo, apertura, máximo, mínimo, cierre, volumen); el resto del
    proyecto, por nombre. Como es un `dict`, `pd.DataFrame(velas)` también funciona."""

    def __getitem__(self, clave):
        """Con un entero devuelve el campo en esa posición (0 = time ... 4 = close); con un texto, el campo por nombre."""
        if isinstance(clave, int):
            return dict.__getitem__(self, _CAMPOS_VELA[clave])
        return dict.__getitem__(self, clave)


# TITULO VELAS DICTS

# ===========================================================================
# Velas
# ===========================================================================
def _velas_dicts(epic: str, timeframe, maximo: int = None, desde=None, hasta=None) -> list:
    """Pide velas a Capital y las devuelve como lista de filas (`_FilaVela`) con las claves de MT5 (`time`, `open`, `high`, `low`, `close`, `tick_volume`, `spread`).

    Recibe el epic, la temporalidad y, opcionalmente, la cantidad máxima y el rango de fechas. El spread de cada vela sale del bid y el ask
    de su cierre, en puntos. La temporalidad mensual se arma con velas semanales y diarias (Capital no tiene resolución mensual).
    """
    if int(timeframe if timeframe is not None else 16385) == TIMEFRAME_MN1:
        filas = cap._datos_mensuales(epic, int(maximo or 100))
        return [_FilaVela(time=f["time"], open=f["open"], high=f["high"], low=f["low"], close=f["close"],
                          tick_volume=f["tick_volume"], spread=f["spread"], real_volume=0) for f in filas]
    res = _TF_A_RES.get(int(timeframe) if timeframe is not None else 16385, "HOUR")
    f = desde.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") if isinstance(desde, datetime) else None
    h = hasta.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") if isinstance(hasta, datetime) else None
    crudas = cap._velas_crudas(epic, res, maximo=maximo, desde=f, hasta=h)
    punto = cap._punto_de(epic)
    out = []
    for v in crudas:
        out.append(_FilaVela(
            time=cap._epoch_utc(v.get("snapshotTimeUTC") or v.get("snapshotTime")),
            open=cap._medio(v.get("openPrice", {})), high=cap._medio(v.get("highPrice", {})),
            low=cap._medio(v.get("lowPrice", {})), close=cap._medio(v.get("closePrice", {})),
            tick_volume=v.get("lastTradedVolume", 0), spread=cap._spread_puntos(v.get("closePrice", {}), punto),
            real_volume=0,
        ))
    return out


# TITULO COPY RATES FROM POS

def copy_rates_from_pos(symbol: str, timeframe, start: int, count: int) -> list:
    """Devuelve una lista de dicts indexables por nombre (rates[i]['close']), como el
    structured array de MT5; `pd.DataFrame(rates)` también funciona."""
    return _velas_dicts(symbol, timeframe, maximo=int(start) + int(count))[-int(count):]


# TITULO COPY RATES RANGE

def copy_rates_range(symbol: str, timeframe, date_from, date_to) -> list:
    """Equivale a `mt5.copy_rates_range`: velas entre dos fechas (máximo 1000, el límite de Capital por consulta)."""
    return _velas_dicts(symbol, timeframe, maximo=1000, desde=date_from, hasta=date_to)


# TITULO ORDER CALC PROFIT

# ===========================================================================
# Cálculos de riesgo (aproximados con contractSize / marginFactor de Capital)
# ===========================================================================
def order_calc_profit(action: int, symbol: str, volume: float, price_open: float, price_close: float):
    """Equivale a `mt5.order_calc_profit`: calcula la ganancia o pérdida, en la moneda de la cuenta, de mover el precio de `price_open` a `price_close` con ese volumen en lotes. Devuelve None si no hay datos del instrumento."""
    s = _specs(symbol)
    if not s:
        return None
    signo = 1.0 if action == ORDER_TYPE_BUY else -1.0
    bruto = signo * float(volume) * s["contract"] * (float(price_close) - float(price_open))
    return bruto * _tasa_a_cuenta(s["moneda"])    # el resultado sale en la moneda de cotización: se pasa a la de la cuenta


# TITULO ORDER CALC MARGIN

def order_calc_margin(action: int, symbol: str, volume: float, price: float):
    """Equivale a `mt5.order_calc_margin`: calcula el margen que exige abrir ese volumen (en lotes) a ese precio, con el factor de margen de Capital y en la moneda de la cuenta. Devuelve None si no hay datos."""
    s = _specs(symbol)
    if not s:
        return None
    mf = s["margin_factor"] or 0.0
    return float(volume) * s["contract"] * float(price) * mf / 100.0 * _tasa_a_cuenta(s["moneda"])


# TITULO ORDER SEND

# ===========================================================================
# Envío de órdenes: enruta al backend Capital según la solicitud
# ===========================================================================
def order_send(solicitud: dict):
    """Interpreta la solicitud estilo MT5 y la enruta al backend Capital.
    Soporta las que arma el proyecto: DEAL de apertura y DEAL de cierre (con 'position')."""
    symbol = solicitud.get("symbol", "")
    volume = float(solicitud.get("volume", 0.0) or 0.0)
    if solicitud.get("position"):                     # cierre de una posición existente
        res = cap.cerrar_posicion(solicitud["position"])
    else:                                             # apertura a mercado
        tipo = "BUY" if solicitud.get("type") == ORDER_TYPE_BUY else "SELL"
        res = cap.ejecutar_orden_mercado(symbol, tipo, volume,
                                         stop_loss=float(solicitud.get("sl", 0.0) or 0.0),
                                         take_profit=float(solicitud.get("tp", 0.0) or 0.0))
    if "error" in res:
        _estado_error.valor = (1, res["error"])
        return SimpleNamespace(retcode=10013, comment=res["error"], order=0, price=0.0)
    return SimpleNamespace(retcode=TRADE_RETCODE_DONE, comment="Done",
                           order=res.get("order", solicitud.get("position", "")),
                           price=float(res.get("price", solicitud.get("price", 0.0)) or 0.0))


# TITULO VERSION

# ===========================================================================
# Totales / versión (los usa la capa del agente de solo lectura)
# ===========================================================================
def version():
    """Equivale a `mt5.version`: devuelve una versión ficticia que identifica este adaptador."""
    return (500, 0, "Capital.com shim")


# TITULO POSITIONS TOTAL

def positions_total() -> int:
    """Equivale a `mt5.positions_total`: cantidad de posiciones abiertas."""
    return len(positions_get())


# TITULO ORDERS TOTAL

def orders_total() -> int:
    """Equivale a `mt5.orders_total`: cantidad de órdenes pendientes."""
    return len(orders_get())


# TITULO SYMBOLS TOTAL

def symbols_total() -> int:
    """Equivale a `mt5.symbols_total`: cantidad de instrumentos del catálogo."""
    return len(symbols_get())


# TITULO HISTORY DEALS TOTAL

def history_deals_total(desde: Any = None, hasta: Any = None) -> int:
    """Equivale a `mt5.history_deals_total`: cantidad de operaciones del historial en el rango pedido."""
    return len(history_deals_get(desde, hasta))


# TITULO HISTORY ORDERS GET

def history_orders_get(desde: Any = None, hasta: Any = None, **kwargs: Any) -> list:
    """Equivale a `mt5.history_orders_get`: Capital no entrega el historial de órdenes, así que devuelve una lista vacía."""
    return []


# TITULO HISTORY ORDERS TOTAL

def history_orders_total(desde: Any = None, hasta: Any = None) -> int:
    """Equivale a `mt5.history_orders_total`: siempre 0 (Capital no entrega el historial de órdenes)."""
    return 0


# TITULO MARKET BOOK ADD

# ===========================================================================
# Profundidad de mercado (DOM): no disponible por REST
# ===========================================================================
def market_book_add(symbol: str) -> bool:
    """Equivale a `mt5.market_book_add`: Capital no publica libro de órdenes, así que devuelve False."""
    return False


# TITULO MARKET BOOK GET

def market_book_get(symbol: str):
    """Equivale a `mt5.market_book_get`: Capital no publica libro de órdenes, así que devuelve una lista vacía."""
    return []


# TITULO MARKET BOOK RELEASE

def market_book_release(symbol: str) -> bool:
    """Equivale a `mt5.market_book_release`: no hay libro que liberar; devuelve True."""
    return True


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara capital_mt5_compat .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
