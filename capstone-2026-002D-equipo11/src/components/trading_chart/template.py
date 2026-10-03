"""Construcción del documento HTML del gráfico."""

from functools import lru_cache
from html import escape
import json
from pathlib import Path

from components.trading_chart.context import ChartContext


ASSETS_DIR = Path(__file__).resolve().parent / "assets"

REQUIRED_ASSETS = (
    "chart.html",
    "chart.css",
    "preflight.js",
    "chart.js",
)


@lru_cache(maxsize=None)
def leer_asset(nombre: str) -> str:
    """Lee un recurso estático utilizando UTF-8."""

    path = ASSETS_DIR / nombre

    if not path.exists():
        raise FileNotFoundError(
            "No se encontró el recurso del gráfico: "
            f"{path}"
        )

    return path.read_text(encoding="utf-8")


def verificar_assets() -> None:
    """Comprueba que existan todos los recursos del gráfico."""

    faltantes = [
        nombre
        for nombre in REQUIRED_ASSETS
        if not (ASSETS_DIR / nombre).exists()
    ]

    if faltantes:
        lista = ", ".join(faltantes)

        raise FileNotFoundError(
            "Faltan recursos del gráfico: "
            f"{lista}. Ejecuta "
            "`python scripts/extract_central_chart.py`."
        )


def _crear_configuracion_js(
    context: ChartContext,
) -> str:
    """Crea una configuración JSON segura para JavaScript."""

    config = {
        "symbol": context.symbol,
        "apiUrl": context.api_url,
        "digits": context.digits,
        "point": context.point,
        "tickSize": context.tick_size,
        "pipSize": context.pip_size,
        "isForex": context.is_forex,
        "feedLabel": context.feed_label,
    }

    return json.dumps(
        config,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def construir_html_grafico(
    context: ChartContext,
) -> str:
    """Construye el documento final que recibirá components.html."""

    verificar_assets()

    html_template = leer_asset("chart.html")
    chart_css = leer_asset("chart.css")
    preflight_js = leer_asset("preflight.js")
    chart_js = leer_asset("chart.js")

    replacements = {
        "__CHART_CSS__": chart_css,
        "__PREFLIGHT_JS__": preflight_js,
        "__CHART_JS__": chart_js,
        "__CHART_CONFIG_JS__": _crear_configuracion_js(
            context
        ),
        "__SIMBOLO_HTML__": escape(context.symbol),
        "__SIMBOLO_JS__": json.dumps(
            context.symbol,
            ensure_ascii=False,
        ),
        "__API_URL_JS__": json.dumps(
            context.api_url,
            ensure_ascii=False,
        ),
        "__DIGITS__": str(context.digits),
        "__POINT__": json.dumps(context.point),
        "__TICK_SIZE__": json.dumps(
            context.tick_size
        ),
        "__PIP__": json.dumps(context.pip_size),
        "__PIP_SIZE__": json.dumps(
            context.pip_size
        ),
        "__FEED_LABEL_HTML__": escape(
            context.feed_label
        ),
    }

    result = html_template

    for placeholder, value in replacements.items():
        result = result.replace(
            placeholder,
            value,
        )

    return result