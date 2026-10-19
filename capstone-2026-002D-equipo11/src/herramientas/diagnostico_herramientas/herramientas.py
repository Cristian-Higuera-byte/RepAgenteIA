# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara herramientas .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Herramientas registradas para el agente (los esquemas viven en esquemas.json).

Herramienta de diagnóstico holístico que combina MT5 (cuenta, posiciones, precio), indicadores
técnicos, análisis de riesgo y noticias (Investing.com y Yahoo Finance) en un solo informe.
"""
from __future__ import annotations

from typing import Any

from database.scripts.fuentes import investing_fuente as inv_fuente
from database.scripts.fuentes import mt5_fuentes as mt5_fuente
from database.scripts.fuentes import yfinance_fuente as yf_fuente
from herramientas import analisis_herramientas
from herramientas.base import herramienta
from herramientas.diagnostico_herramientas.auxiliares import _mapear_simbolo_yfinance


@herramienta(
    descripcion=(
        "Realiza un diagnóstico integral (holístico) de una posición abierta o un activo en MT5. "
        "Consolida exposición actual, análisis de riesgo (distancia a SL/TP, % equidad), "
        "volatilidad (ATR), indicadores técnicos (RSI, MACD, Medias Móviles), contexto de noticias "
        "macroeconómicas de Investing.com/Yahoo Finance y una matriz de 3 escenarios (Alcista, Neutral, Bajista)."
    ),
    parametros={
        "simbolo": {
            "type": "string",
            "description": "Símbolo del activo a diagnosticar (ej. 'EURUSD', 'USDCLP', 'GOLD').",
        },
        "timeframe": {
            "type": "string",
            "enum": list(mt5_fuente.TIMEFRAMES),
            "description": "Temporalidad técnica principal para el diagnóstico (por defecto 'H1').",
        },
    },
    requeridos=["simbolo"],
    nombre="analizar_posicion_holistica",
)
def analizar_posicion_holistica(
    simbolo: str,
    timeframe: str = "H1",
) -> dict[str, Any]:
    """Genera un diagnóstico integral de un símbolo (con o sin posición abierta en MT5).

    Recibe `simbolo` y `timeframe` (H1 por defecto). Reúne: equidad y posición activa, indicadores
    técnicos (cantidad fija de 300 velas), análisis de riesgo de la posición, hasta 4 noticias y tres
    escenarios (alcista, neutral, bajista) basados en 1.5 x ATR con su impacto en dinero según MT5.
    Sin posición abierta, el impacto se ilustra con 0.1 lotes de compra hipotéticos. Efectos
    secundarios: consultas a MT5, Investing.com y Yahoo Finance (los fallos de noticias se ignoran).
    """
    simbolo_clean = simbolo.strip().upper()

    # 1. Obtener datos de MT5 (Cuenta y Posiciones)
    cuenta = mt5_fuente.cuenta()
    equidad = cuenta.get("equidad") or 1.0

    posiciones_resp = mt5_fuente.posiciones(simbolo=simbolo_clean)
    posiciones_lista = posiciones_resp.get("posiciones", [])

    # Si hay varias posiciones del símbolo, solo se toma la primera para el diagnóstico.
    posicion_activa = posiciones_lista[0] if posiciones_lista else None

    # 2. Análisis Técnico e Indicadores
    ind_tecnicos = analisis_herramientas.calcular_indicadores_tecnicos(
        simbolo=simbolo_clean, timeframe=timeframe, cantidad=300
    )

    # Si los indicadores no dieron precio, se consulta el ask actual a MT5.
    precio_actual = ind_tecnicos.get("precio_actual")
    if not precio_actual:
        precio_info = mt5_fuente.precio(simbolo_clean)
        precio_actual = precio_info.get("ask", 0.0)

    # 3. Evaluación de Riesgo de la Posición
    riesgo_info = None
    if posicion_activa:
        riesgo_resp = analisis_herramientas.analizar_riesgo_posicion(simbolo=simbolo_clean)
        if riesgo_resp.get("posiciones"):
            riesgo_info = riesgo_resp["posiciones"][0]

    # 4. Contexto Macro / Noticias (Investing + YFinance)
    # Primero Investing.com; si no trae nada, respaldo con Yahoo Finance. Los errores se ignoran.
    noticias_list = []
    try:
        inv_res = inv_fuente.buscar_noticias(busqueda=simbolo_clean, categoria="forex", cantidad=3)
        noticias_list.extend(inv_res.get("noticias", []))
    except Exception:
        pass

    if not noticias_list:
        try:
            yf_sym = _mapear_simbolo_yfinance(simbolo_clean)
            yf_news = yf_fuente.noticias(yf_sym, cantidad=3)
            noticias_list.extend(yf_news)
        except Exception:
            pass

    # 5. Generación de Escenarios (Alcista / Neutral / Bajista)
    atr_data = ind_tecnicos.get("indicadores", {}).get("atr_14", {})
    # Si no hay ATR se usa 0.5% del precio como amplitud de referencia.
    atr_val = atr_data.get("valor_absoluto") or (precio_actual * 0.005)

    lotes_pos = posicion_activa.get("lotes", 0.1) if posicion_activa else 0.1
    tipo_pos = posicion_activa.get("tipo", "COMPRA") if posicion_activa else "COMPRA"
    hipotetico = posicion_activa is None   # sin posición abierta se ilustra con 0.1 lotes de compra

    def impacto(precio_destino: float) -> float | None:
        """Devuelve el resultado en dinero que calcula MT5 si el precio va del actual al proyectado (None si MT5 no puede calcularlo)."""
        try:
            return mt5_fuente.resultado_si_precio(simbolo_clean, tipo_pos, lotes_pos, precio_actual, precio_destino)
        except mt5_fuente.ErrorMT5:
            return None

    # Precios objetivo a +/- 1.5 ATR del precio actual.
    sube = precio_actual + atr_val * 1.5
    baja = precio_actual - atr_val * 1.5
    escenarios = [
        {
            "escenario": "Alcista",
            "condicion_tecnica": f"Supera resistencia a +{round(atr_val * 1.5, 4)}",
            "precio_proyectado": round(sube, 5),
            "impacto_estimado_usd": impacto(sube),
            "accion_sugerida": "Mantener / Buscar TP si es COMPRA; evaluar SL si es VENTA",
        },
        {
            "escenario": "Consolidación / Neutral",
            "condicion_tecnica": f"Mantener rango ±{round(atr_val, 4)}",
            "precio_proyectado": round(precio_actual, 5),
            "impacto_estimado_usd": 0.0,
            "accion_sugerida": "Ajustar Trailing Stop y vigilar ruptura de rango",
        },
        {
            "escenario": "Bajista",
            "condicion_tecnica": f"Quiebre de soporte a -{round(atr_val * 1.5, 4)}",
            "precio_proyectado": round(baja, 5),
            "impacto_estimado_usd": impacto(baja),
            "accion_sugerida": "Evaluar cierre o cobertura si rompe soporte clave",
        },
    ]
    # Aclaración para el modelo: son escenarios de referencia, no pronósticos.
    nota_escenarios = (
        "Escenarios de referencia basados en 1.5 x ATR (no son predicciones ni tienen probabilidad). "
        + ("Impacto calculado para una posición HIPOTÉTICA de 0.1 lotes de compra: no hay posición abierta."
           if hipotetico else "Impacto calculado sobre la posición abierta, con el cálculo de MT5.")
    )

    return {
        "fuente": "Módulo Diagnóstico Holístico (MT5 + YFinance + Investing)",
        "simbolo": simbolo_clean,
        "timeframe": timeframe,
        "equidad_cuenta_usd": equidad,
        "posicion_activa": {
            "tiene_posicion_abierta": posicion_activa is not None,
            "detalle_posicion": posicion_activa,
            "analisis_riesgo": riesgo_info,
        },
        "tecnico": ind_tecnicos,
        "noticias_fundamentales": noticias_list[:4],
        "matriz_escenarios": escenarios,
        "nota_escenarios": nota_escenarios,
    }


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara herramientas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
