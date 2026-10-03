"""
app.py
------
Dashboard interactivo de Piña & Jara - Financial Terminal,
diseñado con distribución modular avanzada y alineación visual precisa.
"""
import os
import sys

# --- Arreglo de certificado SSL para rutas con tildes ---
try:
    import certifi
    import shutil
    import tempfile
    _ca_ascii = os.path.join(tempfile.gettempdir(), "cacert_ascii.pem")
    shutil.copyfile(certifi.where(), _ca_ascii)
    os.environ["SSL_CERT_FILE"] = _ca_ascii
    os.environ["CURL_CA_BUNDLE"] = _ca_ascii
except Exception:
    pass
# --------------------------------------------------------

from types import ModuleType
from typing import Optional
import streamlit as st

# Asegurar ruta raíz
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Intentar importar la lógica principal del backend
main: Optional[ModuleType] = None
try:
    import main
except ImportError:
    pass

# Importar componentes modulares
from components.central_panel import renderizar_panel_central
from components.favoritos_bar import renderizar_barra_favoritos
from components.market_data import actualizar_precios_mt5, cargar_datos_mercado
from components.watchlist import renderizar_watchlist
from components.nav_bar import renderizar_barra_navegacion as renderizar_nav_lateral
from components.top_navbar import renderizar_barra_navegacion as renderizar_nav_superior
from components.news_panel import renderizar_panel_noticias
from components.login import requerir_login

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard agente analitico Piña & Jara",
    page_icon="📈",
    layout="wide"
)

# ==========================================
# ESTILOS CSS GLOBALES (tema oscuro tipo terminal de trading)
# ==========================================
st.markdown("""
    <style>
        /* Ocultar la barra propia de Streamlit */
        [data-testid="stHeader"] { display: none; }
        [data-testid="stToolbar"] { display: none; }

        /* Ajuste de márgenes generales de la página.
           1er valor (padding-top) = hueco bajo la barra superior fija.
           Súbelo/bájalo para más/menos espacio; debe ir acoplado con el
           margin-top negativo de la barra lateral (más abajo, mismo número). */
        .block-container {
            padding: 1.5rem 1.5rem 2rem 1.2rem !important;
            max-width: 100%;
        }

        /* Fondo y tipografía base */
        .stApp { background-color: #0b0f19; color: #e6edf3; }
        html, body, [class*="css"] { font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }

        /* Jerarquía de títulos discreta */
        h1 { font-size: 24px !important; font-weight: 700 !important; }
        h2 { font-size: 20px !important; font-weight: 700 !important; }
        h3 { font-size: 18px !important; font-weight: 700 !important; }

        /* Botones oscuros y compactos */
        div.stButton > button {
            background-color: #161b22; color: #e6edf3; border: 1px solid #30363d;
            border-radius: 6px; font-size: 13px !important; padding: 4px 10px;
            min-height: 0; transition: all .15s ease;
        }
        div.stButton > button:hover { background-color: #21262d; border-color: #58a6ff; color: #ffffff; }

        /* Selectores oscuros */
        div[data-baseweb="select"] > div {
            background-color: #161b22 !important; border-color: #30363d !important;
        }
        .stSelectbox label, .stTextInput label, .stSlider label {
            font-size: 12px !important; color: #8b949e !important; font-weight: 600 !important;
        }

        /* Métricas */
        [data-testid="stMetricValue"] { font-size: 22px !important; }
        [data-testid="stMetricLabel"] { font-size: 18px !important; color: #8b949e !important; }

        /* Entrada del chat */
        .stChatInput textarea { background-color: #161b22 !important; }

        /* Tarjetas con borde */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #161b22;
            border-radius: 8px;
        }

        /* Barra de navegación superior FIJA */
        .st-key-barra_nav_fija {
            position: fixed !important;
            top: 0; left: 70px; right: 0;
            width: calc(100% - 70px) !important;
            z-index: 100000;
            background: #0d1117;
            border-bottom: 1px solid #1b2430;
            padding: 10px 24px;
            box-sizing: border-box;
        }
        .st-key-barra_nav_fija [data-testid="stVerticalBlock"] { gap: 0 !important; }
        .st-key-barra_nav_fija [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-barra_nav_fija [data-testid="stVerticalBlock"] {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
        }

        /* Barra lateral izquierda extendida sin forzar paddings excesivos */
        div[data-testid="stColumn"]:has(.pj-nav),
        div[data-testid="column"]:has(.pj-nav) {
            background: #0d1117 !important;
            border-right: 1px solid #30363d;
            min-height: 100vh;
            margin-top: -3.9rem !important;  /* = padding-top de .block-container */
            padding-top: 0 !important;
            z-index: 100001;
        }

        /* Baja el logo P&J para alinearlo con el buscador de la barra superior.
           Ajusta este valor (1.6rem) si necesitas subirlo o bajarlo un poco más. */
        .pj-logo {
            margin-top: -0.5rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# LOGIN (Supabase): protege el acceso al dashboard
# ==========================================
usuario_actual = requerir_login()

# Overlay de carga a pantalla completa en la primera entrada
_primera_carga = not st.session_state.get("datos_cargados", False)
_overlay = st.empty()
if _primera_carga:
    _overlay.markdown("""
        <div style='position:fixed; inset:0; background:#0b0f19; z-index:99999;
                    display:flex; flex-direction:column; align-items:center;
                    justify-content:center; gap:14px; color:#8b949e;'>
            <div style='font-size:18px; font-weight:600;'>Cargando terminal…</div>
            <div style='font-size:13px;'>Conectando a MetaTrader 5</div>
        </div>
    """, unsafe_allow_html=True)

# Obtener saldo MT5 para mostrarlo en la barra superior
from tools.mt5_bridge import inicializar_mt5, obtener_info_cuenta
inicializar_mt5()
_info_cuenta = obtener_info_cuenta()
_saldo_mt5 = _info_cuenta.get("equity") if "error" not in _info_cuenta else None
_moneda_mt5 = _info_cuenta.get("currency", "USD") if "error" not in _info_cuenta else "USD"

# Desplazamiento de la barra superior según el ancho de la barra lateral
# (colapsada 70px / expandida 220px) para que no se solapen.
_sidebar_w = 220 if st.session_state.get("sidebar_expandido", False) else 70
st.markdown(
    f"<style>.st-key-barra_nav_fija {{ left:{_sidebar_w}px !important; "
    f"width:calc(100% - {_sidebar_w}px) !important; }}</style>",
    unsafe_allow_html=True,
)

# 1. Barra superior fija
with st.container(key="barra_nav_fija"):
    renderizar_nav_superior(
        usuario=usuario_actual.get("nombre", "Usuario"),
        saldo=_saldo_mt5,
        moneda=_moneda_mt5,
    )

# Carga inicial de datos de mercado
cargar_datos_mercado()

# ==========================================
# NÚMEROS EN VIVO (auto-refresco ligero cada 2 s)
# ==========================================
INTERVALO_PRECIOS = "1s"


@st.fragment(run_every=INTERVALO_PRECIOS)
def _favoritos_en_vivo():
    actualizar_precios_mt5()
    renderizar_barra_favoritos()


@st.fragment(run_every=INTERVALO_PRECIOS)
def _watchlist_en_vivo():
    actualizar_precios_mt5()
    renderizar_watchlist()


# ==========================================
# LAYOUT PRINCIPAL: Barra Lateral + Contenido
# ==========================================
col_nav, col_main = st.columns([0.5, 11.5], gap="small")

# 2. Barra lateral izquierda extendida (nav_bar.py)
with col_nav:
    renderizar_nav_lateral()

# 3. Área de contenido principal — cambia según la vista de la barra lateral
with col_main:
    st.markdown("<div style='height: 0.2rem'></div>", unsafe_allow_html=True)

    _nav = st.session_state.get("nav_activo")
    if _nav == "noticias":
        # --- VISTA DE NOTICIAS ---
        renderizar_panel_noticias(main)
    elif _nav == "cotizaciones":
        # --- VISTA DE COTIZACIONES (tablas estilo Investing) ---
        from components.mercados_panel import renderizar_panel_mercados
        renderizar_panel_mercados(main)
    elif _nav == "copytrading":
        # --- VISTA COPY TRADING (estrategias, MVP mock) ---
        from components.copytrading_panel import renderizar_panel_copytrading
        renderizar_panel_copytrading(main)
    elif _nav == "trading":
        # --- VISTA TRADING (favoritos + watchlist + gráfico + ticket de orden) ---
        _favoritos_en_vivo()
        col_watchlist, col_center, col_orden = st.columns([1.2, 3.7, 0.95])
        with col_watchlist:
            _watchlist_en_vivo()
        with col_center:
            renderizar_panel_central(main)
        with col_orden:
            from components.order_panel import renderizar_panel_orden
            renderizar_panel_orden(main)
    else:
        # --- VISTA INICIO (panel de cuenta estilo XM) — también para botones sin vista propia ---
        from components.inicio_panel import renderizar_panel_inicio
        renderizar_panel_inicio(main)

# Quitamos el overlay de carga una vez renderizado todo
_overlay.empty()

# Diálogo del buscador (se abre con la bandera `mostrar_buscador`). Se renderiza
# aquí, en el script principal, para que no choque con los fragmentos en vivo.
from components.buscador import render_buscador
render_buscador()