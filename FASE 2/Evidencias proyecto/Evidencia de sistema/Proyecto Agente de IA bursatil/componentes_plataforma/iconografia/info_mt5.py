# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara info_mt5 .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos del símbolo según MetaTrader 5 (carpeta y código bursátil), con caché.

Consulta MetaTrader 5 bajo su candado global; si MT5 no está disponible devuelve valores vacíos para que
el ícono caiga en las reglas por nombre.
"""
import re

# Caché símbolo -> (carpeta, ric); solo guarda respuestas reales de MT5, para reintentar si MT5 no estaba listo.
_INFO_CACHE: dict = {}


# TITULO INFO MT5

def info_mt5(simbolo: str) -> tuple:
    """(carpeta, ric) del símbolo según MT5. carpeta = primer nivel de `path`
    ("Stocks", "ETF Derivatives", "Cryptocurrencies"…); ric = código entre
    paréntesis al final de la descripción ("Adidas AG (ADSGn.DE)" -> "ADSGn.DE",
    "Telus Corp (TU)" -> "TU"). ("", "") si no hay MT5.
    Hallazgo: XM nombra las acciones por la empresa ("Adidas", "Nvidia"), sin
    sufijo de bolsa; el código bursátil solo está en la descripción.

    Efectos: consulta MT5 (con MT5_LOCK) la primera vez y guarda el resultado en `_INFO_CACHE`.
    """
    # Respuesta ya conocida: evita volver a consultar MT5.
    if simbolo in _INFO_CACHE:
        return _INFO_CACHE[simbolo]
    # Resultado por defecto si MT5 no está disponible o no conoce el símbolo.
    resultado = ("", "")
    try:
        # Importación diferida: MT5 solo existe en equipos con la terminal instalada.
        from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]
        from herramientas.puente_mt5 import MT5_LOCK, resolver_simbolo
        # Acceso serializado a la API de MT5 (no es segura entre hilos).
        with MT5_LOCK:
            info = mt5.symbol_info(resolver_simbolo(simbolo))
        if info is not None:
            # Primer nivel de la ruta del símbolo (chr(92) es la barra invertida).
            carpeta = (info.path or "").split(chr(92))[0]
            # Código entre paréntesis al final de la descripción.
            m = re.search(r"\(([A-Za-z0-9_]+(?:\.[A-Za-z]{1,3})?)\)\s*$", info.description or "")
            resultado = (carpeta, m.group(1) if m else "")
            _INFO_CACHE[simbolo] = resultado     # solo se guarda si MT5 respondió
    except Exception:
        # MT5 ausente o con error: se devuelve el valor vacío por defecto.
        pass
    return resultado


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara info_mt5 .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
