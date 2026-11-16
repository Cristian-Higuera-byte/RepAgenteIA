# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara puente_mt5 .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

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
candado compartido (fuentes/mt5_fuentes lee `herramientas.puente_mt5.MT5_LOCK`).
"""

import os

from dotenv import load_dotenv

load_dotenv()

PROVEEDOR = os.getenv("PROVEEDOR", "mt5").strip().lower()

# Nombre legible del proveedor activo (para etiquetas de la UI).
NOMBRE_PROVEEDOR = "Capital.com" if PROVEEDOR == "capital" else "MT5 / XM"

# Nombre del broker que ve el usuario en los mensajes del agente ("Capital.com" o "MetaTrader 5").
NOMBRE_BROKER = "Capital.com" if PROVEEDOR == "capital" else "MetaTrader 5"

# Contrato público común a ambos backends.
if PROVEEDOR == "capital":
    from herramientas.backends.capital import (  # noqa: F401
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
        detalle_cierre,
    )
    print("[PUENTE] Backend activo: Capital.com (API REST)")
else:
    from herramientas.backends.mt5 import (  # noqa: F401
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

    # TITULO DETALLE CIERRE

    def detalle_cierre(deal_id, t_cierre):   # MT5 trae entrada/salida en sus deals: sin detalle aparte
        """Con MT5 no hace falta: sus deals ya traen entrada y salida. Devuelve un diccionario vacío."""
        return {}

    # TITULO PRECARGAR PRECIOS

    def precargar_precios(symbols=None):   # MT5 lee local: no necesita precarga batch
        """Con MT5 no hace falta precargar (lee en local). No hace nada."""
        return None


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara puente_mt5 .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
