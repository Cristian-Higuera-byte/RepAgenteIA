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

Genera HTML con las clases `resumen-tarjeta`, `resumen-k`, `resumen-v`, etc. (estilos en `estilos.css`) y toma los colores de acento
de `datos.ACC`. Es una función pura: no usa Streamlit.
"""
from componentes_plataforma.resumen.datos import ACC


# TITULO TARJETA

def tarjeta(clave, k, valor, unidad="", pie="", pastilla_html="", arrow=False, valcls="resumen-neutro",
          valor_attrs=""):
    """Devuelve el HTML de una tarjeta KPI.

    Recibe `clave` (tipo de tarjeta, busca los colores y el ícono en `ACC`), `k` (título), `valor` (texto grande),
    `unidad` (moneda o sufijo pequeño), `foot` (línea inferior), `pill_html` (pastilla opcional, p. ej. el
    porcentaje), `arrow` (si es True añade una flecha según `valcls`) y `valcls` (clase de color: resumen-sube, resumen-baja o
    resumen-neutro).
    val_attrs: atributos data-pj-* para que el feed pinte el valor EN VIVO
    (sub-segundo, sin rerun) igual que el resto del dashboard."""
    # Acento de la barra lateral, ícono y colores del ícono para esta clave.
    cuenta, icono, icbg, icfg = ACC[clave]
    # Flecha hacia arriba o abajo solo cuando se pidió y el valor no es neutro.
    ar = ""
    if arrow:
        ar = ("<span class='resumen-arrow'>▲</span>" if valcls == "resumen-sube"
              else "<span class='resumen-arrow'>▼</span>" if valcls == "resumen-baja" else "")
    # Unidad y pie solo se dibujan si tienen contenido.
    u = f"<span class='u'>{unidad}</span>" if unidad else ""
    pie_html = f"<div class='resumen-pie'>{pie}</div>" if pie else ""
    # Las variables CSS --acc, --icbg y --icfg alimentan los colores definidos en estilos.css.
    return (
        f"<div class='resumen-tarjeta' style='--acc:{cuenta};--icbg:{icbg};--icfg:{icfg}'>"
        f"<div class='resumen-copytrading-superior'><div class='resumen-k'>{k}</div>"
        f"<div class='resumen-copytrading-icono'><span class='m'>{icono}</span></div></div>"
        f"<div class='resumen-v'><span class='{valcls}' {valor_attrs}>{ar}{valor}</span>{u}{pastilla_html}</div>"
        f"{pie_html}</div>"
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
