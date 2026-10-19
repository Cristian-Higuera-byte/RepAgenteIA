# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara datos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos duraderos del usuario (clave -> valor) y borrado total de su memoria."""
from __future__ import annotations

from core.memoria.cliente import _ahora
from core.memoria.constantes import TABLA_CHATS, TABLA_DATOS
from core.memoria.errores import ErrorMemoria


class _DatosMixin:
    """Mixin de Memoria para los datos duraderos del usuario (tabla agente_memoria_usuario)."""

    def guardar_dato(self, clave: str, valor: str) -> None:
        """Crea o actualiza un dato duradero (ej. 'activos_seguidos' -> 'AAPL, EURUSD')."""
        # La clave se normaliza (minúsculas, sin espacios) para que no haya duplicados por formato.
        clave = clave.strip().lower()
        if not clave or not valor.strip():
            raise ErrorMemoria("clave y valor no pueden estar vacíos.")
        # Upsert por (usuario_id, clave): crea el dato o reemplaza su valor.
        self._ejecutar(
            self._db.table(TABLA_DATOS).upsert(
                {"usuario_id": self.usuario_id, "clave": clave, "valor": valor.strip(), "actualizada_en": _ahora()},
                on_conflict="usuario_id,clave",
            ),
            "guardar el dato",
        )

    def datos_usuario(self) -> dict[str, str]:
        """Devuelve todos los datos duraderos del usuario como diccionario clave -> valor (ordenado por clave)."""
        filas = self._ejecutar(
            self._db.table(TABLA_DATOS).select("clave, valor").eq("usuario_id", self.usuario_id).order("clave"),
            "leer los datos del usuario",
        )
        return {f["clave"]: f["valor"] for f in filas}

    def borrar_dato(self, clave: str) -> None:
        """Borra un dato del usuario por su clave (se normaliza igual que al guardar)."""
        self._ejecutar(
            self._db.table(TABLA_DATOS).delete().eq("usuario_id", self.usuario_id).eq("clave", clave.strip().lower()),
            "borrar el dato",
        )

    def olvidar_todo(self) -> None:
        """Borra TODA la memoria del usuario (conversaciones, mensajes y datos)."""
        # Borrar los chats elimina también sus mensajes (se asume borrado en cascada en la base).
        self._ejecutar(self._db.table(TABLA_CHATS).delete().eq("usuario_id", self.usuario_id), "borrar las conversaciones")
        self._ejecutar(self._db.table(TABLA_DATOS).delete().eq("usuario_id", self.usuario_id), "borrar los datos")
        self.chat_id = None
        self._tiene_titulo = False


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara datos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
