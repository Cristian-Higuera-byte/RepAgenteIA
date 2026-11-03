# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara auxiliares .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Funciones auxiliares de las herramientas de órdenes (sin registrar nada)."""
from __future__ import annotations

from typing import Any


# TITULO A NUMERO

def _a_numero(valor: Any) -> Any:
    """Los LLM a veces envían números como texto; se convierten si es posible.

    Si ``valor`` es texto, intenta convertirlo a ``float`` aceptando la coma como
    separador decimal; si no se puede, devuelve el texto original. Cualquier otro
    tipo (número, None, bool) se devuelve sin cambios.
    """
    if isinstance(valor, str):
        try:
            return float(valor.replace(",", "."))
        except ValueError:
            return valor
    return valor


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara auxiliares .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
