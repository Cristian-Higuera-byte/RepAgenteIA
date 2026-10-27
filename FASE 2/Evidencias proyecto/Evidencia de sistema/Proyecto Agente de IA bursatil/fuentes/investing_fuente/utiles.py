# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara utiles .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Utilidades de limpieza de los textos de las noticias.

Funciones puras (sin red ni estado) que normalizan los resúmenes del RSS y
descartan campos vacíos antes de devolver los datos."""
from __future__ import annotations

import re
from typing import Any


# TITULO LIMPIAR HTML

def _limpiar_html(texto: str) -> str:
    """Elimina etiquetas HTML e inconsistencias de formato en los resúmenes.

    Recibe el texto crudo de la descripción del RSS (puede traer etiquetas y
    espacios o saltos de línea repetidos). Devuelve el texto plano con los
    espacios colapsados a uno solo; si el texto viene vacío devuelve ''."""
    if not texto:
        return ""
    # Quita cualquier etiqueta del tipo <...> sin interpretar entidades HTML.
    sin_html = re.sub(r"<[^>]+>", "", texto)
    # split() sin argumentos descarta saltos y espacios múltiples; join los une con un espacio.
    return " ".join(sin_html.split()).strip()


# TITULO SIN NULOS

def _sin_nulos(d: dict[str, Any]) -> dict[str, Any]:
    """Devuelve una copia del diccionario sin las claves cuyo valor es None.

    Se usa para no enviar campos vacíos al modelo y ahorrar contexto. Los
    valores falsos distintos de None (0, '', listas vacías) se conservan."""
    return {k: v for k, v in d.items() if v is not None}


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara utiles .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
