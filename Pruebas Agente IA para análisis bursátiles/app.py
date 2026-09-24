"""
app.py
------
Dashboard interactivo de Piña & Jara - Financial Terminal, 
diseñado con distribución de 3 columnas de forma limpia y modularizada.
"""

import os
import sys
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
from components.market_data import cargar_datos_mercado
from components.top_bar import renderizar_barra_superior
from components.watchlist import renderizar_watchlist
from components.central_panel import renderizar_panel_central
from components.news_panel import renderizar_panel_noticias

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard agente analitico Piña & Jara",
    page_icon="📈",
    layout="wide"
)

# ==========================================

# ESTILOS CSS GLOBALES (Ajuste de Tipografía y Tamaños)

# ==========================================

st.markdown("""

    <style>

        /* 1. Tamaño del texto general en todo el dashboard */

        html, body, [class*="st-"] {

            font-size: 30px !important; /* Aumenta el tamaño base de la letra */

        }



        /* 2. Tamaño de los títulos principales y encabezados */

        h1 {

            font-size: 35px !important;

        }

        h2 {

            font-size: 30px !important;

        }

        h3 {

            font-size: 30px !important;

        }



        /* 3. Tamaño de números, métricas y valores clave */

        [data-testid="stMetricValue"] {

            font-size: 30px !important;

        }

        [data-testid="stMetricLabel"] {

            font-size: 30px !important;

        }



        /* 4. Texto dentro de las tarjetas del watchlist, chat y paneles */

        p, span, label {

            font-size: 25px !important;

        }



        /* 5. Tamaño de texto en tablas y dataframes */

        .dataframe {

            font-size: 30px !important;

        }

    </style>

""", unsafe_allow_html=True)

# ==========================================
# ESTILOS CSS GLOBALES (TEXTOS AMPLIADOS)
# ==========================================
st.markdown("""
    <style>
        /* Tamaño base de fuente general aumentado */
        html, body, [class*="st-"] {
            font-size: 30px !important; 
        }
        
        /* Jerarquía de títulos más visible */
        h1 { font-size: 30px !important; }
        h2 { font-size: 35px !important; }
        h3 { font-size: 30px !important; }
        
        /* Ajuste de fuentes en elementos de entrada y selectores */
        .stSelectbox label, .stSlider label, .stTextInput label {
            font-size: 30px !important;
            font-weight: 600 !important;
        }

        .stApp { background-color: #0b0f19; color: #ffffff; }
        div.stButton > button { background-color: #161b22; color: white; border: 1px solid #30363d; border-radius: 6px; font-size: 16px !important; }
        div.stButton > button:hover { background-color: #21262d; border-color: #8b949e; }
        .card-box { background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 15px; }
        .ticker-header { font-size: 32px; font-weight: bold; color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# 1. Cargar y actualizar datos seguros del mercado
cargar_datos_mercado()

# 2. Renderizar barra superior de índices globales
renderizar_barra_superior()

# 3. Distribución principal de 3 columnas
col_left, col_center, col_right = st.columns([1, 2.1, 1.3])

with col_left:
    renderizar_watchlist()

with col_center:
    renderizar_panel_central(main)

with col_right:
    renderizar_panel_noticias(main)