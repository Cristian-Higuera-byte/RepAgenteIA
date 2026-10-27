# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- INICIO Piña y Jara datos .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Íconos de línea (estilo Lucide/Feather, heredan color con currentColor) y emoji por tipo de notificación.

Los datos viven en iconos.json; este módulo los lee una vez al importar y los expone como
constantes para barra.py (ícono de tema) y notificaciones.py (emoji por tipo de aviso).
"""
from pathlib import Path

from componentes_plataforma._estaticos import datos_json

# Diccionario completo leído de iconos.json (clave -> SVG en cadena, o mapa de emoji).
_D = datos_json(Path(__file__).parent / "iconos.json")

# Ícono SVG del botón de tema (se dibuja junto al saldo en la barra).
ICONO_TEMA = _D["tema"]
# Tipo de notificación -> emoji usado en la lista y en el toast.
ICONO_TIPO = _D["tipo_notificacion"]


# -------------------------------------------------------------------------------------------------------
# -------------------------------------- FIN Piña y Jara datos .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
