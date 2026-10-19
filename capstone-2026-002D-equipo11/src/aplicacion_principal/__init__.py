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
Paquete de la aplicación Streamlit: contiene todas las piezas que arman la página del dashboard
que lanza `app.py` en la raíz del proyecto.

Este archivo se deja sin importaciones a propósito: `app.py` necesita corregir el certificado
SSL ANTES de cargar cualquier librería de red, y si el paquete importara módulos pesados al abrirse
esa corrección llegaría tarde.

Módulos del paquete:
  entorno.py          corrige el certificado SSL e importa (si existe) la consola del agente
  estilos.py          entrega el CSS global y el HTML de la pantalla de carga (leídos de estilos.css
                      y pantalla_carga.html)
  cabecera.py         lee los datos de la cuenta de MT5 y dibuja la barra superior fija
  fragmentos.py       crea los fragmentos que se refrescan solos (favoritos, watchlist y cartera)
  vista_operativa.py  dibuja la vista de operar, común a Trading y Cartera
  vistas.py           decide qué vista se dibuja según el botón activo de la barra lateral
  dialogos.py         dibuja los diálogos que deben vivir fuera de los fragmentos en vivo
  pagina.py           función `ejecutar()` que arma la página completa en el orden correcto
"""


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
