"""
main.py
--------
Punto de entrada del agente bursátil.

Implementa el bucle de conversación con tool calling de forma robusta:
- Soporta múltiples rondas de tool calling (no asume que hay solo una).
- Si el modelo llama una herramienta con un nombre mal formado, el error
  se le devuelve como resultado de la tool, y como 'tools' sigue
  disponible en cada ronda, el modelo puede corregirse solo en el
  siguiente intento (esto evita el error 400 "Tool choice is none,
  but model called a tool" que ocurría cuando la segunda llamada no
  incluía 'tools').
- Cada ejecución de herramienta se guarda automáticamente en memoria
  local (memoria.py), sin que el modelo tenga que pedirlo.
"""

import json
from typing import Any, cast

from core.agent import HERRAMIENTAS, ejecutar_herramienta  # type: ignore[attr-defined]
from core.llm_client import cliente, MODELO, SYSTEM_PROMPT  # type: ignore[attr-defined]
from tools.memoria import guardar_consulta


def chat_agente(mensaje_usuario: str, historial: list[Any] | None = None, max_iteraciones: int = 5) -> tuple[str, list]:
    """
    Procesa un mensaje del usuario a través del agente, ejecutando
    herramientas si el modelo lo solicita, con soporte para varias
    rondas de tool calling (incluyendo reintentos por errores).

    Parámetros:
        mensaje_usuario (str): Pregunta o instrucción del usuario.
        historial (list): Historial de mensajes previos, para mantener
                            contexto entre turnos. Si es None, se crea uno nuevo.
        max_iteraciones (int): Tope de rondas de tool calling para evitar
                                bucles infinitos si el modelo insiste en
                                fallar repetidamente.

    Retorna:
        tuple[str, list]: (respuesta_final_en_texto, historial_actualizado)
    """
    if historial is None:
        historial = [{"role": "system", "content": SYSTEM_PROMPT}]

    historial.append({"role": "user", "content": mensaje_usuario})

    for intento in range(max_iteraciones):
        respuesta = cliente.chat.completions.create(
            model=MODELO,
            messages=cast(Any, historial),
            tools=cast(Any, HERRAMIENTAS),
            tool_choice="auto",
        )

        mensaje = respuesta.choices[0].message

        # Si el modelo ya no necesita ejecutar herramientas, esta es la respuesta final
        if not mensaje.tool_calls:
            historial.append({"role": "assistant", "content": mensaje.content})
            return mensaje.content or "", historial

        # El modelo pidió ejecutar una o más herramientas
        historial.append(mensaje)

        for llamada in mensaje.tool_calls:
            # ``tool_calls`` también puede contener llamadas custom, que no
            # exponen el atributo ``function``. Este agente solo procesa
            # llamadas de función.
            llamada_funcion = getattr(cast(Any, llamada), "function", None)
            if llamada_funcion is None:
                continue

            nombre_funcion = llamada_funcion.name
            argumentos = json.loads(llamada_funcion.arguments)

            print(f"[Agente ejecutando herramienta: {nombre_funcion}({argumentos})]")

            try:
                resultado = ejecutar_herramienta(nombre_funcion, argumentos)
            except Exception as error:
                # El error se devuelve como resultado de la tool (no se
                # interrumpe el programa), para que el modelo lo vea y
                # pueda corregirse en la siguiente ronda del for.
                resultado = {"error": str(error)}

            # Registro automático en memoria local, fuera del control del modelo
            guardar_consulta(
                pregunta=mensaje_usuario,
                resultado={
                    "herramienta": nombre_funcion,
                    "argumentos": argumentos,
                    "resultado": resultado,
                },
            )

            historial.append({
                "role": "tool",
                "tool_call_id": llamada.id,
                "content": json.dumps(resultado, ensure_ascii=False),
            })

        # Vuelve a iterar: la siguiente llamada al modelo SIEMPRE incluye
        # 'tools', ya sea para responder en texto o para reintentar.

    # Si se agotaron los intentos sin una respuesta final en texto
    return "No se pudo completar la solicitud tras varios intentos. Revisa los nombres de las herramientas.", historial


if __name__ == "__main__":
    print("=== Agente de Análisis Bursátil ===")
    print("Escribe 'salir' para terminar.\n")

    historial_conversacion = None

    while True:
        entrada = input("Tú: ")
        if entrada.lower() == "salir":
            break

        respuesta, historial_conversacion = chat_agente(entrada, historial_conversacion)
        print(f"\nAgente: {respuesta}\n")