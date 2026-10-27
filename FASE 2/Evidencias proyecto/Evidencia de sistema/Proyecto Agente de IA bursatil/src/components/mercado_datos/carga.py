# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara carga .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Carga inicial del mercado: índices globales (yfinance), watchlist del usuario y datos de cada símbolo.

Se ejecuta una vez por sesión de Streamlit y deja en `st.session_state` los datos que luego mantiene al día
`precios.actualizar_precios_mt5`. Depende de MetaTrader 5 (precios), yfinance (índices) y Supabase
(watchlist del usuario, vía `gestor_lista_activos`).
"""
import copy
import math
from pathlib import Path

import streamlit as st

from components._estaticos import datos_json
from components.mercado_datos.entrada import construir_entrada
from components.mercado_datos.sparkline import asegurar_semilla
from tools import gestor_lista_activos as wl
from tools.puente_mt5 import inicializar_mt5, precargar_precios

# Valores de respaldo de la barra de índices y su símbolo en yfinance (indices_globales.json)
_INDICES = datos_json(Path(__file__).parent / "indices_globales.json")


def cargar_datos_mercado():
    """Carga (una sola vez por sesión) índices globales, watchlist del usuario y datos de cada símbolo.

    Pasos: inicializa la conexión con MT5; si `datos_cargados` ya está en la sesión, termina sin repetir el
    trabajo; actualiza la barra de índices globales con yfinance (con valores de respaldo si falla la red);
    obtiene la watchlist del usuario (sembrando los símbolos por defecto si es nuevo); y construye la entrada
    de cada símbolo con su semilla de sparkline.

    No recibe parámetros ni devuelve nada. Efectos secundarios: escribe en `st.session_state` las claves
    `datos_indices_globales`, `watchlist_simbolos`, `datos_mercado_real` y `datos_cargados`; consulta MT5,
    yfinance y la base de datos de watchlists.
    """
    # Inicializar conexión a MT5 de forma segura al cargar el mercado
    inicializar_mt5()

    # Si ya se cargó una vez, no repetir el fetch pesado; los fragmentos
    # (actualizar_precios_mt5) mantienen los precios en vivo.
    if st.session_state.get("datos_cargados"):
        return

    # 1. Índices globales (barra superior) — se mantiene con yfinance
    # Primero se parte de los valores de respaldo para que la barra nunca quede vacía
    if "datos_indices_globales" not in st.session_state:
        st.session_state.datos_indices_globales = copy.deepcopy(_INDICES["defecto"])
    try:
        # La importación es perezosa: yfinance es pesado y solo se necesita en esta carga inicial
        import yfinance as yf  # type: ignore[import-untyped]
        simbolos_indices = _INDICES["yfinance"]
        for key, sym in simbolos_indices.items():
            # Tres días de historia bastan para tener el último cierre y el anterior (fines de semana incluidos)
            hist = yf.Ticker(sym).history(period="3d")
            if not hist.empty and "Close" in hist.columns:
                val = hist["Close"].iloc[-1]
                if not math.isnan(float(val)):
                    # Variación = último cierre contra el cierre previo (o contra sí mismo si solo hay una vela)
                    actual = float(val)
                    anterior_val = hist["Close"].iloc[-2] if len(hist) > 1 else actual
                    anterior = float(anterior_val) if not math.isnan(float(anterior_val)) else actual
                    cambio = actual - anterior
                    porc = (cambio / anterior * 100) if anterior != 0 else 0.0
                    st.session_state.datos_indices_globales[key] = {
                        "valor": actual, "var": f"{'+' if cambio >= 0 else ''}{porc:.2f}%", "sube": cambio >= 0}
    except Exception:
        # Sin red o con error de yfinance se conservan los valores de respaldo ya cargados
        pass

    # 2. Watchlist del USUARIO (desde Supabase; si es nuevo, se siembra el default)
    # El id puede faltar (sesión sin login completo): en ese caso uid es None y el gestor decide qué devolver
    usuario = st.session_state.get("usuario_info", {})
    uid = usuario.get("id") if isinstance(usuario, dict) else None
    simbolos = wl.obtener_watchlist(uid)
    if not simbolos:
        simbolos = wl.sembrar_defaults(uid)
    st.session_state.watchlist_simbolos = simbolos

    # 3. Construir los datos de mercado de esos símbolos (nombre EXACTO para MT5)
    # Precarga batch: con Capital, pide todos los precios en 1 llamada (en vez de N).
    precargar_precios(simbolos)
    datos = {}
    for sym in simbolos:
        datos[sym] = construir_entrada(sym)
        # Sembrar el sparkline con histórico M1 (se reintenta si vino vacío)
        asegurar_semilla(sym)
    st.session_state.datos_mercado_real = datos

    # Marca la carga como hecha para que los siguientes reruns la omitan
    st.session_state.datos_cargados = True


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara carga .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
