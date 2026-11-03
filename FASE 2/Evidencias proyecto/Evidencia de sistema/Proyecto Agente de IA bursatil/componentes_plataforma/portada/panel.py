# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara panel .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Portada pública de la plataforma: lo primero que ve quien aún no inició sesión.

`renderizar_portada()` dibuja la página completa (barra, héroe con captura real, beneficios, gráficos, agente, mercados, noticias, herramientas, pasos, planes, preguntas, cierre y pie). Los botones llevan a los formularios
de acceso con `?acceso=entrar` o `?acceso=crear` (ver acceso/pantalla.py). Es una página informativa: no consulta datos de cuentas ni del bróker.
"""
from pathlib import Path

import streamlit as st

from componentes_plataforma._estaticos import estilos
from componentes_plataforma.portada import secciones

# CSS de la portada (los 8 cortes de pantalla de la empresa); se vuelve a leer solo si el archivo cambia en disco.
_CSS = Path(__file__).parent / "estilos.css"
# Cada cuántos segundos se refresca la sección de mercados.
REFRESCO_S = 5


# TITULO MERCADOS EN VIVO

@st.fragment(run_every=f"{REFRESCO_S}s")
def _mercados_en_vivo() -> None:
    """Sección «Mercados» como fragmento: se vuelve a dibujar sola cada pocos segundos (solo ella, no la página) para mostrar los precios más recientes de la caché de `datos.py`.

    Los visitantes solo leen la caché del servidor, así que refrescar no genera peticiones a Capital.com."""
    st.html(secciones.activos())


# TITULO RENDERIZAR PORTADA

def renderizar_portada() -> None:
    """Dibuja la portada completa en la página de Streamlit. No recibe parámetros ni devuelve nada.

    Inyecta el CSS (que además oculta el relleno de Streamlit para usar todo el ancho) y el HTML de cada sección, en orden de arriba a abajo; la sección de mercados es un fragmento que se refresca sola."""
    st.html(estilos(_CSS))
    st.html("".join(f() for f in (secciones.barra, secciones.heroe, secciones.porque, secciones.graficos, secciones.agente)))
    _mercados_en_vivo()
    st.html("".join(f() for f in (secciones.noticias, secciones.herramientas, secciones.pasos, secciones.planes, secciones.preguntas, secciones.cierre, secciones.pie)))


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara panel .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
