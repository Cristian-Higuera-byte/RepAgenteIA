# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara contexto .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Contexto de la consulta en curso (quién la hace).

NOMBRE DEL ARCHIVO: core/contexto.py

Las herramientas del agente son funciones normales y no reciben al usuario como argumento. Mientras
core/turnos/hilo.py ejecuta una consulta en su hilo, fija aquí el usuario; las herramientas que lo
necesitan (p. ej. crear una vigilancia automática) lo leen con usuario_actual(). Es por hilo
(ContextVar), así que consultas de usuarios distintos no se mezclan.
"""

from __future__ import annotations

import builtins
import contextvars

# Usuario de la consulta en curso en este hilo/contexto; "local" cuando nadie lo fijó (p. ej. consola).
# La variable se guarda también en `builtins` para que exista UNA sola por proceso: Streamlit vuelve a importar
# un módulo cuando su archivo cambia en disco (por ejemplo, al actualizar el proyecto con la página abierta) y,
# si cada copia del módulo creara su propia variable, el hilo que fija el usuario y la herramienta que lo lee
# quedarían con variables distintas y la herramienta vería siempre "local" (la vigilancia se guardaba con otro
# usuario y no aparecía en «Órdenes propuestas»).
_USUARIO: contextvars.ContextVar[str] = getattr(builtins, "_pj_contexto_usuario", None) or contextvars.ContextVar(
    "usuario_id", default="local")
builtins._pj_contexto_usuario = _USUARIO  # type: ignore[attr-defined]


def fijar_usuario(usuario_id: str) -> None:
    """Fija el usuario de la consulta en curso en el contexto actual.

    Recibe el id del usuario; si viene vacío o None se usa "local". Solo afecta al hilo/contexto que
    la llama (ContextVar), por lo que no interfiere con consultas de otros usuarios.
    """
    _USUARIO.set(str(usuario_id or "local"))


def usuario_actual() -> str:
    """Devuelve el id del usuario fijado para la consulta en curso ("local" si no se fijó ninguno)."""
    return _USUARIO.get()


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara contexto .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
