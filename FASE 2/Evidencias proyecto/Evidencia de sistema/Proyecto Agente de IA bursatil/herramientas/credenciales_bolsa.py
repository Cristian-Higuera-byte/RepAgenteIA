# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara credenciales_bolsa .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
credenciales_bolsa.py
---------------------
Guarda y lee, cifradas, las credenciales de la API de Capital.com de cada usuario. Cada usuario puede
tener DOS cuentas conectadas, la real y la demo (una fila por usuario y por modo), y elige cuál usar
como en Capital.com (tabla `credenciales_bolsa` en Supabase; el SQL está en `herramientas/sql/esquema_plataforma.sql`).

Diseño de seguridad:
- Cada dato (correo, key y contraseña de la key) se cifra con Fernet (AES-128-CBC + HMAC) antes de salir
  del servidor; Supabase solo ve texto cifrado.
- La clave maestra vive SOLO en el entorno del servidor: `CREDENCIALES_CLAVES` en el `.env`, una o varias
  claves Fernet separadas por coma. La PRIMERA cifra; todas descifran. Para rotarla se antepone una clave
  nueva y se corre `recifrar_todas()`; luego se puede retirar la vieja.
- Nada de esto se escribe en logs ni se devuelve al navegador: `estado_credenciales()` devuelve solo
  si hay cuenta conectada y si es demo o real, nunca los secretos.
- El servidor debe usar la clave `service_role` de Supabase y la tabla tiene RLS activo sin políticas,
  así una clave pública (anon) no puede leerla.
"""
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from dotenv import load_dotenv

from herramientas import gestor_autenticacion

load_dotenv()

# Nombre de la tabla en Supabase
_TABLA = "credenciales_bolsa"
# Versión del formato guardado (por si en el futuro cambian los campos)
_VERSION_FORMATO = 1


# TITULO GENERAR CLAVE

def generar_clave() -> str:
    """Devuelve una clave Fernet nueva (texto) para pegar en `CREDENCIALES_CLAVES` del `.env` del servidor."""
    return Fernet.generate_key().decode()


# TITULO FABRICA DE CIFRADO

def _cifrador() -> MultiFernet:
    """Construye el cifrador desde `CREDENCIALES_CLAVES`; la primera clave cifra y todas descifran.

    Lanza RuntimeError si la variable falta o alguna clave no es válida, para no guardar nunca en claro.
    """
    claves = [c.strip() for c in os.environ.get("CREDENCIALES_CLAVES", "").split(",") if c.strip()]
    if not claves:
        raise RuntimeError("Falta CREDENCIALES_CLAVES en el .env del servidor (genera una con generar_clave()).")
    try:
        return MultiFernet([Fernet(c.encode()) for c in claves])
    except Exception as error:
        raise RuntimeError("CREDENCIALES_CLAVES contiene una clave Fernet inválida.") from error


# TITULO CIFRAR TEXTO

def _cifrar(texto: str) -> str:
    """Cifra un texto con la clave maestra vigente y lo devuelve como texto base64."""
    return _cifrador().encrypt(texto.encode("utf-8")).decode()


# TITULO DESCIFRAR TEXTO

def _descifrar(token: str) -> str:
    """Descifra un texto guardado; lanza InvalidToken si ninguna clave configurada lo abre."""
    return _cifrador().decrypt(token.encode()).decode("utf-8")


# TITULO CLIENTE SUPABASE

def _cliente():
    """Devuelve el cliente Supabase compartido con la autenticación, o lanza RuntimeError si no está configurado."""
    cliente = gestor_autenticacion._supabase
    if cliente is None:
        raise RuntimeError("Supabase no está configurado (revisa SUPABASE_URL / SUPABASE_KEY en .env).")
    return cliente


# TITULO GUARDAR CREDENCIALES

def guardar_credenciales(usuario_id: int, es_demo: bool, identificador: str, api_key: str,
                         api_contrasena: str) -> dict:
    """Guarda (o reemplaza) las credenciales de Capital de un usuario para un modo (demo o real), cifradas.

    Recibe el id del usuario, el modo de la cuenta (True = demo, False = real), el correo de la cuenta, la API key
    y la contraseña de la key.
    Devuelve {"ok": bool, "mensaje": str}. No valida la conexión con Capital: eso lo hace quien la llame.
    """
    identificador, api_key, api_contrasena = identificador.strip(), api_key.strip(), api_contrasena.strip()
    if not (identificador and api_key and api_contrasena):
        return {"ok": False, "mensaje": "Completa el correo, la API key y la contraseña de la key."}
    try:
        registro = {
            "usuario_id": usuario_id,
            "identificador_cifrado": _cifrar(identificador),
            "api_key_cifrada": _cifrar(api_key),
            "api_contrasena_cifrada": _cifrar(api_contrasena),
            "es_demo": bool(es_demo),
            "version": _VERSION_FORMATO,
        }
        _cliente().table(_TABLA).upsert(registro, on_conflict="usuario_id,es_demo").execute()
        return {"ok": True, "mensaje": "Credenciales guardadas."}
    except Exception as error:
        return {"ok": False, "mensaje": f"No se pudieron guardar las credenciales ({type(error).__name__})."}


# TITULO OBTENER CREDENCIALES

def obtener_credenciales(usuario_id: int, es_demo: bool) -> Optional[dict]:
    """Devuelve las credenciales descifradas {identificador, api_key, api_contrasena, es_demo} del modo pedido o None si no hay.

    Es de uso interno del servidor (sesión de Capital): el resultado nunca debe llegar al navegador ni a logs.
    Si el descifrado falla (clave maestra equivocada) lanza InvalidToken en vez de devolver datos erróneos.
    """
    respuesta = _cliente().table(_TABLA).select("*").eq("usuario_id", usuario_id).eq("es_demo", bool(es_demo)).limit(1).execute()
    if not respuesta.data:
        return None
    fila = respuesta.data[0]
    return {
        "identificador": _descifrar(fila["identificador_cifrado"]),
        "api_key": _descifrar(fila["api_key_cifrada"]),
        "api_contrasena": _descifrar(fila["api_contrasena_cifrada"]),
        "es_demo": bool(fila["es_demo"]),
    }


# TITULO ESTADO CREDENCIALES

def estado_credenciales(usuario_id: int) -> dict:
    """Dice qué cuentas tiene conectadas el usuario, sin exponer ningún secreto.

    Devuelve {"demo": bool, "real": bool}: True si ese modo tiene credenciales guardadas. Es lo único que la
    interfaz puede mostrar para decidir qué modos ofrecer en el selector.
    """
    estado = {"demo": False, "real": False}
    try:
        respuesta = _cliente().table(_TABLA).select("es_demo").eq("usuario_id", usuario_id).execute()
    except Exception:
        return estado
    for fila in respuesta.data or []:
        estado["demo" if fila["es_demo"] else "real"] = True
    return estado


# TITULO ELIMINAR CREDENCIALES

def eliminar_credenciales(usuario_id: int, es_demo: bool) -> dict:
    """Borra las credenciales de un modo (desconectar esa cuenta). Devuelve {"ok": bool, "mensaje": str}."""
    try:
        (_cliente().table(_TABLA).delete().eq("usuario_id", usuario_id).eq("es_demo", bool(es_demo)).execute())
        return {"ok": True, "mensaje": "Cuenta desconectada."}
    except Exception as error:
        return {"ok": False, "mensaje": f"No se pudo desconectar la cuenta ({type(error).__name__})."}


# TITULO RECIFRAR TODAS

def recifrar_todas() -> int:
    """Vuelve a cifrar todas las filas con la clave maestra vigente (la primera de `CREDENCIALES_CLAVES`).

    Se usa tras rotar la clave maestra. Devuelve cuántas filas se reescribieron; las que no se pueden
    descifrar con ninguna clave configurada se omiten sin tocarlas.
    """
    cliente, cifrador, total = _cliente(), _cifrador(), 0
    for fila in cliente.table(_TABLA).select("*").execute().data or []:
        try:
            nueva = {campo: cifrador.rotate(fila[campo].encode()).decode()
                     for campo in ("identificador_cifrado", "api_key_cifrada", "api_contrasena_cifrada")}
        except InvalidToken:
            continue
        cliente.table(_TABLA).update(nueva).eq("usuario_id", fila["usuario_id"]).eq("es_demo", fila["es_demo"]).execute()
        total += 1
    return total


# -------------------------------------------------------------------------------------------------------
# ----------------------------- FIN Piña y Jara credenciales_bolsa .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
