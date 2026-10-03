"""Estado de sesión del asistente analítico."""

import streamlit as st


MENSAJE_INICIAL = {
    "role": "assistant",
    "content": (
        "¡Hola! Estoy listo. Pregúntame sobre cualquier "
        "activo o mercado, o pídeme un gráfico con su "
        "respectiva imagen renderizada."
    ),
}


def inicializar_estado_chat() -> None:
    """Crea las claves del chat si todavía no existen."""

    if "mensajes_ui" not in st.session_state:
        st.session_state.mensajes_ui = [
            MENSAJE_INICIAL.copy()
        ]

    if (
        "historial_tecnico_agente"
        not in st.session_state
    ):
        st.session_state.historial_tecnico_agente = None
