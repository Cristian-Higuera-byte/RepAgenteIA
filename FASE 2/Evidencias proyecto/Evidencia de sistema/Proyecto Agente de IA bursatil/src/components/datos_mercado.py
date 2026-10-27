# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara datos_mercado .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada de los datos de mercado.

Apunta al paquete `components/mercado_datos/` (carga, entrada, precios, referencias y sparkline) y
reexporta de allí `cargar_datos_mercado`, `actualizar_precios_mt5` y `construir_entrada` (la API pública), además de
`cierre_previo`, `historial_sparkline` y `variacion` bajo sus nombres antiguos con guion bajo. Existe para que el
`from components.datos_mercado import ...` de `app.py` y de los mercados siga funcionando sin
cambios.
"""
from components.mercado_datos import (actualizar_precios_mt5, cargar_datos_mercado, cierre_previo,
                                      construir_entrada, historial_sparkline, variacion)

# Alias con los nombres con guion bajo que usaba mercados_panel antes de la separación (compatibilidad)
_cierre_previo = cierre_previo
_historial_sparkline = historial_sparkline
_variacion = variacion

__all__ = ["cargar_datos_mercado", "actualizar_precios_mt5", "construir_entrada"]


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara datos_mercado .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
