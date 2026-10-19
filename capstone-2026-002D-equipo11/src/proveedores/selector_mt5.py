"""Selector del proveedor de bajo nivel `mt5`.

Uso en los archivos que antes hacían `import MetaTrader5 as mt5`:
    from proveedores.selector_mt5 import mt5

Según PROVEEDOR del .env entrega el paquete real MetaTrader5 o el shim de Capital.com.
La decisión se toma UNA vez al importar.
"""
import os

from dotenv import load_dotenv

load_dotenv()

_PROVEEDOR = os.getenv("PROVEEDOR", "mt5").strip().lower()

if _PROVEEDOR == "capital":
    from proveedores import capital_mt5_compat as mt5  # noqa: F401
else:
    import MetaTrader5 as mt5  # type: ignore[import-untyped]  # noqa: F401
