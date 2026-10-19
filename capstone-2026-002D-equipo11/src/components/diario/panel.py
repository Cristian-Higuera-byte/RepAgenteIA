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

"""Vista "Diario": cabecera, tabla de operaciones con métricas, ficha por operación y nota al pie.

Recoge los datos de estadisticas_diario.calcular() y delega el dibujo en tabla.py (tabla y
métricas) y ficha.py (detalle por operación). Los estilos están en estilos.css.
"""
import streamlit as st

from components.diario.estilos import CSS
from components.diario.ficha import ficha
from components.diario.tabla import tabla_y_metricas
from tools import estadisticas_diario
from tools.puente_mt5 import NOMBRE_PROVEEDOR, inicializar_mt5, obtener_info_cuenta


def renderizar_panel_journal(main=None):
    """Dibuja la vista completa del Diario.

    Parámetro: main, sin uso actual (se conserva por compatibilidad con quien la invoca).
    Inicializa MT5, inyecta los estilos, calcula las operaciones cerradas y sus métricas, y
    dibuja cabecera, tabla con resumen, ficha y nota al pie. No devuelve nada.
    """
    # Conexión a MT5 (necesaria para las cuentas y las velas) y estilos de la vista.
    inicializar_mt5()
    st.html(CSS)
    # Contenedor con clave jr_wrap: limita el ancho máximo (ver estilos.css).
    with st.container(key="jr_wrap"):
        st.html(
            "<div class='jr-head'><div class='ic'><span class='jrmi'>menu_book</span></div>"
            "<div><div class='jr-title'>Diario</div>"
            "<div class='jr-sub'>Trading journal: registro automático, métricas y notas por operación</div>"
            "</div></div>"
        )
        # Moneda de la cuenta (USD por defecto si MT5 no responde).
        info_c = obtener_info_cuenta()
        m = info_c.get("currency", "USD") if isinstance(info_c, dict) else "USD"
        # Operaciones cerradas reconstruidas desde los deals de MT5 y sus métricas.
        jd = estadisticas_diario.calcular()
        tabla_y_metricas(m, jd["operaciones"], jd["stats"])
        ficha(m, jd["operaciones"])
        # Nota aclaratoria al pie (según el proveedor de datos activo).
        if NOMBRE_PROVEEDOR == "Capital.com":
            nota = ("Operaciones cerradas registradas desde Capital.com (símbolo, resultado y "
                    "fecha). Capital no entrega los precios de entrada/salida ni el R/R que sí "
                    "da MetaTrader 5, por eso esas columnas quedan vacías.")
        else:
            nota = ("Operaciones reconstruidas emparejando los deals de entrada y salida de "
                    "MetaTrader 5. El R/R planificado aparece en operaciones abiertas con SL/TP; "
                    "la captura es un mini-gráfico generado automáticamente.")
        st.html(f"<div class='jr-note'>{nota}</div>")


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
