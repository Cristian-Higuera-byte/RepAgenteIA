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

"""Gráficos SVG sencillos de copy trading (como imágenes incrustadas): sparkline, dona de victorias y avatar.

Cada gráfico se genera como SVG, se codifica en base64 y se devuelve como una etiqueta
img con data URI, para incrustarlo en st.html sin archivos externos.
"""
import base64
import math
import random


# TITULO MINILINEA

def minilinea(seed: str, w=150, h=44, serie=None):
    """Genera una mini línea (sparkline) simulada con área degradada.

    Parámetros: seed (texto que siembra el generador aleatorio, para que la misma
    estrategia dibuje siempre la misma curva), w y h (ancho y alto en píxeles). Devuelve
    el HTML de una imagen SVG (data URI base64). Con `serie` (valores reales, por ejemplo la rentabilidad acumulada de los últimos días) dibuja esa serie
    y, si tiene menos de dos puntos, una línea plana; sin `serie`, una serie simulada de 30 puntos de sesgo alcista.
    """
    if serie is not None:
        puntos = [float(x) for x in serie] if len(serie) >= 2 else [0.0, 0.0]
        n = len(puntos)
    else:
        # Generador reproducible y número de puntos de la serie.
        rnd = random.Random(seed)
        n = 30
        v = 100.0
        puntos = []
        # Paseo aleatorio con sesgo positivo.
        for i in range(n):
            v += rnd.uniform(-1.5, 2.6)  # sesgo alcista
            puntos.append(v)
    # Escala la serie al alto disponible (con margen de 3 px) y la convierte en coordenadas x,y.
    lo, hi = min(puntos), max(puntos)
    rango = (hi - lo) or 1
    coordenadas = []
    for i, p in enumerate(puntos):
        x = i * (w / (n - 1))
        y = h - 3 - (p - lo) / rango * (h - 6)
        coordenadas.append(f"{x:.1f},{y:.1f}")
    # Línea y polígono de área cerrado contra la base; luego el SVG con degradado vertical verde.
    linea = " ".join(coordenadas)
    area = f"0,{h} " + linea + f" {w},{h}"
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' "
           f"preserveAspectRatio='none'><defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'>"
           f"<stop offset='0' stop-color='#3fb950' stop-opacity='0.30'/>"
           f"<stop offset='1' stop-color='#3fb950' stop-opacity='0'/></linearGradient></defs>"
           f"<polygon points='{area}' fill='url(#g)'/>"
           f"<polyline points='{linea}' fill='none' stroke='#3fb950' stroke-width='1.6'/></svg>")
    # Codifica el SVG en base64 para usarlo como imagen incrustada.
    b64 = base64.b64encode(svg.encode()).decode()
    return f"<img src='data:image/svg+xml;base64,{b64}' width='{w}' height='{h}'>"


# TITULO ROSQUILLA

def rosquilla(win_porcentaje: float, tamano=180):
    """Genera una dona SVG del ratio de victorias (verde) frente a pérdidas (rojo).

    Parámetros: win_pct (porcentaje de victorias, 0 a 100) y size (lado en píxeles).
    Devuelve el HTML de una imagen SVG (data URI base64). La dona se dibuja con dos
    círculos: el rojo completo y encima el verde con trazo discontinuo proporcional.
    """
    # Radio, centro y longitud de la circunferencia; el tramo verde es la fracción ganadora.
    r = tamano / 2 - 16
    cx = cy = tamano / 2
    circ = 2 * math.pi * r
    gan = circ * win_porcentaje / 100
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{tamano}' height='{tamano}' viewBox='0 0 {tamano} {tamano}'>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#f85149' stroke-width='22'/>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#3fb950' stroke-width='22' "
        f"stroke-dasharray='{gan:.1f} {circ - gan:.1f}' stroke-dashoffset='{circ/4:.1f}' "
        f"transform='rotate(-90 {cx} {cy})' stroke-linecap='round'/></svg>"
    )
    # Codifica el SVG en base64 para usarlo como imagen incrustada.
    b64 = base64.b64encode(svg.encode()).decode()
    return f"<img src='data:image/svg+xml;base64,{b64}' width='{tamano}' height='{tamano}'>"


# TITULO AVATAR

def avatar(nombre: str) -> str:
    """Devuelve las iniciales (hasta dos, en mayúsculas) del nombre, para usarlas como avatar de texto."""
    return "".join(p[0] for p in nombre.split()[:2]).upper()


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
