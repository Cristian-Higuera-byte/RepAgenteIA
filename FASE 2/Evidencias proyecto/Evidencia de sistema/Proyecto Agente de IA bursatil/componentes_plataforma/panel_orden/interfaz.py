# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara interfaz .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
panel_orden/interfaz.py
-----------------
Piezas de UI reutilizables del ticket: carga de los estáticos (CSS) y el "campo tipo
tarjeta" (etiqueta dentro + número grande, estilo XM). El CSS vive en estatico/ticket.css
y se lee una sola vez (cacheado); cargar_css() lo inyecta acotado a las claves .st-key-ord_*.
"""
from functools import lru_cache
from pathlib import Path

import streamlit as st

from componentes_plataforma._estaticos import sin_creditos

# Carpeta estatico/ del paquete, con ticket.css y avisos.js
_ESTATICO = Path(__file__).resolve().parent / "estatico"


# TITULO LEER ESTATICO

@lru_cache(maxsize=None)
def leer_estatico(nombre: str) -> str:
    """Lee un archivo de panel_orden/estatico/ (CSS/JS). Cacheado en memoria por proceso.

    Recibe el nombre del archivo, le quita el encabezado de créditos con `sin_creditos` y devuelve el texto,
    o una cadena vacía si no se puede leer."""
    try:
        return sin_creditos((_ESTATICO / nombre).read_text(encoding="utf-8"))
    except OSError:
        return ""


# TITULO CARGAR CSS

def cargar_css() -> None:
    """Inyecta el CSS del ticket (estatico/ticket.css).

    Lo envuelve en una etiqueta de estilo y lo pinta con `st.html` en la página."""
    st.html(f"<style>{leer_estatico('ticket.css')}</style>")


# TITULO CAMPO

def campo(clave: str, etiqueta: str, sufijo: str = ""):
    """Contenedor de un campo tipo tarjeta: etiqueta dentro (arriba) + sufijo opcional.

    Crea un contenedor con key `orden_caja_{clave}` (el CSS le da aspecto de tarjeta), le pinta la etiqueta y el
    sufijo (por ejemplo la moneda o %), y lo devuelve para que quien llama use `with campo(...)` y coloque
    dentro el `number_input`."""
    cont = st.container(key=f"orden_caja_{clave}")
    cont.html(f"<div class='orden-caja-etiqueta'>{etiqueta}</div>"
              + (f"<div class='orden-caja-sufijo'>{sufijo}</div>" if sufijo else ""))
    return cont


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara interfaz .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
