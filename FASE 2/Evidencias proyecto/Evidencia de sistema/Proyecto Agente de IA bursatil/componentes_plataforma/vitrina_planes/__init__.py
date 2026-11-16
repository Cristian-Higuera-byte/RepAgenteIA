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

"""Vitrina de planes (paquete): las tarjetas de los cuatro planes con su precio y su detalle.

Fachada de la API pública. La usan las pantallas de acceso (`acceso/pantalla.py`: vitrina completa, enlace «Mira lo que incluye cada plan» y aviso del plan elegido) y
la vista Planes (`planes/panel.py`: cabecera y lista de cada tarjeta alrededor de sus botones). El contenido y la lógica viven en vitrina.py; los estilos, en estilos.css.
"""
from .vitrina import (PLAN_DESTACADO, estilos, html_beneficios, html_cabecera, html_comun, html_lista, html_pista, html_plan_elegido, html_rejilla,
                      html_vitrina, plan_valido, precio_texto)

__all__ = ["PLAN_DESTACADO", "estilos", "html_beneficios", "html_cabecera", "html_comun", "html_lista", "html_pista", "html_plan_elegido",
           "html_rejilla", "html_vitrina", "plan_valido", "precio_texto"]


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
