"""
test.py
------------
Script de prueba para verificar la conexión con Supabase
y el funcionamiento de la recuperación de documentos (RAG).
"""

import os
import sys
from collections.abc import Mapping
from typing import Any, cast

# Añadir la ruta raíz del proyecto al path para permitir importaciones relativas si es necesario
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables del archivo .env (ubicado en la raíz)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print("=== INICIANDO PRUEBA DE CONEXIÓN RAG (SUPABASE) ===")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")
    exit(1)
else:
    print("✅ Credenciales encontradas en el archivo .env")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Cliente de Supabase inicializado correctamente.")

    print("🔍 Consultando la tabla 'documentos_rag'...")
    respuesta = supabase.table("documentos_rag").select("id, contenido, metadata").limit(5).execute()

    print(f"📊 Registros encontrados en la base de conocimiento: {len(respuesta.data)}")

    if len(respuesta.data) > 0:
        print("\n--- Vista previa del primer documento encontrado ---")
        primer_doc = cast(Mapping[str, Any], respuesta.data[0])
        contenido = str(primer_doc.get('contenido') or '')
        print(f"ID: {primer_doc.get('id')}")
        print(f"Metadata: {primer_doc.get('metadata')}")
        print(f"Contenido: {contenido[:150]}...")
    else:
        print("⚠️ La tabla está vacía.")

except Exception as e:
    print(f"❌ Ocurrió un error al conectar con Supabase: {str(e)}")

print("\n=== PRUEBA FINALIZADA ===")