# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara secciones .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Secciones de la página Mercados: "Pulso del mercado" (tarjetas) y tabla por categoría.

Cada tarjeta y cada fila de la tabla lleva un botón "ver" (oculto por CSS y accionado desde el clic en el
HTML) que abre la ficha del instrumento. Los contenedores con `key` (`mercados_tarjeta_*`, `mercados_fila_*`, `mercados_tabla`)
son los que engancha `estilos.css`.
"""
import threading

import streamlit as st

from componentes_plataforma.paralelo import en_paralelo
from herramientas.backends import sesiones_capital
from herramientas.hilos import con_usuario, lanzar_hilo
from componentes_plataforma.mercados.broker import fila, elementos, resolver, serie
from herramientas.puente_mt5 import NOMBRE_PROVEEDOR
from componentes_plataforma.mercados.constantes import CATALOGO, ORDENES, RESUMEN
from componentes_plataforma.mercados.piezas import fila_html, tarjeta_html
from componentes_plataforma.mercado_datos.sparkline import historial_sparkline
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]


# TITULO ABRIR FICHA

def abrir_ficha(real: str, nombre: str, cat: str):
    """Guarda en la sesión el instrumento elegido (`mercados_detalle`) y relanza la app para abrir la ficha.

    Recibe el símbolo real del bróker, el nombre a mostrar y la categoría. No devuelve nada: `st.rerun()`
    interrumpe la ejecución actual."""
    st.session_state.mercados_detalle = {"sym": real, "label": nombre, "cat": cat}
    st.rerun()


# TITULO RESUMEN

def resumen():
    """Dibuja la sección "Pulso del mercado": una tarjeta por cada referencia definida en `RESUMEN`.

    Resuelve el símbolo real de cada referencia en el bróker, obtiene su fila de datos desde MT5 y omite las
    que no existan. Cada tarjeta incluye un botón "ver" que abre la ficha. No recibe parámetros ni devuelve
    nada; se llama dentro de un fragmento que se refresca solo."""
    # Primera visita sin precarga lista: se dibuja un aviso al instante y las tarjetas aparecen en el siguiente refresco.
    if not _PULSO_LISTO.is_set():
        _en_segundo_plano(_calentar_pulso, "pulso", prioridad=True)
        st.html("<div class='mercados-cargando'><span class='mercados-cargando-punto'></span>Cargando el pulso del mercado…</div>")
        return
    # Reunir las filas de las referencias que existen en este bróker y tienen precio (se leen todas a la vez)
    def _referencia(elemento):
        """Fila de una referencia del pulso del mercado como `(fila, categoría, etiqueta)`, o None si no existe o no tiene precio."""
        cat, indice, tag = elemento
        candidatos, nombre = CATALOGO[cat][indice]
        real = resolver(candidatos)
        f = fila(real, nombre) if real else None
        return (f, cat, tag) if f else None
    filas = [x for x in en_paralelo(_referencia, RESUMEN) if x]
    # El mini-gráfico de cada tarjeta necesita sus últimas velas M1: se piden todas a la vez antes de dibujar las tarjetas.
    en_paralelo(lambda x: historial_sparkline(x[0]["sym"]), filas)
    # Sin ninguna referencia disponible (MT5 desconectado) no se dibuja la sección
    if not filas:
        return
    st.html("<div class='mercados-seccion'><b>Pulso del mercado</b><span>la referencia más seguida de "
            "cada mercado · variación de hoy y movimiento de los últimos 30 minutos</span></div>")
    # Una columna por tarjeta; el contenedor con key permite que el CSS posicione el botón sobre la tarjeta
    columnas = st.columns(len(filas), gap="small")
    for i, (f, categoria, etiqueta) in enumerate(filas):
        with columnas[i]:
            with st.container(key=f"mercados_tarjeta_{i}"):
                st.html(tarjeta_html(f, etiqueta))
                if st.button("ver", key=f"mercados_clic_card_{f['sym']}"):
                    abrir_ficha(f["sym"], f["label"], categoria)


# TITULO PRECARGAR

def _precargar(reales: list, fondo: bool = False) -> None:
    """Calienta en paralelo las lecturas históricas que luego pide cada fila (cierre previo y serie de 5 días).
    Con `fondo` los hilos de lectura se marcan como de segundo plano (usan solo la mitad del cupo de peticiones).
    Con Capital cada una es una llamada REST de ~300 ms: en serie, una categoría de 20 instrumentos tardaba
    más de 10 s en dibujarse; en paralelo y cacheadas, 1-2 s."""
    from concurrent.futures import ThreadPoolExecutor
    from proveedores.selector_mt5 import mt5
    from componentes_plataforma.mercado_datos import cierre_previo

    def _una(real):
        """Calienta, para un instrumento, los datos que pedirá su fila: ficha, cierre previo y serie de 5 días."""
        try:
            mt5.symbol_info(real)          # datos del instrumento (en Capital: una llamada REST, cacheada)
            cierre_previo(real)
            serie(real, mt5.TIMEFRAME_H1, 120)
        except Exception:
            pass
    if reales:
        with ThreadPoolExecutor(max_workers=6, initializer=_marcar_fondo if fondo else None) as ex:
            list(ex.map(con_usuario(_una), reales))


_precarga_lanzada = False
_INTERVALO_PRECARGA = 240.0     # s; menor que el TTL de las cachés (300 s) para que nunca se enfríen
# Estado de la precarga: categorías ya calientes, el pulso del mercado listo y las tareas en curso (por nombre).
_LISTAS: set = set()
_PULSO_LISTO = threading.Event()
_EN_CARGA: set = set()
_CANDADO = threading.Lock()


# TITULO MARCAR FONDO

def _marcar_fondo() -> None:
    """Marca el hilo actual como de segundo plano para el limitador de peticiones de Capital.com (no hace nada con MT5): así la
    precarga no le quita a la página que el usuario está viendo más de la mitad del cupo de peticiones."""
    try:
        from herramientas.puente_mt5 import PROVEEDOR
        if PROVEEDOR == "capital":
            from herramientas.backends.capital import marcar_hilo_fondo
            marcar_hilo_fondo()
    except Exception:
        pass


# TITULO EN SEGUNDO PLANO

def _en_segundo_plano(funcion, nombre: str, *args, prioridad: bool = False) -> None:
    """Ejecuta `funcion(*args)` en un hilo, salvo que ya haya otra tarea con ese nombre en curso. No espera ni propaga errores.

    Con `prioridad` (el usuario está esperando esos datos en pantalla) el hilo usa el cupo completo de peticiones; si no, solo la mitad."""
    with _CANDADO:
        if nombre in _EN_CARGA:
            return
        _EN_CARGA.add(nombre)

    def _tarea():
        """Cuerpo del hilo: marca el fondo, ejecuta la función y libera el nombre de la tarea."""
        if not prioridad:
            _marcar_fondo()
        try:
            funcion(*args)
        except Exception:
            pass
        finally:
            with _CANDADO:
                _EN_CARGA.discard(nombre)
    lanzar_hilo(_tarea, nombre=f"mercados-{nombre}")


# TITULO PULSO LISTO

def pulso_listo() -> bool:
    """¿Ya están calientes los datos de las tarjetas del pulso del mercado?"""
    return _PULSO_LISTO.is_set()


# TITULO CATEGORIA LISTA

def categoria_lista(categoria: str) -> bool:
    """¿Ya están calientes los datos de la categoría (instrumentos resueltos, fichas, cierres previos y series de 5 días)?"""
    return categoria in _LISTAS


# TITULO CALENTAR CATEGORIA

def _calentar_categoria(categoria: str, fondo: bool = True) -> None:
    """Resuelve los instrumentos de una categoría y calienta sus lecturas; al terminar la marca como lista.

    Con `fondo` (la precarga periódica) las lecturas usan la mitad del cupo de peticiones; si el usuario está esperando la tabla en
    pantalla se llama con `fondo=False` y usan el cupo completo."""
    _precargar([r for r, _, _ in elementos(categoria)], fondo)
    _LISTAS.add(categoria)


# TITULO CALENTAR PULSO

def _calentar_pulso() -> None:
    """Calienta las cinco referencias del pulso del mercado (fila y mini-gráfico de cada una); al terminar lo marca como listo."""
    def _referencia(elemento):
        """Calienta una referencia: la resuelve, lee su fila y su serie corta."""
        cat, indice, _tag = elemento
        candidatos, nombre = CATALOGO[cat][indice]
        real = resolver(candidatos)
        f = fila(real, nombre) if real else None
        if f:
            historial_sparkline(f["sym"])
    en_paralelo(_referencia, RESUMEN)
    _PULSO_LISTO.set()


# TITULO PRECARGAR TODAS LAS CATEGORIAS

def precargar_todas_las_categorias() -> None:
    """Deja todas las pestañas de Mercados precargadas y las mantiene calientes (una vez por proceso).

    Un hilo de fondo recorre las categorías, trae por REST los datos de cada instrumento (ficha, cierre previo
    y serie de 5 días) y repite cada 4 minutos, antes de que caduquen las cachés (`cache_proceso`, compartidas
    por todas las sesiones). Se lanza al iniciar la app, así al abrir Mercados o cambiar de pestaña no hay espera.
    La lanza `aplicacion_principal/precarga.py` al iniciar la sesión del usuario (no al abrir Mercados). No bloquea ni propaga errores."""
    global _precarga_lanzada
    if _precarga_lanzada or sesiones_capital.MULTIUSUARIO:
        # En modo multiusuario no hay una cuenta "de la plataforma" que haga la precarga (gastaría el cupo de
        # peticiones de un usuario cualquiera): cada pestaña se carga al abrirla y las cachés se comparten entre usuarios.
        return
    _precarga_lanzada = True
    import time

    def _tarea():
        """Cuerpo del hilo de precarga: calienta el pulso del mercado y todas las categorías, y repite cada pocos minutos."""
        _marcar_fondo()
        while True:
            try:
                _calentar_pulso()
            except Exception:
                pass
            for categoria in CATALOGO:
                try:
                    _calentar_categoria(categoria)
                except Exception:
                    pass
            time.sleep(_INTERVALO_PRECARGA)
    threading.Thread(target=_tarea, daemon=True, name="precarga-mercados").start()


# TITULO RENDERIZAR TABLA

def renderizar_tabla(categoria: str):
    """Dibuja la tabla de instrumentos de una categoría, con búsqueda y orden tomados de la sesión.

    Recibe el nombre de la categoría del catálogo. Lee `mercados_q` (texto de búsqueda) y `mercados_orden` (criterio
    de orden) de `st.session_state`, filtra y ordena las filas, y pinta cabecera y filas en un mismo
    contenedor. Devuelve una tupla `(total, mostrados)`: instrumentos disponibles en la categoría y los que
    quedan tras el filtro; `(None, None)` si la categoría aún se está cargando."""
    # Primera visita sin precarga lista: aviso al instante y se pide esta categoría con prioridad; la tabla aparece sola en el
    # siguiente refresco (cada 3 s). Devuelve (None, None) para que la página omita el pie de la tabla.
    if not categoria_lista(categoria):
        _en_segundo_plano(_calentar_categoria, f"categoria-{categoria}", categoria, False, prioridad=True)
        with st.container(key="mercados_tabla"):
            st.html("<div class='mercados-cargando'><span class='mercados-cargando-punto'></span>"
                    f"Cargando {categoria.lower()}…</div>")
        return None, None
    # Filas con datos en vivo de MT5 (las que no tienen precio se descartan)
    items = elementos(categoria)
    _precargar([r for r, _, _ in items])
    filas = [f for f in (fila(r, n) for r, n, _ in items) if f]
    total = len(filas)

    # Filtro de búsqueda: coincide con el nombre, el símbolo o la descripción del bróker
    q = (st.session_state.get("mercados_q") or "").strip().lower()
    if q:
        filas = [f for f in filas if q in f["label"].lower() or q in f["sym"].lower()
                 or q in f["desc"].lower()]
    # Orden elegido por el usuario; con el primero de la lista se conserva el orden del catálogo
    orden = st.session_state.get("mercados_orden") or ORDENES[0]
    if orden == "Mayor alza":
        filas.sort(key=lambda f: f["pct"], reverse=True)
    elif orden == "Mayor baja":
        filas.sort(key=lambda f: f["pct"])
    elif orden == "Nombre (A-Z)":
        filas.sort(key=lambda f: f["label"].lower())

    # Cabecera y filas en el MISMO contenedor (gap 0): si la cabecera va aparte,
    # Streamlit agrega su separación de ~1rem entre ambos bloques.
    with st.container(key="mercados_tabla"):
        st.html(
            "<div class='mercados-cabecera'><div>Instrumento</div><div class='mercados-r'>Precio</div>"
            "<div class='mercados-r'>Cambio</div><div class='mercados-r'>Cambio %</div>"
            "<div>Rango del día</div><div style='text-align:center;'>5 días</div><div>Estado</div></div>"
        )
        # Sin resultados: mensaje distinto si hay búsqueda activa o si falta conexión con MT5
        if not filas:
            mensaje = ("Ningún instrumento coincide con la búsqueda." if q else
                   f"No hay datos para esta categoría. Verifica la conexión con {NOMBRE_PROVEEDOR} "
                   "y que el bróker tenga estos instrumentos.")
            st.html(f"<div class='mercados-vacio'>{mensaje}</div>")
            return total, 0
        # El mini-gráfico de 5 días de cada fila necesita su histórico H1: se piden todos a la vez (quedan en la caché de
        # `serie`) en vez de uno por fila mientras se dibuja la tabla.
        en_paralelo(lambda f: serie(f["sym"], mt5.TIMEFRAME_H1, 120), filas)
        # Cada fila va en su contenedor con key; el botón "ver" invisible abre la ficha al hacer clic
        for i, f in enumerate(filas):
            with st.container(key=f"mercados_fila_{i}"):
                st.html(fila_html(f))
                if st.button("ver", key=f"mercados_clic_{f['sym']}"):
                    abrir_ficha(f["sym"], f["label"], categoria)
    return total, len(filas)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara secciones .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
