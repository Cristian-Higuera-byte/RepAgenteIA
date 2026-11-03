# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara cargando .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Indicador "cargando" de la ficha. Se muestra EN EL NAVEGADOR en el mismo instante del clic (un st.spinner de
Python recién aparecería cuando el servidor ya va a mitad del rerun) y se quita solo cuando el modal de la
ficha está en el DOM. El script vive en estatico/cargando.js."""
from pathlib import Path

from componentes_plataforma._estaticos import texto

# Fragmento HTML con el script de cargando.js dentro de una etiqueta script; `panel.py` lo incrusta con
# `components.html` (altura 0) para que se ejecute en la página sin ocupar espacio
JS_CARGANDO = "\n<script>\n" + texto(Path(__file__).parent / "estatico" / "cargando.js") + "</script>\n"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara cargando .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
