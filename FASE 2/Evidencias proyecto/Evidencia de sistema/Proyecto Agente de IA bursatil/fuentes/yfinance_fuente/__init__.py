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

"""Fuente de datos: Yahoo Finance (librería yfinance).

Esta capa solo sabe OBTENER y NORMALIZAR datos. No conoce al modelo ni a las
herramientas: devuelve diccionarios/listas simples y lanza ValueError con un
mensaje claro cuando algo no existe (el registro de herramientas se lo pasa
al modelo para que pueda corregir el símbolo o explicárselo al usuario).

Símbolos de Yahoo:
    acciones  AAPL, MSFT        forex      EURUSD=X, USDCLP=X
    índices   ^GSPC, ^IXIC      cripto     BTC-USD
    materias primas  GC=F (oro), CL=F (petróleo)

Los datos son gratuitos y pueden llegar con retraso (hasta ~15 min según el mercado).

Prueba rápida (desde la raíz del proyecto):  python -m fuentes.yfinance_fuente

Archivos: constantes.py + datos.json, cache.py, utiles.py, mercado.py, fundamentales.py, noticias.py y __main__.py.

Este archivo es una fachada: reexporta las funciones públicas y los nombres privados que usan
otras capas o las pruebas, para que `from fuentes.yfinance_fuente import cotizacion` funcione sin
conocer en qué submódulo vive cada cosa. Los `# noqa: F401` evitan que el linter marque como
"sin usar" lo que solo se reexporta."""
# Constantes: periodos e intervalos válidos, aviso de retraso y mapas de campos.
from fuentes.yfinance_fuente.constantes import (
    AVISO_RETRASO,
    INTERVALOS,
    PERIODOS,
    _CAMPOS_NUMERO,
    _CAMPOS_TEXTO,
    _ESTADOS,
)  # noqa: F401
# Caché en memoria con vencimiento.
from fuentes.yfinance_fuente.cache import (
    _CACHE,
    _cacheado,
)  # noqa: F401
# Utilidades de normalización de símbolos, números, campos y fechas.
from fuentes.yfinance_fuente.utiles import (
    _entero,
    _formatear_fecha,
    _leer,
    _num,
    _simbolo,
    _sin_nulos,
    _validar_fecha,
)  # noqa: F401
# Búsqueda de símbolos, cotización actual e histórico.
from fuentes.yfinance_fuente.mercado import (
    buscar,
    cotizacion,
    historico,
)  # noqa: F401
# Fundamentales de la empresa y estados financieros.
from fuentes.yfinance_fuente.fundamentales import (
    estados_financieros,
    fundamentales,
)  # noqa: F401
# Noticias del símbolo y consenso de analistas.
from fuentes.yfinance_fuente.noticias import (
    consenso_analistas,
    noticias,
    _normalizar_noticia,
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
