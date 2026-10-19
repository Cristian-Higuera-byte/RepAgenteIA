# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara estado .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Favoritos del usuario: viven en `st.session_state.favoritos` y se guardan por usuario en Supabase
(columna `favorito` de watchlist_usuario, vía herramientas/gestor_lista_activos).

Aquí no se dibuja nada: solo se mantiene la lista y se sincroniza con la base de datos.
"""
from __future__ import annotations

import streamlit as st

# Gestor de la watchlist del usuario en Supabase (lectura y marcado de favoritos).
from tools import gestor_lista_activos as wl

# Máximo de favoritos permitidos.
FAVORITOS_MAX = 6       # tope de favoritos por usuario (solo caben 6 en una fila)
# Favoritos iniciales cuando el usuario aún no tiene ninguno guardado.
FAVORITOS_DEFAULT = wl.FAVORITOS_DEFAULT


def _uid():
    """Devuelve el id del usuario autenticado (de `usuario_info` en session_state) o None si no hay sesión."""
    # `usuario_info` puede faltar o no ser un diccionario; se tolera ambos casos.
    usuario = st.session_state.get("usuario_info") or {}
    return usuario.get("id") if isinstance(usuario, dict) else None


def inicializar_favoritos():
    """Carga los favoritos del usuario desde Supabase (una vez por sesión)."""
    if "favoritos" not in st.session_state:
        # Consulta a Supabase; si no hay registros se usan los favoritos por defecto.
        favs = wl.obtener_favoritos(_uid())
        st.session_state.favoritos = favs if favs else list(FAVORITOS_DEFAULT)


def agregar_favorito(ticker: str):
    """Agrega un activo a favoritos (respetando el máximo y sin duplicar)."""
    # Garantiza que la lista exista antes de modificarla.
    inicializar_favoritos()
    # Nombre sin puntos suspensivos para los mensajes al usuario.
    limpio = ticker.replace("...", "")
    # Evita duplicados.
    if ticker in st.session_state.favoritos:
        st.toast(f"⭐ {limpio} ya está en tus favoritos")
        return
    # Respeta el tope de favoritos.
    if len(st.session_state.favoritos) >= FAVORITOS_MAX:
        st.toast(f"⚠️ Máximo {FAVORITOS_MAX} favoritos. Quita uno primero.")
        return
    # Añade en memoria y persiste en Supabase.
    st.session_state.favoritos.append(ticker)
    wl.marcar_favorito(_uid(), ticker, True)
    st.toast(f"⭐ {limpio} agregado a favoritos")


def quitar_favorito(ticker: str):
    """Quita un activo de favoritos en session_state y lo desmarca en Supabase (no hace nada si no estaba)."""
    inicializar_favoritos()
    if ticker in st.session_state.favoritos:
        st.session_state.favoritos.remove(ticker)
        wl.marcar_favorito(_uid(), ticker, False)


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara estado .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
