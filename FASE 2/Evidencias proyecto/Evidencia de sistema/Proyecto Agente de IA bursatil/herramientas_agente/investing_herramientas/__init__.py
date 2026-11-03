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

"""Herramientas del agente basadas en Investing.com (en español).

Todas llevan el prefijo inv_ para que el modelo distinga claramente de qué
fuente proviene cada noticia. La lógica real vive en fuentes/investing_fuente.py.

Archivos: herramientas.py (registro de las herramientas), esquemas.json.

Este paquete es una fachada: reexporta ``inv_noticias`` e ``inv_buscar_noticias``
para que se importen desde ``herramientas_agente.investing_herramientas``.
"""
from herramientas_agente.investing_herramientas.herramientas import inv_noticias, inv_buscar_noticias


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
