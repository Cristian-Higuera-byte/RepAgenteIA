import streamlit as st
import MetaTrader5 as mt5  # type: ignore[import-untyped]

def renderizar_watchlist():
    # Lista de activos oficiales extraídos directamente de MetaTrader 5 o respaldados en la sesión
    # Puedes personalizar esta lista con los símbolos exactos que tengas en tu Market Watch de MT5
    tickers_watchlist = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD", "ETHUSD", "US30"]
    
    # Asegurar que existan datos en session_state para estos símbolos
    info_activos_real = st.session_state.get("datos_mercado_real", {})

    st.markdown("### 📊 LISTA DE ACTIVOS (MT5)")
    st.caption("Precios institucionales en tiempo real")

    if "activo_seleccionado" not in st.session_state:
        st.session_state.activo_seleccionado = "EURUSD"

    for ticker in tickers_watchlist:
        # Obtener información del activo, con valores por defecto seguros si aún no cargan
        item = info_activos_real.get(ticker, {
            "nombre": ticker, 
            "precio": 1.0000, 
            "var": "+0.00 (0.00%)", 
            "sube": True
        })
        
        is_selected = (st.session_state.activo_seleccionado == ticker)
        
        bg_color = "#1f2937" if is_selected else "#161b22"
        border_color = "#58a6ff" if is_selected else "#30363d"
        color_var = "#3fb950" if item.get("sube", True) else "#f85149"

        precio_val = item.get('precio', 1.0)
        # Formato dinámico de decimales según el tipo de activo (Forex/Metales vs Cripto/Índices)
        formato_precio = f"${precio_val:,.2f}" if precio_val > 100 else f"{precio_val:,.5f}"

        st.markdown(f"""
            <div style='background-color: {bg_color}; padding: 12px 14px; border-radius: 6px; border: 1px solid {border_color}; margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 700; font-size: 16px; color: #ffffff;'>{ticker}</span>
                    <span style='font-family: monospace; font-size: 16px; font-weight: bold; color: #ffffff;'>{formato_precio}</span>
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 4px;'>
                    <span style='font-size: 13px; color: #8b949e;'>{item.get('nombre', ticker)}</span>
                    <span style='font-size: 13px; font-weight: bold; color: {color_var};'>{item.get('var', '+0.00%')}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button(f"Seleccionar {ticker}", key=f"btn_wl_real_{ticker}", use_container_width=True):
            st.session_state.activo_seleccionado = ticker
            st.rerun()

    st.markdown("---")
    if st.button("+ Add Holdings", use_container_width=True):
        st.toast("Función para agregar nuevos símbolos de MT5 próximamente.")