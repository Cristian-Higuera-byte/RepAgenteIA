# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara datos_iniciales .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""Estado inicial del trading desde el gráfico, leído de MetaTrader 5.

Entrega, para un símbolo, las posiciones abiertas y las órdenes pendientes con el mismo formato compacto que usa el
feed en vivo (`acc.pi` / `acc.ord`), más el volumen mínimo, la distancia mínima de stops del bróker, el valor del
punto y el desfase horario del servidor. `js_grafico.py` lo inyecta como `__POS_INI__` en el JS del gráfico, que
luego sigue actualizándose con el feed. Consulta MT5 (con `MT5_LOCK`) y los almacenes de OCO y stop dinámico en
disco; no escribe nada.
"""
import time

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from tools import almacen_oco, almacen_stop_dinamico
from tools.puente_mt5 import MT5_LOCK, inicializar_mt5


def iniciales(real: str) -> dict:
    """Posiciones y órdenes del símbolo con el mismo formato que el feed
    (`acc.pi` / `acc.ord`), más volumen mínimo, distancia mínima y desfase horario.

    Recibe `real`, el nombre del símbolo tal como existe en el bróker. Devuelve un diccionario con las claves
    `pos` (posiciones por ticket), `ord` (órdenes pendientes por ticket), `ba` (Bid/Ask, siempre [0, 0] porque
    llegan en vivo), `vmin` (volumen mínimo), `sm` (distancia mínima de stops en precio), `k` (valor monetario
    por unidad de precio, para proyectar P/G), `off` (desfase horario del servidor en segundos) y `em` (modo de
    expiración permitido). Si MT5 no responde o hay un error devuelve los valores por defecto sin lanzar nada.

    OJO: solo datos ESTABLES. Si algo cambiara a cada segundo (Bid/Ask, P/G), el
    HTML del gráfico sería distinto en cada rerun y Streamlit recargaría el iframe
    (se perdería el zoom). Bid/Ask y P/G llegan en vivo por el feed."""
    # Resultado con valores por defecto; se rellena más abajo si MT5 responde.
    out = {"pos": {}, "ord": {}, "ba": [0, 0], "vmin": 0.01, "sm": 0.0, "k": 0.0, "off": 0, "em": 0}
    try:
        if not inicializar_mt5():
            return out
        # Lecturas de MT5 agrupadas bajo el candado para no cruzarse con otros hilos.
        with MT5_LOCK:
            mt5.symbol_select(real, True)
            posiciones = mt5.positions_get(symbol=real) or []
            ordenes = mt5.orders_get(symbol=real) or []
            si = mt5.symbol_info(real)
            tick = mt5.symbol_info_tick(real)
        # k = valor del tick / tamaño del tick: convierte una diferencia de precio en dinero por lote.
        ts = float(getattr(si, "trade_tick_size", 0) or 0)
        k = (float(si.trade_tick_value) / ts) if si and ts else 0.0
        # sm = distancia mínima (en precio) que el bróker exige entre el precio y un SL/TP.
        sm = float(getattr(si, "trade_stops_level", 0) or 0) * float(getattr(si, "point", 0) or 0)
        # Datos estables del símbolo (no cambian a cada segundo, para no recargar el iframe).
        out.update(sm=sm, k=k, vmin=float(getattr(si, "volume_min", 0.01) or 0.01),
                   em=int(getattr(si, "expiration_mode", 0) or 0))   # 1 GTC · 2 DAY · 4 fecha
        if tick is not None:
            # hora del servidor del bróker − hora real (s), redondeado a 15 min: caducidad por fecha
            out["off"] = round((int(tick.time) - time.time()) / 900) * 900
        tr = almacen_stop_dinamico.leer()      # tickets con stop dinámico activo
        oco_tks = almacen_oco.tickets_en_oco()   # tickets vinculados en un par OCO
        # Posiciones abiertas: se indexan por ticket con las claves cortas que espera el JS.
        for p in posiciones:
            out["pos"][str(p.ticket)] = {
                "s": p.symbol, "t": int(p.type), "v": p.volume, "po": p.price_open,
                "sl": p.sl, "tp": p.tp, "k": k, "sm": sm,
                "tr": 1 if p.ticket in tr else 0,
            }
        # Órdenes pendientes (tipos 2 a 5: Buy/Sell Limit y Buy/Sell Stop); se ignoran las demás.
        for o in ordenes:
            if int(o.type) in (2, 3, 4, 5):
                out["ord"][str(o.ticket)] = {
                    "s": o.symbol, "t": int(o.type), "v": o.volume_current, "po": o.price_open,
                    "sl": o.sl, "tp": o.tp, "k": k, "sm": sm,
                    "tt": int(o.type_time), "ex": int(o.time_expiration or 0),
                    "oco": 1 if o.ticket in oco_tks else 0,
                }
    except Exception:
        # Cualquier fallo de MT5 deja el estado por defecto: el gráfico se dibuja igual, sin posiciones.
        pass
    return out


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara datos_iniciales .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
