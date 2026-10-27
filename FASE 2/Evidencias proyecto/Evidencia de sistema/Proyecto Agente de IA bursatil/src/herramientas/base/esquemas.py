# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara esquemas .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Carga de los esquemas de herramientas guardados en esquemas.json / datos.json de cada paquete.

Mantiene las descripciones y parámetros que ve el modelo fuera del código Python, en archivos JSON.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def cargar_json(ruta: str | Path) -> Any:
    """Lee un archivo JSON y devuelve su contenido ya convertido a objetos Python.

    Recibe `ruta` (str o Path) del archivo, que se lee como UTF-8. Los esquemas se pasan tal cual a
    `@herramienta(**esquema)`. Efecto secundario: lectura de disco; lanza error si falta o es inválido.
    """
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara esquemas .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
