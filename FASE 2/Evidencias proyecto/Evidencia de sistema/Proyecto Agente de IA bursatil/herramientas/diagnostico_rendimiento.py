# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------ INICIO Piña y Jara diagnostico_rendimiento .PY -------------------------
# -------------------------------------------------------------------------------------------------------

"""Medición de tiempos de la plataforma, para saber QUÉ tarda cuando algo se siente lento.

Se activa con la variable de entorno `PJ_DIAGNOSTICO=1` (para todos los usuarios) o con `?diag=1` en la dirección de la página (solo esa sesión). Las fases y la insignia solo
existen con la medición encendida; las peticiones lentas al bróker se anotan siempre (es una comparación barata). Encendido:
  * `marca(nombre)`: anota cuánto pasó desde la marca anterior (una fase de la página: estilos, barra superior, vista…).
  * `llamada(metodo, ruta, segundos)`: anota una petición al bróker; las que pasan de `UMBRAL_LLAMADA_S` quedan en el registro.
  * `etiqueta()`: HTML de una insignia fija (abajo a la izquierda) con el tiempo total de la ejecución, sus fases más lentas y las peticiones lentas. Además cada
    fase y cada petición lenta se imprime en la consola del servidor con el prefijo [RENDIMIENTO].
Con esa insignia (o con la consola) se puede decir con números qué sección o qué llamada tarda."""
import os
import threading
import time
from collections import deque
from html import escape

import streamlit as st

# Segundos desde los que una petición al bróker se considera lenta.
UMBRAL_LLAMADA_S = 0.4
# Segundos desde los que una fase de la página se imprime en la consola aunque la insignia no esté a la vista.
UMBRAL_FASE_S = 0.25
# Últimas peticiones lentas (de cualquier hilo): (instante, método, ruta, segundos).
_LLAMADAS: deque = deque(maxlen=60)
_CANDADO = threading.Lock()


# TITULO ACTIVO

def activo() -> bool:
    """True si la medición está encendida (variable de entorno o `?diag=1` de esta sesión)."""
    if os.getenv("PJ_DIAGNOSTICO", "").strip().lower() in ("1", "true", "si", "sí"):
        return True
    try:
        if st.query_params.get("diag") == "1":
            st.session_state["_diag"] = True
        return bool(st.session_state.get("_diag"))
    except Exception:  # noqa: BLE001 - sin contexto de Streamlit (hilos, pruebas) no hay medición
        return False


# TITULO INICIAR

def iniciar() -> None:
    """Empieza a medir una ejecución de la página: borra las fases anteriores y fija el instante inicial. No hace nada si la medición está apagada."""
    if not activo():
        return
    ahora = time.perf_counter()
    st.session_state["_diag_t0"], st.session_state["_diag_ult"], st.session_state["_diag_fases"] = ahora, ahora, []
    st.session_state["_diag_reloj"] = time.time()


# TITULO MARCA

def marca(nombre: str) -> None:
    """Anota la fase `nombre`: el tiempo desde la marca anterior (o desde `iniciar`). Las fases lentas se imprimen en la consola del servidor."""
    if not activo() or "_diag_ult" not in st.session_state:
        return
    ahora = time.perf_counter()
    segundos = ahora - st.session_state["_diag_ult"]
    st.session_state["_diag_ult"] = ahora
    st.session_state["_diag_fases"].append((nombre, segundos))
    if segundos >= UMBRAL_FASE_S:
        print(f"[RENDIMIENTO] fase «{nombre}»: {segundos * 1000:.0f} ms")


# TITULO LLAMADA

def llamada(metodo: str, ruta: str, segundos: float) -> None:
    """Anota una petición al bróker que tardó `segundos`; solo se guardan (y se imprimen) las que pasan de `UMBRAL_LLAMADA_S`.

    Pensada para llamarse desde cualquier hilo y desde el código del bróker; es una comparación barata cuando la petición fue rápida."""
    if segundos < UMBRAL_LLAMADA_S:
        return
    with _CANDADO:
        _LLAMADAS.append((time.time(), metodo, ruta, segundos))
    print(f"[RENDIMIENTO] petición lenta {metodo} {ruta}: {segundos * 1000:.0f} ms")


# TITULO ETIQUETA

def etiqueta() -> None:
    """Dibuja la insignia fija con el resumen de la ejecución: total, fases más lentas y peticiones lentas desde que empezó. Sin medición no dibuja nada."""
    if not activo() or "_diag_t0" not in st.session_state:
        return
    total = time.perf_counter() - st.session_state["_diag_t0"]
    fases = sorted(st.session_state.get("_diag_fases", []), key=lambda x: -x[1])[:5]
    desde = st.session_state.get("_diag_reloj", 0)
    with _CANDADO:
        lentas = [x for x in _LLAMADAS if x[0] >= desde][-5:]
    filas = "".join(f"<div>{escape(n)} · <b>{s * 1000:.0f} ms</b></div>" for n, s in fases)
    peticiones = "".join(f"<div class='pj-diag-lenta'>{escape(m)} {escape(r)[:40]} · <b>{s * 1000:.0f} ms</b></div>" for _, m, r, s in lentas)
    print(f"[RENDIMIENTO] ejecución completa: {total * 1000:.0f} ms (vista: {st.session_state.get('navegacion_activo')})")
    st.html(
        "<style>.pj-diag{position:fixed;left:76px;bottom:8px;z-index:100002;background:#0d1117ee;border:1px solid #30363d;border-radius:8px;"
        "padding:6px 10px;color:#c9d1d9;font:11px/1.45 monospace;pointer-events:none;max-width:340px}"
        ".pj-diag b{color:#3fb950}.pj-diag-lenta,.pj-diag-lenta b{color:#f85149}</style>"
        f"<div class='pj-diag'><div>⏱ ejecución <b>{total * 1000:.0f} ms</b> · vista {escape(str(st.session_state.get('navegacion_activo')))}</div>"
        f"{filas}{peticiones}</div>"
    )


# -------------------------------------------------------------------------------------------------------
# -------------------------------- FIN Piña y Jara diagnostico_rendimiento .PY --------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
