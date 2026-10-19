# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara pantalla .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
acceso/pantalla.py
-----------------
Pantalla de inicio de sesión / registro (UI) conectada a Supabase (tabla `usuarios`).
`requerir_login()` es la puerta de entrada de la app: si no hay sesión, dibuja el login
centrado y DETIENE la ejecución; si la hay, devuelve el dict del usuario. La mecánica de
sesión (iniciar/cerrar/restaurar token) vive en acceso/sesion.py.

Uso en app.py:
    from components.acceso import requerir_login
    usuario = requerir_login()   # detiene la app si no hay sesión
    # ... a partir de aquí el usuario está autenticado (dict con id/nombre/email)
"""
import streamlit as st

from tools.gestor_autenticacion import autenticar_usuario, registrar_usuario

from .sesion import cerrar_sesion, iniciar_sesion, usuario_en_sesion

# Logo "P&J" en HTML en línea (color naranja de la marca); se inserta en la cabecera del login.
_LOGO_HTML = (
    "<span style='font-size:40px; font-weight:800; color:#ff6b35; letter-spacing:1px; "
    "font-family:-apple-system,\"Segoe UI\",Roboto,Arial,sans-serif;'>P&amp;J</span>"
)


def requerir_login() -> dict:
    """Puerta de entrada de la app: exige que el usuario haya iniciado sesión.

    Si el parámetro de URL `logout=1` está presente, cierra la sesión y limpia la URL. Si hay
    sesión (o se restaura desde el token de la URL) devuelve el dict del usuario
    ({id, nombre, email}). Si no, dibuja la pantalla de login/registro centrada y detiene la
    ejecución con `st.stop()`, de modo que nada del dashboard se renderiza sin autenticar.
    Efectos secundarios: lectura/escritura de `st.query_params`, consultas a Supabase vía
    herramientas.gestor_autenticacion y, al autenticar, un `st.rerun()` desde iniciar_sesion.
    """
    # Cerrar sesión vía enlace del menú (?logout=1)
    if st.query_params.get("logout") == "1":
        cerrar_sesion()
        st.query_params.clear()

    # Reutiliza la sesión de la pestaña o la restaurada desde el token de la URL
    usuario = usuario_en_sesion()
    if usuario is not None:
        return usuario

    # --- No autenticado: renderizar pantalla de login centrada ---
    # Columna central más ancha para que el formulario quede centrado
    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
        # Cabecera con logo, título y subtítulo
        st.markdown(
            f"<div style='text-align:center; margin-top:8vh;'>{_LOGO_HTML}"
            "<h1 style='margin:10px 0 2px;'>Piña &amp; Jara · Terminal</h1>"
            "<p style='color:#8b949e; margin:0 0 18px;'>Inicia sesión para acceder al panel bursátil</p></div>",
            unsafe_allow_html=True,
        )

        # Dos pestañas: entrar con cuenta existente o crear una nueva
        tab_entrar, tab_crear = st.tabs(["Iniciar sesión", "Crear cuenta"])

        # --- Iniciar sesión ---
        with tab_entrar:
            with st.form("form_login", border=True):
                email = st.text_input("Email", key="login_email", placeholder="tucorreo@dominio.com")
                password = st.text_input("Contraseña", type="password", key="login_pass")
                enviar = st.form_submit_button("Entrar", width="stretch", type="primary")
            if enviar:
                # Valida credenciales; si son correctas inicia sesión (rerun), si no muestra el error
                res = autenticar_usuario(email, password)
                if res["ok"]:
                    iniciar_sesion(res["usuario"])
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
                # Registra al usuario nuevo y valida los datos (nombre, email, contraseña)
                res = registrar_usuario(nombre, email_r, pass_r)
                if res["ok"]:
                    # Inicia sesión automáticamente tras registrarse
                    iniciar_sesion(res["usuario"])
                else:
                    st.error(res["mensaje"])

    # Corta la ejecución para que no se pinte el resto de la app
    st.stop()
    return {}  # (nunca se alcanza)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara pantalla .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
