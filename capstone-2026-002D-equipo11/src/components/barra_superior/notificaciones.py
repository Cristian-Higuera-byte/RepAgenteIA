# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara notificaciones .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Campana de notificaciones: insignia, lista desplegable (popover), avisos emergentes y vigilancia de avisos nuevos.

Lee las notificaciones desde core.notificaciones (p. ej. cuando el agente termina de
responder) y las muestra en la barra superior. Los estilos (clases nt-*, contenedor
notif_bell) están en estilos.css.
"""
import html
import time

import streamlit as st

from components.barra_superior.datos import ICONO_TIPO
from core import notificaciones


def usuario_id() -> str:
    """Devuelve el id del usuario en sesión como texto, o "local" si no hay usuario."""
    return str((st.session_state.get("usuario_info") or {}).get("id") or "local")


def hace(creada: float) -> str:
    """Devuelve el tiempo transcurrido desde `creada` (marca de tiempo Unix) en texto corto.

    Ejemplos: "ahora", "hace 5 min", "hace 2 h", "hace 3 d".
    """
    seg = max(0, int(time.time() - creada))
    if seg < 60:
        return "ahora"
    if seg < 3600:
        return f"hace {seg // 60} min"
    if seg < 86400:
        return f"hace {seg // 3600} h"
    return f"hace {seg // 86400} d"


def html_notificaciones(items: list) -> str:
    """Construye el HTML de la lista de notificaciones del desplegable.

    Recibe `items`, la lista de diccionarios de notificaciones (id, tipo, titulo, texto,
    creada, leida). Las no leídas llevan la clase `nueva` y un punto. Devuelve un mensaje
    vacío si la lista no tiene elementos. Todo el texto se escapa con `html.escape`.
    """
    if not items:
        return ("<div class='nt-vacio'>Sin notificaciones por ahora. Aquí te avisamos cuando el agente "
                "termine de responder.</div>")
    # Una fila por notificación
    filas = []
    for n in items:
        punto = "" if n["leida"] else "<span class='nt-punto'></span>"
        filas.append(
            f"<div class='nt-item{'' if n['leida'] else ' nueva'}'>"
            f"<div class='nt-ic'>{ICONO_TIPO.get(n['tipo'], '🔔')}</div>"
            f"<div class='nt-cuerpo'><div class='nt-titulo'>{html.escape(n['titulo'])}{punto}</div>"
            f"<div class='nt-texto'>{html.escape(n['texto'])}</div>"
            f"<div class='nt-hace'>{hace(n['creada'])}</div></div></div>"
        )
    return "".join(filas)


@st.fragment(run_every="3s")
def vigilar_notificaciones(usuario_id: str) -> None:
    """Fragmento que revisa cada 3 s (sin dibujar nada) si llegó un aviso nuevo.

    Recibe el id del usuario. Compara la última notificación con la guardada en
    `st.session_state["_notif_ultima_id"]` y solo si difieren reejecuta la app completa, para
    que aparezcan la insignia y el toast aunque el usuario esté en otra sección.
    """
    if notificaciones.ultima_id(usuario_id) != st.session_state.get("_notif_ultima_id"):
        st.rerun(scope="app")


def campana(usuario_id: str) -> None:
    """Dibuja la campana con insignia y la lista desplegable de notificaciones.

    Recibe el id del usuario. Guarda en sesión el id de la última notificación (para el
    fragmento vigilante), lanza un `st.toast` una sola vez por notificación nueva y sesión, y
    muestra un popover con la lista. Sus botones son reales: "Ver el chat del agente" marca
    todo como leído y navega a Trading; "Marcar como leídas" borra la lista. Al final arranca
    el fragmento `vigilar_notificaciones`.
    """
    # Recuerda la última notificación vista para que el vigilante detecte las nuevas
    st.session_state["_notif_ultima_id"] = notificaciones.ultima_id(usuario_id)
    items = notificaciones.listar(usuario_id, 8)
    sin_leer = notificaciones.no_leidas(usuario_id)

    # Aviso emergente, una sola vez por notificación y sesión.
    vistas = st.session_state.setdefault("_notif_toast", set())
    for n in reversed(items):
        if not n["leida"] and n["id"] not in vistas:
            vistas.add(n["id"])
            st.toast(f"**{n['titulo']}**\n\n{n['texto']}", icon=ICONO_TIPO.get(n["tipo"], "🔔"))

    # Contenedor con clave notif_bell: estilos.css posiciona la insignia sobre la campana
    with st.container(key="notif_bell"):
        # Insignia con el número de avisos sin leer (9+ si son diez o más)
        if sin_leer:
            st.html(f"<span class='nt-badge'>{sin_leer if sin_leer < 10 else '9+'}</span>")
        with st.popover("", icon=":material/notifications:"):
            # Cabecera del desplegable con contador de nuevas
            st.html(
                "<div class='nt-cab'>Notificaciones"
                + (f"<span class='nt-cuenta'>{sin_leer} nueva{'s' if sin_leer != 1 else ''}</span>" if sin_leer else "")
                + "</div>"
            )
            # Lista de notificaciones y, si hay, los botones de acción
            st.html(html_notificaciones(items))
            if items:
                if st.button("Ver el chat del agente", key="notif_ir", icon=":material/chat:", type="primary",
                             width="stretch"):
                    notificaciones.marcar_leidas(usuario_id)
                    st.session_state.nav_activo = "trading"
                    st.rerun()
                # Marcar como leídas = ya las viste: se eliminan de la lista (y desaparece la insignia).
                if st.button("Marcar como leídas", key="notif_leer", icon=":material/done_all:", width="stretch"):
                    notificaciones.limpiar(usuario_id)
                    st.rerun()
    # Arranca el fragmento que detecta avisos nuevos cada 3 s
    vigilar_notificaciones(usuario_id)


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara notificaciones .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
