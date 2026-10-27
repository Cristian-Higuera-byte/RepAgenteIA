# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara conversaciones .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Conversaciones: crear, retomar, listar, cargar el historial, guardar turnos y resúmenes, eliminar."""
from __future__ import annotations

from typing import Any

from core.memoria.cliente import _ahora
from core.memoria.constantes import MAX_TURNOS_CARGADOS, TABLA_CHATS, TABLA_MENSAJES
from core.memoria.errores import ErrorMemoria
from core.memoria.validacion import _sanear, _turno_valido


class _ConversacionesMixin:
    """Mixin de Memoria para las conversaciones; usa `_ejecutar`, `_db`, `chat_id` y `usuario_id` de la base."""

    def iniciar_chat(self) -> str:
        """Crea una conversación nueva y la deja como activa."""
        # Inserta el chat vacío del usuario y toma el id generado por Supabase.
        filas = self._ejecutar(
            self._db.table(TABLA_CHATS).insert({"usuario_id": self.usuario_id}),
            "crear la conversación",
        )
        if not filas:
            raise ErrorMemoria("Supabase no devolvió la conversación creada.")
        self.chat_id = filas[0]["id"]
        self._tiene_titulo = False
        if self.chat_id is None:
            raise ErrorMemoria("La conversación creada no tiene id válido.")
        return self.chat_id

    def retomar_ultimo_chat(self) -> bool:
        """Activa la conversación más reciente del usuario. False si no tiene ninguna."""
        filas = self._ejecutar(
            self._db.table(TABLA_CHATS)
            .select("id, titulo")
            .eq("usuario_id", self.usuario_id)
            .order("actualizada_en", desc=True)
            .limit(1),
            "buscar la última conversación",
        )
        if not filas:
            return False
        self.chat_id = filas[0]["id"]
        self._tiene_titulo = bool(filas[0].get("titulo"))
        return True

    def listar_chats(self, limite: int = 20) -> list[dict[str, Any]]:
        """Conversaciones del usuario, la más reciente primero (id, titulo, resumen, fechas)."""
        return self._ejecutar(
            self._db.table(TABLA_CHATS)
            .select("id, titulo, resumen, creada_en, actualizada_en")
            .eq("usuario_id", self.usuario_id)
            .order("actualizada_en", desc=True)
            .limit(limite),
            "listar las conversaciones",
        )

    def cargar_historial(self, max_turnos: int = MAX_TURNOS_CARGADOS) -> list[dict[str, Any]]:
        """Últimos turnos COMPLETOS del chat activo, listos para enviar al modelo."""
        if not self.chat_id:
            return []
        # El último turno guardado define desde cuál empezar a leer (los últimos max_turnos).
        ultimo = self._ultimo_registro()
        if ultimo is None:
            return []
        desde = max(1, ultimo["turno"] - max_turnos + 1)
        filas = self._ejecutar(
            self._db.table(TABLA_MENSAJES)
            .select("mensaje")
            .eq("chat_id", self.chat_id)
            .gte("turno", desde)
            .order("orden"),
            "cargar el historial",
        )
        return _sanear([f["mensaje"] for f in filas])

    def guardar_turno(self, mensajes: list[dict[str, Any]]) -> None:
        """Guarda un turno completo (user, assistant, tool..., assistant final) en una sola inserción."""
        if not mensajes:
            return
        # Se rechaza un turno que no empiece en "user" o tenga llamadas a herramientas sin resultado.
        if mensajes[0].get("role") != "user" or not _turno_valido(mensajes):
            raise ErrorMemoria("El turno es inconsistente (tool_calls sin resultado o similar); no se guarda.")
        if not self.chat_id:
            self.iniciar_chat()

        # Numeración: el turno y el orden continúan desde el último registro del chat.
        ultimo = self._ultimo_registro()
        turno = ultimo["turno"] + 1 if ultimo else 1
        orden = ultimo["orden"] + 1 if ultimo else 1
        filas = [
            {"chat_id": self.chat_id, "turno": turno, "orden": orden + i, "mensaje": m}
            for i, m in enumerate(mensajes)
        ]
        # Todas las filas del turno van en una sola inserción (todo o nada).
        self._ejecutar(self._db.table(TABLA_MENSAJES).insert(filas), "guardar el turno")

        # Se actualiza la fecha del chat y, si aún no tiene, su título (tomado del primer mensaje).
        cambios: dict[str, Any] = {"actualizada_en": _ahora()}
        titulo = None if self._tiene_titulo else self._titulo_desde(mensajes)
        if titulo:
            cambios["titulo"] = titulo
        self._ejecutar(
            self._db.table(TABLA_CHATS).update(cambios).eq("id", self.chat_id).eq("usuario_id", self.usuario_id),
            "actualizar la conversación",
        )
        if titulo:
            self._tiene_titulo = True

    def guardar_resumen(self, resumen: str, chat_id: str | None = None) -> None:
        """Guarda el resumen de una conversación (por defecto la activa)."""
        objetivo = chat_id or self.chat_id
        if not objetivo:
            raise ErrorMemoria("No hay conversación para guardar el resumen.")
        self._ejecutar(
            self._db.table(TABLA_CHATS)
            .update({"resumen": resumen.strip()})
            .eq("id", objetivo)
            .eq("usuario_id", self.usuario_id),
            "guardar el resumen",
        )

    def eliminar_chat(self, chat_id: str) -> None:
        """Borra una conversación y todos sus mensajes."""
        self._ejecutar(
            self._db.table(TABLA_CHATS).delete().eq("id", chat_id).eq("usuario_id", self.usuario_id),
            "eliminar la conversación",
        )
        if chat_id == self.chat_id:
            self.chat_id = None
            self._tiene_titulo = False


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara conversaciones .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
