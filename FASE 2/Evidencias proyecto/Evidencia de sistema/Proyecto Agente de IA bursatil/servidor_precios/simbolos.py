# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara simbolos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Catálogo de símbolos del terminal (ventana "Comparar" del gráfico), con caché.

Lo consume la ruta GET /simbolos de manejador.py. El resultado se guarda en memoria
durante TTL_SIMBOLOS segundos para no recorrer todo el catálogo de MT5 en cada petición.
"""
import time

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]
from herramientas.puente_mt5 import inicializar_mt5

from .constantes import CANDADO_MT5, TTL_SIMBOLOS

# Caché del catálogo: "t" = instante (time.time) de la última carga exitosa, "datos" = lista [{n, d, c}]
_SIMBOLOS = {"t": 0.0, "datos": []}


# TITULO LISTAR SIMBOLOS

def listar_simbolos() -> list:
    """Catálogo de símbolos del terminal para la ventana "Comparar" del gráfico:
    n = nombre, d = descripción, c = categoría (primer tramo de la ruta del símbolo en MT5).

    Devuelve una lista de dicts {n, d, c} ordenada por nombre. Usa la caché de módulo
    mientras no supere TTL_SIMBOLOS; si no, consulta MT5 (con CANDADO_MT5) y la renueva.
    """
    # Si hay datos en caché y siguen frescos, los devuelve sin tocar MT5
    ahora = time.time()
    if _SIMBOLOS["datos"] and ahora - _SIMBOLOS["t"] < TTL_SIMBOLOS:
        return _SIMBOLOS["datos"]
    # Pide todos los símbolos al terminal bajo el candado compartido
    with CANDADO_MT5:
        inicializar_mt5()
        todos = mt5.symbols_get() or []
    # Normaliza cada símbolo: la categoría es el primer tramo de su ruta (Forex, Crypto...)
    datos = []
    for s in todos:
        ruta = (getattr(s, "path", "") or "").replace("\\", "/")
        datos.append({"n": s.name, "d": getattr(s, "description", "") or "", "c": ruta.split("/")[0] if "/" in ruta else ""})
    # Orden alfabético sin distinguir mayúsculas
    datos.sort(key=lambda x: x["n"].lower())
    # Solo cachea si hubo resultados (evita fijar una lista vacía por un fallo transitorio)
    if datos:
        _SIMBOLOS["t"], _SIMBOLOS["datos"] = ahora, datos
    return datos


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara simbolos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
