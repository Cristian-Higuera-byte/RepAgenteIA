"""Registro de herramientas del agente.

Cada herramienta es una función Python normal, decorada con @herramienta.
El agente no conoce ninguna herramienta en particular: solo pide al registro
sus esquemas (para enviarlos al modelo) y le pasa las llamadas a ejecutar().

Reglas para escribir herramientas:
  * Devolver datos serializables a JSON (dict, list, str, números).
  * Si algo falla, basta con lanzar una excepción: el registro la convierte en
    {"error": ...} para que el modelo pueda corregir o explicarlo al usuario.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

# Tope de caracteres que una herramienta puede devolver al modelo (protege el contexto).
MAX_CHARS_RESULTADO = 20_000


@dataclass(frozen=True)
class Herramienta:
    nombre: str
    descripcion: str
    parametros: dict[str, Any]        # JSON Schema del objeto de argumentos
    funcion: Callable[..., Any]

    def esquema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.nombre,
                "description": self.descripcion,
                "parameters": self.parametros,
            },
        }


def _a_json(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, default=str)


class RegistroHerramientas:
    def __init__(self) -> None:
        self._herramientas: dict[str, Herramienta] = {}

    def registrar(self, herramienta: Herramienta) -> None:
        if herramienta.nombre in self._herramientas:
            raise ValueError(f"Herramienta duplicada: {herramienta.nombre}")
        self._herramientas[herramienta.nombre] = herramienta

    def nombres(self) -> list[str]:
        return list(self._herramientas)

    def esquemas(self) -> list[dict[str, Any]]:
        return [h.esquema() for h in self._herramientas.values()]

    def ejecutar(self, nombre: str, argumentos: dict[str, Any]) -> str:
        """Ejecuta una herramienta y SIEMPRE devuelve un string JSON (nunca lanza)."""
        herramienta = self._herramientas.get(nombre)
        if herramienta is None:
            return _a_json({"error": f"Herramienta desconocida: {nombre}", "disponibles": self.nombres()})

        try:
            resultado = herramienta.funcion(**argumentos)
        except Exception as e:  # noqa: BLE001 - el error se le devuelve al modelo
            return _a_json({"error": f"{type(e).__name__}: {e}"})

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


def herramienta(
    descripcion: str,
    parametros: dict[str, Any] | None = None,
    requeridos: list[str] | None = None,
    nombre: str | None = None,
    registro: RegistroHerramientas = REGISTRO,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorador que registra una función como herramienta del agente."""

    def decorador(funcion: Callable[..., Any]) -> Callable[..., Any]:
        esquema = {
            "type": "object",
            "properties": parametros or {},
            "required": requeridos or [],
        }
        registro.registrar(Herramienta(nombre or funcion.__name__, descripcion, esquema, funcion))
        return funcion

    return decorador