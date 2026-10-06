import json

import streamlit as st
import streamlit.components.v1 as components

# (icono material, clave, etiqueta visible al expandir)
ITEMS = [
    (":material/home:", "home", "Inicio"),                       # panel de cuenta (estilo XM)
    (":material/candlestick_chart:", "trading", "Trading"),      # dashboard: gráfico + listas
    (":material/table_rows:", "cotizaciones", "Cotizaciones"),   # tablas estilo Investing
    (":material/content_copy:", "copytrading", "Copy trading"),  # estrategias (mock)
    (":material/newspaper:", "noticias", "Noticias"),
    (":material/work:", "portafolio", "Cartera"),
    (":material/assignment:", "ordenes", "Órdenes"),
    (":material/bar_chart:", "analisis", "Análisis"),
    (":material/rocket_launch:", "promociones", "Promociones"),
    (":material/settings:", "ajustes", "Ajustes"),
]

# Anchos (px) de la barra lateral: colapsada / expandida.
ANCHO_COLAPSADO = 70
ANCHO_EXPANDIDO = 220
_ANIM = ".22s ease"

# ---------------------------------------------------------------------------
# Expandir / colapsar SIN reejecutar Python (animado)
# ---------------------------------------------------------------------------
# Antes el ☰ hacía st.rerun() de TODA la app y los botones se recreaban con otro
# contenido → recarga brusca. Ahora:
#   - Los botones se dibujan SIEMPRE como en la barra colapsada original
#     (st.button(":material/x:") → solo el ícono). Colapsada se ve idéntica.
#   - Expandida, el texto de cada botón lo agrega el CSS con ::after
#     (content: "Inicio"…), sin tocar el HTML de Streamlit.
#   - Un script intercepta el clic del ☰ (antes de que llegue a Streamlit) y
#     alterna la clase `pj-sb-exp` en <html>; el CSS anima anchos y márgenes.
#   - Al cargar la página / iniciar sesión parte SIEMPRE retraída; se abre solo
#     con el clic del usuario (no se recuerda entre recargas).
_JS_SIDEBAR = """
<script>
(function(){
  var P = window.parent, D, H;
  try { D = P.document; H = D.documentElement; } catch(e) { return; }
  function aplicar(exp){ H.classList.toggle('pj-sb-exp', exp); }
  // Al cargar la página (o iniciar sesión) la barra parte SIEMPRE retraída.
  // La bandera vive en la ventana: si Streamlit recrea este iframe al navegar
  // entre vistas, NO se vuelve a cerrar; se mantiene como el usuario la dejó.
  if (!P.__pjSbIniciada){
    P.__pjSbIniciada = true;
    H.classList.add('pj-sb-sinanim');
    aplicar(false);
    P.setTimeout(function(){ H.classList.remove('pj-sb-sinanim'); }, 80);
  }

  // Un solo oyente en el documento padre (se reemplaza si el iframe se recrea).
  // Fase de CAPTURA en document: corre antes que React; stopPropagation evita
  // que el clic dispare un rerun de Streamlit.
  if (P.__pjSbFn) D.removeEventListener('click', P.__pjSbFn, true);
  P.__pjSbFn = function(e){
    var b = e.target && e.target.closest && e.target.closest('.st-key-top_toggle button');
    if (!b) return;
    e.stopPropagation(); e.preventDefault();
    aplicar(!H.classList.contains('pj-sb-exp'));
  };
  D.addEventListener('click', P.__pjSbFn, true);
})();
</script>
"""

_COL = 'div[data-testid="stColumn"]:has(.pj-nav)'
_EXP = "html.pj-sb-exp"


def _css() -> str:
    # Texto de cada botón en modo expandido (CSS ::after)
    etiquetas = "\n".join(
        f'    {_EXP} .st-key-nav_btn_{clave} button::after {{ content: {json.dumps(txt)}; }}'
        for _, clave, txt in ITEMS
    ) + f'\n    {_EXP} .st-key-nav_soporte button::after {{ content: "Soporte"; }}'

    return f"""
<style>
    /* ====== Animación (desactivada un instante al cargar) ====== */
    .block-container, .st-key-barra_nav_fija, {_COL} {{
        transition: padding {_ANIM}, left {_ANIM}, width {_ANIM},
                    max-width {_ANIM}, flex-basis {_ANIM} !important;
    }}
    html.pj-sb-sinanim .block-container,
    html.pj-sb-sinanim .st-key-barra_nav_fija,
    html.pj-sb-sinanim {_COL} {{ transition: none !important; }}

    /* El contenido se desplaza el ancho de la barra lateral (que va FIJA)
       + un espacio de separación, para que no quede pegado a ella. */
    .block-container {{ padding-left: {ANCHO_COLAPSADO + 20}px !important; }}
    {_EXP} .block-container {{ padding-left: {ANCHO_EXPANDIDO + 20}px !important; }}

    /* Barra superior fija: empieza donde termina la barra lateral */
    .st-key-barra_nav_fija {{
        left: {ANCHO_COLAPSADO}px !important; width: calc(100% - {ANCHO_COLAPSADO}px) !important;
    }}
    {_EXP} .st-key-barra_nav_fija {{
        left: {ANCHO_EXPANDIDO}px !important; width: calc(100% - {ANCHO_EXPANDIDO}px) !important;
    }}

    /* Evita que la columna principal se envuelva debajo de la barra lateral */
    div[data-testid="stHorizontalBlock"]:has(.pj-nav) {{ flex-wrap: nowrap !important; }}

    /* ====== Barra lateral FIJA (colapsada = diseño original) ====== */
    {_COL},
    div[data-testid="column"]:has(.pj-nav) {{
        background: #0d1117;
        border-right: 1px solid #30363d;
        /* Anclado a la IZQUIERDA (no centrado): mismo resultado visual que el
           original ((70-44)/2 = 13 px), pero el ícono no se desplaza mientras
           el ancho se anima al retraer/expandir. */
        padding: 12px 13px !important;
        align-items: flex-start;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        margin-top: 0 !important;
        height: 100vh !important;
        z-index: 100001;
        overflow: hidden;   /* sin scroll; recorta el texto durante la animación */
        flex: 0 0 {ANCHO_COLAPSADO}px !important;
        width: {ANCHO_COLAPSADO}px !important;
        max-width: {ANCHO_COLAPSADO}px !important;
    }}
    {_COL} > div,
    div[data-testid="column"]:has(.pj-nav) > div {{
        align-items: flex-start;
        gap: 4px;
        height: 100%;
    }}
    /* Soporte pegado al fondo */
    [class*="st-key-nav_soporte"] {{ margin-top: auto !important; }}

    /* Script del ☰: fuera del flujo, no ocupa espacio */
    .st-key-pj_sbjs {{ position: absolute !important; width: 0 !important;
                       height: 0 !important; overflow: hidden !important; }}

    /* Logo: "P&J" fijo en la misma x (9 px, centrado en 70 px) en ambos
       estados; "Piña & Jara" aparece a su derecha al expandir */
    .pj-logo {{
        display: flex; align-items: center; justify-content: flex-start; gap: 10px;
        margin: 0 -13px 18px; padding-left: 9px; white-space: nowrap;
    }}
    .pj-logo-pj {{
        font-weight: 900; font-size: 26px; letter-spacing: -1px;
        background: linear-gradient(135deg, #ff4b4b 0%, #ff8f00 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .pj-logo-txt {{ display: none; color: #8b949e; font-size: 15px; font-weight: 700; }}

    /* Botones: iconos sin caja (igual que el original) */
    {_COL} button,
    div[data-testid="column"]:has(.pj-nav) button {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #8b949e !important;
        width: 44px !important;
        height: 44px !important;
        min-height: 44px !important;
        padding: 0 !important;
        border-radius: 10px !important;
        margin: 0 !important;
        white-space: nowrap;
        overflow: hidden;               /* el texto se recorta, no empuja al ícono */
        /* app.py da a todos los botones `transition: all .15s`: aquí animaría
           también ancho/relleno y, mientras el botón seguía angosto, el texto
           comprimía al ícono hasta ocultarlo. Solo se animan los colores. */
        transition: background-color .15s ease, color .15s ease !important;
    }}
    /* El ícono nunca se comprime ni se centra en un espacio variable: el div
       interno de Streamlit trae width:100% (centraba el ícono en un ancho que
       dependía del largo del texto → cada ícono en una x distinta). */
    {_COL} button > div {{ width: auto !important; flex: 0 0 auto !important; }}
    /* Expandida: el contenedor de Streamlit del botón también a todo el ancho
       (si no, el botón medía lo que su contenido y el texto quedaba recortado) */
    {_EXP} {_COL} [data-testid="stElementContainer"]:has(button),
    {_EXP} {_COL} .stButton {{ width: 100% !important; }}
    {_COL} button p,
    div[data-testid="column"]:has(.pj-nav) button p {{
        font-size: 24px !important;
        line-height: 1 !important;
    }}
    {_COL} button:hover,
    div[data-testid="column"]:has(.pj-nav) button:hover {{
        background: rgba(255,255,255,0.08) !important;
        color: #fff !important;
    }}

    /* Botón activo (type="primary") -> verde como en XM */
    {_COL} button[kind="primary"],
    div[data-testid="column"]:has(.pj-nav) button[kind="primary"],
    {_COL} [data-testid="stBaseButton-primary"] {{
        background: rgba(34,197,94,0.12) !important;
        color: #22c55e !important;
    }}

    /* ====== ESTADO EXPANDIDO (clase pj-sb-exp en <html>) ====== */
    {_EXP} {_COL} {{
        flex: 0 0 {ANCHO_EXPANDIDO}px !important;
        width: {ANCHO_EXPANDIDO}px !important;
        max-width: {ANCHO_EXPANDIDO}px !important;
        align-items: stretch !important;
    }}
    {_EXP} {_COL} > div {{ align-items: stretch !important; }}
    {_EXP} .pj-logo-txt {{ display: inline; animation: pjFade .2s ease .1s both; }}
    /* Botones a todo el ancho; el ícono queda en la misma x que colapsada
       (13 px de la columna + 10 px de relleno = 23 px) */
    {_EXP} {_COL} button {{
        width: 100% !important;
        justify-content: flex-start !important;
        padding: 0 10px !important;
        gap: 14px;
    }}
    {_EXP} {_COL} button::after {{
        font-size: 14px; font-weight: 600; line-height: 1;
        animation: pjFade .2s ease .1s both;
    }}
{etiquetas}
    @keyframes pjFade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
</style>
"""


def renderizar_barra_navegacion():
    if "nav_activo" not in st.session_state:
        st.session_state.nav_activo = "trading"  # al entrar, arranca en los gráficos

    st.markdown(_css() + '<div class="pj-nav"></div>', unsafe_allow_html=True)

    # Logo: "P&J" (gradiente) + "Piña & Jara" (solo expandida)
    st.markdown(
        "<div class='pj-logo'><span class='pj-logo-pj'>P&amp;J</span>"
        "<span class='pj-logo-txt'>Piña &amp; Jara</span></div>",
        unsafe_allow_html=True,
    )

    # Script que alterna la barra sin reejecutar Python (ver _JS_SIDEBAR)
    with st.container(key="pj_sbjs"):
        components.html(_JS_SIDEBAR, height=0)

    # Botones SIEMPRE con solo el ícono (como la barra colapsada original);
    # el texto del modo expandido lo pone el CSS (::after).
    for icono, clave, etiqueta in ITEMS:
        activo = st.session_state.nav_activo == clave
        tipo = "primary" if activo else "secondary"
        if st.button(icono, key=f"nav_btn_{clave}", type=tipo):
            st.session_state.nav_activo = clave
            st.rerun()

    # Soporte: se empuja al fondo con margin-top:auto (ver CSS), sin espaciador fijo.
    if st.button(":material/headset_mic:", key="nav_soporte"):
        st.toast("Soporte técnico de Piña & Jara activo.")