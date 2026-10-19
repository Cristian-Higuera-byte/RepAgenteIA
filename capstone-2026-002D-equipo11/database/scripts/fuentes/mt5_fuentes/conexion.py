# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara conexion .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Conexión con el terminal de MT5: reintentos con espera, sesión con candado y envoltorio de solo lectura.
El estado de la conexión (último fallo, error, ruta) vive aquí, junto a las funciones que lo modifican.

Flujo: `_sesion()` toma el candado y llama a `asegurar_conexion()`, que importa
MetaTrader5 (`_modulo`), comprueba si el terminal ya responde y, si no,
intenta `initialize` con cada ruta candidata (`_conectar`). Si todas fallan, se
registra el fallo (`_fallar`) y durante `_REINTENTO_S` segundos las llamadas
siguientes fallan al instante en lugar de volver a bloquearse."""
from __future__ import annotations

import importlib
import os
import time
from contextlib import contextmanager
from typing import Any, Iterator, NoReturn

from dotenv import load_dotenv

from database.scripts.fuentes.mt5_fuentes.candado import _candado
from database.scripts.fuentes.mt5_fuentes.constantes import _MAX_RUTAS, _REINTENTO_S, _TIMEOUT_MS
from database.scripts.fuentes.mt5_fuentes.errores import ErrorMT5
from database.scripts.fuentes.mt5_fuentes.rutas import rutas_candidatas
from database.scripts.fuentes.mt5_fuentes.solo_lectura import _SoloLectura

# Cargar el .env ANTES de leer PROVEEDOR, para que la decisión no dependa del
# orden de import (si no, podría caer a 'mt5' y abrir el terminal por error).
load_dotenv()
# Proveedor de bajo nivel: con PROVEEDOR=capital se usa el shim de Capital.com
# (mismo que el resto de la app), no el terminal MetaTrader 5.
_ES_CAPITAL = os.getenv("PROVEEDOR", "mt5").strip().lower() == "capital"

# Módulo MetaTrader5 real, importado de forma perezosa por `_modulo()` (None hasta entonces).
_raw: Any = None
# Envoltorio de solo lectura sobre `_raw`; es lo único que se entrega a las consultas.
_proxy: _SoloLectura | None = None
# Instante (time.time) del último intento de conexión fallido; base de la espera entre reintentos.
_ultimo_fallo = 0.0
# Mensaje del último fallo de conexión; vacío significa "sin fallo pendiente".
_ultimo_error = ""
# Ruta del terminal64.exe con el que se conectó con éxito (informativa).
_ruta_conectada: str | None = None


def _modulo() -> Any:
    """Importa (una sola vez) la librería MetaTrader5 y crea su envoltorio de solo lectura.

    Devuelve el módulo crudo. Efectos secundarios: rellena las globales `_raw` y
    `_proxy`. Lanza ErrorMT5 si la librería no está instalada."""
    global _raw, _proxy
    if _raw is None:
        if _ES_CAPITAL:
            from proveedores import capital_mt5_compat as _mod
            _raw = _mod
        else:
            try:
                _raw = importlib.import_module("MetaTrader5")
            except ImportError as e:
                raise ErrorMT5("Falta la librería MetaTrader5: pip install -U MetaTrader5") from e
        _proxy = _SoloLectura(_raw)
    return _raw


def _fallar(mensaje: str) -> NoReturn:
    """Registra un fallo de conexión y lanza ErrorMT5 con ese mensaje.

    Guarda el instante y el texto en `_ultimo_fallo` y `_ultimo_error` para que
    `_espera_restante` bloquee nuevos intentos durante `_REINTENTO_S` segundos."""
    global _ultimo_fallo, _ultimo_error
    _ultimo_fallo = time.time()
    _ultimo_error = mensaje
    raise ErrorMT5(mensaje)


def _espera_restante() -> float:
    """Devuelve los segundos que faltan antes de poder reintentar la conexión.

    Es 0.0 si no hay un fallo registrado o si ya transcurrió `_REINTENTO_S`."""
    if not _ultimo_error:
        return 0.0
    return max(0.0, _REINTENTO_S - (time.time() - _ultimo_fallo))


def _conectar(raw: Any) -> None:
    """Inicializa el terminal de MT5 probando las rutas candidatas en orden.

    Recibe el módulo crudo de MetaTrader5. Nunca llama a `initialize()` sin ruta
    (puede colgarse hasta 60 s). Prueba como máximo `_MAX_RUTAS` rutas, con
    `_TIMEOUT_MS` de espera cada una. Si alguna conecta, guarda la ruta en
    `_ruta_conectada` y limpia `_ultimo_error`; si ninguna conecta (o no hay
    rutas) llama a `_fallar`, que lanza ErrorMT5 con el detalle de cada intento."""
    global _ruta_conectada, _ultimo_error
    # Salvaguarda: bajo Capital NUNCA se abre el terminal MetaTrader 5.
    if _ES_CAPITAL:
        _fallar("PROVEEDOR=capital: no se abre el terminal MT5 (se usa la API REST).")
    # Rutas ordenadas por prioridad: MT5_PATH, terminal abierto, carpetas típicas.
    rutas = rutas_candidatas()
    if not rutas:
        _fallar("No se encontró ningún terminal64.exe de MT5.")

    errores: list[str] = []
    # Prueba una ruta tras otra hasta que alguna inicialice correctamente.
    for ruta in rutas[:_MAX_RUTAS]:
        if raw.initialize(path=ruta, timeout=_TIMEOUT_MS):
            _ruta_conectada = ruta
            break
        errores.append(f"{ruta} → {raw.last_error()}")
    else:
        # El for terminó sin break: ninguna ruta funcionó.
        _fallar("No se pudo conectar con MT5: " + " | ".join(errores))

    # Conexión lograda: se borra el error previo para permitir consultas normales.
    _ultimo_error = ""


def asegurar_conexion() -> _SoloLectura:
    """Garantiza que el terminal de MT5 esté conectado y devuelve el módulo de solo lectura.

    Si `terminal_info()` ya responde, reutiliza la sesión. Si no, respeta la
    espera entre reintentos (lanza ErrorMT5 con el error previo y los segundos
    restantes) o intenta conectar con `_conectar`. Debe llamarse con el candado
    tomado (ver `_sesion`). Lanza ErrorMT5 si el módulo no quedó inicializado."""
    raw = _modulo()
    # terminal_info() devuelve None cuando no hay conexión activa con el terminal.
    if raw.terminal_info() is None:
        if _ES_CAPITAL:
            # El shim no usa rutas de terminal: abre/renueva la sesión REST.
            if not raw.initialize():
                _fallar("No se pudo conectar con Capital.com (revisa las credenciales del .env).")
        else:
            espera = _espera_restante()
            if espera > 0:
                # Fallo reciente: se responde al instante en vez de bloquear otra vez.
                raise ErrorMT5(f"{_ultimo_error} (reintento en {espera:.0f} s)")
            _conectar(raw)
    if _proxy is None:
        raise ErrorMT5("Módulo MT5 no inicializado.")
    return _proxy


@contextmanager
def _sesion() -> Iterator[_SoloLectura]:
    """Administrador de contexto que da acceso exclusivo y de solo lectura a MT5.

    Toma el candado compartido, asegura la conexión y entrega el envoltorio
    `_SoloLectura`; al salir siempre libera el candado. Si hay una espera de
    reintento activa y el candado está ocupado, falla de inmediato en lugar de
    bloquearse. Es el único punto de entrada de las consultas de cuenta y mercado."""
    lock = _candado()
    if _espera_restante() > 0:
        # En período de espera: no se bloquea esperando el candado, se falla rápido.
        if not lock.acquire(blocking=False):
            raise ErrorMT5(f"{_ultimo_error} (reintento en {_espera_restante():.0f} s)")
    else:
        lock.acquire()
    try:
        yield asegurar_conexion()
    finally:
        lock.release()


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara conexion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
