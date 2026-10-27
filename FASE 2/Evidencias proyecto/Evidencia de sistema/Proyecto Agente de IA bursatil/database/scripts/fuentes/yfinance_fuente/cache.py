# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara cache .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Caché en memoria con vencimiento para no saturar las peticiones a Yahoo.

Guarda en un diccionario del proceso el resultado de cada consulta junto con el
instante en que se obtuvo, y lo reutiliza mientras no haya pasado el tiempo de
vida (TTL) indicado por quien llama."""
from __future__ import annotations

import time
from typing import Any, Callable

# ──────────────────────────────────────────────────────────────
# Utilidades internas
# ──────────────────────────────────────────────────────────────
# Almacén de la caché: clave de consulta -> (instante monotónico de guardado, valor).
# Vive solo en memoria del proceso; se pierde al reiniciar y no se comparte entre procesos.
_CACHE: dict[str, tuple[float, Any]] = {}


def _cacheado(clave: str, ttl: float, fn: Callable[[], Any]) -> Any:
    """Cache en memoria con vencimiento: evita golpear a Yahoo con consultas repetidas.

    Recibe la clave que identifica la consulta, el tiempo de vida en segundos
    (`ttl`) y la función sin argumentos `fn` que produce el valor cuando no hay
    un resultado vigente. Devuelve el valor cacheado si aún no venció o, si no,
    ejecuta `fn`, guarda el resultado en `_CACHE` y lo devuelve. Si `fn` lanza
    una excepción, esta se propaga y no se guarda nada."""
    # Reloj monotónico: no le afectan los cambios de hora del sistema.
    ahora = time.monotonic()
    guardado = _CACHE.get(clave)
    # Si hay un valor guardado y todavía es reciente, se devuelve sin hacer red.
    if guardado and ahora - guardado[0] < ttl:
        return guardado[1]
    valor = fn()  # si lanza excepción, no se cachea
    _CACHE[clave] = (ahora, valor)
    return valor


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara cache .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
