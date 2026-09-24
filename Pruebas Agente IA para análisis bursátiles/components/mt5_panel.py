import matplotlib.pyplot as plt
import MetaTrader5 as mt5  # type: ignore[import-untyped]
import streamlit as st
from tools.mt5_bridge import inicializar_mt5, obtener_datos_historicos, obtener_precio_actual, obtener_info_cuenta

def renderizar_panel_mt5():
    st.markdown("### ⚡ TERMINAL DE TRADING EN VIVO — METATRADER 5")
    
    # Inicializar MT5
    if not inicializar_mt5():
        st.error("❌ No se pudo conectar con el terminal de MetaTrader 5. Asegúrate de que esté abierto en tu sesión.")
        return

    # Mostrar información rápida de la cuenta en la parte superior
    info_cta = obtener_info_cuenta()
    if "error" not in info_cta:
        col_b, col_e, col_p = st.columns(3)
        col_b.metric("Balance Cuenta", f"${info_cta['balance']:,.2f} {info_cta['currency']}")
        col_e.metric("Equity", f"${info_cta['equity']:,.2f} {info_cta['currency']}")
        col_p.metric("Beneficio Abierto", f"${info_cta['profit']:,.2f} {info_cta['currency']}")

    st.markdown("---")

    # Controles de selección de activo y temporalidad
    col_sym, col_tf = st.columns([2, 1])
    with col_sym:
        simbolo_activo = st.text_input("Símbolo / Activo (Market Watch)", value="EURUSD").upper()
    with col_tf:
        temporalidad_str = st.selectbox("Temporalidad", ["M1", "M5", "M15", "H1", "H4", "D1"], index=3)

    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    tf_elegido = tf_map.get(temporalidad_str, mt5.TIMEFRAME_H1)

    # Obtener cotización en tiempo real (Tick)
    info_tick = obtener_precio_actual(simbolo_activo)
    if "error" not in info_tick:
        st.markdown(f"""
            <div style='background-color: #161b22; padding: 12px; border-radius: 6px; border: 1px solid #30363d; margin-bottom: 12px; display: flex; justify-content: space-around; font-family: monospace;'>
                <div><b>ACTIVO:</b> {simbolo_activo}</div>
                <div><b>BID:</b> <span style='color: #f85149;'>{info_tick['bid']}</span></div>
                <div><b>ASK:</b> <span style='color: #3fb950;'>{info_tick['ask']}</span></div>
                <div><b>ULTIMA ACTUALIZACIÓN:</b> {info_tick['time']}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ El símbolo `{simbolo_activo}` no se encuentra activo o visible en el Market Watch de tu MT5.")

    # Descargar datos históricos para graficar
    df_historico = obtener_datos_historicos(simbolo_activo, timeframe=tf_elegido, n_velas=120)

    if not df_historico.empty:
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 4.5))
        fig.patch.set_facecolor('#0d1117')
        ax.set_facecolor('#161b22')

        # Gráfico de línea con precios reales de MT5
        ax.plot(df_historico.index, df_historico['close'], color='#3fb950', linewidth=2, label=f"Cierre {simbolo_activo}")
        ax.fill_between(df_historico.index, df_historico['close'], df_historico['close'].min() * 0.99, color='#238636', alpha=0.15)
        
        ax.set_title(f"Gráfico en Tiempo Real (MT5) — {simbolo_activo} [{temporalidad_str}]", color='#ffffff', fontsize=14, fontweight='bold', pad=12)
        ax.set_ylabel("Precio en USD / Pips", color='#8b949e', fontsize=11, fontweight='bold')
        ax.set_xlabel("Línea de Tiempo", color='#8b949e', fontsize=11, fontweight='bold')
        ax.grid(True, color='#30363d', linestyle='--', alpha=0.5)
        ax.tick_params(colors='#8b949e', labelsize=10)
        
        for spine in ax.spines.values():
            spine.set_edgecolor('#30363d')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.error("No se pudieron extraer datos históricos para graficar este activo.")