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

"""Órdenes del agente - FASE 1: el agente PROPONE, el usuario CONFIRMA.

NOMBRE DEL PAQUETE: core/ordenes

Garantías de diseño:
  * El agente NO tiene ninguna herramienta que ejecute órdenes. Solo llama a
    proponer_apertura / proponer_cierre (ver herramientas/ordenes_herramientas), que
    validan contra LIMITES y guardan una propuesta PENDIENTE.
  * La única función que envía algo a MetaTrader 5 es confirmar_orden(), y solo la
    llama el botón "Confirmar" del dashboard (components/panel_ordenes.py).
  * Los límites de riesgo están en código (LIMITES), no en el prompt: el modelo no
    puede saltárselos ni cambiarlos.
  * Cada propuesta queda registrada en SQLite (data/ordenes.db) con su justificación:
    es el registro de auditoría de todo lo que el agente decidió.
  * Una propuesta solo se ejecuta una vez (se "reclama" de forma atómica), así que
    un doble clic o un reintento no duplica la orden.

Archivos: limites.py (LIMITES), base_datos.py + sql/ (SQLite), mt5_utiles.py, validacion.py, propuestas.py (API del
agente), envio.py (órdenes a MT5) y tablero.py (listar / rechazar / confirmar).

Este archivo es una FACHADA: no define lógica propia, solo reexporta los nombres de los submódulos (incluidos los
privados que usan el paquete vigilancia y las herramientas del agente) para que
`from core import ordenes` y `ordenes.confirmar_orden(...)` sigan funcionando igual que cuando todo vivía
en un único módulo. Cada bloque de importación de abajo agrupa lo que sale de un submódulo."""
# Límites de riesgo y constantes de MT5 (limites.py).
from core.ordenes.limites import (
    LIMITES,
    LimitesRiesgo,
    MAGIC,
    TOLERANCIA_RIESGO,
    TOLERANCIA_VS_PROPUESTA,
)  # noqa: F401
# Acceso a SQLite, esquema y interruptor de emergencia (base_datos.py).
from core.ordenes.base_datos import (
    DIR_DATOS,
    RUTA_DB,
    kill_switch_activo,
    fijar_kill_switch,
    _COLUMNAS_NUEVAS_ORDENES,
    _DB_LOCK,
    _SQL_ORDENES,
    _SQL_VIGILANCIAS,
    _ahora,
    _conectar,
    _consultar,
    _ejecutar,
    _insertar,
)  # noqa: F401
# Utilidades de MetaTrader 5: símbolos, reloj, pérdida del día, riesgo y chequeos globales (mt5_utiles.py).
from core.ordenes.mt5_utiles import (
    MT5_LOCK,
    inicializar_mt5,
    mt5,
    resolver_simbolo,
    _chequeos_globales,
    _con_lock,
    _desviacion,
    _inicio_dia_servidor,
    _modo_llenado,
    _normalizar,
    _perdida_del_dia,
    _preparar_mt5,
    _resolver_simbolo,
    _riesgo_expuesto,
    _simbolos_para_reloj,
)  # noqa: F401
# Validación de aperturas y de la cuenta demo (validacion.py).
from core.ordenes.validacion import (
    cuenta_demo,
    validar_simbolo,
    _evaluar_apertura,
)  # noqa: F401
# API del agente: proponer y consultar, sin ejecutar nada (propuestas.py).
from core.ordenes.propuestas import (
    estado_riesgo,
    proponer_apertura,
    proponer_cierre,
    resumen_posiciones,
    _propuesta_pendiente,
    _respuesta_duplicada,
)  # noqa: F401
# Envío real de órdenes a MT5 (envio.py).
from core.ordenes.envio import (
    _enviar_apertura,
    _enviar_cierre,
    _interpretar,
)  # noqa: F401
# API del dashboard: listar, rechazar, expirar y confirmar (tablero.py).
from core.ordenes.tablero import (
    confirmar_orden,
    expirar_vencidas,
    listar_historial,
    listar_pendientes,
    rechazar_orden,
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
