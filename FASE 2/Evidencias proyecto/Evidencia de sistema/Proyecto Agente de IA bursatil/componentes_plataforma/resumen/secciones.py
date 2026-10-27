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

from componentes_plataforma.resumen.curva import curva_svg
from componentes_plataforma.resumen.datos import PERIODOS
from componentes_plataforma.resumen.formato import compactar, clase_variacion as _vcls
from componentes_plataforma.resumen.tarjetas import tarjeta


# TITULO TARJETAS KPI

def tarjetas_kpi(s: dict) -> None:
    """Rejilla de 8 tarjetas KPI: capital, P&L, rentabilidad, exposición, riesgo, comisiones y drawdown.

    Recibe `s`, el diccionario de estadísticas del portafolio. Dibuja dos filas de cuatro tarjetas dentro de una
    rejilla `resumen-cuadricula`. Varios valores llevan atributos `data-pj-*` para que el feed en vivo los actualice sin
    recargar la página."""
    # Atajos a los sub-diccionarios de estadísticas usados por las tarjetas.
    m = s["moneda"]
    capital = s["capital"]
    ganancia_perdida = s["pnl"]
    comision = s["comisiones"]
    exposicion = s["exposicion"]
    rie = s["riesgo"]
    drawdown = s["drawdown"]
    div = s["dividendos"]
    rentabilidad = s["rentabilidad"]
    # ---------- Fila 1 ----------
    # Totales de P&L del día y del mes, y pastilla con la rentabilidad porcentual (verde si es >= 0).
    d_tot, mes_tot = ganancia_perdida["dia"]["total"], ganancia_perdida["mes"]["total"]
    porcentaje = rentabilidad["pct"]
    pastilla = f"<span class='resumen-pastilla {'up' if porcentaje >= 0 else 'down'}'>{porcentaje:+.2f}%</span>"
    # Flotante EN VIVO (feed): mismo dato que el P/G de la barra superior.
    flot_live = ("<span data-pj-acc='profit' data-pj-fmt='signed' "
                 "data-pj-color='1'>{:+,.2f}</span>").format(ganancia_perdida['dia']['flotante'])
    # Tarjetas de la fila 1: capital, P&L diario, P&L mensual y rentabilidad acumulada.
    fila1 = [
        tarjeta("cap", "Capital (equity)", f"{capital['equity']:,.2f}", "",
              f"Saldo {capital['balance']:,.2f} · Libre {capital['margen_libre']:,.2f}",
              valor_attrs=f"data-pj-acc='equity' data-pj-base='{capital['equity']:.2f}'"),
        tarjeta("up" if d_tot >= 0 else "down", "P&amp;L diario",
              compactar(d_tot, signo=True), m,
              f"Realizado {ganancia_perdida['dia']['realizado']:+,.2f} · Flot. {flot_live} "
              f"· {ganancia_perdida['dia']['cierres']} cierres", arrow=True, valcls=_vcls(d_tot)),
        tarjeta("up" if mes_tot >= 0 else "down", "P&amp;L mensual",
              compactar(mes_tot, signo=True), m,
              f"Realizado {ganancia_perdida['mes']['realizado']:+,.2f} · Flot. {flot_live} "
              f"· {ganancia_perdida['mes']['cierres']} cierres", arrow=True, valcls=_vcls(mes_tot)),
        tarjeta("acum", "Rentabilidad acumulada", compactar(rentabilidad['abs'], signo=True), m,
              f"Depósito inicial {capital['deposito_inicial']:,.2f} {m}",
              pastilla_html=pastilla, valcls=_vcls(rentabilidad['abs'])),
    ]


    # ---------- Fila 2 ----------
    # Textos de riesgo: posiciones sin stop, apalancamiento (exposición / equity) y costos totales (comisión + swap).
    sin_stop_loss = rie["sin_sl"]
    sinsl_texto = f"{sin_stop_loss} sin stop" if sin_stop_loss else "todas con stop"
    apal = (exposicion["total"] / capital["equity"]) if capital["equity"] else 0.0
    comision_tot = comision["total"] + comision["swap_total"]
    # Drawdown: equity REAL si ya hay snapshots (Tanda 2); si no, el de balance.
    if drawdown["equity_disponible"]:
        drawdown_porcentaje, drawdown_abs_v, drawdown_etiqueta = drawdown["equity_pct"], drawdown["equity_abs"], "Drawdown (equity)"
        drawdown_base = f"Caída máx. {drawdown_abs_v:,.2f} {m} · {drawdown['equity_puntos']} muestras"
    else:
        drawdown_porcentaje, drawdown_abs_v, drawdown_etiqueta = drawdown["balance_pct"], drawdown["balance_abs"], "Drawdown (balance)"
        drawdown_base = f"Caída máx. {drawdown_abs_v:,.2f} {m} · equity acumulando…"
    # Texto del drawdown y de dividendos para el pie de la última tarjeta.
    drawdown_texto = f"-{drawdown_porcentaje:.2f}%" if drawdown_porcentaje else "0%"
    div_texto = (compactar(div['total'], m, signo=True) if abs(div["total"]) > 1e-9
               else "Sin dividendos")
    # Tarjetas de la fila 2: exposición, riesgo definido, comisiones y swaps, y drawdown.
    fila2 = [
        tarjeta("exp", "Exposición total", compactar(exposicion['total']), m,
              f"Largos {compactar(exposicion['largos'])} · Cortos {compactar(exposicion['cortos'])} "
              f"· {apal:.1f}× equity", valcls="resumen-neutro"),
        tarjeta("risk", "Riesgo definido", compactar(rie['definido'], signo=False), m,
              f"Margen usado {rie['margen_usado']:,.2f} · {sinsl_texto}", valcls="resumen-baja"),
        tarjeta("fee", "Comisiones y swaps", f"{comision_tot:,.2f}", m,
              f"Mes {(comision['mes'] + comision['swap_mes']):,.2f} · Hoy {(comision['hoy'] + comision['swap_hoy']):,.2f}",
              valcls="resumen-baja" if comision_tot < 0 else "resumen-neutro"),
        tarjeta("dd", drawdown_etiqueta, drawdown_texto, "",
              f"{drawdown_base} · Div. {div_texto}",
              valcls="resumen-baja" if drawdown_porcentaje else "resumen-neutro"),
    ]
    # Las ocho tarjetas se emiten juntas dentro de la rejilla.
    st.markdown("<div class='resumen-cuadricula'>" + "".join(fila1 + fila2) + "</div>",
                unsafe_allow_html=True)


# TITULO NIVEL MARGEN

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
            "<div class='resumen-panel'><div class='resumen-panel-t'>Nivel de margen "
            "<small>(equity ÷ margen usado)</small></div>"
            "<div class='resumen-nivel-margen-superior'>"
            f"<span class='resumen-nivel-margen-v' style='color:{tcol}' data-pj-acc='margin_level' "
            f"data-pj-fmt='pct'>{nivel:,.0f}%</span>"
            f"<span class='resumen-nivel-margen-etiqueta' style='color:{tcol};background:{tbg}'>{tlbl}</span></div>"
            f"<div class='resumen-nivel-margen-barra'><div class='resumen-nivel-margen-fill' style='width:{ancho:.0f}%;"
            f"background:linear-gradient(90deg,{tcol},{tcol}cc)'></div></div>"
            "<div class='resumen-nota'>Por debajo de 100% hay cierre forzoso (stop out). "
            "Cuanto más alto, más holgura ante movimientos en contra.</div></div>",
            unsafe_allow_html=True,
        )


# TITULO CURVA BALANCE

def curva_balance(s: dict) -> None:
    """Curva de balance con selector de periodo (el selector y la curva forman un solo bloque).

    Recibe `s`, el diccionario de estadísticas (usa `moneda` y `curva`, lista de pares tiempo y balance). El
    selector guarda su valor en `st.session_state["resumen_periodo"]`; según el periodo se filtra la curva y se muestra
    la variación en el rango."""
    m = s["moneda"]
    # ---------- Curva de balance con selector de periodo (interactivo) ----------
    # El selector y la curva van DENTRO del mismo contenedor (resumen_curvapanel)
    # para que se lean como un solo bloque (el selector pertenece al gráfico).
    with st.container(key="resumen_curvapanel"):
        # Selector de periodo; "Todo" por defecto y sin etiqueta visible.
        periodo = st.segmented_control(
            "Periodo", list(PERIODOS.keys()), default="Todo",
            key="resumen_periodo", label_visibility="collapsed")
        # Días del periodo elegido (None = todo el historial) y curva completa de partida.
        dias = PERIODOS.get(periodo or "Todo")
        curva = s["curva"]
        # Se descartan los puntos anteriores al corte; si no queda ninguno, se usan los dos últimos para poder dibujar.
        if dias is not None:
            corte = time.time() - dias * 86400
            curva = [(t, b) for t, b in curva if t >= corte] or s["curva"][-2:]
        # Variación del balance dentro del periodo y su clase de color.
        variacion = (curva[-1][1] - curva[0][1]) if len(curva) >= 2 else 0.0
        vcls = _vcls(variacion)
        # Título con la variación y, debajo, el SVG de la curva.
        st.markdown(
            "<div class='resumen-panel-t'>Curva de balance "
            "<small>(balance realizado acumulado)</small>"
            f"<span class='right {vcls}'>{variacion:+,.2f} {m} en el periodo</span></div>"
            + curva_svg(curva, m),
            unsafe_allow_html=True,
        )


# TITULO EXPOSICION POR ACTIVO

def exposicion_por_activo(s: dict) -> None:
    """Tabla de exposición por activo.

    Recibe `s`, el diccionario de estadísticas (usa `exposicion["por_activo"]`). Dibuja una fila por activo con
    lotes, valor nocional, porcentaje de la cartera y una barra proporcional al mayor nocional. Si no hay
    posiciones no dibuja nada. Escapa el nombre del activo con `html.escape`."""
    m = s["moneda"]
    exposicion = s["exposicion"]
    # ---------- Exposición por activo ----------
    filas = exposicion["por_activo"]
    if filas:
        # Mayor nocional (1.0 si no hay) y total para escalar las barras y calcular el porcentaje.
        maxn = max((r["notional"] for r in filas), default=1.0) or 1.0
        total = exposicion["total"] or 1.0
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
                f"<td style='width:34%'><div class='resumen-barwrap'>"
                f"<div class='bar' style='width:{w}%'></div></div></td></tr>")
        st.markdown(
            "<div class='resumen-panel'><div class='resumen-panel-t'>Exposición por activo</div>"
            "<table class='resumen-exposicion'><thead><tr><th>Activo</th><th>Lotes</th>"
            "<th>Notional</th><th>% cartera</th><th></th></tr></thead>"
            f"<tbody>{cuerpo}</tbody></table></div>",
            unsafe_allow_html=True,
        )


# TITULO NOTA PIE

def nota_pie(s: dict) -> None:
    """Nota al pie sobre el drawdown, los dividendos y el origen de los datos.

    Recibe `s`, el diccionario de estadísticas. El texto cambia si ya hay muestras de equity real o si todavía se
    usa el drawdown de balance."""
    drawdown = s["drawdown"]
    if drawdown["equity_disponible"]:
        drawdown_nota = (f"Drawdown de equity real calculado sobre {drawdown['equity_puntos']} "
                   "muestras registradas en segundo plano (incluye el flotante de "
                   "posiciones abiertas). ")
    else:
        drawdown_nota = ("Drawdown de balance por ahora; el de equity real se está "
                   "registrando en segundo plano y aparecerá al reunir más muestras "
                   "(requiere el servidor de datos encendido). ")
    st.markdown(
        f"<div class='resumen-nota'>{drawdown_nota}Dividendos según los ajustes que reporte el "
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
