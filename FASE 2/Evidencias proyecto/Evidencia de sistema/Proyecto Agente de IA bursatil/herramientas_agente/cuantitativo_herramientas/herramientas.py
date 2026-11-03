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

Herramientas cuantitativas: matriz de correlación de Pearson, simulación Monte Carlo de la cartera
y métricas de rendimiento (Sharpe, Sortino, profit factor, win rate y VaR paramétrico).
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from fuentes import mt5_fuentes as mt5_fuente
from herramientas_agente.base import cargar_json, herramienta
from herramientas_agente.cuantitativo_herramientas.auxiliares import _obtener_retornos_historicos

# Esquemas (descripción y parámetros que ve el modelo) leídos de esquemas.json junto a este archivo.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


# TITULO CALCULAR MATRIZ CORRELACION

@herramienta(**_ESQ["calcular_matriz_correlacion"])
def calcular_matriz_correlacion(
    simbolos: str,
    cantidad_dias: int = 90,
) -> dict[str, Any]:
    """Calcula la matriz de correlación de Pearson entre los retornos diarios de varios símbolos.

    Recibe `simbolos` (texto separado por comas, mínimo 2) y `cantidad_dias` (90 por defecto).
    Descarta símbolos sin datos, recorta todas las series a la longitud común más corta y devuelve
    la matriz, los días usados y alertas para pares con correlación absoluta de 0.80 o más
    (posible sobreexposición). Devuelve {"error": ...} si no hay al menos 2 activos válidos.
    Efecto secundario: consultas a MT5 / Yahoo Finance.
    """
    lista_simbolos = [s.strip().upper() for s in simbolos.split(",") if s.strip()]
    if len(lista_simbolos) < 2:
        return {"error": "Se requieren al menos 2 símbolos para calcular la matriz de correlación."}

    # Retornos por símbolo; se omiten los que no devuelven datos.
    retornos_dict: dict[str, list[float]] = {}
    for simbolo in lista_simbolos:
        rets = _obtener_retornos_historicos(simbolo, cantidad=cantidad_dias)
        if rets:
            retornos_dict[simbolo] = rets

    activos_validos = list(retornos_dict.keys())
    if len(activos_validos) < 2:
        return {"error": "No se obtuvieron suficientes datos históricos para los símbolos indicados."}

    # Alinear longitud de retornos
    min_len = min(len(r) for r in retornos_dict.values())
    for k in activos_validos:
        retornos_dict[k] = retornos_dict[k][-min_len:]

    # Matriz simétrica y alertas de pares muy correlacionados.
    matriz: dict[str, dict[str, float]] = {}
    alertas_sobreexposicion: list[str] = []

    for s1 in activos_validos:
        matriz[s1] = {}
        r1 = retornos_dict[s1]
        m1 = mean(r1)
        sd1 = stdev(r1) if len(r1) > 1 else 1.0

        for s2 in activos_validos:
            if s1 == s2:
                matriz[s1][s2] = 1.0
                continue

            r2 = retornos_dict[s2]
            m2 = mean(r2)
            sd2 = stdev(r2) if len(r2) > 1 else 1.0

            # Covarianza muestral dividida por el producto de desviaciones = correlación de Pearson.
            cov = sum((x - m1) * (y - m2) for x, y in zip(r1, r2)) / (min_len - 1)
            corr = cov / (sd1 * sd2) if (sd1 * sd2) != 0 else 0.0
            corr_round = round(corr, 4)
            matriz[s1][s2] = corr_round

            # Solo se alerta una vez por par (orden alfabético) y con umbral de 0.80.
            if s1 < s2 and abs(corr_round) >= 0.80:
                rel = "positiva" if corr_round > 0 else "inversa"
                alertas_sobreexposicion.append(
                    f"Alta correlación {rel} ({corr_round}) entre {s1} y {s2}."
                )

    return {
        "fuente": "Módulo Cuantitativo (Pearson Correlation)",
        "activos_analizados": activos_validos,
        "dias_historicos": min_len,
        "matriz_correlacion": matriz,
        "alertas_sobreexposicion": alertas_sobreexposicion,
    }


# TITULO SIMULAR MONTE CARLO CARTERA

@herramienta(**_ESQ["simular_monte_carlo_cartera"])
def simular_monte_carlo_cartera(
    dias_proyeccion: int = 30,
    num_simulaciones: int = 1000,
    capital_inicial: float | None = None,
) -> dict[str, Any]:
    """Proyecta la cartera con una simulación Monte Carlo de movimiento browniano geométrico gaussiano.

    Recibe `dias_proyeccion` (30), `num_simulaciones` (1000) y `capital_inicial` (por defecto la
    equidad de MT5, o 10000 si no está disponible). El retorno medio y la volatilidad diarios se
    estiman con los retornos de los símbolos con posición abierta (EURUSD si no hay ninguna); sin
    datos se usan valores por defecto. Devuelve percentiles 5/50/95 del patrimonio final, el
    drawdown máximo del percentil 95 y la probabilidad de terminar bajo el capital inicial.
    Es aleatoria: cada llamada puede dar cifras ligeramente distintas. Consulta MT5 y Yahoo Finance.
    """
    cuenta = mt5_fuente.cuenta()
    capital = capital_inicial or cuenta.get("equidad") or 10000.0

    # Obtener volatilidad y retorno promedio de las posiciones de la cartera
    posiciones = mt5_fuente.posiciones().get("posiciones", [])
    simbolos_cartera = list({p["simbolo"] for p in posiciones}) if posiciones else ["EURUSD"]

    retornos_combinados: list[float] = []
    for s in simbolos_cartera:
        retornos_combinados.extend(_obtener_retornos_historicos(s, cantidad=60))

    if not retornos_combinados:
        mu = 0.0003  # ~0.03% promedio diario por defecto
        sigma = 0.008 # ~0.8% volatilidad diaria por defecto
    else:
        mu = mean(retornos_combinados)
        sigma = stdev(retornos_combinados) if len(retornos_combinados) > 1 else 0.01

    # Patrimonio final y drawdown máximo de cada trayectoria simulada.
    resultados_finales: list[float] = []
    max_drawdowns: list[float] = []

    for _ in range(num_simulaciones):
        patrimonio = capital
        pico = capital
        max_drawdown = 0.0

        # Cada día el patrimonio se multiplica por (1 + retorno aleatorio normal(mu, sigma)).
        for _ in range(dias_proyeccion):
            r = random.gauss(mu, sigma)
            patrimonio *= (1.0 + r)
            if patrimonio > pico:
                pico = patrimonio
            drawdown = (pico - patrimonio) / pico if pico > 0 else 0.0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        resultados_finales.append(patrimonio)
        max_drawdowns.append(max_drawdown)

    # Se ordenan para leer percentiles por índice.
    resultados_finales.sort()
    max_drawdowns.sort()

    porcentaje_5 = round(resultados_finales[int(num_simulaciones * 0.05)], 2)
    mediana = round(resultados_finales[int(num_simulaciones * 0.50)], 2)
    porcentaje_95 = round(resultados_finales[int(num_simulaciones * 0.95)], 2)
    peor_drawdown_esperado = round(max_drawdowns[int(num_simulaciones * 0.95)] * 100, 2)
    prob_pérdida = round(sum(1 for x in resultados_finales if x < capital) / num_simulaciones * 100, 2)

    return {
        "fuente": "Simulador de Monte Carlo (Geométrico Gaussiano)",
        "capital_inicial_usd": capital,
        "dias_proyeccion": dias_proyeccion,
        "simulaciones_ejecutadas": num_simulaciones,
        "parametros_estimados": {
            "retorno_diario_esperado_pct": round(mu * 100, 4),
            "volatilidad_diaria_pct": round(sigma * 100, 4),
        },
        "proyeccion_patrimonio_usd": {
            "escenario_pesimista_p5": porcentaje_5,
            "escenario_mediana_p50": mediana,
            "escenario_optimista_p95": porcentaje_95,
        },
        "metricas_riesgo_monte_carlo": {
            "max_drawdown_esperado_p95_pct": peor_drawdown_esperado,
            "probabilidad_capital_menor_inicial_pct": prob_pérdida,
        },
    }


# TITULO EVALUAR METRICAS RENDIMIENTO

@herramienta(**_ESQ["evaluar_metricas_rendimiento"])
def evaluar_metricas_rendimiento(
    tasa_libre_riesgo_anual: float = 0.04,
) -> dict[str, Any]:
    """Calcula métricas de rendimiento y riesgo: Sharpe, Sortino, profit factor, win rate y VaR 1 día.

    Recibe `tasa_libre_riesgo_anual` (0.04 por defecto). Si hay posiciones abiertas, usa el beneficio
    flotante de cada una dividido por la equidad como "retorno"; si no, usa los retornos diarios de
    EURUSD de los últimos 90 días. Sharpe y Sortino se anualizan con 252 días; el VaR es paramétrico
    (normal) al 95% y 99%. Devuelve {"error": ...} con menos de 2 datos. Consulta MT5 / Yahoo Finance.
    """
    posiciones = mt5_fuente.posiciones().get("posiciones", [])
    beneficios = [p.get("beneficio", 0.0) for p in posiciones]

    if not beneficios:
        # Si no hay operaciones abiertas, recopilar retornos de activos principales para estimar
        retornos = _obtener_retornos_historicos("EURUSD", cantidad=90)
    else:
        cuenta = mt5_fuente.cuenta()
        capital = cuenta.get("equidad") or 10000.0
        retornos = [b / capital for b in beneficios]

    if not retornos or len(retornos) < 2:
        return {"error": "Sin datos suficientes para calcular métricas cuantitativas."}

    # Tasa libre de riesgo diaria (base 252 días hábiles).
    r_diario_rf = tasa_libre_riesgo_anual / 252.0
    m_ret = mean(retornos)
    s_ret = stdev(retornos) if len(retornos) > 1 else 0.0001

    # Sharpe Ratio Anualizado
    sharpe = ((m_ret - r_diario_rf) / s_ret) * math.sqrt(252) if s_ret != 0 else 0.0

    # Sortino Ratio (considera solo volatilidad a la baja)
    retornos_negativos = [r for r in retornos if r < 0]
    s_baja = stdev(retornos_negativos) if len(retornos_negativos) > 1 else 0.0001
    sortino = ((m_ret - r_diario_rf) / s_baja) * math.sqrt(252) if s_baja != 0 else 0.0

    # Win Rate y Profit Factor
    ganadoras = [r for r in retornos if r > 0]
    perdedoras = [abs(r) for r in retornos if r < 0]
    win_rate = (len(ganadoras) / len(retornos)) * 100.0 if retornos else 0.0
    profit_factor = (sum(ganadoras) / sum(perdedoras)) if sum(perdedoras) > 0 else (999.0 if sum(ganadoras) > 0 else 0.0)

    # Value at Risk (VaR Paramétrico 95% y 99%)
    cuenta = mt5_fuente.cuenta()
    capital = cuenta.get("equidad") or 10000.0

    # Z de 95% = 1.645 y de 99% = 2.326; un VaR negativo se trunca a 0 al reportar.
    variacion_95_porcentaje = -(m_ret - (1.645 * s_ret))
    variacion_99_porcentaje = -(m_ret - (2.326 * s_ret))

    return {
        "fuente": "Evaluador de Métricas Cuantitativas",
        "capital_evaluado_usd": capital,
        "muestra_datos": len(retornos),
        "metricas_ratio": {
            "sharpe_ratio_anualizado": round(sharpe, 2),
            "sortino_ratio_anualizado": round(sortino, 2),
            "profit_factor": round(profit_factor, 2),
            "win_rate_pct": round(win_rate, 2),
        },
        "value_at_risk_1dia": {
            "var_95_pct": round(max(0.0, variacion_95_porcentaje * 100), 2),
            "var_95_usd": round(max(0.0, variacion_95_porcentaje * capital), 2),
            "var_99_pct": round(max(0.0, variacion_99_porcentaje * 100), 2),
            "var_99_usd": round(max(0.0, variacion_99_porcentaje * capital), 2),
        },
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
