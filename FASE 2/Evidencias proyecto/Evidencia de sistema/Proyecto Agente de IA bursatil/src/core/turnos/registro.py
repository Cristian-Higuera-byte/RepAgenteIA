# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara registro .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Registro de turnos y agentes por usuario (un turno a la vez por usuario) y API que usa la interfaz."""
from __future__ import annotations

import threading
from typing import Any

from core import notificaciones
from core.turnos.hilo import _correr
from core.turnos.turno import Turno

# Candado que protege _TURNOS y _AGENTES (los usan la interfaz y los hilos de turno).
_LOCK = threading.Lock()
_TURNOS: dict[str, Turno] = {}    # último turno de cada usuario
_AGENTES: dict[str, Any] = {}     # un Agente por usuario (sobrevive a recargas de la página)


# ── API ───────────────────────────────────────────────────────────────────────────────
def agente_de(usuario_id: str) -> Any:
    """Devuelve el Agente registrado para el usuario, o None si aún no tiene."""
    with _LOCK:
        return _AGENTES.get(usuario_id)


def registrar_agente(usuario_id: str, agente: Any) -> None:
    """Guarda (o reemplaza) el Agente del usuario para reutilizarlo entre recargas de la página."""
    with _LOCK:
        _AGENTES[usuario_id] = agente


def turno_de(usuario_id: str) -> Turno | None:
    """Devuelve el último turno del usuario (en curso o terminado), o None si no tiene."""
    with _LOCK:
        return _TURNOS.get(usuario_id)


def hay_turno_en_curso(usuario_id: str) -> bool:
    """Indica si el usuario tiene un turno que aún no ha terminado."""
    t = turno_de(usuario_id)
    return t is not None and not t.terminado


def iniciar(usuario_id: str, agente: Any, prompt: str) -> Turno | None:
    """Lanza el turno en segundo plano. Devuelve None si ya hay uno en curso para ese usuario."""
    with _LOCK:
        actual = _TURNOS.get(usuario_id)
        if actual is not None and not actual.terminado:
            return None
        # Se crea el turno y se registra dentro del candado para que dos clics no lancen dos hilos.
        turno = Turno(usuario_id=usuario_id, prompt=prompt)
        _TURNOS[usuario_id] = turno
    # Hilo daemon: no impide cerrar el proceso y sobrevive a las re-ejecuciones del script de Streamlit.
    threading.Thread(target=_correr, args=(turno, agente), name=f"turno-{turno.id}", daemon=True).start()
    return turno


def cancelar(usuario_id: str) -> bool:
    """Pide detener el turno en curso del usuario. True si había uno al que pedírselo."""
    with _LOCK:
        t = _TURNOS.get(usuario_id)
        if t is None or t.terminado:
            return False
        t.cancelar_solicitado = True
        t.fase = "Deteniendo…"
        return True


def recoger(usuario_id: str, turno_id: str) -> None:
    """La interfaz ya mostró el resultado: se marca como incorporado y se leen sus avisos."""
    with _LOCK:
        t = _TURNOS.get(usuario_id)
        if t is not None and t.id == turno_id:
            t.recogido = True
    notificaciones.marcar_leidas(usuario_id, ref=turno_id)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara registro .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
