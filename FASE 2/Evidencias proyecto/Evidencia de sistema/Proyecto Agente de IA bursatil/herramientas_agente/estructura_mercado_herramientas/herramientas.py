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

Herramientas de estructura de mercado: pivotes y swings (Price Action), Fair Value Gaps y Order
Blocks (Smart Money Concepts) y perfil de volumen (POC, VAH y VAL).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from herramientas_agente.base import cargar_json, herramienta
from herramientas_agente.estructura_mercado_herramientas.auxiliares import _obtener_velas_historicas

# Esquemas (descripción y parámetros que ve el modelo) leídos de esquemas.json junto a este archivo.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


# TITULO DETECTAR NIVELES CLAVE

@herramienta(**_ESQ["detectar_niveles_clave"])
def detectar_niveles_clave(
    simbolo: str,
    timeframe: str = "H1",
    cantidad_velas: int = 100,
) -> dict[str, Any]:
    """Detecta niveles clave: pivotes clásicos y últimos swing highs/lows.

    Recibe `simbolo`, `timeframe` (H1) y `cantidad_velas` (100). Los pivotes (pivot, R1, R2, S1, S2)
    se calculan con la penúltima vela (la última cerrada); los swings son máximos/mínimos locales
    que superan a las 2 velas vecinas de cada lado. Devuelve los 3 swings más recientes de cada tipo
    y el precio actual, o {"error": ...} con menos de 10 velas. Consulta MT5 o Yahoo Finance.
    """
    velas = _obtener_velas_historicas(simbolo, timeframe=timeframe, cantidad=cantidad_velas)
    if not velas or len(velas) < 10:
        return {"error": f"Sin datos suficientes para detectar niveles clave en {simbolo}."}

    # Vela de referencia para los pivotes: la última ya cerrada.
    v_referencia = velas[-2] if len(velas) > 1 else velas[-1]
    h, l, c = v_referencia.get("high", 0.0), v_referencia.get("low", 0.0), v_referencia.get("close", 0.0)

    # Fórmulas clásicas de puntos pivote.
    pivot = (h + l + c) / 3.0
    r1 = (2 * pivot) - l
    s1 = (2 * pivot) - h
    r2 = pivot + (h - l)
    s2 = pivot - (h - l)

    # Un swing se confirma si supera estrictamente a las dos velas anteriores y a las dos posteriores.
    swing_highs: list[float] = []
    swing_lows: list[float] = []

    for i in range(2, len(velas) - 2):
        v_curr = velas[i]
        if (
            v_curr["high"] > velas[i - 1]["high"]
            and v_curr["high"] > velas[i - 2]["high"]
            and v_curr["high"] > velas[i + 1]["high"]
            and v_curr["high"] > velas[i + 2]["high"]
        ):
            swing_highs.append(round(v_curr["high"], 5))

        if (
            v_curr["low"] < velas[i - 1]["low"]
            and v_curr["low"] < velas[i - 2]["low"]
            and v_curr["low"] < velas[i + 1]["low"]
            and v_curr["low"] < velas[i + 2]["low"]
        ):
            swing_lows.append(round(v_curr["low"], 5))

    precio_actual = velas[-1].get("close", 0.0)

    return {
        "fuente": "Extractor de Estructura y Niveles Clave (Price Action)",
        "simbolo": simbolo.upper(),
        "timeframe": timeframe.upper(),
        "precio_actual": precio_actual,
        "puntos_pivote_clasicos": {
            "pivot": round(pivot, 5),
            "resistencia_1": round(r1, 5),
            "resistencia_2": round(r2, 5),
            "soporte_1": round(s1, 5),
            "soporte_2": round(s2, 5),
        },
        "swing_highs_recientes": swing_highs[-3:],
        "swing_lows_recientes": swing_lows[-3:],
    }


# TITULO IDENTIFICAR ORDER BLOCKS FVG

@herramienta(**_ESQ["identificar_order_blocks_fvg"])
def identificar_order_blocks_fvg(
    simbolo: str,
    timeframe: str = "H1",
    cantidad_velas: int = 60,
) -> dict[str, Any]:
    """Escanea Fair Value Gaps (FVG) y Order Blocks (OB) de Smart Money Concepts.

    Recibe `simbolo`, `timeframe` (H1) y `cantidad_velas` (60). Un FVG es un hueco entre el máximo de
    la vela 1 y el mínimo de la vela 3 (alcista) o viceversa (bajista). Un OB es una vela contraria
    seguida de otra de cuerpo mayor a 1.8 veces el suyo. Devuelve hasta 5 FVG (empezando por los más
    recientes) y los últimos 5 OB, o {"error": ...} con menos de 5 velas. Consulta MT5 o Yahoo Finance.
    """
    velas = _obtener_velas_historicas(simbolo, timeframe=timeframe, cantidad=cantidad_velas)
    if not velas or len(velas) < 5:
        return {"error": f"Datos insuficientes para escanear FVG u Order Blocks en {simbolo}."}

    fvgs: list[dict[str, Any]] = []
    orden_bloques: list[dict[str, Any]] = []

    # FVG: recorrido de la más reciente a la más antigua con ventanas de 3 velas consecutivas.
    for i in range(len(velas) - 3, 0, -1):
        v1, v2, v3 = velas[i - 1], velas[i], velas[i + 1]

        if v3["low"] > v1["high"]:
            fvgs.append({
                "tipo": "FVG_ALCISTA",
                "rango_inferior": round(v1["high"], 5),
                "rango_superior": round(v3["low"], 5),
                "vela_index": i,
                "timestamp": v2.get("time"),
            })

        elif v3["high"] < v1["low"]:
            fvgs.append({
                "tipo": "FVG_BAJISTA",
                "rango_inferior": round(v3["high"], 5),
                "rango_superior": round(v1["low"], 5),
                "vela_index": i,
                "timestamp": v2.get("time"),
            })

    # Order Blocks: vela de color contrario antes de un impulso fuerte (cuerpo siguiente > 1.8 x cuerpo).
    for i in range(2, len(velas) - 2):
        cuerpo = abs(velas[i]["close"] - velas[i]["open"])
        cuerpo_siguiente = abs(velas[i + 1]["close"] - velas[i + 1]["open"])

        if velas[i]["close"] < velas[i]["open"] and velas[i + 1]["close"] > velas[i + 1]["open"] and cuerpo_siguiente > cuerpo * 1.8:
            orden_bloques.append({
                "tipo": "ORDER_BLOCK_ALCISTA",
                "zona_high": round(velas[i]["high"], 5),
                "zona_low": round(velas[i]["low"], 5),
                "timestamp": velas[i].get("time"),
            })
        elif velas[i]["close"] > velas[i]["open"] and velas[i + 1]["close"] < velas[i + 1]["open"] and cuerpo_siguiente > cuerpo * 1.8:
            orden_bloques.append({
                "tipo": "ORDER_BLOCK_BAJISTA",
                "zona_high": round(velas[i]["high"], 5),
                "zona_low": round(velas[i]["low"], 5),
                "timestamp": velas[i].get("time"),
            })

    precio_actual = velas[-1].get("close", 0.0)

    return {
        "fuente": "Detector de Smart Money Concepts (FVG & Order Blocks)",
        "simbolo": simbolo.upper(),
        "timeframe": timeframe.upper(),
        "precio_actual": precio_actual,
        "fvg_detectados": fvgs[:5],
        "order_blocks_detectados": orden_bloques[-5:],
    }


# TITULO CALCULAR PERFIL VOLUMEN

@herramienta(**_ESQ["calcular_perfil_volumen"])
def calcular_perfil_volumen(
    simbolo: str,
    timeframe: str = "H1",
    cantidad_velas: int = 100,
    niveles_precio: int = 24,
) -> dict[str, Any]:
    """Calcula el perfil de volumen: POC, área de valor (VAH/VAL) y su % del volumen.

    Recibe `simbolo`, `timeframe` (H1), `cantidad_velas` (100) y `niveles_precio` (24 franjas). El
    rango se divide en franjas y el volumen de tick de cada vela se asigna a la franja de su precio
    medio. El POC es el centro de la franja con más volumen y el área de valor se expande desde ahí
    hasta reunir el 70% del volumen. Devuelve {"error": ...} con menos de 10 velas o rango plano.
    Consulta MT5 o Yahoo Finance.
    """
    velas = _obtener_velas_historicas(simbolo, timeframe=timeframe, cantidad=cantidad_velas)
    if not velas or len(velas) < 10:
        return {"error": f"Sin datos para calcular el Perfil de Volumen en {simbolo}."}

    max_p = max(v["high"] for v in velas)
    min_p = min(v["low"] for v in velas)

    if max_p == min_p:
        return {"error": "El rango de precio es plano en la muestra seleccionada."}

    # Ancho de cada franja de precio y acumulador de volumen por franja.
    paso = (max_p - min_p) / niveles_precio
    bins = [0.0] * niveles_precio

    for v in velas:
        p_medio = (v["high"] + v["low"]) / 2.0
        volumen = v.get("tick_volume", 100.0)
        indice = min(int((p_medio - min_p) / paso), niveles_precio - 1)
        bins[indice] += volumen

    # Punto de control (POC): franja con mayor volumen.
    max_volumen_indice = max(range(niveles_precio), key=lambda i: bins[i])
    poc_precio = min_p + (max_volumen_indice + 0.5) * paso

    # Área de valor: se amplía hacia la franja vecina con más volumen hasta alcanzar el 70% del total.
    volumen_total = sum(bins)
    volumen_objetivo = volumen_total * 0.70

    volumen_acum = bins[max_volumen_indice]
    indice_bajo, indice_alto = max_volumen_indice, max_volumen_indice

    while volumen_acum < volumen_objetivo and (indice_bajo > 0 or indice_alto < niveles_precio - 1):
        v_debajo = bins[indice_bajo - 1] if indice_bajo > 0 else -1
        v_encima = bins[indice_alto + 1] if indice_alto < niveles_precio - 1 else -1

        if v_encima >= v_debajo:
            indice_alto += 1
            volumen_acum += bins[indice_alto]
        else:
            indice_bajo -= 1
            volumen_acum += bins[indice_bajo]

    valor_precio = min_p + indice_bajo * paso
    vah_precio = min_p + (indice_alto + 1) * paso

    return {
        "fuente": "Perfil de Volumen Institucional (Volume Profile)",
        "simbolo": simbolo.upper(),
        "timeframe": timeframe.upper(),
        "velas_analizadas": len(velas),
        "rango_precio": {
            "minimo_rango": round(min_p, 5),
            "maximo_rango": round(max_p, 5),
        },
        "volume_profile_key_levels": {
            "poc_point_of_control": round(poc_precio, 5),
            "vah_value_area_high": round(vah_precio, 5),
            "val_value_area_low": round(valor_precio, 5),
        },
        "distribucion_volumen_pct_value_area": round((volumen_acum / volumen_total) * 100, 2),
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
