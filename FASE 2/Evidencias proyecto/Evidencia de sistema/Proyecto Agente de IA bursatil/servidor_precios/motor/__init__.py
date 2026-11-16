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

"""Motor de precios en vivo: un hilo lee ticks y cuenta de MT5 y los reparte a los clientes SSE.

Fachada del paquete: reexporta `MOTORES` (registro con un motor por cuenta) y la clase `MotorPrecios`,
de modo que el resto del código importe `from .motor import MOTORES` sin conocer los submódulos
base.py, registro.py, oco.py y stop_dinamico.py.
"""
from .base import MotorPrecios
from .registro import MOTORES

__all__ = ["MOTORES", "MotorPrecios"]


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
