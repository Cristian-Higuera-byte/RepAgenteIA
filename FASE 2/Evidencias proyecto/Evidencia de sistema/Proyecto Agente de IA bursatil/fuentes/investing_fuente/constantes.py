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

"""Feeds RSS de Investing.com, aviso de la fuente y cabeceras HTTP (datos.json).

Los valores no están escritos en el código: se leen una sola vez, al importar,
desde el archivo `datos.json` que está junto a este módulo."""
import json
from pathlib import Path

# Contenido completo de datos.json (claves: feeds, aviso_fuente, headers).
_D = json.loads((Path(__file__).parent / "datos.json").read_text(encoding="utf-8"))

# Categoría de noticias (general, mercados, forex, acciones, cripto, economia) -> URL del feed RSS.
FEEDS: dict[str, str] = dict(_D["feeds"])

# Texto de aviso legal/informativo que se adjunta a cada respuesta de noticias.
AVISO_FUENTE = _D["aviso_fuente"]

# Cabeceras HTTP enviadas en cada petición (p. ej. User-Agent) para que el sitio acepte la consulta.
CABECERAS = dict(_D["headers"])


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
