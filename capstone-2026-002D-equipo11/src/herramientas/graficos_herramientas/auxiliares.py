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

"""Funciones y constantes auxiliares de las herramientas de gráficos (sin registrar nada).

Contiene el directorio de salida de las imágenes PNG, los tipos de gráfico
admitidos, el mapeo de símbolos de MT5 a Yahoo Finance, el formateo de
etiquetas de fecha para el eje X y el dibujo manual de velas japonesas.
Fija además el backend no interactivo de matplotlib (``Agg``), por lo que debe
importarse antes que ``matplotlib.pyplot``.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import matplotlib
from matplotlib.patches import Rectangle


# Fija el backend sin ventana antes de que alguien importe pyplot.
matplotlib.use("Agg")  # Backend no interactivo para entornos de servidor/dashboard


# Directorio de salida (ruta absoluta: así el dashboard encuentra el archivo
# aunque Streamlit se lance desde otra carpeta que la terminal).
OUTPUT_DIR = os.path.abspath(os.path.join("static", "graficos"))


# Crea la carpeta de salida al importar el módulo si aún no existe.
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Tipos de gráfico aceptados por la herramienta (también alimentan el enum del esquema).
TIPOS_VALIDOS = ("velas", "lineas", "barras_ohlc", "comparativo")


def _mapear_simbolo_yf(simbolo: str) -> str:
    """Traduce un símbolo de MT5 al ticker equivalente de Yahoo Finance.

    Normaliza (mayúsculas, sin espacios ni "/"), convierte alias conocidos
    (EURUSD, USDCLP, GBPUSD, XAUUSD/GOLD, WTI/CL, BTCUSD) y agrega "=X" a
    cualquier otro par de seis letras (divisas). Los demás símbolos (acciones)
    se devuelven tal cual. Se usa como respaldo cuando MT5 no entrega velas.
    """
    # Normaliza la entrada: sin espacios, mayúsculas y sin separador "/".
    s = (simbolo or "").strip().upper().replace("/", "")
    # Alias explícitos de divisas, metales, petróleo y cripto.
    if s == "EURUSD": return "EURUSD=X"
    if s == "USDCLP": return "USDCLP=X"
    if s == "GBPUSD": return "GBPUSD=X"
    if s in ("XAUUSD", "GOLD"): return "GC=F"
    if s in ("WTI", "CL"): return "CL=F"
    if s == "BTCUSD": return "BTC-USD"
    # Cualquier otro par de seis letras se asume divisa de Yahoo ("XXXYYY=X").
    if not s.endswith("=X") and len(s) == 6 and s.isalpha():
        return f"{s}=X"
    # Si no coincide con nada, se asume que ya es un ticker válido (p. ej. acciones).
    return s


def _etiqueta_fecha(valor: Any, timeframe: str) -> str:
    """Etiqueta legible para el eje X. D1 muestra la fecha; el resto, día-mes y hora.

    Recibe ``valor`` (timestamp numérico o texto ISO) y el ``timeframe``.
    Devuelve el texto formateado; si no se puede interpretar la fecha,
    devuelve los últimos 8 caracteres del valor como texto.
    """
    try:
        # Timestamp numérico (epoch) o cadena ISO, quitando "Z" y "T".
        if isinstance(valor, (int, float)):
            dt = datetime.fromtimestamp(valor)
        else:
            dt = datetime.fromisoformat(str(valor).replace("Z", "").replace("T", " ")[:19])
        return dt.strftime("%Y-%m-%d" if timeframe == "D1" else "%d-%m %H:%M")
    except Exception:
        return str(valor)[-8:]


def _dibujar_velas(ax, df_velas: list[dict[str, Any]]):
    """Dibuja velas japonesas personalizadas con mechas y cuerpos alcistas/bajistas.

    Recibe el eje de matplotlib ``ax`` y una lista de diccionarios con las
    claves open, high, low y close. Dibuja directamente sobre el eje (efecto
    secundario) usando la posición en la lista como coordenada X; no devuelve nada.
    """
    for i, v in enumerate(df_velas):
        o, h, l, c = v["open"], v["high"], v["low"], v["close"]
        color = "#00B0FF" if c >= o else "#FF5252"  # Azul alcista, Rojo bajista

        # Mecha: línea vertical del mínimo al máximo.
        ax.plot([i, i], [l, h], color=color, linewidth=1.0)
        # Cuerpo: rectángulo entre apertura y cierre (altura mínima para dojis).
        altura = max(abs(c - o), (h - l) * 0.001)
        bottom = min(o, c)
        rect = Rectangle((i - 0.35, bottom), 0.7, altura, facecolor=color, edgecolor=color, alpha=0.9)
        ax.add_patch(rect)


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
