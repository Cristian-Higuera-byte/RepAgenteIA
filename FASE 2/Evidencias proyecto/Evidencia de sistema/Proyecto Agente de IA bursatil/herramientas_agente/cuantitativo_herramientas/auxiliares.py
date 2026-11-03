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

Traduce símbolos de MT5 a tickers de Yahoo Finance y obtiene retornos diarios (MT5 primero, Yahoo
Finance como respaldo) para las herramientas cuantitativas.
"""
from __future__ import annotations

from fuentes import mt5_fuentes as mt5_fuente
from fuentes import yfinance_fuente as yf_fuente


# TITULO MAPEAR SIMBOLO YF

def _mapear_simbolo_yf(simbolo: str) -> str:
    """Convierte un símbolo estilo MT5 al ticker equivalente de Yahoo Finance.

    Casos conocidos (EURUSD, USDCLP, GBPUSD, oro, WTI, BTCUSD) se mapean explícitamente; cualquier
    otro par de 6 letras recibe el sufijo "=X" (divisas) y el resto se devuelve en mayúsculas.
    """
    s = (simbolo or "").strip().upper().replace("/", "")
    if s == "EURUSD": return "EURUSD=X"
    if s == "USDCLP": return "USDCLP=X"
    if s == "GBPUSD": return "GBPUSD=X"
    if s in ("XAUUSD", "GOLD"): return "GC=F"
    if s in ("WTI", "CL"): return "CL=F"
    if s == "BTCUSD": return "BTC-USD"
    if not s.endswith("=X") and len(s) == 6 and s.isalpha():
        return f"{s}=X"
    return s


# TITULO OBTENER RETORNOS HISTORICOS

def _obtener_retornos_historicos(simbolo: str, cantidad: int = 100) -> list[float]:
    """Obtiene la serie de retornos diarios (variación relativa, no en %) de un activo.

    Recibe `simbolo` y `cantidad` de velas diarias. Primero intenta MT5 (velas D1); si devuelve menos
    de 10 cierres, recurre a Yahoo Finance (6 meses, 1d). Los errores de cada fuente se ignoran en
    silencio. Devuelve [] si hay menos de 2 cierres; si no, (cierre_i - cierre_i-1) / cierre_i-1.
    """
    s_clean = simbolo.strip().upper()
    cierres = []
    
    # Fuente primaria: velas diarias de MT5.
    try:
        resultado = mt5_fuente.velas(simbolo=s_clean, timeframe="D1", cantidad=cantidad, ultimas_velas=cantidad)
        cierres = [v["close"] for v in resultado.get("ultimas_velas", []) if v.get("close")]
    except Exception:
        pass

    # Respaldo: Yahoo Finance si MT5 no entregó datos suficientes.
    if not cierres or len(cierres) < 10:
        try:
            yahoo_simbolo = _mapear_simbolo_yf(s_clean)
            resultado_yahoo = yf_fuente.historico(simbolo=yahoo_simbolo, periodo="6mo", intervalo="1d", ultimas_velas=cantidad)
            cierres = [v["cierre"] for v in resultado_yahoo.get("ultimas_velas", []) if v.get("cierre")]
        except Exception:
            pass

    if len(cierres) < 2:
        return []

    # Retorno simple día a día.
    retornos = [(cierres[i] - cierres[i - 1]) / cierres[i - 1] for i in range(1, len(cierres))]
    return retornos


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
