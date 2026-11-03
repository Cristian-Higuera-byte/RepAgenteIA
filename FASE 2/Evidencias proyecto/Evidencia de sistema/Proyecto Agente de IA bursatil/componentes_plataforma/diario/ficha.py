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

"""Ficha de la operación: cabecera, mini-gráfico, R/R y notas editables (estrategia, emoción, razón).

Las notas se guardan con herramientas.almacen_diario y el mini-gráfico se genera con las
velas de MT5 del rango de la operación (obtener_velas_rango). Estilos jr-* en estilos.css.
"""
import html
from datetime import datetime

import streamlit as st

from componentes_plataforma.iconografia import icono_activo
from componentes_plataforma.diario.datos import EMOCIONES, ESTRATEGIAS
from componentes_plataforma.diario.formato import duracion
from componentes_plataforma.diario.mini_grafico import mini_grafico_svg
from herramientas import almacen_diario
from herramientas.puente_mt5 import obtener_velas_rango


# TITULO FICHA

def ficha(m, ops):
    """Dibuja la ficha de la operación elegida en un selector.

    Parámetros: m (moneda de la cuenta, para mostrar importes) y ops (lista de operaciones
    cerradas de estadisticas_diario). Muestra cabecera, mini-gráfico, R/R planificado y
    realizado, y un formulario para guardar estrategia, emoción y razón. Al guardar
    escribe en almacen_diario, marca st.session_state.diario_mensaje y relanza la app. No
    devuelve nada; no dibuja nada si no hay operaciones.
    """
    # Sin operaciones no hay ficha que mostrar.
    if not ops:
        return
    # Operaciones indexadas por id de posición, para el selector.
    opciones = {o["pos_id"]: o for o in ops}

    def etiqueta(pid):
        """Texto de cada opción del selector: indicador de color, fecha de cierre, activo, lado y resultado."""
        o = opciones[pid]
        f = datetime.fromtimestamp(o["hora_out"]).strftime("%d-%m %H:%M") if o["hora_out"] else "—"
        lado = "BUY" if o["tipo"] == "Compra" else "SELL"
        dot = "🟢" if o["neto"] >= 0 else "🔴"
        return f"{dot}  {f}   ·   {o['nombre']} {lado}   ·   {o['neto']:+,.2f} {m}"

    st.html("<div class='diario-seccion'><h3>Ficha de la operación</h3>"
            "<span class='s'>captura, estrategia, emoción y R/R</span></div>")
    # Tarjeta de la ficha (clave diario_ficha, estilizada en estilos.css).
    with st.container(key="diario_ficha"):
        pid = st.selectbox("Operación", list(opciones.keys()), format_func=etiqueta,
                           key="diario_seleccion", label_visibility="collapsed")
        o = opciones.get(pid)
        if not o:
            return

        # Datos de presentación: lado, clase de color y fechas de entrada y salida.
        side = "buy" if o["tipo"] == "Compra" else "sell"
        lbl = "BUY" if side == "buy" else "SELL"
        rcls = "up" if o["neto"] >= 0 else "down"
        f_in = datetime.fromtimestamp(o["hora_in"]).strftime("%d-%m %H:%M") if o["hora_in"] else "—"
        f_out = datetime.fromtimestamp(o["hora_out"]).strftime("%d-%m %H:%M") if o["hora_out"] else "—"
        st.html(
            "<div class='diario-operacion-cabecera'>"
            f"<span class='sym'>{icono_activo(o['symbol'], 30)}{html.escape(str(o['nombre']))}"
            f"<span class='diario-posicion-lado {side}'>{lbl}</span></span>"
            f"<span class='meta'>{o['volumen']:,.2f} lotes · {f_in} → {f_out} · "
            f"{duracion(o['duracion_s'])}</span>"
            f"<span class='res {rcls}'>{o['neto']:+,.2f} {m}</span></div>"
        )

        # El mini-gráfico es un SVG grande: st.markdown(unsafe_allow_html) lo respeta
        # mejor que st.html (que puede perder el alto/los nodos del SVG).
        st.markdown(
            mini_grafico_svg(obtener_velas_rango(o["symbol"], o["hora_in"], o["hora_out"]), o),
            unsafe_allow_html=True)

        # Línea de R/R: el planificado solo existe si la operación se abrió con SL/TP.
        riesgo_beneficio_plan, riesgo_beneficio_real = o.get("rr_plan"), o.get("rr_real")
        plan_texto = (f"R/R planificado <b>{riesgo_beneficio_plan:,.2f}</b>" if riesgo_beneficio_plan is not None
                    else "R/R planificado <b>—</b> <span style='color:#4b5563'>(abre con SL/TP para registrarlo)</span>")
        real_texto = (f"R realizado <b class='{rcls}'>{riesgo_beneficio_real:+.2f}R</b>"
                    if riesgo_beneficio_real is not None else "R realizado <b>—</b>")
        st.html(
            f"<div class='diario-riesgo-beneficio'><span>{plan_texto}</span><span>{real_texto}</span>"
            f"<span>Comisión <b>{o['comision']:,.2f} {m}</b></span></div>"
        )

        # Notas editables: estrategia y emoción (si el valor guardado no está en la lista, se usa la primera opción).
        c1, c2 = st.columns(2)
        with c1:
            estrategia = st.selectbox("Estrategia", ESTRATEGIAS,
                                index=(ESTRATEGIAS.index(o["estrategia"])
                                       if o.get("estrategia") in ESTRATEGIAS else 0),
                                key=f"diario_estrategia_{pid}")
        with c2:
            emocion = st.selectbox("Emoción / estado", EMOCIONES,
                               index=(EMOCIONES.index(o["emocion"])
                                      if o.get("emocion") in EMOCIONES else 0),
                               key=f"diario_emocion_{pid}")
        # Razón de entrada, texto libre.
        razon = st.text_area("Razón de entrada (opcional)", value=o.get("razon", ""),
                             key=f"diario_razon_{pid}", height=70,
                             placeholder="Por qué entraste, contexto, qué viste…")
        # Guardar: la opción "—" se almacena como cadena vacía.
        if st.button("Guardar nota", key=f"diario_guardar_{pid}", type="primary"):
            almacen_diario.guardar_notas(
                pid, estrategia=("" if estrategia == "—" else estrategia),
                emocion=("" if emocion == "—" else emocion), razon=razon)
            st.session_state["diario_mensaje"] = True
            st.rerun()
        # Confirmación que se muestra una sola vez tras guardar.
        if st.session_state.pop("diario_mensaje", None):
            st.html("<div class='diario-aceptar'>Nota guardada.</div>")


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
