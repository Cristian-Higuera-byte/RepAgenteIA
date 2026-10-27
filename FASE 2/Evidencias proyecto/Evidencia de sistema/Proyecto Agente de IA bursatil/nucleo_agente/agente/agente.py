# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara agente .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Clase Agente: conversación + memoria persistente + bucle de herramientas.

Mantiene el historial de mensajes en formato OpenAI, lo envía al ClienteLLM, guarda cada turno completo
en la memoria (Supabase) y emite EventoAgente a quien lo use. El bucle de herramientas vive en ciclo.py.
Importar `herramientas_agente` registra todas las herramientas disponibles en REGISTRO.
"""
from __future__ import annotations

from typing import Any, Iterator

import configuracion
import herramientas_agente  # noqa: F401  (importarlo registra todas las herramientas)
from herramientas import consumo_ia, cuota_ia, permisos_plan
from nucleo_agente.agente.ciclo import _CicloMixin
from nucleo_agente.agente.eventos import EventoAgente
from nucleo_agente.agente.instrucciones import _prompt_sistema
from nucleo_agente.llm import ClienteLLM
from nucleo_agente.memoria import ErrorMemoria, Memoria
from herramientas_agente.base import REGISTRO, RegistroHerramientas


# TITULO AGENTE

class Agente(_CicloMixin):
    """Agente conversacional con herramientas y memoria opcional por usuario.

    Atributos principales: `llm` (cliente del modelo), `registro` (herramientas disponibles), `memoria`
    (None si no hay usuario o falló Supabase) e `historial` (lista de mensajes; el primero es el prompt de sistema).
    """

    # TITULO INIT

    def __init__(
        self,
        perfil: str | None = None,
        llm: ClienteLLM | None = None,
        registro: RegistroHerramientas = REGISTRO,
        usuario_id: str | None = None,   # None = sin memoria persistente
        continuar: bool = True,          # True = retoma la última conversación del usuario
    ) -> None:
        """Crea el agente y, si hay `usuario_id`, conecta su memoria y carga la conversación previa.

        Recibe el perfil del modelo (None = el de configuracion.py), un cliente LLM ya creado (opcional), el
        registro de herramientas, el id del usuario y si debe retomar su último chat o abrir uno nuevo.
        Si la memoria falla (ErrorMemoria) imprime un aviso y sigue sin memoria en esta sesión.
        """
        self.perfil = perfil                       # None = perfil por defecto de configuracion.py
        self.llm = llm or ClienteLLM(perfil or configuracion.PERFIL_POR_DEFECTO)
        self.registro = registro

        # Memoria persistente (None = desactivada) y texto de contexto que se añade al prompt de sistema.
        self.memoria: Memoria | None = None
        self._contexto = ""
        previo: list[dict[str, Any]] = []
        if usuario_id:
            try:
                # Se retoma el último chat (y su historial reciente) o se abre uno nuevo.
                self.memoria = Memoria(usuario_id)
                if continuar and self.memoria.retomar_ultimo_chat():
                    previo = self.memoria.cargar_historial()
                else:
                    self.memoria.iniciar_chat()
                self._contexto = self.memoria.contexto_previo()
            except ErrorMemoria as e:
                print(f"[Memoria] Desactivada en esta sesión: {e}")
                self.memoria = None
        # El historial siempre empieza con el mensaje de sistema, seguido de los turnos recuperados (si hay).
        self.historial: list[dict[str, Any]] = [{"role": "system", "content": self._prompt()}] + previo

    # ── API pública ───────────────────────────────────────────

    # TITULO REINICIAR

    def reiniciar(self) -> None:
        """Empieza una conversación nueva. La anterior queda guardada en la memoria."""
        # Con memoria: se crea un chat nuevo y se refresca el contexto; si falla solo se avisa.
        if self.memoria:
            try:
                self.memoria.iniciar_chat()
                self._contexto = self.memoria.contexto_previo()
            except ErrorMemoria as e:
                print(f"[Memoria] {e}")
        # El historial vuelve a contener solo el prompt de sistema.
        self.historial = [{"role": "system", "content": self._prompt()}]

    # TITULO PROMPT

    def _prompt(self) -> str:
        """Devuelve el prompt de sistema vigente (fecha de hoy + contexto de memoria del usuario)."""
        return _prompt_sistema(self._contexto)

    # TITULO GUARDAR TURNO

    def _guardar_turno(self, desde: int) -> None:
        """Guarda el turno recién terminado. Si falla, el agente sigue sin memoria."""
        if not self.memoria:
            return
        try:
            self.memoria.guardar_turno(self.historial[desde:])
        except ErrorMemoria as e:
            print(f"[Memoria] No se pudo guardar el turno: {e}")

    # TITULO RESPONDER

    def responder(self, texto: str) -> str:
        """Versión simple: devuelve solo la respuesta final.

        Consume responder_stream() completo y retorna el texto del evento "fin" (cadena vacía si no llegó).
        """
        final = ""
        for evento in self.responder_stream(texto):
            if evento.tipo == "fin":
                final = evento.texto
        return final

    # TITULO RESPONDER STREAM

    def responder_stream(self, texto: str) -> Iterator[EventoAgente]:
        """Procesa un mensaje del usuario y emite EventoAgente a medida que el modelo responde.

        Recibe el texto del usuario. Actualiza el prompt de sistema, añade el mensaje al historial, delega
        en el ciclo de herramientas y, al llegar el evento "fin", guarda el turno en la memoria. Si el turno
        se interrumpe (error o cierre del generador) elimina del historial lo añadido y relanza la excepción.
        """
        # Sin cuota de tokens no se empieza: se avisa antes de tocar el historial (lanza ErrorCuota con el mensaje para el usuario).
        cuota_ia.exigir()
        # El perfil elegido tiene que estar incluido en el plan (el «profundo» usa el modelo avanzado, más caro): si no, se explica en vez de usarlo.
        permitidos = permisos_plan.valor("perfiles_ia")
        if permitidos and self.perfil not in permitidos:
            raise permisos_plan.ErrorPlan(f"El perfil «{self.perfil}» no está incluido en tu plan {permisos_plan.nombre_plan(cuota_ia.plan_actual())}; "
                                          f"usa «{permitidos[-1]}» o cambia a un plan superior.")
        # Se refresca el prompt (la fecha puede haber cambiado) y se marca dónde empieza este turno.
        self.historial[0]["content"] = self._prompt()
        consumo_ia.nuevo_turno()    # las llamadas al modelo de este turno se anotan juntas (costo de IA por turno)
        punto_inicio = len(self.historial)
        self.historial.append({"role": "user", "content": texto})

        # completo = True cuando el ciclo terminó con un evento "fin"; si no, el turno se descarta.
        completo = False
        try:
            for evento in self._ciclo():
                if evento.tipo == "fin":
                    completo = True
                    self._guardar_turno(punto_inicio)
                yield evento
        except BaseException:
            # Un turno a medias (error o cancelación) dejaría llamadas a herramientas
            # sin resultado en el historial y la API rechazaría el siguiente mensaje.
            if not completo:
                del self.historial[punto_inicio:]
            raise


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara agente .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
