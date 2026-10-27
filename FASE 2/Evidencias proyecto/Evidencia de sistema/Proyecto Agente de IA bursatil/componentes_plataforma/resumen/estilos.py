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

"""CSS de la vista Resumen.

Expone `CSS`, el contenido de `estilos.css` envuelto en una etiqueta style, listo para inyectarlo con `st.html`.
Se lee al importar y se relee solo si el archivo cambia en disco.
"""
from pathlib import Path

from componentes_plataforma._estaticos import estilos

# Hoja de estilos de la vista, ya envuelta en style, que `panel.py` inyecta en cada ejecución.
CSS = estilos(Path(__file__).parent / "estilos.css")


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
