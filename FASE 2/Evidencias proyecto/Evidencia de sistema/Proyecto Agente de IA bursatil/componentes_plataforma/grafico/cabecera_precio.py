# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara cabecera_precio .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""Barra de precio en vivo que va encima del gráfico (símbolo, precio, Bid/Ask y estado de la conexión).

Se dibuja con `st.markdown` dentro de un `st.fragment` que se vuelve a ejecutar solo cada cierto intervalo, de modo
que el resto del dashboard no se recarga. Cuando hay un feed en vivo activo, los números los actualiza el JS de
`flujo_vivo` a través de los atributos `data-*` que genera `atributos()`.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from componentes_plataforma.flujo_precios import atributos as _en_vivo, intervalo as _intervalo
from herramientas.puente_mt5 import NOMBRE_PROVEEDOR, obtener_precio_actual


# TITULO RENDERIZAR CABECERA PRECIO

def renderizar_cabecera_precio(activo_visible: str, digits: int) -> None:
    """Pinta la barra de precio (símbolo, último precio, Bid/Ask y estado de conexión) y la mantiene refrescada.

    Recibe el símbolo ya limpio (`activo_visible`) y la cantidad de decimales con que se formatean los precios.
    Efectos secundarios: consulta el tick a MT5 en cada refresco y guarda en `st.session_state` el último precio y
    el último color por símbolo, para saber si el precio subió o bajó respecto al refresco anterior.
    No devuelve nada; el HTML se emite directamente con `st.markdown`.
    """
    @st.fragment(run_every=_intervalo("2s"))   # con feed: lo pinta flujo_precios/
    def _cabecera_precio():
        """Fragmento autorrefrescable: lee el tick, decide el color de variación y emite la barra HTML."""
        # Tick actual del símbolo; si MT5 devuelve la clave "error" se considera desconectado.
        info_tick = obtener_precio_actual(activo_visible)
        conectado = "error" not in info_tick
        if conectado:
            precio_actual = info_tick.get("last", 0) if info_tick.get("last", 0) > 0 else info_tick.get("bid", 0)
        else:
            precio_actual = 0.0
        # Bid y Ask como float (0 si faltan); luego se exige además un precio positivo para dar por válida la conexión.
        bid = float(info_tick.get("bid", 0) or 0)
        ask = float(info_tick.get("ask", 0) or 0)
        conectado = conectado and precio_actual > 0

        # Claves de sesión por símbolo: último precio visto y último color usado (se conserva si el precio no cambia).
        clave = f"_prev_precio_{activo_visible}"
        clave_color = f"_color_precio_{activo_visible}"
        # Verde si el precio sube, rojo si baja; si no cambia se repite el color anterior. Gris cuando no hay conexión.
        if conectado:
            anterior = st.session_state.get(clave, precio_actual)
            if precio_actual > anterior:
                color_variacion_activo = "#3fb950"
            elif precio_actual < anterior:
                color_variacion_activo = "#f85149"
            else:
                color_variacion_activo = st.session_state.get(clave_color, "#3fb950")
            st.session_state[clave] = precio_actual
            st.session_state[clave_color] = color_variacion_activo
        else:
            color_variacion_activo = "#8b949e"

        # Indicador de estado (punto de color + texto) de la derecha de la barra.
        color_estado = "#3fb950" if conectado else "#f85149"
        texto_estado = "Conectado" if conectado else "Sin conexión"
        
        # Barra HTML: izquierda símbolo, origen, precio y Bid/Ask; derecha estado de la conexión.
        # En tablet y celular (hasta 992 px: tablets horizontales y pantallas más chicas) los datos pasan a dos filas: símbolo, origen y precio arriba; Bid/Ask abajo, a todo el ancho.
        # Los estilos en línea mandan sobre la hoja, por eso las reglas móviles llevan !important (llaves dobles por el f-string).
        st.markdown(f"""
            <style>
            /* tablets horizontales / pantallas medianas (iPad Pro en horizontal, notebooks pequeños) */
            @media (max-width: 992px) {{
                .pj-cab-precio {{ position: relative; padding: 6px 12px !important; margin-bottom: 6px !important; flex-wrap: nowrap !important; }}
                .pj-cab-precio-datos {{ flex-wrap: wrap; gap: 0 10px !important; }}
                .pj-cab-bidask {{ flex: 0 0 100%; font-size: 12px !important; }}
                .pj-cab-estado {{ position: absolute; top: 8px; right: 12px; font-size: 0 !important; }}
                .pj-cab-precio {{ padding: 4px 10px !important; margin: 6px 0 4px !important; }}
                .pj-cab-precio-datos {{ gap: 0 10px !important; }}
                .pj-cab-simbolo {{ font-size: 17px !important; }}
                .pj-cab-precio-datos > span[data-pj-f="px"] {{ font-size: 18px !important; }}
                .pj-cab-bidask {{ font-size: 11px !important; }}
                /* El símbolo es el botón que abre la lista de activos: se dibuja como botón (fondo, borde y flecha de color) y se hunde al tocarlo. */
                .pj-cab-simbolo {{ cursor: pointer; display: inline-flex; align-items: center; gap: 8px; background: #1f2733; border: 1px solid #3b4757; border-radius: 8px;
                    padding: 3px 9px 3px 11px !important; -webkit-tap-highlight-color: transparent; transition: background .15s, border-color .15s; }}
                .pj-cab-simbolo::after {{ content: ""; width: 7px; height: 7px; border-right: 2px solid #58a6ff; border-bottom: 2px solid #58a6ff; transform: rotate(45deg) translateY(-2px); }}
                .pj-cab-simbolo:active {{ background: #2b3646; border-color: #58a6ff; }}
                /* Horizontal bajo (celulares en horizontal, hasta 500 px de alto): una sola línea de 30 px, para dejarle alto al gráfico. */
                @media (orientation: landscape) and (max-height: 500px) {{
                    .pj-cab-precio {{ padding: 2px 10px !important; margin: 3px 0 3px !important; }}
                    .pj-cab-precio-datos {{ flex-wrap: nowrap !important; align-items: center; }}
                    .pj-cab-bidask {{ flex: 0 0 auto !important; }}
                    .pj-cab-estado {{ top: 50% !important; transform: translateY(-50%); }}
                }}
                /* Horizontal muy bajo (hasta 340 px de alto): letras más chicas y sin la insignia del origen. */
                @media (orientation: landscape) and (max-height: 340px) {{
                    .pj-cab-precio {{ padding: 1px 10px !important; margin: 2px 0 2px !important; }}
                    .pj-cab-simbolo {{ font-size: 14px !important; }}
                    .pj-cab-precio-datos > span[data-pj-f="px"] {{ font-size: 15px !important; }}
                    .pj-cab-bidask {{ font-size: 10px !important; }}
                    .pj-cab-origen {{ display: none !important; }}
                }}
            }}
            </style>
            <div class='pj-cab-precio' style='background-color: #161b22; padding: 10px 16px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;'>
                <div class='pj-cab-precio-datos' style='display: flex; align-items: center; gap: 14px;'>
                    <span class='pj-cab-simbolo' role='button' title='Ver lista de activos' style='font-size: 20px; font-weight: bold; color: #ffffff;'>{escape(activo_visible)}</span>
                    <span class='pj-cab-origen' style='background: #30363d; color: #8b949e; padding: 2px 8px; border-radius: 4px; font-size: 11px;'>{NOMBRE_PROVEEDOR}</span>
                    <span {_en_vivo(activo_visible, 'px', d=digits, flash=1)} style='font-size: 22px; font-weight: bold; font-family: monospace; color: {color_variacion_activo};'>{precio_actual:,.{digits}f}</span>
                    <span class='pj-cab-bidask' style='font-size: 14px; font-weight: 600; color: {color_variacion_activo};'>Bid:<span {_en_vivo(activo_visible, 'bid', d=digits)}>{bid:,.{digits}f}</span> | Ask: <span {_en_vivo(activo_visible, 'ask', d=digits)}>{ask:,.{digits}f}</span></span>
                </div>
                <div class='pj-cab-estado' style='font-size: 13px; color: #8b949e; font-weight: 600; display: flex; align-items: center; gap: 6px;'>
                    {texto_estado} <span style='color: {color_estado}; font-size: 16px;'>●</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Primera ejecución inmediata; después Streamlit la repite según run_every.
    _cabecera_precio()


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara cabecera_precio .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
