# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara historial .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Historial de operaciones cerradas de Inicio, con "Ver más / Ver menos" (de a 10 hacia abajo).

Lee el historial de MT5 y lo muestra como resumen (P/G realizado, cantidad y tasa de aciertos) más una
tabla. El número de filas visibles se guarda en `st.session_state.inicio_historial_n`.
"""
import datetime as _dt

import streamlit as st

# Ícono de activo compartido por todo el dashboard.
from componentes_plataforma.iconografia import icono_activo
from componentes_plataforma.inicio.formato import icono_material
# Historial de operaciones cerradas desde MT5.
from herramientas.puente_mt5 import obtener_historial


# TITULO DIBUJAR HISTORIAL

def dibujar_historial():
    """Dibuja la sección de historial: título con contador, resumen, tabla y botones Ver más / Ver menos.

    No recibe parámetros. Consulta MT5, muestra un mensaje vacío si no hay operaciones cerradas y, en
    caso contrario, pinta las primeras `inicio_historial_n` filas (10 por defecto). Los botones ajustan ese
    contador en session_state y relanzan solo el fragmento.
    """
    # Operaciones cerradas obtenidas de MT5.
    historial = obtener_historial()
    st.html("<div class='inicio-seccion'><h3>Historial</h3>"
            f"<span class='s'>{len(historial)} "
            f"{'operación cerrada' if len(historial) == 1 else 'operaciones cerradas'}</span></div>")
    with st.container(key="inicio_historial"):
        if not historial:
            st.html("<div class='posicion-vacio'>" + icono_material("history") +
                    "No hay operaciones cerradas.<br>"
                    "Aquí verás las compras y ventas que cierres.</div>")
            return
        # Métricas del resumen: P/G total, operaciones ganadoras y porcentaje de acierto.
        total = sum(h["pg"] for h in historial)
        ganadoras = sum(1 for h in historial if h["pg"] > 0)
        porcentaje = ganadoras / len(historial) * 100
        # Barra de resumen con las tres métricas.
        st.html(
            "<div class='historial-suma'>"
            "<div class='it'><span class='k'>P/G realizado</span>"
            f"<span class='v {'car-sube' if total >= 0 else 'car-baja'}'>{total:+,.2f}</span></div>"
            "<div class='it'><span class='k'>Operaciones</span>"
            f"<span class='v'>{len(historial)}</span></div>"
            "<div class='it'><span class='k'>Ganadoras</span>"
            f"<span class='v'>{ganadoras}/{len(historial)} · {porcentaje:.0f}%</span></div>"
            "</div>"
        )
        # Cantidad de filas visibles (crece de 10 en 10 con «Ver más»).
        n = st.session_state.get("inicio_historial_n", 10)
        filas = ""
        # Una fila de tabla por operación, de la más reciente a la más antigua.
        for h in historial[:n]:
            compra = h["tipo"] == "Compra"
            simbolo = h["symbol"].replace("...", "")
            fecha = _dt.datetime.fromtimestamp(h["fecha"]).strftime("%d-%m %H:%M")
            filas += (
                "<tr>"
                f"<td class='historial-fecha'>{fecha}</td>"
                f"<td><div class='posicion-simbolo'>{icono_activo(h['symbol'], 26)}{simbolo}</div></td>"
                f"<td><span class='posicion-lado {'buy' if compra else 'sell'}'>{h['tipo']}</span></td>"
                f"<td class='r'>{h['volumen']:,.2f}</td>"
                f"<td class='r'>{h['precio_cierre']:,.5f}</td>"
                f"<td class='r {'car-sube' if h['pg'] >= 0 else 'car-baja'}'>{h['pg']:+,.2f}</td>"
                "</tr>"
            )
        # Tabla completa con las filas acumuladas.
        st.html(
            "<table class='pos'><thead><tr>"
            "<th>Fecha</th><th>Activo</th><th>Tipo</th><th class='r'>Volumen</th>"
            "<th class='r'>Cierre</th><th class='r'>P/G</th>"
            "</tr></thead><tbody>" + filas + "</tbody></table>"
        )
    # Ver más / Ver menos (despliegan de a 10 hacia abajo, dentro de Inicio)
    # Se relee el contador porque este bloque queda fuera del contenedor de la tabla.
    n = st.session_state.get("inicio_historial_n", 10)
    if len(historial) > 10:
        # Operaciones aún ocultas; el botón «Ver más» solo aparece si quedan.
        restantes = len(historial) - n
        c1, c2, _ = st.columns([1, 1, 3])
        if restantes > 0:
            with c1:
                if st.button(f"Ver más ({restantes})", key="inicio_ver_mas",
                             icon=":material/expand_more:", width="stretch"):
                    st.session_state.inicio_historial_n = n + 10
                    st.rerun(scope="fragment")
        # «Ver menos» vuelve a las 10 primeras filas.
        if n > 10:
            with c2:
                if st.button("Ver menos", key="inicio_ver_menos",
                             icon=":material/expand_less:", width="stretch"):
                    st.session_state.inicio_historial_n = 10
                    st.rerun(scope="fragment")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara historial .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
