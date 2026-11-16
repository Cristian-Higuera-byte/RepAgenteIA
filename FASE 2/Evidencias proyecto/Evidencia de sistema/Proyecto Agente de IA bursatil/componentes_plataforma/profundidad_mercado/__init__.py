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

"""Paquete del panel de PROFUNDIDAD DE MERCADO (DOM), estilo XM.

Se abre desde el riel de íconos de la derecha (`riel/`, fachada `riel/`). La fachada
`componentes_plataforma/profundidad_mercado/` reexporta `renderizar_panel_dom` desde aquí.

    panel.py     renderizar_panel_dom(): cabecera + escalera que se refresca sola
    escalera.py  HTML de la escalera (profundidad real del bróker o vista demostrativa)
    estilos.css  estilos del panel
"""
# Función que dibuja el panel completo.
from componentes_plataforma.profundidad_mercado.panel import renderizar_panel_dom

# API pública del paquete.
__all__ = ["renderizar_panel_dom"]


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
