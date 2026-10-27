# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------------- INICIO Piña y Jara __init__ .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""Paquete de CONEXIÓN DE CUENTAS de Capital.com por usuario (demo y real).

modo.py (cuentas conectadas, modo activo y resolvedor del usuario para el backend), pantalla.py (pantalla para conectar
y gestionar cuentas) y menu.py (etiqueta DEMO/REAL y entradas del menú del usuario).
"""
from .menu import entradas_menu, etiqueta_cuenta
from .modo import modo_activo_demo, registrar_resolvedor, url_servidor
from .pantalla import abrir_gestion, completar_cuenta_faltante, requerir_cuenta

__all__ = ["abrir_gestion", "completar_cuenta_faltante", "entradas_menu", "etiqueta_cuenta", "modo_activo_demo", "registrar_resolvedor", "requerir_cuenta", "url_servidor"]


# -------------------------------------------------------------------------------------------------------
# ---------------------------------------- FIN Piña y Jara __init__ .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
