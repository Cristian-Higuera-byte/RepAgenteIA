import streamlit as st

# (icono material, clave, etiqueta visible al expandir)
ITEMS = [
    (":material/home:", "home", "Inicio"),                       # panel de cuenta (estilo XM)
    (":material/candlestick_chart:", "trading", "Trading"),      # dashboard: gráfico + listas
    (":material/table_rows:", "cotizaciones", "Cotizaciones"),   # tablas estilo Investing
    (":material/content_copy:", "copytrading", "Copy trading"),  # estrategias (mock)
    (":material/newspaper:", "noticias", "Noticias"),
    (":material/work:", "portafolio", "Cartera"),
    (":material/assignment:", "ordenes", "Órdenes"),
    (":material/bar_chart:", "analisis", "Análisis"),
    (":material/rocket_launch:", "promociones", "Promociones"),
    (":material/settings:", "ajustes", "Ajustes"),
]

# Anchos (px) de la barra lateral. El colapsado (70) coincide con el offset por
# defecto de la barra superior; el expandido (220) lo ajusta app.py.
ANCHO_EXPANDIDO = 220


def renderizar_barra_navegacion():
    if "nav_activo" not in st.session_state:
        st.session_state.nav_activo = "trading"  # al entrar, arranca en los gráficos
    expandido = st.session_state.get("sidebar_expandido", False)
    ancho = ANCHO_EXPANDIDO if expandido else 70

    st.markdown(f"""
    <style>
        /* El contenido se desplaza el ancho de la barra lateral (que va FIJA)
           + un espacio de separación, para que no quede pegado a ella. */
        .block-container {{
            padding-left: {ancho + 20}px !important;
        }}

        /* Evita que la columna principal se envuelva debajo de la barra lateral
           cuando esta se expande (si no, "se pierde la vista"). */
        div[data-testid="stHorizontalBlock"]:has(.pj-nav) {{ flex-wrap: nowrap !important; }}

        /* Barra lateral FIJA (position: fixed): siempre quieta, no sube al llegar
           al fondo (a diferencia de sticky). */
        div[data-testid="stColumn"]:has(.pj-nav),
        div[data-testid="column"]:has(.pj-nav) {{
            background: #0d1117;
            border-right: 1px solid #30363d;
            padding: 12px 0 !important;
            align-items: center;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            margin-top: 0 !important;   /* anula el -4.8rem de app.py (subía el logo fuera de pantalla) */
            height: 100vh !important;
            z-index: 100001;
            overflow: hidden;   /* sin scroll */
            /* Ancho fijo = coincide con el desplazamiento del contenido y la barra superior */
            flex: 0 0 70px !important;
            width: 70px !important;
            max-width: 70px !important;
        }}
        div[data-testid="stColumn"]:has(.pj-nav) > div,
        div[data-testid="column"]:has(.pj-nav) > div {{
            align-items: center;
            gap: 4px;
            height: 100%;              /* llena la columna para poder empujar Soporte al fondo */
        }}
        /* Soporte pegado al fondo (sin espaciador fijo que causaba scroll) */
        [class*="st-key-nav_soporte"] {{ margin-top: auto !important; }}

        /* Logo */
        .pj-logo {{
            font-weight: 900;
            font-size: 26px;
            letter-spacing: -1px;
            text-align: center;
            background: linear-gradient(135deg, #ff4b4b 0%, #ff8f00 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 18px;
        }}

        /* Botones: iconos sin caja */
        div[data-testid="stColumn"]:has(.pj-nav) button,
        div[data-testid="column"]:has(.pj-nav) button {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #8b949e !important;
            width: 44px !important;
            height: 44px !important;
            min-height: 44px !important;
            padding: 0 !important;
            border-radius: 10px !important;
            margin: 0 auto;
        }}
        div[data-testid="stColumn"]:has(.pj-nav) button p,
        div[data-testid="column"]:has(.pj-nav) button p {{
            font-size: 24px !important;
            line-height: 1 !important;
        }}
        div[data-testid="stColumn"]:has(.pj-nav) button:hover,
        div[data-testid="column"]:has(.pj-nav) button:hover {{
            background: rgba(255,255,255,0.08) !important;
            color: #fff !important;
        }}

        /* Botón activo (type="primary") -> verde como en XM */
        div[data-testid="stColumn"]:has(.pj-nav) button[kind="primary"],
        div[data-testid="column"]:has(.pj-nav) button[kind="primary"],
        div[data-testid="stColumn"]:has(.pj-nav) [data-testid="stBaseButton-primary"] {{
            background: rgba(34,197,94,0.12) !important;
            color: #22c55e !important;
        }}

        /* ====== ESTADO EXPANDIDO (solo cuando existe .pj-exp) ====== */
        div[data-testid="stColumn"]:has(.pj-exp),
        div[data-testid="column"]:has(.pj-exp) {{
            flex: 0 0 {ANCHO_EXPANDIDO}px !important;
            width: {ANCHO_EXPANDIDO}px !important;
            max-width: {ANCHO_EXPANDIDO}px !important;
            align-items: stretch !important;
            padding: 12px 12px !important;
        }}
        div[data-testid="stColumn"]:has(.pj-exp) > div {{ align-items: stretch !important; }}
        .pj-menus {{
            color: #586174; font-size: 11px; font-weight: 700; letter-spacing: 1px;
            padding: 4px 12px 6px;
        }}
        /* Botones a todo el ancho, icono + texto a la izquierda y CENTRADOS vertical */
        div[data-testid="stColumn"]:has(.pj-exp) button {{
            width: 100% !important;
            justify-content: flex-start !important;
            align-items: center !important;
            padding: 0 14px !important;
            gap: 14px;
            margin: 0 !important;
        }}
        div[data-testid="stColumn"]:has(.pj-exp) button p {{
            font-size: 14px !important; font-weight: 600 !important;
            line-height: 1 !important; margin: 0 !important;
        }}
        div[data-testid="stColumn"]:has(.pj-exp) button span[data-testid="stIconMaterial"] {{
            font-size: 22px !important; line-height: 1 !important;
            display: flex !important; align-items: center !important;
        }}
    </style>
    <div class="pj-nav {'pj-exp' if expandido else ''}"></div>
    """, unsafe_allow_html=True)

    if expandido:
        # Logo P&J (gradiente) + "Piña & Jara" en blanco al lado.
        # Se neutraliza el gradiente/recorte del contenedor (background:none,
        # text-fill blanco) para que el texto se vea; el gradiente va solo en P&J.
        st.markdown(
            "<div class='pj-logo' style='display:flex; align-items:center; gap:10px; "
            "justify-content:flex-start; padding-left:12px; background:none !important; "
            "-webkit-background-clip:border-box !important; -webkit-text-fill-color:#ffffff !important;'>"
            "<span style='font-weight:900; font-size:26px; letter-spacing:-1px; "
            "background:linear-gradient(135deg,#ff4b4b 0%,#ff8f00 100%) !important; "
            "-webkit-background-clip:text !important; -webkit-text-fill-color:transparent !important;'>P&amp;J</span>"
            "<span style='color:#8b949e !important; -webkit-text-fill-color:#8b949e !important; "
            "font-size:15px; font-weight:700; letter-spacing:0;'>Piña &amp; Jara</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="pj-logo">P&J</div>', unsafe_allow_html=True)

    for icono, clave, etiqueta in ITEMS:
        activo = st.session_state.nav_activo == clave
        tipo = "primary" if activo else "secondary"
        if expandido:
            clic = st.button(etiqueta, icon=icono, key=f"nav_btn_{clave}", type=tipo)
        else:
            clic = st.button(icono, key=f"nav_btn_{clave}", type=tipo)
        if clic:
            st.session_state.nav_activo = clave
            st.rerun()

    # Soporte: se empuja al fondo con margin-top:auto (ver CSS), sin espaciador fijo.
    if expandido:
        clic_soporte = st.button("Soporte", icon=":material/headset_mic:", key="nav_soporte")
    else:
        clic_soporte = st.button(":material/headset_mic:", key="nav_soporte")
    if clic_soporte:
        st.toast("Soporte técnico de Piña & Jara activo.")