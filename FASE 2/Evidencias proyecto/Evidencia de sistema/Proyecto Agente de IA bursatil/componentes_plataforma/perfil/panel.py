# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara panel .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Vista «Mi perfil»: cabecera con avatar y porcentaje de perfil completo, menú de secciones y formulario de la sección activa.

Se abre desde el menú del usuario de la barra superior («Mi perfil» y «Configuración», enlaces `?perfil=...` que procesa
acceso/pantalla.py). Estética de las plataformas de trading actuales: tarjeta de cabecera con insignias de estado y barra de
progreso, navegación vertical por secciones y formularios sobre tarjetas oscuras, como el resto de la plataforma.
"""
from typing import Any

import streamlit as st

from componentes_plataforma.agente_paneles.formato import escapar_html
from componentes_plataforma.perfil import almacen
from componentes_plataforma.perfil.datos import SECCIONES
from componentes_plataforma.perfil.estilos import CSS
from componentes_plataforma.perfil.secciones import dibujar
from componentes_plataforma.perfil.validacion import completitud, estado_verificacion, seccion_completa
from herramientas.puente_mt5 import NOMBRE_BROKER

# Clave de session_state con la sección abierta (id de datos.json).
CLAVE_SECCION = "perfil_seccion"


# TITULO IR A

def _ir_a(id_seccion: str) -> None:
    """Callback de los botones del menú: guarda la sección elegida (se ejecuta antes de redibujar la vista)."""
    st.session_state[CLAVE_SECCION] = id_seccion


# TITULO INICIALES

def _iniciales(nombre: str) -> str:
    """Iniciales (máximo dos) del nombre para el avatar; «U» si no hay nombre."""
    return "".join(p[0] for p in nombre.split()[:2]).upper() or "U"


# TITULO NOMBRES SUGERIDOS

def _nombres_sugeridos(usuario: dict[str, Any], perfil: dict[str, Any]) -> dict[str, str]:
    """Nombres y apellidos que se sugieren en el formulario cuando el perfil aún no los tiene: salen del nombre con el que se registró el usuario.

    Si el perfil ya tiene apellidos juntos (cuentas antiguas), el primero se sugiere como paterno y el resto como materno. Si no hay nada, se reparte el
    nombre de registro: con 2 palabras, nombre y apellido paterno; con 3, un nombre y dos apellidos; con 4 o más, los dos primeros son nombres y las
    dos últimas los apellidos. Es solo una sugerencia que el usuario puede corregir: no se guarda hasta que pulse «Guardar cambios».
    Devuelve un diccionario vacío si el perfil ya tiene apellido paterno o materno."""
    if perfil.get("apellido_paterno") or perfil.get("apellido_materno"):
        return {}
    if perfil.get("apellidos"):
        partes = str(perfil["apellidos"]).split(None, 1)
        return {"apellido_paterno": partes[0], "apellido_materno": partes[1] if len(partes) > 1 else ""}
    palabras = str(usuario.get("nombre") or "").split()
    if not palabras:
        return {}
    corte = 1 if len(palabras) <= 3 else len(palabras) - 2
    apellidos = palabras[corte:]
    return {"nombres": " ".join(palabras[:corte]), "apellido_paterno": apellidos[0] if apellidos else "", "apellido_materno": " ".join(apellidos[1:])}


# TITULO CABECERA

def _cabecera(usuario: dict[str, Any], perfil: dict[str, Any]) -> None:
    """Dibuja la tarjeta superior: avatar con iniciales, nombre, correo, insignias (verificación y bróker) y progreso del perfil."""
    nombre = f"{perfil.get('nombres') or ''} {perfil.get('apellidos') or ''}".strip() or usuario.get("nombre") or "Usuario"
    porcentaje, faltan = completitud(perfil)
    clave, texto = estado_verificacion(perfil)
    pista = (f"Te faltan {len(faltan)} datos para completar tu perfil." if faltan
             else "Tu perfil está completo. Mantén tus datos al día.")
    st.html(
        "<div class='perfil-cabecera'>"
        f"<div class='perfil-avatar'>{escapar_html(_iniciales(nombre))}</div>"
        "<div class='perfil-identidad'>"
        f"<div class='perfil-nombre'>{escapar_html(nombre)}</div>"
        f"<div class='perfil-correo'>{escapar_html(usuario.get('email', ''))}</div>"
        "<div class='perfil-insignias'>"
        f"<span class='perfil-insignia perfil-{clave}'>{escapar_html(texto)}</span>"
        f"<span class='perfil-insignia perfil-broker'>Cuenta en {escapar_html(NOMBRE_BROKER)}</span></div></div>"
        "<div class='perfil-progreso'>"
        f"<div class='perfil-progreso-texto'><span>Perfil completo</span><b>{porcentaje} %</b></div>"
        f"<div class='perfil-barra'><div class='perfil-barra-relleno' style='width:{porcentaje}%'></div></div>"
        f"<div class='perfil-progreso-pista'>{escapar_html(pista)}</div></div></div>"
    )


# TITULO MENU

def _menu(perfil: dict[str, Any], activa: str) -> None:
    """Dibuja el menú vertical de secciones; la activa va resaltada y las secciones con todos sus datos llevan una marca ✓."""
    with st.container(key="perfil_menu"):
        for s in SECCIONES:
            completa = seccion_completa(s["id"], perfil)
            etiqueta = s["titulo"] + ("  ✓" if completa else "")
            st.button(etiqueta, key=f"perfil_menu_{s['id']}", icon=f":material/{s['icono']}:", width="stretch",
                      type="primary" if s["id"] == activa else "secondary", on_click=_ir_a, args=(s["id"],))


# TITULO RENDERIZAR PANEL PERFIL

def renderizar_panel_perfil(main: Any = None) -> None:
    """Dibuja la vista de perfil completa. `main` se acepta por compatibilidad con los demás paneles y no se usa.

    Lee el perfil del usuario en sesión desde el almacén (Supabase o archivo local), dibuja la cabecera, el menú y la
    sección activa (`st.session_state.perfil_seccion`, «personal» por defecto)."""
    st.html(CSS)
    usuario = st.session_state.get("usuario_informacion") or {}
    perfil = almacen.leer(usuario.get("id") or "local")
    activa = st.session_state.setdefault(CLAVE_SECCION, "personal")
    with st.container(key="perfil_contenedor"):
        _cabecera(usuario, perfil)
        izq, der = st.columns([1, 3.3], gap="medium")
        with izq:
            _menu(perfil, activa)
        with der:
            with st.container(key="perfil_tarjeta"):
                dibujar(activa, usuario, {**perfil, **_nombres_sugeridos(usuario, perfil)})


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara panel .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
