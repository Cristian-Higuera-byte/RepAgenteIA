# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara tablero .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""API para el DASHBOARD: listar, rechazar y confirmar (ÚNICO punto que envía órdenes a MT5).

Lo usa el panel de órdenes (components/panel_ordenes.py) y el motor de vigilancia. Todas las
transiciones de estado se hacen con UPDATE condicionales para que cada propuesta se procese una sola vez."""
from datetime import datetime, timedelta
from typing import Any

from core.ordenes.base_datos import _ahora, _consultar, _ejecutar
from core.ordenes.envio import _enviar_apertura, _enviar_cierre


def expirar_vencidas() -> None:
    """Marca como vencidas las propuestas pendientes que ya pasaron su hora y recupera las atascadas.

    Efectos: dos UPDATE sobre SQLite. Las órdenes EJECUTANDO vencidas hace más de 60 s pasan a ERROR con un
    aviso; las PENDIENTE vencidas pasan a EXPIRADA."""
    # Una orden "EJECUTANDO" mucho después de su vencimiento quedó a medias (se cayó la app al enviarla).
    # No se asume que falló: se avisa para que el usuario lo compruebe en MT5.
    # Umbral: 60 s de gracia tras la expiración antes de dar por interrumpido un envío en curso.
    limite = (datetime.now() - timedelta(seconds=60)).isoformat(timespec="seconds")
    # Las órdenes que quedaron a medias pasan a ERROR (no se asume que fallaron).
    _ejecutar(
        "UPDATE ordenes SET estado = 'ERROR', detalle = ? WHERE estado = 'EJECUTANDO' AND expira <= ?",
        ("Envío interrumpido: revisa en MetaTrader 5 si la orden llegó a abrirse o cerrarse.", limite),
    )
    # Las propuestas pendientes cuya vigencia terminó pasan a EXPIRADA.
    _ejecutar("UPDATE ordenes SET estado = 'EXPIRADA' WHERE estado = 'PENDIENTE' AND expira <= ?", (_ahora(),))


def listar_pendientes() -> list[dict[str, Any]]:
    """Devuelve las propuestas PENDIENTE que debe confirmar el usuario, de la más antigua a la más reciente.

    Antes expira las vencidas. Excluye las de origen 'automatica' (las gestiona el motor de vigilancia)."""
    expirar_vencidas()
    return _consultar(
        "SELECT * FROM ordenes WHERE estado = 'PENDIENTE' AND COALESCE(origen, 'agente') != 'automatica' "
        "ORDER BY creada, rowid"
    )


def listar_historial(limite: int = 15) -> list[dict[str, Any]]:
    """Devuelve las últimas `limite` órdenes de cualquier estado, de la más reciente a la más antigua."""
    return _consultar("SELECT * FROM ordenes ORDER BY creada DESC, rowid DESC LIMIT ?", (int(limite),))


def rechazar_orden(id_orden: str) -> bool:
    """Marca como RECHAZADA_USUARIO una propuesta PENDIENTE. Devuelve True si cambió exactamente una fila."""
    return _ejecutar(
        "UPDATE ordenes SET estado = 'RECHAZADA_USUARIO' WHERE id = ? AND estado = 'PENDIENTE'", (id_orden,)
    ) == 1


def confirmar_orden(id_orden: str) -> dict[str, Any]:
    """ÚNICO punto que envía órdenes a MT5. Solo lo llama el botón Confirmar del dashboard (y el motor de
    vigilancia para las operaciones automáticas autorizadas).

    Reclama la propuesta de forma atómica (PENDIENTE a EJECUTANDO) para que un doble clic no duplique la orden,
    envía la apertura o el cierre y guarda el estado final. Devuelve un diccionario con `ok`, `mensaje` y,
    si hubo ejecución, `ticket`; si la orden no existe, venció o ya se procesó, devuelve `ok` False sin enviar nada."""
    # Paso 1: se "reclama" la propuesta de forma atómica: si ya se ejecutó, venció o fue rechazada, no se repite.
    reclamada = _ejecutar(
        "UPDATE ordenes SET estado = 'EJECUTANDO' WHERE id = ? AND estado = 'PENDIENTE' AND expira > ?",
        (id_orden, _ahora()),
    )
    if reclamada == 0:
        # No se pudo reclamar: se averigua por qué para dar un mensaje preciso.
        filas = _consultar("SELECT estado FROM ordenes WHERE id = ?", (id_orden,))
        if not filas:
            return {"ok": False, "mensaje": "La orden no existe."}
        if filas[0]["estado"] == "PENDIENTE":
            # Seguía PENDIENTE pero vencida: se marca EXPIRADA.
            _ejecutar("UPDATE ordenes SET estado = 'EXPIRADA' WHERE id = ? AND estado = 'PENDIENTE'", (id_orden,))
            return {"ok": False, "mensaje": "La propuesta venció. Pídele al agente que la genere de nuevo."}
        return {"ok": False, "mensaje": f"La orden ya está en estado {filas[0]['estado']}; no se vuelve a ejecutar."}

    # Paso 2: se envía a MT5 según la acción guardada (abrir o cerrar).
    o = _consultar("SELECT * FROM ordenes WHERE id = ?", (id_orden,))[0]
    try:
        res = _enviar_apertura(o) if o["accion"] == "abrir" else _enviar_cierre(o)
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "estado": "ERROR", "mensaje": f"Error inesperado (revisa MT5 por si la orden se envió): {e}"}

    # Paso 3: se registra el resultado final (EJECUTADA u otro estado de fallo) y el ticket devuelto.
    _ejecutar(
        "UPDATE ordenes SET estado = ?, detalle = ?, ticket_resultado = ? WHERE id = ?",
        ("EJECUTADA" if res["ok"] else res.get("estado", "ERROR"), res["mensaje"], res.get("ticket"), id_orden),
    )
    return res


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara tablero .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
