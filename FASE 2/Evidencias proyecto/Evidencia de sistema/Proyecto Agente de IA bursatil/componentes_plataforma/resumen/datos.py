# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara datos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Datos estáticos de la vista Resumen: acentos de las tarjetas KPI y periodos de la curva.

Se leen una vez al importar desde `datos.json` (con el caché de `_estaticos.datos_json`) y se exponen como las
constantes `ACC` (usada por `tarjetas.py`) y `PERIODOS` (usada por `secciones.py`). No escribe nada.
"""
from pathlib import Path

from componentes_plataforma._estaticos import datos_json

# Contenido completo de datos.json (claves "acentos" y "periodos").
_D = datos_json(Path(__file__).parent / "datos.json")

# clave -> (acento, icono, fondo icono, color icono)
ACC = {k: tuple(v) for k, v in _D["acentos"].items()}
# Selector de la curva: etiqueta mostrada -> número de días a incluir (None significa todo el historial).
PERIODOS = dict(_D["periodos"])


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara datos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
