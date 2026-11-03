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
componentes_plataforma/vigilancia_terminos
------------------------------------------
Paquete de la ventana de términos y condiciones de la vigilancia automática del agente.

Cuando el usuario pulsa «Autorizar vigilancia» en el panel «Órdenes propuestas», no se activa al instante: se abre una
ventana (la misma idea que la de One-Click Trading) que explica que el agente de IA actuará de forma libre sobre el dinero
de la cuenta, sin pedir confirmación en cada operación, y que quien acepta asume las consecuencias de confiar sus operaciones
a una inteligencia artificial. En la ventana el usuario puede ACEPTAR (la vigilancia se activa y la aceptación queda
registrada con usuario, fecha y términos) o RECHAZAR la propuesta del agente (la vigilancia se cancela). Cerrar la ventana
con la «X» no decide nada: la vigilancia sigue pendiente hasta que venza su plazo.

Uso:
- agente_paneles/vigilancias.py: el botón «Autorizar vigilancia» llama a `pedir(id)` y reejecuta la app.
- aplicacion_principal/dialogos.py: `renderizar_modal_terminos_vigilancia()` (fuera de los fragmentos en vivo).

Archivos: registro.py (aceptaciones en disco), estado.py (callbacks: pedir, aceptar, rechazar, cancelar), dialogo.py
(ventana), terminos.html (texto legal con marcas %%...%% que se rellenan con los términos de la vigilancia) y estilos.css.

Este `__init__` es una fachada: reexporta la API pública de los submódulos para que el resto de la plataforma importe todo
desde `componentes_plataforma.vigilancia_terminos`.
"""
# Fachada: reexporta la ventana de términos, los callbacks de estado y el registro de aceptaciones
from componentes_plataforma.vigilancia_terminos.dialogo import renderizar_modal_terminos_vigilancia
from componentes_plataforma.vigilancia_terminos.estado import pedir
from componentes_plataforma.vigilancia_terminos.registro import VERSION_TERMINOS, aceptaciones_de

# Nombres públicos del paquete
__all__ = ["VERSION_TERMINOS", "aceptaciones_de", "pedir", "renderizar_modal_terminos_vigilancia"]


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
