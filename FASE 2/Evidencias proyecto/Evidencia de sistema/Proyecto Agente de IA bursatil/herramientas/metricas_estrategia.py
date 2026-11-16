# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara metricas_estrategia .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

"""Métricas de las estrategias de copy trading: se calculan a partir de las operaciones y del equity que registra `registro_operaciones.py`.

Tiene dos partes:
  - Cálculo puro (`calcular`): recibe las operaciones, la foto del equity y las copias de un gestor, y devuelve las métricas de la estrategia, su
    serie diaria y el reparto por tipo de activo. No toca la base de datos, así que se prueba sola.
  - Acceso a Supabase (`recalcular`, `listar_publicadas`, `detalle`, `refrescar_en_segundo_plano`): lee las tablas del copy trading (esquema en
    `herramientas/sql/copytrading.sql`), guarda las métricas en `estrategias_metricas` y `estrategias_diario` y arma los diccionarios que dibuja la vista.

Cómo se calcula cada cosa:
  - Rentabilidad: sale de la curva de equity, un valor por día (el último del día), descontando los depósitos y retiros (`flujo_neto`). Si todavía no
    hay fotos de equity, se usa el resultado acumulado de las operaciones cerradas sobre el equity con que se abrió la primera. Los días sin dato
    repiten el valor anterior. La rentabilidad de 1 mes, 3 meses y 12 meses se mide hacia atrás desde hoy; la total, desde el primer día con dato.
  - Drawdown máximo: la mayor caída, en porcentaje, desde un máximo de la curva hasta el mínimo siguiente.
  - Operaciones: se cuentan las cerradas; ganadoras son las de resultado mayor que cero y perdedoras las menores que cero. El factor de beneficio es
    la ganancia bruta dividida por la pérdida bruta (vacío si no hay pérdidas). Mejor y peor operación son el mayor y el menor resultado.
  - Riesgo: «bajo» con drawdown de hasta 15 %, «medio» hasta 35 % y «alto» por encima; un riesgo «bajo» pasa a «medio» si el apalancamiento medio es de
    200 o más.
  - Reparto por tipo de activo: porcentaje de operaciones de cada tipo, abiertas y cerradas por separado.
  - Inversores e invertido: copias activas o pausadas y suma de sus importes; el histórico diario se arma con las fechas de alta y cierre de cada copia.
Las métricas se recalculan en segundo plano cuando tienen más de 10 minutos. Si algo falla, el cálculo devuelve el error en lugar de lanzarlo.
"""
import threading
from datetime import date, datetime, timedelta, timezone

from herramientas.hilos import lanzar_hilo

# Minutos que valen las métricas antes de recalcularlas
_VIDA_MIN = 10
# Tamaño de página de las consultas a Supabase (PostgREST entrega como máximo 1000 filas por pedido) y de los guardados por lote
_PAGINA = 1000
_LOTE_GUARDADO = 500
# Umbrales de drawdown (%) para el nivel de riesgo y apalancamiento desde el que se sube un nivel
_DD_BAJO, _DD_MEDIO, _APAL_ALTO = 15.0, 35.0, 200
# Estrategias que se están recalculando ahora y su candado
_EN_CURSO: set = set()
_CANDADO = threading.Lock()


# TITULO A FECHA

def _a_fecha(valor) -> date | None:
    """Convierte un texto ISO con hora (de Supabase) o una fecha en `date` (día en UTC); None si no se puede."""
    if isinstance(valor, datetime):
        return valor.astimezone(timezone.utc).date() if valor.tzinfo else valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).astimezone(timezone.utc).date()
    except (TypeError, ValueError):
        return None


# TITULO A NUMERO

def _num(valor, defecto: float = 0.0) -> float:
    """Convierte a número (los numéricos de Supabase pueden llegar como texto); `defecto` si es vacío o inválido."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


# TITULO RIESGO

def nivel_riesgo(drawdown: float | None, apalancamiento: float | None) -> str:
    """Nivel de riesgo («bajo», «medio» o «alto») según el drawdown máximo y el apalancamiento medio (ver el encabezado del archivo)."""
    dd = drawdown if drawdown is not None else 0.0
    nivel = "bajo" if dd <= _DD_BAJO else ("medio" if dd <= _DD_MEDIO else "alto")
    if nivel == "bajo" and (apalancamiento or 0) >= _APAL_ALTO:
        nivel = "medio"
    return nivel


# TITULO INDICE DIARIO

def _indice_diario(equity: list, cerradas: list, hoy: date) -> list:
    """Curva diaria de la estrategia como lista de (día, índice, equity del día): el índice parte en 1 y sube o baja con la rentabilidad diaria.

    Usa las fotos de equity (descontando `flujo_neto`); si no hay, el resultado acumulado de las operaciones cerradas. Rellena los días sin dato con
    el valor anterior hasta `hoy`. Lista vacía si no hay datos."""
    por_dia: dict = {}
    for f in sorted(equity, key=lambda x: str(x.get("registrado_en"))):
        d = _a_fecha(f.get("registrado_en"))
        if d:
            actual = por_dia.setdefault(d, {"equity": 0.0, "flujo": 0.0})
            actual["equity"] = _num(f.get("equity"))        # queda la última foto del día
            actual["flujo"] += _num(f.get("flujo_neto"))
    serie = []
    if por_dia:
        dias = sorted(por_dia)
        indice, previo = 1.0, None
        for d in dias:
            e = por_dia[d]["equity"]
            if previo and previo > 0:
                indice *= max(0.0, (e - por_dia[d]["flujo"]) / previo)
            serie.append((d, indice, e))
            previo = e
    else:
        ops = sorted((o for o in cerradas if _a_fecha(o.get("cerrada_en"))), key=lambda o: str(o.get("cerrada_en")))
        base = next((_num(o.get("equity_apertura")) for o in sorted(cerradas, key=lambda o: str(o.get("abierta_en"))) if _num(o.get("equity_apertura")) > 0), 0.0)
        if not ops or base <= 0:
            return []
        acumulado: dict = {}
        total = 0.0
        for o in ops:
            total += _num(o.get("resultado"))
            acumulado[_a_fecha(o["cerrada_en"])] = total
        for d in sorted(acumulado):
            serie.append((d, 1 + acumulado[d] / base, base + acumulado[d]))
    # Días sin dato: repiten el último valor hasta hoy.
    completa, i = [], 0
    dia, ultimo = serie[0][0], serie[0]
    while dia <= max(hoy, serie[-1][0]):
        while i < len(serie) and serie[i][0] <= dia:
            ultimo = serie[i]
            i += 1
        completa.append((dia, ultimo[1], ultimo[2]))
        dia += timedelta(days=1)
    return completa


# TITULO RENTABILIDAD DESDE

def _rentabilidad_desde(serie: list, hoy: date, dias: int | None) -> float | None:
    """Rentabilidad en % de los últimos `dias` días (todo el historial si es None) a partir de la curva diaria; None si no hay curva."""
    if not serie:
        return None
    final = serie[-1][1]
    if dias is None:
        return round((final - 1) * 100, 2)
    limite = hoy - timedelta(days=dias)
    # Si la estrategia es más joven que el periodo, se mide desde el primer día (índice 1); si no, desde el último dato anterior al límite.
    base = 1.0 if serie[0][0] > limite else next(s[1] for s in reversed(serie) if s[0] <= limite)
    return round((final / base - 1) * 100, 2) if base > 0 else None


# TITULO DRAWDOWN

def _drawdowns(serie: list) -> list:
    """Drawdown en % de cada día de la curva (caída desde el máximo anterior)."""
    pico, salida = 0.0, []
    for _, indice, _e in serie:
        pico = max(pico, indice)
        salida.append(round((pico - indice) / pico * 100, 2) if pico > 0 else 0.0)
    return salida


# TITULO REPARTO

def _reparto(ops: list) -> dict:
    """Porcentaje de operaciones por tipo de activo ({"Índices": 100.0}); vacío si no hay operaciones."""
    cuenta: dict = {}
    for o in ops:
        tipo = o.get("tipo_activo") or "Otros"
        cuenta[tipo] = cuenta.get(tipo, 0) + 1
    total = sum(cuenta.values())
    return {k: round(v * 100 / total, 1) for k, v in sorted(cuenta.items(), key=lambda kv: -kv[1])} if total else {}


# TITULO COPIAS EN EL TIEMPO

def _copias_en(copias: list, dia: date) -> tuple:
    """(inversores, invertido) de las copias vigentes en `dia`: dadas de alta ese día o antes y no cerradas aún."""
    inversores, invertido = 0, 0.0
    for c in copias:
        alta, baja = _a_fecha(c.get("creada_en")), _a_fecha(c.get("cerrada_en"))
        if alta and alta <= dia and (baja is None or baja > dia):
            inversores += 1
            invertido += _num(c.get("importe"))
    return inversores, round(invertido, 2)


# TITULO CALCULAR

def calcular(operaciones: list, equity: list, copias: list | None = None, hoy: date | None = None) -> dict:
    """Calcula las métricas de una estrategia a partir de lo registrado de su gestor.

    Recibe las operaciones (filas de `operaciones`), las fotos de `equity_historial` y las `copias` de la estrategia (opcional). Devuelve
    {"metricas": {...columnas de estrategias_metricas...}, "diario": [{dia, rent_acumulada, equity, drawdown, inversores, invertido}]}."""
    hoy = hoy or datetime.now(timezone.utc).date()
    copias = copias or []
    cerradas = [o for o in operaciones if o.get("estado") == "cerrada"]
    abiertas = [o for o in operaciones if o.get("estado") == "abierta"]
    serie = _indice_diario(equity, cerradas, hoy)
    dds = _drawdowns(serie)
    resultados = [_num(o.get("resultado")) for o in cerradas]
    ganancias, perdidas = [r for r in resultados if r > 0], [r for r in resultados if r < 0]
    apalancamientos = [_num(o.get("apalancamiento")) for o in operaciones if _num(o.get("apalancamiento")) > 0]
    apalancamiento = int(round(sum(apalancamientos) / len(apalancamientos))) if apalancamientos else None
    drawdown = max(dds) if dds else None
    vigentes = [c for c in copias if c.get("estado") in ("activa", "pausada")]
    metricas = {
        "rent_1m": _rentabilidad_desde(serie, hoy, 30), "rent_3m": _rentabilidad_desde(serie, hoy, 90),
        "rent_12m": _rentabilidad_desde(serie, hoy, 365), "rent_total": _rentabilidad_desde(serie, hoy, None),
        "drawdown_max": drawdown, "riesgo": nivel_riesgo(drawdown, apalancamiento) if cerradas or serie else None, "apalancamiento": apalancamiento,
        "operaciones_total": len(cerradas), "operaciones_ganadoras": len(ganancias), "operaciones_perdedoras": len(perdidas),
        "mejor_operacion": round(max(resultados), 2) if resultados else None, "peor_operacion": round(min(resultados), 2) if resultados else None,
        "factor_beneficio": round(sum(ganancias) / -sum(perdidas), 2) if perdidas else None,
        "fondos_propios": round(serie[-1][2], 2) if serie else None,
        "invertido": round(sum(_num(c.get("importe")) for c in vigentes), 2), "inversores": len(vigentes),
        "asignacion_abiertas": _reparto(abiertas), "asignacion_cerradas": _reparto(cerradas),
    }
    diario = []
    for (dia, indice, eq), dd in zip(serie, dds):
        inversores, invertido = _copias_en(copias, dia)
        diario.append({"dia": dia.isoformat(), "rent_acumulada": round((indice - 1) * 100, 2), "equity": round(eq, 2), "drawdown": dd,
                       "inversores": inversores, "invertido": invertido})
    return {"metricas": metricas, "diario": diario}


# TITULO PAGINAR

def _paginar(consulta) -> list:
    """Trae todas las filas de una consulta de Supabase por páginas de `_PAGINA`. `consulta` es una función que devuelve la consulta ya filtrada."""
    filas, i = [], 0
    while True:
        pagina = consulta().range(i, i + _PAGINA - 1).execute().data or []
        filas.extend(pagina)
        if len(pagina) < _PAGINA:
            return filas
        i += _PAGINA


# TITULO RECALCULAR

def recalcular(cliente, estrategia: dict) -> dict:
    """Recalcula y guarda las métricas y la serie diaria de `estrategia` (fila de `estrategias`). Devuelve el resultado de `calcular`, o {"error": texto}."""
    try:
        gestor, cuenta, eid = estrategia["gestor_id"], estrategia.get("cuenta_tipo", "demo"), estrategia["id"]
        operaciones = _paginar(lambda: cliente.table("operaciones").select("estado,resultado,tipo_activo,apalancamiento,abierta_en,cerrada_en,equity_apertura")
                               .eq("usuario_id", gestor).eq("cuenta_tipo", cuenta).order("id"))
        equity = _paginar(lambda: cliente.table("equity_historial").select("equity,flujo_neto,registrado_en").eq("usuario_id", gestor)
                          .eq("cuenta_tipo", cuenta).order("id"))
        copias = _paginar(lambda: cliente.table("copias").select("estado,importe,creada_en,cerrada_en").eq("estrategia_id", eid).order("id"))
        r = calcular(operaciones, equity, copias)
        ahora = datetime.now(timezone.utc).isoformat()
        cliente.table("estrategias_metricas").upsert({"estrategia_id": eid, **r["metricas"], "actualizado_en": ahora}, on_conflict="estrategia_id").execute()
        filas = [{"estrategia_id": eid, **d} for d in r["diario"]]
        for i in range(0, len(filas), _LOTE_GUARDADO):
            cliente.table("estrategias_diario").upsert(filas[i:i + _LOTE_GUARDADO], on_conflict="estrategia_id,dia").execute()
        return r
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:200]}


# TITULO REFRESCAR EN SEGUNDO PLANO

def refrescar_en_segundo_plano(cliente, estrategias: list, metricas: dict) -> int:
    """Recalcula, en un hilo, las métricas de las `estrategias` que no tienen o tienen más de `_VIDA_MIN` minutos (`metricas` = {id: fila}).
    Devuelve cuántas lanzó. No repite una estrategia que ya se está recalculando."""
    limite = datetime.now(timezone.utc) - timedelta(minutes=_VIDA_MIN)
    lanzadas = 0
    for e in estrategias:
        m = metricas.get(e["id"])
        try:
            vigente = bool(m) and datetime.fromisoformat(str(m.get("actualizado_en")).replace("Z", "+00:00")) > limite
        except ValueError:
            vigente = False
        with _CANDADO:
            if vigente or e["id"] in _EN_CURSO:
                continue
            _EN_CURSO.add(e["id"])

        def trabajo(estrategia=e):
            """Recalcula las métricas de una estrategia en el hilo y la quita de las que están en curso al terminar."""
            try:
                recalcular(cliente, estrategia)
            finally:
                with _CANDADO:
                    _EN_CURSO.discard(estrategia["id"])
        lanzar_hilo(trabajo, nombre="metricas-estrategia")
        lanzadas += 1
    return lanzadas


# TITULO TEXTO DE TIPO

_TIPOS = {"manual": "Manual", "algoritmico": "Algorítmico"}


# TITULO PRINCIPAL

def _principal(reparto) -> str | None:
    """Tipo de activo con más peso en un reparto ({"Índices": 70.0, ...}); None si está vacío. Se calcula por valor porque jsonb no conserva el orden."""
    return max(reparto, key=reparto.get) if isinstance(reparto, dict) and reparto else None


# TITULO ARMAR ESTRATEGIA

def _armar(e: dict, m: dict, apodo: str, spark: list) -> dict:
    """Diccionario de una estrategia con la forma que usa la vista (claves como en `estrategias.json`, más `real` y `spark`)."""
    ganadoras, total = int(m.get("operaciones_ganadoras") or 0), int(m.get("operaciones_total") or 0)
    return {
        "id": str(e["id"]), "real": True, "nombre": e["nombre"], "gestor": apodo or "gestor", "riesgo": m.get("riesgo") or "medio",
        "cat": e.get("categoria") or _principal(m.get("asignacion_cerradas")) or "Otros", "rent": _num(m.get("rent_1m")), "fondos": round(_num(m.get("fondos_propios"))),
        "invertido": round(_num(m.get("invertido"))), "inv_min": round(_num(e.get("inversion_minima"), 50)), "comision": _num(e.get("comision_pct")),
        "inversores": int(m.get("inversores") or 0), "drawdown": _num(m.get("drawdown_max")), "apalancamiento": m.get("apalancamiento") or 0,
        "ops": total, "win": round(ganadoras * 100 / total) if total else 0, "tipo": _TIPOS.get(e.get("tipo"), "Manual"),
        "bio": e.get("biografia") or "", "desc": e.get("descripcion") or "", "spark": spark, "pendiente": not m}


# TITULO LISTAR PUBLICADAS

def listar_publicadas(cliente) -> list:
    """Estrategias publicadas con sus métricas y el apodo de su gestor, en la forma de la vista. Lanza el recálculo de las que lo necesiten.

    Lista vacía si no hay ninguna publicada o si falla la consulta."""
    try:
        estrategias = cliente.table("estrategias").select("*").eq("estado", "publicada").execute().data or []
        if not estrategias:
            return []
        ids, gestores = [e["id"] for e in estrategias], list({e["gestor_id"] for e in estrategias})
        metricas = {m["estrategia_id"]: m for m in (cliente.table("estrategias_metricas").select("*").in_("estrategia_id", ids).execute().data or [])}
        apodos = {p["usuario_id"]: p.get("apodo") for p in (cliente.table("perfiles_usuario").select("usuario_id,apodo").in_("usuario_id", gestores).execute().data or [])}
        desde = (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()
        puntos: dict = {}
        for d in cliente.table("estrategias_diario").select("estrategia_id,dia,rent_acumulada").in_("estrategia_id", ids).gte("dia", desde).order("dia").execute().data or []:
            puntos.setdefault(d["estrategia_id"], []).append(_num(d["rent_acumulada"]))
        refrescar_en_segundo_plano(cliente, estrategias, metricas)
        return [_armar(e, metricas.get(e["id"], {}), apodos.get(e["gestor_id"]), puntos.get(e["id"], [])) for e in estrategias]
    except Exception:  # noqa: BLE001
        return []


# TITULO DETALLE

def detalle(cliente, estrategia_id) -> dict:
    """Datos extra de la ficha de una estrategia real: {"metricas": fila completa, "diario": serie diaria, "abiertas": [...], "cerradas": [...]}.

    Las operaciones son las del gestor en la cuenta de la estrategia (las 30 más recientes de cada tipo). Diccionario con listas vacías si falla."""
    vacio = {"metricas": {}, "diario": [], "abiertas": [], "cerradas": []}
    try:
        e = (cliente.table("estrategias").select("*").eq("id", int(estrategia_id)).eq("estado", "publicada").limit(1).execute().data or [None])[0]
        if not e:
            return vacio
        columnas = "simbolo,tipo_activo,lado,volumen,tamano_contrato,precio_apertura,abierta_en,precio_cierre,cerrada_en,resultado"
        def operaciones(estado, orden):
            """Las 30 operaciones más recientes del gestor en el `estado` dado, ordenadas por la columna `orden`."""
            return (cliente.table("operaciones").select(columnas).eq("usuario_id", e["gestor_id"]).eq("cuenta_tipo", e.get("cuenta_tipo", "demo"))
                    .eq("estado", estado).order(orden, desc=True).limit(30).execute().data or [])
        return {"metricas": (cliente.table("estrategias_metricas").select("*").eq("estrategia_id", e["id"]).limit(1).execute().data or [{}])[0],
                "diario": _paginar(lambda: cliente.table("estrategias_diario").select("*").eq("estrategia_id", e["id"]).order("dia")),
                "abiertas": operaciones("abierta", "abierta_en"), "cerradas": operaciones("cerrada", "cerrada_en")}
    except Exception:  # noqa: BLE001
        return vacio



# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara metricas_estrategia .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
