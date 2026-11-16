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

Contiene `calcular_indicadores_tecnicos` (RSI, ATR, MACD, medias móviles y Bollinger sobre velas de
MT5) y `analizar_riesgo_posicion` (riesgo en dinero, distancias a SL/TP y ratio R:B de las
posiciones abiertas). Los cálculos numéricos finos están en `auxiliares.py` y en `fuentes.mt5_fuentes`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fuentes import mt5_fuentes as fuente
from herramientas_agente.analisis_herramientas.auxiliares import (
    _atr,
    _bollinger,
    _ema_serie,
    _macd,
    _rsi,
    _sma,
)
from herramientas_agente.base import cargar_json, herramienta

# Esquemas (descripción y parámetros que ve el modelo) leídos de esquemas.json junto a este archivo.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


# TITULO CALCULAR INDICADORES TECNICOS

@herramienta(
    descripcion=(
        "Calcula indicadores técnicos clave en tiempo real sobre un activo del broker (Capital.com o MT5): "
        "RSI(14), ATR(14), MACD(12,26,9), Medias Móviles (EMA20, SMA50, SMA200) y Bandas de Bollinger(20,2)."
    ),
    parametros={
        "simbolo": {
            "type": "string",
            "description": "Símbolo del activo en el broker (ej. 'EURUSD', 'GOLD', 'US500').",
        },
        "timeframe": {
            "type": "string",
            "enum": list(fuente.TIMEFRAMES),
            "description": "Temporalidad para el cálculo (M1, M5, M15, M30, H1, H4, D1). Por defecto 'H1'.",
        },
        "cantidad": {
            "type": "integer",
            "description": "Número de velas históricas a evaluar (mínimo 250 recomendado). Por defecto 300.",
        },
    },
    requeridos=["simbolo"],
    nombre="calcular_indicadores_tecnicos",
)
def calcular_indicadores_tecnicos(
    simbolo: str,
    timeframe: str = "H1",
    cantidad: int = 300,
) -> dict[str, Any]:
    """Calcula indicadores técnicos de un símbolo con velas en vivo de MetaTrader 5.

    Recibe `simbolo`, `timeframe` (por defecto H1) y `cantidad` de velas (por defecto 300; se
    recomiendan 250 o más para que exista la SMA 200). Devuelve un dict con precio actual, RSI(14)
    con diagnóstico, ATR(14) absoluto y en %, MACD(12,26,9) con sesgo, EMA20/SMA50/SMA200 y Bandas
    de Bollinger(20,2); los indicadores sin datos suficientes quedan en None. Si MT5 no entrega
    velas devuelve {"error": ...}. Efecto secundario: consultas a MT5 (red/terminal).
    """
    # Primera consulta con una sola vela: sirve para obtener el nombre normalizado del símbolo.
    datos_velas = fuente.velas(simbolo=simbolo, timeframe=timeframe, cantidad=cantidad, ultimas_velas=1)
    
    # Segunda consulta con todo el historial pedido para alimentar los indicadores.
    # Extraer arrays de precios históricos
    velas_historicas = fuente.velas(simbolo=simbolo, timeframe=timeframe, cantidad=cantidad, ultimas_velas=cantidad)["ultimas_velas"]
    if not velas_historicas:
        return {"error": f"No se obtuvieron suficientes velas para {simbolo}."}

    cierres = [v["close"] for v in velas_historicas if v["close"] is not None]
    maximos = [v["high"] for v in velas_historicas if v["high"] is not None]
    minimos = [v["low"] for v in velas_historicas if v["low"] is not None]

    # El último cierre se toma como precio actual de referencia.
    precio_actual = cierres[-1]

    # 1. RSI
    rsi_valor = _rsi(cierres, 14)
    # Umbrales clásicos: 70 o más sobrecompra, 30 o menos sobreventa.
    estado_rsi = "NEUTRAL"
    if rsi_valor is not None:
        if rsi_valor >= 70:
            estado_rsi = "SOBRECOMPRA"
        elif rsi_valor <= 30:
            estado_rsi = "SOBREVENTA"

    # 2. ATR
    atr_valor = _atr(maximos, minimos, cierres, 14)

    # 3. MACD
    macd_valor, signal_valor, historial_valor = _macd(cierres)
    # El signo del histograma define el sesgo (positivo alcista, negativo bajista).
    sesgo_macd = "NEUTRAL"
    if historial_valor is not None:
        sesgo_macd = "ALCISTA" if historial_valor > 0 else "BAJISTA"

    # 4. Medias Móviles
    ema_20_list = _ema_serie(cierres, 20)
    ema_20 = round(ema_20_list[-1], 5) if ema_20_list else None

    sma_50_raw = _sma(cierres, 50)
    sma_200_raw = _sma(cierres, 200)
    sma_50 = round(sma_50_raw, 5) if sma_50_raw is not None else None
    sma_200 = round(sma_200_raw, 5) if sma_200_raw is not None else None

    # 5. Bandas de Bollinger
    b_sup, b_med, b_inf = _bollinger(cierres)

    # Respuesta final: valores redondeados a 5 decimales y diagnósticos en texto para el modelo.
    return {
        "fuente": fuente.NOMBRE_FUENTE,
        "simbolo": datos_velas["simbolo"],
        "timeframe": timeframe,
        "precio_actual": precio_actual,
        "indicadores": {
            "rsi_14": {
                "valor": rsi_valor,
                "diagnostico": estado_rsi,
            },
            "atr_14": {
                "valor_absoluto": round(atr_valor, 5) if atr_valor is not None else None,
                "volatilidad_pct": round((atr_valor / precio_actual) * 100, 2) if atr_valor else None,
            },
            "macd_12_26_9": {
                "linea_macd": round(macd_valor, 5) if macd_valor is not None else None,
                "linea_senal": round(signal_valor, 5) if signal_valor is not None else None,
                "histograma": round(historial_valor, 5) if historial_valor is not None else None,
                "sesgo": sesgo_macd,
            },
            "medias_moviles": {
                "ema_20": ema_20,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "precio_vs_sma200": "POR_ENCIMA (Tendencia Alcista)" if (sma_200 and precio_actual > sma_200) else "POR_DEBAJO (Tendencia Bajista)",
            },
            "bandas_bollinger_20_2": {
                "banda_superior": round(b_sup, 5) if b_sup else None,
                "banda_media": round(b_med, 5) if b_med else None,
                "banda_inferior": round(b_inf, 5) if b_inf else None,
            },
        },
    }


# TITULO ANALIZAR RIESGO POSICION

@herramienta(**_ESQ["analizar_riesgo_posicion"])
def analizar_riesgo_posicion(simbolo: str | None = None, ticket: int | None = None) -> dict[str, Any]:
    """Analiza el riesgo de las posiciones abiertas en MT5, opcionalmente filtradas por símbolo o ticket.

    Por cada posición calcula distancias a SL/TP (pips y %), riesgo y beneficio estimados en dinero
    (con el cálculo de beneficios del propio MT5), riesgo como % de la equidad, ratio riesgo/beneficio
    y estado del Stop Loss (ausente, activo o protegiendo ganancia). Devuelve además el riesgo total
    acumulado y avisos cuando hay posiciones sin SL (riesgo ilimitado, excluido del total) o sin cálculo.
    Efecto secundario: consultas a MT5.
    """
    # Datos base: equidad de la cuenta y posiciones abiertas.
    cuenta_info = fuente.cuenta()
    posiciones_info = fuente.posiciones(simbolo=simbolo)

    # Se evita división por cero usando 1.0 si la equidad no viene informada.
    equidad = cuenta_info.get("equidad") or 1.0
    posiciones_lista = posiciones_info.get("posiciones", [])

    # Filtro opcional por ticket concreto.
    if ticket:
        posiciones_lista = [p for p in posiciones_lista if p.get("ticket") == ticket]

    diagnosticos = []
    riesgo_total_usd = 0.0
    sin_stop = 0
    sin_calculo = 0

    # Diagnóstico posición por posición.
    for posicion in posiciones_lista:
        stop_loss = posicion["sl"]
        take_profit = posicion["tp"]
        try:
            d = fuente.distancias_y_riesgo(
                posicion["simbolo"], posicion["tipo"], posicion["lotes"], posicion["precio_apertura"], posicion["precio_actual"], stop_loss, take_profit,
            )
        except fuente.ErrorMT5:
            d = {}
        # Riesgo, beneficio objetivo y ratio R:B (solo si ambos importes existen).
        riesgo_usd = d.get("riesgo_usd")
        beneficio_usd = d.get("beneficio_objetivo_usd")
        ratio_riesgo_beneficio = round(beneficio_usd / riesgo_usd, 2) if riesgo_usd and beneficio_usd else None

        # Estado del Stop Loss: sin SL el riesgo es ilimitado; con SL en o sobre la apertura la posición está protegida.
        if not stop_loss:
            estado_stop_loss = "SIN STOP LOSS (ALTO RIESGO)"
            sin_stop += 1
        else:
            asegura = (posicion["tipo"] == "COMPRA" and stop_loss >= posicion["precio_apertura"]) or (
                posicion["tipo"] != "COMPRA" and stop_loss <= posicion["precio_apertura"])
            estado_stop_loss = "PROTEGIDO EN PROFIT" if asegura else "STOP LOSS ACTIVO"
            if riesgo_usd is None:
                sin_calculo += 1
            else:
                riesgo_total_usd += riesgo_usd

        diagnosticos.append({
            "ticket": posicion["ticket"],
            "simbolo": posicion["simbolo"],
            "tipo": posicion["tipo"],
            "lotes": posicion["lotes"],
            "precio_apertura": posicion["precio_apertura"],
            "precio_actual": posicion["precio_actual"],
            "pnl_flotante_usd": posicion["beneficio"],
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "distancia_sl_desde_precio_actual_pips": d.get("distancia_sl_desde_precio_actual_pips"),
            "distancia_sl_desde_precio_actual_pct": d.get("distancia_sl_desde_precio_actual_pct"),
            "distancia_sl_desde_apertura_pips": d.get("distancia_sl_desde_apertura_pips"),
            "distancia_tp_desde_precio_actual_pips": d.get("distancia_tp_desde_precio_actual_pips"),
            "distancia_tp_desde_apertura_pips": d.get("distancia_tp_desde_apertura_pips"),
            "riesgo_estimado_usd": riesgo_usd,
            "ganancia_asegurada_usd": d.get("ganancia_asegurada_usd"),
            "beneficio_estimado_usd": beneficio_usd,
            "riesgo_equidad_pct": round(riesgo_usd / equidad * 100, 2) if riesgo_usd else None,
            "ratio_riesgo_beneficio": ratio_riesgo_beneficio,
            "estado_stop_loss": estado_stop_loss,
        })

    # Resumen agregado sobre todas las posiciones analizadas.
    resultado = {
        "fuente": f"{fuente.NOMBRE_FUENTE} (riesgo calculado con el cálculo de beneficios del propio broker)",
        "equidad_cuenta_usd": equidad,
        "total_posiciones_analizadas": len(diagnosticos),
        "riesgo_total_acumulado_usd": round(riesgo_total_usd, 2),
        "riesgo_total_equidad_pct": round(riesgo_total_usd / equidad * 100, 2),
        "posiciones_sin_stop_loss": sin_stop,
        "nota_pips": "1 pip = 10 puntos en símbolos de 3 o 5 decimales; en el resto, 1 punto.",
        "posiciones": diagnosticos,
    }
    # Avisos para que el modelo advierta al usuario de lo que el total no incluye.
    if sin_stop:
        resultado["aviso"] = (
            f"{sin_stop} posición(es) sin Stop Loss: su riesgo es ilimitado y NO está incluido en el total."
        )
    if sin_calculo:
        resultado["aviso_calculo"] = (
            f"En {sin_calculo} posición(es) MT5 no pudo calcular el riesgo en dinero; no está incluido en el total."
        )
    return resultado


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
