# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara recaptcha .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Verificación en el servidor de los tokens de reCAPTCHA de Google (v3 y v2).

Cada formulario protegido hace dos cosas: el navegador obtiene un token de v3 (invisible, puntúa a la persona de 0 a 1) y, solo si ese puntaje es bajo, muestra el casillero
«No soy un robot» de v2. Aquí se comprueban esos tokens contra `https://www.google.com/recaptcha/api/siteverify` con las claves secretas, que nunca salen del servidor.

Las claves salen de `configuracion.py` (variables RECAPTCHA_* del .env). Si faltan, la protección queda apagada y todo se acepta (desarrollo); con las cuatro claves puestas se exige.
No usa Streamlit, de modo que se puede probar sin la interfaz.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional

import configuracion

# Dirección de verificación de Google y segundos máximos que se espera su respuesta antes de rechazar el envío.
URL_VERIFICACION = "https://www.google.com/recaptcha/api/siteverify"
ESPERA_SEGUNDOS = 6.0

# Registro de cada verificación en la consola del servidor (nunca lleva claves, tokens ni datos de la persona).
PREFIJO_REGISTRO = "[RECAPTCHA]"

# Textos que ve la persona (sin detalles técnicos).
MENSAJE_CONFIRMAR = "Confirma que no eres un robot para continuar."
MENSAJE_MARCAR = "Marca «No soy un robot» para continuar."
MENSAJE_REINTENTAR = "No pudimos verificar que eres una persona. Inténtalo de nuevo."
MENSAJE_SIN_SERVICIO = "No pudimos contactar al servicio de verificación. Inténtalo de nuevo en un minuto."


# TITULO VEREDICTO

@dataclass
class Veredicto:
    """Resultado de verificar un envío: `ok` si pasa, `pedir_v2` si hay que mostrar el casillero de v2, `mensaje` para la persona y `puntaje` de v3 (None si no hubo)."""
    ok: bool
    pedir_v2: bool = False
    mensaje: str = ""
    puntaje: Optional[float] = None


# TITULO ACTIVO

def activo() -> bool:
    """True si están puestas las cuatro claves de reCAPTCHA (sitio y secreta de v3 y de v2); sin ellas la protección está apagada."""
    return configuracion.RECAPTCHA_ACTIVO


# TITULO CONSULTAR

def _consultar(secreta: str, token: str, ip: Optional[str] = None) -> Optional[dict]:
    """Envía el token a Google y devuelve su respuesta como diccionario, o None si no se pudo contactar el servicio o la respuesta no es válida.

    La clave secreta viaja solo en esta petición; nunca se escribe en mensajes ni registros."""
    datos = {"secret": secreta, "response": token}
    if ip:
        datos["remoteip"] = ip
    peticion = urllib.request.Request(URL_VERIFICACION, data=urllib.parse.urlencode(datos).encode("utf-8"), method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=ESPERA_SEGUNDOS) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None
    return cuerpo if isinstance(cuerpo, dict) else None


# TITULO REGISTRAR

def _registrar(accion: str, version: str, veredicto: "Veredicto", respuesta: Optional[dict]) -> "Veredicto":
    """Escribe en la consola del servidor una línea con lo que respondió Google y devuelve el mismo `veredicto`.

    Dice el formulario (`accion`), la versión comprobada, si pasó, el puntaje de v3, la acción y el sitio (hostname) que Google vio y sus códigos de error. Sirve para saber
    por qué un envío pasó o se rechazó (puntaje bajo, dominio no permitido, token vencido...). No incluye las claves ni los tokens."""
    datos = respuesta or {}
    codigos = ",".join(str(x) for x in (datos.get("error-codes") or [])) or "-"
    print(f"{PREFIJO_REGISTRO} formulario={accion} version={version} paso={'si' if veredicto.ok else 'no'} puntaje={datos.get('score', '-')} "
          f"accion_google={datos.get('action', '-')} sitio={datos.get('hostname', '-')} pide_v2={'si' if veredicto.pedir_v2 else 'no'} errores={codigos}"
          + ("" if respuesta is not None else " sin_respuesta_de_google"), flush=True)
    return veredicto


# TITULO VERIFICAR

def verificar(accion: str, token_v3: str = "", token_v2: str = "", ip: Optional[str] = None) -> Veredicto:
    """Decide si un envío del formulario `accion` (por ejemplo «login») pasa la protección, según `configuracion.RECAPTCHA_MODO` («ambos» o «respaldo»).

    Con la protección apagada acepta todo. En modo «ambos» (por defecto) usa `_verificar_ambos`: el casillero de v2 siempre está a la vista y se exigen v2 y v3. En modo
    «respaldo» usa `_verificar_respaldo`: v3 decide en silencio y el casillero solo se pide si el puntaje es bajo."""
    if not activo():
        return Veredicto(True)
    if configuracion.RECAPTCHA_MODO == "respaldo":
        return _verificar_respaldo(accion, token_v3, token_v2, ip)
    return _verificar_ambos(accion, token_v3, token_v2, ip)


# TITULO VERIFICAR AMBOS

def _puntaje_v3(respuesta: dict) -> Optional[float]:
    """Puntaje de v3 que trae la respuesta de Google, o None si no hay o no es un número."""
    try:
        return float(respuesta.get("score")) if respuesta.get("score") is not None else None
    except (TypeError, ValueError):
        return None


def _verificar_ambos(accion: str, token_v3: str, token_v2: str, ip: Optional[str]) -> Veredicto:
    """Modo «ambos»: el casillero de v2 está siempre a la vista y se exigen las dos comprobaciones.

    1) Debe venir el token de v2 y Google debe aprobarlo; 2) debe venir el token de v3, ser de la misma acción y tener un puntaje de `RECAPTCHA_UMBRAL` o más. Si falta o falla
    cualquiera, el envío se rechaza (el casillero sigue a la vista para reintentar). Si Google no responde, se rechaza sin más."""
    if not token_v2:
        print(f"{PREFIJO_REGISTRO} formulario={accion} version=v2 paso=no sin_token_v2 (casillero sin marcar)", flush=True)
        return Veredicto(False, pedir_v2=True, mensaje=MENSAJE_MARCAR)
    r2 = _consultar(configuracion.RECAPTCHA_V2_SECRETA, token_v2, ip)
    if r2 is None:
        return _registrar(accion, "v2", Veredicto(False, mensaje=MENSAJE_SIN_SERVICIO), None)
    if r2.get("success") is not True:
        return _registrar(accion, "v2", Veredicto(False, pedir_v2=True, mensaje=MENSAJE_REINTENTAR), r2)
    _registrar(accion, "v2", Veredicto(True), r2)
    if not token_v3:
        print(f"{PREFIJO_REGISTRO} formulario={accion} version=v3 paso=no sin_token_v3 (el navegador no entregó token)", flush=True)
        return Veredicto(False, pedir_v2=True, mensaje=MENSAJE_REINTENTAR)
    r3 = _consultar(configuracion.RECAPTCHA_V3_SECRETA, token_v3, ip)
    if r3 is None:
        return _registrar(accion, "v3", Veredicto(False, mensaje=MENSAJE_SIN_SERVICIO), None)
    puntaje = _puntaje_v3(r3)
    if r3.get("success") is True and r3.get("action") == accion and puntaje is not None and puntaje >= configuracion.RECAPTCHA_UMBRAL:
        return _registrar(accion, "v3", Veredicto(True, puntaje=puntaje), r3)
    return _registrar(accion, "v3", Veredicto(False, pedir_v2=True, mensaje=MENSAJE_REINTENTAR, puntaje=puntaje), r3)


# TITULO VERIFICAR RESPALDO

def _verificar_respaldo(accion: str, token_v3: str, token_v2: str, ip: Optional[str]) -> Veredicto:
    """Modo «respaldo»: v3 decide en silencio y el casillero de v2 solo se pide si v3 no alcanza.

    Con un token de v2 lo comprueba contra la clave de v2. Sin él, comprueba el de v3: debe ser válido, de la misma acción y con puntaje de `configuracion.RECAPTCHA_UMBRAL` o
    más; si falta, es inválido o el puntaje es bajo, pide el casillero de v2. Si Google no responde, rechaza (falla cerrado) sin pedir v2, porque el casillero tampoco se podría
    comprobar."""
    if token_v2:
        respuesta = _consultar(configuracion.RECAPTCHA_V2_SECRETA, token_v2, ip)
        if respuesta is None:
            return _registrar(accion, "v2", Veredicto(False, mensaje=MENSAJE_SIN_SERVICIO), None)
        if respuesta.get("success") is True:
            return _registrar(accion, "v2", Veredicto(True), respuesta)
        return _registrar(accion, "v2", Veredicto(False, pedir_v2=True, mensaje=MENSAJE_REINTENTAR), respuesta)
    if not token_v3:
        print(f"{PREFIJO_REGISTRO} formulario={accion} version=v3 paso=no sin_token_v3 (el navegador no entregó token) pide_v2=si", flush=True)
        return Veredicto(False, pedir_v2=True, mensaje=MENSAJE_CONFIRMAR)
    respuesta = _consultar(configuracion.RECAPTCHA_V3_SECRETA, token_v3, ip)
    if respuesta is None:
        return _registrar(accion, "v3", Veredicto(False, mensaje=MENSAJE_SIN_SERVICIO), None)
    try:
        puntaje = float(respuesta.get("score")) if respuesta.get("score") is not None else None
    except (TypeError, ValueError):
        puntaje = None
    if respuesta.get("success") is True and respuesta.get("action") == accion and puntaje is not None and puntaje >= configuracion.RECAPTCHA_UMBRAL:
        return _registrar(accion, "v3", Veredicto(True, puntaje=puntaje), respuesta)
    return _registrar(accion, "v3", Veredicto(False, pedir_v2=True, mensaje=MENSAJE_CONFIRMAR, puntaje=puntaje), respuesta)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara recaptcha .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
