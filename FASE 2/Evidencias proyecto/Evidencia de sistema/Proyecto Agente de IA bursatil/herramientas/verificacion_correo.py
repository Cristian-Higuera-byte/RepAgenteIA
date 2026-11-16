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
  - Un enlace vence (24 horas el de verificación, 5 minutos el de recuperación) y solo sirve una vez: `consumir` lo marca como usado y comprueba que
    no haya vencido en una sola sentencia, de modo que dos clics a la vez no pueden usarlo dos veces.
  - Pedir un enlace nuevo invalida los anteriores del mismo tipo. Hay límites para evitar abusos: entre un envío y otro pasa un minuto (30 minutos en el de recuperación) y se
    permiten cinco al día por usuario y tipo.
  - RECUPERACIÓN DE CONTRASEÑA (corrección de la auditoría, 13-11-2026): dos funciones de la base de datos (herramientas/sql/recuperacion_atomica.sql) la hacen atómica.
    `reservar_recuperacion` reserva el envío de forma atómica (dos solicitudes simultáneas no pueden enviar dos correos) y aplica la espera y el máximo diario por CORREO, exista o no
    una cuenta con él, para que la respuesta sea idéntica y no se pueda averiguar qué cuentas existen; el correo sale en un hilo aparte para que tampoco el tiempo de respuesta
    lo delate. `restablecer_contrasena_atomico` usa el enlace y guarda la contraseña nueva en una sola transacción: si el guardado falla, el enlace sigue sirviendo.
Las funciones reciben el cliente de la base de datos como parámetro (el mismo que usa gestor_autenticacion), así se pueden probar sin una base real.
"""
import hashlib
import os
import secrets
import sys
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from herramientas import correo

# Tabla de la base de datos y tipos de enlace.
TABLA = "enlaces_correo"
VERIFICACION = "verificacion"
RECUPERACION = "recuperacion"

# Cuánto dura cada tipo de enlace.
HORAS_VERIFICACION = 24
MINUTOS_RECUPERACION = 5

# Límites contra abusos: separación mínima entre envíos (en segundos, según el tipo) y máximo de envíos por día, para cada usuario y tipo.
MINUTOS_ENTRE_RECUPERACIONES = 30
SEGUNDOS_ENTRE_ENVIOS = {VERIFICACION: 60, RECUPERACION: MINUTOS_ENTRE_RECUPERACIONES * 60}
MAXIMO_ENVIOS_POR_DIA = 5

# Nombre del parámetro de la dirección con que la plataforma reconoce cada enlace (por ejemplo https://sitio/?verificar=TOKEN).
PARAMETRO = {VERIFICACION: "verificar", RECUPERACION: "recuperar"}

# Funciones y tabla de la base de datos de la recuperación atómica (herramientas/sql/recuperacion_atomica.sql).
FUNCION_RESERVAR = "reservar_recuperacion"
FUNCION_RESTABLECER = "restablecer_contrasena_atomico"
TABLA_SOLICITUDES = "solicitudes_recuperacion"

# Si es True (producción) el correo de recuperación se envía en un hilo aparte, así la respuesta tarda igual exista o no la cuenta. Las pruebas lo apagan para comprobar el envío enseguida.
ENVIO_EN_SEGUNDO_PLANO = True


# TITULO ERROR

class ErrorEnlace(Exception):
    """No se pudo crear o enviar el enlace; el texto está pensado para mostrarse a la persona."""


# TITULO ERROR ESPERA

class ErrorEspera(ErrorEnlace):
    """Se pidió un enlace demasiado pronto: ya se envió uno y hay que esperar. `segundos` es lo que falta para poder pedir otro."""

    def __init__(self, mensaje: str, segundos: int):
        super().__init__(mensaje)
        self.segundos = segundos


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
    if recientes:
        transcurridos = (ahora - leer_fecha(recientes[0]["creado_en"])).total_seconds()
        if transcurridos < SEGUNDOS_ENTRE_ENVIOS[tipo]:
            raise ErrorEspera(f"Espera {MINUTOS_ENTRE_RECUPERACIONES} minutos antes de pedir otro enlace." if tipo == RECUPERACION else "Espera un minuto antes de pedir otro enlace.",
                              int(SEGUNDOS_ENTRE_ENVIOS[tipo] - transcurridos) + 1)
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


# TITULO CONSULTAR

def consultar(cliente: Any, token: str, tipo: str, ahora: Optional[datetime] = None) -> Optional[tuple]:
    """Mira un enlace SIN usarlo: devuelve `(id del usuario, fecha de vencimiento)` si existe, es del tipo pedido, no venció y no se había usado; si no, None.

    Sirve para comprobar el enlace antes de gastarlo (por ejemplo, para no gastarlo si la contraseña nueva es igual a la actual) y para mostrar cuánto tiempo le queda."""
    token = (token or "").strip()
    if not token:
        return None
    ahora = ahora or ahora_utc()
    filas = (cliente.table(TABLA).select("usuario_id,expira_en").eq("token_hash", hash_de(token)).eq("tipo", tipo)
             .is_("usado_en", "null").gt("expira_en", ahora.isoformat()).execute().data or [])
    return (int(filas[0]["usuario_id"]), leer_fecha(filas[0]["expira_en"])) if filas else None


# TITULO HASH DE CORREO

def hash_de_correo(correo: str) -> str:
    """Hash SHA-256 (hexadecimal) del correo ya normalizado (minúsculas y sin espacios): con él se cuentan las solicitudes de recuperación sin guardar el correo."""
    return hashlib.sha256((correo or "").strip().lower().encode("utf-8")).hexdigest()


# TITULO RESERVAR RECUPERACION

def reservar_recuperacion(cliente: Any, correo: str, usuario_id: Optional[int] = None, ahora: Optional[datetime] = None) -> tuple:
    """Reserva de forma atómica el envío de un enlace de recuperación y devuelve `(token, id de la solicitud)`; el token es None si el correo no tiene cuenta (`usuario_id` None).

    La espera entre solicitudes y el máximo diario se aplican por CORREO, exista o no una cuenta, para que la respuesta sea la misma en ambos casos. Lanza ErrorEspera si todavía
    no pasó la espera (con los segundos que faltan) y ErrorEnlace si ya se pidió el máximo del día. Con usuario, la función de la base invalida sus enlaces de recuperación anteriores y crea el
    nuevo; el token solo existe aquí y en el correo. Efecto secundario: una llamada a `reservar_recuperacion` en la base de datos."""
    ahora = ahora or ahora_utc()
    token = secrets.token_urlsafe(32) if usuario_id is not None else None
    filas = cliente.rpc(FUNCION_RESERVAR, {"p_correo_hash": hash_de_correo(correo), "p_usuario": usuario_id, "p_token_hash": hash_de(token) if token else None,
                                           "p_espera_s": SEGUNDOS_ENTRE_ENVIOS[RECUPERACION], "p_maximo_dia": MAXIMO_ENVIOS_POR_DIA,
                                           "p_vigencia_s": int(duracion_de(RECUPERACION).total_seconds()), "p_ahora": ahora.isoformat()}).execute().data or []
    if not filas:
        raise ErrorEnlace("No se pudo reservar el envío del enlace.")
    estado = filas[0].get("estado")
    if estado == "limite":
        raise ErrorEnlace("Pediste demasiados enlaces hoy. Inténtalo de nuevo mañana.")
    if estado == "espera":
        raise ErrorEspera(f"Espera {MINUTOS_ENTRE_RECUPERACIONES} minutos antes de pedir otro enlace.", int(filas[0].get("segundos") or 0))
    if estado != "reservado":
        raise ErrorEnlace("No se pudo reservar el envío del enlace.")
    return token, filas[0].get("solicitud_id")


# TITULO ENVIAR RECUPERACION

def enviar_recuperacion(cliente: Any, usuario_id: int, nombre: str, destinatario: str, token: str, solicitud_id: Any) -> bool:
    """Envía el correo de un enlace ya reservado y devuelve True si salió. Si falla, borra el enlace y libera la solicitud para que un fallo del correo no cuente contra el límite diario.

    Nunca lanza: corre en un hilo aparte, así que el detalle técnico solo queda en el registro del servidor."""
    try:
        asunto, texto, cuerpo = correo.plantilla_recuperacion(nombre, armar_enlace(token, RECUPERACION), MINUTOS_RECUPERACION)
        correo.enviar(destinatario, asunto, texto, cuerpo)
        return True
    except (correo.ErrorCorreo, ErrorEnlace) as error:
        print(f"[Correo] No se pudo enviar el enlace de recuperación al usuario {usuario_id}: {error}", file=sys.stderr, flush=True)
    except Exception as error:  # noqa: BLE001 - un hilo no debe morir en silencio
        print(f"[Correo] Fallo inesperado al enviar la recuperación al usuario {usuario_id}: {error}", file=sys.stderr, flush=True)
    try:
        cliente.table(TABLA).delete().eq("token_hash", hash_de(token)).execute()
        if solicitud_id is not None:
            cliente.table(TABLA_SOLICITUDES).delete().eq("id", solicitud_id).execute()
    except Exception as error:  # noqa: BLE001
        print(f"[Correo] No se pudo liberar la solicitud de recuperación: {error}", file=sys.stderr, flush=True)
    return False


# TITULO EN SEGUNDO PLANO

def en_segundo_plano(tarea: Any) -> None:
    """Ejecuta `tarea` (una función sin argumentos) en un hilo aparte, o enseguida si ENVIO_EN_SEGUNDO_PLANO está apagado (pruebas)."""
    if not ENVIO_EN_SEGUNDO_PLANO:
        tarea()
        return
    threading.Thread(target=tarea, name="envio-recuperacion", daemon=True).start()


# TITULO RESTABLECER ATOMICO

def restablecer_atomico(cliente: Any, token: str, contrasena_cifrada: str, verificar_correo: bool, ahora: Optional[datetime] = None) -> Optional[int]:
    """Usa el enlace de recuperación Y guarda la contraseña nueva (ya cifrada) en una sola transacción de la base de datos; devuelve el id del usuario, o None si el enlace no sirve.

    Si algo falla al guardar la contraseña, la transacción se deshace y el enlace NO queda gastado; la excepción sube a quien llama. Con `verificar_correo` deja además el correo como
    verificado. Efecto secundario: una llamada a `restablecer_contrasena_atomico` en la base de datos."""
    token = (token or "").strip()
    if not token:
        return None
    ahora = ahora or ahora_utc()
    filas = cliente.rpc(FUNCION_RESTABLECER, {"p_token_hash": hash_de(token), "p_password_hash": contrasena_cifrada, "p_verificar": bool(verificar_correo),
                                              "p_ahora": ahora.isoformat()}).execute().data or []
    return int(filas[0]["id_usuario"]) if filas else None


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
