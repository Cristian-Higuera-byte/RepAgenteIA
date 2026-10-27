# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara fila .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fila de un activo de la lista: tarjeta con ícono, precio y variación en vivo, y sus tres botones
(seleccionar, favorito y quitar).

Los botones se superponen a la tarjeta mediante estilos.css (claves de contenedor `wlrow_*`, `wlsel_*`,
`wlfav_*` y `wlrm_*`). Precio y variación llevan atributos `data-pj-*` para el feed en vivo.
"""
import html
import re

import streamlit as st

# Ícono del activo, acciones de lista/favoritos, atributos del feed y gestor de la watchlist.
from componentes_plataforma.iconografia import icono_activo
from componentes_plataforma.lista_activos.acciones import agregar_favorito, quitar_de_lista, quitar_favorito
from componentes_plataforma.flujo_precios import atributos as _en_vivo
from herramientas import gestor_lista_activos as wl


# TITULO DIBUJAR FILA

def dibujar_fila(ticker: str, elemento: dict) -> None:
    """Dibuja una fila de la lista de activos con sus tres botones de acción.

    Recibe el `ticker` y `item`, el diccionario de mercado (nombre, precio, var, sube). Pinta la tarjeta
    con ícono, símbolo, nombre, precio y variación, y añade botones invisibles/pequeños: seleccionar
    (fija `activo_seleccionado` y relanza toda la app), estrella de favorito y ✕ para quitar de la lista.
    """
    # Nombre visible del símbolo y slug seguro para las claves de widgets.
    base = wl.nombre_visible(ticker)
    slug = re.sub(r"\W", "", ticker)
    # Estado de la fila: seleccionada, color según tendencia.
    is_seleccionado = (st.session_state.activo_seleccionado == ticker)
    color_variacion = "#2ebd85" if elemento.get("sube", True) else "#f6465d"

    # Precio con formato: con signo de dólar y 2 decimales si supera 100, si no 5 decimales.
    precio_valor = elemento.get('precio', 1.0)
    formato_precio = f"${precio_valor:,.2f}" if precio_valor > 100 else f"{precio_valor:,.5f}"

    # Textos escapados para insertarlos de forma segura en HTML.
    nombre = html.escape(str(elemento.get('nombre', ticker)))
    variacion = html.escape(str(elemento.get('var', '+0.00%')))
    clase_seleccion = " sel" if is_seleccionado else ""
    dir_cls = "up" if elemento.get("sube", True) else "down"

    # Aspecto y ayuda de la estrella según el estado de favorito.
    es_favorito = ticker in st.session_state.get("favoritos", [])
    estrella = ":material/star:" if es_favorito else ":material/star_border:"
    ayuda = "Quitar de favoritos" if es_favorito else "Agregar a favoritos"

    # Contenedor con clave propia por fila: el CSS lo usa para superponer los botones a la tarjeta.
    with st.container(key=f"wlrow_{slug}"):
        # Tarjeta visual del activo
        st.markdown(f"""
            <div class='lista-activos-fila {dir_cls}{clase_seleccion}'>
                {icono_activo(ticker, 34)}
                <div class='lista-activos-medio'>
                    <div class='lista-activos-ticket'>{html.escape(base)}</div>
                    <div class='lista-activos-nombre'>{nombre}</div>
                </div>
                <div class='lista-activos-derecha'>
                    <div class='lista-activos-precio' {_en_vivo(ticker, 'px', pre='$' if precio_valor > 100 else '')}>{formato_precio}</div>
                    <div class='lista-activos-variacion' {_en_vivo(ticker, 'var', up='#2ebd85', dn='#f6465d')} style='color: {color_variacion};'>{variacion}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Botón invisible que cubre toda la fila -> selecciona el activo.
        # scope="app" fuerza una reejecución de TODA la app (no solo de
        # este fragmento), que es lo que hace que componentes_plataforma/grafico/panel.py
        # -- que lee este mismo st.session_state.activo_seleccionado --
        # cambie de inmediato el precio, el símbolo y el gráfico en vivo.
        if st.button("Seleccionar", key=f"wlsel_{slug}"):
            # OJO: no mostrar elementos (st.toast) aquí dentro del
            # fragmento justo antes de st.rerun(scope="app"): provoca
            # el error de frontend "Cannot set a node at a delta path"
            # y deja la app en blanco al cambiar de activo.
            st.session_state.activo_seleccionado = ticker
            st.rerun(scope="app")

        # Estrella de favoritos
        if st.button(
            estrella,
            key=f"wlfav_{slug}",
            help=ayuda,
            type="primary" if es_favorito else "secondary",
        ):
            if es_favorito:
                quitar_favorito(ticker)
            else:
                agregar_favorito(ticker)
            st.rerun(scope="app")

        # Quitar de mi lista (✕)
        if st.button(":material/close:", key=f"wlrm_{slug}", help="Quitar de mi lista"):
            quitar_de_lista(ticker)
            st.rerun(scope="app")


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- FIN Piña y Jara fila .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
