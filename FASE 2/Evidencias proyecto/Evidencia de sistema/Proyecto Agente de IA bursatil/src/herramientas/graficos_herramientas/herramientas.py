# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara herramientas .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Herramientas registradas para el agente de gráficos (los esquemas viven en esquemas.json).

Registra ``generar_grafico_financiero``, que dibuja con matplotlib gráficos
de velas, líneas, barras OHLC o comparativos de rendimiento, y guarda la
imagen PNG en disco para que el chat la muestre.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from database.scripts.fuentes import mt5_fuentes as mt5_fuente
from database.scripts.fuentes import yfinance_fuente as yf_fuente
from herramientas import analisis_herramientas
from herramientas.base import herramienta
from herramientas.graficos_herramientas.auxiliares import (
    OUTPUT_DIR,
    TIPOS_VALIDOS,
    _dibujar_velas,
    _etiqueta_fecha,
    _mapear_simbolo_yf,
)

# pyplot se importa DESPUÉS de auxiliares: ahí se fija el backend no interactivo (matplotlib.use("Agg")).
import matplotlib.pyplot as plt  # noqa: E402


@herramienta(
    descripcion=(
        "Genera gráficos bursátiles en alta resolución y los muestra al usuario en el chat. "
        "Tipos: 'velas' (velas japonesas + EMA20/SMA50 + RSI 14), 'lineas' (cierres con EMA/SMA + RSI), "
        "'barras_ohlc' (barras tradicionales + EMA/SMA + RSI) y 'comparativo' (rendimiento % relativo "
        "entre varios activos; exige 'comparar_con'). No incluye volumen ni MACD. "
        "El gráfico se muestra solo: no menciones rutas ni enlaces a la imagen en tu respuesta."
    ),
    parametros={
        "simbolo": {
            "type": "string",
            "description": "Símbolo principal (ej. 'EURUSD', 'GOLD', 'USDCLP', 'AAPL').",
        },
        "tipo_grafico": {
            "type": "string",
            "enum": list(TIPOS_VALIDOS),
            "description": "Tipo de gráfico bursátil a generar. Por defecto 'velas'.",
        },
        "timeframe": {
            "type": "string",
            "enum": list(mt5_fuente.TIMEFRAMES),
            "description": "Temporalidad para las velas (M1, M5, M15, M30, H1, H4, D1). Por defecto 'H1'.",
        },
        "cantidad_velas": {
            "type": "integer",
            "description": "Número de velas a graficar (ej. 50 a 200). Por defecto 80.",
        },
        "comparar_con": {
            "type": "string",
            "description": "Solo para 'comparativo': símbolos adicionales separados por coma (ej. 'GBPUSD,USDCLP').",
        },
    },
    requeridos=["simbolo"],
    nombre="generar_grafico_financiero",
)
def generar_grafico_financiero(
    simbolo: str,
    tipo_grafico: str = "velas",
    timeframe: str = "H1",
    cantidad_velas: int = 80,
    comparar_con: str | None = None,
) -> dict[str, Any]:
    """Genera un gráfico bursátil PNG y devuelve los metadatos del archivo.

    Recibe el símbolo principal, el tipo de gráfico (velas, lineas,
    barras_ohlc o comparativo), la temporalidad, la cantidad de velas (se
    limita entre 20 y 300) y, solo para el comparativo, los símbolos extra
    separados por coma. Obtiene las velas de MetaTrader 5 y, si no hay datos,
    recurre a velas diarias de Yahoo Finance. Dibuja medias móviles EMA20/SMA50
    y un panel RSI(14) (salvo en el comparativo, que muestra rendimiento % relativo).

    Efectos secundarios: consulta MT5 y/o yfinance y escribe un PNG en
    ``OUTPUT_DIR``. Devuelve un diccionario con la fuente, el símbolo, el
    tipo, la temporalidad real, las velas graficadas, el último cierre, la
    ruta del archivo y un mensaje; o ``{"error": ...}`` si algo falla.
    """
    # Normaliza el símbolo y acota la cantidad de velas a un rango razonable.
    simbolo_clean = simbolo.strip().upper()
    n_velas = max(20, min(int(cantidad_velas), 300))

    # Valida el tipo de gráfico y los requisitos del comparativo.
    tipo_grafico = (tipo_grafico or "velas").strip().lower()
    if tipo_grafico not in TIPOS_VALIDOS:
        return {"error": f"tipo_grafico '{tipo_grafico}' no válido. Opciones: {', '.join(TIPOS_VALIDOS)}."}
    if tipo_grafico == "comparativo" and not (comparar_con or "").strip():
        return {"error": "El gráfico 'comparativo' requiere 'comparar_con' (ej. 'GBPUSD,USDCLP')."}

    # Obtener velas desde MT5 o YFinance
    # velas_data: lista de velas OHLC; tf_real: temporalidad realmente usada.
    velas_data: list[dict[str, Any]] = []
    tf_real = timeframe
    fuente_datos = "MetaTrader 5"
    try:
        mt5_res = mt5_fuente.velas(simbolo=simbolo_clean, timeframe=timeframe, cantidad=n_velas, ultimas_velas=n_velas)
        velas_data = mt5_res.get("ultimas_velas", [])
    except Exception:
        pass

    # Respaldo: si MT5 no entregó velas, usa Yahoo Finance.
    if not velas_data:
        try:
            yf_sym = _mapear_simbolo_yf(simbolo_clean)
            yf_res = yf_fuente.historico(simbolo=yf_sym, periodo="1mo", intervalo="1d", ultimas_velas=n_velas)
            for v in yf_res.get("ultimas_velas", []):
                velas_data.append({
                    "time": v["fecha"],
                    "open": v["apertura"],
                    "high": v["maximo"],
                    "low": v["minimo"],
                    "close": v["cierre"],
                    "tick_volume": v["volumen"] or 0,
                })
            # Respaldo: yfinance entrega velas diarias, sin importar el timeframe pedido.
            tf_real = "D1"
            fuente_datos = "Yahoo Finance (velas diarias)"
        except Exception as e:
            return {"error": f"No se pudieron obtener datos históricos para graficar {simbolo_clean}: {e}"}

    if not velas_data:
        return {"error": f"Sin datos disponibles para graficar {simbolo_clean}."}

    # Configuración de Estilo Oscuro Institucional
    # Crea la figura y define el nombre único del archivo (símbolo, tipo y marca de tiempo).
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(12, 7), dpi=120)
    fig.patch.set_facecolor("#12141D")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chart_{simbolo_clean}_{tipo_grafico}_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # ──────────────────────────────────────────────────────────
    # 1. Gráfico Comparativo de Rendimiento % Relativo
    # ──────────────────────────────────────────────────────────
    if tipo_grafico == "comparativo":
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1A1D29")

        # Pide a MT5 las velas de cada activo y normaliza cada serie a base 0 %.
        activos = [simbolo_clean] + [s.strip().upper() for s in (comparar_con or "").split(",") if s.strip()]
        graficados: list[str] = []
        for act in activos:
            try:
                data_act = mt5_fuente.velas(simbolo=act, timeframe=timeframe, cantidad=n_velas, ultimas_velas=n_velas)
                cierres_act = [v["close"] for v in data_act.get("ultimas_velas", []) if v.get("close")]
                if cierres_act:
                    base = cierres_act[0]
                    rend_pct = [((c / base) - 1.0) * 100.0 for c in cierres_act]
                    ax.plot(rend_pct, label=f"{act} (%)", linewidth=2.0)
                    graficados.append(act)
            except Exception:
                continue

        # Un comparativo necesita al menos dos activos con datos.
        if len(graficados) < 2:
            plt.close(fig)
            return {
                "error": (
                    "No se pudo armar el comparativo: solo hubo datos de MT5 para "
                    f"{', '.join(graficados) or 'ningún activo'} (de {', '.join(activos)})."
                )
            }

        ax.axhline(0, color="#888888", linestyle="--", alpha=0.6)
        ax.set_title(f"Rendimiento Relativo % ({', '.join(graficados)}) - {timeframe}", color="#FFFFFF", fontsize=14, pad=15)
        ax.set_xlabel("Velas", color="#CCCCCC")
        ax.set_ylabel("Variación Porcentual (%)", color="#CCCCCC")
        ax.legend(loc="upper left")
        ax.grid(True, color="#2A2E3D", linestyle=":", alpha=0.7)

    # ──────────────────────────────────────────────────────────
    # 2. Gráfico de Velas / Barras OHLC / Líneas con Indicadores
    # ──────────────────────────────────────────────────────────
    else:
        # Dos paneles: precio (3/4 de la altura) y RSI (1/4), con el eje X compartido.
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.15)
        ax_main = fig.add_subplot(gs[0])
        ax_sub = fig.add_subplot(gs[1], sharex=ax_main)

        ax_main.set_facecolor("#1A1D29")
        ax_sub.set_facecolor("#1A1D29")

        # Series auxiliares: cierres, etiquetas de fecha e índices del eje X.
        cierres = [v["close"] for v in velas_data]
        fechas_str = [_etiqueta_fecha(v.get("time", i), tf_real) for i, v in enumerate(velas_data)]
        indices = list(range(len(velas_data)))

        # Dibuja la serie principal según el tipo elegido.
        if tipo_grafico == "velas":
            _dibujar_velas(ax_main, velas_data)
        elif tipo_grafico == "lineas":
            ax_main.plot(indices, cierres, color="#00B0FF", linewidth=2.0, label="Precio Cierre")
            ax_main.fill_between(indices, cierres, min(cierres), color="#00B0FF", alpha=0.15)
        elif tipo_grafico == "barras_ohlc":
            # Barra OHLC: línea vertical, marca de apertura a la izquierda y de cierre a la derecha.
            for i, v in enumerate(velas_data):
                color = "#00B0FF" if v["close"] >= v["open"] else "#FF5252"
                ax_main.plot([i, i], [v["low"], v["high"]], color=color, linewidth=1.2)
                ax_main.plot([i - 0.2, i], [v["open"], v["open"]], color=color, linewidth=1.2)
                ax_main.plot([i, i + 0.2], [v["close"], v["close"]], color=color, linewidth=1.2)

        # Superposición de Medias Móviles (EMA20 y SMA50)
        if len(cierres) >= 20:
            ema20 = analisis_herramientas._ema_serie(cierres, 20)
            ax_main.plot(indices[-len(ema20):], ema20, color="#FFB300", linewidth=1.3, label="EMA 20")
        if len(cierres) >= 50:
            sma50 = [analisis_herramientas._sma(cierres[:i + 1], 50) for i in range(49, len(cierres))]
            ax_main.plot(indices[-len(sma50):], sma50, color="#E040FB", linewidth=1.3, label="SMA 50")

        # Panel Inferior: Oscilador RSI(14)
        rsi_series = []
        for i in range(14, len(cierres) + 1):
            r = analisis_herramientas._rsi(cierres[:i], 14)
            if r is not None:
                rsi_series.append(r)

        if rsi_series:
            ax_sub.plot(indices[-len(rsi_series):], rsi_series, color="#00E676", linewidth=1.4, label="RSI (14)")
            ax_sub.axhline(70, color="#FF5252", linestyle="--", alpha=0.7, linewidth=0.8)
            ax_sub.axhline(30, color="#00B0FF", linestyle="--", alpha=0.7, linewidth=0.8)
            ax_sub.fill_between(indices[-len(rsi_series):], rsi_series, 70, where=[x >= 70 for x in rsi_series], color="#FF5252", alpha=0.3)
            ax_sub.fill_between(indices[-len(rsi_series):], rsi_series, 30, where=[x <= 30 for x in rsi_series], color="#00B0FF", alpha=0.3)
            ax_sub.set_ylim(10, 90)

        # Configuración de Ejes y Leyendas
        ax_main.set_title(f"Análisis Bursátil Professional: {simbolo_clean} ({tf_real})", color="#FFFFFF", fontsize=13, pad=12)
        if ax_main.get_legend_handles_labels()[0]:
            ax_main.legend(loc="upper left", facecolor="#12141D", edgecolor="#2A2E3D")
        ax_main.grid(True, color="#2A2E3D", linestyle=":", alpha=0.6)
        ax_sub.grid(True, color="#2A2E3D", linestyle=":", alpha=0.6)

        # Etiquetar fechas en eje X
        paso = max(1, len(indices) // 8)
        ax_sub.set_xticks(indices[::paso])
        ax_sub.set_xticklabels(fechas_str[::paso], rotation=30, ha="right", color="#AAAAAA")
        plt.setp(ax_main.get_xticklabels(), visible=False)

    # Ajusta márgenes para que no se corten títulos ni etiquetas.
    plt.tight_layout()

    # Guardar a archivo físico. La imagen NO se devuelve en Base64: ese texto iría al
    # historial del LLM (cientos de miles de caracteres) y a la memoria en cada turno.
    fig.savefig(filepath, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    # Devuelve solo metadatos y la ruta del PNG, nunca la imagen.
    return {
        "fuente": "Generador Visual Bursátil (Matplotlib)",
        "fuente_datos": fuente_datos,
        "simbolo": simbolo_clean,
        "tipo_grafico": tipo_grafico,
        "timeframe": tf_real,
        "velas_graficadas": len(velas_data),
        "ultimo_cierre": velas_data[-1].get("close"),
        "archivo_guardado": filepath,
        "mensaje": (
            f"Gráfico {tipo_grafico} de {simbolo_clean} ({tf_real}) generado y mostrado al usuario en el chat. "
            "No incluyas rutas ni enlaces a la imagen en tu respuesta."
        ),
    }


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara herramientas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
