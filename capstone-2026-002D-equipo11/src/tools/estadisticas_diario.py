# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara estadisticas_diario .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""
estadisticas_diario.py
----------------
Trading Journal (sección E) — Tanda A: registro AUTOMÁTICO de operaciones cerradas
y estadísticas de rendimiento, todo derivado de los deals reales de MT5.

MT5 guarda cada operación como "deals": al abrir (DEAL_ENTRY_IN) y al cerrar
(DEAL_ENTRY_OUT), ligados por `position_id`. `obtener_historial` del bridge solo
mira los OUT (trae el P/G realizado); aquí se **emparejan IN + OUT por posición**
para reconstruir cada operación completa: entrada, salida, horas, tamaño, resultado,
comisión y swap. Soporta cierres parciales (varios OUT): se agrega por posición.

Estadísticas (todas calculables desde las operaciones cerradas):
  - Win rate, nº de operaciones, P&L total.
  - Profit Factor  = ganancias brutas / |pérdidas brutas|.
  - R/R promedio (payoff) = ganancia media de las ganadoras / pérdida media de las perdedoras.
  - Expectancy  = (winrate × ganancia media) − (lossrate × |pérdida media|)  [$ por operación].
  - Max drawdown sobre la curva de equity de operaciones cerradas (realizado acumulado).

NOTA FUTURO: el R/R *planificado* real (vs el stop con que se abrió) exige registrar
el SL/TP al colocar la orden (Tanda C, almacen_diario por position_id). Aquí el "R/R
promedio" es el payoff ratio, que no necesita el stop. Campos del usuario
(estrategia, emoción) y captura del gráfico = Tanda B (almacen_diario + mini-gráfico).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from tools.puente_mt5 import MT5_LOCK, PROVEEDOR, inicializar_mt5, obtener_historial
from tools import gestor_lista_activos as wl
from tools import almacen_diario

# MetaTrader5 es opcional: si no se puede importar (p. ej. fuera de Windows),
# `mt5` queda en None y las funciones devuelven resultados vacíos.
try:
    from proveedores.selector_mt5 import mt5
except Exception:                      # pragma: no cover
    mt5 = None


def _leer_deals(dias: int):
    """Lee de MT5 los deals (ejecuciones) de los últimos `dias` días.

    Toma el candado global de MT5, inicializa la conexión y consulta
    `history_deals_get` hasta mañana. Devuelve una lista (vacía si MT5 no está
    disponible, no inicializa o ocurre cualquier error); nunca lanza excepciones.
    """
    if mt5 is None:
        return []
    try:
        with MT5_LOCK:
            if not inicializar_mt5():
                return []
            deals = mt5.history_deals_get(datetime.now() - timedelta(days=dias),
                                          datetime.now() + timedelta(days=1))
        return list(deals or [])
    except Exception:
        return []


def _operaciones_capital(dias: int, limite: int) -> list:
    """Diario BÁSICO con Capital.com. Capital no entrega deals de entrada/salida
    emparejables como MT5 (su `/history/transactions` solo da "Trade closed" con
    símbolo, monto y fecha), así que se arma cada operación con lo disponible:
    símbolo, P/L (neto) y fecha de cierre. Los campos ricos de MT5 (entrada/salida
    exactas, duración, R/R) no están disponibles y quedan neutros.
    """
    salida = []
    for h in obtener_historial(dias=dias, limite=limite):
        sym = h.get("symbol", "") or ""
        neto = float(h.get("pg", 0.0) or 0.0)      # en Capital el monto del cierre es el P/L
        cierre = int(h.get("fecha", 0) or 0)
        salida.append({
            "pos_id": h.get("ticket", ""), "symbol": sym,
            "nombre": wl.nombre_visible(sym) if sym else sym,
            "tipo": "—",                           # Capital no expone la dirección en el historial
            "volumen": float(h.get("volumen", 0.0) or 0.0),
            "entrada": 0.0, "salida": float(h.get("precio_cierre", 0.0) or 0.0),
            # Capital no da la hora de apertura; se usa la del cierre (duración 0) para
            # que el mini-gráfico tenga un rango válido (evita timestamps negativos).
            "hora_in": cierre, "hora_out": cierre,
            "neto": neto, "profit": neto, "comision": 0.0, "swap": 0.0,
            "duracion_s": 0,
            "estrategia": "", "emocion": "", "razon": "", "plan": {},
            "sl": 0.0, "tp": 0.0, "rr_plan": None, "rr_real": None,
        })
    salida.sort(key=lambda x: x["hora_out"], reverse=True)
    return salida[:limite]


def operaciones(dias: int = 365, limite: int = 500) -> list:
    """Reconstruye las operaciones cerradas emparejando los deals IN y OUT por position_id.

    Recibe los días de historial a consultar y el máximo de operaciones a devolver.
    Devuelve una lista ordenada de la más reciente a la más antigua; cada elemento
    trae: pos_id, symbol, nombre, tipo, volumen, entrada, salida, hora_in, hora_out,
    neto, profit, comision, swap, duracion_s, y los datos del diario (estrategia,
    emocion, razon, plan, sl, tp, rr_plan, rr_real). Las posiciones aún abiertas se
    omiten. Lee MT5 (vía `_leer_deals`) y `data/journal.json`; no escribe nada.

    Con PROVEEDOR=capital usa un diario básico (ver `_operaciones_capital`), porque
    Capital.com no entrega los deals IN/OUT que MT5 sí empareja.
    """
    if PROVEEDOR == "capital":
        return _operaciones_capital(dias, limite)
    if mt5 is None:
        return []
    # Constantes de MT5 con valores por defecto por si la versión no las expone.
    ENTRY_IN = getattr(mt5, "DEAL_ENTRY_IN", 0)
    ENTRY_OUT = getattr(mt5, "DEAL_ENTRY_OUT", 1)
    TYPE_BUY = getattr(mt5, "DEAL_TYPE_BUY", 0)

    # Paso 1: agrupar los deals por posición, acumulando volumen, precio ponderado,
    # horas y resultados (soporta cierres parciales con varios OUT).
    porpos: dict = {}
    for d in _leer_deals(dias):
        # Se ignoran deals sin posición (depósitos, balance) o que no sean entrada/salida.
        pid = int(getattr(d, "position_id", 0) or 0)
        entry = getattr(d, "entry", None)
        if pid == 0 or entry not in (ENTRY_IN, ENTRY_OUT):
            continue
        r = porpos.setdefault(pid, {"in_vol": 0.0, "in_pv": 0.0, "out_vol": 0.0,
                                    "out_pv": 0.0, "t_in": None, "t_out": None,
                                    "neto": 0.0, "profit": 0.0, "com": 0.0, "swap": 0.0,
                                    "symbol": getattr(d, "symbol", ""), "tipo": None})
        # Extracción defensiva de los campos numéricos del deal.
        vol = float(getattr(d, "volume", 0.0) or 0.0)
        precio = float(getattr(d, "price", 0.0) or 0.0)
        t = int(getattr(d, "time", 0) or 0)
        prof = float(getattr(d, "profit", 0.0) or 0.0)
        com = float(getattr(d, "commission", 0.0) or 0.0) + float(getattr(d, "fee", 0.0) or 0.0)
        sw = float(getattr(d, "swap", 0.0) or 0.0)
        # Neto = ganancia + comisión/fee + swap (los costos vienen en negativo).
        r["neto"] += prof + com + sw
        r["profit"] += prof
        r["com"] += com
        r["swap"] += sw
        # Entrada: acumula volumen y precio ponderado; fija la hora más temprana y el tipo.
        if entry == ENTRY_IN:
            r["in_vol"] += vol
            r["in_pv"] += vol * precio
            r["t_in"] = t if r["t_in"] is None else min(r["t_in"], t)
            if r["tipo"] is None:
                r["tipo"] = "Compra" if getattr(d, "type", TYPE_BUY) == TYPE_BUY else "Venta"
        # Salida: acumula volumen y precio ponderado; fija la hora más tardía.
        else:
            r["out_vol"] += vol
            r["out_pv"] += vol * precio
            r["t_out"] = t if r["t_out"] is None else max(r["t_out"], t)

    notas = almacen_diario.leer()           # notas del usuario + plan por position_id (B/C)
    # Paso 2: convertir cada posición cerrada en una operación completa, con precios
    # medios de entrada/salida y el R/R (planificado y realizado) si hay stop.
    salida = []
    for pid, r in porpos.items():
        if r["t_out"] is None or r["in_vol"] <= 0:
            continue                       # posición aún abierta (sin cierre) → no es del diario
        # Precios medios ponderados por volumen.
        entrada = r["in_pv"] / r["in_vol"] if r["in_vol"] else 0.0
        salida_p = r["out_pv"] / r["out_vol"] if r["out_vol"] else 0.0
        sym = r["symbol"]
        compra = (r["tipo"] == "Compra")

        # Plan guardado al abrir (SL/TP/entrada); si falta entrada, usa la real.
        info = notas.get(str(pid), {})
        plan = info.get("plan") or {}
        sl = float(plan.get("sl", 0.0) or 0.0)
        tp = float(plan.get("tp", 0.0) or 0.0)
        ent_plan = float(plan.get("entrada", 0.0) or 0.0) or entrada
        # R/R solo se calcula si hubo un stop con riesgo positivo.
        rr_plan = rr_real = None
        if sl > 0:
            riesgo = (ent_plan - sl) if compra else (sl - ent_plan)   # distancia al stop
            if riesgo > 0:
                if tp > 0:
                    recompensa = (tp - ent_plan) if compra else (ent_plan - tp)
                    rr_plan = recompensa / riesgo                     # reward:risk planificado
                mov = (salida_p - entrada) if compra else (entrada - salida_p)
                rr_real = mov / riesgo                                # R realizado (múltiplo de R)

        salida.append({
            "pos_id": pid, "symbol": sym, "nombre": wl.nombre_visible(sym),
            "tipo": r["tipo"] or "—", "volumen": r["in_vol"],
            "entrada": entrada, "salida": salida_p,
            "hora_in": r["t_in"] or 0, "hora_out": r["t_out"] or 0,
            "neto": r["neto"], "profit": r["profit"], "comision": r["com"], "swap": r["swap"],
            "duracion_s": max(0, (r["t_out"] or 0) - (r["t_in"] or 0)),
            "estrategia": info.get("estrategia", ""), "emocion": info.get("emocion", ""),
            "razon": info.get("razon", ""), "plan": plan,
            "sl": sl, "tp": tp, "rr_plan": rr_plan, "rr_real": rr_real,
        })
    # Más recientes primero y recorte al límite pedido.
    salida.sort(key=lambda x: x["hora_out"], reverse=True)
    return salida[:limite]


def estadisticas(ops: list) -> dict:
    """Calcula las métricas del diario a partir de la lista de operaciones cerradas.

    Devuelve un dict con n, win_rate (%), pnl, profit_factor, expectancy ($ por
    operación), rr_prom (payoff), avg_win, avg_loss, max_dd, ganadoras, perdedoras,
    r_medio (múltiplo de R medio, None si ninguna tuvo stop) y con_plan. Con lista
    vacía devuelve todo en cero. Puede devolver `inf` si no hay pérdidas.
    """
    n = len(ops)
    # Sin operaciones: resultado neutro para que la UI no falle.
    if n == 0:
        return {"n": 0, "win_rate": 0.0, "pnl": 0.0, "profit_factor": 0.0,
                "expectancy": 0.0, "rr_prom": 0.0, "avg_win": 0.0, "avg_loss": 0.0,
                "max_dd": 0.0, "ganadoras": 0, "perdedoras": 0}
    # Separación de ganadoras y perdedoras por resultado neto.
    ganadoras = [o for o in ops if o["neto"] > 0]
    perdedoras = [o for o in ops if o["neto"] < 0]
    g_brutas = sum(o["neto"] for o in ganadoras)
    p_brutas = -sum(o["neto"] for o in perdedoras)          # positivo
    pnl = sum(o["neto"] for o in ops)
    nw, nl = len(ganadoras), len(perdedoras)
    # Tasa de acierto y promedios; los cocientes protegen la división entre cero.
    win_rate = nw / n * 100.0
    avg_win = (g_brutas / nw) if nw else 0.0
    avg_loss = (p_brutas / nl) if nl else 0.0
    profit_factor = (g_brutas / p_brutas) if p_brutas > 0 else (float("inf") if g_brutas > 0 else 0.0)
    rr_prom = (avg_win / avg_loss) if avg_loss > 0 else (float("inf") if avg_win > 0 else 0.0)
    # Expectancy en $ por operación (incluye ganadoras y perdedoras).
    expectancy = pnl / n
    # Max drawdown sobre la curva de equity de operaciones cerradas (orden cronológico).
    acum = 0.0
    pico = 0.0
    max_dd = 0.0
    for o in sorted(ops, key=lambda x: x["hora_out"]):
        acum += o["neto"]
        pico = max(pico, acum)
        max_dd = max(max_dd, pico - acum)
    # R medio realizado (múltiplo de R) sobre las operaciones que tienen stop planificado.
    reales = [o["rr_real"] for o in ops if o.get("rr_real") is not None]
    r_medio = (sum(reales) / len(reales)) if reales else None
    return {"n": n, "win_rate": win_rate, "pnl": pnl, "profit_factor": profit_factor,
            "expectancy": expectancy, "rr_prom": rr_prom, "avg_win": avg_win,
            "avg_loss": avg_loss, "max_dd": max_dd, "ganadoras": nw, "perdedoras": nl,
            "r_medio": r_medio, "con_plan": len(reales)}


def calcular(dias: int = 365, limite: int = 500) -> dict:
    """Atajo que devuelve {"operaciones": [...], "stats": {...}} para el rango pedido.

    Encadena `operaciones` y `estadisticas`; es el punto de entrada que usa la vista del diario.
    """
    ops = operaciones(dias, limite)
    return {"operaciones": ops, "stats": estadisticas(ops)}


# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara estadisticas_diario .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
