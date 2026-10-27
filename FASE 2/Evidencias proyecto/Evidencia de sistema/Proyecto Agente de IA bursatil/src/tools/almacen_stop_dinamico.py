# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara almacen_stop_dinamico .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

"""
almacen_stop_dinamico.py
-----------------
Almacén COMPARTIDO de las configuraciones de "Stop dinámico" (trailing stop).

Lo escribe el panel de Cartera (proceso de Streamlit, `app.py`) y lo lee el motor
de `servidor_datos.py` (otro proceso): ambos comparten el archivo `data/trailing.json`,
igual que el resto de `data/*.json` del proyecto. La escritura es atómica
(`os.replace`) para que el motor nunca lea un archivo a medias.

Formato de `data/trailing.json`:
    { "<ticket>": {"dist": <distancia en precio>, "paso": <paso mínimo>} }

- `dist`: a qué distancia (en precio) por debajo (compra) / por encima (venta) del
  precio va el stop loss. El motor nunca lo mueve en contra.
- `paso`: mejora mínima para volver a mover el SL (evita reescribir en cada micro-tick).
"""
import json
import os
import tempfile
import threading

# Carpeta `data/` en la raíz del proyecto.
import configuracion  # rutas centrales del proyecto (database/data)
_DIR = str(configuracion.DIR_DATOS)
# Archivo JSON compartido con las configuraciones de trailing por ticket.
_RUTA = os.path.join(_DIR, "trailing.json")
# Candado que serializa las modificaciones dentro del proceso.
_LOCK = threading.Lock()


def _leer_crudo() -> dict:
    """Lee `trailing.json` tal cual (sin validar); devuelve {} si falta o está corrupto."""
    try:
        with open(_RUTA, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def leer() -> dict:
    """Devuelve {ticket(int): {"dist": float, "paso": float}}."""
    out = {}
    # Convierte claves a int y valores a float; descarta entradas dañadas.
    for k, v in _leer_crudo().items():
        try:
            out[int(k)] = {"dist": float(v.get("dist", 0.0)), "paso": float(v.get("paso", 0.0))}
        except (ValueError, TypeError, AttributeError):
            continue
    return out


def _guardar(d: dict) -> None:
    """Escribe las configuraciones en `trailing.json` de forma atómica (claves convertidas a texto)."""
    os.makedirs(_DIR, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile("w", delete=False, dir=_DIR, encoding="utf-8")
    try:
        json.dump({str(k): v for k, v in d.items()}, tmp)
        tmp.flush()
        os.fsync(tmp.fileno())
    finally:
        tmp.close()
    os.replace(tmp.name, _RUTA)   # atómico: el otro proceso nunca ve un archivo a medias


def fijar(ticket: int, dist: float, paso: float = 0.0) -> None:
    """Activa o actualiza el trailing de una posición.

    Recibe el ticket, la distancia `dist` (en precio) del SL respecto al precio y el
    `paso` mínimo de mejora. Persiste el cambio para que el motor lo lea.
    """
    with _LOCK:
        d = leer()
        d[int(ticket)] = {"dist": float(dist), "paso": float(paso)}
        _guardar(d)


def quitar(ticket: int) -> None:
    """Desactiva el trailing de una posición (si existía)."""
    with _LOCK:
        d = leer()
        if int(ticket) in d:
            d.pop(int(ticket))
            _guardar(d)


def mtime() -> float:
    """Marca de tiempo del archivo (para recargar solo cuando cambió)."""
    try:
        return os.path.getmtime(_RUTA)
    except OSError:
        return 0.0


# -------------------------------------------------------------------------------------------------------
# ------------------------------ FIN Piña y Jara almacen_stop_dinamico .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
