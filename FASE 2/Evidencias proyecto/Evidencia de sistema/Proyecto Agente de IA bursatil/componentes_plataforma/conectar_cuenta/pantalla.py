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
from html import escape
from pathlib import Path

import streamlit as st

from componentes_plataforma import _estaticos, recaptcha
from componentes_plataforma.legal import enlaces_html
from herramientas import credenciales_bolsa, limites_formularios as limites, token_datos
from herramientas.backends import sesiones_capital

from .modo import cuentas_conectadas, fijar_modo, invalidar_cuentas, restaurar_modo, usuario_id_actual

# Hoja de estilos de la pantalla (estilos.css, junto a este archivo)
_CSS = Path(__file__).parent / "estilos.css"
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


# TITULO GUIA

def _html_guia() -> str:
    """HTML de la guía de 4 pasos, siempre visible a la derecha del formulario, para crear la API key en Capital.com, con el aviso de seguridad y lo que pasa después."""
    pasos = [("Activa la autenticación en dos pasos", "En Capital.com entra a <strong>Configuración → API integrations</strong> y activa la autenticación en dos pasos."),
             ("Crea una API key nueva", "Define también la contraseña de la key: es distinta de la de tu cuenta."),
             ("Dale permiso para operar", "Habilita <strong>operar</strong> y <strong>no habilites retiros</strong>: la plataforma nunca los necesita."),
             ("Copia la key y su contraseña", "Escríbelas en el formulario de la izquierda y pulsa «Probar conexión».")]
    lista = "".join(f"<li><span class='cc-n'>{i}</span><div><b>{titulo}</b><p>{texto}</p></div></li>" for i, (titulo, texto) in enumerate(pasos, 1))
    return ("<div class='cc-guia'><div class='cc-guia-titulo'>Cómo crear tu API key</div><div class='cc-guia-sub'>Son 4 pasos en Capital.com.</div>"
            f"<ol class='cc-pasos'>{lista}</ol>"
            "<div class='cc-seguridad'><b>Tus claves están protegidas.</b> Se guardan cifradas: en la base de datos solo hay texto ilegible y únicamente el servidor puede usarlas.</div>"
            "<div class='cc-despues'>Verificamos tu cuenta demo y tu cuenta real. La plataforma siempre empieza en demo y cambias de cuenta cuando quieras desde «Seleccione cuenta».</div></div>")


# TITULO RESULTADO DE LA PRUEBA

def _filas_resultado(pruebas: dict) -> None:
    """Muestra una fila por cuenta (demo y real) con el resultado de la prueba: aceptada o el motivo por el que Capital.com no la aceptó."""
    for nombre, es_demo in _TIPOS.items():
        prueba = pruebas["demo" if es_demo else "real"]
        if prueba["ok"]:
            st.success(f"Cuenta {nombre}: la conexión funciona.", icon=":material/check_circle:")
        else:
            st.warning(f"Cuenta {nombre}: {prueba['mensaje']}", icon=":material/error:")


# TITULO FORMULARIO DE CONEXION

# Claves de st.session_state: el resultado de la última prueba (con los datos probados) y los campos del formulario
_CLAVE_PRUEBA = "cuentas_prueba"
_CLAVES_CAMPOS = ("conectar_identificador", "conectar_api_key", "conectar_api_contrasena")
# Segundos que vale la verificación de reCAPTCHA en esta pantalla: una vez aprobada, «Probar conexión» y «Guardar y continuar» no la piden de nuevo (cada token de Google sirve una sola vez).
_VALIDEZ_VERIFICACION = 600


def _formulario(usuario_id: int) -> None:
    """Dibuja el formulario de conexión: se escriben los datos UNA vez, se prueban con la cuenta demo y la real y recién entonces se pueden guardar.

    «Probar conexión» verifica ambas cuentas y muestra el resultado de cada una. «Guardar y continuar» solo se habilita si la prueba corresponde a lo que hay
    escrito (si se cambia un dato, hay que probar de nuevo) y guarda, cifradas, las cuentas que Capital.com aceptó. Siempre se empieza en demo."""
    identificador = st.text_input("Correo de tu cuenta de Capital.com", placeholder="tucorreo@dominio.com", key=_CLAVES_CAMPOS[0], max_chars=limites.CORREO)
    api_key = st.text_input("API key", type="password", key=_CLAVES_CAMPOS[1], max_chars=limites.API_KEY)
    api_contrasena = st.text_input("Contraseña de la API key", type="password", key=_CLAVES_CAMPOS[2], max_chars=limites.API_CONTRASENA,
                                   help="La que definiste al crear la key, no la de tu cuenta.")
    datos = (identificador.strip(), api_key.strip(), api_contrasena.strip())
    prueba = st.session_state.get(_CLAVE_PRUEBA)
    vigente = prueba if prueba and prueba["datos"] == datos else None
    recaptcha.dibujar("conectar", validez=_VALIDEZ_VERIFICACION)
    if st.button("Probar conexión", width="stretch", key="conectar_probar"):
        if not all(datos):
            st.error("Completa el correo, la API key y la contraseña de la key.")
        elif limites.excede((datos[0], limites.CORREO), (datos[1], limites.API_KEY), (datos[2], limites.API_CONTRASENA)):
            st.error("Revisa los datos: alguno es demasiado largo.")
        else:
            recaptcha.exigir("conectar", validez=_VALIDEZ_VERIFICACION)
            with st.spinner("Verificando tu cuenta demo y tu cuenta real en Capital.com..."):
                pruebas = sesiones_capital.probar_ambas_cuentas(*datos)
            vigente = st.session_state[_CLAVE_PRUEBA] = {"datos": datos, "pruebas": pruebas}
    if vigente:
        _filas_resultado(vigente["pruebas"])
    pruebas = vigente["pruebas"] if vigente else None
    aceptada = bool(pruebas and (pruebas["demo"]["ok"] or pruebas["real"]["ok"]))
    if not st.button("Guardar y continuar", type="primary", width="stretch", disabled=not aceptada, key="conectar_guardar"):
        return
    recaptcha.exigir("conectar", validez=_VALIDEZ_VERIFICACION)
    previas = cuentas_conectadas()
    conectadas = []
    for nombre, es_demo in _TIPOS.items():
        if not pruebas["demo" if es_demo else "real"]["ok"]:
            continue
        guardado = credenciales_bolsa.guardar_credenciales(usuario_id, es_demo, *datos)
        if not guardado["ok"]:
            st.error(guardado["mensaje"])
            return
        conectadas.append(nombre)
    sesiones_capital.olvidar_usuario(usuario_id)
    invalidar_cuentas()
    # Solo se cambia sola de cuenta cuando es la primera vez; si ya operaba con otra, no se la cambia por sorpresa
    if not (previas.get("demo") or previas.get("real")):
        fijar_modo(True if "Demo" in conectadas else False)
    st.session_state.pop(_CLAVE_PRUEBA, None)
    for clave in _CLAVES_CAMPOS:
        st.session_state.pop(clave, None)
    st.session_state[_CLAVE_GESTIONAR] = False
    st.success("Conectado: " + " y ".join(f"cuenta {n}" for n in conectadas) + ". La plataforma siempre empieza en demo; "
               "cambias de cuenta cuando quieras desde «Seleccione cuenta».")
    st.button("Ir al panel", type="primary", width="stretch")


# TITULO LISTA DE CUENTAS

def _lista_cuentas(usuario_id: int, cuentas: dict) -> None:
    """Muestra qué cuentas están conectadas, con el botón para desconectar cada una y el de continuar al panel."""
    for nombre, es_demo in _TIPOS.items():
        columna_texto, columna_boton = st.columns([3, 1.2], vertical_alignment="center")
        conectada = cuentas.get("demo" if es_demo else "real")
        columna_texto.html(f"<div class='cc-cuenta'><b>Cuenta {nombre}</b><span class='cc-estado{' cc-estado-ok' if conectada else ''}'>{'Conectada' if conectada else 'Sin conectar'}</span></div>")
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

    st.html(_estaticos.estilos(_CSS))
    with st.container(key="conectar_dividido"):
        st.html("<div class='cc-cabecera'><div class='cc-logo'>P&amp;J</div>"
                f"<div class='cc-titulo'>Hola, {escape(str(usuario.get('nombre', '')))}</div>"
                "<div class='cc-sub'>Escribe los datos de tu API de Capital.com una sola vez: verificamos tu cuenta demo y tu cuenta real, y eliges con cuál operar cuando quieras.</div></div>")
        izquierda, derecha = st.columns(2)
        with izquierda:
            with st.container(key="conectar_formulario"):
                # Con una cuenta ya conectada se puede volver al panel desde arriba (si no, había que bajar hasta el final de la pantalla)
                if hay_cuenta and st.button("Volver al panel", key="cuentas_volver_arriba", icon=":material/arrow_back:"):
                    st.session_state[_CLAVE_GESTIONAR] = False
                    st.rerun()
                if hay_cuenta:
                    _lista_cuentas(usuario_id, cuentas)
                    st.divider()
                _formulario(usuario_id)
            # Salida para quien aún no quiere conectar una API (o la acaba de quitar): sin esto esta pantalla era una puerta sin salida, porque no deja ver nada más.
            st.html("<p class='cc-pie'>¿No quieres conectar tu API ahora? <a href='?logout=1' target='_self'>Cerrar sesión</a></p>"
                    f"<p class='cc-legal'>{enlaces_html()}</p>")
        with derecha:
            st.html(_html_guia())
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
