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
componentes_plataforma/riel
---------------
Rail de iconos FIJO a la derecha (estilo XM), gemelo de la barra lateral izquierda
(componentes_plataforma/barra_lateral/), pero debajo de la barra superior. Cada icono despliega /
oculta su panel.

Rendimiento: el toggle NO reejecuta Python (como el ☰ del nav izquierdo). Los
paneles (Operar, DOM) se dibujan SIEMPRE; un script intercepta el clic del icono
(antes de que llegue a Streamlit) y alterna clases en <html>; el CSS desliza el
panel y reserva el espacio a la derecha → aparece al instante, sin recargar el
gráfico (es autoSize, solo se reajusta).

Estados (clase en <html>):
  - (sin clase)      → Operar abierto (DEFAULT: al entrar o F5 el ticket está visible)
  - pj-panel-dom     → DOM abierto (Operar oculto)
  - pj-panel-favorito     → Favoritos abierto (Operar oculto)
  - pj-panel-none    → todo oculto (gráfico a pantalla completa)
Así, tras un F5 (ventana nueva, sin clases) el ticket queda desplegado; el usuario
lo oculta con su botón. El estado se mantiene al navegar entre vistas (la clase
vive en <html>), solo se reinicia con F5.

Tooltip: en vez del `help` de Streamlit (que en un contenedor fijo se queda
pegado), el nombre se muestra con un tooltip CSS propio (::after) al pasar el mouse.

La fachada `componentes_plataforma/riel/` reexporta desde aquí `RAIL`, `PANEL`, `TOP`, `BOTONES`,
`inyectar_css_riel`, `renderizar_panel_favoritos` y `renderizar_riel_y_paneles`.

Archivos: panel.py (dibuja paneles y rail), estilos.py + estilos.css (plantilla con las medidas), datos.py +
botones.json, riel.js (alterna los paneles sin reejecutar Python).
"""
# Medidas del rail y lista de botones.
from componentes_plataforma.riel.datos import BOTONES, PANEL, RAIL, TOP
# Funciones que inyectan el CSS y dibujan el rail con sus paneles.
from componentes_plataforma.riel.panel import inyectar_css_riel, renderizar_panel_favoritos, renderizar_riel_y_paneles
# Pieza que solo se ve en el celular: barra fija Vender/Comprar.
from componentes_plataforma.riel.movil import renderizar_barra_operar

# API pública del paquete.
__all__ = ["RAIL", "PANEL", "TOP", "BOTONES", "inyectar_css_riel", "renderizar_panel_favoritos", "renderizar_riel_y_paneles",
           "renderizar_barra_operar"]


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
