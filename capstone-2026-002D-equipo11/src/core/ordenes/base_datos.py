# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara base_datos .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Base de datos (SQLite) de las órdenes: propuestas, auditoría, vigilancias e interruptor de emergencia.

El esquema vive en sql/ (ordenes.sql, vigilancias.sql) y las columnas añadidas después en columnas_nuevas.json.
Este módulo abre las conexiones, crea las tablas la primera vez, migra bases antiguas y ofrece ayudantes
mínimos (_ejecutar, _consultar, _insertar) que usan el resto de módulos del paquete y el de vigilancia."""
import json
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from tools.recursos import sin_creditos
from core.ordenes.limites import LIMITES

# Carpeta de este módulo; de ella cuelga la subcarpeta sql/.
_AQUI = Path(__file__).resolve().parent

# Carpeta data/ de la raíz del proyecto (se crea si no existe) y archivo SQLite con todas las órdenes.
import configuracion  # rutas centrales del proyecto (database/data y database/sql)

DIR_DATOS = configuracion.DIR_DATOS
DIR_DATOS.mkdir(parents=True, exist_ok=True)
RUTA_DB = DIR_DATOS / "ordenes.db"

# Sentencias CREATE TABLE IF NOT EXISTS leídas de los archivos .sql al importar el módulo.
_SQL_ORDENES = sin_creditos((configuracion.DIR_SQL / "ordenes.sql").read_text(encoding="utf-8"))
_SQL_VIGILANCIAS = sin_creditos((configuracion.DIR_SQL / "vigilancias.sql").read_text(encoding="utf-8"))

# Columnas añadidas después de la primera versión: se agregan a las bases ya existentes (migración).
_COLUMNAS_NUEVAS_ORDENES = tuple(tuple(c) for c in json.loads((configuracion.DIR_SQL / "columnas_nuevas.json").read_text(encoding="utf-8")))


_DB_PREPARADA: Path | None = None   # ruta de la base ya inicializada en este proceso
_DB_LOCK = threading.Lock()


def _conectar() -> sqlite3.Connection:
    """Abre una conexión SQLite nueva (filas accesibles por nombre) a RUTA_DB.

    La primera vez en el proceso, y bajo _DB_LOCK, activa el modo WAL, crea las tablas, añade a la tabla
    ordenes las columnas de _COLUMNAS_NUEVAS_ORDENES que falten (migración) y crea la tabla estado.
    Devuelve la conexión; quien la llama debe cerrarla."""
    global _DB_PREPARADA
    # Timeout de 10 s para esperar si otra conexión tiene la base bloqueada.
    con = sqlite3.connect(RUTA_DB, timeout=10)
    con.row_factory = sqlite3.Row
    if _DB_PREPARADA != RUTA_DB:  # las tablas se crean una sola vez, no en cada consulta
        with _DB_LOCK:
            try:
                con.execute("PRAGMA journal_mode=WAL")  # lecturas y escrituras no se bloquean entre sí
            except sqlite3.OperationalError:
                pass  # otra conexión la usa ahora mismo: se queda en el modo actual
            con.execute(_SQL_ORDENES)
            existentes = {fila[1] for fila in con.execute("PRAGMA table_info(ordenes)")}
            for nombre, definicion in _COLUMNAS_NUEVAS_ORDENES:   # bases creadas antes de estas columnas
                if nombre not in existentes:
                    con.execute(f"ALTER TABLE ordenes ADD COLUMN {nombre} {definicion}")
            con.execute(_SQL_VIGILANCIAS)
            con.execute("CREATE TABLE IF NOT EXISTS estado (clave TEXT PRIMARY KEY, valor TEXT)")
            con.commit()
            _DB_PREPARADA = RUTA_DB
    return con


def _ejecutar(sql: str, params: tuple = ()) -> int:
    """Ejecuta una sentencia de escritura con confirmación automática (commit) y devuelve las filas afectadas.

    El conteo permite "reclamar" registros de forma atómica (UPDATE ... WHERE estado = ...)."""
    with closing(_conectar()) as con:
        with con:
            return con.execute(sql, params).rowcount


def _consultar(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Ejecuta una consulta SELECT y devuelve todas las filas como lista de diccionarios."""
    with closing(_conectar()) as con:
        return [dict(f) for f in con.execute(sql, params).fetchall()]


def _ahora() -> str:
    """Devuelve la hora local actual como texto ISO sin fracciones (comparable como cadena en SQL)."""
    return datetime.now().isoformat(timespec="seconds")


def _insertar(**campos: Any) -> str:
    """Inserta una fila en la tabla ordenes y devuelve su id.

    Genera un id corto aleatorio (8 caracteres), la fecha de creación y la de expiración (ahora más
    LIMITES.vigencia_propuesta_min); los campos recibidos por nombre completan o sustituyen esos valores.
    Los nombres de columna son fijos del código, nunca provienen del modelo."""
    id_ = uuid.uuid4().hex[:8]
    ahora = datetime.now()
    base = {
        "id": id_,
        "creada": ahora.isoformat(timespec="seconds"),
        "expira": (ahora + timedelta(minutes=LIMITES.vigencia_propuesta_min)).isoformat(timespec="seconds"),
    }
    base.update(campos)
    columnas = ", ".join(base)
    marcas = ", ".join("?" for _ in base)
    _ejecutar(f"INSERT INTO ordenes ({columnas}) VALUES ({marcas})", tuple(base.values()))
    return id_


def kill_switch_activo() -> bool:
    """Indica si el interruptor de emergencia está activado (bloquea nuevas aperturas). Lee la tabla estado."""
    filas = _consultar("SELECT valor FROM estado WHERE clave = 'kill_switch'")
    return bool(filas) and filas[0]["valor"] == "1"


def fijar_kill_switch(activo: bool) -> None:
    """Activa o desactiva el interruptor de emergencia guardando "1" o "0" en la tabla estado (upsert)."""
    _ejecutar(
        "INSERT INTO estado (clave, valor) VALUES ('kill_switch', ?) "
        "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
        ("1" if activo else "0",),
    )


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara base_datos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
