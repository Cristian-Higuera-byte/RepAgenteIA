# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara tabla .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Tabla de operaciones cerradas del Diario con su resumen de métricas (win rate, profit factor, R/R,
expectancy, drawdown y P&L).

Muestra como máximo las 20 operaciones más recientes que le entrega panel.py. Los estilos
(diario-suma, jpos y derivados) están en estilos.css.
"""
import html
from datetime import datetime

import streamlit as st

from componentes_plataforma.iconografia import icono_activo
from componentes_plataforma.diario.formato import duracion, factor, clase_sube_baja


# TITULO TABLA Y METRICAS

def tabla_y_metricas(m, ops, stt):
    """Dibuja el resumen de métricas y la tabla de operaciones cerradas.

    Parámetros: m (moneda de la cuenta), ops (lista de operaciones cerradas) y stt
    (diccionario de estadísticas: n, win_rate, profit_factor, expectancy, pnl, max_dd,
    rr_prom, ganadoras, perdedoras, etc.). Si no hay operaciones muestra un aviso vacío.
    No devuelve nada.
    """
    # Título de la sección.
    st.html("<div class='diario-seccion'><h3>Diario de operaciones</h3>"
            "<span class='s'>registro automático de operaciones cerradas</span></div>")
    # Tarjeta contenedora (clave diario_tarjeta, estilizada en estilos.css).
    with st.container(key="diario_tarjeta"):
        if stt["n"] == 0:
            st.html("<div class='diario-vacio'><span class='jrmi' style='font-size:30px'>history</span>"
                    "Todavía no hay operaciones cerradas.<br>"
                    "Cada operación que cierres quedará registrada aquí automáticamente.</div>")
            return

        # Métricas principales y subtítulo del R/R (R medio si hay operaciones con plan; si no, ganancia y pérdida medias).
        wr = stt["win_rate"]
        pf = stt["profit_factor"]
        exposicion = stt["expectancy"]
        ganancia_perdida = stt["pnl"]
        riesgo_beneficio_subtitulo = (f"R medio {stt['r_medio']:+.2f} · {stt['con_plan']} c/plan"
                  if stt.get("r_medio") is not None
                  else f"gana {stt['avg_win']:,.0f} / pierde {stt['avg_loss']:,.0f}")
        # Tarjetas del resumen: (título, valor, clase de color, subtítulo).
        elementos = [
            ("Win rate", f"{wr:.1f}%", "up" if wr >= 50 else "down",
             f"{stt['ganadoras']}G / {stt['perdedoras']}P"),
            ("Profit factor", factor(pf), "up" if pf >= 1 else "down", "ganancias ÷ pérdidas"),
            ("R/R promedio", factor(stt["rr_prom"]), "", riesgo_beneficio_subtitulo),
            ("Expectancy", f"{exposicion:+,.2f}", "up" if exposicion >= 0 else "down", f"por operación · {m}"),
            ("Max drawdown", f"-{stt['max_dd']:,.2f}", "down" if stt["max_dd"] else "",
             f"en cerradas · {m}"),
            ("P&amp;L (cerradas)", f"{ganancia_perdida:+,.2f}", "up" if ganancia_perdida >= 0 else "down",
             f"{stt['n']} operaciones · {m}"),
        ]
        # HTML del resumen de métricas.
        sum_html = "".join(
            f"<div class='it'><span class='k'>{k}</span>"
            f"<span class='v {cls}'>{v}</span><span class='s'>{s}</span></div>"
            for k, v, cls, s in elementos)

        # Filas de la tabla: solo las 20 operaciones más recientes.
        filas = ""
        for o in ops[:20]:
            lado = "buy" if o["tipo"] == "Compra" else "sell"
            etiqueta = "BUY" if lado == "buy" else "SELL"
            neto = o["neto"]
            ncls = "up" if neto >= 0 else "down"
            fecha = (datetime.fromtimestamp(o["hora_out"]).strftime("%d-%m %H:%M")
                     if o["hora_out"] else "—")
            riesgo_beneficio = o.get("rr_real")
            estrategia = (html.escape(str(o.get("estrategia", "") or ""))
                    or "<span style='color:#424b58'>—</span>")
            filas += (
                "<tr>"
                f"<td class='diario-posicion-fecha'>{fecha}</td>"
                f"<td><div class='diario-posicion-simbolo'>{icono_activo(o['symbol'], 26)}"
                f"{html.escape(str(o['nombre']))}</div></td>"
                f"<td><span class='diario-posicion-lado {lado}'>{etiqueta}</span></td>"
                f"<td class='r'>{o['volumen']:,.2f}</td>"
                f"<td class='r'>{o['entrada']:,.5f}</td>"
                f"<td class='r'>{o['salida']:,.5f}</td>"
                f"<td class='r'>{duracion(o['duracion_s'])}</td>"
                f"<td class='r {clase_sube_baja(riesgo_beneficio) if riesgo_beneficio is not None else ''}'>"
                f"{'—' if riesgo_beneficio is None else f'{riesgo_beneficio:+.2f}R'}</td>"
                f"<td class='diario-posicion-estrategia'>{estrategia}</td>"
                f"<td class='r'><span class='diario-posicion-resultado {ncls}'>{neto:+,.2f}</span></td>"
                "</tr>")

        # Resumen y tabla en un solo bloque HTML.
        st.html(
            f"<div class='diario-suma'>{sum_html}</div>"
            "<table class='jpos'><thead><tr>"
            "<th>Cierre</th><th>Activo</th><th>Dir.</th><th class='r'>Lotes</th>"
            "<th class='r'>Entrada</th><th class='r'>Salida</th><th class='r'>Duración</th>"
            "<th class='r'>R/R</th><th>Estrategia</th><th class='r'>Resultado</th>"
            f"</tr></thead><tbody>{filas}</tbody></table>"
        )


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara tabla .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
