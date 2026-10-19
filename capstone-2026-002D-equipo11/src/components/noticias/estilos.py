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

"""CSS del carrusel y de las tarjetas clicables de noticias (vive en estilos.css).

Expone `CSS_CARRUSEL`, el texto listo para inyectarse con `st.markdown(..., unsafe_allow_html=True)` desde
`secciones.py`.
"""
from pathlib import Path

from components._estaticos import estilos

# Hoja de estilos leída de estilos.css y envuelta para inyectarla en la página
CSS_CARRUSEL = estilos(Path(__file__).parent / "estilos.css")


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
