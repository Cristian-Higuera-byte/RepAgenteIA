# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara dialogo .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
buscador/dialogo.py
-------------------
Modal (st.dialog) del buscador de activos, estilo XM: campo de texto + filtro por
categoría + lista con revelado progresivo ("Ver más"). Cada resultado se puede "Abrir"
(cargar en el gráfico) o "➕ Agregar" a la watchlist. Se abre con el patrón bandera +
render en aplicacion.py (`abrir_buscador` marca, `renderizar_buscador` dibuja) para que el diálogo
no choque con los fragmentos de auto-refresco y deje la pantalla en blanco.
Los datos y el filtrado vienen de datos.py.
"""
from html import escape

import streamlit as st

from .datos import buscar_en_vivo, categorias, estado_buscador, filtrar, _agregar_a_watchlist

# Cantidad de resultados que se revelan al inicio y cada vez que se pulsa "Ver más".
_PASO_RESULTADOS = 30  # cuántos se revelan al inicio y por cada "Ver más"


# TITULO TITULO FILA

def _titulo_fila(a: dict) -> tuple[str, str]:
    """Devuelve (título, subtítulo) de la fila de un activo, ya escapados para HTML.

    Normalmente el título es el símbolo y el subtítulo la descripción. Si el símbolo es solo números (como «0001» en las acciones de Hong Kong) no dice
    qué activo es, así que el título pasa a ser el nombre y el número queda como subtítulo."""
    simbolo, desc = a["visible"], a["desc"]
    if simbolo and not any(c.isalpha() for c in simbolo) and desc and desc != simbolo:
        return escape(desc), escape(simbolo)
    return escape(simbolo), escape(desc)


# TITULO ABRIR BUSCADOR

def abrir_buscador():
    """Marca que el diálogo debe mostrarse (se renderiza en aplicacion.py con
    `renderizar_buscador`). Este patrón (bandera + render en el script principal)
    evita que el diálogo choque con los fragmentos de auto-refresco y deje la
    pantalla en blanco al interactuar dentro."""
    st.session_state.mostrar_buscador = True


# TITULO CERRAR BUSCADOR

def _cerrar_buscador():
    """Callback `on_dismiss` del diálogo: apaga la bandera `mostrar_buscador` al cerrarlo."""
    st.session_state.mostrar_buscador = False


# TITULO RENDERIZAR BUSCADOR

def renderizar_buscador():
    """Abre el diálogo del buscador si la bandera `mostrar_buscador` está activa.

    Debe llamarse UNA vez al final de aplicacion.py. No recibe ni devuelve nada.
    """
    if st.session_state.get("mostrar_buscador"):
        _dialogo_buscador()


# TITULO DIALOGO BUSCADOR

@st.dialog("Buscar activo", width="large", on_dismiss=_cerrar_buscador)
def _dialogo_buscador():
    """Contenido del modal: búsqueda por texto, filtro por categoría y lista de resultados.

    Cada resultado tiene un botón "Abrir" (selecciona el activo, cierra el diálogo y
    reejecuta la app) y un botón de agregar a la watchlist (✓ si ya está). Los resultados se
    revelan por bloques con "Ver más". Dentro del diálogo los rerun son de ámbito fragmento
    para no cerrarlo. El catálogo se lee sin esperar a la red: si aún se está cargando (la primera vez, en segundo plano) se avisa y
    la búsqueda también consulta directamente al servidor del broker, así cualquier instrumento se encuentra igual.
    """
    # Instrumentos del broker ya conocidos (nunca espera a la red) y si el catálogo está completo
    activos, listo = estado_buscador()
    if not activos:
        # Primera carga del catálogo: se avisa y se ofrece volver a mirar (el clic reejecuta solo el diálogo, sin cerrarlo)
        st.info("Cargando el catálogo de instrumentos de Capital.com… la primera vez puede tardar un poco. "
                "Mientras tanto ya puedes buscar por nombre.")
        st.button("Actualizar", key="buscar_actualizar")

    # Campo de texto
    q = st.text_input("Buscar", placeholder="Símbolo o nombre, ej. AAPL, EUR, Silver, Bitcoin…",
                      label_visibility="collapsed", key="buscar_q")
    texto = q.strip()

    # Respaldo: si el catálogo aún no está completo, o está completo pero no hay ninguna coincidencia (por si el catálogo quedó
    # atrás), se busca también en el servidor del broker. Con el catálogo completo y coincidencias no se espera a la red.
    en_vivo: list[dict] = []
    if len(texto) >= 2 and (not listo or not filtrar(activos, q, "Todo")):
        with st.spinner("Buscando en Capital.com…"):
            en_vivo = buscar_en_vivo(texto)
        conocidos = {a["name"] for a in activos}
        en_vivo = [a for a in en_vivo if a["name"] not in conocidos]
    base = activos + en_vivo if en_vivo else activos

    # Filtro de categoría y ambos filtros aplicados
    categoria = st.segmented_control("Categoría", categorias(base), default="Todo",
                               label_visibility="collapsed", key="buscar_categoria")
    resultados = filtrar(base, q, categoria or "Todo")

    # Revelado progresivo: se reinicia al cambiar la búsqueda o la categoría.
    filtro_actual = (q.strip().upper(), categoria or "Todo")
    if st.session_state.get("_buscar_filtro") != filtro_actual:
        st.session_state._buscar_filtro = filtro_actual
        st.session_state._buscar_limite = _PASO_RESULTADOS
    limite = st.session_state.get("_buscar_limite", _PASO_RESULTADOS)
    mostrados = min(limite, len(resultados))

    # Contador de resultados
    st.caption(f"{len(resultados)} de {len(base)} activos"
               + (f" · mostrando {mostrados}" if len(resultados) > mostrados else "")
               + ("" if listo else " · el catálogo completo se sigue cargando en segundo plano"))

    # Símbolos ya agregados a la lista y usuario actual
    en_lista = set(st.session_state.get("watchlist_simbolos", []))
    uid = (st.session_state.get("usuario_informacion") or {}).get("id")

    # Lista con scroll de altura fija
    with st.container(height=400):
        for a in resultados[:mostrados]:
            # Fila: información, botón Abrir y botón Agregar
            c_info, c_abrir, c_agregar = st.columns([6, 1.2, 1.2], vertical_alignment="center")
            # Símbolo, categoría y descripción
            with c_info:
                titulo, subtitulo = _titulo_fila(a)
                st.markdown(
                    f"**{titulo}** · <span style='color:#8b949e; font-size:11px;'>"
                    f"{a['cat']}</span><br>"
                    f"<span style='color:#8b949e; font-size:12px;'>{subtitulo}</span>",
                    unsafe_allow_html=True,
                )
            # Abrir el activo en el gráfico
            with c_abrir:
                if st.button("Abrir", key=f"abrir_{a['name']}", width="stretch"):
                    # Abrir SÍ cierra el diálogo y refresca la app (carga el gráfico).
                    st.session_state.activo_seleccionado = a["name"]
                    st.session_state.mostrar_buscador = False
                    st.rerun()
            # Agregar a la watchlist, o marca si ya está
            with c_agregar:
                if a["name"] in en_lista:
                    st.button("✓", key=f"agregar_{a['name']}", width="stretch", disabled=True,
                              help="Ya está en tu lista")
                else:
                    if st.button("➕", key=f"agregar_{a['name']}", width="stretch",
                                 help="Agregar a mi lista"):
                        # Si el plan ya no deja agregar más, avisa y no cambia nada (no hace falta refrescar).
                        if _agregar_a_watchlist(uid, a):
                            # Rerun SOLO del diálogo (es un fragmento): refresca al instante
                            # para que la fila pase a "✓" y se limpie el tooltip. No cierra
                            # el modal ni reemplaza la app.
                            st.rerun(scope="fragment")

        # "Ver más" al final del scroll: revela otro bloque sin cerrar el modal
        if mostrados < len(resultados):
            restantes = len(resultados) - mostrados
            if st.button(f"Ver más ({restantes} restantes)", key="buscar_ver_mas",
                         width="stretch"):
                st.session_state._buscar_limite = limite + _PASO_RESULTADOS
                st.rerun(scope="fragment")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara dialogo .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
