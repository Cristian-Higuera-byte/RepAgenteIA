"""
diagnostico_mt5.py
------------------
Diagnóstico de SOLO LECTURA de tu terminal MetaTrader 5 (cuenta demo XM).

Qué hace:
  * Lee datos de cuenta (sin login ni saldos), del terminal y de TODOS los
    símbolos que ofrece el servidor.
  * Mide el desfase entre la hora del servidor y UTC.
  * Verifica qué columnas entrega MT5 en las velas.

Qué NO hace:
  * No envía órdenes.
  * No modifica el Market Watch (no usa symbol_select).
  * No toca ni importa nada del dashboard.

Uso (desde la raíz del proyecto, en OTRO proceso; no lo ejecutes desde Streamlit):
    python diagnostico_mt5.py

Genera en la carpeta actual:
    diagnostico_mt5_resumen.txt   <- este es el que debes compartirme
    diagnostico_mt5.json          <- detalle completo (por si hace falta)
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

import MetaTrader5 as mt5  # type: ignore[import-untyped]

SIMBOLOS_PRUEBA = ["BTCUSD", "EURUSD", "USDJPY", "GBPUSD", "GOLD", "AAVEUSD"]
SIMBOLOS_ACCIONES = ["3MCo", "ABInbev", "A2A", "3iGroup"]   # vistos en tu lista de activos


def _const(nombre: str, defecto: int) -> int:
    return getattr(mt5, nombre, defecto)


def _modo_cuenta(v) -> str:
    tabla = {_const("ACCOUNT_TRADE_MODE_DEMO", 0): "DEMO",
             _const("ACCOUNT_TRADE_MODE_CONTEST", 1): "CONCURSO",
             _const("ACCOUNT_TRADE_MODE_REAL", 2): "REAL"}
    return tabla.get(v, f"desconocido({v})")


def _modo_margen(v) -> str:
    tabla = {_const("ACCOUNT_MARGIN_MODE_RETAIL_NETTING", 0): "NETTING",
             _const("ACCOUNT_MARGIN_MODE_EXCHANGE", 1): "EXCHANGE",
             _const("ACCOUNT_MARGIN_MODE_RETAIL_HEDGING", 2): "HEDGING"}
    return tabla.get(v, f"desconocido({v})")


def _hora(ts) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _ficha(s) -> dict:
    return {
        "nombre": s.name, "descripcion": s.description, "ruta": s.path,
        "digitos": s.digits, "visible": s.visible, "modo_trading": s.trade_mode,
        "moneda_base": s.currency_base, "moneda_beneficio": s.currency_profit,
        "tamano_contrato": s.trade_contract_size, "vol_min": s.volume_min,
        "vol_max": s.volume_max, "vol_paso": s.volume_step, "spread": s.spread,
        "modo_llenado": s.filling_mode,
    }


def main() -> int:
    if not mt5.initialize():
        print("No se pudo conectar al terminal MT5:", mt5.last_error())
        print("Comprueba que el terminal está abierto y con sesión iniciada.")
        return 1

    try:
        ahora = datetime.now(timezone.utc)
        resultado: dict = {"generado_utc": ahora.isoformat(timespec="seconds")}

        cuenta = mt5.account_info()
        if cuenta is not None:
            resultado["cuenta"] = {
                "modo": _modo_cuenta(cuenta.trade_mode),
                "margen": _modo_margen(cuenta.margin_mode),
                "moneda": cuenta.currency,
                "apalancamiento": cuenta.leverage,
                "servidor": cuenta.server,
                "empresa": cuenta.company,
                "trading_permitido": cuenta.trade_allowed,
            }
        term = mt5.terminal_info()
        if term is not None:
            resultado["terminal"] = {
                "conectado": term.connected,
                "trading_permitido": term.trade_allowed,
                "build": term.build,
            }

        # ---- Símbolos
        simbolos = mt5.symbols_get() or []
        filas = [_ficha(s) for s in simbolos]
        resultado["simbolos"] = filas

        # ---- Hora del servidor (solo símbolos ya visibles, sin modificar el Market Watch)
        pruebas = []
        for nombre in SIMBOLOS_PRUEBA:
            info = mt5.symbol_info(nombre)
            if info is None:
                pruebas.append({"simbolo": nombre, "estado": "no existe en este servidor"})
                continue
            if not info.visible:
                pruebas.append({"simbolo": nombre,
                                "estado": "no visible en Market Watch (omitido para no modificarlo)"})
                continue
            tick = mt5.symbol_info_tick(nombre)
            if tick is None:
                pruebas.append({"simbolo": nombre, "estado": "sin tick"})
                continue
            delta = tick.time - ahora.timestamp()
            horas = round(delta / 1800) * 0.5
            residuo = delta - horas * 3600
            pruebas.append({
                "simbolo": nombre,
                "tick_hora_servidor": _hora(tick.time),
                "desfase_vs_utc_horas": horas,
                "desfase_fiable": abs(residuo) < 300,   # tick reciente (< 5 min)
                "bid": tick.bid, "ask": tick.ask, "last": tick.last,
            })
        resultado["pruebas_tick"] = pruebas

        # ---- Formato de las velas
        velas = None
        for nombre in SIMBOLOS_PRUEBA:
            info = mt5.symbol_info(nombre)
            if info is not None and info.visible:
                rates = mt5.copy_rates_from_pos(nombre, mt5.TIMEFRAME_H1, 0, 3)
                if rates is not None and len(rates):
                    velas = {"simbolo": nombre,
                             "columnas": list(rates.dtype.names),
                             "ultima_vela_hora_servidor": _hora(rates[-1]["time"])}
                break
        resultado["velas_h1"] = velas

        with open("diagnostico_mt5.json", "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=1, default=str)

        # ---- Resumen legible
        L: list[str] = ["=== DIAGNÓSTICO MT5 ===", f"Generado (UTC): {resultado['generado_utc']}", ""]
        L.append(f"Cuenta:   {resultado.get('cuenta')}")
        L.append(f"Terminal: {resultado.get('terminal')}")
        L.append("")
        visibles = sum(1 for f in filas if f["visible"])
        L.append(f"Símbolos en el servidor: {len(filas)}  (visibles en Market Watch: {visibles})")
        L.append("")

        por_cat: dict[str, list[dict]] = defaultdict(list)
        for fila in filas:
            por_cat[(fila["ruta"] or "").split("\\")[0] or "(sin ruta)"].append(fila)
        L.append("--- CATEGORÍAS (primer nivel de la ruta) ---")
        for cat, items in sorted(por_cat.items(), key=lambda kv: -len(kv[1])):
            L.append(f"[{cat}] {len(items)} símbolos")
            for fila in items[:4]:
                L.append(f"    {fila['nombre']} | {fila['descripcion']} | {fila['ruta']} | dígitos={fila['digitos']}")
        L.append("")

        raros = [fila["nombre"] for fila in filas if not fila["nombre"].isalnum()]
        L.append(f"--- NOMBRES CON CARACTERES ESPECIALES (sufijos, puntos, #): {len(raros)} ---")
        L.append("    " + ", ".join(raros[:20]) if raros else "    (ninguno)")
        L.append("")
        L.append(f"--- DECIMALES (dígitos) ---  {dict(Counter(f['digitos'] for f in filas))}")
        L.append(f"--- MODOS DE TRADING ---     {dict(Counter(f['modo_trading'] for f in filas))}")
        L.append("")

        L.append("--- FICHAS DE SÍMBOLOS DE TU DASHBOARD ---")
        por_nombre = {f["nombre"]: f for f in filas}
        for nombre in SIMBOLOS_PRUEBA + SIMBOLOS_ACCIONES:
            ficha = por_nombre.get(nombre)
            if ficha is None:
                L.append(f"{nombre}: NO ENCONTRADO")
                continue
            L.append(f"{nombre}: desc='{ficha['descripcion']}' ruta='{ficha['ruta']}' dígitos={ficha['digitos']} "
                     f"moneda={ficha['moneda_beneficio']} contrato={ficha['tamano_contrato']} "
                     f"vol(min/paso/max)={ficha['vol_min']}/{ficha['vol_paso']}/{ficha['vol_max']} "
                     f"llenado={ficha['modo_llenado']}")
        L.append("")

        L.append("--- HORA DEL SERVIDOR vs UTC ---")
        for p in pruebas:
            L.append(f"    {p}")
        L.append("")
        L.append(f"--- VELAS H1 ---  {velas}")

        with open("diagnostico_mt5_resumen.txt", "w", encoding="utf-8") as resumen_file:
            resumen_file.write("\n".join(L))

        print("Listo. Comparte el contenido de: diagnostico_mt5_resumen.txt")
        return 0
    finally:
        mt5.shutdown()   # solo cierra la conexión de ESTE proceso, no el terminal ni el dashboard


if __name__ == "__main__":
    sys.exit(main())