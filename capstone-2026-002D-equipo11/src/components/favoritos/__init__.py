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

"""Barra superior de activos favoritos del dashboard (estilo terminal de trading).

Este paquete agrupa todo lo necesario para dibujar la franja de «Mis favoritos» y para
administrar la lista de favoritos de cada usuario. Los módulos son:

    estado.py    favoritos del usuario: cargar, agregar, quitar (se guardan en Supabase)
    tarjeta.py   HTML de cada tarjeta "burbuja" (ícono, precio en vivo, variación, flecha)
    barra.py     renderizar_barra_favoritos(): encabezado + 6 slots + botón «+»
    estilos.css  estilos de la barra

Este `__init__` actúa como fachada: reexporta la función de dibujo, las operaciones de estado
y las constantes para que el resto del dashboard importe todo desde
`components.favoritos` sin conocer la estructura interna.
"""
# Dibuja la barra completa de favoritos.
from components.favoritos.barra import renderizar_barra_favoritos
# Operaciones y límites de la lista de favoritos del usuario.
from components.favoritos.estado import FAVORITOS_DEFAULT, FAVORITOS_MAX, agregar_favorito, quitar_favorito
# Ícono de un activo (reexportado por compatibilidad con módulos que lo importan desde aquí).
from components.favoritos.tarjeta import icono_activo

# API pública del paquete.
__all__ = ["renderizar_barra_favoritos", "agregar_favorito", "quitar_favorito", "icono_activo",
           "FAVORITOS_MAX", "FAVORITOS_DEFAULT"]


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
