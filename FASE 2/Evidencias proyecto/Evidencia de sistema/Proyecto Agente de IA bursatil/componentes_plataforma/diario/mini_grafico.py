# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara mini_grafico .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Mini-gráfico SVG de velas de una operación, con marcas de entrada/salida y SL/TP.

Lo usa ficha.py: recibe las velas del rango de la operación y devuelve HTML con un SVG
(se incrusta con st.markdown). Los estilos diario-grafico y diario-vacio están en estilos.css.
"""
from componentes_plataforma.diario.datos import AZ, DN, TX, UP


# TITULO MINI GRAFICO SVG

def mini_grafico_svg(velas, o):
    """Mini-gráfico de velas de la operación con marcas de entrada/salida y SL/TP,
    etiquetas tipo pill (sin pisarse) y la paleta P&J. Velas: [{t,o,h,l,c}].

    Parámetros: velas (lista de diccionarios con tiempo t, apertura o, máximo h, mínimo l y
    cierre c) y o (operación: entrada, salida, sl, tp, hora_in y hora_out). Devuelve una
    cadena HTML: el SVG, o un aviso si hay menos de 2 velas.
    """
    # Sin datos suficientes se devuelve un aviso en lugar del gráfico.
    if len(velas) < 2:
        return ("<div class='diario-vacio'>No hay velas para esta operación "
                "(histórico fuera de rango).</div>")
    # Niveles de precio que deben caber en el eje vertical (entrada, salida y, si existen, SL y TP).
    niveles = [o["entrada"], o["salida"]]
    if o.get("sl"):
        niveles.append(o["sl"])
    if o.get("tp"):
        niveles.append(o["tp"])
    # Rango de precios visible: abarca las velas y los niveles.
    lo = min(min(v["l"] for v in velas), *niveles)
    hi = max(max(v["h"] for v in velas), *niveles)
    rango = (hi - lo) or 1.0
    # Dimensiones del lienzo SVG (unidades del viewBox) y margen interno.
    W, H, pad = 1000, 270, 16
    padR = 120          # espacio a la derecha para las etiquetas pill
    # Número de velas y ancho disponible por vela.
    n = len(velas)
    cw = (W - pad - padR) / n
    # coord_y convierte un precio en coordenada Y del SVG (los precios altos quedan arriba);
    # coord_x da la coordenada X del centro de la vela de índice i.
    def coord_y(p):
        """Convierte un precio `p` en la coordenada Y del SVG (los precios altos quedan arriba)."""
        return H - pad - (H - 2 * pad) * (p - lo) / rango

    def coord_x(i):
        """Devuelve la coordenada X del centro de la vela de índice `i`."""
        return pad + cw * (i + 0.5)

    # Mecha y cuerpo de cada vela: verde si cierra al alza, roja si no.
    cuerpo = []
    for i, v in enumerate(velas):
        columna = UP if v["c"] >= v["o"] else DN
        x = coord_x(i)
        cuerpo.append(f"<line x1='{x:.1f}' y1='{coord_y(v['h']):.1f}' x2='{x:.1f}' "
                      f"y2='{coord_y(v['l']):.1f}' stroke='{columna}' stroke-width='1'/>")
        y1, y2 = coord_y(v["o"]), coord_y(v["c"])
        yt, alto = min(y1, y2), max(1.0, abs(y1 - y2))
        bw = max(1.8, cw * 0.62)
        cuerpo.append(f"<rect x='{x-bw/2:.1f}' y='{yt:.1f}' width='{bw:.1f}' "
                      f"height='{alto:.1f}' rx='1' fill='{columna}'/>")

    def indice_vela(marca_tiempo):
        """Devuelve el índice de la vela cuyo tiempo está más cerca de `ts` (marca de tiempo)."""
        return min(range(n), key=lambda i: abs(velas[i]["t"] - marca_tiempo))

    # Niveles con etiqueta pill a la derecha; se reparten en Y para no pisarse.
    lineas = []
    lineas.append((coord_y(o["entrada"]), AZ, f"Entrada {o['entrada']:,.5f}", False))
    lineas.append((coord_y(o["salida"]), TX, f"Salida {o['salida']:,.5f}", False))
    if o.get("sl"):
        lineas.append((coord_y(o["sl"]), DN, f"SL {o['sl']:,.5f}", True))
    if o.get("tp"):
        lineas.append((coord_y(o["tp"]), UP, f"TP {o['tp']:,.5f}", True))

    svg = list(cuerpo)
    # Dibujar las líneas horizontales (hasta donde empiezan las pills).
    xL = W - padR
    for y, columna, texto, dash in lineas:
        d = "stroke-dasharray='5 4'" if dash else ""
        svg.append(f"<line x1='{pad}' y1='{y:.1f}' x2='{xL:.1f}' y2='{y:.1f}' "
                   f"stroke='{columna}' stroke-width='1.3' {d} opacity='.85'/>")

    # Repartir las pills en Y (anti-solape): ordenar por y y separar >= 20px.
    pastillas = sorted([(y, columna, texto) for (y, columna, texto, _d) in lineas], key=lambda t: t[0])
    PH = 19
    for i in range(1, len(pastillas)):
        if pastillas[i][0] - pastillas[i - 1][0] < PH:
            pastillas[i] = (pastillas[i - 1][0] + PH, pastillas[i][1], pastillas[i][2])
    for y, columna, texto in pastillas:
        yy = max(PH / 2 + 2, min(H - PH / 2 - 2, y))
        w = 9 + len(texto) * 5.6
        svg.append(
            f"<rect x='{xL + 6:.1f}' y='{yy - PH/2:.1f}' width='{w:.1f}' height='{PH}' "
            f"rx='5' fill='{columna}' fill-opacity='.16' stroke='{columna}' stroke-opacity='.6'/>"
            f"<text x='{xL + 6 + w/2:.1f}' y='{yy + 3.5:.1f}' fill='{columna}' font-size='10.5' "
            f"font-family='ui-monospace,Consolas,monospace' text-anchor='middle'>{texto}</text>")

    # Puntos de entrada/salida sobre las velas.
    ie, isx = indice_vela(o["hora_in"]), indice_vela(o["hora_out"])
    svg.append(f"<circle cx='{coord_x(ie):.1f}' cy='{coord_y(o['entrada']):.1f}' r='5' fill='{AZ}' "
               f"stroke='#0b1017' stroke-width='1.5'/>")
    svg.append(f"<circle cx='{coord_x(isx):.1f}' cy='{coord_y(o['salida']):.1f}' r='5' fill='{TX}' "
               f"stroke='#0b1017' stroke-width='1.5'/>")
    return (f"<div class='diario-grafico'><svg viewBox='0 0 {W} {H}' width='100%' height='270' "
            f"style='width:100%;height:270px;display:block'>"
            + "".join(svg) + "</svg></div>")


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara mini_grafico .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
