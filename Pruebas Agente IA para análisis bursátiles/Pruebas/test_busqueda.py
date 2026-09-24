"""
test_busqueda.py
---------------------
Prueba la recuperación de contenido desde el módulo rag_manager.py ubicado en tools/
"""

import os
import sys

# Añadir la raíz del proyecto al path para que reconozca la carpeta 'tools'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.rag_manager import consultar_rag

print("=== PROBANDO BÚSQUEDA EN EL RAG ===")

pregunta_prueba = "¿Qué evalúa Piña y Jara Transportes y Servicios LTDA. respecto a la IA?"

print(f"Pregunta enviada: '{pregunta_prueba}'\n")

resultado_contexto = consultar_rag(pregunta_prueba)

print("Resultado obtenido del RAG:")
print(resultado_contexto)

print("\n=== PRUEBA DE BÚSQUEDA FINALIZADA ===")