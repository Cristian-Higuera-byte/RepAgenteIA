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
render en app.py (`abrir_buscador` marca, `renderizar_buscador` dibuja) para que el diálogo
no choque con los fragmentos de auto-refresco y deje la pantalla en blanco.
Los datos y el filtrado vienen de datos.py.
"""
import streamlit as st

from .datos import cargar_simbolos_broker, categorias, filtrar, _agregar_a_watchlist

# Cantidad de resultados que se revelan al inicio y cada vez que se pulsa "Ver más".
_PASO_RESULTADOS = 40  # cuántos se revelan al inicio y por cada "Ver más"


def abrir_buscador():
    """Marca que el diálogo debe mostrarse (se renderiza en app.py con
    `renderizar_buscador`). Este patrón (bandera + render en el script principal)
    evita que el diálogo choque con los fragmentos de auto-refresco y deje la
    pantalla en blanco al interactuar dentro."""
    st.session_state.mostrar_buscador = True


def _cerrar_buscador():
    """Callback `on_dismiss` del diálogo: apaga la bandera `mostrar_buscador` al cerrarlo."""
    st.session_state.mostrar_buscador = False


def renderizar_buscador():
    """Abre el diálogo del buscador si la bandera `mostrar_buscador` está activa.

    Debe llamarse UNA vez al final de app.py. No recibe ni devuelve nada.
    """
    if st.session_state.get("mostrar_buscador"):
        _dialogo_buscador()


@st.dialog("Buscar activo", width="large", on_dismiss=_cerrar_buscador)
def _dialogo_buscador():
    """Contenido del modal: búsqueda por texto, filtro por categoría y lista de resultados.

    Cada resultado tiene un botón "Abrir" (selecciona el activo, cierra el diálogo y
    reejecuta la app) y un botón de agregar a la watchlist (✓ si ya está). Los resultados se
    revelan por bloques con "Ver más". Dentro del diálogo los rerun son de ámbito fragmento
    para no cerrarlo. Si MT5 no entrega símbolos, muestra una advertencia.
    """
    # Símbolos del broker (cacheados)
    activos = cargar_simbolos_broker()
    if not activos:
        st.warning("No se pudieron cargar los símbolos de MT5. ¿Está abierto el terminal?")
        return

    # Campo de texto y filtro de categoría
    q = st.text_input("Buscar", placeholder="Símbolo o nombre, ej. AAPL, EUR, Bitcoin…",
                      label_visibility="collapsed", key="buscar_q")
    cat = st.segmented_control("Categoría", categorias(activos), default="Todo",
                               label_visibility="collapsed", key="buscar_cat")

    # Aplica ambos filtros
    resultados = filtrar(activos, q, cat or "Todo")

    # Revelado progresivo: se reinicia al cambiar la búsqueda o la categoría.
    filtro_actual = (q.strip().upper(), cat or "Todo")
    if st.session_state.get("_buscar_filtro") != filtro_actual:
        st.session_state._buscar_filtro = filtro_actual
        st.session_state._buscar_limite = _PASO_RESULTADOS
    limite = st.session_state.get("_buscar_limite", _PASO_RESULTADOS)
    mostrados = min(limite, len(resultados))

    # Contador de resultados
    st.caption(f"{len(resultados)} de {len(activos)} activos"
               + (f" · mostrando {mostrados}" if len(resultados) > mostrados else ""))

    # Símbolos ya agregados a la lista y usuario actual
    en_lista = set(st.session_state.get("watchlist_simbolos", []))
    uid = (st.session_state.get("usuario_info") or {}).get("id")

    # Lista con scroll de altura fija
    with st.container(height=400):
        for a in resultados[:mostrados]:
            # Fila: información, botón Abrir y botón Agregar
            c_info, c_abrir, c_add = st.columns([6, 1.2, 1.2], vertical_alignment="center")
            # Símbolo, categoría y descripción
            with c_info:
                st.markdown(
                    f"**{a['visible']}** · <span style='color:#8b949e; font-size:11px;'>"
                    f"{a['cat']}</span><br>"
                    f"<span style='color:#8b949e; font-size:12px;'>{a['desc']}</span>",
                    unsafe_allow_html=True,
                )
            # Abrir el activo en el gráfico
            with c_abrir:
                if st.button("Abrir", key=f"open_{a['name']}", width="stretch"):
                    # Abrir SÍ cierra el diálogo y refresca la app (carga el gráfico).
                    st.session_state.activo_seleccionado = a["name"]
                    st.session_state.mostrar_buscador = False
                    st.rerun()
            # Agregar a la watchlist, o marca si ya está
            with c_add:
                if a["name"] in en_lista:
                    st.button("✓", key=f"add_{a['name']}", width="stretch", disabled=True,
                              help="Ya está en tu lista")
                else:
                    if st.button("➕", key=f"add_{a['name']}", width="stretch",
                                 help="Agregar a mi lista"):
                        _agregar_a_watchlist(uid, a)
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
