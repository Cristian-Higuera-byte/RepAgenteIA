# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara dialogo .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ventana de la vigilancia automática: términos y condiciones (terminos.html) con «Rechazar propuesta» y «Acepto».

Los estilos de la ventana están en estilos.css y se inyectan dentro del propio diálogo. El texto legal lleva marcas
`%%NOMBRE%%` que aquí se sustituyen por los términos concretos de la vigilancia (activo, riesgo, operaciones, intervalo,
duración y permiso de cierre).
"""
from pathlib import Path
from typing import Any

import streamlit as st

from componentes_plataforma._estaticos import estilos, texto
from componentes_plataforma.agente_paneles.formato import escapar_html
from componentes_plataforma.vigilancia_terminos.estado import CLAVE_VIGILANCIA, aceptar, cancelar, rechazar
from nucleo_agente import ordenes, vigilancia

# Carpeta del paquete, donde viven terminos.html y estilos.css
_DIR = Path(__file__).parent
# Texto legal (HTML) con marcas %%...%% por rellenar
PLANTILLA = texto(_DIR / "terminos.html")
# Hoja de estilos de la ventana, lista para inyectar con st.html
CSS = estilos(_DIR / "estilos.css")


# TITULO TEXTO TERMINOS

def _texto_terminos(v: dict[str, Any]) -> str:
    """Devuelve el HTML de los términos con las marcas rellenas con las condiciones de la vigilancia `v`.

    Todo valor se escapa para HTML. El ámbito indica si la plataforma restringe la operación del agente a la cuenta demo
    (límite `solo_demo`)."""
    valores = {
        "SIMBOLO": v["simbolo"], "RIESGO": f"{v['riesgo_pct']:g} %", "OPERACIONES": str(v["max_operaciones"]),
        "INTERVALO": f"{v['intervalo_min']} min", "DURACION": f"{float(v['duracion_horas']):g} h",
        "CIERRE": "Sí" if v.get("permite_cerrar") else "No",
        "AMBITO": "en la cuenta demo conectada" if ordenes.LIMITES.solo_demo else "en la cuenta conectada",
    }
    salida = PLANTILLA
    for marca, valor in valores.items():
        salida = salida.replace(f"%%{marca}%%", escapar_html(valor))
    return salida


# TITULO DIALOGO

@st.dialog("Vigilancia automática del agente", width="large", on_dismiss=cancelar)
def _dialogo(v: dict[str, Any]) -> None:
    """Dibuja el diálogo con los términos y los botones «Rechazar propuesta» y «Acepto los Términos y Condiciones».

    Recibe la vigilancia pendiente. «Rechazar propuesta» cancela la vigilancia; «Acepto» registra la aceptación y la
    activa; cerrar con la «X» la deja pendiente. Cada botón relanza la app para refrescar los paneles."""
    # Contenedor con key terminos_vigilancia_raiz: lo usa el CSS para estilizar solo este diálogo
    with st.container(key="terminos_vigilancia_raiz"):
        st.html(CSS)
        st.html(_texto_terminos(v))
        c1, c2 = st.columns([1, 1.4])
        with c1:
            with st.container(key="terminos_vigilancia_rechazar"):
                if st.button("Rechazar propuesta", key="terminos_vigilancia_rechazar_boton", width="stretch",
                             on_click=rechazar):
                    st.rerun()
        with c2:
            # Contenedor terminos_vigilancia_aceptar: el CSS le da al botón de aceptar el degradado naranja
            with st.container(key="terminos_vigilancia_aceptar"):
                if st.button("Acepto los Términos y Condiciones", key="terminos_vigilancia_aceptar_boton",
                             width="stretch", on_click=aceptar):
                    st.rerun()


# TITULO RENDERIZAR MODAL TERMINOS VIGILANCIA

def renderizar_modal_terminos_vigilancia() -> None:
    """Llamar desde aplicacion_principal/dialogos.py (fuera de los fragmentos en vivo).

    Abre el diálogo solo si `st.session_state.vigilancia_terminos_id` apunta a una vigilancia que sigue pendiente de
    autorización; si ya no lo está (venció, la rechazó otra pestaña), limpia la marca. No devuelve nada."""
    vid = st.session_state.get(CLAVE_VIGILANCIA)
    if not vid:
        return
    v = vigilancia.obtener(vid)
    if v and v["estado"] == vigilancia.PENDIENTE:
        _dialogo(v)
    else:
        cancelar()


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara dialogo .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
