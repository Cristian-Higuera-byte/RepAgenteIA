# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara posiciones .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Posiciones de una vigilancia (solo las que ella abrió, reconocidas por el comentario de la orden)."""
from __future__ import annotations

from typing import Any

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from core import ordenes
from core.vigilancia.utilidades import _consultar


def _posiciones_de(v: dict[str, Any]) -> list[Any]:
    """Devuelve las posiciones abiertas en MT5 que pertenecen a la vigilancia `v`.

    Busca los ids de las órdenes de apertura EJECUTADAS de esa vigilancia y filtra las posiciones del símbolo
    cuyo comentario (agente-ia:ID) termina en uno de esos ids. Así nunca toca posiciones manuales ni de otras
    vigilancias. Efecto: lectura de SQLite y de MT5 bajo MT5_LOCK."""
    ids = {f["id"] for f in _consultar(
        "SELECT id FROM ordenes WHERE vigilancia_id = ? AND accion = 'abrir' AND estado = 'EJECUTADA'", (v["id"],))}
    if not ids:
        return []
    # El id de la orden va tras los dos puntos del comentario ("agente-ia:<id>").
    with ordenes.MT5_LOCK:
        abiertas = mt5.positions_get(symbol=v["simbolo"]) or []
    return [p for p in abiertas if (getattr(p, "comment", "") or "").rpartition(":")[2] in ids]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara posiciones .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
