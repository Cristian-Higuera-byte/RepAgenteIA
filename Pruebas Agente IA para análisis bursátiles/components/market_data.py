import math
import streamlit as st
import MetaTrader5 as mt5  # type: ignore[import-untyped]
from tools.mt5_bridge import inicializar_mt5, obtener_precio_actual

def cargar_datos_mercado():
    # Inicializar conexión a MT5 de forma segura al cargar el mercado
    inicializar_mt5()

    # 1. Obtención dinámica de índices globales (barra superior)
    if "datos_indices_globales" not in st.session_state:
        st.session_state.datos_indices_globales = {
            "SP500": {"valor": 5432.18, "var": "+0.84%", "sube": True},
            "NASDAQ": {"valor": 17742.90, "var": "+1.22%", "sube": True},
            "DOW": {"valor": 39310.44, "var": "-0.31%", "sube": False},
            "BTC": {"valor": 67204.00, "var": "+2.90%", "sube": True}
        }

    # Intentar actualizar índices globales con MT5 o yfinance
    try:
        import yfinance as yf  # type: ignore[import-untyped]
        simbolos_indices = {
            "SP500": "^GSPC",
            "NASDAQ": "^IXIC",
            "DOW": "^DJI",
            "BTC": "BTC-USD"
        }
        for key, sym in simbolos_indices.items():
            t_obj = yf.Ticker(sym)
            hist = t_obj.history(period="3d")
            if not hist.empty and "Close" in hist.columns:
                val = hist["Close"].iloc[-1]
                if not math.isnan(float(val)):
                    actual = float(val)
                    anterior_val = hist["Close"].iloc[-2] if len(hist) > 1 else actual
                    anterior = float(anterior_val) if not math.isnan(float(anterior_val)) else actual
                    cambio = actual - anterior
                    porc = (cambio / anterior * 100) if anterior != 0 else 0.0
                    sube = cambio >= 0
                    
                    st.session_state.datos_indices_globales[key] = {
                        "valor": actual,
                        "var": f"{'+' if sube else ''}{porc:.2f}%",
                        "sube": sube
                    }
    except Exception:
        pass

    # 2. Carga segura de datos de mercado (Watchlist)
    # Soportando tickers tradicionales y activos directos de MT5 (como EURUSD, GBPUSD, etc.)
    tickers_watchlist = ["EURUSD", "GBPUSD", "USDJPY", "META", "MSFT", "NVDA", "AAPL"]

    if "datos_mercado_real" not in st.session_state:
        st.session_state.datos_mercado_real = {
            "EURUSD": {"nombre": "Euro / US Dollar", "mercado": "FOREX", "precio": 1.0850, "var": "+0.0012 (+0.11%)", "sube": True},
            "GBPUSD": {"nombre": "British Pound / US Dollar", "mercado": "FOREX", "precio": 1.3020, "var": "-0.0025 (-0.19%)", "sube": False},
            "USDJPY": {"nombre": "US Dollar / Japanese Yen", "mercado": "FOREX", "precio": 155.40, "var": "+0.45 (+0.29%)", "sube": True},
            "META": {"nombre": "Meta Platforms, Inc.", "mercado": "NASDAQ", "precio": 738.71, "var": "-2.54 (-0.34%)", "sube": False},
            "MSFT": {"nombre": "Microsoft Corporation", "mercado": "NASDAQ", "precio": 498.38, "var": "-3.23 (-0.64%)", "sube": False},
            "NVDA": {"nombre": "NVIDIA Corporation", "mercado": "NASDAQ", "precio": 1024.58, "var": "+1.97 (+0.87%)", "sube": True},
            "AAPL": {"nombre": "Apple Inc.", "mercado": "NASDAQ", "precio": 340.17, "var": "+1.19 (+0.35%)", "sube": True}
        }

    for ticker in tickers_watchlist:
        # Asegurar que el ticker exista en el estado inicial
        if ticker not in st.session_state.datos_mercado_real:
            st.session_state.datos_mercado_real[ticker] = {
                "nombre": ticker,
                "mercado": "MT5 / General",
                "precio": 100.0,
                "var": "+0.00 (0.00%)",
                "sube": True,
            }

        # Intento 1: Consultar cotización en tiempo real vía MetaTrader 5
        try:
            info_tick = obtener_precio_actual(ticker)
            if "error" not in info_tick:
                precio_actual = info_tick['last'] if info_tick['last'] > 0 else info_tick['bid']
                if precio_actual > 0:
                    # Si MT5 responde correctamente, actualizamos su precio en vivo
                    datos_antiguos = st.session_state.datos_mercado_real[ticker]
                    precio_anterior = datos_antiguos.get("precio", precio_actual)
                    cambio = precio_actual - precio_anterior
                    porcentaje = (cambio / precio_anterior * 100) if precio_anterior != 0 else 0.0
                    sube = cambio >= 0

                    st.session_state.datos_mercado_real[ticker]["precio"] = precio_actual
                    st.session_state.datos_mercado_real[ticker]["sube"] = sube
                    continue
        except Exception:
            pass

        # Intento 2: Respaldo con yfinance para acciones tradicionales si MT5 no las tiene activas
        try:
            import yfinance as yf  # type: ignore[import-untyped]
            t_obj = yf.Ticker(ticker)
            hist = t_obj.history(period="5d")
            if not hist.empty and "Close" in hist.columns:
                val = hist["Close"].iloc[-1]
                if not math.isnan(float(val)):
                    precio_actual = float(val)
                    valor_anterior = hist["Close"].iloc[-2] if len(hist) > 1 else val
                    precio_anterior = float(valor_anterior) if not math.isnan(float(valor_anterior)) else precio_actual
                    cambio = precio_actual - precio_anterior
                    porcentaje = (cambio / precio_anterior * 100) if precio_anterior != 0 else 0.0
                    sube = cambio >= 0

                    st.session_state.datos_mercado_real[ticker]["precio"] = precio_actual
                    st.session_state.datos_mercado_real[ticker]["var"] = f"{'+' if sube else ''}{cambio:.2f} ({'+' if sube else ''}{porcentaje:.2f}%)"
                    st.session_state.datos_mercado_real[ticker]["sube"] = sube
        except Exception:
            pass