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

"""Paquete de la vista de Billetera: saldo virtual del usuario, recargas de prueba, pago de planes y libro de movimientos.

  panel.py      la vista (`renderizar_panel_billetera`)
  estilos.css   estilos de la vista

La lógica del saldo y los movimientos está en `herramientas/billetera.py` (Supabase en multiusuario, archivo en modo local). Este __init__ es una
fachada: reexporta `renderizar_panel_billetera`.
"""
from componentes_plataforma.billetera.panel import renderizar_panel_billetera

# Nombres públicos del paquete
__all__ = ["renderizar_panel_billetera"]



# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara __init__ .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
