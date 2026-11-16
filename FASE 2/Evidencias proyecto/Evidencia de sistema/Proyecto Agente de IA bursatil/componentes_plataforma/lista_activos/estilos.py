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

"""CSS de la lista de activos (vive en estilos.css). Termina con la marca .lista-activos-css que el propio CSS usa para
ocultar el contenedor del bloque de estilos.

Expone `CSS`, ya listo para inyectarse con `st.markdown(..., unsafe_allow_html=True)` en panel.py.
"""
from pathlib import Path

# Lector de CSS que lo devuelve envuelto para inyectar en la página.
from componentes_plataforma._estaticos import estilos

# Hoja de estilos más la marca .lista-activos-css (sirve para ocultar el contenedor que la inyecta).
CSS = estilos(Path(__file__).parent / "estilos.css") + '<span class="lista-activos-css"></span>\n'


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
