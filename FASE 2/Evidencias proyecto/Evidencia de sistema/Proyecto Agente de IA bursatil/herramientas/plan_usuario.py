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
from datetime import datetime, timezone

from herramientas import gestor_autenticacion

# Tablas de Supabase
_TABLA = "planes_usuario"
_TABLA_HISTORIAL = "planes_historial"
# Segundos que se recuerda en memoria el plan de un usuario (y, más corto, el hecho de que la consulta falló)
_VIDA_S = 30.0
_VIDA_FALLO_S = 5.0
# Caché: usuario_id -> (hora de la lectura, plan o None) y su candado
_CACHE: dict = {}
_CANDADO = threading.Lock()


# TITULO PLAN DE

def plan_de(usuario_id) -> str | None:
    """Plan guardado del usuario, o None si no tiene ninguno registrado o no se pudo consultar Supabase.

    Usa la caché en memoria; una consulta fallida se recuerda solo unos segundos para reintentar pronto."""
    if usuario_id in (None, ""):
        return None
    ahora = time.time()
    with _CANDADO:
        guardado = _CACHE.get(usuario_id)
        if guardado and ahora - guardado[0] < (_VIDA_S if guardado[2] else _VIDA_FALLO_S):
            return guardado[1]
    plan, correcto = None, False
    cliente = gestor_autenticacion._supabase
    if cliente is not None:
        try:
            filas = cliente.table(_TABLA).select("plan").eq("usuario_id", int(usuario_id)).limit(1).execute().data or []
            plan, correcto = (filas[0]["plan"] if filas else None), True
        except Exception:  # noqa: BLE001 - sin conexión se usa el plan por defecto
            plan, correcto = None, False
    with _CANDADO:
        _CACHE[usuario_id] = (ahora, plan, correcto)
    return plan


# TITULO GUARDAR

def guardar(usuario_id, plan: str, origen: str = "prueba", anterior: str | None = None) -> bool:
    """Guarda `plan` como el plan del usuario (inserta o actualiza su fila) y anota el cambio en el historial.

    `origen` dice de dónde viene el cambio: "prueba" (elegido en la vista de Planes mientras no se cobra), "pago" o "admin". Devuelve True si
    se pudo guardar. Nunca lanza excepciones."""
    cliente = gestor_autenticacion._supabase
    if cliente is None or usuario_id in (None, ""):
        return False
    try:
        uid = int(usuario_id)
        cliente.table(_TABLA).upsert({"usuario_id": uid, "plan": plan, "origen": origen, "actualizado_en": datetime.now(timezone.utc).isoformat()}).execute()
    except Exception:  # noqa: BLE001
        return False
    try:
        cliente.table(_TABLA_HISTORIAL).insert({"usuario_id": uid, "plan_anterior": anterior, "plan_nuevo": plan, "origen": origen}).execute()
    except Exception:  # noqa: BLE001 - el historial es secundario: si falla, el cambio de plan igual quedó guardado
        pass
    with _CANDADO:
        _CACHE[usuario_id] = (time.time(), plan, True)
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
