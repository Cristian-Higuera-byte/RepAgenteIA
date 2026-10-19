# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara flujo_vivo .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada del feed de precios EN VIVO del navegador (SSE).

Apunta al paquete `components/flujo_precios/` (servidor, atributos, inyección y el JavaScript por
fragmentos en js/) y reexporta de allí: `API_URL` (dirección del servidor de datos), `flujo_activo` (indica si el
feed está disponible), `intervalo` (elige el período de refresco según haya feed), `atributos` (atributos HTML con
que se marcan los elementos vivos) e `inyectar_flujo` (inserta el JS del feed en la página). Existe para que los
`from components.flujo_vivo import intervalo, atributos, inyectar_flujo, flujo_activo` de todo el
proyecto sigan funcionando sin cambios. No contiene lógica propia.
"""
from components.flujo_precios import API_URL, atributos, flujo_activo, inyectar_flujo, intervalo

__all__ = ["API_URL", "flujo_activo", "intervalo", "atributos", "inyectar_flujo"]


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara flujo_vivo .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
