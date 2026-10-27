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

"""Carga del CSS de los paneles del agente (historial, chat y propuestas).

El contenido de las reglas vive en estilos.css; este módulo solo lo lee una vez al importar
y lo expone como cadena para que `inyectar_estilos_agente` (en __init__.py) lo inyecte.
"""
from pathlib import Path

from components._estaticos import estilos

# Texto del CSS ya procesado por el ayudante compartido `estilos` de _estaticos.
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
