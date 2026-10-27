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

"""Herramientas registradas para el agente de tablas y reportes (los esquemas viven en esquemas.json).

Registra ``generar_tabla_reporte``, que arma tablas de posiciones, riesgo o
datos personalizados y las entrega en Markdown, HTML o CSV, guardando además un archivo.
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from database.scripts.fuentes import mt5_fuentes as mt5_fuente
from herramientas import analisis_herramientas
from herramientas.base import cargar_json, herramienta
from herramientas.tablas_herramientas.auxiliares import OUTPUT_DIR

# Esquemas (descripción y parámetros) de la herramienta, leídos de esquemas.json.
_ESQ = cargar_json(Path(__file__).parent / "esquemas.json")


@herramienta(**_ESQ["generar_tabla_reporte"])
def generar_tabla_reporte(
    tipo_reporte: str = "posiciones_abiertas",
    formato: str = "markdown",
    datos_json: str | None = None,
) -> dict[str, Any]:
    """Genera una tabla de reporte y la guarda como archivo descargable.

    Recibe el tipo de reporte (posiciones_abiertas, riesgo_cartera o
    datos_personalizados), el formato de salida (markdown, html o csv) y, para
    los datos personalizados, una lista JSON de objetos con las mismas claves. Los datos salen de
    MT5 (posiciones) o del análisis de riesgo. Escribe un archivo en ``OUTPUT_DIR``. Devuelve el
    texto de la tabla, el número de filas, la ruta del archivo y la URL de descarga, o
    ``{"error": ...}`` si no hay datos o el JSON es inválido.
    """
    # Columnas y filas de la tabla, que se rellenan según el tipo de reporte.
    columnas: list[str] = []
    filas: list[list[Any]] = []

    # 1. Recopilar datos según el tipo de reporte
    if tipo_reporte == "posiciones_abiertas":
        pos_data = mt5_fuente.posiciones()
        posiciones = pos_data.get("posiciones", [])
        columnas = ["Ticket", "Símbolo", "Tipo", "Lotes", "Precio Apertura", "Precio Actual", "SL", "TP", "PnL ($)"]
        for p in posiciones:
            filas.append([
                p["ticket"],
                p["simbolo"],
                p["tipo"],
                p["lotes"],
                p["precio_apertura"],
                p["precio_actual"],
                p["sl"] or "Sin SL",
                p["tp"] or "Sin TP",
                p["beneficio"],
            ])

    # Reporte de riesgo por posición, tomado del análisis de riesgo.
    elif tipo_reporte == "riesgo_cartera":
        riesgo_data = analisis_herramientas.analizar_riesgo_posicion()
        posiciones = riesgo_data.get("posiciones", [])
        columnas = ["Ticket", "Símbolo", "Tipo", "Lotes", "Distancia al SL (Pips)", "Riesgo ($)", "Riesgo Equidad (%)", "Ratio R:R"]
        for r in posiciones:
            filas.append([
                r["ticket"],
                r["simbolo"],
                r["tipo"],
                r["lotes"],
                r.get("distancia_sl_desde_precio_actual_pips") or "N/A",
                r.get("riesgo_estimado_usd") or "N/A",
                f"{r.get('riesgo_equidad_pct')}%" if r.get('riesgo_equidad_pct') else "N/A",
                r.get("ratio_riesgo_beneficio") or "N/A",
            ])

    # Datos libres: el JSON debe ser una lista de objetos; las columnas salen del primero.
    elif tipo_reporte == "datos_personalizados" and datos_json:
        try:
            parsed = json.loads(datos_json)
            if isinstance(parsed, list) and len(parsed) > 0:
                columnas = list(parsed[0].keys())
                for item in parsed:
                    filas.append(list(item.values()))
        except Exception as e:
            return {"error": f"Error al parsear datos_json: {e}"}

    # Sin columnas no hay nada que mostrar.
    if not columnas:
        return {"error": "No hay datos para construir la tabla especificada."}

    # 2. Renderizar según formato
    resultado_texto = ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_{tipo_reporte}_{timestamp}.{formato}"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Tabla Markdown: encabezado, separador y filas.
    if formato == "markdown":
        header = "| " + " | ".join(columnas) + " |"
        sep = "| " + " | ".join(["---"] * len(columnas)) + " |"
        body = "\n".join(["| " + " | ".join(map(str, f)) + " |" for f in filas])
        resultado_texto = f"{header}\n{sep}\n{body}"

    # Tabla HTML simple con la clase tabla-bursatil.
    elif formato == "html":
        th_str = "".join([f"<th>{c}</th>" for c in columnas])
        tr_str = "".join(["<tr>" + "".join([f"<td>{cell}</td>" for cell in f]) + "</tr>" for f in filas])
        resultado_texto = f"<table border='1' class='tabla-bursatil'><thead><tr>{th_str}</tr></thead><tbody>{tr_str}</tbody></table>"

    # CSV: se escribe directamente en el archivo.
    elif formato == "csv":
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columnas)
            writer.writerows(filas)
        resultado_texto = f"Archivo CSV generado en {filepath}"

    # Si es Markdown o HTML, también guardamos copia en archivo para descarga
    if formato != "csv":
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(resultado_texto)

    # Ruta pública del archivo, servida desde static/reportes.
    web_path = f"/static/reportes/{filename}"

    return {
        "fuente": "Generador de Tablas y Reportes",
        "tipo_reporte": tipo_reporte,
        "formato": formato,
        "total_filas": len(filas),
        "tabla_renderizada": resultado_texto,
        "archivo_guardado": filepath,
        "url_descarga": web_path,
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
