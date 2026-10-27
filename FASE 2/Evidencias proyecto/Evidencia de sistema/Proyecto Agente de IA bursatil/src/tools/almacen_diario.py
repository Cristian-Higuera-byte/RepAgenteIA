# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara almacen_diario .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
almacen_diario.py
----------------
Datos del Trading Journal que MT5 NO guarda: notas del usuario por operación
(estrategia, emoción/razón) y el "plan" de la orden al abrir (entrada, SL, TP),
necesario para el R/R planificado. Clave = `position_id` de MT5 (la misma con la
que estadisticas_diario empareja los deals), para que notas y plan se peguen a su operación.

------------------------------------------------------------------------------
NOTA PARA EL FUTURO (lanzamiento / multiusuario) — igual que almacen_capital:
------------------------------------------------------------------------------
Hoy es un archivo local `data/journal.json` para la única cuenta del terminal. Al
lanzar con varios usuarios, mover a Supabase por usuario:
    tabla journal(user_id, position_id, estrategia, emocion, razon,
                  plan_entrada, plan_sl, plan_tp, plan_tipo, plan_vol, ts)
    PK (user_id, position_id)
Toda la app habla con este módulo por su interfaz (`obtener`/`guardar_notas`/
`guardar_plan`), nunca con el archivo → migrar = reescribir SOLO este archivo
(mismas firmas), sin tocar estadisticas_diario, el bridge ni la UI. Ver también
[[drawdown-equity-multiusuario]] (mismo patrón con almacen_capital).
------------------------------------------------------------------------------

Formato: {"<position_id>": {"estrategia","emocion","razon","plan":{...},"ts"}}.
Escritura atómica (os.replace), como almacen_oco / almacen_stop_dinamico / almacen_capital.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time

# Carpeta `data/` en la raíz del proyecto.
import configuracion  # rutas centrales del proyecto (database/data)
_DIR = str(configuracion.DIR_DATOS)
# Archivo JSON del Trading Journal (notas y planes por position_id).
_RUTA = os.path.join(_DIR, "journal.json")
# Candado que serializa lecturas/escrituras dentro del proceso.
_LOCK = threading.Lock()


def leer() -> dict:
    """Devuelve todo el journal como {position_id(str): {...}}; vacío si el archivo falta o está corrupto."""
    try:
        with _LOCK, open(_RUTA, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def obtener(pos_id) -> dict:
    """Devuelve la fila del journal (notas, plan, ts) de una posición, o {} si no existe.

    `pos_id` es el position_id de MT5; se convierte a texto porque JSON solo admite claves str.
    """
    return leer().get(str(pos_id), {})


def _escribir(datos: dict) -> bool:
    """Escribe el diccionario completo en `journal.json` de forma atómica (temporal + os.replace).

    Devuelve True si tuvo éxito y False si hubo un error de disco. No toma el candado:
    lo hace quien la llama (`_merge`).
    """
    try:
        os.makedirs(_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=_DIR, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False)
        os.replace(tmp, _RUTA)
        return True
    except OSError:
        return False


def _merge(pos_id, campos: dict) -> bool:
    """Fusiona `campos` en la fila de una posición y guarda, sin borrar los demás campos.

    Relee el archivo dentro del candado, actualiza la fila (notas y plan conviven),
    sella `ts` con la hora actual y escribe. Devuelve True si se guardó.
    """
    with _LOCK:
        # Relectura bajo candado para no pisar cambios recientes.
        datos = {}
        try:
            with open(_RUTA, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            datos = {}
        # Actualiza solo los campos recibidos y sella la hora de modificación.
        fila = datos.get(str(pos_id), {})
        fila.update(campos)
        fila["ts"] = time.time()
        datos[str(pos_id)] = fila
        return _escribir(datos)


def guardar_notas(pos_id, estrategia: str = "", emocion: str = "", razon: str = "") -> bool:
    """Notas del usuario para una operación (Tanda B)."""
    return _merge(pos_id, {"estrategia": (estrategia or "").strip(),
                           "emocion": (emocion or "").strip(),
                           "razon": (razon or "").strip()})


def guardar_plan(pos_id, entrada: float, sl: float, tp: float,
                 tipo: str = "", symbol: str = "", volumen: float = 0.0) -> bool:
    """Plan de la orden al ABRIR (Tanda C): se usa para el R/R planificado. Lo
    llama el bridge tras ejecutar una orden a mercado con SL/TP. No pisa las notas."""
    return _merge(pos_id, {"plan": {
        "entrada": float(entrada or 0.0), "sl": float(sl or 0.0), "tp": float(tp or 0.0),
        "tipo": tipo, "symbol": symbol, "volumen": float(volumen or 0.0),
    }})


def mtime() -> float:
    """Devuelve la fecha de modificación (epoch) de `journal.json`, o -1.0 si no existe."""
    try:
        return os.path.getmtime(_RUTA)
    except OSError:
        return -1.0


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara almacen_diario .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
