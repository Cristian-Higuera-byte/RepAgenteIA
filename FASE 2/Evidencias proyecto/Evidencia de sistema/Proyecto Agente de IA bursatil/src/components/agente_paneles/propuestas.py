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
(a través de core.ordenes.confirmar_orden, tras la acción explícita del usuario).
"""
from typing import Any

import streamlit as st

from components.agente_paneles.datos import CLAVE_AVISO
from components.agente_paneles.formato import cabecera_agente, clase_lado, escapar_html, hora, par_clave_valor, numero, titulo, vacio
from components.agente_paneles.vigilancias import seccion_vigilancias, usuario_id
from core import ordenes, vigilancia


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
            f"<div class='ag-risk'>Riesgo ≈ <b>{(o.get('riesgo_dinero') or 0):.2f}</b> "
            f"· {(o.get('riesgo_pct') or 0):.2f}% del equity</div>"
        )
    else:
        datos = par_clave_valor("Precio actual", numero(o.get("precio_ref"))) + par_clave_valor("Resultado", f"{(o.get('riesgo_dinero') or 0):+.2f}")
        extra = ""
    # Justificación del agente, con texto por defecto si falta
    just = (o.get("justificacion") or "Sin justificación").strip()
    return (
        "<div class='ag-row'>"
        f"<div class='ag-top'><span class='ag-t'>Vence a las {hora(o.get('expira'))}</span>"
        "<span class='ag-badge' style='color:#f0b90b;border-color:#f0b90b55;background:#f0b90b18'>"
        "Pendiente</span></div>"
        f"<div class='ag-main'>{titulo(o)}</div>"
        f"<div class='ag-grid'>{datos}</div>{extra}"
        f"<div class='ag-quote'>{escapar_html(just)}</div></div>"
    )


def alternar_bloqueo() -> None:
    """Callback del interruptor: guarda en el núcleo el valor de `kill_switch_ui`.

    Activa o desactiva el bloqueo de aperturas (efecto persistente en core.ordenes).
    """
    ordenes.fijar_kill_switch(bool(st.session_state.get("kill_switch_ui")))


def renderizar_ordenes_propuestas(altura: int = 300) -> None:
    """Dibuja el panel derecho: interruptor de emergencia, vigilancias y órdenes pendientes.

    `altura` (px) fija el alto del área con scroll cuando hay más de un elemento. Consume el
    aviso de `st.session_state[CLAVE_AVISO]` y lo muestra. Los botones Confirmar / Rechazar
    llaman a core.ordenes (confirmar puede enviar la orden a MT5) y reejecutan la
    app completa. Si falla la lectura muestra una advertencia y no dibuja el panel.
    """
    # Recupera (y borra) el aviso dejado por la acción anterior
    aviso = st.session_state.pop(CLAVE_AVISO, None)

    # Lee el estado actual: pendientes, interruptor y vigilancias del usuario
    try:
        pendientes = ordenes.listar_pendientes()
        bloqueado = ordenes.kill_switch_activo()
        uid = usuario_id()
        vigs = vigilancia.listar(uid)
    except Exception as e:  # noqa: BLE001
        st.warning(f"No se pudieron leer las órdenes del agente: {e}")
        return

    # Panel con clave fija: estilos.css lo apunta con el prefijo agp_
    with st.container(key="agp_panel"):
        st.html(cabecera_agente(
            "pending_actions", "Órdenes propuestas",
            "El agente propone y tú confirmas. Solo opera solo si autorizas una vigilancia. Solo cuenta demo.",
        ))
        # Resultado de la última acción (verde si ok, rojo si error)
        if aviso:
            (st.success if aviso[0] == "ok" else st.error)(aviso[1])

        # Interruptor de emergencia: bloquea proponer y confirmar aperturas
        st.session_state["kill_switch_ui"] = bloqueado  # el interruptor refleja siempre lo guardado
        with st.container(key="agp_kill"):
            st.toggle(
                "⛔ Bloquear aperturas", key="kill_switch_ui", on_change=alternar_bloqueo,
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
            st.container(height=altura, border=False, key="agp_scroll")
            if len(pendientes) + len(vigs) > 1 else st.container(border=False, key="agp_scroll")
        )
        with contenedor:
            # Sección de vigilancias automáticas
            if vigs:
                st.html("<div class='ag-sec'>Vigilancia automática</div>")
                if any(v["estado"] == vigilancia.ACTIVA for v in vigs):
                    # con vigilancias activas, solo esta sección se refresca sola (sin recargar la página)
                    st.fragment(run_every="8s")(seccion_vigilancias)(uid)
                else:
                    seccion_vigilancias(uid)
            # Subtítulo de órdenes solo si hay ambos grupos
            if vigs and pendientes:
                st.html("<div class='ag-sec'>Órdenes pendientes</div>")
            # Una tarjeta por orden pendiente, con botones Confirmar y Rechazar
            for o in pendientes:
                with st.container(key=f"agp_card_{clase_lado(o)}_{o['id']}"):
                    st.html(tarjeta_pendiente(o))
                    if st.button("Confirmar orden", key=f"agp_ok_{o['id']}", icon=":material/check:",
                                 type="primary", width="stretch"):
                        res = ordenes.confirmar_orden(o["id"])
                        st.session_state[CLAVE_AVISO] = ("ok" if res["ok"] else "error", res["mensaje"])
                        st.rerun(scope="app")  # refresca también el historial de la izquierda
                    if st.button("Rechazar", key=f"agp_no_{o['id']}", width="stretch"):
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
