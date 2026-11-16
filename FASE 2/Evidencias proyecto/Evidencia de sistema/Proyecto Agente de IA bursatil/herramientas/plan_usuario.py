# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara plan_usuario .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Plan de cada usuario guardado en Supabase (tabla `planes_usuario`), para que la plataforma lo recuerde entre sesiones y dispositivos.

El esquema está en `herramientas/sql/planes_usuario.sql`. Lee y guarda con el mismo cliente de Supabase que usa la autenticación, así que
necesita SUPABASE_URL y la clave de servicio en el .env. Cada cambio se anota además en `planes_historial` (plan anterior, nuevo y origen),
para medir cuántos usuarios cambian de plan. Si Supabase no está configurado o falla, las funciones lo dicen devolviendo None / False y
quien las llama usa el archivo local (ver `herramientas/cuota_ia.py`).

Para no consultar la base en cada llamada del agente, el plan de cada usuario se guarda en memoria 30 segundos; al cambiarlo se actualiza al instante.
"""
import threading
import time
from datetime import datetime, timedelta, timezone

from herramientas import gestor_autenticacion

# Tablas de Supabase
_TABLA = "planes_usuario"
_TABLA_HISTORIAL = "planes_historial"
# Segundos que se recuerda en memoria el plan de un usuario (y, más corto, el hecho de que la consulta falló)
_VIDA_S = 30.0
_VIDA_FALLO_S = 5.0
# Caché: usuario_id -> (hora de la lectura, plan o None, si la consulta salió bien, vencimiento en segundos o None) y su candado
_CACHE: dict = {}
_CANDADO = threading.Lock()


# TITULO A SEGUNDOS

def _a_segundos(valor) -> float | None:
    """Convierte el valor de una columna de fecha (texto ISO o datetime) a segundos desde 1970; None si está vacío o no se entiende."""
    if not valor:
        return None
    try:
        fecha = valor if isinstance(valor, datetime) else datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        return (fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)).timestamp()
    except (ValueError, TypeError):
        return None


# TITULO LEER

def _leer(usuario_id) -> tuple:
    """(plan guardado, vencimiento en segundos o None, si la consulta salió bien) del usuario, con la caché en memoria.

    Una consulta fallida se recuerda solo unos segundos para reintentar pronto. Si la columna `vence_en` no existe se consulta solo el plan."""
    if usuario_id in (None, ""):
        return None, None, False
    ahora = time.time()
    with _CANDADO:
        guardado = _CACHE.get(usuario_id)
        if guardado and ahora - guardado[0] < (_VIDA_S if guardado[2] else _VIDA_FALLO_S):
            return guardado[1], guardado[3], guardado[2]
    plan, vence, correcto = None, None, False
    cliente = gestor_autenticacion._supabase
    if cliente is not None:
        try:
            try:
                filas = cliente.table(_TABLA).select("plan,vence_en").eq("usuario_id", int(usuario_id)).limit(1).execute().data or []
            except Exception:  # noqa: BLE001 - todavía no se creó la columna vence_en
                filas = cliente.table(_TABLA).select("plan").eq("usuario_id", int(usuario_id)).limit(1).execute().data or []
            plan, correcto = (filas[0]["plan"] if filas else None), True
            vence = _a_segundos(filas[0].get("vence_en")) if filas else None
        except Exception:  # noqa: BLE001 - sin conexión se usa el plan por defecto
            plan, vence, correcto = None, None, False
    with _CANDADO:
        _CACHE[usuario_id] = (ahora, plan, correcto, vence)
    return plan, vence, correcto


# TITULO PLAN DE

def plan_de(usuario_id) -> str | None:
    """Plan vigente del usuario, o None si no tiene ninguno registrado, ya venció o no se pudo consultar Supabase (quien llama usa entonces el plan por defecto).

    Un plan de pago con fecha de vencimiento ya pasada cuenta como si no hubiera plan."""
    plan, vence, _ = _leer(usuario_id)
    if plan and plan != "gratis" and vence is not None and vence <= time.time():
        return None
    return plan


# TITULO VENCE DE

def vence_de(usuario_id) -> float | None:
    """Cuándo vence el plan de pago vigente del usuario (segundos desde 1970), o None si no tiene plan de pago, no vence o ya venció."""
    plan, vence, _ = _leer(usuario_id)
    if not plan or plan == "gratis" or vence is None or vence <= time.time():
        return None
    return vence


# TITULO GUARDAR

def guardar(usuario_id, plan: str, origen: str = "prueba", anterior: str | None = None, dias: int | None = None) -> bool:
    """Guarda `plan` como el plan del usuario (inserta o actualiza su fila) y anota el cambio en el historial.

    `origen` dice de dónde viene el cambio: "prueba" (elegido en la vista de Planes mientras no se cobra), "pago" o "admin". `dias` es la duración del plan de pago
    desde hoy (por ejemplo 30); sin `dias` el plan no vence, y el plan Gratis nunca vence. Devuelve True si se pudo guardar. Nunca lanza excepciones."""
    cliente = gestor_autenticacion._supabase
    if cliente is None or usuario_id in (None, ""):
        return False
    ahora = datetime.now(timezone.utc)
    vence = ahora + timedelta(days=int(dias)) if dias and plan != "gratis" else None
    fila = {"usuario_id": int(usuario_id), "plan": plan, "origen": origen, "actualizado_en": ahora.isoformat()}
    try:
        uid = int(usuario_id)
        try:
            cliente.table(_TABLA).upsert({**fila, "vence_en": vence.isoformat() if vence else None}).execute()
        except Exception:  # noqa: BLE001 - todavía no se creó la columna vence_en: se guarda el plan sin vencimiento
            cliente.table(_TABLA).upsert(fila).execute()
            vence = None
    except Exception:  # noqa: BLE001
        return False
    try:
        cliente.table(_TABLA_HISTORIAL).insert({"usuario_id": uid, "plan_anterior": anterior, "plan_nuevo": plan, "origen": origen}).execute()
    except Exception:  # noqa: BLE001 - el historial es secundario: si falla, el cambio de plan igual quedó guardado
        pass
    with _CANDADO:
        _CACHE[usuario_id] = (time.time(), plan, True, vence.timestamp() if vence else None)
    return True


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara plan_usuario .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
