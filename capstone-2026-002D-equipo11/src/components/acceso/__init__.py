# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Paquete de acceso (login) de la plataforma.

Fachada que reexporta únicamente `requerir_login`, la API pública que importa app.py
como puerta de entrada de la app. Existe para que el resto del proyecto no dependa de la
estructura interna del paquete: la interfaz de usuario (formularios de login y registro)
vive en pantalla.py y la mecánica de sesión (iniciar, cerrar y restaurar el token de la
URL) vive en sesion.py.
"""
from .pantalla import requerir_login

__all__ = ["requerir_login"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
