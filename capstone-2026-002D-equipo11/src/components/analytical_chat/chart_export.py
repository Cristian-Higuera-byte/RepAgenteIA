"""Generación de gráficos analíticos para el asistente."""

from dataclasses import dataclass
import logging
from pathlib import Path
import re
import time
from typing import Optional

from matplotlib.figure import Figure
import MetaTrader5 as mt5  # type: ignore[import-untyped]
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from tools.mt5_bridge import obtener_datos_historicos


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"


@dataclass(frozen=True)
class AnalyticalChartResult:
    """Resultado preparado para ser mostrado por Streamlit."""

    chart_data: pd.DataFrame
    image_path: str


def solicitud_requiere_grafico(
    prompt: str,
) -> bool:
    """Detecta si el mensaje solicita una visualización."""

    keywords = (
        "gráfico",
        "grafico",
        "graficar",
        "imagen",
        "figura",
        "tendencia",
        "rendimiento",
        "evolución",
        "evolucion",
    )

    prompt_lower = prompt.casefold()

    return any(
        keyword in prompt_lower
        for keyword in keywords
    )


def _normalizar_nombre_archivo(
    value: str,
) -> str:
    """Convierte el símbolo en un nombre de archivo seguro."""

    safe_value = re.sub(
        r"[^a-zA-Z0-9_.-]+",
        "_",
        value,
    )

    return safe_value.strip("._") or "activo"


def _crear_dataframe(
    values: np.ndarray,
    symbol: str,
) -> pd.DataFrame:
    """Construye los datos utilizados por st.line_chart."""

    return pd.DataFrame(
        values,
        columns=[f"Rendimiento - {symbol}"],
    )


def _crear_figura(
    values: np.ndarray,
    symbol: str,
) -> Figure:
    """Construye la figura de Matplotlib."""

    figure = Figure(
        figsize=(8, 4),
        facecolor="#0d1117",
    )

    axis = figure.subplots()
    axis.set_facecolor("#0d1117")
    axis.tick_params(colors="#8b949e")

    for border in axis.spines.values():
        border.set_color("#30363d")

    x_values = np.arange(len(values))
    minimum = float(np.min(values))

    axis.plot(
        x_values,
        values,
        color="#3fb950",
        linewidth=2,
        label=f"Tendencia {symbol}",
    )

    axis.fill_between(
        x_values,
        values,
        minimum * 0.99,
        color="#238636",
        alpha=0.2,
    )

    axis.set_title(
        (
            "Análisis técnico y gráfico renderizado "
            f"(MT5) - {symbol}"
        ),
        color="white",
        fontsize=12,
        fontweight="bold",
    )

    axis.set_xlabel(
        "Barras",
        color="#8b949e",
    )

    axis.set_ylabel(
        "Precio",
        color="#8b949e",
    )

    axis.grid(
        True,
        color="#30363d",
        linestyle="--",
        alpha=0.5,
    )

    axis.legend(
        loc="upper left",
        facecolor="#161b22",
        edgecolor="#30363d",
        labelcolor="white",
    )

    return figure


def generar_grafico_analitico(
    symbol: str,
    timeframe: int = mt5.TIMEFRAME_H1,
    candle_count: int = 30,
) -> Optional[AnalyticalChartResult]:
    """Obtiene datos de MT5 y genera la visualización del chat."""

    try:
        dataframe = obtener_datos_historicos(
            symbol,
            timeframe=timeframe,
            n_velas=candle_count,
        )

        if dataframe is None or dataframe.empty:
            return None

        if "close" not in dataframe.columns:
            logger.warning(
                "Los datos históricos de %s no incluyen close.",
                symbol,
            )
            return None

        close_values = (
            pd.to_numeric(
                dataframe["close"],
                errors="coerce",
            )
            .dropna()
            .to_numpy(dtype=float)
        )

        if close_values.size == 0:
            return None

        chart_data = _crear_dataframe(
            close_values,
            symbol,
        )

        figure = _crear_figura(
            close_values,
            symbol,
        )

        DOWNLOADS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        safe_symbol = _normalizar_nombre_archivo(
            symbol.lower()
        )

        filename = (
            f"grafico_{safe_symbol}_{time.time_ns()}.png"
        )

        image_path = DOWNLOADS_DIR / filename

        figure.savefig(
            image_path,
            dpi=200,
            bbox_inches="tight",
            facecolor=figure.get_facecolor(),
        )

        figure.clear()

        return AnalyticalChartResult(
            chart_data=chart_data,
            image_path=str(image_path),
        )

    except Exception:
        logger.exception(
            "No fue posible generar el gráfico analítico "
            "para %s.",
            symbol,
        )
        return None