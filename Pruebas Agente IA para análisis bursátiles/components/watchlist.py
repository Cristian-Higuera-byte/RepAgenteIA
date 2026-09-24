import streamlit as st

def renderizar_watchlist():
    tickers_watchlist = ["META", "MSFT", "AMZN", "NVDA", "GOOG", "AAPL", "TSLA"]
    info_activos_real = st.session_state.datos_mercado_real

    st.markdown("### 📊 LISTA DE ACTIVOS")
    st.caption("Precios institucionales en tiempo real")

    if "activo_seleccionado" not in st.session_state:
        st.session_state.activo_seleccionado = "NVDA"

    for ticker in tickers_watchlist:
        item = info_activos_real.get(ticker, {"nombre": ticker, "precio": 100.0, "var": "0.00%", "sube": True})
        is_selected = (st.session_state.activo_seleccionado == ticker)
        
        bg_color = "#1f2937" if is_selected else "#161b22"
        border_color = "#58a6ff" if is_selected else "#30363d"
        color_var = "#3fb950" if item.get("sube", True) else "#f85149"

        st.markdown(f"""
            <div style='background-color: {bg_color}; padding: 12px 14px; border-radius: 6px; border: 1px solid {border_color}; margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 700; font-size: 16px; color: #ffffff;'>{ticker}</span>
                    <span style='font-family: monospace; font-size: 16px; font-weight: bold; color: #ffffff;'>${item['precio']:,.2f}</span>
                </div>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 4px;'>
                    <span style='font-size: 13px; color: #8b949e;'>{item['nombre']}</span>
                    <span style='font-size: 13px; font-weight: bold; color: {color_var};'>{item['var']}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button(f"Seleccionar {ticker}", key=f"btn_wl_real_{ticker}", use_container_width=True):
            st.session_state.activo_seleccionado = ticker
            st.rerun()

    st.markdown("---")
    if st.button("+ Add Holdings", use_container_width=True):
        st.toast("Función para agregar nuevos activos próximamente.")