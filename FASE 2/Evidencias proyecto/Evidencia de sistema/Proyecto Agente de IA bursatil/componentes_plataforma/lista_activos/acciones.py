# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara acciones .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Acciones de la lista de activos: favoritos (con respaldo si no existe el módulo) y quitar un símbolo.

Centraliza las operaciones que cambian la lista o los favoritos del usuario, para que fila.py solo
dispare la acción y relance la app.
"""
import streamlit as st

# Implementación real de favoritos; se reexporta aquí porque otros módulos las importan desde acciones.py.
# Si este import fallara se detiene la carga en vez de dejar los favoritos sin funcionar en silencio.
from componentes_plataforma.favoritos import agregar_favorito, quitar_favorito  # noqa: F401


# TITULO QUITAR DE LISTA

def quitar_de_lista(ticker: str):
    """Quita un símbolo de la watchlist del usuario (Supabase + sesión).

    Elimina `ticker` en la base de datos y en session_state (datos de mercado, lista de símbolos y
    favoritos). Si era el activo seleccionado, elige otro de los restantes (o EURUSD... si no queda ninguno).
    """
    # Importación diferida para no cargar el gestor de base de datos hasta que se necesite.
    from herramientas import gestor_lista_activos as wl
    # Id del usuario actual (None si no hay sesión).
    uid = (st.session_state.get("usuario_informacion") or {}).get("id")
    # Borra el símbolo de la watchlist persistida (sin esperar a la red: la sesión se actualiza justo abajo).
    wl.en_segundo_plano(wl.quitar_simbolo, uid, ticker)
    st.session_state.get("datos_mercado_real", {}).pop(ticker, None)
    # Limpia la lista de símbolos en sesión.
    lst = st.session_state.get("watchlist_simbolos", [])
    if ticker in lst:
        lst.remove(ticker)
    # También lo quita de favoritos si estaba.
    favoritos = st.session_state.get("favoritos", [])
    if ticker in favoritos:
        favoritos.remove(ticker)
    # Si el activo eliminado estaba abierto en el gráfico, se cambia a otro disponible.
    if st.session_state.get("activo_seleccionado") == ticker:
        restantes = list(st.session_state.get("datos_mercado_real", {}).keys())
        st.session_state.activo_seleccionado = restantes[0] if restantes else "EURUSD..."


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara acciones .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
