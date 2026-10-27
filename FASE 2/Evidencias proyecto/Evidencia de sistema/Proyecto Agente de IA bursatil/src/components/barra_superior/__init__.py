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
components/barra_superior
------------------------
Barra de navegación superior del dashboard (estilo terminal de trading).
- Buscador (visual por ahora) en la posición del antiguo logo.
- Íconos de tema y campana de notificaciones (core/notificaciones.py): avisa cuando el agente
  termina de responder aunque el usuario esté en otra sección.
- Usuario a la derecha: al hacer clic en el nombre se despliega un menú
  (perfil / configuración / cerrar sesión) — con <details>, sin recargar.

La barra queda FIJA arriba y a todo el ancho gracias al contenedor
`st.container(key="barra_nav_fija")` de app.py + su CSS (position: fixed).

Archivos: barra.py (arma la barra), notificaciones.py (campana), tarjetas.py (Capital/Riesgo/Drawdown/Mercado),
datos.py + iconos.json, usuario_menu.html (menú del usuario), estilos.py y estilos.css.

Este __init__ es una fachada: reexporta `renderizar_barra_navegacion` de barra.py, que es lo
único que app.py necesita importar de este paquete.
"""
from components.barra_superior.barra import renderizar_barra_navegacion

# Nombres públicos del paquete
__all__ = ["renderizar_barra_navegacion"]


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
