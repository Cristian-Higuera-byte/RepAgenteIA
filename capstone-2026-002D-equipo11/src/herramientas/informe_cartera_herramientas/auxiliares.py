# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara auxiliares .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Funciones y constantes auxiliares del informe de cartera (sin registrar nada).

Cada función calcula una sección del informe a partir de las posiciones
abiertas de MT5: exposición y sensibilidad al 1 %, volatilidad (ATR diario),
correlaciones entre activos, riesgo de noticias macro, escenarios de resultado
y alertas. Se mantienen aquí para que ``herramientas.informe_cartera`` solo
orquesten y aísle los fallos de cada sección.
"""
from __future__ import annotations

from typing import Any

from database.scripts.fuentes import mt5_fuentes as mt5_fuente
from herramientas import analisis_herramientas, cuantitativo_herramientas, macro_eventos_herramientas


# Máximo de símbolos para los que se calcula el ATR (limita las llamadas a MT5).
MAX_SIMBOLOS_VOLATILIDAD = 8


UMBRAL_CORRELACION = 0.70       # |correlación| a partir de la cual dos posiciones "se mueven juntas"


UMBRAL_EXPOSICION_EQUIDAD_PCT = 3.0   # una divisa cuyo 1% mueve la equidad más que esto se avisa como exposición alta


NIVEL_MARGEN_MINIMO_PCT = 200   # por debajo se avisa de poco margen de seguridad


# Códigos de divisa reconocidos para identificar pares de forex por su nombre.
_DIVISAS_FX = {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "SEK", "NOK", "MXN", "ZAR", "CLP", "TRY", "PLN"}


def _par_fx(simbolo: str) -> tuple[str, str] | None:
    """('EUR', 'USD') si el símbolo es un par de divisas (admite sufijos del broker: EURUSD.r)."""
    s = "".join(c for c in simbolo.upper() if c.isalpha())[:6]
    if len(s) == 6 and s[:3] in _DIVISAS_FX and s[3:] in _DIVISAS_FX:
        return s[:3], s[3:]
    return None


def _signo(tipo: str) -> int:
    """Devuelve +1 si el tipo de posición es compra (COMPRA/BUY) y -1 en caso contrario (venta)."""
    return 1 if str(tipo).upper() in ("COMPRA", "BUY") else -1


def _sensibilidad_1pct(pos: dict[str, Any]) -> float | None:
    """Lo que gana (+) o pierde (-) la posición, en dinero, si el precio sube 1%."""
    # Sin precio actual no se puede simular el movimiento.
    precio = pos.get("precio_actual")
    if not precio:
        return None
    # Pide a MT5 el resultado de una compra si el precio sube 1 % (usa el cálculo de beneficios de MT5).
    sube = mt5_fuente.resultado_si_precio(pos["simbolo"], "COMPRA", pos["lotes"], precio, precio * 1.01)
    if sube is None:
        return None
    return round(sube * _signo(pos["tipo"]), 2)   # firmada: compra gana si sube, venta pierde


def _exposicion(posiciones: list[dict[str, Any]], equidad: float) -> dict[str, Any]:
    """Calcula la exposición de la cartera por activo y por divisa.

    Para cada posición obtiene la sensibilidad a un movimiento de 1 % del
    precio (en dinero de la cuenta) y la acumula por símbolo (lotes de compra y
    venta, dirección neta y porcentaje de la equidad) y, en pares de divisas,
    por divisa individual (larga en la base, corta en la cotizada). Recibe las
    posiciones de MT5 y la equidad. Devuelve el detalle más una nota y la clave
    interna ``_mayor_divisa`` (divisa, % de equidad) que usa ``_alertas``.
    """
    # Acumuladores: por símbolo y por divisa.
    por_activo: dict[str, dict[str, Any]] = {}
    por_divisa: dict[str, float] = {}
    # Recorre las posiciones sumando su sensibilidad firmada.
    for p in posiciones:
        s = _sensibilidad_1pct(p)
        if s is None:
            continue
        a = por_activo.setdefault(p["simbolo"], {"lotes_compra": 0.0, "lotes_venta": 0.0, "sensibilidad_1pct_usd": 0.0})
        a["lotes_compra" if _signo(p["tipo"]) > 0 else "lotes_venta"] += p["lotes"]
        a["sensibilidad_1pct_usd"] = round(a["sensibilidad_1pct_usd"] + s, 2)
        par = _par_fx(p["simbolo"])
        if par:   # la posición larga en el par es larga en la base y corta en la cotizada
            por_divisa[par[0]] = por_divisa.get(par[0], 0.0) + s
            por_divisa[par[1]] = por_divisa.get(par[1], 0.0) - s
    # Redondea y completa cada activo con su dirección neta y su peso en la equidad.
    for a in por_activo.values():
        a["lotes_compra"], a["lotes_venta"] = round(a["lotes_compra"], 2), round(a["lotes_venta"], 2)
        a["direccion_neta"] = (
            "LARGA" if a["sensibilidad_1pct_usd"] > 0 else "CORTA" if a["sensibilidad_1pct_usd"] < 0 else "NEUTRA"
        )
        a["sensibilidad_1pct_equidad_pct"] = round(a["sensibilidad_1pct_usd"] / equidad * 100, 2) if equidad else None
    # Ordena las divisas por exposición absoluta y detecta la mayor.
    divisas = {d: round(v, 2) for d, v in sorted(por_divisa.items(), key=lambda kv: -abs(kv[1]))}
    mayor = next(iter(divisas.items()), None)
    return {
        "por_activo": por_activo,
        "por_divisa_fx_usd_por_1pct": divisas,
        "nota": (
            "Sensibilidad = ganancia/pérdida en dinero si el precio se mueve 1%, calculada por MT5 "
            "(positiva = gana si sube). Por divisa solo cuentan los pares de divisas; oro, índices y "
            "cripto aparecen únicamente por activo."
        ),
        "_mayor_divisa": (mayor[0], round(abs(mayor[1]) / equidad * 100, 2)) if mayor and equidad else None,
    }


def _volatilidad(simbolos: list[str]) -> dict[str, Any]:
    """Obtiene el ATR(14) diario de cada símbolo (hasta ``MAX_SIMBOLOS_VOLATILIDAD``).

    Usa ``calcular_indicadores_tecnicos`` con velas D1; los símbolos sin datos
    se omiten sin interrumpir el informe. Devuelve un diccionario
    símbolo -> {atr_diario, atr_diario_pct, precio_actual}.
    """
    out: dict[str, Any] = {}
    for s in simbolos[:MAX_SIMBOLOS_VOLATILIDAD]:
        try:
            ind = analisis_herramientas.calcular_indicadores_tecnicos(simbolo=s, timeframe="D1", cantidad=60)
        except Exception:  # noqa: BLE001 - un símbolo sin datos no tumba el informe
            continue
        atr = (ind.get("indicadores") or {}).get("atr_14") or {}
        if atr.get("valor_absoluto"):
            out[s] = {
                "atr_diario": atr["valor_absoluto"],
                "atr_diario_pct": atr.get("volatilidad_pct"),
                "precio_actual": ind.get("precio_actual"),
            }
    return out


def _correlaciones(posiciones: list[dict[str, Any]]) -> dict[str, Any]:
    """Mide las correlaciones de retornos diarios (90 días) entre los activos abiertos.

    Necesita al menos dos símbolos distintos; si no, devuelve un mensaje.
    Lista los pares con correlación absoluta mayor o igual a
    ``UMBRAL_CORRELACION`` indicando si, según la dirección neta de cada
    posición, se refuerzan (misma apuesta) o se compensan (cobertura parcial).
    Devuelve el error de la matriz tal cual si el cálculo falla.
    """
    simbolos = sorted({p["simbolo"] for p in posiciones})
    if len(simbolos) < 2:
        return {"mensaje": "Se necesitan al menos 2 activos distintos abiertos para medir correlaciones."}
    res = cuantitativo_herramientas.calcular_matriz_correlacion(",".join(simbolos), 90)
    if "error" in res:
        return res
    # Dirección neta (lotes con signo) por símbolo, para saber si cada par se refuerza o compensa.
    matriz = res["matriz_correlacion"]
    direccion: dict[str, int] = {}
    for p in posiciones:
        direccion[p["simbolo"]] = direccion.get(p["simbolo"], 0) + _signo(p["tipo"]) * p["lotes"]
    # Recorre cada par único de activos y conserva solo los muy correlacionados.
    pares = []
    for i, a in enumerate(res["activos_analizados"]):
        for b in res["activos_analizados"][i + 1:]:
            c = matriz[a][b]
            if abs(c) < UMBRAL_CORRELACION:
                continue
            # correlación "efectiva": si una larga y otra corta se mueven juntas, se compensan
            efectiva = c * (1 if direccion.get(a, 0) * direccion.get(b, 0) > 0 else -1)
            pares.append({
                "activos": [a, b],
                "correlacion": c,
                "efecto_en_cartera": (
                    "SE REFUERZAN (riesgo concentrado en la misma apuesta)" if efectiva > 0
                    else "SE COMPENSAN (cobertura parcial)"
                ),
            })
    return {
        "dias_historicos": res["dias_historicos"],
        "matriz_correlacion": matriz,
        "pares_relevantes": pares,
        "criterio": f"Relevante = correlación absoluta de {UMBRAL_CORRELACION} o más (retornos diarios).",
    }


def _noticias(posiciones: list[dict[str, Any]]) -> dict[str, Any]:
    """Evalúa titulares de alto impacto sobre las divisas y el oro de la cartera.

    Deduce las divisas implicadas (componentes de los pares FX y XAU para el
    oro; máximo 5, o "ALL" si no hay ninguna), consulta
    ``evaluar_riesgo_noticias_proximas`` (titulares de Investing.com) y
    consolida los titulares sin repetir. Devuelve ``{"disponible": False, ...}``
    si ninguna consulta tuvo datos.
    """
    # Divisas a vigilar, sin repetir y respetando el orden.
    divisas: list[str] = []
    for p in posiciones:
        par = _par_fx(p["simbolo"])
        claves = list(par) if par else (["XAU"] if "XAU" in p["simbolo"].upper() or "GOLD" in p["simbolo"].upper() else [])
        for d in claves:
            if d not in divisas:
                divisas.append(d)
    # Consulta el riesgo de noticias para cada divisa (hasta 5).
    evaluadas = divisas[:5] or ["ALL"]
    resultados = {d: macro_eventos_herramientas.evaluar_riesgo_noticias_proximas(d) for d in evaluadas}
    if all(not r.get("disponible") for r in resultados.values()):
        return {"disponible": False, "mensaje": next(iter(resultados.values())).get("mensaje")}
    # Junta los titulares eliminando duplicados por título.
    titulares: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for d, r in resultados.items():
        for t in r.get("titulares_alto_impacto", []):
            if t["titulo"] not in vistos:
                vistos.add(t["titulo"])
                titulares.append({"divisa": d, **t})
    return {
        "disponible": True,
        "divisas_evaluadas": evaluadas,
        "nivel_cautela_macro": "PRECAUCIÓN" if titulares else "SIN SEÑALES EN TITULARES",
        "titulares_alto_impacto": titulares[:8],
        "limitacion": "Basado en titulares de Investing.com; no es un calendario con horas exactas.",
    }


def _escenarios(posiciones: list[dict[str, Any]], vol: dict[str, Any], riesgo: dict[str, Any], equidad: float) -> dict[str, Any]:
    """Construye cuatro escenarios de referencia para toda la cartera.

    Escenarios: todos los stops activados, todos los objetivos (TP) cumplidos,
    un movimiento de 1 ATR diario en contra de cada posición y otro a favor.
    Recibe las posiciones, la volatilidad por símbolo (de ``_volatilidad``), el
    análisis de riesgo y la equidad. Cada fila trae el resultado en dinero, su
    porcentaje de la equidad y la equidad resultante. Los resultados por ATR se
    calculan con MT5; las posiciones sin ATR o sin precio se cuentan como sin datos.
    """
    # Suma los resultados de un movimiento de 1 ATR adverso y favorable posición a posición.
    adverso = favorable = 0.0
    sin_dato = 0
    for p in posiciones:
        v = vol.get(p["simbolo"])
        if not v or not p.get("precio_actual"):
            sin_dato += 1
            continue
        mov = v["atr_diario"]
        s = _signo(p["tipo"])
        contra = p["precio_actual"] - s * mov     # precio se mueve 1 ATR en contra de la posición
        pro = p["precio_actual"] + s * mov
        r_c = mt5_fuente.resultado_si_precio(p["simbolo"], p["tipo"], p["lotes"], p["precio_actual"], contra)
        r_p = mt5_fuente.resultado_si_precio(p["simbolo"], p["tipo"], p["lotes"], p["precio_actual"], pro)
        if r_c is None or r_p is None:
            sin_dato += 1
            continue
        adverso += r_c
        favorable += r_p

    def fila(nombre: str, delta: float | None, nota: str) -> dict[str, Any]:
        """Arma una fila de escenario con el resultado en dinero, su % de la equidad y la equidad final (None si no hay dato)."""
        return {
            "escenario": nombre, "resultado_usd": None if delta is None else round(delta, 2),
            "resultado_equidad_pct": None if delta is None or not equidad else round(delta / equidad * 100, 2),
            "equidad_resultante_usd": None if delta is None else round(equidad + delta, 2), "nota": nota,
        }

    # Riesgo total con stops y beneficio total esperado si se cumplen los TP.
    tot = riesgo.get("riesgo_total_acumulado_usd")
    objetivo = sum((p.get("beneficio_estimado_usd") or 0) for p in riesgo.get("posiciones", []))
    filas = [
        fila("Todos los stops se activan", None if tot is None else -tot,
             "Peor caso con las protecciones actuales; las posiciones sin SL no están incluidas."),
        fila("Todos los objetivos (TP) se cumplen", objetivo or None, "Solo posiciones con TP definido."),
        fila("Movimiento de 1 ATR diario EN CONTRA de cada posición", adverso if sin_dato < len(posiciones) else None,
             "Día adverso típico para toda la cartera a la vez."),
        fila("Movimiento de 1 ATR diario A FAVOR de cada posición", favorable if sin_dato < len(posiciones) else None,
             "Día favorable típico."),
    ]
    return {
        "escenarios": filas,
        "aviso": "Escenarios de referencia calculados con el ATR y los niveles actuales; no son predicciones ni tienen probabilidad.",
        "posiciones_sin_datos_de_volatilidad": sin_dato,
    }


def _alertas(cuenta: dict[str, Any], riesgo: dict[str, Any], expo: dict[str, Any], corr: dict[str, Any], noticias: dict[str, Any]) -> list[str]:
    """Genera la lista de avisos de texto a partir de las demás secciones del informe.

    Avisa de: posiciones sin Stop Loss, riesgo total por encima del límite del
    agente (``core.ordenes.LIMITES``), exposición alta a una divisa,
    pares correlacionados que se refuerzan, nivel de margen bajo y titulares
    macro de alto impacto. Devuelve una lista (vacía si no hay alertas).
    """
    a: list[str] = []
    if riesgo.get("posiciones_sin_stop_loss"):
        a.append(f"{riesgo['posiciones_sin_stop_loss']} posición(es) SIN Stop Loss: riesgo ilimitado.")
    # Importación diferida: si el límite no se puede leer, solo se omite ese aviso.
    try:
        from core import ordenes
        tope = ordenes.LIMITES.riesgo_max_total_pct
        if (riesgo.get("riesgo_total_equidad_pct") or 0) > tope:
            a.append(f"El riesgo total ({riesgo['riesgo_total_equidad_pct']}% de la equidad) supera el límite del agente ({tope}%).")
    except Exception:  # noqa: BLE001
        pass
    # Exposición concentrada en una sola divisa.
    mayor = expo.get("_mayor_divisa")
    if mayor and mayor[1] >= UMBRAL_EXPOSICION_EQUIDAD_PCT:
        a.append(f"Exposición alta a {mayor[0]}: un movimiento de 1% en esa divisa mueve tu equidad ~{mayor[1]}%.")
    # Pares que se refuerzan: equivalen casi a la misma apuesta.
    for par in corr.get("pares_relevantes", []):
        if par["efecto_en_cartera"].startswith("SE REFUERZAN"):
            a.append(f"{par['activos'][0]} y {par['activos'][1]} se mueven juntos (corr. {par['correlacion']}): es casi la misma apuesta.")
    # Margen de seguridad y noticias macro.
    nivel = cuenta.get("nivel_margen_pct")
    if nivel and nivel < NIVEL_MARGEN_MINIMO_PCT:
        a.append(f"Nivel de margen bajo ({nivel}%).")
    if noticias.get("nivel_cautela_macro") == "PRECAUCIÓN":
        a.append("Hay titulares sobre eventos macro de alto impacto relacionados con tus activos.")
    return a


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara auxiliares .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
