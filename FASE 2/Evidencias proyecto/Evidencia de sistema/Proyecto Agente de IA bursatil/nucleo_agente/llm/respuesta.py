# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara respuesta .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Construye la RespuestaLLM a partir de lo que llegó (contenido, razonamiento, llamadas y uso de tokens)."""
from __future__ import annotations

from typing import Any

import configuracion  # type: ignore[import-not-found]
from nucleo_agente.llm.argumentos import _parsear_argumentos
from nucleo_agente.llm.tipos import LlamadaHerramienta, RespuestaLLM


# TITULO CONSTRUIR RESPUESTA

def construir_respuesta(
    nombre: str,
    contenido: str,
    razonamiento: str | None,
    llamadas_raw: list[dict[str, str]],
    usage: Any,
) -> RespuestaLLM:
    """Ensambla la RespuestaLLM a partir de lo recibido del modelo.

    Recibe el perfil, el texto, el razonamiento (o None), las llamadas crudas (id, nombre, args como
    texto JSON) y el objeto de uso de tokens. Parsea los argumentos de cada llamada (guardando el error
    si el JSON es inválido) y cuenta los tokens (0 si no hay datos). Además anota el consumo de la llamada en el registro de
    la cuenta (`herramientas/consumo_ia.py`).
    """
    thinking = configuracion.PERFILES[nombre].thinking
    # Cada llamada cruda se convierte en LlamadaHerramienta con sus argumentos ya parseados.
    llamadas = []
    for c in llamadas_raw:
        args, error = _parsear_argumentos(c["args"])
        llamadas.append(
            LlamadaHerramienta(
                id=c["id"],
                nombre=c["nombre"],
                argumentos=args,
                argumentos_raw=c["args"] or "{}",
                error=error,
            )
        )
    # El consumo de la llamada se anota por usuario y cuenta (herramientas/consumo_ia.py) para calcular el costo de la IA; nunca interrumpe
    # la respuesta: si no se puede anotar, se ignora.
    try:
        from herramientas import consumo_ia
        consumo_ia.registrar(nombre, configuracion.PERFILES[nombre].modelo, usage)
    except Exception:  # noqa: BLE001
        pass
    return RespuestaLLM(
        contenido=contenido,
        # En thinking siempre se reenvía el campo (aunque venga vacío).
        razonamiento=(razonamiento or "") if thinking else None,
        llamadas=llamadas,
        tokens_entrada=getattr(usage, "prompt_tokens", 0) or 0,
        tokens_salida=getattr(usage, "completion_tokens", 0) or 0,
        perfil=nombre,
    )


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara respuesta .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
