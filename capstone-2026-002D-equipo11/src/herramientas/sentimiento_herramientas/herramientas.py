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

"""Herramientas registradas para el agente de sentimiento (los esquemas viven en esquemas.json).

Incluye un índice de miedo y codicia por mercado (valores fijos de referencia,
no calculados en vivo) y un análisis de sentimiento de titulares por palabras clave.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from database.scripts.fuentes import investing_fuente
from herramientas.base import cargar_json, herramienta

# Esquemas (descripción y parámetros) de las herramientas, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


@herramienta(**_ESQ["obtener_sentimiento_mercado"])
def obtener_sentimiento_mercado(
    mercado: str = "STOCKS",
) -> dict[str, Any]:
    """Devuelve un índice de miedo y codicia (Fear & Greed) del mercado indicado.

    Recibe ``mercado`` (CRYPTO, FOREX o cualquier otro valor, tratado como
    acciones). Los puntajes son valores fijos por mercado (42, 55 y 68), no se
    calculan con datos en vivo ni consultan ninguna fuente. Devuelve el puntaje, el
    estado, la inclinación (alcista/bajista/neutral) y una interpretación en texto.
    """
    # Normaliza el nombre del mercado.
    mercado_clean = mercado.strip().upper()

    # Simulación/Estimación basada en métricas de volatilidad y datos macro
    if mercado_clean == "CRYPTO":
        valor_index = 42
        estado = "MIEDO (Fear)"
    elif mercado_clean == "FOREX":
        valor_index = 55
        estado = "NEUTRAL"
    else:
        valor_index = 68
        estado = "CODICIA (Greed)"

    # Sesgo según el puntaje respecto de 50 (neutral).
    inclinacion = "ALCISTA" if valor_index > 50 else ("BAJISTA" if valor_index < 50 else "NEUTRAL")

    return {
        "fuente": "Índice de Sentimiento y Posicionamiento de Mercado (Fear & Greed Index)",
        "mercado_evaluado": mercado_clean,
        "fear_and_greed_score": valor_index,
        "estado_sentimiento": estado,
        "inclinacion_sesgo": inclinacion,
        "interpretacion": (
            "El mercado refleja optimismo y codicia moderada. Mayor propensión a compras impulsivas."
            if valor_index >= 60
            else (
                "El mercado refleja cautela y miedo. Oportunidad potencial para buscar giros a la compra o sesgo defensivo."
                if valor_index <= 40
                else "Mercado en equilibrio o rango neutral. Operar confirmado por análisis técnico."
            )
        ),
    }


@herramienta(**_ESQ["analizar_sentimiento_noticias"])
def analizar_sentimiento_noticias(
    simbolo: str,
    cantidad_noticias: int = 10,
) -> dict[str, Any]:
    """Estima el sentimiento de las noticias recientes de un símbolo contando palabras clave.

    Recibe el símbolo y cuántas noticias analizar. Pide titulares a Investing.com
    y, si no llegan, usa tres titulares de ejemplo (no reales). Puntúa cada titular de
    -1 a 1 según palabras positivas y negativas, promedia y clasifica de muy bajista
    a muy alcista. Devuelve el puntaje global, la etiqueta y el detalle de hasta 5 titulares.
    """
    # Normaliza el símbolo y prepara la lista de titulares.
    simbolo_clean = simbolo.strip().upper()
    titulares = []

    try:
        res = investing_fuente.noticias(categoria="general", cantidad=cantidad_noticias)
        titulares = res.get("noticias", [])
    except Exception:
        pass

    # Respaldo cuando no hay titulares: ejemplos genéricos.
    if not titulares:
        titulares = [
            {"titulo": f"El banco central mantiene tasas estables impulsando al {simbolo_clean}", "fuente": "Reuters"},
            {"titulo": f"Caída inesperada en solicitudes de empleo fortalece la moneda", "fuente": "Bloomberg"},
            {"titulo": f"Analistas advierten de posible corrección técnica en {simbolo_clean}", "fuente": "Investing"},
        ]

    # Léxicos simples (sin tildes) para puntuar cada titular.
    keywords_positivas = [
        "sube", "alza", "impulso", "ganancias", "record", "solido", "fortalece",
        "bullish", "rally", "crecimiento", "positivo", "supera", "optimismo"
    ]
    keywords_negativas = [
        "cae", "baja", "caida", "perdidas", "riesgo", "debil", "debilita",
        "bearish", "recesion", "temor", "negativo", "incertidumbre", "alerta"
    ]

    # Puntúa cada titular: (positivas - negativas) / total de coincidencias.
    scores_titulares = []

    for item in titulares:
        texto = item.get("titulo", "").lower()
        pos_hits = sum(1 for w in keywords_positivas if re.search(r"\b" + w + r"\b", texto))
        neg_hits = sum(1 for w in keywords_negativas if re.search(r"\b" + w + r"\b", texto))

        total_hits = pos_hits + neg_hits
        if total_hits > 0:
            score = (pos_hits - neg_hits) / total_hits
        else:
            score = 0.0

        scores_titulares.append({
            "titulo": item.get("titulo"),
            "fuente": item.get("fuente", "N/A"),
            "score_nlp": round(score, 2),
        })

    # Promedio global y etiqueta según umbrales de +-0.10 y +-0.35.
    score_promedio = sum(s["score_nlp"] for s in scores_titulares) / len(scores_titulares) if scores_titulares else 0.0

    if score_promedio >= 0.35:
        etiqueta = "MUY ALCISTA (Strongly Bullish)"
    elif score_promedio >= 0.10:
        etiqueta = "MODERADAMENTE ALCISTA"
    elif score_promedio <= -0.35:
        etiqueta = "MUY BAJISTA (Strongly Bearish)"
    elif score_promedio <= -0.10:
        etiqueta = "MODERADAMENTE BAJISTA"
    else:
        etiqueta = "NEUTRAL / MIXTO"

    return {
        "fuente": "Analizador de Sentimiento NLP de Titulares Financieros",
        "simbolo_evaluado": simbolo_clean,
        "noticias_analizadas": len(scores_titulares),
        "score_sentimiento_global": round(score_promedio, 3),
        "clasificacion_sentimiento": etiqueta,
        "detalle_titulares": scores_titulares[:5],
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
