# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara instrucciones .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Prompt de sistema del agente (prompts/sistema.md; con respaldo si el archivo no existe)."""
from __future__ import annotations

from datetime import datetime

import configuracion

try:
    from herramientas.puente_mt5 import NOMBRE_BROKER
except Exception:  # noqa: BLE001 - sin el puente se usa un nombre genérico
    NOMBRE_BROKER = "el broker"

# Prompt mínimo que se usa si no existe prompts/sistema.md; "{fecha}" se sustituye por la fecha de hoy y "{broker}" por el broker.
PROMPT_RESPALDO = (
    "Eres un analista bursátil. Hoy es {fecha}. Usa las herramientas para obtener datos "
    "reales, no inventes cifras y responde siempre en español."
)


# TITULO PROMPT SISTEMA

def _prompt_sistema(contexto: str = "") -> str:
    """Construye el prompt de sistema del agente.

    Lee prompts/sistema.md (o usa PROMPT_RESPALDO), sustituye {fecha} por la fecha local de hoy y {broker} por el nombre del
    broker de la cuenta (Capital.com o MetaTrader 5) y, si hay
    `contexto` de memoria del usuario, lo agrega al final. Devuelve el texto completo.
    """
    # Se prefiere el archivo editable del proyecto; el respaldo evita fallar si falta.
    ruta = configuracion.DIR_PROMPTS / "sistema.md"
    base = ruta.read_text(encoding="utf-8") if ruta.exists() else PROMPT_RESPALDO
    # Solo la fecha (no la hora): así el prefijo del prompt no cambia durante el día
    # y DeepSeek puede reutilizar su caché de contexto (más barato y rápido).
    prompt = base.replace("{fecha}", datetime.now().astimezone().strftime("%Y-%m-%d")).replace("{broker}", NOMBRE_BROKER)
    return f"{prompt}\n\n{contexto}" if contexto else prompt


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara instrucciones .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
