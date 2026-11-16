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

Lee las notificaciones desde nucleo_agente.notificaciones (p. ej. cuando el agente termina de
responder) y las muestra en la barra superior. Los estilos (clases nt-*, contenedor
notificacion_campana) están en estilos.css.
"""
import html
import time

import streamlit as st

from componentes_plataforma.barra_superior.datos import ICONO_TIPO
from componentes_plataforma.refresco_fragmentos import fragmento_con_refresco, pedir_refresco
from herramientas import avisos_usuario
from nucleo_agente import notificaciones


# TITULO USUARIO ID

def usuario_id() -> str:
    """Devuelve el id del usuario en sesión como texto, o "local" si no hay usuario."""
    return str((st.session_state.get("usuario_informacion") or {}).get("id") or "local")


# TITULO HACE

def hace(creada: float) -> str:
    """Devuelve el tiempo transcurrido desde `creada` (marca de tiempo Unix) en texto corto.

    Ejemplos: "ahora", "hace 5 min", "hace 2 h", "hace 3 d".
    """
    segundos = max(0, int(time.time() - creada))
    if segundos < 60:
        return "ahora"
    if segundos < 3600:
        return f"hace {segundos // 60} min"
    if segundos < 86400:
        return f"hace {segundos // 3600} h"
    return f"hace {segundos // 86400} d"


# TITULO HTML NOTIFICACIONES

def html_notificaciones(elementos: list) -> str:
    """Construye el HTML de la lista de notificaciones del desplegable.

    Recibe `items`, la lista de diccionarios de notificaciones (id, tipo, titulo, texto,
    creada, leida). Las no leídas llevan la clase `nueva` y un punto. Devuelve un mensaje
    vacío si la lista no tiene elementos. Todo el texto se escapa con `html.escape`.
    """
    if not elementos:
        return ("<div class='notificacion-vacio'>Sin notificaciones por ahora. Aquí te avisamos de las respuestas y órdenes del agente, "
                "del cierre de tus posiciones y de tus alertas de precio.</div>")
    # Una fila por notificación
    filas = []
    for n in elementos:
        punto = "" if n["leida"] else "<span class='notificacion-punto'></span>"
        filas.append(
            f"<div class='notificacion-elemento{'' if n['leida'] else ' nueva'}'>"
            f"<div class='notificacion-icono'>{ICONO_TIPO.get(n['tipo'], '🔔')}</div>"
            f"<div class='notificacion-cuerpo'><div class='notificacion-titulo'>{html.escape(n['titulo'])}{punto}</div>"
            f"<div class='notificacion-texto'>{html.escape(n['texto'])}</div>"
            f"<div class='notificacion-hace'>{hace(n['creada'])}</div></div></div>"
        )
    return "".join(filas)


# TITULO VIGILAR NOTIFICACIONES

@st.fragment(run_every="3s")
def vigilar_notificaciones(usuario_id: str) -> None:
    """Fragmento que cada 3 s (sin dibujar nada) genera los avisos de posiciones y alertas de precio y revisa si llegó un aviso nuevo.

    Recibe el id del usuario. Compara la última notificación con la guardada en
    `st.session_state["_notificacion_ultima_id"]` y solo si difieren pide refrescar la campana (su fragmento, no la página completa), para
    que aparezcan la insignia y el toast aunque el usuario esté en otra sección.
    """
    avisos_usuario.revisar(usuario_id)   # cierres de posiciones y alertas de precio (cada 10 s por cuenta, sin importar cuántas pestañas haya)
    ultima = notificaciones.ultima_id(usuario_id)
    if ultima != st.session_state.get("_notificacion_ultima_id") and ultima != st.session_state.get("_notificacion_pedida"):
        # Aviso nuevo: solo se refresca la campana (insignia, lista y aviso emergente), sin reejecutar la página; si el refresco no llegara, el siguiente cambio de sección o
        # la próxima pasada completa lo muestra.
        st.session_state["_notificacion_pedida"] = ultima
        pedir_refresco("campana", marca=f"aviso-{ultima}")


# TITULO DESTINO DEL AVISO

def _destino_del_aviso(tipo: str) -> tuple[str, str, str]:
    """Adónde lleva el botón principal de la campana según el tipo del aviso más reciente: (texto, ícono, vista de la plataforma).

    Cierres de posiciones -> Cartera; alertas de precio -> Perfil > Notificaciones (ahí se ven y se crean); lo demás (respuestas, órdenes y
    vigilancias del agente) -> el chat del agente en Trading."""
    if tipo == "posicion":
        return "Ir a Cartera", ":material/account_balance_wallet:", "portafolio"
    if tipo == "alerta":
        return "Ver mis alertas", ":material/add_alert:", "perfil"
    return "Ver el chat del agente", ":material/chat:", "trading"


# TITULO IR A

def _ir_a(usuario_id: str, vista: str) -> None:
    """Marca los avisos como leídos y navega a `vista`; si es el perfil, abre su sección Notificaciones. Relanza la página."""
    notificaciones.marcar_leidas(usuario_id)
    if vista == "perfil":
        st.session_state["perfil_seccion"] = "preferencias"
    st.session_state.navegacion_activo = vista
    st.rerun()


# TITULO CAMPANA

def campana(usuario_id: str) -> None:
    """Dibuja la campana (como fragmento con clave «campana», refrescable sin reiniciar la página) y, aparte, el vigilante de avisos nuevos.

    Recibe el id del usuario; el contenido está en `_campana_contenido`."""
    fragmento_con_refresco("campana", _campana_contenido, usuario_id)
    # Arranca el fragmento que detecta avisos nuevos cada 3 s
    vigilar_notificaciones(usuario_id)


# TITULO CAMPANA CONTENIDO

def _campana_contenido(usuario_id: str) -> None:
    """Dibuja la campana con insignia y la lista desplegable de notificaciones.

    Recibe el id del usuario. Guarda en sesión el id de la última notificación (para el
    fragmento vigilante), lanza un `st.toast` una sola vez por notificación nueva y sesión, y
    muestra un popover con la lista. Sus botones son reales: el principal marca todo como leído y
    navega a donde corresponde al aviso más reciente (Cartera, Perfil o el chat del agente en Trading), "Ver historial" abre Perfil >
    Notificaciones y "Marcar como leídas" solo quita la insignia (los avisos siguen en la lista). Al final arranca
    el fragmento `vigilar_notificaciones`.
    """
    # Recuerda la última notificación vista para que el vigilante detecte las nuevas
    st.session_state["_notificacion_ultima_id"] = notificaciones.ultima_id(usuario_id)
    elementos = notificaciones.listar(usuario_id, 8)
    sin_leer = notificaciones.no_leidas(usuario_id)

    # Aviso emergente, una sola vez por notificación y sesión.
    vistas = st.session_state.setdefault("_notificacion_toast", set())
    for n in reversed(elementos):
        if not n["leida"] and n["id"] not in vistas:
            vistas.add(n["id"])
            st.toast(f"**{n['titulo']}**\n\n{n['texto']}", icon=ICONO_TIPO.get(n["tipo"], "🔔"))

    # Contenedor con clave notificacion_campana: estilos.css posiciona la insignia sobre la campana
    with st.container(key="notificacion_campana"):
        # Insignia con el número de avisos sin leer (9+ si son diez o más)
        if sin_leer:
            st.html(f"<span class='notificacion-insignia'>{sin_leer if sin_leer < 10 else '9+'}</span>")
        with st.popover("", icon=":material/notifications:"):
            # Cabecera del desplegable con contador de nuevas
            st.html(
                "<div class='notificacion-cabecera'>Notificaciones"
                + (f"<span class='notificacion-cuenta'>{sin_leer} nueva{'s' if sin_leer != 1 else ''}</span>" if sin_leer else "")
                + "</div>"
            )
            # Lista de notificaciones y, si hay, los botones de acción
            st.html(html_notificaciones(elementos))
            if elementos:
                # Botón principal: lleva a donde corresponde según el aviso más reciente (sin leer, si hay).
                reciente = next((n for n in elementos if not n["leida"]), elementos[0])
                texto, icono, vista = _destino_del_aviso(reciente["tipo"])
                if st.button(texto, key="notificacion_ir", icon=icono, type="primary", width="stretch"):
                    _ir_a(usuario_id, vista)
                # El historial completo (también lo que ya leíste) está en Perfil > Notificaciones.
                if vista != "perfil" and st.button("Ver historial", key="notificacion_historial", icon=":material/history:", width="stretch"):
                    _ir_a(usuario_id, "perfil")
                # Marcar como leídas solo quita la insignia: los avisos siguen en la lista y en el historial.
                if sin_leer and st.button("Marcar como leídas", key="notificacion_leer", icon=":material/done_all:", width="stretch"):
                    notificaciones.marcar_leidas(usuario_id)
                    st.rerun()


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
