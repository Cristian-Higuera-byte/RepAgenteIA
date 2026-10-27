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

Herramientas de gestión de riesgo: cálculo del lote según el riesgo deseado, criterio de Kelly y
desglose de exposición neta por divisa de las posiciones abiertas.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from database.scripts.fuentes import mt5_fuentes as mt5_fuente
from herramientas.base import cargar_json, herramienta

# Esquemas (descripción y parámetros que ve el modelo) leídos de esquemas.json junto a este archivo.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


@herramienta(**_ESQ["calcular_tamano_posicion"])
def calcular_tamano_posicion(
    simbolo: str,
    distancia_sl_pips: float,
    porcentaje_riesgo: float = 1.0,
    capital_usd: float | None = None,
) -> dict[str, Any]:
    """Calcula el lotaje que arriesga un % del capital dada una distancia de Stop Loss en pips.

    Recibe `simbolo`, `distancia_sl_pips` (debe ser mayor que 0), `porcentaje_riesgo` (1.0 %) y
    `capital_usd` (por defecto la equidad de MT5, o 10000). El valor del pip por lote se obtiene de
    MT5; si no está disponible devuelve {"error": ...} en lugar de estimar. El lote se redondea al
    paso del símbolo y se limita al mínimo y máximo permitidos; si el mínimo obliga a arriesgar más
    de lo pedido se añade un aviso. Efecto secundario: consultas a MT5.
    """
    if distancia_sl_pips <= 0:
        return {"error": "La distancia del Stop Loss debe ser mayor a 0."}

    # Capital base y monto en dinero que se está dispuesto a perder.
    cuenta = mt5_fuente.cuenta()
    capital = capital_usd or cuenta.get("equidad") or 10000.0
    monto_riesgo_usd = capital * (porcentaje_riesgo / 100.0)

    sym_upper = simbolo.strip().upper()

    # Valor real del pip por lote según MT5 (respeta contrato y conversión a la moneda de la cuenta)
    try:
        esp = mt5_fuente.especificacion_simbolo(sym_upper)
    except mt5_fuente.ErrorMT5:
        esp = {}
    valor_pip_lote = esp.get("valor_pip_por_lote")
    if not valor_pip_lote or valor_pip_lote <= 0:
        return {
            "error": (
                f"No se pudo obtener de MT5 el valor del pip de '{sym_upper}', así que no se calcula el lotaje "
                "(una estimación podría ser muy errónea). Verifica el símbolo con mt5_buscar_simbolos."
            ),
        }

    # Lote teórico = riesgo en dinero / (pips de SL x valor del pip por lote).
    lote_calculado = monto_riesgo_usd / (distancia_sl_pips * valor_pip_lote)
    # Ajuste a los límites del símbolo (paso, mínimo y máximo de lote).
    paso = esp.get("paso_lote") or 0.01
    minimo = esp.get("lote_minimo") or paso
    maximo = esp.get("lote_maximo")
    lote_sugerido = max(minimo, math.floor(round(lote_calculado / paso, 6)) * paso)   # se redondea hacia abajo: nunca más riesgo
    if maximo:
        lote_sugerido = min(lote_sugerido, maximo)
    lote_sugerido = round(lote_sugerido, 8)
    # Riesgo efectivo con el lote ya redondeado.
    riesgo_real = round(lote_sugerido * distancia_sl_pips * valor_pip_lote, 2)

    resultado = {
        "fuente": "Calculadora de Gestión de Riesgo y Lote (valor del pip calculado por MT5)",
        "simbolo": esp.get("simbolo", sym_upper),
        "capital_evaluado_usd": capital,
        "porcentaje_riesgo_pct": porcentaje_riesgo,
        "monto_arriesgado_usd": round(monto_riesgo_usd, 2),
        "distancia_sl_pips": distancia_sl_pips,
        "lotaje_teorico": round(lote_calculado, 4),
        "lotaje_sugerido": lote_sugerido,
        "riesgo_real_con_lotaje_sugerido_usd": riesgo_real,
        "valor_pip_por_lote_usd": valor_pip_lote,
        "nota_pips": "1 pip = 10 puntos en símbolos de 3 o 5 decimales; en el resto, 1 punto.",
    }
    if lote_sugerido > lote_calculado:
        resultado["aviso"] = (
            "El lote mínimo del símbolo supera el calculado: el riesgo real es mayor que el pedido."
        )
    return resultado


@herramienta(**_ESQ["calcular_criterio_kelly"])
def calcular_criterio_kelly(
    win_rate_pct: float,
    ratio_rr: float,
) -> dict[str, Any]:
    """Calcula la fracción óptima de capital según el criterio de Kelly.

    Recibe `win_rate_pct` (0 a 100) y `ratio_rr` (beneficio/riesgo, mayor que 0). Devuelve Kelly
    completo, medio y un cuarto (en %, nunca negativos), la expectativa matemática por unidad
    arriesgada y un diagnóstico textual. Devuelve {"error": ...} si los parámetros son inválidos.
    Es un cálculo puro, sin acceso a MT5 ni a la red.
    """
    if ratio_rr <= 0 or win_rate_pct < 0 or win_rate_pct > 100:
        return {"error": "Parámetros inválidos. Win rate debe estar entre 0 y 100, y RR debe ser mayor a 0."}

    p = win_rate_pct / 100.0  # Probabilidad de ganar
    q = 1.0 - p               # Probabilidad de perder
    b = ratio_rr              # Ratio Beneficio/Riesgo

    # Fórmula de Kelly: K% = (b * p - q) / b
    kelly_fraction = (b * p - q) / b if b > 0 else 0.0
    kelly_pct = max(0.0, kelly_fraction * 100.0)

    half_kelly_pct = kelly_pct / 2.0
    quarter_kelly_pct = kelly_pct / 4.0

    expectativa_matematica = (p * b) - q

    return {
        "fuente": "Optimizador de Criterio de Kelly",
        "parametros_entrada": {
            "win_rate_pct": win_rate_pct,
            "ratio_riesgo_beneficio": ratio_rr,
        },
        "expectativa_matematica_esperada_por_unidad": round(expectativa_matematica, 4),
        "resultados_kelly": {
            "full_kelly_pct": round(kelly_pct, 2),
            "half_kelly_sugerido_pct": round(half_kelly_pct, 2),
            "quarter_kelly_conservador_pct": round(quarter_kelly_pct, 2),
        },
        "diagnostico": (
            "Expectativa matemática positiva. Se recomienda aplicar Half-Kelly para mitigar volatilidad."
            if expectativa_matematica > 0
            else "Expectativa matemática negativa o nula. No se recomienda ejecutar esta estrategia."
        ),
    }


@herramienta(**_ESQ["analizar_exposicion_divisas"])
def analizar_exposicion_divisas() -> dict[str, Any]:
    """Desglosa el volumen comprado, vendido y neto por divisa a partir de las posiciones abiertas de MT5.

    No recibe parámetros. Para cada posición separa base y cotizada (pares de 6 letras; otros símbolos
    con USD o, por defecto, cotizados en USD); una compra suma a la base y resta a la cotizada, y una
    venta al revés. Devuelve el diccionario por divisa con volúmenes en lotes o un mensaje si no hay
    posiciones. Efecto secundario: consulta a MT5.
    """
    posiciones = mt5_fuente.posiciones().get("posiciones", [])
    if not posiciones:
        return {
            "fuente": "Desglose de Exposición por Divisa",
            "total_posiciones": 0,
            "exposicion_por_divisa": {},
            "mensaje": "No hay posiciones abiertas activas en la cuenta.",
        }

    # Acumulador por divisa: lotes comprados, vendidos y neto.
    exposicion: dict[str, dict[str, float]] = {}

    for pos in posiciones:
        sym = pos.get("simbolo", "").upper()
        volumen = pos.get("lotes", pos.get("volumen", 0.0))
        tipo = pos.get("tipo", "BUY").upper()

        if len(sym) == 6 and sym.isalpha():
            base = sym[:3]
            quote = sym[3:]
        elif "USD" in sym and sym != "USD":
            base = sym.replace("USD", "")
            quote = "USD"
        else:
            base = sym
            quote = "USD"

        if base not in exposicion:
            exposicion[base] = {"volumen_comprado": 0.0, "volumen_vendido": 0.0, "exposicion_neta": 0.0}
        if quote not in exposicion:
            exposicion[quote] = {"volumen_comprado": 0.0, "volumen_vendido": 0.0, "exposicion_neta": 0.0}

        if tipo in ("BUY", "COMPRA"):
            exposicion[base]["volumen_comprado"] += volumen
            exposicion[quote]["volumen_vendido"] += volumen
        else:
            exposicion[base]["volumen_vendido"] += volumen
            exposicion[quote]["volumen_comprado"] += volumen

    # Redondeo final y cálculo de la exposición neta.
    for div, datos in exposicion.items():
        datos["volumen_comprado"] = round(datos["volumen_comprado"], 2)
        datos["volumen_vendido"] = round(datos["volumen_vendido"], 2)
        datos["exposicion_neta"] = round(datos["volumen_comprado"] - datos["volumen_vendido"], 2)

    return {
        "fuente": "Desglose de Exposición por Divisa",
        "total_posiciones_analizadas": len(posiciones),
        "exposicion_por_divisa": exposicion,
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
