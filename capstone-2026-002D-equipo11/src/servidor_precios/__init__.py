# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
servidor_precios
----------------
Mini-servidor de datos de MetaTrader 5 para alimentar el dashboard en TIEMPO REAL.

Dos funciones:
  1) Velas para el gráfico (Lightweight Charts): carga inicial + última vela.
  2) MOTOR DE PRECIOS EN VIVO (streaming): un único hilo lee los ticks de MT5
     cada ~250 ms para los símbolos que la página está mostrando y los EMPUJA al
     navegador por Server-Sent Events (SSE). El navegador actualiza los números
     directamente en el DOM, sin reejecutar Streamlit (como las plataformas de
     trading). Así hay UNA sola conexión a MT5 para precios, en vez de varios
     fragmentos `run_every` consultando cada uno por su cuenta.

Cómo ejecutarlo (en una terminal APARTE, además del 'streamlit run src/app.py'):
    env\\Scripts\\python src/servidor_datos.py     (lanzador de la raíz; el código vive en este paquete)

Endpoints:
    GET /velas/<símbolo>?tf=H1&n=150   -> lista de velas OHLC (carga inicial del gráfico)
    GET /ultima/<símbolo>?tf=H1        -> última vela (resincroniza volumen/vela nueva)
    GET /stream?s=EURUSD...,BTCUSD     -> SSE: ticks en vivo + cuenta (saldo, P/G y P/G por posición)
    GET /ticks?s=EURUSD...,BTCUSD      -> foto instantánea (JSON) de esos ticks
    GET /simbolos                      -> catálogo de símbolos del terminal [{n, d, c}] (ventana "Comparar" del gráfico)
    GET /salud                         -> {"ok": true} (lo usa Streamlit para saber si hay feed)
    POST /sltp  {"ticket", "sl", "tp"} -> cambia SL/TP de una posición (líneas arrastrables
                                          del gráfico; solo desde páginas de localhost)
    POST /orden {"symbol", "lado", "volumen", "precio"} -> nueva orden pendiente
                                          (Buy/Sell Limit/Stop, menú del clic derecho)
    POST /orden/modificar {"ticket", "precio", "sl", "tp", "caducidad", "expiracion"}
                                       -> modifica una orden pendiente
    POST /orden/eliminar  {"ticket"}   -> cancela una orden pendiente
    POST /mercado {"symbol", "lado", "volumen"} -> orden a mercado (botones VENDER/COMPRAR del gráfico a pantalla completa)

Nota: usa solo la librería estándar de Python (http.server), no requiere instalar nada.
El terminal de MetaTrader 5 debe estar abierto y logueado.

Organización:
  constantes.py   puerto, versión de la API, temporalidades, intervalos y candado de MT5
  velas.py        velas OHLC del gráfico
  simbolos.py     catálogo de símbolos del terminal
  motor/          motor de precios en vivo (ticks, cuenta, stop dinámico, OCO, equity)
  manejador.py    rutas HTTP (GET / POST / SSE)
  ejecucion.py    arranque del servidor
"""

from .ejecucion import ejecutar

__all__ = ["ejecutar"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
