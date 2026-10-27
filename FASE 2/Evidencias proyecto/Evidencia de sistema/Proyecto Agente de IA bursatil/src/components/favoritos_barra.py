# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# -------------------------------- INICIO Piña y Jara favoritos_barra .PY -------------------------------
# -------------------------------------------------------------------------------------------------------

"""Fachada de la barra de FAVORITOS.

Apunta al paquete `components/favoritos/` (estado, tarjeta, barra y estilos) y reexporta de allí:
`renderizar_barra_favoritos` (dibuja la barra), `agregar_favorito` y `quitar_favorito` (modifican la lista),
`icono_activo` (ícono de un activo) y las constantes `FAVORITOS_MAX` (tope de favoritos) y `FAVORITOS_DEFAULT`
(lista inicial). Existe para que los `from components.favoritos_barra import ...` de `app.py`,
`watchlist.py` y `mercados_panel.py` sigan funcionando sin cambios. No contiene lógica propia.
"""
from components.favoritos import (FAVORITOS_DEFAULT, FAVORITOS_MAX, agregar_favorito, icono_activo,
                                  quitar_favorito, renderizar_barra_favoritos)

__all__ = ["renderizar_barra_favoritos", "agregar_favorito", "quitar_favorito", "icono_activo",
           "FAVORITOS_MAX", "FAVORITOS_DEFAULT"]


# -------------------------------------------------------------------------------------------------------
# --------------------------------- FIN Piña y Jara favoritos_barra .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
