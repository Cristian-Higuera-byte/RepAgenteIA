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

"""CSS del rail y sus paneles: plantilla en estilos.css con las medidas (RAIL, PANEL, TOP) y los tooltips.

La plantilla contiene marcadores que `css()` reemplaza por las medidas de `datos.py` y por las reglas de tooltip
generadas a partir de `BOTONES`."""
import json
from pathlib import Path

from components._estaticos import texto
from components.riel.datos import BOTONES, PANEL, RAIL, TOP


def css() -> str:
    """Devuelve el CSS final del rail envuelto en una etiqueta style.

    Lee la plantilla `estilos.css`, genera una regla `::after` con el nombre de cada botón (tooltip propio) y
    sustituye los marcadores de medidas: ancho del rail, ancho del panel, alto de la barra superior y los
    rellenos derechos (rail + panel + 16 y rail + 16). Lee el archivo con caché; no escribe nada."""
    # Una regla de tooltip por botón: el texto sale del tercer elemento de cada tupla de BOTONES.
    tips = "\n".join(
        f'    .st-key-rail_{pid} button::after {{ content: {json.dumps(nom)}; }}'
        for _, pid, nom in BOTONES
    )
    # Plantilla con todos los marcadores sustituidos (los más largos primero para no pisar los más cortos).
    cuerpo = (texto(Path(__file__).parent / "estilos.css")
              .replace("__RAIL_PANEL_16__", str(RAIL + PANEL + 16)).replace("__RAIL_16__", str(RAIL + 16))
              .replace("__RAIL__", str(RAIL)).replace("__PANEL__", str(PANEL)).replace("__TOP__", str(TOP))
              .replace("__TIPS__", tips))
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
