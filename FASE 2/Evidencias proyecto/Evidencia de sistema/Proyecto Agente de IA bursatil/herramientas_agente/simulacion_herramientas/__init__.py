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

"""Módulo de herramientas de simulación y análisis de escenarios 'What-If' para el agente.

NOMBRE DEL ARCHIVO: herramientas_agente/simulacion_herramientas

Archivos: herramientas.py (registro de las herramientas), auxiliares.py, esquemas.json.

Este paquete es una fachada: reexporta la matriz de elasticidades cruzadas, los
helpers de normalización de símbolos y de tamaño de contrato y la herramienta
``simular_escenario_cartera``.
"""
from herramientas_agente.simulacion_herramientas.auxiliares import (
    ELASTICIDAD_CRUZADA,
    _normalizar_simbolo,
    _estimar_tamano_contrato,
)
from herramientas_agente.simulacion_herramientas.herramientas import simular_escenario_cartera


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
