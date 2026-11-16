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

"""Paquete de la vista de Planes: página con los planes y sus precios que mide el interés de los usuarios (prueba de demanda, sin cobrar).

  panel.py      la vista y la función `ir_a_planes` (botones que llevan a ella)
  estilos.css   estilos de la vista
  planes.json   descripción corta y características de cada plan

Este __init__ es una fachada: reexporta `renderizar_panel_planes`, `ir_a_planes` y `dialogo_bloqueo`. Los eventos que genera se guardan con
`herramientas/demanda.py` y se resumen en el Laboratorio.
"""
from componentes_plataforma.planes.panel import dialogo_bloqueo, ir_a_planes, renderizar_panel_planes

# Nombres públicos del paquete
__all__ = ["dialogo_bloqueo", "ir_a_planes", "renderizar_panel_planes"]


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
