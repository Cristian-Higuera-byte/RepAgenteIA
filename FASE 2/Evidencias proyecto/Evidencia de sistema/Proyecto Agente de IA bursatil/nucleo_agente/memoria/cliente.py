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
import os
from datetime import datetime, timezone
from typing import Any

import configuracion  # noqa: F401  (al importarlo se carga el .env)
from nucleo_agente.memoria.errores import ErrorMemoria

# Cliente de Supabase compartido por todo el proceso (None hasta el primer uso).
_cliente_global: Any = None


# TITULO OBTENER CLIENTE

def _obtener_cliente() -> Any:
    """Devuelve el cliente de Supabase del proceso, creándolo la primera vez.

    Lee SUPABASE_URL y SUPABASE_KEY del entorno (.env); lanza ErrorMemoria si faltan o si la creación falla.
    La librería supabase se importa aquí para no exigirla cuando la memoria no se usa.
    """
    global _cliente_global
    if _cliente_global is None:
        url = os.getenv("SUPABASE_URL", "")
        clave = os.getenv("SUPABASE_KEY", "")
        if not url or not clave:
            raise ErrorMemoria("Faltan SUPABASE_URL y/o SUPABASE_KEY en el .env.")
        try:
            from supabase import create_client

            _cliente_global = create_client(url, clave)
        except Exception as e:  # noqa: BLE001
            raise ErrorMemoria(f"No se pudo crear el cliente de Supabase: {e}") from e
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
