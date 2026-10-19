# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara tipos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Tipos de la capa LLM: error legible, llamada a herramienta, respuesta completa y evento de streaming."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ErrorLLM(Exception):
    """Error de la capa LLM con mensaje ya legible para el usuario."""


@dataclass
class LlamadaHerramienta:
    """Una herramienta que el modelo pidió ejecutar: id de la llamada, nombre y argumentos (parseados y en crudo)."""

    id: str
    nombre: str
    argumentos: dict[str, Any]
    argumentos_raw: str = "{}"
    error: str | None = None   # se rellena si el modelo envió un JSON inválido


@dataclass
class RespuestaLLM:
    """Respuesta completa del modelo: texto, razonamiento, llamadas a herramientas y tokens consumidos."""

    contenido: str = ""
    razonamiento: str | None = None            # None = el perfil no usa thinking
    llamadas: list[LlamadaHerramienta] = field(default_factory=list)
    tokens_entrada: int = 0
    tokens_salida: int = 0
    perfil: str = ""

    @property
    def mensaje(self) -> dict[str, Any]:
        """Mensaje del asistente listo para añadir al historial.

        Incluye reasoning_content cuando el perfil usa thinking (DeepSeek lo exige en el historial) y
        tool_calls cuando el modelo pidió herramientas.
        """
        # Mensaje base del asistente; los campos opcionales se agregan solo si existen.
        msg: dict[str, Any] = {"role": "assistant", "content": self.contenido}
        if self.razonamiento is not None:
            msg["reasoning_content"] = self.razonamiento
        if self.llamadas:
            msg["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.nombre, "arguments": c.argumentos_raw or "{}"},
                }
                for c in self.llamadas
            ]
        return msg


@dataclass
class EventoStream:
    """tipo: 'razonamiento' | 'texto' | 'final' (en 'final' viene la RespuestaLLM completa)."""

    tipo: str
    texto: str = ""
    respuesta: RespuestaLLM | None = None


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara tipos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
