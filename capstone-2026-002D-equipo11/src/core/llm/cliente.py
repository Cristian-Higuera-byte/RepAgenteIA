# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara cliente .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Cliente de DeepSeek (API compatible con OpenAI): llamada completa y streaming."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from openai import OpenAI

import configuracion  # type: ignore[import-not-found]
from core.llm.errores import traducir_error
from core.llm.peticion import construir_kwargs
from core.llm.respuesta import construir_respuesta
from core.llm.tipos import EventoStream, RespuestaLLM


class ClienteLLM:
    """Cliente del modelo de DeepSeek (API compatible con OpenAI) con llamada completa y streaming.

    Es el único punto del agente que habla con el proveedor: traduce errores a ErrorLLM y devuelve
    RespuestaLLM / EventoStream ya ensamblados.
    """

    def __init__(self, perfil: str = configuracion.PERFIL_POR_DEFECTO):
        """Crea el cliente para un perfil de configuracion.PERFILES.

        Valida la configuración (clave de API), comprueba que el perfil exista (ValueError si no) y crea
        el cliente OpenAI con la URL base, el timeout y los reintentos definidos en configuracion.py.
        """
        configuracion.validar_configuracion()
        if perfil not in configuracion.PERFILES:
            raise ValueError(f"Perfil desconocido: {perfil!r}. Disponibles: {list(configuracion.PERFILES)}")
        self.perfil_por_defecto = perfil
        self._cliente = OpenAI(
            api_key=configuracion.DEEPSEEK_API_KEY,
            base_url=configuracion.DEEPSEEK_BASE_URL,
            timeout=configuracion.TIMEOUT_LLM_SEG,
            max_retries=configuracion.REINTENTOS_LLM,
        )

    # ── API pública ───────────────────────────────────────────

    def chat(
        self,
        mensajes: list[dict[str, Any]],
        herramientas: list[dict[str, Any]] | None = None,
        perfil: str | None = None,
    ) -> RespuestaLLM:
        """Una llamada completa (sin streaming).

        Recibe los mensajes del historial, los esquemas de herramientas (opcional) y el perfil (por defecto
        el del cliente). Devuelve la RespuestaLLM. Lanza ErrorLLM si la API falla.
        """
        nombre = perfil or self.perfil_por_defecto
        # Llamada bloqueante a la API; cualquier fallo se traduce a un ErrorLLM legible.
        try:
            r = self._cliente.chat.completions.create(
                **construir_kwargs(nombre, mensajes, herramientas, stream=False)
            )
        except Exception as e:
            raise traducir_error(e) from e

        # Se extrae el mensaje y se normalizan las llamadas a herramientas al formato interno.
        msg = r.choices[0].message
        llamadas_raw = [
            {"id": tc.id, "nombre": tc.function.name, "args": tc.function.arguments or ""}
            for tc in (msg.tool_calls or [])
        ]
        return construir_respuesta(
            nombre,
            contenido=msg.content or "",
            razonamiento=getattr(msg, "reasoning_content", None),
            llamadas_raw=llamadas_raw,
            usage=r.usage,
        )

    def chat_stream(
        self,
        mensajes: list[dict[str, Any]],
        herramientas: list[dict[str, Any]] | None = None,
        perfil: str | None = None,
    ) -> Iterator[EventoStream]:
        """Igual que chat() pero emite eventos a medida que llegan.

        Pensado para el chat del dashboard: 'texto' se muestra en vivo y el
        último evento ('final') trae la respuesta completa con las llamadas
        a herramientas ya ensambladas. Eventos: 'razonamiento', 'texto' y 'final'.
        Lanza ErrorLLM si la API falla.
        """
        nombre = perfil or self.perfil_por_defecto
        # Acumuladores: texto, razonamiento y llamadas a herramientas (por índice, llegan en fragmentos).
        contenido: list[str] = []
        razon: list[str] = []
        llamadas: dict[int, dict[str, str]] = {}
        usage = None

        # Se pide la respuesta en streaming y se procesa fragmento a fragmento.
        try:
            stream = self._cliente.chat.completions.create(
                **construir_kwargs(nombre, mensajes, herramientas, stream=True)
            )
            for chunk in stream:
                # El último fragmento trae el uso de tokens (stream_options include_usage).
                if getattr(chunk, "usage", None):
                    usage = chunk.usage
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                # Razonamiento (thinking): se acumula y se emite en vivo.
                r = getattr(delta, "reasoning_content", None)
                if r:
                    razon.append(r)
                    yield EventoStream("razonamiento", r)

                # Texto de la respuesta: se acumula y se emite en vivo.
                if delta.content:
                    contenido.append(delta.content)
                    yield EventoStream("texto", delta.content)

                # Las llamadas a herramientas llegan troceadas: se ensamblan por índice (id, nombre, argumentos).
                for tc in delta.tool_calls or []:
                    c = llamadas.setdefault(tc.index, {"id": "", "nombre": "", "args": ""})
                    if tc.id:
                        c["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            c["nombre"] = tc.function.name
                        if tc.function.arguments:
                            c["args"] += tc.function.arguments
        except Exception as e:
            raise traducir_error(e) from e

        # Terminado el stream, se arma la respuesta completa y se emite como evento final.
        respuesta = construir_respuesta(
            nombre,
            contenido="".join(contenido),
            razonamiento="".join(razon) if razon else None,
            llamadas_raw=[llamadas[i] for i in sorted(llamadas)],
            usage=usage,
        )
        yield EventoStream("final", respuesta=respuesta)

    # ── Internos ──────────────────────────────────────────────

    @staticmethod
    def _traducir_error(e: Exception):
        """Atajo estático a errores.traducir_error (se conserva por compatibilidad)."""
        return traducir_error(e)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara cliente .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
