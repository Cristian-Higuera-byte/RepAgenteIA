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
componentes_plataforma/resumen
------------------
Vista "Resumen": dashboard del portafolio (sección F). Tarjetas KPI con icono,
acento de color y micro-interacción (hover), nivel de margen como barra, curva de
balance con selector de periodo (interactivo) y exposición por activo. Todos los
números salen de herramientas.estadisticas_portafolio (datos reales de MT5). Estética P&J:
fondo oscuro, números grandes, verde/rojo según signo, acento naranja del logo.

Limitaciones honestas que la propia UI indica:
  - Drawdown mostrado = de BALANCE (MT5 no guarda snapshots de equity).
  - Dividendos: si el bróker/demo no generó eventos, muestra "sin dividendos".

La fachada `componentes_plataforma/resumen/` reexporta `renderizar_panel_resumen` desde este paquete para
que `aplicacion.py` siga importando el nombre de siempre.

Archivos: panel.py, secciones.py (bloques), tarjetas.py, curva.py, formato.py, datos.py + datos.json y estilos.css.
"""
# Función que dibuja la vista completa.
from componentes_plataforma.resumen.panel import renderizar_panel_resumen

# API pública del paquete.
__all__ = ["renderizar_panel_resumen"]


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
