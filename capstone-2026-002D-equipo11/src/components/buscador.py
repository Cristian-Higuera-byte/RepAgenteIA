"""
buscador.py
-----------
Buscador de activos estilo XM: modal (st.dialog) que busca entre TODOS los
símbolos del broker MT5 (~688), con filtro por categoría. Cada resultado se
puede "Abrir" (cargar en el gráfico) o "➕ Agregar" a la lista del usuario
(se guarda en Supabase vía watchlist_manager).
"""
import streamlit as st
import MetaTrader5 as mt5  # type: ignore[import-untyped]

from tools.mt5_bridge import MT5_LOCK, inicializar_mt5
from tools import watchlist_manager as wl

_PASO_RESULTADOS = 40  # cuántos se revelan al inicio y por cada "Ver más"


@st.cache_data(ttl=600, show_spinner=False)
def cargar_simbolos_broker() -> list[dict]:
    """Todos los símbolos del broker MT5: {name, visible, desc, cat}. Cache 10 min."""
    inicializar_mt5()
    with MT5_LOCK:
        simbolos = mt5.symbols_get()
    salida: list[dict] = []
    if simbolos:
        for s in simbolos:
            salida.append({
                "name": s.name,                                  # exacto (MT5 / gráfico)
                "visible": wl.nombre_visible(s.name),            # nombre mostrado
                "desc": (s.description or s.name).strip(),
                "cat": wl.categoria_simbolo(getattr(s, "path", ""), s.name),
            })
    salida.sort(key=lambda x: x["visible"])
    return salida


def _categorias(activos: list[dict]) -> list[str]:
    return ["Todo"] + sorted({a["cat"] for a in activos})


def _filtrar(activos: list[dict], q: str, cat: str) -> list[dict]:
    q = (q or "").strip().upper()
    res = []
    for a in activos:
        if cat and cat != "Todo" and a["cat"] != cat:
            continue
        if q and q not in a["visible"].upper() and q not in a["name"].upper() and q not in a["desc"].upper():
            continue
        res.append(a)
    return res


def _agregar_a_watchlist(uid, a: dict):
    """Agrega el activo a la lista SIN llamar a MT5 (la API no es thread-safe y
    chocaría con los fragmentos de precios en vivo → pantalla en blanco).
    Se usa la info ya cacheada del buscador; el precio real lo pone el fragmento
    `actualizar_precios_mt5` en el siguiente tick."""
    name = a["name"]
    wl.agregar_simbolo(uid, name)
    datos = st.session_state.setdefault("datos_mercado_real", {})
    if name not in datos:
        datos[name] = {
            "nombre": a.get("desc") or a.get("visible") or name,
            "mercado": a.get("cat", "OTROS"),
            "precio": 0.0,
            "var": "+0.00 (0.00%)",
            "sube": True,
        }
    lista = st.session_state.setdefault("watchlist_simbolos", [])
    if name not in lista:
        lista.append(name)


def abrir_buscador():
    """Marca que el diálogo debe mostrarse (se renderiza en app.py con
    `render_buscador`). Este patrón (bandera + render en el script principal)
    evita que el diálogo choque con los fragmentos de auto-refresco y deje la
    pantalla en blanco al interactuar dentro."""
    st.session_state.mostrar_buscador = True


def _cerrar_buscador():
    st.session_state.mostrar_buscador = False


def render_buscador():
    """Llamar UNA vez al final de app.py: abre el diálogo si la bandera está activa."""
    if st.session_state.get("mostrar_buscador"):
        _dialogo_buscador()


@st.dialog("Buscar activo", width="large", on_dismiss=_cerrar_buscador)
def _dialogo_buscador():
    activos = cargar_simbolos_broker()
    if not activos:
        st.warning("No se pudieron cargar los símbolos de MT5. ¿Está abierto el terminal?")
        return

    q = st.text_input("Buscar", placeholder="Símbolo o nombre, ej. AAPL, EUR, Bitcoin…",
                      label_visibility="collapsed", key="buscar_q")
    cat = st.segmented_control("Categoría", _categorias(activos), default="Todo",
                               label_visibility="collapsed", key="buscar_cat")

    resultados = _filtrar(activos, q, cat or "Todo")

    # Revelado progresivo: se reinicia al cambiar la búsqueda o la categoría.
    filtro_actual = (q.strip().upper(), cat or "Todo")
    if st.session_state.get("_buscar_filtro") != filtro_actual:
        st.session_state._buscar_filtro = filtro_actual
        st.session_state._buscar_limite = _PASO_RESULTADOS
    limite = st.session_state.get("_buscar_limite", _PASO_RESULTADOS)
    mostrados = min(limite, len(resultados))

    st.caption(f"{len(resultados)} de {len(activos)} activos"
               + (f" · mostrando {mostrados}" if len(resultados) > mostrados else ""))

    en_lista = set(st.session_state.get("watchlist_simbolos", []))
    uid = (st.session_state.get("usuario_info") or {}).get("id")

    with st.container(height=400):
        for a in resultados[:mostrados]:
            c_info, c_abrir, c_add = st.columns([6, 1.2, 1.2], vertical_alignment="center")
            with c_info:
                st.markdown(
                    f"**{a['visible']}** · <span style='color:#8b949e; font-size:11px;'>"
                    f"{a['cat']}</span><br>"
                    f"<span style='color:#8b949e; font-size:12px;'>{a['desc']}</span>",
                    unsafe_allow_html=True,
                )
            with c_abrir:
                if st.button("Abrir", key=f"open_{a['name']}", width="stretch"):
                    # Abrir SÍ cierra el diálogo y refresca la app (carga el gráfico).
                    st.session_state.activo_seleccionado = a["name"]
                    st.session_state.mostrar_buscador = False
                    st.rerun()
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