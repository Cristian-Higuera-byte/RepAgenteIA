# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara formato .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Formateadores del Diario: duración legible, factor numérico (con infinito) y clase CSS de signo."""


def duracion(seg):
    """Convierte segundos en un texto corto de duración.

    Recibe `seg` (segundos, o None) y devuelve "Xd Yh" si supera un día, "Xh Ym" si supera
    una hora, o "Xm" en otro caso.
    """
    # Descompone en días, horas y minutos.
    seg = int(seg or 0)
    d, seg = divmod(seg, 86400)
    h, seg = divmod(seg, 3600)
    mn = seg // 60
    if d:
        return f"{d}d {h}h"
    if h:
        return f"{h}h {mn}m"
    return f"{mn}m"


def factor(x):
    """Formatea un factor (por ejemplo, el profit factor): "∞" si es infinito o el número con 2 decimales."""
    return "∞" if x == float("inf") else f"{x:,.2f}"


def clase_sube_baja(x):
    """Devuelve la clase CSS "up" si `x` es mayor o igual a cero (o None) y "down" si es negativo."""
    return "up" if (x or 0) >= 0 else "down"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara formato .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
