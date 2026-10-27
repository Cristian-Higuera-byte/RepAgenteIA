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
del motor o del broker; los POST modifican posiciones/órdenes y solo se aceptan desde páginas
de los orígenes permitidos (protección CORS/Origin) y bajo CANDADO_MT5.

MULTIUSUARIO: con `CAPITAL_MULTIUSUARIO` encendido cada petición debe traer el token firmado del usuario dentro de la
dirección (`/t/<token>/stream?...`, ver herramientas/token_datos.py); sin token válido responde 401 (salvo /salud).
El token dice quién es el usuario y con qué cuenta (demo o real) opera: la petición entera se ejecuta con la sesión de
Capital.com, el motor y las carpetas de datos de ESA cuenta, nunca con las de otra.
"""
import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote, urlparse

from herramientas import token_datos
from herramientas.backends import sesiones_capital
from herramientas.puente_mt5 import (colocar_orden_pendiente, ejecutar_orden_mercado, eliminar_orden,
                                     modificar_orden, modificar_sltp)

from herramientas.tickets import ticket as _tk
from .constantes import CANDADO_MT5, HOSTS_PERMITIDOS, PING_SSE, VERSION_API
from .motor import MOTORES
from .simbolos import listar_simbolos
from .velas import obtener_ultima, obtener_velas, precalentar


# TITULO LISTA SIMBOLOS

def _lista_simbolos(qs) -> list:
    """Extrae del query string el parámetro `s` (símbolos separados por comas).

    Recibe el dict de parse_qs y devuelve una lista sin vacíos ni espacios, limitada a 80
    símbolos para acotar la carga del motor.
    """
    crudo = qs.get("s", [""])[0]
    return [s for s in (x.strip() for x in crudo.split(",")) if s][:80]


# TITULO MANEJADOR

class Manejador(BaseHTTPRequestHandler):
    """Atiende las peticiones HTTP del dashboard: JSON, SSE, CORS restringido a localhost y POST de trading.

    Una instancia por petición (ThreadingHTTPServer). Delega los datos en vivo en el motor de la cuenta del usuario.
    """

    # HTTP/1.1 es necesario para mantener abierta la conexión del flujo SSE
    protocol_version = "HTTP/1.1"

    # TITULO ORIGEN PERMITIDO

    def _origen_permitido(self):
        """El Origin de la petición si es una página permitida (el dashboard en localhost o los dominios de SERVIDOR_ORIGENES); si no, None."""
        origen = self.headers.get("Origin", "") or ""
        host = urlparse(origen).hostname
        return origen if host in HOSTS_PERMITIDOS else None

    # TITULO CABECERA CORS

    def _cabecera_cors(self):
        """CORS solo para el dashboard (local o de los dominios permitidos): otra web abierta en el navegador
        no puede leer saldo, equidad ni posiciones de esta API."""
        origen = self._origen_permitido()
        if origen:
            self.send_header("Access-Control-Allow-Origin", origen)
            self.send_header("Vary", "Origin")

    # TITULO RESPONDER

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

    # TITULO RECHAZAR

    def _rechazar(self, codigo, mensaje):
        """Responde un error HTTP (por ejemplo 401) con cuerpo JSON {"error": mensaje} y cabecera CORS."""
        cuerpo = json.dumps({"error": mensaje}).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self._cabecera_cors()
        self.end_headers()
        self.wfile.write(cuerpo)

    # TITULO IDENTIFICAR

    def _identificar(self):
        """Averigua de qué cuenta es la petición y deja `self.path` sin el prefijo del token.

        La dirección puede venir como `/t/<token>/ruta`. Con el modo multiusuario apagado devuelve la cuenta del .env
        ("legado",). Encendido, devuelve (usuario_id, es_demo) si el token es auténtico y vigente; si no, responde 401
        y devuelve None (quien llama debe terminar). `/salud` es pública."""
        analizada = urlparse(self.path)
        partes = analizada.path.split("/")
        token = ""
        if len(partes) >= 3 and partes[1] == "t":
            token = unquote(partes[2])
            self.path = "/" + "/".join(partes[3:]) + (("?" + analizada.query) if analizada.query else "")
        if not sesiones_capital.MULTIUSUARIO:
            return ("legado",)
        if urlparse(self.path).path.strip("/") == "salud":
            return ("anonimo",)
        identidad = token_datos.verificar(token) if token else None
        if identidad is None:
            self._rechazar(401, "no autorizado")
            return None
        return identidad

    # TITULO STREAM

    def _stream(self, simbolos, motor, clave):
        """SSE: envía la foto completa y luego solo los cambios, hasta que el
        navegador cierre la conexión.

        Recibe la lista de símbolos a seguir. Registra la suscripción en el motor, y en bucle
        espera cambios (motor.esperar), envía eventos `data:` con ticks ("t") y cuenta ("acc"),
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
        motor.suscribir(simbolos)
        # seq = último cambio ya enviado a este cliente
        seq = 0
        ultimo_envio = time.time()
        try:
            # Indica al navegador reconectar a los 2 s si se corta
            self.wfile.write(b"retry: 2000\n\n")
            while not motor._detenido:     # si el motor se apagó, se corta: el navegador reconecta y recibe uno nuevo
                # Solo lo que cambió desde la última secuencia enviada
                nuevo, ticks, cuenta = motor.foto(simbolos, seq)
                seq = nuevo
                # Hay novedades: las envía; si no, emite ping si pasó mucho tiempo
                if ticks or cuenta:
                    mensaje = {"t": ticks}
                    if cuenta:
                        mensaje["acc"] = cuenta
                    self.wfile.write(b"data: " + json.dumps(mensaje).encode("utf-8") + b"\n\n")
                    self.wfile.flush()
                    ultimo_envio = time.time()
                elif time.time() - ultimo_envio >= PING_SSE:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    ultimo_envio = time.time()
                motor.suscribir(simbolos)          # mantiene viva la suscripción
                motor.esperar(seq, tiempo_espera=PING_SSE)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass   # el navegador cerró la pestaña o cambió de vista

    # TITULO DO GET

    def do_GET(self):
        """Identifica la cuenta de la petición (token) y atiende el GET con la sesión y el motor de esa cuenta."""
        clave = self._identificar()
        if clave is None:
            return
        with sesiones_capital.con_clave(clave):
            self._atender_get(clave)

    # TITULO ATENDER GET

    def _atender_get(self, clave):
        """Enruta las peticiones GET: /stream, /ticks, /simbolos, /salud, /dom/<s>, /velas/<s> y /ultima/<s>.

        Los errores se devuelven como JSON {"error": ...}; las rutas desconocidas también.
        """
        # Separa ruta (por tramos) y parámetros de consulta; tf por defecto H1
        parsed = urlparse(self.path)
        partes = [unquote(p) for p in parsed.path.strip("/").split("/")]
        qs = parse_qs(parsed.query)
        temporalidad = qs.get("tf", ["H1"])[0]
        try:
            if partes and partes[0] == "stream":
                simbolos = _lista_simbolos(qs)
                precalentar(simbolos)          # velas de la lista de activos listas en memoria (solo Capital.com)
                self._stream(simbolos, MOTORES.de(clave), clave)
            elif partes and partes[0] == "ticks":
                simbolos = _lista_simbolos(qs)
                motor = MOTORES.de(clave)
                motor.suscribir(simbolos)
                precalentar(simbolos)
                _, ticks, cuenta = motor.foto(simbolos, 0)
                self._responder({"t": ticks, "acc": cuenta})
            elif partes and partes[0] == "simbolos":
                self._responder(listar_simbolos())
            elif partes and partes[0] == "salud":
                self._responder({"ok": True, "v": VERSION_API})
            elif len(partes) >= 2 and partes[0] == "dom":
                # Nivel 1 del libro (solo Capital.com; MT5 usa su propio libro desde Streamlit)
                from herramientas.puente_mt5 import PROVEEDOR, resolver_simbolo
                if PROVEEDOR == "capital":
                    from .streaming_capital import stream_de
                    self._responder(stream_de(clave).dom(resolver_simbolo(partes[1])))
                else:
                    self._responder({"disponible": False, "motivo": "Solo disponible con Capital.com."})
            elif len(partes) >= 2 and partes[0] == "velas":
                n = int(qs.get("n", ["150"])[0])
                self._responder(obtener_velas(partes[1], temporalidad, n))
            elif len(partes) >= 2 and partes[0] == "ultima":
                self._responder(obtener_ultima(partes[1], temporalidad))
            else:
                self._responder({"error": "ruta no reconocida"})
        except Exception as e:
            try:
                self._responder({"error": str(e)})
            except Exception:
                pass

    # TITULO ORIGEN LOCAL

    # --- Modificaciones (POST) ----------------------------------------------
    def _origen_local(self) -> bool:
        """Devuelve True si el encabezado Origin pertenece a un host permitido (localhost o SERVIDOR_ORIGENES): autoriza los POST.

        Solo las páginas de la propia plataforma pueden modificar posiciones: otra web abierta en el navegador no puede
        (y en modo multiusuario además hace falta el token del usuario)."""
        host = urlparse(self.headers.get("Origin", "") or "").hostname
        return host in HOSTS_PERMITIDOS

    # TITULO DO OPTIONS

    def do_OPTIONS(self):
        """Responde la verificación previa (preflight) de CORS con 204 y los métodos/cabeceras permitidos."""
        self.send_response(204)
        self._cabecera_cors()
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    # TITULO DO POST

    def do_POST(self):
        """Identifica la cuenta de la petición (token) y atiende el POST con la sesión de esa cuenta."""
        clave = self._identificar()
        if clave is None:
            return
        with sesiones_capital.con_clave(clave):
            self._atender_post()

    # TITULO ATENDER POST

    def _atender_post(self):
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
                    resultado = modificar_sltp(_tk(datos["ticket"]), datos.get("sl"), datos.get("tp"))
                elif ruta == "orden":
                    resultado = colocar_orden_pendiente(datos["symbol"], datos["lado"],
                                                  float(datos["volumen"]), float(datos["precio"]))
                elif ruta == "orden/modificar":
                    resultado = modificar_orden(_tk(datos["ticket"]), datos.get("precio"),
                                          datos.get("sl"), datos.get("tp"),
                                          datos.get("caducidad"), datos.get("expiracion"))
                elif ruta == "orden/eliminar":
                    resultado = eliminar_orden(_tk(datos["ticket"]))
                elif ruta == "mercado":
                    lado = str(datos.get("lado", "")).upper()
                    volumen = float(datos["volumen"])
                    if lado not in ("BUY", "SELL") or not volumen > 0:
                        resultado = {"error": "Orden a mercado no válida (lado o volumen)"}
                    else:
                        resultado = ejecutar_orden_mercado(str(datos["symbol"]), lado, volumen)
                else:
                    resultado = None
            if resultado is not None:
                self._responder(resultado)
            else:
                self._responder({"error": "ruta no reconocida"})
        except Exception as e:
            try:
                self._responder({"error": str(e)})
            except Exception:
                pass

    # TITULO LOG MESSAGE

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
