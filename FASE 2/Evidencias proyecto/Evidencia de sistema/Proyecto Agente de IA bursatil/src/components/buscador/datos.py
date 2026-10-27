# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara datos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
buscador/datos.py
-----------------
Datos y lógica del buscador (sin UI): carga de TODOS los símbolos del broker MT5
(cacheada 10 min), categorías, filtro por texto/categoría y alta de un activo en la
watchlist del usuario. `_agregar_a_watchlist` lo reutiliza también mercados_panel.py.
La interfaz (modal) está en dialogo.py.
"""
import streamlit as st
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from tools.puente_mt5 import MT5_LOCK, inicializar_mt5
from tools import gestor_lista_activos as wl


@st.cache_data(ttl=600, show_spinner=False)
def cargar_simbolos_broker() -> list[dict]:
    """Devuelve todos los símbolos del broker MT5 como lista de diccionarios.

    Cada elemento tiene `name` (nombre exacto de MT5, usado en el gráfico), `visible` (nombre
    mostrado), `desc` (descripción) y `cat` (categoría). La lista se ordena por nombre
    visible. El resultado se cachea 10 minutos con `st.cache_data`. Efectos secundarios:
    inicializa MT5 y consulta `symbols_get` bajo `MT5_LOCK` (la API no es thread-safe).
    Devuelve lista vacía si MT5 no entrega símbolos.
    """
    # Asegura la conexión y consulta todos los símbolos con el candado de MT5
    inicializar_mt5()
    with MT5_LOCK:
        simbolos = mt5.symbols_get()
    # Normaliza cada símbolo al formato propio del buscador
    salida: list[dict] = []
    if simbolos:
        for s in simbolos:
            salida.append({
                "name": s.name,                                  # exacto (MT5 / gráfico)
                "visible": wl.nombre_visible(s.name),            # nombre mostrado
                "desc": (s.description or s.name).strip(),
                "cat": wl.categoria_simbolo(getattr(s, "path", ""), s.name),
            })
    # Orden alfabético por el nombre que ve el usuario
    salida.sort(key=lambda x: x["visible"])
    return salida


def categorias(activos: list[dict]) -> list[str]:
    """Devuelve las categorías para el filtro: "Todo" seguido de las presentes en `activos`, ordenadas."""
    return ["Todo"] + sorted({a["cat"] for a in activos})


def filtrar(activos: list[dict], q: str, cat: str) -> list[dict]:
    """Filtra `activos` por categoría y por texto.

    `cat` en blanco o "Todo" no filtra por categoría. `q` se compara sin distinguir
    mayúsculas contra el nombre visible, el nombre exacto y la descripción. Devuelve la
    lista de coincidencias conservando el orden original.
    """
    # Normaliza el texto de búsqueda
    q = (q or "").strip().upper()
    res = []
    for a in activos:
        # Descarta por categoría
        if cat and cat != "Todo" and a["cat"] != cat:
            continue
        # Descarta si el texto no aparece en ningún campo
        if q and q not in a["visible"].upper() and q not in a["name"].upper() and q not in a["desc"].upper():
            continue
        res.append(a)
    return res


def _agregar_a_watchlist(uid, a: dict):
    """Agrega el activo `a` a la lista de seguimiento del usuario `uid`.

    No llama a MT5 (la API no es thread-safe y chocaría con los fragmentos de precios en
    vivo, dejando la pantalla en blanco): usa la información ya cacheada del buscador y el
    precio real lo pone el fragmento `actualizar_precios_mt5` en el siguiente tick.
    Efectos secundarios: persiste el símbolo con `gestor_lista_activos.agregar_simbolo` y
    actualiza `datos_mercado_real` y `watchlist_simbolos` en `st.session_state`.
    """
    # Persiste el símbolo en la lista del usuario
    name = a["name"]
    wl.agregar_simbolo(uid, name)
    # Siembra datos provisionales en sesión para que la fila se pinte de inmediato
    datos = st.session_state.setdefault("datos_mercado_real", {})
    if name not in datos:
        datos[name] = {
            "nombre": a.get("desc") or a.get("visible") or name,
            "mercado": a.get("cat", "OTROS"),
            "precio": 0.0,
            "var": "+0.00 (0.00%)",
            "sube": True,
        }
    # Refleja el alta en la lista de la sesión actual
    lista = st.session_state.setdefault("watchlist_simbolos", [])
    if name not in lista:
        lista.append(name)


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara datos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
