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

"""
barra_lateral/barra.py
----------------
Barra lateral de navegación (estilo terminal). Colapsada = solo iconos (70 px);
expandida = iconos + texto (220 px). Expande/colapsa SIN reejecutar Python: los
botones se dibujan SIEMPRE solo con el ícono y el texto del modo expandido lo agrega
el CSS con ::after; un script (estatico/barra_lateral.js) intercepta el clic del ☰ y alterna
la clase `pj-barra-lateral-expandido` en <html>, que el CSS anima. Al cargar la página parte retraída.

El CSS vive en estatico/barra_lateral.css con marcadores que `_css()` sustituye (selectores,
anchos y etiquetas por ítem); el JS del toggle en estatico/barra_lateral.js. Ambos se leen una
sola vez (lru_cache).
"""
import json
from functools import lru_cache
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from componentes_plataforma._estaticos import sin_creditos

# Carpeta con los archivos estáticos (CSS y JS) de la barra, junto a este módulo.
_ESTATICO = Path(__file__).resolve().parent / "estatico"

# Ítems de navegación, en el orden en que se dibujan: (icono material, clave, etiqueta visible al expandir).
# La clave identifica la vista en `st.session_state.navegacion_activo` y forma la clave del botón (nav_btn_CLAVE).
ITEMS = [
    (":material/home:", "home", "Inicio"),                       # panel de cuenta (estilo XM)
    (":material/candlestick_chart:", "trading", "Trading"),      # dashboard: gráfico + listas
    (":material/work:", "portafolio", "Cartera"),                # posiciones abiertas (bajo Trading)
    (":material/table_rows:", "cotizaciones", "Mercados"),   # tablas estilo Investing
    (":material/content_copy:", "copytrading", "Copy trading"),  # estrategias (mock)
    (":material/newspaper:", "noticias", "Noticias"),
    (":material/dashboard:", "resumen", "Resumen"),           # dashboard del portafolio (F)
    (":material/menu_book:", "journal", "Diario"),            # trading journal (E)
    (":material/science:", "laboratorio", "Laboratorio"),    # simulación de ingresos y del agente (cuenta demo)
    (":material/workspace_premium:", "planes", "Planes"),     # planes y precios (prueba de demanda: aún no se cobra)
    (":material/account_balance_wallet:", "billetera", "Billetera"),   # saldo virtual, recargas de prueba y pago de planes
]

# Anchos (px) de la barra lateral: colapsada / expandida.
ANCHO_COLAPSADO = 70
ANCHO_EXPANDIDO = 220
# Duración y curva de las transiciones CSS al expandir/colapsar.
_ANIM = ".22s ease"
# Selector de la columna de Streamlit que contiene el marcador .pj-navegacion (la barra lateral completa).
_COL = 'div[data-testid="stColumn"]:has(.pj-navegacion)'
# Selector del estado expandido: el JS alterna la clase pj-barra-lateral-expandido en el elemento html.
_EXP = "html.pj-barra-lateral-expandido"
# Selector de la hoja «Más» del celular: barra_lateral.js alterna la clase pj-mas-abierto en el elemento html.
_MAS = "html.pj-mas-abierto"


# TITULO LEER ESTATICO

@lru_cache(maxsize=None)
def _leer_estatico(nombre: str) -> str:
    """Lee un archivo de barra_lateral/estatico/ (CSS/JS) y devuelve su texto.

    Recibe `nombre`, el nombre del archivo dentro de la carpeta estática. Quita el recuadro
    de créditos con `sin_creditos` y cachea el resultado en memoria (lru_cache) para leer el
    disco una sola vez por proceso. Devuelve cadena vacía si el archivo no se puede leer.
    """
    try:
        return sin_creditos((_ESTATICO / nombre).read_text(encoding="utf-8"))
    except OSError:
        return ""


# TITULO ESTILOS

def _estilos() -> str:
    """Devuelve el CSS de la barra listo para inyectar, envuelto en una etiqueta style.

    Toma estatico/barra_lateral.css y sustituye sus marcadores por los selectores, anchos
    en px, transición y etiquetas por ítem calculados desde las constantes de este módulo,
    de modo que cambiar un ancho o un ítem en Python actualiza el CSS sin tocarlo.
    """
    # Texto de cada botón en modo expandido (CSS ::after), generado desde ITEMS.
    etiquetas = "\n".join(
        f'    {_EXP} .st-key-navegacion_boton_{clave} button::after {{ content: {json.dumps(texto)}; }}'
        for _, clave, texto in ITEMS
    ) + f'\n    {_EXP} .st-key-navegacion_soporte button::after {{ content: "Soporte"; }}'
    # Etiquetas de la hoja «Más» del celular (clase pj-mas-abierto en html): las mismas secciones más «Soporte» y el botón que la cierra.
    etiquetas += "\n" + "\n".join(
        f'    {_MAS} .st-key-navegacion_boton_{clave} button::after {{ content: {json.dumps(texto)}; }}'
        for _, clave, texto in ITEMS
    ) + (f'\n    {_MAS} .st-key-navegacion_soporte button::after {{ content: "Soporte"; }}'
         f'\n    {_MAS} .st-key-navegacion_mas button::after {{ content: "Cerrar"; }}')

    # Texto bajo cada icono de la barra inferior del celular (siempre visible, sin clase en html): una regla por sección y «Más».
    etiquetas_movil = "\n".join(
        f'    .st-key-navegacion_boton_{clave} button::after {{ content: {json.dumps(texto)}; }}'
        for _, clave, texto in ITEMS
    ) + '\n    .st-key-navegacion_mas button::after { content: "Más"; }'

    # Sustituye cada marcador del CSS por su valor real (anchos, selectores, animación, etiquetas)
    css = (_leer_estatico("barra_lateral.css")
           .replace("__ETIQUETAS_MOVIL__", etiquetas_movil)
           .replace("__PAD_COL__", str(ANCHO_COLAPSADO + 20))
           .replace("__PAD_EXP__", str(ANCHO_EXPANDIDO + 20))
           .replace("__ANCHO_COL__", str(ANCHO_COLAPSADO))
           .replace("__ANCHO_EXP__", str(ANCHO_EXPANDIDO))
           .replace("__ANIM__", _ANIM)
           .replace("__ETIQUETAS__", etiquetas)
           .replace("__EXP__", _EXP)
           .replace("__COL__", _COL))
    return f"<style>\n{css}\n</style>"


# TITULO IR A VISTA

def _ir_a_vista(clave: str) -> None:
    """Guarda en `st.session_state.navegacion_activo` la vista que se acaba de elegir (la de Planes además anota que se llegó desde el menú).

    Se usa como `on_click` de los botones de la barra: Streamlit lo ejecuta antes de volver a correr el script, de modo
    que la vista nueva se dibuja en una sola pasada. Recibe la clave de la vista y no devuelve nada."""
    if clave == "planes":      # la vista de Planes recuerda desde dónde se llegó (aquí, el menú) para la prueba de demanda
        from componentes_plataforma.planes import ir_a_planes
        ir_a_planes("menu")
        return
    st.session_state.navegacion_activo = clave


# TITULO RENDERIZAR BARRA NAVEGACION

def renderizar_barra_navegacion():
    """Dibuja la barra lateral de navegación dentro de la columna que la contiene.

    Inyecta el CSS y el marcador .pj-navegacion, el logo, el script del toggle (sin altura) y un
    botón de solo icono por cada ítem de ITEMS; el activo se pinta como primary. Al pulsar
    un botón guarda su clave en `st.session_state.navegacion_activo` (con `on_click`, sin `st.rerun()`). El botón de
    Soporte solo muestra un aviso (`st.toast`). Si `navegacion_activo` no existe, inicia en "trading".
    """
    # Vista inicial al entrar
    if "navegacion_activo" not in st.session_state:
        st.session_state.navegacion_activo = "trading"  # al entrar, arranca en los gráficos

    # CSS de la barra más el marcador .pj-navegacion que usan los selectores :has()
    st.markdown(_estilos() + '<div class="pj-navegacion"></div>', unsafe_allow_html=True)

    # Logo: "P&J" (gradiente) + "Piña & Jara" (solo expandida)
    st.markdown(
        "<div class='pj-logo'><span class='pj-logo-pj'>P&amp;J</span>"
        "<span class='pj-logo-texto'>Piña &amp; Jara</span></div>",
        unsafe_allow_html=True,
    )

    # Script que alterna la barra sin reejecutar Python (estatico/barra_lateral.js)
    with st.container(key="pj_sbjs"):
        components.html(f"<script>\n{_leer_estatico('barra_lateral.js')}\n</script>", height=0)

    # Botones SIEMPRE con solo el ícono (como la barra colapsada original);
    # el texto del modo expandido lo pone el CSS (::after).
    for icono, clave, _etiqueta in ITEMS:
        # El botón de la vista activa se marca como primary (verde por CSS)
        activo = st.session_state.navegacion_activo == clave
        tipo = "primary" if activo else "secondary"
        # El cambio de vista se hace en un on_click: Streamlit lo ejecuta ANTES de correr el script, así la página se
        # dibuja una sola vez con la vista nueva (con `st.rerun()` el script corría dos veces por cada clic).
        st.button(icono, key=f"navegacion_boton_{clave}", type=tipo, on_click=_ir_a_vista, args=(clave,))

    # Soporte: se empuja al fondo con margin-top:auto (ver CSS), sin espaciador fijo.
    if st.button(":material/headset_mic:", key="navegacion_soporte"):
        st.toast("Soporte técnico de Piña & Jara activo.")

    # «Más» (solo celular; el CSS lo oculta en escritorio): abre y cierra la hoja con todas las secciones. El clic lo atiende
    # barra_lateral.js alternando una clase en html, sin reejecutar Python.
    st.button(":material/more_horiz:", key="navegacion_mas")


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
