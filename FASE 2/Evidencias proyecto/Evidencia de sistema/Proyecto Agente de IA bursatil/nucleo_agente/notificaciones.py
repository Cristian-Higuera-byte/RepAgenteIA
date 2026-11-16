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

Almacén en memoria del proceso, por usuario, respaldado en la tabla `notificaciones` (nucleo_agente/notificaciones_base.py). No usa
Streamlit, así que lo puede escribir un hilo en segundo plano (nucleo_agente/turnos.py) y leer la barra superior
(componentes_plataforma/barra_superior/).

La campana trabaja siempre con la memoria (el vigilante la consulta cada pocos segundos, sin tocar la base de datos). Cada aviso nuevo y
cada cambio (leído, oculto) se escribe además en la base, en segundo plano, y la primera vez que se consulta un usuario tras un reinicio
se cargan sus últimos avisos desde ella. Así sobreviven a los reinicios y se ven iguales desde cualquier dispositivo. Si la base no
responde o no tiene la tabla, todo sigue funcionando solo en memoria, como antes. No es un registro de auditoría (la de las órdenes
está en data/ordenes.db). Los avisos de más de 90 días se borran solos, una vez al día.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from nucleo_agente import notificaciones_base as base

# Tope de notificaciones que se conservan por usuario; las más antiguas se descartan.
MAX_POR_USUARIO = 50

# Candado que protege _DATOS: lo escriben hilos en segundo plano y lo lee la interfaz.
_CANDADO = threading.Lock()
# Almacén en memoria: id de usuario -> lista de notificaciones (la más reciente primero).
_DATOS: dict[str, list[dict[str, Any]]] = {}
# Usuarios cuyos avisos ya se cargaron desde la base, instante del último intento de carga y segundos antes de reintentar si falló.
_CARGADOS: set[str] = set()
_INTENTO_CARGA: dict[str, float] = {}
REINTENTO_CARGA = 60.0
# Instante de la última limpieza de avisos antiguos y segundos entre limpiezas (una vez al día).
_ULTIMA_DEPURACION = 0.0
INTERVALO_DEPURACION = 86400.0
# Segundos que se recuerdan las preferencias de avisos de un usuario antes de volver a leerlas de su perfil.
VIGENCIA_PREFERENCIAS = 30.0
# Preferencias recordadas: id de usuario -> (instante de lectura, {categoría: True/False}).
_PREFERENCIAS: dict[str, tuple[float, dict[str, bool]]] = {}


# TITULO OLVIDAR PREFERENCIAS

def olvidar_preferencias(usuario_id: Any) -> None:
    """Descarta las preferencias recordadas del usuario; se llama al guardar su perfil para que el cambio rija de inmediato."""
    with _CANDADO:
        _PREFERENCIAS.pop(str(usuario_id), None)


# TITULO QUIERE AVISO

def _quiere_aviso(usuario_id: str, categoria: str | None) -> bool:
    """Dice si el usuario tiene activada la `categoria` en Perfil > Notificaciones (por defecto todas están activas).

    Sin categoría, o si el perfil no se puede leer, devuelve True: ante la duda se avisa. Las preferencias se recuerdan
    VIGENCIA_PREFERENCIAS segundos para no consultar la base de datos en cada aviso."""
    if not categoria:
        return True
    clave, ahora = str(usuario_id), time.time()
    with _CANDADO:
        recordada = _PREFERENCIAS.get(clave)
    if recordada is None or ahora - recordada[0] > VIGENCIA_PREFERENCIAS:
        try:
            from componentes_plataforma.perfil import almacen
            perfil = almacen.leer(usuario_id)
        except Exception:  # noqa: BLE001 - sin perfil legible se avisa igual
            return True
        if perfil.get("_error"):
            return True
        guardadas = perfil.get("notificaciones")
        recordada = (ahora, {k: bool(v) for k, v in guardadas.items()} if isinstance(guardadas, dict) else {})
        with _CANDADO:
            _PREFERENCIAS[clave] = recordada
    return recordada[1].get(categoria, True)


# TITULO ASEGURAR CARGADO

def _asegurar_cargado(usuario_id: str) -> None:
    """Carga desde la base los últimos avisos del usuario la primera vez que se le consulta tras un reinicio del servidor.

    Se mezclan con los que ya estén en memoria (sin repetir ids) y se respeta el tope MAX_POR_USUARIO. Si la base no responde se reintenta
    como mucho cada REINTENTO_CARGA segundos y mientras tanto la campana sigue con la memoria."""
    with _CANDADO:
        if usuario_id in _CARGADOS or time.time() - _INTENTO_CARGA.get(usuario_id, 0.0) < REINTENTO_CARGA:
            return
        _INTENTO_CARGA[usuario_id] = time.time()
    filas = base.leer(usuario_id, MAX_POR_USUARIO)
    if filas is None:
        return
    with _CANDADO:
        lista = _DATOS.setdefault(usuario_id, [])
        conocidos = {n["id"] for n in lista}
        lista.extend(f for f in filas if f["id"] not in conocidos)
        lista.sort(key=lambda n: n["creada"], reverse=True)
        del lista[MAX_POR_USUARIO:]
        _CARGADOS.add(usuario_id)


# TITULO DEPURAR SI TOCA

def _depurar_si_toca() -> None:
    """Pide borrar los avisos de más de 90 días si pasó un día desde la última limpieza de este proceso."""
    global _ULTIMA_DEPURACION
    with _CANDADO:
        if time.time() - _ULTIMA_DEPURACION < INTERVALO_DEPURACION:
            return
        _ULTIMA_DEPURACION = time.time()
    base.depurar()


# TITULO AGREGAR

def agregar(
    usuario_id: str,
    titulo: str,
    texto: str = "",
    tipo: str = "agente",        # agente | orden | auto | error | posicion | alerta
    ref: str | None = None,      # id del turno que la originó
    leida: bool = False,
    categoria: str | None = None,  # interruptor de Perfil > Notificaciones que la gobierna (None = siempre se avisa)
) -> dict[str, Any]:
    """Agrega una notificación al inicio de la lista del usuario y devuelve una copia de ella.

    Recibe el usuario, el título y texto a mostrar, el tipo, la referencia al turno que la originó, si nace ya leída y la
    categoría de preferencias (ordenes_agente, alertas_precio o posiciones). Si el usuario apagó esa categoría en su perfil
    la notificación no se guarda y se devuelve igual la copia, con id None. Si se supera MAX_POR_USUARIO descarta las más viejas.
    """
    usuario_id = str(usuario_id)
    if not _quiere_aviso(usuario_id, categoria):
        return {"id": None, "titulo": titulo, "texto": texto, "tipo": tipo, "ref": ref, "leida": leida, "creada": time.time()}
    _asegurar_cargado(usuario_id)
    # Se arma el registro con un id aleatorio y la hora de creación.
    nueva = {
        "id": uuid.uuid4().hex[:16], "titulo": titulo, "texto": texto, "tipo": tipo,
        "ref": ref, "leida": leida, "creada": time.time(),
    }
    # Inserción protegida por el candado: la lista queda ordenada de más reciente a más antigua.
    with _CANDADO:
        lista = _DATOS.setdefault(usuario_id, [])
        lista.insert(0, nueva)
        del lista[MAX_POR_USUARIO:]
    base.guardar(usuario_id, nueva)
    _depurar_si_toca()
    return dict(nueva)


# TITULO LISTAR

def listar(usuario_id: str, limite: int = 10) -> list[dict[str, Any]]:
    """Devuelve copias de las `limite` notificaciones más recientes del usuario."""
    usuario_id = str(usuario_id)
    _asegurar_cargado(usuario_id)
    with _CANDADO:
        return [dict(n) for n in _DATOS.get(usuario_id, [])[:limite]]


# TITULO HISTORIAL

def historial(usuario_id: str, limite: int = 100) -> list[dict[str, Any]]:
    """Los `limite` avisos más recientes del usuario leídos de la base, incluidos los que quitó de la campana.

    Si la base no responde o no tiene avisos del usuario (por ejemplo en desarrollo, sin id numérico) devuelve los que hay en memoria."""
    filas = base.leer(usuario_id, limite, incluir_ocultas=True)
    return filas if filas else listar(usuario_id, limite)


# TITULO NO LEIDAS

def no_leidas(usuario_id: str) -> int:
    """Cuenta las notificaciones sin leer del usuario (el número que muestra la campana)."""
    usuario_id = str(usuario_id)
    _asegurar_cargado(usuario_id)
    with _CANDADO:
        return sum(1 for n in _DATOS.get(usuario_id, []) if not n["leida"])


# TITULO ULTIMA ID

def ultima_id(usuario_id: str) -> str | None:
    """Id de la notificación más reciente (sirve para detectar que llegó una nueva)."""
    usuario_id = str(usuario_id)
    _asegurar_cargado(usuario_id)
    with _CANDADO:
        lista = _DATOS.get(usuario_id, [])
        return lista[0]["id"] if lista else None


# TITULO MARCAR LEIDAS

def marcar_leidas(usuario_id: str, ref: str | None = None) -> None:
    """Marca como leídas todas las del usuario, o solo las de un turno (`ref`)."""
    usuario_id = str(usuario_id)
    _asegurar_cargado(usuario_id)
    with _CANDADO:
        for n in _DATOS.get(usuario_id, []):
            if ref is None or n["ref"] == ref:
                n["leida"] = True
    base.marcar_leidas(usuario_id, ref)


# TITULO LIMPIAR

def limpiar(usuario_id: str) -> None:
    """Quita todas las notificaciones de la campana del usuario (siguen disponibles en su historial)."""
    usuario_id = str(usuario_id)
    _asegurar_cargado(usuario_id)
    with _CANDADO:
        _DATOS.pop(usuario_id, None)
    base.ocultar(usuario_id)


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
