# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara validacion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Validación de turnos: jamás se guarda ni se carga un turno por la mitad (un 'tool' sin su 'tool_calls' da 400).

La usan guardar_turno (antes de insertar) y cargar_historial (al recuperar mensajes de Supabase).
"""
from typing import Any


# TITULO TURNO VALIDO

def _turno_valido(turno: list[dict[str, Any]]) -> bool:
    """Válido si cada 'tool' responde a un tool_call del asistente anterior
    y no queda ninguna llamada sin resultado."""
    # Ids de tool_calls del asistente que aún no tienen su mensaje "tool" de respuesta.
    pendientes: set[str] = set()
    for m in turno:
        rol = m.get("role")
        if rol == "tool":
            if m.get("tool_call_id") not in pendientes:
                return False
            pendientes.discard(m["tool_call_id"])
        else:
            if pendientes:
                return False
            if rol == "assistant":
                pendientes = {c["id"] for c in (m.get("tool_calls") or [])}
    return not pendientes


# TITULO SANEAR

def _sanear(historial: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Conserva solo turnos completos y consistentes (cada turno empieza en un 'user')."""
    # Se parte el historial en turnos, cada uno iniciado por un mensaje "user".
    turnos: list[list[dict[str, Any]]] = []
    actual: list[dict[str, Any]] = []
    for mensaje in historial:
        if mensaje.get("role") == "user":
            if actual:
                turnos.append(actual)
            actual = [mensaje]
        elif actual:
            actual.append(mensaje)  # lo anterior al primer 'user' (turno cortado) se descarta
    if actual:
        turnos.append(actual)
    # Solo se conservan los turnos válidos, aplanados de nuevo en una lista de mensajes.
    return [m for t in turnos if _turno_valido(t) for m in t]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara validacion .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
