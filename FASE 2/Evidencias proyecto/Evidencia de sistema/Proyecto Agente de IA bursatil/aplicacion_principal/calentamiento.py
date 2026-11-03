# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara calentamiento .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""Lecturas del bróker en paralelo al empezar cada pasada de la página.

Cada lectura al bróker (cuenta, posiciones, datos del activo del gráfico) tarda ~300-500 ms cuando no está en caché, y la página las pedía una tras otra: después de
unos minutos sin usar la plataforma, el primer clic esperaba la SUMA de todas. Aquí se lanzan a la vez, justo antes de dibujar, y se espera como mucho lo que tarde la más
lenta; cuando la página llega a pedirlas, ya están en caché. Con la caché vigente no cuesta nada (las lecturas devuelven al instante) y se repite como máximo cada
`ENFRIAMIENTO_S` segundos por usuario."""
import threading
import time

import streamlit as st

from herramientas.backends import sesiones_capital
from herramientas.hilos import lanzar_hilo

# Segundos mínimos entre dos calentamientos del mismo usuario y cuenta.
ENFRIAMIENTO_S = 15
# Segundos máximos que la página espera por las lecturas en paralelo; pasado ese tiempo sigue sin ellas (las terminan los hilos de todos modos).
ESPERA_MAXIMA_S = 2.5
_ULTIMO: dict = {}
_CANDADO = threading.Lock()


# TITULO LECTURAS

def _lecturas() -> list:
    """Funciones sin argumentos que cargan en caché lo que cualquier vista necesita: cuenta, posiciones y, en las vistas con gráfico, los datos del activo elegido."""
    from herramientas.puente_mt5 import obtener_info_cuenta, obtener_posiciones
    lecturas = [obtener_info_cuenta, obtener_posiciones]
    if st.session_state.get("navegacion_activo") in ("trading", "portafolio"):
        from componentes_plataforma.grafico.simbolo import info_simbolo, limpiar_simbolo
        activo = limpiar_simbolo(str(st.session_state.get("activo_seleccionado") or ""))
        if activo:
            lecturas.append(lambda: info_simbolo(activo))
    return lecturas


# TITULO CALENTAR

def calentar() -> None:
    """Lanza en paralelo las lecturas del bróker de esta pasada y espera por ellas hasta `ESPERA_MAXIMA_S`. No hace nada si se calentó hace menos de
    `ENFRIAMIENTO_S` segundos o si no hay usuario. Cualquier error se descarta: es solo una optimización y la página pide los datos por su cuenta si faltan."""
    try:
        clave = sesiones_capital.clave_actual()
        ahora = time.time()
        with _CANDADO:
            if ahora - _ULTIMO.get(clave, 0) < ENFRIAMIENTO_S:
                return
            _ULTIMO[clave] = ahora
        hilos = []
        for lectura in _lecturas():
            def _tarea(f=lectura):
                """Hilo de una lectura: la pide con la cuenta del usuario y descarta cualquier error."""
                try:
                    f()
                except Exception:  # noqa: BLE001 - es solo una optimización
                    pass
            hilos.append(lanzar_hilo(_tarea, nombre="calentamiento"))
        limite = time.time() + ESPERA_MAXIMA_S
        for hilo in hilos:
            hilo.join(max(0.0, limite - time.time()))
    except Exception:  # noqa: BLE001
        pass


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara calentamiento .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
