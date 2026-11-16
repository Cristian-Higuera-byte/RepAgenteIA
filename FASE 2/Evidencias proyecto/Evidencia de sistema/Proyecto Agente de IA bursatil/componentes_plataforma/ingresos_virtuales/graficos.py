# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara graficos .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Gráfico de barras apiladas del Laboratorio, dibujado como SVG en línea para que respete el tema oscuro de la plataforma.

Una sola función pura (sin Streamlit ni red): recibe los meses, una serie de montos por modelo y los colores, y devuelve el HTML con el
gráfico y su leyenda. Los textos de clase `lab-*` se estilizan en `estilos.css`.
"""
from html import escape

# Colores de cada modelo de cobro (distinguibles entre sí sobre fondo oscuro)
COLORES = {"suscripcion": "#388bfd", "recargo": "#a371f7", "referido": "#f0883e", "performance": "#2ebd85", "patrimonio": "#d29922",
           "chat": "#388bfd", "vigilancia": "#f0883e"}


# TITULO BARRAS APILADAS

def barras_apiladas_svg(meses: list, series: dict, nombres: dict, etiquetas: list | None = None) -> str:
    """Barras apiladas por mes (una pila por mes y un tramo por modelo) con eje de montos, etiquetas de mes y leyenda.

    Recibe `meses` ("AAAA-MM"), `series` ({clave_modelo: [monto por mes]}) y `nombres` ({clave_modelo: nombre visible}). Devuelve el HTML;
    `etiquetas` (opcional) son los textos del eje horizontal, uno por barra; sin ellas se usan los meses sin el siglo. Si no hay montos
    positivos devuelve un aviso."""
    claves = [k for k in series if any(v > 0 for v in series[k])]
    totales = [sum(series[k][i] for k in claves) for i in range(len(meses))]
    tope = max(totales, default=0.0)
    if not meses or tope <= 0:
        return "<div class='lab-pie'>Todavía no hay montos para graficar.</div>"
    ancho, alto, margen_izq, margen_inf, margen_sup = 1000, 260, 56, 30, 14
    area_x, area_y = ancho - margen_izq - 10, alto - margen_inf - margen_sup
    paso = area_x / len(meses)
    barra = min(60.0, paso * 0.62)
    partes = [f"<svg viewBox='0 0 {ancho} {alto}' preserveAspectRatio='none' style='width:100%;height:260px;display:block'>"]
    for i in range(5):                                          # cinco líneas guía del eje de montos
        valor = tope * i / 4
        decimales = 0 if tope >= 100 else 1 if tope >= 10 else 2 if tope >= 1 else 3      # los montos pequeños necesitan decimales en el eje
        y = margen_sup + area_y * (1 - i / 4)
        partes.append(f"<line x1='{margen_izq}' y1='{y:.1f}' x2='{ancho - 10}' y2='{y:.1f}' stroke='#202a37' stroke-width='1'/>"
                      f"<text x='{margen_izq - 8}' y='{y + 4:.1f}' text-anchor='end' fill='#8b949e' font-size='12'>{valor:,.{decimales}f}</text>")
    for i, mes in enumerate(meses):
        x = margen_izq + paso * i + (paso - barra) / 2
        base = margen_sup + area_y
        for k in claves:
            v = series[k][i]
            if v <= 0:
                continue
            h = area_y * v / tope
            base -= h
            partes.append(f"<rect x='{x:.1f}' y='{base:.1f}' width='{barra:.1f}' height='{h:.1f}' fill='{COLORES.get(k, '#8b949e')}'>"
                          f"<title>{escape(nombres.get(k, k))} · {mes}: {v:,.2f} USD</title></rect>")
        partes.append(f"<text x='{x + barra / 2:.1f}' y='{alto - 10}' text-anchor='middle' fill='#8b949e' font-size='12'>{etiquetas[i] if etiquetas else mes[2:]}</text>")
    partes.append("</svg>")
    leyenda = "".join(f"<span class='lab-leyenda-item'><i style='background:{COLORES.get(k, '#8b949e')}'></i>{escape(nombres.get(k, k))}</span>" for k in claves)
    return "".join(partes) + f"<div class='lab-leyenda'>{leyenda}</div>"


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara graficos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
