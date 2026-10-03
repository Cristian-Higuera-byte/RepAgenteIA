"""Construcción del contexto del gráfico de trading."""

from dataclasses import dataclass
import os

import streamlit as st

from components.trading_chart.symbol_info import (
    limpiar_simbolo,
    obtener_metadatos_simbolo,
)
from tools.mt5_bridge import inicializar_mt5


@dataclass(frozen=True)
class ChartContext:
    """Configuración compartida por el gráfico y la cabecera."""

    symbol: str
    api_url: str
    digits: int
    point: float
    tick_size: float
    pip_size: float
    is_forex: bool
    broker_label: str = "XM / MT5"
    feed_label: str = "XM"


def _obtener_api_url() -> str:
    """Obtiene y normaliza la URL del servicio de datos."""

    api_url = os.environ.get(
        "MT5_API_URL",
        "http://localhost:8000",
    )

    return api_url.strip().rstrip("/")


def construir_contexto_grafico() -> ChartContext:
    """Construye el contexto correspondiente al activo seleccionado."""

    inicializar_mt5()

    activo_seleccionado = st.session_state.get(
        "activo_seleccionado",
        "EURUSD...",
    )

    symbol = limpiar_simbolo(
        str(activo_seleccionado),
    )

    if not symbol:
        symbol = "EURUSD"

    metadata = obtener_metadatos_simbolo(symbol)

    return ChartContext(
        symbol=metadata.symbol,
        api_url=_obtener_api_url(),
        digits=metadata.digits,
        point=metadata.point,
        tick_size=metadata.tick_size,
        pip_size=metadata.pip_size,
        is_forex=metadata.is_forex,
    )