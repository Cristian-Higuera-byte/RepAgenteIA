# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara errores .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Traducción de los errores de la API de DeepSeek a mensajes legibles (ErrorLLM)."""
from __future__ import annotations

from openai import APIConnectionError, APIStatusError, APITimeoutError

from nucleo_agente.llm.tipos import ErrorLLM


# TITULO TRADUCIR ERROR

def traducir_error(e: Exception) -> ErrorLLM:
    """Convierte una excepción de la API en un ErrorLLM con mensaje legible en español.

    Reconoce 401 (clave inválida), 402 (saldo), 429 (límite de peticiones), otros estados HTTP, timeout
    y fallo de conexión; cualquier otra excepción se envuelve como error inesperado. Un ErrorLLM se
    devuelve tal cual.
    """
    if isinstance(e, ErrorLLM):
        return e
    if isinstance(e, APIStatusError):
        codigo = e.status_code
        if codigo == 401:
            return ErrorLLM("DeepSeek rechazó la API key (401). Revisa DEEPSEEK_API_KEY en el .env.")
        if codigo == 402:
            return ErrorLLM("Saldo insuficiente en la cuenta de DeepSeek (402).")
        if codigo == 429:
            return ErrorLLM("Límite de peticiones de DeepSeek alcanzado (429). Intenta de nuevo en un momento.")
        return ErrorLLM(f"Error de la API de DeepSeek ({codigo}): {e.message}")
    if isinstance(e, APITimeoutError):
        return ErrorLLM("DeepSeek tardó demasiado en responder (timeout).")
    if isinstance(e, APIConnectionError):
        return ErrorLLM("No se pudo conectar con DeepSeek. Revisa tu conexión a internet.")
    return ErrorLLM(f"Error inesperado en la capa LLM: {e}")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara errores .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
