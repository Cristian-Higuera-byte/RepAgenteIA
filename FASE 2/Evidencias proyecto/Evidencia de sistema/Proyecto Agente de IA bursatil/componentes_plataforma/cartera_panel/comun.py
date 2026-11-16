# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara comun .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""
cartera_panel/comun.py
----------------------
Helpers compartidos por la lista, el modal de cierre y el detalle: cálculo del P/G
neto, formato de precio, texto del botón de cierre (mismo formato que usa live_feed en
JS) y la carga de los 3 CSS del panel (estatico/lista.css · modal.css · detalle.css).
El CSS se lee una sola vez (lru_cache) y se inyecta con st.markdown (como el original).
"""
from functools import lru_cache
from pathlib import Path

import streamlit as st

from componentes_plataforma._estaticos import sin_creditos

# Carpeta con los CSS del panel (cartera_panel/estatico), resuelta respecto a este archivo.
_ESTATICO = Path(__file__).resolve().parent / "estatico"

# Selector que acota el CSS del modal al diálogo que contiene el botón de cierre.
# Sustituye al marcador de selector de modal.css (ver css_modal) para no afectar a otros diálogos.
_SEL_MODAL = "[data-testid='stDialog']:has([class*='st-key-cartera_boton_cerrar_'])"


# TITULO LEER

@lru_cache(maxsize=None)
def _leer(nombre: str) -> str:
    """Lee un CSS de cartera_panel/estatico/. Cacheado en memoria por proceso.

    Recibe el nombre del archivo (por ejemplo "lista.css") y devuelve su texto sin el
    encabezado de créditos (vía sin_creditos). Si el archivo no se puede leer devuelve
    una cadena vacía, de modo que el panel se muestre sin estilos en lugar de fallar.
    """
    # Se lee desde disco una sola vez por proceso gracias a lru_cache.
    try:
        return sin_creditos((_ESTATICO / nombre).read_text(encoding="utf-8"))
    except OSError:
        return ""


# TITULO CSS LISTA

def css_lista() -> None:
    """Inyecta en la página el CSS de la lista de Cartera (estatico/lista.css) mediante una etiqueta style."""
    st.markdown(f"<style>{_leer('lista.css')}</style>", unsafe_allow_html=True)


# TITULO CSS DETALLE

def css_detalle() -> None:
    """Inyecta en la página el CSS del detalle desplegable de una posición (estatico/detalle.css)."""
    st.markdown(f"<style>{_leer('detalle.css')}</style>", unsafe_allow_html=True)


# TITULO CSS MODAL

def css_modal() -> None:
    """Inyecta el CSS del modal de cierre (estatico/modal.css).

    Antes de inyectarlo reemplaza el marcador de selector del archivo por _SEL_MODAL,
    para que las reglas solo apliquen al diálogo que contiene el botón de cierre.
    """
    # Sustitución del marcador por el selector real del diálogo.
    css = _leer("modal.css").replace("__SEL__", _SEL_MODAL)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# TITULO NETO

def neto(p: dict) -> float:
    """P/G neto de una posición (profit + swap), como lo suma MT5 en la cuenta.

    Recibe el diccionario de la posición (claves "profit" y "swap", que pueden faltar o
    ser None) y devuelve la suma como float; los valores ausentes cuentan como 0.0.
    """
    return float(p.get("profit", 0.0) or 0.0) + float(p.get("swap", 0.0) or 0.0)


# TITULO FORMATEAR PRECIO

def formatear_precio(x) -> str:
    """Precio sin ceros finales (no tenemos los dígitos del símbolo aquí).

    Recibe un número (o texto numérico) y devuelve una cadena con separador de miles y
    hasta 5 decimales, quitando ceros y punto sobrantes. Devuelve "—" si el valor no es
    numérico o es cero.
    """
    # Convierte a float; si no es posible, no hay precio que mostrar.
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    return (f"{x:,.5f}".rstrip("0").rstrip(".")) if x else "—"


# TITULO TEXTO CERRAR

def texto_cerrar(prof: float) -> str:
    """Texto del botón de cierre estilo XM, a partir del P/G de la posición.

    Recibe el P/G neto (float) y devuelve, por ejemplo, 'Cerrar con pérdida de -$220.00' /
    'Cerrar con ganancia de $280.00'. (flujo_precios/ usa el mismo formato.)"""
    # Verbo según el signo del P/G (cero cuenta como ganancia).
    verbo = "ganancia" if prof >= 0 else "pérdida"
    # El signo menos va antes del símbolo de dólar; el monto se muestra en valor absoluto.
    signo = "-" if prof < 0 else ""
    return f"Cerrar con {verbo} de {signo}${abs(prof):,.2f}"


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara comun .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
