# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara notificaciones_base .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

"""Persistencia de las notificaciones en la tabla `notificaciones` (herramientas/sql/notificaciones.sql).

NOMBRE DEL ARCHIVO: nucleo_agente/notificaciones_base.py

La campana trabaja con la memoria del proceso (nucleo_agente/notificaciones.py); este módulo solo guarda y lee en la base de datos para que
los avisos sobrevivan a los reinicios y se vean desde cualquier dispositivo. Las escrituras salen por una cola atendida por un solo hilo
en segundo plano, en el mismo orden en que se pidieron (un aviso nunca se modifica antes de haberse insertado) y sin frenar al que avisa.

Todo es tolerante a fallos: sin conexión, sin la tabla, o para un usuario sin id numérico (modo de desarrollo), las funciones no lanzan
errores; las de lectura devuelven None (no se pudo leer) y las de escritura simplemente no hacen nada.
"""
from __future__ import annotations

import queue
import threading
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from herramientas import gestor_autenticacion

# Nombre de la tabla.
TABLA = "notificaciones"
# Días que se conservan los avisos antes de la limpieza automática.
DIAS_RETENCION = 90

# Cola de tareas de escritura y el hilo que las atiende (se crea la primera vez que se necesita).
_COLA: queue.Queue = queue.Queue()
_HILO: threading.Thread | None = None
_CANDADO_HILO = threading.Lock()


# TITULO CLIENTE

def _cliente() -> Any:
    """Cliente de la base de datos (el mismo que usa el resto de la plataforma), o None si no hay conexión configurada."""
    return gestor_autenticacion._supabase


# TITULO ID NUMERICO

def _id_numerico(usuario_id: Any) -> int | None:
    """El id del usuario como entero, o None si no lo es (por ejemplo «local» en desarrollo): esos avisos no se guardan."""
    try:
        return int(usuario_id)
    except (TypeError, ValueError):
        return None


# TITULO ATENDER COLA

def _atender_cola() -> None:
    """Bucle del hilo de escritura: ejecuta las tareas de la cola una por una y descarta (imprimiendo) las que fallen."""
    while True:
        tarea = _COLA.get()
        try:
            tarea()
        except Exception:  # noqa: BLE001 - un fallo de la base no debe detener las siguientes escrituras
            traceback.print_exc()
        finally:
            _COLA.task_done()


# TITULO EN SEGUNDO PLANO

def en_segundo_plano(tarea: Callable[[], None]) -> None:
    """Pone `tarea` en la cola de escritura, arrancando el hilo la primera vez."""
    global _HILO
    with _CANDADO_HILO:
        if _HILO is None or not _HILO.is_alive():
            _HILO = threading.Thread(target=_atender_cola, name="notificaciones-base", daemon=True)
            _HILO.start()
    _COLA.put(tarea)


# TITULO ESPERAR COLA

def esperar_cola() -> None:
    """Bloquea hasta que se hayan ejecutado todas las escrituras pendientes (lo usan las pruebas)."""
    _COLA.join()


# TITULO A FILA

def _a_fila(fila: dict[str, Any]) -> dict[str, Any]:
    """Convierte una fila de la tabla al formato de la memoria (con `creada` como marca de tiempo Unix)."""
    creada = fila.get("creada")
    if isinstance(creada, str):
        creada = datetime.fromisoformat(creada.replace("Z", "+00:00"))
    return {
        "id": str(fila["id"]), "titulo": fila.get("titulo") or "", "texto": fila.get("texto") or "",
        "tipo": fila.get("tipo") or "agente", "ref": fila.get("ref"), "leida": bool(fila.get("leida")),
        "oculta": bool(fila.get("oculta")),
        "creada": creada.timestamp() if isinstance(creada, datetime) else float(creada or 0),
    }


# TITULO GUARDAR

def guardar(usuario_id: Any, aviso: dict[str, Any]) -> None:
    """Inserta el aviso en la tabla (en segundo plano). No hace nada si no hay conexión o el usuario no tiene id numérico."""
    numero, cliente = _id_numerico(usuario_id), _cliente()
    if numero is None or cliente is None:
        return
    fila = {
        "id": aviso["id"], "usuario_id": numero, "tipo": aviso["tipo"], "titulo": aviso["titulo"], "texto": aviso["texto"],
        "ref": aviso.get("ref"), "leida": bool(aviso["leida"]),
        "creada": datetime.fromtimestamp(aviso["creada"], timezone.utc).isoformat(),
    }
    en_segundo_plano(lambda: cliente.table(TABLA).insert(fila).execute())


# TITULO LEER

def leer(usuario_id: Any, limite: int, incluir_ocultas: bool = False) -> list[dict[str, Any]] | None:
    """Los `limite` avisos más recientes del usuario (la campana excluye los ocultos; el historial los incluye).

    Devuelve lista vacía si el usuario no tiene id numérico y None si no se pudo consultar (sin conexión, sin tabla o error)."""
    numero, cliente = _id_numerico(usuario_id), _cliente()
    if numero is None:
        return []
    if cliente is None:
        return None
    try:
        consulta = cliente.table(TABLA).select("*").eq("usuario_id", numero)
        if not incluir_ocultas:
            consulta = consulta.eq("oculta", False)
        return [_a_fila(f) for f in consulta.order("creada", desc=True).limit(limite).execute().data]
    except Exception:  # noqa: BLE001 - la campana sigue con la memoria
        return None


# TITULO MARCAR LEIDAS

def marcar_leidas(usuario_id: Any, ref: str | None = None) -> None:
    """Marca como leídos (en segundo plano) los avisos no leídos del usuario, o solo los de la referencia `ref`."""
    numero, cliente = _id_numerico(usuario_id), _cliente()
    if numero is None or cliente is None:
        return

    def tarea() -> None:
        consulta = cliente.table(TABLA).update({"leida": True}).eq("usuario_id", numero).eq("leida", False)
        (consulta.eq("ref", ref) if ref is not None else consulta).execute()

    en_segundo_plano(tarea)


# TITULO OCULTAR

def ocultar(usuario_id: Any) -> None:
    """Oculta de la campana (y marca como leídos) todos los avisos del usuario; siguen en el historial. En segundo plano."""
    numero, cliente = _id_numerico(usuario_id), _cliente()
    if numero is None or cliente is None:
        return
    en_segundo_plano(lambda: cliente.table(TABLA).update({"oculta": True, "leida": True}).eq("usuario_id", numero).eq("oculta", False).execute())


# TITULO DEPURAR

def depurar() -> None:
    """Borra (en segundo plano) los avisos de más de DIAS_RETENCION días de todos los usuarios."""
    cliente = _cliente()
    if cliente is None:
        return
    limite = (datetime.now(timezone.utc) - timedelta(days=DIAS_RETENCION)).isoformat()
    en_segundo_plano(lambda: cliente.table(TABLA).delete().lt("creada", limite).execute())


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara notificaciones_base .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
