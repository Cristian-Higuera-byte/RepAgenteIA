# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------------- INICIO Piña y Jara modo .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
conectar_cuenta/modo.py
-----------------------
Estado de las cuentas del usuario en la sesión de Streamlit: qué cuentas tiene conectadas (demo y real) y cuál
está usando ahora, como el selector de Capital.com.

Reglas de seguridad:
- Al entrar (o al recargar la página) se parte SIEMPRE en demo si existe; la cuenta real hay que elegirla a propósito.
- El modo elegido solo vale si esa cuenta está conectada; si no, se cae a la que haya.

`registrar_resolvedor()` le dice al backend (herramientas/backends/sesiones_capital.py) cómo saber quién es el usuario
y su modo en cada llamada; lee solo `st.session_state`, así funciona también dentro de los fragmentos en vivo.
"""
import time
from typing import Optional

import streamlit as st

from herramientas import almacen_sesiones, credenciales_bolsa, token_datos
from herramientas.backends import sesiones_capital

# Claves de st.session_state
_CLAVE_CUENTAS = "cuentas_conectadas_cache"   # (epoch, {"demo": bool, "real": bool})
_CLAVE_MODO = "cuenta_modo_demo"              # True = demo, False = real
# Segundos que se confía en la lista de cuentas antes de volver a preguntarle a Supabase
_VIDA_CUENTAS_S = 60.0


# TITULO USUARIO ID ACTUAL

def usuario_id_actual() -> Optional[int]:
    """Devuelve el id del usuario autenticado en esta sesión, o None si no hay."""
    informacion = st.session_state.get("usuario_informacion") or {}
    try:
        return int(informacion["id"])
    except (KeyError, TypeError, ValueError):
        return None


# TITULO CUENTAS CONECTADAS

def cuentas_conectadas(refrescar: bool = False) -> dict:
    """Devuelve {"demo": bool, "real": bool}: qué cuentas tiene conectadas el usuario.

    Consulta Supabase como máximo una vez por minuto (o cuando `refrescar` es True); el resto del tiempo usa la copia
    guardada en la sesión."""
    guardado = st.session_state.get(_CLAVE_CUENTAS)
    if guardado and not refrescar and time.time() - guardado[0] < _VIDA_CUENTAS_S:
        return guardado[1]
    usuario_id = usuario_id_actual()
    estado = credenciales_bolsa.estado_credenciales(usuario_id) if usuario_id is not None else {"demo": False, "real": False}
    st.session_state[_CLAVE_CUENTAS] = (time.time(), estado)
    return estado


# TITULO INVALIDAR CUENTAS

def invalidar_cuentas() -> None:
    """Descarta la copia guardada de las cuentas conectadas, para que se relea en la próxima consulta."""
    st.session_state.pop(_CLAVE_CUENTAS, None)


# TITULO MODO ACTIVO DEMO

def modo_activo_demo() -> bool:
    """True si se está operando en la cuenta demo, False si es la real.

    Usa solo la copia guardada en la sesión (nunca consulta la red): se llama en cada petición al bróker.
    Sin ninguna cuenta conectada devuelve True (demo)."""
    estado = (st.session_state.get(_CLAVE_CUENTAS) or (0, {}))[1]
    elegido = st.session_state.get(_CLAVE_MODO)
    if elegido is True and estado.get("demo"):
        return True
    if elegido is False and estado.get("real"):
        return False
    if estado.get("demo"):
        return True
    if estado.get("real"):
        return False
    return True


# TITULO FIJAR MODO

def fijar_modo(es_demo: bool) -> None:
    """Elige la cuenta con la que se opera: True = demo, False = real.

    Además de la sesión de la pestaña, lo guarda junto a la sesión del servidor (token `s` de la URL): así la elección
    sobrevive a un F5 y a los enlaces del menú (Perfil, Configuración) que recargan la página. Un inicio de sesión
    nuevo no la hereda: siempre parte en demo."""
    st.session_state[_CLAVE_MODO] = bool(es_demo)
    almacen_sesiones.guardar_dato(str(st.query_params.get("s", "")), "modo_demo", bool(es_demo))


# TITULO RESTAURAR MODO

def restaurar_modo() -> None:
    """Si la pestaña acaba de recargarse (sin cuenta elegida), recupera la que el usuario había elegido en esta sesión."""
    if _CLAVE_MODO in st.session_state:
        return
    guardado = almacen_sesiones.leer_dato(str(st.query_params.get("s", "")), "modo_demo")
    if guardado is not None:
        st.session_state[_CLAVE_MODO] = bool(guardado)


# TITULO RESOLVER USUARIO Y MODO

def resolver_usuario_y_modo() -> Optional[tuple]:
    """Devuelve (usuario_id, es_demo) del usuario de esta sesión, o None si no hay sesión (o no hay contexto de Streamlit)."""
    usuario_id = usuario_id_actual()
    if usuario_id is None:
        return None
    return (usuario_id, modo_activo_demo())


# TITULO URL DEL SERVIDOR

def url_servidor(url_base: str) -> str:
    """Devuelve la dirección del servidor de datos que debe usar el navegador de ESTE usuario.

    Con el modo multiusuario apagado es la misma dirección de siempre. Encendido, le agrega el token firmado del
    usuario y su cuenta actual (`<url>/t/<token>`), con lo que el servidor sabe quién es y con qué cuenta operar."""
    if not sesiones_capital.MULTIUSUARIO:
        return url_base
    usuario_id = usuario_id_actual()
    if usuario_id is None:
        return url_base
    return token_datos.url_con_token(url_base, usuario_id, modo_activo_demo())


# TITULO REGISTRAR RESOLVEDOR

def registrar_resolvedor() -> None:
    """Enseña al backend de Capital a saber quién es el usuario actual (idempotente)."""
    sesiones_capital.fijar_resolvedor(resolver_usuario_y_modo)


# -------------------------------------------------------------------------------------------------------
# ----------------------------------------- FIN Piña y Jara modo .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
