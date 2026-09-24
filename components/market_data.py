import streamlit as st
import math

def cargar_datos_mercado():
    # 1. Obtención dinámica de índices globales (barra superior)
    if "datos_indices_globales" not in st.session_state:
        st.session_state.datos_indices_globales = {
            "SP500": {"valor": 5432.18, "var": "+0.84%", "sube": True},
            "NASDAQ": {"valor": 17742.90, "var": "+1.22%", "sube": True},
            "DOW": {"valor": 39310.44, "var": "-0.31%", "sube": False},
            "BTC": {"valor": 67204.00, "var": "+2.90%", "sube": True}
        }

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
    tickers_watchlist = ["META", "MSFT", "AMZN", "NVDA", "GOOG", "AAPL", "TSLA"]

    if "datos_mercado_real" not in st.session_state:
        st.session_state.datos_mercado_real = {
            "META": {"nombre": "Meta Platforms, Inc.", "mercado": "NASDAQ", "precio": 738.71, "var": "-2.54 (-0.34%)", "sube": False},
            "MSFT": {"nombre": "Microsoft Corporation", "mercado": "NASDAQ", "precio": 498.38, "var": "-3.23 (-0.64%)", "sube": False},
            "AMZN": {"nombre": "Amazon.com, Inc.", "mercado": "NASDAQ", "precio": 255.04, "var": "-3.41 (-1.32%)", "sube": False},
            "NVDA": {"nombre": "NVIDIA Corporation", "mercado": "NASDAQ", "precio": 1024.58, "var": "+1.97 (+0.87%)", "sube": True},
            "GOOG": {"nombre": "Alphabet Inc.", "mercado": "NASDAQ", "precio": 347.75, "var": "-3.12 (-0.89%)", "sube": False},
            "AAPL": {"nombre": "Apple Inc.", "mercado": "NASDAQ", "precio": 340.17, "var": "+1.19 (+0.35%)", "sube": True},
            "TSLA": {"nombre": "Tesla, Inc.", "mercado": "NASDAQ", "precio": 379.54, "var": "+4.33 (+1.15%)", "sube": True}
        }

    try:
        import yfinance as yf  # type: ignore[import-untyped]
        for ticker in tickers_watchlist:
            t_obj = yf.Ticker(ticker)
            hist = t_obj.history(period="5d")
            if not hist.empty and "Close" in hist.columns:
                val = hist["Close"].iloc[-1]
                if val == val: 
                    precio_actual = float(val)
                    valor_anterior = hist["Close"].iloc[-2] if len(hist) > 1 else val
                    precio_anterior = float(valor_anterior) if valor_anterior == valor_anterior else precio_actual
                    cambio = precio_actual - precio_anterior
                    porcentaje = (cambio / precio_anterior * 100) if precio_anterior != 0 else 0.0
                    sube = cambio >= 0

                    st.session_state.datos_mercado_real[ticker]["precio"] = precio_actual
                    st.session_state.datos_mercado_real[ticker]["var"] = f"{'+' if sube else ''}{cambio:.2f} ({'+' if sube else ''}{porcentaje:.2f}%)"
                    st.session_state.datos_mercado_real[ticker]["sube"] = sube
    except Exception:
        pass

    for t in tickers_watchlist:
        if t not in st.session_state.datos_mercado_real:
            st.session_state.datos_mercado_real[t] = {
                "nombre": t,
                "mercado": "NASDAQ",
                "precio": 150.0,
                "var": "+0.00 (0.00%)",
                "sube": True,
            }