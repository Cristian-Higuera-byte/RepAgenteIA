# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara manejador .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Rutas HTTP del servidor: GET (velas, ticks, símbolos, salud), SSE (/stream) y POST (SL/TP y órdenes).

Define `Manejador`, el BaseHTTPRequestHandler que usa ejecucion.py. Los GET solo leen datos
del motor o de MT5; los POST modifican posiciones/órdenes y solo se aceptan desde páginas
de localhost (protección CORS/Origin) y bajo CANDADO_MT5.
"""
import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote, urlparse

from tools.puente_mt5 import (colocar_orden_pendiente, ejecutar_orden_mercado, eliminar_orden,
                                     modificar_orden, modificar_sltp)

from .constantes import CANDADO_MT5, PING_SSE, VERSION_API
from .motor import MOTOR
from .simbolos import listar_simbolos
from .velas import obtener_velas


def _lista_simbolos(qs) -> list:
    """Extrae del query string el parámetro `s` (símbolos separados por comas).

    Recibe el dict de parse_qs y devuelve una lista sin vacíos ni espacios, limitada a 80
    símbolos para acotar la carga del motor.
    """
    crudo = qs.get("s", [""])[0]
    return [s for s in (x.strip() for x in crudo.split(",")) if s][:80]


class Manejador(BaseHTTPRequestHandler):
    """Atiende las peticiones HTTP del dashboard: JSON, SSE, CORS restringido a localhost y POST de trading.

    Una instancia por petición (ThreadingHTTPServer). Delega los datos en vivo en MOTOR.
    """

    # HTTP/1.1 es necesario para mantener abierta la conexión del flujo SSE
    protocol_version = "HTTP/1.1"

    def _origen_permitido(self):
        """El Origin de la petición si es una página de este equipo (el dashboard en localhost); si no, None."""
        origen = self.headers.get("Origin", "") or ""
        host = urlparse(origen).hostname
        return origen if host in ("localhost", "127.0.0.1") else None

    def _cabecera_cors(self):
        """CORS solo para el dashboard local: otra web abierta en el navegador no puede leer
        saldo, equidad ni posiciones de esta API."""
        origen = self._origen_permitido()
        if origen:
            self.send_header("Access-Control-Allow-Origin", origen)
            self.send_header("Vary", "Origin")

    def _responder(self, obj):
        """Envía `obj` serializado como JSON con estado 200 y cabecera CORS (si el origen es local)."""
        # Serializa a bytes UTF-8 para calcular Content-Length exacto
        cuerpo = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self._cabecera_cors()   # permite el fetch desde el iframe del gráfico (solo localhost)
        self.end_headers()
        self.wfile.write(cuerpo)

    def _stream(self, simbolos):
        """SSE: envía la foto completa y luego solo los cambios, hasta que el
        navegador cierre la conexión.

        Recibe la lista de símbolos a seguir. Registra la suscripción en el motor, y en bucle
        espera cambios (MOTOR.esperar), envía eventos `data:` con ticks ("t") y cuenta ("acc"),
        o un comentario `: ping` de keep-alive cada PING_SSE segundos. Termina silenciosamente
        cuando el cliente se desconecta.
        """
        # Cabeceras estándar de un flujo Server-Sent Events
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cabecera_cors()
        self.end_headers()
        # Suscribe los símbolos para que el motor empiece a leerlos
        MOTOR.suscribir(simbolos)
        # seq = último cambio ya enviado a este cliente
        seq = 0
        ultimo_envio = time.time()
        try:
            # Indica al navegador reconectar a los 2 s si se corta
            self.wfile.write(b"retry: 2000\n\n")
            while True:
                # Solo lo que cambió desde la última secuencia enviada
                nuevo, ticks, cuenta = MOTOR.foto(simbolos, seq)
                seq = nuevo
                # Hay novedades: las envía; si no, emite ping si pasó mucho tiempo
                if ticks or cuenta:
                    msg = {"t": ticks}
                    if cuenta:
                        msg["acc"] = cuenta
                    self.wfile.write(b"data: " + json.dumps(msg).encode("utf-8") + b"\n\n")
                    self.wfile.flush()
                    ultimo_envio = time.time()
                elif time.time() - ultimo_envio >= PING_SSE:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    ultimo_envio = time.time()
                MOTOR.suscribir(simbolos)          # mantiene viva la suscripción
                MOTOR.esperar(seq, timeout=PING_SSE)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass   # el navegador cerró la pestaña o cambió de vista

    def do_GET(self):
        """Enruta las peticiones GET: /stream, /ticks, /simbolos, /salud, /velas/<s> y /ultima/<s>.

        Los errores se devuelven como JSON {"error": ...}; las rutas desconocidas también.
        """
        # Separa ruta (por tramos) y parámetros de consulta; tf por defecto H1
        parsed = urlparse(self.path)
        partes = [unquote(p) for p in parsed.path.strip("/").split("/")]
        qs = parse_qs(parsed.query)
        tf = qs.get("tf", ["H1"])[0]
        try:
            if partes and partes[0] == "stream":
                self._stream(_lista_simbolos(qs))
            elif partes and partes[0] == "ticks":
                simbolos = _lista_simbolos(qs)
                MOTOR.suscribir(simbolos)
                _, ticks, cuenta = MOTOR.foto(simbolos, 0)
                self._responder({"t": ticks, "acc": cuenta})
            elif partes and partes[0] == "simbolos":
                self._responder(listar_simbolos())
            elif partes and partes[0] == "salud":
                self._responder({"ok": True, "v": VERSION_API})
            elif len(partes) >= 2 and partes[0] == "velas":
                n = int(qs.get("n", ["150"])[0])
                self._responder(obtener_velas(partes[1], tf, n))
            elif len(partes) >= 2 and partes[0] == "ultima":
                velas = obtener_velas(partes[1], tf, 2)
                self._responder(velas[-1] if velas else {})
            else:
                self._responder({"error": "ruta no reconocida"})
        except Exception as e:
            try:
                self._responder({"error": str(e)})
            except Exception:
                pass

    # --- Modificaciones (POST) ----------------------------------------------
    def _origen_local(self) -> bool:
        """Devuelve True si el encabezado Origin pertenece a localhost o 127.0.0.1 (autoriza los POST).

        Solo páginas servidas desde este equipo (el dashboard en localhost) pueden
        modificar posiciones: otra web abierta en el navegador no puede."""
        host = urlparse(self.headers.get("Origin", "") or "").hostname
        return host in ("localhost", "127.0.0.1")

    def do_OPTIONS(self):
        """Responde la verificación previa (preflight) de CORS con 204 y los métodos/cabeceras permitidos."""
        self.send_response(204)
        self._cabecera_cors()
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        """Enruta las órdenes de trading: /sltp, /orden, /orden/modificar, /orden/eliminar y /mercado.

        Rechaza con 403 los orígenes que no sean locales. Lee el cuerpo JSON, ejecuta la
        operación en MT5 bajo CANDADO_MT5 mediante herramientas.puente_mt5 y responde con el
        resultado (o {"error": ...}). Efecto: modifica posiciones u órdenes reales en MT5.
        """
        # Bloquea peticiones de páginas externas (CSRF)
        if not self._origen_local():
            cuerpo = b'{"error": "origen no permitido"}'
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
            return
        try:
            # Lee y decodifica el cuerpo JSON según Content-Length
            n = int(self.headers.get("Content-Length", 0) or 0)
            datos = json.loads(self.rfile.read(n) or b"{}")
            ruta = urlparse(self.path).path.strip("/")
            with CANDADO_MT5:   # mismo candado que el motor: la API de MT5 no es thread-safe
                if ruta == "sltp":
                    res = modificar_sltp(int(datos["ticket"]), datos.get("sl"), datos.get("tp"))
                elif ruta == "orden":
                    res = colocar_orden_pendiente(datos["symbol"], datos["lado"],
                                                  float(datos["volumen"]), float(datos["precio"]))
                elif ruta == "orden/modificar":
                    res = modificar_orden(int(datos["ticket"]), datos.get("precio"),
                                          datos.get("sl"), datos.get("tp"),
                                          datos.get("caducidad"), datos.get("expiracion"))
                elif ruta == "orden/eliminar":
                    res = eliminar_orden(int(datos["ticket"]))
                elif ruta == "mercado":
                    lado = str(datos.get("lado", "")).upper()
                    vol = float(datos["volumen"])
                    if lado not in ("BUY", "SELL") or not vol > 0:
                        res = {"error": "Orden a mercado no válida (lado o volumen)"}
                    else:
                        res = ejecutar_orden_mercado(str(datos["symbol"]), lado, vol)
                else:
                    res = None
            if res is not None:
                self._responder(res)
            else:
                self._responder({"error": "ruta no reconocida"})
        except Exception as e:
            try:
                self._responder({"error": str(e)})
            except Exception:
                pass

    def log_message(self, *args):
        """Anula el registro de accesos del servidor base para no saturar la consola."""
        pass  # silencia los logs de acceso en consola


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara manejador .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
