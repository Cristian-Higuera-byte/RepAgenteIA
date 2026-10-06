"""Fuente de datos: MetaTrader 5 (terminal de XM) — SOLO LECTURA.

Esta capa obtiene y normaliza datos del terminal MT5. No conoce al modelo ni a las
herramientas: devuelve diccionarios simples y lanza ErrorMT5 con un mensaje claro
(el registro de herramientas se lo pasa al modelo).

REQUISITOS
  * Windows, con el terminal MT5 de XM abierto y con la sesión iniciada.
  * pip install -U MetaTrader5   (la librería solo existe para Windows)
  * Opcional en el .env (si no se definen, se usa el terminal ya abierto, lo más simple y seguro):
        MT5_PATH=C:\\Program Files\\XM MT5\\terminal64.exe
        MT5_LOGIN=...  MT5_PASSWORD=...  MT5_SERVER=...
        MT5_PERMITIR_CUENTA=0   -> desactiva las herramientas de cuenta/posiciones/historial

SEGURIDAD
  * Este módulo NO puede operar: el módulo MetaTrader5 se envuelve en _SoloLectura, que solo
    deja pasar funciones de consulta. Intentar order_send (o cualquier otra) lanza error.
  * No se devuelven nombre, número de cuenta ni servidor; solo cifras de la cuenta.
  * Nunca se llama a shutdown(): el dashboard puede estar usando la misma conexión.

HORAS: MT5 entrega las horas en la hora del SERVIDOR del broker, no en la hora local.

Prueba rápida (terminal abierto):  python -m fuentes.mt5_fuente
"""
from __future__ import annotations

import importlib
import os
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

import MetaTrader5 as mt5  # type: ignore[import-untyped]
import config  # noqa: F401  (al importarlo se carga el .env)

_ = config  # referencia explícita para evitar avisos de "no accesado" en analizadores estáticos

TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1")

NOTA_HORAS = "Las horas son del servidor del broker, no tu hora local."

_FUNCIONES_PERMITIDAS = frozenset(
    {
        "initialize", "last_error", "version", "terminal_info", "account_info",
        "symbols_get", "symbol_info", "symbol_info_tick", "symbol_select",
        "copy_rates_from_pos", "copy_rates_range",
        "positions_get", "orders_get", "history_deals_get",
    }
)  # sin shutdown ni ninguna función que envíe, modifique o cierre órdenes

_TIPOS_CUENTA = {0: "demo", 1: "concurso", 2: "REAL"}
_MODOS_OPERACION = {0: "deshabilitado", 1: "solo compras", 2: "solo ventas", 3: "solo cerrar", 4: "completo"}
_TIPOS_ORDEN = {
    2: "buy limit", 3: "sell limit", 4: "buy stop", 5: "sell stop", 6: "buy stop limit", 7: "sell stop limit",
}

# Equivalencias típicas (nombres de Yahoo u otros -> nombres posibles en XM). Se prueban en orden.
_ALIAS: dict[str, tuple[str, ...]] = {
    "XAUUSD": ("XAUUSD", "GOLD"), "GC=F": ("GOLD", "XAUUSD"),
    "XAGUSD": ("XAGUSD", "SILVER"), "SI=F": ("SILVER", "XAGUSD"),
    "CL=F": ("OILCash", "USOIL", "WTI", "OIL"), "BZ=F": ("BRENT", "UKOIL", "OILCash"),
    "^GSPC": ("US500", "SPX500"), "^DJI": ("US30", "DJ30"),
    "^IXIC": ("USTEC", "US100", "NAS100"), "^NDX": ("USTEC", "US100", "NAS100"),
    "^GDAXI": ("DE40", "GER40", "DAX40"), "^FTSE": ("UK100",), "^N225": ("JP225",),
    "BTC-USD": ("BTCUSD",), "ETH-USD": ("ETHUSD",),
}


class ErrorMT5(Exception):
    """Fallo de la fuente MT5 (mensaje ya legible)."""


# ──────────────────────────────────────────────────────────────
# Conexión (solo lectura, un único acceso a la vez)
# ──────────────────────────────────────────────────────────────
class _SoloLectura:
    """Envuelve el módulo MetaTrader5 y solo deja pasar consultas y constantes."""

    def __init__(self, modulo: Any) -> None:
        object.__setattr__(self, "_modulo", modulo)

    def __getattr__(self, nombre: str) -> Any:
        if nombre in _FUNCIONES_PERMITIDAS or nombre.isupper():
            return getattr(self._modulo, nombre)
        raise ErrorMT5(f"Operación no permitida: '{nombre}'. Este agente es de solo lectura.")


_LOCK = threading.RLock()
_proxy: _SoloLectura | None = None

# Ejemplo de ruta típica para XM (ajusta la ruta según tu instalación):
RUTA_MT5 = "C:/Program Files/XM Global MT5/terminal64.exe"

def inicializar_mt5() -> None:
    if not mt5.initialize(path=RUTA_MT5):
        error = mt5.last_error()
        raise ErrorMT5(f"No se pudo conectar a MetaTrader 5 en {RUTA_MT5}. Código de error: {error}")


def _credenciales() -> dict[str, Any]:
    kw: dict[str, Any] = {}
    ruta = os.getenv("MT5_PATH", "").strip()
    if ruta:
        kw["path"] = ruta
    login = os.getenv("MT5_LOGIN", "").strip()
    if login:
        try:
            kw["login"] = int(login)
        except ValueError:
            raise ErrorMT5("MT5_LOGIN debe ser un número (el número de cuenta).") from None
        if os.getenv("MT5_PASSWORD"):
            kw["password"] = os.getenv("MT5_PASSWORD")
        if os.getenv("MT5_SERVER", "").strip():
            kw["server"] = os.getenv("MT5_SERVER", "").strip()
    return kw


def _asegurar_conexion() -> _SoloLectura:
    global _proxy
    if _proxy is None:
        try:
            modulo = importlib.import_module("MetaTrader5")
        except ImportError as e:
            raise ErrorMT5("Falta la librería MetaTrader5 (solo Windows): pip install -U MetaTrader5") from e
        _proxy = _SoloLectura(modulo)

    terminal = _proxy.terminal_info()
    if terminal is None:  # todavía no hay conexión con el terminal
        if not _proxy.initialize(**_credenciales()):
            raise ErrorMT5(
                f"No se pudo conectar con MetaTrader 5: {_proxy.last_error()}. "
                "¿Está abierto el terminal de XM y con la sesión iniciada?"
            )
        terminal = _proxy.terminal_info()
    if terminal is not None and not getattr(terminal, "connected", True):
        raise ErrorMT5("El terminal MT5 está abierto pero sin conexión con el servidor del broker.")
    return _proxy


@contextmanager
def _sesion() -> Iterator[_SoloLectura]:
    with _LOCK:
        yield _asegurar_conexion()


def _exigir_cuenta() -> None:
    if os.getenv("MT5_PERMITIR_CUENTA", "1").strip().lower() in ("0", "false", "no"):
        raise ErrorMT5("Los datos de la cuenta están desactivados para el agente (MT5_PERMITIR_CUENTA=0 en el .env).")


# ──────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────
def _num(v: Any, dec: int = 5) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return round(f, dec)


def _hora(ts: Any) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _sin_nulos(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _nivel(v: Any) -> float | None:
    """sl/tp: MT5 usa 0.0 para 'sin definir'."""
    return _num(v) if v else None


def _fecha_utc(texto: str, campo: str) -> datetime:
    try:
        return datetime.strptime(texto, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ErrorMT5(f"'{campo}' debe tener formato AAAA-MM-DD (recibido: {texto!r}).") from None


def _como_tupla(mt5: _SoloLectura, resultado: Any, accion: str) -> Any:
    """MT5 devuelve None tanto en error como (a veces) cuando no hay datos: se distingue por last_error."""
    if resultado is None:
        err = mt5.last_error()
        if err and err[0] != getattr(mt5, "RES_S_OK", 1):
            raise ErrorMT5(f"MT5 falló al {accion}: {err}")
        return ()
    return resultado


_cache_simbolos: tuple[float, list[dict[str, Any]]] | None = None


def _todos_los_simbolos(mt5: _SoloLectura) -> list[dict[str, Any]]:
    global _cache_simbolos
    ahora = time.monotonic()
    if _cache_simbolos and ahora - _cache_simbolos[0] < 600:
        return _cache_simbolos[1]
    crudos = _como_tupla(mt5, mt5.symbols_get(), "listar los símbolos")
    lista = [
        {
            "simbolo": s.name,
            "descripcion": s.description,
            "categoria": s.path.rsplit("\\", 1)[0] if "\\" in s.path else s.path,
            "visible": bool(s.visible),
        }
        for s in crudos
    ]
    _cache_simbolos = (ahora, lista)
    return lista


def _resolver(mt5: _SoloLectura, texto: str) -> str:
    """Traduce lo que escribe el usuario/modelo al nombre exacto del símbolo en el broker.

    Acepta el nombre exacto, formatos de Yahoo (EURUSD=X, GC=F, ^GSPC), 'EUR/USD',
    la marca '...' del watchlist y símbolos con sufijo del broker (EURUSDm, EURUSD.r...)."""
    bruto = (texto or "").strip()
    if not bruto:
        raise ErrorMT5("Falta el símbolo.")
    limpio = bruto.upper().replace("…", "").rstrip(".").replace("/", "").replace(" ", "")
    if limpio.endswith("=X"):
        limpio = limpio[:-2]
    alias = _ALIAS.get(limpio, ())

    vistos: set[str] = set()
    for candidato in (bruto, *alias, limpio):
        if candidato in vistos:
            continue
        vistos.add(candidato)
        if mt5.symbol_info(candidato) is not None:
            return candidato

    for base in (limpio, *alias):  # por prefijo: sufijos propios del tipo de cuenta
        encontrados = mt5.symbols_get(group=f"{base}*") or ()
        if encontrados:
            return sorted(encontrados, key=lambda s: (not s.visible, len(s.name), s.name))[0].name

    raise ErrorMT5(f"No encontré '{bruto}' en MT5. Usa mt5_buscar_simbolos para ver los nombres exactos de tu broker.")


def _preparar(mt5: _SoloLectura, simbolo: str) -> Any:
    """Se asegura de que el símbolo esté activo en el Market Watch (MT5 lo exige para dar datos)."""
    info = mt5.symbol_info(simbolo)
    if info is None:
        raise ErrorMT5(f"El símbolo '{simbolo}' no existe en MT5.")
    if not info.visible and not mt5.symbol_select(simbolo, True):
        raise ErrorMT5(f"No se pudo activar '{simbolo}' en el Market Watch: {mt5.last_error()}")
    return info


# ──────────────────────────────────────────────────────────────
# Mercado
# ──────────────────────────────────────────────────────────────
def buscar_simbolos(texto: str, max_resultados: int = 15) -> dict[str, Any]:
    t = (texto or "").strip().lower()
    if not t:
        raise ErrorMT5("Falta el texto a buscar.")
    n = max(1, min(int(max_resultados), 40))
    with _sesion() as mt5:
        todos = _todos_los_simbolos(mt5)
    coincidencias = [
        s for s in todos
        if t in s["simbolo"].lower() or t in (s["descripcion"] or "").lower() or t in (s["categoria"] or "").lower()
    ]
    coincidencias.sort(key=lambda s: (not s["simbolo"].lower().startswith(t), not s["visible"], len(s["simbolo"]), s["simbolo"]))
    return {"total_coincidencias": len(coincidencias), "simbolos": coincidencias[:n]}


def precio(simbolo: str) -> dict[str, Any]:
    with _sesion() as mt5:
        s = _resolver(mt5, simbolo)
        info = _preparar(mt5, s)
        tick = mt5.symbol_info_tick(s)
        if tick is None or (not tick.bid and not tick.ask):
            raise ErrorMT5(f"Sin cotización para {s} (mercado cerrado o sin datos): {mt5.last_error()}")

        previo = None
        d1 = mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_D1, 0, 2)
        if d1 is not None and len(d1) == 2:
            previo = float(d1[0]["close"])

        modo_operacion = getattr(info, "trade_mode", None)

        return _sin_nulos(
            {
                "simbolo": s,
                "descripcion": getattr(info, "description", None),
                "bid": _num(tick.bid),
                "ask": _num(tick.ask),
                "ultimo": _num(tick.last) if tick.last else None,
                "spread_puntos": int(info.spread),
                "spread_precio": _num(tick.ask - tick.bid),
                "maximo_dia_bid": _num(getattr(info, "bidhigh", 0)) or None,
                "minimo_dia_bid": _num(getattr(info, "bidlow", 0)) or None,
                "cierre_dia_anterior": _num(previo),
                "variacion_dia_pct": round((tick.bid / previo - 1) * 100, 2) if previo and tick.bid else None,
                "hora_ultimo_tick_servidor": _hora(tick.time),
                "operable": _MODOS_OPERACION.get(modo_operacion, "desconocido")
                if isinstance(modo_operacion, int)
                else "desconocido",
                "digitos": int(info.digits),
                "tamano_contrato": _num(getattr(info, "trade_contract_size", None)),
                "lote_minimo": _num(getattr(info, "volume_min", None)),
                "paso_lote": _num(getattr(info, "volume_step", None)),
                "moneda_base": getattr(info, "currency_base", None),
                "moneda_cotizacion": getattr(info, "currency_profit", None),
                "nota": NOTA_HORAS,
            }
        )


def velas(
    simbolo: str,
    timeframe: str = "H1",
    cantidad: int = 100,
    ultimas_velas: int = 20,
    desde: str | None = None,
    hasta: str | None = None,
) -> dict[str, Any]:
    """Resumen estadístico de TODAS las velas pedidas + detalle de las últimas N."""
    import numpy as np  # viene instalado junto con MetaTrader5

    tf = (timeframe or "").upper()
    if tf not in TIMEFRAMES:
        raise ErrorMT5(f"timeframe inválido: {timeframe!r}. Opciones: {', '.join(TIMEFRAMES)}")
    n = max(1, min(int(cantidad), 5000))
    k = max(0, min(int(ultimas_velas), 200))
    inicio = _fecha_utc(desde, "desde") if desde else None
    fin = (_fecha_utc(hasta, "hasta") + timedelta(days=1)) if hasta else datetime.now(timezone.utc) + timedelta(days=1)

    with _sesion() as mt5:
        s = _resolver(mt5, simbolo)
        _preparar(mt5, s)
        marco = getattr(mt5, f"TIMEFRAME_{tf}")
        if inicio:
            datos = mt5.copy_rates_range(s, marco, inicio, fin)
        else:
            datos = mt5.copy_rates_from_pos(s, marco, 0, n)
        if datos is None or len(datos) == 0:
            raise ErrorMT5(f"MT5 no devolvió velas para {s} ({tf}): {mt5.last_error()}")

    total = len(datos)
    cierres = datos["close"].astype(float)
    altos = datos["high"].astype(float)
    bajos = datos["low"].astype(float)
    retornos = np.diff(cierres) / cierres[:-1] if total > 1 else np.array([])
    i_max, i_min = int(np.argmax(altos)), int(np.argmin(bajos))

    resumen = _sin_nulos(
        {
            "velas_totales": total,
            "desde": _hora(datos["time"][0]),
            "hasta": _hora(datos["time"][-1]),
            "cierre_inicial": _num(cierres[0]),
            "cierre_final": _num(cierres[-1]),
            "variacion_pct": round((cierres[-1] / cierres[0] - 1) * 100, 2) if cierres[0] else None,
            "maximo": _num(altos[i_max]),
            "hora_maximo": _hora(datos["time"][i_max]),
            "minimo": _num(bajos[i_min]),
            "hora_minimo": _hora(datos["time"][i_min]),
            "rango_promedio_por_vela": _num(np.mean(altos - bajos)),
            "desv_estandar_retornos_por_vela_pct": round(float(np.std(retornos, ddof=1)) * 100, 3) if len(retornos) > 1 else None,
            "volumen_ticks_promedio": int(np.mean(datos["tick_volume"])),
        }
    )
    detalle = []
    if k:
        for f in datos[-k:]:
            detalle.append(
                {
                    "hora_servidor": _hora(f["time"])[:16],
                    "apertura": _num(f["open"]),
                    "maximo": _num(f["high"]),
                    "minimo": _num(f["low"]),
                    "cierre": _num(f["close"]),
                    "volumen_ticks": int(f["tick_volume"]),
                }
            )
    return {
        "simbolo": s,
        "timeframe": tf,
        "ultima_vela_en_formacion": inicio is None,
        "resumen_rango_completo": resumen,
        "ultimas_velas": detalle,
        "nota": NOTA_HORAS,
    }


# ──────────────────────────────────────────────────────────────
# Cuenta (solo cifras; sin nombre, número de cuenta ni servidor)
# ──────────────────────────────────────────────────────────────
def cuenta() -> dict[str, Any]:
    _exigir_cuenta()
    with _sesion() as mt5:
        a = mt5.account_info()
        if a is None:
            raise ErrorMT5(f"No se pudo leer la cuenta: {mt5.last_error()}")
        return _sin_nulos(
            {
                "tipo_cuenta": _TIPOS_CUENTA.get(a.trade_mode, "desconocida"),
                "moneda": a.currency,
                "apalancamiento": f"1:{a.leverage}",
                "balance": _num(a.balance, 2),
                "equity": _num(a.equity, 2),
                "beneficio_flotante": _num(a.profit, 2),
                "margen_usado": _num(a.margin, 2),
                "margen_libre": _num(a.margin_free, 2),
                "nivel_margen_pct": _num(a.margin_level, 2) if a.margin else None,
                "credito": _num(a.credit, 2) if a.credit else None,
                "trading_permitido": bool(a.trade_allowed),
            }
        )


def posiciones(simbolo: str | None = None) -> dict[str, Any]:
    _exigir_cuenta()
    with _sesion() as mt5:
        s = _resolver(mt5, simbolo) if simbolo else None
        crudas = _como_tupla(mt5, mt5.positions_get(symbol=s) if s else mt5.positions_get(), "leer las posiciones")

        lista: list[dict[str, Any]] = []
        neto: dict[str, float] = {}
        for p in crudas:
            compra = p.type == mt5.POSITION_TYPE_BUY
            neto[p.symbol] = round(neto.get(p.symbol, 0.0) + (p.volume if compra else -p.volume), 2)
            lista.append(
                _sin_nulos(
                    {
                        "ticket": int(p.ticket),
                        "simbolo": p.symbol,
                        "tipo": "compra" if compra else "venta",
                        "volumen": _num(p.volume, 2),
                        "precio_apertura": _num(p.price_open),
                        "precio_actual": _num(p.price_current),
                        "stop_loss": _nivel(p.sl),
                        "take_profit": _nivel(p.tp),
                        "beneficio": _num(p.profit, 2),
                        "swap": _num(p.swap, 2),
                        "abierta_servidor": _hora(p.time),
                    }
                )
            )
        lista.sort(key=lambda x: x["abierta_servidor"], reverse=True)
        return {
            "cantidad": len(lista),
            "beneficio_flotante_total": round(sum(x.get("beneficio", 0.0) for x in lista), 2),
            "volumen_neto_por_simbolo": neto,
            "posiciones": lista[:50],
            "omitidas": max(0, len(lista) - 50),
            "nota": NOTA_HORAS,
        }


def ordenes_pendientes(simbolo: str | None = None) -> dict[str, Any]:
    _exigir_cuenta()
    with _sesion() as mt5:
        s = _resolver(mt5, simbolo) if simbolo else None
        crudas = _como_tupla(mt5, mt5.orders_get(symbol=s) if s else mt5.orders_get(), "leer las órdenes pendientes")
        lista = [
            _sin_nulos(
                {
                    "ticket": int(o.ticket),
                    "simbolo": o.symbol,
                    "tipo": _TIPOS_ORDEN.get(o.type, f"tipo {o.type}"),
                    "volumen": _num(o.volume_current, 2),
                    "precio": _num(o.price_open),
                    "stop_loss": _nivel(o.sl),
                    "take_profit": _nivel(o.tp),
                    "creada_servidor": _hora(o.time_setup),
                    "expira_servidor": _hora(o.time_expiration) if o.time_expiration else None,
                }
            )
            for o in crudas
        ]
        return {"cantidad": len(lista), "ordenes": lista[:50], "omitidas": max(0, len(lista) - 50), "nota": NOTA_HORAS}


def historial_operaciones(dias: int = 30, simbolo: str | None = None, ultimas: int = 15) -> dict[str, Any]:
    """Operaciones CERRADAS en los últimos N días, con estadísticas (sin depósitos ni retiros)."""
    _exigir_cuenta()
    d = max(1, min(int(dias), 365))
    k = max(0, min(int(ultimas), 100))
    ahora = datetime.now(timezone.utc)

    with _sesion() as mt5:
        s = _resolver(mt5, simbolo) if simbolo else None
        deals = _como_tupla(
            mt5, mt5.history_deals_get(ahora - timedelta(days=d), ahora + timedelta(days=1)), "leer el historial"
        )
        salidas = (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_INOUT, mt5.DEAL_ENTRY_OUT_BY)
        tipos = (mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL)
        cerradas = [x for x in deals if x.type in tipos and x.entry in salidas and (s is None or x.symbol == s)]
        compra_id = mt5.DEAL_TYPE_BUY

    def neto(x: Any) -> float:
        return float(x.profit) + float(x.commission) + float(x.swap) + float(getattr(x, "fee", 0.0))

    if not cerradas:
        return {"dias": d, "operaciones_cerradas": 0, "nota": "No hay operaciones cerradas en ese periodo."}

    resultados = [neto(x) for x in cerradas]
    ganadoras = [r for r in resultados if r > 0]
    perdedoras = [r for r in resultados if r < 0]
    bruto_perdida = abs(sum(perdedoras))

    por_simbolo: dict[str, list[float]] = {}
    for x, r in zip(cerradas, resultados):
        por_simbolo.setdefault(x.symbol, []).append(r)
    ranking = sorted(
        (
            {"simbolo": sim, "operaciones": len(rs), "resultado_neto": round(sum(rs), 2)}
            for sim, rs in por_simbolo.items()
        ),
        key=lambda item: float(item["resultado_neto"]) if isinstance(item["resultado_neto"], (int, float)) else 0.0,
        reverse=True,
    )

    recientes = sorted(zip(cerradas, resultados), key=lambda t: t[0].time, reverse=True)[:k]
    detalle = [
        {
            "cerrada_servidor": _hora(x.time),
            "simbolo": x.symbol,
            # el deal de salida es contrario a la posición: un deal de compra cierra una venta
            "posicion_cerrada": "venta" if x.type == compra_id else "compra",
            "volumen": _num(x.volume, 2),
            "precio_cierre": _num(x.price),
            "resultado_neto": round(r, 2),
        }
        for x, r in recientes
    ]
    return _sin_nulos(
        {
            "dias": d,
            "operaciones_cerradas": len(cerradas),
            "ganadoras": len(ganadoras),
            "perdedoras": len(perdedoras),
            "tasa_acierto_pct": round(len(ganadoras) / len(cerradas) * 100, 1),
            "resultado_neto_total": round(sum(resultados), 2),
            "ganancia_bruta": round(sum(ganadoras), 2),
            "perdida_bruta": round(-bruto_perdida, 2),
            "factor_de_beneficio": round(sum(ganadoras) / bruto_perdida, 2) if bruto_perdida else None,
            "mejor_operacion": round(max(resultados), 2),
            "peor_operacion": round(min(resultados), 2),
            "por_simbolo": ranking[:10],
            "ultimas_operaciones": detalle,
            "nota": "resultado_neto = beneficio + comisión + swap. " + NOTA_HORAS,
        }
    )


if __name__ == "__main__":
    import json

    pruebas = (
        ("buscar_simbolos('eurusd')", lambda: buscar_simbolos("eurusd", 5)),
        ("precio('EURUSD')", lambda: precio("EURUSD")),
        ("velas('EURUSD', 'H1')", lambda: velas("EURUSD", "H1", 50, 3)),
        ("cuenta()", cuenta),
        ("posiciones()", posiciones),
        ("ordenes_pendientes()", ordenes_pendientes),
        ("historial_operaciones(30)", lambda: historial_operaciones(30, None, 3)),
    )
    for nombre, prueba in pruebas:
        print(f"\n=== {nombre}")
        try:
            print(json.dumps(prueba(), ensure_ascii=False, indent=2, default=str))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: {type(e).__name__}: {e}")