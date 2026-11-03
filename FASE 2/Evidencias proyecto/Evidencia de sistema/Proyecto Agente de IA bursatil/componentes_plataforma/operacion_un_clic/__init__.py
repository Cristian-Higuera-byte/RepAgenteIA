# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara __init__ .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
componentes_plataforma/operacion_un_clic
----------------------------
Paquete del modo "One-Click Trading" (como MT5): con el interruptor activo, las órdenes del
ticket, del menú del clic derecho del gráfico y los arrastres de líneas
(Buy/Sell Limit/Stop, Take Profit, Stop Loss) se envían SIN confirmación.

La PRIMERA vez que un usuario lo activa debe aceptar la renuncia de
responsabilidades (modal). La aceptación queda registrada en el servidor, con
fecha, en `data/one_click_aceptaciones.json` (ignorado por git) y no se vuelve a
pedir. El interruptor vive en el ticket de órdenes (clave `orden_un_clic`); el gráfico
lee su estado del DOM y, para activarlo desde el menú, pulsa ese mismo interruptor.

Uso:
- panel_orden/panel.py: `st.toggle(..., key="orden_un_clic", on_change=al_cambiar)`
- aplicacion.py: `renderizar_modal_terminos()` (fuera de los fragmentos en vivo)

Archivos: registro.py (aceptación por usuario; PEDIR_SIEMPRE vive aquí), estado.py (callbacks del
interruptor), dialogo.py (ventana), terminos.html (texto legal) y estilos.css.

Este `__init__` es una fachada: reexporta la API pública de los submódulos para que el resto de la
plataforma importe todo desde `componentes_plataforma.operacion_un_clic`.
"""
# Fachada: reexporta la ventana de términos, los callbacks del interruptor y el registro de aceptación
from componentes_plataforma.operacion_un_clic.dialogo import renderizar_modal_terminos
from componentes_plataforma.operacion_un_clic.estado import al_cambiar, pedir_terminos_si_corresponde
from componentes_plataforma.operacion_un_clic.registro import PEDIR_SIEMPRE, aceptado

# Nombres públicos del paquete
__all__ = ["aceptado", "al_cambiar", "pedir_terminos_si_corresponde", "renderizar_modal_terminos", "PEDIR_SIEMPRE"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara __init__ .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
