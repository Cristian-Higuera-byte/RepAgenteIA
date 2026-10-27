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
Mecánica de la sesión de usuario (sin UI): iniciar, cerrar y restaurar la sesión a
partir del token que vive en la URL (?s=...). El token lo guarda almacen_sesiones en el
servidor, así la sesión sobrevive a un F5 mientras la consola esté encendida. Además, una cookie de larga duración (herramientas/sesion_persistente.py y
acceso/cookie.py) la mantiene abierta al cerrar el navegador y al reiniciar el servidor (30 días, hasta que el usuario cierre sesión).

Estado de sesión de Streamlit que maneja este módulo:
  * `usuario_autenticado` (bool): indica que esta pestaña ya inició sesión.
  * `usuario_informacion` (dict): datos del usuario ({id, nombre, email}).
Lo consume acceso/pantalla.py (requerir_login) y, a través de él, aplicacion.py.
"""
import streamlit as st

from herramientas import almacen_sesiones, sesion_persistente

from . import cookie


# TITULO CERRAR SESION

def cerrar_sesion() -> None:
    """Cierra la sesión del usuario actual.

    Efectos secundarios: elimina del almacén de sesiones del servidor el token que viaja en
    el parámetro `s` de la URL y borra de `st.session_state` las claves `usuario_autenticado`
    y `usuario_informacion`, revoca la sesión persistente de la cookie y programa borrar esa cookie. No devuelve nada; el llamador decide si limpia la URL y reejecuta.
    """
    # Invalida el token en el servidor para que un F5 ya no restaure la sesión
    almacen_sesiones.eliminar(st.query_params.get("s", ""))
    # Invalida también la sesión de larga duración (cookie) y deja pendiente borrarla del navegador
    sesion_persistente.revocar(cookie.leer())
    cookie.programar_borrado()
    # Olvida el estado local de la pestaña
    for clave in ("usuario_autenticado", "usuario_informacion"):
        st.session_state.pop(clave, None)


# TITULO INICIAR SESION

def iniciar_sesion(usuario: dict) -> None:
    """Inicia la sesión de un usuario ya validado.

    Recibe `usuario`, el dict ({id, nombre, email}) devuelto por la autenticación o el
    registro. Marca la sesión en `st.session_state`, crea un token en almacen_sesiones y lo
    guarda en la URL (`?s=...`) para que sobreviva al F5, y fuerza un `st.rerun()` (por lo
    que no retorna con normalidad). El overlay de carga de aplicacion.py tapa el login
    mientras el dashboard se arma, así se entra directo sin verlo encima.
    """
    # Marca la pestaña como autenticada y guarda los datos del usuario
    st.session_state.usuario_autenticado = True
    st.session_state.usuario_informacion = usuario
    st.query_params["s"] = almacen_sesiones.crear(usuario)  # persiste tras F5
    # «Mantener sesión iniciada»: token de larga duración guardado en Supabase y en una cookie del navegador (se escribe en la próxima pasada)
    token_larga = sesion_persistente.crear(usuario.get("id"), st.context.headers.get("User-Agent", ""), reemplaza_token=cookie.leer())
    if token_larga:
        cookie.programar_guardado(token_larga)
    st.rerun()


# TITULO USUARIO EN SESION

def usuario_en_sesion() -> dict | None:
    """Devuelve el usuario autenticado de esta pestaña, o None si no hay sesión.

    Primero consulta `st.session_state`; si está vacío (por ejemplo tras un F5) intenta
    restaurar la sesión con el token `s` de la URL consultando almacen_sesiones y, si no hay, con la cookie de larga duración. Al
    restaurar, vuelve a poblar `usuario_autenticado` y `usuario_informacion` en el estado de sesión.
    """
    # Caso normal: la pestaña ya está autenticada
    if st.session_state.get("usuario_autenticado"):
        return st.session_state.get("usuario_informacion", {})

    # Tras un F5, session_state se vacía pero el token sigue en la URL:
    # si el servidor aún lo tiene (consola encendida), restauramos la sesión.
    token = st.query_params.get("s")
    if token:
        usuario = almacen_sesiones.obtener(token)
        if usuario:
            st.session_state.usuario_autenticado = True
            st.session_state.usuario_informacion = usuario
            return usuario

    # Sin token en la URL (navegador cerrado y abierto de nuevo, o servidor reiniciado): se prueba la cookie de «mantener sesión iniciada».
    # Si es válida se restaura la sesión y se crea un token `?s=` nuevo para esta pestaña.
    usuario = sesion_persistente.validar(cookie.leer())
    if usuario:
        st.session_state.usuario_autenticado = True
        st.session_state.usuario_informacion = usuario
        st.query_params["s"] = almacen_sesiones.crear(usuario)
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
