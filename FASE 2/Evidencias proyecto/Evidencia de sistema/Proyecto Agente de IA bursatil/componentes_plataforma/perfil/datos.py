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

"""Datos constantes del perfil de usuario: listas de opciones, secciones y campos (cargados de datos.json).

Lo usan panel.py y secciones.py para dibujar los formularios, y validacion.py para calcular el porcentaje de perfil completo.
"""
from pathlib import Path
from typing import Any

from componentes_plataforma._estaticos import datos_json

# Contenido completo de datos.json (listas de opciones, secciones con sus campos y campos requeridos).
_D: dict[str, Any] = datos_json(Path(__file__).parent / "datos.json")

# Secciones del perfil en el orden en que se muestran: id, título, ícono Material, descripción y campos.
SECCIONES: list[dict[str, Any]] = _D["secciones"]
# Campos que cuentan para el porcentaje de perfil completo.
REQUERIDOS: list[str] = _D["requeridos_completitud"]
# Prefijo telefónico por código de país (CL -> +56), para el campo de celular.
PREFIJOS: dict[str, str] = {p["id"]: p["prefijo"] for p in _D["paises"]}


# TITULO OPCIONES

def opciones(nombre: str) -> list[tuple[str, str]]:
    """Devuelve la lista de opciones `nombre` (p. ej. "paises") como pares (id, texto visible), en el orden del archivo."""
    return [(o["id"], o["nombre"]) for o in _D[nombre]]


# TITULO NOMBRE DE

def nombre_de(lista: str, id_: Any) -> str:
    """Texto visible de una opción guardada (el id si no se encuentra, vacío si no hay valor)."""
    if not id_:
        return ""
    return dict(opciones(lista)).get(id_, str(id_))


# TITULO SECCION

def seccion(id_: str) -> dict[str, Any]:
    """Devuelve la sección con ese id (la primera si el id no existe)."""
    return next((s for s in SECCIONES if s["id"] == id_), SECCIONES[0])


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
