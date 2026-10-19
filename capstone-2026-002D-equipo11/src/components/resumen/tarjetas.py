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

"""Tarjeta KPI del Resumen (icono, valor, pie y pastilla), con atributos data-pj-* para el feed en vivo.

Genera HTML con las clases `rs-card`, `rs-k`, `rs-v`, etc. (estilos en `estilos.css`) y toma los colores de acento
de `datos.ACC`. Es una función pura: no usa Streamlit.
"""
from components.resumen.datos import ACC


def tarjeta(clave, k, valor, unidad="", foot="", pill_html="", arrow=False, valcls="rs-neu",
          val_attrs=""):
    """Devuelve el HTML de una tarjeta KPI.

    Recibe `clave` (tipo de tarjeta, busca los colores y el ícono en `ACC`), `k` (título), `valor` (texto grande),
    `unidad` (moneda o sufijo pequeño), `foot` (línea inferior), `pill_html` (pastilla opcional, p. ej. el
    porcentaje), `arrow` (si es True añade una flecha según `valcls`) y `valcls` (clase de color: rs-up, rs-down o
    rs-neu).
    val_attrs: atributos data-pj-* para que el feed pinte el valor EN VIVO
    (sub-segundo, sin rerun) igual que el resto del dashboard."""
    # Acento de la barra lateral, ícono y colores del ícono para esta clave.
    acc, ico, icbg, icfg = ACC[clave]
    # Flecha hacia arriba o abajo solo cuando se pidió y el valor no es neutro.
    ar = ""
    if arrow:
        ar = ("<span class='rs-arrow'>▲</span>" if valcls == "rs-up"
              else "<span class='rs-arrow'>▼</span>" if valcls == "rs-down" else "")
    # Unidad y pie solo se dibujan si tienen contenido.
    u = f"<span class='u'>{unidad}</span>" if unidad else ""
    foot_html = f"<div class='rs-foot'>{foot}</div>" if foot else ""
    # Las variables CSS --acc, --icbg y --icfg alimentan los colores definidos en estilos.css.
    return (
        f"<div class='rs-card' style='--acc:{acc};--icbg:{icbg};--icfg:{icfg}'>"
        f"<div class='rs-ctop'><div class='rs-k'>{k}</div>"
        f"<div class='rs-cico'><span class='m'>{ico}</span></div></div>"
        f"<div class='rs-v'><span class='{valcls}' {val_attrs}>{ar}{valor}</span>{u}{pill_html}</div>"
        f"{foot_html}</div>"
    )


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
