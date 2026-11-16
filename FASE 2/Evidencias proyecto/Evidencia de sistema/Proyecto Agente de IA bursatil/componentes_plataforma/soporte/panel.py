# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- INICIO Piña y Jara panel .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Vista «Soporte» (botón del audífono de la barra lateral): reportar un problema, contacto, documentos y preguntas frecuentes.

A la izquierda va el formulario del reporte; a la derecha, el correo de contacto y los enlaces a los documentos legales; debajo, las preguntas frecuentes. El reporte lo
envía herramientas/soporte.py por correo, con el correo del usuario en «Responder a», y respeta sus límites de envío. La vista no necesita datos del bróker.
"""
from html import escape
from pathlib import Path

import streamlit as st

from componentes_plataforma import _estaticos, recaptcha
from componentes_plataforma.acceso.sesion import usuario_en_sesion
from componentes_plataforma.legal.contenido import CORREO
from herramientas import soporte

# Hoja de estilos de la vista, junto a este archivo
_CSS = Path(__file__).parent / "estilos.css"
# Clave de st.session_state con el resultado del último envío (se muestra bajo el formulario)
_CLAVE_RESULTADO = "soporte_resultado"

# Preguntas frecuentes: (pregunta, respuesta).
PREGUNTAS = (
    ("¿El agente puede operar sin mi permiso?",
     "Propone las órdenes y solo se ejecutan cuando tú las confirmas, o si autorizas una vigilancia automática, que opera dentro de los límites de riesgo que defines y que puedes detener cuando quieras."),
    ("¿Es seguro conectar mi cuenta de Capital.com?",
     "Las claves de tu cuenta se guardan cifradas y solo se usan para lo que tú pides o confirmas. Puedes desconectarla cuando quieras."),
    ("¿Cómo cierro sesión en todos mis dispositivos?",
     "Desde Mi perfil, en la sección de seguridad."),
    ("¿Cómo elimino mi cuenta y mis datos?",
     f"Escríbenos a {CORREO} y lo gestionamos."),
)


# TITULO FORMULARIO

def _formulario() -> None:
    """Dibuja el formulario del reporte (tema, mensaje y botón) y, debajo, el resultado del último intento.

    Al enviar guarda el resultado en la sesión y llama a herramientas/soporte.enviar_reporte, que valida, aplica los límites y manda el correo."""
    with st.form("form_soporte", border=False):
        tema = st.selectbox("Tema", soporte.TEMAS)
        mensaje = st.text_area("Qué pasó", placeholder="Describe qué hacías y qué viste en pantalla.", height=150, max_chars=soporte.MAXIMO_CARACTERES)
        st.caption("Adjuntamos solos tu usuario, la sección en que estabas, la hora y tu navegador. Nunca incluimos contraseñas ni claves.")
        recaptcha.dibujar("soporte")
        enviar = st.form_submit_button("Enviar reporte", type="primary", width="stretch")
    if enviar:
        recaptcha.exigir("soporte")
        try:
            navegador = st.context.headers.get("User-Agent", "")
        except Exception:
            navegador = ""
        st.session_state[_CLAVE_RESULTADO] = soporte.enviar_reporte(
            usuario_en_sesion() or {}, tema, mensaje, "soporte", navegador)
    resultado = st.session_state.get(_CLAVE_RESULTADO)
    if resultado:
        (st.success if resultado["ok"] else st.error)(resultado["mensaje"])
    st.caption(f"Puedes enviar hasta {soporte.MAXIMO_POR_DIA} reportes al día.")


# TITULO RENDERIZAR PANEL SOPORTE

def renderizar_panel_soporte(main=None) -> None:
    """Dibuja la vista Soporte completa. `main` no se usa (se conserva por compatibilidad con las demás vistas). No devuelve nada."""
    st.html(_estaticos.estilos(_CSS))
    with st.container(key="soporte_contenedor"):
        st.html("<div class='sop-titulo'>Soporte</div><div class='sop-subtitulo'>Cuéntanos qué pasó y te respondemos por correo.</div>")
        izquierda, derecha = st.columns([1.6, 1], gap="large")
        with izquierda:
            st.html("<div class='sop-seccion'>Reportar un problema</div>")
            _formulario()
        with derecha:
            st.html("<div class='sop-seccion'>Contacto</div>"
                    f"<div class='sop-tarjeta'><div class='sop-etiqueta'>Correo</div><div class='sop-valor'>{escape(CORREO)}</div></div>")
            st.html("<div class='sop-seccion'>Documentos</div>"
                    "<div class='sop-tarjeta sop-enlaces'>"
                    "<a href='?legal=terminos' target='_blank' rel='noopener'>Términos de uso</a>"
                    "<a href='?legal=privacidad' target='_blank' rel='noopener'>Privacidad y cookies</a>"
                    "<a href='?legal=riesgo' target='_blank' rel='noopener'>Aviso de riesgo</a></div>")
        st.html("<div class='sop-seccion'>Preguntas frecuentes</div>")
        for pregunta, respuesta in PREGUNTAS:
            with st.expander(pregunta):
                st.write(respuesta)


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara panel .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
