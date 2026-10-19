# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara herramientas .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Herramientas registradas para el agente de órdenes y vigilancias (los esquemas viven en esquemas.json).

Ninguna ejecuta operaciones por sí sola: solo proponen aperturas, cierres y
vigilancias (que el usuario debe autorizar en el dashboard) o consultan estado.
La lógica vive en ``core.ordenes`` y ``core.vigilancia``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core import contexto, ordenes, vigilancia
from herramientas.base import cargar_json, herramienta
from herramientas.ordenes_herramientas.auxiliares import _a_numero

# Esquemas (descripción y parámetros) de las herramientas, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


@herramienta(**_ESQ["proponer_orden"])
def proponer_orden(
    simbolo: str,
    lado: str,
    stop_loss: float,
    justificacion: str,
    take_profit: float | None = None,
    riesgo_pct: float | None = 0.5,
) -> dict[str, Any]:
    """Registra una propuesta de apertura de operación pendiente de confirmación del usuario.

    Recibe símbolo, lado (compra/venta), stop loss, justificación, take profit
    opcional y el porcentaje de equidad a arriesgar (0.5 por defecto). Convierte
    a número los valores enviados como texto por el modelo y delega en
    ``ordenes.proponer_apertura``, que valida los límites de riesgo y calcula el
    tamaño. Devuelve su resultado, o ``{"estado": "RECHAZADA", ...}`` si el riesgo no es numérico.
    """
    # Normaliza el riesgo: el modelo puede enviar texto, null o vacío.
    riesgo = _a_numero(riesgo_pct)
    if riesgo in (None, ""):          # el modelo envió null o vacío: se usa el valor por defecto
        riesgo = 0.5
    if isinstance(riesgo, bool) or not isinstance(riesgo, (int, float)):
        return {"estado": "RECHAZADA", "motivo": "'riesgo_pct' debe ser un número (por ejemplo 0.5)."}
    # Delega la validación y el registro de la propuesta.
    return ordenes.proponer_apertura(
        simbolo=simbolo,
        lado=lado,
        stop_loss=_a_numero(stop_loss),
        take_profit=_a_numero(take_profit),
        riesgo_pct=riesgo,
        justificacion=justificacion,
    )


@herramienta(**_ESQ["proponer_cierre_posicion"])
def proponer_cierre_posicion(ticket: int, justificacion: str) -> dict[str, Any]:
    """Registra una propuesta de cierre de la posición con el ticket indicado, pendiente de confirmación del usuario."""
    return ordenes.proponer_cierre(ticket=ticket, justificacion=justificacion)


@herramienta(**_ESQ["ver_posiciones"])
def ver_posiciones() -> dict[str, Any]:
    """Devuelve el resumen de las posiciones abiertas (solo lectura)."""
    return ordenes.resumen_posiciones()


@herramienta(**_ESQ["ver_limites_riesgo"])
def ver_limites_riesgo() -> dict[str, Any]:
    """Devuelve los límites de riesgo del agente y cuánto de ellos está usado (solo lectura)."""
    return ordenes.estado_riesgo()


@herramienta(**_ESQ["proponer_vigilancia"])
def proponer_vigilancia(
    simbolo: str,
    instruccion: str,
    riesgo_pct: float | None = None,
    max_operaciones: int | None = None,
    duracion_horas: float | None = None,
    intervalo_min: int | None = None,
) -> dict[str, Any]:
    """Registra una vigilancia automática de un símbolo, pendiente de autorización del usuario.

    Recibe símbolo, instrucción en texto y límites opcionales (riesgo %, máximo de
    operaciones, duración en horas e intervalo en minutos). La crea para el
    usuario actual (``contexto.usuario_actual``) vía ``vigilancia.crear``. No queda
    activa hasta que el usuario pulse «Autorizar». Devuelve el estado
    VIGILANCIA_PENDIENTE_DE_AUTORIZACION con id, resumen e instrucciones para el
    modelo, o RECHAZADA con el motivo.
    """
    # Crea la vigilancia convirtiendo a número los parámetros enviados como texto.
    r = vigilancia.crear(
        contexto.usuario_actual(), simbolo, instruccion,
        riesgo_pct=_a_numero(riesgo_pct), max_operaciones=_a_numero(max_operaciones),
        duracion_horas=_a_numero(duracion_horas), intervalo_min=_a_numero(intervalo_min),
    )
    # Si la validación falla, informa el motivo.
    if not r["ok"]:
        return {"estado": "RECHAZADA", "motivo": r["motivo"]}
    # Aclara al modelo que aún no está activa.
    return {
        "estado": "VIGILANCIA_PENDIENTE_DE_AUTORIZACION",
        "id": r["id"],
        "resumen": r["resumen"],
        "mensaje": (
            "Vigilancia registrada, pero NO está activa: el usuario debe pulsar «Autorizar» en la tarjeta del panel "
            "«Órdenes propuestas» (vale unos minutos). Hasta entonces NO se vigila ni se opera. No afirmes que ya está "
            "vigilando: resume los términos (activo, riesgo, operaciones máximas, duración, frecuencia) y dile cómo autorizarla."
        ),
    }


@herramienta(**_ESQ["detener_vigilancia"])
def detener_vigilancia(simbolo: str | None = None, id: str | None = None) -> dict[str, Any]:  # noqa: A002
    """Detiene la vigilancia indicada por ``id`` o las del ``simbolo`` del usuario actual y devuelve el resultado de ``vigilancia.detener``."""
    return vigilancia.detener(contexto.usuario_actual(), vid=id, simbolo=simbolo)


@herramienta(**_ESQ["ver_vigilancias"])
def ver_vigilancias() -> dict[str, Any]:
    """Lista hasta 8 vigilancias recientes (incluidas las finalizadas) del usuario actual con términos, vencimiento, próximo chequeo y último resumen."""
    # Obtiene las filas y arma el resumen de cada una.
    filas = vigilancia.listar(contexto.usuario_actual(), incluir_finalizadas=True, limite=8)
    return {
        "vigilancias": [
            {**vigilancia.resumen_terminos(f), "vence": f.get("vence"), "proximo_chequeo": f.get("proximo_chequeo"),
             "ultimo_resumen": f.get("ultimo_resumen"), "detalle": f.get("detalle")}
            for f in filas
        ]
    }


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara herramientas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
