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

"""Fuente de datos: Investing.com (en español).

Esta capa solo se encarga de OBTENER y NORMALIZAR noticias macroeconómicas y
de mercados. No conoce al modelo ni a las herramientas: devuelve listas/dict
simples y lanza ErrorInvesting con un mensaje claro si ocurre algún fallo.

Feeds disponibles (Investing.com España):
    general, mercados, forex, acciones, cripto, economia

Prueba rápida (desde la raíz del proyecto):  python -m fuentes.investing_fuente

Archivos: constantes.py + datos.json, errores.py, cache.py, utiles.py, noticias.py y __main__.py.

Este archivo es una fachada: reexporta los nombres públicos (y los privados que
usan otras capas o las pruebas) desde los submódulos, de modo que el resto del
proyecto pueda hacer `from fuentes.investing_fuente import noticias` sin conocer
la organización interna del paquete. Los `# noqa: F401` evitan que el linter
marque como "sin usar" los nombres que solo se reexportan."""
# Constantes de la fuente: feeds RSS, aviso legal y cabeceras HTTP.
from fuentes.investing_fuente.constantes import (
    AVISO_FUENTE,
    FEEDS,
    CABECERAS,
)  # noqa: F401
# Excepción propia de la fuente.
from fuentes.investing_fuente.errores import (
    ErrorInvesting,
)  # noqa: F401
# Caché en memoria con vencimiento (diccionario y envoltorio).
from fuentes.investing_fuente.cache import (
    _CACHE,
    _cacheado,
)  # noqa: F401
# Utilidades de limpieza de textos y diccionarios.
from fuentes.investing_fuente.utiles import (
    _limpiar_html,
    _sin_nulos,
)  # noqa: F401
# Funciones públicas: lectura del RSS y búsqueda por palabra clave.
from fuentes.investing_fuente.noticias import (
    buscar_noticias,
    noticias,
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
