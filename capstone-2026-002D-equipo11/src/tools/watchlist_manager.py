"""
watchlist_manager.py
--------------------
Gestiona la lista de activos (watchlist) de cada usuario en Supabase
(tabla `watchlist_usuario`). Guarda el nombre EXACTO del símbolo de MT5
(con "..." en Forex/metales, con sufijo de bolsa en acciones, etc.).
"""
import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client  # type: ignore[import-not-found]

load_dotenv()

_URL = os.environ.get("SUPABASE_URL", "")
_KEY = os.environ.get("SUPABASE_KEY", "")

_supabase: Optional[Client] = None
if _URL and _KEY:
    try:
        _supabase = create_client(_URL, _KEY)
    except Exception:
        _supabase = None

# Watchlist por defecto para usuarios nuevos (nombres EXACTOS del broker)
DEFAULTS = ["EURUSD...", "GBPUSD...", "USDJPY...", "XAUUSD...", "BTCUSD", "ETHUSD", "US30"]


def nombre_visible(simbolo: str) -> str:
    """Nombre limpio para mostrar: quita '...' y el sufijo de bolsa (.OQ, .N, .HK...)."""
    s = (simbolo or "").replace("...", "")
    if "." in s:
        base, suf = s.rsplit(".", 1)
        if suf.isalpha() and 1 <= len(suf) <= 3:
            s = base
    return s


def categoria_simbolo(path: str, name: str) -> str:
    """Categoría legible a partir del 'path' del símbolo en MT5 y su nombre."""
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


def _extraer_simbolos(rows) -> list[str]:
    """Convierte filas de Supabase en una lista de símbolos tipeada."""
    if not rows:
        return []
    simbolos: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            valor = row.get("simbolo")
            if isinstance(valor, str):
                simbolos.append(valor)
    return simbolos


def obtener_watchlist(usuario_id) -> list[str]:
    """Símbolos de la watchlist del usuario, en orden de agregado."""
    if _supabase is None or not usuario_id:
        return []
    try:
        r = (_supabase.table("watchlist_usuario")
             .select("simbolo")
             .eq("usuario_id", usuario_id)
             .order("creado_en")
             .execute())
        return _extraer_simbolos(r.data)
    except Exception:
        return []


def agregar_simbolo(usuario_id, simbolo: str) -> bool:
    """Agrega un símbolo a la watchlist del usuario. False si ya existía o falló."""
    if _supabase is None or not usuario_id or not simbolo:
        return False
    try:
        _supabase.table("watchlist_usuario").insert(
            {"usuario_id": usuario_id, "simbolo": simbolo}).execute()
        return True
    except Exception:
        return False  # normalmente: ya existe (restricción unique)


def quitar_simbolo(usuario_id, simbolo: str) -> bool:
    """Quita un símbolo de la watchlist del usuario."""
    if _supabase is None or not usuario_id:
        return False
    try:
        (_supabase.table("watchlist_usuario").delete()
         .eq("usuario_id", usuario_id).eq("simbolo", simbolo).execute())
        return True
    except Exception:
        return False


def sembrar_defaults(usuario_id) -> list[str]:
    """Inserta la watchlist por defecto para un usuario nuevo. Retorna los símbolos."""
    if _supabase is None or not usuario_id:
        return list(DEFAULTS)
    try:
        favs_def = set(FAVORITOS_DEFAULT)
        filas = [{"usuario_id": usuario_id, "simbolo": s, "favorito": s in favs_def}
                 for s in DEFAULTS]
        _supabase.table("watchlist_usuario").insert(filas).execute()
    except Exception:
        pass
    return list(DEFAULTS)


# --- Favoritos (barra superior): subconjunto de la watchlist marcado con `favorito` ---
FAVORITOS_DEFAULT = ["BTCUSD", "ETHUSD", "XAUUSD...", "EURUSD...", "US30"]


def obtener_favoritos(usuario_id) -> list[str]:
    """Símbolos marcados como favoritos del usuario, en orden de agregado."""
    if _supabase is None or not usuario_id:
        return []
    try:
        r = (_supabase.table("watchlist_usuario")
             .select("simbolo")
             .eq("usuario_id", usuario_id)
             .eq("favorito", True)
             .order("creado_en")
             .execute())
        return _extraer_simbolos(r.data)
    except Exception:
        return []


def marcar_favorito(usuario_id, simbolo: str, valor: bool) -> bool:
    """Marca o desmarca un símbolo de la watchlist como favorito."""
    if _supabase is None or not usuario_id or not simbolo:
        return False
    try:
        (_supabase.table("watchlist_usuario").update({"favorito": bool(valor)})
         .eq("usuario_id", usuario_id).eq("simbolo", simbolo).execute())
        return True
    except Exception:
        return False