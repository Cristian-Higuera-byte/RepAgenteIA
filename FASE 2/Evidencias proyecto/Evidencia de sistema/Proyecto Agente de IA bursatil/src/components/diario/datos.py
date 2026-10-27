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

"""Opciones de las notas del Diario (viven en datos.json) y paleta P&J.

Las listas de estrategias y emociones alimentan los selectores de la ficha de operación
(ficha.py); la paleta la usan el mini-gráfico (mini_grafico.py) y, por coherencia, el CSS.
"""
from pathlib import Path

from components._estaticos import datos_json

# Contenido de datos.json (claves "estrategias" y "emociones"), editable sin tocar código.
_D = datos_json(Path(__file__).parent / "datos.json")
# Opciones del selector "Estrategia" (el primer elemento actúa como "sin valor").
ESTRATEGIAS = list(_D["estrategias"])
# Opciones del selector "Emoción / estado" (el primer elemento actúa como "sin valor").
EMOCIONES = list(_D["emociones"])

# Paleta (P&J): verde #3fb950, rojo #f85149, azul #58a6ff, naranja #ff8f00.
# Abreviaturas en orden: UP verde (ganancia), DN rojo (pérdida), AZ azul (entrada), NA naranja (acento),
# TX texto claro (salida) y GR gris (texto secundario).
UP, DN, AZ, NA, TX, GR = "#3fb950", "#f85149", "#58a6ff", "#ff8f00", "#e6edf3", "#8b949e"


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
