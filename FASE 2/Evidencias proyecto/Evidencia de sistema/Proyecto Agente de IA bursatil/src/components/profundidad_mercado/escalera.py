# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara escalera .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""HTML de la escalera del DOM: filas Ask (arriba) y Bid (abajo) alrededor del spread.

Contiene funciones puras que reciben precios y volúmenes y devuelven cadenas HTML (clases `dom-row`, `dom-bar`,
`dom-px`, `dom-spread`, `dom-nota`, `dom-cols` definidas en `estilos.css`). Ofrece dos variantes: la profundidad
real del bróker y una vista demostrativa con volúmenes de muestra. No toca MT5 ni Streamlit.
"""
from __future__ import annotations

# Volúmenes de muestra por nivel (del más lejano al spread, al más cercano).
# La liquidez suele crecer al alejarse del precio → barras mayores arriba/abajo.
# Volúmenes de muestra para el lado vendedor (Ask), en lotes; solo para la vista demo.
VOL_ASK = [22, 16, 12, 9, 6]   # arriba (lejos) → abajo (mejor ask, pegado al spread)
# Volúmenes de muestra para el lado comprador (Bid), en lotes; solo para la vista demo.
VOL_BID = [6, 9, 13, 18, 25]   # arriba (mejor bid) → abajo (lejos)
# Mayor volumen de muestra: sirve de 100 % para calcular el ancho de las barras de la vista demo.
MAXVOL = max(VOL_ASK + VOL_BID)


def _fila(lado: str, volumen_txt: str, precio_txt: str, ancho: int) -> str:
    """Devuelve el HTML de una fila de la escalera.

    Recibe `lado` ('ask' o 'bid', determina el color), `volumen_txt` y `precio_txt` ya formateados, y `ancho`, el
    porcentaje (0-100) de la barra de volumen."""
    return (f"<div class='dom-row'><div class='dom-bar {lado}'>"
            f"<div style='width:{ancho}%'></div><span>{volumen_txt}</span></div>"
            f"<div class='dom-px {lado}'>{precio_txt}</div></div>")


def _spread(ask: float, bid: float, dig: int) -> str:
    """Devuelve el HTML de la fila central con el spread (Ask menos Bid) redondeado a `dig` decimales."""
    return (f"<div class='dom-spread'><span class='k'>spread</span>"
            f"<span class='v'>{round(ask - bid, dig):,.{dig}f}</span></div>")


def filas_reales(dom: dict, bid: float, ask: float, dig: int) -> tuple[str, str]:
    """Escalera con la PROFUNDIDAD REAL del bróker. Devuelve (filas, nota).

    Recibe `dom` (diccionario con listas `ask` y `bid` de niveles con `price` y `volume`), el `bid` y `ask`
    actuales y `dig`, los decimales del símbolo. Las barras se escalan contra el mayor volumen del libro. `filas`
    es el HTML de la escalera y `nota` el aviso que indica que los datos son reales."""
    # Los asks se invierten para que el precio mayor quede arriba y el mejor ask pegado al spread.
    asks = list(reversed(dom["ask"]))      # mayor precio arriba
    bids = dom["bid"]                      # mejor bid arriba
    # Volumen máximo del libro (1 si está vacío, para evitar división por cero).
    vols = [e["volume"] for e in asks + bids] or [1]
    mx = max(vols)
    # Se arma la escalera: asks, spread y bids.
    filas = ""
    for e in asks:
        filas += _fila("ask", f"{e['volume']:g}", f"{e['price']:,.{dig}f}", int(e["volume"] / mx * 100))
    filas += _spread(ask, bid, dig)
    for e in bids:
        filas += _fila("bid", f"{e['volume']:g}", f"{e['price']:,.{dig}f}", int(e["volume"] / mx * 100))
    nota = "<div class='dom-nota'>Profundidad real del bróker (libro de órdenes).</div>"
    return filas, nota


def filas_demo(bid: float, ask: float, dig: int, point: float) -> tuple[str, str]:
    """Sin profundidad del bróker: escalera DEMO sobre el precio en vivo. Devuelve (filas, nota).

    Recibe `bid`, `ask`, `dig` (decimales) y `point` (tamaño del punto). Genera niveles escalonados alrededor del
    spread con los volúmenes de muestra `VOL_ASK` y `VOL_BID`; los precios son reales y los volúmenes ficticios, lo
    que advierte la `nota`."""
    # Separación entre niveles: el spread, con un mínimo de 5 puntos para que las filas no se solapen.
    paso = round(max(ask - bid, point * 5), dig) or point
    filas = ""
    # Asks: del nivel más lejano (arriba) al mejor ask (pegado al spread).
    for i, vol in enumerate(VOL_ASK):
        nivel = len(VOL_ASK) - 1 - i
        px = round(ask + nivel * paso, dig)
        filas += _fila("ask", str(vol), f"{px:,.{dig}f}", int(vol / MAXVOL * 100))
    filas += _spread(ask, bid, dig)
    # Bids: del mejor bid (pegado al spread) hacia abajo.
    for i, vol in enumerate(VOL_BID):
        px = round(bid - i * paso, dig)
        filas += _fila("bid", str(vol), f"{px:,.{dig}f}", int(vol / MAXVOL * 100))
    nota = ("<div class='dom-nota'><b>Vista demostrativa.</b> Precios Bid/Ask reales "
            "en vivo; volúmenes de muestra (XM no entrega profundidad de mercado).</div>")
    return filas, nota


def html_escalera(filas: str, nota: str) -> str:
    """Devuelve el HTML final del DOM: encabezado de columnas (Volumen/Precio), las `filas` y la `nota`."""
    return "<div class='dom-cols'><span>Volumen</span><span>Precio</span></div>" + filas + nota


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara escalera .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
