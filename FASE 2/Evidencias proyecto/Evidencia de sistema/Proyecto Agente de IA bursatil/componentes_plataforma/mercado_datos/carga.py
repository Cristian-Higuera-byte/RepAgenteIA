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

from componentes_plataforma._estaticos import datos_json
from componentes_plataforma.paralelo import en_paralelo
from componentes_plataforma.mercado_datos.entrada import construir_entrada
from componentes_plataforma.mercado_datos.sparkline import asegurar_semilla, historial_sparkline
from herramientas import gestor_lista_activos as wl
from herramientas.puente_mt5 import inicializar_mt5, precargar_precios

# Valores de respaldo de la barra de índices y su símbolo en yfinance (indices_globales.json)
_INDICES = datos_json(Path(__file__).parent / "indices_globales.json")

# Segundos máximos que se espera a los índices globales (yfinance) antes de dibujar la página.
_ESPERA_INDICES = 6.0


# TITULO INDICE GLOBAL

def _indice_global(par):
    """Último valor y variación de un índice global (par `(clave, símbolo de yfinance)`) o None si no hay datos."""
    import yfinance as yf  # type: ignore[import-untyped]
    key, simbolo = par
    historial = yf.Ticker(simbolo).history(period="3d")
    if historial.empty or "Close" not in historial.columns:
        return None
    valor = historial["Close"].iloc[-1]
    if math.isnan(float(valor)):
        return None
    actual = float(valor)
    anterior_valor = historial["Close"].iloc[-2] if len(historial) > 1 else actual
    anterior = float(anterior_valor) if not math.isnan(float(anterior_valor)) else actual
    cambio = actual - anterior
    porc = (cambio / anterior * 100) if anterior != 0 else 0.0
    return key, {"valor": actual, "var": f"{'+' if cambio >= 0 else ''}{porc:.2f}%", "sube": cambio >= 0}


# TITULO CALENTAR SIMBOLO

def _calentar_simbolo(simbolo: str):
    """Pide por adelantado (en un hilo) todo lo que luego necesita la entrada de un símbolo: su ficha, su precio, el cierre
    previo y el histórico del sparkline. Así la pasada que arma la lista encuentra todo en caché."""
    construir_entrada(simbolo)
    historial_sparkline(simbolo)


# TITULO CARGAR DATOS MERCADO

def cargar_datos_mercado():
    """Carga (una sola vez por sesión) índices globales, watchlist del usuario y datos de cada símbolo.

    Pasos: inicializa la conexión con MT5; si `datos_cargados` ya está en la sesión, termina sin repetir el
    trabajo; actualiza la barra de índices globales con yfinance (con valores de respaldo si falla la red);
    obtiene la watchlist del usuario (sembrando los símbolos por defecto si es nuevo); y construye la entrada
    de cada símbolo con su semilla de sparkline. Los índices y las lecturas de cada símbolo se piden en paralelo.

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
    # Los índices se piden a la vez (antes uno tras otro) y sin esperar más de `_ESPERA_INDICES` s: si yfinance tarda o no hay
    # red, se conservan los valores de respaldo ya cargados y la página se dibuja igual.
    for resultado in en_paralelo(_indice_global, _INDICES["yfinance"].items(), max_hilos=len(_INDICES["yfinance"]),
                                  espera=_ESPERA_INDICES):
        if resultado:
            st.session_state.datos_indices_globales[resultado[0]] = resultado[1]

    # 2. Watchlist del USUARIO (desde Supabase; si es nuevo, se siembra el default)
    # El id puede faltar (sesión sin login completo): en ese caso uid es None y el gestor decide qué devolver
    usuario = st.session_state.get("usuario_informacion", {})
    uid = usuario.get("id") if isinstance(usuario, dict) else None
    simbolos = wl.obtener_watchlist(uid)
    if not simbolos:
        simbolos = wl.sembrar_por_defecto(uid)
    st.session_state.watchlist_simbolos = simbolos
    # Activo inicial = el primero de la lista del usuario (antes siempre arrancaba en EURUSD, aunque no estuviera).
    if simbolos and st.session_state.get("activo_seleccionado") in (None, ""):
        st.session_state.activo_seleccionado = simbolos[0]

    # 3. Construir los datos de mercado de esos símbolos (nombre EXACTO para MT5)
    # Precarga batch: con Capital, pide todos los precios en 1 llamada (en vez de N).
    precargar_precios(simbolos)
    # Cada símbolo necesita varias lecturas a la API (ficha, cierre previo, histórico del sparkline): se piden todas a la vez
    # y la pasada de abajo, que arma la lista, las encuentra ya en caché (antes eran decenas de llamadas una tras otra).
    en_paralelo(_calentar_simbolo, simbolos)
    datos = {}
    for simbolo in simbolos:
        datos[simbolo] = construir_entrada(simbolo)
        # Sembrar el sparkline con histórico M1 (se reintenta si vino vacío)
        asegurar_semilla(simbolo)
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
