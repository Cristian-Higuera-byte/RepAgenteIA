# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara notificaciones .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Notificaciones del dashboard (campana de la barra superior).

NOMBRE DEL ARCHIVO: nucleo_agente/notificaciones.py

Almacén en memoria del proceso, por usuario. No usa Streamlit, así que lo puede escribir un hilo
en segundo plano (nucleo_agente/turnos.py) y leer la barra superior (componentes_plataforma/barra_superior/).

Las notificaciones se pierden si se reinicia el servidor; es un aviso, no un registro de auditoría
(la auditoría de las órdenes ya está en data/ordenes.db).
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

# Tope de notificaciones que se conservan por usuario; las más antiguas se descartan.
MAX_POR_USUARIO = 50

# Candado que protege _DATOS: lo escriben hilos en segundo plano y lo lee la interfaz.
_CANDADO = threading.Lock()
# Almacén en memoria: id de usuario -> lista de notificaciones (la más reciente primero).
_DATOS: dict[str, list[dict[str, Any]]] = {}


# TITULO AGREGAR

def agregar(
    usuario_id: str,
    titulo: str,
    texto: str = "",
    tipo: str = "agente",        # agente | orden | error
    ref: str | None = None,      # id del turno que la originó
    leida: bool = False,
) -> dict[str, Any]:
    """Agrega una notificación al inicio de la lista del usuario y devuelve una copia de ella.

    Recibe el usuario, el título y texto a mostrar, el tipo (agente, orden o error), la referencia
    al turno que la originó y si nace ya leída. Si se supera MAX_POR_USUARIO descarta las más viejas.
    """
    # Se arma el registro con un id corto aleatorio y la hora de creación.
    nueva = {
        "id": uuid.uuid4().hex[:8], "titulo": titulo, "texto": texto, "tipo": tipo,
        "ref": ref, "leida": leida, "creada": time.time(),
    }
    # Inserción protegida por el candado: la lista queda ordenada de más reciente a más antigua.
    with _CANDADO:
        lista = _DATOS.setdefault(usuario_id, [])
        lista.insert(0, nueva)
        del lista[MAX_POR_USUARIO:]
    return dict(nueva)


# TITULO LISTAR

def listar(usuario_id: str, limite: int = 10) -> list[dict[str, Any]]:
    """Devuelve copias de las `limite` notificaciones más recientes del usuario."""
    with _CANDADO:
        return [dict(n) for n in _DATOS.get(usuario_id, [])[:limite]]


# TITULO NO LEIDAS

def no_leidas(usuario_id: str) -> int:
    """Cuenta las notificaciones sin leer del usuario (el número que muestra la campana)."""
    with _CANDADO:
        return sum(1 for n in _DATOS.get(usuario_id, []) if not n["leida"])


# TITULO ULTIMA ID

def ultima_id(usuario_id: str) -> str | None:
    """Id de la notificación más reciente (sirve para detectar que llegó una nueva)."""
    with _CANDADO:
        lista = _DATOS.get(usuario_id, [])
        return lista[0]["id"] if lista else None


# TITULO MARCAR LEIDAS

def marcar_leidas(usuario_id: str, ref: str | None = None) -> None:
    """Marca como leídas todas las del usuario, o solo las de un turno (`ref`)."""
    with _CANDADO:
        for n in _DATOS.get(usuario_id, []):
            if ref is None or n["ref"] == ref:
                n["leida"] = True


# TITULO LIMPIAR

def limpiar(usuario_id: str) -> None:
    """Elimina todas las notificaciones del usuario."""
    with _CANDADO:
        _DATOS.pop(usuario_id, None)


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara notificaciones .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
