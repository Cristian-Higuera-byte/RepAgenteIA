# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara verificacion_correo .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""
verificacion_correo.py
----------------------
Enlaces de un solo uso que se envían por correo para confirmar una cuenta o recuperar una contraseña.

Cómo funciona:
  - Se genera un token aleatorio. En la base de datos (tabla `enlaces_correo`, herramientas/sql/verificacion_correo.sql) se guarda solo su hash SHA-256, con
    el usuario, el tipo (verificacion o recuperacion) y el vencimiento; el token viaja únicamente en el correo, dentro de un enlace de la plataforma.
  - Un enlace vence (24 horas el de verificación, 60 minutos el de recuperación) y solo sirve una vez: `consumir` lo marca como usado y comprueba que
    no haya vencido en una sola sentencia, de modo que dos clics a la vez no pueden usarlo dos veces.
  - Pedir un enlace nuevo invalida los anteriores del mismo tipo. Hay límites para evitar abusos: un envío por minuto y cinco al día por usuario y tipo.
Las funciones reciben el cliente de la base de datos como parámetro (el mismo que usa gestor_autenticacion), así se pueden probar sin una base real.
"""
import hashlib
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from herramientas import correo

# Tabla de la base de datos y tipos de enlace.
TABLA = "enlaces_correo"
VERIFICACION = "verificacion"
RECUPERACION = "recuperacion"

# Cuánto dura cada tipo de enlace.
HORAS_VERIFICACION = 24
MINUTOS_RECUPERACION = 60

# Límites contra abusos: separación mínima entre envíos y máximo de envíos por día, para cada usuario y tipo.
SEGUNDOS_ENTRE_ENVIOS = 60
MAXIMO_ENVIOS_POR_DIA = 5

# Nombre del parámetro de la dirección con que la plataforma reconoce cada enlace (por ejemplo https://sitio/?verificar=TOKEN).
PARAMETRO = {VERIFICACION: "verificar", RECUPERACION: "recuperar"}


# TITULO ERROR

class ErrorEnlace(Exception):
    """No se pudo crear o enviar el enlace; el texto está pensado para mostrarse a la persona."""


# TITULO HASH

def hash_de(token: str) -> str:
    """Devuelve el hash SHA-256 (hexadecimal) de un token; es lo único que se guarda en la base de datos."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# TITULO FECHAS

def ahora_utc() -> datetime:
    """Hora actual con zona horaria UTC."""
    return datetime.now(timezone.utc)


def leer_fecha(texto: str) -> datetime:
    """Convierte un texto ISO 8601 que entrega la base de datos en datetime con zona horaria (sin zona se asume UTC)."""
    fecha = datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


# TITULO DURACION

def duracion_de(tipo: str) -> timedelta:
    """Cuánto dura un enlace del tipo indicado; lanza ValueError si el tipo no existe."""
    if tipo == VERIFICACION:
        return timedelta(hours=HORAS_VERIFICACION)
    if tipo == RECUPERACION:
        return timedelta(minutes=MINUTOS_RECUPERACION)
    raise ValueError(f"Tipo de enlace desconocido: {tipo!r}")


# TITULO CREAR ENLACE

def crear_enlace(cliente: Any, usuario_id: int, tipo: str, ahora: Optional[datetime] = None) -> str:
    """Crea un enlace nuevo para el usuario y devuelve su token (que solo existe en este momento y en el correo).

    Aplica los límites de envío (lanza ErrorEnlace si se pide muy seguido o demasiadas veces en el día) e invalida los enlaces anteriores sin usar del
    mismo tipo. Efecto secundario: una actualización y una inserción en la tabla `enlaces_correo`.
    """
    ahora = ahora or ahora_utc()
    vigencia = duracion_de(tipo)
    recientes = (cliente.table(TABLA).select("creado_en").eq("usuario_id", usuario_id).eq("tipo", tipo)
                 .gte("creado_en", (ahora - timedelta(days=1)).isoformat()).order("creado_en", desc=True).execute().data or [])
    if len(recientes) >= MAXIMO_ENVIOS_POR_DIA:
        raise ErrorEnlace("Pediste demasiados enlaces hoy. Inténtalo de nuevo mañana.")
    if recientes and (ahora - leer_fecha(recientes[0]["creado_en"])).total_seconds() < SEGUNDOS_ENTRE_ENVIOS:
        raise ErrorEnlace("Espera un minuto antes de pedir otro enlace.")
    cliente.table(TABLA).update({"usado_en": ahora.isoformat()}).eq("usuario_id", usuario_id).eq("tipo", tipo).is_("usado_en", "null").execute()
    token = secrets.token_urlsafe(32)
    cliente.table(TABLA).insert({"usuario_id": usuario_id, "tipo": tipo, "token_hash": hash_de(token),
                                 "creado_en": ahora.isoformat(), "expira_en": (ahora + vigencia).isoformat()}).execute()
    return token


# TITULO CONSUMIR

def consumir(cliente: Any, token: str, tipo: str, ahora: Optional[datetime] = None) -> Optional[int]:
    """Usa un enlace: devuelve el id del usuario si el enlace existe, es del tipo pedido, no venció y no se había usado; si no, None.

    Todo ocurre en una sola sentencia (marca como usado solo si sigue vigente), así que un enlace no se puede usar dos veces ni siquiera con dos
    solicitudes simultáneas. Efecto secundario: una actualización en la tabla `enlaces_correo`.
    """
    token = (token or "").strip()
    if not token:
        return None
    ahora = ahora or ahora_utc()
    filas = (cliente.table(TABLA).update({"usado_en": ahora.isoformat()}).eq("token_hash", hash_de(token)).eq("tipo", tipo)
             .is_("usado_en", "null").gt("expira_en", ahora.isoformat()).execute().data or [])
    return int(filas[0]["usuario_id"]) if filas else None


# TITULO ARMAR ENLACE

def armar_enlace(token: str, tipo: str) -> str:
    """Arma la dirección que va en el correo con la dirección pública de la plataforma (PLATAFORMA_URL del .env); lanza ErrorEnlace si falta."""
    base = os.environ.get("PLATAFORMA_URL", "").strip().rstrip("/")
    if not base:
        raise ErrorEnlace("Falta configurar PLATAFORMA_URL en el .env (la dirección pública de la plataforma).")
    return f"{base}/?{PARAMETRO[tipo]}={token}"


# TITULO ENVIAR ENLACE

def enviar_enlace(cliente: Any, usuario_id: int, nombre: str, destinatario: str, tipo: str) -> None:
    """Crea el enlace y lo envía por correo. Lanza ErrorEnlace con un texto para la persona; el detalle técnico queda en el registro del servidor.

    Si el envío falla se borra el enlace recién creado, de modo que un fallo del servidor de correo no cuente contra el límite diario de la persona.
    """
    token = crear_enlace(cliente, usuario_id, tipo)
    try:
        enlace = armar_enlace(token, tipo)
        if tipo == VERIFICACION:
            asunto, texto, cuerpo = correo.plantilla_verificacion(nombre, enlace, HORAS_VERIFICACION)
        else:
            asunto, texto, cuerpo = correo.plantilla_recuperacion(nombre, enlace, MINUTOS_RECUPERACION)
        correo.enviar(destinatario, asunto, texto, cuerpo)
    except (correo.ErrorCorreo, ErrorEnlace) as error:
        cliente.table(TABLA).delete().eq("token_hash", hash_de(token)).execute()
        print(f"[Correo] No se pudo enviar el enlace de {tipo} al usuario {usuario_id}: {error}", file=sys.stderr, flush=True)
        raise ErrorEnlace("No pudimos enviar el correo ahora. Inténtalo de nuevo en unos minutos.") from None


# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara verificacion_correo .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
