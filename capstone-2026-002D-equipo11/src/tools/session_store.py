"""
session_store.py
----------------
Almacén de sesiones EN MEMORIA del servidor. Vive mientras el proceso de
Streamlit (la consola) esté encendido; al apagarlo, se borra todo.

Se combina con un token en la URL (?s=<token>) que sí sobrevive al F5:
  - F5 del navegador  -> la URL conserva el token -> el servidor lo encuentra
                         aquí y restaura la sesión (sigues dentro).
  - Apagar la consola -> este diccionario se vacía -> el token queda inválido
                         -> pide login de nuevo.
  - Cerrar sesión     -> se elimina el token de aquí.
"""
import secrets

# {token: {"id":..., "nombre":..., "email":...}}
_sesiones: dict[str, dict] = {}


def crear(usuario: dict) -> str:
    """Crea un token nuevo para el usuario y lo guarda. Retorna el token."""
    token = secrets.token_urlsafe(24)
    _sesiones[token] = usuario
    return token


def obtener(token: str) -> dict | None:
    """Retorna el usuario asociado al token, o None si no existe."""
    if not token:
        return None
    return _sesiones.get(token)


def eliminar(token: str) -> None:
    """Elimina el token (cerrar sesión)."""
    if token:
        _sesiones.pop(token, None)