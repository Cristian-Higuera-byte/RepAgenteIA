# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara aplicacion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
aplicacion.py
-------------
Lanzador del dashboard interactivo de Piña & Jara - Financial Terminal.

    streamlit run aplicacion.py

Este archivo es solo la puerta de entrada: prepara el entorno y le pide a `aplicacion_principal/`
que dibuje la página. Streamlit lo ejecuta de arriba abajo en CADA interacción del usuario, por eso
no define funciones: cada paso se ejecuta en el orden en que está escrito.
"""
import os
import sys

# Asegurar que la carpeta raíz del proyecto esté en la ruta de importación, para poder importar
# los paquetes del proyecto (aplicacion_principal, componentes_plataforma, nucleo_agente...).
_raiz = os.path.abspath(os.path.dirname(__file__))
if _raiz not in sys.path:
    sys.path.append(_raiz)

from aplicacion_principal.entorno import corregir_certificado_ssl, importar_consola

# El certificado SSL debe corregirse ANTES de importar cualquier librería de red.
corregir_certificado_ssl()
# Lógica del backend (consola_agente.py); vale None si el módulo no está disponible.
consola = importar_consola()

from aplicacion_principal.pagina import ejecutar

# Dibuja la página completa del dashboard.
ejecutar(consola)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara aplicacion .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
