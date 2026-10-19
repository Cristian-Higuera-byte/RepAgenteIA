# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara secciones .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Bloques de la vista Resumen: tarjetas KPI, nivel de margen, curva de balance, exposición y nota al pie.
Todos reciben el diccionario `s` de herramientas.estadisticas_portafolio.calcular().

Cada función dibuja su bloque directamente con `st.markdown` (HTML con las clases `rs-*` de `estilos.css`); no
devuelven nada. `panel.py` las llama en orden dentro de un fragmento que se refresca solo.
"""
import html
import time

import streamlit as st

from components.resumen.curva import curva_svg
from components.resumen.datos import PERIODOS
from components.resumen.formato import compactar, clase_variacion as _vcls
from components.resumen.tarjetas import tarjeta


def tarjetas_kpi(s: dict) -> None:
    """Rejilla de 8 tarjetas KPI: capital, P&L, rentabilidad, exposición, riesgo, comisiones y drawdown.

    Recibe `s`, el diccionario de estadísticas del portafolio. Dibuja dos filas de cuatro tarjetas dentro de una
    rejilla `rs-grid`. Varios valores llevan atributos `data-pj-*` para que el feed en vivo los actualice sin
    recargar la página."""
    # Atajos a los sub-diccionarios de estadísticas usados por las tarjetas.
    m = s["moneda"]
    cap = s["capital"]
    pnl = s["pnl"]
    com = s["comisiones"]
    exp = s["exposicion"]
    rie = s["riesgo"]
    dd = s["drawdown"]
    div = s["dividendos"]
    rent = s["rentabilidad"]
    # ---------- Fila 1 ----------
    # Totales de P&L del día y del mes, y pastilla con la rentabilidad porcentual (verde si es >= 0).
    d_tot, mes_tot = pnl["dia"]["total"], pnl["mes"]["total"]
    pct = rent["pct"]
    pill = f"<span class='rs-pill {'up' if pct >= 0 else 'down'}'>{pct:+.2f}%</span>"
    # Flotante EN VIVO (feed): mismo dato que el P/G de la barra superior.
    flot_live = ("<span data-pj-acc='profit' data-pj-fmt='signed' "
                 "data-pj-color='1'>{:+,.2f}</span>").format(pnl['dia']['flotante'])
    # Tarjetas de la fila 1: capital, P&L diario, P&L mensual y rentabilidad acumulada.
    fila1 = [
        tarjeta("cap", "Capital (equity)", f"{cap['equity']:,.2f}", "",
              f"Saldo {cap['balance']:,.2f} · Libre {cap['margen_libre']:,.2f}",
              val_attrs=f"data-pj-acc='equity' data-pj-base='{cap['equity']:.2f}'"),
        tarjeta("up" if d_tot >= 0 else "down", "P&amp;L diario",
              compactar(d_tot, signo=True), m,
              f"Realizado {pnl['dia']['realizado']:+,.2f} · Flot. {flot_live} "
              f"· {pnl['dia']['cierres']} cierres", arrow=True, valcls=_vcls(d_tot)),
        tarjeta("up" if mes_tot >= 0 else "down", "P&amp;L mensual",
              compactar(mes_tot, signo=True), m,
              f"Realizado {pnl['mes']['realizado']:+,.2f} · Flot. {flot_live} "
              f"· {pnl['mes']['cierres']} cierres", arrow=True, valcls=_vcls(mes_tot)),
        tarjeta("acum", "Rentabilidad acumulada", compactar(rent['abs'], signo=True), m,
              f"Depósito inicial {cap['deposito_inicial']:,.2f} {m}",
              pill_html=pill, valcls=_vcls(rent['abs'])),
    ]


    # ---------- Fila 2 ----------
    # Textos de riesgo: posiciones sin stop, apalancamiento (exposición / equity) y costos totales (comisión + swap).
    sin_sl = rie["sin_sl"]
    sinsl_txt = f"{sin_sl} sin stop" if sin_sl else "todas con stop"
    apal = (exp["total"] / cap["equity"]) if cap["equity"] else 0.0
    com_tot = com["total"] + com["swap_total"]
    # Drawdown: equity REAL si ya hay snapshots (Tanda 2); si no, el de balance.
    if dd["equity_disponible"]:
        dd_pct, dd_abs_v, dd_lbl = dd["equity_pct"], dd["equity_abs"], "Drawdown (equity)"
        dd_base = f"Caída máx. {dd_abs_v:,.2f} {m} · {dd['equity_puntos']} muestras"
    else:
        dd_pct, dd_abs_v, dd_lbl = dd["balance_pct"], dd["balance_abs"], "Drawdown (balance)"
        dd_base = f"Caída máx. {dd_abs_v:,.2f} {m} · equity acumulando…"
    # Texto del drawdown y de dividendos para el pie de la última tarjeta.
    dd_txt = f"-{dd_pct:.2f}%" if dd_pct else "0%"
    div_txt = (compactar(div['total'], m, signo=True) if abs(div["total"]) > 1e-9
               else "Sin dividendos")
    # Tarjetas de la fila 2: exposición, riesgo definido, comisiones y swaps, y drawdown.
    fila2 = [
        tarjeta("exp", "Exposición total", compactar(exp['total']), m,
              f"Largos {compactar(exp['largos'])} · Cortos {compactar(exp['cortos'])} "
              f"· {apal:.1f}× equity", valcls="rs-neu"),
        tarjeta("risk", "Riesgo definido", compactar(rie['definido'], signo=False), m,
              f"Margen usado {rie['margen_usado']:,.2f} · {sinsl_txt}", valcls="rs-down"),
        tarjeta("fee", "Comisiones y swaps", f"{com_tot:,.2f}", m,
              f"Mes {(com['mes'] + com['swap_mes']):,.2f} · Hoy {(com['hoy'] + com['swap_hoy']):,.2f}",
              valcls="rs-down" if com_tot < 0 else "rs-neu"),
        tarjeta("dd", dd_lbl, dd_txt, "",
              f"{dd_base} · Div. {div_txt}",
              valcls="rs-down" if dd_pct else "rs-neu"),
    ]
    # Las ocho tarjetas se emiten juntas dentro de la rejilla.
    st.markdown("<div class='rs-grid'>" + "".join(fila1 + fila2) + "</div>",
                unsafe_allow_html=True)


def nivel_margen(s: dict) -> None:
    """Panel con la barra del nivel de margen (semáforo).

    Recibe `s`, el diccionario de estadísticas. Si no hay margen en uso (nivel vacío o cero) no dibuja nada. El color
    y la etiqueta cambian por umbrales: 300 % o más Saludable, 150 % o más Moderado y menos En riesgo."""
    rie = s["riesgo"]
    # ---------- Nivel de margen (barra) ----------
    nivel = rie["margin_level"]
    if nivel:
        # Semáforo según el nivel de margen: color de texto, fondo de la etiqueta y etiqueta.
        if nivel >= 300:
            tcol, tbg, tlbl = "#2ebd85", "rgba(46,189,133,.14)", "Saludable"
        elif nivel >= 150:
            tcol, tbg, tlbl = "#f0b429", "rgba(240,180,41,.14)", "Moderado"
        else:
            tcol, tbg, tlbl = "#f6465d", "rgba(246,70,93,.14)", "En riesgo"
        # Barra: 100% (cierre forzoso) a 1000%+ como tope visual.
        ancho = max(4, min(100, nivel / 1000 * 100))
        st.markdown(
            "<div class='rs-panel'><div class='rs-panel-t'>Nivel de margen "
            "<small>(equity ÷ margen usado)</small></div>"
            "<div class='rs-ml-top'>"
            f"<span class='rs-ml-v' style='color:{tcol}' data-pj-acc='margin_level' "
            f"data-pj-fmt='pct'>{nivel:,.0f}%</span>"
            f"<span class='rs-ml-tag' style='color:{tcol};background:{tbg}'>{tlbl}</span></div>"
            f"<div class='rs-ml-bar'><div class='rs-ml-fill' style='width:{ancho:.0f}%;"
            f"background:linear-gradient(90deg,{tcol},{tcol}cc)'></div></div>"
            "<div class='rs-note'>Por debajo de 100% hay cierre forzoso (stop out). "
            "Cuanto más alto, más holgura ante movimientos en contra.</div></div>",
            unsafe_allow_html=True,
        )


def curva_balance(s: dict) -> None:
    """Curva de balance con selector de periodo (el selector y la curva forman un solo bloque).

    Recibe `s`, el diccionario de estadísticas (usa `moneda` y `curva`, lista de pares tiempo y balance). El
    selector guarda su valor en `st.session_state["rs_periodo"]`; según el periodo se filtra la curva y se muestra
    la variación en el rango."""
    m = s["moneda"]
    # ---------- Curva de balance con selector de periodo (interactivo) ----------
    # El selector y la curva van DENTRO del mismo contenedor (rs_curvapanel)
    # para que se lean como un solo bloque (el selector pertenece al gráfico).
    with st.container(key="rs_curvapanel"):
        # Selector de periodo; "Todo" por defecto y sin etiqueta visible.
        periodo = st.segmented_control(
            "Periodo", list(PERIODOS.keys()), default="Todo",
            key="rs_periodo", label_visibility="collapsed")
        # Días del periodo elegido (None = todo el historial) y curva completa de partida.
        dias = PERIODOS.get(periodo or "Todo")
        curva = s["curva"]
        # Se descartan los puntos anteriores al corte; si no queda ninguno, se usan los dos últimos para poder dibujar.
        if dias is not None:
            corte = time.time() - dias * 86400
            curva = [(t, b) for t, b in curva if t >= corte] or s["curva"][-2:]
        # Variación del balance dentro del periodo y su clase de color.
        var = (curva[-1][1] - curva[0][1]) if len(curva) >= 2 else 0.0
        vcls = _vcls(var)
        # Título con la variación y, debajo, el SVG de la curva.
        st.markdown(
            "<div class='rs-panel-t'>Curva de balance "
            "<small>(balance realizado acumulado)</small>"
            f"<span class='right {vcls}'>{var:+,.2f} {m} en el periodo</span></div>"
            + curva_svg(curva, m),
            unsafe_allow_html=True,
        )


def exposicion_por_activo(s: dict) -> None:
    """Tabla de exposición por activo.

    Recibe `s`, el diccionario de estadísticas (usa `exposicion["por_activo"]`). Dibuja una fila por activo con
    lotes, valor nocional, porcentaje de la cartera y una barra proporcional al mayor nocional. Si no hay
    posiciones no dibuja nada. Escapa el nombre del activo con `html.escape`."""
    m = s["moneda"]
    exp = s["exposicion"]
    # ---------- Exposición por activo ----------
    filas = exp["por_activo"]
    if filas:
        # Mayor nocional (1.0 si no hay) y total para escalar las barras y calcular el porcentaje.
        maxn = max((r["notional"] for r in filas), default=1.0) or 1.0
        total = exp["total"] or 1.0
        cuerpo = ""
        # Una fila de tabla por activo; la barra mide al menos 3 % para que siempre se vea.
        for r in filas:
            w = max(3, int(r["notional"] / maxn * 100))
            share = r["notional"] / total * 100
            cuerpo += (
                f"<tr><td class='nm'>{html.escape(str(r['nombre']))}</td>"
                f"<td>{r['volumen']:,.2f}</td>"
                f"<td>{compactar(r['notional'], m)}</td>"
                f"<td>{share:.0f}%</td>"
                f"<td style='width:34%'><div class='rs-barwrap'>"
                f"<div class='bar' style='width:{w}%'></div></div></td></tr>")
        st.markdown(
            "<div class='rs-panel'><div class='rs-panel-t'>Exposición por activo</div>"
            "<table class='rs-expo'><thead><tr><th>Activo</th><th>Lotes</th>"
            "<th>Notional</th><th>% cartera</th><th></th></tr></thead>"
            f"<tbody>{cuerpo}</tbody></table></div>",
            unsafe_allow_html=True,
        )


def nota_pie(s: dict) -> None:
    """Nota al pie sobre el drawdown, los dividendos y el origen de los datos.

    Recibe `s`, el diccionario de estadísticas. El texto cambia si ya hay muestras de equity real o si todavía se
    usa el drawdown de balance."""
    dd = s["drawdown"]
    if dd["equity_disponible"]:
        dd_nota = (f"Drawdown de equity real calculado sobre {dd['equity_puntos']} "
                   "muestras registradas en segundo plano (incluye el flotante de "
                   "posiciones abiertas). ")
    else:
        dd_nota = ("Drawdown de balance por ahora; el de equity real se está "
                   "registrando en segundo plano y aparecerá al reunir más muestras "
                   "(requiere el servidor de datos encendido). ")
    st.markdown(
        f"<div class='rs-note'>{dd_nota}Dividendos según los ajustes que reporte el "
        "bróker; en demo pueden no existir. P&amp;L, comisiones, swaps y exposición "
        "salen de operaciones reales de MetaTrader 5.</div>",
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara secciones .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
