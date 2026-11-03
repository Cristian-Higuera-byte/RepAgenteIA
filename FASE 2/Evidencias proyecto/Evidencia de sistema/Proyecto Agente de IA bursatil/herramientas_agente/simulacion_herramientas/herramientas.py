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

"""Herramientas registradas para el agente de simulación (los esquemas viven en esquemas.json).

Registra ``simular_escenario_cartera``, que proyecta el efecto de variaciones
porcentuales hipotéticas sobre las posiciones abiertas de MT5.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fuentes import investing_fuente as inv_fuente
from fuentes import mt5_fuentes as mt5_fuente
from herramientas_agente.base import cargar_json, herramienta
from herramientas_agente.simulacion_herramientas.auxiliares import (
    ELASTICIDAD_CRUZADA,
    _estimar_tamano_contrato,
    _normalizar_simbolo,
)

# Esquemas (descripción y parámetros) de la herramienta, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


# TITULO SIMULAR ESCENARIO CARTERA

@herramienta(**_ESQ["simular_escenario_cartera"])
def simular_escenario_cartera(
    variaciones_pct: str | dict[str, float],
    incluir_noticias_contexto: bool = True,
) -> dict[str, Any]:
    """Simula el efecto de variaciones porcentuales hipotéticas sobre la cartera abierta.

    Recibe ``variaciones_pct`` (diccionario o texto JSON/"SIMBOLO:valor" con la
    variación % por activo) e indica si se incluyen noticias de contexto. Lee la
    cuenta y las posiciones de MT5; a cada posición le aplica la variación directa
    o, si no hay, una indirecta por elasticidad cruzada; calcula el cambio de PnL por valor
    nocional estimado, la equidad y el nivel de margen proyectados y un estado de
    riesgo (stop out, margin call, drawdown, etc.). Opcionalmente busca noticias en
    Investing.com. No ejecuta operaciones. Devuelve el resumen de cartera,
    el impacto por posición y las noticias (hasta 5).
    """
    # Parsear parámetro de entrada
    if isinstance(variaciones_pct, str):
        try:
            variaciones_dict: dict[str, float] = json.loads(variaciones_pct)
        except Exception:
            # Fallback para cadenas simples tipo "USDCLP:3.0"
            variaciones_dict = {}
            for par in variaciones_pct.replace("{", "").replace("}", "").split(","):
                if ":" in par:
                    k, v = par.split(":", 1)
                    variaciones_dict[k.strip().replace('"', '')] = float(v.strip())
    else:
        variaciones_dict = variaciones_pct

    # Normaliza los símbolos de las variaciones para poder compararlos con las posiciones.
    variaciones_norm = {_normalizar_simbolo(k): float(v) for k, v in variaciones_dict.items()}

    # Obtener estado actual de la cuenta y posiciones
    cuenta = mt5_fuente.cuenta()
    posiciones_data = mt5_fuente.posiciones()

    equidad_actual = cuenta.get("equidad") or 0.0
    margen_usado = cuenta.get("margen_usado") or 0.0
    nivel_margen_actual = cuenta.get("nivel_margen_pct", cuenta.get("nivel_margen")) or 0.0

    # Lista de posiciones y acumuladores del desglose y del PnL simulado.
    posiciones = posiciones_data.get("posiciones", [])

    desglose_posiciones = []
    ganancia_perdida_simulado_total = 0.0

    # Proyecta cada posición por separado.
    for posicion in posiciones:
        ticket = posicion["ticket"]
        simbolo_raw = posicion["simbolo"]
        simbolo_norm = _normalizar_simbolo(simbolo_raw)
        tipo = posicion["tipo"]  # "COMPRA" o "VENTA"
        lotes = posicion["lotes"]
        precio_act = posicion["precio_actual"]
        ganancia_perdida_actual = posicion["beneficio"]

        # Determinar la variación porcentual proyectada para este activo
        variacion_porcentaje_aplicada = 0.0
        tipo_impacto = "NINGUNO"

        if simbolo_norm in variaciones_norm:
            # Impacto directo
            variacion_porcentaje_aplicada = variaciones_norm[simbolo_norm]
            tipo_impacto = "DIRECTO"
        else:
            # Impacto indirecto vía sensibilidad / correlación
            for causa, variacion_causa in variaciones_norm.items():
                if causa in ELASTICIDAD_CRUZADA and simbolo_norm in ELASTICIDAD_CRUZADA[causa]:
                    beta = ELASTICIDAD_CRUZADA[causa][simbolo_norm]
                    variacion_porcentaje_aplicada = variacion_causa * beta
                    tipo_impacto = f"INDIRECTO (vía {causa}, Beta={beta})"
                    break

        # Cálculo del cambio de PnL (valor nocional x variación x signo según compra o venta)
        contract_tamano = _estimar_tamano_contrato(simbolo_raw)
        valor_nocional = precio_act * lotes * contract_tamano
        
        # En COMPRA: subida (+%) es ganancia. En VENTA: subida (+%) es pérdida.
        multiplicador_tipo = 1.0 if tipo == "COMPRA" else -1.0
        delta_ganancia_perdida = valor_nocional * (variacion_porcentaje_aplicada / 100.0) * multiplicador_tipo
        ganancia_perdida_proyectado = ganancia_perdida_actual + delta_ganancia_perdida
        ganancia_perdida_simulado_total += delta_ganancia_perdida

        desglose_posiciones.append({
            "ticket": ticket,
            "simbolo": simbolo_raw,
            "tipo": tipo,
            "lotes": lotes,
            "precio_actual": precio_act,
            "variacion_simulada_pct": round(variacion_porcentaje_aplicada, 2),
            "tipo_impacto": tipo_impacto,
            "pnl_flotante_actual_usd": round(ganancia_perdida_actual, 2),
            "impacto_estimado_usd": round(delta_ganancia_perdida, 2),
            "pnl_flotante_proyectado_usd": round(ganancia_perdida_proyectado, 2),
        })

    # Recálculo de métricas de cuenta (equidad, nivel de margen = equidad / margen usado)
    equidad_proyectada = equidad_actual + ganancia_perdida_simulado_total
    
    nivel_margen_proyectado = (
        round((equidad_proyectada / margen_usado) * 100.0, 2)
        if margen_usado > 0
        else 999.0
    )

    variacion_equidad_porcentaje = (
        round(((equidad_proyectada - equidad_actual) / equidad_actual) * 100.0, 2)
        if equidad_actual > 0
        else 0.0
    )

    # Evaluación de estado de riesgo con umbrales de margen (50 % y 100 %) y de caída de equidad (15 %)
    if nivel_margen_proyectado <= 50.0:
        estado_riesgo = "CRÍTICO - STOP OUT (Riesgo inminente de liquidación forzosa)"
    elif nivel_margen_proyectado <= 100.0:
        estado_riesgo = "ALERTA - MARGIN CALL (Insuficiencia de margen libre)"
    elif variacion_equidad_porcentaje <= -15.0:
        estado_riesgo = "ADVERTENCIA - DRAWDOWN ELEVADO (>15% de la equidad)"
    elif variacion_equidad_porcentaje < 0:
        estado_riesgo = "MODERADO - Impacto negativo controlado"
    else:
        estado_riesgo = "POSITIVO - Impacto favorable en cartera"

    # Noticias macro de contexto (vía Investing.com)
    noticias_contexto = []
    if incluir_noticias_contexto:
        for causa in variaciones_norm.keys():
            try:
                # Búsqueda de noticias relacionadas
                resultado_noticias = inv_fuente.buscar_noticias(busqueda=causa, categoria="forex", cantidad=3)
                noticias_contexto.extend(resultado_noticias.get("noticias", []))
            except Exception:
                pass

    return {
        "fuente": f"Motor de Simulación {mt5_fuente.NOMBRE_FUENTE} + Investing.com",
        "escenario_simulado": variaciones_norm,
        "resumen_cartera": {
            "equidad_actual_usd": round(equidad_actual, 2),
            "equidad_proyectada_usd": round(equidad_proyectada, 2),
            "variacion_equidad_usd": round(ganancia_perdida_simulado_total, 2),
            "variacion_equidad_pct": variacion_equidad_porcentaje,
            "nivel_margen_actual_pct": round(nivel_margen_actual, 2),
            "nivel_margen_proyectado_pct": nivel_margen_proyectado,
            "estado_riesgo_cartera": estado_riesgo,
        },
        "impacto_por_posicion": desglose_posiciones,
        "contexto_noticias_macro": noticias_contexto[:5],
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
