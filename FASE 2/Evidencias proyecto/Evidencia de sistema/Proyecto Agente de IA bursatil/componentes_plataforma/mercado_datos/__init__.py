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
componentes_plataforma/mercado_datos
------------------------
Paquete de datos de mercado en sesión (watchlist, índices globales, variación del día y sparklines).

Existe para que el resto de la plataforma (barra de índices, watchlist, favoritos, mini-gráficos) lea siempre
del mismo estado de Streamlit (`st.session_state`) y para que la carga pesada ocurra una sola vez por sesión,
mientras que un fragmento ligero mantiene los precios en vivo con el tick de MT5. Está separado por
responsabilidad:
  carga.py        carga inicial (indices_globales.json + watchlist del usuario)
  entrada.py      entrada de un símbolo (nombre, categoría, precio, variación)
  precios.py      actualización ligera de precios con el tick de MT5
  referencias.py  cierre diario anterior y variación del día
  sparkline.py    semilla M1 y buffer del mini-gráfico
"""
# Fachada: reexporta la API pública del paquete para que los consumidores importen desde un solo lugar
from componentes_plataforma.mercado_datos.carga import cargar_datos_mercado
from componentes_plataforma.mercado_datos.entrada import construir_entrada
from componentes_plataforma.mercado_datos.precios import actualizar_precios_mt5
from componentes_plataforma.mercado_datos.referencias import cierre_previo, variacion
from componentes_plataforma.mercado_datos.sparkline import historial_sparkline

# Nombres públicos del paquete (lo que se puede importar con `from ... import *`)
__all__ = ["cargar_datos_mercado", "construir_entrada", "actualizar_precios_mt5", "cierre_previo", "variacion",
           "historial_sparkline"]


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
