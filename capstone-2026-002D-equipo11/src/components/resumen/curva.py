# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara curva .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Curva de balance de la vista Resumen dibujada como SVG en línea (línea, área con degradado y punto final).

Contiene una sola función pura que convierte la lista de puntos (marca de tiempo, balance) en una cadena HTML/SVG;
no usa Streamlit ni MT5. Los textos de clase (`rs-empty`) se estilizan en `estilos.css`.
"""


def curva_svg(curva, moneda):
    """Curva de balance como SVG (área con degradado). Estática; se redibuja en
    cada refresco. El color depende de si el periodo sube o baja.

    Recibe `curva`, una lista de pares (tiempo, balance) ya filtrada por periodo, y `moneda`, el código que se
    muestra junto al máximo. Devuelve el HTML con el SVG y una línea inferior con el mínimo y el máximo; si hay
    menos de dos puntos devuelve un aviso `rs-empty` en su lugar."""
    # Solo interesan los valores de balance; el tiempo sirve para ordenar y filtrar fuera de aquí.
    puntos = [b for _t, b in curva]
    if len(puntos) < 2:
        return ("<div class='rs-empty'>Aún no hay suficientes operaciones en este "
                "periodo para dibujar la curva.</div>")
    # Rango vertical de la curva; si todos los puntos son iguales se usa 1.0 para no dividir por cero.
    lo, hi = min(puntos), max(puntos)
    rng = (hi - lo) or 1.0
    # Lienzo virtual del SVG (ancho, alto y margen interior); el SVG se escala al ancho real con viewBox.
    W, H, pad = 1000, 230, 12
    n = len(puntos)
    # Coordenadas: x reparte los puntos uniformemente; y invierte el eje (el SVG crece hacia abajo).
    xs = [pad + (W - 2 * pad) * i / (n - 1) for i in range(n)]
    ys = [H - pad - (H - 2 * pad) * (b - lo) / rng for b in puntos]
    # Trazo de la línea (M = mover al primer punto, L = línea al siguiente).
    linea = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    # Área bajo la curva: baja hasta la base, recorre los puntos y vuelve a cerrar la figura.
    area = (f"M{xs[0]:.1f},{H - pad:.1f} "
            + " ".join(f"L{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
            + f" L{xs[-1]:.1f},{H - pad:.1f} Z")
    # Verde si el periodo termina igual o por encima de donde empezó; rojo si baja.
    sube = puntos[-1] >= puntos[0]
    col = "#2ebd85" if sube else "#f6465d"
    # Línea base punteada al nivel inicial del periodo + punto final resaltado.
    y0 = ys[0]
    return (
        f"<svg viewBox='0 0 {W} {H}' preserveAspectRatio='none' style='width:100%;height:230px;display:block'>"
        f"<defs><linearGradient id='rsg' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0%' stop-color='{col}' stop-opacity='.30'/>"
        f"<stop offset='100%' stop-color='{col}' stop-opacity='0'/></linearGradient></defs>"
        f"<line x1='{pad}' y1='{y0:.1f}' x2='{W-pad}' y2='{y0:.1f}' stroke='#2b3550' "
        f"stroke-width='1' stroke-dasharray='4 5'/>"
        f"<path d='{area}' fill='url(#rsg)'/>"
        f"<path d='{linea}' fill='none' stroke='{col}' stroke-width='2.2' "
        f"stroke-linejoin='round' stroke-linecap='round'/>"
        f"<circle cx='{xs[-1]:.1f}' cy='{ys[-1]:.1f}' r='4.5' fill='{col}'/>"
        f"<circle cx='{xs[-1]:.1f}' cy='{ys[-1]:.1f}' r='9' fill='{col}' fill-opacity='.22'/></svg>"
        f"<div style='display:flex;justify-content:space-between;color:#8b949e;"
        f"font-size:11px;margin-top:6px;font-variant-numeric:tabular-nums'>"
        f"<span>mín {lo:,.2f}</span><span>máx {hi:,.2f} {moneda}</span></div>"
    )


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara curva .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
