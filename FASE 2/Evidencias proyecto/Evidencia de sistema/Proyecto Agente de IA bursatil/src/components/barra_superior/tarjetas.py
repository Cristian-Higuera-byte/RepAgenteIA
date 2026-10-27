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


def chip(label: str, valor_html: str, *, label_color: str = "#8b949e",
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
        f"<span style='font-size:10px; color:{label_color}; text-transform:uppercase; "
        f"letter-spacing:.5px;'>{label}</span>"
        f"<span style='display:flex; align-items:baseline; gap:6px;'>{valor_html}</span>"
        "</div>"
    )


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
    r_pct = float(r.get("pct", 0.0) or 0.0)
    sin_sl = int(r.get("sin_sl", 0) or 0)
    # Verde hasta 2 %, ámbar hasta 5 %, rojo por encima (umbrales de gestión de riesgo).
    r_color = "#8b949e" if r_pct == 0 else ("#3fb950" if r_pct <= 2 else ("#d29922" if r_pct <= 5 else "#f85149"))
    aviso_sl = (f"<span style='font-size:10px; font-weight:700; color:#d29922;' "
                f"title='{sin_sl} posición(es) sin Stop Loss: riesgo no acotado'>"
                f"·{sin_sl} sin SL</span>") if sin_sl else ""
    chip_riesgo = chip(
        "Riesgo",
        f"<span style='{mono} color:{r_color};'>{r_pct:.1f}%</span>{aviso_sl}",
    )

    # --- Drawdown: caída máxima de equity (negativo, en rojo) ---
    d = metricas.get("drawdown", {})
    d_pct = float(d.get("pct", 0.0) or 0.0)
    if d.get("disponible") and d_pct >= 0.05:
        dd_html = f"<span style='{mono} color:#f85149;'>-{d_pct:.1f}%</span>"
    elif d.get("disponible"):   # sin caída: se muestra neutro, no como "-0.0%" en rojo
        dd_html = f"<span style='{mono} color:#8b949e;' title='Sin caída de equity registrada'>0.0%</span>"
    else:
        dd_html = ("<span style='font-size:14px; font-weight:700; color:#8b949e; "
                   "font-family:monospace;' title='Aún se están registrando datos de "
                   "equity para calcular el drawdown real'>—</span>")
    chip_dd = chip("Drawdown", dd_html)

    # --- Mercado: estado de sesión del símbolo activo ---
    m = metricas.get("mercado", {})
    abierto = m.get("abierto")
    if abierto is True:
        punto, texto, col = "#3fb950", "Abierto", "#3fb950"
    elif abierto is False:
        punto, texto, col = "#f85149", "Cerrado", "#f85149"
    else:
        punto, texto, col = "#8b949e", "—", "#8b949e"
    mercado_html = (
        f"<span style='display:flex; align-items:center; gap:5px; font-size:12px; "
        f"font-weight:700; color:{col};'>"
        f"<span style='width:7px; height:7px; border-radius:50%; background:{punto}; "
        f"display:inline-block;'></span>{texto}</span>"
    )
    chip_mercado = chip("Mercado", mercado_html)

    return chip_riesgo + chip_dd + chip_mercado


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
