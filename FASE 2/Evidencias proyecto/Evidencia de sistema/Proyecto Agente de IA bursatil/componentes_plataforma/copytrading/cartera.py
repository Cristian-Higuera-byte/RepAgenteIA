# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.


# -------------------------------------------------------------------------------------------------------
# ----------------------------------- INICIO Piña y Jara cartera .PY ------------------------------------
# -------------------------------------------------------------------------------------------------------

"""Sección «Cartera» del copy trading: las copias del usuario con su estado y resultado, y los botones para pausarlas, reanudarlas o detenerlas.

Cada copia muestra la estrategia, el @gestor, cómo se asigna (importe o multiplicador), su take profit y stop loss, las posiciones abiertas y cerradas y el resultado
realizado. Al detener una copia se puede pedir cerrar también sus posiciones abiertas y restaurar el perfil de inversor anterior. También muestra la comisión de rendimiento pagada y la pendiente. Debajo de cada una, las operaciones que se intentaron replicar y cómo salieron.
La lógica está en `herramientas/copiador.py`; los estilos (ges-*) en estilos.css.
"""
from datetime import datetime
from html import escape

import pandas as pd
import streamlit as st

from componentes_plataforma.copytrading import perfil_copia
from herramientas import copiador

# Aviso de la última acción (se muestra una vez), texto y estilo de cada estado de la copia
_CLAVE_AVISO = "cartera_copias_aviso"
_ESTADOS = {"activa": ("Activa", "p"), "pausada": ("Pausada", "m"), "cerrada": ("Detenida", "c")}
_MOTIVOS = {"stop_loss": "Stop loss alcanzado", "take_profit": "Take profit alcanzado", "usuario": "Detenida por ti", "usuario_cierra_posiciones": "Detenida por ti (con cierre de posiciones)"}
_ESTADOS_OP = {"pendiente": "Pendiente", "copiada": "Abierta", "cerrada": "Cerrada", "fallida": "No copiada"}


# TITULO ACCION

def _accion(funcion, *argumentos, exito: str, **opciones) -> None:
    """Ejecuta una acción de `copiador` y deja el aviso (éxito o el error legible). Sirve de `on_click`."""
    try:
        funcion(*argumentos, **opciones)
        st.session_state[_CLAVE_AVISO] = ("ok", exito)
    except copiador.ErrorCopia as e:
        st.session_state[_CLAVE_AVISO] = ("error", str(e))
    except Exception:  # noqa: BLE001
        st.session_state[_CLAVE_AVISO] = ("error", "No se pudo completar la acción. Inténtalo de nuevo.")


# TITULO DETENER

def _detener(uid, c: dict, cerrar_posiciones: bool, restaurar_perfil: bool) -> None:
    """Detiene la copia `c` (con o sin cierre de posiciones) y, si se pidió y la copia tenía un perfil anterior guardado, lo restaura. Deja el aviso. Sirve de `on_click`."""
    try:
        copiador.cambiar_estado_copia(uid, c["id"], "cerrada", cerrar_posiciones=cerrar_posiciones)
        restaurado = restaurar_perfil and c.get("perfil_previo") and perfil_copia.restaurar(uid, c["perfil_previo"])
        st.session_state[_CLAVE_AVISO] = ("ok", "Dejaste de copiar esta estrategia." + (" Tu perfil de inversor volvió a como estaba." if restaurado else ""))
    except copiador.ErrorCopia as e:
        st.session_state[_CLAVE_AVISO] = ("error", str(e))
    except Exception:  # noqa: BLE001
        st.session_state[_CLAVE_AVISO] = ("error", "No se pudo completar la acción. Inténtalo de nuevo.")


# TITULO TARJETA

def _cabecera(c: dict) -> str:
    """HTML de la cabecera de una copia: estrategia, estado y cifras."""
    texto, cls = _ESTADOS.get(c["estado"], (c["estado"], "b"))
    asignacion = f"${float(c['importe']):,.0f}" if c.get("modo") == "importe" and c.get("importe") else f"x{float(c.get('multiplicador') or 0):g}"
    protecciones = " · ".join(x for x in (f"Take profit {float(c['take_profit_pct']):g}%" if c.get("take_profit_pct") else "", f"Stop loss {float(c['stop_loss_pct']):g}%" if c.get("stop_loss_pct") else "") if x)
    motivo = f" · {_MOTIVOS[c['motivo_cierre']]}" if c["estado"] == "cerrada" and c.get("motivo_cierre") in _MOTIVOS else ""
    res = c["resultado"]
    return (f"<div class='ges-cab'><span class='ges-nombre'>{escape(c['nombre'])}</span><span class='ges-estado {cls}'>{texto}</span><span class='ges-tipo'>@{escape(c['gestor'])}{motivo}</span></div>"
            f"<div class='ges-cifras'>Asignación: <b>{asignacion}</b> · Posiciones abiertas: <b>{c['abiertas']}</b> · Cerradas: <b>{c['cerradas']}</b> · "
            f"Resultado realizado: <b style='color:{'#3fb950' if res >= 0 else '#f85149'}'>{'-' if res < 0 else ''}${abs(res):,.2f}</b>{' · ' + protecciones if protecciones else ''}</div>"
            f"<div class='ges-cifras'>Comisión de rendimiento: <b>{c['comision_pct_estrategia']:g}%</b> · Pagada: <b>${c['comision_pagada']:,.2f}</b> · Pendiente: <b>${c['comision_pendiente']:,.2f}</b></div>")


# TITULO OPERACIONES

def _operaciones(uid, c: dict) -> None:
    """Tabla de las operaciones que se intentaron replicar en la copia y cómo salieron."""
    with st.expander("Operaciones copiadas"):
        try:
            filas = copiador.operaciones_de_copia(uid, c["id"])
        except Exception:  # noqa: BLE001
            st.error("No se pudieron consultar las operaciones. Inténtalo de nuevo en un momento.")
            return
        if not filas:
            st.info("Todavía no se copió ninguna operación.")
            return
        tabla = []
        for f in filas:
            try:
                fecha = datetime.fromisoformat(str(f["fecha"]).replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
            except (KeyError, ValueError):
                fecha = ""
            tabla.append({"Fecha": fecha, "Símbolo": f["simbolo"], "Tipo": "COMPRA" if f["lado"] == "compra" else "VENTA", "Volumen gestor": f.get("volumen_origen"),
                          "Volumen copia": f.get("volumen_copia"), "Estado": _ESTADOS_OP.get(f["estado"], f["estado"]), "Detalle": f.get("error") or ""})
        st.dataframe(pd.DataFrame(tabla), hide_index=True, width="stretch")


# TITULO RENDERIZAR CARTERA

def renderizar_cartera_copias() -> None:
    """Dibuja la sección Cartera: las copias del usuario con sus botones (pausar, reanudar, detener) y sus operaciones. No devuelve nada."""
    if not copiador.disponible():
        st.info("Las copias necesitan la base de datos (Supabase) y el modo multiusuario, que no están activos en este equipo.")
        return
    usuario = st.session_state.get("usuario_informacion") or {}
    uid = usuario.get("id") if isinstance(usuario, dict) else None
    if uid is None:
        st.info("Inicia sesión para ver tus copias.")
        return
    aviso = st.session_state.pop(_CLAVE_AVISO, None)
    if aviso:
        (st.success if aviso[0] == "ok" else st.error)(aviso[1])
    try:
        copias = copiador.mis_copias(uid)
    except Exception:  # noqa: BLE001
        st.error("No se pudieron consultar tus copias. Inténtalo de nuevo en un momento.")
        return
    if not copias:
        st.info("Todavía no copias ninguna estrategia. Elige una en la pestaña Estrategias y pulsa Copiar.")
        return
    for c in copias:
        with st.container(border=True):
            st.html(_cabecera(c))
            if c["estado"] == "pausada" and c.get("motivo_cierre") == "comision_pendiente":
                st.warning(f"Copia pausada: tienes ${c['comision_pendiente']:,.2f} de comisión pendiente. Recarga tu billetera virtual y se reanudará sola.")
            if c["estado"] != "cerrada":
                b1, b2, b3, b4 = st.columns([1.2, 3, 1.4, 1.6], vertical_alignment="bottom")
                if c["estado"] == "activa":
                    b1.button("Pausar", key=f"cop_pausar_{c['id']}", width="stretch", on_click=_accion, args=(copiador.cambiar_estado_copia, uid, c["id"], "pausada"),
                              kwargs={"exito": "Copia pausada: no abrirá operaciones nuevas, pero seguirá cerrando las que cierre el gestor."})
                else:
                    b1.button("Reanudar", key=f"cop_reanudar_{c['id']}", type="primary", width="stretch", on_click=_accion, args=(copiador.cambiar_estado_copia, uid, c["id"], "activa"),
                              kwargs={"exito": "Copia reanudada."})
                cerrar = b2.checkbox("Cerrar también mis posiciones abiertas de esta copia", key=f"cop_cerrar_pos_{c['id']}")
                restaurar = st.checkbox("Restaurar mi perfil de inversor anterior", key=f"cop_restaurar_{c['id']}", value=True) if c.get("perfil_previo") else False
                confirma = b3.checkbox("Confirmo detener", key=f"cop_confirma_{c['id']}")
                b4.button("Dejar de copiar", key=f"cop_detener_{c['id']}", width="stretch", disabled=not confirma, on_click=_detener, args=(uid, c, cerrar, restaurar))
            _operaciones(uid, c)



# -------------------------------------------------------------------------------------------------------
# ------------------------------------- FIN Piña y Jara cartera .PY -------------------------------------
# -------------------------------------------------------------------------------------------------------

# Sitio Web Creado por Piña y Jara Transportes y Servicios Ltda.
# Dirección: José Joaquín Prieto #5373 -
# San Miguel - Santiago - Chile
# contacto.pinayjara@gmail.com
# https://www.pinayjara.cl
# Creado, Programado y Diseñado por Piña y Jara
# Transportes y Servicios Ltda.
