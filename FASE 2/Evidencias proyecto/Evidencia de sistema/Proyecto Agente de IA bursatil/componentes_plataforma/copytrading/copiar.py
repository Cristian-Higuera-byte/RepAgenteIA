# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ INICIO Piña y Jara copiar .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Ventanas del copy trading para el inversor: abrir la cuenta de inversor y configurar una copia.

Sigue el flujo de XM. Primero «Abrir una cuenta de inversor» (aceptar los términos); luego el panel de copia con la inversión mínima, el equity de tu cuenta demo, los
fondos propios del gestor, el multiplicador de asignación (por importe invertido o por multiplicador fijo), «Copiar operaciones abiertas» y los interruptores de take profit
y stop loss (porcentaje del importe). La lógica está en `herramientas/copiador.py`. Al crear la copia se lleva al usuario a la sección Cartera.
Es solo demo: con una cuenta real la ventana avisa y no deja copiar. Avisa de la comisión de rendimiento (se paga con la billetera virtual) y ofrece ajustar el perfil de inversor a la estrategia.
"""
import streamlit as st

from componentes_plataforma.copytrading import perfil_copia
import configuracion
from herramientas import billetera, copiador, gestor_autenticacion, gestor_estrategias, metricas_estrategia
from herramientas.puente_mt5 import obtener_info_cuenta

# Texto resumido de los términos de la cuenta de inversor
_TERMINOS = ("Copiar estrategias es solo para cuentas demo de práctica. El rendimiento pasado no garantiza resultados futuros y copiar conlleva riesgo de pérdida. "
             "Las operaciones se replican de forma automática en tu cuenta demo con el tamaño que elijas; puede haber diferencias de precio y operaciones que no se puedan copiar. "
             "Puedes pausar o detener una copia cuando quieras.")


# TITULO USUARIO

def _usuario_id():
    """Id del usuario de la sesión o None."""
    usuario = st.session_state.get("usuario_informacion") or {}
    return usuario.get("id") if isinstance(usuario, dict) else None


# TITULO ABRIR CUENTA

def _abrir_cuenta(uid) -> None:
    """Panel para abrir la cuenta de inversor: términos, casilla de aceptación y botón para crearla."""
    st.markdown("#### Abrir una cuenta de inversor")
    st.caption("Una cuenta de inversor permite seguir estrategias en el copy trading de la plataforma.")
    st.info(_TERMINOS)
    acepto = st.checkbox("Declaro que he leído y comprendo los términos y condiciones, y los acepto.", key="copiar_acepto_terminos")
    if st.button("Crear cuenta de inversor", type="primary", width="stretch", disabled=not acepto, key="copiar_crear_cuenta"):
        try:
            copiador.abrir_cuenta_inversor(uid, acepto)
            st.rerun(scope="fragment")
        except copiador.ErrorCopia as e:
            st.error(str(e))


# TITULO PROPUESTA DE PERFIL

def _propuesta_perfil(uid, e: dict) -> dict:
    """Cambios que haría al perfil de inversor asemejarlo a la estrategia `e` (nivel de riesgo y tipos de activo que opera); sin cambios si no se puede calcular."""
    vacio = {"cambios": [], "nuevos": {}, "previos": {}}
    try:
        metricas = metricas_estrategia.detalle(gestor_autenticacion._supabase, e["id"])["metricas"]
        tipos = list((metricas.get("asignacion_cerradas") or {}).keys()) or ([e["cat"]] if e.get("cat") else [])
        return perfil_copia.propuesta(uid, e["riesgo"], tipos)
    except Exception:  # noqa: BLE001 - el ajuste de perfil es opcional: si falla, se copia sin él
        return vacio


# TITULO FORMULARIO DE COPIA

def _formulario(uid, e: dict) -> None:
    """Panel de la copia: datos de la estrategia, asignación, copiar abiertas, take profit y stop loss, y el botón Copiar."""
    try:
        info = obtener_info_cuenta() or {}
    except Exception:  # noqa: BLE001
        info = {}
    equity = float(info.get("equity") or 0) if "error" not in info else 0.0
    c1, c2, c3 = st.columns(3)
    c1.metric("Inversión mínima", f"${e['inv_min']:,}")
    c2.metric("Equidad de tu cuenta", f"${equity:,.2f}")
    c3.metric("Fondos propios del gestor", f"${e['fondos']:,}")
    modo = st.radio("Multiplicador de asignación", ["Importe invertido", "Multiplicador fijo"], horizontal=True, key="copiar_modo")
    por_importe = modo == "Importe invertido"
    importe = st.number_input("Importe invertido ($)", min_value=float(e["inv_min"]), value=float(e["inv_min"]), step=10.0, key="copiar_importe", disabled=not por_importe,
                              help="Dinero de tu cuenta que asignas a esta estrategia. Las operaciones se copian proporcionalmente a los fondos del gestor.")
    multiplicador = st.number_input("Multiplicador fijo", min_value=0.01, max_value=100.0, value=0.02, step=0.01, format="%.2f", key="copiar_multiplicador", disabled=por_importe,
                                    help="Cada operación se copia con el volumen del gestor multiplicado por este número.")
    if por_importe and e["fondos"]:
        st.caption(f"Proporción de copia: x{importe / e['fondos']:.4f} el volumen del gestor.")
    st.info(f"Comisión de rendimiento: **{e['comision']:g}%** de tu ganancia nueva, que se liquida cada {configuracion.COPYTRADING['liquidacion_dias']} días y al detener la copia. "
            f"Se paga con tu billetera virtual (saldo: ${billetera.saldo():,.2f}).")
    abiertas = st.checkbox("Copiar operaciones abiertas", key="copiar_abiertas",
                           help="Si lo marcas, las posiciones que el gestor ya tiene abiertas se abrirán al precio de mercado vigente (si el mercado está cerrado, cuando abra).")
    tp_on = st.toggle("Take profit", key="copiar_tp_on")
    tp = st.number_input("Cerrar la copia al ganar (% del importe)", min_value=1.0, max_value=1000.0, value=50.0, step=5.0, key="copiar_tp", disabled=not tp_on or not por_importe) if tp_on else None
    sl_on = st.toggle("Stop loss", key="copiar_sl_on")
    sl = st.number_input("Cerrar la copia al perder (% del importe)", min_value=1.0, max_value=100.0, value=30.0, step=5.0, key="copiar_sl", disabled=not sl_on or not por_importe) if sl_on else None
    if (tp_on or sl_on) and not por_importe:
        st.warning("El take profit y el stop loss se calculan sobre el importe invertido: usa el modo «Importe invertido».")
    propuesta = _propuesta_perfil(uid, e)
    ajustar = False
    if propuesta["cambios"]:
        ajustar = st.checkbox("Ajustar mi perfil de inversor a esta estrategia", key="copiar_ajustar_perfil",
                              help="Tu perfil se parecerá al de la estrategia. Puedes volver a tu perfil anterior al dejar de copiar.")
        if ajustar:
            for cambio in propuesta["cambios"]:
                st.caption(f"{cambio['etiqueta']}: {cambio['antes']} → **{cambio['despues']}**")
    if st.button("Copiar", type="primary", width="stretch", key="copiar_confirmar"):
        try:
            copiador.crear_copia(uid, int(e["id"]), "importe" if por_importe else "multiplicador", importe if por_importe else None, None if por_importe else multiplicador,
                                 abiertas, tp if por_importe else None, sl if por_importe else None, equity_cuenta=equity or None,
                                 perfil_previo=propuesta["previos"] if ajustar else None)
        except copiador.ErrorCopia as err:
            st.error(str(err))
            return
        if ajustar:
            perfil_copia.aplicar(uid, propuesta["nuevos"])
        st.session_state["copytrading_aviso"] = f"Ya estás copiando «{e['nombre']}». Las operaciones nuevas del gestor se replicarán en tu cuenta demo."
        st.session_state["copytrading_seccion"] = "Cartera"
        st.session_state.copytrading_estrategia = None
        st.rerun()


# TITULO DIALOGO COPIAR

@st.dialog("Copiar estrategia", width="large")
def dialogo_copiar(e: dict) -> None:
    """Ventana de copia de la estrategia real `e`: pide abrir la cuenta de inversor si falta y luego muestra el formulario de copia."""
    if not copiador.disponible():
        st.info("Copiar estrategias necesita la base de datos (Supabase) y el modo multiusuario, que no están activos en este equipo.")
        return
    if gestor_estrategias.cuenta_actual() != "demo":
        st.warning("Por ahora el copy trading funciona solo con la cuenta demo. Cambia a tu cuenta demo para copiar.")
        return
    uid = _usuario_id()
    if uid is None:
        st.info("Inicia sesión para copiar estrategias.")
        return
    st.markdown(f"**{e['nombre']}** · @{e['gestor']}")
    try:
        tiene_cuenta = copiador.cuenta_inversor(uid) is not None
    except Exception:  # noqa: BLE001
        st.error("No se pudo consultar tu cuenta de inversor. Inténtalo de nuevo en un momento.")
        return
    (_formulario if tiene_cuenta else _abrir_cuenta)(*((uid, e) if tiene_cuenta else (uid,)))



# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara copiar .PY --------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
