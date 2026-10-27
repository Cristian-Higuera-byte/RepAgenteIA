# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara tarjetas .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Tarjetas (chips) de la barra superior: Capital, Riesgo, Drawdown y Mercado.

Funciones puras que devuelven fragmentos HTML en línea (sin CSS externo) para que barra.py
los ensamble en la fila de saldo y métricas.
"""


# TITULO CHIP

def chip(etiqueta: str, valor_html: str, *, etiqueta_color: str = "#8b949e",
          borde: str = "#30363d") -> str:
    """Construye un chip compacto: etiqueta en mayúsculas arriba (gris) y valor abajo.

    Recibe `label` (texto de la etiqueta), `valor_html` (HTML ya preparado del valor, se
    inserta tal cual), `label_color` (color de la etiqueta) y `borde` (color del borde).
    Devuelve el HTML de la tarjeta con estilos en línea.
    """
    return (
        "<div style='display:flex; flex-direction:column; align-items:flex-end; "
        f"line-height:1.1; padding:4px 11px; background:#161b22; border:1px solid {borde}; "
        "border-radius:8px; white-space:nowrap;'>"
        f"<span style='font-size:10px; color:{etiqueta_color}; text-transform:uppercase; "
        f"letter-spacing:.5px;'>{etiqueta}</span>"
        f"<span style='display:flex; align-items:baseline; gap:6px;'>{valor_html}</span>"
        "</div>"
    )


# TITULO CHIPS METRICAS

def chips_metricas(metricas: dict | None) -> str:
    """Construye los chips de Riesgo, Drawdown y Mercado a partir de las métricas de la barra.

    Recibe `metricas`, el diccionario de estadisticas_portafolio.metricas_barra() con las
    claves `riesgo`, `drawdown` y `mercado`. Devuelve el HTML de los tres chips concatenados,
    o cadena vacía si no hay datos (sin conexión), de modo que la barra queda como antes.
    """
    if not metricas:
        return ""
    # Estilo común de los valores numéricos (fuente monoespaciada)
    mono = "font-size:14px; font-weight:700; font-family:monospace;"

    # --- Riesgo: % del capital en riesgo si saltan los SL ---
    r = metricas.get("riesgo", {})
    r_porcentaje = float(r.get("pct", 0.0) or 0.0)
    sin_stop_loss = int(r.get("sin_sl", 0) or 0)
    # Verde hasta 2 %, ámbar hasta 5 %, rojo por encima (umbrales de gestión de riesgo).
    r_color = "#8b949e" if r_porcentaje == 0 else ("#3fb950" if r_porcentaje <= 2 else ("#d29922" if r_porcentaje <= 5 else "#f85149"))
    aviso_stop_loss = (f"<span style='font-size:10px; font-weight:700; color:#d29922;' "
                f"title='{sin_stop_loss} posición(es) sin Stop Loss: riesgo no acotado'>"
                f"·{sin_stop_loss} sin SL</span>") if sin_stop_loss else ""
    chip_riesgo = chip(
        "Riesgo",
        f"<span style='{mono} color:{r_color};'>{r_porcentaje:.1f}%</span>{aviso_stop_loss}",
    )

    # --- Drawdown: caída máxima de equity (negativo, en rojo) ---
    d = metricas.get("drawdown", {})
    d_porcentaje = float(d.get("pct", 0.0) or 0.0)
    if d.get("disponible") and d_porcentaje >= 0.05:
        drawdown_html = f"<span style='{mono} color:#f85149;'>-{d_porcentaje:.1f}%</span>"
    elif d.get("disponible"):   # sin caída: se muestra neutro, no como "-0.0%" en rojo
        drawdown_html = f"<span style='{mono} color:#8b949e;' title='Sin caída de equity registrada'>0.0%</span>"
    else:
        drawdown_html = ("<span style='font-size:14px; font-weight:700; color:#8b949e; "
                   "font-family:monospace;' title='Aún se están registrando datos de "
                   "equity para calcular el drawdown real'>—</span>")
    chip_drawdown = chip("Drawdown", drawdown_html)

    # --- Mercado: estado de sesión del símbolo activo ---
    m = metricas.get("mercado", {})
    abierto = m.get("abierto")
    if abierto is True:
        punto, texto, columna = "#3fb950", "Abierto", "#3fb950"
    elif abierto is False:
        punto, texto, columna = "#f85149", "Cerrado", "#f85149"
    else:
        punto, texto, columna = "#8b949e", "—", "#8b949e"
    mercado_html = (
        f"<span style='display:flex; align-items:center; gap:5px; font-size:12px; "
        f"font-weight:700; color:{columna};'>"
        f"<span style='width:7px; height:7px; border-radius:50%; background:{punto}; "
        f"display:inline-block;'></span>{texto}</span>"
    )
    chip_mercado = chip("Mercado", mercado_html)

    return chip_riesgo + chip_drawdown + chip_mercado


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara tarjetas .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
