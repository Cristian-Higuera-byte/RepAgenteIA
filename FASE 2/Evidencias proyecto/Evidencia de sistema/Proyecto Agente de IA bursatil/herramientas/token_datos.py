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

- Formato: `<carga>.<firma>`; la carga es JSON en base64 con {u: usuario, d: demo, e: vencimiento} y la firma es
  HMAC-SHA256 con el secreto `SERVIDOR_SECRETO` del .env del servidor. Sin ese secreto no se emiten ni se aceptan tokens.
- Vence a las 12 horas; Streamlit emite uno nuevo en cada carga de la página.
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
import time
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Segundos de vida de un token
VIDA_TOKEN_S = 12 * 3600


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

def emitir(usuario_id: int, es_demo: bool, vida_s: int = VIDA_TOKEN_S) -> str:
    """Emite un token para el usuario y su cuenta; devuelve '' si no hay secreto configurado."""
    secreto = _secreto()
    if secreto is None:
        return ""
    carga = _b64(json.dumps({"u": int(usuario_id), "d": bool(es_demo), "e": int(time.time()) + int(vida_s)},
                            separators=(",", ":")).encode())
    return f"{carga}.{_firmar(carga, secreto)}"


# TITULO VERIFICAR

def verificar(token: str) -> Optional[tuple]:
    """Devuelve (usuario_id, es_demo) si el token es auténtico y no venció; si no, None.

    Compara la firma en tiempo constante. Cualquier formato inválido da None, nunca una excepción."""
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
        return (int(datos["u"]), bool(datos["d"]))
    except (ValueError, KeyError, TypeError):
        return None


# TITULO URL CON TOKEN

def url_con_token(url_base: str, usuario_id: int, es_demo: bool) -> str:
    """Devuelve la dirección base del servidor con el token del usuario: `<url>/t/<token>`.

    Si no hay secreto configurado devuelve `url_base` sin cambios (modo de un solo usuario)."""
    token = emitir(usuario_id, es_demo)
    return f"{url_base.rstrip('/')}/t/{token}" if token else url_base


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
