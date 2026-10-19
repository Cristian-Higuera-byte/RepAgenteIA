# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara decision .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Decisión del modelo: lee el bloque ```decision {...}``` del final de la respuesta."""
from __future__ import annotations

import json
import re
from typing import Any

from core.vigilancia.utilidades import _a_numero


# Detecta objetos JSON planos (sin llaves anidadas) dentro del texto de la respuesta del modelo.
_RE_OBJETO = re.compile(r"\{[^{}]*\}", re.S)
# Traduce las palabras de acción que el modelo pueda usar (español o inglés) a las tres acciones válidas.
_SINONIMOS = {
    "espera": "esperar", "esperar": "esperar", "wait": "esperar", "hold": "esperar", "mantener": "esperar",
    "abrir": "abrir", "open": "abrir", "comprar": "abrir", "vender": "abrir",
    "cerrar": "cerrar", "close": "cerrar",
}


def parsear_decision(texto: str) -> dict[str, Any]:
    """Lee el bloque ```decision {...}``` del final de la respuesta del modelo.

    Recibe el texto completo. Devuelve un diccionario con accion (esperar/abrir/cerrar), lado, stop_loss,
    take_profit, ticket y resumen (máx. 300 caracteres). Si no hay un bloque válido, la decisión es
    ESPERAR con `invalida` True (nunca se opera por una respuesta que no se entiende)."""
    # Paso 1: reunir los objetos JSON del texto que mencionan "accion".
    candidatos = []
    for m in _RE_OBJETO.finditer(texto or ""):
        if '"accion"' in m.group(0) or "'accion'" in m.group(0):
            candidatos.append(m.group(0))
    # Paso 2: se prueba desde el último (la decisión va al final) hasta hallar uno válido.
    for crudo in reversed(candidatos):
        try:
            d = json.loads(crudo)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        # La acción se normaliza con los sinónimos; si no se reconoce se descarta este candidato.
        accion = _SINONIMOS.get(str(d.get("accion", "")).strip().lower())
        if accion is None:
            continue
        # "comprar" y "vender" implican el lado aunque no venga el campo.
        lado = str(d.get("lado", "")).strip().lower()
        if str(d.get("accion", "")).strip().lower() == "comprar":
            lado = "compra"
        elif str(d.get("accion", "")).strip().lower() == "vender":
            lado = "venta"
        # Los números pueden venir como texto; _a_numero los tolera.
        ticket = _a_numero(d.get("ticket"))
        return {
            "accion": accion,
            "lado": lado if lado in ("compra", "venta") else None,
            "stop_loss": _a_numero(d.get("stop_loss")),
            "take_profit": _a_numero(d.get("take_profit")),
            "ticket": int(ticket) if ticket is not None else None,
            "resumen": str(d.get("resumen") or "").strip()[:300],
        }
    # Paso 3: sin decisión legible se espera (seguro por defecto) y se marca como inválida.
    return {"accion": "esperar", "lado": None, "stop_loss": None, "take_profit": None, "ticket": None,
            "resumen": "No se pudo leer la decisión del análisis; se espera al próximo chequeo.", "invalida": True}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara decision .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
