# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara inyeccion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Inyección del script del feed en la página de Streamlit.

Usa un componente HTML de altura cero para que el script corra en un iframe invisible con acceso al
DOM de la página padre.
"""
import streamlit as st
import streamlit.components.v1 as components

from components.flujo_precios.ensamblador import script_flujo
from components.flujo_precios.servidor import API_URL, flujo_activo


def inyectar_flujo():
    """Inserta (una vez por página) el script del feed en vivo. No ocupa espacio.

    Si el servidor de datos no responde no hace nada. En caso contrario crea un contenedor con clave
    `pj_feed` y dentro un componente HTML de altura 0 con el script ensamblado. No recibe ni devuelve nada.
    """
    # Sin servidor de datos no hay nada que transmitir: los fragmentos run_every siguen refrescando.
    if not flujo_activo():
        return
    # OJO: el CSS que oculta este contenedor (.st-key-pj_feed) va en el bloque de
    # estilos global de app.py. Un st.markdown(_CSS) propio aquí agregaba un
    # elemento más al flujo y Streamlit le sumaba ~1rem de separación (hueco
    # visible bajo la barra superior).
    # La clave pj_feed permite ocultar el contenedor desde el CSS global.
    with st.container(key="pj_feed"):
        components.html(script_flujo(API_URL), height=0)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara inyeccion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
