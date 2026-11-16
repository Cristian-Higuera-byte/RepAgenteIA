# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara mercado .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Búsqueda de símbolos, cotización e histórico de precios.

Funciones públicas que consultan Yahoo Finance mediante yfinance, cachean el
resultado unos segundos o minutos y lanzan ValueError con un mensaje claro
cuando los parámetros son inválidos o Yahoo no devuelve datos."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf  # type: ignore[import-untyped]

from fuentes.yfinance_fuente.cache import _cacheado
from fuentes.yfinance_fuente.constantes import AVISO_RETRASO, INTERVALOS, PERIODOS
from fuentes.yfinance_fuente.utiles import _entero, _formatear_fecha, _leer, _num, _simbolo, _sin_nulos, _validar_fecha


# TITULO BUSCAR

# ──────────────────────────────────────────────────────────────
# Búsqueda de símbolos
# ──────────────────────────────────────────────────────────────
def buscar(consulta: str, max_resultados: int = 8) -> list[dict[str, Any]]:
    """Busca símbolos en Yahoo Finance por nombre o texto libre (p. ej. 'apple').

    Recibe el texto a buscar y el máximo de resultados (se limita a 1-15).
    Devuelve una lista de diccionarios con símbolo, nombre, tipo de instrumento
    y bolsa (los datos ausentes se omiten). Resultado cacheado 1 hora. Lanza
    ValueError si el texto está vacío."""
    consulta = (consulta or "").strip()
    if not consulta:
        raise ValueError("Falta el texto a buscar.")
    n = max(1, min(int(max_resultados), 15))

    def _fn() -> list[dict[str, Any]]:
        """Ejecuta la búsqueda en Yahoo y normaliza cada resultado; solo se ejecuta si la caché no tiene un valor vigente."""
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


# TITULO COTIZACION

# ──────────────────────────────────────────────────────────────
# Cotización actual
# ──────────────────────────────────────────────────────────────
def cotizacion(simbolo: str) -> dict[str, Any]:
    """Devuelve la cotización actual de un símbolo (precio, variación, rango del día y de 52 semanas, medias, etc.).

    Recibe el símbolo de Yahoo (acciones, forex 'EURUSD=X', índices '^GSPC',
    cripto 'BTC-USD', futuros 'GC=F'). Lee `fast_info` de yfinance, calcula la
    variación absoluta y porcentual contra el cierre anterior y omite los campos
    sin dato. Incluye la hora de consulta en UTC y el aviso de posible retraso.
    Resultado cacheado 30 segundos. Lanza ValueError si Yahoo no devuelve precio."""
    s = _simbolo(simbolo)

    def _fn() -> dict[str, Any]:
        """Lee `fast_info` del símbolo y arma la cotización; solo se ejecuta si la caché no tiene un valor vigente."""
        fi = yf.Ticker(s).fast_info
        precio = _leer(fi, "last_price")
        # Sin precio no hay cotización útil: se informa al modelo para que corrija el símbolo.
        if precio is None:
            raise ValueError(
                f"Yahoo no devolvió precio para '{s}'. Verifica el símbolo "
                "(ej. AAPL, EURUSD=X, ^GSPC, BTC-USD, GC=F) o reintenta en un momento."
            )
        previo = _leer(fi, "previous_close")
        variacion = variacion_porcentaje = None
        # La variación solo se calcula si hay un cierre anterior distinto de cero.
        if previo:
            variacion = _num(precio - previo)
            variacion_porcentaje = _num((precio / previo - 1) * 100, 2)

        return _sin_nulos(
            {
                "simbolo": s,
                "precio": precio,
                "cierre_anterior": previo,
                "variacion": variacion,
                "variacion_pct": variacion_porcentaje,
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


# TITULO HISTORICO

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
    """Resumen estadístico de TODO el rango + las últimas N velas (para no inundar el contexto).

    Recibe el símbolo, el periodo (p. ej. '3mo'; se ignora si hay `inicio`), el
    intervalo de las velas (p. ej. '1d', '1h') y, opcionalmente, un rango
    'AAAA-MM-DD' (`inicio`/`fin`). `ultimas_velas` (0-200) indica cuántas velas
    recientes se detallan. El resumen incluye número de velas, fechas extremas,
    cierre inicial y final, variación %, máximo y mínimo con sus fechas, volumen
    promedio y desviación estándar de los retornos por vela. Resultado
    cacheado 60 s (intradía) o 600 s (diario o mayor). Lanza ValueError si el
    intervalo, periodo o fechas son inválidos, o si Yahoo no devuelve datos."""
    s = _simbolo(simbolo)
    # Valida los parámetros antes de consultar: el intervalo siempre; el periodo solo si no hay fecha de inicio.
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
        """Descarga el histórico, calcula el resumen del rango y las últimas velas; solo se ejecuta si la caché no tiene un valor vigente."""
        ticker = yf.Ticker(s)
        # Con fecha de inicio se pide un rango explícito; si no, un periodo relativo a hoy.
        if inicio:
            tabla_datos = ticker.history(start=inicio, end=fin, interval=intervalo, auto_adjust=True)
        else:
            tabla_datos = ticker.history(period=periodo, interval=intervalo, auto_adjust=True)
        if tabla_datos is None or tabla_datos.empty:
            raise ValueError(
                f"Yahoo no devolvió datos para '{s}' con esos parámetros. Revisa el símbolo; "
                "los intervalos intradía solo tienen datos recientes (1m: 7 días, resto: ~60 días)."
            )
        # Descarta velas sin cierre, que distorsionarían los cálculos.
        tabla_datos = tabla_datos.dropna(subset=["Close"])

        cierres = tabla_datos["Close"]
        retornos = cierres.pct_change().dropna()
        primero, ultimo = cierres.iloc[0], cierres.iloc[-1]

        # Estadísticas de TODO el rango descargado (no solo de las velas detalladas).
        resumen = _sin_nulos(
            {
                "velas_totales": len(tabla_datos),
                "desde": _formatear_fecha(tabla_datos.index[0], intradia),
                "hasta": _formatear_fecha(tabla_datos.index[-1], intradia),
                "cierre_inicial": _num(primero),
                "cierre_final": _num(ultimo),
                "variacion_pct": _num((ultimo / primero - 1) * 100, 2) if primero else None,
                "maximo": _num(tabla_datos["High"].max()),
                "fecha_maximo": _formatear_fecha(tabla_datos["High"].idxmax(), intradia),
                "minimo": _num(tabla_datos["Low"].min()),
                "fecha_minimo": _formatear_fecha(tabla_datos["Low"].idxmin(), intradia),
                "volumen_promedio": _entero(tabla_datos["Volume"].mean()),
                "desv_estandar_retornos_por_vela_pct": _num(retornos.std() * 100, 3) if len(retornos) > 1 else None,
            }
        )
        # Solo las últimas n velas con OHLC y volumen, para no inundar el contexto del modelo.
        velas = [
            {
                "fecha": _formatear_fecha(indice, intradia),
                "apertura": _num(fila["Open"]),
                "maximo": _num(fila["High"]),
                "minimo": _num(fila["Low"]),
                "cierre": _num(fila["Close"]),
                "volumen": _entero(fila["Volume"]),
            }
            for indice, fila in tabla_datos.tail(n).iterrows()
        ]
        return {
            "simbolo": s,
            "intervalo": intervalo,
            "resumen_rango_completo": resumen,
            "ultimas_velas": velas,
            "aviso": AVISO_RETRASO,
        }

    # Los datos intradía cambian más rápido, por eso su caché es más corta.
    tiempo_vida = 60 if intradia else 600
    return _cacheado(f"historico:{s}:{periodo}:{intervalo}:{inicio}:{fin}:{n}", tiempo_vida, _fn)


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara mercado .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
