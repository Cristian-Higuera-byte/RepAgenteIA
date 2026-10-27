# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara propuestas .PY ----------------------------------
# -------------------------------------------------------------------------------------------------------

"""Panel DERECHO: propuestas pendientes con Confirmar / Rechazar, interruptor de emergencia y vigilancias.

Es el único panel desde el que una orden propuesta por el agente puede llegar a MT5
(a través de nucleo_agente.ordenes.confirmar_orden, tras la acción explícita del usuario).
"""
from typing import Any

import streamlit as st

from componentes_plataforma.agente_paneles.datos import CLAVE_AVISO
from componentes_plataforma.agente_paneles.formato import cabecera_agente, clase_lado, escapar_html, hora, par_clave_valor, numero, titulo, vacio
from componentes_plataforma.agente_paneles.vigilancias import seccion_vigilancias, usuario_id
from nucleo_agente import ordenes, vigilancia


# TITULO TARJETA PENDIENTE

def tarjeta_pendiente(o: dict[str, Any]) -> str:
    """Construye el HTML de la tarjeta de una orden pendiente `o`.

    Para aperturas muestra precio de referencia, stop loss, take profit y el riesgo estimado
    (dinero y % del equity); para cierres, el precio actual y el resultado flotante. Incluye
    hora de vencimiento, insignia "Pendiente" y la justificación del agente (escapada).
    """
    # Apertura: niveles y riesgo; cierre: precio actual y resultado
    if o.get("accion") == "abrir":
        datos = (
            par_clave_valor("Precio ref.", numero(o.get("precio_ref")))
            + par_clave_valor("Stop loss", numero(o.get("sl")), "neg")
            + par_clave_valor("Take profit", numero(o.get("tp")), "pos")
        )
        extra = (
            f"<div class='agente-riesgo'>Riesgo ≈ <b>{(o.get('riesgo_dinero') or 0):.2f}</b> "
            f"· {(o.get('riesgo_pct') or 0):.2f}% del equity</div>"
        )
    else:
        datos = par_clave_valor("Precio actual", numero(o.get("precio_ref"))) + par_clave_valor("Resultado", f"{(o.get('riesgo_dinero') or 0):+.2f}")
        extra = ""
    # Justificación del agente, con texto por defecto si falta
    just = (o.get("justificacion") or "Sin justificación").strip()
    return (
        "<div class='agente-fila'>"
        f"<div class='agente-superior'><span class='agente-t'>Vence a las {hora(o.get('expira'))}</span>"
        "<span class='agente-insignia' style='color:#f0b90b;border-color:#f0b90b55;background:#f0b90b18'>"
        "Pendiente</span></div>"
        f"<div class='agente-principal'>{titulo(o)}</div>"
        f"<div class='agente-cuadricula'>{datos}</div>{extra}"
        f"<div class='agente-quote'>{escapar_html(just)}</div></div>"
    )


# TITULO ALTERNAR BLOQUEO

def alternar_bloqueo() -> None:
    """Callback del interruptor: guarda en el núcleo el valor de `parada_emergencia_interruptor_ui`.

    Activa o desactiva el bloqueo de aperturas (efecto persistente en nucleo_agente.ordenes).
    """
    ordenes.fijar_interruptor_emergencia(bool(st.session_state.get("parada_emergencia_interruptor_ui")))


# TITULO RENDERIZAR ORDENES PROPUESTAS

def renderizar_ordenes_propuestas(altura: int = 300) -> None:
    """Dibuja el panel derecho: interruptor de emergencia, vigilancias y órdenes pendientes.

    `altura` (px) fija el alto del área con scroll cuando hay más de un elemento. Consume el
    aviso de `st.session_state[CLAVE_AVISO]` y lo muestra. Los botones Confirmar / Rechazar
    llaman a nucleo_agente.ordenes (confirmar puede enviar la orden a MT5) y reejecutan la
    app completa. Si falla la lectura muestra una advertencia y no dibuja el panel.
    """
    # Recupera (y borra) el aviso dejado por la acción anterior
    aviso = st.session_state.pop(CLAVE_AVISO, None)

    # Lee el estado actual: pendientes, interruptor y vigilancias del usuario
    try:
        pendientes = ordenes.listar_pendientes()
        bloqueado = ordenes.interruptor_emergencia_activo()
        uid = usuario_id()
        vigs = vigilancia.listar(uid)
    except Exception as e:  # noqa: BLE001
        st.warning(f"No se pudieron leer las órdenes del agente: {e}")
        return

    # Panel con clave fija: estilos.css lo apunta con el prefijo agp_
    with st.container(key="agente_propuestas_panel"):
        st.html(cabecera_agente(
            "pending_actions", "Órdenes propuestas",
            "El agente propone y tú confirmas. Solo opera solo si autorizas una vigilancia. Solo cuenta demo.",
        ))
        # Resultado de la última acción (verde si ok, rojo si error)
        if aviso:
            (st.success if aviso[0] == "ok" else st.error)(aviso[1])

        # Interruptor de emergencia: bloquea proponer y confirmar aperturas
        st.session_state["parada_emergencia_interruptor_ui"] = bloqueado  # el interruptor refleja siempre lo guardado
        with st.container(key="agente_propuestas_parada_emergencia"):
            st.toggle(
                "⛔ Bloquear aperturas", key="parada_emergencia_interruptor_ui", on_change=alternar_bloqueo,
                help="Interruptor de emergencia: no se podrán proponer ni confirmar aperturas.",
            )

        # Sin nada que mostrar: mensaje vacío y fin
        if not pendientes and not vigs:
            st.html(vacio(
                "inbox", "No hay órdenes pendientes ni vigilancias. Cuando el agente proponga una orden o "
                "una vigilancia, aparecerá aquí para que la autorices o la rechaces.",
            ))
            return

        # Solo se usa scroll de altura fija si hay más de un elemento
        contenedor = (
            st.container(height=altura, border=False, key="agente_propuestas_desplazamiento")
            if len(pendientes) + len(vigs) > 1 else st.container(border=False, key="agente_propuestas_desplazamiento")
        )
        with contenedor:
            # Sección de vigilancias automáticas
            if vigs:
                st.html("<div class='agente-seccion'>Vigilancia automática</div>")
                if any(v["estado"] == vigilancia.ACTIVA for v in vigs):
                    # con vigilancias activas, solo esta sección se refresca sola (sin recargar la página)
                    st.fragment(run_every="8s")(seccion_vigilancias)(uid)
                else:
                    seccion_vigilancias(uid)
            # Subtítulo de órdenes solo si hay ambos grupos
            if vigs and pendientes:
                st.html("<div class='agente-seccion'>Órdenes pendientes</div>")
            # Una tarjeta por orden pendiente, con botones Confirmar y Rechazar
            for o in pendientes:
                with st.container(key=f"agente_propuestas_tarjeta_{clase_lado(o)}_{o['id']}"):
                    st.html(tarjeta_pendiente(o))
                    if st.button("Confirmar orden", key=f"agente_propuestas_aceptar_{o['id']}", icon=":material/check:",
                                 type="primary", width="stretch"):
                        resultado = ordenes.confirmar_orden(o["id"])
                        st.session_state[CLAVE_AVISO] = ("ok" if resultado["ok"] else "error", resultado["mensaje"])
                        st.rerun(scope="app")  # refresca también el historial de la izquierda
                    if st.button("Rechazar", key=f"agente_propuestas_no_{o['id']}", width="stretch"):
                        ordenes.rechazar_orden(o["id"])
                        st.rerun(scope="app")


# -------------------------------------------------------------------------------------------------------
# ------------------------------------ FIN Piña y Jara propuestas .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
