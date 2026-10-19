# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara referencias .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Referencias de precio de un símbolo: cierre diario anterior y variación del día.

La variación del día se calcula contra el cierre de la vela diaria anterior de MT5, la misma base que usan
Favoritos, la lista de activos y el feed en vivo, para que todas las vistas muestren el mismo número.
"""
import streamlit as st
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from tools.puente_mt5 import obtener_datos_historicos


class SinDatos(Exception):
    """Se lanza dentro de las funciones cacheadas cuando MT5 aún no entrega
    histórico: st.cache_data NO cachea excepciones, así se reintenta luego."""


@st.cache_data(ttl=300, show_spinner=False)
def _cierre_previo_cache(simbolo: str) -> float:
    """Lee de MT5 las dos últimas velas D1 y devuelve el cierre de la penúltima (cierre del día anterior).

    Lanza `SinDatos` si MT5 no entrega al menos dos velas, para que `st.cache_data` no guarde el fallo.
    Resultado cacheado 300 s por símbolo.
    """
    df = obtener_datos_historicos(simbolo, timeframe=mt5.TIMEFRAME_D1, n_velas=2)
    if df is None or len(df) < 2:
        raise SinDatos(simbolo)
    return float(df["close"].iloc[-2])


def cierre_previo(simbolo: str):
    """Cierre de la vela diaria anterior (base de la variación del día, igual
    que el feed en vivo de servidor_datos.py). Cacheado 5 min (solo si hay dato).

    Devuelve el cierre como float, o None si MT5 no entregó histórico o hubo cualquier error."""
    try:
        return _cierre_previo_cache(simbolo)
    except Exception:
        return None


def variacion(simbolo: str, precio: float, decimales: int):
    """(texto, sube) de la variación del día, o None si no hay referencia.

    Recibe el símbolo, el precio actual y los decimales a mostrar. Devuelve una tupla con el texto
    `+cambio (+porcentaje%)` y un booleano que indica si el cambio es no negativo; devuelve None si falta el
    cierre previo o el precio.
    """
    previo = cierre_previo(simbolo)
    # Sin cierre previo (o sin precio) no hay base para calcular la variación
    if not previo or not precio:
        return None
    cambio = precio - previo
    return f"{cambio:+.{decimales}f} ({cambio / previo * 100:+.2f}%)", cambio >= 0


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara referencias .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
