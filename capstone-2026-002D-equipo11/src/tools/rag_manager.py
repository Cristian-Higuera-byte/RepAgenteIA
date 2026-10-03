"""
rag_manager.py
---------------
Módulo encargado de gestionar la recuperación aumentada de conocimiento (RAG)
utilizando Supabase con la extensión pgvector.
"""

import os
from collections.abc import Mapping
from typing import Any, cast
from dotenv import load_dotenv
from supabase import Client, create_client  # type: ignore[import-not-found]

load_dotenv()

# Credenciales de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def consultar_rag(pregunta: str, limite: int = 3) -> str:
    """
    Realiza una búsqueda semántica en la base de datos vectorial de Supabase
    basada en la pregunta del usuario.
    
    Parámetros:
        pregunta (str): Pregunta o consulta del usuario.
        limite (int): Cantidad máxima de fragmentos relevantes a recuperar.
        
    Retorna:
        str: Texto combinado con el contexto recuperado de los documentos internos.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return "Advertencia: Las credenciales de Supabase (SUPABASE_URL, SUPABASE_KEY) no están configuradas en el archivo .env."

    try:
        respuesta = supabase.table("documentos_rag").select("contenido, metadata").limit(limite).execute()
        
        if not respuesta.data:
            return "No se encontraron documentos indexados en la base de conocimiento interna."
            
        contexto_acumulado = "--- CONTEXTO RECUPERADO DE DOCUMENTOS INTERNOS ---\n"
        for idx, item in enumerate(respuesta.data, 1):
            doc = cast(dict, item)
            
            metadata = doc.get("metadata", {})
            
            fuente = "Documento interno"
            if isinstance(metadata, dict):
                fuente = metadata.get("fuente", "Documento interno")

            contenido = doc.get("contenido", "")
            contexto_acumulado += f"[{idx}] (Fuente: {fuente})\n{contenido}\n\n"
             
        return contexto_acumulado

    except Exception as e:
        return f"Error al consultar el sistema RAG: {str(e)}"