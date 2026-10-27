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
HTML) que abre la ficha del instrumento. Los contenedores con `key` (`mktcard_*`, `mktrow_*`, `mkt_tabla`)
son los que engancha `estilos.css`.
"""
import streamlit as st

from components.mercados.broker import fila, elementos, resolver
from components.mercados.constantes import CATALOGO, ORDENES, RESUMEN
from components.mercados.piezas import fila_html, tarjeta_html


def abrir_ficha(real: str, nombre: str, cat: str):
    """Guarda en la sesión el instrumento elegido (`mkt_detalle`) y relanza la app para abrir la ficha.

    Recibe el símbolo real del bróker, el nombre a mostrar y la categoría. No devuelve nada: `st.rerun()`
    interrumpe la ejecución actual."""
    st.session_state.mkt_detalle = {"sym": real, "label": nombre, "cat": cat}
    st.rerun()


def resumen():
    """Dibuja la sección "Pulso del mercado": una tarjeta por cada referencia definida en `RESUMEN`.

    Resuelve el símbolo real de cada referencia en el bróker, obtiene su fila de datos desde MT5 y omite las
    que no existan. Cada tarjeta incluye un botón "ver" que abre la ficha. No recibe parámetros ni devuelve
    nada; se llama dentro de un fragmento que se refresca solo."""
    # Reunir las filas de las referencias que existen en este bróker y tienen precio
    filas = []
    for cat, idx, tag in RESUMEN:
        cands, nombre = CATALOGO[cat][idx]
        real = resolver(cands)
        f = fila(real, nombre) if real else None
        if f:
            filas.append((f, cat, tag))
    # Sin ninguna referencia disponible (MT5 desconectado) no se dibuja la sección
    if not filas:
        return
    st.html("<div class='mkt-sec'><b>Pulso del mercado</b><span>la referencia más seguida de "
            "cada mercado · variación de hoy y movimiento de los últimos 30 minutos</span></div>")
    # Una columna por tarjeta; el contenedor con key permite que el CSS posicione el botón sobre la tarjeta
    cols = st.columns(len(filas), gap="small")
    for i, (f, cat, tag) in enumerate(filas):
        with cols[i]:
            with st.container(key=f"mktcard_{i}"):
                st.html(tarjeta_html(f, tag))
                if st.button("ver", key=f"mktclk_card_{f['sym']}"):
                    abrir_ficha(f["sym"], f["label"], cat)


def renderizar_tabla(categoria: str):
    """Dibuja la tabla de instrumentos de una categoría, con búsqueda y orden tomados de la sesión.

    Recibe el nombre de la categoría del catálogo. Lee `mkt_q` (texto de búsqueda) y `mkt_orden` (criterio
    de orden) de `st.session_state`, filtra y ordena las filas, y pinta cabecera y filas en un mismo
    contenedor. Devuelve una tupla `(total, mostrados)`: instrumentos disponibles en la categoría y los que
    quedan tras el filtro."""
    # Filas con datos en vivo de MT5 (las que no tienen precio se descartan)
    filas = [f for f in (fila(r, n) for r, n, _ in elementos(categoria)) if f]
    total = len(filas)

    # Filtro de búsqueda: coincide con el nombre, el símbolo o la descripción del bróker
    q = (st.session_state.get("mkt_q") or "").strip().lower()
    if q:
        filas = [f for f in filas if q in f["label"].lower() or q in f["sym"].lower()
                 or q in f["desc"].lower()]
    # Orden elegido por el usuario; con el primero de la lista se conserva el orden del catálogo
    orden = st.session_state.get("mkt_orden") or ORDENES[0]
    if orden == "Mayor alza":
        filas.sort(key=lambda f: f["pct"], reverse=True)
    elif orden == "Mayor baja":
        filas.sort(key=lambda f: f["pct"])
    elif orden == "Nombre (A-Z)":
        filas.sort(key=lambda f: f["label"].lower())

    # Cabecera y filas en el MISMO contenedor (gap 0): si la cabecera va aparte,
    # Streamlit agrega su separación de ~1rem entre ambos bloques.
    with st.container(key="mkt_tabla"):
        st.html(
            "<div class='mkt-head'><div>Instrumento</div><div class='mkt-r'>Precio</div>"
            "<div class='mkt-r'>Cambio</div><div class='mkt-r'>Cambio %</div>"
            "<div>Rango del día</div><div style='text-align:center;'>5 días</div><div>Estado</div></div>"
        )
        # Sin resultados: mensaje distinto si hay búsqueda activa o si falta conexión con MT5
        if not filas:
            msg = ("Ningún instrumento coincide con la búsqueda." if q else
                   "No hay datos para esta categoría. Verifica que MetaTrader 5 esté abierto "
                   "y que el bróker tenga estos instrumentos.")
            st.html(f"<div class='mkt-vacio'>{msg}</div>")
            return total, 0
        # Cada fila va en su contenedor con key; el botón "ver" invisible abre la ficha al hacer clic
        for i, f in enumerate(filas):
            with st.container(key=f"mktrow_{i}"):
                st.html(fila_html(f))
                if st.button("ver", key=f"mktclk_{f['sym']}"):
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
