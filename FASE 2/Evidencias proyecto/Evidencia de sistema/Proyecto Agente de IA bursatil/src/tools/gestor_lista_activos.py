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
from typing import Optional

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

# Watchlist por defecto para usuarios nuevos (nombres EXACTOS del broker)
DEFAULTS = ["EURUSD...", "GBPUSD...", "USDJPY...", "XAUUSD...", "BTCUSD", "ETHUSD", "US30"]


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
        base, suf = s.rsplit(".", 1)
        if suf.isalpha() and 1 <= len(suf) <= 3:
            s = base
    return s


def categoria_simbolo(path: str, name: str) -> str:
    """
    Clasifica un símbolo en una categoría legible (METALES, CRIPTO, FOREX,
    ENERGÍA, ÍNDICE, ACCIONES, FUTUROS u OTROS).

    Recibe el 'path' del símbolo en MT5 (carpeta del broker) y su nombre, y
    busca palabras clave en ese orden de prioridad; el primer grupo que coincide
    gana. Devuelve "OTROS" si nada coincide.
    """
    # Normaliza: path en minúsculas, nombre en mayúsculas.
    p = (path or "").lower()
    n = (name or "").upper()
    if n.startswith("XAU") or n.startswith("XAG") or "metal" in p or "gold" in p:
        return "METALES"
    if "crypto" in p or "cripto" in p:
        return "CRIPTO"
    if "forex" in p or "mb pro" in p or "currenc" in p:
        return "FOREX"
    if "oil" in p or "energ" in p or "gas" in p:
        return "ENERGÍA"
    if "indic" in p or "index" in p or "cash indices" in p:
        return "ÍNDICE"
    if "shares" in p or "stock" in p or "equit" in p:
        return "ACCIONES"
    if "futures" in p or "futuro" in p:
        return "FUTUROS"
    return "OTROS"


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
        return [row["simbolo"] for row in (r.data or [])]
    except Exception:
        return []


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


def sembrar_defaults(usuario_id) -> list[str]:
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
        favs_def = set(FAVORITOS_DEFAULT)
        filas = [{"usuario_id": usuario_id, "simbolo": s, "favorito": s in favs_def}
                 for s in DEFAULTS]
        # Inserta todas las filas en una sola llamada.
        _supabase.table("watchlist_usuario").insert(filas).execute()
    except Exception:
        pass
    return list(DEFAULTS)


# --- Favoritos (barra superior): subconjunto de la watchlist marcado con `favorito` ---
# Símbolos marcados como favoritos al sembrar la watchlist de un usuario nuevo
# (se define después de `sembrar_defaults`, pero se resuelve en tiempo de ejecución).
FAVORITOS_DEFAULT = ["BTCUSD", "ETHUSD", "XAUUSD...", "EURUSD...", "US30"]


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
        return [row["simbolo"] for row in (r.data or [])]
    except Exception:
        return []


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
