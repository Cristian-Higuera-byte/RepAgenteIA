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

Define los límites de riesgo (LimitesRiesgo) y las constantes de tolerancia y de identificación de órdenes en MT5. Los valores de riesgo ya NO están fijos en
el código: cada usuario decide los suyos (riesgo máximo por operación, riesgo total, pérdida diaria, volumen y apalancamiento máximos) y se guardan en el archivo
`limites_agente.json` de su carpeta. Un límite vacío (None) significa «sin límite»: por defecto el agente opera con el riesgo que el usuario le pida y no hay tope.
`limites_actuales()` devuelve los del usuario actual (los de `LIMITES` con lo que el usuario haya definido encima); `guardar_limites` los guarda.
Se siguen aplicando, porque no son de riesgo, que solo se opere en cuenta demo, la vigencia de las propuestas, el deslizamiento máximo y las listas de símbolos."""
import json
import os
import threading
from dataclasses import dataclass, replace

from herramientas.backends import sesiones_capital
from herramientas.carpeta_usuario import carpeta_de

# Nombre del archivo con los límites del usuario
_ARCHIVO = "limites_agente.json"
# Candado de las escrituras y caché de lecturas por archivo: ruta -> (fecha de modificación, límites)
_CANDADO = threading.Lock()
_CACHE: dict = {}


# TITULO LIMITES RIESGO

@dataclass(frozen=True)
class LimitesRiesgo:
    """Conjunto inmutable (frozen) de límites que aplican las validaciones de órdenes.

    Cada campo se comenta con su unidad; None en un límite de riesgo significa «sin límite». `LIMITES` son los valores base; los de cada usuario salen de
    `limites_actuales()`."""
    solo_demo: bool = True                       # rechaza TODO si la cuenta conectada no es demo
    riesgo_max_por_operacion_pct: float | None = None   # % del equity que se puede perder si salta el SL (None = sin límite)
    riesgo_max_total_pct: float | None = None           # % del equity en riesgo sumando posiciones abiertas + propuestas pendientes + la nueva (None = sin límite)
    max_posiciones_abiertas: int | None = None          # None = sin tope de posiciones abiertas
    perdida_max_diaria_pct: float | None = None         # % del balance; al alcanzarlo no se abren más (None = sin límite)
    volumen_max: float | None = None                    # lotes máximos por orden (None = el máximo del bróker)
    apalancamiento_max: float | None = None             # exposición total (valor de las posiciones) ÷ equity; None = sin límite
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

# Campos que el usuario puede definir: clave -> (texto, unidad, tipo)
CAMPOS_EDITABLES = {
    "riesgo_max_por_operacion_pct": ("Riesgo máximo por operación", "% del equity", float),
    "riesgo_max_total_pct": ("Riesgo total máximo", "% del equity", float),
    "perdida_max_diaria_pct": ("Pérdida diaria máxima", "% del balance", float),
    "volumen_max": ("Volumen máximo por orden", "lotes", float),
    "apalancamiento_max": ("Apalancamiento máximo", "veces el equity", float),
    "max_posiciones_abiertas": ("Posiciones abiertas máximas", "posiciones", int),
}


# TITULO RUTA LIMITES

def _ruta() -> str:
    """Archivo con los límites del usuario actual: en la carpeta del usuario (un nivel sobre la de su cuenta demo o real en multiusuario)."""
    clave = sesiones_capital.clave_actual()
    carpeta = carpeta_de(clave)
    return os.path.join(os.path.dirname(carpeta) if len(clave) == 2 else carpeta, _ARCHIVO)


# TITULO LIMPIAR VALOR

def _limpiar(campo: str, valor):
    """Convierte `valor` al tipo del campo; None si es vacío, no es un número o no es mayor que cero (se toma como «sin límite»)."""
    tipo = CAMPOS_EDITABLES[campo][2]
    try:
        v = tipo(valor)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


# TITULO LIMITES ACTUALES

def limites_actuales() -> LimitesRiesgo:
    """Límites vigentes del usuario actual: los de `LIMITES` con encima lo que el usuario definió en su archivo. Sin archivo o con uno dañado, `LIMITES` (sin límites de riesgo)."""
    ruta = _ruta()
    try:
        fecha = os.path.getmtime(ruta)
    except OSError:
        return LIMITES
    with _CANDADO:
        guardado = _CACHE.get(ruta)
        if guardado and guardado[0] == fecha:
            return guardado[1]
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        efectivos = replace(LIMITES, **{c: _limpiar(c, datos.get(c)) for c in CAMPOS_EDITABLES}) if isinstance(datos, dict) else LIMITES
    except (OSError, ValueError):
        efectivos = LIMITES
    with _CANDADO:
        _CACHE[ruta] = (fecha, efectivos)
    return efectivos


# TITULO GUARDAR LIMITES

def guardar_limites(valores: dict) -> LimitesRiesgo:
    """Guarda los límites del usuario actual y devuelve los vigentes. `valores` es {campo: número o None}; un campo vacío, cero o negativo queda «sin límite»;
    los campos que no estén en `CAMPOS_EDITABLES` se ignoran. Escritura atómica."""
    limpios = {c: _limpiar(c, valores.get(c)) for c in CAMPOS_EDITABLES}
    ruta = _ruta()
    with _CANDADO:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta + ".tmp", "w", encoding="utf-8") as f:
            json.dump(limpios, f)
        os.replace(ruta + ".tmp", ruta)
        _CACHE.pop(ruta, None)
    return limites_actuales()

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
