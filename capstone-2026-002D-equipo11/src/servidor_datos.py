# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara servidor_datos .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""
servidor_datos.py
-----------------
Lanzador del servidor de datos de MetaTrader 5 (precios en vivo por SSE, velas y órdenes del gráfico).
El código vive en el paquete `servidor_precios/`.

Ejecutar en una terminal APARTE, además del `streamlit run src/app.py`:
    env\\Scripts\\python src/servidor_datos.py
"""
import os
import sys

# Deja src/ (paquetes del proyecto) y la raíz (carpeta database/) en la ruta de importación.
_src = os.path.abspath(os.path.dirname(__file__))
_raiz = os.path.dirname(_src)
for _ruta in (_raiz, _src):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

from servidor_precios import ejecutar

# Solo arranca el servidor cuando el archivo se ejecuta directamente, no cuando otro módulo lo importa.
if __name__ == "__main__":
    ejecutar()


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara servidor_datos .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
