# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara gestor_rag .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
gestor_rag.py
---------------
Módulo encargado de gestionar la recuperación aumentada de conocimiento (RAG)
utilizando Supabase con la extensión pgvector.

Expone `consultar_rag`, que el agente usa para traer fragmentos de documentos
internos (tabla `documentos_rag`) como contexto adicional. Las credenciales se
leen del archivo .env (SUPABASE_URL y SUPABASE_KEY).
"""
import os
from typing import cast
from dotenv import load_dotenv
from supabase import Client, create_client  # type: ignore[import-not-found]

load_dotenv()

# Credenciales de Supabase (URL del proyecto y clave de API), leídas del entorno
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Cliente único de Supabase compartido por el módulo (se crea al importar)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# TITULO CONSULTAR RAG

def consultar_rag(pregunta: str, limite: int = 3) -> str:
    """
    Realiza una búsqueda semántica en la base de datos vectorial de Supabase
    basada en la pregunta del usuario.

    Parámetros:
        pregunta (str): Pregunta o consulta del usuario.
        limite (int): Cantidad máxima de fragmentos relevantes a recuperar.

    Retorna:
        str: Texto combinado con el contexto recuperado de los documentos internos.

    Efecto secundario: consulta de red a Supabase. Nota: actualmente no filtra
    por similitud con la pregunta; solo lee los primeros `limite` registros de
    la tabla. Ante credenciales ausentes, tabla vacía o error devuelve un
    mensaje de texto en lugar de lanzar excepción.
    """
    # Verifica que haya credenciales antes de consultar.
    if not SUPABASE_URL or not SUPABASE_KEY:
        return "Advertencia: Las credenciales de Supabase (SUPABASE_URL, SUPABASE_KEY) no están configuradas en el archivo .env."
    try:
        # Lee contenido y metadata de los primeros documentos indexados.
        respuesta = supabase.table("documentos_rag").select("contenido, metadata").limit(limite).execute()
        if not respuesta.data:
            return "No se encontraron documentos indexados en la base de conocimiento interna."
        # Concatena cada fragmento numerado con su fuente (si la metadata la trae).
        contexto_acumulado = "--- CONTEXTO RECUPERADO DE DOCUMENTOS INTERNOS ---\n"
        for indice, elemento in enumerate(respuesta.data, 1):
            doc = cast(dict, elemento)
            metadata = doc.get("metadata", {})
            fuente = "Documento interno"
            if isinstance(metadata, dict):
                fuente = metadata.get("fuente", "Documento interno")
            contenido = doc.get("contenido", "")
            contexto_acumulado += f"[{indice}] (Fuente: {fuente})\n{contenido}\n\n"
        return contexto_acumulado
    except Exception as e:
        return f"Error al consultar el sistema RAG: {str(e)}"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara gestor_rag .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
