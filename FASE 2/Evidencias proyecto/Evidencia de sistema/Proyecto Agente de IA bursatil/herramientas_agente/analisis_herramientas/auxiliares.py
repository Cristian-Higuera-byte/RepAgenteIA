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

Implementa en Python puro los indicadores técnicos clásicos (SMA, EMA, RSI, ATR, MACD, Bandas de
Bollinger) sobre listas de precios ordenadas de la vela más antigua a la más reciente.
"""
from __future__ import annotations

import math


# TITULO SMA

def _sma(valores: list[float], periodo: int) -> float | None:
    """Media móvil simple de las últimas `periodo` cotizaciones; None si no hay suficientes datos."""
    if len(valores) < periodo:
        return None
    return sum(valores[-periodo:]) / periodo


# TITULO EMA SERIE

def _ema_serie(valores: list[float], periodo: int) -> list[float]:
    """Calcula la serie completa de la media móvil exponencial (EMA) de `valores`.

    La primera EMA se siembra con la SMA de las primeras `periodo` cotizaciones y luego se aplica
    el factor de suavizado k = 2 / (periodo + 1). Devuelve una lista de longitud
    len(valores) - periodo + 1, o vacía si no hay datos suficientes.
    """
    if len(valores) < periodo:
        return []
    # Factor de suavizado estándar de la EMA.
    k = 2 / (periodo + 1)
    ema_list = [sum(valores[:periodo]) / periodo]
    for v in valores[periodo:]:
        ema_list.append((v * k) + (ema_list[-1] * (1 - k)))
    return ema_list


# TITULO RSI

def _rsi(cierres: list[float], periodo: int = 14) -> float | None:
    """Índice de Fuerza Relativa (RSI) de Wilder sobre los cierres, redondeado a 2 decimales.

    Devuelve un valor entre 0 y 100 (100 si no hubo pérdidas) o None si hay `periodo` cierres o menos.
    """
    # 1. Ganancias y pérdidas de cada variación entre cierres consecutivos.
    if len(cierres) <= periodo:
        return None
    gains, losses = [], []
    for i in range(1, len(cierres)):
        diferencia = cierres[i] - cierres[i - 1]
        gains.append(max(0.0, diferencia))
        losses.append(max(0.0, -diferencia))

    # 2. Promedios iniciales (simples) y luego suavizado de Wilder sobre el resto de la serie.
    promedio_gain = sum(gains[:periodo]) / periodo
    promedio_loss = sum(losses[:periodo]) / periodo

    for i in range(periodo, len(gains)):
        promedio_gain = (promedio_gain * (periodo - 1) + gains[i]) / periodo
        promedio_loss = (promedio_loss * (periodo - 1) + losses[i]) / periodo

    # 3. Fuerza relativa y transformación al rango 0-100.
    if promedio_loss == 0:
        return 100.0
    rs = promedio_gain / promedio_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


# TITULO ATR

def _atr(maximos: list[float], minimos: list[float], cierres: list[float], periodo: int = 14) -> float | None:
    """Rango Verdadero Promedio (ATR) de Wilder: medida de volatilidad en unidades de precio.

    Recibe listas de máximos, mínimos y cierres alineadas. Devuelve None si hay `periodo` velas o menos.
    """
    if len(cierres) <= periodo:
        return None
    # Rango verdadero de cada vela: el mayor entre su rango y los saltos contra el cierre previo.
    tr_list = []
    for i in range(1, len(cierres)):
        tr = max(
            maximos[i] - minimos[i],
            abs(maximos[i] - cierres[i - 1]),
            abs(minimos[i] - cierres[i - 1]),
        )
        tr_list.append(tr)

    # Promedio inicial y suavizado de Wilder.
    atr = sum(tr_list[:periodo]) / periodo
    for i in range(periodo, len(tr_list)):
        atr = (atr * (periodo - 1) + tr_list[i]) / periodo
    return atr


# TITULO MACD

def _macd(cierres: list[float], rapida: int = 12, lenta: int = 26, senal: int = 9) -> tuple[float | None, float | None, float | None]:
    """Calcula el MACD (EMA rápida - EMA lenta), su línea de señal y el histograma.

    Devuelve (macd, señal, histograma) con el último valor de cada serie, o (None, None, None) si
    faltan datos (se necesitan al menos lenta + senal cierres).
    """
    if len(cierres) < lenta + senal:
        return None, None, None
    ema_rapida = _ema_serie(cierres, rapida)
    ema_lenta = _ema_serie(cierres, lenta)

    # Se alinean ambas EMA por el final (la rápida es más larga) y se restan para obtener la línea MACD.
    diferencia_len = len(ema_rapida) - len(ema_lenta)
    macd_linea = [r - l for r, l in zip(ema_rapida[diferencia_len:], ema_lenta)]

    # La línea de señal es una EMA de la propia línea MACD.
    signal_linea_list = _ema_serie(macd_linea, senal)
    if not signal_linea_list:
        return None, None, None

    macd_valor = macd_linea[-1]
    signal_valor = signal_linea_list[-1]
    historial_valor = macd_valor - signal_valor
    return macd_valor, signal_valor, historial_valor


# TITULO BOLLINGER

def _bollinger(cierres: list[float], periodo: int = 20, desv: float = 2.0) -> tuple[float | None, float | None, float | None]:
    """Bandas de Bollinger: devuelve (superior, media, inferior) sobre los últimos `periodo` cierres.

    La banda se separa de la media `desv` desviaciones estándar poblacionales. Devuelve
    (None, None, None) si no hay datos suficientes.
    """
    if len(cierres) < periodo:
        return None, None, None
    subtitulo = cierres[-periodo:]
    sma = sum(subtitulo) / periodo
    varianza = sum((x - sma) ** 2 for x in subtitulo) / periodo
    std = math.sqrt(varianza)
    return sma + (desv * std), sma, sma - (desv * std)


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
