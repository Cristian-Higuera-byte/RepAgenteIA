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

"""Paquete del Laboratorio de ingresos: prueba con la cuenta demo cuánto ganaría la plataforma con distintos modelos de cobro y qué tan
bien opera el agente de IA como gestor. No cobra ni mueve dinero.

  datos.py       parámetros por usuario, operaciones cerradas y operaciones abiertas por el agente
  panel.py       la vista (tres pestañas: ingresos hipotéticos, agente como gestor y parámetros)
  estilos.css    estilos de la vista
  parametros.json  valores por defecto de cada modelo

Este __init__ es una fachada: reexporta `renderizar_panel_laboratorio` para que `aplicacion_principal/vistas.py` lo importe desde aquí.
La lógica de cálculo vive en `herramientas/ingresos_virtuales.py`.
"""
from componentes_plataforma.ingresos_virtuales.panel import renderizar_panel_laboratorio

# Nombres públicos del paquete
__all__ = ["renderizar_panel_laboratorio"]


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
