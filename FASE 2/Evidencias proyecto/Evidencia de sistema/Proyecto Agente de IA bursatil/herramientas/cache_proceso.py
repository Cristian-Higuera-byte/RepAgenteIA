# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara cache_proceso .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Caché en memoria del proceso (no depende de Streamlit) con "stale-while-revalidate".

Sirve para datos lentos de pedir (velas por REST) que se comparten entre sesiones y se calientan desde hilos
de fondo: `st.cache_data` no garantiza compartir lo que escribe un hilo sin contexto de Streamlit. Una excepción
dentro de la función NO se cachea (igual que en `st.cache_data`), así un fallo transitorio se reintenta.

Uso:
    @cache_proceso(ttl=300)
    def serie(real, tf, n): ...

La función decorada también ofrece `en_cache(*args)`, que mira lo guardado sin calcular ni esperar. Dentro de `ttl` devuelve el valor guardado; pasado el `ttl` (hasta 6 veces) lo devuelve igual al instante y lo
refresca en un hilo aparte; más allá, vuelve a calcularlo bloqueando."""
import functools
import time

from herramientas.hilos import lanzar_hilo


# TITULO CACHE PROCESO

def cache_proceso(tiempo_vida: float):
    """Decorador de caché en memoria del proceso con refresco en segundo plano; recibe el tiempo de vida `ttl` en segundos."""
    def decorador(funcion):
        """Envuelve la función con la caché y le agrega `limpiar()` para vaciarla."""
        datos: dict = {}
        refrescando: set = set()

        def _calcular_y_guardar(clave, args):
            """Calcula el valor con la función original y lo guarda con su hora; un error no se guarda."""
            valor = funcion(*args)
            datos[clave] = (time.time(), valor)
            return valor

        @functools.wraps(funcion)
        def envoltorio(*args):
            """Devuelve el valor guardado si es reciente; si está vencido (hasta 6 veces el `ttl`) lo devuelve igual y lo refresca aparte; si no hay valor, lo calcula."""
            impacto = datos.get(args)
            if impacto:
                edad = time.time() - impacto[0]
                if edad < tiempo_vida:
                    return impacto[1]
                if edad < tiempo_vida * 6:
                    if args not in refrescando:
                        refrescando.add(args)

                        def _bg():
                            """Hilo de refresco del valor vencido; ignora los errores y libera la marca de "refrescando"."""
                            try:
                                _calcular_y_guardar(args, args)
                            except Exception:
                                pass
                            finally:
                                refrescando.discard(args)
                        lanzar_hilo(_bg)
                    return impacto[1]
            return _calcular_y_guardar(args, args)

        def en_cache(*args):
            """Devuelve el valor guardado para esos argumentos (aunque esté vencido) o None si nunca se calculó; no calcula nada ni espera."""
            impacto = datos.get(args)
            return impacto[1] if impacto else None

        envoltorio.limpiar = datos.clear
        envoltorio.en_cache = en_cache
        return envoltorio
    return decorador


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara cache_proceso .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
