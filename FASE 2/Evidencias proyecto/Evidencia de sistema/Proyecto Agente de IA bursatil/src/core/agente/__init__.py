# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Núcleo del agente: conversación + bucle de herramientas.

No sabe nada de la interfaz (terminal, Streamlit...) ni de las herramientas
concretas. Emite eventos (EventoAgente) y quien lo use decide cómo mostrarlos.

Uso básico:
    agente = Agente()
    print(agente.responder("¿Qué día es hoy?"))

Uso con streaming (chat del dashboard):
    for ev in agente.responder_stream("..."):
        if ev.tipo == "texto": ...

Archivos: agente.py (clase Agente), ciclo.py (bucle de herramientas), eventos.py, instrucciones.py (prompt de sistema).

Este `__init__` también reexporta, por compatibilidad con código antiguo que importaba todo desde aquí,
PROMPT_RESPALDO, _prompt_sistema, ClienteLLM, ErrorMemoria, Memoria, REGISTRO y RegistroHerramientas.
"""
# Reexportaciones de la API pública del paquete.
from core.agente.agente import Agente
from core.agente.eventos import EventoAgente
# Los siguientes imports se conservan solo como reexportaciones (no se usan en este archivo).
from core.agente.instrucciones import PROMPT_RESPALDO, _prompt_sistema  # noqa: F401
from core.llm import ClienteLLM  # noqa: F401
from core.memoria import ErrorMemoria, Memoria  # noqa: F401
from herramientas.base import REGISTRO, RegistroHerramientas  # noqa: F401


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
