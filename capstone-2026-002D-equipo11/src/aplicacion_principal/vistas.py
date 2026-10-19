# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara vistas .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Enrutado de vistas: decide qué pantalla se dibuja en el área de contenido.

La vista activa depende del botón elegido en la barra lateral, que queda guardado en
`st.session_state["nav_activo"]`.
"""
import streamlit as st

from components.noticias_panel import renderizar_panel_noticias

from .vista_operativa import renderizar_vista_operativa


def renderizar_vista(fragmentos, consola) -> None:
    """
    Dibuja en el área de contenido la vista que corresponde al botón activo de la barra lateral.

    Vistas disponibles: noticias, cotizaciones, copytrading, trading, portafolio (cartera),
    resumen y journal (diario). Cualquier otro valor, o ninguno, muestra la vista de Inicio, de
    modo que los botones sin vista propia caen ahí. Los paneles menos usados se importan al
    momento de dibujarlos para que un problema en uno no impida abrir los demás.
    Recibe `fragmentos` (de `crear_fragmentos()`) y `consola` (módulo `consola_agente` o `None`).
    """
    vista_activa = st.session_state.get("nav_activo")
    # Pequeño espacio superior para separar el contenido de la barra fija. Las vistas de operar (Trading y
    # Cartera) lo omiten: ahí el gráfico y la lista de activos van pegados arriba para verse completos.
    if vista_activa not in ("trading", "portafolio"):
        st.markdown("<div style='height: 0.2rem'></div>", unsafe_allow_html=True)
    if vista_activa == "noticias":
        # --- VISTA DE NOTICIAS ---
        renderizar_panel_noticias(consola)
    elif vista_activa == "cotizaciones":
        # --- VISTA DE COTIZACIONES (tablas estilo Investing) ---
        from components.mercados_panel import renderizar_panel_mercados
        renderizar_panel_mercados(consola)
    elif vista_activa == "copytrading":
        # --- VISTA COPY TRADING (estrategias, MVP de demostración) ---
        from components.copytrading_panel import renderizar_panel_copytrading
        renderizar_panel_copytrading(consola)
    elif vista_activa == "trading":
        # --- VISTA TRADING (favoritos + watchlist + gráfico + ticket de orden) ---
        renderizar_vista_operativa(fragmentos.watchlist, fragmentos, consola)
    elif vista_activa == "portafolio":
        # --- VISTA CARTERA (igual a Trading, pero la lista izquierda son las
        #     posiciones abiertas en vez del watchlist) ---
        renderizar_vista_operativa(fragmentos.cartera, fragmentos, consola)
    elif vista_activa == "resumen":
        # --- VISTA RESUMEN (dashboard del portafolio: KPIs + curva + exposición) ---
        from components.resumen_panel import renderizar_panel_resumen
        renderizar_panel_resumen(consola)
    elif vista_activa == "journal":
        # --- VISTA DIARIO (trading journal: operaciones + métricas + notas) ---
        from components.diario_panel import renderizar_panel_journal
        renderizar_panel_journal(consola)
    else:
        # --- VISTA INICIO (panel de cuenta estilo XM), también para botones sin vista propia ---
        from components.inicio_panel import renderizar_panel_inicio
        renderizar_panel_inicio(consola)


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara vistas .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
