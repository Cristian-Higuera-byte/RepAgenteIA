# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara cliente .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Cliente de Supabase (se crea al primer uso, no al importar) y hora UTC."""
from datetime import datetime, timezone
from typing import Any

import configuracion  # noqa: F401  (al importarlo se carga el .env)
from nucleo_agente.memoria.errores import ErrorMemoria

# Cliente de Supabase compartido por todo el proceso (None hasta el primer uso).
_cliente_global: Any = None


# TITULO OBTENER CLIENTE

def _obtener_cliente() -> Any:
    """Devuelve el cliente de Supabase del proceso, creándolo la primera vez.

    Usa el motor que indique BASE_DATOS en el .env (Supabase por defecto, o PostgreSQL); lanza ErrorMemoria si faltan sus variables o si la
    creación falla. Las librerías de cada motor se importan solo cuando ese motor se elige.
    """
    global _cliente_global
    if _cliente_global is None:
        from herramientas import base_datos

        if not base_datos.hay_credenciales():
            raise ErrorMemoria("Faltan las credenciales de la base de datos en el .env (SUPABASE_URL y SUPABASE_KEY, o las POSTGRES_* si BASE_DATOS=postgres).")
        try:
            _cliente_global = base_datos.crear_cliente()
        except Exception as e:  # noqa: BLE001
            raise ErrorMemoria(f"No se pudo crear el cliente de la base de datos: {e}") from e
    return _cliente_global


# TITULO AHORA

def _ahora() -> str:
    """Hora actual en UTC como texto ISO 8601 (para las columnas de fecha de Supabase)."""
    return datetime.now(timezone.utc).isoformat()


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara cliente .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
