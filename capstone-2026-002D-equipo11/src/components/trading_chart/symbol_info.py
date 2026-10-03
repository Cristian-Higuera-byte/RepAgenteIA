"""Obtención y normalización de metadatos de símbolos de MetaTrader 5."""

from dataclasses import dataclass
import logging

import MetaTrader5 as mt5  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SymbolMetadata:
    """Metadatos necesarios para representar un símbolo financiero."""

    symbol: str
    digits: int
    point: float
    tick_size: float
    pip_size: float
    is_forex: bool


def limpiar_simbolo(valor: str) -> str:
    """Elimina los puntos usados para abreviar el símbolo en la interfaz."""

    return (
        str(valor)
        .replace("...", "")
        .replace("…", "")
        .strip()
    )


def _crear_metadatos_predeterminados(
    simbolo: str,
) -> SymbolMetadata:
    """Crea metadatos seguros cuando MT5 no responde."""

    return SymbolMetadata(
        symbol=simbolo,
        digits=5,
        point=0.00001,
        tick_size=0.00001,
        pip_size=0.0,
        is_forex=False,
    )


def obtener_metadatos_simbolo(
    simbolo: str,
) -> SymbolMetadata:
    """
    Obtiene la precisión, punto, tamaño de tick y pip del símbolo.

    La función utiliza valores predeterminados si MetaTrader 5 no
    devuelve información válida. Esto permite que la interfaz siga
    renderizándose mientras se muestra el estado de desconexión.
    """

    simbolo = limpiar_simbolo(simbolo)
    predeterminados = _crear_metadatos_predeterminados(simbolo)

    if not simbolo:
        return predeterminados

    try:
        seleccionado = mt5.symbol_select(simbolo, True)

        if not seleccionado:
            logger.warning(
                "MT5 no pudo seleccionar el símbolo %s.",
                simbolo,
            )
            return predeterminados

        info = mt5.symbol_info(simbolo)

        if info is None:
            logger.warning(
                "MT5 no devolvió metadatos para %s.",
                simbolo,
            )
            return predeterminados

        digits = max(0, int(info.digits))
        point = float(info.point or 0.0)

        if point <= 0:
            point = 10 ** (-digits)

        trade_tick_size = getattr(
            info,
            "trade_tick_size",
            0.0,
        )

        tick_size = float(trade_tick_size or point)

        if tick_size <= 0:
            tick_size = point

        forex_mode = getattr(
            mt5,
            "SYMBOL_CALC_MODE_FOREX",
            0,
        )

        forex_no_leverage_mode = getattr(
            mt5,
            "SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE",
            None,
        )

        modos_forex = {forex_mode}

        if forex_no_leverage_mode is not None:
            modos_forex.add(forex_no_leverage_mode)

        is_forex = info.trade_calc_mode in modos_forex

        if is_forex:
            pip_size = (
                point * 10
                if digits in (3, 5)
                else point
            )
        else:
            pip_size = 0.0

        return SymbolMetadata(
            symbol=simbolo,
            digits=digits,
            point=point,
            tick_size=tick_size,
            pip_size=pip_size,
            is_forex=is_forex,
        )

    except Exception:
        logger.exception(
            "Error al obtener metadatos de MT5 para %s.",
            simbolo,
        )
        return predeterminados