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

"""Prueba rápida (desde la raíz del proyecto):  python -m database.scripts.fuentes.investing_fuente

Ejecuta tres consultas de ejemplo contra Investing.com (noticias generales,
noticias de forex y una búsqueda por palabra clave) e imprime el resultado en
formato JSON legible. Si una consulta falla, imprime el error sin detener las
demás. Hace peticiones de red reales; no se usa en producción."""
from database.scripts.fuentes.investing_fuente import buscar_noticias, noticias

import json

# Casos de prueba: (nombre mostrado, función sin argumentos que ejecuta la consulta).
pruebas = (
    ("noticias generales", lambda: noticias("general", 3)),
    ("noticias forex", lambda: noticias("forex", 3)),
    ("buscar_noticias", lambda: buscar_noticias("inflación", "economia", 3)),
)
# Ejecuta cada prueba y muestra su resultado (o el error) por consola.
for nombre, prueba in pruebas:
    print(f"\n=== {nombre}")
    try:
        # default=str permite serializar cualquier objeto no JSON (p. ej. fechas).
        print(json.dumps(prueba(), ensure_ascii=False, indent=2, default=str))
    except Exception as e:
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
