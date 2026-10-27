# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ---------------------------------- INICIO Piña y Jara vigilancias .PY ---------------------------------
# -------------------------------------------------------------------------------------------------------

"""Vigilancias automáticas: tarjetas del panel derecho (pendientes de autorizar y activas).

Una vigilancia es una autorización para que el agente opere solo, dentro de límites, sobre
un símbolo. Este módulo dibuja sus tarjetas y los botones Autorizar / Rechazar / Detener,
delegando la lógica en core.vigilancia. Lo usa propuestas.py.
"""
from typing import Any

import streamlit as st

from components.agente_paneles.datos import CLAVE_AVISO
from components.agente_paneles.formato import escapar_html, hora, par_clave_valor
from core import vigilancia


def usuario_id() -> str:
    """Devuelve el id del usuario en sesión como texto, o "local" si no hay usuario."""
    return str((st.session_state.get("usuario_info") or {}).get("id") or "local")


def tarjeta_vigilancia(v: dict[str, Any]) -> str:
    """Construye el HTML de la tarjeta de una vigilancia `v` (diccionario del núcleo).

    Según su estado muestra: si está pendiente, el plazo para autorizar, la duración y el
    aviso de operación autónoma; si está activa, el vencimiento, los chequeos y el último
    y próximo chequeo. Siempre incluye riesgo por operación, operaciones e intervalo, y
    una cita con la instrucción o el último resumen del agente.
    """
    pendiente = v["estado"] == vigilancia.PENDIENTE
    # Operaciones realizadas sobre el máximo permitido
    ops = f"{v.get('operaciones') or 0}/{v['max_operaciones']}"
    # Contenido distinto según esté pendiente de autorizar o activa
    if pendiente:
        tiempo = f"Autoriza antes de las {hora(v.get('expira_autorizacion'))}"
        badge = ("<span class='ag-badge' style='color:#f0b90b;border-color:#f0b90b55;background:#f0b90b18'>"
                 "Pendiente de autorizar</span>")
        cuarto = par_clave_valor("Dura", f"{v['duracion_horas']:g} h")
        pie = (f"<div class='ag-aviso'>El agente analizará <b>{escapar_html(v['simbolo'])}</b> y, si autorizas, "
               "<b>comprará o venderá solo</b>, sin pedirte confirmación, dentro de estos límites. "
               "Solo cuenta demo; puedes detenerla cuando quieras.</div>")
        cita = escapar_html((v.get("instruccion") or "").strip())
    else:
        tiempo = f"Vence a las {hora(v.get('vence'))}"
        badge = ("<span class='ag-badge' style='color:#2ebd85;border-color:#2ebd8555;background:#2ebd8518'>"
                 "Activa</span>")
        cuarto = par_clave_valor("Chequeos", str(v.get("chequeos") or 0))
        ultimo = hora(v["ultimo_chequeo"]) if v.get("ultimo_chequeo") else "—"
        pie = (f"<div class='ag-aviso'>Último chequeo {ultimo} · próximo {hora(v.get('proximo_chequeo'))}</div>")
        cita = escapar_html((v.get("ultimo_resumen") or "Aún sin chequeos.").strip())
    # Cuadrícula de parámetros común a ambos estados
    datos = (par_clave_valor("Riesgo/op.", f"{v['riesgo_pct']:g}%") + par_clave_valor("Operaciones", ops)
             + par_clave_valor("Cada", f"{v['intervalo_min']} min") + cuarto)
    # Ensambla la tarjeta; la cita solo se agrega si hay texto
    return (
        "<div class='ag-row'>"
        f"<div class='ag-top'><span class='ag-t'>{escapar_html(tiempo)}</span>{badge}</div>"
        f"<div class='ag-main'><span class='auto'>VIGILANCIA</span> · {escapar_html(v['simbolo'])}</div>"
        f"<div class='ag-grid'>{datos}</div>{pie}"
        + (f"<div class='ag-quote'>{cita}</div>" if cita else "")
        + "</div>"
    )


def seccion_vigilancias(uid: str) -> None:
    """Dibuja las tarjetas de todas las vigilancias del usuario `uid` con sus botones.

    Pendientes: Autorizar y Rechazar. Activas: Detener. Cada acción guarda un aviso en
    `st.session_state[CLAVE_AVISO]` y reejecuta toda la app (`st.rerun(scope="app")`) para
    refrescar también el historial. Se puede ejecutar como fragmento con auto-refresco.
    """
    for v in vigilancia.listar(uid):
        with st.container(key=f"agp_card_auto_{v['id']}"):
            st.html(tarjeta_vigilancia(v))
            if v["estado"] == vigilancia.PENDIENTE:
                if st.button("Autorizar vigilancia", key=f"agp_ok_vig_{v['id']}", icon=":material/check:",
                             type="primary", width="stretch"):
                    res = vigilancia.autorizar(v["id"], uid)
                    st.session_state[CLAVE_AVISO] = ("ok" if res["ok"] else "error", res["mensaje"])
                    st.rerun(scope="app")
                if st.button("Rechazar", key=f"agp_no_vig_{v['id']}", width="stretch"):
                    vigilancia.rechazar(v["id"], uid)
                    st.rerun(scope="app")
            else:
                if st.button("Detener vigilancia", key=f"agp_no_stopvig_{v['id']}",
                             icon=":material/stop_circle:", width="stretch"):
                    st.session_state[CLAVE_AVISO] = ("ok", vigilancia.detener(uid, vid=v["id"])["mensaje"])
                    st.rerun(scope="app")


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- FIN Piña y Jara vigilancias .PY -----------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
