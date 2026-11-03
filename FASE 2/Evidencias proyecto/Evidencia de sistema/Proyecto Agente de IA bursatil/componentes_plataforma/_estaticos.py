# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara _estaticos .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Lectura de los archivos estáticos (CSS, JS, HTML, JSON) que viven junto a cada componente.

Cada componente separado (profundidad_mercado/, favoritos/, copytrading/…) guarda su CSS en `estilos.css` y sus datos
en `.json`. Aquí se leen una sola vez y se vuelven a leer solos si el archivo cambia en disco (como el
ensamblador del gráfico), así que editar un CSS se ve al recargar la página sin reiniciar Streamlit.

Funciones públicas: `texto` (contenido de texto sin créditos), `datos_json` (JSON convertido) y `estilos` (CSS
envuelto en una etiqueta style). El caché se guarda en memoria del proceso, indexado por ruta y fecha de
modificación, y no escribe nada en disco.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from herramientas.recursos import sin_creditos  # se reexporta: los recursos estáticos lo usan desde aquí

# Caché en memoria: ruta (texto) -> (fecha de modificación en nanosegundos, valor ya convertido).
# Si la fecha del archivo cambia, la entrada se descarta y el archivo se vuelve a leer.
_cache: dict[str, tuple[int, Any]] = {}


# TITULO LEER

def _leer(ruta: Path, convertir) -> Any:
    """Lee un archivo con caché y lo convierte con la función dada.

    Recibe la ruta (`Path`) y `convertir`, un callable que transforma el texto leído (por ejemplo `sin_creditos` o
    `json.loads`). Devuelve el valor ya convertido. Si la fecha de modificación del archivo coincide con la del
    caché devuelve el valor guardado sin tocar el disco; si no, lee el archivo en UTF-8, convierte y actualiza el
    caché (efecto secundario sobre `_cache`)."""
    # Fecha de modificación actual: sirve de huella para detectar cambios en disco.
    marca = ruta.stat().st_mtime_ns
    guardado = _cache.get(str(ruta))
    # Caché vigente: el archivo no cambió desde la última lectura.
    if guardado and guardado[0] == marca:
        return guardado[1]
    # Caché ausente o vencida: se lee de disco, se convierte y se guarda.
    valor = convertir(ruta.read_text(encoding="utf-8"))
    _cache[str(ruta)] = (marca, valor)
    return valor


# TITULO TEXTO

def texto(ruta: str | Path) -> str:
    """Contenido de un archivo de texto (sin el encabezado y pie de créditos, si los tiene)."""
    return _leer(Path(ruta), sin_creditos)


# TITULO DATOS JSON

def datos_json(ruta: str | Path) -> Any:
    """Contenido de un archivo JSON ya convertido (listas, diccionarios…)."""
    return _leer(Path(ruta), json.loads)


# TITULO ESTILOS

def estilos(ruta: str | Path) -> str:
    """CSS de un archivo `.css` envuelto en <style>, listo para `st.html(...)` o `st.markdown(..., unsafe_allow_html=True)`."""
    return "\n<style>\n" + texto(ruta) + "</style>\n"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara _estaticos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
