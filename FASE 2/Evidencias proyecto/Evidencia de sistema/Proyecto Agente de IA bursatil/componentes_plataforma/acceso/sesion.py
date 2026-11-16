# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara sesion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
acceso/sesion.py
---------------
Mecánica de la sesión de usuario (sin UI): iniciar, cerrar y restaurar la sesión.

La sesión NO viaja en la dirección (antes era `?s=<token>`: quedaba en el historial, en capturas de pantalla, en enlaces copiados y en los registros de los
servidores). Se mantiene con una cookie de larga duración (herramientas/sesion_persistente.py y acceso/cookie.py): sobrevive a un F5, a los enlaces del menú, al cierre del
navegador y al reinicio del servidor (30 días, hasta que el usuario cierre sesión). Cada dispositivo tiene su propia cookie y de ella se deriva el identificador de la
sesión (`identificador()`), que se usa dentro del servidor para guardar datos de la sesión (la cuenta elegida) y para revocar el token del servidor de datos.

Estado de sesión de Streamlit que maneja este módulo:
  * `usuario_autenticado` (bool): indica que esta pestaña ya inició sesión.
  * `usuario_informacion` (dict): datos del usuario ({id, nombre, email}).
  * `_sid` (str): identificador de la sesión de este dispositivo (resumen de su cookie; ver `identificador()`).
Lo consume acceso/pantalla.py (requerir_login) y, a través de él, aplicacion.py.
"""
import secrets
import time

import streamlit as st

from herramientas import almacen_sesiones, sesion_persistente, token_datos

from . import cookie

# Clave de st.session_state con el identificador de la sesión de este dispositivo
_SID = "_sid"

# Claves de st.session_state que se borran al cerrar o perder la sesión
_CLAVES = ("usuario_autenticado", "usuario_informacion", "_sesion_desde", _SID)


# TITULO IDENTIFICADOR

def identificador() -> str:
    """Identificador de la sesión de ESTE dispositivo (16 caracteres hexadecimales), o '' si no hay sesión.

    Sale del resumen de la cookie de sesión, así que es el mismo tras un F5, en otra pestaña del mismo navegador y tras reiniciar la página; nunca contiene la cookie
    ni viaja en la dirección. Se usa para guardar datos de la sesión (la cuenta elegida) y para invalidar el token del servidor de datos al cerrar sesión."""
    return st.session_state.get(_SID) or token_datos.huella_sesion(cookie.leer())


# TITULO QUITAR PARAMETRO ANTIGUO

def _quitar_parametro_antiguo() -> None:
    """Quita de la dirección el parámetro `s` de las versiones anteriores (enlaces guardados o abiertos antes del cambio): ya no se usa para nada."""
    if "s" in st.query_params:
        del st.query_params["s"]


# TITULO CERRAR SESION EN TODOS

def cerrar_sesion_en_todos(usuario_id) -> None:
    """Cierra la sesión del usuario en este dispositivo y en todos los demás.

    Borra todas sus sesiones persistentes (las cookies de larga duración dejan de servir) y sus tokens de la URL, y anota el instante: las pestañas de otros dispositivos que
    ya estaban abiertas se cierran en su próxima ejecución completa (el celular, al recargar o pulsar algo). Luego cierra la de este dispositivo."""
    sesion_persistente.revocar_todas(usuario_id)
    almacen_sesiones.revocar_usuario(usuario_id)
    token_datos.revocar_usuario(usuario_id)       # el token del servidor de datos (otro proceso) y sus conexiones en vivo también dejan de servir
    cerrar_sesion()


# TITULO CERRAR SESION

def cerrar_sesion() -> None:
    """Cierra la sesión del usuario actual.

    Efectos secundarios: elimina del almacén de sesiones del servidor el token que viaja en
    el parámetro `s` de la URL y borra de `st.session_state` las claves `usuario_autenticado`
    y `usuario_informacion`, revoca la sesión persistente de la cookie y programa borrar esa cookie. No devuelve nada; el llamador decide si limpia la URL y reejecuta.
    """
    # El token del servidor de datos de esta sesión (y sus conexiones en vivo) deja de servir; debe hacerse antes de olvidar quién es el usuario
    usuario_id = (st.session_state.get("usuario_informacion") or {}).get("id")
    sid = identificador()
    if usuario_id is not None and sid:
        token_datos.revocar_sesion(usuario_id, sid)
    # Olvida los datos de la sesión guardados en el servidor
    almacen_sesiones.eliminar(sid)
    _quitar_parametro_antiguo()
    # Invalida también la sesión de larga duración (cookie) y deja pendiente borrarla del navegador
    sesion_persistente.revocar(cookie.leer())
    cookie.programar_borrado()
    # Olvida el estado local de la pestaña
    for clave in _CLAVES:
        st.session_state.pop(clave, None)


# TITULO INICIAR SESION

def iniciar_sesion(usuario: dict) -> None:
    """Inicia la sesión de un usuario ya validado.

    Recibe `usuario`, el dict ({id, nombre, email}) devuelto por la autenticación o el
    registro. Marca la sesión en `st.session_state`, crea un token en almacen_sesiones y lo
    deja la cookie de «mantener sesión» (de ella sale el identificador de la sesión, que no viaja en la dirección) y fuerza un `st.rerun()` (por lo
    que no retorna con normalidad). El overlay de carga de aplicacion.py tapa el login
    mientras el dashboard se arma, así se entra directo sin verlo encima.
    """
    # Marca la pestaña como autenticada y guarda los datos del usuario
    st.session_state.usuario_autenticado = True
    st.session_state.usuario_informacion = usuario
    st.session_state["_sesion_desde"] = time.time()   # para saber si la sesión se cerró en todos los dispositivos después de iniciarla
    if "acceso" in st.query_params:   # ya no hace falta el parámetro de la portada
        del st.query_params["acceso"]
    _quitar_parametro_antiguo()
    # Sesión de larga duración: token guardado (solo su hash) en la base y en una cookie del navegador (se escribe en la próxima pasada). Ella es lo que mantiene la
    # sesión tras un F5 o un enlace del menú. Si no se pudo guardar, la sesión vive solo en esta pestaña, con un identificador aleatorio.
    token_larga = sesion_persistente.crear(usuario.get("id"), st.context.headers.get("User-Agent", ""), reemplaza_token=cookie.leer())
    sid = token_datos.huella_sesion(token_larga or secrets.token_urlsafe(24))
    almacen_sesiones.registrar(sid, usuario)
    st.session_state[_SID] = sid
    if token_larga:
        cookie.programar_guardado(token_larga)
    st.rerun()


# TITULO USUARIO EN SESION

def usuario_en_sesion() -> dict | None:
    """Devuelve el usuario autenticado de esta pestaña, o None si no hay sesión.

    Primero consulta `st.session_state`; si está vacío (por ejemplo tras un F5 o un enlace del menú) intenta restaurar la sesión con la cookie de larga duración. Al
    restaurar, vuelve a poblar `usuario_autenticado`, `usuario_informacion` y el identificador de la sesión en el estado de sesión.
    """
    # Caso normal: la pestaña ya está autenticada
    if st.session_state.get("usuario_autenticado"):
        usuario = st.session_state.get("usuario_informacion", {})
        # Si el usuario cerró sus sesiones en todos los dispositivos después de abrir esta, ya no vale: se olvida y se pide iniciar sesión de nuevo
        if almacen_sesiones.revocada_desde(usuario.get("id")) > st.session_state.get("_sesion_desde", 0):
            for clave in _CLAVES:
                st.session_state.pop(clave, None)
            return None
        return usuario

    # Tras un F5, un enlace del menú o con el navegador cerrado y abierto de nuevo, session_state está vacío: se restaura con la cookie de «mantener sesión iniciada».
    # Un parámetro `?s=` de enlaces antiguos se ignora y se quita de la dirección.
    _quitar_parametro_antiguo()
    token = cookie.leer()
    usuario = sesion_persistente.validar(token)
    if usuario:
        sid = token_datos.huella_sesion(token)
        almacen_sesiones.registrar(sid, usuario)
        st.session_state.usuario_autenticado = True
        st.session_state.usuario_informacion = usuario
        st.session_state["_sesion_desde"] = time.time()
        st.session_state[_SID] = sid
        return usuario
    return None


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara sesion .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
