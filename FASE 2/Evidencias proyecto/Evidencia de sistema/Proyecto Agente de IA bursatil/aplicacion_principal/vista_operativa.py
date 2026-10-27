# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara vista_operativa .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Vista de operar, compartida por las secciones Trading y Cartera.

Se dibuja en dos filas: arriba la lista de activos o posiciones, el gráfico y (a la derecha, en un
rail de iconos fijo) el ticket de orden; abajo el historial del agente, el chat y las órdenes
propuestas.
"""
import streamlit as st

from componentes_plataforma.chat import renderizar_chat_agente
from componentes_plataforma.grafico.panel import renderizar_panel_central
from componentes_plataforma.agente_paneles import (inyectar_estilos_agente,
                                                   renderizar_historial_agente,
                                                   renderizar_ordenes_propuestas)

# Proporción de columnas compartida por las dos filas de la vista de operar, para que el
# historial quede bajo la lista, el chat bajo el gráfico y las propuestas bajo el ticket.
COLUMNAS_OPERAR = [1.7, 3.2, 0.95]
# Alto de las zonas con scroll del historial y de las propuestas, calculado para que su borde
# inferior coincida con el del chat (cabecera + selector + 450 de mensajes + campo de texto).
# Se ajusta si no cuadra.
ALTURA_HISTORIAL = 587
ALTURA_PROPUESTAS = 500


# TITULO RENDERIZAR VISTA OPERATIVA

def renderizar_vista_operativa(renderizar_lista_izquierda, fragmentos, consola) -> None:
    """
    Dibuja la vista de operar (Trading y Cartera) en dos filas.

    Fila 1: lista de la izquierda (watchlist o posiciones) | gráfico | rail derecho (ticket, profundidad, favoritos).
    Fila 2: historial del agente | chat del agente | órdenes propuestas.

    Los paneles del agente van en su propia fila para que queden siempre a la altura del chat y no
    se desplacen cuando cambia el alto de la lista o del ticket de arriba.

    Recibe `renderizar_lista_izquierda` (la función que dibuja la lista de la izquierda, distinta
    en Trading y en Cartera), `fragmentos` (el objeto de `crear_fragmentos()`) y `consola` (el
    módulo `consola_agente`, o `None`), que se pasa a los paneles que lo usan.
    """
    inyectar_estilos_agente()

    # El ticket y los favoritos ya no van como columnas ni como barra superior: viven en el rail de iconos fijo
    # a la derecha (componentes_plataforma/riel/). El CSS del rail se inyecta PRIMERO, antes de las
    # columnas, para que el gráfico se mida con el espacio reservado a la derecha y para que el panel de favoritos
    # nazca ya en su sitio. Los favoritos se dibujan antes que la lista de activos porque su fragmento también
    # refresca los precios de mercado que esa lista usa.
    from componentes_plataforma.riel import (inyectar_css_riel, renderizar_barra_operar, renderizar_panel_favoritos,
                                             renderizar_riel_y_paneles)
    inyectar_css_riel()
    renderizar_panel_favoritos(fragmentos.favoritos)

    # Primera fila: lista a la izquierda y panel central (gráfico) a la derecha.
    columna_izquierda, columna_centro = st.columns([COLUMNAS_OPERAR[0],
                                            COLUMNAS_OPERAR[1] + COLUMNAS_OPERAR[2]])
    with columna_izquierda:
        renderizar_lista_izquierda()
    with columna_centro:
        renderizar_panel_central(consola)
    renderizar_riel_y_paneles(consola)
    # Solo celular: barra fija Vender/Comprar sobre el rail; abre el ticket de órdenes.
    renderizar_barra_operar()

    # Separador fino entre las dos filas (con st.markdown("---") quedaba una franja alta de ~50px).
    st.html("<div class='pj-separador'></div>")

    # Segunda fila: paneles del agente, con las mismas proporciones que la primera.
    columna_historial, columna_chat, columna_propuestas = st.columns(COLUMNAS_OPERAR)
    with columna_historial:
        renderizar_historial_agente(altura=ALTURA_HISTORIAL)
    with columna_chat:
        renderizar_chat_agente()
    with columna_propuestas:
        renderizar_ordenes_propuestas(altura=ALTURA_PROPUESTAS)


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara vista_operativa .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
