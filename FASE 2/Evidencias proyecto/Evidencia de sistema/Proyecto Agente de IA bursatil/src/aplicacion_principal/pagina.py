# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara pagina .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Armado de la página completa del dashboard.

Contiene `ejecutar()`, que Streamlit invoca en cada reejecución del script y que dibuja la página
en el mismo orden que tenía el antiguo app.py: configuración, estilos, login, pantalla de carga,
barra superior, feed en vivo, datos de mercado, fragmentos, barra lateral, vista activa y diálogos.
"""
import streamlit as st

from components.acceso import requerir_login
from components.barra_lateral import renderizar_barra_navegacion as renderizar_nav_lateral
from components.datos_mercado import cargar_datos_mercado
from components.flujo_vivo import inyectar_flujo
from components.transicion import inyectar_transicion

from .cabecera import datos_cuenta, renderizar_barra_superior
from .dialogos import renderizar_dialogos
from .estilos import css_global, html_pantalla_carga
from .fragmentos import crear_fragmentos
from .vistas import renderizar_vista


def ejecutar(consola) -> None:
    """
    Dibuja el dashboard completo.

    Recibe `consola`, el módulo `consola_agente` (o `None` si no se pudo importar), que se reparte
    a las vistas que lo necesitan. El orden de los pasos importa: `set_page_config` debe ser la
    primera llamada de Streamlit, el login debe ir antes de cualquier dato de la cuenta y la
    cubierta de carga debe retirarse cuando todo lo demás ya se dibujó.
    """
    # Configuración inicial de la página (debe ser la primera llamada de Streamlit).
    st.set_page_config(
        page_title="Dashboard agente analitico Piña & Jara",
        page_icon="📈",
        layout="wide"
    )

    # Estilos CSS globales (tema oscuro tipo terminal de trading).
    st.markdown(css_global(), unsafe_allow_html=True)

    # Cortina de transición entre secciones (oculta la vista mientras carga y la muestra ya armada).
    inyectar_transicion()

    # Login (Supabase): protege el acceso al dashboard y devuelve los datos del usuario.
    usuario_actual = requerir_login()

    # Cubierta de carga a pantalla completa, solo en la primera entrada a la página.
    primera_carga = not st.session_state.get("datos_cargados", False)
    cubierta_carga = st.empty()
    if primera_carga:
        cubierta_carga.markdown(html_pantalla_carga(), unsafe_allow_html=True)

    # 1. Barra superior fija (saldo de MT5 y métricas de riesgo).
    saldo, moneda, pl, metricas = datos_cuenta()
    renderizar_barra_superior(usuario_actual, saldo, moneda, pl, metricas)

    # Feed de precios en vivo (SSE desde servidor_datos.py): pinta los números directo en el
    # navegador unas 4 veces por segundo, sin reejecutar Streamlit.
    inyectar_flujo()

    # Carga inicial de los datos de mercado.
    cargar_datos_mercado()

    # Fragmentos con números en vivo (favoritos, watchlist y cartera).
    fragmentos = crear_fragmentos()

    # Disposición principal: columna angosta para la barra lateral y columna ancha para el contenido.
    col_nav, col_principal = st.columns([0.5, 11.5], gap="small")

    # 2. Barra lateral izquierda extendida.
    with col_nav:
        renderizar_nav_lateral()

    # 3. Área de contenido principal: cambia según la vista elegida en la barra lateral.
    with col_principal:
        # El contenedor con clave `pj_vista` es lo que la cortina de transición oculta mientras se carga la sección.
        with st.container(key="pj_vista"):
            renderizar_vista(fragmentos, consola)

    # Se quita la cubierta de carga una vez dibujado todo.
    cubierta_carga.empty()

    # Diálogos (buscador, cierre de posición y términos de One-Click) fuera de los fragmentos.
    renderizar_dialogos()


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara pagina .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
