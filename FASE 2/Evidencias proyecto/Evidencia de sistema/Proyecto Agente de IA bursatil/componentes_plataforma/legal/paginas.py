# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara paginas .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Páginas y avisos legales de la plataforma.

`vista_legal` dibuja un documento completo (términos, privacidad y cookies, o aviso de riesgo) a pantalla completa; la llama `requerir_login()` cuando llega
`?legal=<documento>`, con o sin sesión iniciada. El resto son los textos cortos que se repiten por la plataforma: el pie con los enlaces, el aviso de cookie del
inicio de sesión, la casilla de aceptación del registro y la nota bajo el agente. Los textos largos viven en legal/contenido.py.
"""
from html import escape
from pathlib import Path

import streamlit as st

from componentes_plataforma._estaticos import estilos

from . import contenido

_CSS = Path(__file__).parent / "estilos.css"

# Nombre corto de cada documento en los enlaces.
_ENLACES = (("terminos", "Términos de uso"), ("privacidad", "Privacidad y cookies"), ("riesgo", "Aviso de riesgo"))


# TITULO ENLACES

def enlaces_html(separador: str = " · ", color: str = "#8b949e") -> str:
    """Devuelve el HTML con los tres enlaces a los documentos legales, abiertos en otra pestaña para no perder lo que el usuario está haciendo."""
    return separador.join(f"<a href='?legal={clave}' target='_blank' rel='noopener' style='color:{color};'>{texto}</a>" for clave, texto in _ENLACES)


# TITULO PIE

def pie_legal() -> None:
    """Dibuja al final de la plataforma una línea discreta con la frase de riesgo y los enlaces legales."""
    st.markdown(f"<div style='margin:28px 0 8px; padding:12px 4px 0; border-top:1px solid #21262d; color:#6b7686; font-size:12px; line-height:1.5; text-align:center;'>"
                f"{escape(contenido.FRASE_RIESGO)} {enlaces_html()}</div>", unsafe_allow_html=True)


# TITULO NOTA DEL AGENTE

def nota_agente() -> None:
    """Dibuja bajo el encabezado del agente una nota breve de que sus respuestas no son asesoría financiera."""
    st.markdown("<div style='margin:0 0 6px; color:#8b949e; font-size:12px; line-height:1.4;'>Las respuestas del agente son informativas y pueden tener errores; no son asesoría financiera. "
                "Las órdenes se ejecutan solo si tú las confirmas o si autorizas una vigilancia automática.</div>", unsafe_allow_html=True)


# TITULO AVISO DE COOKIE

def aviso_cookie() -> None:
    """Dibuja en el inicio de sesión el aviso de la cookie que mantiene la sesión abierta, con el enlace a la política de privacidad."""
    st.markdown("<p style='margin:10px 0 10px; color:#8b949e; font-size:12px; line-height:1.5; text-align:center;'>Al iniciar sesión guardamos en este dispositivo una cookie para mantenerla abierta hasta 30 días; "
                "se borra al cerrar sesión. <a href='?legal=privacidad' target='_blank' rel='noopener' style='color:#8b949e;'>Más información</a>.</p>", unsafe_allow_html=True)


# TITULO CASILLA DE ACEPTACION

def casilla_aceptacion(clave: str) -> bool:
    """Dibuja los enlaces a los tres documentos y debajo la casilla «He leído y acepto…» del registro; devuelve si está marcada. `clave` identifica la casilla.

    Los enlaces van FUERA de la casilla a propósito: Streamlit toma todo el texto de una casilla como parte de ella, y un clic en un enlace dentro de su texto solo
    marca o desmarca la casilla sin abrir el documento."""
    st.markdown(f"<p style='margin:2px 0 6px; font-size:14px; color:#8b949e;'>Lee antes de aceptar: {enlaces_html(color='#58a6ff')}</p>", unsafe_allow_html=True)
    return st.checkbox("He leído y acepto los términos de uso, la política de privacidad y cookies, y el aviso de riesgo.", key=clave)


# TITULO BLOQUES

def _bloque(bloque) -> str:
    """Convierte un bloque de contenido (texto o lista de textos) en HTML: un párrafo o una lista con viñetas."""
    if isinstance(bloque, str):
        return f"<p>{escape(bloque)}</p>"
    return "<ul>" + "".join(f"<li>{escape(t)}</li>" for t in bloque) + "</ul>"


# TITULO VISTA LEGAL

def vista_legal(clave: str, con_sesion: bool) -> None:
    """Dibuja un documento legal completo: título, versión, aviso de revisión (si corresponde), secciones y enlace para volver.

    Recibe la clave del documento (`terminos`, `privacidad` o `riesgo`) y si el usuario tiene la sesión iniciada, que decide a dónde lleva «Volver»
    (a la plataforma o a la pantalla de acceso). No devuelve nada."""
    documento = contenido.DOCUMENTOS[clave]
    st.html(estilos(_CSS))
    revision = ("<div class='pj-legal-revision'>Este documento está en revisión legal por la empresa y puede cambiar.</div>" if contenido.EN_REVISION else "")
    secciones = "".join(f"<h2>{escape(titulo)}</h2>{''.join(_bloque(b) for b in bloques)}" for titulo, bloques in documento["secciones"])
    otros = " · ".join(f"<a href='?legal={c}' target='_self'>{t}</a>" for c, t in _ENLACES if c != clave)
    volver = "./" if con_sesion else "?acceso=entrar"
    st.html(
        f"<div class='pj-legal'>"
        f"<div class='pj-legal-logo'>P&amp;J</div>"
        f"<h1>{escape(documento['titulo'])}</h1>"
        f"<p class='pj-legal-resumen'>{escape(documento['resumen'])}</p>"
        f"<p class='pj-legal-version'>Versión {contenido.VERSION} · vigente desde el {contenido.VIGENTE_DESDE}</p>"
        f"{revision}{secciones}"
        f"<div class='pj-legal-fin'><p>Otros documentos: {otros}</p>"
        f"<a class='pj-legal-volver' href='{volver}' target='_self'>← Volver</a></div></div>")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara paginas .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
