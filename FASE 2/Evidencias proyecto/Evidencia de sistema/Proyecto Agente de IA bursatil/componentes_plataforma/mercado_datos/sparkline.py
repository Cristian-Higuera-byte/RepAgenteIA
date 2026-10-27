# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara sparkline .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Mini-gráfico (sparkline) de cada símbolo: semilla con histórico M1 y buffer que crece con cada tick.

El buffer vive en `st.session_state["_spark"]` (símbolo -> lista de precios) y nunca supera `SPARK_MAX` puntos.
"""
import streamlit as st
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from componentes_plataforma.mercado_datos.referencias import SinDatos
from herramientas.cache_proceso import cache_proceso
from herramientas.puente_mt5 import obtener_datos_historicos

# Puntos máximos del mini-gráfico (sparkline) por símbolo
SPARK_MAX = 40


# TITULO HISTORIAL SPARKLINE CACHE

@cache_proceso(tiempo_vida=120)
def _historial_sparkline_cache(simbolo: str) -> list:
    """Pide a MT5 las últimas 30 velas M1 y devuelve sus cierres (como máximo `SPARK_MAX`).

    Lanza `SinDatos` si no llega histórico, para que `st.cache_data` no cachee una lista vacía.
    Cacheado 120 s por símbolo.
    """
    tabla_datos = obtener_datos_historicos(simbolo, timeframe=mt5.TIMEFRAME_M1, n_velas=30)
    if tabla_datos is None or tabla_datos.empty or "close" not in tabla_datos.columns:
        raise SinDatos(simbolo)
    return [float(x) for x in tabla_datos["close"].tolist()][-SPARK_MAX:]


# TITULO HISTORIAL SPARKLINE

def historial_sparkline(simbolo: str) -> list:
    """Últimos ~30 cierres (M1) para sembrar el sparkline. Cacheado 2 min.
    Hallazgo: en un símbolo recién agregado (p. ej. GOLD o Adidas en XM) la
    primera lectura viene VACÍA porque el terminal todavía está descargando su
    historial; antes ese [] se cacheaba y el mini-gráfico quedaba plano.

    Devuelve una lista de floats, o una lista vacía si todavía no hay datos."""
    try:
        return _historial_sparkline_cache(simbolo)
    except Exception:
        return []


# TITULO ASEGURAR SEMILLA

def asegurar_semilla(simbolo: str):
    """Si el sparkline de un símbolo está vacío o casi (recién agregado, o la
    primera lectura vino vacía), lo vuelve a sembrar con el histórico M1.

    Modifica `st.session_state["_spark"][simbolo]` anteponiendo el histórico a lo que ya hubiera en el buffer."""
    # Buffer actual del símbolo (se crea el diccionario global si no existe)
    spark = st.session_state.setdefault("_spark", {})
    buf = spark.get(simbolo) or []
    # Con 5 puntos o más el gráfico ya se ve bien: no se vuelve a sembrar
    if len(buf) >= 5:
        return
    historial = historial_sparkline(simbolo)
    if historial:
        # Histórico primero, ticks ya acumulados al final; se recorta al máximo permitido
        spark[simbolo] = (historial + buf)[-SPARK_MAX:]


# TITULO EMPUJAR MINILINEA

def empujar_minilinea(simbolo: str, precio: float):
    """Agrega un precio al buffer del sparkline (crece con el refresco en vivo).

    Ignora precios vacíos o no positivos y descarta los puntos más antiguos al superar `SPARK_MAX`."""
    if not precio or precio <= 0:
        return
    buf = st.session_state.setdefault("_spark", {}).setdefault(simbolo, [])
    buf.append(float(precio))
    # Recorta por el principio para conservar solo los últimos SPARK_MAX puntos
    if len(buf) > SPARK_MAX:
        del buf[:-SPARK_MAX]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara sparkline .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
