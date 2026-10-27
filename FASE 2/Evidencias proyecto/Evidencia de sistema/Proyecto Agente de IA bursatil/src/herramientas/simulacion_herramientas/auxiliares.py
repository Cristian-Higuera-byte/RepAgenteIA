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

"""Funciones y constantes auxiliares de la simulación de escenarios (sin registrar nada).

Contiene la matriz de elasticidades cruzadas entre activos y helpers para
normalizar símbolos y estimar el tamaño de contrato por lote.
"""
from __future__ import annotations

# ──────────────────────────────────────────────────────────────
# Matriz de Sensibilidad / Elasticidad Cruzada por Defecto
# ──────────────────────────────────────────────────────────────
# Muestra la elasticidad estimada (Beta cruzado) entre activos cuando no hay posición directa.
# Estructura: {activo que se mueve: {activo afectado: beta}}; valores aproximados fijos, no calculados.
ELASTICIDAD_CRUZADA: dict[str, dict[str, float]] = {
    "USDCLP": {
        "EURUSD": -0.30,  # Un alza de 1% en USD/CLP suele coincidir con -0.30% en EUR/USD (fortaleza del USD)
        "GBPUSD": -0.25,
        "XAUUSD": -0.20,
    },
    "EURUSD": {
        "GBPUSD": 0.80,   # Alta correlación positiva
        "USDCHF": -0.85,  # Correlación inversa fuerte
        "USDCLP": -0.40,
    },
    "CL=F": {             # Petróleo WTI
        "USDCAD": -0.55,  # Dólar canadiense se fortalece con el petróleo
    },
    "GC=F": {             # Oro
        "XAUUSD": 1.00,
        "USDJPY": -0.35,
    },
}


def _normalizar_simbolo(simbolo: str) -> str:
    """Devuelve el símbolo en mayúsculas sin "/" ni "-", unificando alias (GOLD a XAUUSD; OIL/WTI/CL a CL=F)."""
    s = (simbolo or "").strip().upper().replace("/", "").replace("-", "")
    if s in ("GOLD", "XAUUSD"):
        return "XAUUSD"
    if s in ("OIL", "WTI", "CL"):
        return "CL=F"
    return s


def _estimar_tamano_contrato(simbolo: str) -> float:
    """Estima las unidades por lote del símbolo según su tipo: oro 100, petróleo 1000, índices 10 y forex 100.000.

    Es una heurística por nombre, no el tamaño real de contrato del broker.
    """
    s = _normalizar_simbolo(simbolo)
    if "XAU" in s or "GOLD" in s:
        return 100.0  # 100 oz por lote
    if s.startswith("CL") or "OIL" in s:
        return 1000.0  # 1000 barriles
    if "US500" in s or "SPX" in s or "NAS100" in s:
        return 10.0
    return 100000.0  # Forex estándar: 100.000 unidades


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
