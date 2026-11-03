# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara ejecucion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ejecución de la decisión (solo el motor ejecuta): valida, propone y confirma por nucleo_agente.ordenes."""
from __future__ import annotations

from typing import Any

from herramientas.tickets import ticket as _tk
from nucleo_agente import ordenes
from nucleo_agente.vigilancia.configuracion import MAX_ABIERTAS_POR_VIGILANCIA
from nucleo_agente.vigilancia.utilidades import _lado_texto, _notificar


# TITULO APLICAR

def _aplicar(v: dict[str, Any], d: dict[str, Any], posiciones: list[Any]) -> str:
    """Valida y ejecuta la decisión del modelo; es el único punto donde la vigilancia opera.

    Recibe la vigilancia `v`, la decisión `d` (de parsear_decision) y las posiciones propias abiertas.
    Para abrir exige no superar la posición abierta ni el máximo de operaciones, y un lado y stop loss válidos;
    luego propone por ordenes.proponer_apertura (que aplica todos los límites de riesgo) y confirma de inmediato.
    Para cerrar exige el permiso de la vigilancia y que el ticket sea propio. Cada resultado notifica al usuario.
    Devuelve el resumen de una línea para el historial de la vigilancia."""
    # Símbolo de la vigilancia (el modelo no elige otro) y resumen de la decisión.
    simbolo, resumen = v["simbolo"], d.get("resumen") or ""
    if d["accion"] == "abrir":
        if len(posiciones) >= MAX_ABIERTAS_POR_VIGILANCIA:
            return f"Esperar: ya hay una posición abierta. {resumen}".strip()
        if (v.get("operaciones") or 0) >= v["max_operaciones"]:
            return "Esperar: se alcanzó el máximo de operaciones de esta vigilancia."
        if d["lado"] is None or d["stop_loss"] is None:
            return "No se abrió: la decisión no traía un lado y un stop loss válidos."
        # Se propone con el riesgo fijado en la vigilancia; los límites globales se aplican dentro.
        prop = ordenes.proponer_apertura(
            simbolo, d["lado"], d["stop_loss"], d["take_profit"], v["riesgo_pct"],
            resumen or "Operación automática de la vigilancia", origen="automatica", vigilancia_id=v["id"],
        )
        if prop.get("estado") != "PROPUESTA_PENDIENTE":
            motivo = prop.get("motivo") or prop.get("mensaje") or "bloqueada por los límites de riesgo"
            _notificar(v, f"Operación bloqueada · {simbolo}", f"El agente quiso abrir {d['lado']} pero: {motivo}", tipo="error")
            return f"Bloqueada: {motivo}"
        # Como el usuario ya autorizó la vigilancia, el motor confirma la propuesta sin pasar por el panel.
        resultado = ordenes.confirmar_orden(prop["id"])
        if resultado.get("ok"):
            ordenes._ejecutar("UPDATE vigilancias SET operaciones = operaciones + 1 WHERE id = ?", (v["id"],))
            r = prop["resumen"]
            detalle = (f"{r['volumen']:g} lotes · SL {r['stop_loss']} · TP {r['take_profit'] or '—'} · "
                       f"riesgo {r['riesgo']}")
            _notificar(v, f"{_lado_texto(d['lado'])} automática · {simbolo}", f"{detalle}. {resultado.get('mensaje', '')}")
            return f"Abrió {d['lado']}: {resumen}".strip()
        _notificar(v, f"No se pudo ejecutar · {simbolo}", resultado.get("mensaje", "Error al enviar la orden."), tipo="error")
        return f"No se ejecutó: {resultado.get('mensaje', '')}"
    if d["accion"] == "cerrar":
        if not v.get("permite_cerrar"):
            return "No se cerró: esta vigilancia no tiene permiso para cerrar."
        # Solo se puede cerrar una posición abierta por esta misma vigilancia; con una sola, el ticket es implícito.
        propias = {_tk(p.ticket): p for p in posiciones}
        ticket = d["ticket"] if d["ticket"] is not None else (next(iter(propias)) if len(propias) == 1 else None)
        if ticket not in propias:
            return "No se cerró: el ticket no corresponde a una posición abierta por esta vigilancia."
        resultado_actual = propias[ticket].profit
        prop = ordenes.proponer_cierre(ticket, resumen or "Cierre automático de la vigilancia",
                                       origen="automatica", vigilancia_id=v["id"])
        if prop.get("estado") != "PROPUESTA_PENDIENTE":
            motivo = prop.get("motivo") or "no se pudo preparar el cierre"
            _notificar(v, f"No se pudo cerrar · {simbolo}", motivo, tipo="error")
            return f"No se cerró: {motivo}"
        resultado = ordenes.confirmar_orden(prop["id"])
        if resultado.get("ok"):
            _notificar(v, f"Posición cerrada · {simbolo}",
                       f"Resultado ≈ {resultado_actual:+.2f}. {resumen or resultado.get('mensaje', '')}".strip())
            return f"Cerró la posición #{ticket}: {resumen}".strip()
        _notificar(v, f"No se pudo cerrar · {simbolo}", resultado.get("mensaje", "Error al enviar la orden."), tipo="error")
        return f"No se cerró: {resultado.get('mensaje', '')}"
    # Cualquier otra acción equivale a esperar.
    return f"Esperar: {resumen}".strip()


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara ejecucion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
