"""
login.py
--------
Pantalla de inicio de sesión / registro conectada a Supabase (tabla `usuarios`).

Uso en app.py:
    from components.login import requerir_login
    usuario = requerir_login()   # detiene la app si no hay sesión
    # ... a partir de aquí el usuario está autenticado (dict con id/nombre/email)
"""
import streamlit as st

from tools.auth_manager import autenticar_usuario, registrar_usuario
from tools import session_store

_LOGO_SVG = (
    "<span style='font-size:40px; font-weight:800; color:#ff6b35; letter-spacing:1px; "
    "font-family:-apple-system,\"Segoe UI\",Roboto,Arial,sans-serif;'>P&amp;J</span>"
)


def _cerrar_sesion():
    """Limpia la sesión del usuario (y el token en memoria del servidor)."""
    session_store.eliminar(st.query_params.get("s", ""))
    for clave in ("usuario_autenticado", "usuario_info"):
        st.session_state.pop(clave, None)


def _iniciar_sesion(usuario: dict):
    """
    Marca la sesión, guarda el token en la URL (para que sobreviva al F5) y
    rerun normal. El overlay de carga de app.py tapa el login mientras el
    dashboard se arma, así se entra directo sin verlo encima.
    """
    st.session_state.usuario_autenticado = True
    st.session_state.usuario_info = usuario
    st.query_params["s"] = session_store.crear(usuario)  # persiste tras F5
    st.rerun()


def requerir_login() -> dict:
    """
    Muestra el login si no hay sesión y DETIENE la ejecución de la app.
    Si hay sesión, retorna el dict del usuario ({id, nombre, email}).
    """
    # Cerrar sesión vía enlace del menú (?logout=1)
    if st.query_params.get("logout") == "1":
        _cerrar_sesion()
        st.query_params.clear()

    # Sesión activa en esta pestaña
    if st.session_state.get("usuario_autenticado"):
        return st.session_state.get("usuario_info", {})

    # Tras un F5, session_state se vacía pero el token sigue en la URL:
    # si el servidor aún lo tiene (consola encendida), restauramos la sesión.
    _token = st.query_params.get("s")
    if _token:
        _usuario = session_store.obtener(_token)
        if _usuario:
            st.session_state.usuario_autenticado = True
            st.session_state.usuario_info = _usuario
            return _usuario

    # --- No autenticado: renderizar pantalla de login centrada ---
    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
        st.markdown(
            f"<div style='text-align:center; margin-top:8vh;'>{_LOGO_SVG}"
            "<h1 style='margin:10px 0 2px;'>Piña &amp; Jara · Terminal</h1>"
            "<p style='color:#8b949e; margin:0 0 18px;'>Inicia sesión para acceder al panel bursátil</p></div>",
            unsafe_allow_html=True,
        )

        tab_entrar, tab_crear = st.tabs(["Iniciar sesión", "Crear cuenta"])

        # --- Iniciar sesión ---
        with tab_entrar:
            with st.form("form_login", border=True):
                email = st.text_input("Email", key="login_email", placeholder="tucorreo@dominio.com")
                password = st.text_input("Contraseña", type="password", key="login_pass")
                enviar = st.form_submit_button("Entrar", width="stretch", type="primary")
            if enviar:
                res = autenticar_usuario(email, password)
                if res["ok"]:
                    _iniciar_sesion(res["usuario"])
                else:
                    st.error(res["mensaje"])

        # --- Crear cuenta ---
        with tab_crear:
            with st.form("form_registro", border=True):
                nombre = st.text_input("Nombre", key="reg_nombre", placeholder="Nombre...Ap")
                email_r = st.text_input("Email", key="reg_email", placeholder="tucorreo@dominio.com")
                pass_r = st.text_input("Contraseña", type="password", key="reg_pass",
                                       help="Mínimo 6 caracteres")
                crear = st.form_submit_button("Crear cuenta", width="stretch", type="primary")
            if crear:
                res = registrar_usuario(nombre, email_r, pass_r)
                if res["ok"]:
                    # Inicia sesión automáticamente tras registrarse
                    _iniciar_sesion(res["usuario"])
                else:
                    st.error(res["mensaje"])

    st.stop()
    return {}  # (nunca se alcanza)