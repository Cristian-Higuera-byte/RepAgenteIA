# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara ensamblador .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Arma el HTML del gráfico a partir de los fragmentos de `estatico/`.

`estatico/esqueleto.html` es el documento completo; cada línea `@@ruta` se reemplaza por el contenido de
ese fragmento (css/, html/ o js/). Todos los fragmentos de JS comparten UN mismo bloque (la función
`iniciar()`), por eso el orden del esqueleto importa: no cambies el orden de los `@@js/...` sin probar.

El resultado se guarda en memoria y se rehace solo si algún fragmento cambia en disco.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

from components._estaticos import sin_creditos

# Carpeta con esqueleto.html y los fragmentos css/, html/ y js/.
_DIR = Path(__file__).parent / "estatico"
# Una línea completa "@@ruta" del esqueleto: el grupo 1 es la ruta relativa del fragmento a incluir.
_INCLUIR = re.compile(r"^@@(\S+)\n", re.MULTILINE)
# Caché en memoria: firma = (ruta, fecha de modificación) de todos los archivos; plantilla = HTML ya ensamblado.
_cache: dict = {"firma": None, "plantilla": ""}


def _firma() -> tuple:
    """Devuelve una tupla (ruta, mtime) de todos los archivos de estatico/, usada para detectar cambios en disco."""
    return tuple((str(p), p.stat().st_mtime_ns) for p in sorted(_DIR.rglob("*")) if p.is_file())


def plantilla() -> str:
    """HTML completo del gráfico, con los marcadores __X__ todavía sin sustituir.

    Lee el esqueleto, reemplaza cada línea `@@ruta` por el contenido del fragmento (quitando el bloque de créditos
    con `sin_creditos`) y guarda el resultado en caché. Solo se rehace cuando cambia la firma de los archivos.
    """
    # Si ningún archivo cambió desde la última vez, se reutiliza el resultado guardado.
    firma = _firma()
    if _cache["firma"] != firma:
        # Esqueleto limpio de créditos y expansión de cada inclusión.
        esqueleto = sin_creditos((_DIR / "esqueleto.html").read_text(encoding="utf-8"))
        _cache["plantilla"] = _INCLUIR.sub(lambda m: sin_creditos((_DIR / m.group(1)).read_text(encoding="utf-8")), esqueleto)
        _cache["firma"] = firma
    return _cache["plantilla"]


def html_grafico(simbolo: str, api_url: str, digits: int, pip: float, posiciones_js: str, activos_json: str = "[]") -> str:
    """HTML listo para `components.html` con los datos del símbolo.

    Recibe el símbolo, la URL de la API de velas, los decimales, el tamaño del pip, el JS de posiciones y el JSON
    de activos del selector. Devuelve la plantilla con cada marcador `__X__` sustituido (texto escapado para HTML
    o serializado como JSON para JS según corresponda).
    """
    return (
        plantilla()
        .replace("__SIMBOLO_HTML__", escape(simbolo))
        .replace("__SIMBOLO_JS__", json.dumps(simbolo))
        .replace("__API_URL_JS__", json.dumps(api_url))
        .replace("__DIGITS__", str(digits))
        .replace("__PIP__", json.dumps(pip))
        .replace("__ACTIVOS_JSON__", activos_json)   # lista de activos del selector de pantalla completa
        .replace("__POSICIONES_JS__", posiciones_js)   # líneas de posición, SL/TP y órdenes
    )


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara ensamblador .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
