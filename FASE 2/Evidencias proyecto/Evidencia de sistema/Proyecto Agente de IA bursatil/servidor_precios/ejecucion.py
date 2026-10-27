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

"""Arranque del servidor de datos (motores por cuenta + servidor HTTP).

Lo invoca el lanzador servidor_datos.py de la raíz a través de `servidor_precios.ejecutar`.
"""
import threading
import time

from http.server import ThreadingHTTPServer

from herramientas import token_datos
from herramientas.backends import sesiones_capital
from herramientas.puente_mt5 import PROVEEDOR, inicializar_mt5

from .constantes import INTERVALO_TICKS, PUERTO
from .manejador import Manejador
from .motor import MOTORES

# Cada cuántos segundos se buscan cuentas con stop dinámico u OCO para mantener su motor encendido
INTERVALO_DESCUBRIMIENTO = 30


# TITULO VIGILAR CUENTAS

def _vigilar_cuentas() -> None:
    """Hilo del servidor (solo modo multiusuario): enciende el motor de toda cuenta con stop dinámico u OCO activos.

    Esas vigilancias deben seguir funcionando con el navegador cerrado, así que no dependen de que el usuario esté
    conectado; un error al buscar se imprime y se reintenta en el próximo ciclo."""
    while True:
        try:
            MOTORES.descubrir()
        except Exception as error:
            print(f"[servidor] no se pudieron revisar las vigilancias de las cuentas: {error}")
        time.sleep(INTERVALO_DESCUBRIMIENTO)


# TITULO EJECUTAR

def ejecutar() -> None:
    """Inicia el servidor de datos y lo mantiene en ejecución hasta Ctrl+C.

    Modo de un solo usuario: inicializa la conexión con el broker y deja encendido el motor de la cuenta del .env.
    Modo multiusuario (`CAPITAL_MULTIUSUARIO=true`): no hay cuenta propia; cada motor nace cuando un usuario se conecta
    (o cuando tiene vigilancias activas, que un hilo revisa cada pocos segundos). Luego levanta un ThreadingHTTPServer
    en 127.0.0.1:PUERTO (solo local; en producción va detrás de un proxy HTTPS) con el Manejador, que atiende cada
    petición en su propio hilo. Imprime avisos en consola y bloquea en serve_forever().
    """
    # Con Capital.com el límite de 10 peticiones por segundo es de la sesión, que comparten este servidor y el dashboard:
    # aquí se dejan 4 (velas, precargas y consulta de la cuenta) y 6 quedan para las vistas de Streamlit.
    if PROVEEDOR == "capital":
        sesiones_capital.fijar_limite_peticiones(4)
    if sesiones_capital.MULTIUSUARIO:
        if not token_datos.emitir(0, True):
            raise SystemExit("Modo multiusuario sin SERVIDOR_SECRETO (mínimo 32 caracteres) en el .env: "
                             "genera uno con herramientas.token_datos.generar_secreto().")
        threading.Thread(target=_vigilar_cuentas, name="vigilar-cuentas", daemon=True).start()
    else:
        # Conecta con el broker y deja encendido el motor de la cuenta del .env antes de aceptar peticiones
        inicializar_mt5()
        MOTORES.de(("legado",))
    # Servidor HTTP solo en loopback; un hilo por petición (SSE mantiene conexiones largas)
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    servidor.daemon_threads = True
    # Mensajes informativos de arranque
    modo = "multiusuario" if sesiones_capital.MULTIUSUARIO else "un solo usuario"
    print(f"Servidor de datos activo ({modo}) en http://localhost:{PUERTO}  (Ctrl+C para detener)")
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
