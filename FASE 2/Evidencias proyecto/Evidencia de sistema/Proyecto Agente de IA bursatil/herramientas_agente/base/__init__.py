# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Registro de herramientas del agente.

Cada herramienta es una función Python normal, decorada con @herramienta.
El agente no conoce ninguna herramienta en particular: solo pide al registro
sus esquemas (para enviarlos al modelo) y le pasa las llamadas a ejecutar().

Reglas para escribir herramientas:
  * Devolver datos serializables a JSON (dict, list, str, números).
  * Si algo falla, basta con lanzar una excepción: el registro la convierte en
    {"error": ...} para que el modelo pueda corregir o explicarlo al usuario.

Archivos: registro.py (Herramienta, RegistroHerramientas, REGISTRO), decorador.py (@herramienta) y esquemas.py
(cargar_json: lee el esquemas.json de cada paquete de herramientas).

Este __init__ es una fachada: reexporta la API pública (herramienta, cargar_json, REGISTRO,
Herramienta, RegistroHerramientas, MAX_CHARS_RESULTADO y _a_json) para que el resto del código
importe todo desde `herramientas_agente.base` sin conocer en qué archivo vive cada pieza.
"""
from herramientas_agente.base.decorador import herramienta
from herramientas_agente.base.esquemas import cargar_json
# _a_json se reexporta aunque sea privado porque otros módulos del agente lo usan para serializar.
from herramientas_agente.base.registro import (  # noqa: F401
    MAX_CHARS_RESULTADO,
    REGISTRO,
    Herramienta,
    RegistroHerramientas,
    _a_json,
)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
