# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara cuenta .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
panel_orden/cuenta.py
---------------------
Lecturas de MetaTrader 5 que alimentan el ticket: info del símbolo, margen requerido,
margen libre y capital de la cuenta. Todo acotado por MT5_LOCK (acceso serializado).
Cada función devuelve None / valores neutros si MT5 no responde, para que la UI no falle.
"""
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from tools.puente_mt5 import MT5_LOCK


def info_simbolo(real):
    """symbol_info del símbolo (dígitos, volúmenes, contrato...). None si no está.

    Recibe el nombre real del símbolo, lo selecciona en el Market Watch de MT5 (efecto secundario) y
    devuelve su `symbol_info`."""
    try:
        with MT5_LOCK:
            mt5.symbol_select(real, True)
            return mt5.symbol_info(real)
    except Exception:
        return None


def margen(real, volumen, precio, tipo):
    """Margen requerido para una orden del lado `tipo` ('BUY'/'SELL'). None si falla.

    Recibe el símbolo real, el volumen en lotes y el precio de entrada; pregunta a MT5 con
    `order_calc_margin` y devuelve el margen en la moneda de la cuenta."""
    try:
        # Cualquier lado distinto de BUY se calcula como venta
        action = mt5.ORDER_TYPE_BUY if tipo == "BUY" else mt5.ORDER_TYPE_SELL
        with MT5_LOCK:
            return mt5.order_calc_margin(action, real, float(volumen), float(precio))
    except Exception:
        return None


def margen_libre():
    """Margen libre de la cuenta (account_info().margin_free) o None."""
    try:
        with MT5_LOCK:
            cuenta = mt5.account_info()
        return float(cuenta.margin_free) if cuenta is not None else None
    except Exception:
        return None


def capital_cuenta():
    """Equity y moneda de la cuenta (base de la Calculadora de riesgo): (equity, moneda).

    Si MT5 no responde devuelve `(None, "USD")` para que la interfaz use valores neutros."""
    try:
        with MT5_LOCK:
            cuenta = mt5.account_info()
        if cuenta is None:
            return None, "USD"
        return float(cuenta.equity), getattr(cuenta, "currency", "USD") or "USD"
    except Exception:
        return None, "USD"


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara cuenta .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
