# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara sesion_persistente .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""
sesion_persistente.py
---------------------
Sesiones que sobreviven al cierre del navegador y al reinicio del servidor («mantener sesión iniciada»).

Cómo funciona:
  - Al iniciar sesión se crea un token aleatorio. El navegador lo guarda en una cookie (la escribe acceso/cookie.py) y aquí se guarda en
    Supabase solo su hash SHA-256, con el usuario y la fecha de vencimiento (tabla `sesiones_persistentes`, herramientas/sql/).
  - Al abrir la web sin sesión, la cookie llega al servidor; `validar` busca su hash en la tabla y, si no venció, devuelve el usuario.
  - Cerrar sesión borra la fila (`revocar`), de modo que la cookie queda inservible aunque alguien la conserve.
El almacén en memoria (almacen_sesiones.py) sigue siendo el que usa cada pestaña con su token `?s=`; este módulo es el respaldo de larga duración.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from herramientas import gestor_autenticacion

# Nombre de la cookie del navegador y días que dura una sesión persistente desde que se crea.
NOMBRE_COOKIE = "pj_sesion"
DIAS_DURACION = 30
# Máximo de dispositivos con sesión abierta por usuario; al iniciar sesión en uno más se cierra la sesión que hace más tiempo no se usa.
MAX_DISPOSITIVOS = 5


# TITULO HASH

def _hash(token: str) -> str:
    """Devuelve el hash SHA-256 (hexadecimal) de un token; es lo único que se guarda en la base de datos."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# TITULO CREAR

def crear(usuario_id, dispositivo: str = "", reemplaza_token: str = "") -> Optional[str]:
    """Crea una sesión persistente para el usuario y devuelve el token que debe guardar la cookie.

    Recibe el `usuario_id`, un resumen del navegador (`dispositivo`) y, si el navegador ya traía una cookie, ese token en `reemplaza_token`: su fila se borra
    para que iniciar sesión varias veces en el mismo navegador no acumule filas. Guarda en Supabase el hash del token y su vencimiento (DIAS_DURACION días),
    borra las sesiones ya vencidas y deja como máximo MAX_DISPOSITIVOS por usuario, cerrando las que hace más tiempo no se usan. Devuelve None si no hay
    conexión con Supabase o si falla el guardado (por ejemplo, si todavía no existe la tabla): el inicio de sesión sigue funcionando, solo que sin «mantener sesión».
    """
    cliente = gestor_autenticacion._supabase
    if cliente is None or usuario_id is None:
        return None
    token = secrets.token_urlsafe(32)
    ahora = datetime.now(timezone.utc)
    try:
        cliente.table("sesiones_persistentes").delete().lt("expira_en", ahora.isoformat()).execute()
        if reemplaza_token:
            cliente.table("sesiones_persistentes").delete().eq("token_hash", _hash(reemplaza_token)).execute()
        cliente.table("sesiones_persistentes").insert({
            "usuario_id": usuario_id,
            "token_hash": _hash(token),
            "expira_en": (ahora + timedelta(days=DIAS_DURACION)).isoformat(),
            "dispositivo": (dispositivo or "")[:160],
        }).execute()
        # Tope de dispositivos: se conservan los más recientes (por último uso) y se borran los demás.
        filas = cliente.table("sesiones_persistentes").select("id").eq("usuario_id", usuario_id).order("ultimo_uso", desc=True).execute()
        for fila in (filas.data or [])[MAX_DISPOSITIVOS:]:
            cliente.table("sesiones_persistentes").delete().eq("id", fila["id"]).execute()
    except Exception:
        return None
    return token


# TITULO VALIDAR

def validar(token: str) -> Optional[dict]:
    """Devuelve el usuario ({id, nombre, email}) dueño del token, o None si no existe, venció o falla la consulta.

    Busca la fila por el hash del token y comprueba el vencimiento; si es válida anota la fecha de último uso y lee los datos del usuario.
    """
    cliente = gestor_autenticacion._supabase
    if cliente is None or not token:
        return None
    try:
        fila = cliente.table("sesiones_persistentes").select("id, usuario_id, expira_en").eq("token_hash", _hash(token)).limit(1).execute()
        if not fila.data:
            return None
        sesion = fila.data[0]
        if datetime.fromisoformat(str(sesion["expira_en"]).replace("Z", "+00:00")) <= datetime.now(timezone.utc):
            return None
        cliente.table("sesiones_persistentes").update({"ultimo_uso": datetime.now(timezone.utc).isoformat()}).eq("id", sesion["id"]).execute()
        usuario = cliente.table("usuarios").select("id, nombre, email").eq("id", sesion["usuario_id"]).limit(1).execute()
        if not usuario.data:
            return None
        datos = usuario.data[0]
        return {"id": datos.get("id"), "nombre": datos.get("nombre"), "email": datos.get("email")}
    except Exception:
        return None


# TITULO REVOCAR

def revocar(token: str) -> None:
    """Borra la sesión persistente de ese token (cerrar sesión); no hace nada si no existe o falla la conexión."""
    cliente = gestor_autenticacion._supabase
    if cliente is None or not token:
        return
    try:
        cliente.table("sesiones_persistentes").delete().eq("token_hash", _hash(token)).execute()
    except Exception:
        pass


# TITULO REVOCAR TODAS

def revocar_todas(usuario_id) -> None:
    """Borra todas las sesiones persistentes de un usuario (por ejemplo, tras cambiar su contraseña)."""
    cliente = gestor_autenticacion._supabase
    if cliente is None or usuario_id is None:
        return
    try:
        cliente.table("sesiones_persistentes").delete().eq("usuario_id", usuario_id).execute()
    except Exception:
        pass


# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara sesion_persistente .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
