"""Interfaz del asistente analítico central."""

import logging
from types import ModuleType
from typing import Any, Optional

import streamlit as st

from components.analytical_chat.chart_export import (
    AnalyticalChartResult,
    generar_grafico_analitico,
    solicitud_requiere_grafico,
)
from components.analytical_chat.state import (
    inicializar_estado_chat,
)


logger = logging.getLogger(__name__)


def _renderizar_elementos_mensaje(
    message: dict[str, Any],
) -> None:
    """Renderiza el contenido complementario de un mensaje."""

    chart_data = message.get("chart_data")
    image_path = message.get("imagen_path")

    if chart_data is not None:
        st.line_chart(chart_data)

    if image_path:
        st.image(
            image_path,
            caption="Imagen renderizada del análisis técnico",
            use_container_width=True,
        )


def _renderizar_historial(
    container: Any,
) -> None:
    """Muestra todos los mensajes almacenados."""

    with container:
        for message in st.session_state.mensajes_ui:
            role = message.get(
                "role",
                "assistant",
            )

            content = message.get(
                "content",
                "",
            )

            with st.chat_message(role):
                st.markdown(content)
                _renderizar_elementos_mensaje(message)


def _ejecutar_agente(
    main: Optional[ModuleType],
    user_prompt: str,
) -> str:
    """Invoca chat_agente si se encuentra disponible."""

    if main is None or not hasattr(
        main,
        "chat_agente",
    ):
        return (
            "No se pudo importar la función "
            "`chat_agente` desde `main.py`."
        )

    try:
        response, history = main.chat_agente(
            user_prompt,
            st.session_state.historial_tecnico_agente,
        )

        st.session_state.historial_tecnico_agente = (
            history
        )

        return str(response)

    except Exception as error:
        logger.exception(
            "Error al ejecutar chat_agente."
        )

        return (
            "Error al ejecutar el agente en "
            f"`main.py`: {error}"
        )


def _generar_resultado_grafico(
    prompt: str,
    symbol: str,
) -> Optional[AnalyticalChartResult]:
    """Genera un gráfico solamente cuando el mensaje lo pide."""

    if not solicitud_requiere_grafico(prompt):
        return None

    return generar_grafico_analitico(symbol)


def renderizar_chat_analitico(
    main: Optional[ModuleType],
    symbol: str,
) -> None:
    """Renderiza el asistente mostrado debajo del gráfico."""

    inicializar_estado_chat()

    st.markdown("---")
    st.markdown(
        "### 🤖 Asistente IA Analítico "
        "(Consola, Gráficos e Imágenes)"
    )

    st.caption(
        "Interactúa con el agente bursátil. "
        "El asistente mantiene contexto, herramientas, "
        "gráficos e imágenes renderizadas."
    )

    chat_container = st.container(height=450)
    _renderizar_historial(chat_container)

    user_prompt = st.chat_input(
        "Escribe tu consulta o pide un gráfico en imagen..."
    )

    if not user_prompt:
        return

    user_message = {
        "role": "user",
        "content": user_prompt,
    }

    st.session_state.mensajes_ui.append(
        user_message
    )

    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_prompt)

    with chat_container:
        with st.chat_message("assistant"):
            with st.spinner(
                "El agente está procesando la solicitud..."
            ):
                response = _ejecutar_agente(
                    main=main,
                    user_prompt=user_prompt,
                )

                chart_result = _generar_resultado_grafico(
                    prompt=user_prompt,
                    symbol=symbol,
                )

                chart_data = None
                image_path = None

                if chart_result is not None:
                    chart_data = chart_result.chart_data
                    image_path = chart_result.image_path

                    response += (
                        "\n\n*Gráfico interactivo e imagen "
                        "renderizada con datos de MetaTrader 5 "
                        f"para **{symbol}**.*"
                    )

                st.markdown(response)

                if chart_data is not None:
                    st.line_chart(chart_data)

                if image_path:
                    st.image(
                        image_path,
                        caption=(
                            "Imagen renderizada del análisis"
                        ),
                        use_container_width=True,
                    )

    st.session_state.mensajes_ui.append(
        {
            "role": "assistant",
            "content": response,
            "chart_data": chart_data,
            "imagen_path": image_path,
        }
    )