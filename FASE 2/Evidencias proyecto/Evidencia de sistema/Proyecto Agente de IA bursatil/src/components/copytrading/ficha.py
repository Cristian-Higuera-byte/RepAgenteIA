# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara ficha .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ficha de detalle de una estrategia (al hacer clic en una tarjeta): datos, botón de copiar y pestañas.

Los datos son simulados: las series de rendimiento se generan con un generador aleatorio
sembrado con el id de la estrategia, de modo que cada estrategia muestra siempre la misma
curva. Los estilos (fic-*, don-center) están en estilos.css.
"""
import random
from html import escape

import streamlit as st

from components.copytrading.graficos import avatar, rosquilla


def ficha(e: dict):
    """Dibuja la ficha de detalle de una estrategia.

    Recibe `e`, el diccionario de la estrategia (ver estrategias.json). Muestra el botón
    "Atrás" (limpia st.session_state.ct_estrategia y relanza), la cabecera con avatar y
    rentabilidad, la información del gestor, el botón de copiar (solo avisa con un toast,
    sin copiar nada real) y tres pestañas: Rendimiento, Riesgo y Cartera. No devuelve nada.
    """
    # Vuelta al listado.
    if st.button("← Atrás", key="ct_atras"):
        st.session_state.ct_estrategia = None
        st.rerun()

    # Cabecera: avatar y nombre a la izquierda, rentabilidad a la derecha.
    c_av, c_rent = st.columns([3, 1], vertical_alignment="center")
    with c_av:
        st.html(
            f"<div class='fic-av'>{avatar(e['nombre'])}</div>"
            f"<div class='fic-nm'>{escape(str(e['nombre']))}</div><div class='fic-gs'>@{escape(str(e['gestor']))}</div>"
        )
    with c_rent:
        st.html(f"<div class='fic-sec' style='text-align:right;'>Rentabilidad 1 mes</div>"
                f"<div class='fic-rent'>{e['rent']:.2f}%</div>")

    # Bloque de texto: tipo, categoría, biografía, descripción e información importante.
    st.html(
        f"<div style='margin-top:8px;'><span class='fic-chip'>👥 {escape(str(e['tipo']))}</span>"
        f"<span class='fic-chip'>Ⓢ {escape(str(e['cat']))}</span></div>"
        f"<div class='fic-sec'>Biografía del gestor</div><div class='fic-txt'>{escape(str(e['bio']))}</div>"
        f"<div class='fic-sec'>Descripción</div><div class='fic-txt'>{escape(str(e['desc']))}</div>"
        f"<div class='fic-sec'>Información importante</div><div style='margin-top:4px;'>"
        f"<span class='fic-chip'>Apalancamiento: {e['apalancamiento']}</span>"
        f"<span class='fic-chip'>Comisiones: {e['comision']}%</span>"
        f"<span class='fic-chip'>Inversores: {e['inversores']}</span>"
        f"<span class='fic-chip'>Inversión mínima: ${e['inv_min']:,}</span>"
        f"<span class='fic-chip'>Invertido: ${e['invertido']:,}</span></div>"
    )

    # Botón de copia: en esta versión solo informa que está en modo demostración.
    if st.button("＋ Cuenta de inversor  ·  Copiar estrategia", key="ct_copiar",
                 type="primary", width="stretch"):
        st.toast("Copy trading en modo demostración (UI). La copia real se habilitará "
                 "cuando conectemos la fuente de datos.")

    # Pestañas de detalle.
    tab_rend, tab_riesgo, tab_cart = st.tabs(["Rendimiento", "Riesgo", "Cartera"])
    with tab_rend:
        c_graf, c_don = st.columns([2, 1], vertical_alignment="center")
        with c_graf:
            # Serie simulada de 30 puntos con sesgo alcista, reproducible por estrategia.
            rnd = random.Random(e["id"] + "perf")
            serie = []
            base = 1000.0
            for _ in range(30):
                base *= 1 + rnd.uniform(-0.01, 0.045)
                serie.append(base)
            st.area_chart(serie, height=230, color="#3fb950")
        with c_don:
            # Dona del ratio de victorias con el total de operaciones en el centro.
            st.html(rosquilla(e["win"]))
            st.html(f"<div class='don-center'><div class='n'>{e['ops']:,}</div>"
                    f"<div class='l'>Operaciones totales</div></div>")
        # Métricas resumen.
        g1, g2, g3 = st.columns(3)
        g1.metric("Rentabilidad 1 mes", f"{e['rent']:.2f}%")
        g2.metric("Ratio de victorias", f"{e['win']}%")
        g3.metric("Operaciones", f"{e['ops']:,}")
    # Pestaña de riesgo: métricas simuladas.
    with tab_riesgo:
        r1, r2, r3 = st.columns(3)
        r1.metric("Drawdown máx.", f"{e['drawdown']}%")
        r2.metric("Apalancamiento", f"{e['apalancamiento']}:1")
        nivel = {"bajo": "Bajo", "medio": "Medio", "alto": "Alto"}[e["riesgo"]]
        r3.metric("Nivel de riesgo", nivel)
        st.caption("Métricas de riesgo simuladas (MVP).")
    # Pestaña de cartera: pesos simulados por tipo de activo.
    with tab_cart:
        st.caption("Distribución simulada de la cartera de la estrategia.")
        st.bar_chart({"Peso %": {"Forex": 45, "Índices": 25, "Materias primas": 20, "Cripto": 10}})


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara ficha .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
