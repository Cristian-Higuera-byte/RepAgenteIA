# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara capital .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
capital.py  —  Fachada multiusuario del backend de Capital.com
--------------------------------------------------------------
Mantiene el mismo contrato público de siempre (`from herramientas.backends.capital import ...` y `cap.<nombre>`),
pero cada llamada se enruta a la copia del núcleo (`capital_nucleo.py`) que pertenece al usuario actual (ver
`sesiones_capital.py`). Así los ~45 archivos que usan el backend no cambian y cada usuario opera solo con su cuenta.

- Las funciones se entregan como envolturas estables: la copia se elige en CADA llamada, no al importar.
- Los datos (por ejemplo `cap.BASE` o `cap._tokens`) se leen de la copia del usuario actual en el momento de acceder.
"""
import functools

from herramientas.backends import sesiones_capital

# Envolturas ya creadas, por nombre (así `capital.f is capital.f`)
_envolturas: dict = {}


# TITULO ENVOLTURA

def _envolver(nombre: str, referencia):
    """Crea la función que, al llamarla, busca `nombre` en la copia del usuario actual y la ejecuta.

    `referencia` es la función de la copia usada solo para copiar su nombre y documentación."""

    def envoltura(*argumentos, **opciones):
        """Ejecuta la función homónima de la copia del núcleo que corresponde al usuario actual."""
        return getattr(sesiones_capital.modulo_actual(), nombre)(*argumentos, **opciones)

    functools.update_wrapper(envoltura, referencia)
    return envoltura


# TITULO OBTENER ATRIBUTO

def __getattr__(nombre: str):
    """Resuelve cualquier nombre del backend contra la copia del usuario actual (funciones envueltas, datos directos)."""
    if nombre.startswith("__"):
        raise AttributeError(nombre)
    envoltura = _envolturas.get(nombre)
    if envoltura is not None:
        return envoltura
    valor = getattr(sesiones_capital.modulo_actual(), nombre)
    if callable(valor) and not isinstance(valor, type):
        envoltura = _envolver(nombre, valor)
        _envolturas[nombre] = envoltura
        return envoltura
    return valor


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara capital .PY ---------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
