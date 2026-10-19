# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara gestion .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Gestión de vigilancias (la usan las herramientas del agente y el panel): crear, autorizar, rechazar, detener y listar."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from core import ordenes
from core.vigilancia.caducidad import _caducar_autorizaciones
from core.vigilancia.configuracion import (
    DURACION_DEFECTO_H, DURACION_MAX_H, DURACION_MIN_H, ACTIVA, EXPIRADA, INTERVALO_DEFECTO_MIN, INTERVALO_MAX,
    INTERVALO_MIN, MAX_OPERACIONES_DEFECTO, MAX_OPERACIONES_TOPE, MAX_VIGILANCIAS_POR_USUARIO, PENDIENTE,
    RIESGO_DEFECTO_PCT,
)
from core.vigilancia.motor import iniciar_motor
from core.vigilancia.posiciones import _posiciones_de
from core.vigilancia.utilidades import _a_numero, _actualizar, _consultar, _iso, obtener


def resumen_terminos(v: dict[str, Any]) -> dict[str, Any]:
    """Devuelve los términos de una vigilancia (id, símbolo, estado, riesgo, operaciones, intervalo, duración,
    permiso de cierre) con claves legibles para mostrar al modelo o al usuario."""
    return {
        "id": v["id"], "simbolo": v["simbolo"], "estado": v["estado"],
        "riesgo_por_operacion_pct": v["riesgo_pct"], "max_operaciones": v["max_operaciones"],
        "operaciones_realizadas": v.get("operaciones") or 0,
        "chequeo_cada_min": v["intervalo_min"], "duracion_horas": v["duracion_horas"],
        "puede_cerrar_sus_posiciones": bool(v.get("permite_cerrar")),
    }


def crear(
    usuario_id: str, simbolo: str, instruccion: str = "", riesgo_pct: Any = None,
    max_operaciones: Any = None, duracion_horas: Any = None, intervalo_min: Any = None,
) -> dict[str, Any]:
    """Registra una vigilancia PENDIENTE de autorización. {"ok": False, "motivo"} si no se puede.

    Recibe el usuario, el símbolo, la instrucción libre y los términos opcionales (riesgo %, máximo de
    operaciones, duración en horas, intervalo en minutos); los que falten usan los valores por defecto de
    configuracion.py. Valida rangos, cuenta demo, símbolo, que no haya otra vigilancia para el mismo activo y
    el tope por usuario. No opera: el usuario debe autorizarla después. Devuelve {"ok": True, "id", "resumen"}.
    Efecto: inserta una fila en la tabla vigilancias."""
    def no(motivo: str) -> dict[str, Any]:
        """Construye la respuesta de rechazo con el motivo dado."""
        return {"ok": False, "motivo": motivo}

    def leer(valor: Any, nombre: str, defecto: float) -> tuple[float | None, str | None]:
        """Devuelve (valor, error). Sin valor → el de por defecto; con un valor que no es número → error (no se adivina)."""
        if valor is None or valor == "":
            return defecto, None
        n = _a_numero(valor)
        return (n, None) if n is not None else (None, f"'{nombre}' debe ser un número.")

    # Paso 1: leer y convertir los términos; un valor presente pero no numérico es error.
    riesgo, e1 = leer(riesgo_pct, "riesgo_pct", RIESGO_DEFECTO_PCT)
    n_ops, e2 = leer(max_operaciones, "max_operaciones", MAX_OPERACIONES_DEFECTO)
    horas, e3 = leer(duracion_horas, "duracion_horas", DURACION_DEFECTO_H)
    cada, e4 = leer(intervalo_min, "intervalo_min", INTERVALO_DEFECTO_MIN)
    for error in (e1, e2, e3, e4):
        if error:
            return no(error)
    # Paso 2: validar rangos (el riesgo nunca puede superar el máximo global por operación).
    n_ops, cada = int(n_ops), int(cada)
    if riesgo <= 0:
        return no("El riesgo por operación debe ser mayor que 0.")
    if riesgo > ordenes.LIMITES.riesgo_max_por_operacion_pct:
        return no(f"El riesgo por operación ({riesgo}%) supera el máximo permitido "
                  f"({ordenes.LIMITES.riesgo_max_por_operacion_pct}%).")
    if not 1 <= n_ops <= MAX_OPERACIONES_TOPE:
        return no(f"El máximo de operaciones debe estar entre 1 y {MAX_OPERACIONES_TOPE}.")
    if not DURACION_MIN_H <= horas <= DURACION_MAX_H:
        return no(f"La duración debe estar entre {DURACION_MIN_H:g} y {DURACION_MAX_H:g} horas.")
    if not INTERVALO_MIN <= cada <= INTERVALO_MAX:
        return no(f"El intervalo de chequeo debe estar entre {INTERVALO_MIN} y {INTERVALO_MAX} minutos.")

    # Paso 3: cuenta demo y símbolo operable.
    _, motivo = ordenes.cuenta_demo()
    if motivo:
        return no(motivo)
    val = ordenes.validar_simbolo(simbolo)
    if not val["ok"]:
        return no(val["motivo"])
    sym = val["simbolo"]

    # Paso 4: sin duplicar el activo y respetando el máximo de vigilancias vigentes por usuario.
    _caducar_autorizaciones()
    vigentes = _consultar(
        "SELECT * FROM vigilancias WHERE usuario_id = ? AND estado IN ('PENDIENTE_AUTORIZACION', 'ACTIVA')",
        (usuario_id,),
    )
    for otra in vigentes:
        if otra["simbolo"].upper() == sym.upper():
            estado = "pendiente de tu autorización" if otra["estado"] == PENDIENTE else "activa"
            return no(f"Ya hay una vigilancia {estado} para {sym}. Detenla o resuélvela antes de crear otra.")
    if len(vigentes) >= MAX_VIGILANCIAS_POR_USUARIO:
        return no(f"Ya hay {len(vigentes)} vigilancias vigentes (máximo {MAX_VIGILANCIAS_POR_USUARIO}). "
                  "Detén alguna antes de crear otra.")

    # Paso 5: se guarda PENDIENTE con plazo de autorización igual a la vigencia de una propuesta.
    ahora = datetime.now()
    vid = uuid.uuid4().hex[:8]
    ordenes._ejecutar(
        "INSERT INTO vigilancias (id, usuario_id, simbolo, estado, instruccion, creada, expira_autorizacion, "
        "duracion_horas, intervalo_min, riesgo_pct, max_operaciones, permite_cerrar) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
        (vid, usuario_id, sym, PENDIENTE, (instruccion or "").strip()[:500], _iso(ahora),
         _iso(ahora + timedelta(minutes=ordenes.LIMITES.vigencia_propuesta_min)), horas, cada, riesgo, n_ops),
    )
    return {"ok": True, "id": vid, "resumen": resumen_terminos(obtener(vid) or {})}


def autorizar(vid: str, usuario_id: str) -> dict[str, Any]:
    """El usuario autoriza la vigilancia (botón del panel). La activa y arranca el motor.

    Recibe el id y el usuario (debe ser el dueño). Exige cuenta demo y que la autorización no haya vencido; la
    activación es atómica (UPDATE condicional) para que un doble clic no la active dos veces. Fija inicio,
    vencimiento y primer chequeo inmediato. Devuelve {"ok", "mensaje"}."""
    v = obtener(vid)
    if not v or v["usuario_id"] != usuario_id:
        return {"ok": False, "mensaje": "La vigilancia no existe."}
    _, motivo = ordenes.cuenta_demo()
    if motivo:
        return {"ok": False, "mensaje": motivo}
    ahora = datetime.now()
    reclamada = ordenes._ejecutar(
        "UPDATE vigilancias SET estado = 'ACTIVA', autorizada = ?, vence = ?, proximo_chequeo = ?, "
        "chequeos = 0, errores = 0 "
        "WHERE id = ? AND estado = 'PENDIENTE_AUTORIZACION' AND expira_autorizacion > ?",
        (_iso(ahora), _iso(ahora + timedelta(hours=float(v["duracion_horas"]))), _iso(ahora), vid, _iso(ahora)),
    )
    if reclamada == 0:
        if v["estado"] == PENDIENTE:
            _actualizar(vid, estado=EXPIRADA)
            return {"ok": False, "mensaje": "La autorización venció. Pídele al agente que la prepare de nuevo."}
        return {"ok": False, "mensaje": f"La vigilancia ya está en estado {v['estado']}."}
    iniciar_motor()
    return {"ok": True, "mensaje": f"Vigilancia de {v['simbolo']} activada. Te avisaré de cada operación."}


def rechazar(vid: str, usuario_id: str) -> bool:
    """Cancela una vigilancia aún PENDIENTE_AUTORIZACION del usuario (el botón Rechazar del panel).
    Devuelve True si cambió exactamente una fila."""
    return ordenes._ejecutar(
        "UPDATE vigilancias SET estado = 'CANCELADA', detalle = 'No autorizada por el usuario' "
        "WHERE id = ? AND usuario_id = ? AND estado = 'PENDIENTE_AUTORIZACION'", (vid, usuario_id),
    ) == 1


def detener(usuario_id: str, vid: str | None = None, simbolo: str | None = None) -> dict[str, Any]:
    """Detiene (por id o por símbolo) las vigilancias vigentes del usuario. No cierra posiciones abiertas."""
    filas = _consultar(
        "SELECT * FROM vigilancias WHERE usuario_id = ? AND estado IN ('PENDIENTE_AUTORIZACION', 'ACTIVA')",
        (usuario_id,),
    )
    if vid:
        filas = [f for f in filas if f["id"] == vid]
    elif simbolo:
        real = ordenes._resolver_simbolo(simbolo).upper()
        filas = [f for f in filas if f["simbolo"].upper() in (real, ordenes._normalizar(simbolo))]
    if not filas:
        return {"ok": False, "mensaje": "No hay una vigilancia vigente que coincida."}
    detenidas, con_posicion = [], []
    for f in filas:
        ordenes._ejecutar(
            "UPDATE vigilancias SET estado = 'CANCELADA', detalle = 'Detenida por el usuario' WHERE id = ?", (f["id"],))
        detenidas.append(f["simbolo"])
        if f["estado"] == ACTIVA and _posiciones_de(f):
            con_posicion.append(f["simbolo"])
    mensaje = f"Vigilancia detenida: {', '.join(detenidas)}."
    if con_posicion:
        mensaje += (f" Ojo: queda una posición abierta en {', '.join(con_posicion)} "
                    "(sigue con su stop loss y take profit); ciérrala tú si lo prefieres.")
    return {"ok": True, "mensaje": mensaje, "detenidas": detenidas}


def listar(usuario_id: str, incluir_finalizadas: bool = False, limite: int = 10) -> list[dict[str, Any]]:
    """Vigilancias del usuario: las vigentes, y opcionalmente las últimas ya terminadas."""
    _caducar_autorizaciones()
    if incluir_finalizadas:
        return _consultar("SELECT * FROM vigilancias WHERE usuario_id = ? ORDER BY creada DESC, rowid DESC LIMIT ?",
                          (usuario_id, int(limite)))
    return _consultar(
        "SELECT * FROM vigilancias WHERE usuario_id = ? AND estado IN ('PENDIENTE_AUTORIZACION', 'ACTIVA') "
        "ORDER BY creada, rowid", (usuario_id,),
    )


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara gestion .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
