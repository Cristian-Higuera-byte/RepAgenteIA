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
Datos y lógica del buscador (sin UI): lectura del catálogo de TODOS los instrumentos del broker (Capital.com o MT5) sin
esperar ni bloquear, búsqueda en vivo en el servidor del broker como respaldo del catálogo, categorías, filtro por
texto/categoría y alta de un activo en la watchlist del usuario. `_agregar_a_watchlist` lo reutiliza también mercados/.
La interfaz (modal) está en dialogo.py.

Con Capital.com el catálogo lo recorre en segundo plano `proveedores/capital_mt5_compat.py` (todo el árbol de mercados, no solo
los primeros niveles) y este módulo solo lo lee: abrir el buscador nunca espera a la red.
"""
import streamlit as st
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from herramientas.puente_mt5 import MT5_LOCK, inicializar_mt5
from herramientas import gestor_lista_activos as wl
from herramientas import permisos_plan

# Resultado de convertir el catálogo del broker al formato del buscador, para no rehacerlo en cada interacción:
# (huella del catálogo, lista de activos). La huella cambia cuando el catálogo cambia.
_CONVERTIDO: dict = {"huella": None, "activos": []}


# TITULO A ACTIVO

def _a_activo(s) -> dict:
    """Convierte un símbolo del broker (objeto con `name`, `description` y `path`) al diccionario del buscador.

    Tiene `name` (nombre exacto del broker, usado en el gráfico), `visible` (nombre mostrado), `desc` (descripción), `cat`
    (categoría) y `_k`, el texto ya en mayúsculas contra el que se compara lo que escribe el usuario."""
    visible = wl.nombre_visible(s.name)
    desc = (s.description or s.name).strip()
    return {
        "name": s.name,                                          # exacto (broker / gráfico)
        "visible": visible,                                      # nombre mostrado
        "desc": desc,
        "cat": wl.categoria_simbolo(getattr(s, "path", ""), s.name),
        "_k": f"{visible}\n{s.name}\n{desc}".upper(),
    }


# TITULO ESTADO BUSCADOR

def estado_buscador() -> tuple:
    """Devuelve `(activos, listo)` sin esperar a la red: `activos` es la lista de instrumentos conocida ahora (ordenada por nombre
    visible) y `listo` indica si es el catálogo completo (con Capital.com puede estar aún cargándose en segundo plano).

    Con MT5 consulta `symbols_get` bajo `MT5_LOCK` (la API no es thread-safe) y cachea el resultado 10 minutos."""
    leer = getattr(mt5, "catalogo_actual", None)
    if leer is None:
        return _simbolos_mt5(), True
    simbolos, listo = leer()
    huella = (len(simbolos), simbolos[0].name if simbolos else "", simbolos[-1].name if simbolos else "")
    if _CONVERTIDO["huella"] != huella:
        activos = [_a_activo(x) for x in simbolos]
        activos.sort(key=lambda x: x["visible"])
        _CONVERTIDO.update(huella=huella, activos=activos)
    return _CONVERTIDO["activos"], listo


# TITULO SIMBOLOS MT5

@st.cache_data(ttl=600, show_spinner=False)
def _simbolos_mt5() -> list[dict]:
    """Símbolos del terminal MT5 en el formato del buscador, cacheados 10 minutos. Lista vacía si MT5 no entrega símbolos."""
    inicializar_mt5()
    with MT5_LOCK:
        simbolos = mt5.symbols_get()
    salida = [_a_activo(x) for x in (simbolos or [])]
    salida.sort(key=lambda x: x["visible"])
    return salida


# TITULO CARGAR SIMBOLOS BROKER

def cargar_simbolos_broker() -> list[dict]:
    """Devuelve los símbolos del broker como lista de diccionarios (ver `_a_activo`), ordenados por nombre visible.

    No espera a la red: con Capital.com devuelve lo que ya se conoce del catálogo. Lista vacía si no hay ninguno."""
    return estado_buscador()[0]


# TITULO BUSCAR EN VIVO

def buscar_en_vivo(texto: str) -> list[dict]:
    """Busca `texto` directamente en el servidor del broker (Capital.com: `/markets?searchTerm=`) y devuelve los resultados en el
    formato del buscador. Sirve de respaldo para encontrar un instrumento aunque el catálogo aún se esté cargando o no lo incluya.
    Con MT5, o si no hay conexión, devuelve lista vacía."""
    buscar = getattr(mt5, "buscar_simbolos", None)
    if buscar is None:
        return []
    try:
        return [_a_activo(x) for x in buscar(texto)]
    except Exception:  # noqa: BLE001
        return []


# TITULO CATEGORIAS

def categorias(activos: list[dict]) -> list[str]:
    """Devuelve las categorías para el filtro: "Todo" seguido de las presentes en `activos`, ordenadas."""
    return ["Todo"] + sorted({a["cat"] for a in activos})


# TITULO FILTRAR

def filtrar(activos: list[dict], q: str, cat: str) -> list[dict]:
    """Filtra `activos` por categoría y por texto.

    `cat` en blanco o "Todo" no filtra por categoría. `q` se compara sin distinguir
    mayúsculas contra el nombre visible, el nombre exacto y la descripción. Los resultados cuyo nombre empieza por `q` van
    primero (SILVER antes que "Silverline Corp"). Devuelve la lista de coincidencias.
    """
    # Normaliza el texto de búsqueda
    q = (q or "").strip().upper()
    resultado = []
    for a in activos:
        # Descarta por categoría
        if cat and cat != "Todo" and a["cat"] != cat:
            continue
        # Descarta si el texto no aparece en ningún campo (`_k` ya trae nombre visible, nombre exacto y descripción en mayúsculas)
        if q and q not in a["_k"]:
            continue
        resultado.append(a)
    return ordenar_por_relevancia(resultado, q)


# TITULO ORDENAR POR RELEVANCIA

def ordenar_por_relevancia(resultados: list[dict], q: str) -> list[dict]:
    """Ordena `resultados` poniendo primero el nombre igual a `q`, luego los que empiezan por `q` y al final el resto; dentro de cada
    grupo se conserva el orden que traían. Sin texto buscado devuelve la lista tal cual."""
    q = (q or "").strip().upper()
    if not q:
        return resultados

    def peso(a: dict) -> int:
        """0 si el nombre (exacto o visible) es igual a lo buscado, 1 si empieza por ello, 2 en el resto."""
        nombre, visible = a["name"].upper(), a["visible"].upper()
        return 0 if q in (nombre, visible) else 1 if nombre.startswith(q) or visible.startswith(q) else 2
    return sorted(resultados, key=peso)


# TITULO AGREGAR A WATCHLIST

def _agregar_a_watchlist(uid, a: dict) -> bool:
    """Agrega el activo `a` a la lista de seguimiento del usuario `uid`. Devuelve True si lo agregó y False si el plan del usuario ya no deja
    agregar más (en ese caso muestra el aviso con qué plan permite más y no cambia nada).

    No llama a MT5 (la API no es thread-safe y chocaría con los fragmentos de precios en
    vivo, dejando la pantalla en blanco): usa la información ya cacheada del buscador y el
    precio real lo pone el fragmento `actualizar_precios_mt5` en el siguiente tick.
    Efectos secundarios: persiste el símbolo con `gestor_lista_activos.agregar_simbolo` y
    actualiza `datos_mercado_real` y `watchlist_simbolos` en `st.session_state`.
    """
    name = a["name"]
    # El plan limita cuántos activos puede tener el usuario en su lista (herramientas/permisos_plan.py)
    tope = permisos_plan.limite("activos_en_lista")
    lista_actual = st.session_state.get("watchlist_simbolos", [])
    if tope is not None and name not in lista_actual and len(lista_actual) >= tope:
        st.toast(permisos_plan.mensaje_bloqueo("activos_en_lista"), icon="⚠️")
        return False
    # Persiste el símbolo en la lista del usuario (en segundo plano: la fila se pinta de inmediato con datos de la sesión)
    wl.en_segundo_plano(wl.agregar_simbolo, uid, name)
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
    return True


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
