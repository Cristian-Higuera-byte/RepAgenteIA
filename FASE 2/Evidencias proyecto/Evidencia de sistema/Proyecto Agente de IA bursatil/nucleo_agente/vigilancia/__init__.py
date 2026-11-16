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

"""Vigilancia automática: el agente analiza un activo cada cierto tiempo y, si el usuario lo autorizó,
compra o vende solo.

NOMBRE DEL PAQUETE: nucleo_agente/vigilancia

Cómo funciona
  1. El usuario pide en el chat que el agente vigile un activo y opere por su cuenta.
  2. El agente llama a la herramienta `proponer_vigilancia`: queda PENDIENTE_AUTORIZACION con sus
     términos (activo, riesgo, máx. operaciones, duración, intervalo). NO hace nada todavía.
  3. El usuario pulsa «Autorizar» en el panel (componentes_plataforma/agente_paneles/). Solo entonces pasa a ACTIVA.
  4. Un motor en segundo plano (iniciar_motor) despierta cada pocos segundos y, cuando a una vigilancia
     le toca, le pide al agente un análisis. El agente responde con una DECISIÓN estructurada
     (esperar / abrir / cerrar) y el MOTOR (no el modelo) la valida y la ejecuta.
  5. Cada compra, venta o cierre automático avisa en la campana de notificaciones.

Garantías de diseño (están en código, no en el prompt):
  * El modelo NO tiene ninguna herramienta que ejecute órdenes, tampoco en este modo: el registro que
    usa el análisis excluye las de proponer/vigilar. Solo este motor ejecuta, y solo lo autorizado.
  * Solo CUENTA DEMO (se comprueba en la autorización y en cada chequeo, aunque LIMITES.solo_demo se relaje).
  * Solo el activo de la vigilancia, con el riesgo de la vigilancia (nunca más que el límite global).
  * Todas las comprobaciones de nucleo_agente/ordenes.py siguen aplicando: stop loss obligatorio, riesgo total,
    pérdida diaria, interruptor de emergencia, margen, distancia mínima, etc.
  * Tope de operaciones, UNA posición abierta a la vez y vencimiento automático.
  * Solo puede cerrar las posiciones que ella misma abrió (las reconoce por el comentario de la orden).
  * El usuario puede detenerla cuando quiera; si la detiene mientras el modelo analizaba, se descarta.

Archivos: configuracion.py, utilidades.py, gestion.py (crear/autorizar/detener/listar), posiciones.py, decision.py,
analisis.py (agente del análisis), ejecucion.py, chequeo.py, caducidad.py y motor.py.

Este archivo es una FACHADA: no tiene lógica propia, solo reexporta los nombres de todos los submódulos (incluidos
los privados) para que `from nucleo_agente import vigilancia` y `vigilancia.crear(...)` sigan funcionando igual que
cuando todo vivía en un único módulo. También deja accesibles `mt5`, `ordenes` y `notificaciones`, que las pruebas
sustituyen o consultan.
Para inyectar un agente falso en pruebas, sustituye `nucleo_agente.vigilancia.analisis.fabrica_agente`."""
# Constantes y estados de la vigilancia (configuracion.py).
from nucleo_agente.vigilancia.configuracion import (
    ACTIVA,
    CANCELADA,
    DURACION_DEFECTO_H,
    DURACION_MAX_H,
    DURACION_MIN_H,
    ERROR,
    ERRORES_SEGUIDOS_MAX,
    ESPERA_MOTOR_S,
    EXPIRADA,
    FINALIZADA,
    HERRAMIENTAS_EXCLUIDAS,
    INTERVALO_DEFECTO_MIN,
    INTERVALO_MAX,
    INTERVALO_MIN,
    MAX_ABIERTAS_POR_VIGILANCIA,
    MAX_OPERACIONES_DEFECTO,
    MAX_OPERACIONES_TOPE,
    MAX_VIGILANCIAS_POR_USUARIO,
    NOMBRE_HILO_MOTOR,
    PENDIENTE,
    PERFIL_VIGILANCIA,
    PREFIJO_HILO_CHEQUEO,
    RIESGO_DEFECTO_PORCENTAJE,
    VIGENTES,
)  # noqa: F401
# Utilidades de base de datos, notificación y conversión (utilidades.py).
from nucleo_agente.vigilancia.utilidades import (
    notificaciones,
    obtener,
    ordenes,
    _a_numero,
    _actualizar,
    _consultar,
    _finalizar,
    _iso,
    _lado_texto,
    _notificar,
)  # noqa: F401
# Posiciones abiertas por cada vigilancia (posiciones.py).
from nucleo_agente.vigilancia.posiciones import (
    mt5,
    _posiciones_de,
)  # noqa: F401
# Caducidad de autorizaciones y vigilancias (caducidad.py).
from nucleo_agente.vigilancia.caducidad import (
    _caducar_autorizaciones,
    _caducar_vencidas,
)  # noqa: F401
# Lectura de la decisión del modelo (decision.py).
from nucleo_agente.vigilancia.decision import (
    parsear_decision,
    _RE_OBJETO,
    _SINONIMOS,
)  # noqa: F401
# Agente del análisis y su mensaje (analisis.py).
from nucleo_agente.vigilancia.analisis import (
    fabrica_agente,
    _RegistroSinEjecucion,
    _fabrica_agente_real,
    _mensaje_analisis,
)  # noqa: F401
# Ejecución de la decisión (ejecucion.py).
from nucleo_agente.vigilancia.ejecucion import (
    _aplicar,
)  # noqa: F401
# Chequeo completo de una vigilancia (chequeo.py).
from nucleo_agente.vigilancia.chequeo import (
    chequear,
)  # noqa: F401
# Motor en segundo plano (motor.py).
from nucleo_agente.vigilancia.motor import (
    iniciar_motor,
    tick,
    _CANDADO_MOTOR,
    _bucle,
    _chequear_seguro,
    _chequeo_en_curso,
)  # noqa: F401
# Alta, autorización, detención y listado (gestion.py).
from nucleo_agente.vigilancia.gestion import (
    autorizar,
    crear,
    detener,
    listar,
    rechazar,
    resumen_terminos,
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
