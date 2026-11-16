# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara registro .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Registro de herramientas: la herramienta (esquema + función) y el registro global que usa el agente.

Contiene la dataclass `Herramienta`, la clase `RegistroHerramientas` (alta, listado, esquemas y
ejecución segura) y la instancia global `REGISTRO`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

# Tope de caracteres que una herramienta puede devolver al modelo (protege el contexto).
MAX_CHARS_RESULTADO = 20_000


# TITULO HERRAMIENTA

@dataclass(frozen=True)
class Herramienta:
    """Una herramienta del agente: su nombre, descripción, esquema de argumentos y función a ejecutar.

    Es inmutable (frozen) para que, una vez registrada, nadie cambie el contrato con el modelo.
    """

    nombre: str
    descripcion: str
    parametros: dict[str, Any]        # JSON Schema del objeto de argumentos
    funcion: Callable[..., Any]

    # TITULO ESQUEMA

    def esquema(self) -> dict[str, Any]:
        """Devuelve la herramienta en el formato "function calling" que consume la API del modelo."""
        return {
            "type": "function",
            "function": {
                "name": self.nombre,
                "description": self.descripcion,
                "parameters": self.parametros,
            },
        }


# TITULO A JSON

def _a_json(valor: Any) -> str:
    """Serializa cualquier valor a JSON sin escapar tildes; lo no serializable (fechas, etc.) se pasa a str."""
    return json.dumps(valor, ensure_ascii=False, default=str)


# TITULO REGISTRO HERRAMIENTAS

class RegistroHerramientas:
    """Colección de herramientas por nombre, con ejecución segura que nunca propaga excepciones."""

    # TITULO INIT

    def __init__(self) -> None:
        """Crea un registro vacío."""
        # Mapa nombre -> Herramienta, en orden de registro.
        self._herramientas: dict[str, Herramienta] = {}

    # TITULO REGISTRAR

    def registrar(self, herramienta: Herramienta) -> None:
        """Añade una herramienta; lanza ValueError si el nombre ya estaba registrado."""
        if herramienta.nombre in self._herramientas:
            raise ValueError(f"Herramienta duplicada: {herramienta.nombre}")
        self._herramientas[herramienta.nombre] = herramienta

    # TITULO NOMBRES

    def nombres(self) -> list[str]:
        """Devuelve la lista de nombres de herramientas registradas."""
        return list(self._herramientas)

    # TITULO ESQUEMAS

    def esquemas(self) -> list[dict[str, Any]]:
        """Devuelve los esquemas de todas las herramientas, listos para enviarse al modelo."""
        return [h.esquema() for h in self._herramientas.values()]

    # TITULO EJECUTAR

    def ejecutar(self, nombre: str, argumentos: dict[str, Any]) -> str:
        """Ejecuta una herramienta y SIEMPRE devuelve un string JSON (nunca lanza)."""
        # 1. Buscar la herramienta; si no existe se informa al modelo cuáles hay disponibles.
        herramienta = self._herramientas.get(nombre)
        if herramienta is None:
            return _a_json({"error": f"Herramienta desconocida: {nombre}", "disponibles": self.nombres()})

        # 2. Ejecutar con los argumentos del modelo; cualquier excepción se devuelve como {"error": ...}.
        try:
            resultado = herramienta.funcion(**argumentos)
        except Exception as e:  # noqa: BLE001 - el error se le devuelve al modelo
            return _a_json({"error": f"{type(e).__name__}: {e}"})

        # 3. Serializar y proteger el contexto: si excede el tope se devuelve solo el inicio con un aviso.
        texto = _a_json(resultado)
        if len(texto) > MAX_CHARS_RESULTADO:
            return _a_json(
                {
                    "truncado": True,
                    "aviso": "Resultado demasiado largo; se muestra solo el inicio. Pide un rango o filtro más acotado.",
                    "contenido_parcial": texto[:MAX_CHARS_RESULTADO],
                }
            )
        return texto


# Registro global usado por el agente.
REGISTRO = RegistroHerramientas()


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara registro .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
