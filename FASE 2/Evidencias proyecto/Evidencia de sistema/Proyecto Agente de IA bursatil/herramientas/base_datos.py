# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara base_datos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
base_datos.py
-------------
Decide con qué base de datos trabaja la plataforma y entrega el cliente de consultas.

La variable BASE_DATOS del .env elige el motor, igual que PROVEEDOR elige entre MetaTrader 5 y Capital.com:
  - supabase (por defecto): como siempre, con SUPABASE_URL y SUPABASE_KEY. Si BASE_DATOS no existe, todo funciona igual que antes.
  - postgres: un PostgreSQL común (por ejemplo el del hosting) con POSTGRES_SERVIDOR, POSTGRES_PUERTO, POSTGRES_BASE_DATOS,
    POSTGRES_USUARIO y POSTGRES_CONTRASENA. Usa el adaptador de herramientas/base_datos_postgres.py.
Volver atrás es cambiar esa línea del .env y reiniciar. Los módulos que acceden a datos piden el cliente aquí y no importan nada de Supabase.
"""
import os
import threading
from typing import Any

from herramientas.base_datos_postgres import ErrorBaseDatos, crear_cliente_desde_entorno

# Motores admitidos y variables que cada uno necesita en el .env.
MOTORES = ("supabase", "postgres")
VARIABLES_SUPABASE = ("SUPABASE_URL", "SUPABASE_KEY")
VARIABLES_POSTGRES = ("POSTGRES_SERVIDOR", "POSTGRES_PUERTO", "POSTGRES_BASE_DATOS", "POSTGRES_USUARIO", "POSTGRES_CONTRASENA")

# Cliente de PostgreSQL compartido por todo el proceso: así los módulos comparten un solo grupo de conexiones y no abren uno cada uno.
_cliente_postgres: Any = None
_candado = threading.Lock()


# TITULO MOTOR

def motor() -> str:
    """Devuelve el motor elegido en BASE_DATOS (supabase si no está definida); lanza ErrorBaseDatos si el valor no es válido."""
    valor = os.environ.get("BASE_DATOS", "").strip().lower() or "supabase"
    if valor not in MOTORES:
        raise ErrorBaseDatos(f"BASE_DATOS={valor!r} no es válido; usa uno de: {', '.join(MOTORES)}.")
    return valor


# TITULO HAY CREDENCIALES

def hay_credenciales() -> bool:
    """Indica si el .env trae todas las variables del motor elegido (False también si BASE_DATOS tiene un valor no válido)."""
    try:
        variables = VARIABLES_POSTGRES if motor() == "postgres" else VARIABLES_SUPABASE
    except ErrorBaseDatos:
        return False
    return all(os.environ.get(variable, "").strip() for variable in variables)


# TITULO CREAR CLIENTE

def crear_cliente() -> Any:
    """Devuelve el cliente de consultas del motor elegido.

    Con postgres devuelve siempre el mismo cliente del proceso (se crea la primera vez y no abre conexiones hasta la primera consulta).
    Con supabase crea un cliente nuevo, como hacía el código antes; la librería `supabase` se importa solo en ese caso, de modo que se
    puede desinstalar cuando ya no se use. Lanza ErrorBaseDatos si faltan variables o el valor de BASE_DATOS no es válido.
    """
    global _cliente_postgres
    if motor() == "postgres":
        with _candado:
            if _cliente_postgres is None:
                _cliente_postgres = crear_cliente_desde_entorno()
            return _cliente_postgres
    faltantes = [variable for variable in VARIABLES_SUPABASE if not os.environ.get(variable, "").strip()]
    if faltantes:
        raise ErrorBaseDatos("Faltan variables en el .env: " + ", ".join(faltantes))
    from supabase import create_client  # type: ignore[import-not-found]
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara base_datos .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
