"""Selector de proveedor de bajo nivel (`mt5`) para el proyecto.

Los archivos que antes hacían `import MetaTrader5 as mt5` pasan a hacer
`from proveedores.selector_mt5 import mt5`. Según `PROVEEDOR` del .env reciben:
  - el paquete real MetaTrader5 (PROVEEDOR=mt5), o
  - un objeto compatible respaldado por Capital.com (PROVEEDOR=capital),
que expone las MISMAS constantes y funciones que usa el proyecto.

Este paquete NO importa MetaTrader5 al cargarse: solo el selector decide, así que
con PROVEEDOR=capital la app arranca aunque el paquete MetaTrader5 no esté instalado.
"""
