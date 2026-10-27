# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara tickets .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Normalización de tickets entre brókers.

MT5 identifica posiciones y órdenes con enteros; Capital.com con un dealId de texto.
`ticket()` conserva el entero cuando el valor es numérico y deja el texto tal cual si no,
para no romper nada con `int()` según el proveedor activo."""


# TITULO TICKET

def ticket(valor):
    """Devuelve el ticket como int (si es numérico) o como str (dealId de Capital.com).

    Recibe int, float, str o None; None se devuelve sin cambios."""
    if valor is None:
        return None
    t = str(valor).strip()
    if t.endswith(".0"):
        t = t[:-2]
    return int(t) if t.isdigit() else t


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara tickets .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
