# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara constantes .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Puerto, versión de la API, temporalidades, intervalos del motor y candado de MT5.

Centraliza los valores compartidos por manejador.py, ejecucion.py, velas.py, simbolos.py
y el paquete motor, para que se ajusten en un solo lugar.
"""
import os
import threading

from herramientas.puente_mt5 import PROVEEDOR
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

# Puerto TCP local (127.0.0.1) en el que escucha el servidor de datos
PUERTO = 8000
# Versión de la API. Se sube cuando cambian rutas o datos que usa el navegador:
# el gráfico la compara (GET /salud) y avisa si este proceso quedó desactualizado.
# 3 = órdenes pendientes con caducidad (POST /orden/modificar con "caducidad").
# 4 = stop dinámico (trailing): motor que mueve el SL + flag "tr" por posición en el feed.
# 5 = OCO (One-Cancels-the-Other): motor que cancela la pata sobrante + flag "oco" por orden.
# 6 = POST /mercado (orden a mercado desde los botones VENDER/COMPRAR del gráfico en pantalla completa).
# Versión vigente; se publica en GET /salud como "v"
VERSION_API = 6

# Temporalidades soportadas (igual que el selector del dashboard)
# Traduce el nombre de temporalidad recibido por HTTP a la constante de MT5
TF_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}

# TITULO SIN CANDADO

class _SinCandado:
    """Candado que no bloquea nunca (misma interfaz que `threading.RLock`), para el proveedor Capital.com."""

    # TITULO ENTER

    def __enter__(self):
        """Entra al bloque `with` del candado y lo devuelve."""
        return self

    # TITULO EXIT

    def __exit__(self, *exc):
        """Sale del bloque `with` del candado sin ocultar errores."""
        return False

    # TITULO ACQUIRE

    def acquire(self, *args, **kwargs):
        """Imita la toma del candado: siempre tiene éxito y nunca espera."""
        return True

    # TITULO RELEASE

    def release(self):
        """Imita la liberación del candado: no hace nada."""
        return None


# Con MT5, todas las llamadas de ESTE proceso pasan por aquí (la API no es thread-safe y el servidor atiende cada petición
# en su propio hilo); RLock reentrante: permite anidar secciones críticas en el mismo hilo.
# Con Capital.com (API REST) NO se serializa nada: un candado global hacía que cada lectura de ~300-800 ms bloqueara a las
# demás y que las velas del gráfico no llegaran mientras el motor consultaba la cuenta. Las órdenes se serializan en el
# backend (`_ORDEN_CANDADO`) y el ritmo de peticiones lo limita `capital._limitar()`.
CANDADO_MT5 = _SinCandado() if PROVEEDOR == "capital" else threading.RLock()

INTERVALO_TICKS = 0.5        # s entre refrescos de ticks (con Capital los ticks llegan por WebSocket: leer es instantáneo)
INTERVALO_CUENTA = 3.0       # s entre lecturas de saldo / P-G (sigue siendo REST)
INTERVALO_EQUITY = 60.0      # s entre snapshots de equity (para el drawdown real)
TTL_REFERENCIA = 300         # s que se reutiliza el cierre del día anterior
TTL_SUSCRIPCION = 60         # s sin clientes pidiendo un símbolo -> se deja de leer
PING_SSE = 15                # s sin cambios -> comentario keep-alive
INACTIVIDAD_MOTOR = 300      # s sin clientes ni vigilancias (stop dinámico, OCO) -> el motor de esa cuenta se apaga
# Direcciones desde las que el navegador puede hablar con el servidor (cabecera Origin). Por defecto solo este equipo;
# en producción se agregan los dominios de la plataforma en SERVIDOR_ORIGENES (separados por coma, solo el nombre del host).
HOSTS_PERMITIDOS = {"localhost", "127.0.0.1"} | {h.strip().lower() for h in os.environ.get("SERVIDOR_ORIGENES", "").split(",") if h.strip()}

TTL_SIMBOLOS = 300   # s que se reutiliza el catálogo de símbolos


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara constantes .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
