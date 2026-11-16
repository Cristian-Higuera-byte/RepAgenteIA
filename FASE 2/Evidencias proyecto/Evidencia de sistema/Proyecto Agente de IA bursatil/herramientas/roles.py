# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- INICIO Piña y Jara roles .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Roles de los usuarios de la plataforma: «usuario» (el de todos) y «root» (administrador).

NOMBRE DEL ARCHIVO: herramientas/roles.py

Un usuario es root si (1) su correo está en la variable `ROOT_CORREOS` del .env (lista separada por comas; sirve para empezar sin tocar la base de datos) o
(2) su fila de la tabla `usuarios` tiene la columna `rol` en «root» (herramientas/sql/roles.sql). Solo los root ven las secciones internas (hoy, el Laboratorio),
porque muestran datos de toda la plataforma: costos, demanda de planes, correos de la lista de espera y consumo de IA de todos los usuarios.

Detalles de seguridad: la comprobación se hace del lado del servidor cada vez que se dibuja la sección (no basta con ocultar el botón). El rol de la base de
datos se recuerda 60 segundos; si la columna `rol` no existe todavía o la base falla, nadie es root por esa vía (se falla cerrado). Ser root por correo depende de
que el correo esté verificado (`VERIFICACION_CORREO=true`): sin eso, cualquiera podría registrarse con ese correo; por eso conviene preferir el rol en la base de datos.
En el modo de un solo usuario (desarrollo, sin `CAPITAL_MULTIUSUARIO`) el dueño del equipo es root.
"""
import threading
import time
from typing import Any

import configuracion
from herramientas import gestor_autenticacion
from herramientas.backends import sesiones_capital

# Valores del rol
ROL_USUARIO = "usuario"
ROL_ROOT = "root"
# Segundos que se recuerda el rol leído de la base de datos
VIGENCIA_ROL = 60.0
# Roles recordados: id del usuario -> (instante de lectura, rol o None si no se pudo leer)
_RECORDADOS: dict[str, tuple[float, str | None]] = {}
_CANDADO = threading.Lock()


# TITULO ROL EN BASE

def _rol_en_base(usuario_id: Any) -> str | None:
    """Rol del usuario según la columna `rol` de la tabla `usuarios`, o None si no hay conexión, la columna no existe o falla la consulta."""
    cliente = gestor_autenticacion._supabase
    if cliente is None or usuario_id in (None, ""):
        return None
    clave, ahora = str(usuario_id), time.time()
    with _CANDADO:
        guardado = _RECORDADOS.get(clave)
    if guardado is not None and ahora - guardado[0] < VIGENCIA_ROL:
        return guardado[1]
    try:
        filas = cliente.table("usuarios").select("rol").eq("id", int(usuario_id)).limit(1).execute().data
        rol = filas[0].get("rol") if filas else None
    except Exception:  # noqa: BLE001 - sin la columna o sin base no se concede nada
        rol = None
    with _CANDADO:
        _RECORDADOS[clave] = (ahora, rol)
    return rol


# TITULO OLVIDAR

def olvidar(usuario_id: Any) -> None:
    """Descarta el rol recordado del usuario (úsalo tras cambiar su rol en la base de datos para que rija de inmediato)."""
    with _CANDADO:
        _RECORDADOS.pop(str(usuario_id), None)


# TITULO ES ROOT

def es_root(usuario: Any) -> bool:
    """True si `usuario` (el diccionario de la sesión, con `id` y `email`) es administrador.

    Sin usuario o con un valor que no es un diccionario devuelve False (salvo en el modo de un solo usuario de desarrollo)."""
    if not sesiones_capital.MULTIUSUARIO:
        return True
    if not isinstance(usuario, dict):
        return False
    correo = str(usuario.get("email") or "").strip().lower()
    if correo and correo in configuracion.ROOT_CORREOS:
        return True
    return _rol_en_base(usuario.get("id")) == ROL_ROOT


# -------------------------------------------------------------------------------------------------------
# ---------------------------------------- FIN Piña y Jara roles .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
