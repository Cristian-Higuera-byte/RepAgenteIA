# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara caducidad .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Caducidad: autorizaciones que vencieron y vigilancias cuyo tiempo terminó."""
from __future__ import annotations

from nucleo_agente import ordenes
from nucleo_agente.vigilancia.configuracion import EXPIRADA
from nucleo_agente.vigilancia.posiciones import _posiciones_de
from nucleo_agente.vigilancia.utilidades import _consultar, _finalizar


# TITULO CADUCAR AUTORIZACIONES

def _caducar_autorizaciones() -> None:
    """Pasa a EXPIRADA las vigilancias que siguen PENDIENTE_AUTORIZACION después de su plazo de autorización."""
    ordenes._ejecutar(
        "UPDATE vigilancias SET estado = 'EXPIRADA', detalle = 'La autorización venció' "
        "WHERE estado = 'PENDIENTE_AUTORIZACION' AND expira_autorizacion <= ?", (ordenes._ahora(),),
    )


# TITULO CADUCAR VENCIDAS

def _caducar_vencidas() -> None:
    """Finaliza como EXPIRADA las vigilancias ACTIVA cuyo tiempo total (`vence`) ya pasó y avisa al usuario.

    Si queda una posición abierta lo indica: no se cierra sola, conserva su SL y TP."""
    for v in _consultar("SELECT * FROM vigilancias WHERE estado = 'ACTIVA' AND vence <= ?", (ordenes._ahora(),)):
        extra = " Queda una posición abierta (con su stop loss y take profit)." if _posiciones_de(v) else ""
        _finalizar(v, EXPIRADA, f"Vigilancia terminada · {v['simbolo']}",
                   f"Se cumplió el tiempo de la vigilancia ({v['duracion_horas']:g} h).{extra}")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara caducidad .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
