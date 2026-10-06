"""Fuente de datos: Investing.com (en español).

Esta capa solo se encarga de OBTENER y NORMALIZAR noticias macroeconómicas y
de mercados. No conoce al modelo ni a las herramientas: devuelve listas/dict
simples y lanza ErrorInvesting con un mensaje claro si ocurre algún fallo.

Feeds disponibles (Investing.com España):
    general, mercados, forex, acciones, cripto, economia

Prueba rápida (desde la raíz del proyecto):  python -m fuentes.investing_fuente
"""

from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Callable

import requests

FEEDS: dict[str, str] = {
    "general": "https://es.investing.com/rss/news.rss",
    "mercados": "https://es.investing.com/rss/market_overview.rss",
    "forex": "https://es.investing.com/rss/news_1.rss",
    "acciones": "https://es.investing.com/rss/news_25.rss",
    "cripto": "https://es.investing.com/rss/news_301.rss",
    "economia": "https://es.investing.com/rss/news_14.rss",
}

AVISO_FUENTE = "Noticias en tiempo real obtenidas de Investing.com (en español)."

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class ErrorInvesting(Exception):
    """Fallo de la fuente Investing.com (mensaje ya legible)."""


# ──────────────────────────────────────────────────────────────
# Utilidades internas
# ──────────────────────────────────────────────────────────────
_CACHE: dict[str, tuple[float, Any]] = {}


def _cacheado(clave: str, ttl: float, fn: Callable[[], Any]) -> Any:
    """Cache en memoria con vencimiento para no saturar las peticiones a Investing."""
    ahora = time.monotonic()
    guardado = _CACHE.get(clave)
    if guardado and ahora - guardado[0] < ttl:
        return guardado[1]
    valor = fn()
    _CACHE[clave] = (ahora, valor)
    return valor


def _limpiar_html(texto: str) -> str:
    """Elimina etiquetas HTML e inconsistencias de formato en los resúmenes."""
    if not texto:
        return ""
    sin_html = re.sub(r"<[^>]+>", "", texto)
    return " ".join(sin_html.split()).strip()


def _sin_nulos(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


# ──────────────────────────────────────────────────────────────
# Extracción de Noticias
# ──────────────────────────────────────────────────────────────
def noticias(categoria: str = "general", cantidad: int = 10) -> dict[str, Any]:
    """Obtiene las últimas noticias publicadas en Investing.com para una categoría dada.

    Categorías válidas: 'general', 'mercados', 'forex', 'acciones', 'cripto', 'economia'.
    """
    cat = (categoria or "general").strip().lower()
    if cat not in FEEDS:
        raise ErrorInvesting(
            f"Categoría inválida: {categoria!r}. Opciones permitidas: {', '.join(FEEDS.keys())}"
        )

    n = max(1, min(int(cantidad), 30))
    url = FEEDS[cat]

    def _fn() -> dict[str, Any]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ErrorInvesting(
                f"No se pudo conectar con Investing.com ({cat}): {e}"
            ) from e

        try:
            root = ET.fromstring(resp.content)
            channel = root.find("channel")
            if channel is None:
                raise ErrorInvesting("El feed RSS de Investing.com no devolvió un canal válido.")
        except ET.ParseError as e:
            raise ErrorInvesting(
                f"Error al procesar la respuesta XML de Investing.com: {e}"
            ) from e

        items = channel.findall("item")
        resultado = []

        for item in items[:n]:
            titulo = item.findtext("title", default="").strip()
            enlace = item.findtext("link", default="").strip()
            fecha_raw = item.findtext("pubDate", default="").strip()
            descripcion_raw = item.findtext("description", default="")

            resumen = _limpiar_html(descripcion_raw)
            if len(resumen) > 300:
                resumen = resumen[:300] + "..."

            if titulo:
                resultado.append(
                    _sin_nulos(
                        {
                            "titulo": titulo,
                            "resumen": resumen or None,
                            "fecha": fecha_raw or None,
                            "enlace": enlace or None,
                        }
                    )
                )

        return {
            "fuente": "Investing.com",
            "categoria": cat,
            "noticias_totales": len(resultado),
            "noticias": resultado,
            "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "aviso": AVISO_FUENTE,
        }

    # Cache de 5 minutos (300 segundos) para noticias
    return _cacheado(f"investing:{cat}:{n}", 300, _fn)


def buscar_noticias(
    busqueda: str, categoria: str = "general", cantidad: int = 10
) -> dict[str, Any]:
    """Filtra las noticias recientes de una categoría por una palabra clave (ej. 'FED', 'Oro', 'Inflación')."""
    palabra = (busqueda or "").strip().lower()
    if not palabra:
        raise ErrorInvesting("Falta el término de búsqueda.")

    datos_cat = noticias(categoria=categoria, cantidad=30)
    filtradas = [
        n for n in datos_cat["noticias"]
        if palabra in n["titulo"].lower() or palabra in (n.get("resumen") or "").lower()
    ]

    return {
        "fuente": "Investing.com",
        "busqueda": palabra,
        "categoria": categoria,
        "coincidencias": len(filtradas),
        "noticias": filtradas[:cantidad],
        "consultado_utc": datos_cat["consultado_utc"],
        "aviso": AVISO_FUENTE,
    }


if __name__ == "__main__":
    import json

    pruebas = (
        ("noticias generales", lambda: noticias("general", 3)),
        ("noticias forex", lambda: noticias("forex", 3)),
        ("buscar_noticias", lambda: buscar_noticias("inflación", "economia", 3)),
    )
    for nombre, prueba in pruebas:
        print(f"\n=== {nombre}")
        try:
            print(json.dumps(prueba(), ensure_ascii=False, indent=2, default=str))
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")