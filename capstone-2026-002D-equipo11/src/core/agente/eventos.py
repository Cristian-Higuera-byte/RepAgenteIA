# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara eventos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Evento que emite el agente mientras responde (lo consumen la consola, el hilo de turnos y el chat)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventoAgente:
    """Evento del agente.

    tipo: 'razonamiento' | 'texto' | 'herramienta' | 'resultado' | 'fin'.
    texto: fragmento de texto, o nombre de la herramienta en los eventos "herramienta"/"resultado".
    datos: argumentos de la herramienta, su resultado o los tokens/perfil del evento "fin".
    """

    tipo: str
    texto: str = ""
    datos: dict[str, Any] = field(default_factory=dict)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara eventos .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
