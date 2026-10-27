# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara gestor_lista_activos .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""
gestor_lista_activos.py
--------------------
Gestiona la lista de activos (watchlist) de cada usuario en Supabase
(tabla `watchlist_usuario`). Guarda el nombre EXACTO del símbolo de MT5
(con "..." en Forex/metales, con sufijo de bolsa en acciones, etc.).

Cada fila de `watchlist_usuario` tiene usuario_id, simbolo, favorito y
creado_en. Los favoritos son el subconjunto que se muestra en la barra
superior. Todas las funciones degradan con elegancia (lista vacía o False) si
Supabase no está configurado o la consulta falla. Las credenciales se leen de
.env (SUPABASE_URL y SUPABASE_KEY).
"""
import os
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

from dotenv import load_dotenv
from supabase import Client, create_client  # type: ignore[import-not-found]

load_dotenv()

# URL y clave de Supabase leídas del entorno (.env); vacías si no existen
_URL = os.environ.get("SUPABASE_URL", "")
_KEY = os.environ.get("SUPABASE_KEY", "")

# Cliente Supabase compartido del módulo; None si no hay credenciales o falla la conexión
_supabase: Optional[Client] = None
if _URL and _KEY:
    try:
        _supabase = create_client(_URL, _KEY)
    except Exception:
        _supabase = None

# Watchlist por defecto para usuarios nuevos (nombres EXACTOS del broker). Con Capital.com se usan sus nombres propios
# (el oro es GOLD y no hay sufijo "..."); con MT5 los de ese terminal.
if os.environ.get("PROVEEDOR", "mt5").strip().lower() == "capital":
    DEFAULTS = ["EURUSD", "GBPUSD", "USDJPY", "GOLD", "BTCUSD", "ETHUSD", "US30"]
else:
    DEFAULTS = ["EURUSD...", "GBPUSD...", "USDJPY...", "XAUUSD...", "BTCUSD", "ETHUSD", "US30"]


# Cola de un solo hilo para las escrituras en Supabase que no necesitan esperarse: así se hacen en el orden en que se pidieron
# (agregar y luego quitar el mismo símbolo no se cruzan) y sin que el clic del usuario espere la red.
_ESCRITOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pj-lista-activos")


# TITULO EN SEGUNDO PLANO

def en_segundo_plano(funcion: Callable, *argumentos) -> None:
    """Ejecuta `funcion(*argumentos)` (una escritura en Supabase) en un hilo aparte, en orden y sin esperar el resultado.

    La pantalla ya muestra el cambio (se hace sobre la sesión antes de persistir), así que el clic no espera a la base de datos.
    Las funciones de este módulo no lanzan excepciones: ante un fallo devuelven False y el cambio queda solo en la sesión."""
    _ESCRITOR.submit(funcion, *argumentos)


# TITULO NOMBRE VISIBLE

def nombre_visible(simbolo: str) -> str:
    """
    Devuelve el nombre limpio de un símbolo MT5 para mostrarlo en pantalla.

    Quita los puntos suspensivos "..." (Forex/metales) y el sufijo de bolsa de
    1 a 3 letras (.OQ, .N, .HK...). Solo presentación: para operar o consultar
    MT5 se debe usar siempre el nombre exacto original.
    """
    # Elimina los "..." propios del broker.
    s = (simbolo or "").replace("...", "")
    # Si queda un sufijo corto alfabético tras el último punto, se descarta.
    if "." in s:
        base, sufijo = s.rsplit(".", 1)
        if sufijo.isalpha() and 1 <= len(sufijo) <= 3:
            s = base
    return s


# Instrumentos que Capital.com publica con nombre propio (no con el XAU/XAG de MT5) y que son metales o energía.
_METALES = {"GOLD", "SILVER", "PLATINUM", "PALLADIUM", "COPPER", "ALUMINIUM", "ALUMINUM", "NICKEL", "ZINC", "LEAD", "TIN"}
_ENERGIA = {"OIL_CRUDE", "OIL_BRENT", "CRUDEOIL", "BRENT", "NATURALGAS", "NATGAS", "GASOLINE", "HEATINGOIL", "GAS_OIL"}


# TITULO SIN ACENTOS

def _sin_acentos(texto: str) -> str:
    """Devuelve `texto` en minúsculas y sin tildes, para comparar palabras clave sin que importe cómo estén escritas."""
    return "".join(c for c in unicodedata.normalize("NFD", (texto or "").lower()) if unicodedata.category(c) != "Mn")


# TITULO CATEGORIA SIMBOLO

def categoria_simbolo(path: str, name: str) -> str:
    """
    Clasifica un símbolo en una categoría legible (METALES, CRIPTO, FOREX, ENERGÍA, ÍNDICE, ACCIONES, ETF, BONOS,
    TASAS, MATERIAS PRIMAS, FUTUROS u OTROS).

    Recibe el 'path' del símbolo (carpeta del broker: la de MT5 o la que arma el catálogo de Capital.com) y su nombre, y
    busca palabras clave en ese orden de prioridad; el primer grupo que coincide gana. Reconoce los nombres propios de
    Capital.com (GOLD, SILVER, OIL_CRUDE…) y las carpetas en español o inglés, sin importar tildes ni mayúsculas.
    Devuelve "OTROS" si nada coincide.
    """
    # Normaliza: path en minúsculas y sin tildes, nombre en mayúsculas.
    p = _sin_acentos(path)
    n = (name or "").upper()
    carpeta = p.split("\\")[0]
    directorio = p.rsplit("\\", 1)[0] if "\\" in p else ""    # el path sin el último tramo, que es el propio símbolo
    base = n.split("_")[0]
    # Las acciones y los ETF se reconocen por su carpeta antes que por el nombre: el ticker de una acción puede parecerse al de
    # un metal o contener "gas" u "oil" sin serlo.
    if carpeta in ("stocks", "acciones", "shares"):
        return "ACCIONES"
    if carpeta.startswith("etf"):
        return "ETF"
    if n.startswith("XAU") or n.startswith("XAG") or "metal" in p or "gold" in p or n in _METALES or base in _METALES:
        return "METALES"
    if "crypto" in p or "cripto" in p:
        return "CRIPTO"
    if "forex" in p or "mb pro" in p or "currenc" in p or "divisa" in p:
        return "FOREX"
    if "oil" in directorio or "energ" in directorio or "gas" in directorio or n in _ENERGIA or n.startswith("OIL_"):
        return "ENERGÍA"
    if "indic" in p or "index" in p or "cash indices" in p:
        return "ÍNDICE"
    if "shares" in p or "stock" in p or "equit" in p or "accion" in p:
        return "ACCIONES"
    if "futures" in p or "futuro" in p:
        return "FUTUROS"
    if carpeta.startswith(("bond", "bono")):
        return "BONOS"
    if carpeta.startswith(("rate", "tasa", "interest")):
        return "TASAS"
    if carpeta.startswith(("commodit", "materia")):
        return "MATERIAS PRIMAS"
    return "OTROS"


# TITULO OBTENER WATCHLIST

def obtener_watchlist(usuario_id) -> list[str]:
    """
    Devuelve los símbolos de la watchlist del usuario, en orden de agregado.

    Consulta `watchlist_usuario` ordenando por `creado_en`. Devuelve lista vacía
    si no hay Supabase, falta el usuario o la consulta falla.
    """
    if _supabase is None or not usuario_id:
        return []
    try:
        r = (_supabase.table("watchlist_usuario")
             .select("simbolo")
             .eq("usuario_id", usuario_id)
             .order("creado_en")
             .execute())
        return [fila["simbolo"] for fila in (r.data or [])]
    except Exception:
        return []


# TITULO AGREGAR SIMBOLO

def agregar_simbolo(usuario_id, simbolo: str) -> bool:
    """
    Inserta un símbolo en la watchlist del usuario.

    Devuelve True si se insertó; False si faltan datos, no hay Supabase, ya
    existía (restricción unique) o falló la inserción. Efecto secundario:
    escritura en Supabase.
    """
    if _supabase is None or not usuario_id or not simbolo:
        return False
    try:
        _supabase.table("watchlist_usuario").insert(
            {"usuario_id": usuario_id, "simbolo": simbolo}).execute()
        return True
    except Exception:
        return False  # normalmente: ya existe (restricción unique)


# TITULO QUITAR SIMBOLO

def quitar_simbolo(usuario_id, simbolo: str) -> bool:
    """
    Elimina un símbolo de la watchlist del usuario.

    Devuelve True si la operación se ejecutó (aunque el símbolo no existiera) y
    False si falta Supabase/usuario o hubo error. Efecto secundario: borrado en
    Supabase.
    """
    if _supabase is None or not usuario_id:
        return False
    try:
        (_supabase.table("watchlist_usuario").delete()
         .eq("usuario_id", usuario_id).eq("simbolo", simbolo).execute())
        return True
    except Exception:
        return False


# TITULO SEMBRAR POR DEFECTO

def sembrar_por_defecto(usuario_id) -> list[str]:
    """
    Inserta la watchlist por defecto (`DEFAULTS`) para un usuario nuevo.

    Marca como favoritos los símbolos de `FAVORITOS_DEFAULT`. Los errores de
    inserción se ignoran en silencio. Devuelve siempre la lista de símbolos por
    defecto, tenga o no éxito la escritura. Efecto secundario: inserción masiva
    en Supabase.
    """
    if _supabase is None or not usuario_id:
        return list(DEFAULTS)
    try:
        # Conjunto de favoritos por defecto para marcar cada fila.
        favoritos_def = set(FAVORITOS_DEFAULT)
        filas = [{"usuario_id": usuario_id, "simbolo": s, "favorito": s in favoritos_def}
                 for s in DEFAULTS]
        # Inserta todas las filas en una sola llamada.
        _supabase.table("watchlist_usuario").insert(filas).execute()
    except Exception:
        pass
    return list(DEFAULTS)


# --- Favoritos (barra superior): subconjunto de la watchlist marcado con `favorito` ---
# Símbolos marcados como favoritos al sembrar la watchlist de un usuario nuevo
# (se define después de `sembrar_por_defecto`, pero se resuelve en tiempo de ejecución).
FAVORITOS_DEFAULT = ["BTCUSD", "ETHUSD", "GOLD", "EURUSD", "US30"] if DEFAULTS[0] == "EURUSD" else ["BTCUSD", "ETHUSD", "XAUUSD...", "EURUSD...", "US30"]


# TITULO OBTENER FAVORITOS

def obtener_favoritos(usuario_id) -> list[str]:
    """
    Devuelve los símbolos con `favorito = True` del usuario, en orden de agregado.

    Lista vacía si no hay Supabase, falta el usuario o la consulta falla.
    """
    if _supabase is None or not usuario_id:
        return []
    try:
        r = (_supabase.table("watchlist_usuario")
             .select("simbolo")
             .eq("usuario_id", usuario_id)
             .eq("favorito", True)
             .order("creado_en")
             .execute())
        return [fila["simbolo"] for fila in (r.data or [])]
    except Exception:
        return []


# TITULO MARCAR FAVORITO

def marcar_favorito(usuario_id, simbolo: str, valor: bool) -> bool:
    """
    Marca o desmarca (según `valor`) un símbolo de la watchlist como favorito.

    Devuelve True si el UPDATE se ejecutó y False si faltan datos, no hay
    Supabase o hubo error. Efecto secundario: actualización en Supabase.
    """
    if _supabase is None or not usuario_id or not simbolo:
        return False
    try:
        (_supabase.table("watchlist_usuario").update({"favorito": bool(valor)})
         .eq("usuario_id", usuario_id).eq("simbolo", simbolo).execute())
        return True
    except Exception:
        return False


# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara gestor_lista_activos .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
