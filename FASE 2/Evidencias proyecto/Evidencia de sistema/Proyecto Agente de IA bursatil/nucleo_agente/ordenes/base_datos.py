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

from herramientas import paradas_emergencia
from herramientas.backends import sesiones_capital
from herramientas.recursos import sin_creditos
from nucleo_agente.ordenes.limites import LIMITES

# Carpeta de este módulo; de ella cuelga la subcarpeta sql/.
_AQUI = Path(__file__).resolve().parent

# Carpeta data/ de la raíz del proyecto (se crea si no existe) y archivo SQLite con todas las órdenes.
DIR_DATOS = _AQUI.parent.parent / "data"
DIR_DATOS.mkdir(exist_ok=True)
RUTA_DB = DIR_DATOS / "ordenes.db"

# Sentencias CREATE TABLE IF NOT EXISTS leídas de los archivos .sql al importar el módulo.
_SQL_ORDENES = sin_creditos((_AQUI / "sql" / "ordenes.sql").read_text(encoding="utf-8"))
_SQL_VIGILANCIAS = sin_creditos((_AQUI / "sql" / "vigilancias.sql").read_text(encoding="utf-8"))

# Columnas añadidas después de la primera versión: se agregan a las bases ya existentes (migración).
_COLUMNAS_NUEVAS_ORDENES = tuple(tuple(c) for c in json.loads((_AQUI / "sql" / "columnas_nuevas.json").read_text(encoding="utf-8")))


# Texto que se anota en las propuestas pendientes de antes de que existiera el dueño (solo en el modo multiusuario): no se puede saber de quién eran.
_MOTIVO_SIN_DUENO = "Propuesta anterior al control por usuario y cuenta: no se puede comprobar de quién era. Pídele al agente que la genere de nuevo."


class SinSesionError(RuntimeError):
    """No hay un usuario identificado: no se puede crear ni tocar ninguna propuesta de órdenes."""


_DB_PREPARADA: Path | None = None   # ruta de la base ya inicializada en este proceso
_DB_LOCK = threading.Lock()


# TITULO CONECTAR

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
            con.execute("CREATE INDEX IF NOT EXISTS ordenes_dueno ON ordenes (usuario_id, cuenta, estado)")
            if sesiones_capital.MULTIUSUARIO:    # las propuestas pendientes sin dueño comprobable no se muestran a nadie: se vencen para que no queden colgadas
                con.execute("UPDATE ordenes SET estado = 'EXPIRADA', detalle = ? WHERE usuario_id IS NULL AND estado = 'PENDIENTE'", (_MOTIVO_SIN_DUENO,))
            con.execute(_SQL_VIGILANCIAS)
            con.execute("CREATE TABLE IF NOT EXISTS estado (clave TEXT PRIMARY KEY, valor TEXT)")
            try:     # el interruptor antiguo era UNA clave para todos: si estaba activado, pasa a ser la parada global del operador (no se pierde un bloqueo)
                antiguo = con.execute("SELECT valor FROM estado WHERE clave = 'kill_switch'").fetchone()
                if antiguo and antiguo[0] == "1":
                    paradas_emergencia.fijar_global(True)
                    con.execute("UPDATE estado SET valor = '0' WHERE clave = 'kill_switch'")
            except Exception:  # noqa: BLE001 - la migración es de una sola vez: si falla se reintenta en el próximo arranque
                pass
            con.commit()
            _DB_PREPARADA = RUTA_DB
    return con


# TITULO EJECUTAR

def _ejecutar(sql: str, params: tuple = ()) -> int:
    """Ejecuta una sentencia de escritura con confirmación automática (commit) y devuelve las filas afectadas.

    El conteo permite "reclamar" registros de forma atómica (UPDATE ... WHERE estado = ...)."""
    with closing(_conectar()) as con:
        with con:
            return con.execute(sql, params).rowcount


# TITULO CONSULTAR

def _consultar(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Ejecuta una consulta SELECT y devuelve todas las filas como lista de diccionarios."""
    with closing(_conectar()) as con:
        return [dict(f) for f in con.execute(sql, params).fetchall()]


# TITULO AHORA

def _ahora() -> str:
    """Devuelve la hora local actual como texto ISO sin fracciones (comparable como cadena en SQL)."""
    return datetime.now().isoformat(timespec="seconds")


# TITULO DUENO ACTUAL

def dueno_actual() -> tuple[str, str] | None:
    """Dueño de las propuestas con las que se trabaja ahora: (usuario_id, cuenta), o None si no hay un usuario identificado.

    Sale de la misma clave que decide con qué cuenta de Capital.com se opera (sesiones_capital.clave_actual): el usuario autenticado y si está en demo o real, o
    ('legado', 'legado') con el modo multiusuario apagado. Nunca viene de un parámetro del navegador ni del modelo."""
    clave = sesiones_capital.clave_actual()
    if clave == ("legado",):
        return ("legado", "legado")
    if len(clave) == 2:
        return (str(int(clave[0])), "demo" if clave[1] else "real")
    return None


# TITULO CONDICION DUENO

def condicion_dueno() -> tuple[str, tuple]:
    """Texto SQL y valores que limitan una consulta a las propuestas del usuario y la cuenta actuales, para añadirlos con `+` al final de un WHERE.

    Devuelve (" AND COALESCE(usuario_id, 'legado') = ? AND COALESCE(cuenta, 'legado') = ?", (usuario, cuenta)); sin usuario identificado devuelve una condición que nunca
    se cumple. Las filas antiguas sin dueño se leen como 'legado': solo las ve el modo de un solo usuario, nunca un usuario del modo multiusuario."""
    dueno = dueno_actual()
    if dueno is None:
        return " AND 1 = 0", ()
    return " AND COALESCE(usuario_id, 'legado') = ? AND COALESCE(cuenta, 'legado') = ?", dueno


# TITULO INSERTAR

def _insertar(**campos: Any) -> str:
    """Inserta una fila en la tabla ordenes y devuelve su id.

    Genera un id corto aleatorio (8 caracteres), la fecha de creación y la de expiración (ahora más
    LIMITES.vigencia_propuesta_min); los campos recibidos por nombre completan o sustituyen esos valores.
    Los nombres de columna son fijos del código, nunca provienen del modelo. El dueño (usuario y cuenta) lo fija siempre el servidor con `dueno_actual`, aunque el
    llamador pase otro valor; sin usuario identificado lanza SinSesionError y no guarda nada."""
    dueno = dueno_actual()
    if dueno is None:
        raise SinSesionError("No hay una sesión de usuario: no se puede registrar la propuesta.")
    id_ = uuid.uuid4().hex[:8]
    ahora = datetime.now()
    base = {
        "id": id_,
        "creada": ahora.isoformat(timespec="seconds"),
        "expira": (ahora + timedelta(minutes=LIMITES.vigencia_propuesta_min)).isoformat(timespec="seconds"),
    }
    base.update(campos)
    base["usuario_id"], base["cuenta"] = dueno
    columnas = ", ".join(base)
    marcas = ", ".join("?" for _ in base)
    _ejecutar(f"INSERT INTO ordenes ({columnas}) VALUES ({marcas})", tuple(base.values()))
    return id_


# TITULO INTERRUPTOR EMERGENCIA ACTIVO

def interruptor_emergencia_activo() -> bool:
    """Indica si el usuario actual activó SU interruptor de emergencia en la cuenta actual (herramientas/paradas_emergencia.py). No mira la parada global del operador."""
    return paradas_emergencia.activa_usuario()


# TITULO APERTURAS BLOQUEADAS

def aperturas_bloqueadas() -> bool:
    """True si ahora NO se puede abrir por cualquier motivo de la política de apertura: parada global, parada del usuario, cuenta real deshabilitada o sin sesión."""
    from herramientas import politica_apertura
    return politica_apertura.motivo_de_bloqueo() is not None


# TITULO PARADA GLOBAL ACTIVA

def parada_global_activa() -> bool:
    """True si el operador de la plataforma bloqueó las aperturas de todos los usuarios."""
    return paradas_emergencia.activa_global()


# TITULO FIJAR PARADA GLOBAL

def fijar_parada_global(activa: bool) -> None:
    """Activa o desactiva la parada global. Solo la llama el panel de los administradores, que comprueba el rol antes."""
    paradas_emergencia.fijar_global(bool(activa))


# TITULO FIJAR INTERRUPTOR EMERGENCIA

def fijar_interruptor_emergencia(activo: bool) -> None:
    """Activa o desactiva el interruptor de emergencia DEL USUARIO ACTUAL en la cuenta actual; la parada de otro usuario no se toca."""
    paradas_emergencia.fijar_usuario(bool(activo))


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
