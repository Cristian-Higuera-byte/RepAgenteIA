# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara almacen_oco .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""
almacen_oco.py
------------
Almacén COMPARTIDO de los pares OCO (One-Cancels-the-Other).

Un OCO son DOS órdenes pendientes vinculadas: cuando una se EJECUTA, la otra se
cancela sola. MT5 no tiene OCO nativo (igual que el trailing, la lógica vive en
el cliente): el ticket de órdenes (`components/panel_orden.py`, proceso de
Streamlit) registra el par aquí al colocar las dos patas, y el motor de
`servidor_datos.py` (otro proceso) lo vigila y cancela la pata sobrante.

Ambos procesos comparten el archivo `data/oco.json`, como el resto de
`data/*.json`. La escritura es atómica (`os.replace`) para que el motor nunca
lea un archivo a medias.

Formato de `data/oco.json`:
    { "<par_id>": {"a": <ticketA>, "b": <ticketB>, "symbol": "<real>", "ts": <epoch>} }

- `par_id`: "<a>-<b>" (los dos tickets ordenados), identifica el par.
- `a` / `b`: los tickets de las dos órdenes pendientes de MT5 que forman el par.
- `symbol`: nombre real del símbolo en el terminal (informativo / para la UI).
- `ts`: epoch en que se creó el par (informativo).

Semántica OCO (la aplica el motor): si una pata SE EJECUTA (pasa a posición), se
cancela la otra. Si el usuario cancela una pata a mano, solo se rompe el vínculo
(la otra queda como orden pendiente normal).
"""
import json
import os
import tempfile
import threading
import time

# Carpeta `data/` en la raíz del proyecto.
import configuracion  # rutas centrales del proyecto (database/data)
_DIR = str(configuracion.DIR_DATOS)
# Archivo JSON compartido entre Streamlit y el motor con los pares OCO.
_RUTA = os.path.join(_DIR, "oco.json")
# Candado que serializa las modificaciones dentro del proceso.
_LOCK = threading.Lock()


def _par_id(a: int, b: int) -> str:
    """Construye el id del par "<menor>-<mayor>" a partir de dos tickets, sin importar el orden."""
    x, y = sorted((int(a), int(b)))
    return f"{x}-{y}"


def _leer_crudo() -> dict:
    """Lee `oco.json` tal cual (sin validar); devuelve {} si falta o está corrupto."""
    try:
        with open(_RUTA, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def leer() -> dict:
    """Devuelve {par_id(str): {"a": int, "b": int, "symbol": str, "ts": float}}."""
    out = {}
    # Normaliza tipos y descarta entradas dañadas sin interrumpir la lectura.
    for k, v in _leer_crudo().items():
        try:
            out[str(k)] = {"a": int(v["a"]), "b": int(v["b"]),
                           "symbol": str(v.get("symbol", "")), "ts": float(v.get("ts", 0.0))}
        except (ValueError, TypeError, KeyError, AttributeError):
            continue
    return out


def tickets_en_oco() -> set:
    """Conjunto de todos los tickets que participan en algún par OCO (para la UI/feed)."""
    s = set()
    for v in leer().values():
        s.add(v["a"])
        s.add(v["b"])
    return s


def _guardar(d: dict) -> None:
    """Escribe el diccionario de pares en `oco.json` de forma atómica (temporal + fsync + os.replace)."""
    os.makedirs(_DIR, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile("w", delete=False, dir=_DIR, encoding="utf-8")
    try:
        json.dump(d, tmp)
        tmp.flush()
        os.fsync(tmp.fileno())
    finally:
        tmp.close()
    os.replace(tmp.name, _RUTA)   # atómico: el otro proceso nunca ve un archivo a medias


def fijar(a: int, b: int, symbol: str = "") -> str:
    """Vincula dos órdenes pendientes como un par OCO y lo guarda. Devuelve el par_id.

    Recibe los tickets `a` y `b` y el nombre real del símbolo (informativo).
    Si el par ya existía, lo reemplaza con una marca de tiempo nueva.
    """
    with _LOCK:
        d = leer()
        pid = _par_id(a, b)
        d[pid] = {"a": int(a), "b": int(b), "symbol": str(symbol or ""), "ts": time.time()}
        _guardar(d)
        return pid


def quitar_par(par_id: str) -> None:
    """Elimina un par OCO por su id (si existía)."""
    with _LOCK:
        d = leer()
        if str(par_id) in d:
            d.pop(str(par_id))
            _guardar(d)


def quitar_ticket(ticket: int) -> None:
    """Elimina cualquier par que contenga este ticket (si existía)."""
    with _LOCK:
        d = leer()
        tk = int(ticket)
        cambio = False
        # Busca todos los pares donde el ticket sea pata A o B.
        for pid in [p for p, v in d.items() if v["a"] == tk or v["b"] == tk]:
            d.pop(pid, None)
            cambio = True
        if cambio:
            _guardar(d)


def mtime() -> float:
    """Marca de tiempo del archivo (para recargar solo cuando cambió)."""
    try:
        return os.path.getmtime(_RUTA)
    except OSError:
        return 0.0


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara almacen_oco .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
