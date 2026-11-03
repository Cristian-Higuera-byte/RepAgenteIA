# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara peticion .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Parámetros de la petición a DeepSeek según el perfil (modelo, thinking, temperatura, stream)."""
from __future__ import annotations

from typing import Any

import configuracion  # type: ignore[import-not-found]


# TITULO CONSTRUIR KWARGS

def construir_kwargs(
    nombre: str,
    mensajes: list[dict[str, Any]],
    herramientas: list[dict[str, Any]] | None,
    stream: bool,
) -> dict[str, Any]:
    """Arma los argumentos de chat.completions.create para el perfil indicado.

    Recibe el nombre del perfil, los mensajes, los esquemas de herramientas (o None) y si es streaming.
    Con thinking envía reasoning_effort y activa el modo; sin thinking envía la temperatura y lo
    desactiva (en thinking la temperatura no tiene efecto). Con stream pide también el uso de tokens.
    """
    # Parámetros del perfil (modelo, max_tokens, thinking, esfuerzo, temperatura).
    p = configuracion.PERFILES[nombre]
    kw: dict[str, Any] = {
        "model": p.modelo,
        "messages": mensajes,
        "max_tokens": p.max_tokens,
    }
    # Solo se envían las herramientas si las hay.
    if herramientas:
        kw["tools"] = herramientas
    # Modo de razonamiento según el perfil.
    if p.thinking:
        kw["reasoning_effort"] = p.esfuerzo
        kw["extra_body"] = {"thinking": {"type": "enabled"}}
    else:
        kw["temperature"] = p.temperatura
        kw["extra_body"] = {"thinking": {"type": "disabled"}}
    # Streaming: include_usage hace que el último fragmento traiga los tokens consumidos.
    if stream:
        kw["stream"] = True
        kw["stream_options"] = {"include_usage": True}
    return kw


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara peticion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
