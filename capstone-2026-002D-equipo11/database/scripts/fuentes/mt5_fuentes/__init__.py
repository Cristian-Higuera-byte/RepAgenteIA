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

"""Conexión con MetaTrader 5, candado, símbolos y utilidades — SOLO LECTURA.

NOMBRE DEL PAQUETE: database/scripts/fuentes/mt5_fuentes (se importa como `from fuentes import mt5_fuentes`).

Estrategia de conexión (la de tu puente_mt5.py, que ya funciona con tu terminal):
  * NUNCA se llama a initialize() sin ruta (en tu equipo da "IPC timeout" y cuelga hasta 60 s).
  * Se prueban rutas candidatas, en este orden: MT5_PATH del .env -> terminal64.exe que esté
    abierto ahora -> carpetas típicas de instalación (máximo 3 intentos).
  * Máximo 10 s por intento y, si no conecta, espera 15 s antes de reintentar. Durante esa
    espera las llamadas fallan al instante (no se quedan esperando el candado).
  * Se usa la sesión que ya está iniciada en el terminal. Solo si MT5_LOGIN, MT5_PASSWORD y
    MT5_SERVER están los tres en el .env se hace login explícito.

CANDADO: la API de MT5 no es segura entre hilos. Si existe el bridge del dashboard
(herramientas.puente_mt5, o el módulo indicado en MT5_BRIDGE_MODULO) se comparte su MT5_LOCK; si no,
se usa uno propio. Se decide UNA vez, al importar este módulo (nunca cambia a mitad de camino).
Un candado no cruza procesos: si dashboard y agente corren en procesos distintos, MT5 los
atiende a ambos, pero no se excluyen entre sí.

SEGURIDAD: los datos se leen a través de _SoloLectura, que solo deja pasar consultas. Cualquier
otra función (order_send, order_check, login, initialize, shutdown...) queda bloqueada.
Nunca se llama a shutdown().

DATOS POR USUARIO: MT5 trabaja con UNA cuenta por terminal. Para no entregar los datos de una
persona a otra, las consultas leen siempre la cuenta abierta en el terminal. El usuario debe venir de
la sesión del dashboard, NUNCA de un argumento que decida el LLM.

Las horas de MT5 son del SERVIDOR del broker, no tu hora local.

Archivos: entorno.py (.env), constantes.py + datos.json, errores.py, solo_lectura.py, candado.py, rutas.py, conexion.py,
utiles.py, cuenta.py (cuenta, posiciones, órdenes, historial) y mercado.py (precio, velas, símbolos, riesgo).

Este archivo es una fachada: reexporta desde los submódulos las constantes, errores, funciones
públicas y también los nombres privados (con guion bajo) que usan otras capas del proyecto o las
pruebas, para que `database.scripts.fuentes.mt5_fuentes.<nombre>` siga funcionando sin importar en qué archivo vive
cada cosa. Los `# noqa: F401` evitan que el linter marque como "sin usar" lo que solo se reexporta."""
# Importar entorno.py tiene el efecto de cargar el .env antes que cualquier otro módulo del paquete.
import database.scripts.fuentes.mt5_fuentes.entorno  # noqa: F401  (carga el .env antes que nada)
# Tiempos, temporalidades, lista blanca de funciones y alias de símbolos.
from database.scripts.fuentes.mt5_fuentes.constantes import (
    TIMEFRAMES,
    _ALIAS,
    _FUNCIONES_PERMITIDAS,
    _MAX_RUTAS,
    _REINTENTO_S,
    _TIMEOUT_MS,
    _TTL_OFFSET_S,
    _TTL_RUTAS_S,
    _TTL_SIMBOLOS_S,
)  # noqa: F401
# Excepciones del paquete.
from database.scripts.fuentes.mt5_fuentes.errores import (
    ErrorMT5,
    OperacionNoPermitida,
)  # noqa: F401
# Envoltorio de solo lectura sobre el módulo MetaTrader5.
from database.scripts.fuentes.mt5_fuentes.solo_lectura import (
    _SoloLectura,
)  # noqa: F401
# Candado de acceso a MT5 (compartido con el dashboard o propio).
from database.scripts.fuentes.mt5_fuentes.candado import (
    _LOCK_COMPARTIDO,
    _LOCK_PROPIO,
    _candado,
    _resolver_lock_compartido,
)  # noqa: F401
# Descubrimiento de las rutas del terminal64.exe.
from database.scripts.fuentes.mt5_fuentes.rutas import (
    rutas_candidatas,
    _rutas_cache,
    _terminal_en_ejecucion,
)  # noqa: F401
# Conexión, reintentos y sesión con candado (incluye el estado global de la conexión).
from database.scripts.fuentes.mt5_fuentes.conexion import (
    asegurar_conexion,
    _conectar,
    _espera_restante,
    _fallar,
    _modulo,
    _proxy,
    _raw,
    _ruta_conectada,
    _sesion,
    _ultimo_error,
    _ultimo_fallo,
)  # noqa: F401
# Utilidades de números, fechas, símbolos y tipos de orden.
from database.scripts.fuentes.mt5_fuentes.utiles import (
    _como_tupla,
    _fecha_utc,
    _hora_utc,
    _nivel,
    _num,
    _resolver,
    _simbolo_temporal,
    _tamano_pip,
    _tipo_orden,
)  # noqa: F401
# Consultas de la cuenta: resumen, posiciones, órdenes pendientes e historial.
from database.scripts.fuentes.mt5_fuentes.cuenta import (
    cuenta,
    historial_operaciones,
    ordenes_pendientes,
    posiciones,
)  # noqa: F401
# Consultas de mercado: precio, velas, símbolos, especificación y riesgo.
from database.scripts.fuentes.mt5_fuentes.mercado import (
    buscar_simbolos,
    distancias_y_riesgo,
    especificacion_simbolo,
    precio,
    resultado_si_precio,
    velas,
)  # noqa: F401


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
