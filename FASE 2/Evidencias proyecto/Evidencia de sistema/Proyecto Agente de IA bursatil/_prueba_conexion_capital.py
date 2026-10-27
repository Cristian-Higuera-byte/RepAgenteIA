# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------- INICIO Piña y Jara _prueba_conexion_capital .PY ---------------------------
# -------------------------------------------------------------------------------------------------------

"""
_prueba_conexion_capital.py  —  16-10-2026
---------------------------------------------------------------
Prueba RÁPIDA de la API REST de Capital.com, ANTES de construir el
backend completo. No toca nada del dashboard: solo verifica tres cosas
de una sola vez:

  1. Que tus credenciales del .env son correctas (abre una sesión).
  2. Que la API es alcanzable y entrega datos de tu cuenta (saldo).
  3. Que el certificado SSL funciona desde esta carpeta con tildes
     ("análisis bursátiles"), que es justo donde yfinance fallaba
     (curl error 77). Por eso fijamos el CA bundle de certifi a mano.

CÓMO USARLO:
  1. Completa en el .env: CAPITAL_API_KEY, CAPITAL_IDENTIFIER y
     CAPITAL_API_PASSWORD (y CAPITAL_DEMO=true).
  2. Ejecuta desde el entorno del proyecto:
        python _prueba_conexion_capital.py
"""

import os
import sys

import certifi
import requests
from dotenv import load_dotenv

# La consola de Windows (cp1252) no imprime tildes/acentos sin esto.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- Fix SSL para la ruta con tildes (mismo problema que tuvimos con yfinance) ---
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

ES_DEMO = os.getenv("CAPITAL_DEMO", "true").strip().lower() in ("true", "1", "si", "sí")
BASE = ("https://demo-api-capital.backend-capital.com" if ES_DEMO
        else "https://api-capital.backend-capital.com") + "/api/v1"

API_KEY = os.getenv("CAPITAL_API_KEY", "").strip()
IDENTIFIER = os.getenv("CAPITAL_IDENTIFIER", "").strip()
API_CONTRASENA = os.getenv("CAPITAL_API_PASSWORD", "").strip()


# TITULO ABORTAR

def _abortar(mensaje: str):
    """Muestra el mensaje de error de la prueba de conexión y termina el programa con código 1."""
    print(f"\n[ERROR] {mensaje}")
    sys.exit(1)


# TITULO ABRIR SESION

def abrir_sesion() -> dict:
    """POST /session -> devuelve los tokens de sesión (CST y X-SECURITY-TOKEN)."""
    if not (API_KEY and IDENTIFIER and API_CONTRASENA):
        _abortar("Faltan credenciales en el .env "
                 "(CAPITAL_API_KEY / CAPITAL_IDENTIFIER / CAPITAL_API_PASSWORD).")

    print(f"Entorno: {'DEMO' if ES_DEMO else 'REAL'}  ->  {BASE}")
    print("Abriendo sesión...")
    try:
        r = requests.post(
            f"{BASE}/session",
            headers={"X-CAP-API-KEY": API_KEY, "Content-Type": "application/json"},
            json={"identifier": IDENTIFIER, "password": API_CONTRASENA,
                  "encryptedPassword": False},
            timeout=15,
        )
    except requests.exceptions.SSLError as e:
        _abortar(f"Error SSL (el fix de certifi no bastó): {e}")
    except requests.exceptions.RequestException as e:
        _abortar(f"No se pudo contactar a Capital.com: {e}")

    if r.status_code != 200:
        _abortar(f"La sesión falló (HTTP {r.status_code}): {r.text}\n"
                 "   Revisa la API key, el correo (identifier) y la contraseña "
                 "de la key. Recuerda que la key exige 2FA activado.")

    tokens = {"CST": r.headers.get("CST", ""),
              "X-SECURITY-TOKEN": r.headers.get("X-SECURITY-TOKEN", "")}
    print("[OK] Sesión abierta correctamente.")
    return tokens


# TITULO VER CUENTA

def ver_cuenta(tokens: dict):
    """GET /accounts -> saldo y disponible de la cuenta."""
    print("\nConsultando cuenta...")
    r = requests.get(f"{BASE}/accounts", headers=tokens, timeout=15)
    if r.status_code != 200:
        _abortar(f"No se pudo leer la cuenta (HTTP {r.status_code}): {r.text}")
    for cta in r.json().get("accounts", []):
        bal = cta.get("balance", {})
        activa = "  <- activa" if cta.get("preferred") else ""
        print(f"   - {cta.get('accountName')} ({cta.get('currency')}): "
              f"saldo={bal.get('balance')}  disponible={bal.get('available')}  "
              f"P/G={bal.get('profitLoss')}{activa}")


# TITULO VER PRECIO ORO

def ver_precio_oro(tokens: dict):
    """GET /markets?searchTerm=Gold -> precio Bid/Offer del oro (como prueba)."""
    print("\nBuscando el precio del oro...")
    r = requests.get(f"{BASE}/markets", headers=tokens,
                     params={"searchTerm": "Gold"}, timeout=15)
    if r.status_code != 200:
        _abortar(f"No se pudo buscar mercados (HTTP {r.status_code}): {r.text}")
    mercados = r.json().get("markets", [])
    if not mercados:
        print("   (no se encontró 'Gold'; la búsqueda respondió vacío)")
        return
    m = mercados[0]
    print(f"   - {m.get('instrumentName')}  epic={m.get('epic')}  "
          f"Bid={m.get('bid')}  Offer={m.get('offer')}  estado={m.get('marketStatus')}")
    print("\n   (El 'epic' es el identificador que usará el backend para pedir "
          "precios y enviar órdenes de este instrumento.)")


if __name__ == "__main__":
    print("=" * 60)
    print("  PRUEBA DE CONEXIÓN — Capital.com API REST")
    print("=" * 60)
    tokens = abrir_sesion()
    ver_cuenta(tokens)
    ver_precio_oro(tokens)
    print("\n[OK] Todo funcionó. La API de Capital.com responde bien desde aquí.")
    print("   Siguiente paso: construir el backend herramientas/backends/capital.py")


# -------------------------------------------------------------------------------------------------------
# ----------------------------- FIN Piña y Jara _prueba_conexion_capital .PY ----------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
