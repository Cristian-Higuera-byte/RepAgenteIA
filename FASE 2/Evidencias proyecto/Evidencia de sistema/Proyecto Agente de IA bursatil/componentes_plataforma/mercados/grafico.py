# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara grafico .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Gráfico interactivo de la ficha (Lightweight Charts): carcasa HTML y JS en estatico/.

La plantilla `grafico_ficha.html` contiene marcadores (`__JS__`, `__DATA__`, `__DIG__`, `__H__`, `__SYM__`)
que este módulo sustituye antes de incrustarla con `components.html`.
"""
import json
from pathlib import Path

import streamlit.components.v1 as components

from componentes_plataforma._estaticos import texto

# Carpeta con la plantilla HTML y el JavaScript del gráfico
_DIR = Path(__file__).parent / "estatico"


# TITULO HTML GRAFICO

def _html_grafico() -> str:
    """Devuelve la plantilla HTML del gráfico con el marcador `__JS__` reemplazado por el contenido de
    `grafico_ficha.js`."""
    return texto(_DIR / "grafico_ficha.html").replace("__JS__", texto(_DIR / "grafico_ficha.js"))


# TITULO GRAFICO

def grafico(real: str, tabla_datos_d1, tabla_datos_h1, tabla_datos_m5, digitos: int, alto: int = 300):
    """Dibuja en la ficha el gráfico de línea interactivo con los periodos diario, horario y de 5 minutos.

    Recibe el símbolo real, tres DataFrames de velas (D1, H1 y M5; pueden ser None o vacíos), los decimales
    del precio y el alto en píxeles. Convierte cada serie a puntos `{time, value}` con el cierre, sustituye
    los marcadores de la plantilla y la incrusta con `components.html` (iframe con altura `alto + 40`).
    No devuelve nada."""
    def _puntos(tabla_datos):
        """Convierte un DataFrame de velas en una lista de puntos con tiempo unix y cierre redondeado;
        devuelve lista vacía si no hay datos."""
        if tabla_datos is None or tabla_datos.empty:
            return []
        return [{"time": int(marca_tiempo.timestamp()), "value": round(float(v), digitos)}
                for marca_tiempo, v in tabla_datos["close"].items()]
    # Datos serializados por periodo; el JS elige cuál mostrar según el botón activo
    data = {"d1": _puntos(tabla_datos_d1), "h1": _puntos(tabla_datos_h1), "m5": _puntos(tabla_datos_m5)}
    html = (_html_grafico().replace("__DATA__", json.dumps(data))
            .replace("__DIG__", str(digitos)).replace("__H__", str(alto))
            .replace("__SYM__", json.dumps(real)))
    components.html(html, height=alto + 40)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara grafico .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
