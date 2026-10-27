# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara utilidades .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Herramientas generales, no ligadas a ninguna fuente de datos (hoy: fecha y hora del sistema)."""
from datetime import datetime

from herramientas.base import herramienta


@herramienta(
    descripcion=(
        "Devuelve la fecha y hora actual del sistema del usuario. Úsala cuando necesites "
        "saber qué día es hoy o calcular periodos relativos (ej. 'últimos 30 días')."
    )
)
def obtener_fecha_hora() -> dict:
    """Devuelve la fecha y hora actuales del equipo del usuario.

    No recibe parámetros. Devuelve un dict con la fecha en ISO 8601 (segundos, con zona horaria),
    el día de la semana (según la configuración regional del sistema) y el nombre de la zona horaria.
    Existe porque el modelo no conoce la fecha actual y la necesita para periodos relativos.
    """
    # Hora local con zona horaria explícita (astimezone convierte la hora ingenua del sistema).
    ahora = datetime.now().astimezone()
    return {
        "iso": ahora.isoformat(timespec="seconds"),
        "dia_semana": ahora.strftime("%A"),
        "zona_horaria": ahora.tzname(),
    }


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara utilidades .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
