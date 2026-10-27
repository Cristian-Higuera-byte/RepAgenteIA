# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara candado .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Candado de MT5: se comparte el del bridge del dashboard si existe; si no, uno propio (se decide UNA vez al importar).

La API de MetaTrader5 no es segura entre hilos, por lo que toda consulta debe
hacerse con un candado tomado. Para que el dashboard y el agente no choquen
dentro del mismo proceso, se reutiliza el `MT5_LOCK` del puente del dashboard
(`herramientas.puente_mt5`, o el módulo indicado en la variable de entorno
MT5_BRIDGE_MODULO); si ese módulo no se puede importar, se usa un RLock propio."""
from __future__ import annotations

import importlib
import os
from typing import Any

import threading

# Candado propio de respaldo; es reentrante (RLock) para que una misma consulta pueda anidar sesiones.
_LOCK_PROPIO = threading.RLock()


def _resolver_lock_compartido() -> Any:
    """Intenta obtener el `MT5_LOCK` del puente MT5 del dashboard.

    Lee el nombre del módulo de la variable de entorno MT5_BRIDGE_MODULO (por
    defecto `herramientas.puente_mt5`), lo importa y devuelve su atributo
    `MT5_LOCK`. Devuelve None si el módulo no existe, falla al importarse o no
    tiene ese atributo. Efecto secundario: importa el módulo indicado."""
    ruta = os.getenv("MT5_BRIDGE_MODULO", "herramientas.puente_mt5").strip() or "herramientas.puente_mt5"
    try:
        return importlib.import_module(ruta).MT5_LOCK
    except Exception:
        return None


# Candado del puente del dashboard (o None). Se resuelve UNA sola vez al importar
# para que el candado en uso nunca cambie a mitad de camino.
_LOCK_COMPARTIDO: Any = _resolver_lock_compartido()


def _candado() -> Any:
    """Devuelve el candado que debe usarse para hablar con MT5.

    Prefiere el candado compartido con el dashboard y, si no existe, el propio.
    El resultado es siempre el mismo durante la vida del proceso."""
    return _LOCK_COMPARTIDO if _LOCK_COMPARTIDO is not None else _LOCK_PROPIO


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara candado .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
