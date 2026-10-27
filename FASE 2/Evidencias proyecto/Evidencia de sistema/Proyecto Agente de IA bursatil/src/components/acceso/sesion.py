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
servidor, así la sesión sobrevive a un F5 mientras la consola esté encendida.

Estado de sesión de Streamlit que maneja este módulo:
  * `usuario_autenticado` (bool): indica que esta pestaña ya inició sesión.
  * `usuario_info` (dict): datos del usuario ({id, nombre, email}).
Lo consume acceso/pantalla.py (requerir_login) y, a través de él, app.py.
"""
import streamlit as st

from tools import almacen_sesiones


def cerrar_sesion() -> None:
    """Cierra la sesión del usuario actual.

    Efectos secundarios: elimina del almacén de sesiones del servidor el token que viaja en
    el parámetro `s` de la URL y borra de `st.session_state` las claves `usuario_autenticado`
    y `usuario_info`. No devuelve nada; el llamador decide si limpia la URL y reejecuta.
    """
    # Invalida el token en el servidor para que un F5 ya no restaure la sesión
    almacen_sesiones.eliminar(st.query_params.get("s", ""))
    # Olvida el estado local de la pestaña
    for clave in ("usuario_autenticado", "usuario_info"):
        st.session_state.pop(clave, None)


def iniciar_sesion(usuario: dict) -> None:
    """Inicia la sesión de un usuario ya validado.

    Recibe `usuario`, el dict ({id, nombre, email}) devuelto por la autenticación o el
    registro. Marca la sesión en `st.session_state`, crea un token en almacen_sesiones y lo
    guarda en la URL (`?s=...`) para que sobreviva al F5, y fuerza un `st.rerun()` (por lo
    que no retorna con normalidad). El overlay de carga de app.py tapa el login
    mientras el dashboard se arma, así se entra directo sin verlo encima.
    """
    # Marca la pestaña como autenticada y guarda los datos del usuario
    st.session_state.usuario_autenticado = True
    st.session_state.usuario_info = usuario
    st.query_params["s"] = almacen_sesiones.crear(usuario)  # persiste tras F5
    st.rerun()


def usuario_en_sesion() -> dict | None:
    """Devuelve el usuario autenticado de esta pestaña, o None si no hay sesión.

    Primero consulta `st.session_state`; si está vacío (por ejemplo tras un F5) intenta
    restaurar la sesión con el token `s` de la URL consultando almacen_sesiones. Al
    restaurar, vuelve a poblar `usuario_autenticado` y `usuario_info` en el estado de sesión.
    """
    # Caso normal: la pestaña ya está autenticada
    if st.session_state.get("usuario_autenticado"):
        return st.session_state.get("usuario_info", {})

    # Tras un F5, session_state se vacía pero el token sigue en la URL:
    # si el servidor aún lo tiene (consola encendida), restauramos la sesión.
    token = st.query_params.get("s")
    if token:
        usuario = almacen_sesiones.obtener(token)
        if usuario:
            st.session_state.usuario_autenticado = True
            st.session_state.usuario_info = usuario
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
