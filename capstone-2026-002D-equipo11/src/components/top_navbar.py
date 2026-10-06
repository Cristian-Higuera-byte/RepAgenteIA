"""
top_navbar.py
-------------
Barra de navegación superior del dashboard (estilo terminal de trading).
- Buscador (visual por ahora) en la posición del antiguo logo.
- Íconos de tema/notificaciones.
- Usuario a la derecha: al hacer clic en el nombre se despliega un menú
  (perfil / configuración / cerrar sesión) — con <details>, sin recargar.

La barra queda FIJA arriba y a todo el ancho gracias al contenedor
`st.container(key="barra_nav_fija")` de app.py + su CSS (position: fixed).
"""
import streamlit as st

from components.buscador import abrir_buscador

# --- Íconos de línea (estilo Lucide/Feather), heredan color con currentColor ---
_IC_BUSCAR = (
    "<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<circle cx='11' cy='11' r='8'/><path d='m21 21-4.3-4.3'/></svg>"
)
_IC_TEMA = (
    "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<path d='M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z'/></svg>"
)
_IC_NOTIF = (
    "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<path d='M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9'/>"
    "<path d='M10.3 21a1.94 1.94 0 0 0 3.4 0'/></svg>"
)


def renderizar_barra_navegacion(usuario: str = "Emilio Fuentes",
                                saldo: float | None = None,
                                moneda: str = "USD",
                                pl: float | None = None):
    iniciales = "".join([p[0] for p in usuario.split()[:2]]).upper() or "U"

    # Chip de saldo total de MT5 (equity). Si no hay dato, se muestra "—".
    if saldo is not None:
        saldo_txt = f"${saldo:,.2f} {moneda}"
    else:
        saldo_txt = "— sin conexión MT5"

    # P/G flotante (de posiciones abiertas) junto al saldo, estilo XM.
    # Siempre se dibuja el <span> (aunque esté vacío) para que el feed en vivo
    # (data-pj-acc, ver components/live_feed.py) pueda rellenarlo.
    pl_txt = f"{pl:+,.2f}" if pl is not None and abs(pl) >= 0.005 else ""
    color_pl = "#3fb950" if (pl or 0) >= 0 else "#f85149"
    pl_span = (
        f"<span data-pj-acc='profit' style='font-size:13px; font-weight:700; color:{color_pl}; "
        f"font-family:monospace;'>{pl_txt}</span>"
    )
    attr_saldo = "data-pj-acc='equity'" if saldo is not None else ""
    chip_saldo = (
        "<div style='display:flex; flex-direction:column; align-items:flex-end; "
        "line-height:1.1; padding:4px 12px; background:#161b22; border:1px solid #30363d; "
        "border-radius:8px;'>"
        "<span style='font-size:10px; color:#8b949e; text-transform:uppercase; "
        "letter-spacing:.5px;'>Saldo MT5</span>"
        "<span style='display:flex; align-items:baseline; gap:8px;'>"
        f"<span {attr_saldo} style='font-size:14px; font-weight:700; color:#3fb950; "
        f"font-family:monospace;'>{saldo_txt}</span>{pl_span}</span>"
        "</div>"
    )

    # Estilos de la navbar + del botón buscador
    st.markdown(
        """
        <style>
            .nav-user > summary { list-style: none; }
            .nav-user > summary::-webkit-details-marker { display: none; }
            .nav-user[open] .nav-flecha { transform: rotate(180deg); }
            .nav-menu-item:hover { background: #21262d; }
            .nav-ico { color:#8b949e; cursor:pointer; display:flex; align-items:center;
                       transition: color .15s ease; }
            .nav-ico:hover { color:#e6edf3; }
            /* Centrado vertical robusto */
            .st-key-barra_nav_fija [data-testid="stHorizontalBlock"] { align-items:center !important; }
            .st-key-barra_nav_fija [data-testid="stColumn"] {
                display:flex !important; flex-direction:column; justify-content:center !important;
            }
            .st-key-barra_nav_fija [data-testid="stColumn"] [data-testid="stMarkdownContainer"] { margin:0 !important; }
            .st-key-barra_nav_fija .stButton { margin:0 !important; }
            .st-key-barra_nav_fija [data-testid="stElementContainer"]:has(style) { display:none !important; }
            /* Botón que abre el buscador: se expande para aprovechar el espacio del antiguo logo */
            [class*="st-key-btn_abrir_buscador"] button {
                background:#161b22 !important; border:1px solid #30363d !important;
                border-radius:20px !important; color:#8b949e !important;
                justify-content:flex-start !important; font-weight:400 !important;
                padding:4px 16px !important; height:32px; min-height:32px !important;
            }
            [class*="st-key-btn_abrir_buscador"] button:hover {
                border-color:#58a6ff !important; color:#e6edf3 !important;
            }
            /* Botón ☰ que expande/colapsa la barra lateral (estilo SIGMA) */
            [class*="st-key-top_toggle"] button {
                background:transparent !important; border:none !important; box-shadow:none !important;
                color:#8b949e !important; padding:0 !important; height:40px; min-height:40px !important;
                width:40px !important; border-radius:8px !important;
            }
            [class*="st-key-top_toggle"] button:hover {
                color:#e6edf3 !important; background:rgba(255,255,255,0.06) !important;
            }
            [class*="st-key-top_toggle"] button p,
            [class*="st-key-top_toggle"] button p *,
            [class*="st-key-top_toggle"] button span[data-testid="stIconMaterial"] { font-size:28px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    right_html = f"""
        <div style='display:flex; align-items:center; justify-content:flex-end; gap:18px;'>
            {chip_saldo}
            <span class='nav-ico' title='Tema'>{_IC_TEMA}</span>
            <span class='nav-ico' title='Notificaciones'>{_IC_NOTIF}</span>
            <details class='nav-user' style='position:relative;'>
                <summary style='display:flex; align-items:center; gap:8px; cursor:pointer;'>
                    <div style='width:30px; height:30px; border-radius:50%;
                                background:#1f6feb; color:#ffffff; display:flex;
                                align-items:center; justify-content:center;
                                font-weight:bold; font-size:12px;'>{iniciales}</div>
                    <span style='color:#e6edf3; font-size:13px;'>{usuario}</span>
                    <span class='nav-flecha' style='color:#8b949e; font-size:11px;
                          transition:transform .15s ease;'>▾</span>
                </summary>
                <div style='position:absolute; right:0; top:calc(100% + 10px);
                            background:#161b22; border:1px solid #30363d; border-radius:8px;
                            min-width:190px; padding:6px; z-index:3000;
                            box-shadow:0 8px 24px rgba(0,0,0,0.5);'>
                    <div class='nav-menu-item' style='display:flex; align-items:center; gap:10px;
                         padding:9px 12px; border-radius:6px; color:#e6edf3; font-size:13px;
                         cursor:pointer;'>👤 Mi perfil</div>
                    <div class='nav-menu-item' style='display:flex; align-items:center; gap:10px;
                         padding:9px 12px; border-radius:6px; color:#e6edf3; font-size:13px;
                         cursor:pointer;'>⚙️ Configuración</div>
                    <div style='height:1px; background:#30363d; margin:4px 6px;'></div>
                    <a href='?logout=1' target='_self' class='nav-menu-item'
                       style='display:flex; align-items:center; gap:10px;
                         padding:9px 12px; border-radius:6px; color:#f85149; font-size:13px;
                         cursor:pointer; text-decoration:none;'>🚪 Cerrar sesión</a>
                </div>
            </details>
        </div>
    """

    # ☰ + buscador (corto, a la izquierda) + espacio + derecha (saldo/usuario)
    c_toggle, c_buscar, c_spacer, c_der = st.columns(
        [0.2, 1.3, 1.3, 2.0], vertical_alignment="center")
    with c_toggle:
        # El clic lo intercepta un script en el navegador (nav_bar.py, _JS_SIDEBAR)
        # que alterna la barra lateral con animación CSS, SIN reejecutar Python.
        st.button(":material/menu:", key="top_toggle")
    with c_buscar:
        if st.button("Buscar activo, par o ticker...", icon=":material/search:",
                     key="btn_abrir_buscador", width="stretch"):
            abrir_buscador()
            st.rerun()
    with c_spacer:
        st.empty()
    with c_der:
        st.markdown(right_html, unsafe_allow_html=True)