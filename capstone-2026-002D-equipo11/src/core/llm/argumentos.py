# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara argumentos .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Argumentos de las llamadas a herramientas (JSON del modelo)."""
from __future__ import annotations

import json
from typing import Any


def _parsear_argumentos(raw: str) -> tuple[dict[str, Any], str | None]:
    """Convierte el texto JSON de argumentos de una herramienta en un diccionario.

    Recibe `raw`, la cadena que envió el modelo. Devuelve (argumentos, error): con cadena vacía devuelve
    ({}, None); si el JSON es inválido o no es un objeto devuelve ({}, mensaje). El error se le devuelve
    al modelo como resultado de la herramienta para que corrija su llamada.
    """
    if not raw:
        return {}, None
    try:
        datos = json.loads(raw)
        if not isinstance(datos, dict):
            return {}, f"Los argumentos deben ser un objeto JSON, llegó: {raw!r}"
        return datos, None
    except json.JSONDecodeError:
        return {}, f"Argumentos con JSON inválido: {raw!r}"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara argumentos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
