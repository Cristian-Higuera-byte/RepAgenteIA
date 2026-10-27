# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara servidor .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Estado del servidor de datos (servidor_datos.py) e intervalo de los fragmentos `run_every`.

Expone la URL del servidor, una comprobación de salud con caché y la función que elige la frecuencia
de refresco de los fragmentos de Streamlit según haya o no feed en vivo.
"""
import os
import urllib.request

import streamlit as st

# URL base del servidor de datos (variable de entorno MT5_API_URL; por defecto, el puerto local 8000).
API_URL = os.environ.get("MT5_API_URL", "http://localhost:8000")


# TITULO FLUJO ACTIVO

@st.cache_data(ttl=15, show_spinner=False)
def flujo_activo() -> bool:
    """True si servidor_datos.py responde (se revisa como máximo cada 15 s).

    Consulta el endpoint `/salud` con un timeout de 0,4 s; cualquier error de red cuenta como inactivo.
    El resultado se cachea 15 s con `st.cache_data` para no hacer una petición en cada rerun.
    """
    # Petición breve de salud: el servidor está activo si responde 200.
    try:
        with urllib.request.urlopen(API_URL + "/salud", timeout=0.4) as r:
            return r.status == 200
    except Exception:
        # Servidor caído, URL inválida o timeout: se considera inactivo.
        return False


# TITULO INTERVALO

def intervalo(rapido: str = "2s", lento: str | None = None) -> str | None:
    """Intervalo de los fragmentos `run_every`. Con feed en vivo, por defecto
    NINGUNO (None): el feed ya pinta todo y cada recarga de Streamlit atenúa el
    bloque un instante (parpadeo). Los fragmentos se siguen recargando al
    interactuar (✕, +, botones). Sin feed, el refresco rápido de siempre.

    Recibe `rapido` (intervalo sin feed, "2s" por defecto) y `lento` (intervalo con feed; None desactiva
    el refresco periódico). Devuelve la cadena de intervalo o None, lista para `run_every`.
    """
    # Con feed activo se usa el intervalo lento (normalmente None); sin feed, el rápido.
    return lento if flujo_activo() else rapido


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara servidor .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
