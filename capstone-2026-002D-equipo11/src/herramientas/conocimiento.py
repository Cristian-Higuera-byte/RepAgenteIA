"""Herramienta para consultas RAG en la base de conocimiento interna."""

from herramientas.base import herramienta
from tools.rag_manager import consultar_rag


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
    resultado = consultar_rag(pregunta=pregunta, limite=limite)
    return {"resultado": resultado}