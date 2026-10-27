# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara ejecucion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Arranque del servidor de datos (hilo del motor + servidor HTTP).

Lo invoca el lanzador servidor_datos.py de la raíz a través de `servidor_precios.ejecutar`.
"""
import threading

from http.server import ThreadingHTTPServer

from tools.puente_mt5 import inicializar_mt5

from .constantes import INTERVALO_TICKS, PUERTO
from .manejador import Manejador
from .motor import MOTOR


def ejecutar() -> None:
    """Inicia el servidor de datos y lo mantiene en ejecución hasta Ctrl+C.

    Inicializa la conexión con MT5, lanza el motor de precios en un hilo demonio y
    levanta un ThreadingHTTPServer en 127.0.0.1:PUERTO (solo local) con el Manejador,
    que atiende cada petición en su propio hilo. Imprime avisos en consola y bloquea
    en serve_forever().
    """
    # Conecta con el terminal MT5 antes de aceptar peticiones
    inicializar_mt5()
    # Hilo demonio del motor: lee ticks y cuenta en segundo plano
    threading.Thread(target=MOTOR.correr, name="motor-precios", daemon=True).start()
    # Servidor HTTP solo en loopback; un hilo por petición (SSE mantiene conexiones largas)
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    servidor.daemon_threads = True
    # Mensajes informativos de arranque
    print(f"Servidor de datos MT5 activo en http://localhost:{PUERTO}  (Ctrl+C para detener)")
    print(f"  · Precios en vivo por SSE cada {int(INTERVALO_TICKS * 1000)} ms  (/stream)")
    # Bucle de atención de peticiones (bloqueante)
    servidor.serve_forever()


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara ejecucion .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
