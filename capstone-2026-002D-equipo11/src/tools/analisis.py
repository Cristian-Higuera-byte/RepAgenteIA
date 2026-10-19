# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara analisis .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
analisis.py
------------
Contiene funciones de análisis técnico y estadístico básico sobre
los datos históricos obtenidos con obtencion_datos.py (Yahoo Finance).

Incluye indicadores (media móvil, RSI, MACD, volatilidad, soportes y
resistencias) y comparativas entre fechas o entre varios activos. Varias de
estas funciones se exponen al agente como herramientas; sus descripciones y
parámetros para el modelo viven en `esquemas.json`, no en estos docstrings.
Todas descargan datos por red (yfinance) y no tocan disco ni estado de sesión.
"""

import pandas as pd  # type: ignore[import-untyped]
import yfinance as yf  # type: ignore[import-untyped]

from tools.obtencion_datos import obtener_datos_historicos, obtener_precio_en_fecha

def calcular_media_movil(datos: pd.DataFrame, ventana: int = 20) -> pd.Series:
    """
    Calcula la media móvil simple (SMA) sobre el precio de cierre.

    Parámetros:
        datos (pd.DataFrame): DataFrame con columna 'Close'.
        ventana (int): Número de periodos para la media móvil.

    Retorna:
        pd.Series: Serie con la media móvil calculada.
    """
    # Media móvil simple: promedio de los últimos `ventana` cierres.
    return datos["Close"].rolling(window=ventana).mean()

def calcular_rendimiento(datos: pd.DataFrame) -> pd.Series:
    """
    Calcula el rendimiento porcentual diario del activo.

    Parámetros:
        datos (pd.DataFrame): DataFrame con columna 'Close'.

    Retorna:
        pd.Series: Rendimientos diarios en porcentaje.
    """
    # Cambio porcentual de cada cierre respecto al anterior, expresado en %.
    return datos["Close"].pct_change() * 100

def calcular_volatilidad(datos: pd.DataFrame, ventana: int = 20) -> float:
    """
    Calcula la volatilidad histórica (desviación estándar de los
    rendimientos diarios) anualizada.

    Parámetros:
        datos (pd.DataFrame): DataFrame con columna 'Close'.
        ventana (int): Periodos a considerar para el cálculo.

    Retorna:
        float: Volatilidad anualizada en porcentaje.
    """
    # Toma solo los rendimientos de la ventana reciente.
    rendimientos = calcular_rendimiento(datos).tail(ventana)
    volatilidad_diaria = rendimientos.std()
    volatilidad_anualizada = volatilidad_diaria * (252 ** 0.5)  # 252 días hábiles/año
    return round(volatilidad_anualizada, 2)

def resumen_basico(datos: pd.DataFrame) -> dict:
    """
    Genera un resumen rápido con los principales indicadores.

    Parámetros:
        datos (pd.DataFrame): DataFrame con datos históricos OHLCV.

    Retorna:
        dict: Resumen con precio actual, SMA20, SMA50 y volatilidad.
    """
    # Último cierre, SMA20, SMA50 (solo si hay 50 datos) y volatilidad anualizada.
    return {
        "precio_actual": round(datos["Close"].iloc[-1], 2),
        "sma_20": round(calcular_media_movil(datos, 20).iloc[-1], 2),
        "sma_50": round(calcular_media_movil(datos, 50).iloc[-1], 2) if len(datos) >= 50 else None,
        "volatilidad_anualizada_%": calcular_volatilidad(datos),
    }

def comparar_precio_historico(ticker: str, fecha: str) -> dict:
    """
    Compara el precio actual de un activo contra su precio en una
    fecha pasada específica.

    Parámetros:
        ticker (str): Símbolo bursátil.
        fecha (str): Fecha de referencia en formato 'YYYY-MM-DD'.

    Retorna:
        dict: precio actual, precio en la fecha, diferencia % y absoluta.
    """
    # Precio actual = último cierre de los últimos 5 días; el histórico se pide aparte.
    datos_recientes = obtener_datos_historicos(ticker, periodo="5d")
    precio_actual = round(datos_recientes["Close"].iloc[-1], 2)
    precio_historico = obtener_precio_en_fecha(ticker, fecha)

    # Diferencia en dinero y en porcentaje respecto al precio de la fecha pasada.
    diferencia_absoluta = round(precio_actual - precio_historico, 2)
    diferencia_pct = round((diferencia_absoluta / precio_historico) * 100, 2)

    return {
        "ticker": ticker,
        "precio_actual": precio_actual,
        "precio_en_fecha": precio_historico,
        "fecha_referencia": fecha,
        "diferencia_absoluta": diferencia_absoluta,
        "diferencia_%": diferencia_pct,
    }

def calcular_rendimiento_periodo(ticker: str, fecha_inicio: str, fecha_fin: str) -> dict:
    """
    Calcula el rendimiento porcentual de un activo entre dos fechas.

    Parámetros:
        ticker (str): Símbolo bursátil.
        fecha_inicio (str): Fecha de inicio 'YYYY-MM-DD'.
        fecha_fin (str): Fecha de fin 'YYYY-MM-DD'.

    Retorna:
        dict: precios de inicio/fin, rendimiento % y días transcurridos.
    """
    # Precios de cierre más cercanos a cada fecha (consulta a Yahoo Finance).
    precio_inicio = obtener_precio_en_fecha(ticker, fecha_inicio)
    precio_fin = obtener_precio_en_fecha(ticker, fecha_fin)

    # Rendimiento % entre ambas fechas y días calendario transcurridos.
    rendimiento_pct = round(((precio_fin - precio_inicio) / precio_inicio) * 100, 2)
    dias = (pd.to_datetime(fecha_fin) - pd.to_datetime(fecha_inicio)).days

    return {
        "ticker": ticker,
        "precio_inicio": precio_inicio,
        "precio_fin": precio_fin,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "dias_transcurridos": dias,
        "rendimiento_%": rendimiento_pct,
    }

def obtener_volatilidad(ticker: str, periodo: str = "6mo", ventana: int = 20) -> dict:
    """
    Calcula la volatilidad histórica anualizada de un activo, como
    herramienta independiente (no solo como parte del resumen general).

    Parámetros:
        ticker (str): Símbolo bursátil.
        periodo (str): Rango de datos a descargar. Ej: '1mo', '3mo', '6mo', '1y'.
        ventana (int): Número de días recientes a considerar para el cálculo.

    Retorna:
        dict: ticker, volatilidad anualizada (%) y la ventana usada.
    """
    # Importación local redundante con la del módulo; se conserva tal cual.
    from tools.obtencion_datos import obtener_datos_historicos

    # Descarga el histórico del periodo pedido.
    datos = obtener_datos_historicos(ticker, periodo=periodo)

    # Sin datos suficientes la desviación estándar no es confiable: se aborta con error.
    if len(datos) < ventana:
        raise ValueError(
            f"No hay suficientes datos ({len(datos)} días) para calcular "
            f"volatilidad con ventana de {ventana} días. Prueba un 'periodo' mayor."
        )

    volatilidad = calcular_volatilidad(datos, ventana=ventana)

    return {
        "ticker": ticker,
        "volatilidad_anualizada_%": volatilidad,
        "ventana_dias": ventana,
        "periodo_consultado": periodo,
    }

def calcular_rsi(datos: pd.DataFrame, ventana: int = 14) -> float:
    """
    Calcula el Índice de Fuerza Relativa (RSI) actual del activo.

    Parámetros:
        datos (pd.DataFrame): DataFrame con datos históricos OHLCV.
        ventana (int): Periodos para el cálculo del RSI (por defecto 14).

    Retorna:
        float: Valor actual del RSI redondeado a 2 decimales.
    """
    # Variación diaria de cierre; se separan ganancias y pérdidas y se promedian en la ventana.
    delta = datos["Close"].diff()
    ganancia = (delta.where(delta > 0, 0)).rolling(window=ventana).mean()
    perdida = (-delta.where(delta < 0, 0)).rolling(window=ventana).mean()

    # Fuerza relativa y fórmula clásica del RSI (0-100).
    rs = ganancia / perdida
    rsi = 100 - (100 / (1 + rs))

    # Se devuelve el último valor; si es NaN faltan datos.
    valor_actual = rsi.iloc[-1]
    if pd.isna(valor_actual):
        raise ValueError("No hay suficientes datos para calcular el RSI.")
    return round(float(valor_actual), 2)

def calcular_macd(datos: pd.DataFrame, span_rapido: int = 12, span_lento: int = 26, señal: int = 9) -> dict:
    """
    Calcula el indicador MACD (Moving Average Convergence Divergence).

    Parámetros:
        datos (pd.DataFrame): DataFrame con datos históricos OHLCV.
        span_rapido (int): Media móvil exponencial rápida (por defecto 12).
        span_lento (int): Media móvil exponencial lenta (por defecto 26).
        señal (int): Línea de señal (por defecto 9).

    Retorna:
        dict: Valores actuales de la línea MACD, la línea de señal y el histograma.
    """
    # Medias exponenciales rápida y lenta del cierre.
    ema_rapida = datos["Close"].ewm(span=span_rapido, adjust=False).mean()
    ema_lenta = datos["Close"].ewm(span=span_lento, adjust=False).mean()

    # MACD = rápida - lenta; señal = EMA del MACD; histograma = diferencia entre ambos.
    linea_macd = ema_rapida - ema_lenta
    linea_señal = linea_macd.ewm(span=señal, adjust=False).mean()
    histograma = linea_macd - linea_señal

    return {
        "macd": round(float(linea_macd.iloc[-1]), 2),
        "señal": round(float(linea_señal.iloc[-1]), 2),
        "histograma": round(float(histograma.iloc[-1]), 2),
    }

def calcular_soportes_resistencias(datos: pd.DataFrame, ventana: int = 20) -> dict:
    """
    Calcula niveles aproximados de soporte y resistencia basados en los
    mínimos y máximos locales de un período reciente.

    Parámetros:
        datos (pd.DataFrame): DataFrame con datos históricos OHLCV.
        ventana (int): Días recientes a evaluar.

    Retorna:
        dict: Soporte y resistencia estimados.
    """
    # Soporte = mínimo de la ventana; resistencia = máximo de la ventana.
    recientes = datos.tail(ventana)
    soporte = round(float(recientes["Low"].min()), 2)
    resistencia = round(float(recientes["High"].max()), 2)
    precio_actual = round(float(datos["Close"].iloc[-1]), 2)

    return {
        "precio_actual": precio_actual,
        "soporte_estimado": soporte,
        "resistencia_estimada": resistencia,
        "ventana_evaluada_dias": ventana,
    }

def comparar_multi_activos(tickers: list, periodo: str = "1mo") -> dict:
    """
    Compara el precio actual y el rendimiento porcentual de una lista de tickers en un período dado.

    Parámetros:
        tickers (list): Lista de símbolos bursátiles (ej. ["TSLA", "AAPL", "NVDA"]).
        periodo (str): Período de análisis (ej. "1mo", "6mo", "1y").

    Retorna:
        dict: Por ticker (en mayúsculas), precio actual, rendimiento % y estado, o un
        mensaje de error si no hubo datos o la descarga falló (no lanza excepciones).
    """
    resultados = {}

    # Un fallo en un ticker no interrumpe a los demás.
    for ticker in tickers:
        t = ticker.upper().strip()
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period=periodo)
            if not hist.empty:
                # Rendimiento entre el primer y el último cierre del periodo.
                precio_inicio = float(hist["Close"].iloc[0])
                precio_fin = float(hist["Close"].iloc[-1])
                rendimiento_pct = ((precio_fin - precio_inicio) / precio_inicio) * 100

                resultados[t] = {
                    "precio_actual": round(precio_fin, 2),
                    "rendimiento_pct": round(rendimiento_pct, 2),
                    "estado": "Éxito"
                }
            else:
                resultados[t] = {"error": "No hay datos históricos disponibles para el período."}
        except Exception as e:
            resultados[t] = {"error": str(e)}

    return resultados

def screening_rapido_mercado(tickers: list) -> str:
    """
    Realiza un barrido o screening básico sobre una lista de activos para evaluar su tendencia actual.

    Para cada ticker descarga el último mes, calcula el cambio entre el primer y el
    último cierre y lo etiqueta como alcista o bajista.

    Retorna:
        str: Reporte de texto con una línea por activo (los que fallan indican error;
        los que tienen menos de 2 datos se omiten sin mensaje).
    """
    reporte = f"--- SCREENING DE MERCADO ({len(tickers)} activos analizados) ---\n"

    for ticker in tickers:
        t = ticker.upper().strip()
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="1mo")
            if len(hist) >= 2:
                actual = float(hist["Close"].iloc[-1])
                previo_mes = float(hist["Close"].iloc[0])
                # Cambio mensual en % y etiqueta de tendencia.
                cambio = ((actual - previo_mes) / previo_mes) * 100

                tendencia = "📈 Alcista" if cambio > 0 else "📉 Bajista"
                reporte += f"• {t}: Actual ${actual:.2f} | Cambio mensual: {cambio:+.2f}% ({tendencia})\n"
        except Exception:
            reporte += f"• {t}: Error al procesar datos.\n"

    return reporte


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara analisis .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
