"""
mt5_bridge.py
---------------
Módulo encargado de la comunicación directa con MetaTrader 5 (MT5)
para extracción de datos en tiempo real, histórico y ejecución de órdenes.
"""

import os
import threading
from datetime import datetime
from typing import Optional

import MetaTrader5 as mt5  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Candado GLOBAL de acceso a MetaTrader 5
# ---------------------------------------------------------------------------
MT5_LOCK = threading.RLock()
_ORDER_LOCK = MT5_LOCK

# Ruta al ejecutable del terminal MetaTrader 5 (configurable por .env)
RUTA_TERMINAL_MT5 = os.getenv(
    "MT5_PATH",
    r"C:\Program Files\MetaTrader 5\terminal64.exe",
)


def inicializar_mt5(
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
) -> bool:
    """
    Inicializa y conecta con el terminal de MetaTrader 5 de forma segura.
    """
    with MT5_LOCK:
        # Verificar si ya está inicializado para evitar llamadas redundantes
        if mt5.terminal_info() is not None:
            return True

        # Intentar inicializar con la ruta configurada
        if not mt5.initialize(path=RUTA_TERMINAL_MT5):
            # Fallback: intentar inicializar sin ruta específica si la personalizada falla
            if not mt5.initialize():
                return False

        # Si se proporcionan credenciales específicas de cuenta
        if login and password and server:
            autorizado = mt5.login(login, password=password, server=server)
            if not autorizado:
                return False

        return True


def cerrar_mt5():
    """Cierra la conexión con MetaTrader 5."""
    with MT5_LOCK:
        mt5.shutdown()


# ---------------------------------------------------------------------------
# Resolvedor de símbolos entre brókers
# ---------------------------------------------------------------------------
_INDICE_SIMBOLOS: Optional[dict] = None


def _core_simbolo(name: str) -> str:
    """Núcleo comparable de un símbolo: sin '...' ni sufijos de bróker/bolsa."""
    s = (name or "").upper().strip().replace("...", "")
    if "." in s:  
        base, suf = s.rsplit(".", 1)
        if suf.isalnum() and 1 <= len(suf) <= 4:
            s = base
    return s


def _indice_local(refrescar: bool = False) -> dict:
    """Índice del terminal actual con validación para evitar caché vacío."""
    global _INDICE_SIMBOLOS
    if _INDICE_SIMBOLOS is not None and not refrescar:
        return _INDICE_SIMBOLOS

    exact: set = set()
    core: dict = {}
    
    try:
        if not inicializar_mt5():
            return {"exact": exact, "core": core}
            
        with MT5_LOCK:
            simbolos = mt5.symbols_get() or []
            
        for s in simbolos:
            exact.add(s.name)
            core.setdefault(_core_simbolo(s.name), s.name)
    except Exception:
        pass

    # CORRECCIÓN CRÍTICA: Si no hay símbolos, NO cachear para permitir reintentos
    if not exact:
        return {"exact": exact, "core": core}
        
    _INDICE_SIMBOLOS = {"exact": exact, "core": core}
    return _INDICE_SIMBOLOS


def resolver_simbolo(symbol: str) -> str:
    """Devuelve el nombre real del símbolo en el terminal actual."""
    if not symbol:
        return symbol
    idx = _indice_local()
    if symbol in idx["exact"]:
        return symbol
    return idx["core"].get(_core_simbolo(symbol), symbol)


def obtener_info_cuenta() -> dict:
    """Retorna el balance, equity y margen de la cuenta activa."""
    with MT5_LOCK:
        if not inicializar_mt5():
            return {"error": "Sin conexión con MT5"}
        cuenta = mt5.account_info()
        
    if cuenta is None:
        return {"error": "No se pudo obtener información de la cuenta MT5"}
    
    modo = getattr(cuenta, "trade_mode", 0)
    tipo = "Real" if modo == 2 else ("Concurso" if modo == 1 else "Demo")
    return {
        "login": cuenta.login,
        "nombre": getattr(cuenta, "name", ""),
        "servidor": getattr(cuenta, "server", ""),
        "tipo": tipo,
        "balance": cuenta.balance,
        "equity": cuenta.equity,
        "profit": cuenta.profit,
        "margin": getattr(cuenta, "margin", 0.0),
        "margin_free": cuenta.margin_free,
        "margin_level": getattr(cuenta, "margin_level", 0.0),
        "credit": getattr(cuenta, "credit", 0.0),
        "leverage": cuenta.leverage,
        "currency": cuenta.currency,
    }


def obtener_posiciones() -> list:
    """Posiciones abiertas de la cuenta."""
    try:
        with MT5_LOCK:
            if not inicializar_mt5():
                return []
            posiciones = mt5.positions_get()
    except Exception:
        posiciones = None
        
    salida = []
    for p in (posiciones or []):
        salida.append({
            "ticket": p.ticket,
            "symbol": p.symbol,
            "tipo": "Compra" if p.type == 0 else "Venta",
            "volumen": p.volume,
            "precio_apertura": p.price_open,
            "precio_actual": p.price_current,
            "profit": p.profit,
        })
    return salida


def obtener_precio_actual(symbol: str) -> dict:
    """Obtiene el precio Bid, Ask y último tick de un símbolo."""
    symbol = resolver_simbolo(symbol)
    with MT5_LOCK:
        if not inicializar_mt5():
            return {"error": "Sin conexión con MT5"}
        mt5.symbol_select(symbol, True)
        tick = mt5.symbol_info_tick(symbol)
        
    if tick is not None and (tick.bid or tick.ask):
        return {
            "symbol": symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "last": tick.last,
            "time": datetime.fromtimestamp(tick.time).strftime('%Y-%m-%d %H:%M:%S'),
        }

    with MT5_LOCK:
        info = mt5.symbol_info(symbol)
        
    if info is not None:
        try:
            bid = float(info.bid)
            ask = float(info.ask)
            last = float(info.last)
        except (AttributeError, TypeError, ValueError):
            bid = ask = last = 0.0
            
        if bid or ask:
            return {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "last": last,
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
    return {"error": f"No se pudo obtener el precio para {symbol}"}


def obtener_datos_historicos(symbol: str, timeframe=mt5.TIMEFRAME_H1, n_velas: int = 100) -> pd.DataFrame:
    """Descarga datos históricos OHLCV de MT5."""
    symbol = resolver_simbolo(symbol)
    with MT5_LOCK:
        if not inicializar_mt5():
            return pd.DataFrame()
        mt5.symbol_select(symbol, True)
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_velas)

    if rates is None or len(rates) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df


def ejecutar_orden_mercado(symbol: str, tipo: str, volumen: float, sl: float = 0.0, tp: float = 0.0) -> dict:
    """Ejecuta una orden de compra o venta a mercado en MT5."""
    symbol = resolver_simbolo(symbol)
    with _ORDER_LOCK:
        if not inicializar_mt5():
            return {"error": "Sin conexión con MT5"}
        mt5.symbol_select(symbol, True)
        sim_info = mt5.symbol_info(symbol)
        if sim_info is None:
            return {"error": f"Símbolo {symbol} no encontrado en MT5"}

        tipo_orden = mt5.ORDER_TYPE_BUY if tipo.upper() == 'BUY' else mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(symbol)
        precio = (tick.ask if tipo.upper() == 'BUY' else tick.bid) if tick else \
                 (sim_info.ask if tipo.upper() == 'BUY' else sim_info.bid)

        fm = getattr(sim_info, "filling_mode", 0)
        if fm & 1:
            filling = mt5.ORDER_FILLING_FOK
        elif fm & 2:
            filling = mt5.ORDER_FILLING_IOC
        else:
            filling = mt5.ORDER_FILLING_RETURN

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volumen),
            "type": tipo_orden,
            "price": precio,
            "deviation": 20,
            "magic": 234000,
            "comment": "Piña & Jara Terminal",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }
        if sl and sl > 0:
            request["sl"] = float(sl)
        if tp and tp > 0:
            request["tp"] = float(tp)

        resultado = mt5.order_send(request)
        
    if resultado is None:
        return {"error": f"order_send devolvió None: {mt5.last_error()}"}
    if resultado.retcode != mt5.TRADE_RETCODE_DONE:
        return {"error": f"Fallo al enviar orden (retcode {resultado.retcode}): "
                         f"{getattr(resultado, 'comment', '')}"}

    return {
        "status": "success",
        "order": resultado.order,
        "price": resultado.price,
        "volume": resultado.volume,
        "symbol": symbol,
    }


def cerrar_posicion(ticket: int) -> dict:
    """Cierra una posición abierta por su ticket."""
    with MT5_LOCK:
        if not inicializar_mt5():
            return {"error": "Sin conexión con MT5"}
        pos = mt5.positions_get(ticket=int(ticket))
        if not pos:
            return {"error": f"No se encontró la posición {ticket} (¿ya está cerrada?)"}
        p = pos[0]
        symbol = p.symbol
        mt5.symbol_select(symbol, True)
        sim_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)

        if p.type == mt5.ORDER_TYPE_BUY:
            tipo_cierre = mt5.ORDER_TYPE_SELL
            precio = (tick.bid if tick else sim_info.bid)
        else:
            tipo_cierre = mt5.ORDER_TYPE_BUY
            precio = (tick.ask if tick else sim_info.ask)

        fm = getattr(sim_info, "filling_mode", 0)
        if fm & 1:
            filling = mt5.ORDER_FILLING_FOK
        elif fm & 2:
            filling = mt5.ORDER_FILLING_IOC
        else:
            filling = mt5.ORDER_FILLING_RETURN

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(p.volume),
            "type": tipo_cierre,
            "position": int(ticket),
            "price": precio,
            "deviation": 20,
            "magic": 234000,
            "comment": "Cierre Piña & Jara",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }
        profit = p.profit
        resultado = mt5.order_send(request)

    if resultado is None:
        return {"error": f"order_send devolvió None: {mt5.last_error()}"}
    if resultado.retcode != mt5.TRADE_RETCODE_DONE:
        return {"error": f"Fallo al cerrar (retcode {resultado.retcode}): "
                         f"{getattr(resultado, 'comment', '')}"}
                         
    return {"status": "success", "profit": profit, "symbol": symbol}