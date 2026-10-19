"""CSS de la lista colapsable: plantilla en estilos.css con las medidas sustituidas."""
from pathlib import Path

from components._estaticos import texto
from components.lista_colapsable.datos import NAV_COL, NAV_EXP, TOP


def css() -> str:
    reemplazos = {
        "__TABY__": TOP + 60,          # a la altura de «Mis favoritos» / cabecera de la lista
        "__TABX_COL__": NAV_COL + 2,   # pegada al borde izquierdo del contenido
        "__TABX_EXP__": NAV_EXP + 2,
    }
    cuerpo = texto(Path(__file__).parent / "estilos.css")
    for marca, valor in reemplazos.items():
        cuerpo = cuerpo.replace(marca, str(valor))
    return "\n<style>\n" + cuerpo + "</style>\n"
