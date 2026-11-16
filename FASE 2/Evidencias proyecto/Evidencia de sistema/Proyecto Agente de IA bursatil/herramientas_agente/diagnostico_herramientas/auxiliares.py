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

Contiene el traductor de símbolos MT5 a tickers de Yahoo Finance usado por el diagnóstico.
"""
from __future__ import annotations

# TITULO MAPEAR SIMBOLO YFINANCE

def _mapear_simbolo_yfinance(simbolo: str) -> str:
    """Convierte un símbolo estilo MT5 al ticker de Yahoo Finance (EURUSD a EURUSD=X, oro a GC=F, etc.).

    Los pares de 6 letras sin sufijo reciben "=X"; los demás símbolos se devuelven en mayúsculas.
    """
    s = (simbolo or "").strip().upper().replace("/", "")
    if s == "EURUSD":
        return "EURUSD=X"
    if s == "USDCLP":
        return "USDCLP=X"
    if s == "GBPUSD":
        return "GBPUSD=X"
    if s in ("XAUUSD", "GOLD"):
        return "GC=F"
    if s in ("WTI", "CL"):
        return "CL=F"
    if s == "BTCUSD":
        return "BTC-USD"
    if not s.endswith("=X") and len(s) == 6 and s.isalpha():
        return f"{s}=X"
    return s


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
