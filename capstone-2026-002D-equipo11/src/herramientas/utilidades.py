"""Herramientas generales, no ligadas a ninguna fuente de datos."""
from datetime import datetime

from herramientas.base import herramienta


@herramienta(
    descripcion=(
        "Devuelve la fecha y hora actual del sistema del usuario. Úsala cuando necesites "
        "saber qué día es hoy o calcular periodos relativos (ej. 'últimos 30 días')."
    )
)
def obtener_fecha_hora() -> dict:
    ahora = datetime.now().astimezone()
    return {
        "iso": ahora.isoformat(timespec="seconds"),
        "dia_semana": ahora.strftime("%A"),
        "zona_horaria": ahora.tzname(),
    }