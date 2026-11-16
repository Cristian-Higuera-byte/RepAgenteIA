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

"""Datos constantes de los paneles del agente.

Define el mapa de estados de una orden del agente -> (texto, color), cargado desde
estados.json, y la clave de `st.session_state` donde se guarda el aviso mostrado tras
confirmar, rechazar o autorizar. Lo usan historial.py, propuestas.py y vigilancias.py.
"""
from pathlib import Path

from componentes_plataforma._estaticos import datos_json

# Clave de session_state con el aviso pendiente de mostrar; el panel de propuestas lo consume (pop) en cada ejecución.
CLAVE_AVISO = "_aviso_orden"   # session_state: aviso (ok|error, mensaje) tras confirmar/rechazar/autorizar

# Estado de la orden (p. ej. "EJECUTADA") -> (etiqueta visible, color hexadecimal) para la insignia del historial.
# Se convierten las listas del JSON a tuplas para que sean inmutables y se puedan desempaquetar.
ESTADOS = {k: tuple(v) for k, v in datos_json(Path(__file__).parent / "estados.json").items()}


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
