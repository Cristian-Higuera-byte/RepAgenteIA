# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara cookie .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
acceso/cookie.py
----------------
Escribe y borra en el navegador la cookie de «mantener sesión iniciada». Streamlit puede LEER las cookies del navegador (`st.context.cookies`) pero no
crearlas, así que la cookie la pone un script mínimo que corre en el navegador. La acción se deja pendiente en `st.session_state` (porque al iniciar o cerrar
sesión la app se vuelve a ejecutar enseguida) y `aplicar_pendiente()` la emite en la siguiente pasada de `requerir_login()`.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

from herramientas.sesion_persistente import DIAS_DURACION, NOMBRE_COOKIE

# Clave de st.session_state donde queda la acción pendiente: ("guardar", token) o ("borrar", None).
_PENDIENTE = "_cookie_sesion_pendiente"


# TITULO PROGRAMAR GUARDADO

def programar_guardado(token: str) -> None:
    """Deja pendiente guardar la cookie con ese token en el navegador (se escribe en la próxima pasada de la app)."""
    st.session_state[_PENDIENTE] = ("guardar", token)


# TITULO PROGRAMAR BORRADO

def programar_borrado() -> None:
    """Deja pendiente borrar la cookie del navegador (cerrar sesión)."""
    st.session_state[_PENDIENTE] = ("borrar", None)


# TITULO LEER

def leer() -> str:
    """Devuelve el token de la cookie que el navegador envió en esta petición, o una cadena vacía si no hay."""
    try:
        return st.context.cookies.get(NOMBRE_COOKIE, "") or ""
    except Exception:
        return ""


# TITULO APLICAR PENDIENTE

def aplicar_pendiente() -> None:
    """Escribe o borra la cookie en el navegador si hay una acción pendiente; luego la olvida.

    Emite un componente de altura 0 cuyo script usa `document.cookie` de la página de Streamlit (el componente es del mismo origen). Atributos de la cookie:
    `Max-Age` de DIAS_DURACION días (sobrevive al cierre del navegador), `Path=/`, `SameSite=Lax` y `Secure` cuando la página va por HTTPS.
    """
    accion = st.session_state.pop(_PENDIENTE, None)
    if not accion:
        return
    tipo, token = accion
    nombre = json.dumps(NOMBRE_COOKIE)
    if tipo == "guardar":
        valor = json.dumps(token)
        duracion = DIAS_DURACION * 24 * 3600
    else:
        valor = json.dumps("")
        duracion = 0
    components.html(
        "<script>(function(){"
        "var D;try{D=window.parent.document;}catch(e){return;}"
        "var seguro=(window.parent.location.protocol==='https:')?'; Secure':'';"
        f"D.cookie={nombre}+'='+{valor}+'; Max-Age={duracion}; Path=/; SameSite=Lax'+seguro;"
        "})();</script>",
        height=0,
    )


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara cookie .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
