# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
componentes_plataforma/noticias
-------------------
Paquete del panel de noticias financieras. Expone solo `renderizar_panel_noticias`, que dibuja la página completa;
los demás módulos son piezas internas.
  - Noticia PRINCIPAL grande + CARRUSEL paginado (‹ ›, de 4 en 4 hasta 20, loop) + «Más noticias».
  - Varias fuentes gratuitas y sin inicio de sesión (Investing, FXStreet, MarketWatch, Benzinga, Cinco Días,
    Expansión, Seeking Alpha), en español e inglés, con selector de idioma.
  - Se revisan cada 10 s con peticiones condicionales (ETag / Last-Modified): casi no cuestan cuando no hay
    novedades. Una línea de estado muestra la hora de la última revisión y cuántas noticias nuevas llegaron.
  - Al hacer clic en una noticia se abre un MODAL propio con la imagen y el texto del artículo (del RSS o leído desde
    el servidor), sin iframe: casi todos los medios prohíben incrustarse o piden iniciar sesión. Un botón la abre en
    su sitio en una pestaña real.

Archivos: panel.py (arma la página), secciones.py (principal, carrusel, más noticias), modal.py (ventana de la
noticia), articulo.py (lectura del texto de un artículo), tarjetas.py, rss.py (lectura por fuente con revisión
condicional), datos.py + fuentes.json (fuentes y parámetros) y estilos.css.
"""
# Fachada: reexporta la función que la aplicación llama para pintar la página de noticias
from componentes_plataforma.noticias.panel import renderizar_panel_noticias

# Nombres públicos del paquete
__all__ = ["renderizar_panel_noticias"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
