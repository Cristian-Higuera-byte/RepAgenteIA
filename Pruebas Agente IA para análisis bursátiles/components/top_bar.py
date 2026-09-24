import streamlit as st

def renderizar_barra_superior():
    indices = st.session_state.datos_indices_globales

    c_top1, c_top2, c_top3, c_top4, c_top5, c_top6 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5, 1])

    with c_top1:
        st.markdown("**Dashboard** <span style='font-size:20px; color:#8b949e;'>TERMINAL V1.0</span>", unsafe_allow_html=True)

    with c_top2:
        color_sp = "#3fb950" if indices["SP500"]["sube"] else "#f85149"
        val_sp = f"{indices['SP500']['valor']:,.2f}" if indices['SP500']['valor'] > 1000 else f"{indices['SP500']['valor']:.2f}"
        st.markdown(f"S&P 500 <span style='color:{color_sp};'>{val_sp} ({indices['SP500']['var']})</span>", unsafe_allow_html=True)

    with c_top3:
        color_nas = "#3fb950" if indices["NASDAQ"]["sube"] else "#f85149"
        val_nas = f"{indices['NASDAQ']['valor']:,.2f}"
        st.markdown(f"NASDAQ <span style='color:{color_nas};'>{val_nas} ({indices['NASDAQ']['var']})</span>", unsafe_allow_html=True)

    with c_top4:
        color_dow = "#3fb950" if indices["DOW"]["sube"] else "#f85149"
        val_dow = f"{indices['DOW']['valor']:,.2f}"
        st.markdown(f"DOW <span style='color:{color_dow};'>{val_dow} ({indices['DOW']['var']})</span>", unsafe_allow_html=True)

    with c_top5:
        color_btc = "#3fb950" if indices["BTC"]["sube"] else "#f85149"
        val_btc = f"${indices['BTC']['valor']:,.2f}"
        st.markdown(f"BTC <span style='color:{color_btc};'>{val_btc} ({indices['BTC']['var']})</span>", unsafe_allow_html=True)

    with c_top6:
        st.markdown("🟢 <span style='color:#3fb950; font-size:12px;'>EN VIVO</span>", unsafe_allow_html=True)

    st.markdown("---")