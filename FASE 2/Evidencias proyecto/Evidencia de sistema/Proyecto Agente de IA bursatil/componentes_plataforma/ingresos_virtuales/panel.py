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

"""Vista "Laboratorio": prueba, con la cuenta DEMO y sin cobrar nada, cuánto ganaría la plataforma con distintos modelos de cobro y si el
agente de IA tiene un historial que justifique cobrarle un porcentaje al usuario.

Es una sección INTERNA: solo la ven los administradores (root, herramientas/roles.py), porque muestra datos de toda la plataforma (costos, demanda y consumo de IA de
todos los usuarios).

Tiene cinco pestañas:
  - Ingresos hipotéticos: aplica a las operaciones cerradas (todas, solo las del agente o solo las manuales) cinco modelos de cobro
    (suscripción, recargo por operación, referido del broker, comisión de performance y comisión sobre patrimonio) y muestra el total,
    el aporte de cada uno y la serie por mes. Es un cálculo sobre el historial: no se cobra ni se descuenta dinero.
  - Agente como gestor: compara el historial del agente con el manual (aciertos, resultado, caída máxima), muestra cuántas de sus
    propuestas acepta el usuario y una lista de verificación para decidir si ya hay evidencia suficiente.
  - Demanda: interés en los planes (la vista Planes): personas que los vieron, interesadas en contratar un plan de pago por plan y por precio, origen
    de los interesados y encuesta. Son cifras de intención, no de ventas.
  - Costo y planes: cuánto cuesta la IA del agente en TODA la plataforma (tokens y dólares, por origen y modelo), el costo por pregunta del chat, qué margen deja
    cada plan (sus preguntas por semana salen de `configuracion.PLANES_IA`) y el resultado neto mensual de esta cuenta (ingresos hipotéticos menos costo de IA).
  - Parámetros: valores de cada modelo y los precios de la IA, que se guardan por usuario y cuenta.

La lógica de cálculo está en `herramientas/ingresos_virtuales.py` y la lectura de datos en `datos.py`.
"""
import time
from html import escape
from pathlib import Path

import streamlit as st

from componentes_plataforma import _estaticos
from componentes_plataforma.ingresos_virtuales import datos
from componentes_plataforma.ingresos_virtuales.graficos import barras_apiladas_svg
from componentes_plataforma.resumen.curva import curva_svg
import configuracion
from herramientas import consumo_ia, cuota_ia, demanda, roles
from herramientas import ingresos_virtuales as calculo
from herramientas.estadisticas_diario import estadisticas

# Hoja de estilos de la vista (estilos.css, junto a este archivo)
_CSS = Path(__file__).parent / "estilos.css"
# Periodos que se pueden elegir (días hacia atrás)
_PERIODOS = {"30 días": 30, "90 días": 90, "6 meses": 180, "1 año": 365}
# Qué operaciones se incluyen en el cálculo de ingresos
_BASES = ["Todas", "Solo del agente", "Solo manuales"]
# Estados de una propuesta del agente, con su nombre legible y en el orden en que se muestran
_ESTADOS = {"EJECUTADA": "Aceptadas y ejecutadas", "RECHAZADA_USUARIO": "Rechazadas por el usuario", "EXPIRADA": "Sin respuesta (vencieron)",
            "RECHAZADA_RIESGO": "Bloqueadas por el control de riesgo", "ERROR": "Con error al enviar", "PENDIENTE": "Pendientes"}


# TITULO DINERO

def _dinero(valor: float, signo: bool = False) -> str:
    """Formatea un monto en dólares con separador de miles y dos decimales; con `signo` antepone + a los positivos."""
    return f"{valor:+,.2f}" if signo else f"{valor:,.2f}"


# TITULO TARJETA

def _tarjeta(titulo: str, valor: str, pie: str = "", clase: str = "") -> str:
    """HTML de una tarjeta de cifra: título pequeño, valor grande y una línea de apoyo. `clase` pinta el valor (sube/baja)."""
    pie_html = f"<div class='lab-pie'>{escape(pie)}</div>" if pie else ""
    return (f"<div class='lab-tarjeta'><div class='lab-k'>{escape(titulo)}</div>"
            f"<div class='lab-v {clase}'>{escape(valor)}</div>{pie_html}</div>")


# TITULO TABLA HTML

def _tabla_html(encabezados: list, filas: list) -> str:
    """HTML de una tabla con el estilo del laboratorio. Las filas son listas de textos ya escapados o de HTML propio."""
    cab = "".join(f"<th>{escape(h)}</th>" for h in encabezados)
    cuerpo = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in fila) + "</tr>" for fila in filas)
    return f"<table class='lab-tabla'><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table>"


# TITULO SELECCIONAR BASE

def _seleccionar_base(base: str, grupos: dict) -> list:
    """Devuelve las operaciones que corresponden a la opción elegida: todas, solo las del agente (propuestas y automáticas) o solo manuales."""
    agente = grupos["agente"] + grupos["automatica"]
    if base == "Solo del agente":
        return agente
    if base == "Solo manuales":
        return grupos["manual"]
    return agente + grupos["manual"]


# TITULO PESTANA INGRESOS

def _pestana_ingresos(grupos: dict, p: dict, capital: float) -> None:
    """Pestaña "Ingresos hipotéticos": tarjetas con el total, tabla por modelo y gráfico mensual."""
    base = st.segmented_control("Operaciones incluidas", _BASES, default="Todas", key="lab_base") or "Todas"
    ops = _seleccionar_base(base, grupos)
    if not ops:
        st.info("No hay operaciones cerradas en este grupo y periodo. Opera en la cuenta demo (o deja que el agente lo haga) y vuelve a "
                "calcular.")
        return
    r = calculo.calcular_ingresos(ops, p, capital)
    modelos, activos, total = r["modelos"], r["activos"], r["total_activos"]
    mejor = max(activos, key=lambda k: modelos[k]["total"], default="")
    st.html("<div class='lab-cuadricula'>"
            + _tarjeta("Ingreso hipotético total", f"{_dinero(total)} USD", f"{len(activos)} modelos activos · {len(r['meses'])} meses", "lab-sube")
            + _tarjeta("Operaciones", str(r["n_ops"]), f"base: {base.lower()}")
            + _tarjeta("Ingreso por operación", f"{_dinero(total / r['n_ops'])} USD", "total entre operaciones")
            + _tarjeta("Modelo que más aporta", calculo.MODELOS.get(mejor, "—"), f"{_dinero(modelos[mejor]['total'])} USD" if mejor else "")
            + "</div>")
    filas = []
    for clave, nombre in calculo.MODELOS.items():
        m = modelos[clave]
        activo = clave in activos
        parte = f"{m['total'] / total * 100:.0f} %" if activo and total > 0 else "—"
        filas.append([escape(nombre), f"{_dinero(m['total'])}", parte, escape(m["nota"]), "Sí" if activo else "No"])
    st.html(_tabla_html(["Modelo", "Total (USD)", "Del total", "Supuesto usado", "Activo"], filas))
    if activos and r["meses"]:
        # El gráfico es un SVG: `st.html` lo elimina al limpiar el HTML, así que se dibuja con markdown (igual que la curva del Resumen)
        st.markdown("<div class='lab-subtitulo'>Ingreso hipotético por mes (USD)</div>"
                    + barras_apiladas_svg(r["meses"], {k: [modelos[k]["mensual"].get(m, 0.0) for m in r["meses"]] for k in activos}, calculo.MODELOS),
                    unsafe_allow_html=True)
    st.caption("Es un cálculo sobre el historial de la cuenta: no se cobra ni se descuenta dinero. El referido y el recargo usan los supuestos "
               "de la pestaña Parámetros; ajústalos a lo que ofrezca de verdad el broker.")


# TITULO FILA ESTADISTICAS

def _fila_estadisticas(nombre: str, ops: list, capital: float) -> list:
    """Fila de la tabla agente/manual: cantidad, aciertos, resultado, profit factor, esperanza, caída máxima y retorno sobre el capital."""
    s = estadisticas(ops)
    if not ops:
        return [escape(nombre)] + ["—"] * 7
    pf = "∞" if s["profit_factor"] == float("inf") else f"{s['profit_factor']:.2f}"
    clase = "lab-sube" if s["pnl"] > 0 else "lab-baja" if s["pnl"] < 0 else ""
    return [escape(nombre), str(s["n"]), f"{s['win_rate']:.0f} %", f"<span class='{clase}'>{_dinero(s['pnl'], True)}</span>", pf,
            _dinero(s["expectancy"], True), _dinero(s["max_dd"]), f"{s['pnl'] / capital * 100:+.2f} %" if capital > 0 else "—"]


# TITULO CURVA GRUPO

def _curva_grupo(titulo: str, ops: list) -> None:
    """Dibuja la curva de resultado acumulado de un grupo de operaciones (o un aviso si aún no hay suficientes)."""
    curva = calculo.curva_acumulada(ops)
    if len(curva) >= 1:
        curva = [(curva[0][0] - 1, 0.0)] + curva      # parte desde cero para que se vea el resultado acumulado
    # La curva es un SVG: se dibuja con markdown porque `st.html` elimina los SVG
    st.markdown(f"<div class='lab-subtitulo'>{escape(titulo)}</div>" + curva_svg(curva, "USD"), unsafe_allow_html=True)


# TITULO PESTANA AGENTE

def _pestana_agente(grupos: dict, p: dict, capital: float) -> None:
    """Pestaña "Agente como gestor": comparación con lo manual, propuestas aceptadas, lista de verificación y comisión de performance."""
    agente = grupos["agente"] + grupos["automatica"]
    st.html(_tabla_html(["Grupo", "Operaciones", "Acierto", "Resultado (USD)", "Profit factor", "Esperanza (USD)", "Caída máx. (USD)", "Retorno / capital"],
                        [_fila_estadisticas("Agente de IA", agente, capital), _fila_estadisticas("Manual", grupos["manual"], capital)]))
    if grupos["automatica"]:
        st.caption(f"Del agente: {len(grupos['agente'])} propuestas confirmadas por el usuario y {len(grupos['automatica'])} automáticas por vigilancia.")
    izquierda, derecha = st.columns(2)
    with izquierda:
        _curva_grupo("Resultado acumulado · agente", agente)
    with derecha:
        _curva_grupo("Resultado acumulado · manual", grupos["manual"])

    propuestas = datos.resumen_propuestas()
    if propuestas:
        filas = [[escape(nombre), str(propuestas[k])] for k, nombre in _ESTADOS.items() if k in propuestas]
        decididas = propuestas.get("EJECUTADA", 0) + propuestas.get("RECHAZADA_USUARIO", 0) + propuestas.get("EXPIRADA", 0)
        tasa = f"{propuestas.get('EJECUTADA', 0) / decididas * 100:.0f} %" if decididas else "—"
        st.html("<div class='lab-subtitulo'>Propuestas del agente</div>"
                + _tabla_html(["Resultado de la propuesta", "Cantidad"], filas)
                + f"<div class='lab-pie'>Tasa de aceptación (ejecutadas sobre decididas): <b>{tasa}</b></div>")
    else:
        st.caption("Aún no hay propuestas del agente registradas.")

    verificacion = calculo.semaforo(estadisticas(agente), capital, p["umbrales"])
    cumplidos = sum(1 for _c, _v, ok in verificacion if ok)
    lista = "".join(f"<li class='{'lab-ok' if ok else 'lab-no'}'><span>{'✓' if ok else '✗'}</span> {escape(c)} <b>{escape(v)}</b></li>"
                    for c, v, ok in verificacion)
    veredicto = ("Hay evidencia suficiente para probar una comisión de performance con dinero real." if cumplidos == len(verificacion)
                 else "Todavía falta historial: sigue operando en demo hasta cumplir todos los criterios.")
    st.html(f"<div class='lab-subtitulo'>¿Hay evidencia para cobrar por rendimiento?</div><ul class='lab-lista'>{lista}</ul>"
            f"<div class='lab-pie'>{cumplidos} de {len(verificacion)} criterios cumplidos. {veredicto} Los umbrales se cambian en Parámetros.</div>")
    if agente:
        fee = calculo.performance(agente, p)
        st.html(_tarjeta("Si cobraras solo por lo que gana el agente", f"{_dinero(fee['total'])} USD", fee["nota"]))


# TITULO TOKENS

def _tokens(n: int) -> str:
    """Formatea una cantidad de tokens de forma corta: 1.234 · 12,3 mil · 1,2 M."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} M".replace(".", ",")
    if n >= 10_000:
        return f"{n / 1_000:.1f} mil".replace(".", ",")
    return f"{n:,}".replace(",", ".")


# TITULO PESTANA COSTOS

def _pestana_costos(p: dict, ops: list, capital: float, dias: int) -> None:
    """Pestaña «Costo y planes»: consumo y costo de la IA de TODA la plataforma, costo por pregunta, margen de cada plan y resultado neto mensual de esta cuenta."""
    desde = time.time() - dias * 86400
    registros = consumo_ia.leer_todos(desde)
    # Para proyectar al mes se promedia sobre los días que el registro realmente cubre (no sobre todo el periodo elegido): con 5 días de
    # consumo en un periodo de un año, promediar por 365 subestimaría el gasto.
    cubiertos = max(1, min(dias, int((time.time() - min(float(x.get("t", 0) or 0) for x in registros)) // 86400) + 1)) if registros else dias
    r = consumo_ia.resumir(registros, p["precios_ia"], cubiertos)
    total = r["total"]
    usuarios = len({x.get("usuario") for x in registros})
    chat = r["por_origen"].get("chat")
    costo_pregunta_real = (chat["costo"] / chat["turnos"]) if chat and chat["turnos"] else None
    if not registros:
        st.info("Todavía no hay consumo de IA registrado: se anota cada vez que el agente responde en el chat o analiza una vigilancia, en cualquier cuenta. "
                "Mientras tanto puedes simular los planes con un costo supuesto por pregunta (abajo).")
    else:
        st.html("<div class='lab-cuadricula'>"
                + _tarjeta("Costo de IA del periodo", f"{_dinero(total['costo'])} USD", f"{total['llamadas']} llamadas al modelo · {usuarios} usuario{'s' if usuarios != 1 else ''} con consumo")
                + _tarjeta("Preguntas del chat", str(chat["turnos"]) if chat else "0", f"{_tokens(total['entrada'])} tokens de entrada · {_tokens(total['salida'])} de salida")
                + _tarjeta("Costo por pregunta", f"{costo_pregunta_real:.4f} USD" if costo_pregunta_real is not None else "—", "un mensaje del usuario y todo lo que hace el agente para responderlo")
                + _tarjeta("Proyección mensual de la plataforma", f"{_dinero(r['mensual_proyectado'])} USD", f"promedio de {cubiertos} días con registro × 30")
                + "</div>")
        if r["sin_precio"]:
            st.warning("Estos modelos no tienen precio en la tabla de Parámetros, así que su costo aparece en cero: " + ", ".join(r["sin_precio"]))
        etiquetas = {"chat": "Chat con el agente", "vigilancia": "Vigilancias automáticas"}
        filas = [[escape(etiquetas.get(k, k)), str(v["llamadas"]), str(v["turnos"]), _tokens(v["entrada"] + v["salida"]), _dinero(v["costo"])]
                 for k, v in r["por_origen"].items()]
        filas += [[f"<i>{escape(k)}</i>", str(v["llamadas"]), str(v["turnos"]), _tokens(v["entrada"] + v["salida"]), _dinero(v["costo"])]
                  for k, v in r["por_modelo"].items()]
        st.html("<div class='lab-subtitulo'>Dónde se gasta (por origen y, en cursiva, por modelo)</div>"
                + _tabla_html(["Origen / modelo", "Llamadas", "Turnos", "Tokens", "Costo (USD)"], filas))
        dias_con_datos = list(r["por_dia_origen"])[-30:]
        if dias_con_datos:
            origenes = sorted({o for d in dias_con_datos for o in r["por_dia_origen"][d]})
            st.markdown("<div class='lab-subtitulo'>Costo de IA por día, últimos 30 días con consumo (USD)</div>"
                        + barras_apiladas_svg(dias_con_datos, {o: [r["por_dia_origen"][d].get(o, 0.0) for d in dias_con_datos] for o in origenes},
                                              etiquetas, [d[5:] for d in dias_con_datos]), unsafe_allow_html=True)

    st.html("<div class='lab-subtitulo'>¿Cuánto deja cada plan?</div>")
    supuesto = round(costo_pregunta_real, 4) if costo_pregunta_real is not None else 0.02
    pregunta = st.number_input("Costo de IA por pregunta a usar en el cálculo (USD)", 0.0, 100.0, supuesto, 0.005, format="%.4f", key=f"lab_costo_pregunta_{supuesto}",
                               help="Se llena con el costo real por pregunta del chat si ya hay consumo; si no, con un valor supuesto que puedes cambiar.")
    semanas_por_mes = 52 / 12
    # Uso actual de IA por usuario al mes (chat y vigilancias): lo observado en toda la plataforma dividido entre los usuarios con consumo.
    uso_actual = r["mensual_proyectado"] / usuarios if registros and usuarios else 0.0
    filas = []
    for plan in configuracion.PLANES_IA.values():
        precio = float((plan.get("precios") or [0])[0])
        maximo = plan["preguntas_semana"] * semanas_por_mes * pregunta
        peor = precio - maximo - p["costo_fijo_usuario"]
        con_uso = precio - uso_actual - p["costo_fijo_usuario"]
        if precio <= 0:
            lectura = f"Plan gratuito: cuesta hasta {_dinero(maximo + p['costo_fijo_usuario'])} USD al mes por usuario"
        elif peor >= 0:
            lectura = "Rentable aunque use todas sus preguntas"
        elif con_uso >= 0:
            lectura = "Rentable con el uso actual; pierde si usa todas sus preguntas"
        else:
            lectura = "Pierde con este uso"
        filas.append([escape(plan["nombre"]), _dinero(precio), str(plan["preguntas_semana"]), _dinero(maximo),
                      f"<span class='{'lab-sube' if peor > 0 else 'lab-baja'}'>{_dinero(peor, True)}</span>",
                      f"<span class='{'lab-sube' if con_uso > 0 else 'lab-baja'}'>{_dinero(con_uso, True)}</span>",
                      f"{peor / precio * 100:.0f} %" if precio > 0 else "—", lectura])
    st.html(_tabla_html(["Plan", "Precio/mes", "Preguntas por semana", "Costo máximo de IA", "Margen si usa todas sus preguntas", "Margen con el uso actual", "Margen % (peor caso)", "Lectura"], filas)
            + f"<div class='lab-pie'>Margen = precio − costo de IA − {_dinero(p['costo_fijo_usuario'])} USD de costo fijo por usuario (infraestructura y soporte). "
              f"«Costo máximo» = preguntas por semana × {semanas_por_mes:.2f} semanas por mes × costo por pregunta. «Uso actual» = {_dinero(uso_actual)} USD al mes por usuario, "
              "promedio de lo observado en toda la plataforma (incluye las vigilancias automáticas, que gastan IA fuera de las preguntas del plan).</div>")

    # El resultado neto compara ingresos hipotéticos de ESTA cuenta con el costo de IA de esta misma cuenta (así los dos lados son comparables).
    r_cuenta = consumo_ia.resumir(consumo_ia.leer(desde), p["precios_ia"], cubiertos)
    neto = calculo.serie_neta(_ingresos_por_mes(ops, p, capital), r_cuenta["por_dia"])
    if neto:
        filas = [[mes, _dinero(v["ingresos"]), _dinero(v["costo_ia"]),
                  f"<span class='{'lab-sube' if v['neto'] > 0 else 'lab-baja'}'>{_dinero(v['neto'], True)}</span>"] for mes, v in neto.items()]
        suma = sum(v["neto"] for v in neto.values())
        st.html("<div class='lab-subtitulo'>Resultado neto mensual de esta cuenta: ingresos hipotéticos menos costo de IA</div>"
                + _tabla_html(["Mes", "Ingresos hipotéticos (USD)", "Costo de IA (USD)", "Neto (USD)"], filas)
                + f"<div class='lab-pie'>Neto del periodo: <b>{_dinero(suma, True)} USD</b>. Los ingresos son los de la pestaña Ingresos hipotéticos (modelos activos, "
                  "todas las operaciones de esta cuenta) y el costo de IA es el de esta misma cuenta.</div>")
    st.caption("Los precios de la IA de la tabla son referenciales (tomados de fuentes de terceros): confírmalos en la página de precios de DeepSeek y "
               "edítalos en Parámetros. Las llamadas anteriores a esta versión no tienen registro de consumo.")


# TITULO INGRESOS POR MES

def _ingresos_por_mes(ops: list, p: dict, capital: float) -> dict:
    """Suma por mes los ingresos hipotéticos de los modelos activos para las operaciones dadas ({"AAAA-MM": monto})."""
    if not ops:
        return {}
    r = calculo.calcular_ingresos(ops, p, capital)
    salida: dict = {}
    for clave in r["activos"]:
        for mes, monto in r["modelos"][clave]["mensual"].items():
            salida[mes] = salida.get(mes, 0.0) + monto
    return salida


# TITULO PESTANA DEMANDA

def _pestana_demanda(p: dict, dias: int) -> None:
    """Pestaña "Demanda": resultados de la prueba de interés en los planes (visitantes, clics por plan y precio, origen y encuesta)."""
    eventos = demanda.leer(time.time() - dias * 86400)
    r = demanda.resumir(eventos, configuracion.PLANES_IA, p["conversion_interes_a_pago"])
    if not eventos:
        st.info("Todavía no hay datos: la vista «Planes» del menú lateral registra quién la mira y qué plan elige. Cuando haya movimiento "
                "aparecerá aquí.")
        return
    tasa = r["interesados"] / r["visitantes"] * 100.0 if r["visitantes"] else 0.0
    st.html("<div class='lab-cuadricula'>"
            + _tarjeta("Personas que vieron los planes", str(r["visitantes"]), f"últimos {dias} días")
            + _tarjeta("Interesadas en un plan de pago", str(r["interesados"]), f"{tasa:.0f} % de quienes lo vieron", "lab-sube")
            + _tarjeta("Pidieron que les avisen", str(r["lista_espera"]), "lista de espera (con su permiso)")
            + _tarjeta("Ingreso mensual potencial", f"{_dinero(r['ingreso_potencial'])} USD", f"supone que {p['conversion_interes_a_pago'] * 100:.0f} % de los interesados pagaría")
            + "</div>")
    filas = []
    for clave, v in r["por_plan"].items():
        ingreso = v["clics"] * v["precio_medio"] * p["conversion_interes_a_pago"]
        filas.append([escape(configuracion.PLANES_IA[clave]["nombre"]), _dinero(v["precio_medio"]), str(v["clics"]), f"{v['tasa']:.0f} %", str(v["espera"]), _dinero(ingreso)])
    st.html("<div class='lab-subtitulo'>Interés por plan</div>"
            + _tabla_html(["Plan", "Precio medio mostrado (USD)", "Interesadas", "Tasa sobre quienes vieron", "En lista de espera", "Ingreso potencial (USD/mes)"], filas))
    filas = []
    for (clave, v), d in r["por_variante"].items():
        if len(configuracion.PLANES_IA[clave].get("precios", [])) < 2:
            continue
        # El precio más bajo casi siempre tiene más clics: lo que importa es cuánto deja cada persona que mira (tasa × precio), no solo la tasa.
        conversion = p["conversion_interes_a_pago"]
        con_datos = [x for (c, _), x in r["por_variante"].items() if c == clave and x["visitantes"] >= 20]
        mejor_tasa = max((x["tasa"] for x in con_datos), default=None)
        mejor_ingreso = max((x["tasa"] / 100 * x["precio"] for x in con_datos), default=None)
        ingreso_pp = d["tasa"] / 100 * d["precio"] * conversion
        if d["visitantes"] < 20:
            lectura = "pocos datos (menos de 20 personas)"
        elif mejor_ingreso is not None and d["tasa"] / 100 * d["precio"] >= mejor_ingreso:
            lectura = "mayor ingreso por persona"
        elif mejor_tasa is not None and d["tasa"] >= mejor_tasa:
            lectura = "mayor tasa de clic"
        else:
            lectura = ""
        filas.append([escape(configuracion.PLANES_IA[clave]["nombre"]), f"Variante {v + 1}", _dinero(d["precio"]), str(d["visitantes"]), str(d["clics"]),
                      f"{d['tasa']:.0f} %", f"{ingreso_pp:.2f}", lectura])
    if filas:
        st.html("<div class='lab-subtitulo'>Comparación de precios (prueba A/B)</div>"
                + _tabla_html(["Plan", "Variante", "Precio (USD)", "Personas que lo vieron", "Interesadas", "Tasa", "Ingreso potencial por persona (USD)", "Lectura"], filas)
                + "<div class='lab-pie'>Cada persona ve siempre el mismo precio. Con pocas personas por variante, las diferencias pueden ser azar: conviene esperar a "
                  "tener al menos 100 por variante antes de decidir un precio.</div>")
    nombres_origen = {"menu": "Menú lateral", "barra_cuota": "Barra de uso (uso alto)", "cuota_agotada": "Cuota agotada"}
    if r["por_origen"]:
        st.html("<div class='lab-subtitulo'>Desde dónde llegaron los interesados</div>"
                + _tabla_html(["Origen", "Interesadas"], [[escape(nombres_origen.get(k, k)), str(v)] for k, v in r["por_origen"].items()]))
    if r["precio_justo"] or r["motivo"]:
        izquierda, derecha = st.columns(2)
        with izquierda:
            st.html("<div class='lab-subtitulo'>Precio que les parece justo</div>"
                    + _tabla_html(["Rango", "Personas"], [[escape(k), str(r["precio_justo"].get(k, 0))] for k in demanda.RANGOS_PRECIO]))
        with derecha:
            st.html("<div class='lab-subtitulo'>Lo que más les interesa</div>"
                    + _tabla_html(["Motivo", "Personas"], [[escape(k), str(r["motivo"].get(k, 0))] for k in demanda.MOTIVOS]))
    import csv
    import io
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["hora", "evento", "usuario", "plan", "precio", "variante", "origen", "precio_justo", "motivo"])
    for e in eventos:
        escritor.writerow([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e.get("t", 0))), e.get("evento"), e.get("usuario"), e.get("plan"), e.get("precio"),
                           e.get("variante"), e.get("origen"), e.get("precio_justo", ""), e.get("motivo", "")])
    st.download_button("Descargar los eventos (CSV, sin correos)", salida.getvalue(), file_name="demanda_planes.csv", mime="text/csv", key="lab_descargar_demanda")
    st.caption("Son cifras de intención, no de ventas: un clic no es un pago. Cuentan personas distintas, no clics repetidos. Los eventos están en data/demanda.jsonl.")


# TITULO PESTANA PARAMETROS

def _pestana_parametros(p: dict) -> None:
    """Pestaña "Parámetros": formulario para editar los valores de cada modelo, con guardado y restablecer."""
    st.html("<div class='lab-aviso'>Estos valores son <b>supuestos de simulación</b> para el Laboratorio: no cambian los precios ni los límites reales de los planes "
            "(esos se definen en configuracion.py).</div>")
    with st.form("lab_parametros"):
        activos = st.multiselect("Modelos que suman al total", list(calculo.MODELOS), default=p["activos"], format_func=calculo.MODELOS.get)
        c1, c2, c3 = st.columns(3)
        with c1:
            planes_pago = [k for k, v in configuracion.PLANES_IA.items() if float((v.get("precios") or [0])[0]) > 0]
            plan_suscripcion = st.selectbox("Plan que se simula como suscripción", planes_pago, index=planes_pago.index(p["plan_suscripcion"]) if p["plan_suscripcion"] in planes_pago else 0,
                                            format_func=lambda k: f"{configuracion.PLANES_IA[k]['nombre']} · {float(configuracion.PLANES_IA[k]['precios'][0]):.2f} USD al mes",
                                            help="El precio es el real del plan (configuracion.py); aquí solo eliges cuál plan simular.")
            fijo = st.number_input("Recargo fijo por operación (USD)", 0.0, 1000.0, p["recargo_fijo"], 0.1)
            por_lote = st.number_input("Recargo por lote (USD)", 0.0, 1000.0, p["recargo_por_lote"], 0.1)
        with c2:
            spread = st.number_input("Spread supuesto por lote (USD)", 0.0, 1000.0, p["spread_usd_por_lote"], 0.5)
            participacion = st.number_input("Participación del referido (%)", 0.0, 100.0, p["referido_participacion"] * 100, 1.0)
            tasa_perf = st.number_input("Comisión de performance (%)", 0.0, 100.0, p["performance_tasa"] * 100, 1.0)
        with c3:
            tasa_pat = st.number_input("Comisión sobre patrimonio (% anual)", 0.0, 50.0, p["patrimonio_tasa_anual"] * 100, 0.05)
            dias = st.selectbox("Periodo analizado", list(_PERIODOS.values()), index=list(_PERIODOS.values()).index(p["dias"]) if p["dias"] in _PERIODOS.values() else 3,
                                format_func=lambda d: next(n for n, v in _PERIODOS.items() if v == d))
        st.markdown("**Umbrales para cobrar por rendimiento**")
        u1, u2, u3, u4 = st.columns(4)
        u = p["umbrales"]
        with u1:
            n_min = st.number_input("Operaciones mínimas", 1, 10000, int(u["min_operaciones"]), 5)
        with u2:
            pf_min = st.number_input("Profit factor mínimo", 0.0, 100.0, float(u["min_profit_factor"]), 0.1)
        with u3:
            wr_min = st.number_input("Acierto mínimo (%)", 0.0, 100.0, float(u["min_win_rate"]), 5.0)
        with u4:
            dd_max = st.number_input("Caída máxima (% del capital)", 0.0, 100.0, float(u["max_caida_pct"]), 1.0)
        st.markdown("**Costo y precios de la IA**")
        costo_fijo = st.number_input("Costo fijo por usuario al mes (USD, infraestructura y soporte)", 0.0, 10000.0, p["costo_fijo_usuario"], 0.5)
        conversion = st.number_input("De los interesados en un plan, ¿qué % supones que terminaría pagando?", 0.0, 100.0, p["conversion_interes_a_pago"] * 100, 1.0,
                                     help="Se usa para el ingreso potencial de la pestaña Demanda. Es un supuesto: los clics no son pagos.")
        import pandas as pd
        precios_editados = st.data_editor(pd.DataFrame([{"modelo": m, **v} for m, v in p["precios_ia"].items()]), num_rows="dynamic", key="lab_precios_ia",
                                          width="stretch", column_config={"modelo": "Modelo (como aparece en la configuración)",
                                                                          "entrada_acierto": st.column_config.NumberColumn("Entrada en caché (USD/M)", min_value=0.0, format="%.4f"),
                                                                          "entrada_fallo": st.column_config.NumberColumn("Entrada sin caché (USD/M)", min_value=0.0, format="%.4f"),
                                                                          "salida": st.column_config.NumberColumn("Salida (USD/M)", min_value=0.0, format="%.4f")})
        plan_cuota = None
        if configuracion.PLANES_LIBRES:      # solo en desarrollo: cambiar de plan sin pagar
            st.markdown("**Cuota de preguntas del agente**")
            claves_planes = list(configuracion.PLANES_IA)
            plan_cuota = st.selectbox("Plan del usuario (para probar la cuota)", claves_planes, index=claves_planes.index(cuota_ia.plan_actual()),
                                      format_func=lambda k: f"{configuracion.PLANES_IA[k]['nombre']} · {cuota_ia.formato(configuracion.PLANES_IA[k]['preguntas_semana'])} preguntas por semana",
                                      help="Define cuántas preguntas puede hacerle este usuario al agente por semana. Los montos de cada plan están en configuracion.py (PLANES_IA).")
        guardar = st.form_submit_button("Guardar parámetros", type="primary")
    if guardar:
        if plan_cuota is not None:
            cuota_ia.fijar_plan(plan_cuota)
        datos.guardar_parametros({
            "activos": activos, "dias": dias, "plan_suscripcion": plan_suscripcion, "recargo_fijo": fijo, "recargo_por_lote": por_lote,
            "spread_usd_por_lote": spread, "referido_participacion": participacion / 100, "performance_tasa": tasa_perf / 100,
            "patrimonio_tasa_anual": tasa_pat / 100,
            "umbrales": {"min_operaciones": n_min, "min_profit_factor": pf_min, "min_win_rate": wr_min, "max_caida_pct": dd_max},
            "costo_fijo_usuario": costo_fijo, "conversion_interes_a_pago": conversion / 100,
            "precios_ia": {f["modelo"]: {k: f.get(k) for k in ("entrada_acierto", "entrada_fallo", "salida")}
                           for f in precios_editados.to_dict("records") if isinstance(f.get("modelo"), str)}})
        st.rerun()
    if st.button("Restablecer valores por defecto", key="lab_restablecer"):
        datos.guardar_parametros({})
        st.rerun()


# TITULO RENDERIZAR PANEL LABORATORIO

def renderizar_panel_laboratorio(main=None):
    """Dibuja la vista Laboratorio completa (cabecera, aviso de simulación, periodo y las cinco pestañas). Solo para administradores: a cualquier otro usuario le muestra un aviso.

    `main` no se usa (se conserva por compatibilidad con las demás vistas). No devuelve nada."""
    if not roles.es_root(st.session_state.get("usuario_informacion")):
        st.error("Esta sección es solo para administradores de la plataforma.")
        return
    st.html(_estaticos.estilos(_CSS))
    p = datos.leer_parametros()
    capital, es_demo = datos.capital_de_referencia()
    with st.container(key="laboratorio_contenedor"):
        st.html("<div class='lab-cabecera'><div class='lab-ic'><span class='lab-m'>science</span></div><div>"
                "<div class='lab-titulo'>Laboratorio de ingresos</div>"
                "<div class='lab-subtitulo-cab'>Simula cómo ganaría la plataforma y qué tan bien lo hace el agente, sin cobrar nada</div></div></div>")
        if es_demo:
            st.html("<div class='lab-aviso'>Simulación sobre tu cuenta <b>demo</b>: no se cobra ni se mueve dinero. Capital de referencia: "
                    f"<b>{_dinero(capital)} USD</b>.</div>")
        else:
            st.html("<div class='lab-aviso lab-aviso-real'>Estás en una cuenta <b>real</b>. Este módulo solo calcula sobre el historial: no cobra ni "
                    "opera. Para las pruebas conviene usar la cuenta demo.</div>")
        fila = st.columns([3, 1])
        with fila[0]:
            etiqueta = next((n for n, v in _PERIODOS.items() if v == p["dias"]), "1 año")
            elegido = st.segmented_control("Periodo", list(_PERIODOS), default=etiqueta, key="lab_periodo") or etiqueta
        with fila[1]:
            if st.button("Actualizar datos", key="lab_actualizar", width="stretch"):
                datos.cargar_operaciones(_PERIODOS[elegido], forzar=True)
        ops = datos.cargar_operaciones(_PERIODOS[elegido])
        grupos = datos.dividir_por_origen(ops, datos.tickets_del_agente())
        pestanas = st.tabs(["Ingresos hipotéticos", "Agente como gestor", "Costo y planes", "Demanda", "Parámetros"])
        with pestanas[0]:
            _pestana_ingresos(grupos, p, capital)
        with pestanas[1]:
            _pestana_agente(grupos, p, capital)
        with pestanas[2]:
            _pestana_costos(p, _seleccionar_base("Todas", grupos), capital, _PERIODOS[elegido])
        with pestanas[3]:
            _pestana_demanda(p, _PERIODOS[elegido])
        with pestanas[4]:
            _pestana_parametros(p)


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
