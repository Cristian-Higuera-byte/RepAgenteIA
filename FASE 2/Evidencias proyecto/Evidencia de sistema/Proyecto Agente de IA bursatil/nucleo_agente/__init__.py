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

"""Paquete del núcleo del agente: LLM, bucle de herramientas, memoria y turnos en segundo plano.

Es la capa que une al modelo de lenguaje (DeepSeek) con las herramientas de `herramientas_agente`
y con la interfaz (dashboard Streamlit o consola_agente.py), sin depender de ninguna de ellas.
Subpaquetes principales: `agente` (conversación y bucle de herramientas), `llm` (cliente de la API),
`memoria` (persistencia en Supabase) y `turnos` (ejecución del agente en un hilo propio); además de
`contexto` (usuario de la consulta en curso) y `notificaciones` (avisos de la campana).

Este `__init__` actúa como fachada: reexporta `Agente` y `ClienteLLM`.
Las importaciones son perezosas a propósito: así `python -m nucleo_agente.llm` (prueba
de conexión) no carga el agente ni las herramientas.

    from nucleo_agente import Agente, ClienteLLM
"""

# Nombres públicos que expone la fachada (se resuelven bajo demanda en __getattr__).
__all__ = ["Agente", "ClienteLLM"]


# TITULO GETATTR

def __getattr__(nombre: str):
    """Resuelve de forma perezosa (PEP 562) los nombres públicos del paquete.

    Recibe el nombre del atributo pedido ("Agente" o "ClienteLLM"), importa el módulo correspondiente
    solo en ese momento y devuelve la clase. Lanza AttributeError para cualquier otro nombre.
    """
    # Cada rama importa dentro de la función para no cargar dependencias pesadas al importar el paquete.
    if nombre == "Agente":
        from .agente import Agente
        return Agente
    if nombre == "ClienteLLM":
        from .llm import ClienteLLM
        return ClienteLLM
    raise AttributeError(f"module 'nucleo_agente' has no attribute {nombre!r}")


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
