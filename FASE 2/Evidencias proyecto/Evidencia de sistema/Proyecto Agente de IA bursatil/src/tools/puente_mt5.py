"""
puente_mt5.py  —  DESPACHADOR de backend (16-10-2026)
---------------------------------------------------------------
Este módulo ya NO contiene la lógica de MetaTrader 5. Ahora elige el backend
según la variable `PROVEEDOR` del .env y reexporta su contrato público:

    PROVEEDOR=mt5       -> herramientas/backends/mt5.py      (MetaTrader 5 / XM, terminal)
    PROVEEDOR=capital   -> herramientas/backends/capital.py  (Capital.com, API REST)

Los ~45 archivos que hacen `from herramientas.puente_mt5 import ...` NO cambian:
siguen importando los mismos nombres; solo cambia a quién llaman por debajo.

El nombre del archivo se conserva ("puente_mt5") para no tocar esos imports ni el
candado compartido (database/scripts/fuentes/mt5_fuentes lee `herramientas.puente_mt5.MT5_LOCK`).
"""

import os

from dotenv import load_dotenv

load_dotenv()

PROVEEDOR = os.getenv("PROVEEDOR", "mt5").strip().lower()

# Nombre legible del proveedor activo (para etiquetas de la UI).
NOMBRE_PROVEEDOR = "Capital.com" if PROVEEDOR == "capital" else "MT5 / XM"

# Contrato público común a ambos backends.
if PROVEEDOR == "capital":
    from tools.backends.capital import (  # noqa: F401
        MT5_LOCK,
        inicializar_mt5,
        cerrar_mt5,
        resolver_simbolo,
        obtener_info_cuenta,
        obtener_posiciones,
        obtener_historial,
        especs_posicion,
        obtener_precio_actual,
        obtener_datos_historicos,
        obtener_velas_rango,
        ejecutar_orden_mercado,
        colocar_orden_pendiente,
        cerrar_posicion,
        modificar_sltp,
        modificar_orden,
        obtener_dom,
        eliminar_orden,
        precargar_precios,
    )
    print("[PUENTE] Backend activo: Capital.com (API REST)")
else:
    from tools.backends.mt5 import (  # noqa: F401
        MT5_LOCK,
        inicializar_mt5,
        cerrar_mt5,
        resolver_simbolo,
        obtener_info_cuenta,
        obtener_posiciones,
        obtener_historial,
        especs_posicion,
        obtener_precio_actual,
        obtener_datos_historicos,
        obtener_velas_rango,
        ejecutar_orden_mercado,
        colocar_orden_pendiente,
        cerrar_posicion,
        modificar_sltp,
        modificar_orden,
        obtener_dom,
        eliminar_orden,
    )

    def precargar_precios(symbols=None):   # MT5 lee local: no necesita precarga batch
        return None
