# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara panel .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Vista "Resumen": cabecera y cuerpo en un fragmento que se refresca solo.

Orquesta los bloques de `secciones.py` con los datos de `herramientas.estadisticas_portafolio` (MT5) y los estilos
de `estilos.py`. Es el punto de entrada que reexporta la fachada `resumen_panel.py`.
"""
import streamlit as st

from components.flujo_precios import intervalo as _intervalo
from components.resumen.estilos import CSS
from components.resumen.secciones import (curva_balance, exposicion_por_activo, nivel_margen, nota_pie,
                                          tarjetas_kpi)
from tools import estadisticas_portafolio
from tools.puente_mt5 import inicializar_mt5


def renderizar_panel_resumen(main=None):
    """Dibuja la vista Resumen completa.

    Recibe `main` (no se usa; se conserva por compatibilidad con la firma que espera `app.py`). Inicializa
    MT5, inyecta el CSS y dibuja la cabecera; el cuerpo (tarjetas, margen, curva, exposición y nota) va en un
    fragmento que se refresca solo. Si MT5 no responde muestra una advertencia. No devuelve nada."""
    # Conexión con MT5 (idempotente) y estilos de la vista.
    inicializar_mt5()
    st.html(CSS)

    # Contenedor con clave rs_wrap: el CSS lo centra y limita su ancho.
    with st.container(key="rs_wrap"):
        # Cabecera fija: ícono, título y subtítulo.
        st.markdown(
            "<div class='rs-head'><div class='ic'><span class='rmi'>dashboard</span></div>"
            "<div><div class='rs-title'>Resumen</div>"
            "<div class='rs-sub'>Rendimiento y riesgo del portafolio en tiempo real</div></div></div>",
            unsafe_allow_html=True,
        )

        # Con el feed activo, los valores de CUENTA (equity, flotante, nivel de margen)
        # se pintan en vivo por el feed (data-pj-acc), sin rerun; el fragmento solo
        # recalcula lo que necesita cómputo (realizado, exposición, curva) cada pocos s.
        @st.fragment(run_every=_intervalo("2s", "4s"))
        def _cuerpo():
            """Calcula las estadísticas del portafolio y dibuja los cinco bloques; avisa si MT5 no responde."""
            # Estadísticas completas del portafolio (diccionario con clave "error" si falla MT5).
            s = estadisticas_portafolio.calcular()
            if "error" in s:
                st.warning("No se pudo conectar con MetaTrader 5. Abre el terminal "
                           "con la cuenta iniciada para ver tu portafolio.")
                return
            # Orden de los bloques: KPI, nivel de margen, curva, exposición y nota al pie.
            tarjetas_kpi(s)
            nivel_margen(s)
            curva_balance(s)
            exposicion_por_activo(s)
            nota_pie(s)

        # Primera ejecución del fragmento; después se repite solo según run_every.
        _cuerpo()


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
