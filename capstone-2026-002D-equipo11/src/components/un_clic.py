# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara un_clic .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada del modo One-Click Trading.

Apunta al paquete `components/operacion_un_clic/` (registro, estado, ventana, texto legal y estilos) y
reexporta de allí: `aceptado` (indica si el usuario aceptó los términos), `al_cambiar` (reacciona al interruptor
del ticket), `pedir_terminos_si_corresponde`, `renderizar_modal_terminos` (ventana de términos) y `PEDIR_SIEMPRE`
(bandera del modo demo). Existe para que
`from components.un_clic import al_cambiar, pedir_terminos_si_corresponde, renderizar_modal_terminos`
(ticket y `app.py`) siga funcionando sin cambios.
OJO: el modo demo (PEDIR_SIEMPRE) ahora se cambia en components/operacion_un_clic/registro.py.
"""
from components.operacion_un_clic import (PEDIR_SIEMPRE, aceptado, al_cambiar,
                                          pedir_terminos_si_corresponde, renderizar_modal_terminos)

__all__ = ["aceptado", "al_cambiar", "pedir_terminos_si_corresponde", "renderizar_modal_terminos", "PEDIR_SIEMPRE"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara un_clic .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
