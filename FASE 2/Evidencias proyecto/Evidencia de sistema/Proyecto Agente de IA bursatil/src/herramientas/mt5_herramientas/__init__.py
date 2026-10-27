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

"""Herramientas del agente basadas en MetaTrader 5 (terminal de XM) — SOLO LECTURA.

Archivos: herramientas.py (registro de las herramientas), auxiliares.py, esquemas.json.

Este paquete es una fachada: reexporta la definición de parámetro ``_SIMBOLO`` y
las siete herramientas de consulta (símbolos, precio, velas, cuenta, posiciones,
órdenes pendientes e historial). Ninguna envía órdenes.
"""
from herramientas.mt5_herramientas.auxiliares import _SIMBOLO
from herramientas.mt5_herramientas.herramientas import (
    mt5_buscar_simbolos,
    mt5_precio,
    mt5_velas,
    mt5_cuenta,
    mt5_posiciones,
    mt5_ordenes_pendientes,
    mt5_historial_operaciones,
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
