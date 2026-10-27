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

"""Informe integral de la cartera abierta.

NOMBRE DEL ARCHIVO: herramientas_agente/informe_cartera_herramientas

Junta en una sola llamada lo que hoy el agente tendría que encadenar a mano: exposición actual,
riesgo, volatilidad, distancia al stop, correlaciones entre las posiciones abiertas, noticias de
alto impacto y escenarios de la cartera. Cada sección se calcula por separado: si una falla se
informa en `secciones_no_disponibles` y el resto sigue valiendo. Los importes salen del cálculo de
beneficios de MT5 (moneda de la cuenta); nada se inventa ni se estima con tablas fijas.

Archivos: herramientas.py (registro de las herramientas), auxiliares.py, esquemas.json.

Este paquete es una fachada: reexporta las constantes de umbrales y los helpers
de cálculo de ``auxiliares`` y la herramienta ``informe_cartera`` de
``herramientas``, de modo que el resto del proyecto puede importar todo desde
``herramientas_agente.informe_cartera_herramientas`` sin conocer los archivos internos.
"""
from herramientas_agente.informe_cartera_herramientas.auxiliares import (
    MAX_SIMBOLOS_VOLATILIDAD,
    UMBRAL_CORRELACION,
    UMBRAL_EXPOSICION_EQUIDAD_PCT,
    NIVEL_MARGEN_MINIMO_PCT,
    _DIVISAS_FX,
    _par_fx,
    _signo,
    _sensibilidad_1pct,
    _exposicion,
    _volatilidad,
    _correlaciones,
    _noticias,
    _escenarios,
    _alertas,
)
from herramientas_agente.informe_cartera_herramientas.herramientas import informe_cartera


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
