# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara solo_lectura .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Envoltorio del módulo MetaTrader5 que solo deja pasar consultas (el agente es de SOLO LECTURA).

Es la barrera de seguridad del paquete: aunque el código del agente intente
enviar órdenes, el envoltorio lo bloquea porque solo reenvía las funciones de
la lista blanca `_FUNCIONES_PERMITIDAS` y las constantes en mayúsculas."""
from __future__ import annotations

from typing import Any

from fuentes.mt5_fuentes.constantes import _FUNCIONES_PERMITIDAS
from fuentes.mt5_fuentes.errores import OperacionNoPermitida


# TITULO SOLO LECTURA

class _SoloLectura:
    """Envuelve el módulo MetaTrader5 y solo deja pasar consultas.

    Cualquier atributo que no sea una función permitida o una constante
    (nombre en mayúsculas) lanza OperacionNoPermitida; además, no admite
    asignar atributos."""

    # TITULO INIT

    def __init__(self, modulo: Any) -> None:
        """Guarda el módulo real de MetaTrader5 dentro del envoltorio.

        Usa `object.__setattr__` para saltarse el bloqueo de `__setattr__`, que
        impediría asignar incluso este atributo interno."""
        object.__setattr__(self, "_modulo", modulo)

    # TITULO GETATTR

    def __getattr__(self, nombre: str) -> Any:
        """Reenvía al módulo real solo lo permitido: funciones de la lista blanca y constantes.

        Los nombres dunder (`__x__`) lanzan AttributeError normal para no romper
        protocolos de Python (copy, pickle...). Lo demás (order_send, login,
        shutdown, etc.) lanza OperacionNoPermitida. Python llama a este método
        solo cuando el atributo no existe en el objeto."""
        if nombre.startswith("__"):
            raise AttributeError(nombre)
        # Las constantes de MT5 (TIMEFRAME_H1, ORDER_TYPE_BUY...) están en mayúsculas.
        if nombre in _FUNCIONES_PERMITIDAS or nombre.isupper():
            return getattr(self._modulo, nombre)
        raise OperacionNoPermitida(f"Operación no permitida: '{nombre}'. El agente es de solo lectura.")

    # TITULO SETATTR

    def __setattr__(self, nombre: str, valor: Any) -> None:
        """Bloquea toda asignación de atributos sobre el módulo MT5; siempre lanza OperacionNoPermitida."""
        raise OperacionNoPermitida("El módulo MT5 es de solo lectura.")


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara solo_lectura .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
