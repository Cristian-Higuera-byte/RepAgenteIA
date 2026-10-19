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
from core.llm.argumentos import _parsear_argumentos
from core.llm.tipos import LlamadaHerramienta, RespuestaLLM


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
    si el JSON es inválido) y cuenta los tokens (0 si no hay datos).
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
