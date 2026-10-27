# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara decorador .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Decorador @herramienta: registra una función Python como herramienta del agente.

Convierte los metadatos entregados (descripción, parámetros, requeridos) en un esquema JSON Schema
y registra la función en el registro global, sin modificarla (la función sigue siendo invocable normal).
"""
from __future__ import annotations

from typing import Any, Callable

from herramientas.base.registro import REGISTRO, Herramienta, RegistroHerramientas


def herramienta(
    descripcion: str,
    parametros: dict[str, Any] | None = None,
    requeridos: list[str] | None = None,
    nombre: str | None = None,
    registro: RegistroHerramientas = REGISTRO,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Crea el decorador que registra una función como herramienta del agente.

    Recibe `descripcion` (texto que lee el modelo), `parametros` (propiedades JSON Schema de los
    argumentos), `requeridos` (nombres de argumentos obligatorios), `nombre` (por defecto, el de la
    función; es el contrato con el modelo) y `registro` (por defecto, el global `REGISTRO`).
    Devuelve el decorador propiamente dicho. Normalmente se usa como `@herramienta(**_ESQ["nombre"])`.
    """

    def decorador(funcion: Callable[..., Any]) -> Callable[..., Any]:
        """Registra `funcion` en el registro y la devuelve sin cambios.

        Efecto secundario: lanza ValueError si ya existe una herramienta con el mismo nombre.
        """
        # Esquema del objeto de argumentos en formato JSON Schema (lo que espera la API del modelo).
        esquema = {
            "type": "object",
            "properties": parametros or {},
            "required": requeridos or [],
        }
        # Se crea la Herramienta (nombre explícito o el de la función) y se inscribe en el registro.
        registro.registrar(Herramienta(nombre or funcion.__name__, descripcion, esquema, funcion))
        return funcion

    return decorador


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara decorador .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
