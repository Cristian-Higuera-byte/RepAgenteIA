# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara precarga .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Precarga en segundo plano de las secciones lentas, para que al abrirlas la primera vez se dibujen al instante.

MULTIUSUARIO: Noticias y Mercados son datos públicos y se precargan una sola vez por proceso; el Diario es de cada cuenta,
así que se precarga una vez por usuario y modo (demo o real), con la sesión de Capital de ESE usuario.

Algunas secciones tardaban segundos (hasta decenas) en su primera visita porque ese era el momento en que empezaban a leer sus
datos: el catálogo de instrumentos del buscador, las fuentes de noticias, los instrumentos y series de Mercados y el detalle de cada operación del Diario. Aquí se lanzan
todas esas lecturas apenas el usuario inicia sesión, en hilos de fondo (con la mitad del cupo de peticiones de Capital.com, para
no quitarle velocidad a lo que está viendo). Se hace una sola vez por proceso; si el usuario abre la sección antes de que termine,
cada una muestra un aviso de carga en vez de bloquear la página.
"""
import threading
import time

from herramientas.backends import sesiones_capital
from herramientas.hilos import lanzar_hilo

# Cuentas para las que ya se lanzó la precarga en este proceso (la comparten todas las sesiones) y su candado.
_LANZADAS: set = set()
_CANDADO = threading.Lock()
# Segundos de espera antes de empezar, para que la primera página se dibuje sin competir por la red.
_RETRASO_S = 1.5


# TITULO MARCAR FONDO

def _marcar_fondo() -> None:
    """Marca el hilo actual como de segundo plano para el limitador de peticiones de Capital.com (no hace nada con MT5)."""
    try:
        from herramientas.puente_mt5 import PROVEEDOR
        if PROVEEDOR == "capital":
            from herramientas.backends.capital import marcar_hilo_fondo
            marcar_hilo_fondo()
    except Exception:  # noqa: BLE001 - sin limitador no hay nada que marcar
        pass


# TITULO PRECARGAR CATALOGO

def _precargar_catalogo() -> None:
    """Pone en marcha la lectura del catálogo completo de instrumentos del broker (la que usa el buscador de activos). Es
    inmediata: el recorrido del árbol de Capital.com sigue en su propio hilo y deja el resultado en disco para los próximos
    arranques. Con MT5, que no tiene ese catálogo en segundo plano, no hace nada."""
    from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]
    leer = getattr(mt5, "catalogo_actual", None)
    if leer is not None:
        leer()


# TITULO PRECARGAR DIARIO

def _precargar_diario() -> None:
    """Calcula el Diario una vez para que el detalle de cada operación cerrada (que se guarda en disco) ya esté listo al abrirlo."""
    _marcar_fondo()
    from herramientas import estadisticas_diario
    estadisticas_diario.calcular()


# TITULO TAREA

def _tarea(primera_del_proceso: bool) -> None:
    """Cuerpo del hilo de precarga: espera un momento y lanza, cada una a su ritmo y sin que un fallo detenga a las demás, la precarga
    del catálogo de instrumentos (buscador), de Noticias, de Mercados y del Diario. Noticias y Mercados solo si es la primera precarga
    del proceso (son datos públicos)."""
    time.sleep(_RETRASO_S)
    try:
        _precargar_catalogo()
    except Exception:  # noqa: BLE001
        pass
    if primera_del_proceso:
        try:
            from componentes_plataforma.noticias.rss import precargar as precargar_noticias
            precargar_noticias()
        except Exception:  # noqa: BLE001
            pass
        try:
            from componentes_plataforma.mercados.secciones import precargar_todas_las_categorias
            precargar_todas_las_categorias()
        except Exception:  # noqa: BLE001
            pass
    try:
        _precargar_diario()
    except Exception:  # noqa: BLE001
        pass


# TITULO INICIAR PRECARGAS

def iniciar_precargas() -> None:
    """Lanza la precarga de las secciones lentas en un hilo de fondo, una sola vez por cuenta (usuario y modo). No espera ni devuelve nada.

    El hilo atiende al usuario que lo lanzó: así el Diario se calcula con SU cuenta de Capital y no con la de otro."""
    clave = sesiones_capital.clave_actual()
    with _CANDADO:
        if clave in _LANZADAS:
            return
        primera = not _LANZADAS
        _LANZADAS.add(clave)
    lanzar_hilo(_tarea, primera, nombre="pj-precarga-secciones")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara precarga .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
