# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara posiciones .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Posiciones abiertas de Inicio (precio y P/G en vivo por el feed).

Las celdas de precio actual y P/G llevan `data-pj-posc` y `data-pj-pos` con el ticket de la posición; el
script de flujo_precios las actualiza en el navegador sin recargar Streamlit.
"""
import streamlit as st

# Ícono de activo compartido por todo el dashboard.
from components.iconografia import icono_activo
from components.inicio.formato import icono_material
# Posiciones abiertas desde MT5.
from tools.puente_mt5 import obtener_posiciones


def dibujar_posiciones():
    """Dibuja la sección «Posiciones abiertas»: título con contador, botón «Ver cartera» y tabla.

    No recibe parámetros. Consulta MT5; si no hay posiciones muestra un mensaje vacío. El botón fija
    `nav_activo = "portafolio"` y relanza la app. Pensada para ejecutarse dentro de un fragmento.
    """
    # Posiciones abiertas de la cuenta.
    pos = obtener_posiciones()
    # Encabezado: título a la izquierda y botón a la derecha.
    s1, s2 = st.columns([4, 1], vertical_alignment="center")
    with s1:
        st.html(f"<div class='ini-sec'><h3>Posiciones abiertas</h3>"
                f"<span class='s'>{len(pos)} {'posición' if len(pos) == 1 else 'posiciones'}</span></div>")
    with s2:
        if st.button("Ver cartera", key="ini_vercartera", icon=":material/arrow_forward:",
                     width="stretch"):
            st.session_state.nav_activo = "portafolio"
            st.rerun()
    with st.container(key="ini_cartera"):
        if not pos:
            st.html("<div class='pos-empty'>" + icono_material("inventory_2") +
                    "No tienes posiciones abiertas.<br>Las operaciones que abras aparecerán aquí.</div>")
            return
        # Una fila de tabla por posición.
        filas = ""
        for p in pos:
            neto = p["profit"] + p.get("swap", 0.0)     # igual que Cartera y la barra superior
            tk = p.get("ticket")
            compra = p["tipo"] == "Compra"
            sym = p["symbol"].replace("...", "")
            filas += (
                "<tr>"
                f"<td><div class='pos-sym'>{icono_activo(p['symbol'], 26)}{sym}</div></td>"
                f"<td><span class='pos-side {'buy' if compra else 'sell'}'>{p['tipo']}</span></td>"
                f"<td class='r'>{p['volumen']:,.2f}</td>"
                f"<td class='r'>{p['precio_apertura']:,.5f}</td>"
                f"<td class='r' data-pj-posc='{tk}' data-pj-d='5'>{p['precio_actual']:,.5f}</td>"
                f"<td class='r {'car-up' if neto >= 0 else 'car-down'}' data-pj-pos='{tk}'>{neto:+,.2f}</td>"
                "</tr>"
            )
        # Tabla con todas las filas generadas.
        st.html(
            "<table class='pos'><thead><tr>"
            "<th>Activo</th><th>Tipo</th><th class='r'>Volumen</th>"
            "<th class='r'>Apertura</th><th class='r'>Actual</th><th class='r'>P/G</th>"
            "</tr></thead><tbody>" + filas + "</tbody></table>"
        )


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara posiciones .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
