# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara cuota .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Barra de uso del agente: porcentaje de la cuota mensual de tokens que lleva gastada el usuario, con el detalle debajo.

Se dibuja arriba del chat (ver `panel.py`). El color cambia con el uso: verde, ámbar desde `configuracion.UMBRAL_AVISO_PCT` y rojo desde
`configuracion.UMBRAL_CRITICO_PCT`; al agotarse muestra además el aviso de límite alcanzado. Los estilos (clases `cuota-ia-*`) están en
`componentes_plataforma/agente_paneles/estilos.css`. La cuenta de tokens sale de `herramientas/cuota_ia.py`. Con el uso en ámbar o rojo
agrega el botón «Ver planes» que lleva a la vista de Planes (prueba de demanda).
"""
from html import escape

import streamlit as st

from componentes_plataforma.planes import ir_a_planes
from herramientas import cuota_ia


# TITULO BARRA CUOTA

def barra_cuota(e: dict | None = None) -> None:
    """Dibuja la barra con el porcentaje de uso del mes, los tokens gastados sobre el total del plan y cuándo se renueva.

    Recibe el estado de la cuota (`cuota_ia.estado()`); si no se pasa, lo calcula. No devuelve nada."""
    e = e or cuota_ia.estado()
    detalle = (f"{cuota_ia.formato(e['usado'])} / {cuota_ia.formato(e['limite'])} tokens · quedan {cuota_ia.formato(e['restante'])} · "
               f"se renueva el {e['renueva']}")
    aviso = ("<div class='cuota-ia-limite'>Alcanzaste el límite de tu plan: el agente queda en pausa hasta que se renueve la cuota o cambies de plan.</div>"
             if e["agotada"] else "")
    st.html(
        f"<div class='cuota-ia cuota-ia-{e['nivel']}'>"
        f"<div class='cuota-ia-fila'><span class='cuota-ia-titulo'>Uso del agente · plan {escape(e['nombre'])}</span>"
        f"<span class='cuota-ia-pct'>{e['porcentaje']:.0f} %</span></div>"
        f"<div class='cuota-ia-barra'><div class='cuota-ia-relleno' style='width:{e['porcentaje']:.1f}%'></div></div>"
        f"<div class='cuota-ia-detalle'>{escape(detalle)}</div>{aviso}</div>"
    )
    # Con el uso alto o agotado se ofrece ver los planes: es el momento de mayor interés (y se anota el origen en la prueba de demanda).
    if e["nivel"] != "ok":
        st.button("Ver planes", key="cuota_ver_planes", icon=":material/workspace_premium:", on_click=ir_a_planes,
                  args=("cuota_agotada" if e["agotada"] else "barra_cuota",))


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara cuota .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
