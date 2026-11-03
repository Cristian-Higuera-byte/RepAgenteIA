# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara _descubrir_capital .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""
_descubrir_capital.py  — SOLO LECTURA. Vuelca la forma real de las respuestas
de Capital.com para construir el backend sin adivinar nombres de campos.
No envía ninguna orden. Desechable.
"""
import json
import os
import sys
import time

import certifi
import requests
from dotenv import load_dotenv

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
load_dotenv()

BASE = "https://demo-api-capital.backend-capital.com/api/v1"
API_KEY = os.getenv("CAPITAL_API_KEY", "").strip()
IDENT = os.getenv("CAPITAL_IDENTIFIER", "").strip()
PWD = os.getenv("CAPITAL_API_PASSWORD", "").strip()

r = requests.post(f"{BASE}/session",
                  headers={"X-CAP-API-KEY": API_KEY, "Content-Type": "application/json"},
                  json={"identifier": IDENT, "password": PWD, "encryptedPassword": False},
                  timeout=15)
r.raise_for_status()
H = {"CST": r.headers["CST"], "X-SECURITY-TOKEN": r.headers["X-SECURITY-TOKEN"]}


# TITULO DUMP

def dump(titulo, metodo, ruta, parametros=None, limite=2500):
    """Imprime la respuesta de un endpoint de Capital.com para explorarlo: título, método, ruta y los primeros caracteres del JSON.

    Recibe el título, el método HTTP, la ruta, los parámetros opcionales y el límite de caracteres a mostrar.
    """
    print("\n" + "=" * 70)
    print(f"### {titulo}   [{metodo} {ruta}]")
    print("=" * 70)
    try:
        resp = requests.request(metodo, f"{BASE}{ruta}", headers=H, params=parametros, timeout=15)
        print(f"HTTP {resp.status_code}")
        try:
            data = resp.json()
        except Exception:
            print(resp.text[:limite]); return
        texto = json.dumps(data, indent=2, ensure_ascii=False)
        print(texto[:limite] + ("\n...(recortado)" if len(texto) > limite else ""))
    except Exception as e:
        print(f"ERROR: {e}")
    time.sleep(0.4)  # respeta rate limit


dump("CUENTAS", "GET", "/accounts")
dump("ESPECS INSTRUMENTO (oro)", "GET", "/markets/GOLD")
dump("BUSCAR US30", "GET", "/markets", {"searchTerm": "US30"})
dump("PRECIOS/VELAS (oro, 1h, 3)", "GET", "/prices/GOLD", {"resolution": "HOUR", "max": 3})
dump("POSICIONES ABIERTAS", "GET", "/positions")
dump("ORDENES PENDIENTES", "GET", "/workingorders")
dump("HISTORIAL TRANSACCIONES", "GET", "/history/transactions", {"lastPeriod": 86400})
dump("HISTORIAL ACTIVIDAD", "GET", "/history/activity", {"lastPeriod": 86400})
dump("RESOLUCIONES/CLIENT INFO (session)", "GET", "/session")
print("\n[FIN] Volcado de solo lectura completo.")


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara _descubrir_capital .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
