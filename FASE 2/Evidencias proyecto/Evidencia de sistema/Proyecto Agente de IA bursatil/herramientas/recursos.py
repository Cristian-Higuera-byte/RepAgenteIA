# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara recursos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Utilidades para leer recursos de texto (CSS, JS, HTML, SQL) que llevan el encabezado de créditos.

Todos los archivos del proyecto llevan arriba y abajo el bloque de créditos de Piña y Jara y dos recuadros de
INICIO/FIN. Los recursos que se envían al navegador o a la base de datos deben recibirse SIN ese envoltorio, tal
como eran antes; este módulo ofrece la función que lo descarta.
"""


# TITULO SIN CREDITOS

def sin_creditos(contenido: str) -> str:
    """Descarta el encabezado, los recuadros de INICIO/FIN y el pie de créditos de un archivo CSS, JS o HTML.

    Los recursos estáticos llevan el bloque de créditos de Piña y Jara y dos recuadros que marcan dónde empieza y
    dónde termina el contenido real. Esta función devuelve solo ese contenido, exactamente como era antes de agregar
    los créditos, para que el navegador reciba el mismo código de siempre. Si el archivo no tiene recuadros (por
    ejemplo, uno anterior a los créditos) lo devuelve sin cambios."""
    # Posición de la primera marca de INICIO y de la última marca de FIN del archivo.
    marca_inicio = contenido.find("INICIO Piña y Jara")
    marca_fin = contenido.rfind("FIN Piña y Jara")
    # Sin recuadros no hay nada que recortar.
    if marca_inicio < 0 or marca_fin < 0:
        return contenido
    # El recuadro ocupa tres líneas; el contenido empieza tras la última y una línea en blanco.
    cierre_recuadro = contenido.index("\n", contenido.index("\n", marca_inicio) + 1)
    empieza = cierre_recuadro + 2
    # El recuadro de FIN empieza dos líneas por encima de la línea que contiene "FIN"; se descarta el salto previo.
    linea_fin = contenido.rfind("\n", 0, marca_fin) + 1
    inicio_recuadro_fin = contenido.rfind("\n", 0, linea_fin - 1) + 1
    return contenido[empieza:inicio_recuadro_fin - 1]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara recursos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
