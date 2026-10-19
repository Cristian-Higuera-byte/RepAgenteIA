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

"""Piezas HTML de los íconos: cajas, imágenes circulares, pares de banderas, índices, iniciales y logos.

Todo el HTML usa estilos en línea (el CSS global no interviene) y `<img>`; cada función devuelve una cadena
sin efectos secundarios. `caja` es el contenedor posicionado sobre el que se apilan las demás piezas.
"""
import html
import re
import zlib

# Plantilla de banderas, paleta de colores de iniciales y generador de SVG data-URI.
from components.iconografia.datos import FLAG, PALETA, svg_circulo


def caja(s: int, interior: str, ancho: int | None = None) -> str:
    """Contenedor del ícono: `<span>` relativo de alto `s` px (y ancho `ancho`, por defecto `s`) que aloja `interior`."""
    # Ancho efectivo de la caja.
    w = ancho or s
    # flex:0 0 evita que la caja se encoja dentro de filas flex.
    return (
        f"<span style='position:relative; display:inline-block; flex:0 0 {w}px; "
        f"width:{w}px; height:{s}px; vertical-align:middle;'>{interior}</span>"
    )


def imagen(src: str, d: int, left: float, top: float, z: int = 1, borde: bool = False,
        fondo: str = "transparent") -> str:
    """Imagen circular de diámetro `d` px posicionada de forma absoluta en (`left`, `top`) con capa `z`.

    `borde` agrega un aro oscuro para separar círculos superpuestos; `fondo` es el color tras la imagen.
    """
    # Aro del color del fondo de la app para recortar visualmente el círculo que queda delante.
    aro = "box-shadow:0 0 0 1.5px #0d1117;" if borde else ""
    return (
        f"<img src='{src}' alt='' style='position:absolute; left:{left:.1f}px; top:{top:.1f}px; "
        f"width:{d}px; height:{d}px; border-radius:50%; z-index:{z}; background:{fondo}; "
        f"object-fit:cover; {aro}'>"
    )


def iniciales(texto: str, s: int, z: int = 0) -> str:
    """Círculo de color con las dos primeras letras o dígitos de `texto` (tamaño `s`, capa `z`).

    El color sale de un hash estable (crc32) del texto para que un mismo activo siempre tenga el mismo color.
    """
    # Hasta 2 caracteres alfanuméricos en mayúscula ("?" si no hay ninguno).
    t = re.sub(r"[^A-Za-z0-9]", "", texto)[:2].upper() or "?"
    # Color estable elegido de la paleta según el hash del texto.
    color = PALETA[zlib.crc32(texto.encode()) % len(PALETA)]
    return (
        f"<span style='position:absolute; inset:0; border-radius:50%; background:{color}; "
        f"color:#fff; font-weight:800; font-size:{max(9, int(s * 0.38))}px; z-index:{z}; "
        f"display:flex; align-items:center; justify-content:center; "
        f"font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'>{html.escape(t)}</span>"
    )


def par(src_a: str, src_b: str, s: int) -> str:
    """Dos círculos superpuestos: A adelante-izquierda, B atrás-derecha."""
    # Diámetro de cada círculo (66% del tamaño) y posición vertical centrada.
    d = round(s * 0.66)
    top = (s - d) / 2
    return caja(s, imagen(src_b, d, s - d, top, z=1) + imagen(src_a, d, 0, top, z=2, borde=True))


def indice(pais: str, etiqueta: str, s: int) -> str:
    """Ícono de índice bursátil: bandera redonda del `pais` con una etiqueta (`etiqueta`) en la parte inferior."""
    # Diámetro de la bandera y tamaño de la letra de la etiqueta.
    d = round(s * 0.84)
    fs = max(6, round(s * 0.2))
    # Etiqueta pequeña centrada abajo.
    badge = (
        f"<span style='position:absolute; left:50%; bottom:-1px; transform:translateX(-50%); "
        f"z-index:3; background:#11151c; color:#e6edf3; font-size:{fs}px; font-weight:700; "
        f"line-height:1; padding:1px 3px; border-radius:3px; white-space:nowrap; "
        f"font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'>{etiqueta}</span>"
    )
    return caja(s, imagen(FLAG.format(pais), d, (s - d) / 2, 0, z=1) + badge)


def logo(url: str, s: int) -> str:
    """Logo COMPLETO dentro de un círculo blanco (object-fit: contain + margen).
    Hallazgo: con 'cover' los logos apaisados (Adidas 128×86) se recortaban al
    centro y el círculo quedaba en blanco."""
    # Margen interior para que el logo no toque el borde del círculo.
    m = max(2, round(s * 0.14))
    return (
        f"<span style='position:absolute; inset:0; border-radius:50%; background:#ffffff; "
        f"overflow:hidden; display:flex; align-items:center; justify-content:center;'>"
        f"<img src='{url}' alt='' style='width:{s - 2 * m}px; height:{s - 2 * m}px; "
        f"object-fit:contain;'></span>"
    )


def svg_iniciales(texto: str) -> str:
    """Círculo con iniciales como imagen (para combinarlo en `par`).

    Devuelve un data-URI SVG con hasta 3 caracteres de `texto` sobre un círculo de color estable.
    """
    # Hasta 3 caracteres escapados para HTML/SVG.
    t = html.escape(re.sub(r"[^A-Za-z0-9]", "", texto)[:3].upper() or "?")
    color = PALETA[zlib.crc32(texto.encode()) % len(PALETA)]
    # Letra más pequeña si hay 3 caracteres.
    fs = 11 if len(t) <= 2 else 9
    # Texto SVG centrado.
    figura = (f"<text x='16' y='16' text-anchor='middle' dominant-baseline='central' "
              f"font-family='Arial,sans-serif' font-weight='700' font-size='{fs}' fill='#fff'>{t}</text>")
    return svg_circulo(color, figura)


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
