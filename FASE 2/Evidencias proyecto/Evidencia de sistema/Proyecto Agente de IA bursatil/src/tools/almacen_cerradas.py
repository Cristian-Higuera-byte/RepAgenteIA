# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara almacen_cerradas .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
almacen_cerradas.py
-----------------
Persistencia de las TARJETAS DE POSICIONES CERRADAS de la Cartera.

Viven en `st.session_state`, que se reinicia al recargar la página (F5 = sesión
nueva). Para que las tarjetas sobrevivan al F5 mientras el navegador está abierto,
se respaldan en `data/cerradas.json` (escritura atómica, como `trailing.json`).

Es un archivo único (demo de una sola cuenta MT5). Si en el futuro hay varias
cuentas/usuarios, convendría keyearlo por usuario.
"""
import json
import os
import tempfile
import threading

# Carpeta `data/` en la raíz del proyecto.
import configuracion  # rutas centrales del proyecto (database/data)
_DIR = str(configuracion.DIR_DATOS)
# Archivo JSON de respaldo de las tarjetas cerradas.
_RUTA = os.path.join(_DIR, "cerradas.json")
# Candado que serializa las escrituras dentro del proceso.
_LOCK = threading.Lock()


def leer() -> list:
    """Lee `data/cerradas.json` y devuelve la lista de tarjetas cerradas (más recientes primero).

    Si el archivo falta, está corrupto o no contiene una lista, devuelve una lista vacía.
    """
    # Cualquier fallo de lectura se trata como "sin tarjetas guardadas".
    try:
        with open(_RUTA, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def guardar(lista: list) -> None:
    """Persiste la lista de tarjetas cerradas en `data/cerradas.json`, reemplazando el contenido previo.

    Escribe en un archivo temporal, fuerza el volcado a disco (fsync) y lo mueve con
    os.replace, de modo que el archivo nunca queda a medias. Crea la carpeta si falta.
    """
    with _LOCK:
        os.makedirs(_DIR, exist_ok=True)
        # Archivo temporal en la misma carpeta para que el reemplazo sea atómico.
        tmp = tempfile.NamedTemporaryFile("w", delete=False, dir=_DIR, encoding="utf-8")
        try:
            json.dump(list(lista), tmp)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.replace(tmp.name, _RUTA)   # atómico


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara almacen_cerradas .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
