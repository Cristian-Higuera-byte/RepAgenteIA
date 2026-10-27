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

"""Módulo de generación de gráficos bursátiles profesionales para el agente.

NOMBRE DEL ARCHIVO: herramientas/graficos_herramientas

Archivos: herramientas.py (registro de las herramientas), auxiliares.py.

Este paquete es una fachada: reexporta las constantes y helpers de
``auxiliares`` (directorio de salida, tipos válidos, mapeo de símbolos,
etiquetas de fecha y dibujo de velas) y la herramienta
``generar_grafico_financiero`` de ``herramientas``. Importar el paquete
también registra la herramienta en el catálogo del agente, y permite que el
resto del proyecto use ``herramientas.graficos_herramientas.<nombre>``
sin conocer la división interna en archivos.
"""
from herramientas.graficos_herramientas.auxiliares import (
    OUTPUT_DIR,
    TIPOS_VALIDOS,
    _mapear_simbolo_yf,
    _etiqueta_fecha,
    _dibujar_velas,
)
from herramientas.graficos_herramientas.herramientas import generar_grafico_financiero


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
