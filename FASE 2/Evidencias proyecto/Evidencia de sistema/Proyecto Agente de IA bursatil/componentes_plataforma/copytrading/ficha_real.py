# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara ficha_real .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ficha de detalle de una estrategia REAL de copy trading (con los datos registrados de su gestor).

Es la versión con datos de `ficha.py` (que sigue mostrando las estrategias de ejemplo). Presenta lo mismo que XM: cabecera con la rentabilidad de 1 mes,
biografía, descripción y datos clave; y tres pestañas:
  - Rendimiento: curva con selector de periodo, dona de operaciones (ganadoras y perdedoras con la mejor y la peor) y barras mensuales de
    rentabilidades, inversores e invertido con selector de año.
  - Riesgo: drawdown máximo, apalancamiento, nivel de riesgo, factor de beneficio, mejor y peor operación.
  - Cartera: reparto por tipo de activo y tabla de operaciones abiertas y cerradas.
Los datos salen de `metricas_estrategia.detalle`. El botón de copiar abre la ventana de `copiar.py` (cuenta de inversor y configuración de la copia). Los estilos (fic-*, don-centro)
están en estilos.css.
"""
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from componentes_plataforma.copytrading.copiar import dialogo_copiar
from componentes_plataforma.copytrading.graficos import avatar, rosquilla
from herramientas import gestor_autenticacion, metricas_estrategia

# Periodos del selector de la curva: texto y días hacia atrás (None = todo el historial)
_PERIODOS = {"7 días": 7, "30 días": 30, "90 días": 90, "1 año": 365, "Todo": None}
_MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


# TITULO A NUMERO

def _n(valor, defecto: float = 0.0) -> float:
    """Convierte a número (Supabase puede entregar los numéricos como texto); `defecto` si está vacío."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


# TITULO CURVA DEL PERIODO

def _curva(diario: list, dias: int | None) -> pd.DataFrame:
    """Serie de rentabilidad (%) de los últimos `dias` días, reiniciada en 0 al comienzo del periodo, como DataFrame con índice de fechas."""
    tramo = diario if dias is None else diario[-(dias + 1):]
    if not tramo:
        return pd.DataFrame({"Rentabilidad %": []})
    base = 1 + _n(tramo[0]["rent_acumulada"]) / 100
    valores = [round(((1 + _n(d["rent_acumulada"]) / 100) / base - 1) * 100, 2) if base > 0 else 0.0 for d in tramo]
    return pd.DataFrame({"Rentabilidad %": valores}, index=pd.to_datetime([d["dia"] for d in tramo]))


# TITULO BARRAS MENSUALES

def _mensual(diario: list, anio: int, vista: str) -> pd.DataFrame:
    """Valores por mes del año `anio` para la vista elegida: «Rentabilidades» (% del mes), «Inversores» o «Invertido» (valor al cierre del mes)."""
    ultimos: dict = {}                     # (año, mes) -> último registro del mes
    for d in diario:
        ultimos[(int(d["dia"][:4]), int(d["dia"][5:7]))] = d
    valores = []
    for mes in range(1, 13):
        d = ultimos.get((anio, mes))
        if d is None:
            valores.append(0.0)
            continue
        if vista == "Rentabilidades":
            # Rentabilidad del mes: de la rentabilidad acumulada al cierre del mes anterior a la de este mes.
            anterior = next((_n(ultimos[k]["rent_acumulada"]) for k in sorted(ultimos, reverse=True) if k < (anio, mes)), 0.0)
            valores.append(round(((1 + _n(d["rent_acumulada"]) / 100) / (1 + anterior / 100) - 1) * 100, 2))
        else:
            valores.append(_n(d["inversores" if vista == "Inversores" else "invertido"]))
    # El eje ordena los nombres alfabéticamente: el número delante mantiene el orden del calendario.
    return pd.DataFrame({vista: valores}, index=[f"{i:02d} {mes}" for i, mes in enumerate(_MESES, 1)])


# TITULO TABLA DE OPERACIONES

def _tabla(ops: list, cerradas: bool) -> pd.DataFrame:
    """Tabla de operaciones para mostrar: símbolo, tipo, tipo de activo, volumen, precio de apertura, hora de apertura y ganancia (solo las cerradas)."""
    filas = []
    for o in ops:
        try:
            hora = datetime.fromisoformat(str(o["abierta_en"]).replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y, %H:%M")
        except (KeyError, ValueError):
            hora = ""
        filas.append({"Símbolo": o.get("simbolo", ""), "Tipo": "COMPRA" if o.get("lado") == "compra" else "VENTA", "Tipo de activo": o.get("tipo_activo") or "—",
                      "Volumen": f"{_n(o.get('volumen')):.3f}", "Precio de apertura": f"{_n(o.get('precio_apertura')):,.2f}", "Hora de apertura": hora,
                      "Ganancia": (f"{'-' if _n(o.get('resultado')) < 0 else ''}${abs(_n(o.get('resultado'))):,.2f}" if cerradas and o.get("resultado") is not None else "—")})
    return pd.DataFrame(filas, columns=["Símbolo", "Tipo", "Tipo de activo", "Volumen", "Precio de apertura", "Hora de apertura", "Ganancia"])


# TITULO FICHA REAL

def ficha_real(e: dict) -> None:
    """Dibuja la ficha de una estrategia real. Recibe `e`, el diccionario armado por `metricas_estrategia.listar_publicadas`. No devuelve nada."""
    if st.button("← Atrás", key="copytrading_atras"):
        st.session_state.copytrading_estrategia = None
        st.rerun()
    datos = metricas_estrategia.detalle(gestor_autenticacion._supabase, e["id"])
    m, diario = datos["metricas"], datos["diario"]

    c_av, c_rentabilidad = st.columns([3, 1], vertical_alignment="center")
    with c_av:
        st.html(f"<div class='ficha-av'>{avatar(e['nombre'])}</div><div class='ficha-nombre'>{escape(str(e['nombre']))}</div>"
                f"<div class='ficha-gestion'>@{escape(str(e['gestor']))}</div>")
    with c_rentabilidad:
        st.html(f"<div class='ficha-seccion' style='text-align:right;'>Rentabilidad 1 mes</div><div class='ficha-rentabilidad'>{e['rent']:.2f}%</div>")
    st.html(
        f"<div style='margin-top:8px;'><span class='ficha-chip'>👥 {escape(str(e['tipo']))}</span><span class='ficha-chip'>Ⓢ {escape(str(e['cat']))}</span></div>"
        f"<div class='ficha-seccion'>Biografía del gestor</div><div class='ficha-texto'>{escape(e['bio'] or 'El gestor de estrategia no ha añadido una biografía.')}</div>"
        f"<div class='ficha-seccion'>Descripción</div><div class='ficha-texto'>{escape(e['desc'] or 'Sin descripción.')}</div>"
        f"<div class='ficha-seccion'>Información importante</div><div style='margin-top:4px;'>"
        f"<span class='ficha-chip'>Apalancamiento: {e['apalancamiento'] or '—'}</span><span class='ficha-chip'>Comisiones: {e['comision']:g}%</span>"
        f"<span class='ficha-chip'>Inversores: {e['inversores']}</span><span class='ficha-chip'>Inversión mínima: ${e['inv_min']:,}</span>"
        f"<span class='ficha-chip'>Invertido: ${e['invertido']:,}</span></div>")
    if st.button("＋ Cuenta de inversor  ·  Copiar estrategia", key="copytrading_copiar", type="primary", width="stretch"):
        dialogo_copiar(e)

    pestana_rend, pestana_riesgo, pestana_cart = st.tabs(["Rendimiento", "Riesgo", "Cartera"])
    with pestana_rend:
        c_grafico, c_don = st.columns([2, 1], vertical_alignment="center")
        with c_grafico:
            periodo = st.selectbox("Periodo", list(_PERIODOS), index=1, key="copytrading_periodo", label_visibility="collapsed")
            curva = _curva(diario, _PERIODOS[periodo])
            st.html(f"<div class='ficha-seccion'>{escape(periodo)}</div><div class='ficha-rentabilidad'>{(curva.iloc[-1, 0] if len(curva) else 0.0):.2f}%</div>")
            if len(curva) >= 2:
                st.area_chart(curva, height=230, color="#3fb950")
            else:
                st.info("Todavía no hay suficientes datos para dibujar la curva.")
        with c_don:
            total = int(m.get("operaciones_total") or 0)
            ganadoras, perdedoras = int(m.get("operaciones_ganadoras") or 0), int(m.get("operaciones_perdedoras") or 0)
            st.html(f"<div style='text-align:center;'>{rosquilla(round(ganadoras * 100 / total) if total else 0)}</div>")
            st.html(f"<div class='don-centro'><div class='n'>{total:,}</div><div class='l'>Operaciones totales</div></div>")
            pct = lambda x: round(x * 100 / total) if total else 0           # noqa: E731
            st.html(f"<div class='ficha-texto'><b style='color:#3fb950'>{ganadoras}/{pct(ganadoras)}%</b> ganadoras · mejor <b>{_n(m.get('mejor_operacion')):,.2f}</b><br>"
                    f"<b style='color:#f85149'>{perdedoras}/{pct(perdedoras)}%</b> perdedoras · peor <b>{_n(m.get('peor_operacion')):,.2f}</b></div>")
        anios = sorted({int(d["dia"][:4]) for d in diario}, reverse=True) or [datetime.now().year]
        v1, v2 = st.columns([3, 1])
        vista = v1.segmented_control("Vista", ["Rentabilidades", "Inversores", "Invertido"], default="Rentabilidades", key="copytrading_vista",
                                     label_visibility="collapsed") or "Rentabilidades"
        anio = v2.selectbox("Año", anios, key="copytrading_anio", label_visibility="collapsed")
        st.bar_chart(_mensual(diario, anio, vista), height=220, color="#3fb950")
        st.caption("Invertir conlleva riesgos. El rendimiento pasado no garantiza resultados futuros.")
    with pestana_riesgo:
        r1, r2, r3 = st.columns(3)
        r1.metric("Drawdown máx.", f"{_n(m.get('drawdown_max')):.2f}%")
        r2.metric("Apalancamiento", f"{e['apalancamiento']}:1" if e["apalancamiento"] else "—")
        r3.metric("Nivel de riesgo", {"bajo": "Bajo", "medio": "Medio", "alto": "Alto"}.get(e["riesgo"], "—"))
        r4, r5, r6 = st.columns(3)
        r4.metric("Factor de beneficio", f"{_n(m.get('factor_beneficio')):.2f}" if m.get("factor_beneficio") is not None else "—")
        r5.metric("Mejor operación", f"{_n(m.get('mejor_operacion')):,.2f}" if m.get("mejor_operacion") is not None else "—")
        r6.metric("Peor operación", f"{_n(m.get('peor_operacion')):,.2f}" if m.get("peor_operacion") is not None else "—")
    with pestana_cart:
        estado = st.segmented_control("Estado", ["Abiertas", "Cerradas"], default="Abiertas", key="copytrading_estado", label_visibility="collapsed") or "Abiertas"
        reparto = m.get("asignacion_abiertas" if estado == "Abiertas" else "asignacion_cerradas") or {}
        if reparto:
            st.caption("Reparto por tipo de activo (% de operaciones)")
            st.html("".join(f"<div class='fic-rep'><span class='k'>{escape(str(k))}</span><span class='b'><i style='width:{min(100.0, float(v)):.1f}%'></i></span>"
                            f"<span class='v'>{float(v):g}%</span></div>" for k, v in reparto.items()))
        ops = datos["abiertas" if estado == "Abiertas" else "cerradas"]
        if ops:
            st.dataframe(_tabla(ops, estado == "Cerradas"), hide_index=True, width="stretch")
        else:
            st.info("Sin operaciones para mostrar.")



# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara ficha_real .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
