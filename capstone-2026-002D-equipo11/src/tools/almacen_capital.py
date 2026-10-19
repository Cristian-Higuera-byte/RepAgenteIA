# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara almacen_capital .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
almacen_capital.py
---------------
Registro histórico del EQUITY de la cuenta a lo largo del tiempo (snapshots).

¿Por qué existe? MT5 entrega el equity ACTUAL (`account_info().equity`) y el
historial de operaciones CERRADAS (de ahí se reconstruye la curva de *balance*),
pero NO guarda el histórico del equity segundo a segundo. El drawdown REAL —el que
incluye lo que sufre la cuenta con posiciones abiertas— solo se puede calcular si
alguien va anotando el equity en el tiempo. Eso hace este módulo: `servidor_datos.py`
llama a `registrar(...)` periódicamente y la vista Resumen lee `serie(...)`.

  >>> drawdown de equity (real)  ≠  drawdown de balance (solo cambia en cierres)

------------------------------------------------------------------------------
NOTA PARA EL FUTURO (lanzamiento / multiusuario) — leer antes de escalar:
------------------------------------------------------------------------------
Esta implementación es MONO-USUARIO y LOCAL (un archivo `data/equity.json` para la
única cuenta conectada en el terminal de esta máquina). Es correcta para la demo y
para un solo trader, PERO al lanzar la app con varios usuarios hay que mover el
almacenamiento a una base por usuario (p. ej. Supabase, que el proyecto ya usa):

    tabla equity_snapshots(user_id, ts, equity, balance)   -- índice (user_id, ts)

La CLAVE del diseño: toda la app habla con este módulo por su interfaz
(`registrar` / `serie`), nunca con el archivo directamente. Por eso migrar a
Supabase el día del lanzamiento = reescribir SOLO este archivo (mismas firmas),
sin tocar `servidor_datos.py`, `estadisticas_portafolio.py` ni la UI. La lógica del
drawdown, la curva y las tarjetas se reaprovechan intactas. Lo único que no se
puede recuperar hacia atrás es la serie ya acumulada en la demo (ese dato nunca
existió para un usuario real): la curva de equity de cada usuario empieza a
construirse desde que su cuenta queda conectada.
------------------------------------------------------------------------------

Formato del archivo: {"puntos": [[ts, equity, balance], ...]} (ts = epoch, float).
Escritura atómica con os.replace (igual que almacen_oco / almacen_stop_dinamico).
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time

# Carpeta `data/` en la raíz del proyecto (dos niveles arriba de este archivo).
import configuracion  # rutas centrales del proyecto (database/data)
_DIR = str(configuracion.DIR_DATOS)
# Archivo JSON con la serie de snapshots de equity.
_RUTA = os.path.join(_DIR, "equity.json")

# Candado del proceso.
_LOCK = threading.Lock()         # serializa lecturas/escrituras dentro del proceso
# Tope de puntos guardados.
MAX_PUNTOS = 40_000              # ~4 semanas a 1 punto/min; se recorta el más antiguo
MIN_INTERVALO = 55.0            # s mínimos entre snapshots (lo controla también el motor)

_ultimo_ts = 0.0                # último snapshot escrito en ESTA ejecución (anti-spam)


def leer() -> list:
    """Lee `data/equity.json` y devuelve la serie completa [[ts, equity, balance], ...] (vieja → nueva).

    Toma el candado del proceso para no leer mientras `registrar` escribe. Si el archivo
    no existe, está corrupto o no se puede leer, devuelve una lista vacía (nunca lanza).
    """
    # Lectura protegida: cualquier fallo de archivo/JSON equivale a "sin histórico".
    try:
        with _LOCK, open(_RUTA, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return list(datos.get("puntos", []))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def serie(desde: float | None = None) -> list:
    """Devuelve la serie de snapshots, opcionalmente recortada a ts >= `desde` (epoch).

    Es la interfaz de lectura que usa la vista Resumen para calcular el drawdown de equity.
    """
    pts = leer()
    # Filtro por fecha de inicio (descarta también filas vacías o malformadas).
    if desde is not None:
        pts = [p for p in pts if p and p[0] >= desde]
    return pts


def registrar(equity: float, balance: float, ts: float | None = None,
              min_intervalo: float = MIN_INTERVALO) -> bool:
    """Añade un snapshot [ts, equity, balance] si pasó `min_intervalo` desde el anterior.

    Recibe el equity y balance actuales, un `ts` opcional (epoch; por defecto la hora
    actual) y el intervalo mínimo en segundos. Devuelve True si escribió y False si
    se omitió (anti-spam), si los valores no son numéricos o si falló el disco.
    Efectos: reescribe `data/equity.json` de forma atómica, recorta la serie a
    `MAX_PUNTOS` y actualiza `_ultimo_ts`. Pensado para llamarse en el bucle del
    motor sin saturar el disco.
    """
    global _ultimo_ts
    ahora = ts if ts is not None else time.time()
    # Anti-spam: si el último snapshot de esta ejecución es muy reciente, no escribe.
    if ahora - _ultimo_ts < min_intervalo:
        return False
    # Normaliza a 2 decimales; valores no numéricos abortan sin escribir.
    try:
        eq = round(float(equity), 2)
        bal = round(float(balance), 2)
    except (TypeError, ValueError):
        return False

    with _LOCK:
        # Relee el archivo dentro del candado para no perder puntos de otro hilo.
        pts = []
        try:
            with open(_RUTA, "r", encoding="utf-8") as f:
                pts = json.load(f).get("puntos", [])
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pts = []
        pts.append([round(ahora, 1), eq, bal])
        # Recorte: se descartan los puntos más antiguos al superar el máximo.
        if len(pts) > MAX_PUNTOS:
            pts = pts[-MAX_PUNTOS:]
        # Escritura atómica: archivo temporal en la misma carpeta y luego os.replace.
        try:
            os.makedirs(_DIR, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=_DIR, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"puntos": pts}, f)
            os.replace(tmp, _RUTA)          # atómico
        except OSError:
            return False
    _ultimo_ts = ahora
    return True


def mtime() -> float:
    """Devuelve la fecha de modificación (epoch) de `equity.json`, o -1.0 si no existe.

    Permite a quien consulta recargar la serie solo cuando el archivo cambió.
    """
    try:
        return os.path.getmtime(_RUTA)
    except OSError:
        return -1.0


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara almacen_capital .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
