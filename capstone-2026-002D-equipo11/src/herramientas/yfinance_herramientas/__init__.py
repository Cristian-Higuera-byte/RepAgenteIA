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

"""Herramientas del agente basadas en Yahoo Finance.

Todas llevan el prefijo yf_ para que, cuando se sumen las de MT5 e
investing.com, el modelo distinga de qué fuente viene cada dato.
La lógica real vive en database/scripts/fuentes/yfinance_fuente.py; aquí solo se describe
cada herramienta para el modelo.

Archivos: herramientas.py (registro de las herramientas), auxiliares.py, esquemas.json.

Este paquete es una fachada: reexporta la definición de parámetro ``_SIMBOLO`` y
las siete herramientas ``yf_*`` (búsqueda, cotización, histórico, fundamentales,
estados financieros, noticias y consenso de analistas).
"""
from herramientas.yfinance_herramientas.auxiliares import _SIMBOLO
from herramientas.yfinance_herramientas.herramientas import (
    yf_buscar_simbolo,
    yf_cotizacion,
    yf_historico,
    yf_fundamentales,
    yf_estados_financieros,
    yf_noticias,
    yf_consenso_analistas,
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
