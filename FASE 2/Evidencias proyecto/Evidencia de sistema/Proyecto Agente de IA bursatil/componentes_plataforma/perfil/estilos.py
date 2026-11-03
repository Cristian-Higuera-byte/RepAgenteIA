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

"""CSS de la vista de perfil (vive en estilos.css).

Expone `CSS`, la hoja ya envuelta en etiqueta de estilo, para inyectarla con `st.html` en el panel del perfil.
"""
from pathlib import Path

# Lector de CSS que lo devuelve listo para inyectar en la página.
from componentes_plataforma._estaticos import estilos

# Estilos de la vista de perfil.
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
