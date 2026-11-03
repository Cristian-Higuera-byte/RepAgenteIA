# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- INICIO Piña y Jara hilos .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
hilos.py
--------
Hilos y tareas de segundo plano que siguen atendiendo al MISMO usuario que las lanzó.

Un hilo nuevo (o una tarea de un `ThreadPoolExecutor`) empieza sin saber quién es el usuario actual: Python no copia
el contexto al crear hilos, y la sesión de Streamlit solo es visible desde su propio hilo. Sin esto, una precarga o un
refresco lanzado por el usuario A podría quedar sin cuenta (o, peor, usar la de otro). Aquí la clave del usuario se
captura en el momento de crear la tarea y se vuelve a fijar dentro del hilo que la ejecuta.

Usar `lanzar_hilo` en vez de `threading.Thread(...).start()`, `enviar_al_pool` en vez de `pool.submit(...)` y
`con_usuario` al pasar la función a `executor.map(...)`, en cualquier código que llame al broker.
"""
import threading
from concurrent.futures import Executor, Future
from typing import Callable, Optional

from herramientas.backends import sesiones_capital


# TITULO CON USUARIO

def con_usuario(funcion: Callable) -> Callable:
    """Devuelve `funcion` envuelta para que corra con la clave del usuario que la envolvió (captura la clave ahora).

    Sirve para `executor.map(con_usuario(f), elementos)` y para cualquier tarea que se ejecute en otro hilo."""
    clave = sesiones_capital.clave_actual()

    def ejecutar(*argumentos, **opciones):
        """Ejecuta la función original con el usuario capturado al crear la tarea."""
        with sesiones_capital.con_clave(clave):
            return funcion(*argumentos, **opciones)

    return ejecutar


# TITULO LANZAR HILO

def lanzar_hilo(funcion: Callable, *argumentos, nombre: Optional[str] = None, demonio: bool = True) -> threading.Thread:
    """Lanza `funcion(*argumentos)` en un hilo nuevo que atiende al mismo usuario que lo lanzó, y devuelve el hilo."""
    hilo = threading.Thread(target=con_usuario(funcion), args=argumentos, name=nombre, daemon=demonio)
    hilo.start()
    return hilo


# TITULO ENVIAR AL POOL

def enviar_al_pool(pool: Executor, funcion: Callable, *argumentos, **opciones) -> Future:
    """Equivale a `pool.submit(funcion, ...)`, pero la tarea corre con el usuario que la envió."""
    return pool.submit(con_usuario(funcion), *argumentos, **opciones)


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara hilos .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
