# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara memoria .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
memoria.py
-----------
Guarda un historial local de las consultas que el usuario le hace al
agente, junto con el resultado obtenido, en un archivo JSON. Esto
permite llevar un registro simple sin necesidad de una base de datos.
"""

import json
import os
from datetime import datetime

# Ruta (relativa al directorio de ejecución) del JSON con el historial de consultas.
ARCHIVO_MEMORIA = "data/consultas_guardadas.json"

# TITULO GUARDAR CONSULTA

def guardar_consulta(pregunta: str, resultado: dict) -> dict:
    """
    Agrega una nueva consulta o actualiza la existente si la pregunta
    es exactamente la misma, evitando duplicados y saturación.

    Parámetros:
        pregunta (str): Pregunta o instrucción original del usuario.
        resultado (dict): Resultado obtenido de la herramienta ejecutada.

    Retorna:
        dict: Confirmación de la acción realizada y total de consultas.
    """
    # Carga el historial existente; si no hay archivo o está corrupto, parte de cero.
    consultas = []
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as f:
            try:
                consultas = json.load(f)
            except json.JSONDecodeError:
                consultas = []

    # Buscamos si ya existe una consulta con exactamente la misma pregunta
    encontrada = False
    for elemento in consultas:
        if elemento.get("pregunta") == pregunta:
            elemento["fecha_hora"] = datetime.now().isoformat(timespec="seconds")
            elemento["resultado"] = resultado
            encontrada = True
            break

    # Si no existe, la agregamos como un registro nuevo
    if not encontrada:
        nuevo_registro = {
            "fecha_hora": datetime.now().isoformat(timespec="seconds"),
            "pregunta": pregunta,
            "resultado": resultado,
        }
        consultas.append(nuevo_registro)

    # Guardamos la lista actualizada en el archivo JSON
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump(consultas, f, ensure_ascii=False, indent=2)

    # Informa si se actualizó una pregunta repetida o se creó una nueva.
    accion = "actualizado" if encontrada else "guardado"
    return {"estado": accion, "total_consultas": len(consultas)}

# TITULO LIMPIAR MEMORIA

def limpiar_memoria() -> dict:
    """
    Elimina por completo el archivo de consultas guardadas o vacía su contenido,
    reiniciando el historial local.

    Retorna:
        dict: Confirmación de que el historial fue limpiado.
    """
    if os.path.exists(ARCHIVO_MEMORIA):
        # Opción 1: Borrar el archivo físicamente
        os.remove(ARCHIVO_MEMORIA)

    return {"estado": "limpiado", "mensaje": "El historial de consultas guardadas ha sido borrado exitosamente."}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara memoria .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
