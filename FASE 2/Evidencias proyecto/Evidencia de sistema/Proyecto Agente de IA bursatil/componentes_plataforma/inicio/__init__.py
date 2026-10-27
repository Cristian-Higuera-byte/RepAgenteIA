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
componentes_plataforma/inicio
-----------------
Panel de Inicio (vista "Home") con diseño de panel de bróker profesional:
- Encabezado: saludo + selector de cuenta (chip) + botón "Operar".
- Tarjeta principal: equity grande, P/G flotante (pastilla) y 3 indicadores
  (Saldo, Margen libre, Margen usado). Botón de ojo para ocultar los montos.
- "Salud de la cuenta": nivel de margen con semáforo, barra de margen usado y
  datos técnicos (apalancamiento, crédito, tipo, servidor).
- Accesos rápidos (tarjetas con ícono, título, subtítulo y flecha).
- Promociones (banners sobrios) y Posiciones abiertas (tabla con íconos).

Archivos: panel.py (arma la vista), cuenta.py, posiciones.py, historial.py, modal_cuentas.py,
formato.py, datos.py (lee datos.json: accesos y promos), estilos.py (carga estilos.css) y estilos.css.

Datos en vivo: los números llevan atributos data-pj-* y los pinta el feed
(componentes_plataforma/flujo_precios) con el MISMO dato que la barra superior.

Este `__init__` es una fachada: reexporta solo `renderizar_panel_inicio`, el punto de entrada que usa
`aplicacion.py` (a través de `componentes_plataforma/inicio/`) para dibujar la vista Inicio.
"""
# Función que dibuja toda la vista de Inicio.
from componentes_plataforma.inicio.panel import renderizar_panel_inicio

# API pública del paquete.
__all__ = ["renderizar_panel_inicio"]


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
