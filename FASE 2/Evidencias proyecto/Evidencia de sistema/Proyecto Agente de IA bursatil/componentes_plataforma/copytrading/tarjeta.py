# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara tarjeta .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Tarjeta de una estrategia en el listado (nombre, riesgo, sparkline, rentabilidad y métricas).

El HTML devuelto usa las clases ct-* definidas en estilos.css.
"""
from html import escape

from componentes_plataforma.copytrading.datos import RIESGO_CLS, RIESGO_TEXTO
from componentes_plataforma.copytrading.graficos import avatar, minilinea


# TITULO TARJETA HTML

def tarjeta_html(e: dict) -> str:
    """Construye el HTML de la tarjeta de una estrategia para el listado.

    Recibe `e`, el diccionario de la estrategia, y devuelve una cadena HTML con el avatar,
    nombre, gestor, insignia de riesgo, sparkline, rentabilidad a un mes y la cuadrícula
    de métricas (fondos, invertido, inversión mínima, comisión, inversores y drawdown).
    """
    # Clase CSS de la insignia según el nivel de riesgo.
    rcls = RIESGO_CLS[e["riesgo"]]
    return (
        "<div class='copytrading-tarjeta'>"
        "<div class='copytrading-cabecera'>"
        f"<span class='copytrading-av'>{avatar(e['nombre'])}</span>"
        f"<div><div class='copytrading-nombre'>{escape(str(e['nombre']))}</div><div class='copytrading-gestion'>@{escape(str(e['gestor']))}</div></div>"
        f"<span class='copytrading-insignia {rcls}'>{RIESGO_TEXTO[e['riesgo']]}</span>"
        "</div>"
        "<div class='copytrading-medio'>"
        f"{minilinea(e['id'], serie=e.get('spark'))}"
        f"<div style='text-align:right;'><div class='copytrading-rentabilidad-etiqueta'>Rentabilidad 1 mes</div>"
        f"<div class='copytrading-rentabilidad'>{e['rent']:.2f}%</div></div>"
        "</div>"
        "<div class='copytrading-cuadricula'>"
        f"<div><div class='k'>Fondos propios</div><div class='v'>${e['fondos']:,}</div></div>"
        f"<div><div class='k'>Invertido</div><div class='v'>${e['invertido']:,}</div></div>"
        f"<div><div class='k'>Inversión mín.</div><div class='v'>${e['inv_min']:,}</div></div>"
        f"<div><div class='k'>Comisión</div><div class='v'>{e['comision']}%</div></div>"
        f"<div><div class='k'>Inversores</div><div class='v'>{e['inversores']}</div></div>"
        f"<div><div class='k'>Drawdown</div><div class='v'>{e['drawdown']}%</div></div>"
        "</div></div>"
    )


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara tarjeta .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
