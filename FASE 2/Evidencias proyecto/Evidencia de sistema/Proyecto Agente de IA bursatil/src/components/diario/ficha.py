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

from components.iconografia import icono_activo
from components.diario.datos import EMOCIONES, ESTRATEGIAS
from components.diario.formato import duracion
from components.diario.mini_grafico import mini_grafico_svg
from tools import almacen_diario
from tools.puente_mt5 import obtener_velas_rango


def ficha(m, ops):
    """Dibuja la ficha de la operación elegida en un selector.

    Parámetros: m (moneda de la cuenta, para mostrar importes) y ops (lista de operaciones
    cerradas de estadisticas_diario). Muestra cabecera, mini-gráfico, R/R planificado y
    realizado, y un formulario para guardar estrategia, emoción y razón. Al guardar
    escribe en almacen_diario, marca st.session_state.jr_msg y relanza la app. No
    devuelve nada; no dibuja nada si no hay operaciones.
    """
    # Sin operaciones no hay ficha que mostrar.
    if not ops:
        return
    # Operaciones indexadas por id de posición, para el selector.
    opts = {o["pos_id"]: o for o in ops}

    def etiqueta(pid):
        """Texto de cada opción del selector: indicador de color, fecha de cierre, activo, lado y resultado."""
        o = opts[pid]
        f = datetime.fromtimestamp(o["hora_out"]).strftime("%d-%m %H:%M") if o["hora_out"] else "—"
        lado = "BUY" if o["tipo"] == "Compra" else "SELL"
        dot = "🟢" if o["neto"] >= 0 else "🔴"
        return f"{dot}  {f}   ·   {o['nombre']} {lado}   ·   {o['neto']:+,.2f} {m}"

    st.html("<div class='jr-sec'><h3>Ficha de la operación</h3>"
            "<span class='s'>captura, estrategia, emoción y R/R</span></div>")
    # Tarjeta de la ficha (clave jr_ficha, estilizada en estilos.css).
    with st.container(key="jr_ficha"):
        pid = st.selectbox("Operación", list(opts.keys()), format_func=etiqueta,
                           key="jr_sel", label_visibility="collapsed")
        o = opts.get(pid)
        if not o:
            return

        # Datos de presentación: lado, clase de color y fechas de entrada y salida.
        side = "buy" if o["tipo"] == "Compra" else "sell"
        lbl = "BUY" if side == "buy" else "SELL"
        rcls = "up" if o["neto"] >= 0 else "down"
        f_in = datetime.fromtimestamp(o["hora_in"]).strftime("%d-%m %H:%M") if o["hora_in"] else "—"
        f_out = datetime.fromtimestamp(o["hora_out"]).strftime("%d-%m %H:%M") if o["hora_out"] else "—"
        st.html(
            "<div class='jr-ophead'>"
            f"<span class='sym'>{icono_activo(o['symbol'], 30)}{html.escape(str(o['nombre']))}"
            f"<span class='jpos-side {side}'>{lbl}</span></span>"
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
        rr_plan, rr_real = o.get("rr_plan"), o.get("rr_real")
        plan_txt = (f"R/R planificado <b>{rr_plan:,.2f}</b>" if rr_plan is not None
                    else "R/R planificado <b>—</b> <span style='color:#4b5563'>(abre con SL/TP para registrarlo)</span>")
        real_txt = (f"R realizado <b class='{rcls}'>{rr_real:+.2f}R</b>"
                    if rr_real is not None else "R realizado <b>—</b>")
        st.html(
            f"<div class='jr-rr'><span>{plan_txt}</span><span>{real_txt}</span>"
            f"<span>Comisión <b>{o['comision']:,.2f} {m}</b></span></div>"
        )

        # Notas editables: estrategia y emoción (si el valor guardado no está en la lista, se usa la primera opción).
        c1, c2 = st.columns(2)
        with c1:
            estr = st.selectbox("Estrategia", ESTRATEGIAS,
                                index=(ESTRATEGIAS.index(o["estrategia"])
                                       if o.get("estrategia") in ESTRATEGIAS else 0),
                                key=f"jr_estr_{pid}")
        with c2:
            emo = st.selectbox("Emoción / estado", EMOCIONES,
                               index=(EMOCIONES.index(o["emocion"])
                                      if o.get("emocion") in EMOCIONES else 0),
                               key=f"jr_emo_{pid}")
        # Razón de entrada, texto libre.
        razon = st.text_area("Razón de entrada (opcional)", value=o.get("razon", ""),
                             key=f"jr_raz_{pid}", height=70,
                             placeholder="Por qué entraste, contexto, qué viste…")
        # Guardar: la opción "—" se almacena como cadena vacía.
        if st.button("Guardar nota", key=f"jr_save_{pid}", type="primary"):
            almacen_diario.guardar_notas(
                pid, estrategia=("" if estr == "—" else estr),
                emocion=("" if emo == "—" else emo), razon=razon)
            st.session_state["jr_msg"] = True
            st.rerun()
        # Confirmación que se muestra una sola vez tras guardar.
        if st.session_state.pop("jr_msg", None):
            st.html("<div class='jr-ok'>Nota guardada.</div>")


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
