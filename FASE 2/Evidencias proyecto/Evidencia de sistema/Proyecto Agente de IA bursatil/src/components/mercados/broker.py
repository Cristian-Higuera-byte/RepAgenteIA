# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara broker .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos del bróker (MT5): símbolos disponibles, resolución de nombres, estado del mercado y filas de la tabla.

Es la única capa de la página Mercados que habla con MetaTrader 5. Las consultas costosas se cachean con
`st.cache_data` y lanzan `SinDatos` cuando MT5 no responde, para que Streamlit no guarde resultados vacíos.
"""
import re

import streamlit as st
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from components.mercado_datos import cierre_previo as _cierre_previo
from components.mercado_datos.referencias import SinDatos
from components.mercados.constantes import CATALOGO
from tools.puente_mt5 import MT5_LOCK, obtener_datos_historicos, resolver_simbolo


def leer_atributo(info, attr):
    """Lee un atributo numérico de un objeto de MT5 (`symbol_info`); devuelve 0 si no existe o es vacío."""
    return getattr(info, attr, 0) or 0


@st.cache_data(ttl=600, show_spinner=False)
def _indice_broker_cache():
    """Construye el índice de símbolos del bróker, cacheado 10 minutos.

    Devuelve una tupla `(nombres, por_ticker)`: el conjunto de nombres de símbolo y un diccionario
    ticker en mayúsculas -> nombre real, extraído de la descripción de las acciones. Lanza `SinDatos` si MT5
    no devuelve ningún símbolo.
    """
    # Listado completo de símbolos del terminal (protegido con el candado de MT5)
    with MT5_LOCK:
        simbolos = mt5.symbols_get() or []
    if not simbolos:
        raise SinDatos("symbols_get")
    nombres = {s.name for s in simbolos}
    por_ticker = {}
    for s in simbolos:
        # "Apple Inc (AAPL.OQ)" -> AAPL ; se ignoran las variantes _turbo
        m = re.search(r"\(([A-Za-z0-9\-]+)(?:\.[A-Za-z]+)?\)\s*$", s.description or "")
        if m and "_turbo" not in s.name:
            por_ticker.setdefault(m.group(1).upper(), s.name)
    return nombres, por_ticker


def _indice_broker():
    """Devuelve el índice de símbolos del bróker, o `(set(), {})` si MT5 no está disponible."""
    try:
        return _indice_broker_cache()
    except Exception:
        return set(), {}


def resolver(candidatos) -> str | None:
    """Nombre real en el bróker del primer candidato que exista, o None.

    Recibe una lista de nombres posibles de un instrumento. Prueba, en orden y para cada candidato: el nombre
    resuelto por el puente de MT5, el mismo con sufijo `Cash`, y el primer futuro cuyo nombre empiece por
    `candidato-`. Si ninguno funciona, busca el candidato como ticker en la descripción de las acciones."""
    nombres, por_ticker = _indice_broker()
    # Sin índice (MT5 desconectado) no se puede resolver nada
    if not nombres:
        return None
    for c in candidatos:
        r = resolver_simbolo(c)
        if r in nombres:
            return r
        if c + "Cash" in nombres:                         # XM: FRA40Cash, SpainCash...
            return c + "Cash"
        futuros = sorted(n for n in nombres if n.upper().startswith(c.upper() + "-"))
        if futuros:                                       # XM: COCOA-DEC26
            return futuros[0]
    for c in candidatos:                                  # acciones: ticker en la descripción
        if c.upper() in por_ticker:
            return por_ticker[c.upper()]
    return None


@st.cache_data(ttl=600, show_spinner=False)
def _elementos_cache(categoria: str):
    """Resuelve los instrumentos del catálogo de una categoría que existen en el bróker (cacheado 10 min).

    Devuelve una lista de tuplas `(real, nombre, indice)`. Lanza `SinDatos` si no se resolvió ninguno."""
    out = []
    for i, (cands, nombre) in enumerate(CATALOGO.get(categoria, [])):
        real = resolver(cands)
        if real:
            out.append((real, nombre, i))
    if not out:
        raise SinDatos(categoria)        # MT5 sin conexión: no cachear el vacío
    return out


def elementos(categoria: str):
    """[(real, nombre, índice)] de la categoría, solo los que existen en el bróker."""
    try:
        return _elementos_cache(categoria)
    except Exception:
        return []


@st.cache_data(ttl=10, show_spinner=False)
def hora_servidor() -> int:
    """Hora del servidor del bróker (unix) ≈ último tick de las cripto (cotizan 24/7)."""
    # Se toma el tick más reciente entre varios símbolos de referencia
    mejor = 0
    for c in ("BTCUSD", "ETHUSD", "EURUSD"):
        try:
            with MT5_LOCK:
                t = mt5.symbol_info_tick(resolver_simbolo(c))
            mejor = max(mejor, int(getattr(t, "time", 0) or 0))
        except Exception:
            pass
    return mejor


def esta_abierto(t_tick: int) -> bool:
    """Indica si un mercado está abierto: su último tick (unix) debe estar a menos de 180 s de la hora del servidor."""
    ref = hora_servidor()
    return bool(t_tick and ref and ref - t_tick < 180)


@st.cache_data(ttl=300, show_spinner=False)
def _serie_cache(real: str, tf: int, n: int):
    """Descarga `n` velas del timeframe `tf` para el símbolo (cacheado 5 min). Lanza `SinDatos` si llega vacío."""
    df = obtener_datos_historicos(real, timeframe=tf, n_velas=n)
    if df is None or df.empty:
        raise SinDatos(real)
    return df


def serie(real: str, tf: int, n: int):
    """Devuelve el DataFrame de velas del símbolo, o None si MT5 no entregó datos."""
    try:
        return _serie_cache(real, tf, n)
    except Exception:
        return None


def fila(real: str, nombre: str):
    """Datos de una fila desde MT5, o None si no hay precio.

    Selecciona el símbolo en MT5, lee su información y su tick, y calcula precio, máximo y mínimo del día,
    cambio y porcentaje contra el cierre diario anterior. Devuelve un diccionario con las claves `sym`,
    `label`, `last`, `hi`, `lo`, `ch`, `pct`, `dig`, `t` (hora del tick) y `desc`."""
    # Información y último tick del símbolo, protegidos con el candado de MT5
    try:
        with MT5_LOCK:
            mt5.symbol_select(real, True)
            info = mt5.symbol_info(real)
            tick = mt5.symbol_info_tick(real) if info is not None else None
    except Exception:
        return None
    if info is None:
        return None
    # Precio: bid del tick; si no hay, bid/last de la info; si el mercado está cerrado, último cierre diario
    last = float(getattr(tick, "bid", 0) or 0) if tick is not None else 0.0
    if last <= 0:
        last = float(leer_atributo(info, "bid") or leer_atributo(info, "last"))
    if last <= 0:   # bolsa cerrada (acciones antes de la apertura): último cierre diario
        d1 = serie(real, mt5.TIMEFRAME_D1, 2)
        last = float(d1["close"].iloc[-1]) if d1 is not None else 0.0
    if last <= 0:
        return None
    dig = int(leer_atributo(info, "digits") or 2)
    # Rango del día (se corrige para que siempre contenga el precio actual)
    hi = float(leer_atributo(info, "bidhigh") or last)
    lo = float(leer_atributo(info, "bidlow") or last)
    # Variación del día contra el cierre de la vela diaria anterior
    prev = _cierre_previo(real)
    ch = (last - prev) if prev else 0.0
    pct = (ch / prev * 100) if prev else 0.0
    return {"sym": real, "label": nombre, "last": last, "hi": max(hi, last), "lo": min(lo, last),
            "ch": ch, "pct": pct, "dig": dig, "t": int(getattr(tick, "time", 0) or 0),
            "desc": getattr(info, "description", "") or ""}


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara broker .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
