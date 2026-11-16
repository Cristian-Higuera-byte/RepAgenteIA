# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------- INICIO Piña y Jara paradas_emergencia .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
paradas_emergencia.py
---------------------
Interruptores de emergencia que bloquean la apertura de operaciones.

Hay dos, y son independientes:
  * PARADA DE LA PERSONA, por usuario y por cuenta (demo o real): la activa cada persona desde el panel del agente y solo frena sus propias aperturas en esa cuenta. Antes era
    una sola clave para toda la plataforma: si A la activaba bloqueaba a B, y B podía quitársela a A.
  * PARADA GLOBAL, del operador de la plataforma: frena las aperturas de TODOS los usuarios. Solo la activan los administradores.

Quién es el usuario y su cuenta lo decide el servidor con la misma clave que elige la cuenta de Capital.com (herramientas/backends/sesiones_capital.py), nunca un valor que
mande el navegador o el modelo de IA. Los cierres de posiciones y las cancelaciones no dependen de estos interruptores: reducir exposición siempre se puede.

El estado vive en un archivo SQLite propio (data/paradas_emergencia.db), así lo ven todos los procesos (Streamlit, servidor de datos, motor de vigilancias).
"""
import sqlite3
import threading
from contextlib import closing
from datetime import datetime
from pathlib import Path

from herramientas.backends import sesiones_capital

# Archivo con el estado de los interruptores (carpeta data/ de la raíz del proyecto).
DIR_DATOS = Path(__file__).resolve().parent.parent / "data"
RUTA_DB = DIR_DATOS / "paradas_emergencia.db"

# Clave de la parada del operador.
_CLAVE_GLOBAL = "global"

_PREPARADA: Path | None = None
_CANDADO = threading.Lock()


# TITULO CONECTAR

def _conectar() -> sqlite3.Connection:
    """Abre una conexión nueva al archivo de paradas (lo crea con su tabla la primera vez en este proceso). Quien la llama debe cerrarla."""
    global _PREPARADA
    DIR_DATOS.mkdir(exist_ok=True)
    con = sqlite3.connect(RUTA_DB, timeout=10)
    if _PREPARADA != RUTA_DB:
        with _CANDADO:
            con.execute("CREATE TABLE IF NOT EXISTS paradas (clave TEXT PRIMARY KEY, activa INTEGER NOT NULL, cambiada TEXT NOT NULL)")
            con.commit()
            _PREPARADA = RUTA_DB
    return con


# TITULO DUENO ACTUAL

def dueno_actual() -> tuple[str, str] | None:
    """(usuario_id, cuenta) del usuario con el que se trabaja ahora, o None si no hay un usuario identificado.

    Sale de sesiones_capital.clave_actual(): el usuario autenticado y si está en demo o real, o ('legado', 'legado') con el modo multiusuario apagado."""
    clave = sesiones_capital.clave_actual()
    if clave == ("legado",):
        return ("legado", "legado")
    if len(clave) == 2:
        return (str(int(clave[0])), "demo" if clave[1] else "real")
    return None


# TITULO LEER

def _leer(clave: str) -> bool:
    """True si el interruptor con esa clave está activado."""
    with closing(_conectar()) as con:
        fila = con.execute("SELECT activa FROM paradas WHERE clave = ?", (clave,)).fetchone()
    return bool(fila and fila[0])


# TITULO ESCRIBIR

def _escribir(clave: str, activa: bool) -> None:
    """Guarda el estado del interruptor con esa clave (lo crea si no existe)."""
    with closing(_conectar()) as con:
        with con:
            con.execute("INSERT INTO paradas (clave, activa, cambiada) VALUES (?, ?, ?) ON CONFLICT(clave) DO UPDATE SET activa = excluded.activa, cambiada = excluded.cambiada",
                        (clave, 1 if activa else 0, datetime.now().isoformat(timespec="seconds")))


# TITULO PARADA GLOBAL

def activa_global() -> bool:
    """True si el operador de la plataforma bloqueó las aperturas de todos los usuarios."""
    return _leer(_CLAVE_GLOBAL)


def fijar_global(activa: bool) -> None:
    """Activa o desactiva la parada global del operador. Quien la llama debe haber comprobado que la persona es administradora."""
    _escribir(_CLAVE_GLOBAL, activa)


# TITULO PARADA DE LA PERSONA

def _clave_usuario(dueno: tuple[str, str]) -> str:
    """Clave del interruptor de un usuario y una cuenta."""
    return f"usuario:{dueno[0]}:{dueno[1]}"


def activa_usuario() -> bool:
    """True si el usuario actual activó su parada en la cuenta actual; sin usuario identificado devuelve False (la política de aperturas rechaza ese caso por otro motivo)."""
    dueno = dueno_actual()
    return False if dueno is None else _leer(_clave_usuario(dueno))


def fijar_usuario(activa: bool) -> None:
    """Activa o desactiva la parada del usuario actual en la cuenta actual; sin usuario identificado lanza PermissionError y no guarda nada."""
    dueno = dueno_actual()
    if dueno is None:
        raise PermissionError("No hay una sesión de usuario: no se puede cambiar la parada de emergencia.")
    _escribir(_clave_usuario(dueno), activa)


# -------------------------------------------------------------------------------------------------------
# ----------------------------- FIN Piña y Jara paradas_emergencia .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
