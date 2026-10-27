# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara movil .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Elementos de la vista operativa que solo se ven en el celular (pantallas de hasta 1024 px (celulares y tablets)).

En escritorio el rail derecho ya ofrece los favoritos y el ticket; en el celular se agrega una barra fija «Vender / Comprar»
que muestra los precios en vivo y abre el ticket de órdenes. Se dibuja siempre y el CSS de `estilos.css` la oculta en
escritorio; la atiende `riel.js`, sin reejecutar Python. Los favoritos se eligen tocando el símbolo de la cabecera de precio
(`grafico/cabecera_precio.py`), que abre el panel «Favoritos»: una fila de chips ocupaba alto del gráfico y con un solo
favorito no se entendía, por eso se quitó.
"""
import streamlit as st


# TITULO RENDERIZAR BARRA OPERAR

def renderizar_barra_operar() -> None:
    """Dibuja la barra fija «Vender / Comprar» con el Bid y el Ask del activo mostrado.

    Los dos botones son HTML con atributos `data-pj-*`, que el feed del navegador (flujo_precios) rellena en vivo.
    Al pulsar cualquiera, `riel.js` abre el panel Operar (ticket de órdenes) sin reejecutar Python; la orden se confirma
    allí, nunca desde esta barra. No recibe parámetros ni devuelve nada."""
    # Importaciones locales para evitar importaciones circulares al cargar el paquete.
    from componentes_plataforma.flujo_precios import atributos
    from componentes_plataforma.grafico.simbolo import info_simbolo, limpiar_simbolo
    activo = limpiar_simbolo(st.session_state.get("activo_seleccionado", "EURUSD..."))
    decimales, _pip = info_simbolo(activo)
    with st.container(key="pj_barra_operar"):
        st.markdown(
            "<div class='pj-barra-op'>"
            f"<button type='button' class='pj-op-vender'><span>VENDER</span><b {atributos(activo, 'bid', d=decimales)}>—</b></button>"
            f"<button type='button' class='pj-op-comprar'><span>COMPRAR</span><b {atributos(activo, 'ask', d=decimales)}>—</b></button>"
            "</div>",
            unsafe_allow_html=True,
        )


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara movil .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
