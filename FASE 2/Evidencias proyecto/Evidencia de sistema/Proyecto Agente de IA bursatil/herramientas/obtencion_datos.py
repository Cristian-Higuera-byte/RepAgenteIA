# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara obtencion_datos .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""
obtencion_datos.py
----------------
Módulo encargado de conectarse a Yahoo Finance mediante la biblioteca
'yfinance' y extraer información bursátil (precios históricos, datos
fundamentales, dividendos, etc.) para un ticker dado.

Es la capa de acceso a datos de mercado que usan `analisis.py` y las
herramientas del agente. Todas las funciones hacen llamadas de red; no
escriben en disco ni modifican estado de sesión.
"""

import pandas as pd  # type: ignore[import-untyped]
import yfinance as yf  # type: ignore[import-untyped]

# TITULO OBTENER DATOS HISTORICOS

def obtener_datos_historicos(ticker: str, periodo: str = "6mo", intervalo: str = "1d") -> pd.DataFrame:
    """
    Descarga el historial de precios de un activo desde Yahoo Finance.

    Parámetros:
        ticker (str): Símbolo bursátil, ej. "AAPL", "GOOGL", "SQM.SN".
        periodo (str): Rango de tiempo a consultar.
                       Ej: '1mo', '3mo', '6mo', '1y', '5y', 'max'.
        intervalo (str): Frecuencia de los datos.
                         Ej: '1d', '1wk', '1mo'.

    Retorna:
        pd.DataFrame: DataFrame con columnas Open, High, Low, Close,
                       Volume, Dividends, Stock Splits, indexado por fecha.
    """
    # Objeto yfinance del ticker y descarga del histórico pedido.
    activo = yf.Ticker(ticker)
    historico = activo.history(period=periodo, interval=intervalo)

    # Un DataFrame vacío indica ticker inexistente o sin datos.

    if historico.empty:
        raise ValueError(f"No se encontraron datos para el ticker '{ticker}'.")

    return historico

# TITULO OBTENER INFO GENERAL

def obtener_info_general(ticker: str) -> dict:
    """
    Obtiene información general/fundamental de la empresa
    (sector, capitalización de mercado, PER, etc.)

    Parámetros:
        ticker (str): Símbolo bursátil.

    Retorna:
        dict: Diccionario con los datos fundamentales disponibles.
    """
    activo = yf.Ticker(ticker)
    info = activo.info  # Puede tardar unos segundos (llamada a la API)

    # Se seleccionan solo los campos de interés y se renombran a claves en español.
    campos_relevantes = {
        "nombre": info.get("longName"),
        "sector": info.get("sector"),
        "industria": info.get("industry"),
        "precio_actual": info.get("currentPrice"),
        "capitalizacion_mercado": info.get("marketCap"),
        "per": info.get("trailingPE"),
        "dividend_yield": info.get("dividendYield"),
        "moneda": info.get("currency"),
    }
    return campos_relevantes

# TITULO OBTENER PRECIO EN FECHA

def obtener_precio_en_fecha(ticker: str, fecha: str) -> float:
    """
    Obtiene el precio de cierre de un activo en una fecha específica
    (o el día hábil más cercano si la fecha exacta no tiene datos).

    Parámetros:
        ticker (str): Símbolo bursátil.
        fecha (str): Fecha en formato 'YYYY-MM-DD'.

    Retorna:
        float: Precio de cierre más cercano a esa fecha.
    """
    activo = yf.Ticker(ticker)
    fecha_dt = pd.to_datetime(fecha)
    # Se pide una ventana de +-5 días para asegurar encontrar un día hábil
    inicio = (fecha_dt - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
    fin = (fecha_dt + pd.Timedelta(days=5)).strftime("%Y-%m-%d")

    # Descarga la ventana de +-5 días alrededor de la fecha.
    historico = activo.history(start=inicio, end=fin)
    if historico.empty:
        raise ValueError(f"No hay datos disponibles cerca de la fecha {fecha} para {ticker}.")

    # Toma el dato más cercano a la fecha solicitada
    historico.index = historico.index.tz_localize(None)
    indice_cercano = historico.index.get_indexer([fecha_dt], method="nearest")[0]
    return round(historico.iloc[indice_cercano]["Close"], 2)

# TITULO OBTENER NOTICIAS ACTIVO

def obtener_noticias_activo(ticker: str, limite: int = 5) -> list:
    """
    Obtiene las noticias y titulares recientes de un activo utilizando yfinance.

    Parámetros:
        ticker (str): Símbolo bursátil (ej. AAPL, TSLA).
        limite (int): Cantidad máxima de noticias a retornar.

    Retorna:
        list: Lista de diccionarios con título, fuente y enlace de cada noticia.
    """
    # Cualquier error de red/estructura se devuelve como un elemento con la clave "error".
    try:
        ticket = yf.Ticker(ticker)
        noticias = ticket.news

        if not noticias:
            return [{"titulo": "No hay noticias recientes disponibles para este ticker."}]

        # Se recorren solo las primeras `limite` noticias.
        resultados = []
        for elemento in noticias[:limite]:
            # yfinance maneja la estructura de diccionarios (puede variar según la versión)
            contenido_noticia = elemento.get("content", elemento)

            titulo = contenido_noticia.get("title", "Sin título")
            publisher = contenido_noticia.get("publisher", "Desconocido")

            # Extraer enlace si está disponible
            enlace_obj = contenido_noticia.get("clickThroughUrl", {})
            enlace = enlace_obj.get("url", "#") if isinstance(enlace_obj, dict) else "#"

            resultados.append({
                "titulo": titulo,
                "fuente": publisher,
                "enlace": enlace
            })

        return resultados
    except Exception as e:
        return [{"error": f"No se pudieron obtener noticias para {ticker}: {str(e)}"}]

# TITULO OBTENER INDICADORES MACRO

def obtener_indicadores_macro() -> dict:
    """
    Obtiene los principales indicadores macroeconómicos globales utilizando proxies de mercado en yfinance.

    Retorna:
        dict: Valores actuales del Bono del Tesoro (Tasas), Oro (Inflación/Refugio), y Petróleo (Energía).
    """
    # Símbolos de Yahoo usados como proxy -> descripción legible.
    indicadores = {
        "^TNX": "Bonos del Tesoro 10 Años (Tasas de Interés)",
        "GC=F": "Oro (Refugio / Inflación)",
        "CL=F": "Petróleo Crudo (Costos Energéticos)"
    }

    resultados_macro = {}

    try:
        # Para cada proxy: último cierre y variación frente al cierre previo.
        for ticker, descripcion in indicadores.items():
            ticket = yf.Ticker(ticker)
            historial = ticket.history(period="5d")
            if not historial.empty:
                precio_actual = float(historial["Close"].iloc[-1])
                precio_anterior = float(historial["Close"].iloc[-2]) if len(historial) > 1 else precio_actual
                variacion_porcentaje = ((precio_actual - precio_anterior) / precio_anterior) * 100

                resultados_macro[ticker] = {
                    "nombre": descripcion,
                    "valor_actual": round(precio_actual, 2),
                    "variacion_diaria_pct": round(variacion_porcentaje, 2)
                }
            else:
                resultados_macro[ticker] = {"nombre": descripcion, "error": "Sin datos recientes"}

        return resultados_macro
    except Exception as e:
        return {"error": f"No se pudieron obtener los indicadores macroeconómicos: {str(e)}"}

if __name__ == "__main__":
    # Prueba rápida del módulo (solo al ejecutarlo directamente, no al importarlo)
    datos = obtener_datos_historicos("AAPL", periodo="1mo")
    print(datos.tail())

    info = obtener_info_general("AAPL")
    print(info)


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara obtencion_datos .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
