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
componentes_plataforma/perfil
-----------------------------
Perfil de usuario («Mi perfil»): los datos que piden las plataformas de trading para operar — datos personales, documento de
identidad, contacto y dirección, perfil de inversor (experiencia, origen de fondos, tolerancia al riesgo), preferencias,
seguridad (cambio de contraseña) y cuenta de trading conectada.

Dónde se guardan: en la tabla `perfiles_usuario` de Supabase (se crea con `esquema.sql`) o, sin credenciales de Supabase, en
`data/perfiles_locales.json`. La contraseña NO vive aquí: sigue en `usuarios` como hash PBKDF2 (herramientas/gestor_autenticacion.py).

Cómo se abre: el menú del usuario de la barra superior enlaza a `?perfil=1` (o `?perfil=<sección>`); acceso/pantalla.py lo
convierte en `navegacion_activo = "perfil"` y aplicacion_principal/vistas.py dibuja `renderizar_panel_perfil`.

Archivos: panel.py (cabecera, menú y sección activa), secciones.py (formularios), almacen.py (lectura y escritura), validacion.py
(RUT, teléfono, edad, contraseña, porcentaje completo), datos.py + datos.json (opciones y campos), esquema.sql y estilos.css.

Este `__init__` es una fachada: reexporta el punto de entrada que usa la plataforma.
"""
# Función que dibuja toda la vista de perfil.
from componentes_plataforma.perfil.panel import renderizar_panel_perfil

# API pública del paquete.
__all__ = ["renderizar_panel_perfil"]


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
