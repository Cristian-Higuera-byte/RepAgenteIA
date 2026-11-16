# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara correo .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
correo.py
---------
Envío de correos de la plataforma (confirmación del correo y recuperación de contraseña) por SMTP, con las plantillas de los mensajes.

Funciona con cualquier servidor SMTP: un buzón del hosting, Gmail con contraseña de aplicación o el de la empresa. Cambiar de uno a otro es
cambiar las variables del .env, sin tocar el código:
  CORREO_SERVIDOR     servidor de salida (por ejemplo pyj.rmcabogados.cl o smtp.gmail.com)
  CORREO_PUERTO       465 (conexión segura desde el inicio) o 587 (STARTTLS)
  CORREO_SEGURIDAD    ssl (por defecto, para el 465) o starttls (para el 587)
  CORREO_USUARIO      dirección del buzón que envía
  CORREO_CLAVE        contraseña del buzón (o contraseña de aplicación en Gmail)
  CORREO_REMITENTE    nombre que ve quien recibe, por ejemplo «Piña & Jara Terminal»
  CORREO_VERIFICAR_CERTIFICADO   true (por defecto); false solo si el certificado del servidor no coincide con su nombre y se confía en él
Los errores se informan con ErrorCorreo y un texto que dice qué revisar. Nunca se escribe la contraseña en un mensaje de error.
"""
import html
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from typing import Optional

# Variables que deben existir para poder enviar correo.
VARIABLES_OBLIGATORIAS = ("CORREO_SERVIDOR", "CORREO_PUERTO", "CORREO_USUARIO", "CORREO_CLAVE")

# Segundos que se espera la respuesta del servidor de correo antes de darlo por caído.
SEGUNDOS_ESPERA = 20


# TITULO ERROR

class ErrorCorreo(Exception):
    """No se pudo enviar el correo; el texto dice qué pasó y qué revisar."""


# TITULO CONFIGURADO

def configurado() -> bool:
    """True si el .env trae las cuatro variables obligatorias del servidor de correo."""
    return all(os.environ.get(variable, "").strip() for variable in VARIABLES_OBLIGATORIAS)


# TITULO CONFIGURACION

def leer_configuracion() -> dict:
    """Lee la configuración del .env y la devuelve como diccionario; lanza ErrorCorreo si falta algo o el puerto no es un número."""
    faltantes = [variable for variable in VARIABLES_OBLIGATORIAS if not os.environ.get(variable, "").strip()]
    if faltantes:
        raise ErrorCorreo("Falta configurar el correo en el .env: " + ", ".join(faltantes) + ".")
    try:
        puerto = int(os.environ["CORREO_PUERTO"].strip())
    except ValueError:
        raise ErrorCorreo("CORREO_PUERTO debe ser un número, por ejemplo 465.") from None
    seguridad = os.environ.get("CORREO_SEGURIDAD", "ssl").strip().lower() or "ssl"
    if seguridad not in ("ssl", "starttls"):
        raise ErrorCorreo("CORREO_SEGURIDAD debe ser ssl o starttls.")
    return {
        "servidor": os.environ["CORREO_SERVIDOR"].strip(),
        "puerto": puerto,
        "seguridad": seguridad,
        "usuario": os.environ["CORREO_USUARIO"].strip(),
        "clave": os.environ["CORREO_CLAVE"],
        "remitente": os.environ.get("CORREO_REMITENTE", "").strip() or "Piña & Jara Terminal",
        "verificar_certificado": os.environ.get("CORREO_VERIFICAR_CERTIFICADO", "true").strip().lower() not in ("0", "false", "no"),
    }


# TITULO ARMAR MENSAJE

def armar_mensaje(destinatario: str, asunto: str, texto: str, cuerpo_html: Optional[str], configuracion: dict, responder_a: Optional[str] = None) -> EmailMessage:
    """Construye el mensaje: de quién, para quién, asunto, texto simple y, si se entrega, la versión con formato (HTML).

    Con `responder_a` se agrega la cabecera «Reply-To», para que al contestar el correo la respuesta vaya a esa dirección y no al buzón que envía."""
    mensaje = EmailMessage()
    mensaje["From"] = formataddr((configuracion["remitente"], configuracion["usuario"]))
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    if responder_a:
        mensaje["Reply-To"] = responder_a
    mensaje["Date"] = formatdate(localtime=True)
    mensaje["Message-ID"] = make_msgid(domain=configuracion["usuario"].split("@")[-1])
    mensaje.set_content(texto)
    if cuerpo_html:
        mensaje.add_alternative(cuerpo_html, subtype="html")
    return mensaje


# TITULO ENVIAR

def enviar(destinatario: str, asunto: str, texto: str, cuerpo_html: Optional[str] = None, responder_a: Optional[str] = None) -> None:
    """Envía un correo; lanza ErrorCorreo si no se pudo (servidor inalcanzable, certificado, usuario o contraseña rechazados, destinatario rechazado).

    `responder_a` (opcional) es la dirección a la que irán las respuestas, por ejemplo la de la persona que escribió un reporte de soporte."""
    destinatario = (destinatario or "").strip()
    if "@" not in destinatario or any(letra in destinatario for letra in "\r\n"):
        raise ErrorCorreo("La dirección de destino no es válida.")
    configuracion = leer_configuracion()
    if responder_a and ("@" not in responder_a or any(letra in responder_a for letra in chr(13) + chr(10))):
        responder_a = None
    mensaje = armar_mensaje(destinatario, asunto, texto, cuerpo_html, configuracion, responder_a)
    contexto = ssl.create_default_context()
    if not configuracion["verificar_certificado"]:
        contexto.check_hostname = False
        contexto.verify_mode = ssl.CERT_NONE
    servidor, puerto = configuracion["servidor"], configuracion["puerto"]
    try:
        if configuracion["seguridad"] == "ssl":
            conexion = smtplib.SMTP_SSL(servidor, puerto, timeout=SEGUNDOS_ESPERA, context=contexto)
        else:
            conexion = smtplib.SMTP(servidor, puerto, timeout=SEGUNDOS_ESPERA)
            conexion.starttls(context=contexto)
        with conexion:
            conexion.login(configuracion["usuario"], configuracion["clave"])
            conexion.send_message(mensaje)
    except ssl.SSLCertVerificationError:
        raise ErrorCorreo(f"El certificado del servidor de correo no coincide con «{servidor}». Revisa CORREO_SERVIDOR o, solo si confías en ese "
                          "servidor, define CORREO_VERIFICAR_CERTIFICADO=false.") from None
    except smtplib.SMTPAuthenticationError:
        raise ErrorCorreo("El servidor de correo rechazó el usuario o la contraseña. Revisa CORREO_USUARIO y CORREO_CLAVE.") from None
    except smtplib.SMTPRecipientsRefused:
        raise ErrorCorreo("El servidor de correo rechazó la dirección de destino.") from None
    except smtplib.SMTPException as error:
        raise ErrorCorreo(f"El servidor de correo respondió con un error: {error.__class__.__name__}.") from None
    except OSError as error:
        raise ErrorCorreo(f"No se pudo conectar con el servidor de correo ({servidor}:{puerto}): {error.__class__.__name__}.") from None


# TITULO PLANTILLA HTML

def plantilla_html(titulo: str, saludo: str, parrafos: list, texto_boton: str, enlace: str, pie: str) -> str:
    """Arma el correo con formato: un recuadro claro, un solo botón con el enlace y un pie. Todo el texto variable se escapa."""
    cuerpo = "".join(f'<p style="margin:0 0 12px;font-size:14px;line-height:1.5;color:#1f2328">{html.escape(p)}</p>' for p in parrafos)
    return (
        '<div style="background:#f6f8fa;padding:24px;font-family:Arial,Helvetica,sans-serif">'
        '<div style="max-width:460px;margin:0 auto;background:#ffffff;border:1px solid #d0d7de;border-radius:8px;padding:24px">'
        '<p style="margin:0 0 4px;font-size:22px;font-weight:bold;color:#ff6a1a">P&amp;J</p>'
        f'<p style="margin:0 0 16px;font-size:16px;font-weight:bold;color:#1f2328">{html.escape(titulo)}</p>'
        f'<p style="margin:0 0 12px;font-size:14px;color:#1f2328">{html.escape(saludo)}</p>'
        f'{cuerpo}'
        f'<p style="margin:20px 0"><a href="{html.escape(enlace, quote=True)}" '
        'style="display:inline-block;background:#ff4b4b;color:#ffffff;text-decoration:none;font-size:14px;font-weight:bold;'
        f'padding:10px 20px;border-radius:6px">{html.escape(texto_boton)}</a></p>'
        f'<p style="margin:0 0 6px;font-size:12px;color:#656d76">Si el botón no funciona, copia esta dirección en tu navegador:<br>{html.escape(enlace)}</p>'
        f'<p style="margin:12px 0 0;font-size:12px;color:#656d76">{html.escape(pie)}</p>'
        '</div></div>'
    )


# TITULO PLANTILLA VERIFICACION

def plantilla_verificacion(nombre: str, enlace: str, horas: int) -> tuple:
    """Devuelve (asunto, texto, html) del correo que confirma la dirección de correo al crear una cuenta."""
    saludo = f"Hola {nombre},"
    parrafos = [f"Confirma tu correo para activar tu cuenta. El enlace vence en {horas} horas y solo sirve una vez."]
    pie = "Si no creaste esta cuenta, ignora este mensaje."
    texto = f"{saludo}\n\n{parrafos[0]}\n\nConfirmar mi correo: {enlace}\n\n{pie}\n"
    return "Confirma tu correo", texto, plantilla_html("Confirma tu correo", saludo, parrafos, "Confirmar mi correo", enlace, pie)


# TITULO PLANTILLA RECUPERACION

def plantilla_recuperacion(nombre: str, enlace: str, minutos: int) -> tuple:
    """Devuelve (asunto, texto, html) del correo con el enlace para elegir una contraseña nueva."""
    saludo = f"Hola {nombre},"
    parrafos = [f"Recibimos una solicitud para restablecer tu contraseña. Elige una nueva con el botón de abajo. El enlace vence en {minutos} minutos y solo sirve una vez."]
    pie = "Si no pediste este cambio, ignora este mensaje: tu contraseña actual sigue funcionando."
    texto = f"{saludo}\n\n{parrafos[0]}\n\nRestablecer mi contraseña: {enlace}\n\n{pie}\n"
    return "Restablece tu contraseña", texto, plantilla_html("Restablece tu contraseña", saludo, parrafos, "Restablecer mi contraseña", enlace, pie)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara correo .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
