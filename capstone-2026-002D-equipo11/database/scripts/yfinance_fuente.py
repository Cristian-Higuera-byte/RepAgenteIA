"""Fuente de datos: Yahoo Finance (librería yfinance).

Esta capa solo sabe OBTENER y NORMALIZAR datos. No conoce al modelo ni a las
herramientas: devuelve diccionarios/listas simples y lanza ValueError con un
mensaje claro cuando algo no existe (el registro de herramientas se lo pasa
al modelo para que pueda corregir el símbolo o explicárselo al usuario).

Símbolos de Yahoo:
    acciones  AAPL, MSFT        forex      EURUSD=X, USDCLP=X
    índices   ^GSPC, ^IXIC      cripto     BTC-USD
    materias primas  GC=F (oro), CL=F (petróleo)

Los datos son gratuitos y pueden llegar con retraso (hasta ~15 min según el mercado).

Prueba rápida (desde la raíz del proyecto):  python -m fuentes.yfinance_fuente
"""
from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Any, Callable

import yfinance as yf  # type: ignore[import-untyped]

PERIODOS = ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
INTERVALOS = ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")

AVISO_RETRASO = "Datos de Yahoo Finance; pueden tener retraso de hasta ~15 min según el mercado."

# ──────────────────────────────────────────────────────────────
# Utilidades internas
# ──────────────────────────────────────────────────────────────
_CACHE: dict[str, tuple[float, Any]] = {}


def _cacheado(clave: str, ttl: float, fn: Callable[[], Any]) -> Any:
    """Cache en memoria con vencimiento: evita golpear a Yahoo con consultas repetidas."""
    ahora = time.monotonic()
    guardado = _CACHE.get(clave)
    if guardado and ahora - guardado[0] < ttl:
        return guardado[1]
    valor = fn()  # si lanza excepción, no se cachea
    _CACHE[clave] = (ahora, valor)
    return valor


def _simbolo(texto: str) -> str:
    s = (texto or "").strip().upper()
    if not s:
        raise ValueError("Falta el símbolo.")
    return s


def _num(valor: Any, decimales: int = 4) -> float | None:
    """Convierte a float JSON-seguro (NaN/inf/None -> None)."""
    try:
        f = float(valor)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, decimales)


def _entero(valor: Any) -> int | None:
    n = _num(valor, 0)
    return int(n) if n is not None else None


def _leer(obj: Any, nombre: str, texto: bool = False) -> Any:
    try:
        v = getattr(obj, nombre)
    except Exception:  # noqa: BLE001 - fast_info lanza KeyError/AttributeError si falta
        return None
    return v if texto else _num(v)


def _sin_nulos(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _validar_fecha(texto: str, campo: str) -> str:
    try:
        datetime.strptime(texto, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"'{campo}' debe tener formato AAAA-MM-DD (recibido: {texto!r}).") from None
    return texto


def _fmt_fecha(ts: Any, intradia: bool) -> str:
    return ts.strftime("%Y-%m-%d %H:%M" if intradia else "%Y-%m-%d")


# ──────────────────────────────────────────────────────────────
# Búsqueda de símbolos
# ──────────────────────────────────────────────────────────────
def buscar(consulta: str, max_resultados: int = 8) -> list[dict[str, Any]]:
    consulta = (consulta or "").strip()
    if not consulta:
        raise ValueError("Falta el texto a buscar.")
    n = max(1, min(int(max_resultados), 15))

    def _fn() -> list[dict[str, Any]]:
        resultado = yf.Search(consulta, max_results=n)
        return [
            _sin_nulos(
                {
                    "simbolo": q.get("symbol"),
                    "nombre": q.get("longname") or q.get("shortname"),
                    "tipo": q.get("quoteType"),
                    "bolsa": q.get("exchDisp") or q.get("exchange"),
                }
            )
            for q in (resultado.quotes or [])
        ]

    return _cacheado(f"buscar:{consulta.lower()}:{n}", 3600, _fn)


# ──────────────────────────────────────────────────────────────
# Cotización actual
# ──────────────────────────────────────────────────────────────
def cotizacion(simbolo: str) -> dict[str, Any]:
    s = _simbolo(simbolo)

    def _fn() -> dict[str, Any]:
        fi = yf.Ticker(s).fast_info
        precio = _leer(fi, "last_price")
        if precio is None:
            raise ValueError(
                f"Yahoo no devolvió precio para '{s}'. Verifica el símbolo "
                "(ej. AAPL, EURUSD=X, ^GSPC, BTC-USD, GC=F) o reintenta en un momento."
            )
        previo = _leer(fi, "previous_close")
        variacion = variacion_pct = None
        if previo:
            variacion = _num(precio - previo)
            variacion_pct = _num((precio / previo - 1) * 100, 2)

        return _sin_nulos(
            {
                "simbolo": s,
                "precio": precio,
                "cierre_anterior": previo,
                "variacion": variacion,
                "variacion_pct": variacion_pct,
                "apertura": _leer(fi, "open"),
                "maximo_dia": _leer(fi, "day_high"),
                "minimo_dia": _leer(fi, "day_low"),
                "volumen": _entero(_leer(fi, "last_volume")),
                "maximo_52s": _leer(fi, "year_high"),
                "minimo_52s": _leer(fi, "year_low"),
                "media_50d": _leer(fi, "fifty_day_average"),
                "media_200d": _leer(fi, "two_hundred_day_average"),
                "capitalizacion": _leer(fi, "market_cap"),
                "moneda": _leer(fi, "currency", texto=True),
                "bolsa": _leer(fi, "exchange", texto=True),
                "consultado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "aviso": AVISO_RETRASO,
            }
        )

    return _cacheado(f"cotizacion:{s}", 30, _fn)


# ──────────────────────────────────────────────────────────────
# Histórico de precios
# ──────────────────────────────────────────────────────────────
def historico(
    simbolo: str,
    periodo: str = "3mo",
    intervalo: str = "1d",
    inicio: str | None = None,
    fin: str | None = None,
    ultimas_velas: int = 20,
) -> dict[str, Any]:
    """Resumen estadístico de TODO el rango + las últimas N velas (para no inundar el contexto)."""
    s = _simbolo(simbolo)
    if intervalo not in INTERVALOS:
        raise ValueError(f"Intervalo inválido: {intervalo!r}. Opciones: {', '.join(INTERVALOS)}")
    if inicio:
        _validar_fecha(inicio, "inicio")
        if fin:
            _validar_fecha(fin, "fin")
    elif periodo not in PERIODOS:
        raise ValueError(f"Periodo inválido: {periodo!r}. Opciones: {', '.join(PERIODOS)}")
    n = max(0, min(int(ultimas_velas), 200))
    intradia = intervalo[-1] in ("m", "h")  # 1m, 5m, 60m, 1h... (no '1mo', '3mo')

    def _fn() -> dict[str, Any]:
        ticker = yf.Ticker(s)
        if inicio:
            df = ticker.history(start=inicio, end=fin, interval=intervalo, auto_adjust=True)
        else:
            df = ticker.history(period=periodo, interval=intervalo, auto_adjust=True)
        if df is None or df.empty:
            raise ValueError(
                f"Yahoo no devolvió datos para '{s}' con esos parámetros. Revisa el símbolo; "
                "los intervalos intradía solo tienen datos recientes (1m: 7 días, resto: ~60 días)."
            )
        df = df.dropna(subset=["Close"])

        cierres = df["Close"]
        retornos = cierres.pct_change().dropna()
        primero, ultimo = cierres.iloc[0], cierres.iloc[-1]

        resumen = _sin_nulos(
            {
                "velas_totales": len(df),
                "desde": _fmt_fecha(df.index[0], intradia),
                "hasta": _fmt_fecha(df.index[-1], intradia),
                "cierre_inicial": _num(primero),
                "cierre_final": _num(ultimo),
                "variacion_pct": _num((ultimo / primero - 1) * 100, 2) if primero else None,
                "maximo": _num(df["High"].max()),
                "fecha_maximo": _fmt_fecha(df["High"].idxmax(), intradia),
                "minimo": _num(df["Low"].min()),
                "fecha_minimo": _fmt_fecha(df["Low"].idxmin(), intradia),
                "volumen_promedio": _entero(df["Volume"].mean()),
                "desv_estandar_retornos_por_vela_pct": _num(retornos.std() * 100, 3) if len(retornos) > 1 else None,
            }
        )
        velas = [
            {
                "fecha": _fmt_fecha(idx, intradia),
                "apertura": _num(fila["Open"]),
                "maximo": _num(fila["High"]),
                "minimo": _num(fila["Low"]),
                "cierre": _num(fila["Close"]),
                "volumen": _entero(fila["Volume"]),
            }
            for idx, fila in df.tail(n).iterrows()
        ]
        return {
            "simbolo": s,
            "intervalo": intervalo,
            "resumen_rango_completo": resumen,
            "ultimas_velas": velas,
            "aviso": AVISO_RETRASO,
        }

    ttl = 60 if intradia else 600
    return _cacheado(f"historico:{s}:{periodo}:{intervalo}:{inicio}:{fin}:{n}", ttl, _fn)


# ──────────────────────────────────────────────────────────────
# Fundamentales (Ticker.info)
# ──────────────────────────────────────────────────────────────
_CAMPOS_TEXTO = {
    "nombre": "longName",
    "sector": "sector",
    "industria": "industry",
    "pais": "country",
    "moneda": "currency",
    "sitio_web": "website",
}
_CAMPOS_NUM = {
    "capitalizacion": "marketCap",
    "per_trailing": "trailingPE",
    "per_forward": "forwardPE",
    "eps_trailing": "trailingEps",
    "eps_forward": "forwardEps",
    "precio_sobre_valor_libro": "priceToBook",
    "dividendo_anual_por_accion": "dividendRate",
    "beta": "beta",
    "margen_bruto": "grossMargins",
    "margen_operativo": "operatingMargins",
    "margen_neto": "profitMargins",
    "roe": "returnOnEquity",
    "roa": "returnOnAssets",
    "deuda_total": "totalDebt",
    "caja_total": "totalCash",
    "deuda_sobre_capital": "debtToEquity",
    "ratio_corriente": "currentRatio",
    "ingresos_totales": "totalRevenue",
    "crecimiento_ingresos": "revenueGrowth",
    "crecimiento_beneficios": "earningsGrowth",
    "ebitda": "ebitda",
    "flujo_caja_libre": "freeCashflow",
    "empleados": "fullTimeEmployees",
}


def fundamentales(simbolo: str) -> dict[str, Any]:
    s = _simbolo(simbolo)

    def _fn() -> dict[str, Any]:
        info = yf.Ticker(s).info or {}
        if len(info) <= 1:
            raise ValueError(
                f"Yahoo no tiene datos fundamentales para '{s}'. Es normal en forex, "
                "índices y cripto; para acciones verifica el símbolo."
            )
        datos: dict[str, Any] = {"simbolo": s}
        for clave, campo in _CAMPOS_TEXTO.items():
            datos[clave] = info.get(campo)
        for clave, campo in _CAMPOS_NUM.items():
            datos[clave] = _num(info.get(campo))
        descripcion = info.get("longBusinessSummary")
        if descripcion:
            datos["descripcion"] = descripcion[:500] + ("..." if len(descripcion) > 500 else "")
        datos["nota"] = (
            "Márgenes, ROE, ROA y crecimientos vienen como fracción (0.25 = 25%). "
            "deuda_sobre_capital viene en porcentaje (150 = 150%)."
        )
        return _sin_nulos(datos)

    return _cacheado(f"fundamentales:{s}", 3600, _fn)


# ──────────────────────────────────────────────────────────────
# Estados financieros
# ──────────────────────────────────────────────────────────────
# tipo -> (atributo anual, atributo trimestral, filas clave)
_ESTADOS = {
    "resultados": (
        "income_stmt",
        "quarterly_income_stmt",
        ("Total Revenue", "Gross Profit", "Operating Income", "EBITDA", "Net Income", "Diluted EPS"),
    ),
    "balance": (
        "balance_sheet",
        "quarterly_balance_sheet",
        (
            "Total Assets",
            "Total Liabilities Net Minority Interest",
            "Stockholders Equity",
            "Total Debt",
            "Net Debt",
            "Cash And Cash Equivalents",
        ),
    ),
    "flujo_caja": (
        "cashflow",
        "quarterly_cashflow",
        ("Operating Cash Flow", "Capital Expenditure", "Free Cash Flow"),
    ),
}


def estados_financieros(
    simbolo: str, tipo: str = "resultados", frecuencia: str = "anual", periodos: int = 4
) -> dict[str, Any]:
    s = _simbolo(simbolo)
    if tipo not in _ESTADOS:
        raise ValueError(f"Tipo inválido: {tipo!r}. Opciones: {', '.join(_ESTADOS)}")
    if frecuencia not in ("anual", "trimestral"):
        raise ValueError("frecuencia debe ser 'anual' o 'trimestral'.")
    n = max(1, min(int(periodos), 8))
    anual, trimestral, filas = _ESTADOS[tipo]
    atributo = anual if frecuencia == "anual" else trimestral

    def _fn() -> dict[str, Any]:
        df = getattr(yf.Ticker(s), atributo)
        if df is None or df.empty:
            raise ValueError(
                f"Sin estado de {tipo} ({frecuencia}) para '{s}'. Índices, forex y cripto no tienen estados financieros."
            )
        presentes = [f for f in filas if f in df.index]
        df = df.loc[presentes] if presentes else df.head(15)

        salida = []
        for columna in df.columns[:n]:  # Yahoo entrega primero el periodo más reciente
            fila: dict[str, Any] = {
                "periodo": columna.strftime("%Y-%m-%d") if hasattr(columna, "strftime") else str(columna)
            }
            for item, valor in df[columna].items():
                fila[str(item)] = _num(valor, 2)
            salida.append(fila)
        return {
            "simbolo": s,
            "tipo": tipo,
            "frecuencia": frecuencia,
            "periodos": salida,
            "nota": "Cifras en la moneda de reporte de la empresa.",
        }

    return _cacheado(f"estados:{s}:{tipo}:{frecuencia}:{n}", 6 * 3600, _fn)


# ──────────────────────────────────────────────────────────────
# Noticias
# ──────────────────────────────────────────────────────────────
def _normalizar_noticia(item: dict[str, Any] | None) -> dict[str, Any] | None:
    """Yahoo ha cambiado el formato de las noticias; aquí se soportan el nuevo y el antiguo."""
    if not isinstance(item, dict):
        return None

    c = item.get("content") if isinstance(item.get("content"), dict) else item
    if not isinstance(c, dict):
        return None

    titulo = c.get("title")
    if not titulo:
        return None

    proveedor = c.get("provider")
    fuente = proveedor.get("displayName") if isinstance(proveedor, dict) else c.get("publisher")

    fecha = c.get("pubDate") or c.get("displayTime")
    provider_publish_time = c.get("providerPublishTime")
    if not fecha and isinstance(provider_publish_time, (int, float)):
        fecha = datetime.fromtimestamp(provider_publish_time, tz=timezone.utc).isoformat(timespec="seconds")

    url = None
    for clave in ("canonicalUrl", "clickThroughUrl"):
        v = c.get(clave)
        if isinstance(v, dict) and v.get("url"):
            url = v["url"]
            break
    url = url or c.get("link")

    resumen = c.get("summary") or c.get("description")
    if isinstance(resumen, str) and len(resumen) > 300:
        resumen = resumen[:300] + "..."

    return _sin_nulos({"titulo": titulo, "resumen": resumen, "fuente": fuente, "fecha": fecha, "url": url})


def noticias(simbolo: str, cantidad: int = 8) -> list[dict[str, Any]]:
    s = _simbolo(simbolo)
    n = max(1, min(int(cantidad), 20))

    def _fn() -> list[dict[str, Any]]:
        ticker = yf.Ticker(s)
        try:
            crudo = ticker.get_news(count=n)
        except (AttributeError, TypeError):  # versiones antiguas de yfinance
            crudo = ticker.news
        normalizadas = (_normalizar_noticia(i) for i in (crudo or []))
        return [x for x in normalizadas if x][:n]

    return _cacheado(f"noticias:{s}:{n}", 300, _fn)


# ──────────────────────────────────────────────────────────────
# Consenso de analistas
# ──────────────────────────────────────────────────────────────
def consenso_analistas(simbolo: str) -> dict[str, Any]:
    s = _simbolo(simbolo)

    def _fn() -> dict[str, Any]:
        ticker = yf.Ticker(s)
        resultado: dict[str, Any] = {"simbolo": s}

        try:
            objetivos = ticker.analyst_price_targets
            if objetivos:
                resultado["precio_objetivo"] = {k: _num(v) for k, v in objetivos.items()}
        except Exception:  # noqa: BLE001
            pass

        try:
            df = ticker.recommendations_summary
            if df is not None and not df.empty:
                resultado["recomendaciones"] = [
                    {k: (v if isinstance(v, str) else _entero(v)) for k, v in fila.items()}
                    for fila in df.head(2).to_dict("records")
                ]
        except Exception:  # noqa: BLE001
            pass

        if len(resultado) == 1:
            raise ValueError(f"Sin datos de analistas para '{s}' (solo existen para acciones y algunos ETF).")
        resultado["nota"] = "recomendaciones: conteo de analistas por periodo ('0m' = mes actual, '-1m' = mes anterior)."
        return resultado

    return _cacheado(f"analistas:{s}", 3600, _fn)


if __name__ == "__main__":
    import json

    pruebas = (
        ("buscar", lambda: buscar("apple", 3)),
        ("cotizacion", lambda: cotizacion("AAPL")),
        ("historico", lambda: historico("EURUSD=X", "1mo", ultimas_velas=3)),
        ("fundamentales", lambda: fundamentales("AAPL")),
        ("estados_financieros", lambda: estados_financieros("AAPL", "resultados", "anual", 2)),
        ("noticias", lambda: noticias("AAPL", 3)),
        ("consenso_analistas", lambda: consenso_analistas("AAPL")),
    )
    for nombre, prueba in pruebas:
        print(f"\n=== {nombre}")
        try:
            print(json.dumps(prueba(), ensure_ascii=False, indent=2, default=str))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: {type(e).__name__}: {e}")