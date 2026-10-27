# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara barra .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Barra de navegación superior (estilo terminal de trading): buscador, saldo y métricas, campana y usuario.

Ensambla, en una fila de columnas de Streamlit, el botón del menú (que alterna la barra
lateral mediante el JS de barra_lateral/estatico/barra_lateral.js), el botón que abre el buscador, las tarjetas de capital y
métricas, la campana de notificaciones y el menú del usuario. aplicacion.py la dibuja dentro del contenedor fijo
`barra_navegacion_fija`.
"""
import html
from pathlib import Path

import streamlit as st

from componentes_plataforma._estaticos import texto
from componentes_plataforma.barra_superior.tarjetas import chip, chips_metricas as _calcular_chips
from componentes_plataforma.barra_superior.datos import ICONO_TEMA
from componentes_plataforma.barra_superior.estilos import CSS
from componentes_plataforma.barra_superior.notificaciones import campana, usuario_id as _usuario_id
from componentes_plataforma.buscador import abrir_buscador
from herramientas import copiador
from herramientas.puente_mt5 import NOMBRE_BROKER
from componentes_plataforma.conectar_cuenta import entradas_menu, etiqueta_cuenta
from nucleo_agente import vigilancia

# Carpeta de este paquete (para localizar usuario_menu.html).
_DIR = Path(__file__).parent


# TITULO RENDERIZAR BARRA NAVEGACION

def renderizar_barra_navegacion(usuario: str = "Emilio Fuentes",
                                saldo: float | None = None,
                                moneda: str = "USD",
                                pl: float | None = None,
                                usuario_id: str | None = None,
                                metricas: dict | None = None):
    """Dibuja la barra superior fija con buscador, capital, métricas, campana y usuario.

    Recibe `usuario` (nombre mostrado), `saldo` (equity de MT5 o None si no hay conexión),
    `moneda`, `pl` (ganancia/pérdida flotante), `usuario_id` (id para las notificaciones; si
    es None se toma de la sesión) y `metricas` (diccionario de métricas de la barra, o None).
    Efectos secundarios: inicia el motor de vigilancias y el del copy trading (idempotentes), inyecta el CSS, y el
    botón del buscador activa la bandera del diálogo y reejecuta la app.
    """
    # Iniciales para el avatar (hasta dos palabras)
    iniciales = "".join([p[0] for p in usuario.split()[:2]]).upper() or "U"
    # Retoma las vigilancias activas tras un reinicio de la app
    try:
        vigilancia.iniciar_motor()   # idempotente: retoma las vigilancias activas tras reiniciar la app
    except Exception:  # noqa: BLE001 - la barra nunca debe fallar por esto
        pass
    try:
        copiador.iniciar_motor()     # idempotente: motor del copy trading (solo corre en modo multiusuario)
    except Exception:  # noqa: BLE001
        pass

    # Chip de saldo total de MT5 (equity). Si no hay dato, se muestra "—".
    if saldo is not None:
        saldo_texto = f"${saldo:,.2f} {moneda}"
    else:
        saldo_texto = f"— sin conexión {NOMBRE_BROKER}"

    # P/G flotante (de posiciones abiertas) junto al saldo, estilo XM.
    # Siempre se dibuja el <span> (aunque esté vacío) para que el feed en vivo
    # (data-pj-acc, ver componentes_plataforma/flujo_precios/) pueda rellenarlo.
    ganancia_perdida_texto = f"{pl:+,.2f}" if pl is not None and abs(pl) >= 0.005 else ""
    color_ganancia_perdida = "#3fb950" if (pl or 0) >= 0 else "#f85149"
    ganancia_perdida_span = (
        f"<span data-pj-acc='profit' style='font-size:13px; font-weight:700; color:{color_ganancia_perdida}; "
        f"font-family:monospace;'>{ganancia_perdida_texto}</span>"
    )
    attr_saldo = "data-pj-acc='equity'" if saldo is not None else ""
    # Tarjeta CAPITAL: equity + P/G flotante juntos (estilo XM). El <span
    # data-pj-acc='profit'> lo rellena el feed en vivo (componentes_plataforma/flujo_precios/).
    chip_capital = chip(
        "Capital",
        f"<span {attr_saldo} style='font-size:14px; font-weight:700; color:#3fb950; "
        f"font-family:monospace;'>{saldo_texto}</span>{ganancia_perdida_span}",
    )

    # Chips de Riesgo, Drawdown y Mercado (cadena vacía si no hay métricas)
    chips_metricas = _calcular_chips(metricas)
    # Etiqueta DEMO / REAL de la cuenta activa (vacía con el modo multiusuario apagado)
    chips_metricas = etiqueta_cuenta() + chips_metricas

    # Estilos de la navbar + del botón buscador
    st.markdown(CSS, unsafe_allow_html=True)

    # 4 tarjetas: Capital (equity + P&L) · Riesgo · Drawdown · Mercado.
    html_saldo = f"""
        <div style='display:flex; align-items:center; justify-content:flex-end; gap:7px; white-space:nowrap;'>
            {chip_capital}{chips_metricas}
            <span class='navegacion-icono' title='Tema' style='margin-left:6px;'>{ICONO_TEMA}</span>
        </div>
    """

    # Menú del usuario: plantilla HTML con marcadores sustituidos por las iniciales y el nombre
    html_usuario = (texto(_DIR / "usuario_menu.html")
                    .replace("__INICIALES__", html.escape(iniciales)).replace("__USUARIO__", html.escape(usuario))
                    .replace("__TOKEN__", str(st.query_params.get("s", "")))
                    .replace("__ENTRADAS_CUENTA__", entradas_menu()))

    # ☰ + buscador (corto, a la izquierda) + espacio + saldo/tema + campana + usuario
    c_interruptor, c_buscar, c_spacer, c_saldo, c_campana, c_usuario = st.columns(
        [0.2, 1.3, 1.49, 1.05, 0.16, 0.6], vertical_alignment="center")
    with c_interruptor:
        # El clic lo intercepta un script en el navegador (barra_lateral/estatico/barra_lateral.js)
        # que alterna la barra lateral con animación CSS, SIN reejecutar Python.
        st.button(":material/menu:", key="superior_interruptor")
    with c_buscar:
        # Abre el diálogo del buscador mediante la bandera de sesión y reejecuta
        if st.button("Buscar activo, par o ticker...", icon=":material/search:",
                     key="boton_abrir_buscador", width="stretch"):
            abrir_buscador()
            st.rerun()
    with c_spacer:
        # Columna vacía que empuja el resto a la derecha (ver estilos.css)
        st.empty()
    with c_saldo:
        st.markdown(html_saldo, unsafe_allow_html=True)
    with c_campana:
        # Campana de notificaciones del usuario
        campana(usuario_id or _usuario_id())
    with c_usuario:
        st.markdown(html_usuario, unsafe_allow_html=True)


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara barra .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
