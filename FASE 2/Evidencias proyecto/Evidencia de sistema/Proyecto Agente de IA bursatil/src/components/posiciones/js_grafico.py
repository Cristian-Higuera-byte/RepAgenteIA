# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara js_grafico .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ensamblador del JavaScript de trading desde el gráfico.

Concatena los fragmentos de `js/` en orden alfabético (00_, 10_…) y sustituye los marcadores `__POS_REAL__` (símbolo
real del bróker) y `__POS_INI__` (estado inicial de posiciones y órdenes). Todos los fragmentos forman un solo bloque
JS que `grafico/panel.py` inserta DENTRO de `iniciar()` del gráfico, por eso solo se cortan por responsabilidad y
ninguno cierra ni abre llaves por su cuenta.
"""
import json
from pathlib import Path

from components._estaticos import texto
from components.posiciones.datos_iniciales import iniciales
from tools.puente_mt5 import resolver_simbolo

# Carpeta con los fragmentos JavaScript, junto a este archivo.
_JS_DIR = Path(__file__).parent / "js"


def js_posiciones(simbolo: str) -> str:
    """Devuelve el JS de trading desde el gráfico para el símbolo cargado.

    Recibe `simbolo` (nombre mostrado en el dashboard, p. ej. "EURUSD..."). Resuelve el nombre real en MT5, lee y
    concatena los fragmentos de `js/` (sin sus créditos) y sustituye los marcadores por JSON válido. Lee MT5 a
    través de `iniciales`."""
    # Nombre real del símbolo en el bróker.
    real = resolver_simbolo(simbolo)
    # Todos los fragmentos .js concatenados en orden alfabético.
    js = "\n" + "".join(texto(f) for f in sorted(_JS_DIR.glob("*.js")))
    # Sustitución de marcadores: json.dumps garantiza comillas y escapes correctos dentro del JS.
    return (js.replace("__POS_REAL__", json.dumps(real))
              .replace("__POS_INI__", json.dumps(iniciales(real))))


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara js_grafico .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
