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

"""Ventana "One-Click Trading": renuncia de responsabilidades (terminos.html) con Cancelar / Acepto.

Los estilos de la ventana están en estilos.css y se inyectan dentro del propio diálogo.
"""
from pathlib import Path

import streamlit as st

from components._estaticos import estilos, texto
from components.operacion_un_clic.estado import aceptar, cancelar

# Carpeta del paquete, donde viven terminos.html y estilos.css
_DIR = Path(__file__).parent
# Texto legal (HTML) de la renuncia de responsabilidades
TEXTO = texto(_DIR / "terminos.html")
# Hoja de estilos de la ventana, lista para inyectar con st.html
CSS = estilos(_DIR / "estilos.css")


@st.dialog("One-Click Trading", width="large", on_dismiss=cancelar)
def _dialogo():
    """Dibuja el diálogo con los términos y los botones Cancelar y "Acepto".

    Cancelar (o cerrar el diálogo) llama a `cancelar`; Acepto llama a `aceptar`, que registra la
    aceptación y activa el interruptor; luego se muestra un aviso y se relanza la app."""
    # Contenedor con key oct_root: lo usa el CSS para estilizar solo este diálogo
    with st.container(key="oct_root"):
        st.html(CSS)
        st.html(TEXTO)
        c1, c2 = st.columns([1, 1.4])
        with c1:
            if st.button("Cancelar", key="oct_cancel", width="stretch", on_click=cancelar):
                st.rerun()
        with c2:
            # Contenedor oct_ok: el CSS le da al botón de aceptar el degradado naranja
            with st.container(key="oct_ok"):
                if st.button("Acepto los Términos y Condiciones", key="oct_ok_btn",
                             width="stretch", on_click=aceptar):
                    st.toast("One-Click Trading activado.", icon=":material/bolt:")
                    st.rerun()


def renderizar_modal_terminos():
    """Llamar desde app.py (fuera de los fragmentos en vivo).

    Abre el diálogo de términos solo si `st.session_state.oct_terminos` es verdadero. No devuelve nada."""
    if st.session_state.get("oct_terminos"):
        _dialogo()


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
