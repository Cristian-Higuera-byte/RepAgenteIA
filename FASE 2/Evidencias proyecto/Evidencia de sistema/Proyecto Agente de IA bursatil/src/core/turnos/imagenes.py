# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara imagenes .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Imágenes que una herramienta guardó en disco, a partir de su resultado (campo 'archivo_guardado')."""
from __future__ import annotations

import json
import os
from typing import Any

# Extensiones de archivo que se consideran imagen mostrable en el chat.
_EXT_IMAGEN = (".png", ".jpg", ".jpeg", ".webp")


def _buscar_rutas_imagen(dato: Any, rutas: list) -> None:
    """Busca de forma recursiva el campo 'archivo_guardado' (imagen en disco) en un resultado."""
    # En un diccionario se revisa su propio campo y luego se desciende a sus valores anidados.
    if isinstance(dato, dict):
        ruta = dato.get("archivo_guardado")
        if isinstance(ruta, str) and ruta.lower().endswith(_EXT_IMAGEN) and os.path.isfile(ruta):
            if ruta not in rutas:
                rutas.append(ruta)
        for valor in dato.values():
            if isinstance(valor, (dict, list)):
                _buscar_rutas_imagen(valor, rutas)
    elif isinstance(dato, list):
        for valor in dato:
            _buscar_rutas_imagen(valor, rutas)


def imagenes_de_resultado(resultado: Any) -> list:
    """Devuelve las rutas de imágenes que una herramienta guardó en disco, a partir de su resultado.

    Recibe el resultado como texto JSON, dict o lista; si no se puede interpretar devuelve [].
    Solo incluye rutas que existan realmente en disco.
    """
    # El resultado de la herramienta suele ser un JSON en texto.
    try:
        datos = json.loads(resultado) if isinstance(resultado, str) else resultado
    except (TypeError, ValueError):
        return []
    rutas: list = []
    _buscar_rutas_imagen(datos, rutas)
    return rutas


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara imagenes .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
