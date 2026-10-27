# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara ciclo .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Bucle de herramientas del agente: el modelo responde, pide herramientas, se ejecutan y se repite."""
from __future__ import annotations

import json
from typing import Iterator

import configuracion
from core.agente.eventos import EventoAgente


class _CicloMixin:
    """Mixin con el bucle de herramientas; espera que la clase tenga `llm`, `registro`, `historial` y `perfil`."""

    def _ciclo(self) -> Iterator[EventoAgente]:
        """Ejecuta el bucle modelo -> herramientas -> modelo hasta obtener una respuesta final.

        Emite eventos de razonamiento y texto en vivo, uno "herramienta" y uno "resultado" por cada llamada,
        y un "fin" con los tokens acumulados y el perfil. Añade al historial cada mensaje del asistente y cada
        resultado de herramienta. Si se agota MAX_ITERACIONES_HERRAMIENTAS pide una última respuesta sin
        herramientas. Lanza RuntimeError si el LLM no entrega respuesta final.
        """
        # Esquemas de herramientas para el modelo (None si no hay ninguna) y acumuladores de tokens del turno.
        esquemas = self.registro.esquemas() or None
        tokens = {"tokens_entrada": 0, "tokens_salida": 0}

        # Cada vuelta del bucle es una llamada al modelo; el tope evita ciclos infinitos de herramientas.
        for _ in range(configuracion.MAX_ITERACIONES_HERRAMIENTAS):
            final = None
            # Se retransmite el streaming al llamador y se captura la respuesta final ensamblada.
            for ev in self.llm.chat_stream(self.historial, esquemas, self.perfil):
                if ev.tipo == "final":
                    final = ev.respuesta
                else:
                    yield EventoAgente(ev.tipo, ev.texto)

            if final is None:
                raise RuntimeError("El LLM no devolvió una respuesta final para este turno.")

            tokens["tokens_entrada"] += final.tokens_entrada
            tokens["tokens_salida"] += final.tokens_salida
            # El mensaje del asistente (con reasoning_content y tool_calls) debe quedar en el historial.
            self.historial.append(final.mensaje)

            # Sin llamadas a herramientas el modelo ya contestó: se termina el turno.
            if not final.llamadas:
                yield EventoAgente("fin", final.contenido, {**tokens, "perfil": final.perfil})
                return

            # Se ejecuta cada herramienta pedida; un JSON inválido se devuelve al modelo como error.
            for llamada in final.llamadas:
                yield EventoAgente("herramienta", llamada.nombre, llamada.argumentos)
                if llamada.error:
                    resultado = json.dumps({"error": llamada.error}, ensure_ascii=False)
                else:
                    resultado = self.registro.ejecutar(llamada.nombre, llamada.argumentos)
                # El resultado se añade como mensaje "tool" enlazado por tool_call_id.
                self.historial.append(
                    {"role": "tool", "tool_call_id": llamada.id, "content": resultado}
                )
                yield EventoAgente("resultado", llamada.nombre, {"resultado": resultado})

        # Se alcanzó el tope de ciclos: se pide una respuesta final sin más herramientas.
        self.historial.append(
            {
                "role": "user",
                "content": (
                    "Alcanzaste el límite de consultas a herramientas. Responde ahora con la "
                    "información que ya tienes e indica qué te faltó."
                ),
            }
        )
        final = self.llm.chat(self.historial, None, self.perfil)
        tokens["tokens_entrada"] += final.tokens_entrada
        tokens["tokens_salida"] += final.tokens_salida
        self.historial.append(final.mensaje)
        yield EventoAgente("texto", final.contenido)
        yield EventoAgente("fin", final.contenido, {**tokens, "perfil": final.perfil})


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara ciclo .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
