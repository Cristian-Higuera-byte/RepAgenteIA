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

"""Formato de duraciones para el pie del turno y el cronómetro en vivo."""
from __future__ import annotations


def formatear_duracion(segundos: float) -> str:
    """Formatea una duración en segundos como texto legible: '7 s', '1 min 12 s'... (los negativos cuentan como 0)."""
    s = max(0, int(segundos))
    return f"{s} s" if s < 60 else f"{s // 60} min {s % 60:02d} s"


def formatear_reloj(segundos: float) -> str:
    """Formatea segundos como reloj mm:ss: '00:07', '01:12' (para el cronómetro en vivo)."""
    s = max(0, int(segundos))
    return f"{s // 60:02d}:{s % 60:02d}"


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
