# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara conocimiento .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Herramienta para consultas RAG en la base de conocimiento interna.

Registra `buscar_en_base_de_conocimiento`, que delega en `herramientas.gestor_rag.consultar_rag`
(búsqueda de fragmentos de documentos internos guardados en Supabase) y devuelve el texto al modelo.
"""

from herramientas.base import herramienta
from tools.gestor_rag import consultar_rag


@herramienta(
    descripcion=(
        "Consulta la base de conocimiento interna en Supabase para obtener "
        "información sobre reglamentos, manuales, operativas o documentos guardados."
    ),
    parametros={
        "pregunta": {
            "type": "string",
            "description": "La consulta o tema a buscar en los documentos internos.",
        },
        "limite": {
            "type": "integer",
            "description": "Cantidad de fragmentos a recuperar (por defecto 3).",
        },
    },
    requeridos=["pregunta"],
)
def buscar_en_base_de_conocimiento(pregunta: str, limite: int = 3) -> dict:
    """Busca en la base de conocimiento interna (RAG) los fragmentos más relevantes para una pregunta.

    Recibe `pregunta` (tema a buscar) y `limite` (cantidad de fragmentos a recuperar, 3 por defecto).
    Devuelve {"resultado": ...} con lo que entrega `consultar_rag`. Efecto secundario: consulta
    la red (Supabase) a través del gestor RAG.
    """
    # Delega toda la lógica de recuperación en el gestor RAG y envuelve la respuesta en un dict serializable.
    resultado = consultar_rag(pregunta=pregunta, limite=limite)
    return {"resultado": resultado}


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara conocimiento .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
