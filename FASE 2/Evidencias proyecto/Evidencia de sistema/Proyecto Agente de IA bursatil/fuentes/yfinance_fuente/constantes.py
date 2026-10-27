# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara constantes .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Periodos e intervalos válidos de Yahoo Finance, aviso de retraso y mapas de campos (datos.json).

Los valores no están escritos en el código: se leen una sola vez, al importar,
desde el archivo `datos.json` que está junto a este módulo."""
import json
from pathlib import Path

# Contenido completo de datos.json (claves: periodos, intervalos, aviso_retraso, campos_texto, campos_num, estados).
_D = json.loads((Path(__file__).parent / "datos.json").read_text(encoding="utf-8"))

# Periodos aceptados por Yahoo en el histórico (p. ej. '1mo', '3mo', '1y').
PERIODOS = tuple(_D["periodos"])
# Intervalos de vela aceptados por Yahoo (p. ej. '1m', '1h', '1d').
INTERVALOS = tuple(_D["intervalos"])

# Texto que advierte que los datos gratuitos pueden llegar con retraso; se adjunta a las respuestas.
AVISO_RETRASO = _D["aviso_retraso"]

# Fundamentales (Ticker.info): clave de salida -> campo de Yahoo
# Campos de texto (sector, industria, país...) y campos numéricos (ratios, márgenes...).
_CAMPOS_TEXTO = dict(_D["campos_texto"])
_CAMPOS_NUMERO = dict(_D["campos_num"])

# Estados financieros: tipo -> (atributo anual, atributo trimestral, filas clave)
_ESTADOS = {k: (v[0], v[1], tuple(v[2])) for k, v in _D["estados"].items()}


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara constantes .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
