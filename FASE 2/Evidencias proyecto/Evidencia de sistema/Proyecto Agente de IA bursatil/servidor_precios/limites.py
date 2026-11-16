# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara limites .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
limites.py
----------
Límites de tamaño, tiempo, concurrencia y frecuencia del servidor de datos, validación de las órdenes y errores neutros (V04 de la auditoría).

  * TAMAÑO: un POST no puede declarar más de MAX_CUERPO_POST bytes (413).
  * TIEMPO: cada conexión tiene un tiempo máximo de espera por lectura o escritura (TIEMPO_ESPERA_CONEXION).
  * CONCURRENCIA: tope de conexiones abiertas a la vez en todo el servidor y de streams en vivo por cuenta (429 / 503).
  * FRECUENCIA: máximo de peticiones por minuto y por cuenta, separado para lecturas y para órdenes (429).
  * VALIDACIÓN: tipos, rangos y valores finitos de cada orden ANTES de llamar al bróker (400).
  * ERRORES NEUTROS: al cliente solo llega un mensaje genérico con un ID de correlación; el detalle de la excepción queda en el registro del servidor.
  * AUDITORÍA: cada acción de trading deja una línea (actor, cuenta, operación, resultado, ID) sin tokens ni cuerpos de petición.

Este módulo no importa nada del bróker ni de Streamlit, así se prueba por separado.
"""
import json
import math
import re
import threading
import time
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path

# Tamaño máximo declarado de un POST (las órdenes reales pesan menos de 1 KB).
MAX_CUERPO_POST = 16 * 1024
# Segundos que una conexión puede quedar sin leer o escribir antes de cortarse (frena conexiones lentas).
TIEMPO_ESPERA_CONEXION = 30
# Conexiones abiertas a la vez en todo el servidor (cada una usa un hilo; un SSE ocupa una durante toda su vida).
MAX_CONEXIONES = 150
# Streams de precios en vivo simultáneos por cuenta (un navegador necesita uno por pestaña).
MAX_STREAMS_POR_CUENTA = 6
# Peticiones por minuto y por cuenta: lecturas (velas, ticks, símbolos) y órdenes (POST).
LECTURAS_POR_MINUTO = 600
ORDENES_POR_MINUTO = 30
# Velas máximas que se pueden pedir de una vez.
MAX_VELAS = 5000
# Volumen máximo de una orden (lotes o unidades); valores mayores son un error de tipeo o un abuso.
MAX_VOLUMEN = 1000

TEMPORALIDADES = {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"}
_SIMBOLO = re.compile(r"^[A-Za-z0-9._#&/ -]{1,40}$")
_TIPO_ORDEN = re.compile(r"^[A-Za-z_ ]{1,20}$")

# Archivo con las acciones de trading (una línea JSON por acción).
RUTA_AUDITORIA = Path(__file__).resolve().parent.parent / "data" / "auditoria_trading.jsonl"
_CANDADO_AUDITORIA = threading.Lock()

MENSAJE_SOLICITUD_INVALIDA = "Solicitud no válida."
MENSAJE_ERROR_INTERNO = "No se pudo completar la solicitud."
MENSAJE_DEMASIADAS = "Demasiadas solicitudes: espera un momento e inténtalo de nuevo."
MENSAJE_CUERPO_GRANDE = "La solicitud es demasiado grande."


class ErrorSolicitud(Exception):
    """Solicitud mal formada o fuera de rango; el detalle es para el registro del servidor, nunca para el cliente."""


# TITULO ID DE CORRELACION

def nuevo_id() -> str:
    """ID corto que une lo que ve el cliente con lo que queda en el registro del servidor."""
    return uuid.uuid4().hex[:12]


def mensaje_con_id(mensaje: str, id_correlacion: str) -> str:
    """Mensaje neutro para el cliente con el ID que se puede citar al pedir ayuda."""
    return f"{mensaje} Código: {id_correlacion}"


# TITULO FRECUENCIA

class Frecuencia:
    """Cuenta peticiones en una ventana deslizante por cuenta y categoría; `permitir()` dice si todavía se puede."""

    def __init__(self, ventana_s: int = 60):
        """Crea el contador con una ventana de `ventana_s` segundos."""
        self._ventana = ventana_s
        self._registros: dict = {}
        self._candado = threading.Lock()
        self._ultima_limpieza = time.monotonic()

    def permitir(self, clave, categoria: str, limite: int) -> bool:
        """Registra una petición de `clave` en `categoria` y devuelve True si no supera `limite` dentro de la ventana; si la supera NO la cuenta y devuelve False."""
        ahora = time.monotonic()
        with self._candado:
            if ahora - self._ultima_limpieza > self._ventana * 5:
                self._limpiar(ahora)
            cola = self._registros.setdefault((clave, categoria), deque())
            while cola and ahora - cola[0] > self._ventana:
                cola.popleft()
            if len(cola) >= limite:
                return False
            cola.append(ahora)
            return True

    def _limpiar(self, ahora: float) -> None:
        """Descarta las cuentas sin actividad reciente para que el contador no crezca sin fin."""
        self._ultima_limpieza = ahora
        for llave in [k for k, c in self._registros.items() if not c or ahora - c[-1] > self._ventana]:
            del self._registros[llave]


# TITULO STREAMS ABIERTOS

class StreamsAbiertos:
    """Cuenta los streams en vivo abiertos por cuenta."""

    def __init__(self):
        """Crea el contador vacío."""
        self._cuentas: dict = {}
        self._candado = threading.Lock()

    def entrar(self, clave, maximo: int) -> bool:
        """Registra un stream nuevo de `clave`; devuelve False (sin registrar) si ya tiene `maximo`."""
        with self._candado:
            actual = self._cuentas.get(clave, 0)
            if actual >= maximo:
                return False
            self._cuentas[clave] = actual + 1
            return True

    def salir(self, clave) -> None:
        """Quita un stream de `clave` al cerrarse."""
        with self._candado:
            actual = self._cuentas.get(clave, 0) - 1
            if actual > 0:
                self._cuentas[clave] = actual
            else:
                self._cuentas.pop(clave, None)


# TITULO VALIDAR

def _numero(valor, nombre: str, minimo_exclusivo: float | None = None, minimo: float | None = None, maximo: float | None = None):
    """Devuelve `valor` como float si es un número finito dentro del rango; si no, lanza ErrorSolicitud. Un booleano o un texto no son números."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErrorSolicitud(f"{nombre}: no es un número")
    numero = float(valor)
    if not math.isfinite(numero):
        raise ErrorSolicitud(f"{nombre}: no es finito")
    if minimo_exclusivo is not None and not numero > minimo_exclusivo:
        raise ErrorSolicitud(f"{nombre}: fuera de rango")
    if minimo is not None and numero < minimo:
        raise ErrorSolicitud(f"{nombre}: fuera de rango")
    if maximo is not None and numero > maximo:
        raise ErrorSolicitud(f"{nombre}: fuera de rango")
    return numero


def _numero_opcional(valor, nombre: str, minimo: float = 0.0):
    """Como `_numero`, pero None es válido (campo no enviado)."""
    return None if valor is None else _numero(valor, nombre, minimo=minimo)


def _ticket(valor):
    """Valida que el ticket sea un entero o un texto corto sin caracteres raros (dealId de Capital.com)."""
    if isinstance(valor, bool) or not isinstance(valor, (int, str)):
        raise ErrorSolicitud("ticket: tipo no válido")
    texto = str(valor).strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", texto):
        raise ErrorSolicitud("ticket: formato no válido")
    return valor


def simbolo_valido(valor) -> str:
    """Devuelve el símbolo si es un texto corto con caracteres de instrumento; si no, lanza ErrorSolicitud."""
    if not isinstance(valor, str) or not _SIMBOLO.match(valor):
        raise ErrorSolicitud("symbol: formato no válido")
    return valor


def _fecha_opcional(valor, nombre: str):
    """Caducidad o expiración: None, un número o un texto corto."""
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(valor, (int, float, str)):
        raise ErrorSolicitud(f"{nombre}: tipo no válido")
    if isinstance(valor, str) and len(valor) > 40:
        raise ErrorSolicitud(f"{nombre}: demasiado largo")
    if isinstance(valor, float) and not math.isfinite(valor):
        raise ErrorSolicitud(f"{nombre}: no es finito")
    return valor


def validar_orden(ruta: str, datos) -> dict:
    """Valida el cuerpo de un POST de trading según su ruta y devuelve los valores ya limpios; lanza ErrorSolicitud si algo no cuadra.

    Rutas: sltp, orden, orden/modificar, orden/eliminar y mercado. Se llama ANTES de tocar el bróker."""
    if not isinstance(datos, dict):
        raise ErrorSolicitud("el cuerpo no es un objeto JSON")
    if ruta == "sltp":
        return {"ticket": _ticket(datos.get("ticket")), "sl": _numero_opcional(datos.get("sl"), "sl"), "tp": _numero_opcional(datos.get("tp"), "tp")}
    if ruta == "orden":
        tipo = datos.get("lado")
        if not isinstance(tipo, str) or not _TIPO_ORDEN.match(tipo):
            raise ErrorSolicitud("lado: no válido")
        return {"symbol": simbolo_valido(datos.get("symbol")), "lado": tipo,
                "volumen": _numero(datos.get("volumen"), "volumen", minimo_exclusivo=0, maximo=MAX_VOLUMEN),
                "precio": _numero(datos.get("precio"), "precio", minimo_exclusivo=0)}
    if ruta == "orden/modificar":
        return {"ticket": _ticket(datos.get("ticket")), "precio": _numero_opcional(datos.get("precio"), "precio"),
                "sl": _numero_opcional(datos.get("sl"), "sl"), "tp": _numero_opcional(datos.get("tp"), "tp"),
                "caducidad": _fecha_opcional(datos.get("caducidad"), "caducidad"), "expiracion": _fecha_opcional(datos.get("expiracion"), "expiracion")}
    if ruta == "orden/eliminar":
        return {"ticket": _ticket(datos.get("ticket"))}
    if ruta == "mercado":
        lado = datos.get("lado")
        if not isinstance(lado, str) or lado.upper() not in ("BUY", "SELL"):
            raise ErrorSolicitud("lado: no válido")
        return {"symbol": simbolo_valido(datos.get("symbol")), "lado": lado.upper(),
                "volumen": _numero(datos.get("volumen"), "volumen", minimo_exclusivo=0, maximo=MAX_VOLUMEN)}
    raise ErrorSolicitud("ruta desconocida")


# TITULO AUDITORIA

def auditar(id_correlacion: str, actor: str, ruta: str, resultado: str, simbolo: str | None = None, lado: str | None = None, volumen: float | None = None) -> None:
    """Agrega una línea al archivo de auditoría: cuándo, quién, qué operación y cómo terminó. Nunca guarda tokens ni el cuerpo de la petición; un fallo al escribir no tumba la petición."""
    linea = {"cuando": datetime.now().isoformat(timespec="seconds"), "id": id_correlacion, "actor": actor, "ruta": ruta, "resultado": resultado}
    if simbolo:
        linea["simbolo"] = simbolo
    if lado:
        linea["lado"] = lado
    if volumen is not None:
        linea["volumen"] = volumen
    try:
        with _CANDADO_AUDITORIA:
            RUTA_AUDITORIA.parent.mkdir(exist_ok=True)
            with open(RUTA_AUDITORIA, "a", encoding="utf-8") as archivo:
                archivo.write(json.dumps(linea, ensure_ascii=False) + "\n")
    except OSError as error:
        print(f"[servidor] no se pudo escribir la auditoría: {error}")


def texto_actor(clave) -> str:
    """Texto del actor para la auditoría: `u<id>:demo|real` en multiusuario o `legado`."""
    if len(clave) == 2:
        return f"u{clave[0]}:{'demo' if clave[1] else 'real'}"
    return str(clave[0])


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara limites .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
