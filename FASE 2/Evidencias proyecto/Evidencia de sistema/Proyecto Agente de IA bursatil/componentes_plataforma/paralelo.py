# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara paralelo .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Lecturas en paralelo para las vistas de Streamlit: pide a la vez lo que antes se pedía una cosa tras otra.

Con Capital.com cada lectura es una llamada REST de 300-800 ms; una vista que necesita 20 lecturas tardaba 20 veces eso.
`en_paralelo` las lanza en hilos y devuelve los resultados en el mismo orden. Cada hilo recibe el contexto de ejecución de
Streamlit, así las funciones con `st.cache_data` guardan su resultado en la caché normal y las siguientes lecturas son
instantáneas. El límite de peticiones por segundo lo controla el backend de Capital.com, de modo que abrir más hilos nunca
provoca un 429.
"""
import threading
from concurrent.futures import ThreadPoolExecutor, wait

from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

# Hilos que se usan por defecto (el backend limita el ritmo real de peticiones).
HILOS_POR_DEFECTO = 6


# TITULO EN PARALELO

def en_paralelo(funcion, elementos, max_hilos: int = HILOS_POR_DEFECTO, espera: float | None = None) -> list:
    """Ejecuta `funcion(elemento)` para cada elemento en hilos paralelos y devuelve los resultados en el mismo orden.

    Una función que lanza una excepción devuelve None en su lugar. Con `espera` (segundos) no se aguarda más que ese tiempo:
    los resultados que no llegaron quedan como None y sus hilos terminan por su cuenta. Con un solo elemento o sin contexto
    de Streamlit se ejecuta en el hilo actual, sin crear hilos."""
    elementos = list(elementos)
    if not elementos:
        return []
    contexto = get_script_run_ctx()

    def _tarea(e):
        """Aplica la función a un elemento y devuelve su resultado, o None si falla."""
        try:
            return funcion(e)
        except Exception:
            return None
    if len(elementos) == 1 or contexto is None:
        return [_tarea(e) for e in elementos]

    def _iniciar_hilo():
        """Asocia al hilo del grupo el contexto de Streamlit, para que sus funciones puedan usar la sesión."""
        add_script_run_ctx(threading.current_thread(), contexto)
    pool = ThreadPoolExecutor(max_workers=min(max_hilos, len(elementos)), initializer=_iniciar_hilo)
    futuros = [pool.submit(_tarea, e) for e in elementos]
    wait(futuros, timeout=espera)
    pool.shutdown(wait=False)
    return [f.result() if f.done() else None for f in futuros]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara paralelo .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
