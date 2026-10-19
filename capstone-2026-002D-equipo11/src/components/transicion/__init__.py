# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
components/transicion
---------------
Transición entre las secciones de la plataforma.

Problema que resuelve: al cambiar de sección, Streamlit va dibujando la vista nueva de arriba hacia abajo sobre la
anterior, y durante esos instantes se ve el contenido viejo atenuado, textos sin estilo y bloques que se acomodan
(todo «amontonado» antes de distribuirse). Este paquete cubre solo el área de contenido en cuanto se pulsa un botón de
navegación y la descubre, ya armada, con un fundido corto cuando la ejecución termina. La barra lateral y la barra
superior no se tocan.

Cómo funciona: `pagina.py` guarda la vista dentro del contenedor con clave `pj_vista`; `transicion.js` (en un iframe
sin altura, como el del rail) detecta el clic en un botón de navegación, pone la clase `pj-navegando` en el elemento
html y la retira cuando Streamlit termina de ejecutar el script; `estilos.css` oculta `pj_vista` mientras esa clase
esté puesta y muestra una barra fina de progreso arriba. Si algo falla, un tope de 8 s retira la cortina.

Archivos: transicion.py (inyecta CSS y script), estilos.css, transicion.js.
"""
from components.transicion.transicion import inyectar_transicion

__all__ = ["inyectar_transicion"]

# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara __init__ .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
