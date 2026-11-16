# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara navegacion .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Navegación sin recargar entre la portada, el inicio de sesión, el registro y «Olvidé mi contraseña», y entre las opciones del menú del usuario.

Los enlaces entre esas pantallas (`?acceso=entrar`, `?acceso=crear`, `./`...) recargaban toda la página y dejaban ver el esqueleto gris de Streamlit al volver a arrancar.
El componente de estatico/navegacion.js intercepta esos clics y avisa a Python; aquí se traduce el destino a parámetros de la dirección y Streamlit dibuja la pantalla
nueva en la misma sesión, sin recarga. Un clic con Ctrl, Mayús o el botón medio sigue abriendo el enlace normal.

Con la sesión iniciada, el mismo componente atiende los enlaces del menú del usuario (`?perfil=...`, `?cuenta=...`, `?cuentas=1`): como la sesión ya no viaja en la
dirección, un enlace normal obliga a recargar la página, volver a levantar el terminal y validar la cookie; así se abre Perfil o Configuración al instante.
"""
from pathlib import Path
from urllib.parse import parse_qs

import streamlit as st

from componentes_plataforma._estaticos import texto

# Claves del componente en `st.session_state` (una para las pantallas de acceso y otra para el menú de la aplicación) y carpeta del script.
_CLAVE = "pj_navegacion_acceso"
_CLAVE_APP = "pj_navegacion_app"
_ESTATICO = Path(__file__).parent / "estatico"

# El componente se declara una sola vez al importar el módulo (no dentro de la función, para no registrarlo dos veces).
_COMPONENTE = st.components.v2.component("pj_navegacion_acceso", html="<span></span>", js=texto(_ESTATICO / "navegacion.js") + "\n", isolate_styles=False)


# TITULO AL NAVEGAR

def _al_navegar() -> None:
    """Cambia los parámetros de la dirección según el enlace pulsado (`?acceso=crear&plan=pro` → acceso y plan; `./` → ninguno, la portada).

    Solo se aceptan las claves `acceso` y `plan` (pantallas de acceso) y `perfil`, `cuenta` y `cuentas` (menú del usuario); cualquier otra se ignora. Streamlit vuelve a
    ejecutar la página con la dirección nueva."""
    destino = str((st.session_state.get(_CLAVE) or {}).get("destino") or (st.session_state.get(_CLAVE_APP) or {}).get("destino") or "")
    if not destino:
        return
    pedidos = parse_qs(destino[1:] if destino.startswith("?") else "")
    st.query_params.clear()
    for clave in ("acceso", "plan", "perfil", "cuenta", "cuentas"):
        if pedidos.get(clave):
            st.query_params[clave] = pedidos[clave][0]


# TITULO MONTAR

def montar() -> None:
    """Pone en la pantalla el componente que evita la recarga al pasar entre las pantallas de acceso; va una vez, antes de dibujarlas. No devuelve nada."""
    _COMPONENTE(key=_CLAVE, data={"prefijos": ["?acceso="], "portada": True}, on_destino_change=_al_navegar)


# TITULO MONTAR MENU DE LA APLICACION

def montar_menu_aplicacion() -> None:
    """Pone en la pantalla el componente que abre Perfil, Configuración y las cuentas del menú del usuario sin recargar la página; va una vez, con la sesión iniciada."""
    _COMPONENTE(key=_CLAVE_APP, data={"prefijos": ["?perfil=", "?cuenta=", "?cuentas="], "portada": False}, on_destino_change=_al_navegar)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara navegacion .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
