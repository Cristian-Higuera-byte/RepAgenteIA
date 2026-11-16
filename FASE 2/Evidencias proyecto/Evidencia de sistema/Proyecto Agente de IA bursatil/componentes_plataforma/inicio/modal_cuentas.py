# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# --------------------------------- INICIO Piña y Jara modal_cuentas .PY --------------------------------
# -------------------------------------------------------------------------------------------------------

"""Modal "Seleccione cuenta".

Diálogo de Streamlit para ver las cuentas y elegir con cuál operar. Con el modo multiusuario muestra las dos cuentas
del usuario, Demo y Real: la conectada se puede elegir y la que falta se puede conectar desde ahí. Sin ese modo
(MT5 expone solo la cuenta conectada en el terminal) muestra la cuenta activa y recuerda cómo agregar otra.
Su visibilidad se controla con `st.session_state.inicio_modal_cuentas`.
"""
import streamlit as st

# Estilos de Inicio (las clases selc-* del diálogo viven en estilos.css).

from componentes_plataforma.conectar_cuenta import abrir_gestion, completar_cuenta_faltante
from componentes_plataforma.conectar_cuenta.modo import cuentas_conectadas, fijar_modo, invalidar_cuentas, modo_activo_demo, usuario_id_actual
from componentes_plataforma.inicio.estilos import CSS
# Formato de dinero del equity.
from componentes_plataforma.inicio.formato import formatear_dinero
# Datos de la cuenta conectada en MT5.
from herramientas.backends import sesiones_capital
from herramientas.puente_mt5 import obtener_info_cuenta


# TITULO CERRAR MODAL CUENTAS

def _cerrar_modal_cuentas():
    """Callback `on_dismiss` del diálogo: apaga la bandera `inicio_modal_cuentas` para que no se reabra en el próximo rerun."""
    st.session_state.inicio_modal_cuentas = False


# TITULO TARJETA DE CUENTA

def _tarjeta(tipo: str, activa: bool, equity=None, meta: str = "") -> str:
    """HTML de la tarjeta de una cuenta: tipo (Demo/Real), saldo y detalle; sin saldo se muestra como "Sin conectar"."""
    cls_tipo = "selector-cuenta-real" if tipo == "Real" else "selector-cuenta-demo"
    saldo = formatear_dinero(equity) if equity is not None else "Sin conectar"
    return (
        f"<div class='selector-cuenta-tarjeta{' activa' if activa else ''}'><div class='selector-cuenta-superior'>"
        f"<div><div style='color:#e6edf3;font-weight:700;'>Cuenta {tipo}</div>"
        f"<div class='selector-cuenta-bal'>{saldo}</div>"
        f"<div class='selector-cuenta-meta'>{meta}</div></div>"
        f"<span class='selector-cuenta-tipo {cls_tipo}'>{tipo}</span></div></div>"
    )


# TITULO CUENTAS MULTIUSUARIO

def _cuentas_multiusuario() -> None:
    """Contenido del modal con el modo multiusuario: tarjetas Demo y Real, con botón para usar o conectar cada una.

    Elegir una cuenta conectada cambia el modo activo y reejecuta la página; la que falta lleva a la pantalla de conexión."""
    usuario_id = usuario_id_actual()
    # Si solo hay una cuenta conectada se prueba la otra con los mismos datos (una vez por sesión)
    with st.spinner("Revisando tus cuentas en Capital.com..."):
        intento = completar_cuenta_faltante(usuario_id)
    cuentas = cuentas_conectadas(refrescar=True)
    en_demo = modo_activo_demo()
    for tipo, es_demo in (("Demo", True), ("Real", False)):
        conectada = cuentas.get("demo" if es_demo else "real")
        activa = conectada and es_demo == en_demo
        equity, meta = None, ""
        if conectada:
            try:
                with sesiones_capital.con_clave((usuario_id, es_demo)):
                    info = obtener_info_cuenta()
            except Exception:
                info = {"error": "sin lectura"}
            if "error" not in info:
                equity = info.get("equity", 0)
                meta = f"#{info.get('login', '—')} · Capital.com ({'demo' if es_demo else 'real'})"
            else:
                meta = "Conectada, sin lectura de saldo en este momento"
                equity = 0
        if not conectada and intento and not intento.get("ok") and intento.get("tipo") == tipo:
            meta = "Capital.com no aceptó tu API en esta cuenta"
        st.html(_tarjeta(tipo, bool(activa), equity, meta))
        if not conectada and intento and not intento.get("ok") and intento.get("tipo") == tipo:
            st.caption(intento.get("mensaje", ""))
            if st.button("Reintentar con la misma API", width="stretch", key=f"selector_cuenta_reintentar_{tipo}"):
                completar_cuenta_faltante(usuario_id, reintentar=True)
                st.rerun()
        if activa:
            st.caption(f"Cuenta {tipo.lower()} en uso.")
        elif conectada:
            rotulo = f"Usar cuenta {tipo}" + (" (opera con dinero real)" if not es_demo else "")
            if st.button(rotulo, width="stretch", key=f"selector_cuenta_usar_{tipo}"):
                fijar_modo(es_demo)
                invalidar_cuentas()
                st.session_state.inicio_modal_cuentas = False
                st.rerun()
        elif st.button(f"Conectar cuenta {tipo}", icon=":material/add:", width="stretch", key=f"selector_cuenta_conectar_{tipo}"):
            abrir_gestion()
            st.session_state.inicio_modal_cuentas = False
            st.rerun()


# TITULO MODAL CUENTAS

@st.dialog("Seleccione cuenta", on_dismiss=_cerrar_modal_cuentas)
def modal_cuentas():
    """Diálogo «Seleccione cuenta»: muestra la cuenta conectada (equity, login, servidor, tipo Demo/Real).

    Decorada con `st.dialog`. Sin conexión a MT5 muestra una advertencia. El botón «Crear nueva cuenta»
    solo informa por toast que hay que iniciar sesión con otra cuenta en el terminal MT5.
    """
    # Los diálogos se montan fuera del flujo normal, por eso necesitan su propia inyección de estilos.
    st.html(CSS)
    if sesiones_capital.MULTIUSUARIO:
        _cuentas_multiusuario()
        return
    # Datos de la cuenta conectada.
    info = obtener_info_cuenta()
    if "error" in info:
        st.warning("No hay conexión con MetaTrader 5.")
        return
    tipo = info.get("tipo", "Demo")
    # Clase de color de la etiqueta Real/Demo.
    cls_tipo = "selector-cuenta-real" if tipo == "Real" else "selector-cuenta-demo"
    # Tarjeta de la cuenta activa.
    st.html(
        "<div class='selector-cuenta-tarjeta activa'><div class='selector-cuenta-superior'>"
        "<div><div style='color:#e6edf3;font-weight:700;'>Standard</div>"
        f"<div class='selector-cuenta-bal'>{formatear_dinero(info.get('equity', 0))}</div>"
        f"<div class='selector-cuenta-meta'>#{info.get('login','—')} · Standard · MT5 · "
        f"{info.get('servidor','')}</div></div>"
        f"<span class='selector-cuenta-tipo {cls_tipo}'>{tipo}</span>"
        "</div></div>"
    )
    st.caption("MetaTrader 5 muestra solo la cuenta conectada en el terminal.")
    if st.button("Crear nueva cuenta", icon=":material/add:", width="stretch", key="selector_cuenta_crear"):
        st.toast("Para agregar otra cuenta, inicia sesión con ella en el terminal MT5.")


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- FIN Piña y Jara modal_cuentas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
