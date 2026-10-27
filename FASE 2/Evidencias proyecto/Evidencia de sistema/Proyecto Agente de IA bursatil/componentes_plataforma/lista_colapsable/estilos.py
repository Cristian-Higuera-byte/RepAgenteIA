# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara estilos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""CSS de la lista colapsable: plantilla en estilos.css con las medidas sustituidas."""
from pathlib import Path

from componentes_plataforma._estaticos import texto
from componentes_plataforma.lista_colapsable.datos import NAVEGACION_COLAPSADA, NAVEGACION_EXPANDIDA, TOP


# TITULO CSS

def css() -> str:
    """Devuelve el CSS de la pestaña y del colapso de la lista, con las posiciones calculadas a partir de las medidas de la barra lateral."""
    reemplazos = {
        "__TABY__": TOP + 60,          # a la altura de «Mis favoritos» / cabecera de la lista
        "__TABX_COL__": NAVEGACION_COLAPSADA + 2,   # pegada al borde izquierdo del contenido
        "__TABX_EXP__": NAVEGACION_EXPANDIDA + 2,
    }
    cuerpo = texto(Path(__file__).parent / "estilos.css")
    for marca, valor in reemplazos.items():
        cuerpo = cuerpo.replace(marca, str(valor))
    return "\n<style>\n" + cuerpo + "</style>\n"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara estilos .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
