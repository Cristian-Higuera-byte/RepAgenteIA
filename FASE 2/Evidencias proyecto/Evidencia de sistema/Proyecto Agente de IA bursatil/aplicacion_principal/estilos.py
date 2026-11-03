# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara estilos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Acceso al CSS global y a la pantalla de carga de la página.

Los textos viven en archivos propios (`estilos.css` y `pantalla_carga.html`) para poder editarlos
con colores y autocompletado. Cada archivo lleva encabezado, recuadros de INICIO/FIN y pie de
créditos; `texto()` (de `componentes_plataforma/_estaticos.py`) descarta todo eso y este módulo entrega solo el contenido, con la misma sangría que
tenía cuando el texto estaba escrito dentro del antiguo app.py, de modo que el HTML que recibe
Streamlit es idéntico al de siempre.
"""
import textwrap
from pathlib import Path

from componentes_plataforma._estaticos import texto

# Carpeta de este paquete, donde están los archivos estilos.css y pantalla_carga.html.
_DIRECTORIO = Path(__file__).parent


# TITULO CSS GLOBAL

def css_global() -> str:
    """
    Entrega el bloque `<style>` con el tema oscuro tipo terminal de trading, listo para `st.markdown`.

    Lee `estilos.css` (sin créditos), aplica la sangría de 8 espacios que
    tenía el CSS original y lo encierra entre las etiquetas `<style>`.
    """
    # `texto` ya entrega el CSS sin encabezado, recuadros ni pie de créditos.
    css = texto(_DIRECTORIO / "estilos.css")
    return "\n    <style>\n" + textwrap.indent(css, " " * 8) + "    </style>\n"


# TITULO HTML PANTALLA CARGA

def html_pantalla_carga() -> str:
    """
    Entrega el HTML de la cubierta de carga a pantalla completa ("Cargando terminal…").

    Lee `pantalla_carga.html` (sin créditos) y mantiene la sangría
    original, para que el texto enviado a Streamlit sea exactamente el mismo de siempre.
    """
    # `texto` ya entrega el HTML sin encabezado, recuadros ni pie de créditos.
    html = texto(_DIRECTORIO / "pantalla_carga.html")
    return "\n" + textwrap.indent(html, " " * 8) + "    "


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara estilos .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
