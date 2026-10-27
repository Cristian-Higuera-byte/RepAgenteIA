# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------- INICIO Piña y Jara almacen_sesiones .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
almacen_sesiones.py
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

# Diccionario en memoria (se pierde al apagar el proceso) con la forma
# {token: {"id":..., "nombre":..., "email":...}}
_sesiones: dict[str, dict] = {}

# Datos que acompañan a cada sesión y deben sobrevivir a un F5 o a un enlace del menú (que recargan la página y vacían
# `st.session_state`): por ejemplo la cuenta elegida, demo o real. Forma: {token: {clave: valor}}
_datos: dict[str, dict] = {}


# TITULO CREAR

def crear(usuario: dict) -> str:
    """Crea un token aleatorio seguro (secrets) para el usuario, lo guarda en memoria y lo devuelve.

    `usuario` es el dict con id, nombre y email del usuario autenticado.
    """
    token = secrets.token_urlsafe(24)
    _sesiones[token] = usuario
    return token


# TITULO OBTENER

def obtener(token: str) -> dict | None:
    """Retorna el usuario asociado al token, o None si no existe."""
    if not token:
        return None
    return _sesiones.get(token)


# TITULO GUARDAR DATO

def guardar_dato(token: str, clave: str, valor) -> None:
    """Guarda un dato junto a la sesión del token (no hace nada si el token no existe)."""
    if token and token in _sesiones:
        _datos.setdefault(token, {})[clave] = valor


# TITULO LEER DATO

def leer_dato(token: str, clave: str, defecto=None):
    """Devuelve el dato guardado junto a la sesión del token, o `defecto` si no hay."""
    if not token or token not in _sesiones:
        return defecto
    return _datos.get(token, {}).get(clave, defecto)


# TITULO ELIMINAR

def eliminar(token: str) -> None:
    """Elimina el token (cerrar sesión) y los datos que guardaba."""
    if token:
        _sesiones.pop(token, None)
        _datos.pop(token, None)


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara almacen_sesiones .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
