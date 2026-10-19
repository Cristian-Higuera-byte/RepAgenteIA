# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara velas .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Velas OHLC de MT5 en el formato que espera Lightweight Charts.

Expone `obtener_velas`, que usan las rutas GET /velas y /ultima de manejador.py.
Todas las lecturas a MT5 se serializan con CANDADO_MT5 (la API no es thread-safe).

Las peticiones grandes (el historial que pide el replay, 3000 velas o más) se guardan unos segundos en memoria: el
gráfico las pide por adelantado y así, al pulsar «Replay», la respuesta es inmediata. Si MT5 todavía no tiene el
historial de un activo (lo descarga la primera vez que se le pide), se reintenta antes de rendirse.
"""
import time

from tools.puente_mt5 import inicializar_mt5, obtener_datos_historicos
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from .constantes import CANDADO_MT5, TF_MAP

# Desde cuántas velas una respuesta se guarda en memoria, cuántos segundos vale y cuántas respuestas se conservan.
_N_MIN_CACHE = 3000
_TTL_CACHE = 45.0
_MAX_CACHE = 32
# Respuestas guardadas: (símbolo, tf, n) -> (instante, velas).
_CACHE: dict = {}
# Intentos de lectura cuando MT5 devuelve vacío (descarga de historial en curso) y pausa entre ellos, en segundos.
_REINTENTOS = 3
_PAUSA = 0.5


def _leer(simbolo: str, tf: str, n: int) -> list:
    """Lee `n` velas de MT5 y las convierte a la lista de dicts del gráfico (lista vacía si MT5 no entrega datos).

    Convierte por columnas, no fila por fila: con 5000 velas es mucho más rápido. Cada valor se redondea con `round`
    de Python, igual que antes. Inicializa MT5 y consulta el histórico bajo CANDADO_MT5."""
    with CANDADO_MT5:
        inicializar_mt5()
        df = obtener_datos_historicos(simbolo, timeframe=TF_MAP.get(tf, mt5.TIMEFRAME_H1), n_velas=n)
    if df.empty:
        return []
    tiempos = [int(t.timestamp()) for t in df.index]
    abre = [round(x, 5) for x in df["open"].astype(float).tolist()]
    alto = [round(x, 5) for x in df["high"].astype(float).tolist()]
    bajo = [round(x, 5) for x in df["low"].astype(float).tolist()]
    cierra = [round(x, 5) for x in df["close"].astype(float).tolist()]
    volumen = df["tick_volume"].astype(float).tolist()
    spread = df["spread"].astype(float).tolist() if "spread" in df.columns else [0.0] * len(tiempos)   # puntos; lo usa el backtest
    return [{"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v, "spread": sp}
            for t, o, h, l, c, v, sp in zip(tiempos, abre, alto, bajo, cierra, volumen, spread)]


def obtener_velas(simbolo: str, tf: str, n: int) -> list:
    """Devuelve una lista de velas OHLC de MT5 en formato JSON para Lightweight Charts.

    Recibe el símbolo, la temporalidad como texto (clave de TF_MAP; si no existe se usa H1)
    y la cantidad `n` de velas. Cada vela es un dict con time (segundos UNIX), open, high,
    low, close (redondeados a 5 decimales), volume (tick_volume) y spread (puntos, 0.0 si
    el dato no existe). Devuelve una lista vacía si MT5 no entrega datos.
    Las peticiones de `_N_MIN_CACHE` velas o más se sirven de memoria durante `_TTL_CACHE` segundos. Si MT5 devuelve
    vacío se reintenta `_REINTENTOS` veces y, para peticiones grandes, se prueba por último con 500 velas.
    Efectos: inicializa MT5 y consulta el histórico bajo CANDADO_MT5.
    """
    grande = n >= _N_MIN_CACHE
    clave = (simbolo, tf, n)
    if grande:
        guardada = _CACHE.get(clave)
        if guardada and time.monotonic() - guardada[0] < _TTL_CACHE:
            return guardada[1]
    velas = _leer(simbolo, tf, n)
    intento = 1
    while not velas and intento < _REINTENTOS:
        time.sleep(_PAUSA)
        velas = _leer(simbolo, tf, n)
        intento += 1
    if not velas and n > 500:
        velas = _leer(simbolo, tf, 500)
    if grande and velas:
        if len(_CACHE) >= _MAX_CACHE:
            _CACHE.pop(min(_CACHE, key=lambda k: _CACHE[k][0]), None)
        _CACHE[clave] = (time.monotonic(), velas)
    return velas


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara velas .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
