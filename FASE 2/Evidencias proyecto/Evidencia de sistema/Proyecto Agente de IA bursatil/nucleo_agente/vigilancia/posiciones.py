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

"""Posiciones de una vigilancia (solo las que ella abrió, reconocidas por el comentario de la orden o por el ticket que devolvió el envío)."""
from __future__ import annotations

from typing import Any

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from nucleo_agente import ordenes
from nucleo_agente.vigilancia.utilidades import _consultar


# TITULO POSICIONES DE

def _posiciones_de(v: dict[str, Any]) -> list[Any]:
    """Devuelve las posiciones abiertas del bróker que pertenecen a la vigilancia `v`.

    Busca las órdenes de apertura EJECUTADAS de esa vigilancia y filtra las posiciones del símbolo que sean suyas: con
    MetaTrader 5, por el comentario (agente-ia:ID) que termina en el id de la orden; con Capital.com, que no guarda comentarios,
    por el ticket (dealId) que devolvió el envío y quedó en `ticket_resultado`. Así nunca toca posiciones manuales ni de otras
    vigilancias. Efecto: lectura de SQLite y del bróker bajo MT5_LOCK."""
    filas = _consultar(
        "SELECT id, ticket_resultado FROM ordenes WHERE vigilancia_id = ? AND accion = 'abrir' AND estado = 'EJECUTADA'",
        (v["id"],))
    ids = {f["id"] for f in filas}
    tickets = {str(f["ticket_resultado"]) for f in filas if f["ticket_resultado"] not in (None, "")}
    if not ids:
        return []
    # El id de la orden va tras los dos puntos del comentario ("agente-ia:<id>").
    with ordenes.MT5_LOCK:
        abiertas = mt5.positions_get(symbol=v["simbolo"]) or []
    return [p for p in abiertas
            if (getattr(p, "comment", "") or "").rpartition(":")[2] in ids or str(p.ticket) in tickets]


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
