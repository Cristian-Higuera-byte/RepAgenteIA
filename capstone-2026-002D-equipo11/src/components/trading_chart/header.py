"""Cabecera de precio y estado de conexión del gráfico."""

from dataclasses import dataclass
from html import escape
from typing import Any, Mapping

import streamlit as st

from components.trading_chart.context import ChartContext
from tools.mt5_bridge import obtener_precio_actual


COLOR_POSITIVO = "#3fb950"
COLOR_NEGATIVO = "#f85149"
COLOR_NEUTRO = "#8b949e"


@dataclass(frozen=True)
class HeaderQuote:
    """Información procesada que se mostrará en la cabecera."""

    price: float
    bid: float
    ask: float
    connected: bool
    price_color: str
    status_color: str
    status_text: str


def _a_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Convierte un valor a float de forma segura."""

    try:
        result = float(value)

        if result != result:
            return default

        return result

    except (TypeError, ValueError):
        return default


def _tick_tiene_error(
    tick: Mapping[str, Any],
) -> bool:
    """Determina si la respuesta de precio contiene un error."""

    return bool(
        tick.get("error")
        or tick.get("status") == "error"
    )


def _obtener_precio_representativo(
    tick: Mapping[str, Any],
) -> float:
    """
    Selecciona el precio principal de la cabecera.

    Conserva el comportamiento original:
    primero utiliza last y, si no existe, utiliza bid.
    """

    last = _a_float(tick.get("last"))
    bid = _a_float(tick.get("bid"))

    if last > 0:
        return last

    return bid


def _calcular_color_precio(
    context: ChartContext,
    current_price: float,
    connected: bool,
) -> str:
    """Compara el precio actual con el precio anterior."""

    if not connected:
        return COLOR_NEUTRO

    price_key = f"_prev_precio_{context.symbol}"
    color_key = f"_color_precio_{context.symbol}"

    previous_price = _a_float(
        st.session_state.get(
            price_key,
            current_price,
        ),
        current_price,
    )

    if current_price > previous_price:
        color = COLOR_POSITIVO
    elif current_price < previous_price:
        color = COLOR_NEGATIVO
    else:
        color = st.session_state.get(
            color_key,
            COLOR_POSITIVO,
        )

    st.session_state[price_key] = current_price
    st.session_state[color_key] = color

    return color


def obtener_quote_cabecera(
    context: ChartContext,
) -> HeaderQuote:
    """Consulta y procesa el último tick del símbolo."""

    raw_tick = obtener_precio_actual(context.symbol)

    if not isinstance(raw_tick, Mapping):
        raw_tick = {
            "error": (
                "La fuente de precio devolvió una "
                "respuesta no válida."
            )
        }

    bid = _a_float(raw_tick.get("bid"))
    ask = _a_float(raw_tick.get("ask"))
    price = _obtener_precio_representativo(raw_tick)

    connected = (
        not _tick_tiene_error(raw_tick)
        and price > 0
    )

    price_color = _calcular_color_precio(
        context=context,
        current_price=price,
        connected=connected,
    )

    return HeaderQuote(
        price=price,
        bid=bid,
        ask=ask,
        connected=connected,
        price_color=price_color,
        status_color=(
            COLOR_POSITIVO
            if connected
            else COLOR_NEGATIVO
        ),
        status_text=(
            "Conectado"
            if connected
            else "Sin conexión"
        ),
    )


def construir_html_cabecera(
    context: ChartContext,
    quote: HeaderQuote,
) -> str:
    """Construye el HTML correspondiente a la cabecera."""

    symbol = escape(context.symbol)
    broker_label = escape(context.broker_label)
    status_text = escape(quote.status_text)

    formatted_price = (
        f"{quote.price:,.{context.digits}f}"
    )
    formatted_bid = (
        f"{quote.bid:,.{context.digits}f}"
    )
    formatted_ask = (
        f"{quote.ask:,.{context.digits}f}"
    )

    return f"""
    <div class="trading-header">
        <div class="trading-header__quote">
            <span class="trading-header__symbol">
                {symbol}
            </span>

            <span class="trading-header__broker">
                {broker_label}
            </span>

            <span
                class="trading-header__price"
                style="color: {quote.price_color};"
            >
                {formatted_price}
            </span>

            <span
                class="trading-header__spread"
                style="color: {quote.price_color};"
            >
                Bid: {formatted_bid}
                <span class="trading-header__separator">|</span>
                Ask: {formatted_ask}
            </span>
        </div>

        <div class="trading-header__status">
            <span>{status_text}</span>
            <span
                class="trading-header__status-dot"
                style="color: {quote.status_color};"
                aria-hidden="true"
            >
                ●
            </span>
        </div>
    </div>

    <style>
        .trading-header {{
            box-sizing: border-box;
            width: 100%;
            margin-bottom: 10px;
            padding: 10px 16px;

            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;

            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
        }}

        .trading-header__quote {{
            min-width: 0;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 14px;
        }}

        .trading-header__symbol {{
            color: #ffffff;
            font-size: 20px;
            font-weight: 700;
        }}

        .trading-header__broker {{
            padding: 2px 8px;

            color: #8b949e;
            background: #30363d;
            border-radius: 4px;

            font-size: 11px;
            white-space: nowrap;
        }}

        .trading-header__price {{
            font-family:
                ui-monospace,
                SFMono-Regular,
                Menlo,
                Monaco,
                Consolas,
                monospace;
            font-size: 22px;
            font-weight: 700;
            white-space: nowrap;
        }}

        .trading-header__spread {{
            font-family:
                ui-monospace,
                SFMono-Regular,
                Menlo,
                Monaco,
                Consolas,
                monospace;
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
        }}

        .trading-header__separator {{
            color: #6e7681;
            padding: 0 3px;
        }}

        .trading-header__status {{
            display: flex;
            align-items: center;
            gap: 6px;

            color: #8b949e;
            font-size: 13px;
            font-weight: 600;
            white-space: nowrap;
        }}

        .trading-header__status-dot {{
            font-size: 16px;
            line-height: 1;
        }}

        @media (max-width: 760px) {{
            .trading-header {{
                align-items: flex-start;
            }}

            .trading-header__quote {{
                gap: 8px 12px;
            }}

            .trading-header__price {{
                font-size: 18px;
            }}

            .trading-header__spread {{
                width: 100%;
                font-size: 12px;
            }}
        }}
    </style>
    """


def renderizar_cabecera_precio(
    context: ChartContext,
) -> None:
    """Renderiza la cabecera y la actualiza cada dos segundos."""

    @st.fragment(run_every="2s")
    def _fragmento_cabecera() -> None:
        quote = obtener_quote_cabecera(context)
        html = construir_html_cabecera(
            context=context,
            quote=quote,
        )

        st.markdown(
            html,
            unsafe_allow_html=True,
        )

    _fragmento_cabecera()