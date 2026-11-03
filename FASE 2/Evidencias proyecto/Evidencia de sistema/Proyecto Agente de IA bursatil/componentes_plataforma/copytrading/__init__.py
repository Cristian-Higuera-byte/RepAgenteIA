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

"""Vista "Copy trading": estrategias reales de los gestores (o de ejemplo mientras no haya ninguna).

    datos.py        estrategias reales (Supabase) o de ejemplo (estrategias.json), categorías, pestañas de orden
    graficos.py     sparkline, dona y avatar en SVG
    tarjeta.py      tarjeta del listado
    ficha.py        ficha de detalle de una estrategia de ejemplo
    ficha_real.py   ficha de detalle de una estrategia real (con las métricas calculadas)
    copiar.py       ventanas del inversor: abrir la cuenta de inversor y configurar una copia
    cartera.py      sección Cartera: copias del usuario (pausar, reanudar, detener)
    gestor.py       sección Área de gestor
    panel.py        renderizar_panel_copytrading(): listado + detalle
    estilos.css     estilos de la vista

Este archivo es la fachada del paquete: reexporta renderizar_panel_copytrading (definida
en panel.py) para que el resto de la plataforma muestre la vista con una sola importación.
Las copias las replica el motor de `herramientas/copiador.py` (solo demo y en modo multiusuario).
"""
# Reexporta la función pública de la vista.
from componentes_plataforma.copytrading.panel import renderizar_panel_copytrading

# Nombres públicos del paquete.
__all__ = ["renderizar_panel_copytrading"]


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
