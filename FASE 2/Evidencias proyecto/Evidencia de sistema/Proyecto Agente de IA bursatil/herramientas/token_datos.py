# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara token_datos .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
token_datos.py
--------------
Token firmado que identifica al usuario y a su cuenta (demo o real) ante el servidor de datos.

El navegador del usuario habla directo con el servidor de datos (precios en vivo, velas y órdenes). Ese servidor es
otro proceso y no puede ver la sesión de Streamlit, así que Streamlit le entrega al navegador un token firmado y el
servidor lo verifica por su cuenta, sin base de datos ni memoria compartida.

- Formato: `<carga>.<firma>`; la carga es JSON en base64 con {u: usuario, d: demo, e: vencimiento, i: emisión, s: huella de la sesión de Streamlit}
  y la firma es HMAC-SHA256 con el secreto `SERVIDOR_SECRETO` del .env del servidor. Sin ese secreto no se emiten ni se aceptan tokens.
- Vence a las 12 horas; Streamlit emite uno nuevo en cada carga de la página.
- REVOCACIÓN: la firma no basta, porque un token firmado seguiría valiendo hasta vencer aunque la persona cerrara sesión. Cada cierre de sesión, cierre en todos los
  dispositivos o cambio de contraseña deja una fila en la tabla `revocaciones_acceso` (herramientas/sql/revocaciones_acceso.sql) y el servidor de datos la consulta
  (con una memoria de 5 segundos, para no ir a la base en cada petición) al recibir cada petición y mientras mantiene abierta una conexión de precios en vivo.
  Un token anterior al cierre del usuario, o emitido desde la sesión cerrada, deja de servir.
- El token viaja dentro de la dirección base (`<servidor>/t/<token>`) para que todos los scripts del navegador sigan
  construyendo sus URL con `API + '/ruta'` sin cambios.
- El token NO es una contraseña de Capital.com: solo prueba quién es el usuario ante este servidor. Hay que servirlo
  por HTTPS en producción.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Segundos de vida de un token
VIDA_TOKEN_S = 12 * 3600

# Segundos que el servidor recuerda el resultado de consultar las revocaciones de un usuario antes de volver a preguntar a la base
MEMORIA_REVOCACION_S = 5

# Tabla donde se anotan los cierres de sesión
_TABLA = "revocaciones_acceso"

# Resultados recientes de la consulta de revocaciones: {(usuario, sesión, emisión): (¿revocado?, instante de la consulta)}
_memoria: dict = {}


# TITULO GENERAR SECRETO

def generar_secreto() -> str:
    """Devuelve un secreto aleatorio nuevo para `SERVIDOR_SECRETO` en el .env del servidor."""
    return secrets.token_urlsafe(48)


# TITULO SECRETO

def _secreto() -> Optional[bytes]:
    """Devuelve el secreto de firma del .env, o None si falta o es demasiado corto (menos de 32 caracteres)."""
    valor = os.environ.get("SERVIDOR_SECRETO", "").strip()
    return valor.encode() if len(valor) >= 32 else None


# TITULO BASE64

def _b64(datos: bytes) -> str:
    """Codifica bytes en base64 seguro para URL, sin relleno."""
    return base64.urlsafe_b64encode(datos).decode().rstrip("=")


def _deb64(texto: str) -> bytes:
    """Decodifica base64 seguro para URL (con o sin relleno)."""
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


# TITULO FIRMAR

def _firmar(carga: str, secreto: bytes) -> str:
    """Firma HMAC-SHA256 de la carga, en base64 seguro para URL."""
    return _b64(hmac.new(secreto, carga.encode(), hashlib.sha256).digest())


# TITULO EMITIR

def emitir(usuario_id: int, es_demo: bool, vida_s: int = VIDA_TOKEN_S, sesion: str = "") -> str:
    """Emite un token para el usuario y su cuenta; devuelve '' si no hay secreto configurado.

    `sesion` es la huella de la sesión de Streamlit que lo pide (ver `huella_sesion`): así cerrar ESA sesión invalida este token."""
    secreto = _secreto()
    if secreto is None:
        return ""
    ahora = time.time()
    # La emisión lleva milésimas de segundo: un token emitido justo DESPUÉS de un cierre de sesión no debe quedar invalidado por él
    datos = {"u": int(usuario_id), "d": bool(es_demo), "e": int(ahora) + int(vida_s), "i": round(ahora, 3)}
    if sesion:
        datos["s"] = str(sesion)
    carga = _b64(json.dumps(datos, separators=(",", ":")).encode())
    return f"{carga}.{_firmar(carga, secreto)}"


# TITULO LEER

def leer(token: str) -> Optional[dict]:
    """Devuelve {u, d, i, s, e} (usuario, demo, instante de emisión, huella de sesión y vencimiento) si el token es auténtico y no venció; si no, None.

    Compara la firma en tiempo constante. Cualquier formato inválido da None, nunca una excepción. Un token emitido antes de que existiera la revocación no trae
    `i` ni `s`: se lee con emisión 0 y sin sesión."""
    secreto = _secreto()
    if secreto is None or not token or token.count(".") != 1:
        return None
    carga, firma = token.split(".")
    if not hmac.compare_digest(firma.encode("utf-8"), _firmar(carga, secreto).encode("utf-8")):
        return None
    try:
        datos = json.loads(_deb64(carga))
        if int(datos["e"]) < time.time():
            return None
        return {"u": int(datos["u"]), "d": bool(datos["d"]), "i": float(datos.get("i", 0)), "s": str(datos.get("s", "")), "e": float(datos["e"])}
    except (ValueError, KeyError, TypeError):
        return None


# TITULO VERIFICAR

def verificar(token: str) -> Optional[tuple]:
    """Devuelve (usuario_id, es_demo) si el token es auténtico y no venció; si no, None. No consulta las revocaciones (para eso, `esta_revocado`)."""
    datos = leer(token)
    return None if datos is None else (datos["u"], datos["d"])


# TITULO URL CON TOKEN

def url_con_token(url_base: str, usuario_id: int, es_demo: bool, sesion: str = "") -> str:
    """Devuelve la dirección base del servidor con el token del usuario: `<url>/t/<token>`.

    `sesion` es la huella de la sesión de Streamlit (ver `huella_sesion`). Si no hay secreto configurado devuelve `url_base` sin cambios (modo de un solo usuario)."""
    token = emitir(usuario_id, es_demo, sesion=sesion)
    return f"{url_base.rstrip('/')}/t/{token}" if token else url_base


# TITULO HUELLA DE LA SESION

def huella_sesion(token_sesion: str) -> str:
    """Resumen corto (16 caracteres hexadecimales) de un token de sesión (la cookie de «mantener sesión»), o '' si no hay. Es el identificador de la sesión (acceso/sesion.py):
    va dentro del token de datos y en `revocaciones_acceso` en lugar del token de la sesión, que no debe viajar ni guardarse."""
    return hashlib.sha256(token_sesion.encode("utf-8")).hexdigest()[:16] if token_sesion else ""


# TITULO CLIENTE DE BASE DE DATOS

def _cliente():
    """Cliente de la base de datos de la plataforma (el mismo de la autenticación), o None si no hay credenciales. Se importa al usarlo para evitar ciclos de importación."""
    from herramientas import gestor_autenticacion
    return gestor_autenticacion._supabase


# TITULO REVOCAR

def _revocar(usuario_id, sesion) -> bool:
    """Anota una revocación (de una sesión, o de todas si `sesion` es None) y borra las que ya no tienen efecto. Devuelve False si no se pudo escribir en la base."""
    cliente = _cliente()
    if cliente is None or usuario_id is None:
        return False
    ahora = time.time()
    try:
        cliente.table(_TABLA).insert({"usuario_id": int(usuario_id), "sesion": sesion, "desde": ahora}).execute()
    except Exception as error:  # noqa: BLE001
        print(f"[Revocación] No se pudo anotar el cierre de sesión: {error}", file=sys.stderr, flush=True)
        return False
    _memoria.clear()
    try:
        cliente.table(_TABLA).delete().lt("desde", ahora - VIDA_TOKEN_S - 3600).execute()
    except Exception:  # noqa: BLE001 - la limpieza es opcional
        pass
    return True


# TITULO REVOCAR SESION

def revocar_sesion(usuario_id, huella: str) -> bool:
    """Invalida los tokens de datos emitidos desde esa sesión (cerrar sesión en este dispositivo); `huella` es el identificador de la sesión (`huella_sesion`)."""
    return _revocar(usuario_id, huella) if huella else False


# TITULO REVOCAR USUARIO

def revocar_usuario(usuario_id) -> bool:
    """Invalida todos los tokens de datos del usuario emitidos hasta ahora (cerrar sesión en todos los dispositivos o cambiar la contraseña)."""
    return _revocar(usuario_id, None)


# TITULO ESTA REVOCADO

def esta_revocado(datos: dict) -> Optional[bool]:
    """True si el token (ya leído con `leer`) fue invalidado por un cierre de sesión; False si sigue vigente; None si no se pudo comprobar (la base no responde).

    Vale por revocación de todo el usuario posterior a la emisión del token, o de la sesión desde la que se emitió. El resultado se recuerda MEMORIA_REVOCACION_S
    segundos; si la base falla se usa el último resultado conocido de ese usuario y sesión, y solo sin ninguno se devuelve None."""
    clave = (datos["u"], datos.get("s", ""), datos.get("i", 0))
    ahora = time.time()
    previo = _memoria.get(clave)
    if previo is not None and ahora - previo[1] < MEMORIA_REVOCACION_S:
        return previo[0]
    cliente = _cliente()
    if cliente is None:
        return None if previo is None else previo[0]
    try:
        filas = cliente.table(_TABLA).select("sesion,desde").eq("usuario_id", datos["u"]).execute().data or []
    except Exception as error:  # noqa: BLE001
        print(f"[Revocación] No se pudo consultar las revocaciones: {error}", file=sys.stderr, flush=True)
        return None if previo is None else previo[0]
    revocado = any((fila.get("sesion") in (None, "") and float(fila.get("desde") or 0) >= datos.get("i", 0))
                   or (datos.get("s") and fila.get("sesion") == datos.get("s")) for fila in filas)
    _memoria[clave] = (revocado, ahora)
    if len(_memoria) > 5000:
        _memoria.clear()
    return revocado


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara token_datos .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
