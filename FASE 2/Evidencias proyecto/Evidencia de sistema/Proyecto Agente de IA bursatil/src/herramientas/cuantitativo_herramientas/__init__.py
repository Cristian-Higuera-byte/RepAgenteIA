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

"""Módulo de análisis cuantitativo, riesgo estadístico y simulación para el agente.

NOMBRE DEL ARCHIVO: herramientas/cuantitativo_herramientas

Archivos: herramientas.py (registro de las herramientas), auxiliares.py, esquemas.json.

Reexporta los auxiliares de retornos históricos y las tres herramientas cuantitativas (correlación,
Monte Carlo y métricas de rendimiento) para importarlas desde el paquete.
"""
from herramientas.cuantitativo_herramientas.auxiliares import (
    _mapear_simbolo_yf,
    _obtener_retornos_historicos,
)
from herramientas.cuantitativo_herramientas.herramientas import (
    calcular_matriz_correlacion,
    simular_monte_carlo_cartera,
    evaluar_metricas_rendimiento,
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
