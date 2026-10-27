# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara panel .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Panel de profundidad de mercado (DOM): cabecera fija y escalera que se refresca sola.

Lee de MT5 el Bid/Ask y, si existe, el libro de órdenes del activo seleccionado (`activo_seleccionado` en la
sesión) y dibuja el resultado con `escalera.py` y los estilos de `estilos.css`.

ESTADO: la escalera se centra en el Bid/Ask EN VIVO del activo (precios reales que se mueven con el mercado),
con VOLÚMENES DE MUESTRA cuando el bróker no publica el libro (en Forex/CFD de XM suele venir vacío). Si el
bróker lo publica (`mt5.market_book_get`), se muestra la profundidad real.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st
from proveedores.selector_mt5 import mt5  # type: ignore[import-untyped]

from components import _estaticos
from components.profundidad_mercado import escalera
from components.flujo_precios import intervalo
from tools.puente_mt5 import (MT5_LOCK, inicializar_mt5, obtener_precio_actual,
                              resolver_simbolo, obtener_dom)

# Ruta de la hoja de estilos del panel, junto a este archivo.
_CSS = Path(__file__).parent / "estilos.css"


def _dibujar_escalera(real: str) -> None:
    """Contenido de la escalera. Se ejecuta como FRAGMENTO (ver renderizar_panel_dom): solo este bloque se refresca.

    Recibe `real`, el símbolo real del bróker. Consulta el precio actual y la información del símbolo en MT5 y
    dibuja con `st.html` la escalera real (si el bróker publica el libro) o la demostrativa. Si no hay precio
    muestra un aviso. No devuelve nada."""
    inicializar_mt5()
    # Precio en vivo; sin él no se puede dibujar la escalera.
    t = obtener_precio_actual(real)
    if "error" in t or not (t.get("bid") or t.get("ask")):
        st.caption("Sin precio en vivo. ¿Está abierto MetaTrader 5?")
        return
    bid, ask = float(t.get("bid", 0)), float(t.get("ask", 0))
    # Información del símbolo (decimales y punto) para dar formato a los precios.
    try:
        with MT5_LOCK:
            info = mt5.symbol_info(real)
    except Exception:
        info = None
    # Decimales del símbolo (5 por defecto) y tamaño del punto (10 elevado a -decimales si falta).
    dig = int(getattr(info, "digits", 5) or 5) if info else 5
    point = (float(getattr(info, "point", 0.0) or 0.0) if info else 0.0) or (10 ** -dig)

    # Libro de órdenes con hasta 8 niveles por lado; si el bróker no lo publica se usa la vista demo.
    dom = obtener_dom(real, 8)
    if dom.get("disponible"):
        filas, nota = escalera.filas_reales(dom, bid, ask, dig)
    else:
        filas, nota = escalera.filas_demo(bid, ask, dig, point)
    st.html(escalera.html_escalera(filas, nota))


def renderizar_panel_dom():
    """Dibuja el panel DOM completo: estilos, cabecera con el activo y la escalera como fragmento.

    Lee `activo_seleccionado` de la sesión (por defecto EURUSD...). No recibe parámetros ni devuelve nada."""
    # Inyecta el CSS del panel.
    st.html(_estaticos.estilos(_CSS))
    # El contenedor con clave `dom_panel` permite darle estilo desde el CSS.
    with st.container(key="dom_panel"):
        # Activo elegido en la plataforma, su símbolo real en MT5 y el nombre para mostrar sin los puntos.
        activo = st.session_state.get("activo_seleccionado", "EURUSD...")
        real = resolver_simbolo(activo)
        visible = activo.replace("...", "").strip()
        st.html(f"<div class='dom-h'>Profundidad · {visible}</div>"
                f"<div class='dom-sub'>Libro de órdenes (DOM)</div>")

        # La escalera es un fragmento: se refresca sola cada 2 s (o la actualiza el feed en vivo) sin recargar la
        # página. IMPORTANTE: esta línea es la que dibuja la escalera; sin ella el panel solo muestra el título.
        st.fragment(run_every=intervalo("2s"))(_dibujar_escalera)(real)


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara panel .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
