# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara configuracion .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Configuración de la vigilancia automática: intervalos, límites, estados y herramientas excluidas.

Solo contiene constantes; las leen gestion.py (validación de términos), chequeo.py, motor.py y analisis.py.
Los tiempos están en minutos u horas según se indica en cada constante."""
from __future__ import annotations


# Intervalo, duración y cantidades por defecto y sus rangos permitidos.
INTERVALO_DEFECTO_MIN = 15       # cada cuánto se analiza el activo
INTERVALO_MIN, INTERVALO_MAX = 5, 240
DURACION_DEFECTO_H = 8.0         # la vigilancia termina sola a las N horas de autorizarla
DURACION_MIN_H, DURACION_MAX_H = 0.5, 24.0
MAX_OPERACIONES_DEFECTO = 3      # aperturas máximas por vigilancia
MAX_OPERACIONES_TOPE = 10
RIESGO_DEFECTO_PCT = 0.5         # % del equity por operación si el usuario no indica otro
MAX_VIGILANCIAS_POR_USUARIO = 3  # activas + pendientes de autorizar (acota el gasto de tokens)
MAX_ABIERTAS_POR_VIGILANCIA = 1  # no se acumulan posiciones: una abierta a la vez
ERRORES_SEGUIDOS_MAX = 3         # tras N fallos seguidos del análisis, la vigilancia se detiene
ESPERA_MOTOR_S = 20              # cada cuánto despierta el motor
PERFIL_VIGILANCIA: str | None = None   # None = perfil por defecto del agente (config.PERFIL_POR_DEFECTO)

# Nombres de hilos: permiten detectar si el motor o un chequeo ya está corriendo (iniciar_motor, _chequeo_en_curso).
NOMBRE_HILO_MOTOR = "pj-vigilancia-motor"
PREFIJO_HILO_CHEQUEO = "pj-vigilancia-"

# Estados del ciclo de vida de una vigilancia (columna estado de la tabla vigilancias).
PENDIENTE, ACTIVA = "PENDIENTE_AUTORIZACION", "ACTIVA"
FINALIZADA, CANCELADA, EXPIRADA, ERROR = "FINALIZADA", "CANCELADA", "EXPIRADA", "ERROR"
# Estados "vigentes": ocupan cupo del usuario y pueden detenerse.
VIGENTES = (PENDIENTE, ACTIVA)

# Herramientas que el análisis automático NO puede usar (ninguna ejecuta o programa órdenes).
HERRAMIENTAS_EXCLUIDAS = frozenset({
    "proponer_orden", "proponer_cierre_posicion", "proponer_vigilancia", "detener_vigilancia", "ver_vigilancias",
})


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara configuracion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
