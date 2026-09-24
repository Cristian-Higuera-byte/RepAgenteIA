"""
archivos.py
------------
Herramienta utilitaria para listar los archivos presentes en un
directorio, útil para que el agente pueda revisar, por ejemplo, qué
reportes o históricos ya se han generado.
"""

import os


def listar_archivos(directorio: str = ".") -> dict:
    """
    Lista los archivos y carpetas contenidos en un directorio dado.

    Parámetros:
        directorio (str): Ruta del directorio a inspeccionar.
                           Por defecto, el directorio actual.

    Retorna:
        dict: Lista de archivos, lista de carpetas y ruta consultada.
    """
    if not os.path.isdir(directorio):
        raise ValueError(f"El directorio '{directorio}' no existe.")

    elementos = os.listdir(directorio)
    archivos = [e for e in elementos if os.path.isfile(os.path.join(directorio, e))]
    carpetas = [e for e in elementos if os.path.isdir(os.path.join(directorio, e))]

    return {
        "directorio": os.path.abspath(directorio),
        "archivos": archivos,
        "carpetas": carpetas,
    }