"""Backends de datos/órdenes del proyecto bursátil.

Cada backend implementa el MISMO contrato público (el de `herramientas/puente_mt5.py`)
para que la plataforma funcione igual con cualquiera:

  - mt5.py      -> MetaTrader 5 (XM) vía el terminal local.
  - capital.py  -> Capital.com vía API REST (sin terminal).

El módulo `herramientas/puente_mt5.py` actúa de despachador según la variable
`PROVEEDOR` del .env (mt5 | capital) y reexporta el backend elegido, de modo que
los ~45 archivos que hacen `from herramientas.puente_mt5 import ...` no cambian.
"""
