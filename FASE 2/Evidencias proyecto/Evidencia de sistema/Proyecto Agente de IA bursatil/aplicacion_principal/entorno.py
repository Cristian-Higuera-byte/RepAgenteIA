# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara entorno .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Preparación del entorno de ejecución antes de cargar el resto de la aplicación.

Reúne dos tareas que `aplicacion.py` debe hacer ANTES de importar las pantallas:
corregir el certificado SSL y cargar, si está disponible, la lógica de la consola del agente.
"""
import os
import traceback
from types import ModuleType
from typing import Optional


# TITULO CORREGIR CERTIFICADO SSL

def corregir_certificado_ssl() -> None:
    """
    Copia el certificado raíz de `certifi` a una ruta sin tildes y apunta las variables de entorno a ella.

    En Windows, cuando la carpeta del proyecto o del usuario contiene tildes, las librerías de red
    (requests, curl, supabase) no logran abrir el archivo de certificados y fallan al conectarse.
    Esta función evita ese problema usando una copia en la carpeta temporal del sistema.
    Si algo falla (por ejemplo, `certifi` no está instalado) el error se ignora, porque la
    aplicación puede seguir funcionando con la configuración de certificados por defecto.
    """
    try:
        import certifi
        import shutil
        import tempfile
        # Ruta de la copia del certificado, dentro de la carpeta temporal del sistema (sin tildes).
        ruta_certificado = os.path.join(tempfile.gettempdir(), "cacert_ascii.pem")
        # Se copia una sola vez, no en cada reejecución de Streamlit.
        if not os.path.exists(ruta_certificado):
            shutil.copyfile(certifi.where(), ruta_certificado)
        # Las dos variables que leen las librerías de red para encontrar el certificado.
        os.environ["SSL_CERT_FILE"] = ruta_certificado
        os.environ["CURL_CA_BUNDLE"] = ruta_certificado
    except Exception:
        pass


# TITULO IMPORTAR CONSOLA

def importar_consola() -> Optional[ModuleType]:
    """
    Importa el módulo `consola_agente` (la lógica principal del backend) y lo devuelve.

    Devuelve `None` cuando el módulo no existe o falla al cargarse, para que la página siga
    abriendo igual. Los errores reales (por ejemplo, una dependencia que le falta a
    `consola_agente.py`) se imprimen en la terminal con su traza completa en lugar de ocultarse;
    solo se omite el aviso cuando el módulo directamente no está.
    """
    try:
        import consola_agente
        return consola_agente
    except ModuleNotFoundError as error:
        # Si lo que falta es otro módulo distinto de consola_agente, se muestra el error.
        if error.name != "consola_agente":
            traceback.print_exc()
    except Exception:
        # Cualquier otro fallo ocurrido dentro de consola_agente.py.
        traceback.print_exc()
    return None


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara entorno .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
