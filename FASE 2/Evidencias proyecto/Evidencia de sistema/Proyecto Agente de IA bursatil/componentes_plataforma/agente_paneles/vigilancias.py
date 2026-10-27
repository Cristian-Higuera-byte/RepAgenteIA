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
delegando la lógica en nucleo_agente.vigilancia. Lo usa propuestas.py.
"""
from typing import Any

import streamlit as st

from componentes_plataforma.agente_paneles.datos import CLAVE_AVISO
from componentes_plataforma.agente_paneles.formato import escapar_html, hora, par_clave_valor
from componentes_plataforma.vigilancia_terminos import pedir as pedir_terminos
from nucleo_agente import vigilancia


# TITULO USUARIO ID

def usuario_id() -> str:
    """Devuelve el id del usuario en sesión como texto, o "local" si no hay usuario."""
    return str((st.session_state.get("usuario_informacion") or {}).get("id") or "local")


# TITULO TARJETA VIGILANCIA

def tarjeta_vigilancia(v: dict[str, Any]) -> str:
    """Construye el HTML de la tarjeta de una vigilancia `v` (diccionario del núcleo).

    Según su estado muestra: si está pendiente, el plazo para autorizar, la duración y el
    aviso de operación autónoma; si está activa, el vencimiento, los chequeos y el último
    y próximo chequeo. Siempre incluye riesgo por operación, operaciones e intervalo, y
    una cita con la instrucción o el último resumen del agente.
    """
    pendiente = v["estado"] == vigilancia.PENDIENTE
    # Operaciones realizadas sobre el máximo permitido
    operaciones = f"{v.get('operaciones') or 0}/{v['max_operaciones']}"
    # Contenido distinto según esté pendiente de autorizar o activa
    if pendiente:
        tiempo = f"Autoriza antes de las {hora(v.get('expira_autorizacion'))}"
        insignia = ("<span class='agente-insignia' style='color:#f0b90b;border-color:#f0b90b55;background:#f0b90b18'>"
                 "Pendiente de autorizar</span>")
        cuarto = par_clave_valor("Dura", f"{v['duracion_horas']:g} h")
        pie = (f"<div class='agente-aviso'>El agente analizará <b>{escapar_html(v['simbolo'])}</b> y, si autorizas, "
               "<b>comprará o venderá solo</b>, sin pedirte confirmación, dentro de estos límites. "
               "Solo cuenta demo; puedes detenerla cuando quieras.</div>")
        cita = escapar_html((v.get("instruccion") or "").strip())
    else:
        tiempo = f"Vence a las {hora(v.get('vence'))}"
        insignia = ("<span class='agente-insignia' style='color:#2ebd85;border-color:#2ebd8555;background:#2ebd8518'>"
                 "Activa</span>")
        cuarto = par_clave_valor("Chequeos", str(v.get("chequeos") or 0))
        ultimo = hora(v["ultimo_chequeo"]) if v.get("ultimo_chequeo") else "—"
        pie = (f"<div class='agente-aviso'>Último chequeo {ultimo} · próximo {hora(v.get('proximo_chequeo'))}</div>")
        cita = escapar_html((v.get("ultimo_resumen") or "Aún sin chequeos.").strip())
    # Cuadrícula de parámetros común a ambos estados
    datos = (par_clave_valor("Riesgo/op.", f"{v['riesgo_pct']:g}%") + par_clave_valor("Operaciones", operaciones)
             + par_clave_valor("Cada", f"{v['intervalo_min']} min") + cuarto)
    # Ensambla la tarjeta; la cita solo se agrega si hay texto
    return (
        "<div class='agente-fila'>"
        f"<div class='agente-superior'><span class='agente-t'>{escapar_html(tiempo)}</span>{insignia}</div>"
        f"<div class='agente-principal'><span class='auto'>VIGILANCIA</span> · {escapar_html(v['simbolo'])}</div>"
        f"<div class='agente-cuadricula'>{datos}</div>{pie}"
        + (f"<div class='agente-quote'>{cita}</div>" if cita else "")
        + "</div>"
    )


# TITULO SECCION VIGILANCIAS

def seccion_vigilancias(uid: str) -> None:
    """Dibuja las tarjetas de todas las vigilancias del usuario `uid` con sus botones.

    Pendientes: Autorizar (abre la ventana de términos y condiciones, donde el usuario acepta o rechaza) y Rechazar. Activas: Detener. Cada acción guarda un aviso en
    `st.session_state[CLAVE_AVISO]` y reejecuta toda la app (`st.rerun(scope="app")`) para
    refrescar también el historial. Se puede ejecutar como fragmento con auto-refresco.
    """
    for v in vigilancia.listar(uid):
        with st.container(key=f"agente_propuestas_tarjeta_auto_{v['id']}"):
            st.html(tarjeta_vigilancia(v))
            if v["estado"] == vigilancia.PENDIENTE:
                if st.button("Autorizar vigilancia", key=f"agente_propuestas_aceptar_vig_{v['id']}", icon=":material/check:",
                             type="primary", width="stretch"):
                    pedir_terminos(v["id"])     # no se activa al instante: primero la ventana de términos y condiciones
                    st.rerun(scope="app")
                if st.button("Rechazar", key=f"agente_propuestas_no_vig_{v['id']}", width="stretch"):
                    vigilancia.rechazar(v["id"], uid)
                    st.rerun(scope="app")
            else:
                if st.button("Detener vigilancia", key=f"agente_propuestas_no_stopvig_{v['id']}",
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
