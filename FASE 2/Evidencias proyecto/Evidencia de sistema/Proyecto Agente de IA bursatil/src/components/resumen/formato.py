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

"""Formateadores de texto y clases CSS de la vista Resumen (montos compactos y color según el signo)."""


def compactar(x, moneda="", signo=False):
    """Formatea montos grandes de forma compacta (1.2M, 31.6K) y legible.

    Recibe `x` (número), `moneda` (código opcional que se añade al final) y `signo` (si es True antepone "+" a los
    positivos; los negativos siempre llevan "-"). Devuelve el texto: millones con sufijo M, desde 10 mil con sufijo
    K y el resto con dos decimales."""
    a = abs(x)
    # Prefijo de signo: "+" solo si se pidió y el valor es positivo; "-" si es negativo.
    s = ("+" if (signo and x > 0) else ("-" if x < 0 else ""))
    # Escala del número según su magnitud.
    if a >= 1_000_000:
        cuerpo = f"{a/1_000_000:,.2f}M"
    elif a >= 10_000:
        cuerpo = f"{a/1_000:,.1f}K"
    else:
        cuerpo = f"{a:,.2f}"
    return f"{s}{cuerpo}" + (f" {moneda}" if moneda else "")


def clase_variacion(x):
    """Devuelve la clase CSS según el signo de `x`: rs-up (positivo), rs-down (negativo) o rs-neu (cero)."""
    return "rs-up" if x > 0 else ("rs-down" if x < 0 else "rs-neu")


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
