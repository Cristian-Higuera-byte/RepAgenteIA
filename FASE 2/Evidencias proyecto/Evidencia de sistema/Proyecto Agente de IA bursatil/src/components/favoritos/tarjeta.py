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

"""Tarjeta «burbuja» de un favorito: contorno degradé verde (sube) / rojo (baja), ícono, nombre, precio en
vivo, variación y flecha de tendencia.

Solo construye cadenas HTML; los estilos viven en estilos.css y los números en vivo los repinta el
script del feed (flujo_precios) a partir de los atributos `data-pj-*` que genera `_en_vivo`.
"""
from __future__ import annotations

import streamlit as st

# Generador de íconos compartido por todo el dashboard (se importa con alias privado porque este módulo define su propia `icono_activo`).
from components.iconografia import icono_activo as _icono
# Generador de atributos data-pj-* para que el feed en vivo actualice precio y variación.
from components.flujo_precios import atributos as _en_vivo


def icono_activo(ticker: str, size: int = 30) -> str:
    """Ícono del activo (estilo XM). Lo define components/iconos.py para todo el
    dashboard; se mantiene aquí por compatibilidad con quien lo importa."""
    return _icono(ticker, size)


def formatear_precio(precio: float) -> str:
    """Formatea un precio para la tarjeta: 2 decimales si es 100 o más, 5 decimales si es menor (pares de divisas)."""
    if precio >= 100:
        return f"{precio:,.2f}"
    return f"{precio:,.5f}"


def tarjeta_html(tk: str, datos: dict) -> str:
    """Construye el HTML de la tarjeta de un favorito.

    Recibe el ticker `tk` y `datos` (diccionario ticker -> {precio, var, sube}). Si el ticker no tiene
    datos usa valores neutros. Devuelve la cadena HTML con clases `up`/`down` (contorno verde o rojo)
    y `sel` si es el activo seleccionado en session_state. Precio y variación llevan atributos
    `data-pj-*` para que el feed del navegador los actualice sin recargar Streamlit.
    """
    # Datos del activo con valores por defecto si aún no hay cotización.
    item = datos.get(tk, {"precio": 0.0, "var": "", "sube": True})
    # Dirección del día: define la clase CSS, el color y la flecha.
    sube = item.get("sube", True)
    dir_cls = "up" if sube else "down"
    color = "#3fb950" if sube else "#f85149"
    flecha = "↗" if sube else "↘"
    # Textos a mostrar; el nombre quita los puntos suspensivos con que se marcan algunos símbolos.
    precio = item.get("precio", 0.0)
    var = item.get("var", "") or "0.00 (0.00%)"
    nombre = tk.replace("...", "")
    # Marca la tarjeta del activo que está abierto en el gráfico.
    sel = " sel" if st.session_state.get("activo_seleccionado") == tk else ""
    # Composición final de la tarjeta (ícono, ticker, precio, variación y flecha).
    return (
        f"<div class='fav-card {dir_cls}{sel}'>"
        f"<span class='fav-ic'>{icono_activo(tk)}</span>"
        "<div class='fav-l'>"
        f"<div class='fav-tk'>{nombre}</div>"
        "<div class='fav-row'>"
        f"<span class='fav-px' {_en_vivo(tk, 'px')}>{formatear_precio(precio)}</span>"
        f"<span class='fav-var' {_en_vivo(tk, 'var')} style='color:{color};'>{var}</span>"
        "</div></div>"
        f"<span class='fav-arrow' style='color:{color};'>{flecha}</span>"
        "</div>"
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
