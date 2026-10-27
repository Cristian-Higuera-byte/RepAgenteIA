# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara avisos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
panel_orden/avisos.py
--------------------
Aviso flotante (toast) del resultado de la orden: recuadro NARANJA (verde→naranja P&J)
para éxito, rojo para error; se cierra solo a los ~6 s o con la ✕. El JS vive en
estatico/avisos.js y se inyecta en el documento padre una sola vez por resultado
(gracias al `nonce`).
"""
import json

from .interfaz import leer_estatico


# TITULO AVISO JS

def aviso_js(mensaje: str, es_error: bool, nonce: str) -> str:
    """Devuelve el <script> listo para components.html(), con el mensaje/estado sustituidos.

    Recibe el texto del aviso, si es un error (fondo rojo) o un éxito (fondo naranja) y el `nonce` que
    identifica este resultado. Lee `avisos.js` y reemplaza sus marcadores de fondo, ícono, nonce y mensaje;
    el nonce y el mensaje se serializan con `json.dumps` para que queden como literales JS seguros."""
    # Degradado rojo para error y naranja de la marca para éxito
    fondo = ("linear-gradient(135deg,#f85149,#da3633)" if es_error
             else "linear-gradient(135deg,#ff4b4b,#ff8f00)")
    # Entidades HTML: triángulo de advertencia para error y marca de verificación para éxito
    icono = "&#9888;" if es_error else "&#10003;"
    js = (leer_estatico("avisos.js")
          .replace("__FONDO__", fondo)
          .replace("__ICONO__", icono)
          .replace("__NONCE__", json.dumps(str(nonce)))
          .replace("__MSG__", json.dumps(mensaje)))
    return f"<script>\n{js}\n</script>"


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara avisos .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
