# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara precios .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Actualización LIGERA de precios de la watchlist desde MT5 (tick en vivo).

Pensada para ejecutarse con frecuencia desde un fragmento de Streamlit: no recarga la watchlist, solo refresca
precio, variación y sparkline de los símbolos ya cargados en la sesión.
"""
import streamlit as st

from components.mercado_datos.referencias import variacion
from components.mercado_datos.sparkline import asegurar_semilla, empujar_minilinea
from tools.puente_mt5 import inicializar_mt5, obtener_precio_actual


def actualizar_precios_mt5():
    """Actualización LIGERA de precios de la watchlist desde MT5 (tick en vivo).
    Usa el nombre EXACTO del símbolo (con '...') — sin limpiarlo.

    No recibe parámetros ni devuelve nada. Recorre `st.session_state.datos_mercado_real` y, por cada símbolo,
    lee el tick de MT5, actualiza `precio`, `var` y `sube`, y empuja el precio al buffer del sparkline.
    Cualquier error en un símbolo se ignora para no interrumpir la actualización de los demás.
    """
    # Garantiza que la conexión a MT5 esté viva antes de pedir ticks
    inicializar_mt5()
    # Si la carga inicial aún no ocurrió no hay nada que actualizar
    datos = st.session_state.get("datos_mercado_real")
    if not datos:
        return
    # Se itera sobre una copia de las claves porque el diccionario se modifica durante el bucle
    for simbolo in list(datos.keys()):
        try:
            # Tick en vivo; si MT5 devuelve error se salta este símbolo
            info_tick = obtener_precio_actual(simbolo)
            if "error" in info_tick:
                continue
            # Último trade si es positivo; si no, el bid
            precio_actual = info_tick.get("last", 0) if info_tick.get("last", 0) > 0 else info_tick.get("bid", 0)
            if precio_actual and precio_actual > 0:
                # Cambio contra el precio guardado antes de este refresco (respaldo si no hay variación diaria)
                precio_anterior = datos[simbolo].get("precio", precio_actual)
                cambio = precio_actual - precio_anterior
                porcentaje = (cambio / precio_anterior * 100) if precio_anterior else 0.0
                decimales = 2 if precio_actual > 100 else 5
                datos[simbolo]["precio"] = precio_actual
                var = variacion(simbolo, precio_actual, decimales)
                if var:                                   # variación del día
                    datos[simbolo]["var"], datos[simbolo]["sube"] = var
                else:                                     # sin referencia: vs. tick anterior
                    datos[simbolo]["sube"] = cambio >= 0
                    if cambio != 0:
                        datos[simbolo]["var"] = f"{cambio:+.{decimales}f} ({porcentaje:+.2f}%)"
                asegurar_semilla(simbolo)   # símbolos agregados después de la carga
                empujar_minilinea(simbolo, precio_actual)
        except Exception:
            # Un símbolo con error no debe detener la actualización del resto
            pass


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara precios .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
