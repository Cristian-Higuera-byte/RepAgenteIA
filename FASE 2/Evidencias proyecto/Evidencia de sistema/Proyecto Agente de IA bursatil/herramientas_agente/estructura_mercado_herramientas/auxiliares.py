# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara auxiliares .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Funciones y constantes auxiliares de las herramientas (sin registrar nada).

Obtiene velas OHLC con respaldo: MT5 primero y Yahoo Finance si MT5 no responde.
"""
from __future__ import annotations

from typing import Any

from fuentes import mt5_fuentes as mt5_fuente
from fuentes import yfinance_fuente as yf_fuente


# TITULO OBTENER VELAS HISTORICAS

def _obtener_velas_historicas(simbolo: str, timeframe: str = "H1", cantidad: int = 100) -> list[dict[str, Any]]:
    """Devuelve las últimas `cantidad` velas de un símbolo como lista de dicts (time, open, high, low, close, tick_volume).

    Intenta MT5 y, si no hay velas, Yahoo Finance (periodo 1 mes; intervalo 1h si la temporalidad
    contiene "H", si no 1d), normalizando sus claves en español al formato de MT5. Los errores se
    ignoran y puede devolverse una lista vacía. Efecto secundario: consultas de red.
    """
    s_clean = simbolo.strip().upper()
    velas = []

    # Fuente primaria: MT5.
    try:
        resultado = mt5_fuente.velas(simbolo=s_clean, timeframe=timeframe, cantidad=cantidad, ultimas_velas=cantidad)
        velas = resultado.get("ultimas_velas", [])
    except Exception:
        pass

    # Respaldo: Yahoo Finance con el ticker equivalente (par de divisas con "=X", oro como GC=F).
    if not velas:
        try:
            yahoo_simbolo = s_clean
            if len(s_clean) == 6 and s_clean.isalpha() and not s_clean.endswith("=X"):
                yahoo_simbolo = f"{s_clean}=X"
            elif s_clean in ("XAUUSD", "GOLD"):
                yahoo_simbolo = "GC=F"

            temporalidad_yahoo = "1h" if "H" in timeframe.upper() else "1d"
            resultado_yahoo = yf_fuente.historico(simbolo=yahoo_simbolo, periodo="1mo", intervalo=temporalidad_yahoo, ultimas_velas=cantidad)
            # Se traducen las claves de Yahoo (fecha, apertura...) a las de MT5 (time, open...).
            for v in resultado_yahoo.get("ultimas_velas", []):
                velas.append({
                    "time": v.get("fecha"),
                    "open": v.get("apertura"),
                    "high": v.get("maximo"),
                    "low": v.get("minimo"),
                    "close": v.get("cierre"),
                    "tick_volume": v.get("volumen", 1000),
                })
        except Exception:
            pass

    return velas


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara auxiliares .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
