# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara modal .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Modal de una noticia: imagen, título, fuente y fecha, el texto del artículo dentro de la plataforma y un botón para abrirla en su sitio.

No incrusta la página del medio (casi todos prohíben los iframes o piden iniciar sesión): el texto sale del propio RSS si
la fuente lo incluye, o se lee desde el servidor con `articulo.texto_articulo` (que ya está en caché porque `rss.py` lo
comprobó antes de mostrar la noticia); si no hay texto suficiente se muestra el resumen del RSS. El botón «Leer en …» abre la noticia en una pestaña real del navegador."""
import html as _html

import streamlit as st

from components.noticias.articulo import texto_articulo


def _parrafos_html(texto: str) -> str:
    """Convierte un texto con un párrafo por línea en HTML de párrafos con estilo, escapando cualquier carácter especial."""
    return "".join(
        f"<p style='color:#c9d1d9; font-size:15px; line-height:1.7; margin:0 0 12px;'>{_html.escape(p)}</p>"
        for p in texto.split("\n") if p.strip()
    )


def _cuerpo(n: dict) -> tuple:
    """Texto que se muestra de una noticia y su origen: devuelve `(texto, completo)`.

    Usa el texto completo del RSS si lo trae; si la fuente permite extraer, lee la página del artículo (con un indicador
    de carga); si nada sirve, devuelve el resumen y `completo = False`."""
    if n.get("texto"):
        return n["texto"], True
    if n.get("extraer"):
        with st.spinner("Cargando el artículo…"):
            t = texto_articulo(n["link"])
        if t:
            return t, True
    return n.get("desc", ""), False


def _contenido_modal(n: dict):
    """Dibuja el interior del modal de una noticia.

    Recibe el diccionario de la noticia (`img`, `title`, `fecha`, `fuente`, `link`, `desc`, `texto`). Pinta la imagen, el
    título y la fuente con la fecha, luego el texto del artículo (o el resumen con un aviso si no se puede mostrar
    completo) y un botón que abre la noticia en una pestaña real. No devuelve nada."""
    # El contenedor con clave `noticia_root` permite que estilos.css oscurezca el diálogo sin importar el tema de Streamlit.
    with st.container(key="noticia_root"):
        st.html(f"""
            <img src="{_html.escape(n['img'])}" referrerpolicy="no-referrer"
                 style="width:100%; height:260px; object-fit:cover; border-radius:10px; background:#161b22;">
            <h2 style="color:#ffffff; font-size:24px; font-weight:800; line-height:1.3; margin:14px 0 6px;">{_html.escape(n['title'])}</h2>
            <p style="color:#8b949e; font-size:12px; margin:0 0 14px;">{_html.escape(n.get('fuente', ''))} &nbsp;·&nbsp; {_html.escape(n['fecha'])}</p>
        """)
        texto, completo = _cuerpo(n)
        if texto:
            st.html(_parrafos_html(texto))
        if not completo:
            st.caption("Este medio no permite mostrar el artículo completo aquí. Ábrelo en su sitio con el botón de abajo.")
        st.link_button(f"Leer en {n.get('fuente') or 'el sitio'} ↗", n["link"], type="primary", width="stretch")


def abrir_modal(n: dict):
    """Abre el diálogo "Noticia" con la noticia indicada.

    Recibe el diccionario de la noticia. Al cerrar el diálogo se limpia `noticia_abierta` de la sesión para
    que no se reabra en el siguiente rerun. Se define el diálogo dentro de la función para capturar `n`."""
    def _al_cerrar():
        """Callback de cierre: borra la noticia abierta del estado de sesión."""
        st.session_state.noticia_abierta = None

    @st.dialog("Noticia", width="large", on_dismiss=_al_cerrar)
    def _dialogo_noticia():
        """Cuerpo del diálogo: delega en `_contenido_modal`."""
        _contenido_modal(n)

    _dialogo_noticia()

# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara modal .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
