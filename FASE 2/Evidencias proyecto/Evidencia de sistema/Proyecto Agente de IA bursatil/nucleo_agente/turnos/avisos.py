# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara avisos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Aviso en la campana de notificaciones cuando termina un turno (lo llama el hilo en turnos/hilo.py)."""
from __future__ import annotations

import time

from nucleo_agente import notificaciones
from nucleo_agente.turnos.formato import formatear_duracion
from nucleo_agente.turnos.turno import VISTA_RECIENTE_S, Turno


# TITULO AVISAR

def _avisar(turno: Turno) -> None:
    """Deja el aviso en la campana. Si el usuario está viendo el chat, nace ya leído."""
    # Si la interfaz mostró el turno hace poco, el usuario lo está viendo y no hace falta marcarlo sin leer.
    viendo = (time.time() - turno.ui_viva) < VISTA_RECIENTE_S
    # Se acorta la pregunta a 80 caracteres para el texto de la notificación.
    pregunta = turno.prompt if len(turno.prompt) <= 80 else turno.prompt[:77] + "…"
    tiempo = formatear_duracion(turno.duracion)
    # Título y tipo según cómo terminó el turno: error, vigilancia, orden propuesta o respuesta normal.
    if turno.error:
        titulo, tipo = "El agente no pudo responder", "error"
    elif turno.hubo_vigilancia:
        titulo, tipo = "El agente preparó una vigilancia automática", "orden"
        pregunta = "Revísala y autorízala en «Órdenes propuestas»"
    elif turno.hubo_orden:
        titulo, tipo = "El agente propuso una orden", "orden"
    else:
        titulo, tipo = "El agente respondió", "agente"
    # Se registra la notificación vinculada al turno (ref) para poder marcarla leída al recogerlo.
    notificaciones.agregar(
        turno.usuario_id, titulo, f"{pregunta} · {tiempo}", tipo=tipo, ref=turno.id, leida=viendo,
    )


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara avisos .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
