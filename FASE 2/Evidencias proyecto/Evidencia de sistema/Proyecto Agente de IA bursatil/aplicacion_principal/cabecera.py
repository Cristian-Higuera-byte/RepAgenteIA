# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara cabecera .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

"""
Cabecera de la página: datos de la cuenta de MetaTrader 5 y barra superior fija.

La barra superior muestra el usuario, el saldo (equity), la ganancia/pérdida flotante y las
métricas de riesgo. Este módulo obtiene esos datos y los entrega al componente que la dibuja.
"""
import streamlit as st

from componentes_plataforma.barra_superior import renderizar_barra_navegacion as renderizar_nav_superior


# TITULO DATOS CUENTA

def datos_cuenta():
    """
    Lee de MetaTrader 5 los datos que necesita la barra superior y los devuelve en una tupla.

    Inicia la conexión con MT5 (si ya está iniciada no hace nada) y consulta la información de la
    cuenta. Devuelve `(saldo, moneda, pl, metricas)`: el equity, la moneda de la cuenta (USD si no
    se pudo leer), la ganancia/pérdida flotante y las métricas ligeras de la barra (Riesgo,
    Drawdown y Mercado). Si MT5 responde con error, saldo y pl quedan en `None` para que la barra
    muestre un valor vacío en vez de romper la página.
    """
    from herramientas.puente_mt5 import inicializar_mt5, obtener_info_cuenta
    inicializar_mt5()
    info_cuenta = obtener_info_cuenta()
    # Cuando MT5 devuelve un diccionario con la clave "error", ningún dato de la cuenta es confiable.
    sin_error = "error" not in info_cuenta
    saldo = info_cuenta.get("equity") if sin_error else None
    moneda = info_cuenta.get("currency", "USD") if sin_error else "USD"
    ganancia_perdida = info_cuenta.get("profit") if sin_error else None  # ganancia/pérdida flotante

    # Métricas ligeras de la barra superior (Riesgo · Drawdown · Mercado). No lee el historial
    # de operaciones, así que es barata; el símbolo activo define el estado del mercado.
    try:
        from herramientas.estadisticas_portafolio import metricas_barra
        metricas = metricas_barra(st.session_state.get("activo_seleccionado"))
    except Exception:
        # La barra nunca debe romper la aplicación por culpa de estas métricas.
        metricas = None
    return saldo, moneda, ganancia_perdida, metricas


# TITULO RENDERIZAR BARRA SUPERIOR

def renderizar_barra_superior(usuario: dict, saldo, moneda, pl, metricas) -> None:
    """
    Dibuja la barra superior fija con el usuario, el saldo, la ganancia/pérdida y las métricas.

    Recibe el diccionario del usuario autenticado (de él toma solo el nombre) y los datos que
    devolvió `datos_cuenta()`. La barra va dentro de un contenedor con la clave `barra_navegacion_fija`,
    que el CSS global usa para fijarla arriba. El desplazamiento de la barra según el ancho de la
    barra lateral (70 px o 220 px) lo resuelve el CSS de `componentes_plataforma/barra_lateral`,
    sin necesidad de volver a ejecutar Python.
    """
    with st.container(key="barra_navegacion_fija"):
        renderizar_nav_superior(
            usuario=usuario.get("nombre", "Usuario"),
            saldo=saldo,
            moneda=moneda,
            pl=pl,
            metricas=metricas,
        )


# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara cabecera .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
