# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara errores .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Errores de la fuente MT5.

Define `ErrorMT5` (fallo genérico con mensaje legible) y `OperacionNoPermitida`
(intento de usar una función de MT5 fuera de la lista de solo lectura)."""


# TITULO ERROR MT5

class ErrorMT5(Exception):
    """Fallo de la fuente MT5.

    Se lanza ante conexión imposible, símbolo inexistente, datos vacíos o
    parámetros inválidos; el mensaje se puede mostrar al usuario o al modelo."""


# TITULO OPERACION NO PERMITIDA

class OperacionNoPermitida(ErrorMT5, AttributeError):
    """Se intentó usar una función de MT5 vetada (solo lectura).

    Hereda también de AttributeError porque se lanza desde `__getattr__` del
    envoltorio `_SoloLectura`, donde Python espera ese tipo de excepción."""


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara errores .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
