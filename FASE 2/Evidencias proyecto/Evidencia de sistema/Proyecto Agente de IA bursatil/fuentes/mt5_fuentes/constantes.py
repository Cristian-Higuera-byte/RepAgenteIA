# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara constantes .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Tiempos de conexión, temporalidades, funciones de MT5 permitidas (solo lectura) y alias de símbolos (datos.json).

Los tiempos están escritos aquí; los mapas (temporalidades, funciones
permitidas y alias) se cargan una sola vez desde `datos.json`, junto a este módulo."""
import json
import os
from pathlib import Path

# Contenido completo de datos.json (claves: timeframes, funciones_permitidas, alias).
_D = json.loads((Path(__file__).parent / "datos.json").read_text(encoding="utf-8"))

# Nombre del origen de los datos que ven el usuario y el modelo: Capital.com con PROVEEDOR=capital; si no, MetaTrader 5.
NOMBRE_FUENTE = "Capital.com" if os.getenv("PROVEEDOR", "mt5").strip().lower() == "capital" else "MetaTrader 5"

# Máximo de milisegundos que se espera a que el terminal responda a cada `initialize`.
_TIMEOUT_MS = 10_000
# Segundos de espera tras un fallo de conexión antes de volver a intentarlo.
_REINTENTO_S = 15
# Segundos de vida de la caché de símbolos (600 s = 10 min).
_TIEMPO_VIDA_SIMBOLOS_S = 600
# Segundos de vida de la caché de rutas candidatas del terminal (300 s = 5 min).
_TTL_RUTAS_S = 300
# Segundos de vida de la caché del desfase horario del servidor del broker (300 s = 5 min).
_TIEMPO_VIDA_OFFSET_S = 300
# Máximo de rutas de terminal que se prueban por intento de conexión.
_MAX_RUTAS = 3

# Nombre de temporalidad (p. ej. "H1") -> constante TIMEFRAME de MetaTrader5.
TIMEFRAMES = dict(_D["timeframes"])

# Únicas funciones de MetaTrader5 accesibles (todas de consulta); el resto se bloquea.
_FUNCIONES_PERMITIDAS = frozenset(_D["funciones_permitidas"])

# Símbolo genérico -> lista de nombres alternativos que usan distintos brokers.
_ALIAS = {k: list(v) for k, v in _D["alias"].items()}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara constantes .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
