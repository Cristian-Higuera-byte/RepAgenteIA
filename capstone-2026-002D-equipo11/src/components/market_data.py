import math
import streamlit as st
import MetaTrader5 as mt5  # type: ignore[import-untyped]
from tools.mt5_bridge import (
    MT5_LOCK, inicializar_mt5, obtener_precio_actual, obtener_datos_historicos, resolver_simbolo,
)

# Puntos máximos del mini-gráfico (sparkline) por símbolo
_SPARK_MAX = 40


class _SinDatos(Exception):
    """Se lanza dentro de las funciones cacheadas cuando MT5 aún no entrega
    histórico: st.cache_data NO cachea excepciones, así se reintenta luego."""


@st.cache_data(ttl=120, show_spinner=False)
def _historial_sparkline_cache(simbolo: str) -> list:
    df = obtener_datos_historicos(simbolo, timeframe=mt5.TIMEFRAME_M1, n_velas=30)
    if df is None or df.empty or "close" not in df.columns:
        raise _SinDatos(simbolo)
    return [float(x) for x in df["close"].tolist()][-_SPARK_MAX:]


def _historial_sparkline(simbolo: str) -> list:
    """Últimos ~30 cierres (M1) para sembrar el sparkline. Cacheado 2 min.
    Hallazgo: en un símbolo recién agregado (p. ej. GOLD o Adidas en XM) la
    primera lectura viene VACÍA porque el terminal todavía está descargando su
    historial; antes ese [] se cacheaba y el mini-gráfico quedaba plano."""
    try:
        return _historial_sparkline_cache(simbolo)
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def _cierre_previo_cache(simbolo: str) -> float:
    df = obtener_datos_historicos(simbolo, timeframe=mt5.TIMEFRAME_D1, n_velas=2)
    if df is None or len(df) < 2:
        raise _SinDatos(simbolo)
    return float(df["close"].iloc[-2])


def _cierre_previo(simbolo: str):
    """Cierre de la vela diaria anterior (base de la variación del día, igual
    que el feed en vivo de servidor_datos.py). Cacheado 5 min (solo si hay dato)."""
    try:
        return _cierre_previo_cache(simbolo)
    except Exception:
        return None


def _asegurar_semilla(simbolo: str):
    """Si el sparkline de un símbolo está vacío o casi (recién agregado, o la
    primera lectura vino vacía), lo vuelve a sembrar con el histórico M1."""
    spark = st.session_state.setdefault("_spark", {})
    buf = spark.get(simbolo) or []
    if len(buf) >= 5:
        return
    hist = _historial_sparkline(simbolo)
    if hist:
        spark[simbolo] = (hist + buf)[-_SPARK_MAX:]


def _variacion(simbolo: str, precio: float, decimales: int):
    """(texto, sube) de la variación del día, o None si no hay referencia."""
    previo = _cierre_previo(simbolo)
    if not previo or not precio:
        return None
    cambio = precio - previo
    return f"{cambio:+.{decimales}f} ({cambio / previo * 100:+.2f}%)", cambio >= 0


def _empujar_spark(simbolo: str, precio: float):
    """Agrega un precio al buffer del sparkline (crece con el refresco en vivo)."""
    if not precio or precio <= 0:
        return
    buf = st.session_state.setdefault("_spark", {}).setdefault(simbolo, [])
    buf.append(float(precio))
    if len(buf) > _SPARK_MAX:
        del buf[:-_SPARK_MAX]
from tools import watchlist_manager as wl


def construir_entrada(simbolo: str) -> dict:
    """Arma la entrada de un símbolo para la watchlist (nombre, categoría, precio)
    usando el nombre EXACTO de MT5 (sin limpiar los '...')."""
    try:
        sim_real = resolver_simbolo(simbolo)  # nombre real en ESTE terminal (con/sin '...')
        with MT5_LOCK:
            mt5.symbol_select(sim_real, True)
            info = mt5.symbol_info(sim_real)
    except Exception:
        info = None
    nombre = (info.description if info and getattr(info, "description", "") else wl.nombre_visible(simbolo))
    mercado = wl.categoria_simbolo(getattr(info, "path", "") if info else "", simbolo)
    precio = 0.0
    try:
        tick = obtener_precio_actual(simbolo)
        if "error" not in tick:
            precio = tick.get("last", 0) if tick.get("last", 0) > 0 else tick.get("bid", 0)
    except Exception:
        pass
    var = _variacion(simbolo, float(precio or 0.0), 2 if precio > 100 else 5)
    return {
        "nombre": nombre,
        "mercado": mercado,
        "precio": float(precio or 0.0),
        "var": var[0] if var else "+0.00 (0.00%)",
        "sube": var[1] if var else True,
    }


def cargar_datos_mercado():
    # Inicializar conexión a MT5 de forma segura al cargar el mercado
    inicializar_mt5()

    # Si ya se cargó una vez, no repetir el fetch pesado; los fragmentos
    # (actualizar_precios_mt5) mantienen los precios en vivo.
    if st.session_state.get("datos_cargados"):
        return

    # 1. Índices globales (barra superior) — se mantiene con yfinance
    if "datos_indices_globales" not in st.session_state:
        st.session_state.datos_indices_globales = {
            "SP500": {"valor": 5432.18, "var": "+0.84%", "sube": True},
            "NASDAQ": {"valor": 17742.90, "var": "+1.22%", "sube": True},
            "DOW": {"valor": 39310.44, "var": "-0.31%", "sube": False},
            "BTC": {"valor": 67204.00, "var": "+2.90%", "sube": True},
        }
    try:
        import yfinance as yf  # type: ignore[import-untyped]
        simbolos_indices = {"SP500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI", "BTC": "BTC-USD"}
        for key, sym in simbolos_indices.items():
            hist = yf.Ticker(sym).history(period="3d")
            if not hist.empty and "Close" in hist.columns:
                val = hist["Close"].iloc[-1]
                if not math.isnan(float(val)):
                    actual = float(val)
                    anterior_val = hist["Close"].iloc[-2] if len(hist) > 1 else actual
                    anterior = float(anterior_val) if not math.isnan(float(anterior_val)) else actual
                    cambio = actual - anterior
                    porc = (cambio / anterior * 100) if anterior != 0 else 0.0
                    st.session_state.datos_indices_globales[key] = {
                        "valor": actual, "var": f"{'+' if cambio >= 0 else ''}{porc:.2f}%", "sube": cambio >= 0}
    except Exception:
        pass

    # 2. Watchlist del USUARIO (desde Supabase; si es nuevo, se siembra el default)
    usuario = st.session_state.get("usuario_info", {})
    uid = usuario.get("id") if isinstance(usuario, dict) else None
    simbolos = wl.obtener_watchlist(uid)
    if not simbolos:
        simbolos = wl.sembrar_defaults(uid)
    st.session_state.watchlist_simbolos = simbolos

    # 3. Construir los datos de mercado de esos símbolos (nombre EXACTO para MT5)
    datos = {}
    for sym in simbolos:
        datos[sym] = construir_entrada(sym)
        # Sembrar el sparkline con histórico M1 (se reintenta si vino vacío)
        _asegurar_semilla(sym)
    st.session_state.datos_mercado_real = datos

    st.session_state.datos_cargados = True


def actualizar_precios_mt5():
    """Actualización LIGERA de precios de la watchlist desde MT5 (tick en vivo).
    Usa el nombre EXACTO del símbolo (con '...') — sin limpiarlo."""
    inicializar_mt5()
    datos = st.session_state.get("datos_mercado_real")
    if not datos:
        return
    for simbolo in list(datos.keys()):
        try:
            info_tick = obtener_precio_actual(simbolo)
            if "error" in info_tick:
                continue
            precio_actual = info_tick.get("last", 0) if info_tick.get("last", 0) > 0 else info_tick.get("bid", 0)
            if precio_actual and precio_actual > 0:
                precio_anterior = datos[simbolo].get("precio", precio_actual)
                cambio = precio_actual - precio_anterior
                porcentaje = (cambio / precio_anterior * 100) if precio_anterior else 0.0
                decimales = 2 if precio_actual > 100 else 5
                datos[simbolo]["precio"] = precio_actual
                var = _variacion(simbolo, precio_actual, decimales)
                if var:                                   # variación del día
                    datos[simbolo]["var"], datos[simbolo]["sube"] = var
                else:                                     # sin referencia: vs. tick anterior
                    datos[simbolo]["sube"] = cambio >= 0
                    if cambio != 0:
                        datos[simbolo]["var"] = f"{cambio:+.{decimales}f} ({porcentaje:+.2f}%)"
                _asegurar_semilla(simbolo)   # símbolos agregados después de la carga
                _empujar_spark(simbolo, precio_actual)
        except Exception:
            pass