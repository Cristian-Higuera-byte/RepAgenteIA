# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara limites .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Límites de riesgo del agente.

Define la configuración inmutable de riesgo (LIMITES) y las constantes de tolerancia y de identificación
de órdenes en MT5. Los valores viven en código y no en el prompt, de modo que el modelo no puede leerlos como
instrucción ni modificarlos; para cambiarlos hay que editar este archivo."""
from dataclasses import dataclass


@dataclass(frozen=True)
class LimitesRiesgo:
    """Conjunto inmutable (frozen) de límites de riesgo que aplican las validaciones de órdenes.

    Cada campo se comenta con su unidad; la instancia única es LIMITES. Al ser frozen, ningún módulo puede
    alterarlos en tiempo de ejecución por accidente."""
    solo_demo: bool = True                       # rechaza TODO si la cuenta conectada no es demo
    riesgo_max_por_operacion_pct: float = 1.0    # % del equity que se puede perder si salta el SL
    riesgo_max_total_pct: float = 3.0            # % del equity en riesgo sumando posiciones abiertas + propuestas pendientes + la nueva
    max_posiciones_abiertas: int = 3
    perdida_max_diaria_pct: float = 3.0          # % del balance; al alcanzarlo no se abren más
    volumen_max: float = 0.5                     # lotes máximos por orden
    vigencia_propuesta_min: int = 10             # minutos antes de que una propuesta venza
    desviacion_puntos: int = 20                  # deslizamiento máximo aceptado al ejecutar
    # Símbolos que el agente puede operar. None = CUALQUIER activo disponible en MT5 (el nombre se traduce
    # al del bróker con resolver_simbolo: XAUUSD <-> GOLD, sufijos .m / ..., etc.). Para restringirlo pon
    # una tupla, por ejemplo ("EURUSD", "GBPUSD", "GOLD").
    simbolos_permitidos: tuple | None = None
    # Lista negra opcional: símbolos que NUNCA se operan aunque existan en MT5.
    simbolos_bloqueados: tuple = ()


# Instancia única de límites que importan validación, propuestas, envío y vigilancia.
LIMITES = LimitesRiesgo()

# Número mágico: permite reconocer en MT5 las órdenes de este agente.
MAGIC = 940731  # identifica en MT5 las órdenes enviadas desde este módulo
# Multiplicador de holgura sobre los límites de riesgo al validar con precio actualizado.
TOLERANCIA_RIESGO = 1.10  # al confirmar, el precio pudo moverse: se tolera hasta +10 % sobre el límite
# Multiplicador máximo del riesgo real frente al riesgo aprobado en la propuesta.
TOLERANCIA_VS_PROPUESTA = 1.25  # al confirmar, el riesgo real no puede superar en más de 25 % lo que vio el usuario


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara limites .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
