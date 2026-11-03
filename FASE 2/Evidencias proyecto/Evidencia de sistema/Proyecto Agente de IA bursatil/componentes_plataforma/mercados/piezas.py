# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara piezas .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Piezas HTML de Mercados: mini-gráfico, pastilla de variación, rango del día, fila de la tabla y tarjeta.

Todas las funciones devuelven cadenas HTML que `secciones.py` y `ficha.py` pintan con `st.html`. Las clases
(`mkt-*`) se estilizan en `estilos.css` y los atributos `data-pj-*` los actualiza el feed en vivo.
"""
import base64

from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from componentes_plataforma.iconografia import icono_activo   # íconos estilo XM (comunes)
from componentes_plataforma.flujo_precios import atributos as _en_vivo
from componentes_plataforma.mercado_datos import historial_sparkline as _historial_sparkline
from componentes_plataforma.mercados.broker import esta_abierto, serie
from componentes_plataforma.mercados.constantes import ROJO, VERDE


# TITULO SVG MINILINEA

def svg_minilinea(valores, w=104, h=34, area=True) -> str:
    """Mini-gráfico como <img> data-URI (st.html sanea el SVG en línea).

    Recibe la lista de valores, el ancho y alto en píxeles y si se rellena el área bajo la línea. Colorea en
    verde si el último valor es mayor o igual al primero y en rojo si no. Con menos de 2 puntos devuelve un
    espacio vacío del mismo tamaño."""
    if not valores or len(valores) < 2:
        return f"<span style='display:inline-block;width:{w}px;height:{h}px;'></span>"
    # Escala vertical: mínimo y máximo de la serie (rango 1 si es plana para evitar división por cero)
    lo, hi = min(valores), max(valores)
    rango = (hi - lo) or 1
    n = len(valores)
    # Puntos (x, y) con 3 px de margen vertical; el eje y SVG crece hacia abajo, por eso se invierte
    puntos = [(i * w / (n - 1), h - 3 - (v - lo) / rango * (h - 6)) for i, v in enumerate(valores)]
    columna = VERDE if valores[-1] >= valores[0] else ROJO
    linea = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    # Relleno degradado bajo la línea (opcional)
    relleno = ""
    if area:
        relleno = (f"<defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'>"
                   f"<stop offset='0' stop-color='{columna}' stop-opacity='.28'/>"
                   f"<stop offset='1' stop-color='{columna}' stop-opacity='0'/></linearGradient></defs>"
                   f"<polygon fill='url(#g)' points='0,{h} {linea} {w},{h}'/>")
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
           f"{relleno}<polyline fill='none' stroke='{columna}' stroke-width='1.6' "
           f"stroke-linejoin='round' points='{linea}'/></svg>")
    # Se codifica en base64 para incrustarlo como imagen y evitar el saneado del SVG en línea
    b64 = base64.b64encode(svg.encode()).decode()
    return f"<img src='data:image/svg+xml;base64,{b64}' width='{w}' height='{h}' alt=''>"


# TITULO PILDORA

def pildora(f) -> str:
    """Devuelve la pastilla de variación porcentual (verde con flecha arriba o roja con flecha abajo).

    Recibe la fila de datos `f` (claves `ch`, `pct`, `sym`); el feed en vivo la actualiza por su atributo."""
    sube = f["ch"] >= 0
    columna, bg = (VERDE, "rgba(63,185,80,.12)") if sube else (ROJO, "rgba(248,81,73,.12)")
    texto = f"▲ +{f['pct']:.2f}%" if sube else f"▼ {f['pct']:.2f}%"
    return (f"<span class='mercados-pastilla' style='color:{columna};background:{bg};' "
            f"{_en_vivo(f['sym'], 'pct', pill=1)}>{texto}</span>")


# TITULO RANGO HTML

def rango_html(f) -> str:
    """Devuelve la barra del rango del día con mínimo, máximo y un punto en la posición del precio actual."""
    d = f["dig"]
    # Posición del precio dentro del rango en porcentaje; 50 si el rango es nulo
    posicion = 50.0 if f["hi"] <= f["lo"] else (f["last"] - f["lo"]) / (f["hi"] - f["lo"]) * 100
    return (f"<div class='mercados-rango'><span class='mercados-numero'>{f['lo']:,.{d}f}</span>"
            f"<div class='bar'><div class='dot' style='left:{max(0, min(100, posicion)):.1f}%;'></div></div>"
            f"<span class='mercados-numero'>{f['hi']:,.{d}f}</span></div>")


# TITULO FILA HTML

def fila_html(f) -> str:
    """Devuelve el HTML de una fila de la tabla: instrumento, precio, cambio, cambio %, rango, 5 días y estado.

    Recibe la fila de datos `f`. Consulta las velas H1 para el mini-gráfico y el estado abierto/cerrado."""
    d = f["dig"]
    columna = VERDE if f["ch"] >= 0 else ROJO
    # Mini-gráfico de las últimas 120 velas H1 (aprox. 5 días); sin datos queda un hueco
    h1 = serie(f["sym"], mt5.TIMEFRAME_H1, 120)
    spark = svg_minilinea([float(x) for x in h1["close"].tolist()] if h1 is not None else [], 104, 30, area=False)
    abierto = esta_abierto(f["t"])
    estado = (f"<span class='mercados-estado'><span class='mercados-dot{'' if abierto else ' off'}'></span>"
              f"{'Abierto' if abierto else 'Cerrado'}</span>")
    return (
        "<div class='mercados-fila'>"
        f"<div><div class='mercados-nombre'><span class='mercados-icono'>{icono_activo(f['sym'], 32)}</span>"
        f"<div style='min-width:0;'><b>{f['label']}</b><small>{f['sym']}</small></div></div></div>"
        f"<div class='mercados-r mercados-numero' style='font-weight:700;' "
        f"{_en_vivo(f['sym'], 'px', d=d, flash=1)}>{f['last']:,.{d}f}</div>"
        f"<div class='mercados-r mercados-numero' style='color:{columna};' {_en_vivo(f['sym'], 'ch', d=d)}>{f['ch']:+,.{d}f}</div>"
        f"<div class='mercados-r'>{pildora(f)}</div>"
        f"<div>{rango_html(f)}</div>"
        f"<div style='display:flex;justify-content:center;'>{spark}</div>"
        f"<div style='display:flex;align-items:center;justify-content:space-between;'>{estado}"
        "<span class='mercados-flecha'>›</span></div>"
        "</div>"
    )


# TITULO TARJETA HTML

def tarjeta_html(f, etiqueta: str) -> str:
    """Devuelve el HTML de una tarjeta de "Pulso del mercado" (ícono, nombre, etiqueta, precio, variación y sparkline).

    Recibe la fila de datos `f` y la etiqueta `tag` que indica qué representa la referencia."""
    d = f["dig"]
    # Mini-gráfico EN VIVO: semilla M1 (últimos 30 min) y el feed agrega cada tick
    valores = _historial_sparkline(f["sym"])
    semilla = ",".join(f"{v:.6g}" for v in valores)
    spark = (f"<span data-pj-spark='{f['sym']}' data-pj-vals='{semilla}'>"
             f"{svg_minilinea(valores, 92, 40)}</span>")
    return (
        "<div class='mercados-tarjeta'>"
        f"<div class='mercados-tarjeta-superior'><span class='mercados-icono'>{icono_activo(f['sym'], 28)}</span>"
        f"<div><div class='mercados-tarjeta-nombre'>{f['label']}</div><div class='mercados-tarjeta-simbolo'>{f['sym']}</div></div>"
        f"<span class='mercados-tarjeta-etiqueta'>{etiqueta}</span></div>"
        f"<div class='mercados-tarjeta-precio' {_en_vivo(f['sym'], 'px', d=d, flash=1)}>{f['last']:,.{d}f}</div>"
        f"<div class='mercados-tarjeta-boton'>{pildora(f)}{spark}</div>"
        "</div>"
    )


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara piezas .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
