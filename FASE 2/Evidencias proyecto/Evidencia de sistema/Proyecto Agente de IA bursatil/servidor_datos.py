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

Ejecutar en una terminal APARTE, además del `streamlit run aplicacion.py`:
    env\\Scripts\\python servidor_datos.py
"""
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
