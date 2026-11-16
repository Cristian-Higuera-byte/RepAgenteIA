# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara motor .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Motor en segundo plano: despierta cada pocos segundos y lanza los chequeos que ya tocan.

Cada chequeo corre en su propio hilo demonio (uno por vigilancia) para que un análisis lento del modelo no
retrase a las demás. Con el modo multiusuario cada chequeo opera con la cuenta DEMO de SU dueño (el agente solo opera
en demo): la vigilancia guarda el usuario que la creó."""
from __future__ import annotations

import threading
import time
import traceback

from herramientas.backends import sesiones_capital
from nucleo_agente import ordenes
from nucleo_agente.vigilancia.caducidad import _caducar_autorizaciones, _caducar_vencidas
from nucleo_agente.vigilancia.chequeo import chequear
from nucleo_agente.vigilancia.configuracion import ESPERA_MOTOR_S, NOMBRE_HILO_MOTOR, PREFIJO_HILO_CHEQUEO
from nucleo_agente.vigilancia.utilidades import _consultar


# TITULO CHEQUEO EN CURSO

def _chequeo_en_curso(vid: str) -> bool:
    """Indica si ya hay un hilo de chequeo vivo para esa vigilancia (evita lanzar dos a la vez)."""
    nombre = f"{PREFIJO_HILO_CHEQUEO}{vid}"
    return any(t.name == nombre and t.is_alive() for t in threading.enumerate())


# TITULO CHEQUEAR SEGURO

def _chequear_seguro(vid: str) -> None:
    """Ejecuta chequear(vid) capturando cualquier excepción (se imprime) para que nunca tumbe el hilo."""
    try:
        chequear(vid)
    except Exception:  # noqa: BLE001
        traceback.print_exc()


# TITULO CHEQUEAR COMO DUEÑO

def _chequear_como_dueno(vid: str, usuario_id) -> None:
    """Ejecuta el chequeo de la vigilancia con la sesión de Capital.com (demo) de su dueño; sin dueño válido no opera."""
    try:
        clave = (int(usuario_id), True)
    except (TypeError, ValueError):
        clave = ("anonimo",)
    with sesiones_capital.con_clave(clave):
        _chequear_seguro(vid)


# TITULO TICK

def tick(sincrono: bool = False) -> int:
    """Una pasada del motor: caduca lo vencido y lanza los chequeos que ya tocan. Devuelve cuántos lanzó."""
    # Primero se caduca lo vencido; luego se buscan las vigilancias ACTIVA a las que ya les toca chequeo.
    _caducar_autorizaciones()
    _caducar_vencidas()
    toca = _consultar(
        "SELECT id, usuario_id FROM vigilancias WHERE estado = 'ACTIVA' AND (proximo_chequeo IS NULL OR proximo_chequeo <= ?)",
        (ordenes._ahora(),),
    )
    # Cada chequeo va en un hilo aparte (o en línea si `sincrono`, útil en pruebas); se omiten los que siguen en curso.
    lanzados = 0
    for fila in toca:
        vid = fila["id"]
        if _chequeo_en_curso(vid):
            continue
        if sincrono:
            _chequear_como_dueno(vid, fila["usuario_id"])
        else:
            threading.Thread(target=_chequear_como_dueno, args=(vid, fila["usuario_id"]),
                             name=f"{PREFIJO_HILO_CHEQUEO}{vid}", daemon=True).start()
        lanzados += 1
    return lanzados


# TITULO BUCLE

def _bucle() -> None:
    """Bucle infinito del hilo del motor: ejecuta tick() y duerme ESPERA_MOTOR_S segundos; los errores se imprimen."""
    while True:
        try:
            tick()
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        time.sleep(ESPERA_MOTOR_S)


# Evita que dos llamadas simultáneas a iniciar_motor creen dos motores.
_CANDADO_MOTOR = threading.Lock()


# TITULO INICIAR MOTOR

def iniciar_motor() -> bool:
    """Arranca el motor si no está ya en marcha (idempotente, también si Streamlit recarga el módulo).
    Devuelve True si lo arrancó ahora."""
    with _CANDADO_MOTOR:
        if any(t.name == NOMBRE_HILO_MOTOR and t.is_alive() for t in threading.enumerate()):
            return False
        threading.Thread(target=_bucle, name=NOMBRE_HILO_MOTOR, daemon=True).start()
        return True


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara motor .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
