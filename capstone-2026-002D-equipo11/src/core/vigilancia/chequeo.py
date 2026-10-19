# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara chequeo .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Chequeo de una vigilancia: analiza el activo y, si el modelo lo decide, ejecuta. Lo lanza el motor."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from core import ordenes
from core.vigilancia import analisis
from core.vigilancia.analisis import _mensaje_analisis
from core.vigilancia.configuracion import ACTIVA, ERROR, ERRORES_SEGUIDOS_MAX, FINALIZADA
from core.vigilancia.decision import parsear_decision
from core.vigilancia.ejecucion import _aplicar
from core.vigilancia.posiciones import _posiciones_de
from core.vigilancia.utilidades import _actualizar, _finalizar, _iso, obtener


def chequear(vid: str) -> dict[str, Any]:
    """Un chequeo: analiza el activo y, si el modelo lo decide, ejecuta. Lo lanza el motor.

    Recibe el id de la vigilancia. Secuencia: reprograma el próximo chequeo, exige cuenta demo, finaliza si se
    agotaron las operaciones, respeta el interruptor de emergencia, omite el análisis si el mercado no se movió
    (ahorra tokens), pide el análisis al agente, descarta la decisión si el usuario detuvo la vigilancia mientras
    tanto, y aplica la decisión. Devuelve un diccionario con `ok` y el estado, la decisión o el motivo.
    Efectos: escritura en SQLite, lectura de MT5, llamada al modelo y posibles órdenes."""
    # Paso 1: la vigilancia debe seguir activa.
    v = obtener(vid)
    if not v or v["estado"] != ACTIVA:
        return {"ok": False, "motivo": "La vigilancia no está activa."}
    # Paso 2: se registra el chequeo y se programa el siguiente antes de analizar (así un fallo no lo repite sin pausa).
    ahora = datetime.now()
    _actualizar(vid, ultimo_chequeo=_iso(ahora), chequeos=(v.get("chequeos") or 0) + 1,
                proximo_chequeo=_iso(ahora + timedelta(minutes=int(v["intervalo_min"]))))
    v = obtener(vid) or v

    # Paso 3: solo cuenta demo; si MT5 no responde se reintenta luego.
    cuenta, motivo = ordenes.cuenta_demo()
    if motivo and cuenta is not None:      # MT5 responde pero la cuenta NO es demo: se detiene todo
        _finalizar(v, ERROR, f"Vigilancia detenida · {v['simbolo']}", motivo, tipo="error")
        return {"ok": False, "motivo": motivo}
    if motivo:                              # MT5 sin conexión: se reintenta en el próximo chequeo
        _actualizar(vid, ultimo_resumen=f"Sin conexión con MetaTrader 5; se reintenta. ({motivo})"[:300])
        return {"ok": False, "motivo": motivo}

    # Paso 4: fin natural (operaciones agotadas y sin posición) o pausa por el interruptor de emergencia.
    posiciones = _posiciones_de(v)
    if (v.get("operaciones") or 0) >= v["max_operaciones"] and not posiciones:
        _finalizar(v, FINALIZADA, f"Vigilancia finalizada · {v['simbolo']}",
                   f"Se realizaron las {v['max_operaciones']} operaciones previstas y no queda ninguna posición abierta.")
        return {"ok": True, "estado": FINALIZADA}
    if ordenes.kill_switch_activo() and not posiciones:
        _actualizar(vid, ultimo_resumen="En pausa: el interruptor de emergencia bloquea las aperturas.")
        return {"ok": True, "estado": "EN_PAUSA"}

    # Paso 5: si el último tick es el mismo del chequeo anterior, el mercado no se movió y no se analiza.
    with ordenes.MT5_LOCK:
        tick = mt5.symbol_info_tick(v["simbolo"])
    hora_tick = int(tick.time) if tick is not None and getattr(tick, "time", 0) else None
    if hora_tick is not None and v.get("ultimo_tick") == hora_tick:   # nada se movió: no se gastan tokens
        _actualizar(vid, ultimo_resumen="Mercado sin movimiento desde el último chequeo: no se analizó.")
        return {"ok": True, "estado": "SIN_MOVIMIENTO"}

    # Paso 6: análisis del modelo; los fallos se cuentan y, al llegar al máximo seguido, se detiene la vigilancia.
    try:
        texto = analisis.fabrica_agente().responder(_mensaje_analisis(v, posiciones))
    except Exception as e:  # noqa: BLE001 - el fallo del modelo no debe tumbar el motor
        errores = (v.get("errores") or 0) + 1
        _actualizar(vid, errores=errores, ultimo_resumen=f"Falló el análisis: {e}"[:300])
        if errores >= ERRORES_SEGUIDOS_MAX:
            _finalizar(v, ERROR, f"Vigilancia detenida · {v['simbolo']}",
                       f"El análisis falló {errores} veces seguidas: {e}", tipo="error")
        return {"ok": False, "motivo": str(e)}

    # Paso 7: se relee el estado por si el usuario la detuvo durante el análisis.
    actual = obtener(vid)
    if not actual or actual["estado"] != ACTIVA:   # el usuario la detuvo mientras el modelo pensaba
        return {"ok": False, "motivo": "La vigilancia fue detenida durante el análisis; se descartó la decisión."}
    # Paso 8: se interpreta y ejecuta la decisión, y se guarda el resumen y el contador de errores a cero.
    decision = parsear_decision(texto)
    resumen = _aplicar(actual, decision, _posiciones_de(actual))
    _actualizar(vid, errores=0, ultimo_tick=hora_tick, ultimo_resumen=f"{ahora:%H:%M} · {resumen}"[:300])
    return {"ok": True, "decision": decision, "resumen": resumen}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara chequeo .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
