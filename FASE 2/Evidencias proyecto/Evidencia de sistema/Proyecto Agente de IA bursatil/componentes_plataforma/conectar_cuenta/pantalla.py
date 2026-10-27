# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- INICIO Piña y Jara pantalla .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
conectar_cuenta/pantalla.py
---------------------------
Pantalla "Conectar mi cuenta de Capital.com". Cada usuario trae sus propias cuentas, la demo y la real, y elige
con cuál operar, como en Capital.com.

`requerir_cuenta(usuario)` va justo después del login: si el usuario no tiene ninguna cuenta conectada (o pidió
gestionarlas desde el menú) dibuja esta pantalla y DETIENE la ejecución; si no, no hace nada. Solo actúa cuando
el modo multiusuario está encendido (`CAPITAL_MULTIUSUARIO=true`); apagado, la plataforma usa la cuenta del .env.

Antes de guardar, las credenciales se verifican contra Capital.com y se cifran (herramientas/credenciales_bolsa.py).
Ninguna se muestra ni se registra en logs después de escribirlas.
"""
import streamlit as st

from herramientas import credenciales_bolsa, token_datos
from herramientas.backends import sesiones_capital

from .modo import cuentas_conectadas, fijar_modo, invalidar_cuentas, restaurar_modo, usuario_id_actual

# Clave de st.session_state que mantiene abierta la pantalla de gestión
_CLAVE_GESTIONAR = "cuentas_gestionar"
# Los dos tipos de cuenta: nombre mostrado -> es_demo
_TIPOS = {"Demo": True, "Real": False}


# TITULO ABRIR GESTION

def abrir_gestion() -> None:
    """Pide mostrar la pantalla de conexión de cuentas en el próximo rerun.

    Lo usa la ventana «Seleccione cuenta» de Inicio para el botón de conectar la cuenta que falta."""
    st.session_state[_CLAVE_GESTIONAR] = True


# TITULO COMPLETAR CUENTA FALTANTE

# Clave de st.session_state con el resultado del último intento de completar la cuenta que falta
_CLAVE_COMPLETAR = "cuenta_faltante_estado"


def completar_cuenta_faltante(usuario_id: int, reintentar: bool = False) -> dict:
    """Si el usuario tiene UNA sola cuenta conectada, prueba sus mismos datos con la otra y la conecta si Capital la acepta.

    Así no hay que escribir la API dos veces: la demo y la real salen de los mismos datos. Se intenta una vez por sesión
    (para no abrir sesiones en Capital cada vez que se abre la ventana) o de nuevo si `reintentar` es True. Devuelve el
    último resultado {"tipo", "ok", "mensaje"}, o {} si no había nada que completar."""
    cuentas = cuentas_conectadas(refrescar=True)
    if cuentas.get("demo") == cuentas.get("real"):
        return {}
    falta_demo = not cuentas.get("demo")
    tipo = "Demo" if falta_demo else "Real"
    anterior = st.session_state.get(_CLAVE_COMPLETAR)
    if anterior and anterior.get("tipo") == tipo and not reintentar:
        return anterior
    datos = credenciales_bolsa.obtener_credenciales(usuario_id, not falta_demo)
    if datos is None:
        return {}
    prueba = sesiones_capital.probar_credenciales(datos["identificador"], datos["api_key"], datos["api_contrasena"], falta_demo)
    resultado = {"tipo": tipo, "ok": prueba["ok"], "mensaje": prueba["mensaje"]}
    if prueba["ok"]:
        guardado = credenciales_bolsa.guardar_credenciales(usuario_id, falta_demo, datos["identificador"],
                                                           datos["api_key"], datos["api_contrasena"])
        resultado["ok"] = guardado["ok"]
        resultado["mensaje"] = guardado["mensaje"]
        sesiones_capital.olvidar_usuario(usuario_id)
        invalidar_cuentas()
    st.session_state[_CLAVE_COMPLETAR] = resultado
    return resultado


# TITULO PROCESAR ENLACES

def _procesar_enlaces(cuentas: dict) -> None:
    """Atiende los enlaces del menú del usuario: `?cuenta=demo|real` cambia de cuenta y `?cuentas=1` abre la gestión.

    Quita de la URL solo esos parámetros (el token de sesión `s` se conserva)."""
    solicitada = st.query_params.get("cuenta")
    if solicitada in ("demo", "real"):
        if cuentas.get(solicitada):
            fijar_modo(solicitada == "demo")
        del st.query_params["cuenta"]
    if st.query_params.get("cuentas") == "1":
        st.session_state[_CLAVE_GESTIONAR] = True
        del st.query_params["cuentas"]


# TITULO FORMULARIO DE CONEXION

def _formulario(usuario_id: int) -> None:
    """Dibuja el formulario de conexión: se escriben los datos UNA vez y se verifican con la cuenta demo y la real.

    Se guardan, cifrados, los datos de cada cuenta que Capital.com acepte (una, otra o las dos). Al terminar muestra
    qué quedó conectado y un botón para ir al panel."""
    with st.form("form_conectar_cuenta", border=True, clear_on_submit=True):
        identificador = st.text_input("Correo de tu cuenta de Capital.com", placeholder="tucorreo@dominio.com")
        api_key = st.text_input("API key", type="password")
        api_contrasena = st.text_input("Contraseña de la API key", type="password",
                                       help="La que definiste al crear la key, no la de tu cuenta.")
        enviar = st.form_submit_button("Conectar mis cuentas", width="stretch", type="primary")
    if not enviar:
        return
    identificador, api_key, api_contrasena = identificador.strip(), api_key.strip(), api_contrasena.strip()
    if not (identificador and api_key and api_contrasena):
        st.error("Completa el correo, la API key y la contraseña de la key.")
        return
    with st.spinner("Verificando tu cuenta demo y tu cuenta real en Capital.com..."):
        pruebas = sesiones_capital.probar_ambas_cuentas(identificador, api_key, api_contrasena)
    if not (pruebas["demo"]["ok"] or pruebas["real"]["ok"]):
        st.error(pruebas["demo"]["mensaje"])
        return
    previas = cuentas_conectadas()
    conectadas = []
    for nombre, es_demo in _TIPOS.items():
        if not pruebas["demo" if es_demo else "real"]["ok"]:
            continue
        guardado = credenciales_bolsa.guardar_credenciales(usuario_id, es_demo, identificador, api_key, api_contrasena)
        if not guardado["ok"]:
            st.error(guardado["mensaje"])
            return
        conectadas.append(nombre)
    sesiones_capital.olvidar_usuario(usuario_id)
    invalidar_cuentas()
    # Solo se cambia sola de cuenta cuando es la primera vez; si ya operaba con otra, no se la cambia por sorpresa
    if not (previas.get("demo") or previas.get("real")):
        fijar_modo(True if "Demo" in conectadas else False)
    st.session_state[_CLAVE_GESTIONAR] = False
    st.success("Conectado: " + " y ".join(f"cuenta {n}" for n in conectadas) + ". La plataforma siempre empieza en demo; "
               "cambias de cuenta cuando quieras desde «Seleccione cuenta».")
    faltante = [n for n in _TIPOS if n not in conectadas]
    if faltante:
        st.info(f"Con estos datos Capital.com no aceptó la cuenta {faltante[0]}: "
                f"{pruebas['demo' if faltante[0] == 'Demo' else 'real']['mensaje']}")
    st.button("Ir al panel", type="primary", width="stretch")


# TITULO LISTA DE CUENTAS

def _lista_cuentas(usuario_id: int, cuentas: dict) -> None:
    """Muestra qué cuentas están conectadas, con el botón para desconectar cada una y el de continuar al panel."""
    for nombre, es_demo in _TIPOS.items():
        columna_texto, columna_boton = st.columns([3, 1], vertical_alignment="center")
        conectada = cuentas.get("demo" if es_demo else "real")
        columna_texto.markdown(f"**Cuenta {nombre}:** {'conectada' if conectada else 'sin conectar'}")
        if conectada and columna_boton.button("Desconectar", key=f"desconectar_{nombre}", width="stretch"):
            credenciales_bolsa.eliminar_credenciales(usuario_id, es_demo)
            sesiones_capital.olvidar_usuario(usuario_id)
            invalidar_cuentas()
            st.rerun()
    if (cuentas.get("demo") or cuentas.get("real")) and st.button("Volver al panel", type="primary", width="stretch"):
        st.session_state[_CLAVE_GESTIONAR] = False
        st.rerun()


# TITULO REQUERIR CUENTA

def requerir_cuenta(usuario: dict) -> None:
    """Exige que el usuario tenga una cuenta de Capital.com conectada antes de mostrar el panel.

    Recibe el diccionario del usuario autenticado. Si no hay cuenta conectada, o el usuario pidió gestionarlas desde
    el menú, dibuja la pantalla de conexión y detiene la ejecución con `st.stop()`. Con el modo multiusuario apagado
    no hace nada."""
    if not sesiones_capital.MULTIUSUARIO:
        return
    if not token_datos.emitir(0, True):
        st.error("Falta configurar el servidor: SERVIDOR_SECRETO (mínimo 32 caracteres) en el .env.")
        st.stop()
    usuario_id = usuario_id_actual()
    if usuario_id is None:
        return
    restaurar_modo()   # tras un F5 o un enlace del menú, vuelve a la cuenta que había elegido en esta sesión
    # Se usa la copia guardada en la sesión (Supabase se consulta como máximo una vez por minuto y cada vez que se conecta o desconecta
    # una cuenta, que invalidan la copia): antes se consultaba en CADA clic, y cada clic esperaba ese viaje a la base de datos.
    # Si la copia dice que no hay cuenta se confirma con Supabase, porque ahí sí hay que mostrar la pantalla de conexión.
    cuentas = cuentas_conectadas()
    if not (cuentas.get("demo") or cuentas.get("real")):
        cuentas = cuentas_conectadas(refrescar=True)
    _procesar_enlaces(cuentas)
    hay_cuenta = bool(cuentas.get("demo") or cuentas.get("real"))
    if hay_cuenta and not st.session_state.get(_CLAVE_GESTIONAR):
        return

    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
        st.markdown(
            "<div style='text-align:center; margin-top:6vh;'>"
            f"<h2 style='margin:0 0 4px;'>Hola, {usuario.get('nombre', '')}</h2>"
            "<p style='color:#8b949e; margin:0 0 14px;'>Escribe los datos de tu API de Capital.com una sola vez: "
            "verificamos tu cuenta demo y tu cuenta real, y eliges con cuál operar cuando quieras.</p></div>",
            unsafe_allow_html=True,
        )
        with st.expander("¿Cómo creo mi API key?"):
            st.markdown(
                "1. En Capital.com entra a **Configuración → API integrations** y activa la autenticación en dos pasos.\n"
                "2. Crea una API key nueva y define su contraseña.\n"
                "3. Dale permiso para **operar** y **no** habilites retiros.\n"
                "4. Copia aquí la key y su contraseña. Se guardan cifradas: en la base de datos solo hay texto ilegible y únicamente el servidor puede usarlas."
            )
        if hay_cuenta:
            _lista_cuentas(usuario_id, cuentas)
            st.divider()
        _formulario(usuario_id)
    st.stop()


# -------------------------------------------------------------------------------------------------------
# ---------------------------------------- FIN Piña y Jara pantalla .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
