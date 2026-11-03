# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------- INICIO Piña y Jara gestor_visualizacion .PY -----------------------------
# -------------------------------------------------------------------------------------------------------

"""
gestor_visualizacion.py
--------------
Módulo ampliado para generar gráficos financieros (líneas y barras) y exportarlos localmente.

Usa yfinance para los datos y matplotlib para dibujar; cada función guarda un
PNG (300 dpi) en la carpeta `outputs/` y devuelve un mensaje de texto con la
ruta o el error. Ofrece tres gráficos: evolución de precio, barras comparativas
de rendimiento y proyección lineal de tendencia.
"""
import os
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
import yfinance as yf  # type: ignore[import-untyped]

# Carpeta (relativa a la ejecución) donde se guardan los PNG generados
OUTPUT_DIR = "outputs"


# TITULO GENERAR GRAFICO RENDIMIENTO

def generar_grafico_rendimiento(ticker: str, periodo: str = "6mo") -> str:
    """
    Genera y guarda un gráfico de líneas con la evolución del precio de cierre de un activo.

    Parámetros:
        ticker (str): Símbolo bursátil (se normaliza a mayúsculas).
        periodo (str): Período de yfinance (ej. "1mo", "6mo", "1y").

    Devuelve un mensaje con la ruta del PNG guardado o con el error/ausencia de
    datos. Efectos secundarios: consulta de red, crea `outputs/` y escribe el
    archivo `grafico_<ticker>_<periodo>.png`.
    """
    # Asegura que exista la carpeta de salida y normaliza el ticker.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    t = ticker.upper().strip()
    try:
        # Descarga el histórico de precios.
        ticket = yf.Ticker(t)
        historial = ticket.history(period=periodo)
        if historial.empty:
            return f"❌ No hay datos históricos suficientes para graficar {t} en el período {periodo}."
        # Dibuja la línea de cierre con título, ejes y cuadrícula.
        plt.figure(figsize=(10, 5))
        plt.plot(historial.index, historial["Close"], label=f"Precio Cierre ({t})", color="#1f77b4", linewidth=2)
        plt.title(f"Evolución de Precio: {t} (Período: {periodo})", fontsize=14, fontweight="bold")
        plt.xlabel("Fecha", fontsize=10)
        plt.ylabel("Precio (USD)", fontsize=10)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        # Guarda la imagen y libera la figura para no acumular memoria.
        plt.tight_layout()
        ruta_archivo = os.path.join(OUTPUT_DIR, f"grafico_{t}_{periodo}.png")
        plt.savefig(ruta_archivo, dpi=300)
        plt.close()
        return f"✅ Gráfico de líneas generado exitosamente y guardado en: {ruta_archivo}"
    except Exception as e:
        return f"❌ Error generando el gráfico para {t}: {str(e)}"


# TITULO GENERAR GRAFICO BARRAS COMPARATIVO

def generar_grafico_barras_comparativo(tickers: list, periodo: str = "1mo") -> str:
    """
    Genera y guarda un gráfico de barras comparativo con el rendimiento porcentual
    de una lista de activos en un período determinado.

    Parámetros:
        tickers (list): Lista de símbolos bursátiles (ej. ["TSLA", "AAPL", "MSFT", "NVDA"]).
        periodo (str): Período de análisis (ej. "1mo", "6mo", "1y").

    El rendimiento es (último cierre - primer cierre) / primer cierre * 100. Los
    tickers sin datos o que fallan se omiten en silencio. Devuelve un mensaje con
    la ruta del PNG o un error si ningún ticker tuvo datos. Efectos secundarios:
    consultas de red y escritura de `outputs/grafico_barras_comparativo_<periodo>.png`.
    """
    # Asegura la carpeta de salida y prepara el diccionario ticker -> rendimiento.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rendimientos = {}
    # Calcula el rendimiento porcentual de cada activo.
    for ticker in tickers:
        t = ticker.upper().strip()
        try:
            ticket = yf.Ticker(t)
            historial = ticket.history(period=periodo)
            if not historial.empty:
                precio_inicio = float(historial["Close"].iloc[0])
                precio_fin = float(historial["Close"].iloc[-1])
                rendimiento_porcentaje = ((precio_fin - precio_inicio) / precio_inicio) * 100
                rendimientos[t] = round(rendimiento_porcentaje, 2)
        except Exception:
            continue
    if not rendimientos:
        return "❌ No se pudieron obtener datos válidos para generar el gráfico de barras comparativo."
    # Crear gráfico de barras
    plt.figure(figsize=(9, 5))
    activos = list(rendimientos.keys())
    valores = list(rendimientos.values())
    # Colores dinámicos: verde si es positivo, rojo si es negativo
    colores = ['#2ca02c' if v >= 0 else '#d62728' for v in valores]
    barras = plt.bar(activos, valores, color=colores, alpha=0.85, width=0.5)
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.title(f"Comparativa de Rendimiento Porcentual ({periodo})", fontsize=14, fontweight="bold")
    plt.xlabel("Activos", fontsize=10)
    plt.ylabel("Rendimiento (%)", fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    # Añadir las etiquetas de valor sobre cada barra
    for barra in barras:
        altura = barra.get_height()
        plt.text(
            barra.get_x() + barra.get_width()/2.,
            altura + (0.5 if altura >= 0 else -1.5),
            f"{altura}%",
            ha='center', va='bottom' if altura >= 0 else 'top',
            fontsize=9, fontweight='bold'
        )
    # Guarda la imagen y cierra la figura.
    plt.tight_layout()
    ruta_archivo = os.path.join(OUTPUT_DIR, f"grafico_barras_comparativo_{periodo}.png")
    plt.savefig(ruta_archivo, dpi=300)
    plt.close()
    return f"✅ Gráfico de barras comparativo generado exitosamente y guardado en: {ruta_archivo}"


# TITULO GENERAR GRAFICO PREDICTIVO

def generar_grafico_predictivo(ticker: str, periodo: str = "6mo", dias_futuros: int = 30) -> str:
    """
    Genera un gráfico que muestra el histórico de precios de un activo y añade
    una proyección de tendencia lineal estimada para los próximos días.

    Parámetros:
        ticker (str): Símbolo bursátil (ej. TSLA, AAPL).
        periodo (str): Período histórico de base (ej. "6mo", "1y").
        dias_futuros (int): Cantidad de días a proyectar hacia adelante.

    Ajusta una regresión lineal (np.polyfit grado 1) sobre los cierres y la
    extiende `dias_futuros` días calendario; la banda sombreada es +/-1.96
    desviaciones estándar de los residuos (aproximación visual, no un intervalo
    de predicción estadístico riguroso). Requiere al menos 30 datos. Devuelve la
    ruta del PNG y un resumen (precio actual, proyectado y variación %), o un
    mensaje de error. Efectos secundarios: red y escritura de
    `outputs/grafico_predictivo_<ticker>.png`.
    """
    # Prepara carpeta de salida y ticker normalizado.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    t = ticker.upper().strip()
    try:
        ticket = yf.Ticker(t)
        historial = ticket.history(period=periodo)
        if historial.empty or len(historial) < 30:
            return f"❌ No hay suficientes datos históricos para proyectar una tendencia para {t}."
        # Datos históricos
        fechas_historial = historial.index
        precios_historial = historial["Close"].values
        # Crear eje numérico para la regresión lineal
        x_historial = np.arange(len(precios_historial))
        y_historial = precios_historial
        # Calcular regresión lineal (tendencia de fondo)
        m, b = np.polyfit(x_historial, y_historial, 1)
        # Generar fechas y precios futuros proyectados
        ultima_fecha = fechas_historial[-1]
        fechas_futuras = [ultima_fecha + timedelta(days=i) for i in range(1, dias_futuros + 1)]
        x_futuro = np.arange(len(x_historial), len(x_historial) + dias_futuros)
        y_futuro = m * x_futuro + b
        # Crear el gráfico
        plt.figure(figsize=(11, 6))
        # Graficar histórico y tendencia proyectada
        plt.plot(fechas_historial, y_historial, label=f"Precio Histórico ({t})", color="#1f77b4", linewidth=2)
        plt.plot(fechas_futuras, y_futuro, label=f"Tendencia Estimada ({dias_futuros} días)", color="#ff7f0e", linestyle="--", linewidth=2)
        # Intervalo de confianza visual básico (banda alrededor de la tendencia estimada)
        desviacion = np.std(y_historial - (m * x_historial + b))
        plt.fill_between(
            fechas_futuras,
            y_futuro - (1.96 * desviacion),
            y_futuro + (1.96 * desviacion),
            color="#ff7f0e", alpha=0.15, label="Banda de Estimación (95%)"
        )
        plt.title(f"Proyección y Estimación de Precio: {t} (Modelo de Tendencia)", fontsize=14, fontweight="bold")
        plt.xlabel("Fecha", fontsize=10)
        plt.ylabel("Precio Estimado (USD)", fontsize=10)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(loc="upper left")
        # Guarda la imagen y cierra la figura.
        plt.tight_layout()
        ruta_archivo = os.path.join(OUTPUT_DIR, f"grafico_predictivo_{t}.png")
        plt.savefig(ruta_archivo, dpi=300)
        plt.close()
        # Calcula el resumen numérico de la proyección.
        precio_final_estimado = y_futuro[-1]
        variacion_estimada = ((precio_final_estimado - y_historial[-1]) / y_historial[-1]) * 100
        return (
            f"✅ Gráfico predictivo generado con éxito y guardado en: {ruta_archivo}\n"
            f"📊 Resumen de la proyección a {dias_futuros} días para {t}:\n"
            f"• Precio actual de cierre: ${y_historial[-1]:.2f}\n"
            f"• Precio proyectado estimado: ${precio_final_estimado:.2f}\n"
            f"• Variación estimada de tendencia: {variacion_estimada:+.2f}%"
        )
    except Exception as e:
        return f"❌ Error generando la proyección predictiva para {t}: {str(e)}"


# -------------------------------------------------------------------------------------------------------
# ------------------------------- FIN Piña y Jara gestor_visualizacion .PY ------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
