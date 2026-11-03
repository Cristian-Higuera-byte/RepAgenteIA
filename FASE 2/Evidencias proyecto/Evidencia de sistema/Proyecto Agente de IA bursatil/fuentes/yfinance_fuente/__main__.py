# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __main__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Prueba rápida (desde la raíz del proyecto):  python -m fuentes.yfinance_fuente

Ejecuta una consulta de ejemplo por cada función pública de la fuente Yahoo
Finance (búsqueda, cotización, histórico, fundamentales, estados financieros,
noticias y consenso de analistas) e imprime el resultado en JSON legible. Si una
consulta falla, imprime el error y continúa con la siguiente. Hace peticiones de
red reales; no se usa en producción."""
from fuentes.yfinance_fuente import (buscar, consenso_analistas, cotizacion, estados_financieros, fundamentales,
                                     historico, noticias)

import json

# Casos de prueba: (nombre mostrado, función sin argumentos que ejecuta la consulta).
pruebas = (
    ("buscar", lambda: buscar("apple", 3)),
    ("cotizacion", lambda: cotizacion("AAPL")),
    ("historico", lambda: historico("EURUSD=X", "1mo", ultimas_velas=3)),
    ("fundamentales", lambda: fundamentales("AAPL")),
    ("estados_financieros", lambda: estados_financieros("AAPL", "resultados", "anual", 2)),
    ("noticias", lambda: noticias("AAPL", 3)),
    ("consenso_analistas", lambda: consenso_analistas("AAPL")),
)
# Ejecuta cada prueba y muestra su resultado (o el error) por consola.
for nombre, prueba in pruebas:
    print(f"\n=== {nombre}")
    try:
        # default=str permite serializar cualquier objeto no JSON (p. ej. fechas).
        print(json.dumps(prueba(), ensure_ascii=False, indent=2, default=str))
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {type(e).__name__}: {e}")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __main__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
