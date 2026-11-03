# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara archivos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
archivos.py
------------
Herramienta utilitaria para listar los archivos presentes en un
directorio, útil para que el agente pueda revisar, por ejemplo, qué
reportes o históricos ya se han generado.
"""

import os

# TITULO LISTAR ARCHIVOS

def listar_archivos(directorio: str = ".") -> dict:
    """
    Lista los archivos y carpetas contenidos en un directorio dado.

    Parámetros:
        directorio (str): Ruta del directorio a inspeccionar.
                           Por defecto, el directorio actual.

    Retorna:
        dict: Lista de archivos, lista de carpetas y ruta consultada.
    """
    # Valida que la ruta exista y sea un directorio antes de listar.
    if not os.path.isdir(directorio):
        raise ValueError(f"El directorio '{directorio}' no existe.")

    # Separa los elementos en archivos y carpetas.
    elementos = os.listdir(directorio)
    archivos = [e for e in elementos if os.path.isfile(os.path.join(directorio, e))]
    carpetas = [e for e in elementos if os.path.isdir(os.path.join(directorio, e))]

    # Devuelve la ruta absoluta consultada junto con ambos listados.
    return {
        "directorio": os.path.abspath(directorio),
        "archivos": archivos,
        "carpetas": carpetas,
    }


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara archivos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
