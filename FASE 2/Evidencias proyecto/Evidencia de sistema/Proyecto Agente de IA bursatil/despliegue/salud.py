# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara salud .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
salud.py
--------
Comprobación de salud del contenedor (HEALTHCHECK del Dockerfile): consulta el dashboard y el servidor de precios y sale con
código 0 si ambos responden, o con 1 si alguno no lo hace.

Se ejecuta con:  python despliegue/salud.py
"""
import os
import sys
import urllib.request

# Direcciones de comprobación dentro del contenedor: (nombre, URL).
COMPROBACIONES = (
    ("dashboard", f"http://127.0.0.1:{os.environ.get('PUERTO_DASHBOARD', '8501')}/_stcore/health"),
    ("servidor de precios", "http://127.0.0.1:8000/salud"),
)


# TITULO RESPONDE

def responde(url: str) -> bool:
    """True si la dirección responde con código 200 en menos de 4 segundos."""
    try:
        with urllib.request.urlopen(url, timeout=4) as respuesta:
            return respuesta.status == 200
    except Exception:
        return False


if __name__ == "__main__":
    fallos = [nombre for nombre, url in COMPROBACIONES if not responde(url)]
    if fallos:
        print("Sin respuesta: " + ", ".join(fallos), file=sys.stderr)
        sys.exit(1)
    print("Plataforma operativa")


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara salud .PY ---------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
