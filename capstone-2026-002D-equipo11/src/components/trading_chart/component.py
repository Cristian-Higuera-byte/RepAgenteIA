"""Renderizado del componente HTML del gráfico."""

import logging

import streamlit as st
import streamlit.components.v1 as components

from components.trading_chart.context import ChartContext
from components.trading_chart.template import construir_html_grafico


logger = logging.getLogger(__name__)


def renderizar_grafico(
    context: ChartContext,
    height: int = 750,
) -> None:
    """Renderiza el gráfico dentro de un iframe de Streamlit."""

    try:
        html_chart = construir_html_grafico(context)

    except Exception as error:
        logger.exception(
            "No fue posible construir el gráfico de %s.",
            context.symbol,
        )

        st.error(
            "No fue posible construir el componente del gráfico."
        )

        with st.expander("Detalle técnico"):
            st.code(str(error))

        return

    components.html(
        html_chart,
        height=height,
        scrolling=False,
    )