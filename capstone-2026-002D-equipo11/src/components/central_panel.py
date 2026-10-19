# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara central_panel .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada de compatibilidad del panel central del dashboard.

Antes este archivo contenía todo (el gráfico, su HTML/JS y el chat del agente, casi 3000 líneas). Ahora cada cosa
vive en su propio paquete y aquí solo se reexportan los dos nombres que usa `app.py`:

  renderizar_panel_central  ->  components/grafico/panel.py   (gráfico; su HTML/CSS/JS en grafico/estatico/)
  renderizar_chat_agente    ->  components/chat_agente.py     (que a su vez apunta al paquete chat/)

No define lógica propia: existe para que los imports antiguos sigan funcionando sin tocar `app.py`.
"""
from components.chat_agente import renderizar_chat_agente
from components.grafico.panel import renderizar_panel_central

__all__ = ["renderizar_chat_agente", "renderizar_panel_central"]


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara central_panel .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
