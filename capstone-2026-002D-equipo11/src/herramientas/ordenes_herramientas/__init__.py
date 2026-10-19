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

"""Herramientas del agente para operar: SOLO proponer y consultar (Fase 1).

NOMBRE DEL ARCHIVO: herramientas/ordenes_herramientas

Ninguna de estas herramientas ejecuta órdenes en MetaTrader 5. Las propuestas quedan
pendientes y el usuario las confirma con un botón en el dashboard (core/ordenes.py).

Archivos: herramientas.py (registro de las herramientas), auxiliares.py, esquemas.json.

Este paquete es una fachada: reexporta el conversor ``_a_numero`` y las siete
herramientas (proponer orden, proponer cierre, ver posiciones, ver límites,
y gestión de vigilancias) para importarlas desde un único punto.
"""
from herramientas.ordenes_herramientas.auxiliares import _a_numero
from herramientas.ordenes_herramientas.herramientas import (
    proponer_orden,
    proponer_cierre_posicion,
    ver_posiciones,
    ver_limites_riesgo,
    proponer_vigilancia,
    detener_vigilancia,
    ver_vigilancias,
)


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
