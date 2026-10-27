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

"""Panel central: la cabecera de precio, el gráfico y los botones invisibles de cierre de posiciones.

Es el punto de entrada que usa `aplicacion.py` para dibujar la zona principal del dashboard. Junta la barra de
precio (`cabecera_precio`), el HTML del gráfico ensamblado (`ensamblador`) incrustado con `components.html`, y los
botones ocultos de Streamlit que el JS del gráfico pulsa para cerrar posiciones o cambiar de activo.
"""
from __future__ import annotations

import json
import os
from types import ModuleType
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from componentes_plataforma.conectar_cuenta import url_servidor
from componentes_plataforma.grafico.cabecera_precio import renderizar_cabecera_precio
from componentes_plataforma.grafico.ensamblador import html_grafico
from componentes_plataforma.grafico.simbolo import info_simbolo, limpiar_simbolo
from componentes_plataforma.posiciones import gatillos_cierre, js_posiciones
from herramientas import permisos_plan
from herramientas.puente_mt5 import inicializar_mt5
from herramientas.gestor_lista_activos import nombre_visible

# URL de la API que sirve las velas al gráfico (/velas y /ultima).
# Se puede sobrescribir con la variable de entorno MT5_API_URL; por defecto, el servidor local en el puerto 8000.
API_URL = os.environ.get("MT5_API_URL", "http://localhost:8000")


# TITULO LISTA ACTIVOS

def _lista_activos(activo_visible: str) -> str:
    """Activos que ofrece el selector del gráfico en pantalla completa (la watchlist del usuario), como JSON para el JS.
    Deja en la sesión los tickers en el mismo orden: posiciones_grafico.gatillos_cierre() crea un botón oculto por cada
    uno y el JS del gráfico pulsa el nº i para cambiar de activo sin salir de la pantalla completa."""
    # Datos de mercado en sesión (nombre por ticker) y lista de seguimiento; si no hay watchlist se usan las claves de los datos.
    info = st.session_state.get("datos_mercado_real") or {}
    tickers = list(st.session_state.get("watchlist_simbolos") or info.keys())
    if not tickers:
        tickers = [st.session_state.get("activo_seleccionado", "EURUSD...")]
    tickers = tickers[:40]
    # El módulo de íconos es opcional: si falla la importación, el selector se muestra sin íconos.
    try:
        from componentes_plataforma.iconografia import icono_activo
    except Exception:  # noqa: BLE001 - sin íconos el selector sigue funcionando
        icono_activo = None
    # Un diccionario por activo con claves cortas para el JS: t=ticker, b=nombre visible, n=nombre largo, i=ícono, a=activo actual.
    lista = []
    for t in tickers:
        try:
            icono = icono_activo(t, 26) if icono_activo else ""
        except Exception:  # noqa: BLE001
            icono = ""
        lista.append({
            "t": t, "b": nombre_visible(t), "n": str((info.get(t) or {}).get("nombre", "")),
            "i": icono, "a": limpiar_simbolo(t) == activo_visible,
        })
    # Orden compartido con gatillos_cierre(), que crea un botón oculto por cada ticker.
    st.session_state["_grafico_lista_activos"] = tickers
    # Se escapa "</" para que el JSON no cierre por error una etiqueta script al incrustarse en el HTML.
    return json.dumps(lista).replace("</", "<\\/")


# TITULO RENDERIZAR PANEL CENTRAL

def renderizar_panel_central(main: Optional[ModuleType] = None) -> None:
    """Dibuja el panel central completo: cabecera de precio, gráfico interactivo y botones ocultos de cierre.

    `main` se acepta por compatibilidad con quien la invoca y no se usa. Efectos secundarios: inicializa MT5,
    lee `activo_seleccionado` de la sesión, consulta decimales/pip del símbolo y emite componentes de Streamlit.
    """
    # Conexión con MT5 (idempotente) antes de pedir datos del símbolo.
    inicializar_mt5()

    # Símbolo elegido por el usuario, sin los puntos suspensivos de la lista, y su precisión.

    activo_actual = st.session_state.get("activo_seleccionado", "EURUSD...")
    activo_visible = limpiar_simbolo(activo_actual)
    digits, pip = info_simbolo(activo_visible)

    # Barra de precio en vivo encima del gráfico.
    renderizar_cabecera_precio(activo_visible, digits)

    # HTML final del gráfico con símbolo, API, decimales, pip, posiciones y lista de activos ya sustituidos.
    activos_json = _lista_activos(activo_visible)
    # Límites del plan del usuario para el gráfico (indicadores, símbolos comparados, velas del backtest y Replay)
    html_chart = html_grafico(activo_visible, url_servidor(API_URL), digits, pip, js_posiciones(activo_visible), activos_json,
                              json.dumps(permisos_plan.para_grafico()))
    # Iframe de 750 px de alto con el gráfico.
    components.html(html_chart, height=750)
    gatillos_cierre()   # ✕ de las líneas → modal de cierre


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
