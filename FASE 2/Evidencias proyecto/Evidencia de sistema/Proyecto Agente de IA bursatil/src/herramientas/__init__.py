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

"""Paquete de herramientas del agente (antes `herramientas/`).

Cada módulo nuevo de herramientas (mt5, yfinance, investing, conocimiento, analisis, simulacion, diagnostico, graficos, tablas...)
se importa aquí para que sus funciones queden registradas al arrancar el agente.

Importar este paquete tiene como efecto secundario ejecutar el decorador `@herramienta` de cada
módulo, lo que llena el registro global `REGISTRO` (ver `herramientas.base`). El agente no
referencia las herramientas una a una: solo le pide al registro sus esquemas y le entrega las llamadas.
Los nombres de herramientas son parte del contrato con el modelo de IA y no deben renombrarse.
"""

from importlib import import_module
from types import ModuleType

# Cada línea importa un subpaquete de herramientas por nombre relativo; el import dispara el registro.
# Se usa import_module (en vez de "from . import") para que las anotaciones de tipo queden explícitas.
utilidades: ModuleType = import_module(".utilidades", __name__)
yfinance_herramientas: ModuleType = import_module(".yfinance_herramientas", __name__)
investing_herramientas: ModuleType = import_module(".investing_herramientas", __name__)
mt5_herramientas: ModuleType = import_module(".mt5_herramientas", __name__)
conocimiento: ModuleType = import_module(".conocimiento", __name__)
analisis_herramientas: ModuleType = import_module(".analisis_herramientas", __name__)
simulacion_herramientas: ModuleType = import_module(".simulacion_herramientas", __name__)
diagnostico_herramientas: ModuleType = import_module(".diagnostico_herramientas", __name__)
graficos_herramientas: ModuleType = import_module(".graficos_herramientas", __name__)
tablas_herramientas: ModuleType = import_module(".tablas_herramientas", __name__)
cuantitativo_herramientas: ModuleType = import_module(".cuantitativo_herramientas", __name__)
gestion_riesgo_herramientas: ModuleType = import_module(".gestion_riesgo_herramientas", __name__)
estructura_mercado_herramientas: ModuleType = import_module(".estructura_mercado_herramientas", __name__)
macro_eventos_herramientas: ModuleType = import_module(".macro_eventos_herramientas", __name__)
sentimiento_herramientas: ModuleType = import_module(".sentimiento_herramientas", __name__)
ordenes_herramientas: ModuleType = import_module(".ordenes_herramientas", __name__)
informe_cartera_herramientas: ModuleType = import_module(".informe_cartera_herramientas", __name__)

# Subpaquetes que expone el paquete al hacer "from herramientas import *".
__all__ = [
    "utilidades",
    "yfinance_herramientas",
    "investing_herramientas",
    "mt5_herramientas",
    "conocimiento",
    "analisis_herramientas",
    "simulacion_herramientas",
    "diagnostico_herramientas",
    "graficos_herramientas",
    "tablas_herramientas",
    "cuantitativo_herramientas",
    "gestion_riesgo_herramientas",
    "estructura_mercado_herramientas",
    "macro_eventos_herramientas",
    "sentimiento_herramientas",
    "ordenes_herramientas",
    "informe_cartera_herramientas",
]


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
