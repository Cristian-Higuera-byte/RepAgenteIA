# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara ingresos_virtuales .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""Cálculo de los INGRESOS HIPOTÉTICOS de la plataforma sobre una lista de operaciones cerradas (cuenta demo).

Es lógica pura: no usa Streamlit, ni red, ni disco; recibe las operaciones (las que entrega `estadisticas_diario.operaciones`)
y los parámetros de cada modelo de cobro, y devuelve cuánto habría ganado la plataforma con cada uno. No cobra nada a nadie
ni mueve dinero: sirve para comparar modelos antes de decidir cuál probar con dinero real.

Modelos que calcula (cada uno es independiente y se puede activar o no):
  - `suscripcion`  cuota fija por cada mes en que el usuario estuvo activo.
  - `recargo`      tarifa por operación: un monto fijo más un monto por lote (una sola vez por operación cerrada).
  - `referido`     participación en el spread que el broker cobra al cliente referido (programa de Introducing Broker).
  - `performance`  porcentaje de las ganancias nuevas por encima del máximo anterior (high-water mark), cobrado por trimestre.
  - `patrimonio`   porcentaje anual sobre el capital de referencia, repartido por días de cada mes.

También calcula el margen de cada plan de suscripción descontando el costo de IA (`margen_por_plan`) y el resultado neto mensual
(`serie_neta`).

Las operaciones son diccionarios con al menos `neto` (resultado en dinero), `volumen` (lotes) y `hora_out` (marca de tiempo del
cierre, en segundos). El resultado de cada modelo trae el `total` y la serie `mensual` ({"AAAA-MM": monto}).
"""
import calendar
from datetime import datetime

# Orden y nombre visible de los modelos
MODELOS = {
    "suscripcion": "Suscripción mensual",
    "recargo": "Recargo por operación",
    "referido": "Referido del broker (IB)",
    "performance": "Comisión de performance",
    "patrimonio": "Comisión sobre patrimonio",
}


# TITULO MES DE

def mes_de(marca_tiempo) -> str:
    """Devuelve el mes ("AAAA-MM", hora local) de una marca de tiempo en segundos."""
    return datetime.fromtimestamp(int(marca_tiempo or 0)).strftime("%Y-%m")


# TITULO MESES ENTRE

def meses_entre(primero: str, ultimo: str) -> list:
    """Lista los meses "AAAA-MM" desde `primero` hasta `ultimo`, ambos incluidos. Lista vacía si alguno falta."""
    if not primero or not ultimo or primero > ultimo:
        return []
    a, m = int(primero[:4]), int(primero[5:])
    salida = []
    while f"{a:04d}-{m:02d}" <= ultimo:
        salida.append(f"{a:04d}-{m:02d}")
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return salida


# TITULO SUMAR POR MES

def _sumar_por_mes(pares) -> dict:
    """Suma montos por mes: recibe pares (mes, monto) y devuelve {mes: total}, ordenado por mes."""
    salida: dict = {}
    for mes, monto in pares:
        salida[mes] = salida.get(mes, 0.0) + monto
    return dict(sorted(salida.items()))


# TITULO RESULTADO

def _resultado(mensual: dict, nota: str) -> dict:
    """Arma el resultado de un modelo: su serie mensual, el total y una nota con el supuesto usado."""
    return {"total": sum(mensual.values()), "mensual": mensual, "nota": nota}


# TITULO SUSCRIPCION

def suscripcion(ops: list, p: dict) -> dict:
    """Cuota mensual fija `suscripcion_mensual` por cada mes entre la primera y la última operación (ambos incluidos)."""
    meses = meses_entre(min((mes_de(o["hora_out"]) for o in ops), default=""), max((mes_de(o["hora_out"]) for o in ops), default=""))
    cuota = float(p["suscripcion_mensual"])
    return _resultado({m: cuota for m in meses}, f"{cuota:.2f} USD por mes activo ({len(meses)} meses)")


# TITULO RECARGO

def recargo(ops: list, p: dict) -> dict:
    """Tarifa por operación cerrada: `recargo_fijo` más `recargo_por_lote` por cada lote operado."""
    fijo, por_lote = float(p["recargo_fijo"]), float(p["recargo_por_lote"])
    pares = [(mes_de(o["hora_out"]), fijo + por_lote * float(o.get("volumen", 0.0) or 0.0)) for o in ops]
    return _resultado(_sumar_por_mes(pares), f"{fijo:.2f} USD por operación + {por_lote:.2f} USD por lote")


# TITULO REFERIDO

def referido(ops: list, p: dict) -> dict:
    """Participación en el spread: lotes × `spread_usd_por_lote` (costo de spread supuesto) × `referido_participacion` (0 a 1)."""
    spread, parte = float(p["spread_usd_por_lote"]), float(p["referido_participacion"])
    pares = [(mes_de(o["hora_out"]), float(o.get("volumen", 0.0) or 0.0) * spread * parte) for o in ops]
    return _resultado(_sumar_por_mes(pares), f"{parte * 100:.0f} % de un spread supuesto de {spread:.2f} USD por lote")


# TITULO TRIMESTRE DE

def _trimestre_de(marca_tiempo) -> tuple:
    """Devuelve (año, trimestre 1-4) de una marca de tiempo en segundos (hora local)."""
    f = datetime.fromtimestamp(int(marca_tiempo or 0))
    return f.year, (f.month - 1) // 3 + 1


# TITULO PERFORMANCE

def performance(ops: list, p: dict) -> dict:
    """Comisión de performance con high-water mark, cristalizada al cierre de cada trimestre.

    Se acumula el resultado neto de las operaciones por trimestre. Si el acumulado al cerrar el trimestre supera el máximo
    anterior (el high-water mark), se cobra `performance_tasa` sobre la diferencia y el máximo sube; si no, no se cobra nada y el
    máximo se mantiene (las pérdidas deben recuperarse antes de volver a cobrar). Se anota en el último mes del trimestre."""
    tasa = float(p["performance_tasa"])
    por_trimestre: dict = {}
    for o in sorted(ops, key=lambda x: x["hora_out"]):
        clave = _trimestre_de(o["hora_out"])
        por_trimestre[clave] = por_trimestre.get(clave, 0.0) + float(o.get("neto", 0.0) or 0.0)
    acumulado = maximo = 0.0
    pares = []
    for (anio, trimestre), resultado in sorted(por_trimestre.items()):
        acumulado += resultado
        if acumulado > maximo:
            pares.append((f"{anio:04d}-{trimestre * 3:02d}", tasa * (acumulado - maximo)))
            maximo = acumulado
    return _resultado(_sumar_por_mes(pares), f"{tasa * 100:.0f} % de las ganancias nuevas sobre el máximo anterior, por trimestre")


# TITULO PATRIMONIO

def patrimonio(ops: list, p: dict, capital: float) -> dict:
    """Porcentaje anual `patrimonio_tasa_anual` sobre el `capital` de referencia, repartido por los días de cada mes
    entre la primera y la última operación."""
    tasa = float(p["patrimonio_tasa_anual"])
    meses = meses_entre(min((mes_de(o["hora_out"]) for o in ops), default=""), max((mes_de(o["hora_out"]) for o in ops), default=""))
    mensual = {}
    for m in meses:
        dias = calendar.monthrange(int(m[:4]), int(m[5:]))[1]
        mensual[m] = capital * tasa * dias / 365.0
    return _resultado(mensual, f"{tasa * 100:.2f} % anual sobre {capital:,.0f} USD de capital")


# TITULO CALCULAR INGRESOS

def calcular_ingresos(ops: list, p: dict, capital: float) -> dict:
    """Calcula los ingresos hipotéticos de todos los modelos sobre `ops`.

    Recibe las operaciones cerradas, los parámetros `p` (ver `parametros.json` del componente) y el capital de referencia.
    Devuelve {"modelos": {clave: resultado}, "meses": [...], "total_activos": suma de los modelos con `p["activos"]`,
    "n_ops": cantidad de operaciones}. Con lista vacía todos los montos son cero."""
    modelos = {
        "suscripcion": suscripcion(ops, p),
        "recargo": recargo(ops, p),
        "referido": referido(ops, p),
        "performance": performance(ops, p),
        "patrimonio": patrimonio(ops, p, capital),
    }
    meses = sorted({m for r in modelos.values() for m in r["mensual"]})
    activos = [k for k in modelos if k in (p.get("activos") or [])]
    return {"modelos": modelos, "meses": meses, "n_ops": len(ops),
            "total_activos": sum(modelos[k]["total"] for k in activos), "activos": activos}


# TITULO CURVA ACUMULADA

def curva_acumulada(ops: list) -> list:
    """Curva de resultado acumulado de las operaciones en orden de cierre: lista de pares (marca de tiempo, acumulado)."""
    acumulado = 0.0
    salida = []
    for o in sorted(ops, key=lambda x: x["hora_out"]):
        acumulado += float(o.get("neto", 0.0) or 0.0)
        salida.append((int(o["hora_out"]), acumulado))
    return salida


# TITULO SEMAFORO

def semaforo(stats: dict, capital: float, umbrales: dict) -> list:
    """Revisa si el historial de un grupo de operaciones basta para cobrar por rendimiento.

    Recibe las estadísticas del grupo (`estadisticas_diario.estadisticas`), el capital de referencia y los `umbrales`
    (`min_operaciones`, `min_profit_factor`, `min_win_rate`, `max_caida_pct`). Devuelve una lista de
    (criterio, valor mostrado, cumple) para dibujarla como lista de verificación."""
    n = int(stats.get("n", 0))
    pf = float(stats.get("profit_factor", 0.0))
    caida_pct = (float(stats.get("max_dd", 0.0)) / capital * 100.0) if capital > 0 else 0.0
    return [
        (f"Al menos {umbrales['min_operaciones']} operaciones", f"{n}", n >= umbrales["min_operaciones"]),
        (f"Profit factor de {umbrales['min_profit_factor']} o más", "∞" if pf == float("inf") else f"{pf:.2f}", pf >= umbrales["min_profit_factor"]),
        (f"Acierto de {umbrales['min_win_rate']} % o más", f"{stats.get('win_rate', 0.0):.0f} %", stats.get("win_rate", 0.0) >= umbrales["min_win_rate"]),
        (f"Caída máxima menor a {umbrales['max_caida_pct']} % del capital", f"{caida_pct:.1f} %", caida_pct < umbrales["max_caida_pct"]),
        ("Resultado total positivo", f"{stats.get('pnl', 0.0):+,.2f}", stats.get("pnl", 0.0) > 0),
    ]


# TITULO MARGEN POR PLAN

def margen_por_plan(planes: list, mensual_ia: float, costo_fijo: float) -> list:
    """Calcula, para cada plan, cuánto le queda a la plataforma por usuario al mes con el consumo de IA observado.

    Recibe los `planes` (cada uno con `nombre`, `precio` mensual y `tope_ia`, el gasto de IA mensual en dólares que incluye), el costo
    de IA mensual proyectado de un usuario (`mensual_ia`) y el costo fijo mensual por usuario (infraestructura y soporte).
    Devuelve una lista de diccionarios con: `margen_tope` (si se limita el uso al tope del plan), `margen_libre` (si la plataforma absorbe
    todo el gasto), `margen_pct` (del precio, con tope), `equilibrio` (cuántas veces el uso actual aguanta el plan antes de dar pérdida;
    None si el uso es cero o el precio no cubre ni el costo fijo) y `excede` (si el uso supera el tope del plan)."""
    salida = []
    for pl in planes:
        precio, tope = float(pl["precio"]), float(pl["tope_ia"])
        con_tope = min(mensual_ia, tope) if tope > 0 else mensual_ia
        margen_tope = precio - con_tope - costo_fijo
        margen_libre = precio - mensual_ia - costo_fijo
        salida.append({"nombre": pl["nombre"], "precio": precio, "tope_ia": tope, "margen_tope": margen_tope, "margen_libre": margen_libre,
                       "margen_pct": (margen_tope / precio * 100.0) if precio > 0 else None,
                       "equilibrio": ((precio - costo_fijo) / mensual_ia) if mensual_ia > 0 and precio > costo_fijo else None,
                       "excede": tope > 0 and mensual_ia > tope})
    return salida


# TITULO SERIE NETA

def serie_neta(ingresos_mensual: dict, costo_por_dia: dict) -> dict:
    """Resultado neto por mes: ingresos hipotéticos del mes menos el costo de IA de ese mes.

    `ingresos_mensual` es {"AAAA-MM": monto} (la suma de los modelos activos) y `costo_por_dia` {"AAAA-MM-DD": costo}. Devuelve
    {"AAAA-MM": {"ingresos", "costo_ia", "neto"}} con todos los meses que aparezcan en alguno de los dos."""
    costo_mes: dict = {}
    for dia, monto in costo_por_dia.items():
        costo_mes[dia[:7]] = costo_mes.get(dia[:7], 0.0) + monto
    meses = sorted(set(ingresos_mensual) | set(costo_mes))
    return {m: {"ingresos": ingresos_mensual.get(m, 0.0), "costo_ia": costo_mes.get(m, 0.0),
                "neto": ingresos_mensual.get(m, 0.0) - costo_mes.get(m, 0.0)} for m in meses}


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara ingresos_virtuales .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
