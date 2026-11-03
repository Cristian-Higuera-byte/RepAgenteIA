# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara turno .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Un turno del agente: estado compartido entre el hilo que corre al agente y la interfaz que lo consulta."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from nucleo_agente.turnos.formato import formatear_duracion

# Segundos de margen para considerar que el usuario está viendo el turno (ver turnos/avisos.py).
VISTA_RECIENTE_S = 2.0   # la interfaz late cada 1 s: si lo mostró hace menos de esto, el usuario lo está viendo


# TITULO TURNO

@dataclass
class Turno:
    """Estado de una consulta al agente, compartido entre el hilo que la ejecuta y la interfaz que la consulta."""

    usuario_id: str
    prompt: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    terminado: bool = False
    recogido: bool = False           # la interfaz ya incorporó el resultado al chat
    fase: str = "Pensando…"          # texto corto de lo que está haciendo ahora mismo
    texto: str = ""                  # respuesta acumulada (se va llenando mientras llega)
    herramientas: list = field(default_factory=list)
    imagenes: list = field(default_factory=list)
    hubo_orden: bool = False         # el agente llamó a proponer_orden / proponer_cierre_posicion
    hubo_vigilancia: bool = False    # el agente preparó una vigilancia automática (pendiente de autorizar)
    error: str = ""
    tokens_entrada: Any = "?"
    tokens_salida: Any = "?"
    perfil: Any = "?"
    cuota: str = ""                  # uso de tokens del mes al terminar el turno (para el pie del mensaje)
    t_inicio: float = field(default_factory=time.time)
    t_fin: float | None = None
    ui_viva: float = 0.0             # última vez que la interfaz estaba mostrando este turno
    cancelar_solicitado: bool = False  # el usuario pulsó "Detener" (el hilo aún puede estar terminando)
    cancelado: bool = False          # el turno se interrumpió de verdad antes de terminar solo

    # TITULO DURACION

    @property
    def duracion(self) -> float:
        """Segundos transcurridos desde el inicio hasta el fin (o hasta ahora si sigue en curso)."""
        return (self.t_fin or time.time()) - self.t_inicio

    # TITULO PIE

    @property
    def pie(self) -> str:
        """Texto del pie del mensaje: duración, tokens, perfil y uso del mes, o aviso de consulta detenida."""
        if self.cancelado:
            return f"⏹ Detenida a los {formatear_duracion(self.duracion)}"
        base = (f"⏱ {formatear_duracion(self.duracion)} · {self.tokens_entrada} entrada / "
                f"{self.tokens_salida} salida | perfil: {self.perfil}")
        return f"{base} | {self.cuota}" if self.cuota else base

    # TITULO RESPUESTA FINAL

    def respuesta_final(self) -> str:
        """Texto que se guarda en el chat al terminar el turno.

        Si se canceló, agrega una nota (y recuerda revisar órdenes/vigilancias ya propuestas); si hubo error lo
        añade al final; si no hubo texto devuelve un mensaje de relleno.
        """
        texto = self.texto
        if self.cancelado:
            nota = "⏹ **Consulta detenida por el usuario.**"
            if self.hubo_orden:
                nota += (" El agente ya había propuesto una orden: revísala en «Órdenes propuestas» y "
                         "confírmala o recházala.")
            if self.hubo_vigilancia:
                nota += (" El agente ya había preparado una vigilancia automática: autorízala o recházala en "
                         "«Órdenes propuestas».")
            return f"{texto.rstrip()}\n\n{nota}" if texto.strip() else nota
        if self.error:
            texto += f"\n\n⚠️ {self.error}"
        if not texto.strip():
            texto = "(Sin texto adicional del agente.)" if self.imagenes else "(El agente no devolvió texto.)"
        return texto


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara turno .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
