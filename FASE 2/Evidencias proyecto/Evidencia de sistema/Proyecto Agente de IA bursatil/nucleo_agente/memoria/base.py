# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara base .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Base de la clase Memoria: usuario, cliente de Supabase y utilidades internas.

Los mixins de conversaciones, datos y contexto se apoyan en lo que define _BaseMemoria.
"""
from __future__ import annotations

from typing import Any

from nucleo_agente.memoria.cliente import _obtener_cliente
from nucleo_agente.memoria.constantes import TABLA_MENSAJES
from nucleo_agente.memoria.errores import ErrorMemoria


# TITULO BASE MEMORIA

class _BaseMemoria:
    """Estado común de la memoria: usuario, chat activo y acceso perezoso al cliente de Supabase."""

    # TITULO INIT

    def __init__(self, usuario_id: str, cliente: Any = None) -> None:
        """Guarda el usuario (obligatorio, ErrorMemoria si está vacío) y opcionalmente un cliente ya creado.

        `cliente` permite inyectar un doble en pruebas; con None se crea al primer uso (ver `_db`).
        """
        if not usuario_id or not str(usuario_id).strip():
            raise ErrorMemoria("Se necesita un usuario_id para usar la memoria.")
        self.usuario_id = str(usuario_id).strip()
        # Conversación activa (None hasta iniciar o retomar una) y si ya tiene título asignado.
        self.chat_id: str | None = None
        self._tiene_titulo = False
        self._cli = cliente  # None = se crea al primer uso

    # ── Interno ───────────────────────────────────────────────

    # TITULO DB

    @property
    def _db(self) -> Any:
        """Cliente de Supabase de esta memoria; se crea al primer acceso."""
        if self._cli is None:
            self._cli = _obtener_cliente()
        return self._cli

    # TITULO EJECUTAR

    @staticmethod
    def _ejecutar(consulta: Any, accion: str) -> list[dict[str, Any]]:
        """Ejecuta una consulta de Supabase y devuelve sus filas ([] si no hay datos).

        `accion` describe la operación en infinitivo para el mensaje de error; cualquier excepción se
        convierte en ErrorMemoria.
        """
        try:
            return consulta.execute().data or []
        except Exception as e:  # noqa: BLE001
            raise ErrorMemoria(f"Supabase falló al {accion}: {e}") from e

    # TITULO ULTIMO REGISTRO

    def _ultimo_registro(self) -> dict[str, Any] | None:
        """Devuelve el turno y orden del último mensaje del chat activo, o None si no tiene mensajes."""
        filas = self._ejecutar(
            self._db.table(TABLA_MENSAJES)
            .select("turno, orden")
            .eq("chat_id", self.chat_id)
            .order("orden", desc=True)
            .limit(1),
            "leer el último mensaje",
        )
        return filas[0] if filas else None

    # TITULO TITULO DESDE

    @staticmethod
    def _titulo_desde(mensajes: list[dict[str, Any]]) -> str | None:
        """Genera el título de un chat desde el primer mensaje del usuario (máx. 60 caracteres)."""
        for m in mensajes:
            if m.get("role") == "user" and m.get("content"):
                texto = " ".join(str(m["content"]).split())
                return texto[:60] + ("…" if len(texto) > 60 else "")
        return None


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara base .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
