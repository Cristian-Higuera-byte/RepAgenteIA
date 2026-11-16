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

"""Selector de proveedor de bajo nivel (`mt5`) para el proyecto.

Los archivos que antes hacían `import MetaTrader5 as mt5` pasan a hacer
`from proveedores.selector_mt5 import mt5`. Según `PROVEEDOR` del .env reciben:
  - el paquete real MetaTrader5 (PROVEEDOR=mt5), o
  - un objeto compatible respaldado por Capital.com (PROVEEDOR=capital),
que expone las MISMAS constantes y funciones que usa el proyecto.

Este paquete NO importa MetaTrader5 al cargarse: solo el selector decide, así que
con PROVEEDOR=capital la app arranca aunque el paquete MetaTrader5 no esté instalado.
"""


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
